"""Loop scheduler backends — systemd-user (Linux/WSL2), launchd (macOS Phase 2).

Decouples loop cadence from Claude Code's in-session CronCreate so loops can be
truly paused (`systemctl --user stop`) without depending on Claude cooperation,
while preserving wake-from-idle via the Monitor tool bridge (see goal f718156c
decision log).

Public API:
  - SystemdLoopScheduler — Phase 1a backend (Linux, WSL2-with-systemd)
  - is_systemd_available() — capability probe

Future:
  - LaunchdLoopScheduler (macOS Phase 2)
  - TaskSchedulerLoopScheduler (Windows native Phase 3 — most users on WSL2)
"""

from .systemd import (
    SystemdLoopScheduler,
    SystemdUnavailable,
    is_systemd_available,
)

__all__ = [
    "SystemdLoopScheduler",
    "SystemdUnavailable",
    "is_systemd_available",
]
