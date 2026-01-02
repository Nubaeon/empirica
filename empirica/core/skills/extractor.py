"""
Skill Extractor - Extract decision frameworks from skill references/ to meta-agent-config.yaml

Converts verbose skill reference files into concise YAML config for epistemic bootstrap cards.
Achieves 80-90% token reduction while preserving decision-relevant knowledge.

Usage:
    from empirica.core.skills.extractor import SkillExtractor, extract_all_skills

    # Single skill
    extractor = SkillExtractor(Path("~/.claude/skills/empirica-framework"))
    domain_data = extractor.extract()

    # All skills
    extract_all_skills(Path("~/.claude/skills"), Path("meta-agent-config.yaml"))
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional


class SkillExtractor:
    """Extract decision frameworks from a skill's references/ directory."""

    def __init__(self, skill_dir: Path):
        self.skill_dir = Path(skill_dir).expanduser()
        self.references_dir = self.skill_dir / "references"
        self.skill_md = self.skill_dir / "SKILL.md"

    def extract(self) -> Dict[str, Any]:
        """Extract decision frameworks from all reference files."""
        domain = self.skill_dir.name

        domain_knowledge = {
            'decision_frameworks': {},
            'anti_patterns': [],
            'cost_models': {},
            'key_commands': [],
            'references': {},
            'metadata': {}
        }

        # Extract metadata from SKILL.md frontmatter
        if self.skill_md.exists():
            metadata = self._extract_metadata(self.skill_md.read_text())
            domain_knowledge['metadata'] = metadata

        # Process all markdown files in references/
        if self.references_dir.exists():
            for ref_file in self.references_dir.glob("*.md"):
                content = ref_file.read_text()
                self._extract_from_content(content, domain_knowledge)

        # Also extract from SKILL.md body if references/ is sparse
        if self.skill_md.exists():
            content = self.skill_md.read_text()
            self._extract_from_content(content, domain_knowledge)

        # Clean up empty entries
        domain_knowledge = {k: v for k, v in domain_knowledge.items() if v}

        return {domain: domain_knowledge}

    def _extract_metadata(self, content: str) -> Dict[str, str]:
        """Extract YAML frontmatter metadata."""
        metadata = {}

        # Match YAML frontmatter
        match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if match:
            try:
                frontmatter = yaml.safe_load(match.group(1))
                if isinstance(frontmatter, dict):
                    metadata = {
                        'name': frontmatter.get('name', ''),
                        'description': frontmatter.get('description', ''),
                        'version': frontmatter.get('version', '')
                    }
            except yaml.YAMLError:
                pass

        return {k: v for k, v in metadata.items() if v}

    def _extract_from_content(self, content: str, domain_knowledge: Dict):
        """Extract all knowledge types from markdown content."""

        # Extract decision frameworks
        for pattern in [r"## When to [Uu]se", r"## Use [Ww]hen", r"## Prerequisites"]:
            items = self._extract_section(content, pattern)
            if items:
                domain_knowledge['decision_frameworks']['when_to_use'] = items
                break

        for pattern in [r"## When NOT to [Uu]se", r"## Don'?t [Uu]se", r"## Avoid"]:
            items = self._extract_section(content, pattern)
            if items:
                domain_knowledge['decision_frameworks']['when_not_to_use'] = items
                break

        # Extract DO/DON'T patterns
        do_items = self._extract_section(content, r"##+ DO\s*$")
        if do_items:
            domain_knowledge['decision_frameworks']['do'] = do_items

        dont_items = self._extract_section(content, r"##+ DON'?T")
        if dont_items:
            domain_knowledge['decision_frameworks']['dont'] = dont_items

        # Extract anti-patterns
        anti_patterns = self._extract_anti_patterns(content)
        domain_knowledge['anti_patterns'].extend(anti_patterns)

        # Extract cost models
        costs = self._extract_costs(content)
        domain_knowledge['cost_models'].update(costs)

        # Extract key commands
        commands = self._extract_commands(content)
        domain_knowledge['key_commands'].extend(commands)

        # Extract doc references
        refs = self._extract_references(content)
        domain_knowledge['references'].update(refs)

    def _extract_section(self, content: str, header_pattern: str) -> List[str]:
        """Extract bullet points from a section."""
        match = re.search(f"({header_pattern})(.*?)(?=##|$)", content, re.DOTALL | re.MULTILINE)
        if not match:
            return []

        section = match.group(2)

        # Extract bullet points
        bullets = re.findall(r"^[-*✅❌]\s+(.+)$", section, re.MULTILINE)
        return [b.strip() for b in bullets if b.strip()]

    def _extract_anti_patterns(self, content: str) -> List[Dict]:
        """Extract anti-patterns from Common Mistakes, Anti-patterns sections."""
        patterns = []

        for header in [r"## Common [Mm]istakes?", r"## Anti-[Pp]atterns?",
                       r"## [Pp]itfalls?", r"## Calibration Anti-[Pp]atterns"]:
            match = re.search(f"{header}(.*?)(?=##|$)", content, re.DOTALL)
            if not match:
                continue

            section = match.group(1)

            for line in section.split('\n'):
                line = line.strip()
                if not line or not line.startswith(('-', '*', '•')):
                    continue

                # Remove bullet
                line = re.sub(r"^[-*•]\s+", "", line)

                # Strip markdown formatting (bold, italic)
                line = re.sub(r'\*\*|\*|__|_', '', line)

                # Try to parse "description: reason"
                if ':' in line and not line.startswith('http'):
                    parts = line.split(':', 1)
                    desc = parts[0].strip()
                    detail = parts[1].strip()

                    pattern = {
                        'id': self._make_id(desc),
                        'description': desc
                    }

                    # Check if detail contains cost (kb, ms, etc)
                    if re.search(r'\d+\s*(kb|ms|MB|%|tokens?)', detail, re.IGNORECASE):
                        pattern['cost'] = detail
                    else:
                        pattern['reason'] = detail

                    patterns.append(pattern)
                elif line:
                    # Simple pattern without cost
                    patterns.append({
                        'id': self._make_id(line[:30]),
                        'description': line
                    })

        return patterns

    def _extract_costs(self, content: str) -> Dict[str, str]:
        """Extract performance/token costs."""
        costs = {}

        for header in [r"## Performance", r"## Cost", r"## Token [Ee]conomics",
                       r"## Bundle [Ss]ize", r"## Overhead"]:
            match = re.search(f"{header}(.*?)(?=##|$)", content, re.DOTALL)
            if not match:
                continue

            section = match.group(1)

            for line in section.split('\n'):
                # Match "X: Nkb" or "X: N tokens"
                cost_match = re.search(r"(.+?):\s*(\d+[-\d]*\s*(?:kb|tokens?|ms|MB|%))",
                                       line, re.IGNORECASE)
                if cost_match:
                    key = self._make_id(cost_match.group(1))
                    costs[key] = cost_match.group(2).strip()

                # Match reduction percentages
                reduction_match = re.search(r"[Rr]eduction[:\s]+(\d+[-\d]*%)", line)
                if reduction_match:
                    costs['reduction'] = reduction_match.group(1)

                # Match decision rules
                rule_match = re.search(r"[Rr]ule:\s*(.+)$", line)
                if rule_match:
                    costs['decision_rule'] = rule_match.group(1).strip()

        return costs

    def _extract_commands(self, content: str) -> List[Dict[str, str]]:
        """Extract key CLI commands."""
        commands = []

        # Find command blocks
        for header in [r"## Key Commands", r"## Commands", r"## Quick Start",
                       r"## Quick Reference"]:
            match = re.search(f"{header}(.*?)(?=##|$)", content, re.DOTALL)
            if not match:
                continue

            section = match.group(1)

            # Extract commands from code blocks
            code_blocks = re.findall(r"```(?:bash|shell)?\s*\n(.*?)```", section, re.DOTALL)
            for block in code_blocks:
                for line in block.split('\n'):
                    line = line.strip()
                    # Skip comments
                    if line.startswith('#') or not line:
                        continue
                    # Extract empirica commands
                    if line.startswith('empirica '):
                        cmd_parts = line.split()
                        if len(cmd_parts) >= 2:
                            commands.append({
                                'command': cmd_parts[1],
                                'full': line[:100]  # Truncate long commands
                            })

        # Deduplicate by command name
        seen = set()
        unique_commands = []
        for cmd in commands:
            if cmd['command'] not in seen:
                seen.add(cmd['command'])
                unique_commands.append(cmd)

        return unique_commands[:10]  # Limit to 10 commands

    def _extract_references(self, content: str) -> Dict[str, Any]:
        """Extract doc references."""
        refs = {}

        # Find references section
        match = re.search(r"## (?:More )?[Rr]eferences?(.*?)(?=##|$)", content, re.DOTALL)
        if match:
            section = match.group(1)

            # Extract markdown links
            links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", section)
            if links:
                refs['links'] = [{'title': t, 'url': u} for t, u in links[:5]]

        # Also look for inline references
        doc_matches = re.findall(r"[Ss]ee \[([^\]]+)\]\(([^)]+)\)", content)
        if doc_matches and 'links' not in refs:
            refs['links'] = [{'title': t, 'url': u} for t, u in doc_matches[:5]]

        return refs

    def _make_id(self, text: str) -> str:
        """Convert text to ID (lowercase, hyphens)."""
        # Remove special characters
        text = re.sub(r"[^\w\s-]", "", text.lower().strip())
        # Replace spaces with hyphens
        text = re.sub(r"\s+", "-", text)
        return text[:40]  # Limit length


