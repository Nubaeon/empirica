#!/usr/bin/env python3
"""
Epistemic Documentation Commands - docs-assess and docs-explain

docs-assess: Analyzes documentation coverage and suggests NotebookLM content
docs-explain: Retrieves focused information about Empirica topics

Philosophy:
- "Know what you know" - Measure actual documentation coverage
- "Know what you don't know" - Reveal undocumented features
- "Honest uncertainty" - Report coverage gaps with precision
- "Focused retrieval" - Get exactly what you need to know

Usage:
    empirica docs-assess                     # Full documentation assessment
    empirica docs-assess --output json       # JSON output for automation
    empirica docs-explain --topic "vectors"  # Explain epistemic vectors
    empirica docs-explain --question "How do I start a session?"
"""

import ast
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..cli_utils import handle_cli_error


@dataclass
class FeatureCoverage:
    """Tracks coverage for a feature category."""
    name: str
    total: int
    documented: int
    undocumented: list[str] = field(default_factory=list)

    @property
    def coverage(self) -> float:
        return self.documented / self.total if self.total > 0 else 0.0

    @property
    def moon(self) -> str:
        """Convert coverage to moon phase."""
        if self.coverage >= 0.85:
            return "🌕"
        elif self.coverage >= 0.70:
            return "🌔"
        elif self.coverage >= 0.50:
            return "🌓"
        elif self.coverage >= 0.30:
            return "🌒"
        else:
            return "🌑"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "total": self.total,
            "documented": self.documented,
            "coverage": round(self.coverage * 100, 1),
            "moon": self.moon,
            "undocumented": self.undocumented[:10]  # Top 10
        }


