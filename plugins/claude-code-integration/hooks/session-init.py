#!/usr/bin/env python3
"""
Empirica Session Init Hook - Auto-creates session + bootstrap for new conversations

This hook runs on new/fresh session starts (not compactions) and:
1. Creates a new Empirica session
2. Runs project-bootstrap to load context
3. Prompts the AI to run PREFLIGHT with loaded context

This ensures every conversation starts with proper epistemic baseline.
"""

import json
import sys
import subprocess
import os
import re
import shutil
from pathlib import Path
from datetime import datetime

def archive_stale_plans() -> list:
    """
    Archive plan files whose goals are complete.

    Scans ~/.claude/plans/ for .md files, extracts goal_id from content,
    checks if goal is complete, and moves to archive if so.

    Returns list of archived plan names.
    """
    plans_dir = Path.home() / ".claude" / "plans"
    archive_dir = plans_dir / "archive"

    if not plans_dir.exists():
        return []

    archived = []
    goal_id_pattern = re.compile(r'\*\*Goal ID:\*\*\s*`([a-f0-9-]+)`')

    for plan_file in plans_dir.glob("*.md"):
        if plan_file.name.startswith("."):
            continue

        try:
            content = plan_file.read_text()

            # Extract goal_id if present
            match = goal_id_pattern.search(content)
            if not match:
                continue

            goal_id = match.group(1)

            # Check if goal exists and is complete
            result = subprocess.run(
                ['empirica', 'goals-progress', '--goal-id', goal_id, '--output', 'json'],
                capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                try:
                    goal_data = json.loads(result.stdout)
                    status = goal_data.get('status', '')
                    completion_pct = goal_data.get('completion_percentage', 0)

                    # Archive if completed or all subtasks done
                    if status == 'completed' or completion_pct >= 100:
                        archive_dir.mkdir(parents=True, exist_ok=True)
                        dest = archive_dir / plan_file.name
                        shutil.move(str(plan_file), str(dest))
                        archived.append(plan_file.name)
                except json.JSONDecodeError:
                    pass
        except Exception:
            continue

    return archived


def find_git_root() -> Path | None:
    """Find git repository root from current directory."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except:
        pass
    return None


def find_project_root() -> Path:
    """Find project root - prefers git repo, falls back to cwd."""
    # First check for explicit workspace root
    if workspace_root := os.getenv('EMPIRICA_WORKSPACE_ROOT'):
        workspace_path = Path(workspace_root).expanduser().resolve()
        if workspace_path.exists():
            return workspace_path

    # Try to find git repo root (most common case)
    git_root = find_git_root()
    if git_root:
        return git_root

    # Fall back to current working directory
    return Path.cwd()


def create_session_and_bootstrap(ai_id: str, project_id: str = None) -> dict:
    """
    Create session + run bootstrap in sequence.

    Returns dict with session_id, bootstrap_output, error
    """
    result = {
        "session_id": None,
        "bootstrap_output": None,
        "project_context": None,
        "error": None
    }

    try:
        # Create session
        create_cmd = subprocess.run(
            ['empirica', 'session-create', '--ai-id', ai_id, '--output', 'json'],
            capture_output=True, text=True, timeout=15
        )

        if create_cmd.returncode != 0:
            result["error"] = f"session-create failed: {create_cmd.stderr}"
            return result

        create_output = json.loads(create_cmd.stdout)
        session_id = create_output.get('session_id')

        if not session_id:
            result["error"] = "session-create returned no session_id"
            return result

        result["session_id"] = session_id

        # Run bootstrap
        bootstrap_cmd = subprocess.run(
            ['empirica', 'project-bootstrap', '--session-id', session_id, '--output', 'json'],
            capture_output=True, text=True, timeout=30
        )

        if bootstrap_cmd.returncode == 0:
            try:
                bootstrap_data = json.loads(bootstrap_cmd.stdout)
                result["bootstrap_output"] = bootstrap_data

                # Extract key context
                result["project_context"] = {
                    "goals": bootstrap_data.get("goals", [])[:3],
                    "findings": bootstrap_data.get("findings", [])[:5],
                    "unknowns": bootstrap_data.get("unknowns", [])[:5]
                }
            except json.JSONDecodeError:
                result["bootstrap_output"] = {"raw": bootstrap_cmd.stdout[:500]}

    except subprocess.TimeoutExpired:
        result["error"] = "Command timed out"
    except Exception as e:
        result["error"] = str(e)

    return result


def format_context(ctx: dict) -> str:
    """Format project context for prompt."""
    if not ctx:
        return "  (No context available)"

    parts = []

    if ctx.get("goals"):
        parts.append("**Active Goals:**")
        for g in ctx["goals"]:
            obj = g.get("objective", g) if isinstance(g, dict) else str(g)
            parts.append(f"  - {obj[:100]}")

    if ctx.get("findings"):
        parts.append("\n**Recent Findings:**")
        for f in ctx["findings"]:
            finding = f.get("finding", f) if isinstance(f, dict) else str(f)
            parts.append(f"  - {finding[:100]}")

    if ctx.get("unknowns"):
        parts.append("\n**Open Unknowns:**")
        for u in ctx["unknowns"]:
            unknown = u.get("unknown", u) if isinstance(u, dict) else str(u)
            parts.append(f"  - {unknown[:100]}")

    return "\n".join(parts) if parts else "  (No context loaded)"


def main():
    """Main session init logic."""
    hook_input = {}
    try:
        hook_input = json.loads(sys.stdin.read())
    except:
        pass

    # Find project root
    project_root = find_project_root()
    os.chdir(project_root)

    ai_id = os.getenv('EMPIRICA_AI_ID', 'claude-code')

    # Archive stale plans (whose goals are complete)
    archived_plans = archive_stale_plans()

    # Create session and bootstrap
    result = create_session_and_bootstrap(ai_id)

    if result.get("error"):
        # Error creating session - provide fallback guidance
        output = {
            "ok": False,
            "error": result["error"],
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": f"""
## Session Init Failed

Error: {result["error"]}

**Manual Setup Required:**

```bash
empirica session-create --ai-id {ai_id} --output json
empirica project-bootstrap --session-id <SESSION_ID> --output json
empirica preflight-submit - << 'EOF'
{{
  "session_id": "<SESSION_ID>",
  "task_context": "<task>",
  "vectors": {{ "know": 0.3, "uncertainty": 0.6, "context": 0.3, "engagement": 0.7 }},
  "reasoning": "New session baseline"
}}
EOF
```
"""
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    # Success - generate PREFLIGHT prompt
    session_id = result["session_id"]
    context_text = format_context(result.get("project_context"))

    prompt = f"""
## New Session Initialized

**Session ID:** `{session_id}`
**Project context loaded via bootstrap**

### Project Context:
{context_text}

### REQUIRED: Run PREFLIGHT (Baseline)

Assess your epistemic state after reviewing the context above:

```bash
empirica preflight-submit - << 'EOF'
{{
  "session_id": "{session_id}",
  "task_context": "<what the user is asking for>",
  "vectors": {{
    "know": <0.0-1.0: How much do you know about this task/codebase?>,
    "uncertainty": <0.0-1.0: How uncertain are you?>,
    "context": <0.0-1.0: How well do you understand the current state?>,
    "engagement": <0.0-1.0: How engaged/aligned are you with the task?>
  }},
  "reasoning": "New session: <explain your starting epistemic state>"
}}
EOF
```

**After PREFLIGHT:** Before any Edit/Write/Bash, run CHECK to validate readiness.
"""

    output = {
        "ok": True,
        "session_id": session_id,
        "bootstrap_complete": result.get("bootstrap_output") is not None,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": prompt
        }
    }

    # User-visible message
    archive_msg = f"\n🗄️  Archived {len(archived_plans)} stale plan(s)" if archived_plans else ""
    print(f"""
🚀 Empirica: New Session Initialized

✅ Session created: {session_id}
✅ Project context loaded{archive_msg}

📋 Run PREFLIGHT to establish baseline, then CHECK before actions.
""", file=sys.stderr)

    print(json.dumps(output))
    sys.exit(0)


if __name__ == '__main__':
    main()
