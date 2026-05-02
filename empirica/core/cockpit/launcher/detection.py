"""Abnormal-exit detection for the cockpit launcher.

Compares ``last_session_start`` mtime against ``last_clean_shutdown``
mtime + checks the active.lock PID. Three outcomes:
  - ``None`` — last shutdown was clean (start ≤ clean) OR no session
    has ever been launched
  - ``SessionAlreadyRunning`` — start > clean AND the locked PID is
    alive (cockpit is currently running, not abnormal)
  - ``AbnormalExit`` — start > clean AND no live PID. The cockpit
    died without writing a clean-shutdown marker.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from empirica.core.cockpit.launcher.state import (
    cockpit_status,
)


@dataclass
class AbnormalExit:
    """Set when start > clean and no live lock PID."""
    started_at: float
    duration_lost_seconds: float
    likely_cause: str  # 'reboot' | 'forced_kill' | 'oom' | 'unknown'


@dataclass
class SessionAlreadyRunning:
    """Set when start > clean and the lock PID is alive."""
    pid: int
    started_at: float


def _infer_cause(started_at: float) -> str:
    """Best-effort inference. Reboot is the only signal we can read
    portably without root; the others are placeholders for richer
    detection (dmesg parsing, journalctl) in v1.1."""
    try:
        with open('/proc/uptime', encoding='utf-8') as fh:
            uptime_seconds = float(fh.read().split()[0])
        boot_time = time.time() - uptime_seconds
        # If the system rebooted after the session started, that's
        # the most likely cause.
        if boot_time > started_at:
            return 'reboot'
    except (OSError, ValueError, IndexError):
        pass
    return 'unknown'


def detect_abnormal_exit() -> AbnormalExit | SessionAlreadyRunning | None:
    """Run the abnormal-exit decision tree. See module docstring for
    the three possible outcomes."""
    snap = cockpit_status()
    last_start = snap.last_session_start
    last_clean = snap.last_clean_shutdown

    # No launch has ever happened
    if last_start is None:
        return None

    # Last shutdown was clean (≥ start), nothing to flag
    if last_clean is not None and last_clean >= last_start:
        return None

    # Start > clean (or clean missing) AND lock PID alive → still running
    if snap.lock_pid is not None and snap.lock_alive:
        return SessionAlreadyRunning(pid=snap.lock_pid, started_at=last_start)

    # Start > clean AND no live PID → abnormal exit
    return AbnormalExit(
        started_at=last_start,
        duration_lost_seconds=max(0.0, time.time() - last_start),
        likely_cause=_infer_cause(last_start),
    )
