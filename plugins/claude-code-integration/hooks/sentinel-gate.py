#!/usr/bin/env python3
"""
Empirica Sentinel Gate Hook - Enforces CHECK before high-impact tools

This hook intercepts Edit, Write, and Bash (non-read-only) tool calls and
checks if we have a passing CHECK gate. If not, it blocks the tool
and prompts the AI to run CHECK first.

Architecture:
1. Hook receives tool call info via stdin (JSON)
2. Check reflexes table for CHECK with decision="proceed"
3. If valid CHECK exists, allow
4. If no CHECK or CHECK returned "investigate", block with guidance

Environment variables:
- EMPIRICA_SENTINEL_CHECK_EXPIRY=true - Enable 30-min CHECK expiry (disabled by default)
  Note: Expiry is problematic for paused sessions; user may resume later.
- EMPIRICA_SENTINEL_LOOPING=false - Disable sentinel looping entirely

This enforces noetic-before-praxic at the tool level.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add empirica to path
sys.path.insert(0, str(Path.home() / 'empirical-ai' / 'empirica'))


def find_project_root() -> Path:
    """Find Empirica project root with valid database."""
    def has_valid_db(path: Path) -> bool:
        db_path = path / '.empirica' / 'sessions' / 'sessions.db'
        return db_path.exists() and db_path.stat().st_size > 0

    # Check environment variable
    if workspace_root := os.getenv('EMPIRICA_WORKSPACE_ROOT'):
        workspace_path = Path(workspace_root).expanduser().resolve()
        if has_valid_db(workspace_path):
            return workspace_path

    # Known development paths
    known_paths = [
        Path.home() / 'empirical-ai' / 'empirica',
        Path.home() / 'empirica',
    ]
    for path in known_paths:
        if has_valid_db(path):
            return path

    # Search upward from cwd
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if has_valid_db(parent):
            return parent
        if parent == parent.parent:
            break

    return Path.cwd()


def get_active_session() -> str:
    """Get the active Empirica session ID."""
    try:
        from empirica.utils.session_resolver import get_latest_session_id
        return get_latest_session_id(ai_id='claude-code', active_only=True)
    except Exception:
        return None


def get_bootstrap_status(session_id: str) -> dict:
    """
    Check if project-bootstrap has been run for this session.

    Returns:
        {
            "has_bootstrap": bool,
            "project_id": str or None
        }
    """
    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()
        cursor = db.conn.cursor()

        cursor.execute("""
            SELECT project_id FROM sessions
            WHERE session_id = ?
        """, (session_id,))
        row = cursor.fetchone()
        db.close()

        if not row:
            return {"has_bootstrap": False, "project_id": None}

        project_id = row[0]
        return {
            "has_bootstrap": project_id is not None,
            "project_id": project_id
        }
    except Exception as e:
        return {"has_bootstrap": False, "project_id": None, "error": str(e)}


def get_session_phase_state(session_id: str) -> dict:
    """
    Get the CASCADE phase state of a session.

    Returns:
        {
            "has_preflight": bool,
            "has_check": bool,
            "has_postflight": bool,
            "last_phase": str or None,
            "is_active_cycle": bool  # Has PREFLIGHT but no POSTFLIGHT
        }
    """
    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()
        cursor = db.conn.cursor()

        cursor.execute("""
            SELECT phase FROM reflexes
            WHERE session_id = ?
            ORDER BY timestamp DESC
        """, (session_id,))
        rows = cursor.fetchall()
        db.close()

        if not rows:
            return {
                "has_preflight": False,
                "has_check": False,
                "has_postflight": False,
                "last_phase": None,
                "is_active_cycle": False
            }

        phases = [r[0] for r in rows]
        last_phase = phases[0] if phases else None

        has_preflight = "PREFLIGHT" in phases
        has_check = "CHECK" in phases
        has_postflight = "POSTFLIGHT" in phases

        # Active cycle = has PREFLIGHT but last phase is not POSTFLIGHT
        is_active_cycle = has_preflight and last_phase != "POSTFLIGHT"

        return {
            "has_preflight": has_preflight,
            "has_check": has_check,
            "has_postflight": has_postflight,
            "last_phase": last_phase,
            "is_active_cycle": is_active_cycle
        }
    except Exception as e:
        return {
            "has_preflight": False,
            "has_check": False,
            "has_postflight": False,
            "last_phase": None,
            "is_active_cycle": False,
            "error": str(e)
        }


def get_last_compact_timestamp() -> datetime:
    """
    Get the timestamp of the most recent compact (from pre_summary snapshot).

    Returns None if no compact found.
    """
    try:
        ref_docs_dir = Path.cwd() / ".empirica" / "ref-docs"
        if not ref_docs_dir.exists():
            return None

        snapshots = sorted(ref_docs_dir.glob("pre_summary_*.json"), reverse=True)
        if not snapshots:
            return None

        # Parse timestamp from filename: pre_summary_2026-01-21T12-30-45.json
        filename = snapshots[0].name
        timestamp_str = filename.replace("pre_summary_", "").replace(".json", "")
        # Convert 2026-01-21T12-30-45 to ISO format
        timestamp_str = timestamp_str.replace("T", " ").replace("-", ":", 2)
        # Now it's like "2026:01:21 12:30:45", need to fix the date part
        parts = timestamp_str.split(" ")
        if len(parts) == 2:
            date_part = parts[0].replace(":", "-")  # Back to 2026-01-21
            time_part = parts[1].replace("-", ":")  # 12:30:45
            timestamp_str = f"{date_part}T{time_part}"

        return datetime.fromisoformat(timestamp_str)
    except Exception:
        return None


def get_last_check_decision(session_id: str, max_age_minutes: int = 30) -> dict:
    """
    Get the most recent CHECK decision for this session.

    Returns:
        {
            "has_check": bool,
            "decision": "proceed" | "investigate" | None,
            "age_minutes": float,
            "is_valid": bool,  # True if recent CHECK with proceed AND no compact since
            "invalidated_by_compact": bool  # True if compact happened after CHECK
        }
    """
    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Get most recent CHECK phase
        cursor.execute("""
            SELECT phase, reflex_data, timestamp
            FROM reflexes
            WHERE session_id = ? AND phase = 'CHECK'
            ORDER BY timestamp DESC
            LIMIT 1
        """, (session_id,))

        row = cursor.fetchone()
        db.close()

        if not row:
            return {
                "has_check": False,
                "decision": None,
                "age_minutes": None,
                "is_valid": False,
                "invalidated_by_compact": False
            }

        phase, reflex_data, timestamp = row

        # Parse decision from reflex_data
        decision = None
        if reflex_data:
            try:
                data = json.loads(reflex_data)
                decision = data.get('decision')
            except json.JSONDecodeError:
                pass

        # Calculate age - handle both ISO format and Unix timestamps (SQLite float)
        check_time = None
        age_minutes = None
        try:
            # Check if timestamp is a Unix timestamp (float/int)
            if isinstance(timestamp, (int, float)) or (isinstance(timestamp, str) and timestamp.replace('.', '').replace('-', '').isdigit()):
                check_time = datetime.fromtimestamp(float(timestamp))
            else:
                # ISO format
                check_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                # Make timezone-naive for comparison
                if check_time.tzinfo is not None:
                    check_time = check_time.replace(tzinfo=None)
            age = datetime.now() - check_time
            age_minutes = age.total_seconds() / 60
        except Exception:
            # Skip age check if timestamp parsing fails rather than blocking
            age_minutes = None

        # Check if a compact happened AFTER this CHECK
        invalidated_by_compact = False
        last_compact = get_last_compact_timestamp()
        if last_compact and check_time:
            if last_compact > check_time:
                invalidated_by_compact = True

        # Check validity - skip age check if age_minutes is None (parsing failed)
        # Age check is disabled by default via EMPIRICA_SENTINEL_CHECK_EXPIRY env var
        check_expiry_enabled = os.getenv('EMPIRICA_SENTINEL_CHECK_EXPIRY', 'false').lower() == 'true'
        age_ok = True
        if check_expiry_enabled and age_minutes is not None:
            age_ok = age_minutes <= max_age_minutes

        is_valid = (
            decision == 'proceed' and
            age_ok and
            not invalidated_by_compact  # Compact invalidates CHECK
        )

        return {
            "has_check": True,
            "decision": decision,
            "age_minutes": round(age_minutes, 1) if age_minutes is not None else None,
            "is_valid": is_valid,
            "invalidated_by_compact": invalidated_by_compact,
            "check_time": str(check_time) if check_time else None,
            "last_compact_time": str(last_compact) if last_compact else None
        }

    except Exception as e:
        return {
            "has_check": False,
            "decision": None,
            "age_minutes": None,
            "is_valid": False,
            "invalidated_by_compact": False,
            "error": str(e)
        }


def main():
    """Main hook logic."""
    # Parse hook input
    try:
        hook_input = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        hook_input = {}

    tool_name = hook_input.get('tool_name', 'unknown')

    # Find project root and change to it
    project_root = find_project_root()
    os.chdir(project_root)

    # Get active session
    session_id = get_active_session()

    if not session_id:
        # No active session - allow but warn
        output = {
            "decision": "allow",
            "reason": "No active Empirica session - gate bypassed",
            "hookSpecificOutput": {
                "hookEventName": "PreToolCall",
                "warning": "No active session. Consider running: empirica session-create"
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    # Check for bootstrap context
    bootstrap_status = get_bootstrap_status(session_id)

    if not bootstrap_status.get('has_bootstrap'):
        # No bootstrap - block and provide guidance
        reason = f"No project context loaded. Run project-bootstrap before {tool_name}."
        guidance = f"""
