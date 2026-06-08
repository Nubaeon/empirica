"""Tests for the listener liveness probe (silent-zombie defeater).

Closes mesh-support's prop_rbrlwiu7zfgkxm245guu6f2ala. The probe is a
separate daemon thread that os._exit(2)s when the most-recent
successful bearer-authenticated GET to cortex is older than the
fail-threshold — even when the main listener thread is hung inside a
catch-up HTTP call.
"""

from __future__ import annotations

import io
import json
import threading
import urllib.error
from pathlib import Path

import pytest

from empirica.core.loop_scheduler.liveness_probe import (
    LivenessProbe,
    _listener_health_path,
)


# Sentinel raised by the fake exit_fn so test code can assert on it
# without actually terminating the test process.
class _ExitCalled(Exception):
    def __init__(self, code: int) -> None:
        self.code = code


def _raising_exit(code: int) -> None:
    raise _ExitCalled(code)


def _stub_cortex_loader() -> dict[str, str]:
    return {"url": "https://cortex.test", "api_key": "ctx_test_key"}


def _stub_cortex_loader_empty() -> None:
    return None


# ── start / stop lifecycle ─────────────────────────────────────────────


def test_start_no_op_when_disabled(monkeypatch):
    monkeypatch.setenv("EMPIRICA_LIVENESS_PROBE_DISABLE", "1")
    err = io.StringIO()
    probe = LivenessProbe("empirica", _err_stream=err, _cortex_loader=_stub_cortex_loader)
    probe.start()
    assert probe._thread is None
    assert "liveness probe disabled" in err.getvalue()


