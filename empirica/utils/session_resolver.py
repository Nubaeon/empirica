"""
Session ID Resolver - Resolve session aliases to UUIDs

Supports magic aliases for easy session resumption:
- "latest", "last", or "auto" - Most recent session
- "latest:active" - Most recent active session (not ended)
- "latest:<ai_id>" - Most recent session for specific AI
- "latest:active:<ai_id>" - Most recent active session for specific AI

Also provides TTY-based session isolation for multi-instance support:
- get_tty_key() - Get TTY-based key for current terminal
- get_tty_session() - Read Claude session mapping from TTY-keyed file
- write_tty_session() - Write Claude session mapping (called by hooks)

Examples:
    resolve_session_id("latest")
    resolve_session_id("latest:active")
    resolve_session_id("latest:claude-code")
    resolve_session_id("latest:active:claude-code")
    resolve_session_id("88dbf132")  # Partial UUID still works
"""

import json
import logging
import os
import subprocess
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# TTY-based Session Isolation (Multi-Instance Support)
# =============================================================================

def get_tty_key() -> Optional[str]:
    """Get a TTY-based key for session isolation. Returns None if no TTY.

    Walks up the process tree to find the controlling TTY. This handles
    cases where CLI commands run via bash (which may not have a TTY) but
    the grandparent Claude process does.

    Returns sanitized string like 'pts-2' or None if no TTY found.

    CRITICAL: No PPID fallback. If TTY detection fails, return None to signal
    that instance isolation cannot be guaranteed. Callers must handle None
    by failing safely rather than risking cross-instance bleed.
    """
    try:
        # Walk up process tree looking for a TTY
        pid = os.getppid()
        for _ in range(5):  # Max 5 levels up
            if pid <= 1:
                break

            result = subprocess.run(
                ['ps', '-p', str(pid), '-o', 'tty=,ppid='],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode != 0:
                break

            parts = result.stdout.strip().split()
            if not parts:
                break

            tty = parts[0]
            if tty and tty != '?':
                return tty.replace('/', '-')

            # Move to parent
            if len(parts) > 1:
                try:
                    pid = int(parts[1])
                except ValueError:
                    break
            else:
                break
    except Exception:
        pass
    return None  # No fallback - fail safely


def get_tty_session(warn_if_stale: bool = True) -> Optional[Dict[str, Any]]:
    """Read session mapping from TTY-keyed file.

    Returns dict with:
        - claude_session_id: Claude Code conversation UUID
        - empirica_session_id: Empirica session UUID
        - project_path: Project directory path
        - tty_key: The TTY key used
        - timestamp: When the mapping was written

    Args:
        warn_if_stale: If True, logs warnings for potentially stale sessions

    Returns None if no TTY key available, no session file exists, or on read error.
    """
    tty_key = get_tty_key()
    if not tty_key:
        return None  # No TTY - cannot determine instance

    tty_sessions_dir = Path.home() / '.empirica' / 'tty_sessions'
    session_file = tty_sessions_dir / f'{tty_key}.json'

    if not session_file.exists():
        return None

    try:
        with open(session_file, 'r') as f:
            session = json.load(f)

        # Validate and warn if stale
        if warn_if_stale:
            validation = validate_tty_session(session)
            for warning in validation.get('warnings', []):
                logger.warning(f"TTY session warning: {warning}")

            # If TTY device is gone, return None (session is invalid)
            if not validation.get('valid', True):
                logger.warning("TTY session is invalid, ignoring")
                return None

        return session
    except Exception as e:
        logger.debug(f"Failed to read TTY session file: {e}")
        return None


def write_tty_session(
    claude_session_id: str = None,
    empirica_session_id: str = None,
    project_path: str = None
) -> bool:
    """Write session mapping to TTY-keyed file for CLI commands to read.

    This bridges the gap between hooks (which receive claude_session_id) and
    CLI commands (which don't). Both run in the same TTY context.

    Can be called from:
    - Claude Code hooks (have claude_session_id, may have empirica_session_id)
    - CLI session-create (no claude_session_id, has empirica_session_id)

    CRITICAL: Returns False if no TTY available - does not use PPID fallback
    to avoid cross-instance bleed risk.

    Also writes an instance mapping file keyed by TMUX_PANE (if available).
    This enables hook context lookups where `tty` command fails but TMUX_PANE
    is available.

    Args:
        claude_session_id: Claude Code conversation UUID (optional for CLI)
        empirica_session_id: Empirica session UUID (optional)
        project_path: Project directory path (optional)

    Returns:
        True if successfully written, False if neither TTY nor TMUX_PANE available.
    """
    from datetime import datetime

    tty_key = get_tty_key()
    tmux_pane = os.environ.get('TMUX_PANE')
    instance_id = f"tmux_{tmux_pane.lstrip('%')}" if tmux_pane else None

    wrote_something = False

    try:
        # Write instance_projects FIRST - works via Bash tool where tty fails
        # This is the PRIMARY mechanism for multi-instance isolation
        if instance_id and project_path:
            instance_dir = Path.home() / '.empirica' / 'instance_projects'
            instance_dir.mkdir(parents=True, exist_ok=True)
            instance_file = instance_dir / f'{instance_id}.json'
            instance_data = {
                'project_path': project_path,
                'tty_key': tty_key,  # May be None if via Bash tool
                'claude_session_id': claude_session_id,  # Key for active_work lookup
                'empirica_session_id': empirica_session_id,
                'timestamp': datetime.now().isoformat()
            }
            with open(instance_file, 'w') as f:
                json.dump(instance_data, f, indent=2)
            logger.debug(f"Wrote instance mapping: {instance_file}")
            wrote_something = True

        # Write TTY session file if TTY is available (direct terminal context)
        if tty_key:
            tty_sessions_dir = Path.home() / '.empirica' / 'tty_sessions'
            tty_sessions_dir.mkdir(parents=True, exist_ok=True)
            session_file = tty_sessions_dir / f'{tty_key}.json'

            data = {
                'claude_session_id': claude_session_id,
                'empirica_session_id': empirica_session_id,
                'project_path': project_path,
                'tty_key': tty_key,
                'instance_id': instance_id,  # Store for cross-reference
                'timestamp': datetime.now().isoformat(),
                'pid': os.getpid(),
                'ppid': os.getppid()
            }

            with open(session_file, 'w') as f:
                json.dump(data, f, indent=2)
            wrote_something = True

        if not wrote_something:
            logger.debug("No TTY or TMUX_PANE available - cannot write session files")
            return False

        return True
    except Exception as e:
        logger.debug(f"Failed to write session file: {e}")
        return False


def get_claude_session_id() -> Optional[str]:
    """Get the Claude Code session ID for the current terminal.

    Convenience function that reads the TTY session file and returns
    just the claude_session_id.

    Returns:
        Claude Code conversation UUID or None if not available.
    """
    session = get_tty_session()
    return session.get('claude_session_id') if session else None


def validate_tty_session(session: Dict[str, Any] = None) -> Dict[str, Any]:
    """Validate a TTY session for staleness and warn if issues detected.

    Checks:
    1. Process still exists (PID that wrote the session)
    2. TTY device still exists (if real TTY, not ppid-based)
    3. Timestamp not too old (default: 4 hours)

    Args:
        session: TTY session dict (if None, reads current TTY session)

    Returns:
        Dict with:
            - valid: bool - True if session appears valid
            - warnings: list[str] - Warning messages if any
            - session: dict - The session data (if valid)
    """
    from datetime import datetime, timedelta

    result = {
        'valid': True,
        'warnings': [],
        'session': None
    }

    if session is None:
        session = get_tty_session()

    if not session:
        result['valid'] = False
        result['warnings'].append("No TTY session file found")
        return result

    result['session'] = session

    # Note: We don't check if the original PID exists because the hook that writes
    # the TTY session file always exits immediately after writing. The PID check
    # would always warn for valid sessions. TTY device check is the meaningful validation.

    # Check 1: TTY device exists (for real TTYs)
    tty_key = session.get('tty_key', '')
    if tty_key.startswith('pts-'):
        tty_device = f"/dev/{tty_key.replace('-', '/')}"
        if not Path(tty_device).exists():
            result['valid'] = False
            result['warnings'].append(f"TTY device {tty_device} no longer exists - terminal closed?")

    # Check 2: Timestamp staleness (4 hour threshold)
    timestamp_str = session.get('timestamp')
    if timestamp_str:
        try:
            # Handle ISO format with or without timezone
            if '+' in timestamp_str or 'Z' in timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                # Make comparison timezone-aware
                now = datetime.now(timestamp.tzinfo)
            else:
                timestamp = datetime.fromisoformat(timestamp_str)
                now = datetime.now()

            age = now - timestamp
            if age > timedelta(hours=4):
                hours = age.total_seconds() / 3600
                result['warnings'].append(f"TTY session is {hours:.1f} hours old - may be stale")
        except (ValueError, TypeError):
            pass  # Can't parse timestamp, skip check

    # Only mark invalid if TTY device is gone (terminal closed)
    # PID being gone is just a warning - project_path can still be valid
    # (e.g., project-switch updates the file after original process exits)
    if any("TTY device" in w and "no longer exists" in w for w in result['warnings']):
        result['valid'] = False

    return result


def cleanup_stale_tty_sessions(max_age_hours: float = 24) -> int:
    """Remove stale TTY session files.

    Removes files where:
    - The TTY device no longer exists
    - The original process is dead AND file is older than max_age_hours

    Args:
        max_age_hours: Maximum age in hours before a session with dead process is removed

    Returns:
        Number of files removed
    """
    from datetime import datetime, timedelta

    tty_sessions_dir = Path.home() / '.empirica' / 'tty_sessions'
    if not tty_sessions_dir.exists():
        return 0

    removed = 0
    for session_file in tty_sessions_dir.glob('*.json'):
        try:
            with open(session_file, 'r') as f:
                session = json.load(f)

            should_remove = False
            reason = ""

            # Check TTY device
            tty_key = session.get('tty_key', '')
            if tty_key.startswith('pts-'):
                tty_device = f"/dev/{tty_key.replace('-', '/')}"
                if not Path(tty_device).exists():
                    should_remove = True
                    reason = "TTY device gone"

            # Check process + age
            if not should_remove:
                pid = session.get('pid')
                process_alive = False
                if pid:
                    try:
                        os.kill(pid, 0)
                        process_alive = True
                    except OSError:
                        pass

                if not process_alive:
                    timestamp_str = session.get('timestamp')
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00').split('+')[0])
                            age = datetime.now() - timestamp
                            if age > timedelta(hours=max_age_hours):
                                should_remove = True
                                reason = f"Process dead, file {age.total_seconds()/3600:.1f}h old"
                        except (ValueError, TypeError):
                            pass

            if should_remove:
                session_file.unlink()
                removed += 1
                logger.debug(f"Removed stale TTY session {session_file.name}: {reason}")

        except Exception as e:
            logger.debug(f"Error checking TTY session {session_file}: {e}")

    return removed


# =============================================================================
# Session ID Resolution
# =============================================================================


def resolve_session_id(session_id_or_alias: str, ai_id: Optional[str] = None) -> str:
    """
    Resolve session ID from alias or return original UUID.

    Args:
        session_id_or_alias: UUID (full or partial), "latest", "last", "auto", or compound alias
        ai_id: Optional AI identifier for scoped resolution (used as fallback filter)

    Returns:
        Resolved full UUID

    Raises:
        ValueError: If alias doesn't match any session

    Examples:
        >>> resolve_session_id("88dbf132-cc7c-4a4b-9b59-77df3b13dbd2")
        '88dbf132-cc7c-4a4b-9b59-77df3b13dbd2'

        >>> resolve_session_id("88dbf132")  # Partial UUID
        '88dbf132-cc7c-4a4b-9b59-77df3b13dbd2'

        >>> resolve_session_id("latest")
        '88dbf132-cc7c-4a4b-9b59-77df3b13dbd2'  # Most recent session

        >>> resolve_session_id("latest:active")
        'fc87adfc-...'  # Most recent active session

        >>> resolve_session_id("latest:claude-code")
        '20586d3b-...'  # Most recent claude-code session

        >>> resolve_session_id("latest:active:claude-code")
        '88dbf132-...'  # Most recent active claude-code session
    """
    # Guard against None input
    if not session_id_or_alias:
        raise ValueError("session_id is required (got None or empty)")

    # Check if it's an alias
    if not session_id_or_alias.startswith("latest") and session_id_or_alias not in ("last", "auto"):
        # Regular UUID (partial or full) - resolve via database
        return _resolve_partial_uuid(session_id_or_alias)

    # Parse alias
    alias = session_id_or_alias
    if alias in ("last", "auto"):
        alias = "latest"  # Normalize to "latest"

    parts = alias.split(":")

    # Extract filters from alias parts
    filters = {
        'active_only': False,
        'ai_id': None
    }

    for part in parts[1:]:  # Skip first part ("latest")
        if part == "active":
            filters['active_only'] = True
        else:
            # Assume it's an AI identifier
            filters['ai_id'] = part

    # Use provided ai_id as fallback if no AI specified in alias
    if not filters['ai_id'] and ai_id:
        filters['ai_id'] = ai_id
        logger.debug(f"Using provided ai_id as fallback filter: {ai_id}")

    # Query database
    try:
        from empirica.data.session_database import SessionDatabase

        db = SessionDatabase()

        # Build query
        query = "SELECT session_id FROM sessions WHERE 1=1"
        params = []

        if filters['active_only']:
            query += " AND end_time IS NULL"
            logger.debug("Filtering for active sessions only")

        if filters['ai_id']:
            query += " AND ai_id = ?"
            params.append(filters['ai_id'])
            logger.debug(f"Filtering for ai_id: {filters['ai_id']}")

        # Multi-instance isolation: filter by instance_id
        current_instance_id = get_instance_id()
        if current_instance_id:
            # Match exact instance_id OR sessions without instance_id (legacy)
            query += " AND (instance_id = ? OR instance_id IS NULL)"
            params.append(current_instance_id)
            logger.debug(f"Filtering for instance_id: {current_instance_id}")

        query += " ORDER BY start_time DESC LIMIT 1"

        logger.debug(f"Executing query: {query} with params: {params}")

        cursor = db.conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()

        db.close()

        if result:
            resolved_id = result[0]
            logger.info(f"Resolved alias '{session_id_or_alias}' to session: {resolved_id[:8]}")
            return resolved_id
        else:
            error_msg = f"No session found for alias: {session_id_or_alias}"
            if filters['ai_id']:
                error_msg += f" (ai_id: {filters['ai_id']})"
            if filters['active_only']:
                error_msg += " (active only)"
            if current_instance_id:
                error_msg += f" (instance: {current_instance_id})"
            logger.warning(error_msg)
            raise ValueError(error_msg)

    except ImportError as e:
        logger.error(f"Failed to import SessionDatabase: {e}")
        raise ValueError(f"Cannot resolve session alias - database unavailable: {e}")


def _resolve_partial_uuid(partial_or_full_uuid: str) -> str:
    """
    Resolve partial UUID (8 chars) to full UUID, or validate full UUID.

    Args:
        partial_or_full_uuid: Partial (8+ chars) or full UUID string

    Returns:
        Full UUID

    Raises:
        ValueError: If UUID not found or ambiguous
    """
    # If it looks like a full UUID (contains hyphens), return as-is
    if "-" in partial_or_full_uuid:
        logger.debug(f"Full UUID provided: {partial_or_full_uuid}")
        return partial_or_full_uuid

    # Partial UUID - query database
    try:
        from empirica.data.session_database import SessionDatabase

        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Match beginning of session_id
        cursor.execute(
            "SELECT session_id FROM sessions WHERE session_id LIKE ? ORDER BY start_time DESC",
            (f"{partial_or_full_uuid}%",)
        )

        results = cursor.fetchall()
        db.close()

        if not results:
            raise ValueError(f"No session found matching: {partial_or_full_uuid}")

        if len(results) > 1:
            logger.warning(f"Multiple sessions match '{partial_or_full_uuid}' - using most recent")

        resolved = results[0][0]
        logger.debug(f"Resolved partial UUID '{partial_or_full_uuid}' to {resolved}")
        return resolved

    except ImportError as e:
        logger.error(f"Failed to import SessionDatabase: {e}")
        # Fallback: assume it's a full UUID if it's 36 chars
        if len(partial_or_full_uuid) == 36:
            logger.debug("Database unavailable, assuming full UUID")
            return partial_or_full_uuid
        raise ValueError(f"Cannot resolve partial UUID - database unavailable: {e}")


def get_latest_session_id(ai_id: Optional[str] = None, active_only: bool = False) -> str:
    """
    Get the most recent session ID.

    Convenience function equivalent to resolve_session_id("latest:...").

    Args:
        ai_id: Optional AI identifier to filter by
        active_only: If True, only return active (not ended) sessions

    Returns:
        Most recent session UUID

    Raises:
        ValueError: If no session found

    Examples:
        >>> get_latest_session_id()
        '88dbf132-cc7c-4a4b-9b59-77df3b13dbd2'

        >>> get_latest_session_id(ai_id="claude-code")
        '20586d3b-...'

        >>> get_latest_session_id(ai_id="claude-code", active_only=True)
        '88dbf132-...'
    """
    # Build alias string
    alias_parts = ["latest"]

    if active_only:
        alias_parts.append("active")

    if ai_id:
        alias_parts.append(ai_id)

    alias = ":".join(alias_parts)

    return resolve_session_id(alias)


def get_session_empirica_root(session_id: str) -> Optional[Path]:
    """
    Get the .empirica root directory for a session's project.

    Looks up the session in the database to find its project,
    then returns the path to that project's .empirica directory.

    Args:
        session_id: UUID of the session

    Returns:
        Path to the project's .empirica directory, or None if not found

    Examples:
        >>> get_session_empirica_root("88dbf132-cc7c-4a4b-9b59-77df3b13dbd2")
        PosixPath('/home/user/project/.empirica')
    """
    try:
        from empirica.data.session_database import SessionDatabase

        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Get project_id from session
        cursor.execute("""
            SELECT project_id FROM sessions WHERE session_id = ?
        """, (session_id,))
        row = cursor.fetchone()

        if not row or not row[0]:
            logger.debug(f"No project_id found for session {session_id}")
            return None

        project_id = row[0]

        # Get project path from projects table
        cursor.execute("""
            SELECT project_path FROM projects WHERE project_id = ?
        """, (project_id,))
        project_row = cursor.fetchone()

        if project_row and project_row[0]:
            project_path = Path(project_row[0])
            empirica_root = project_path / '.empirica'
            if empirica_root.exists():
                return empirica_root

        logger.debug(f"No project path found for project {project_id}")
        return None

    except Exception as e:
        logger.debug(f"Failed to get empirica root for session: {e}")
        return None


def is_session_alias(session_id_or_alias: str) -> bool:
    """
    Check if string is a session alias (not a UUID).

    Args:
        session_id_or_alias: String to check

    Returns:
        True if it's an alias, False if it's a UUID

    Examples:
        >>> is_session_alias("latest")
        True

        >>> is_session_alias("latest:active:claude-code")
        True

        >>> is_session_alias("88dbf132-cc7c-4a4b-9b59-77df3b13dbd2")
        False
    """
    return session_id_or_alias.startswith("latest") or session_id_or_alias in ("last", "auto")


def get_instance_id() -> Optional[str]:
    """
    Get a unique instance identifier for multi-instance isolation.

    This allows multiple Claude instances to run simultaneously without
    session cross-talk. Each instance gets its own session namespace.

    Priority order:
    1. EMPIRICA_INSTANCE_ID env var (explicit override)
    2. TMUX_PANE (tmux terminal pane ID, e.g., "%0", "%1")
    3. TERM_SESSION_ID (macOS Terminal.app session ID)
    4. WINDOWID (X11 window ID)
    5. None (fallback to legacy behavior - first match wins)

    Returns:
        Instance identifier string, or None for legacy behavior

    Examples:
        # In tmux pane %0
        >>> get_instance_id()
        'tmux_0'

        # With explicit env var
        >>> os.environ['EMPIRICA_INSTANCE_ID'] = 'my-instance'
        >>> get_instance_id()
        'my-instance'

        # Outside tmux, no special env
        >>> get_instance_id()
        None
    """
    import os

    # Priority 1: Explicit override
    explicit_id = os.environ.get('EMPIRICA_INSTANCE_ID')
    if explicit_id:
        logger.debug(f"Using explicit instance_id: {explicit_id}")
        return explicit_id

    # Priority 2: tmux pane (most common for multi-instance work)
    # IMPORTANT: Use tmux_{N} format (not tmux:%N) to match file naming convention
    # Files are named: instance_projects/tmux_4.json, active_transaction_tmux_4.json
    tmux_pane = os.environ.get('TMUX_PANE')
    if tmux_pane:
        instance_id = f"tmux_{tmux_pane.lstrip('%')}"
        logger.debug(f"Using tmux pane as instance_id: {instance_id}")
        return instance_id

    # Priority 3: macOS Terminal.app session
    term_session = os.environ.get('TERM_SESSION_ID')
    if term_session:
        # Truncate to reasonable length (full ID is very long)
        instance_id = f"term:{term_session[:16]}"
        logger.debug(f"Using Terminal.app session as instance_id: {instance_id}")
        return instance_id

    # Priority 4: X11 window ID
    window_id = os.environ.get('WINDOWID')
    if window_id:
        instance_id = f"x11:{window_id}"
        logger.debug(f"Using X11 window ID as instance_id: {instance_id}")
        return instance_id

    # Priority 5: No isolation (legacy behavior)
    logger.debug("No instance_id available - using legacy behavior")
    return None


def _get_instance_suffix() -> str:
    """Get the instance-specific filename suffix for file-based tracking."""
    instance_id = get_instance_id()
    if instance_id:
        safe = instance_id.replace(":", "_").replace("%", "")
        return f"_{safe}"
    return ""


def _update_instance_project(instance_id: str, project_path: str, claude_session_id: str = None) -> bool:
    """Update instance_projects file to match active_work (self-heal stale instance mapping).

    Called when active_work (set by project-switch) disagrees with instance_projects
    (set by session-init). active_work represents explicit user intent and wins.

    Args:
        instance_id: The instance ID (e.g., 'tmux_4')
        project_path: The authoritative project path from active_work
        claude_session_id: Optional Claude session ID to include

    Returns:
        True if successfully updated, False otherwise
    """
    import time
    from pathlib import Path

    try:
        instance_dir = Path.home() / '.empirica' / 'instance_projects'
        instance_dir.mkdir(parents=True, exist_ok=True)
        instance_file = instance_dir / f'{instance_id}.json'

        # Read existing data to preserve other fields
        existing_data = {}
        if instance_file.exists():
            try:
                with open(instance_file, 'r') as f:
                    existing_data = json.load(f)
            except Exception:
                pass

        # Update with new project_path (authoritative from active_work)
        existing_data['project_path'] = project_path
        existing_data['timestamp'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
        existing_data['source'] = 'self-heal-from-active_work'
        if claude_session_id:
            existing_data['claude_session_id'] = claude_session_id

        with open(instance_file, 'w') as f:
            json.dump(existing_data, f, indent=2)

        logger.debug(f"_update_instance_project: updated {instance_id} -> {project_path}")
        return True

    except Exception as e:
        logger.warning(f"_update_instance_project failed: {e}")
        return False


def get_active_project_path(claude_session_id: str = None) -> 'Optional[str]':
    """Get the active project path for the current instance.

    CANONICAL function for project resolution. All components should use this
    instead of implementing their own priority chain.

    Priority chain (NO CWD FALLBACK) - per INSTANCE_ISOLATION.md Section 4.1:
    0. active_work_{claude_session_id}.json - AUTHORITATIVE (set by project-switch, user intent)
    1. instance_projects/{instance_id}.json - fallback (set by session-init, may be stale)

    Self-healing: If both exist but disagree, active_work wins (explicit user intent
    via project-switch) and instance_projects is updated to match.

    Args:
        claude_session_id: Optional Claude Code conversation UUID (from hook input)

    Returns:
        Absolute path to the project, or None if cannot be resolved.
        Returns None rather than falling back to CWD to fail explicitly.

    Usage:
        # In hooks (have claude_session_id from stdin):
        project_path = get_active_project_path(claude_session_id=hook_input.get('session_id'))

        # In CLI commands (no claude_session_id):
        project_path = get_active_project_path()
    """
    from pathlib import Path

    active_work_path = None
    instance_path = None

    # Read active_work file (if claude_session_id provided)
    if claude_session_id:
        active_work_file = Path.home() / '.empirica' / f'active_work_{claude_session_id}.json'
        if active_work_file.exists():
            try:
                with open(active_work_file, 'r') as f:
                    data = json.load(f)
                    active_work_path = data.get('project_path')
            except Exception:
                pass

    # Read instance_projects (TMUX_PANE-based) - AUTHORITATIVE source
    instance_id = get_instance_id()
    if instance_id:
        instance_file = Path.home() / '.empirica' / 'instance_projects' / f'{instance_id}.json'
        if instance_file.exists():
            try:
                with open(instance_file, 'r') as f:
                    data = json.load(f)
                    instance_path = data.get('project_path')
            except Exception:
                pass

    # PRIORITY 0: active_work wins (set by project-switch - explicit user intent)
    # Per INSTANCE_ISOLATION.md Section 4.1:
    #   Priority 0: active_work file (set by project-switch)
    #   Priority 1: instance_projects (set by session-init, can be stale)
    if active_work_path:
        # Self-heal: If instance_projects disagrees, update it to match active_work
        if instance_id and instance_path and instance_path != active_work_path:
            logger.info(f"get_active_project_path: self-healing stale instance_projects "
                       f"({Path(instance_path).name} → {Path(active_work_path).name})")
            try:
                _update_instance_project(instance_id, active_work_path, claude_session_id)
            except Exception as e:
                logger.debug(f"Failed to self-heal instance_projects: {e}")

        logger.debug(f"get_active_project_path: from active_work: {active_work_path}")
        return active_work_path

    # Fallback: instance_projects (only if active_work doesn't exist)
    if instance_path:
        logger.debug(f"get_active_project_path: from instance_projects: {instance_path}")
        return instance_path

    # NO CWD FALLBACK - fail explicitly
    logger.debug("get_active_project_path: could not resolve (no active_work or instance_projects)")
    return None


def _get_tracking_file(name: str) -> 'Path':
    """Get the path for a tracking file (active_session, active_transaction, etc.)."""
    from pathlib import Path
    suffix = _get_instance_suffix()
    local_empirica = Path.cwd() / '.empirica'
    if local_empirica.exists():
        return local_empirica / f'{name}{suffix}'
    return Path.home() / '.empirica' / f'{name}{suffix}'


def write_active_transaction(
    transaction_id: str,
    session_id: str = None,
    preflight_timestamp: float = None,
    status: str = "open",
    project_path: str = None
) -> None:
    """Atomically write the active transaction state to JSON file.

    This file is read by Sentinel to track transaction state across sessions.
    Transactions survive compaction - the session_id here is the one that
    opened the transaction, which may differ from the current session.

    IMPORTANT: Uses instance suffix for multi-instance isolation. Each Claude
    instance writes to its own transaction file (e.g., active_transaction_pts-6.json).

    Args:
        transaction_id: UUID of the epistemic transaction
        session_id: Session that opened this transaction (for PREFLIGHT lookup)
        preflight_timestamp: When PREFLIGHT was submitted
        status: "open" or "closed"
        project_path: Absolute path to the project (git root) this transaction belongs to
    """
    import os
    import time
    import tempfile

    # Use instance-aware filename for multi-instance isolation
    suffix = _get_instance_suffix()
    from pathlib import Path

    # Determine project_path if not provided (use CWD's git root or CWD itself)
    if not project_path:
        local_empirica = Path.cwd() / '.empirica'
        if local_empirica.exists():
            project_path = str(Path.cwd())

    # Write transaction file to the project's .empirica directory
    if project_path:
        path = Path(project_path) / '.empirica' / f'active_transaction{suffix}.json'
    else:
        path = Path.home() / '.empirica' / f'active_transaction{suffix}.json'

    path.parent.mkdir(parents=True, exist_ok=True)

    tx_data = {
        "transaction_id": transaction_id,
        "session_id": session_id,
        "preflight_timestamp": preflight_timestamp or time.time(),
        "status": status,
        "project_path": project_path,  # Essential for cross-CWD operations
        "updated_at": time.time()
    }

    tmp_fd, tmp_path = tempfile.mkstemp(dir=str(path.parent))
    try:
        with os.fdopen(tmp_fd, 'w') as tmp_f:
            json.dump(tx_data, tmp_f, indent=2)
        os.rename(tmp_path, str(path))
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def read_active_transaction_full(claude_session_id: str = None) -> Optional[dict]:
    """Read the full active transaction data from the tracking file.

    Returns the complete transaction dict including:
    - transaction_id: The transaction UUID
    - session_id: The session where PREFLIGHT was run (CRITICAL for cross-compact continuity)
    - preflight_timestamp: When PREFLIGHT was submitted
    - status: "open" or "closed"
    - project_path: Project this transaction belongs to

    Uses get_active_project_path() to find the correct project, then reads transaction from there.
    """
    from pathlib import Path
    suffix = _get_instance_suffix()

    # Use canonical project resolution
    project_path = get_active_project_path(claude_session_id)
    if project_path:
        candidate = Path(project_path) / '.empirica' / f'active_transaction{suffix}.json'
        if candidate.exists():
            try:
                with open(candidate, 'r') as f:
                    return json.load(f)
            except Exception:
                pass

    # Fallback: Global ~/.empirica/
    global_candidate = Path.home() / '.empirica' / f'active_transaction{suffix}.json'
    if global_candidate.exists():
        try:
            with open(global_candidate, 'r') as f:
                return json.load(f)
        except Exception:
            pass

    return None


def read_active_transaction(claude_session_id: str = None) -> Optional[str]:
    """Read the active transaction ID from the tracking file. Returns None if no active transaction.

    For full transaction data including session_id, use read_active_transaction_full().
    """
    data = read_active_transaction_full(claude_session_id)
    if data:
        return data.get('transaction_id')
    return None


def get_active_empirica_session_id(claude_session_id: str = None) -> Optional[str]:
    """Get the active Empirica session ID for CLI commands.

    CANONICAL function for session_id resolution. CLI commands should use this
    instead of implementing their own transaction-first logic.

    Priority chain:
    1. Active transaction (TRANSACTION-FIRST - transaction survives compaction)
    2. active_work file (from project-switch/PREFLIGHT)
    3. instance_projects file (TMUX-based fallback)

    Args:
        claude_session_id: Optional Claude Code conversation UUID (from hook input)

    Returns:
        Empirica session UUID, or None if no active session found.

    Usage:
        session_id = get_active_empirica_session_id()
        if not session_id:
            print("No active transaction - run PREFLIGHT first")
            return
    """
    # Priority 1: Active transaction (AUTHORITATIVE during transaction)
    tx_data = read_active_transaction_full(claude_session_id)
    if tx_data and tx_data.get('status') == 'open':
        session_id = tx_data.get('session_id')
        if session_id:
            logger.debug(f"get_active_empirica_session_id: from transaction: {session_id[:8]}...")
            return session_id

    # Priority 2: active_work file
    if claude_session_id:
        from pathlib import Path
        active_work_file = Path.home() / '.empirica' / f'active_work_{claude_session_id}.json'
        if active_work_file.exists():
            try:
                with open(active_work_file, 'r') as f:
                    data = json.load(f)
                    session_id = data.get('empirica_session_id')
                    if session_id:
                        logger.debug(f"get_active_empirica_session_id: from active_work: {session_id[:8]}...")
                        return session_id
            except Exception:
                pass

    # Priority 3: instance_projects (TMUX-based)
    instance_id = get_instance_id()
    if instance_id:
        from pathlib import Path
        instance_file = Path.home() / '.empirica' / 'instance_projects' / f'{instance_id}.json'
        if instance_file.exists():
            try:
                with open(instance_file, 'r') as f:
                    data = json.load(f)
                    session_id = data.get('empirica_session_id')
                    if session_id:
                        logger.debug(f"get_active_empirica_session_id: from instance_projects: {session_id[:8]}...")
                        return session_id
            except Exception:
                pass

    logger.debug("get_active_empirica_session_id: no active session found")
    return None


def clear_active_transaction(claude_session_id: str = None) -> None:
    """Remove the active transaction tracking file (called on POSTFLIGHT).

    Uses get_active_project_path() to find correct project, NOT CWD.
    """
    from pathlib import Path
    suffix = _get_instance_suffix()

    # Use canonical project resolution
    project_path = get_active_project_path(claude_session_id)
    if project_path:
        candidate = Path(project_path) / '.empirica' / f'active_transaction{suffix}.json'
        if candidate.exists():
            try:
                candidate.unlink()
                return  # Found and cleared
            except Exception:
                pass

    # Priority 2: Global fallback
    global_candidate = Path.home() / '.empirica' / f'active_transaction{suffix}.json'
    if global_candidate.exists():
        try:
            global_candidate.unlink()
        except Exception:
            pass


# ============================================================================
# Unified Context Resolver
# ============================================================================

def get_active_context(claude_session_id: str = None) -> dict:
    """Get the complete active epistemic context.

    CANONICAL function for getting the full context. All components should
    use this instead of reading individual files.

    Returns a dict with:
        - claude_session_id: Claude Code conversation UUID (if available)
        - empirica_session_id: Empirica session UUID
        - transaction_id: Active transaction UUID (if in a transaction)
        - project_path: Project directory path
        - instance_id: Instance identifier (TMUX_PANE, etc.)

    Priority chain for resolution:
    1. active_work_{claude_session_id}.json (if claude_session_id provided)
    2. TTY session file (if TTY available)
    3. instance_projects (if TMUX_PANE available)

    Args:
        claude_session_id: Optional Claude Code conversation UUID (from hook input)

    Returns:
        Dict with context fields. Missing fields are None, not absent.
    """
    from pathlib import Path

    context = {
        'claude_session_id': claude_session_id,
        'empirica_session_id': None,
        'transaction_id': None,
        'project_path': None,
        'instance_id': get_instance_id(),
    }

    # Priority 0: Check active_work file by Claude session_id (most authoritative)
    if claude_session_id:
        active_work_file = Path.home() / '.empirica' / f'active_work_{claude_session_id}.json'
        if active_work_file.exists():
            try:
                with open(active_work_file, 'r') as f:
                    data = json.load(f)
                    context['empirica_session_id'] = data.get('empirica_session_id')
                    context['project_path'] = data.get('project_path')
                    logger.debug(f"get_active_context: loaded from active_work file")
            except Exception:
                pass

    # Priority 0b: Canonical active_work.json (no session suffix)
    # CLI commands via Bash subprocess have no claude_session_id and no TMUX_PANE.
    # project-switch writes to both active_work_{id}.json AND active_work.json.
    # Without this fallback, SessionDatabase() resolves to the wrong project DB.
    if not context['project_path']:
        canonical_work_file = Path.home() / '.empirica' / 'active_work.json'
        if canonical_work_file.exists():
            try:
                with open(canonical_work_file, 'r') as f:
                    data = json.load(f)
                    if not context['empirica_session_id']:
                        context['empirica_session_id'] = data.get('empirica_session_id')
                    if not context['project_path']:
                        context['project_path'] = data.get('project_path')
                    if not context['claude_session_id']:
                        context['claude_session_id'] = data.get('claude_session_id')
                    logger.debug(f"get_active_context: loaded from canonical active_work.json")
            except Exception:
                pass

    # Priority 1: Instance projects (HIGHER priority - updated by project-switch)
    # This is the most reliable source when user switches projects
    if context['instance_id'] and (not context['empirica_session_id'] or not context['project_path']):
        instance_file = Path.home() / '.empirica' / 'instance_projects' / f"{context['instance_id']}.json"
        if instance_file.exists():
            try:
                with open(instance_file, 'r') as f:
                    data = json.load(f)
                    if not context['project_path']:
                        context['project_path'] = data.get('project_path')
                    if not context['empirica_session_id']:
                        context['empirica_session_id'] = data.get('empirica_session_id')
                    if not context['claude_session_id']:
                        context['claude_session_id'] = data.get('claude_session_id')
            except Exception:
                pass

    # Priority 2: TTY session (fallback - may be stale after project-switch)
    if not context['empirica_session_id'] or not context['project_path']:
        tty_session = get_tty_session(warn_if_stale=False)
        if tty_session:
            if not context['claude_session_id']:
                context['claude_session_id'] = tty_session.get('claude_session_id')
            if not context['empirica_session_id']:
                context['empirica_session_id'] = tty_session.get('empirica_session_id')
            if not context['project_path']:
                context['project_path'] = tty_session.get('project_path')

    # Load transaction from transaction file
    if context['project_path']:
        tx_data = read_active_transaction_full(claude_session_id)
        if tx_data:
            context['transaction_id'] = tx_data.get('transaction_id')
            # Transaction file may have more recent session_id (from PREFLIGHT)
            tx_session = tx_data.get('session_id')
            if tx_session:
                context['empirica_session_id'] = tx_session

    return context


def update_active_context(
    claude_session_id: str,
    empirica_session_id: str = None,
    project_path: str = None,
    **extra_fields
) -> bool:
    """Update the active_work file with new context values.

    CANONICAL function for updating context. PREFLIGHT, project-switch,
    and other state-changing operations should use this.

    Only updates fields that are provided (non-None). Existing values
    are preserved for fields not specified.

    Args:
        claude_session_id: Claude Code conversation UUID (required)
        empirica_session_id: New Empirica session UUID
        project_path: New project directory path
        **extra_fields: Additional fields to store

    Returns:
        True if successfully updated, False otherwise.
    """
    from pathlib import Path
    import time

    if not claude_session_id:
        logger.warning("update_active_context: claude_session_id required")
        return False

    active_work_file = Path.home() / '.empirica' / f'active_work_{claude_session_id}.json'
    active_work_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load existing data
        data = {}
        if active_work_file.exists():
            try:
                with open(active_work_file, 'r') as f:
                    data = json.load(f)
            except Exception:
                pass

        # Update with new values (only if provided)
        if empirica_session_id is not None:
            data['empirica_session_id'] = empirica_session_id
        if project_path is not None:
            data['project_path'] = project_path

        # Add extra fields
        for key, value in extra_fields.items():
            if value is not None:
                data[key] = value

        # Always update timestamp
        data['updated_at'] = time.time()

        # Atomic write
        with open(active_work_file, 'w') as f:
            json.dump(data, f, indent=2)

        logger.debug(f"update_active_context: updated {active_work_file.name}")
        return True

    except Exception as e:
        logger.warning(f"update_active_context failed: {e}")
        return False


# ============================================================================
# Project Identifier Resolution
# ============================================================================

def _is_uuid_format(value: str) -> bool:
    """Check if a string looks like a UUID (8-4-4-4-12 hex format)."""
    import re
    if not value or not isinstance(value, str):
        return False
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, value.lower()))


