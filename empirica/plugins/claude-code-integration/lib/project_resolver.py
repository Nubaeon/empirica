"""
Project Resolver - Unified context resolution for Claude Code hooks

This module provides project/session resolution functions for hooks.
It wraps empirica.utils.session_resolver when available, with fallbacks
for standalone operation.

IMPORTANT: This module uses ONLY stdlib imports. Hooks run before the
empirica package is guaranteed available. The empirica imports inside
functions are optional (try/except ImportError).

Functions:
    get_instance_id() - Instance identifier for multi-instance isolation
    get_active_project_path(claude_session_id) - Active project path
    get_active_session_id(claude_session_id) - Active Empirica session ID
    find_project_root(claude_session_id, **) - Comprehensive project resolution
    has_valid_db(project_path) - Check if project has valid sessions.db
"""

import json
import os
import sqlite3
import subprocess
from pathlib import Path
from typing import Optional


def get_instance_id() -> Optional[str]:
    """
    Get a unique instance identifier for multi-instance isolation.

    Priority order:
    1. EMPIRICA_INSTANCE_ID env var (explicit override)
    2. TMUX_PANE (tmux terminal pane ID, e.g., "%0", "%1")
    3. TERM_SESSION_ID (macOS Terminal.app session ID)
    4. WINDOWID (X11 window ID)
    5. None (fallback to legacy behavior)

    Returns:
        Instance identifier string, or None for legacy behavior
    """
    # Try empirica import first
    try:
        from empirica.utils.session_resolver import get_instance_id as _get_instance_id
        return _get_instance_id()
    except ImportError:
        pass

    # Fallback implementation
    # Priority 1: Explicit override
    explicit_id = os.environ.get('EMPIRICA_INSTANCE_ID')
    if explicit_id:
        return explicit_id

    # Priority 2: tmux pane (most common for multi-instance work)
    tmux_pane = os.environ.get('TMUX_PANE')
    if tmux_pane:
        return f"tmux_{tmux_pane.lstrip('%')}"

    # Priority 3: macOS Terminal.app session
    term_session = os.environ.get('TERM_SESSION_ID')
    if term_session:
        return f"term:{term_session[:16]}"

    # Priority 4: X11 window ID
    window_id = os.environ.get('WINDOWID')
    if window_id:
        return f"x11:{window_id}"

    return None


def get_active_project_path(claude_session_id: str = None) -> Optional[str]:
    """
    Get the active project path for the current instance.

    Priority chain (NO CWD FALLBACK):
    1. instance_projects/{instance_id}.json - AUTHORITATIVE (updated by project-switch)
    2. active_work_{claude_session_id}.json - fallback (may be stale after project-switch)

    Args:
        claude_session_id: Optional Claude Code conversation UUID (from hook input)

    Returns:
        Absolute path to the project, or None if cannot be resolved.
    """
    # Try empirica import first
    try:
        from empirica.utils.session_resolver import get_active_project_path as _get_active_project_path
        return _get_active_project_path(claude_session_id)
    except ImportError:
        pass

    # Fallback implementation
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

    # PRIORITY: instance_projects wins (updated by project-switch)
    if instance_path:
        return instance_path

    # Fallback: active_work
    if active_work_path:
        return active_work_path

    return None


def get_active_session_id(claude_session_id: str = None) -> Optional[str]:
    """
    Get the active Empirica session ID for the current instance.

    Priority chain:
    1. Active transaction (TRANSACTION-FIRST - transaction survives compaction)
    2. active_work file (from project-switch/PREFLIGHT)
    3. instance_projects file (TMUX-based fallback)

    Args:
        claude_session_id: Optional Claude Code conversation UUID (from hook input)

    Returns:
        Empirica session UUID, or None if no active session found.
    """
    # Try empirica import first
    try:
        from empirica.utils.session_resolver import get_active_empirica_session_id
        return get_active_empirica_session_id(claude_session_id)
    except ImportError:
        pass

    # Fallback implementation
    project_path = get_active_project_path(claude_session_id)

    # Priority 1: Active transaction
    if project_path:
        instance_id = get_instance_id()
        suffix = f"_{instance_id}" if instance_id else ""
        tx_file = Path(project_path) / '.empirica' / f'active_transaction{suffix}.json'
        if tx_file.exists():
            try:
                with open(tx_file, 'r') as f:
                    tx_data = json.load(f)
                    if tx_data.get('status') == 'open':
                        session_id = tx_data.get('session_id')
                        if session_id:
                            return session_id
            except Exception:
                pass

    # Priority 2: active_work file
    if claude_session_id:
        active_work_file = Path.home() / '.empirica' / f'active_work_{claude_session_id}.json'
        if active_work_file.exists():
            try:
                with open(active_work_file, 'r') as f:
                    data = json.load(f)
                    session_id = data.get('empirica_session_id')
                    if session_id:
                        return session_id
            except Exception:
                pass

    # Priority 3: instance_projects (TMUX-based)
    instance_id = get_instance_id()
    if instance_id:
        instance_file = Path.home() / '.empirica' / 'instance_projects' / f'{instance_id}.json'
        if instance_file.exists():
            try:
                with open(instance_file, 'r') as f:
                    data = json.load(f)
                    session_id = data.get('empirica_session_id')
                    if session_id:
                        return session_id
            except Exception:
                pass

    return None


def has_valid_db(project_path: Path) -> bool:
    """Check if a project path has a valid .empirica/sessions/sessions.db."""
    db_path = project_path / '.empirica' / 'sessions' / 'sessions.db'
    if not db_path.exists():
        return False
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("SELECT 1 FROM sessions LIMIT 1")
        conn.close()
        return True
    except Exception:
        return False


