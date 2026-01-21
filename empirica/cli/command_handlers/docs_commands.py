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
from datetime import datetime, timedelta, timezone
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
        """Calculate documentation coverage ratio (0.0 to 1.0)."""
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
        """Convert coverage data to dictionary representation."""
        return {
            "name": self.name,
            "total": self.total,
            "documented": self.documented,
            "coverage": round(self.coverage * 100, 1),
            "moon": self.moon,
            "undocumented": self.undocumented[:10]  # Top 10
        }


@dataclass
class StalenessItem:
    """A single staleness detection result."""
    doc_path: str
    section: str
    severity: str  # "high", "medium", "low"
    audience: str  # "ai", "developer", "user"
    memory_type: str  # "finding", "dead_end", "mistake", "unknown"
    memory_text: str
    memory_age_days: int
    similarity: float
    suggestion: str

    def to_dict(self) -> dict[str, Any]:
        """Convert staleness item to dictionary."""
        return {
            "doc_path": self.doc_path,
            "section": self.section,
            "severity": self.severity,
            "audience": self.audience,
            "memory_type": self.memory_type,
            "memory_text": self.memory_text[:200],  # Truncate for display
            "memory_age_days": self.memory_age_days,
            "similarity": round(self.similarity, 3),
            "suggestion": self.suggestion
        }