class EpistemicDocsAgent:
    """
    Epistemic Documentation Assessment Agent.

    Measures documentation coverage against actual codebase features.
    Returns honest epistemic assessment of what's documented vs hidden.
    """

    def __init__(self, project_root: Path | None = None, verbose: bool = False):
        self.root = project_root or Path.cwd()
        self.verbose = verbose
        self.categories: list[FeatureCoverage] = []

    def _load_all_docs_content(self) -> str:
        """Load all documentation content for searching."""
        docs_dir = self.root / "docs"
        readme = self.root / "README.md"

        content = ""

        # Load README
        if readme.exists():
            content += readme.read_text()

        # Load all non-archived docs
        if docs_dir.exists():
            for md_file in docs_dir.rglob("*.md"):
                if "_archive" not in str(md_file):
                    try:
                        content += "\n" + md_file.read_text()
                    except Exception:
                        pass

        return content.lower()

    def _extract_cli_commands(self) -> list[str]:
        """Extract all CLI commands from cli_core.py."""
        cli_core = self.root / "empirica" / "cli" / "cli_core.py"
        commands = []

        if not cli_core.exists():
            return commands

        content = cli_core.read_text()

        # Find COMMAND_HANDLERS dictionary entries
        # Pattern: 'command-name': handler_function (single quotes)
        pattern = r"'([a-z]+-?[a-z-]*)'\s*:\s*\w+"
        matches = re.findall(pattern, content)
        commands.extend(matches)

        # Also find add_parser calls with either quote style
        parser_pattern = r"add_parser\(\s*['\"]([a-z]+-?[a-z-]*)['\"]"
        parser_matches = re.findall(parser_pattern, content)
        commands.extend(parser_matches)

        return list(set(commands))

    def _extract_core_modules(self) -> tuple[list[str], dict[str, list[str]]]:
        """
        Extract ALL classes/modules from core/ with their categories.

        Returns:
            tuple: (all_classes, category_map)
                - all_classes: List of all discovered class names
                - category_map: Dict mapping directory name -> list of classes
        """
        core_dir = self.root / "empirica" / "core"
        modules = []
        category_map = {}

        if not core_dir.exists():
            return modules, category_map

        for py_file in core_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            try:
                content = py_file.read_text()
                # Find class definitions
                class_pattern = r"^class\s+(\w+)\s*[\(:]"
                matches = re.findall(class_pattern, content, re.MULTILINE)

                # Get category from parent directory
                rel_path = py_file.relative_to(core_dir)
                if len(rel_path.parts) > 1:
                    # e.g., lessons/storage.py -> "Lessons"
                    category = rel_path.parts[0].replace("_", " ").title()
                else:
                    # e.g., sentinel.py -> "Sentinel"
                    category = py_file.stem.replace("_", " ").title()

                for match in matches:
                    # Filter out internal/private classes
                    if not match.startswith("_") and len(match) > 3:
                        modules.append(match)
                        # Add to category map
                        if category not in category_map:
                            category_map[category] = []
                        category_map[category].append(match)
            except Exception:
                pass

        return list(set(modules)), category_map

    def _check_if_documented(self, term: str, docs_content: str) -> bool:
        """Check if a term appears in documentation."""
        # Normalize the term for searching
        normalized = term.lower().replace("-", " ").replace("_", " ")

        # Check various forms
        return (
            term.lower() in docs_content or
            normalized in docs_content or
            term.replace("-", "_").lower() in docs_content or
            # For camelCase classes, check word boundaries
            re.search(r'\b' + term.lower() + r'\b', docs_content) is not None
        )

    def assess_cli_coverage(self, docs_content: str) -> FeatureCoverage:
        """Assess CLI command documentation coverage."""
        commands = self._extract_cli_commands()
        documented = []
        undocumented = []

        for cmd in commands:
            if self._check_if_documented(cmd, docs_content):
                documented.append(cmd)
            else:
                undocumented.append(cmd)

        return FeatureCoverage(
            name="CLI Commands",
            total=len(commands),
            documented=len(documented),
            undocumented=sorted(undocumented)
        )

    def assess_core_coverage(self, docs_content: str) -> tuple[FeatureCoverage, dict[str, list[str]]]:
        """
        Assess core module documentation coverage - ALL discovered classes.

        Returns:
            tuple: (coverage, category_map) for use by assess_feature_categories
        """
        modules, category_map = self._extract_core_modules()
        documented = []
        undocumented = []

        # Check ALL discovered modules - no static filtering
        for module in modules:
            if self._check_if_documented(module, docs_content):
                documented.append(module)
            else:
                undocumented.append(module)

        return FeatureCoverage(
            name="Core Modules",
            total=len(modules),
            documented=len(documented),
            undocumented=sorted(undocumented)
        ), category_map

    def assess_feature_categories(self, docs_content: str, category_map: dict[str, list[str]]) -> list[FeatureCoverage]:
        """
        Assess coverage of feature categories - DYNAMICALLY discovered from code.

        Args:
            docs_content: All documentation text
            category_map: Dict from _extract_core_modules mapping directory -> classes
        """
        results = []

        # Use dynamically discovered categories from code structure
        for category_name, classes in sorted(category_map.items()):
            documented = []
            undocumented = []

            for cls in classes:
                if self._check_if_documented(cls, docs_content):
                    documented.append(cls)
                else:
                    undocumented.append(cls)

            coverage = FeatureCoverage(
                name=category_name,
                total=len(classes),
                documented=len(documented),
                undocumented=sorted(undocumented)
            )
            results.append(coverage)

        return results

    def run_assessment(self) -> dict[str, Any]:
        """Run full documentation assessment with DYNAMIC discovery."""
        docs_content = self._load_all_docs_content()

        # Assess each category - core_coverage now returns category_map for features
        cli_coverage = self.assess_cli_coverage(docs_content)
        core_coverage, category_map = self.assess_core_coverage(docs_content)
        feature_categories = self.assess_feature_categories(docs_content, category_map)

        self.categories = [cli_coverage, core_coverage] + feature_categories

        # Calculate overall coverage
        total_items = sum(c.total for c in self.categories)
        documented_items = sum(c.documented for c in self.categories)
        overall_coverage = documented_items / total_items if total_items > 0 else 0.0

        # Generate epistemic assessment
        if overall_coverage >= 0.80:
            know = 0.85
            uncertainty = 0.15
            assessment = "Documentation is comprehensive"
        elif overall_coverage >= 0.60:
            know = 0.65
            uncertainty = 0.30
            assessment = "Documentation has notable gaps"
        elif overall_coverage >= 0.40:
            know = 0.45
            uncertainty = 0.50
            assessment = "Significant features undocumented"
        else:
            know = 0.25
            uncertainty = 0.70
            assessment = "Major documentation debt"

        return {
            "overall": {
                "coverage": round(overall_coverage * 100, 1),
                "total_features": total_items,
                "documented": documented_items,
                "moon": self._score_to_moon(overall_coverage)
            },
            "epistemic_assessment": {
                "know": know,
                "uncertainty": uncertainty,
                "assessment": assessment
            },
            "categories": [c.to_dict() for c in self.categories],
            "recommendations": self._generate_recommendations(),
            "notebooklm_suggestions": self._generate_notebooklm_suggestions()
        }

    def _score_to_moon(self, score: float) -> str:
        """Convert 0-1 score to moon phase."""
        if score >= 0.85:
            return "🌕"
        elif score >= 0.70:
            return "🌔"
        elif score >= 0.50:
            return "🌓"
        elif score >= 0.30:
            return "🌒"
        else:
            return "🌑"

    def _generate_recommendations(self) -> list[str]:
        """Generate prioritized recommendations."""
        recommendations = []

        for category in self.categories:
            if category.coverage < 0.50 and category.undocumented:
                recommendations.append(
                    f"Document {category.name}: {', '.join(category.undocumented[:3])}"
                )

        return recommendations[:5]  # Top 5 recommendations

    def _generate_notebooklm_suggestions(self) -> dict[str, Any]:
        """Generate NotebookLM content suggestions based on doc structure."""
        docs_dir = self.root / "docs"
        suggestions = {
            "slide_decks": [],
            "infographics": [],
            "audio_overviews": [],
            "study_guides": []
        }

        if not docs_dir.exists():
            return suggestions

        # Group docs by directory/topic
        doc_groups = {}
        for md_file in docs_dir.rglob("*.md"):
            if "_archive" in str(md_file):
                continue
            rel_path = md_file.relative_to(docs_dir)
            parent = str(rel_path.parent) if rel_path.parent != Path(".") else "root"
            if parent not in doc_groups:
                doc_groups[parent] = []
            doc_groups[parent].append(str(rel_path))

        # Slide deck suggestions - grouped tutorials/guides
        if "guides" in doc_groups:
            suggestions["slide_decks"].append({
                "topic": "Getting Started with Empirica",
                "sources": doc_groups["guides"][:5],
                "audience": "user",
                "format": "tutorial"
            })

        if "root" in doc_groups:
            intro_docs = [d for d in doc_groups.get("root", [])
                         if any(x in d.lower() for x in ["start", "install", "quickstart", "explained"])]
            if intro_docs:
                suggestions["slide_decks"].append({
                    "topic": "Empirica Overview",
                    "sources": intro_docs,
                    "audience": "user",
                    "format": "overview"
                })

        # Architecture docs -> infographics
        if "architecture" in doc_groups:
            suggestions["infographics"].append({
                "topic": "System Architecture",
                "sources": doc_groups["architecture"][:6],
                "audience": "developer",
                "recommended": True
            })
            suggestions["slide_decks"].append({
                "topic": "Empirica Architecture Deep Dive",
                "sources": doc_groups["architecture"],
                "audience": "developer",
                "format": "technical"
            })

        # Reference/API docs -> study guides
        if "reference" in doc_groups or "reference/api" in doc_groups:
            api_docs = doc_groups.get("reference/api", []) + doc_groups.get("reference", [])
            suggestions["study_guides"].append({
                "topic": "CLI & API Reference",
                "sources": api_docs[:8],
                "audience": "developer"
            })

        # Conceptual docs -> audio overviews
        epistemic_docs = []
        for group, files in doc_groups.items():
            epistemic_docs.extend([f for f in files if "epistemic" in f.lower() or "vector" in f.lower()])
        if epistemic_docs:
            suggestions["audio_overviews"].append({
                "topic": "Understanding Epistemic Vectors",
                "sources": epistemic_docs[:3],
                "audience": "user",
                "format": "deep_dive"
            })

        # Integration docs
        if "integrations" in doc_groups:
            suggestions["slide_decks"].append({
                "topic": "Integrations & Extensions",
                "sources": doc_groups["integrations"],
                "audience": "developer",
                "format": "how-to"
            })

        # System prompts -> specialized audio
        if "system-prompts" in doc_groups:
            suggestions["audio_overviews"].append({
                "topic": "Multi-Model Support",
                "sources": doc_groups["system-prompts"][:4],
                "audience": "developer",
                "format": "brief"
            })

        return suggestions


