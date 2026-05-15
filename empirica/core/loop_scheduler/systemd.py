"""Systemd-user backend for canonical loops.

Replaces Claude Code's in-session CronCreate as the firing mechanism for
canonical loops. The actual wake-from-idle bridge into a running Claude
session is handled by the Monitor tool (armed at SessionStart), tailing the
fires log this scheduler appends to.

Design (decision logged 2026-05-15, goal f718156c):

  systemd-user timer (cadence)
       ↓ fires per schedule
  service ExecStart=empirica loop tick <inst> <name>
       ↓ appends one JSON line to ~/.empirica/loop_fires.log
       ↓
  [Monitor armed in running Claude session]
       ↓ streams each new line as an event
  Claude reacts in-context (full epistemic state intact)

Public API:

  SystemdLoopScheduler(empirica_bin="empirica")
    .enable(instance_id, name, interval)   → installs timer+service, starts
    .disable(instance_id, name)             → stops + removes from systemctl
    .status(instance_id, name)              → {active, enabled, last_trigger}
    .list_enabled()                          → list of unit names
    .unit_paths(instance_id, name)           → (timer_path, service_path)

  is_systemd_available()                     → bool capability probe

Cross-platform: this module is Linux/WSL2 only. macOS (launchd) ships in
Phase 2 with the same scheduler protocol. is_systemd_available() returns
False on macOS/Windows-native so callers can graceful-degrade.
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


# Sanitize instance_id / loop name for unit-file naming. systemd accepts
# [A-Za-z0-9:-_.\\] in unit names but we want our paths URL-safe + readable.
def _safe(s: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_") else "-" for c in s) or "default"


def _unit_name(instance_id: str, name: str) -> str:
    return f"empirica-loop-{_safe(instance_id)}-{_safe(name)}"


def _systemd_user_dir() -> Path:
    """`~/.config/systemd/user/` — created idempotently."""
    p = Path.home() / ".config" / "systemd" / "user"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _fires_log_path() -> Path:
    """`~/.empirica/loop_fires.log` — single tail target for the Monitor bridge."""
    p = Path.home() / ".empirica"
    p.mkdir(parents=True, exist_ok=True)
    return p / "loop_fires.log"


class SystemdUnavailable(RuntimeError):
    """Raised when systemd-user operations are attempted on a host without it."""


def is_systemd_available() -> bool:
    """Probe `systemctl --user is-system-running` returns ANY exit code → OK.

    We only need systemctl to exist and respond — even a "degraded" reply is
    fine; the timers/services we own still work. Hosts without systemd (macOS,
    Windows-native, minimal Alpine) lack systemctl entirely.
    """
    if shutil.which("systemctl") is None:
        return False
    try:
        # --user with no DBus user-bus → exits non-zero with stderr "Failed to
        # connect to bus". We don't care about exit code; the binary must just
        # respond. Timeout 2s — anything hung means broken environment.
        r = subprocess.run(
            ["systemctl", "--user", "is-system-running"],
            capture_output=True, text=True, timeout=2, check=False,
        )
        # If the binary ran (even with non-zero exit), systemd-user is callable.
        # The real availability test happens when we actually enable a timer.
        return "Failed to connect to bus" not in (r.stderr or "")
    except Exception:
        return False


def _systemctl(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    """Run `systemctl --user <args>` with a short timeout."""
    return subprocess.run(
        ["systemctl", "--user", *args],
        capture_output=True, text=True, timeout=5, check=check,
    )


@dataclass
class LoopUnitFiles:
    """Resolved on-disk paths for one loop's systemd units."""
    timer: Path
    service: Path


@dataclass
class LoopStatus:
    """systemctl is-active / is-enabled result + last trigger timestamp."""
    name: str
    active: bool
    enabled: bool
    last_trigger: str | None = None
    next_trigger: str | None = None


# ── Unit-file templates ──────────────────────────────────────────────────