class EpistemicDocsAgent:
    """
    Epistemic Documentation Assessment Agent.

    Measures documentation coverage against actual codebase features.
    Returns honest epistemic assessment of what's documented vs hidden.
    """

    def __init__(self, project_root: Path | None = None, verbose: bool = False):
        """Initialize docs agent with optional project root and verbosity setting."""
        self.root = project_root or self._detect_project_root()
        self.verbose = verbose
        self.categories: list[FeatureCoverage] = []

    @staticmethod
    def _detect_project_root() -> Path:
        """Auto-detect project root by walking up to find markers."""
        cwd = Path.cwd()

        # Walk up the directory tree looking for project markers
        for parent in [cwd] + list(cwd.parents):
            # Check for pyproject.toml (Python project root)
            if (parent / "pyproject.toml").exists():
                return parent
            # Check for empirica package directory
            if (parent / "empirica" / "__init__.py").exists():
                return parent
            # Check for .git directory (repo root)
            if (parent / ".git").exists():
                return parent

        # Fallback to cwd if no markers found
        return cwd

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

    def check_docstrings(self) -> dict[str, Any]:
        """
        Check Python code for missing docstrings using AST.

        Returns dict with:
        - modules_missing: List of modules without module docstrings
        - classes_missing: List of classes without docstrings
        - functions_missing: List of public functions without docstrings
        - coverage: Overall docstring coverage percentage
        """
        modules_missing: list[str] = []
        classes_missing: list[str] = []
        functions_missing: list[str] = []
        total_items = 0
        documented_items = 0

        # Scan empirica package
        package_dir = self.root / "empirica"
        if not package_dir.exists():
            return {
                "modules_missing": modules_missing,
                "classes_missing": classes_missing,
                "functions_missing": functions_missing,
                "total_items": total_items,
                "documented_items": documented_items,
                "coverage": 0.0
            }

        for py_file in package_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                rel_path = py_file.relative_to(self.root)

                # Check module docstring
                total_items += 1
                if ast.get_docstring(tree):
                    documented_items += 1
                else:
                    modules_missing.append(str(rel_path))

                # Check classes and functions
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        total_items += 1
                        if ast.get_docstring(node):
                            documented_items += 1
                        else:
                            classes_missing.append(f"{rel_path}:{node.name}")

                    elif isinstance(node, ast.FunctionDef):
                        # Skip private/dunder methods
                        if node.name.startswith("_") and not node.name.startswith("__"):
                            continue
                        # Skip dunder except __init__
                        if node.name.startswith("__") and node.name != "__init__":
                            continue

                        total_items += 1
                        if ast.get_docstring(node):
                            documented_items += 1
                        else:
                            functions_missing.append(f"{rel_path}:{node.name}")

            except (SyntaxError, UnicodeDecodeError):
                # Skip files that can't be parsed
                continue

        # Calculate coverage
        coverage = round(documented_items / total_items * 100, 1) if total_items > 0 else 0.0

        return {
            "modules_missing": modules_missing,
            "classes_missing": classes_missing,
            "functions_missing": functions_missing,
            "total_items": total_items,
            "documented_items": documented_items,
            "coverage": coverage
        }

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

    def run_turtle_assessment(self, max_rounds: int = 3) -> dict[str, Any]:
        """
        Epistemic recursive assessment - turtles all the way down.

        Iterates between code and docs to surface gaps:
        1. Run standard assessment (code → docs comparison)
        2. Check docstrings (code self-documentation)
        3. Compare docstrings to external docs (consistency)
        4. Generate epistemic vectors for convergence tracking

        Args:
            max_rounds: Maximum iteration rounds (default 3)

        Returns:
            Combined assessment with convergence tracking
        """
        rounds: list[dict[str, Any]] = []
        prev_uncertainty = 1.0

        for round_num in range(1, max_rounds + 1):
            # Layer 1: Standard docs assessment
            docs_result = self.run_assessment()

            # Layer 2: Docstring assessment
            docstring_result = self.check_docstrings()

            # Layer 3: Cross-reference - find items documented externally but missing docstrings
            docs_content = self._load_all_docs_content()
            cross_gaps = []
            for func in docstring_result["functions_missing"][:20]:  # Top 20
                # Check if it's documented externally
                func_name = func.split(":")[-1] if ":" in func else func
                if self._check_if_documented(func_name, docs_content):
                    cross_gaps.append(f"{func} (in docs, missing docstring)")

            # Calculate combined epistemic state
            docs_coverage = docs_result["overall"]["coverage"] / 100
            docstring_coverage = docstring_result["coverage"] / 100
            combined_coverage = (docs_coverage + docstring_coverage) / 2

            # Epistemic vectors for this round
            know = combined_coverage
            uncertainty = 1 - combined_coverage
            delta = prev_uncertainty - uncertainty

            round_data = {
                "round": round_num,
                "docs_coverage": docs_result["overall"]["coverage"],
                "docstring_coverage": docstring_result["coverage"],
                "combined_coverage": round(combined_coverage * 100, 1),
                "cross_gaps": cross_gaps[:5],
                "vectors": {
                    "know": round(know, 2),
                    "uncertainty": round(uncertainty, 2),
                    "delta": round(delta, 3)
                },
                "convergence": abs(delta) < 0.01  # Converged if delta < 1%
            }
            rounds.append(round_data)

            # Check convergence
            if round_data["convergence"]:
                break

            prev_uncertainty = uncertainty

        # Final summary
        final_round = rounds[-1]
        return {
            "turtle_mode": True,
            "total_rounds": len(rounds),
            "converged": final_round["convergence"],
            "final_state": {
                "docs_coverage": final_round["docs_coverage"],
                "docstring_coverage": final_round["docstring_coverage"],
                "combined": final_round["combined_coverage"],
                "moon": self._score_to_moon(final_round["combined_coverage"] / 100)
            },
            "epistemic_vectors": final_round["vectors"],
            "cross_gaps": final_round["cross_gaps"],
            "rounds": rounds,
            "recommendations": self._generate_recommendations(),
            "docstring_gaps": {
                "modules": docstring_result["modules_missing"][:10],
                "classes": docstring_result["classes_missing"][:10],
                "functions": docstring_result["functions_missing"][:10]
            }
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

    def _classify_audience(self, doc_path: str) -> str:
        """
        Classify doc audience based on path.

        AI-first model: Everything is AI-facing by default.
        Only explicitly human-prefixed paths are for humans.
        """
        path_str = str(doc_path).lower()
        if "human/end-users" in path_str or "human/end_users" in path_str:
            return "user"
        elif "human/developers" in path_str or "human/developer" in path_str:
            return "developer"
        else:
            return "ai"  # Default - AI is primary consumer

    def _get_sensitivity_threshold(self, audience: str, base_threshold: float) -> float:
        """
        Get staleness sensitivity threshold by audience.

        AI docs need highest sensitivity (any drift matters).
        """
        if audience == "ai":
            return base_threshold - 0.05  # More sensitive
        elif audience == "developer":
            return base_threshold
        else:  # user
            return base_threshold + 0.05  # Less sensitive

    def check_staleness(
        self,
        threshold: float = 0.7,  # Kept for API compatibility, not used
        lookback_days: int = 30
    ) -> dict[str, Any]:
        """
        Detect stale docs using deterministic heuristics (no AI/semantic search).

        Fast pre-filter that identifies:
        1. Orphaned references - Docs mentioning CLI commands or classes that no longer exist
        2. Undocumented code - New CLI commands or classes with no doc coverage
        3. Activity gaps - Docs in directories with recent code changes but stale doc timestamps
        4. Explicit mentions - Dead ends/findings that literally reference doc paths

        For deep semantic analysis, use agent-spawn with an LLM.

        Args:
            threshold: Unused (kept for API compatibility)
            lookback_days: How far back to check git activity (default 30)

        Returns:
            Dict with staleness report organized by issue type
        """
        docs_dir = self.root / "docs"
        if not docs_dir.exists():
            return {
                "ok": False,
                "error": f"No docs directory found at {docs_dir}",
                "issues": []
            }

        # Gather code inventory
        cli_commands = set(self._extract_cli_commands())
        core_modules, _ = self._extract_core_modules()
        core_classes = set(core_modules)

        # Gather doc inventory
        docs_content = self._load_all_docs_content()
        doc_files = list(docs_dir.rglob("*.md"))
        doc_files = [f for f in doc_files if "_archive" not in str(f)]

        issues: list[dict[str, Any]] = []

        # === Check 1: Undocumented CLI commands ===
        for cmd in cli_commands:
            if not self._check_if_documented(cmd, docs_content):
                issues.append({
                    "type": "undocumented_code",
                    "severity": "high",
                    "item": cmd,
                    "category": "CLI command",
                    "suggestion": f"Add documentation for 'empirica {cmd}' command"
                })

        # === Check 2: Undocumented core classes ===
        for cls in core_classes:
            if not self._check_if_documented(cls, docs_content):
                issues.append({
                    "type": "undocumented_code",
                    "severity": "medium",
                    "item": cls,
                    "category": "Core class",
                    "suggestion": f"Add documentation for {cls} class"
                })

        # === Check 3: Orphaned doc references ===
        # Check if docs reference CLI commands that no longer exist
        for doc_file in doc_files:
            try:
                content = doc_file.read_text()
                rel_path = str(doc_file.relative_to(docs_dir))

                # Look for empirica command patterns in docs
                cmd_pattern = r'empirica\s+([a-z]+-[a-z-]+)'  # Require hyphen to be a command
                doc_cmds = set(re.findall(cmd_pattern, content))

                for doc_cmd in doc_cmds:
                    # Skip common words and invalid patterns
                    if doc_cmd in {'the', 'a', 'an', 'to', 'is', 'and', 'or', 'empirica'}:
                        continue
                    if not re.match(r'^[a-z]+-[a-z-]+$', doc_cmd):  # Must have at least one hyphen
                        continue
                    if doc_cmd not in cli_commands and len(doc_cmd) > 5:
                        issues.append({
                            "type": "orphaned_reference",
                            "severity": "high",
                            "doc_path": rel_path,
                            "item": f"empirica {doc_cmd}",
                            "category": "Removed CLI command",
                            "suggestion": f"Remove or update reference to 'empirica {doc_cmd}' - command no longer exists"
                        })
            except Exception:
                continue

        # === Check 4: Git activity gap ===
        activity_gaps = self._check_git_activity_gaps(docs_dir, lookback_days)
        for gap in activity_gaps:
            issues.append({
                "type": "activity_gap",
                "severity": "medium",
                "doc_path": gap["doc_path"],
                "item": f"{gap['code_commits']} code commits, doc unchanged",
                "category": "Stale doc",
                "suggestion": f"Doc may be stale - {gap['code_commits']} commits to related code in last {lookback_days} days"
            })

        # === Check 5: Explicit doc references in memory ===
        explicit_refs = self._check_explicit_doc_references(docs_dir)
        for ref in explicit_refs:
            issues.append({
                "type": "explicit_reference",
                "severity": "high",
                "doc_path": ref["doc_path"],
                "item": ref["memory_text"][:100],
                "category": ref["memory_type"],
                "suggestion": ref["suggestion"]
            })

        # Categorize by severity
        high = [i for i in issues if i["severity"] == "high"]
        medium = [i for i in issues if i["severity"] == "medium"]
        low = [i for i in issues if i["severity"] == "low"]

        # Assessment
        if len(high) >= 10:
            assessment = "Critical documentation debt"
        elif len(high) >= 5:
            assessment = "Significant gaps detected"
        elif len(high) > 0 or len(medium) >= 5:
            assessment = "Some docs need attention"
        else:
            assessment = "Documentation appears current"

        return {
            "ok": True,
            "summary": {
                "total_issues": len(issues),
                "high_severity": len(high),
                "medium_severity": len(medium),
                "low_severity": len(low),
                "assessment": assessment,
                "cli_commands_checked": len(cli_commands),
                "core_classes_checked": len(core_classes),
                "docs_checked": len(doc_files)
            },
            "by_type": {
                "undocumented_code": [i for i in issues if i["type"] == "undocumented_code"],
                "orphaned_reference": [i for i in issues if i["type"] == "orphaned_reference"],
                "activity_gap": [i for i in issues if i["type"] == "activity_gap"],
                "explicit_reference": [i for i in issues if i["type"] == "explicit_reference"]
            },
            "by_severity": {
                "high": high[:15],
                "medium": medium[:15],
                "low": low[:10]
            },
            "note": "For deep semantic analysis, use: empirica agent-spawn --task 'Analyze <doc> for staleness'"
        }

    def _check_git_activity_gaps(self, docs_dir: Path, lookback_days: int) -> list[dict]:
        """Check for docs that haven't been updated despite related code changes."""
        gaps = []
        try:
            import subprocess

            # Get list of files changed in last N days
            result = subprocess.run(
                ["git", "log", f"--since={lookback_days} days ago", "--name-only", "--pretty=format:"],
                capture_output=True, text=True, cwd=self.root
            )
            if result.returncode != 0:
                return gaps

            changed_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]

            # Group changes by directory
            from collections import Counter
            dir_changes = Counter()
            for f in changed_files:
                if f.startswith("empirica/"):
                    # Map code path to potential doc area
                    parts = f.split("/")
                    if len(parts) >= 2:
                        area = parts[1]  # e.g., "core", "cli", "data"
                        dir_changes[area] += 1

            # Check if corresponding docs have been updated
            for area, count in dir_changes.items():
                if count < 5:  # Only flag if significant activity
                    continue

                # Look for docs about this area (exclude archives)
                area_docs = [d for d in docs_dir.rglob(f"*{area}*.md") if "_archive" not in str(d)]
                if not area_docs:
                    continue

                for doc in area_docs:
                    # Check if doc was modified recently
                    doc_result = subprocess.run(
                        ["git", "log", f"--since={lookback_days} days ago", "--oneline", str(doc)],
                        capture_output=True, text=True, cwd=self.root
                    )
                    doc_commits = len([l for l in doc_result.stdout.strip().split('\n') if l])

                    if doc_commits == 0:  # Doc not updated but code was
                        gaps.append({
                            "doc_path": str(doc.relative_to(docs_dir)),
                            "code_area": area,
                            "code_commits": count,
                            "doc_commits": doc_commits
                        })

        except Exception:
            pass

        return gaps[:10]  # Limit results

    def _check_explicit_doc_references(self, docs_dir: Path) -> list[dict]:
        """Check if any memory items explicitly reference doc paths."""
        refs = []

        try:
            from empirica.data.session_database import SessionDatabase
            db = SessionDatabase()

            # Query recent findings and dead_ends that mention doc paths
            cursor = db.conn.cursor()

            # Look for mentions of .md files or "docs/" in memory
            for table, mem_type in [("project_findings", "finding"), ("project_dead_ends", "dead_end")]:
                try:
                    cursor.execute(f"""
                        SELECT text FROM {table}
                        WHERE (text LIKE '%.md%' OR text LIKE '%docs/%' OR text LIKE '%documentation%')
                        AND timestamp > ?
                        ORDER BY timestamp DESC LIMIT 10
                    """, (datetime.now(timezone.utc).timestamp() - 30*24*3600,))

                    for row in cursor.fetchall():
                        text = row[0] if row else ""
                        # Extract mentioned doc paths
                        md_matches = re.findall(r'[\w/-]+\.md', text)
                        for md in md_matches:
                            # Check if this doc exists
                            potential_path = docs_dir / md
                            if potential_path.exists() or (docs_dir / md.split('/')[-1]).exists():
                                refs.append({
                                    "doc_path": md,
                                    "memory_type": mem_type,
                                    "memory_text": text[:200],
                                    "suggestion": f"Memory explicitly mentions {md} - review for updates"
                                })
                except Exception:
                    continue

            db.close()

        except Exception:
            pass

        return refs[:5]  # Limit results

    def _detect_project_id(self) -> str | None:
        """Detect project ID from .empirica config."""
        try:
            import yaml

            # Try reading from .empirica/project.yaml (primary method)
            project_yaml = self.root / ".empirica" / "project.yaml"
            if project_yaml.exists():
                with open(project_yaml, 'r') as f:
                    data = yaml.safe_load(f)
                    if data and data.get("project_id"):
                        return data["project_id"]

            # Fallback: Try .empirica/project.json
            project_json = self.root / ".empirica" / "project.json"
            if project_json.exists():
                data = json.loads(project_json.read_text())
                return data.get("project_id")

        except Exception:
            pass
        return None

    def _extract_doc_sections(self, content: str) -> list[tuple[str, str]]:
        """Extract sections from markdown content by headers."""
        sections = []
        lines = content.split('\n')
        current_header = "Introduction"
        current_content: list[str] = []

        for line in lines:
            if line.startswith('#'):
                # Save previous section
                if current_content:
                    sections.append((current_header, '\n'.join(current_content)))
                # Start new section
                current_header = line.lstrip('#').strip()
                current_content = []
            else:
                current_content.append(line)

        # Don't forget last section
        if current_content:
            sections.append((current_header, '\n'.join(current_content)))

        return sections

    def _calculate_age_days(self, timestamp_val) -> int:
        """Calculate age in days from timestamp (Unix float or ISO string)."""
        if timestamp_val is None:
            return 999  # Treat missing timestamp as very old

        try:
            # Handle Unix timestamp (float)
            if isinstance(timestamp_val, (int, float)):
                ts = datetime.fromtimestamp(timestamp_val, tz=timezone.utc)
            elif isinstance(timestamp_val, str):
                # Handle ISO string formats
                if 'T' in timestamp_val:
                    if timestamp_val.endswith('Z'):
                        timestamp_val = timestamp_val[:-1] + '+00:00'
                    ts = datetime.fromisoformat(timestamp_val)
                else:
                    ts = datetime.fromisoformat(timestamp_val)

                # Make timezone-aware if naive
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            else:
                return 999

            now = datetime.now(timezone.utc)
            delta = now - ts
            return max(0, delta.days)
        except Exception:
            return 999

    def _determine_severity(
        self,
        score: float,
        memory_type: str,
        age_days: int,
        audience: str
    ) -> str:
        """
        Determine staleness severity based on multiple factors.

        High severity:
        - High similarity (>0.8) + recent (<7 days) + AI docs
        - Dead end or mistake with any similarity + AI docs

        Medium severity:
        - Moderate similarity (0.7-0.8) + recent (<14 days)
        - Finding with high similarity on any doc

        Low severity:
        - Lower similarity or older items
        """
        # Dangerous memory types get elevated severity
        dangerous_types = {"dead_end", "mistake"}

        if memory_type in dangerous_types:
            if audience == "ai":
                return "high"  # AI following bad advice is critical
            elif score >= 0.75:
                return "high"
            else:
                return "medium"

        # High similarity + recent = high severity for AI docs
        if score >= 0.8 and age_days <= 7:
            if audience == "ai":
                return "high"
            else:
                return "medium"

        # Moderate signals
        if score >= 0.75 and age_days <= 14:
            return "medium"

        if score >= 0.7:
            return "low"

        return "low"

    def _generate_staleness_suggestion(
        self,
        memory_type: str,
        memory_text: str,
        section_title: str
    ) -> str:
        """Generate actionable suggestion for staleness fix."""
        type_suggestions = {
            "finding": f"Update '{section_title}' to reflect: {memory_text[:100]}...",
            "dead_end": f"Add warning to '{section_title}': this approach may not work",
            "mistake": f"Review '{section_title}': following this led to errors",
            "unknown": f"Clarify '{section_title}': questions remain about this topic"
        }
        return type_suggestions.get(
            memory_type,
            f"Review '{section_title}' for potential updates"
        )

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
        check_docstrings = getattr(args, 'check_docstrings', False)
        turtle_mode = getattr(args, 'turtle', False)
        check_staleness = getattr(args, 'check_staleness', False)
        staleness_threshold = getattr(args, 'staleness_threshold', 0.7)
        staleness_days = getattr(args, 'staleness_days', 30)

        agent = EpistemicDocsAgent(project_root=project_root, verbose=verbose)

        # Staleness detection mode
        if check_staleness:
            result = agent.check_staleness(
                threshold=staleness_threshold,
                lookback_days=staleness_days
            )
            if output_format == 'json':
                print(json.dumps(result, indent=2))
            else:
                _print_staleness_output(result, verbose)
            return 0

        # Turtle mode: recursive epistemic assessment
        if turtle_mode:
            result = agent.run_turtle_assessment()
            if output_format == 'json':
                print(json.dumps(result, indent=2))
            else:
                _print_turtle_output(result, verbose)
            return 0

        # Check docstrings only mode
        if check_docstrings:
            result = agent.check_docstrings()
            if output_format == 'json':
                print(json.dumps(result, indent=2))
            else:
                _print_docstring_output(result, verbose)
            return 0

        # Standard assessment
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


