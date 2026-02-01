"""
Generate browsable .empirica/ artifact files from git notes.

Reads epistemic data from git notes (the canonical source) and generates
markdown files that render in any git forge (Forgejo, GitHub, GitLab).

Directory structure:
    .empirica/
    ├── README.md              # Project epistemic dashboard
    ├── findings/
    │   ├── README.md          # Index sorted by impact/time
    │   └── {short-id}.md      # Individual finding
    ├── unknowns/
    │   ├── README.md          # Unresolved unknowns index
    │   └── {short-id}.md      # Individual unknown
    ├── dead-ends/
    │   ├── README.md          # Dead ends index
    │   └── {short-id}.md      # Individual dead end
    ├── mistakes/
    │   ├── README.md          # Mistakes index
    │   └── {short-id}.md      # Individual mistake
    ├── goals/
    │   ├── README.md          # Goals index with progress
    │   └── {short-id}.md      # Individual goal with subtasks
    └── sessions/
        ├── README.md          # Session timeline
        └── {short-id}.md      # Session summary
"""

import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def _short_id(uuid_str):
    """First 8 chars of UUID for file naming."""
    return str(uuid_str)[:8] if uuid_str else "unknown"


def _format_date(ts):
    """Format timestamp to human-readable date."""
    if not ts:
        return "unknown"
    if isinstance(ts, (int, float)):
        try:
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        except (ValueError, OSError):
            return str(ts)
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return ts[:16] if len(ts) > 16 else ts
    return str(ts)


def _format_date_short(ts):
    """Format timestamp to date only."""
    full = _format_date(ts)
    return full[:10] if len(full) >= 10 else full


def _impact_bar(impact):
    """Render impact as a visual bar."""
    if impact is None:
        return ""
    n = int(float(impact) * 10)
    return "\u2588" * n + "\u2591" * (10 - n) + f" {float(impact):.1f}"


def _truncate(text, length=100):
    """Truncate text with ellipsis."""
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    return text[:length] + "\u2026" if len(text) > length else text


def _type_emoji(artifact_type):
    """Emoji for artifact type."""
    return {
        "finding": "\U0001f4dd",
        "unknown": "\u2753",
        "dead_end": "\U0001f6ab",
        "mistake": "\u26a0\ufe0f",
        "goal": "\U0001f3af",
        "session": "\U0001f4ca",
    }.get(artifact_type, "\u25c8")


def _read_note_blob(workspace, ref):
    """Read the JSON content from a git notes ref.

    Git notes refs point to commits whose trees contain blobs keyed by
    the annotated commit SHA. We walk: ref → commit → tree → first blob.
    """
    try:
        # Get the tree from the commit
        tree_result = subprocess.run(
            ["git", "cat-file", "-p", ref],
            cwd=workspace, capture_output=True, text=True, timeout=10
        )
        if tree_result.returncode != 0:
            return None

        # Parse tree SHA from commit output (first line: "tree <sha>")
        for cline in tree_result.stdout.split("\n"):
            if cline.startswith("tree "):
                tree_sha = cline.split()[1]
                break
        else:
            return None

        # List blobs in the tree
        ls_result = subprocess.run(
            ["git", "ls-tree", tree_sha],
            cwd=workspace, capture_output=True, text=True, timeout=10
        )
        if ls_result.returncode != 0 or not ls_result.stdout.strip():
            return None

        # Read first blob (there's typically one per note ref)
        first_line = ls_result.stdout.strip().split("\n")[0]
        blob_sha = first_line.split()[2]

        blob_result = subprocess.run(
            ["git", "cat-file", "-p", blob_sha],
            cwd=workspace, capture_output=True, text=True, timeout=10
        )
        if blob_result.returncode == 0 and blob_result.stdout.strip():
            return json.loads(blob_result.stdout.strip())
    except (json.JSONDecodeError, subprocess.TimeoutExpired, IndexError, ValueError):
        pass
    return None