## Sentinel Gate: BOOTSTRAP Required

Session `{session_id}` has no project context loaded.
Without bootstrap, your epistemic assessments are hollow.

**Run bootstrap first:**

```bash
empirica project-bootstrap --session-id {session_id} --output json
```

Then run CHECK to proceed with this action.
"""

        output = {
            "decision": "block",
            "reason": reason,
            "session_id": session_id,
            "bootstrap_status": bootstrap_status,
            "hookSpecificOutput": {
                "hookEventName": "PreToolCall",
                "additionalContext": guidance
            }
        }

        print(f"""
🚫 Sentinel Gate: {tool_name} blocked

{reason}

Run project-bootstrap first. See guidance in context.
""", file=sys.stderr)

        print(json.dumps(output))
        sys.exit(0)

    # Check phase state to determine PREFLIGHT vs CHECK requirement
    phase_state = get_session_phase_state(session_id)

    # If no PREFLIGHT at all, require PREFLIGHT first
    if not phase_state.get('has_preflight'):
        reason = f"No PREFLIGHT found. Run PREFLIGHT to establish baseline before {tool_name}."
        guidance = f"""
## Sentinel Gate: PREFLIGHT Required

Session `{session_id}` has no PREFLIGHT - you need to establish an epistemic baseline.

**Run PREFLIGHT:**

