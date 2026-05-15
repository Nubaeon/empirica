"""Tests for empirica.core.loop_scheduler.systemd.

Mocks `subprocess.run` so tests don't require a real systemd-user environment.
Filesystem effects (unit file writes) are exercised against tmp_path; we patch
`_systemd_user_dir` to point there.

The scheduler is the Phase 1a scaffolding for the systemd-decoupled loop
firing mechanism (goal f718156c). Tests assert:
  - unit-name slugging is filesystem-safe + readable
  - enable() writes timer + service files + invokes systemctl daemon-reload + enable
  - disable() is idempotent (no raise if loop never installed)
  - status() parses is-active / is-enabled into a typed LoopStatus
  - tick() appends a JSON event to the fires log (the Monitor bridge target)
"""

from __future__ import annotations

import json
import subprocess
from unittest.mock import patch

import pytest

from empirica.core.loop_scheduler import systemd as scheduler_mod
from empirica.core.loop_scheduler.systemd import (
    LoopStatus,
    SystemdLoopScheduler,
    SystemdUnavailable,
    _unit_name,
)


@pytest.fixture
def fake_systemd_env(tmp_path, monkeypatch):
    """Redirect ~/.config/systemd/user and ~/.empirica to tmp_path. Stub
    is_systemd_available() to True so the constructor doesn't raise."""
    sysd = tmp_path / "systemd" / "user"
    empirica = tmp_path / "empirica_home"
    sysd.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(scheduler_mod, "_systemd_user_dir", lambda: sysd)
    monkeypatch.setattr(scheduler_mod, "_fires_log_path", lambda: empirica / "loop_fires.log")
    empirica.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(scheduler_mod, "is_systemd_available", lambda: True)
    return {"sysd": sysd, "empirica": empirica}


def _fake_run(stdout: str = "", stderr: str = "", returncode: int = 0):
    """Builds a fake subprocess.CompletedProcess for patching subprocess.run."""
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=stdout, stderr=stderr,
    )


# ── Slug safety ─────────────────────────────────────────────────────────


def test_unit_name_sanitizes_unsafe_chars():
    assert _unit_name("user@host", "loop/name") == "empirica-loop-user-host-loop-name"


def test_unit_name_idempotent_on_safe_input():
    assert _unit_name("cortex", "mailbox-poll") == "empirica-loop-cortex-mailbox-poll"


def test_unit_name_empty_falls_back_to_default():
    # An empty instance_id becomes 'default' to keep unit names non-degenerate.
    assert "default" in _unit_name("", "x")


# ── Constructor / availability ──────────────────────────────────────────


def test_constructor_raises_when_systemd_unavailable(monkeypatch):
    monkeypatch.setattr(scheduler_mod, "is_systemd_available", lambda: False)
    with pytest.raises(SystemdUnavailable):
        SystemdLoopScheduler()


# ── enable() ────────────────────────────────────────────────────────────


def test_enable_writes_unit_files_and_invokes_systemctl(fake_systemd_env):
    calls: list[tuple] = []

    def fake_run(args, **kw):
        calls.append(tuple(args))
        return _fake_run(stdout="active\n", returncode=0)

    with patch.object(subprocess, "run", fake_run):
        sched = SystemdLoopScheduler(empirica_bin="/usr/bin/empirica")
        paths = sched.enable("cortex", "mailbox-poll", "30s")

    assert paths.timer.exists()
    assert paths.service.exists()
    timer_content = paths.timer.read_text()
    service_content = paths.service.read_text()
    assert "OnUnitActiveSec=30s" in timer_content
    assert "Unit=empirica-loop-cortex-mailbox-poll.service" in timer_content
    assert "ExecStart=/usr/bin/empirica loop tick cortex mailbox-poll" in service_content

    # daemon-reload + enable --now must both fire
    flat = [" ".join(c) for c in calls]
    assert any("daemon-reload" in c for c in flat)
    assert any("enable --now empirica-loop-cortex-mailbox-poll.timer" in c for c in flat)


def test_enable_uses_default_empirica_bin_when_unspecified(fake_systemd_env):
    with patch.object(subprocess, "run", lambda *a, **kw: _fake_run(returncode=0)):
        sched = SystemdLoopScheduler()
        paths = sched.enable("inst", "loop", "1min")
    assert "ExecStart=empirica loop tick inst loop" in paths.service.read_text()


# ── disable() ───────────────────────────────────────────────────────────