_SERVICE_TEMPLATE = """\
[Unit]
Description=Empirica canonical loop tick — {name} (instance: {instance_id})
After=default.target

[Service]
Type=oneshot
ExecStart={empirica_bin} loop tick {instance_id} {name}
# Append-only — failures here should not propagate to the timer. The body
# skill reacts to log lines via the Monitor bridge; even a missed tick is
# recoverable on the next interval.
SuccessExitStatus=0
"""

_TIMER_TEMPLATE = """\
[Unit]
Description=Empirica canonical loop timer — {name} (instance: {instance_id})

[Timer]
# Cadence — every {interval}. AccuracySec keeps systemd from coalescing
# multiple loop timers into one fire if they happen to align.
OnUnitActiveSec={interval}
OnBootSec={interval}
AccuracySec=1s
Unit={unit_name}.service

[Install]
WantedBy=timers.target
"""


# ── Scheduler ────────────────────────────────────────────────────────────


class SystemdLoopScheduler:
    """Manages loop timers via systemd-user.

    Stateless — the source of truth for "is this loop running?" lives in
    systemd itself (`systemctl --user is-active`). This class only knows
    where to write unit files + how to invoke systemctl.

    Args:
        empirica_bin: Absolute path to the `empirica` CLI binary used in
            the service's ExecStart. Defaults to the bare command — relies
            on the user's PATH at timer-fire time. For installer use,
            resolve this to `shutil.which('empirica')` so the unit file
            captures the canonical path (resilient to PATH drift).
    """

    def __init__(self, empirica_bin: str = "empirica"):
        self.empirica_bin = empirica_bin
        if not is_systemd_available():
            raise SystemdUnavailable(
                "systemd-user not available on this host — "
                "macOS uses launchd (Phase 2), Windows-native uses Task Scheduler (Phase 3); "
                "Linux+WSL2 should have it."
            )

    # ── Path resolution ──────────────────────────────────────────────────

    def unit_paths(self, instance_id: str, name: str) -> LoopUnitFiles:
        base = _systemd_user_dir()
        unit = _unit_name(instance_id, name)
        return LoopUnitFiles(
            timer=base / f"{unit}.timer",
            service=base / f"{unit}.service",
        )

    # ── Write + register ─────────────────────────────────────────────────

    def enable(self, instance_id: str, name: str, interval: str) -> LoopUnitFiles:
        """Write the .timer + .service unit files, daemon-reload, enable+start.

        Args:
            instance_id: cockpit slot name (e.g. 'cortex', 'empirica').
            name: canonical loop name (e.g. 'cortex-mailbox-poll').
            interval: systemd time spec (e.g. '30s', '5min', '1h').

        Returns:
            LoopUnitFiles with on-disk paths (timer + service).

        Raises:
            subprocess.CalledProcessError on systemctl failures.
        """
        paths = self.unit_paths(instance_id, name)
        unit_name = _unit_name(instance_id, name)

        paths.service.write_text(
            _SERVICE_TEMPLATE.format(
                name=name, instance_id=instance_id,
                empirica_bin=self.empirica_bin,
            ),
            encoding="utf-8",
        )
        paths.timer.write_text(
            _TIMER_TEMPLATE.format(
                name=name, instance_id=instance_id,
                interval=interval, unit_name=unit_name,
            ),
            encoding="utf-8",
        )

        _systemctl("daemon-reload", check=True)
        _systemctl("enable", "--now", f"{unit_name}.timer", check=True)
        logger.info(f"systemd loop enabled: {unit_name}.timer (every {interval})")
        return paths

    def disable(self, instance_id: str, name: str) -> bool:
        """Stop + disable the timer, remove the unit files.

        Returns True if anything was removed, False if the loop wasn't installed.
        Never raises on a non-existent loop — disable is idempotent by design.
        """
        paths = self.unit_paths(instance_id, name)
        unit_name = _unit_name(instance_id, name)
        removed = False

        if paths.timer.exists() or paths.service.exists():
            _systemctl("disable", "--now", f"{unit_name}.timer", check=False)
            if paths.timer.exists():
                paths.timer.unlink()
                removed = True
            if paths.service.exists():
                paths.service.unlink()
                removed = True
            _systemctl("daemon-reload", check=False)
            logger.info(f"systemd loop disabled: {unit_name}.timer")
        return removed

    # ── Inspect ──────────────────────────────────────────────────────────

    def status(self, instance_id: str, name: str) -> LoopStatus:
        """Query systemd for is-active + is-enabled + (optionally) trigger times."""
        unit_name = _unit_name(instance_id, name)
        timer_unit = f"{unit_name}.timer"

        active = _systemctl("is-active", timer_unit).stdout.strip() == "active"
        enabled = _systemctl("is-enabled", timer_unit).stdout.strip() == "enabled"

        last_trigger: str | None = None
        next_trigger: str | None = None
        if active:
            r = _systemctl(
                "show", timer_unit,
                "--property=LastTriggerUSec,NextElapseUSecRealtime",
            )
            for ln in r.stdout.splitlines():
                if "=" not in ln:
                    continue
                k, v = ln.split("=", 1)
                if k == "LastTriggerUSec" and v and v != "n/a":
                    last_trigger = v
                elif k == "NextElapseUSecRealtime" and v and v != "n/a":
                    next_trigger = v

        return LoopStatus(
            name=name,
            active=active,
            enabled=enabled,
            last_trigger=last_trigger,
            next_trigger=next_trigger,
        )

    def list_enabled(self) -> list[str]:
        """Return unit names (without .timer suffix) for all empirica-loop-* timers
        that systemd currently knows about. Includes both active and inactive."""
        # `list-timers --all` shows all timers including inactive
        r = _systemctl("list-unit-files", "empirica-loop-*.timer", "--no-legend")
        out: list[str] = []
        for ln in r.stdout.splitlines():
            parts = ln.split()
            if parts and parts[0].endswith(".timer"):
                out.append(parts[0].removesuffix(".timer"))
        return out

    # ── Tick (service ExecStart target) ──────────────────────────────────

    @staticmethod
    def tick(instance_id: str, name: str) -> Path:
        """Append one JSON line to the fires log — the Monitor bridge target.

        Called by the systemd service's ExecStart. Idempotent + cheap so a
        failing tick doesn't escalate (the next interval will fire again).

        Returns the path of the fires log (caller may want to log it).
        """
        import datetime as _dt

        path = _fires_log_path()
        event = {
            "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
            "instance_id": instance_id,
            "loop": name,
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
        return path


# ── Convenience: instance-scoped discovery (used by SessionStart hook) ───


def list_active_loops_for_instance(instance_id: str) -> list[str]:
    """Names of canonical loops with an active systemd timer for this instance.

    Returns loop names (not unit names) — e.g. ['cortex-mailbox-poll'].
    Empty list when systemd isn't available or no loops are enabled, never
    raises. Caller uses this to decide whether to arm a Monitor at SessionStart.
    """
    if not is_systemd_available():
        return []
    try:
        r = _systemctl(
            "list-unit-files", "empirica-loop-*.timer", "--no-legend",
        )
    except Exception:
        return []

    safe_inst = _safe(instance_id)
    prefix = f"empirica-loop-{safe_inst}-"
    loops: list[str] = []
    for ln in r.stdout.splitlines():
        parts = ln.split()
        if not parts or not parts[0].endswith(".timer"):
            continue
        unit = parts[0].removesuffix(".timer")
        if not unit.startswith(prefix):
            continue
        loop_name = unit.removeprefix(prefix)
        # Only count timers that are actually active (running), not just
        # installed-but-disabled.
        try:
            chk = _systemctl("is-active", f"{unit}.timer")
            if chk.stdout.strip() == "active":
                loops.append(loop_name)
        except Exception:
            continue
    return loops