```bash
empirica preflight-submit - << 'EOF'
{{
  "session_id": "{session_id}",
  "task_context": "<what you're working on>",
  "vectors": {{
    "know": <0.0-1.0: What do you know about this task?>,
    "uncertainty": <0.0-1.0: How uncertain are you?>,
    "context": <0.0-1.0: How well do you understand the codebase?>,
    "engagement": <0.0-1.0: How engaged are you?>
  }},
  "reasoning": "<explain your starting epistemic state>"
}}
EOF
```

After PREFLIGHT, run CHECK to proceed with this action.
"""
        output = {
            "decision": "block",
            "reason": reason,
            "session_id": session_id,
            "phase_state": phase_state,
            "hookSpecificOutput": {
                "hookEventName": "PreToolCall",
                "additionalContext": guidance
            }
        }

        print(f"""
🚫 Sentinel Gate: {tool_name} blocked

{reason}

Run PREFLIGHT first. See guidance in context.
""", file=sys.stderr)

        print(json.dumps(output))
        sys.exit(0)

    # Check for recent valid CHECK
    check_status = get_last_check_decision(session_id)

    if check_status.get('is_valid'):
        # Valid CHECK exists - allow
        output = {
            "decision": "allow",
            "reason": f"Valid CHECK (decision={check_status['decision']}, age={check_status['age_minutes']}min)",
            "session_id": session_id,
            "check_status": check_status,
            "phase_state": phase_state
        }
        print(json.dumps(output))
        sys.exit(0)

    # No valid CHECK - check if sentinel looping is disabled
    if os.getenv('EMPIRICA_SENTINEL_LOOPING', 'true').lower() == 'false':
        output = {
            "decision": "allow",
            "reason": "Sentinel looping disabled (EMPIRICA_SENTINEL_LOOPING=false)",
            "session_id": session_id
        }
        print(json.dumps(output))
        sys.exit(0)

    # Block and provide guidance
    if check_status.get('has_check'):
        if check_status.get('invalidated_by_compact'):
            # CRITICAL: Compact happened after CHECK - need fresh calibration
            reason = f"CHECK invalidated by compact. Run CHECK to calibrate post-compact state before {tool_name}."
            guidance = f"""
