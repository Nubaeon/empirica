"""Context markdown formatter for AI prompt injection"""
from typing import Dict


def generate_context_markdown(breadcrumbs: Dict) -> str:
    """
    Generate markdown-formatted context for injection into AI prompts.

    Args:
        breadcrumbs: Dictionary from bootstrap_project_breadcrumbs()

    Returns:
        Markdown string formatted for context injection
    """
    lines = []

    # Project header
    project = breadcrumbs.get('project', {})
    lines.append(f"# Project: {project.get('name', 'Unknown')}")
    lines.append(f"> {project.get('description', 'No description')}")
    lines.append(f"> Total sessions: {project.get('total_sessions', 0)}")
    lines.append("")

    # Last activity
    last = breadcrumbs.get('last_activity', {})
    if last.get('summary'):
        lines.append("## Last Activity")
        lines.append(f"**Summary:** {last['summary']}")
        lines.append(f"**Next focus:** {last.get('next_focus', 'Continue project work')}")
        lines.append("")

    # Key findings
    findings = breadcrumbs.get('findings', [])
    if findings:
        lines.append("## Key Findings")
        for f in findings:
            lines.append(f"- {f}")
        lines.append("")

    # Remaining unknowns
    unknowns = breadcrumbs.get('unknowns', [])
    unresolved = [u for u in unknowns if not u.get('is_resolved', False)]
    if unresolved:
        lines.append("## Remaining Unknowns")
        for u in unresolved:
            lines.append(f"- {u['unknown']}")
        lines.append("")

    # Dead ends to avoid
    dead_ends = breadcrumbs.get('dead_ends', [])
    if dead_ends:
        lines.append("## Dead Ends (Avoid These)")
        for d in dead_ends:
            lines.append(f"- **{d['approach']}** - {d['why_failed']}")
        lines.append("")

    # Mistakes to avoid
    mistakes = breadcrumbs.get('mistakes_to_avoid', [])
    if mistakes:
        lines.append("## Mistakes to Avoid")
        for m in mistakes:
            lines.append(f"- **{m['mistake']}** → {m['prevention']} (cost: {m.get('cost', 'unknown')})")
        lines.append("")

    # Incomplete work
    incomplete = breadcrumbs.get('incomplete_work', [])
    if incomplete:
        lines.append("## Incomplete Work")
        for item in incomplete:
            goal = item.get('goal') or item.get('objective', 'Unknown goal')
            progress = item.get('progress', 'unknown')
            lines.append(f"- {goal} ({progress})")
        lines.append("")

    # Full skills (matched to task) - filter empty skills
    full_skills = breadcrumbs.get('full_skills', [])
    # Only include skills with actual content (non-empty summary, steps, or gotchas)
    non_empty_skills = [
        s for s in full_skills
        if s.get('summary') or s.get('steps') or s.get('gotchas')
    ]
    if non_empty_skills:
        lines.append("## Relevant Skills")
        for skill in non_empty_skills:
            lines.append(f"### {skill.get('title') or skill.get('id', 'Unknown Skill')}")
            lines.append(f"**Tags:** {', '.join(skill.get('tags', []))}")

            if skill.get('summary'):
                lines.append(f"**Summary:** {skill['summary']}")

            if skill.get('steps'):
                lines.append("**Steps:**")
                for step in skill['steps']:
                    lines.append(f"1. {step}")

            if skill.get('gotchas'):
                lines.append("**Gotchas:**")
                for gotcha in skill['gotchas']:
                    lines.append(f"- ⚠️ {gotcha}")

            if skill.get('references'):
                lines.append("**References:**")
                for ref in skill['references']:
                    lines.append(f"- {ref}")

            lines.append("")

    # Context budget info
    budget = breadcrumbs.get('context_budget')
    if budget:
        lines.append("## Context Budget")
        lines.append(f"**Task complexity:** {budget.get('task_complexity', 'medium')}")
        lines.append(f"**Total tokens:** {budget.get('total_tokens', 0)}")
        lines.append("")

    # Reference docs
    ref_docs = breadcrumbs.get('reference_docs', [])
    if ref_docs:
        lines.append("## Reference Documentation")
        for doc in ref_docs:
            lines.append(f"- `{doc['path']}` ({doc['type']}) - {doc['description']}")
        lines.append("")

    # Recent artifacts
    artifacts = breadcrumbs.get('recent_artifacts', [])
    if artifacts:
        lines.append("## Recent File Changes")
        for art in artifacts[:5]:  # Top 5
            lines.append(f"- {art.get('ai_id', 'unknown')}: {art.get('task_summary', '')}")
            if art.get('files_modified'):
                for file in art['files_modified'][:3]:  # Top 3 files
                    lines.append(f"  - `{file}`")
        lines.append("")

    return "\n".join(lines)