def _print_staleness_output(result: dict, verbose: bool):
    """Print staleness detection output (deterministic heuristics mode)."""
    print("\n" + "=" * 60)
    print("🔍 DOC STALENESS DETECTION (Heuristic Mode)")
    print("=" * 60)

    if not result.get("ok"):
        print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
        return

    summary = result["summary"]

    # Assessment header
    assessment = summary.get("assessment", "Unknown")
    if "Critical" in assessment:
        icon = "🔴"
    elif "Significant" in assessment:
        icon = "🟡"
    elif "Some" in assessment:
        icon = "🟠"
    else:
        icon = "🟢"

    print(f"\n{icon} {assessment}")
    print(f"   CLI commands checked: {summary.get('cli_commands_checked', 0)}")
    print(f"   Core classes checked: {summary.get('core_classes_checked', 0)}")
    print(f"   Docs checked: {summary.get('docs_checked', 0)}")

    # Severity breakdown
    print("\n📊 Issues Found:")
    print(f"   🔴 High:   {summary['high_severity']}")
    print(f"   🟡 Medium: {summary['medium_severity']}")
    print(f"   🟢 Low:    {summary['low_severity']}")

    # By type breakdown
    by_type = result.get("by_type", {})
    undoc = by_type.get("undocumented_code", [])
    orphan = by_type.get("orphaned_reference", [])
    gaps = by_type.get("activity_gap", [])
    explicit = by_type.get("explicit_reference", [])

    print("\n📋 By Type:")
    print(f"   📝 Undocumented code:    {len(undoc)}")
    print(f"   🔗 Orphaned references:  {len(orphan)}")
    print(f"   ⏰ Activity gaps:        {len(gaps)}")
    print(f"   📌 Explicit mentions:    {len(explicit)}")

    # High severity items
    by_severity = result.get("by_severity", {})
    high_items = by_severity.get("high", [])
    if high_items:
        print("\n" + "-" * 60)
        print("🔴 HIGH SEVERITY")
        print("-" * 60)
        for item in high_items[:8]:
            _print_staleness_item_v2(item)

    # Medium severity items
    medium_items = by_severity.get("medium", [])
    if medium_items and (verbose or len(high_items) < 5):
        print("\n" + "-" * 60)
        print("🟡 MEDIUM SEVERITY")
        print("-" * 60)
        limit = 8 if verbose else 5
        for item in medium_items[:limit]:
            _print_staleness_item_v2(item)
        if len(medium_items) > limit:
            print(f"   ... and {len(medium_items) - limit} more")

    # Note about deep analysis
    if result.get("note"):
        print(f"\n💡 {result['note']}")

    print("\n" + "=" * 60)