def extract_all_skills(skills_dir: Path, output_file: Path,
                       verbose: bool = False) -> Dict[str, Any]:
    """
    Extract all skills to meta-agent-config.yaml.

    Args:
        skills_dir: Directory containing skill subdirectories
        output_file: Output YAML file path
        verbose: Print progress

    Returns:
        The generated config dict
    """
    skills_dir = Path(skills_dir).expanduser()
    output_file = Path(output_file)

    config = {
        'meta_agent': {
            'version': '1.0',
            'epistemic_thresholds': {
                'bootstrap_trigger': [
                    {'condition': 'context < 0.5', 'action': 'load_full_context'},
                    {'condition': 'uncertainty > 0.6', 'action': 'load_domain_knowledge'}
                ]
            },
            'domain_knowledge': {}
        }
    }

    # Process each skill
    processed = 0
    for skill_path in skills_dir.iterdir():
        if not skill_path.is_dir():
            continue

        # Skip hidden directories
        if skill_path.name.startswith('.'):
            continue

        # Check if it has SKILL.md or references/
        has_skill_md = (skill_path / "SKILL.md").exists()
        has_references = (skill_path / "references").exists()

        if not (has_skill_md or has_references):
            continue

        if verbose:
            print(f"Extracting {skill_path.name}...")

        try:
            extractor = SkillExtractor(skill_path)
            domain_data = extractor.extract()
            config['meta_agent']['domain_knowledge'].update(domain_data)
            processed += 1
        except Exception as e:
            if verbose:
                print(f"  Error: {e}")

    # Write output
    with open(output_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False,
                  allow_unicode=True, width=120)

    if verbose:
        print(f"\nExtracted {processed} skills to {output_file}")

        # Calculate reduction
        original_size = sum(
            f.stat().st_size
            for skill in skills_dir.iterdir()
            if skill.is_dir()
            for f in skill.rglob("*.md")
        )
        output_size = output_file.stat().st_size
        if original_size > 0:
            reduction = (1 - output_size / original_size) * 100
            print(f"Original: {original_size:,} bytes")
            print(f"Extracted: {output_size:,} bytes")
            print(f"Reduction: {reduction:.1f}%")

    return config


def extract_single_skill(skill_path: Path, verbose: bool = False) -> Dict[str, Any]:
    """
    Extract a single skill to dict format.

    Args:
        skill_path: Path to skill directory
        verbose: Print progress

    Returns:
        Domain knowledge dict for this skill
    """
    skill_path = Path(skill_path).expanduser()

    if verbose:
        print(f"Extracting {skill_path.name}...")

    extractor = SkillExtractor(skill_path)
    return extractor.extract()
