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
from typing import Optional

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
    # Empirica CLI: read-only commands only (tiered whitelist - see is_safe_empirica_command)
    # NOTE: State-changing empirica commands (preflight-submit, goals-create, etc.)
    # are handled separately in is_safe_empirica_command() with loop-state checks.
    # Blanket 'empirica ' whitelist removed to prevent prompt injection bypass.
    # Package inspection (not install)
    'pip show', 'pip list', 'pip freeze', 'pip index',
    'pip3 show', 'pip3 list', 'pip3 freeze', 'pip3 index',
    # Database inspection (read-only)
    'sqlite3 ',
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
# Blocks: ls; rm -rf, echo > file, etc.
# NOTE: Pipes handled separately - allowed only to safe targets
DANGEROUS_SHELL_OPERATORS = (
    ';',      # Command chaining
    '&&',     # Conditional AND
    '||',     # Conditional OR
    '`',      # Backtick command substitution
    '$(',     # Modern command substitution
    # NOTE: Redirection (>, >>, <) checked separately to allow safe patterns
)

# Safe redirection patterns (stderr suppression, etc.)
import re
SAFE_REDIRECT_PATTERN = re.compile(r'2>/dev/null|2>&1|>/dev/null|2>\s*/dev/null')

# Safe pipe targets - read-only commands that can receive piped input
# Allows: grep ... | head, cat ... | wc -l, etc.
SAFE_PIPE_TARGETS = (
    'head', 'tail', 'wc', 'sort', 'uniq', 'grep', 'rg', 'awk', 'sed -n',
    'cut', 'tr', 'less', 'more', 'cat', 'xargs echo', 'tee /dev/stderr',
    'python3 -c', 'python -c',  # For simple JSON parsing
)

# Thresholds for CHECK validation
# NOTE: Using RAW thresholds - bias corrections are FEEDBACK for AI to internalize,
# not silent adjustments. What AI sees in statusline = what sentinel evaluates.
KNOW_THRESHOLD = 0.70
UNCERTAINTY_THRESHOLD = 0.35
MAX_CHECK_AGE_MINUTES = 30


# Ask-before-investigate thresholds (from ask_before_investigate.yaml)
# Hardcoded to avoid YAML dependency in hook (hooks must be fast + minimal deps)
ASK_UNCERTAINTY_THRESHOLD = 0.65   # Uncertainty >= this triggers ask-first
ASK_CONTEXT_THRESHOLD = 0.50       # Context >= this means we CAN formulate questions
ASK_SIGNAL_THRESHOLD = 0.40        # Signal >= this means not completely lost

PAUSE_FILE = Path.home() / '.empirica' / 'sentinel_paused'


def is_empirica_paused() -> bool:
    """Check if Empirica tracking is paused (off-the-record mode).

    Signal file: ~/.empirica/sentinel_paused (JSON with timestamp, reason).
    This is the cheapest check - no DB needed. Called before any other logic.
    """
    return PAUSE_FILE.exists()


# Tiered Empirica CLI whitelist (replaces blanket 'empirica ' whitelist)
# Tier 1: Read-only commands - always safe, no state changes
EMPIRICA_TIER1_PREFIXES = (
    'empirica epistemics-list', 'empirica epistemics-show',
    'empirica goals-list', 'empirica get-goal-progress', 'empirica get-goal-subtasks',
    'empirica project-bootstrap', 'empirica project-search',
    'empirica session-snapshot', 'empirica get-session-summary',
    'empirica get-epistemic-state', 'empirica get-calibration-report',
    'empirica monitor', 'empirica check-drift',
    'empirica workspace-overview', 'empirica workspace-map',
    'empirica efficiency-report', 'empirica skill-suggest',
    'empirica goals-ready', 'empirica list-goals',
    'empirica query-mistakes', 'empirica query-handoff',
    'empirica discover-goals', 'empirica list-identities',
    'empirica issue-list',
    'empirica --help', 'empirica -h',
    'empirica version',
)

