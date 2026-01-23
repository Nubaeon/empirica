#!/usr/bin/env python3
"""
Empirica Sentinel Gate - Noetic Firewall with Epistemic ACLs

Implements least-privilege principle for AI tool access:
- NOETIC tools (read/investigate) → always allowed
- PRAXIC tools (write/execute) → require PREFLIGHT, auto-proceed if confident

This is essentially iptables for cognition - default deny, explicit allow.

Core features (always on):
- Smart project root discovery (env var, known paths, cwd search)
- Noetic tool whitelist (Read, Grep, Glob, etc.)
- Safe Bash command whitelist (ls, cat, git status, etc.)
- PREFLIGHT required for praxic actions (epistemic assessment)
- AUTO-PROCEED: If PREFLIGHT passes gate (know >= 0.70, unc <= 0.35), skip CHECK
- LOW-CONFIDENCE: If PREFLIGHT fails gate, explicit CHECK required
- Decision parsing (blocks if CHECK returned "investigate")

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

# Noetic tools - read/investigate/search - always allowed (whitelist)
NOETIC_TOOLS = {
    'Read', 'Glob', 'Grep', 'LSP',           # File inspection
    'WebFetch', 'WebSearch',                  # Web research
    'Task', 'TaskOutput',                     # Agent delegation
    'TodoWrite',                              # Planning
    'AskUserQuestion',                        # User interaction
    'Skill',                                  # Skill invocation
    'KillShell',                              # Process management (cleanup)
}

# Safe Bash command prefixes - read-only operations (ACL)
SAFE_BASH_PREFIXES = (
    # File inspection
    'cat ', 'head ', 'tail ', 'less ', 'more ',
    'ls', 'ls ', 'dir ', 'tree ', 'file ', 'stat ', 'wc ',
    'find ', 'locate ', 'which ', 'type ', 'whereis ',
    # Text search/processing (read-only)
    'grep ', 'rg ', 'ag ', 'ack ', 'sed -n', 'awk ',
    # Git read operations
    'git status', 'git log', 'git diff', 'git show', 'git branch',
    'git remote', 'git tag', 'git stash list', 'git blame',
    'git ls-files', 'git ls-tree', 'git cat-file',
    # Environment inspection
    'pwd', 'echo ', 'printf ', 'env', 'printenv', 'set',
    'whoami', 'id', 'hostname', 'uname', 'date', 'cal',
    # Empirica CLI (has its own auth)
    'empirica ',
    # Package inspection (not install)
    'pip show', 'pip list', 'pip freeze', 'pip index',
    'npm list', 'npm ls', 'npm view', 'npm info',
    'cargo tree', 'cargo metadata',
    # Process inspection
    'ps ', 'top -b -n 1', 'pgrep ', 'jobs',
    # Disk inspection
    'df ', 'du ', 'mount', 'lsblk',
    # Network inspection (not modification)
    'curl ', 'wget -O-', 'ping -c', 'dig ', 'nslookup ', 'host ',
    # Documentation
    'man ', 'info ', 'help ',
    # Testing (read-only check)
    'test ', '[ ',
)

# Dangerous shell operators (command injection prevention)
# Blocks: ls; rm -rf, cat file | malicious, echo > file, etc.
DANGEROUS_SHELL_OPERATORS = (
    ';',      # Command chaining
    '&&',     # Conditional AND
    '||',     # Conditional OR
    '|',      # Pipe (could send to malicious command)
    '`',      # Backtick command substitution
    '$(',     # Modern command substitution
    '>',      # Output redirection
    '>>',     # Append redirection
    '<',      # Input redirection
)

# Thresholds for CHECK validation
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


def is_safe_bash_command(tool_input: dict) -> bool:
    """Check if a Bash command is in the safe (noetic) whitelist."""
    command = tool_input.get('command', '')
    if not command:
        return False

    # Check for dangerous shell operators (command injection prevention)
    # This blocks: ls; rm -rf, cat file | malicious, echo > file, etc.
    for operator in DANGEROUS_SHELL_OPERATORS:
        if operator in command:
            return False

    # Strip leading whitespace and check against safe prefixes
    command_stripped = command.lstrip()

    # Check if command starts with any safe prefix
    for prefix in SAFE_BASH_PREFIXES:
        if command_stripped.startswith(prefix):
            return True
        # Also check without trailing space for commands like 'ls', 'pwd'
        if prefix.endswith(' ') and command_stripped == prefix.rstrip():
            return True

    return False


def main():
    try:
        hook_input = json.loads(sys.stdin.read() or '{}')
    except Exception:
        hook_input = {}

    tool_name = hook_input.get('tool_name', 'unknown')
    tool_input = hook_input.get('tool_input', {})

    # === NOETIC FIREWALL: Whitelist-based access control ===

    # Rule 1: Noetic tools always allowed (read/investigate)
    if tool_name in NOETIC_TOOLS:
        respond("allow", f"Noetic tool: {tool_name}")
        sys.exit(0)

    # Rule 2: Safe Bash commands always allowed (read-only shell)
    if tool_name == 'Bash' and is_safe_bash_command(tool_input):
        respond("allow", "Safe Bash (read-only)")
        sys.exit(0)

    # Rule 3: Everything else is PRAXIC - requires CHECK authorization
    # This includes: Edit, Write, NotebookEdit, unsafe Bash, unknown tools

    # Check if sentinel looping is disabled (escape hatch)
    if os.getenv('EMPIRICA_SENTINEL_LOOPING', 'true').lower() == 'false':
        respond("allow", "Sentinel disabled")
        sys.exit(0)

    # === AUTHORIZATION CHECK ===

    # Setup paths - smart discovery
    project_root = find_project_root()
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))

    # Get active session
    session_id = None
    try:
        from empirica.utils.session_resolver import get_latest_session_id
        session_id = get_latest_session_id(ai_id='claude-code', active_only=True)
    except ValueError as e:
        # No session found - this is expected when no active session exists
        if "No session found" in str(e):
            respond("allow", "WARNING: No active Empirica session. Run 'empirica session-create --ai-id claude-code' for epistemic tracking.")
            sys.exit(0)
        # Other ValueError - treat as resolver issue
        respond("allow", f"Session resolver error: {e}")
        sys.exit(0)
    except Exception as e:
        respond("allow", f"No session resolver: {e}")
        sys.exit(0)

    if not session_id:
        # Shouldn't reach here, but handle gracefully
        respond("allow", "WARNING: No active Empirica session. Run 'empirica session-create --ai-id claude-code' for epistemic tracking.")
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
            respond("deny", f"No bootstrap for {session_id[:8]}. Run: empirica project-bootstrap")
            sys.exit(0)

    # Check for PREFLIGHT (authentication) - with vectors for auto-proceed
    cursor.execute("""
        SELECT know, uncertainty, timestamp FROM reflexes
        WHERE session_id = ? AND phase = 'PREFLIGHT'
        ORDER BY timestamp DESC LIMIT 1
    """, (session_id,))
    preflight_row = cursor.fetchone()

    if not preflight_row:
        db.close()
        respond("deny", f"No PREFLIGHT. Assess your knowledge state first.")
        sys.exit(0)

    preflight_know, preflight_uncertainty, preflight_timestamp = preflight_row

    # Apply bias corrections to PREFLIGHT vectors
    corrected_preflight_know = (preflight_know or 0) + KNOW_BIAS
    corrected_preflight_unc = (preflight_uncertainty or 1) + UNCERTAINTY_BIAS

    # AUTO-PROCEED: If PREFLIGHT passes readiness gate, skip CHECK requirement
    if corrected_preflight_know >= KNOW_THRESHOLD and corrected_preflight_unc <= UNCERTAINTY_THRESHOLD:
        db.close()
        respond("allow", f"PREFLIGHT passed gate (know={corrected_preflight_know:.2f}, unc={corrected_preflight_unc:.2f}) - auto-proceed")
        sys.exit(0)

    # PREFLIGHT confidence too low - require explicit CHECK
    cursor.execute("""
        SELECT know, uncertainty, reflex_data, timestamp
        FROM reflexes
        WHERE session_id = ? AND phase = 'CHECK'
        ORDER BY timestamp DESC LIMIT 1
    """, (session_id,))
    check_row = cursor.fetchone()
    db.close()

    if not check_row:
        respond("deny", f"Low confidence (know={corrected_preflight_know:.2f}, unc={corrected_preflight_unc:.2f}). Submit CHECK to verify readiness.")
        sys.exit(0)

    know, uncertainty, reflex_data, check_timestamp = check_row

    # Verify CHECK is after PREFLIGHT (proper sequence)
    try:
        if float(check_timestamp) < float(preflight_timestamp):
            respond("deny", f"CHECK predates PREFLIGHT. Reassess with fresh CHECK.")
            sys.exit(0)
    except (TypeError, ValueError):
        pass  # Can't compare timestamps, skip this check

    # Parse decision from reflex_data
    decision = None
    if reflex_data:
        try:
            data = json.loads(reflex_data)
            decision = data.get('decision')
        except Exception:
            pass

    # Check if decision was "investigate" (not authorized for praxic)
    if decision == 'investigate':
        respond("deny", f"CHECK returned 'investigate'. Continue noetic phase first.")
        sys.exit(0)

    # Optional: Check age expiry
    check_time = None
    if os.getenv('EMPIRICA_SENTINEL_CHECK_EXPIRY', 'false').lower() == 'true':
        try:
            if isinstance(check_timestamp, (int, float)) or (isinstance(check_timestamp, str) and check_timestamp.replace('.', '').isdigit()):
                check_time = datetime.fromtimestamp(float(check_timestamp))
            else:
                check_time = datetime.fromisoformat(check_timestamp.replace('Z', '+00:00').replace('+00:00', ''))
            age_minutes = (datetime.now() - check_time).total_seconds() / 60

            if age_minutes > MAX_CHECK_AGE_MINUTES:
                respond("deny", f"CHECK expired ({age_minutes:.0f}min). Refresh epistemic state.")
                sys.exit(0)
        except Exception:
            pass

    # Optional: Compact invalidation
    if os.getenv('EMPIRICA_SENTINEL_COMPACT_INVALIDATION', 'false').lower() == 'true':
        last_compact = get_last_compact_timestamp(project_root)
        if last_compact and check_time and last_compact > check_time:
            respond("deny", "Context compacted. Recalibrate with fresh CHECK.")
            sys.exit(0)

    # Apply bias corrections and check thresholds
    corrected_know = (know or 0) + KNOW_BIAS
    corrected_unc = (uncertainty or 1) + UNCERTAINTY_BIAS

    if corrected_know >= KNOW_THRESHOLD and corrected_unc <= UNCERTAINTY_THRESHOLD:
        respond("allow", f"CHECK passed (know={corrected_know:.2f}, unc={corrected_unc:.2f})")
        sys.exit(0)
    else:
        respond("deny", f"Insufficient confidence: know={corrected_know:.2f}, uncertainty={corrected_unc:.2f}. Investigate more.")
        sys.exit(0)


if __name__ == '__main__':
    main()
