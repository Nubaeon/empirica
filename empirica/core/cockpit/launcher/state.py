"""Cockpit launcher state files — ``~/.empirica/cockpit/``.

Three files:
  - ``last_session_start``  written on every ``cockpit launch``
  - ``last_clean_shutdown`` written on graceful exit (kill, detach trap)
  - ``active.lock``         PID lockfile while session active

Abnormal-exit detection compares mtime of the first two; ``active.lock``
distinguishes "still running" from "abnormal" when the start mtime
exceeds the clean-shutdown mtime.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

COCKPIT_DIR = Path.home() / '.empirica' / 'cockpit'
LAST_SESSION_START_PATH = COCKPIT_DIR / 'last_session_start'
LAST_CLEAN_SHUTDOWN_PATH = COCKPIT_DIR / 'last_clean_shutdown'
LOCK_PATH = COCKPIT_DIR / 'active.lock'


def _ensure_dir() -> None:
    COCKPIT_DIR.mkdir(parents=True, exist_ok=True)


def _touch(path: Path) -> None:
    """Write current epoch seconds to a file (mtime + content match)."""
    _ensure_dir()
    with path.open('w', encoding='utf-8') as fh:
        fh.write(str(int(time.time())))


def write_session_start() -> Path:
    """Mark a cockpit launch. Returns the written path."""
    _touch(LAST_SESSION_START_PATH)
    return LAST_SESSION_START_PATH


def write_clean_shutdown() -> Path:
    """Mark a graceful detach/kill. Returns the written path."""
    _touch(LAST_CLEAN_SHUTDOWN_PATH)
    # Clear the lock if it exists — clean shutdown ends the session.
    try:
        if LOCK_PATH.exists():
            LOCK_PATH.unlink()
    except OSError:
        pass
    return LAST_CLEAN_SHUTDOWN_PATH


def write_lock(pid: int | None = None) -> Path:
    """Write the active.lock with the given PID (defaults to current)."""
    _ensure_dir()
    target_pid = pid if pid is not None else os.getpid()
    with LOCK_PATH.open('w', encoding='utf-8') as fh:
        fh.write(str(target_pid))
    return LOCK_PATH


def read_lock_pid() -> int | None:
    """Return the PID recorded in active.lock, or None if missing/invalid."""
    if not LOCK_PATH.exists():
        return None
    try:
        text = LOCK_PATH.read_text(encoding='utf-8').strip()
        return int(text)
    except (OSError, ValueError):
        return None


def pid_alive(pid: int) -> bool:
    """Cheap liveness check via ``os.kill(pid, 0)``."""
    if pid <= 1:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError, OSError):
        return False


def _mtime(path: Path) -> float | None:
    try:
        return path.stat().st_mtime
    except OSError:
        return None


@dataclass
class CockpitStateSnapshot:
    """Read-only summary of cockpit state files."""
    last_session_start: float | None
    last_clean_shutdown: float | None
    lock_pid: int | None
    lock_alive: bool

    def has_clean_state(self) -> bool:
        """True when nothing is running and the last shutdown was clean."""
        if self.lock_alive:
            return False
        if self.last_session_start is None:
            return True
        if self.last_clean_shutdown is None:
            return False
        return self.last_clean_shutdown >= self.last_session_start


def cockpit_status() -> CockpitStateSnapshot:
    """Snapshot the cockpit state files for diagnostic / status renders."""
    pid = read_lock_pid()
    return CockpitStateSnapshot(
        last_session_start=_mtime(LAST_SESSION_START_PATH),
        last_clean_shutdown=_mtime(LAST_CLEAN_SHUTDOWN_PATH),
        lock_pid=pid,
        lock_alive=pid_alive(pid) if pid is not None else False,
    )