# Tier 2: State-changing commands - allowed (these ARE the epistemic workflow)
# These need to pass through to enable PREFLIGHT/CHECK/POSTFLIGHT and breadcrumbs.
# The Sentinel already gates praxic actions via vectors - these commands
# are HOW the AI satisfies those gates.
EMPIRICA_TIER2_PREFIXES = (
    'empirica preflight-submit', 'empirica check-submit', 'empirica postflight-submit',
    'empirica finding-log', 'empirica unknown-log', 'empirica deadend-log',
    'empirica mistake-log', 'empirica log-mistake',
    'empirica goals-create', 'empirica goals-complete', 'empirica goals-add-subtask',
    'empirica goals-complete-subtask', 'empirica goals-claim',
    'empirica session-create', 'empirica session-end',
    'empirica create-goal', 'empirica add-subtask', 'empirica complete-subtask',
    'empirica create-handoff', 'empirica resume-goal',
    'empirica unknown-resolve', 'empirica issue-handoff',
    'empirica project-init', 'empirica project-embed',
    'empirica create-git-checkpoint', 'empirica load-git-checkpoint',
    'empirica memory-compact', 'empirica resume-previous-session',
    'empirica agent-spawn', 'empirica investigate',
    'empirica refdoc-add',
)


def is_safe_empirica_command(command: str) -> bool:
    """Tiered whitelist for empirica CLI commands.

    Tier 1: Read-only (always allowed)
    Tier 2: State-changing (allowed - these are the epistemic workflow itself)

    Toggle operations are NOT whitelisted here - they use self-exemption
    in the main gate logic to prevent prompt injection bypass.
    """
    cmd = command.lstrip()
    if not cmd.startswith('empirica '):
        return False

    # Tier 1: Read-only - always safe
    for prefix in EMPIRICA_TIER1_PREFIXES:
        if cmd.startswith(prefix):
            return True

    # Tier 2: State-changing - allowed (these enable the workflow)
    for prefix in EMPIRICA_TIER2_PREFIXES:
        if cmd.startswith(prefix):
            return True

    return False


def is_toggle_command(command: str) -> Optional[str]:
    """Detect if a command is writing or removing the Sentinel pause file.

    Returns 'pause' if writing, 'unpause' if removing, None otherwise.
    This enables Sentinel self-exemption for the toggle without
    whitelisting it as a general safe command.
    """
    cmd = command.lstrip()

    # Detect pause file write (python3 -c "..." writing sentinel_paused)
    if 'sentinel_paused' in cmd and ('write_text' in cmd or 'open(' in cmd):
        return 'pause'

    # Detect pause file removal
    if cmd.startswith('rm ') and ('sentinel_paused' in cmd):
        return 'unpause'

    return None


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


def find_empirica_package() -> Optional[Path]:
    """Find where empirica package can be imported from.

    This is ONLY for setting up sys.path to enable imports.
    Actual path resolution (DB location, etc.) is delegated to
    empirica.config.path_resolver after import.

    Returns:
        Path to add to sys.path, or None if empirica is already importable.
    """
    # Check if already importable (pip installed)
    try:
        import empirica.config.path_resolver
        return None  # Already available, no path needed
    except ImportError:
        pass

    # Search for empirica package in known development locations
    def has_empirica_package(path: Path) -> bool:
        return (path / 'empirica' / '__init__.py').exists()

    # Check cwd and parents first (respect project context)
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if has_empirica_package(parent):
            return parent
        if parent == parent.parent:
            break

    # Fallback to known dev paths
    known_paths = [
        Path.home() / 'empirical-ai' / 'empirica',
        Path.home() / 'empirica',
    ]
    for path in known_paths:
        if has_empirica_package(path):
            return path

    return None