def handle_docs_assess(args) -> int:
    """Handle the docs-assess command."""
    try:
        project_root = Path(args.project_root) if args.project_root else None
        verbose = getattr(args, 'verbose', False)
        output_format = getattr(args, 'output', 'human')
        summary_only = getattr(args, 'summary_only', False)

        agent = EpistemicDocsAgent(project_root=project_root, verbose=verbose)
        result = agent.run_assessment()

        # Lightweight summary for bootstrap context (~50 tokens)
        if summary_only:
            summary = _generate_summary(result, agent.categories)
            if output_format == 'json':
                print(json.dumps(summary))
            else:
                print(f"Docs: {summary['coverage']}% {summary['moon']} | "
                      f"K:{summary['know']:.0%} U:{summary['uncertainty']:.0%} | "
                      f"Gaps: {', '.join(summary['top_gaps'][:2]) or 'none'}")
            return 0

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            _print_human_output(result, agent.categories, verbose)

        return 0

    except Exception as e:
        return handle_cli_error(e, "docs-assess")


def _generate_summary(result: dict, categories: list) -> dict:
    """Generate lightweight summary (~50 tokens) for bootstrap context."""
    overall = result["overall"]
    epistemic = result["epistemic_assessment"]

    # Find top gaps (categories with coverage < 70%)
    top_gaps = [c.name for c in categories if c.coverage < 0.70][:3]

    # Count total docs
    docs_dir = Path.cwd() / "docs"
    doc_count = len(list(docs_dir.rglob("*.md"))) if docs_dir.exists() else 0

    return {
        "coverage": overall["coverage"],
        "moon": overall["moon"],
        "know": epistemic["know"],
        "uncertainty": epistemic["uncertainty"],
        "top_gaps": top_gaps,
        "doc_count": doc_count
    }


