"""
Session ID Resolver - Resolve session aliases to UUIDs

Supports magic aliases for easy session resumption:
- "latest" or "last" - Most recent session
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

    Args:
        claude_session_id: Claude Code conversation UUID (optional for CLI)
        empirica_session_id: Empirica session UUID (optional)
        project_path: Project directory path (optional)

    Returns:
        True if successfully written, False if no TTY or on error.
    """
    from datetime import datetime

    tty_key = get_tty_key()
    if not tty_key:
        logger.debug("No TTY key available - cannot write TTY session file")
        return False  # No TTY - skip writing to avoid bleed

    tty_sessions_dir = Path.home() / '.empirica' / 'tty_sessions'
    tty_sessions_dir.mkdir(parents=True, exist_ok=True)

    session_file = tty_sessions_dir / f'{tty_key}.json'

    data = {
        'claude_session_id': claude_session_id,
        'empirica_session_id': empirica_session_id,
        'project_path': project_path,
        'tty_key': tty_key,
        'timestamp': datetime.now().isoformat(),
        'pid': os.getpid(),
        'ppid': os.getppid()
    }

    try:
        with open(session_file, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.debug(f"Failed to write TTY session file: {e}")
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

    # Check 1: Process still exists
    pid = session.get('pid')
    if pid:
        try:
            os.kill(pid, 0)  # Signal 0 = check if process exists
        except OSError:
            result['warnings'].append(f"Original process (PID {pid}) no longer exists - session may be stale")

    # Check 2: TTY device exists (for real TTYs)
    tty_key = session.get('tty_key', '')
    if tty_key.startswith('pts-'):
        tty_device = f"/dev/{tty_key.replace('-', '/')}"
        if not Path(tty_device).exists():
            result['valid'] = False
            result['warnings'].append(f"TTY device {tty_device} no longer exists - terminal closed?")

    # Check 3: Timestamp staleness (4 hour threshold)
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

    # If we have critical warnings, mark as invalid
    if any("no longer exists" in w for w in result['warnings']):
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
        session_id_or_alias: UUID (full or partial), "latest", "last", or compound alias
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
    # Check if it's an alias
    if not session_id_or_alias.startswith("latest") and session_id_or_alias != "last":
        # Regular UUID (partial or full) - resolve via database
        return _resolve_partial_uuid(session_id_or_alias)

    # Parse alias
    alias = session_id_or_alias
    if alias == "last":
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
    return session_id_or_alias.startswith("latest") or session_id_or_alias == "last"


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
        'tmux:%0'

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
    tmux_pane = os.environ.get('TMUX_PANE')
    if tmux_pane:
        instance_id = f"tmux:{tmux_pane}"
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
    status: str = "open"
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
    """
    import os
    import time
    import tempfile

    # Use instance-aware filename for multi-instance isolation
    suffix = _get_instance_suffix()
    from pathlib import Path
    local_empirica = Path.cwd() / '.empirica'
    if local_empirica.exists():
        path = local_empirica / f'active_transaction{suffix}.json'
    else:
        path = Path.home() / '.empirica' / f'active_transaction{suffix}.json'

    path.parent.mkdir(parents=True, exist_ok=True)

    tx_data = {
        "transaction_id": transaction_id,
        "session_id": session_id,
        "preflight_timestamp": preflight_timestamp or time.time(),
        "status": status,
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


def read_active_transaction() -> Optional[str]:
    """Read the active transaction ID from the tracking file. Returns None if no active transaction."""
    from pathlib import Path
    suffix = _get_instance_suffix()
    # Search local then global - use .json extension to match write_active_transaction
    for base in [Path.cwd() / '.empirica', Path.home() / '.empirica']:
        candidate = base / f'active_transaction{suffix}.json'
        if candidate.exists():
            try:
                with open(candidate, 'r') as f:
                    data = json.load(f)
                    return data.get('transaction_id')
            except Exception:
                pass
    return None


def clear_active_transaction() -> None:
    """Remove the active transaction tracking file (called on POSTFLIGHT)."""
    from pathlib import Path
    suffix = _get_instance_suffix()
    for base in [Path.cwd() / '.empirica', Path.home() / '.empirica']:
        candidate = base / f'active_transaction{suffix}.json'
        if candidate.exists():
            try:
                candidate.unlink()
            except Exception:
                pass