def _get_current_project_id() -> Optional[str]:
    """Get project_id from current working directory's git repo."""
    import subprocess
    import hashlib
    try:
        # Get git remote origin URL as project identifier
        result = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            url = result.stdout.strip()
            return hashlib.sha256(url.encode()).hexdigest()[:16]

        # Fallback: use git root directory name
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            path = result.stdout.strip()
            return hashlib.sha256(path.encode()).hexdigest()[:16]
    except Exception:
        pass
    return None


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

    # EMPIRICA CLI: Tiered whitelist (not blanket - prevents prompt injection bypass)
    if is_safe_empirica_command(command):
        return True

    # Check for dangerous shell operators (command injection prevention)
    # This blocks: ls; rm -rf, echo > file, etc.
    for operator in DANGEROUS_SHELL_OPERATORS:
        if operator in command:
            return False

    # Check for file redirection (dangerous) vs stderr suppression (safe)
    # Strip safe patterns first, then check for remaining redirects
    cmd_without_safe_redirects = SAFE_REDIRECT_PATTERN.sub('', command)
    if '>' in cmd_without_safe_redirects or '>>' in cmd_without_safe_redirects:
        return False  # Actual file redirection - not safe
    if '<' in cmd_without_safe_redirects:
        # Allow heredocs for safe commands (empirica already handled above)
        if '<<' not in command:
            return False  # Input redirection from file - not safe

    # Handle pipes specially - allow if all segments are safe
    if '|' in command:
        return is_safe_pipe_chain(command)

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


def is_safe_pipe_chain(command: str) -> bool:
    """
    Check if a piped command chain is safe (all segments are read-only).

    Allows: grep pattern file | head -20 | wc -l
    Blocks: grep pattern | xargs rm, cat file | bash
    """
    segments = [s.strip() for s in command.split('|')]

    if not segments:
        return False

    # First segment must be a safe command
    first_cmd = segments[0]
    first_is_safe = False
    for prefix in SAFE_BASH_PREFIXES:
        if first_cmd.startswith(prefix) or (prefix.endswith(' ') and first_cmd == prefix.rstrip()):
            first_is_safe = True
            break

    if not first_is_safe:
        return False

    # All subsequent segments must start with safe pipe targets
    for segment in segments[1:]:
        segment_safe = False
        for target in SAFE_PIPE_TARGETS:
            if segment.startswith(target):
                segment_safe = True
                break
        if not segment_safe:
            return False

    return True


def _get_preflight_context(cursor, session_id: str) -> float:
    """Extract context vector from PREFLIGHT reflex_data.

    Returns the context score (0.0-1.0) from the most recent PREFLIGHT.
    Falls back to 0.0 if not available.
    """
    try:
        cursor.execute("""
            SELECT reflex_data FROM reflexes
            WHERE session_id = ? AND phase = 'PREFLIGHT'
            ORDER BY timestamp DESC LIMIT 1
        """, (session_id,))
        row = cursor.fetchone()
        if row and row[0]:
            data = json.loads(row[0])
            vectors = data.get('vectors', {})
            return float(vectors.get('context', 0.0))
    except Exception:
        pass
    return 0.0


def _get_check_context(reflex_data: Optional[str]) -> float:
    """Extract context vector from CHECK reflex_data.

    Returns the context score (0.0-1.0) from CHECK data.
    Falls back to 0.0 if not available.
    """
    if not reflex_data:
        return 0.0
    try:
        data = json.loads(reflex_data)
        vectors = data.get('vectors', {})
        return float(vectors.get('context', 0.0))
    except Exception:
        return 0.0