def _find_git_root() -> Optional[Path]:
    """Find the git repo root from CWD."""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except Exception:
        pass
    return None


def _read_json_file(path: Path) -> Optional[dict]:
    """Read a JSON file, returning None on any error."""
    try:
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return None


def _scan_workspace_for_project(instance_id: Optional[str]) -> Optional[Path]:
    """Scan all registered projects in workspace.db for one with an open transaction."""
    workspace_db = Path.home() / '.empirica' / 'workspace' / 'workspace.db'
    if not workspace_db.exists():
        return None
    try:
        conn = sqlite3.connect(str(workspace_db))
        cursor = conn.execute("SELECT trajectory_path FROM global_projects")
        rows = cursor.fetchall()
        conn.close()
    except Exception:
        return None

    suffix = f"_{instance_id}" if instance_id else ""
    best_match = None
    best_mtime = 0

    for (traj_path,) in rows:
        if not traj_path:
            continue
        proj_path = Path(traj_path)
        tx_file = proj_path / '.empirica' / f'active_transaction{suffix}.json'
        if tx_file.exists():
            try:
                mtime = tx_file.stat().st_mtime
                tx_data = _read_json_file(tx_file)
                if tx_data and tx_data.get('status') == 'open':
                    tx_project = tx_data.get('project_path', str(proj_path))
                    if has_valid_db(Path(tx_project)) and mtime > best_mtime:
                        best_match = Path(tx_project)
                        best_mtime = mtime
            except Exception:
                continue

    return best_match


def find_project_root(
    claude_session_id: Optional[str] = None,
    *,
    check_compact_handoff: bool = False,
    allow_workspace_scan: bool = True,
    allow_cwd_fallback: bool = False,
    allow_git_root: bool = False,
) -> Optional[Path]:
    """
    Comprehensive project root resolution for hooks.

    Unified priority chain (highest to lowest):
    1. Compact handoff file (only if check_compact_handoff=True, for post-compact)
    2. Open transaction file (AUTHORITATIVE during transaction)
    3. active_work_{claude_session_id}.json
    4. instance_projects/{instance_id}.json
    5. Workspace scan (if allow_workspace_scan=True)
    6. EMPIRICA_WORKSPACE_ROOT env var
    7. Git repo root (if allow_git_root=True)
    8. CWD (if allow_cwd_fallback=True, for session-init only)

    Args:
        claude_session_id: Claude Code conversation UUID from hook input
        check_compact_handoff: Check compact handoff file (post-compact only)
        allow_workspace_scan: Scan workspace.db for projects with open transactions
        allow_cwd_fallback: Fall back to CWD as last resort
        allow_git_root: Try git repo root before CWD

    Returns:
        Path to project root, or None if cannot be resolved.
    """
    instance_id = get_instance_id()
    suffix = f"_{instance_id}" if instance_id else ""

    # Priority 1: Compact handoff (post-compact only)
    if check_compact_handoff and instance_id:
        handoff_file = Path.home() / '.empirica' / f'compact_handoff_{instance_id}.json'
        data = _read_json_file(handoff_file)
        if data:
            project_path = data.get('project_path')
            if project_path and has_valid_db(Path(project_path)):
                return Path(project_path)

    # Priority 2: Open transaction file
    # Check via active_work or instance_projects for project path first
    candidate_paths = set()

    if claude_session_id:
        aw_file = Path.home() / '.empirica' / f'active_work_{claude_session_id}.json'
        data = _read_json_file(aw_file)
        if data and data.get('project_path'):
            candidate_paths.add(data['project_path'])

    if instance_id:
        ip_file = Path.home() / '.empirica' / 'instance_projects' / f'{instance_id}.json'
        data = _read_json_file(ip_file)
        if data and data.get('project_path'):
            candidate_paths.add(data['project_path'])

    # Check each candidate for open transaction (most authoritative)
    for cpath in candidate_paths:
        tx_file = Path(cpath) / '.empirica' / f'active_transaction{suffix}.json'
        tx_data = _read_json_file(tx_file)
        if tx_data and tx_data.get('status') == 'open':
            tx_project = tx_data.get('project_path', cpath)
            if has_valid_db(Path(tx_project)):
                return Path(tx_project)

    # Priority 3-4: active_work / instance_projects (already in candidate_paths)
    # instance_projects is authoritative (updated by project-switch)
    if instance_id:
        ip_file = Path.home() / '.empirica' / 'instance_projects' / f'{instance_id}.json'
        data = _read_json_file(ip_file)
        if data and data.get('project_path'):
            p = Path(data['project_path'])
            if has_valid_db(p):
                return p

    if claude_session_id:
        aw_file = Path.home() / '.empirica' / f'active_work_{claude_session_id}.json'
        data = _read_json_file(aw_file)
        if data and data.get('project_path'):
            p = Path(data['project_path'])
            if has_valid_db(p):
                return p

    # Priority 5: Workspace scan
    if allow_workspace_scan:
        ws_result = _scan_workspace_for_project(instance_id)
        if ws_result:
            return ws_result

    # Priority 6: EMPIRICA_WORKSPACE_ROOT env var
    ws_root = os.environ.get('EMPIRICA_WORKSPACE_ROOT')
    if ws_root and has_valid_db(Path(ws_root)):
        return Path(ws_root)

    # Priority 7: Git repo root
    if allow_git_root:
        git_root = _find_git_root()
        if git_root and has_valid_db(git_root):
            return git_root

    # Priority 8: CWD (last resort)
    if allow_cwd_fallback:
        cwd = Path.cwd()
        if has_valid_db(cwd):
            return cwd
        # Also check git root from CWD
        git_root = _find_git_root()
        if git_root and has_valid_db(git_root):
            return git_root
        return cwd  # Return CWD even without valid DB (session-init creates it)

    return None
