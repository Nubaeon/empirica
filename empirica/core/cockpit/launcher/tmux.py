"""Tmux command wrappers for the cockpit launcher.

Subprocess shell-outs to the system ``tmux`` binary. Idempotent —
``launch_cockpit`` attaches to an existing session if one is already
running with the configured ``session_name``.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

from empirica.core.cockpit.launcher.config import LauncherConfig
from empirica.core.cockpit.launcher.state import (
    write_clean_shutdown,
    write_lock,
    write_session_start,
)


@dataclass
class LaunchResult:
    """Returned by ``launch_cockpit``. Lets the caller decide whether
    to attach interactively or print a summary."""
    session_name: str
    created: bool          # True if a new session was created; False if attached to existing
    windows_created: list[str]
    status_windows_created: list[str]
    error: str | None = None


def _tmux(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    """Run a tmux command, capturing output. Doesn't raise on non-zero
    by default — callers inspect ``returncode`` and ``stderr``."""
    return subprocess.run(
        ['tmux', *args],
        capture_output=True,
        text=True,
        check=check,
        timeout=10,
    )


def tmux_available() -> bool:
    """True iff the ``tmux`` binary is on PATH."""
    return shutil.which('tmux') is not None


def cockpit_session_exists(session_name: str) -> bool:
    """Check whether a tmux session with the given name is running."""
    if not tmux_available():
        return False
    result = _tmux('has-session', '-t', session_name)
    return result.returncode == 0


def launch_cockpit(
    config: LauncherConfig,
    attach: bool | None = None,
) -> LaunchResult:
    """Bring up the canonical layout per ``config``. Idempotent —
    attaches to an existing session if one already exists.

    Args:
        config: Loaded launcher config.
        attach: Override config.attach_on_launch when set.

    Returns:
        ``LaunchResult`` with what was created and an optional error.
        The caller does the actual attach (subprocess.run with
        ``tmux attach`` taking over stdin/stdout) — this function
        only sets up the layout.
    """
    if not tmux_available():
        return LaunchResult(
            session_name=config.session_name,
            created=False,
            windows_created=[],
            status_windows_created=[],
            error='tmux binary not found on PATH',
        )

    # Idempotent: if the session exists, just record we're attaching.
    if cockpit_session_exists(config.session_name):
        return LaunchResult(
            session_name=config.session_name,
            created=False,
            windows_created=[],
            status_windows_created=[],
        )

    # Create the session with the first project as the initial window so
    # tmux doesn't open an extra empty window we'd have to close.
    if not config.projects and not config.status_windows:
        return LaunchResult(
            session_name=config.session_name,
            created=False,
            windows_created=[],
            status_windows_created=[],
            error='config has no projects and no status windows — nothing to launch',
        )

    write_session_start()

    windows_created: list[str] = []
    status_windows_created: list[str] = []

    # Initial window — first project, or first status window if no projects.
    if config.projects:
        first = config.projects[0]
        result = _tmux(
            'new-session', '-d',
            '-s', config.session_name,
            '-n', first.name,
            '-c', first.path,
            first.launch,
        )
        if result.returncode != 0:
            return LaunchResult(
                session_name=config.session_name,
                created=False,
                windows_created=[],
                status_windows_created=[],
                error=f'tmux new-session failed: {result.stderr.strip() or result.stdout.strip()}',
            )
        windows_created.append(first.name)
        remaining_projects = config.projects[1:]
    else:
        # No projects — bootstrap with the first status window.
        first_status = config.status_windows[0]
        result = _tmux(
            'new-session', '-d',
            '-s', config.session_name,
            '-n', first_status.name,
            first_status.command,
        )
        if result.returncode != 0:
            return LaunchResult(
                session_name=config.session_name,
                created=False,
                windows_created=[],
                status_windows_created=[],
                error=f'tmux new-session failed: {result.stderr.strip() or result.stdout.strip()}',
            )
        status_windows_created.append(first_status.name)
        remaining_projects = []

    # Additional project windows
    for project in remaining_projects:
        result = _tmux(
            'new-window',
            '-t', config.session_name,
            '-n', project.name,
            '-c', project.path,
            project.launch,
        )
        if result.returncode == 0:
            windows_created.append(project.name)

    # Status windows (skip the first if we already used it as the bootstrap)
    if config.projects:
        status_iter = config.status_windows
    else:
        status_iter = config.status_windows[1:]
    for status in status_iter:
        result = _tmux(
            'new-window',
            '-t', config.session_name,
            '-n', status.name,
            status.command,
        )
        if result.returncode == 0:
            status_windows_created.append(status.name)

    # Lock file — records that the cockpit is now active.
    write_lock()

    return LaunchResult(
        session_name=config.session_name,
        created=True,
        windows_created=windows_created,
        status_windows_created=status_windows_created,
    )


def cockpit_kill(session_name: str = 'cockpit') -> tuple[bool, str | None]:
    """Destroy the tmux session and write the clean-shutdown marker.

    Returns ``(success, error_message)``. Returns ``(True, None)`` even
    if the session didn't exist (idempotent).
    """
    if not tmux_available():
        return False, 'tmux binary not found on PATH'

    if cockpit_session_exists(session_name):
        result = _tmux('kill-session', '-t', session_name)
        if result.returncode != 0:
            return False, f'tmux kill-session failed: {result.stderr.strip()}'

    # Clean shutdown marker even when the session didn't exist —
    # the operator's intent was to have the cockpit gone.
    write_clean_shutdown()
    return True, None