def _check_ask_before_investigate(know: float, uncertainty: float, context: float) -> Optional[str]:
    """Check if vectors match ask-before-investigate thresholds.

    Returns an escalation message if the AI should ask the user first,
    or None if normal flow should continue.

    Triggers when:
    - Uncertainty is high (>= 0.65) - significant doubt
    - Context is sufficient (>= 0.50) - enough info to formulate questions
    - Know is below gate (< 0.70) - not ready to proceed

    This prevents wasteful investigation loops when the AI has enough
    context to ask targeted questions instead.
    """
    if (uncertainty >= ASK_UNCERTAINTY_THRESHOLD
            and context >= ASK_CONTEXT_THRESHOLD
            and know < KNOW_THRESHOLD):
        return (
            f"ESCALATE: High uncertainty ({uncertainty:.2f}) with sufficient context ({context:.2f}). "
            f"Ask the user before investigating. You have enough context to formulate specific questions. "
            f"Use AskUserQuestion to clarify approach, then CHECK again."
        )
    return None


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

    # OFF-RECORD CHECK: If Empirica is paused, allow everything (cheapest check first)
    if is_empirica_paused():
        respond("allow", "Empirica paused (off-record)")
        sys.exit(0)

    # Check if sentinel looping is disabled (escape hatch)
    if os.getenv('EMPIRICA_SENTINEL_LOOPING', 'true').lower() == 'false':
        respond("allow", "Sentinel disabled")
        sys.exit(0)

    # === AUTHORIZATION CHECK ===

    # Setup imports - find empirica package if not already installed
    package_path = find_empirica_package()
    if package_path:
        sys.path.insert(0, str(package_path))

    # Import path_resolver for canonical path resolution
    try:
        from empirica.config.path_resolver import get_empirica_root
    except ImportError as e:
        respond("allow", f"Cannot import path_resolver: {e}")
        sys.exit(0)

    # Change to the resolved empirica root (for relative paths in DB)
    empirica_root = get_empirica_root()
    if empirica_root.exists():
        os.chdir(empirica_root.parent)  # .empirica's parent is project root

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

    # SessionDatabase uses path_resolver internally for DB location
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
    # Include project_id to check for project context switches
    cursor.execute("""
        SELECT know, uncertainty, timestamp, project_id FROM reflexes
        WHERE session_id = ? AND phase = 'PREFLIGHT'
        ORDER BY timestamp DESC LIMIT 1
    """, (session_id,))
    preflight_row = cursor.fetchone()

    if not preflight_row:
        db.close()
        respond("deny", f"No PREFLIGHT. Assess your knowledge state first.")
        sys.exit(0)

    preflight_know, preflight_uncertainty, preflight_timestamp, preflight_project_id = preflight_row

    # PROJECT CONTEXT CHECK: Require new PREFLIGHT if project changed
    # This implicitly closes the previous project's epistemic loop
    current_project_id = _get_current_project_id()
    if current_project_id and preflight_project_id and current_project_id != preflight_project_id:
        # Check if previous project loop was properly closed with POSTFLIGHT
        cursor.execute("""
            SELECT timestamp FROM reflexes
            WHERE session_id = ? AND phase = 'POSTFLIGHT' AND project_id = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (session_id, preflight_project_id))
        prev_postflight = cursor.fetchone()

        db.close()
        if prev_postflight:
            respond("deny", f"Project context changed. Run PREFLIGHT for new project.")
        else:
            respond("deny", f"Project context changed (previous loop unclosed - consider POSTFLIGHT). Run PREFLIGHT for new project.")
        sys.exit(0)

    # POSTFLIGHT LOOP CHECK: If POSTFLIGHT exists after PREFLIGHT, loop is closed
    # This enforces the epistemic cycle: PREFLIGHT → work → POSTFLIGHT → (new PREFLIGHT required)
    cursor.execute("""
        SELECT timestamp FROM reflexes
        WHERE session_id = ? AND phase = 'POSTFLIGHT'
        ORDER BY timestamp DESC LIMIT 1
    """, (session_id,))
    postflight_row = cursor.fetchone()

    if postflight_row:
        postflight_timestamp = postflight_row[0]
        try:
            preflight_ts = float(preflight_timestamp)
            postflight_ts = float(postflight_timestamp)

            if postflight_ts > preflight_ts:
                # SELF-EXEMPTION: Allow toggle commands when loop is closed
                # This is the only way to write/remove the pause file.
                # Prevents prompt injection: toggle ONLY works when loop is genuinely closed.
                if tool_name == 'Bash':
                    toggle_action = is_toggle_command(tool_input.get('command', ''))
                    if toggle_action == 'pause':
                        db.close()
                        respond("allow", "Sentinel self-exemption: pause toggle (loop closed)")
                        sys.exit(0)
                    elif toggle_action == 'unpause':
                        db.close()
                        respond("allow", "Sentinel self-exemption: unpause toggle")
                        sys.exit(0)

                db.close()
                respond("deny", f"Epistemic loop closed (POSTFLIGHT completed). Run new PREFLIGHT to start next goal.")
                sys.exit(0)
        except (ValueError, TypeError):
            pass  # If timestamps can't be compared, continue with other checks

    # Use RAW vectors - bias corrections are feedback for AI to internalize, not silent adjustments
    raw_know = preflight_know or 0
    raw_unc = preflight_uncertainty or 1

    # AUTO-PROCEED: If PREFLIGHT passes readiness gate, skip CHECK requirement
    if raw_know >= KNOW_THRESHOLD and raw_unc <= UNCERTAINTY_THRESHOLD:
        db.close()
        respond("allow", f"PREFLIGHT passed gate (know={raw_know:.2f}, unc={raw_unc:.2f}) - auto-proceed")
        sys.exit(0)

    # ESCALATION CHECK: High uncertainty but context exists → ask user first
    # Uses ask_before_investigate.yaml thresholds (loaded from MCO config)
    preflight_context = _get_preflight_context(cursor, session_id)
    escalation = _check_ask_before_investigate(raw_know, raw_unc, preflight_context)
    if escalation:
        db.close()
        respond("deny", escalation)
        sys.exit(0)

    # PREFLIGHT confidence too low - require explicit CHECK
    cursor.execute("""
        SELECT know, uncertainty, reflex_data, timestamp
        FROM reflexes
        WHERE session_id = ? AND phase = 'CHECK'
        ORDER BY timestamp DESC LIMIT 1
    """, (session_id,))
    check_row = cursor.fetchone()
    # NOTE: db kept open - reused for anti-gaming check below (single connection per invocation)

    if not check_row:
        respond("deny", f"Insufficient understanding (know={raw_know:.2f}, unc={raw_unc:.2f}). Investigate before acting.")
        sys.exit(0)

    know, uncertainty, reflex_data, check_timestamp = check_row

    # Verify CHECK is after PREFLIGHT (proper sequence)
    try:
        preflight_ts = float(preflight_timestamp)
        check_ts = float(check_timestamp)

        if check_ts < preflight_ts:
            respond("deny", f"Assessment sequence invalid. Start fresh noetic phase.")
            sys.exit(0)

        # Anti-gaming: Minimum noetic duration with evidence check
        # If CHECK is very fast (<30s) AND no evidence of investigation, reject
        noetic_duration = check_ts - preflight_ts
        MIN_NOETIC_DURATION = float(os.getenv('EMPIRICA_MIN_NOETIC_DURATION', '30'))

        if noetic_duration < MIN_NOETIC_DURATION:
            # Check for evidence of investigation (findings or unknowns logged)
            # Reuse existing db connection (single connection per sentinel invocation)
            cursor.execute("""
                SELECT COUNT(*) FROM project_findings
                WHERE session_id = ? AND timestamp > ? AND timestamp < ?
            """, (session_id, preflight_ts, check_ts))
            findings_count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM project_unknowns
                WHERE session_id = ? AND timestamp > ? AND timestamp < ?
            """, (session_id, preflight_ts, check_ts))
            unknowns_count = cursor.fetchone()[0]

            if findings_count == 0 and unknowns_count == 0:
                respond("deny", f"Rushed assessment ({noetic_duration:.0f}s). Investigate and log learnings first.")
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
        # ESCALATION: If ask-before-investigate thresholds match, suggest asking
        check_know = know or 0
        check_unc = uncertainty or 1
        check_context = _get_check_context(reflex_data)
        escalation = _check_ask_before_investigate(check_know, check_unc, check_context)
        if escalation:
            respond("deny", escalation)
        else:
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
        last_compact = get_last_compact_timestamp(empirica_root.parent)
        if last_compact and check_time and last_compact > check_time:
            respond("deny", "Context compacted. Recalibrate with fresh CHECK.")
            sys.exit(0)

    # Use RAW vectors - what AI sees = what sentinel evaluates
    raw_check_know = know or 0
    raw_check_unc = uncertainty or 1

    if raw_check_know >= KNOW_THRESHOLD and raw_check_unc <= UNCERTAINTY_THRESHOLD:
        respond("allow", f"CHECK passed (know={raw_check_know:.2f}, unc={raw_check_unc:.2f})")
        sys.exit(0)
    else:
        respond("deny", f"Insufficient confidence: know={raw_check_know:.2f}, uncertainty={raw_check_unc:.2f}. Investigate more.")
        sys.exit(0)


if __name__ == '__main__':
    main()
