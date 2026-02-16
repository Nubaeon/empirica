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

# Add lib folder to path for shared modules
_lib_path = Path(__file__).parent.parent / 'lib'
if str(_lib_path) not in sys.path:
    sys.path.insert(0, str(_lib_path))

from project_resolver import get_active_project_path, get_instance_id, get_active_session_id

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
    # Text/data search/processing (read-only)
    'grep ', 'rg ', 'ag ', 'ack ', 'sed -n', 'awk ',
    'jq ', 'jq.',  # JSON processing (read-only)
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
    'npm list', 'npm ls', 'npm view', 'npm info',
    'cargo tree', 'cargo metadata',
    # Process inspection
    'ps ', 'top -b -n 1', 'pgrep ', 'jobs',
    # Terminal/tmux inspection (read-only)
    'tmux capture-pane', 'tmux list-panes', 'tmux list-windows',
    'tmux list-sessions', 'tmux display-message', 'tmux show-option',
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
    'jq', 'jq ',  # JSON processing (read-only)
)

# Thresholds for CHECK validation
# NOTE: Using RAW thresholds - bias corrections are FEEDBACK for AI to internalize,
# not silent adjustments. What AI sees in statusline = what sentinel evaluates.
KNOW_THRESHOLD = 0.70
UNCERTAINTY_THRESHOLD = 0.35
MAX_CHECK_AGE_MINUTES = 30

# Transition commands - allowed after POSTFLIGHT to enable new cycle
# These are the commands needed to properly switch projects or start new sessions
TRANSITION_COMMANDS = (
    'cd ',                           # Directory change (project switch)
    'empirica session-create',       # New session
    'empirica project-bootstrap',    # Bootstrap new project context
    'empirica project-init',         # Initialize new project
    'empirica project-switch',       # Switch active project context
    'empirica project-list',         # List available projects
    'empirica preflight-submit',     # Start new epistemic cycle (was missing = chicken-and-egg bug)
    'git add',                       # Stage work from completed transaction
    'git commit',                    # Commit work from completed transaction
)


PAUSE_FILE_BASE = Path.home() / '.empirica'
PAUSE_FILE_GLOBAL = PAUSE_FILE_BASE / 'sentinel_paused'


def get_pause_file_path() -> Path:
    """Get instance-specific pause file path.

    Returns ~/.empirica/sentinel_paused_{instance_id} for per-instance control.
    Falls back to ~/.empirica/sentinel_paused global file if no instance_id.
    """
    instance_id = get_instance_id()
    if instance_id:
        # Sanitize instance_id for filename (remove special chars)
        safe_id = instance_id.replace('/', '-').replace('%', '')
        return PAUSE_FILE_BASE / f'sentinel_paused_{safe_id}'
    return PAUSE_FILE_GLOBAL