def _read_git_notes(workspace, ref_prefix):
    """Read all notes under a git notes ref prefix.

    Returns list of (id, data_dict) tuples.
    """
    items = []
    try:
        result = subprocess.run(
            ["git", "for-each-ref", f"refs/notes/empirica/{ref_prefix}/"],
            cwd=workspace, capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0 or not result.stdout.strip():
            return items

        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            ref = parts[1]
            item_id = ref.split("/")[-1]

            data = _read_note_blob(workspace, ref)
            if data:
                items.append((item_id, data))
    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout reading git notes for {ref_prefix}")
    return items


# ── Individual artifact page generators ──


def _generate_finding_page(finding_id, data, workspace_root=None):
    """Generate markdown for a single finding."""
    short = _short_id(finding_id)
    finding_text = data.get("finding") or data.get("finding_data", {}).get("finding", "")
    impact = data.get("impact", 0.5)
    session_id = data.get("session_id", "")
    goal_id = data.get("goal_id", "")
    ai_id = data.get("ai_id", "unknown")
    date = data.get("created_at") or data.get("created_timestamp", "")
    subject = data.get("subject", "")

    lines = [
        f"# \U0001f4dd Finding: {short}",
        "",
    ]
    if subject:
        lines.append(f"> **Subject:** {subject}")
        lines.append("")
    lines.extend([
        finding_text,
        "",
        "## Context",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| **Impact** | {_impact_bar(impact)} |",
        f"| **AI Agent** | `{ai_id}` |",
        f"| **Date** | {_format_date(date)} |",
        f"| **Session** | [{_short_id(session_id)}](../sessions/{_short_id(session_id)}.md) |",
    ])
    if goal_id:
        lines.append(f"| **Goal** | [{_short_id(goal_id)}](../goals/{_short_id(goal_id)}.md) |")
    lines.extend([
        "",
        "---",
        f"*Finding ID: `{finding_id}`*",
    ])
    return "\n".join(lines)


def _generate_unknown_page(unknown_id, data):
    """Generate markdown for a single unknown."""
    short = _short_id(unknown_id)
    text = data.get("unknown", "")
    resolved = data.get("resolved") or data.get("is_resolved", False)
    resolved_by = data.get("resolved_by", "")
    session_id = data.get("session_id", "")
    goal_id = data.get("goal_id", "")
    ai_id = data.get("ai_id", "unknown")
    date = data.get("created_at") or data.get("created_timestamp", "")

    status = "\u2705 Resolved" if resolved else "\U0001f534 Open"
    lines = [
        f"# \u2753 Unknown: {short}",
        "",
        f"**Status:** {status}",
        "",
        text,
        "",
        "## Context",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| **AI Agent** | `{ai_id}` |",
        f"| **Date** | {_format_date(date)} |",
        f"| **Session** | [{_short_id(session_id)}](../sessions/{_short_id(session_id)}.md) |",
    ]
    if goal_id:
        lines.append(f"| **Goal** | [{_short_id(goal_id)}](../goals/{_short_id(goal_id)}.md) |")
    if resolved_by:
        lines.append(f"| **Resolved by** | {resolved_by} |")
    lines.extend([
        "",
        "---",
        f"*Unknown ID: `{unknown_id}`*",
    ])
    return "\n".join(lines)


def _generate_dead_end_page(dead_end_id, data):
    """Generate markdown for a single dead end."""
    short = _short_id(dead_end_id)
    approach = data.get("approach", "")
    why_failed = data.get("why_failed", "")
    session_id = data.get("session_id", "")
    goal_id = data.get("goal_id", "")
    ai_id = data.get("ai_id", "unknown")
    date = data.get("created_at") or data.get("created_timestamp", "")

    lines = [
        f"# \U0001f6ab Dead End: {short}",
        "",
        "## Approach Tried",
        "",
        approach,
        "",
        "## Why It Failed",
        "",
        why_failed,
        "",
        "## Context",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| **AI Agent** | `{ai_id}` |",
        f"| **Date** | {_format_date(date)} |",
        f"| **Session** | [{_short_id(session_id)}](../sessions/{_short_id(session_id)}.md) |",
    ]
    if goal_id:
        lines.append(f"| **Goal** | [{_short_id(goal_id)}](../goals/{_short_id(goal_id)}.md) |")
    lines.extend([
        "",
        "---",
        f"*Dead End ID: `{dead_end_id}`*",
    ])
    return "\n".join(lines)


def _generate_mistake_page(mistake_id, data):
    """Generate markdown for a single mistake."""
    short = _short_id(mistake_id)
    mistake = data.get("mistake", "")
    why_wrong = data.get("why_wrong", "")
    prevention = data.get("prevention", "")
    cost = data.get("cost_estimate", "")
    root_cause = data.get("root_cause_vector", "")
    session_id = data.get("session_id", "")
    goal_id = data.get("goal_id", "")
    ai_id = data.get("ai_id", "unknown")
    date = data.get("created_at") or data.get("created_timestamp", "")

    lines = [
        f"# \u26a0\ufe0f Mistake: {short}",
        "",
        "## What Went Wrong",
        "",
        mistake,
        "",
        "## Why It Was Wrong",
        "",
        why_wrong,
        "",
        "## Prevention",
        "",
        prevention,
        "",
        "## Context",
        "",
        "| Field | Value |",
        "|-------|-------|",
    ]
    if cost:
        lines.append(f"| **Cost** | {cost} |")
    if root_cause:
        lines.append(f"| **Root Cause Vector** | `{root_cause}` |")
    lines.extend([
        f"| **AI Agent** | `{ai_id}` |",
        f"| **Date** | {_format_date(date)} |",
        f"| **Session** | [{_short_id(session_id)}](../sessions/{_short_id(session_id)}.md) |",
    ])
    if goal_id:
        lines.append(f"| **Goal** | [{_short_id(goal_id)}](../goals/{_short_id(goal_id)}.md) |")
    lines.extend([
        "",
        "---",
        f"*Mistake ID: `{mistake_id}`*",
    ])
    return "\n".join(lines)


def _generate_goal_page(goal_id, data):
    """Generate markdown for a single goal."""
    short = _short_id(goal_id)
    objective = data.get("objective", "")
    scope = data.get("scope", {})
    complexity = data.get("estimated_complexity", "")
    is_completed = data.get("is_completed", False)
    status = data.get("status", "active")
    subtasks = data.get("subtasks", [])
    lineage = data.get("lineage", [])
    session_id = data.get("session_id", "")
    ai_id = data.get("ai_id", "unknown")
    date = data.get("created_at") or data.get("created_timestamp", "")

    total = len(subtasks)
    completed = sum(1 for s in subtasks if s.get("status") == "completed")
    pct = int(completed / total * 100) if total > 0 else 0
    status_icon = "\u2705" if is_completed else "\u23f3"

    lines = [
        f"# \U0001f3af Goal: {short}",
        "",
        f"**Status:** {status_icon} {status}",
        f"**Progress:** {completed}/{total} subtasks ({pct}%)",
        "",
        f"> {objective}",
        "",
    ]

    if scope:
        lines.extend([
            "## Scope",
            "",
            "| Dimension | Value |",
            "|-----------|-------|",
            f"| Breadth | {scope.get('breadth', '?')} |",
            f"| Duration | {scope.get('duration', '?')} |",
            f"| Coordination | {scope.get('coordination', '?')} |",
        ])
        if complexity:
            lines.append(f"| Complexity | {complexity} |")
        lines.append("")

    if subtasks:
        lines.append("## Subtasks")
        lines.append("")
        for st in subtasks:
            st_status = st.get("status", "pending")
            icon = "\u2705" if st_status == "completed" else "\u2b1c" if st_status == "pending" else "\U0001f7e1"
            desc = _truncate(st.get("description", ""), 120)
            importance = st.get("epistemic_importance", "")
            imp_tag = f" `{importance}`" if importance else ""
            lines.append(f"- {icon} {desc}{imp_tag}")
        lines.append("")

    if lineage:
        lines.extend([
            "## Lineage",
            "",
            "| AI | Action | Session | Date |",
            "|----|--------|---------|------|",
        ])
        for entry in lineage:
            lines.append(
                f"| `{entry.get('ai_id', '?')}` "
                f"| {entry.get('action', '?')} "
                f"| [{_short_id(entry.get('session_id', ''))}](../sessions/{_short_id(entry.get('session_id', ''))}.md) "
                f"| {_format_date_short(entry.get('timestamp', ''))} |"
            )
        lines.append("")

    lines.extend([
        "## Context",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| **AI Agent** | `{ai_id}` |",
        f"| **Date** | {_format_date(date)} |",
        f"| **Session** | [{_short_id(session_id)}](../sessions/{_short_id(session_id)}.md) |",
        "",
        "---",
        f"*Goal ID: `{goal_id}`*",
    ])
    return "\n".join(lines)


def _generate_session_page(session_id, checkpoints):
    """Generate markdown for a session from its checkpoints."""
    short = _short_id(session_id)
    phase_order = {"PREFLIGHT": 0, "CHECK": 1, "ACT": 2, "POSTFLIGHT": 3}
    checkpoints.sort(key=lambda c: (
        c.get("round") or 0,
        phase_order.get(c.get("phase", ""), 99)
    ))

    first = checkpoints[0] if checkpoints else {}
    ai_id = first.get("ai_id", "unknown")
    date = first.get("timestamp", "")

    lines = [
        f"# \U0001f4ca Session: {short}",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| **AI Agent** | `{ai_id}` |",
        f"| **Started** | {_format_date(date)} |",
        f"| **Checkpoints** | {len(checkpoints)} |",
        "",
    ]

    for cp in checkpoints:
        phase = cp.get("phase", "?")
        rnd = cp.get("round", 1)
        vectors = cp.get("vectors", {})
        reasoning = cp.get("reasoning", "")
        decision = cp.get("decision", "")

        lines.append(f"## {phase} (Round {rnd})")
        lines.append("")
        if decision:
            lines.append(f"**Decision:** {decision}")
            lines.append("")

        if vectors:
            lines.extend(["| Vector | Value |", "|--------|-------|"])
            for k, v in sorted(vectors.items()):
                if isinstance(v, dict):
                    for sub_k, sub_v in sorted(v.items()):
                        lines.append(f"| {sub_k} | {sub_v} |")
                else:
                    lines.append(f"| {k} | {v} |")
            lines.append("")

        if reasoning:
            lines.extend([
                "<details>",
                "<summary>Reasoning</summary>",
                "",
                reasoning,
                "",
                "</details>",
                "",
            ])

        delta = cp.get("learning_delta", {})
        if delta:
            lines.extend(["### Learning Delta", "", "| Vector | Change |", "|--------|--------|"])
            for k, v in sorted(delta.items()):
                if isinstance(v, (int, float)):
                    sign = "+" if v > 0 else ""
                    lines.append(f"| {k} | {sign}{v:.2f} |")
            lines.append("")

    lines.extend(["---", f"*Session ID: `{session_id}`*"])
    return "\n".join(lines)


# ── Index page generators ──


def _generate_index_findings(findings):
    """Generate findings/README.md index."""
    findings.sort(key=lambda x: -(x[1].get("impact", 0) or 0))

    lines = [
        f"# \U0001f4dd Findings ({len(findings)})",
        "",
        "> Discoveries, learnings, and validated knowledge",
        "",
        "| Impact | Finding | AI | Date |",
        "|--------|---------|-----|------|",
    ]
    for fid, data in findings:
        short = _short_id(fid)
        impact = data.get("impact", 0.5)
        text = _truncate(data.get("finding", data.get("finding_data", {}).get("finding", "")), 80)
        ai = data.get("ai_id", "?")
        date = _format_date_short(data.get("created_at") or data.get("created_timestamp", ""))
        lines.append(f"| {float(impact):.1f} | [{text}]({short}.md) | `{ai}` | {date} |")

    return "\n".join(lines)


def _generate_index_unknowns(unknowns):
    """Generate unknowns/README.md index."""
    lines = [
        f"# \u2753 Unknowns ({len(unknowns)})",
        "",
        "> Questions, gaps, and areas needing investigation",
        "",
        "| Status | Unknown | AI | Date |",
        "|--------|---------|-----|------|",
    ]
    for uid, data in unknowns:
        short = _short_id(uid)
        resolved = data.get("resolved") or data.get("is_resolved", False)
        status = "\u2705" if resolved else "\U0001f534"
        text = _truncate(data.get("unknown", ""), 80)
        ai = data.get("ai_id", "?")
        date = _format_date_short(data.get("created_at") or data.get("created_timestamp", ""))
        lines.append(f"| {status} | [{text}]({short}.md) | `{ai}` | {date} |")

    return "\n".join(lines)


def _generate_index_dead_ends(dead_ends):
    """Generate dead-ends/README.md index."""
    lines = [
        f"# \U0001f6ab Dead Ends ({len(dead_ends)})",
        "",
        "> Approaches that were tried and failed. Prevents re-exploration.",
        "",
        "| Approach | Why Failed | Date |",
        "|----------|-----------|------|",
    ]
    for did, data in dead_ends:
        short = _short_id(did)
        approach = _truncate(data.get("approach", ""), 60)
        why = _truncate(data.get("why_failed", ""), 60)
        date = _format_date_short(data.get("created_at") or data.get("created_timestamp", ""))
        lines.append(f"| [{approach}]({short}.md) | {why} | {date} |")

    return "\n".join(lines)


def _generate_index_mistakes(mistakes):
    """Generate mistakes/README.md index."""
    lines = [
        f"# \u26a0\ufe0f Mistakes ({len(mistakes)})",
        "",
        "> Errors made and how to prevent them in the future",
        "",
        "| Mistake | Root Cause | Cost | Date |",
        "|---------|-----------|------|------|",
    ]
    for mid, data in mistakes:
        short = _short_id(mid)
        text = _truncate(data.get("mistake", ""), 60)
        root = data.get("root_cause_vector", "")
        cost = data.get("cost_estimate", "")
        date = _format_date_short(data.get("created_at") or data.get("created_timestamp", ""))
        lines.append(f"| [{text}]({short}.md) | `{root}` | {cost} | {date} |")

    return "\n".join(lines)


def _generate_index_goals(goals):
    """Generate goals/README.md index."""
    lines = [
        f"# \U0001f3af Goals ({len(goals)})",
        "",
        "> Work units with subtasks and epistemic tracking",
        "",
        "| Progress | Objective | AI | Status |",
        "|----------|-----------|-----|--------|",
    ]
    for gid, data in goals:
        short = _short_id(gid)
        objective = _truncate(data.get("objective", ""), 70)
        ai = data.get("ai_id", "?")
        subtasks = data.get("subtasks", [])
        total = len(subtasks)
        completed = sum(1 for s in subtasks if s.get("status") == "completed")
        pct = int(completed / total * 100) if total > 0 else 0
        is_done = data.get("is_completed", False)
        status = "\u2705 Done" if is_done else f"{completed}/{total}"
        lines.append(f"| {pct}% | [{objective}]({short}.md) | `{ai}` | {status} |")

    return "\n".join(lines)


def _generate_index_sessions(sessions_map):
    """Generate sessions/README.md index."""
    items = sorted(sessions_map.items(), key=lambda x: x[0], reverse=True)[:50]
    lines = [
        f"# \U0001f4ca Sessions ({len(sessions_map)})",
        "",
        "> Work sessions with epistemic state snapshots",
        "",
        "| Session | AI | Checkpoints | Date |",
        "|---------|-----|-------------|------|",
    ]
    for sid, checkpoints in items:
        short = _short_id(sid)
        first = checkpoints[0] if checkpoints else {}
        ai = first.get("ai_id", "?")
        date = _format_date_short(first.get("timestamp", ""))
        lines.append(f"| [{short}]({short}.md) | `{ai}` | {len(checkpoints)} | {date} |")

    return "\n".join(lines)


# ── Root dashboard ──


def _generate_root_readme(counts, recent_items):
    """Generate the top-level .empirica/README.md dashboard."""
    lines = [
        "# Empirica Epistemic State",
        "",
        "> Knowledge state of this project, tracked by [Empirica](https://getempirica.com)",
        "",
        "## Overview",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| \U0001f4dd [Findings](findings/) | **{counts.get('findings', 0)}** |",
        f"| \u2753 [Unknowns](unknowns/) | **{counts.get('unknowns', 0)}** |",
        f"| \U0001f6ab [Dead Ends](dead-ends/) | **{counts.get('dead_ends', 0)}** |",
        f"| \u26a0\ufe0f [Mistakes](mistakes/) | **{counts.get('mistakes', 0)}** |",
        f"| \U0001f3af [Goals](goals/) | **{counts.get('goals', 0)}** |",
        f"| \U0001f4ca [Sessions](sessions/) | **{counts.get('sessions', 0)}** |",
        "",
        "## Recent Activity",
        "",
        "| Date | Type | Summary |",
        "|------|------|---------|",
    ]

    for item_type, item_id, item_data in recent_items[:15]:
        date = _format_date_short(
            item_data.get("created_at") or item_data.get("created_timestamp", "")
        )
        emoji = _type_emoji(item_type)
        short = _short_id(item_id)

        type_dirs = {
            "finding": "findings",
            "unknown": "unknowns",
            "dead_end": "dead-ends",
            "mistake": "mistakes",
            "goal": "goals",
        }
        link_dir = type_dirs.get(item_type, "sessions")

        text_keys = {
            "finding": lambda d: d.get("finding", d.get("finding_data", {}).get("finding", "")),
            "unknown": lambda d: d.get("unknown", ""),
            "dead_end": lambda d: d.get("approach", ""),
            "mistake": lambda d: d.get("mistake", ""),
            "goal": lambda d: d.get("objective", ""),
        }
        text = _truncate(text_keys.get(item_type, lambda d: "Session")(item_data), 80)
        lines.append(f"| {date} | {emoji} [{item_type}]({link_dir}/{short}.md) | {text} |")

    lines.extend([
        "",
        "---",
        "*Generated by [Empirica](https://getempirica.com) \u2014 epistemic infrastructure for AI-assisted work*",
    ])
    return "\n".join(lines)


# ── Main generation function ──


def generate_artifacts(workspace_root, output_dir=None, verbose=False):
    """Read git notes and generate .empirica/ markdown files.

    Args:
        workspace_root: Git repository root path
        output_dir: Output directory (default: {workspace_root}/.empirica)
        verbose: Print progress

    Returns:
        dict with counts and status
    """
    workspace = str(workspace_root)
    out = Path(output_dir or os.path.join(workspace, ".empirica"))

    if verbose:
        print(f"Reading git notes from {workspace}...")

    # Read all artifact types
    findings = _read_git_notes(workspace, "findings")
    unknowns = _read_git_notes(workspace, "unknowns")
    dead_ends = _read_git_notes(workspace, "dead_ends")
    mistakes = _read_git_notes(workspace, "mistakes")
    goals = _read_git_notes(workspace, "goals")

    # Read session checkpoints (nested ref structure)
    sessions_map = {}
    try:
        result = subprocess.run(
            ["git", "for-each-ref", "refs/notes/empirica/session/"],
            cwd=workspace, capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split("\t")
                if len(parts) < 2:
                    continue
                ref = parts[1]
                # ref: refs/notes/empirica/session/{session_id}/{phase}/{round}
                ref_parts = ref.split("/")
                if len(ref_parts) >= 7:
                    sid = ref_parts[4]
                    data = _read_note_blob(workspace, ref)
                    if data:
                        if sid not in sessions_map:
                            sessions_map[sid] = []
                        sessions_map[sid].append(data)
    except subprocess.TimeoutExpired:
        logger.warning("Timeout reading session checkpoints")

    if verbose:
        print(f"  Findings: {len(findings)}")
        print(f"  Unknowns: {len(unknowns)}")
        print(f"  Dead ends: {len(dead_ends)}")
        print(f"  Mistakes: {len(mistakes)}")
        print(f"  Goals: {len(goals)}")
        print(f"  Sessions: {len(sessions_map)}")

    # Create directory structure
    for subdir in ["findings", "unknowns", "dead-ends", "mistakes", "goals", "sessions"]:
        (out / subdir).mkdir(parents=True, exist_ok=True)

    # Generate individual artifact pages
    for fid, data in findings:
        (out / "findings" / f"{_short_id(fid)}.md").write_text(
            _generate_finding_page(fid, data, workspace))

    for uid, data in unknowns:
        (out / "unknowns" / f"{_short_id(uid)}.md").write_text(
            _generate_unknown_page(uid, data))

    for did, data in dead_ends:
        (out / "dead-ends" / f"{_short_id(did)}.md").write_text(
            _generate_dead_end_page(did, data))

    for mid, data in mistakes:
        (out / "mistakes" / f"{_short_id(mid)}.md").write_text(
            _generate_mistake_page(mid, data))

    for gid, data in goals:
        (out / "goals" / f"{_short_id(gid)}.md").write_text(
            _generate_goal_page(gid, data))

    for sid, checkpoints in sessions_map.items():
        (out / "sessions" / f"{_short_id(sid)}.md").write_text(
            _generate_session_page(sid, checkpoints))

    # Generate index pages
    (out / "findings" / "README.md").write_text(_generate_index_findings(findings))
    (out / "unknowns" / "README.md").write_text(_generate_index_unknowns(unknowns))
    (out / "dead-ends" / "README.md").write_text(_generate_index_dead_ends(dead_ends))
    (out / "mistakes" / "README.md").write_text(_generate_index_mistakes(mistakes))
    (out / "goals" / "README.md").write_text(_generate_index_goals(goals))
    (out / "sessions" / "README.md").write_text(_generate_index_sessions(sessions_map))

    # Build recent items for root dashboard
    recent_items = []
    for fid, data in findings:
        recent_items.append(("finding", fid, data))
    for uid, data in unknowns:
        recent_items.append(("unknown", uid, data))
    for did, data in dead_ends:
        recent_items.append(("dead_end", did, data))
    for mid, data in mistakes:
        recent_items.append(("mistake", mid, data))

    def _get_ts(item):
        d = item[2]
        ts = d.get("created_at") or d.get("created_timestamp") or 0
        if isinstance(ts, str):
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
            except ValueError:
                return 0
        return float(ts) if ts else 0

    recent_items.sort(key=_get_ts, reverse=True)

    counts = {
        "findings": len(findings),
        "unknowns": len(unknowns),
        "dead_ends": len(dead_ends),
        "mistakes": len(mistakes),
        "goals": len(goals),
        "sessions": len(sessions_map),
    }

    (out / "README.md").write_text(_generate_root_readme(counts, recent_items))

    total_files = sum(counts.values()) + 7  # +7 for README index files
    if verbose:
        print(f"\nGenerated {total_files} files in {out}/")

    return {
        "ok": True,
        "output_dir": str(out),
        "counts": counts,
        "total_files": total_files,
    }


# ── CLI handler ──


def handle_artifacts_generate_command(args):
    """CLI handler for artifacts-generate command."""
    try:
        verbose = getattr(args, "verbose", False)
        output_format = getattr(args, "output", "text")
        output_dir = getattr(args, "output_dir", None)

        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print("Error: Not in a git repository")
            return 1

        workspace_root = result.stdout.strip()

        result = generate_artifacts(
            workspace_root=workspace_root,
            output_dir=output_dir,
            verbose=(verbose or output_format != "json"),
        )

        if output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            counts = result["counts"]
            print(f"\n\u2705 Generated .empirica/ artifacts:")
            print(f"   \U0001f4dd Findings:  {counts['findings']}")
            print(f"   \u2753 Unknowns:  {counts['unknowns']}")
            print(f"   \U0001f6ab Dead Ends: {counts['dead_ends']}")
            print(f"   \u26a0\ufe0f  Mistakes:  {counts['mistakes']}")
            print(f"   \U0001f3af Goals:     {counts['goals']}")
            print(f"   \U0001f4ca Sessions:  {counts['sessions']}")
            print(f"\n   Total: {result['total_files']} files in {result['output_dir']}")

        return 0

    except Exception as e:
        logger.error(f"Error generating artifacts: {e}")
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        print(f"Error: {e}")
        return 1
