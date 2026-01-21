#!/usr/bin/env python3
"""
Empirica Sentinel Gate - Enforces CASCADE workflow before praxic tools.

Gates Edit, Write, NotebookEdit until valid PREFLIGHT + CHECK exist.

Core features (always on):
- Smart project root discovery (env var, known paths, cwd search)
- PREFLIGHT requirement detection
- Decision parsing (blocks if CHECK returned "investigate")
- Vector threshold validation (know >= 0.70, uncertainty <= 0.35 after bias)

Optional features (off by default):
- EMPIRICA_SENTINEL_REQUIRE_BOOTSTRAP=true - Require project-bootstrap before praxic
- EMPIRICA_SENTINEL_COMPACT_INVALIDATION=true - Invalidate CHECK after compact
- EMPIRICA_SENTINEL_CHECK_EXPIRY=true - Enable 30-minute CHECK expiry
- EMPIRICA_SENTINEL_LOOPING=false - Disable sentinel entirely
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime

PRAXIC_TOOLS = {'Edit', 'Write', 'NotebookEdit'}
KNOW_THRESHOLD = 0.70
UNCERTAINTY_THRESHOLD = 0.35
KNOW_BIAS = 0.10
UNCERTAINTY_BIAS = -0.04
MAX_CHECK_AGE_MINUTES = 30


def respond(decision, reason=""):
    """Output in Claude Code's expected format."""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason
        }
    }
    # Suppress output for "allow" to avoid "hook error" display bug in Claude Code TUI
    if decision == "allow":
        output["suppressOutput"] = True
    print(json.dumps(output))


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


def get_last_compact_timestamp(project_root: Path) -> datetime:
    """Get timestamp of most recent compact from pre_summary snapshot."""
    try:
        ref_docs_dir = project_root / ".empirica" / "ref-docs"
        if not ref_docs_dir.exists():
            return None
        snapshots = sorted(ref_docs_dir.glob("pre_summary_*.json"), reverse=True)
        if not snapshots:
            return None
        # Parse: pre_summary_2026-01-21T12-30-45.json
        filename = snapshots[0].name
        ts = filename.replace("pre_summary_", "").replace(".json", "")
        # Convert 2026-01-21T12-30-45 to ISO
        date_part, time_part = ts.split("T")
        time_part = time_part.replace("-", ":")
        return datetime.fromisoformat(f"{date_part}T{time_part}")
    except Exception:
        return None


def main():
    try:
        hook_input = json.loads(sys.stdin.read() or '{}')
    except Exception:
        hook_input = {}

    tool_name = hook_input.get('tool_name', 'unknown')

    # Allow noetic tools unconditionally
    if tool_name not in PRAXIC_TOOLS:
        respond("allow", f"Noetic: {tool_name}")
        sys.exit(0)

    # Check if sentinel looping is disabled
    if os.getenv('EMPIRICA_SENTINEL_LOOPING', 'true').lower() == 'false':
        respond("allow", "Sentinel looping disabled")
        sys.exit(0)

    # Setup paths - smart discovery
    project_root = find_project_root()
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))

    # Get active session
    try:
        from empirica.utils.session_resolver import get_latest_session_id
        session_id = get_latest_session_id(ai_id='claude-code', active_only=True)
    except Exception:
        respond("allow", "No session resolver")
        sys.exit(0)

    if not session_id:
        respond("allow", "No active session")
        sys.exit(0)

    from empirica.data.session_database import SessionDatabase
    db = SessionDatabase()
    cursor = db.conn.cursor()

    # Optional: Bootstrap requirement
    if os.getenv('EMPIRICA_SENTINEL_REQUIRE_BOOTSTRAP', 'false').lower() == 'true':
        cursor.execute("SELECT project_id FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        if not row or not row[0]:
            db.close()
            print(f"No project-bootstrap for session {session_id[:8]}. Run: empirica project-bootstrap --session-id {session_id}", file=sys.stderr)
            sys.exit(2)

    # Check for PREFLIGHT
    cursor.execute("""
        SELECT 1 FROM reflexes
        WHERE session_id = ? AND phase = 'PREFLIGHT'
        LIMIT 1
    """, (session_id,))
    has_preflight = cursor.fetchone() is not None

    if not has_preflight:
        db.close()
        print(f"No PREFLIGHT for session {session_id[:8]}. Run PREFLIGHT first, then CHECK.", file=sys.stderr)
        sys.exit(2)

    # Check for CHECK with decision and timestamp
    cursor.execute("""
        SELECT know, uncertainty, reflex_data, timestamp
        FROM reflexes
        WHERE session_id = ? AND phase = 'CHECK'
        ORDER BY timestamp DESC LIMIT 1
    """, (session_id,))
    check_row = cursor.fetchone()
    db.close()

    if not check_row:
        print(f"No CHECK for session {session_id[:8]}. Run CHECK first.", file=sys.stderr)
        sys.exit(2)

    know, uncertainty, reflex_data, timestamp = check_row

    # Parse decision from reflex_data
    decision = None
    if reflex_data:
        try:
            data = json.loads(reflex_data)
            decision = data.get('decision')
        except Exception:
            pass

    # Check if decision was "investigate"
    if decision == 'investigate':
        print(f"Last CHECK returned 'investigate'. Complete investigation before {tool_name}.", file=sys.stderr)
        sys.exit(2)

    # Optional: Check age expiry (disabled by default - problematic for paused sessions)
    # Users may pause work and resume later; wall-clock time doesn't reflect actual activity
    check_time = None
    if os.getenv('EMPIRICA_SENTINEL_CHECK_EXPIRY', 'false').lower() == 'true':
        try:
            # Handle both ISO format and Unix timestamp (SQLite float)
            if isinstance(timestamp, (int, float)) or (isinstance(timestamp, str) and timestamp.replace('.', '').isdigit()):
                check_time = datetime.fromtimestamp(float(timestamp))
            else:
                check_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00').replace('+00:00', ''))
            age_minutes = (datetime.now() - check_time).total_seconds() / 60

            if age_minutes > MAX_CHECK_AGE_MINUTES:
                print(f"CHECK expired (age={age_minutes:.0f}min > {MAX_CHECK_AGE_MINUTES}min). Run CHECK first.", file=sys.stderr)
                sys.exit(2)
        except Exception as e:
            # Timestamp parsing failed - skip age check rather than blocking
            pass

    # Optional: Compact invalidation
    if os.getenv('EMPIRICA_SENTINEL_COMPACT_INVALIDATION', 'false').lower() == 'true':
        last_compact = get_last_compact_timestamp(project_root)
        if last_compact and check_time and last_compact > check_time:
            print(f"CHECK invalidated by compact. Run CHECK to recalibrate post-compact state.", file=sys.stderr)
            sys.exit(2)

    # Apply bias corrections and check thresholds
    corrected_know = (know or 0) + KNOW_BIAS
    corrected_unc = (uncertainty or 1) + UNCERTAINTY_BIAS

    if corrected_know >= KNOW_THRESHOLD and corrected_unc <= UNCERTAINTY_THRESHOLD:
        respond("allow", f"CHECK passed (know={corrected_know:.2f}, unc={corrected_unc:.2f})")
        sys.exit(0)
    else:
        print(f"CHECK failed: know={corrected_know:.2f} (need >=0.70), unc={corrected_unc:.2f} (need <=0.35)", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