def test_disable_is_idempotent_when_loop_never_installed(fake_systemd_env):
    with patch.object(subprocess, "run", lambda *a, **kw: _fake_run(returncode=0)):
        sched = SystemdLoopScheduler()
        # No prior enable — disable should not raise + return False
        result = sched.disable("ghost", "nonexistent")
    assert result is False


def test_disable_removes_unit_files_after_enable(fake_systemd_env):
    with patch.object(subprocess, "run", lambda *a, **kw: _fake_run(returncode=0)):
        sched = SystemdLoopScheduler()
        sched.enable("cortex", "poll", "30s")
        # Verify files exist
        paths = sched.unit_paths("cortex", "poll")
        assert paths.timer.exists() and paths.service.exists()

        result = sched.disable("cortex", "poll")

    assert result is True
    assert not paths.timer.exists()
    assert not paths.service.exists()


# ── status() ────────────────────────────────────────────────────────────


def test_status_reports_active_and_enabled(fake_systemd_env):
    responses = {
        "is-active": "active\n",
        "is-enabled": "enabled\n",
        "show": "LastTriggerUSec=Thu 2026-05-15 14:00:00 UTC\nNextElapseUSecRealtime=Thu 2026-05-15 14:00:30 UTC\n",
    }

    def fake_run(args, **kw):
        for key, out in responses.items():
            if key in args:
                return _fake_run(stdout=out, returncode=0)
        return _fake_run(stdout="", returncode=0)

    with patch.object(subprocess, "run", fake_run):
        sched = SystemdLoopScheduler()
        st = sched.status("cortex", "poll")

    assert isinstance(st, LoopStatus)
    assert st.active is True
    assert st.enabled is True
    assert st.last_trigger and "2026-05-15 14:00:00" in st.last_trigger
    assert st.next_trigger and "2026-05-15 14:00:30" in st.next_trigger


def test_status_reports_inactive_when_unit_missing(fake_systemd_env):
    # systemctl exits non-zero with "inactive" for unknown units
    def fake_run(args, **kw):
        if "is-active" in args:
            return _fake_run(stdout="inactive\n", returncode=3)
        if "is-enabled" in args:
            return _fake_run(stdout="disabled\n", returncode=1)
        return _fake_run(stdout="")

    with patch.object(subprocess, "run", fake_run):
        sched = SystemdLoopScheduler()
        st = sched.status("ghost", "absent")

    assert st.active is False
    assert st.enabled is False
    assert st.last_trigger is None


# ── list_enabled() ──────────────────────────────────────────────────────


def test_list_enabled_returns_unit_names_without_suffix(fake_systemd_env):
    fake_output = (
        "empirica-loop-cortex-mailbox-poll.timer enabled enabled\n"
        "empirica-loop-empirica-mailbox-poll.timer enabled enabled\n"
    )
    with patch.object(subprocess, "run", lambda *a, **kw: _fake_run(stdout=fake_output)):
        sched = SystemdLoopScheduler()
        units = sched.list_enabled()
    assert "empirica-loop-cortex-mailbox-poll" in units
    assert "empirica-loop-empirica-mailbox-poll" in units
    assert not any(u.endswith(".timer") for u in units)


# ── tick() — Monitor bridge target ──────────────────────────────────────


def test_tick_appends_json_event_to_fires_log(fake_systemd_env):
    log = fake_systemd_env["empirica"] / "loop_fires.log"
    # Reset (fixture may have created it empty)
    if log.exists():
        log.unlink()

    SystemdLoopScheduler.tick("cortex", "mailbox-poll")

    assert log.exists()
    lines = log.read_text().splitlines()
    assert len(lines) == 1
    ev = json.loads(lines[0])
    assert ev["instance_id"] == "cortex"
    assert ev["loop"] == "mailbox-poll"
    assert "ts" in ev


def test_tick_appends_not_truncates(fake_systemd_env):
    SystemdLoopScheduler.tick("a", "loop1")
    SystemdLoopScheduler.tick("a", "loop1")
    SystemdLoopScheduler.tick("b", "loop2")
    log = fake_systemd_env["empirica"] / "loop_fires.log"
    assert len(log.read_text().splitlines()) == 3


def test_tick_static_method_does_not_require_systemd(monkeypatch, fake_systemd_env):
    """tick() is the ExecStart target — it must work even on hosts without
    systemd-user (it just appends to a log file). No SystemdLoopScheduler
    instantiation needed."""
    monkeypatch.setattr(scheduler_mod, "is_systemd_available", lambda: False)
    # Should not raise — tick is a @staticmethod that doesn't need the class
    SystemdLoopScheduler.tick("inst", "name")
    log = fake_systemd_env["empirica"] / "loop_fires.log"
    assert log.exists()