def _print_staleness_item_v2(item: dict):
    """Print a single staleness item (v2 format for deterministic mode)."""
    issue_type = item.get("type", "unknown")
    severity = item.get("severity", "medium")
    doc_path = item.get("doc_path", "")
    item_name = item.get("item", "")
    category = item.get("category", "")
    suggestion = item.get("suggestion", "")

    # Type icons
    type_icons = {
        "undocumented_code": "📝",
        "orphaned_reference": "🔗",
        "activity_gap": "⏰",
        "explicit_reference": "📌"
    }
    type_icon = type_icons.get(issue_type, "❓")

    if doc_path:
        print(f"\n   {type_icon} {doc_path}")
        print(f"      {category}: {item_name[:60]}")
    else:
        print(f"\n   {type_icon} {category}: {item_name[:60]}")

    print(f"      → {suggestion[:70]}...")


def _print_turtle_output(result: dict, verbose: bool):
    """Print turtle mode (recursive epistemic) output."""
    print("\n" + "=" * 60)
    print("🐢 TURTLE MODE: RECURSIVE EPISTEMIC ASSESSMENT")
    print("=" * 60)

    final = result["final_state"]
    vectors = result["epistemic_vectors"]

    print(f"\n{final['moon']} Combined Coverage: {final['combined']}%")
    print(f"   External docs: {final['docs_coverage']}%")
    print(f"   Code docstrings: {final['docstring_coverage']}%")

    print(f"\n📊 Epistemic Vectors:")
    print(f"   know: {vectors['know']:.2f}")
    print(f"   uncertainty: {vectors['uncertainty']:.2f}")
    print(f"   delta: {vectors['delta']:+.3f}")

    print(f"\n🔄 Convergence: {'✅ Converged' if result['converged'] else '⚠️ Not converged'}")
    print(f"   Rounds: {result['total_rounds']}")

    if result.get("cross_gaps"):
        print(f"\n⚠️ Cross-Reference Gaps (in docs but missing docstring):")
        for gap in result["cross_gaps"][:5]:
            print(f"   • {gap}")

    if verbose and result.get("docstring_gaps"):
        gaps = result["docstring_gaps"]
        if gaps.get("modules"):
            print(f"\n📄 Modules missing docstrings:")
            for m in gaps["modules"][:5]:
                print(f"   • {m}")
        if gaps.get("classes"):
            print(f"\n🏛️ Classes missing docstrings:")
            for c in gaps["classes"][:5]:
                print(f"   • {c}")
        if gaps.get("functions"):
            print(f"\n⚙️ Functions missing docstrings:")
            for f in gaps["functions"][:5]:
                print(f"   • {f}")

    if result.get("recommendations"):
        print(f"\n💡 Recommendations:")
        for rec in result["recommendations"][:3]:
            print(f"   • {rec}")

    print("\n" + "=" * 60)