## Sentinel Gate: POST-COMPACT CHECK Required

Your context was compacted since your last CHECK. Your previous epistemic assessment
is now **invalid** because you lost detailed context.

**This CHECK is critical for calibration data** - it captures how your knowledge
changed across the compact boundary.

**Run CHECK with HONEST post-compact assessment:**

```bash
empirica check-submit - << 'EOF'
{{
  "session_id": "{session_id}",
  "action_description": "<what you intend to do>",
  "vectors": {{
    "know": <0.0-1.0: What do you ACTUALLY know now after compact?>,
    "uncertainty": <0.0-1.0: How uncertain are you with only summary context?>,
    "context": <0.0-1.0: How well do you understand current state?>
  }},
  "reasoning": "Post-compact assessment: <explain what you remember vs what you lost>"
}}
EOF
```

**Key principle:** Post-compact know should typically be LOWER than pre-compact.
Be honest - this data is used for calibration.
"""
        elif check_status.get('decision') == 'investigate':
            reason = f"Last CHECK returned 'investigate'. Complete investigation before {tool_name}."
            guidance = """
## Sentinel Gate: INVESTIGATE Required

Your last CHECK returned `investigate` - you need more information before this action.

**Steps:**
1. Continue investigation (read files, search, ask questions)
2. When ready, run CHECK again:

```bash
empirica check-submit - << 'EOF'
{
  "session_id": "<SESSION_ID>",
  "action_description": "<what you intend to do>",
  "vectors": {
    "know": <updated_value>,
    "uncertainty": <updated_value>,
    "context": <updated_value>
  },
  "reasoning": "<why you're now ready>"
}
EOF
```

3. If CHECK returns `proceed`, you can continue with the action.
"""
        else:
            # Fallback: CHECK exists but is invalid for other reasons
            # (e.g., age expired if EMPIRICA_SENTINEL_CHECK_EXPIRY=true, or unexpected decision)
            age_info = f" (age={check_status.get('age_minutes')}min)" if check_status.get('age_minutes') else ""
            decision_info = check_status.get('decision', 'unknown')
            reason = f"CHECK not valid{age_info}, decision={decision_info}. Run CHECK before {tool_name}."
            guidance = """
## Sentinel Gate: CHECK Required

Your last CHECK is not valid. Run a fresh CHECK before this action.

```bash
empirica check-submit - << 'EOF'
{
  "session_id": "<SESSION_ID>",
  "action_description": "<what you intend to do>",
  "vectors": {
    "know": <0.0-1.0>,
    "uncertainty": <0.0-1.0>,
    "context": <0.0-1.0>
  },
  "reasoning": "<current epistemic state>"
}
EOF
```
"""
    else:
        reason = f"No CHECK found for this session. Run CHECK before {tool_name}."
        guidance = f"""
## Sentinel Gate: CHECK Required

No CHECK gate found for session `{session_id}`.
Before high-impact actions (Edit, Write, Bash), you must assess readiness.

**Run CHECK:**

```bash
empirica check-submit - << 'EOF'
{{
  "session_id": "{session_id}",
  "action_description": "<what you intend to do>",
  "vectors": {{
    "know": <0.0-1.0: How much do you know about this task?>,
    "uncertainty": <0.0-1.0: How uncertain are you?>,
    "context": <0.0-1.0: How well do you understand the codebase?>
  }},
  "reasoning": "<explain your current epistemic state>"
}}
EOF
```

**If CHECK returns:**
- `proceed` - You can continue with the action
- `investigate` - Do more research first, then CHECK again
"""

    output = {
        "decision": "block",
        "reason": reason,
        "session_id": session_id,
        "check_status": check_status,
        "hookSpecificOutput": {
            "hookEventName": "PreToolCall",
            "additionalContext": guidance
        }
    }

    # Print guidance to stderr for user visibility
    print(f"""
🚫 Sentinel Gate: {tool_name} blocked

{reason}

Run CHECK to proceed. See guidance in context.
""", file=sys.stderr)

    print(json.dumps(output))
    sys.exit(0)


if __name__ == '__main__':
    main()