def resolve_project_identifier(identifier: str) -> Optional[dict]:
    """Resolve project identifier to canonical project info.

    CANONICAL function for project resolution. All CLI commands that accept
    --project-id should use this to normalize the input.

    Accepts:
        - UUID: e.g., "748a81a2-ac14-45b8-a185-994997b76828"
        - Folder name: e.g., "empirica", "my-project"
        - Path: e.g., "/home/user/projects/empirica"

    Resolution priority:
        1. If UUID format: validate in workspace.db or local sessions.db
        2. If path: extract folder_name and resolve
        3. If folder_name: lookup in workspace.db

    Args:
        identifier: Project UUID, folder name, or path

    Returns:
        Dict with:
            - project_id: Canonical UUID
            - folder_name: Project folder name (ground truth)
            - project_path: Absolute path to project directory
            - source: Where the resolution came from ('workspace', 'local', 'path')
        Or None if project cannot be resolved.

    Example:
        >>> resolve_project_identifier("empirica")
        {'project_id': '748a81a2-...', 'folder_name': 'empirica',
         'project_path': '/home/user/empirica', 'source': 'workspace'}

        >>> resolve_project_identifier("748a81a2-ac14-45b8-a185-994997b76828")
        {'project_id': '748a81a2-...', 'folder_name': 'empirica',
         'project_path': '/home/user/empirica', 'source': 'workspace'}
    """
    from pathlib import Path as P
    import sqlite3

    if not identifier:
        return None

    identifier = identifier.strip()

    # Normalize path input to folder_name
    if identifier.startswith('/') or identifier.startswith('~') or '/' in identifier:
        # It's a path - extract folder name and resolve
        path = P(identifier).expanduser().resolve()
        if path.exists() and path.is_dir():
            folder_name = path.name
            # Check if it has .empirica (valid project)
            if (path / '.empirica').exists():
                # Try to get UUID from local sessions.db
                project_id = _get_project_id_from_local_db(path)
                return {
                    'project_id': project_id,
                    'folder_name': folder_name,
                    'project_path': str(path),
                    'source': 'path'
                }
        # Path doesn't exist or isn't a valid project
        identifier = path.name  # Fall through to folder_name resolution

    # Try workspace.db lookup first (enhanced resolution)
    workspace_result = _resolve_via_workspace_db(identifier)
    if workspace_result:
        return workspace_result

    # Fallback: local .empirica lookup (basic resolution)
    # This handles projects not yet registered in workspace
    local_result = _resolve_via_local_empirica(identifier)
    if local_result:
        return local_result

    return None