def _print_human_output(result: dict, categories: list[FeatureCoverage], verbose: bool):
    """Print human-readable output."""
    overall = result["overall"]
    epistemic = result["epistemic_assessment"]

    print("\n" + "=" * 60)
    print("📚 EPISTEMIC DOCUMENTATION ASSESSMENT")
    print("=" * 60)

    # Overall score
    print(f"\n{overall['moon']} Overall Coverage: {overall['coverage']}%")
    print(f"   Features: {overall['documented']}/{overall['total_features']} documented")

    # Epistemic assessment
    print(f"\n📊 Epistemic Assessment:")
    print(f"   know: {epistemic['know']:.2f}")
    print(f"   uncertainty: {epistemic['uncertainty']:.2f}")
    print(f"   → {epistemic['assessment']}")

    # Category breakdown
    print("\n📋 Category Coverage:")
    print("-" * 50)

    for cat in categories:
        status = "✅" if cat.coverage >= 0.70 else "⚠️" if cat.coverage >= 0.40 else "❌"
        print(f"   {cat.moon} {cat.name}: {cat.coverage*100:.0f}% ({cat.documented}/{cat.total})")

        if verbose and cat.undocumented:
            for item in cat.undocumented[:5]:
                print(f"      └─ Missing: {item}")

    # Recommendations
    if result["recommendations"]:
        print("\n💡 Recommendations:")
        for rec in result["recommendations"]:
            print(f"   • {rec}")

    # NotebookLM suggestions
    nlm = result.get("notebooklm_suggestions", {})
    if any(nlm.get(k) for k in ["slide_decks", "infographics", "audio_overviews", "study_guides"]):
        print("\n📽️  NotebookLM Content Suggestions:")
        print("-" * 50)

        if nlm.get("slide_decks"):
            print("\n   🎴 Slide Decks:")
            for deck in nlm["slide_decks"]:
                aud = f"[{deck.get('audience', 'all')}]"
                fmt = deck.get('format', '')
                print(f"      • {deck['topic']} {aud} ({fmt})")
                if verbose:
                    for src in deck.get("sources", [])[:3]:
                        print(f"         └─ {src}")

        if nlm.get("infographics"):
            print("\n   📊 Infographics:")
            for info in nlm["infographics"]:
                rec = "⭐" if info.get("recommended") else ""
                print(f"      • {info['topic']} [{info.get('audience', 'all')}] {rec}")

        if nlm.get("audio_overviews"):
            print("\n   🎧 Audio Overviews:")
            for audio in nlm["audio_overviews"]:
                fmt = audio.get('format', 'deep_dive')
                print(f"      • {audio['topic']} [{audio.get('audience', 'all')}] ({fmt})")

        if nlm.get("study_guides"):
            print("\n   📖 Study Guides:")
            for guide in nlm["study_guides"]:
                print(f"      • {guide['topic']} [{guide.get('audience', 'all')}]")

    print("\n" + "=" * 60)


