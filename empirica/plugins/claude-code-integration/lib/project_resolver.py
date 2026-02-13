"""
Project Resolver - Unified context resolution for Claude Code hooks

This module provides project/session resolution functions for hooks.
It wraps empirica.utils.session_resolver when available, with fallbacks
for standalone operation.

Functions:
    get_active_project_path(claude_session_id) - Get active project path
    get_instance_id() - Get instance identifier for multi-instance isolation
    get_active_session_id(claude_session_id) - Get active Empirica session ID
"""

import json
import os
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
