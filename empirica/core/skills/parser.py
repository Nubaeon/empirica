"""
Skill Parser - normalize markdown skill cards into YAML runtime objects.
Very simple heuristic parser for headings/lists.
"""
from __future__ import annotations
import os
import re
from typing import Dict, List


def parse_markdown_to_skill(md_text: str, name: str, tags: List[str] | None = None) -> Dict:
    """Parse markdown text into a skill dictionary."""
    # Heuristic: extract sections by headings
    sections = {}
    current = "body"
    sections[current] = []
    for line in md_text.splitlines():
        m = re.match(r"^#{1,6}\s+(.*)$", line.strip())
        if m:
            current = m.group(1).strip().lower()
            sections.setdefault(current, [])
        else:
            sections[current].append(line)

    def extract_list(sec_key: str) -> List[str]:
        """Extract list items from a section."""
        lines = sections.get(sec_key, [])
        items: List[str] = []
        for ln in lines:
            s = ln.strip()
            if s.startswith(('- ', '* ', '• ')):
                items.append(s[2:].strip())
        return items

    def extract_paragraph(sec_key: str) -> str:
        """Extract paragraph text from a section."""
        return "\n".join([ln for ln in sections.get(sec_key, []) if ln.strip()])

    skill = {
        'id': re.sub(r"[^a-z0-9]+", "-", name.lower()).strip('-'),
        'title': name,
        'tags': tags or [],
        'preconditions': extract_list('preconditions') or extract_list('requirements'),
        'steps': extract_list('steps') or extract_list('procedure'),
        'gotchas': extract_list('gotchas') or extract_list('pitfalls') or extract_list('notes'),
        'references': extract_list('references') or extract_list('links'),
        'summary': extract_paragraph('body'),
    }
    return skill