def _print_docstring_output(result: dict, verbose: bool):
    """Print docstring check output."""
    print("\n" + "=" * 60)
    print("📝 DOCSTRING COVERAGE CHECK")
    print("=" * 60)

    coverage = result["coverage"]
    total = result["total_items"]
    documented = result["documented_items"]

    # Moon phase
    if coverage >= 85:
        moon = "🌕"
    elif coverage >= 70:
        moon = "🌔"
    elif coverage >= 50:
        moon = "🌓"
    elif coverage >= 30:
        moon = "🌒"
    else:
        moon = "🌑"

    print(f"\n{moon} Docstring Coverage: {coverage}%")
    print(f"   Items: {documented}/{total} documented")

    if result["modules_missing"]:
        print(f"\n📄 Modules missing docstrings ({len(result['modules_missing'])}):")
        limit = 10 if verbose else 5
        for m in result["modules_missing"][:limit]:
            print(f"   • {m}")
        if len(result["modules_missing"]) > limit:
            print(f"   ... and {len(result['modules_missing']) - limit} more")

    if result["classes_missing"]:
        print(f"\n🏛️ Classes missing docstrings ({len(result['classes_missing'])}):")
        limit = 10 if verbose else 5
        for c in result["classes_missing"][:limit]:
            print(f"   • {c}")
        if len(result["classes_missing"]) > limit:
            print(f"   ... and {len(result['classes_missing']) - limit} more")

    if result["functions_missing"]:
        print(f"\n⚙️ Functions missing docstrings ({len(result['functions_missing'])}):")
        limit = 10 if verbose else 5
        for f in result["functions_missing"][:limit]:
            print(f"   • {f}")
        if len(result["functions_missing"]) > limit:
            print(f"   ... and {len(result['functions_missing']) - limit} more")

    print("\n" + "=" * 60)


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
        """Initialize explain agent with optional project root and project ID."""
        self.root = project_root or EpistemicDocsAgent._detect_project_root()
        self.docs_dir = self.root / "docs"
        self._docs_cache: dict[str, str] = {}
        self.project_id = project_id or self._detect_project_id()
        self._qdrant_available: bool | None = None

        # Fallback: if docs_dir doesn't exist, try to find Empirica's package docs
        # This enables docs-explain to work from any directory, not just within the project
        if not self.docs_dir.exists():
            self.docs_dir = self._find_empirica_package_docs()

    def _find_empirica_package_docs(self) -> Path:
        """Find Empirica's installed package docs directory as fallback."""
        try:
            # Method 1: Use the package's __file__ location
            import empirica
            package_dir = Path(empirica.__file__).parent.parent
            docs_candidate = package_dir / "docs"
            if docs_candidate.exists():
                return docs_candidate

            # Method 2: Check common installation patterns
            # For editable installs, the package is often in a 'empirica' subdir
            if (package_dir / "empirica" / "__init__.py").exists():
                docs_candidate = package_dir / "docs"
                if docs_candidate.exists():
                    return docs_candidate
        except Exception:
            pass

        # Return original (non-existent) path if fallback fails
        return self.root / "docs"

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