# =============================================================================
# DOCS-EXPLAIN: Focused Information Retrieval
# =============================================================================

class DocsExplainAgent:
    """
    Epistemic Documentation Explain Agent.

    Retrieves focused information about Empirica topics for users and AIs.
    Inverts docs-assess: instead of analyzing coverage, it retrieves answers.

    Supports two search modes:
    1. Qdrant semantic search (if available): Uses embeddings for better relevance
    2. Keyword-based fallback: Uses topic aliases and keyword matching
    """

    # Topic -> keywords mapping for better matching (used in fallback mode)
    TOPIC_ALIASES = {
        "vectors": ["epistemic", "vectors", "know", "uncertainty", "engagement", "preflight", "postflight"],
        "session": ["session", "create", "start", "cascade", "workflow"],
        "goals": ["goals", "objectives", "subtasks", "tracking", "progress"],
        "check": ["check", "gate", "sentinel", "proceed", "investigate"],
        "findings": ["findings", "unknowns", "dead ends", "breadcrumbs", "learning"],
        "lessons": ["lessons", "procedural", "atomics", "replay", "knowledge graph"],
        "memory": ["memory", "qdrant", "semantic", "eidetic", "episodic"],
        "handoff": ["handoff", "continuity", "context", "switch", "ai-to-ai"],
        "investigation": ["investigation", "branch", "multi-branch", "turtle", "explore"],
        "persona": ["persona", "emerged", "profile", "identity"],
        "calibration": ["calibration", "bayesian", "bias", "accuracy"],
        "env": ["environment", "variable", "config", "configuration", "setting"],
        "autopilot": ["autopilot", "binding", "enforce", "mode", "sentinel"],
    }

    def __init__(self, project_root: Path | None = None, project_id: str | None = None):
        self.root = project_root or Path.cwd()
        self.docs_dir = self.root / "docs"
        self._docs_cache: dict[str, str] = {}
        self.project_id = project_id or self._detect_project_id()
        self._qdrant_available: bool | None = None

    def _detect_project_id(self) -> str | None:
        """Detect project ID from .empirica config or database."""
        try:
            # Try reading from .empirica/project.json
            project_file = self.root / ".empirica" / "project.json"
            if project_file.exists():
                import json
                data = json.loads(project_file.read_text())
                return data.get("project_id")

            # Try querying database for project matching this path
            from empirica.data.session_database import SessionDatabase
            db = SessionDatabase()
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT project_id FROM projects
                WHERE root_path LIKE ? OR name = ?
                ORDER BY created_timestamp DESC LIMIT 1
            """, (f"%{self.root.name}%", self.root.name))
            row = cursor.fetchone()
            db.close()
            if row:
                return row[0]
        except Exception:
            pass
        return None

    def _check_qdrant_available(self) -> bool:
        """Check if Qdrant is available for semantic search."""
        if self._qdrant_available is not None:
            return self._qdrant_available

        try:
            from empirica.core.qdrant.vector_store import _check_qdrant_available
            self._qdrant_available = _check_qdrant_available()
        except ImportError:
            self._qdrant_available = False

        return self._qdrant_available

    def _semantic_search(self, query: str, limit: int = 5) -> list[dict]:
        """
        Perform semantic search using Qdrant if available.

        Returns list of {doc_path, score, concepts, tags} or empty list if unavailable.
        """
        if not self.project_id or not self._check_qdrant_available():
            return []

        try:
            from empirica.core.qdrant.vector_store import search
            results = search(self.project_id, query, kind="docs", limit=limit)
            return results.get("docs", [])
        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"Qdrant search failed: {e}")
            return []

    def _load_docs(self) -> dict[str, str]:
        """Load all docs into memory with their content."""
        if self._docs_cache:
            return self._docs_cache

        if not self.docs_dir.exists():
            return {}

        for md_file in self.docs_dir.rglob("*.md"):
            if "_archive" in str(md_file):
                continue
            try:
                rel_path = str(md_file.relative_to(self.docs_dir))
                self._docs_cache[rel_path] = md_file.read_text()
            except Exception:
                pass

        return self._docs_cache

    def _expand_topic(self, topic: str) -> list[str]:
        """Expand topic to related keywords."""
        topic_lower = topic.lower()
        keywords = [topic_lower]

        # Add aliases if topic matches
        for alias_key, alias_keywords in self.TOPIC_ALIASES.items():
            if topic_lower in alias_key or alias_key in topic_lower:
                keywords.extend(alias_keywords)
            elif any(kw in topic_lower for kw in alias_keywords):
                keywords.extend(alias_keywords)

        return list(set(keywords))

    def _score_doc(self, content: str, keywords: list[str]) -> float:
        """Score a document based on keyword relevance."""
        content_lower = content.lower()
        score = 0.0

        for kw in keywords:
            # Count occurrences
            count = content_lower.count(kw)
            if count > 0:
                # Diminishing returns for high counts
                score += min(count, 10) * 0.1

            # Bonus for keyword in headers
            if f"# {kw}" in content_lower or f"## {kw}" in content_lower:
                score += 0.5

        return score

    def _extract_relevant_sections(self, content: str, keywords: list[str], max_sections: int = 3) -> list[str]:
        """Extract the most relevant sections from a document."""
        sections = []

        # Split by headers
        lines = content.split('\n')
        current_section = []
        current_header = ""

        for line in lines:
            if line.startswith('#'):
                if current_section and current_header:
                    sections.append((current_header, '\n'.join(current_section)))
                current_header = line
                current_section = []
            else:
                current_section.append(line)

        # Don't forget last section
        if current_section and current_header:
            sections.append((current_header, '\n'.join(current_section)))

        # Score sections by keyword relevance
        scored_sections = []
        for header, body in sections:
            combined = f"{header}\n{body}"
            score = self._score_doc(combined, keywords)
            if score > 0:
                scored_sections.append((score, header, body[:500]))  # Truncate long sections

        # Sort by score and return top sections
        scored_sections.sort(reverse=True)
        return [(h, b) for _, h, b in scored_sections[:max_sections]]

    def explain(self, topic: str = None, question: str = None, audience: str = "all") -> dict[str, Any]:
        """
        Get focused explanation of an Empirica topic.

        Uses Qdrant semantic search if available, falls back to keyword matching.

        Args:
            topic: Topic to explain (e.g., "vectors", "sessions")
            question: Question to answer (e.g., "How do I start a session?")
            audience: Target audience ("user", "developer", "ai", "all")

        Returns:
            dict with explanation, sources, and suggestions
        """
        docs = self._load_docs()

        if not docs:
            return {
                "ok": False,
                "error": "No documentation found",
                "explanation": None
            }

        search_text = topic or question or ""
        search_mode = "keyword"  # Track which mode was used
        scored_docs = []

        # Try Qdrant semantic search first
        semantic_results = self._semantic_search(search_text, limit=5)
        if semantic_results:
            search_mode = "semantic"
            # Use semantic results, but need to load content from disk
            for result in semantic_results:
                doc_path = result.get("doc_path")
                if doc_path and doc_path in docs:
                    # Convert Qdrant score (0-1) to our scoring scale
                    score = result.get("score", 0.5) * 2.0  # Scale to comparable range
                    scored_docs.append((score, doc_path, docs[doc_path]))

        # Fall back to keyword search if semantic search unavailable or returned nothing
        if not scored_docs:
            search_mode = "keyword"
            keywords = self._expand_topic(search_text)

            for path, content in docs.items():
                score = self._score_doc(content, keywords)
                if score > 0.1:  # Minimum relevance threshold
                    scored_docs.append((score, path, content))

            scored_docs.sort(reverse=True)

        if not scored_docs:
            return {
                "ok": True,
                "query": search_text,
                "explanation": f"No documentation found for '{search_text}'. Try: vectors, sessions, goals, check, findings, lessons, memory, handoff",
                "sources": [],
                "related_topics": list(self.TOPIC_ALIASES.keys()),
                "notebooklm_suggestion": None
            }

        # Get top docs and extract relevant sections
        top_docs = scored_docs[:5]
        all_sections = []
        sources = []

        # For section extraction, use keywords from topic expansion
        keywords = self._expand_topic(search_text)

        for score, path, content in top_docs:
            sections = self._extract_relevant_sections(content, keywords)
            for header, body in sections:
                all_sections.append(f"**{path}** {header}\n{body.strip()}")
            sources.append({
                "path": path,
                "relevance": round(score, 2)
            })

        # Build explanation
        if question:
            explanation_header = f"**Answering:** {question}\n\n"
        else:
            explanation_header = f"**Topic:** {topic}\n\n"

        explanation = explanation_header + "\n\n---\n\n".join(all_sections[:5])

        # Suggest NotebookLM content for deeper dive
        notebooklm_suggestion = None
        if len(sources) >= 2:
            notebooklm_suggestion = {
                "type": "audio_overview" if len(sources) <= 3 else "slide_deck",
                "topic": topic or question,
                "sources": [s["path"] for s in sources[:5]],
                "format": "deep_dive" if "how" in search_text.lower() else "brief"
            }

        # Find related topics
        related = []
        for alias_key in self.TOPIC_ALIASES.keys():
            if alias_key not in search_text.lower():
                # Check if any source mentions this topic
                for _, path, content in top_docs[:3]:
                    if any(kw in content.lower() for kw in self.TOPIC_ALIASES[alias_key][:2]):
                        related.append(alias_key)
                        break

        return {
            "ok": True,
            "query": search_text,
            "audience": audience,
            "search_mode": search_mode,  # "semantic" if Qdrant used, "keyword" otherwise
            "explanation": explanation,
            "sources": sources,
            "related_topics": related[:5],
            "notebooklm_suggestion": notebooklm_suggestion
        }


def handle_docs_explain(args) -> int:
    """Handle the docs-explain command."""
    try:
        project_root = Path(args.project_root) if hasattr(args, 'project_root') and args.project_root else None
        project_id = getattr(args, 'project_id', None)
        output_format = getattr(args, 'output', 'human')
        topic = getattr(args, 'topic', None)
        question = getattr(args, 'question', None)
        audience = getattr(args, 'audience', 'all')

        if not topic and not question:
            print("Error: Please provide --topic or --question")
            return 1

        agent = DocsExplainAgent(project_root=project_root, project_id=project_id)
        result = agent.explain(topic=topic, question=question, audience=audience)

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            _print_explain_human_output(result)

        return 0

    except Exception as e:
        return handle_cli_error(e, "docs-explain")


def _print_explain_human_output(result: dict):
    """Print human-readable docs-explain output."""
    print("\n" + "=" * 60)
    print("📖 EMPIRICA DOCS EXPLAIN")
    print("=" * 60)

    if not result.get("ok"):
        print(f"\n❌ {result.get('error', 'Unknown error')}")
        return

    print(f"\n🔍 Query: {result.get('query', 'N/A')}")

    # Show search mode (semantic vs keyword)
    search_mode = result.get("search_mode", "keyword")
    mode_icon = "🧠" if search_mode == "semantic" else "🔤"
    print(f"{mode_icon} Search: {search_mode}")

    if result.get("audience") != "all":
        print(f"👤 Audience: {result['audience']}")

    print("\n" + "-" * 60)

    # Main explanation
    explanation = result.get("explanation", "No explanation available")
    # Truncate for terminal display
    if len(explanation) > 2000:
        explanation = explanation[:2000] + "\n\n... (truncated, use --output json for full content)"
    print(explanation)

    print("\n" + "-" * 60)

    # Sources
    sources = result.get("sources", [])
    if sources:
        print("\n📚 Sources:")
        for src in sources[:5]:
            print(f"   • {src['path']} (relevance: {src['relevance']})")

    # Related topics
    related = result.get("related_topics", [])
    if related:
        print(f"\n🔗 Related: {', '.join(related)}")

    # NotebookLM suggestion
    nlm = result.get("notebooklm_suggestion")
    if nlm:
        print(f"\n📽️  For deeper learning, generate NotebookLM {nlm['type']}:")
        print(f"   Topic: {nlm['topic']}")
        print(f"   Format: {nlm['format']}")
        print(f"   Sources: {', '.join(nlm['sources'][:3])}")

    print("\n" + "=" * 60)