def test_start_no_op_when_no_creds(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    err = io.StringIO()
    probe = LivenessProbe(
        "empirica", _err_stream=err, _cortex_loader=_stub_cortex_loader_empty,
        _probe_fn=lambda *a, **k: 200,
    )
    probe.start()
    probe._thread.join(timeout=1.0)  # type: ignore[union-attr]
    assert "no cortex credentials" in err.getvalue()


def test_start_is_idempotent():
    probe = LivenessProbe(
        "empirica",
        interval_sec=10.0,
        _cortex_loader=_stub_cortex_loader_empty,
    )
    probe.start()
    probe.start()  # idempotent
    probe.stop()


def test_stop_idempotent():
    probe = LivenessProbe(
        "empirica",
        interval_sec=10.0,
        _cortex_loader=_stub_cortex_loader_empty,
    )
    probe.stop()  # never started — no-op


# ── successful-probe path ──────────────────────────────────────────────


def test_successful_probe_writes_ok_marker(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    (tmp_path / ".empirica").mkdir()
    probes_run = threading.Event()

    def fake_probe(_url, _key):
        probes_run.set()
        return 200

    stop_after_first = threading.Event()

    def fake_sleep(_secs):
        # Wait until the first probe completes then signal stop so the loop exits.
        probes_run.wait(timeout=1.0)
        stop_after_first.set()
        # Tell the probe to stop by mutating its stop event from outside —
        # we'll set it explicitly below.

    probe = LivenessProbe(
        "empirica",
        interval_sec=60.0,
        fail_threshold_sec=240.0,
        _cortex_loader=_stub_cortex_loader,
        _probe_fn=fake_probe,
        _sleep=fake_sleep,
        _exit_fn=_raising_exit,
    )
    probe.start()
    probes_run.wait(timeout=1.0)
    stop_after_first.wait(timeout=1.0)
    probe.stop(timeout=2.0)

    marker = _listener_health_path("empirica")
    assert marker.exists()
    body = json.loads(marker.read_text())
    assert body["status"] == "ok"
    assert body["source"] == "liveness_probe"
    assert body["instance_id"] == "empirica"


def test_successful_probe_resets_failure_counter():
    fake_now = [1_000_000.0]

    probe = LivenessProbe(
        "empirica",
        interval_sec=60.0,
        _cortex_loader=_stub_cortex_loader,
        _probe_fn=lambda u, k: 200,
        _now=lambda: fake_now[0],
    )
    probe._consecutive_failures = 7
    probe._last_ok_at = fake_now[0]
    probe._do_probe("https://cortex.test", "k")
    assert probe._consecutive_failures == 0
    assert probe._last_ok_at == fake_now[0]


# ── failed-probe path ──────────────────────────────────────────────────


def test_probe_miss_on_http_error_increments_counter():
    err = urllib.error.HTTPError("http://x", 500, "ISE", {}, None)
    probe = LivenessProbe(
        "empirica",
        _cortex_loader=_stub_cortex_loader,
        _probe_fn=lambda u, k: (_ for _ in ()).throw(err),
    )
    probe._do_probe("https://cortex.test", "k")
    assert probe._consecutive_failures == 1


def test_probe_miss_on_urlerror_increments_counter():
    probe = LivenessProbe(
        "empirica",
        _cortex_loader=_stub_cortex_loader,
        _probe_fn=lambda u, k: (_ for _ in ()).throw(
            urllib.error.URLError("network down")
        ),
    )
    probe._do_probe("https://cortex.test", "k")
    assert probe._consecutive_failures == 1


def test_probe_miss_on_4xx_status_increments_counter():
    probe = LivenessProbe(
        "empirica",
        _cortex_loader=_stub_cortex_loader,
        _probe_fn=lambda u, k: 403,
    )
    probe._do_probe("https://cortex.test", "k")
    assert probe._consecutive_failures == 1


# ── staleness → hard exit ──────────────────────────────────────────────


def test_staleness_past_threshold_exits_with_degraded_marker(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    (tmp_path / ".empirica").mkdir()
    fake_now = [1_000_000.0]
    probe = LivenessProbe(
        "empirica",
        interval_sec=60.0,
        fail_threshold_sec=240.0,
        _cortex_loader=_stub_cortex_loader,
        _probe_fn=lambda u, k: 200,
        _now=lambda: fake_now[0],
        _exit_fn=_raising_exit,
    )
    # Simulate last successful probe 300s ago — exceeds 240s threshold.
    probe._last_ok_at = fake_now[0] - 300.0
    with pytest.raises(_ExitCalled) as exc_info:
        probe._check_staleness()
    assert exc_info.value.code == 2

    marker = _listener_health_path("empirica")
    assert marker.exists()
    body = json.loads(marker.read_text())
    assert body["status"] == "degraded"
    assert "liveness_probe_stale" in body["reason"]


def test_staleness_under_threshold_does_not_exit():
    fake_now = [1_000_000.0]
    exit_calls: list[int] = []
    probe = LivenessProbe(
        "empirica",
        fail_threshold_sec=240.0,
        _cortex_loader=_stub_cortex_loader,
        _now=lambda: fake_now[0],
        _exit_fn=exit_calls.append,
    )
    probe._last_ok_at = fake_now[0] - 100.0  # 100s ago — fresh
    probe._check_staleness()
    assert exit_calls == []


def test_staleness_check_no_op_when_never_probed_ok():
    """If the probe has never seen a success, staleness check should not
    fire — the run-loop's first iteration always probes before checking,
    so this guards against a spurious exit before the first probe."""
    fake_now = [1_000_000.0]
    exit_calls: list[int] = []
    probe = LivenessProbe(
        "empirica",
        fail_threshold_sec=240.0,
        _cortex_loader=_stub_cortex_loader,
        _now=lambda: fake_now[0],
        _exit_fn=exit_calls.append,
    )
    probe._last_ok_at = None
    probe._check_staleness()
    assert exit_calls == []


# ── env overrides ──────────────────────────────────────────────────────


def test_env_override_interval(monkeypatch):
    monkeypatch.setenv("EMPIRICA_LIVENESS_PROBE_INTERVAL_SEC", "30")
    probe = LivenessProbe("empirica", _cortex_loader=_stub_cortex_loader)
    assert probe.interval_sec == 30.0


def test_env_override_threshold(monkeypatch):
    monkeypatch.setenv("EMPIRICA_LIVENESS_PROBE_FAIL_THRESHOLD_SEC", "120")
    probe = LivenessProbe("empirica", _cortex_loader=_stub_cortex_loader)
    assert probe.fail_threshold_sec == 120.0


def test_constructor_overrides_env(monkeypatch):
    monkeypatch.setenv("EMPIRICA_LIVENESS_PROBE_INTERVAL_SEC", "30")
    probe = LivenessProbe(
        "empirica", interval_sec=15.0, _cortex_loader=_stub_cortex_loader,
    )
    assert probe.interval_sec == 15.0


# ── integration: probe target shape ────────────────────────────────────


def test_probe_target_url_uses_roster_endpoint():
    """Smoke check that the probe shape matches what diagnose --cortex uses —
    proves both reachability and auth in one bearer-authenticated GET.
    """
    from empirica.core.loop_scheduler import liveness_probe as lp

    calls: list[tuple[str, str]] = []

    def fake_urlopen(req, timeout, context):
        calls.append((req.full_url, req.get_header("Authorization")))

        class _Resp:
            status = 200

            def read(self, _n=None):
                return b""

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        return _Resp()

    import urllib.request as _urlreq
    orig = _urlreq.urlopen
    _urlreq.urlopen = fake_urlopen
    try:
        status = lp._probe_cortex_roster("https://cortex.test", "ctx_key")
    finally:
        _urlreq.urlopen = orig

    assert status == 200
    assert calls[0][0] == "https://cortex.test/v1/users/me/roster"
    assert calls[0][1] == "Bearer ctx_key"


# ── end-to-end: hard exit on accumulated staleness ─────────────────────


def test_run_loop_exits_when_probes_keep_failing(tmp_path, monkeypatch):
    """The full _run loop should call exit_fn once probe failures push
    last_ok_at past the threshold. Simulates 'cortex unreachable for 5
    minutes' — supervisor restart is the desired outcome.
    """
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    (tmp_path / ".empirica").mkdir()

    # Time advances by interval (60s) each sleep call. The loop:
    # iter 1: probe fails, age = 0 - 0 = 0  -> no exit
    # iter 2: probe fails, age = 60 - 0 = 60 -> no exit
    # iter 3: probe fails, age = 120 - 0 = 120 -> no exit
    # iter 4: probe fails, age = 180 - 0 = 180 -> no exit
    # iter 5: probe fails, age = 240 - 0 = 240 -> still <= threshold
    # iter 6: probe fails, age = 300 - 0 = 300 -> EXIT
    fake_now = [0.0]

    def fake_sleep(secs):
        fake_now[0] += secs

    def fake_probe(_u, _k):
        raise urllib.error.URLError("cortex down")

    probe = LivenessProbe(
        "empirica",
        interval_sec=60.0,
        fail_threshold_sec=240.0,
        _cortex_loader=_stub_cortex_loader,
        _probe_fn=fake_probe,
        _now=lambda: fake_now[0],
        _sleep=fake_sleep,
        _exit_fn=_raising_exit,
    )
    with pytest.raises(_ExitCalled) as exc_info:
        probe._run()
    assert exc_info.value.code == 2

    marker = _listener_health_path("empirica")
    assert marker.exists()
    assert json.loads(marker.read_text())["status"] == "degraded"


def test_run_loop_keeps_probing_while_healthy(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    (tmp_path / ".empirica").mkdir()
    fake_now = [0.0]
    probe_count = [0]

    def fake_sleep(secs):
        fake_now[0] += secs
        if probe_count[0] >= 5:
            raise _ExitCalled(99)  # break the loop after 5 iterations

    def fake_probe(_u, _k):
        probe_count[0] += 1
        return 200

    probe = LivenessProbe(
        "empirica",
        interval_sec=60.0,
        fail_threshold_sec=240.0,
        _cortex_loader=_stub_cortex_loader,
        _probe_fn=fake_probe,
        _now=lambda: fake_now[0],
        _sleep=fake_sleep,
        _exit_fn=_raising_exit,
    )
    with pytest.raises(_ExitCalled) as exc_info:
        probe._run()
    # Only the sentinel _ExitCalled(99) should fire — never the
    # staleness exit, because probes kept succeeding.
    assert exc_info.value.code == 99
    assert probe_count[0] == 5