def get_instance_id() -> Optional[str]:
    """Get instance identifier for multi-Claude isolation.

    Priority: TMUX_PANE (works in hooks) > TTY (works in CLI).
    Returns None if neither available.
    """
    try:
        tmux_pane = os.environ.get('TMUX_PANE')
        if tmux_pane:
            return f"tmux_{tmux_pane.lstrip('%')}"
        # Fallback to TTY for non-tmux users
        import subprocess
        result = subprocess.run(['tty'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            tty = result.stdout.strip()
            if tty and tty != 'not a tty':
                return tty.replace('/dev/', '').replace('/', '-')
    except Exception:
        pass
    return None


def is_empirica_paused() -> bool:
    """Check if Empirica tracking is paused (off-the-record mode).

    Checks instance-specific pause file first, then global.
    Instance: ~/.empirica/sentinel_paused_{instance_id}
    Global:   ~/.empirica/sentinel_paused

    This is the cheapest check - no DB needed. Called before any other logic.
    """
    # Check instance-specific pause file first
    instance_pause = get_pause_file_path()
    if instance_pause.exists():
        return True
    # Fallback to global pause (backward compat, also allows pausing ALL instances)
    return PAUSE_FILE_GLOBAL.exists()


# Tiered Empirica CLI whitelist (replaces blanket 'empirica ' whitelist)
# Tier 1: Read-only commands - always safe, no state changes
# Also includes administrative commands (project-switch, project-list) that should always be allowed
EMPIRICA_TIER1_PREFIXES = (
    'empirica epistemics-list', 'empirica epistemics-show',
    'empirica goals-list', 'empirica goal-list', 'empirica gl',  # Goal list + aliases
    'empirica goals-progress', 'empirica goal-progress',  # Goal progress + alias
    'empirica get-goal-progress', 'empirica get-goal-subtasks', 'empirica goals-get-subtasks',
    'empirica goals-discover', 'empirica goal-analysis',  # Goal queries
    'empirica project-bootstrap', 'empirica project-search',
    'empirica project-switch', 'empirica project-list',  # Administrative - always allowed
    'empirica session-snapshot', 'empirica get-session-summary',
    'empirica get-epistemic-state', 'empirica get-calibration-report',
    'empirica monitor', 'empirica check-drift',
    'empirica workspace-overview', 'empirica workspace-map',
    'empirica efficiency-report', 'empirica skill-suggest',
    'empirica goals-ready', 'empirica list-goals',
    'empirica query-mistakes', 'empirica query-handoff',
    'empirica discover-goals', 'empirica list-identities',
    'empirica issue-list',
    'empirica docs-assess',  # Documentation assessment - read-only investigation tool
    'empirica calibration-report',  # Calibration analysis - read-only
    'empirica lesson-list', 'empirica lesson-search', 'empirica lesson-recommend',
    'empirica lesson-stats',  # Lesson queries - read-only
    'empirica sentinel-status', 'empirica sentinel-check',  # Sentinel queries - read-only
    'empirica goals-search', 'empirica goals-get-stale',  # Goal queries - read-only
    'empirica workspace-list', 'empirica ecosystem-check',  # Workspace queries - read-only
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
    'empirica goals-create', 'empirica goal-create', 'empirica gc',  # Goal create + aliases
    'empirica goals-complete', 'empirica goal-complete',  # Goal complete + alias
    'empirica goals-add-subtask', 'empirica goal-add-subtask',  # Add subtask + alias
    'empirica goals-complete-subtask', 'empirica goal-complete-subtask',  # Complete subtask + alias
    'empirica goals-add-dependency', 'empirica goals-resume',  # Goal management
    'empirica goals-claim',
    'empirica session-create', 'empirica session-end',
    'empirica create-goal', 'empirica add-subtask', 'empirica complete-subtask',
    'empirica create-handoff', 'empirica resume-goal',
    'empirica unknown-resolve', 'empirica issue-handoff',
    'empirica project-init', 'empirica project-embed',
    'empirica create-git-checkpoint', 'empirica load-git-checkpoint',
    'empirica memory-compact', 'empirica resume-previous-session',
    'empirica agent-spawn', 'empirica investigate',
    'empirica refdoc-add', 'empirica source-add',
    'empirica assumption-log', 'empirica decision-log',  # Noetic artifacts - assumptions/decisions
    'empirica lesson-create', 'empirica lesson-load', 'empirica lesson-path',
    'empirica lesson-replay-start', 'empirica lesson-replay-end',
    'empirica lesson-embed',  # Lesson lifecycle commands
    'empirica sentinel-orchestrate', 'empirica sentinel-load-profile',  # Sentinel management
    'empirica artifacts-generate',  # Artifact generation
    'empirica goals-mark-stale', 'empirica goals-refresh',  # Goal staleness management
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


def is_transition_command(command: str) -> bool:
    """Check if command is a transition command (allowed after POSTFLIGHT).

    Transition commands enable starting a new epistemic cycle:
    - cd to switch projects
    - session-create to start new session
    - project-bootstrap/init for new project context

    These are allowed after POSTFLIGHT to prevent the chicken-and-egg
    problem where you can't switch projects without a new PREFLIGHT,
    but can't create a PREFLIGHT in the new project without switching.

    Also handles piped and chained commands:
    - echo '...' | empirica preflight-submit -
    - cat file | empirica preflight-submit -
    - cd /path && empirica preflight-submit - << 'EOF'
    """
    cmd = command.lstrip()

    # Direct match
    for prefix in TRANSITION_COMMANDS:
        if cmd.startswith(prefix):
            return True

    # Check pipe segments: echo '...' | empirica preflight-submit -
    if '|' in cmd:
        for segment in cmd.split('|'):
            segment = segment.strip()
            for prefix in TRANSITION_COMMANDS:
                if segment.startswith(prefix):
                    return True

    # Check && chain segments: cd /path && empirica preflight-submit -
    if '&&' in cmd:
        for segment in cmd.split('&&'):
            segment = segment.strip()
            # Strip heredoc suffix for matching
            segment_clean = segment.split('<<')[0].strip() if '<<' in segment else segment
            for prefix in TRANSITION_COMMANDS:
                if segment_clean.startswith(prefix):
                    return True

    return False


def respond(decision: str, reason: str = "") -> None:
    """Output in Claude Code's expected format."""
    output: dict = {
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


def resolve_project_root(claude_session_id: Optional[str] = None) -> Optional[Path]:
    """Resolve the correct project root using the shared project_resolver.

    Uses canonical get_active_project_path() from lib/project_resolver.py.
    NO CWD FALLBACK - fails explicitly if instance-aware mechanisms don't work.

    Args:
        claude_session_id: Claude Code conversation UUID from hook input

    Returns:
        Path to project root (parent of .empirica), or None if not found.
    """
    project_path = get_active_project_path(claude_session_id)
    if project_path:
        project_root = Path(project_path)
        if (project_root / '.empirica').exists():
            return project_root
    return None


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
        import empirica.config.path_resolver  # type: ignore[import-not-found]
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


def _get_current_project_id(db_conn, session_id: str) -> Optional[str]:
    """Get project_id from session table (authoritative source).

    The session table stores the project_id that was resolved at session
    creation time. This is the SAME project_id that gets stored in reflexes
    table via store_vectors().

    Args:
        db_conn: Database connection
        session_id: Session UUID to look up

    Returns:
        project_id (UUID) from the session, or None
    """
    try:
        cursor = db_conn.execute(
            "SELECT project_id FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        if row and row[0]:
            return row[0]
    except Exception:
        pass
    return None


def get_last_compact_timestamp(project_root: Path) -> Optional[datetime]:
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

    # Special case: && and || chains where ALL segments are safe (noetic)
    # This allows: cd /path && grep ..., tmux capture-pane || echo "fallback"
    for chain_op in ('&&', '||'):
        if chain_op in command:
            segments = [s.strip() for s in command.split(chain_op)]
            all_segments_safe = True
            for segment in segments:
                # Strip heredoc suffix for matching
                segment_clean = segment.split('<<')[0].strip() if '<<' in segment else segment
                # Strip safe redirects for matching (2>/dev/null, 2>&1)
                segment_clean = SAFE_REDIRECT_PATTERN.sub('', segment_clean).strip()
                # Check if segment is: cd, safe empirica, or starts with safe prefix
                if segment_clean.startswith('cd '):
                    continue  # cd is always safe
                if is_safe_empirica_command(segment_clean):
                    continue  # empirica tier1/tier2 commands are safe
                # Check against SAFE_BASH_PREFIXES (grep, cat, ls, git status, etc.)
                segment_is_safe = False
                for prefix in SAFE_BASH_PREFIXES:
                    if segment_clean.startswith(prefix) or (prefix.endswith(' ') and segment_clean == prefix.rstrip()):
                        segment_is_safe = True
                        break
                if not segment_is_safe:
                    all_segments_safe = False
                    break
            if all_segments_safe:
                return True

    # Check for dangerous shell operators (command injection prevention)
    # This blocks: ls; rm -rf, echo > file, etc.
    # NOTE: && and || are handled above for safe chains, so we skip them here
    for operator in DANGEROUS_SHELL_OPERATORS:
        if operator in ('&&', '||'):
            continue  # Already handled above - only block if chain wasn't all-safe
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

    # Special case: sqlite3 read-only queries (noetic DB access)
    if command_stripped.startswith('sqlite3 '):
        if is_safe_sqlite_command(command_stripped):
            return True

    # Check if command starts with any safe prefix
    for prefix in SAFE_BASH_PREFIXES:
        if command_stripped.startswith(prefix):
            return True
        # Also check without trailing space for commands like 'ls', 'pwd'
        if prefix.endswith(' ') and command_stripped == prefix.rstrip():
            return True

    return False


def is_safe_sqlite_command(command: str) -> bool:
    """
    Check if a sqlite3 command is read-only (noetic).

    Allows:
    - sqlite3 db ".schema", ".tables", ".dump" (meta commands)
    - sqlite3 db "SELECT ..." (read queries)
    - sqlite3 db "PRAGMA ..." (read pragmas)

    Blocks:
    - sqlite3 db "INSERT/UPDATE/DELETE/DROP/CREATE/ALTER ..."
    """
    import re

    # Extract the SQL/command part (everything after db path in quotes)
    # Pattern: sqlite3 <db_path> "<query>" or sqlite3 <db_path> '<query>'
    # Also handles: sqlite3 <db_path> ".tables" (dot commands)
    match = re.search(r'sqlite3\s+\S+\s+["\'](.+?)["\']', command)
    if not match:
        # No quoted query found - could be interactive mode, block it
        return False

    query = match.group(1).strip().upper()

    # Safe meta commands (dot commands)
    safe_meta = ('.SCHEMA', '.TABLES', '.DUMP', '.INDICES', '.INDEXES',
                 '.MODE', '.HEADERS', '.WIDTH', '.HELP', '.DATABASES')
    for meta in safe_meta:
        if query.startswith(meta):
            return True

    # Safe SQL operations (read-only)
    safe_sql = ('SELECT', 'PRAGMA', 'EXPLAIN', 'ANALYZE')
    for sql in safe_sql:
        if query.startswith(sql):
            return True

    # Everything else is potentially write (INSERT, UPDATE, DELETE, etc.)
    return False


def is_safe_pipe_chain(command: str) -> bool:
    """
    Check if a piped command chain is safe (all segments are read-only).

    Allows: grep pattern file | head -20 | wc -l
    Allows: echo '...' | empirica preflight-submit -  (empirica CLI)
    Blocks: grep pattern | xargs rm, cat file | bash
    """
    segments = [s.strip() for s in command.split('|')]

    if not segments:
        return False

    # First segment must be a safe command
    first_cmd = segments[0]
    first_is_safe = False

    # Check sqlite3 commands first
    if first_cmd.startswith('sqlite3 ') and is_safe_sqlite_command(first_cmd):
        first_is_safe = True

    # Check standard safe prefixes
    if not first_is_safe:
        for prefix in SAFE_BASH_PREFIXES:
            if first_cmd.startswith(prefix) or (prefix.endswith(' ') and first_cmd == prefix.rstrip()):
                first_is_safe = True
                break

    if not first_is_safe:
        return False

    # All subsequent segments must start with safe pipe targets OR be safe empirica commands
    for segment in segments[1:]:
        segment = segment.strip()
        # Strip heredoc suffix for matching (e.g., "empirica preflight-submit - << 'EOF'")
        segment_clean = segment.split('<<')[0].strip() if '<<' in segment else segment
        segment_safe = False

        # Check empirica CLI whitelist (tiered)
        if is_safe_empirica_command(segment_clean):
            segment_safe = True

        # Check standard safe pipe targets
        if not segment_safe:
            for target in SAFE_PIPE_TARGETS:
                if segment.startswith(target):
                    segment_safe = True
                    break

        if not segment_safe:
            return False

    return True


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

    # Get Claude session_id from hook input (available for ALL users)
    claude_session_id = hook_input.get('session_id')

    # Resolve project root using priority chain (claude_session → transaction → instance → TTY → CWD)
    # This is critical for multi-project scenarios where CWD may be reset
    project_root = resolve_project_root(claude_session_id=claude_session_id)
    if project_root:
        empirica_root = project_root / '.empirica'
        os.chdir(project_root)  # Set CWD to the correct project
    else:
        # Fallback to path_resolver if priority chain fails
        try:
            from empirica.config.path_resolver import get_empirica_root  # type: ignore[import-not-found]
            empirica_root = get_empirica_root()
            if empirica_root.exists():
                os.chdir(empirica_root.parent)
        except ImportError as e:
            respond("allow", f"Cannot import path_resolver: {e}")
            sys.exit(0)

    # Read active transaction first (transactions can span compaction boundaries)
    # The transaction file's session_id is authoritative when a transaction is open
    current_transaction_id = None
    tx_session_id = None
    if empirica_root:
        instance_id = get_instance_id()
        suffix = f'_{instance_id}' if instance_id else ''
        tx_file = empirica_root / f'active_transaction{suffix}.json'
        # DEBUG: Log what we're looking for
        import sys as _sys
        _sys.stderr.write(f"SENTINEL_DEBUG: instance_id={instance_id}, tx_file={tx_file}, exists={tx_file.exists()}\n")
        if tx_file.exists():
            try:
                with open(tx_file, 'r') as f:
                    tx_data = json.load(f)
                current_transaction_id = tx_data.get('transaction_id')
                tx_session_id = tx_data.get('session_id')  # Session that started this transaction
                _sys.stderr.write(f"SENTINEL_DEBUG: current_transaction_id={current_transaction_id}, tx_session_id={tx_session_id}\n")
            except Exception as e:
                _sys.stderr.write(f"SENTINEL_DEBUG: tx file read error: {e}\n")

    # Get session_id - transaction file takes priority (survives compaction)
    # Fallback to active_work file for when no transaction is open
    session_id = tx_session_id  # Priority 0: transaction file (authoritative during transaction)

    if not session_id and claude_session_id:
        # Priority 1: active_work file (updated by PREFLIGHT, project-switch)
        try:
            active_work_file = Path.home() / '.empirica' / f'active_work_{claude_session_id}.json'
            if active_work_file.exists():
                with open(active_work_file, 'r') as f:
                    work_data = json.load(f)
                session_id = work_data.get('empirica_session_id')
        except Exception:
            pass

    if not session_id:
        respond("allow", "WARNING: No active transaction or empirica_session_id. Run PREFLIGHT first.")
        sys.exit(0)

    # SessionDatabase uses path_resolver internally for DB location
    from empirica.data.session_database import SessionDatabase  # type: ignore[import-not-found]
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
    # Scope by transaction_id if available (current transaction only)
    if current_transaction_id:
        cursor.execute("""
            SELECT know, uncertainty, timestamp, project_id FROM reflexes
            WHERE session_id = ? AND phase = 'PREFLIGHT' AND transaction_id = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (session_id, current_transaction_id))
    else:
        cursor.execute("""
            SELECT know, uncertainty, timestamp, project_id FROM reflexes
            WHERE session_id = ? AND phase = 'PREFLIGHT'
            ORDER BY timestamp DESC LIMIT 1
        """, (session_id,))
    preflight_row = cursor.fetchone()

    if not preflight_row:
        # No PREFLIGHT yet - allow read-only/workflow commands + transitions
        # This enables artifact lifecycle review before starting a new transaction:
        # goals-list, epistemics-list, goals-complete, unknown-resolve, etc.
        if tool_name == 'Bash':
            command = tool_input.get('command', '')
            if is_safe_bash_command(tool_input):
                db.close()
                respond("allow", "Safe Bash before PREFLIGHT (artifact review)")
                sys.exit(0)
            if is_transition_command(command):
                db.close()
                respond("allow", "Transition command (no PREFLIGHT yet - starting new cycle)")
                sys.exit(0)
        db.close()
        respond("deny", f"No PREFLIGHT. Assess your knowledge state first.")
        sys.exit(0)

    preflight_know, preflight_uncertainty, preflight_timestamp, preflight_project_id = preflight_row

    # PROJECT CONTEXT CHECK: Require new PREFLIGHT if project changed
    # This implicitly closes the previous project's epistemic loop
    # Uses session's project_id (same source as reflexes storage)
    current_project_id = _get_current_project_id(db, session_id)
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
    # Scope by transaction_id to prevent cross-instance bleed (multiple Claudes sharing session)
    if current_transaction_id:
        cursor.execute("""
            SELECT timestamp FROM reflexes
            WHERE session_id = ? AND phase = 'POSTFLIGHT' AND transaction_id = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (session_id, current_transaction_id))
    else:
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
                # Loop closed. Only block truly praxic operations (file modification).
                # Allow read-only, empirica workflow, toggles, and transitions.
                # This enables artifact lifecycle between transactions:
                # goals-list, goals-complete, unknown-resolve, finding-log, etc.
                if tool_name == 'Bash':
                    command = tool_input.get('command', '')

                    # Safe Bash (read-only + empirica workflow) — always allowed
                    # This is a safety net: Rule 2 should catch most of these,
                    # but edge cases (|| chains, complex pipes) may reach here.
                    if is_safe_bash_command(tool_input):
                        db.close()
                        respond("allow", "Safe Bash between transactions (artifact lifecycle)")
                        sys.exit(0)

                    # Toggle commands (pause/unpause)
                    toggle_action = is_toggle_command(command)
                    if toggle_action == 'pause':
                        db.close()
                        respond("allow", "Sentinel self-exemption: pause toggle (loop closed)")
                        sys.exit(0)
                    elif toggle_action == 'unpause':
                        db.close()
                        respond("allow", "Sentinel self-exemption: unpause toggle")
                        sys.exit(0)

                    # Transition commands (cd, session-create, project-bootstrap)
                    if is_transition_command(command):
                        db.close()
                        respond("allow", "Transition command (starting new cycle)")
                        sys.exit(0)

                db.close()
                respond("deny", f"Epistemic loop closed (POSTFLIGHT completed). Run new PREFLIGHT to start next goal.")
                sys.exit(0)
        except (ValueError, TypeError):
            pass  # If timestamps can't be compared, continue with other checks

    # Use RAW vectors - bias corrections are feedback for AI to internalize, not silent adjustments
    raw_know = preflight_know or 0
    raw_unc = preflight_uncertainty or 1

    # ANTI-GAMING: Check if previous transaction ended with INVESTIGATE
    # If so, require explicit CHECK with evidence - can't just start fresh with high confidence
    cursor.execute("""
        SELECT json_extract(reflex_data, '$.decision') as decision, transaction_id
        FROM reflexes
        WHERE session_id = ? AND phase = 'CHECK'
        ORDER BY timestamp DESC LIMIT 1
    """, (session_id,))
    prev_check = cursor.fetchone()

    if prev_check:
        prev_decision, prev_tx_id = prev_check
        # If previous CHECK was INVESTIGATE and this is a NEW transaction, block auto-proceed
        if prev_decision == 'investigate' and prev_tx_id != current_transaction_id:
            # Check if there's been any noetic evidence since (findings, etc.)
            cursor.execute("""
                SELECT COUNT(*) FROM project_findings
                WHERE session_id = ? AND created_timestamp > ?
            """, (session_id, preflight_timestamp))
            findings_since = cursor.fetchone()[0] or 0

            if findings_since == 0:
                db.close()
                respond("deny", f"Previous transaction ended with INVESTIGATE. Show evidence of investigation (findings) or submit CHECK with proceed decision.")
                sys.exit(0)

    # AUTO-PROCEED: If PREFLIGHT passes readiness gate, skip CHECK requirement
    if raw_know >= KNOW_THRESHOLD and raw_unc <= UNCERTAINTY_THRESHOLD:
        db.close()
        respond("allow", "PREFLIGHT confidence sufficient - proceeding")
        sys.exit(0)

    # PREFLIGHT confidence too low - require explicit CHECK
    # Scope by transaction_id to only find CHECK within current transaction
    if current_transaction_id:
        cursor.execute("""
            SELECT know, uncertainty, reflex_data, timestamp
            FROM reflexes
            WHERE session_id = ? AND phase = 'CHECK' AND transaction_id = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (session_id, current_transaction_id))
    else:
        cursor.execute("""
            SELECT know, uncertainty, reflex_data, timestamp
            FROM reflexes
            WHERE session_id = ? AND phase = 'CHECK'
            ORDER BY timestamp DESC LIMIT 1
        """, (session_id,))
    check_row = cursor.fetchone()
    # NOTE: db kept open - reused for anti-gaming check below (single connection per invocation)

    if not check_row:
        respond("deny", "No valid CHECK found. Run CHECK after investigation to proceed.")
        sys.exit(0)

    know, uncertainty, reflex_data, check_timestamp = check_row

    # Verify CHECK is after PREFLIGHT (proper sequence)
    try:
        preflight_ts = float(preflight_timestamp)
        check_ts = float(check_timestamp)

        if check_ts < preflight_ts:
            respond("deny", f"CHECK is from previous transaction (before current PREFLIGHT). Run CHECK to validate readiness.")
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
        respond("allow", "CHECK passed - proceeding")
        sys.exit(0)
    else:
        respond("deny", "CHECK confidence insufficient. Continue investigation, then re-submit CHECK.")
        sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        # Fail-open: if sentinel crashes, allow the action but warn
        # This prevents transient errors (DB lock, import race) from blocking work
        import sys as _sys
        _sys.stderr.write(f"SENTINEL_CRASH: {type(e).__name__}: {e}\n")
        respond("allow", f"Sentinel error (fail-open): {type(e).__name__}: {e}")
        _sys.exit(0)