def _get_project_id_from_local_db(project_path: 'Path') -> Optional[str]:
    """Extract project_id from a project's local sessions.db."""
    import sqlite3
    from pathlib import Path as P

    db_path = P(project_path) / '.empirica' / 'sessions' / 'sessions.db'
    if not db_path.exists():
        return None

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        # Get project_id from the most recent session
        cursor.execute("""
            SELECT DISTINCT project_id FROM sessions
            WHERE project_id IS NOT NULL AND project_id != ''
            ORDER BY created_at DESC LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0]
    except Exception:
        pass
    return None


def _resolve_via_workspace_db(identifier: str) -> Optional[dict]:
    """Resolve project via workspace.db (global registry).

    Workspace.db stores all registered projects with:
    - id: UUID
    - name: Project name (may differ from folder)
    - trajectory_path: Absolute path to project folder

    Args:
        identifier: UUID, folder_name, or project name

    Returns:
        Project info dict or None
    """
    import sqlite3
    from pathlib import Path as P

    workspace_db = P.home() / '.empirica' / 'workspace' / 'workspace.db'
    if not workspace_db.exists():
        return None

    try:
        conn = sqlite3.connect(str(workspace_db))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Strategy 1: Check if it's a UUID - look up by id
        if _is_uuid_format(identifier):
            cursor.execute("""
                SELECT id, name, trajectory_path FROM global_projects
                WHERE id = ? AND status = 'active'
            """, (identifier,))
        else:
            # Strategy 2: Look up by folder name (from trajectory_path)
            # or by project name
            cursor.execute("""
                SELECT id, name, trajectory_path FROM global_projects
                WHERE (
                    trajectory_path LIKE ? OR
                    name = ?
                ) AND status = 'active'
            """, (f'%/{identifier}', identifier))

        row = cursor.fetchone()
        conn.close()

        if row:
            trajectory_path = row['trajectory_path']
            # Normalize: strip /.empirica suffix if present (legacy data format)
            if trajectory_path and trajectory_path.endswith('/.empirica'):
                trajectory_path = trajectory_path[:-10]  # Remove /.empirica
            folder_name = P(trajectory_path).name if trajectory_path else None
            return {
                'project_id': row['id'],
                'folder_name': folder_name,
                'project_path': trajectory_path,
                'source': 'workspace'
            }
    except Exception as e:
        logger.debug(f"workspace.db lookup failed: {e}")

    return None


def _resolve_via_local_empirica(identifier: str) -> Optional[dict]:
    """Resolve project via local .empirica discovery.

    Fallback when workspace.db is not available or doesn't have the project.
    Searches common project locations.

    Args:
        identifier: folder_name (UUID lookup not supported in fallback)

    Returns:
        Project info dict or None
    """
    from pathlib import Path as P

    # If it's a UUID, we can't resolve without workspace.db
    if _is_uuid_format(identifier):
        return None

    # Search common locations for the folder
    search_paths = [
        P.home() / identifier,
        P.home() / 'projects' / identifier,
        P.home() / 'code' / identifier,
        P.home() / 'empirical-ai' / identifier,
        P.cwd().parent / identifier,  # Sibling directory
    ]

    for path in search_paths:
        if path.exists() and path.is_dir() and (path / '.empirica').exists():
            project_id = _get_project_id_from_local_db(path)
            return {
                'project_id': project_id,  # May be None if no sessions yet
                'folder_name': path.name,
                'project_path': str(path),
                'source': 'local'
            }

    return None
