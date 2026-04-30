"""Tests for empirica.core.cockpit.loop_registry.

Covers register/heartbeat/pause idempotency, validation, atomic writes,
and the auto-register-on-heartbeat behavior.
"""

from __future__ import annotations

import json

import pytest

from empirica.core.cockpit import loop_registry as lr


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    fake_dir = tmp_path / '.empirica'
    fake_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(lr, 'EMPIRICA_DIR', fake_dir)
    return fake_dir


def test_registry_empty_for_unknown_instance(fake_home):
    reg = lr.LoopRegistry('tmux_42')
    assert reg.list_loops() == []
    assert reg.get('nonexistent') is None


def test_register_creates_entry_and_persists(fake_home):
    reg = lr.LoopRegistry('tmux_42', label='outreach')
    entry = reg.register(
        name='inbox-poll',
        kind='cron',
        cron='*/5 * * * *',
        description='check inbox',
    )
    assert entry.name == 'inbox-poll'
    assert entry.kind == 'cron'

    reloaded = lr.LoopRegistry('tmux_42').get('inbox-poll')
    assert reloaded is not None
    assert reloaded.cron == '*/5 * * * *'

    # Verify on-disk JSON is well-formed
    on_disk = json.loads((fake_home / 'loops_tmux_42.json').read_text())
    assert on_disk['instance_id'] == 'tmux_42'
    assert on_disk['instance_label'] == 'outreach'
    assert 'inbox-poll' in on_disk['loops']


def test_register_is_idempotent_preserving_runtime_state(fake_home):
    reg = lr.LoopRegistry('tmux_42')
    reg.register(name='poll', kind='cron', cron='*/5 * * * *')
    reg.heartbeat('poll', status='ok', message='first run')

    # Re-register with new schedule — heartbeat history must survive
    reg.register(name='poll', kind='cron', cron='*/10 * * * *', description='updated')
    entry = reg.get('poll')
    assert entry is not None
    assert entry.cron == '*/10 * * * *'
    assert entry.description == 'updated'
    assert entry.last_run is not None
    assert entry.last_status == 'ok'
    assert entry.last_message == 'first run'


def test_unregister_removes_entry_and_pause_sidecar(fake_home):
    reg = lr.LoopRegistry('tmux_42')
    reg.register(name='poll', kind='monitor')
    lr.set_loop_paused('tmux_42', 'poll', True)
    assert lr.is_loop_paused('tmux_42', 'poll')

    assert reg.unregister('poll') is True
    assert reg.get('poll') is None
    assert not lr.is_loop_paused('tmux_42', 'poll')


def test_unregister_unknown_returns_false(fake_home):
    reg = lr.LoopRegistry('tmux_42')
    assert reg.unregister('never-existed') is False


def test_unregister_clears_pending_install_and_uninstall(fake_home, monkeypatch):
    """Regression: orphan-install gap. If pending install/uninstall files
    exist when unregister fires, they must be cleaned — otherwise the
    next prompt re-arms a loop that's no longer registered. Mirrors the
    listener registry test for symmetric coverage."""
    from empirica.core.cockpit import (
        loop_install_request as inst,
    )
    from empirica.core.cockpit import (
        loop_uninstall_request as uninst,
    )
    monkeypatch.setattr(inst, 'EMPIRICA_DIR', fake_home)
    monkeypatch.setattr(uninst, 'EMPIRICA_DIR', fake_home)

    reg = lr.LoopRegistry('tmux_42')
    reg.register(name='poll', kind='cron', cron='*/15 * * * *')

    install_path = inst.write_pending(
        'tmux_42', 'poll', interval='15m',
    )
    uninstall_path = uninst.write_pending(
        'tmux_42', 'poll', job_id='cron-job-xyz',
    )
    assert install_path.exists()
    assert uninstall_path.exists()

    reg.unregister('poll')
    assert not install_path.exists(), 'install pending must be cleaned'
    assert not uninstall_path.exists(), 'uninstall pending must be cleaned'


def test_heartbeat_auto_registers_when_missing(fake_home):
    reg = lr.LoopRegistry('tmux_42')
    entry = reg.heartbeat('orphan-loop', status='ok', message='auto-create')
    assert entry.name == 'orphan-loop'
    assert entry.kind == 'monitor'
    assert entry.last_status == 'ok'


def test_pause_resume_round_trip(fake_home):
    lr.set_loop_paused('tmux_42', 'poll', True)
    assert lr.is_loop_paused('tmux_42', 'poll')
    lr.set_loop_paused('tmux_42', 'poll', False)
    assert not lr.is_loop_paused('tmux_42', 'poll')


def test_set_interval_requires_existing_loop(fake_home):
    reg = lr.LoopRegistry('tmux_42')
    with pytest.raises(KeyError):
        reg.set_interval('absent', '10m')


def test_invalid_name_rejected(fake_home):
    reg = lr.LoopRegistry('tmux_42')
    with pytest.raises(ValueError):
        reg.register(name='', kind='monitor')
    with pytest.raises(ValueError):
        reg.register(name='has spaces', kind='monitor')
    with pytest.raises(ValueError):
        reg.register(name='-leading-dash', kind='monitor')


def test_invalid_kind_rejected(fake_home):
    reg = lr.LoopRegistry('tmux_42')
    with pytest.raises(ValueError):
        reg.register(name='valid', kind='not-a-kind')


def test_invalid_status_rejected(fake_home):
    reg = lr.LoopRegistry('tmux_42')
    reg.register(name='poll', kind='monitor')
    with pytest.raises(ValueError):
        reg.heartbeat('poll', status='maybe')


def test_corrupt_registry_json_recovers_to_empty(fake_home):
    (fake_home / 'loops_tmux_42.json').write_text('{not json')
    reg = lr.LoopRegistry('tmux_42')
    assert reg.list_loops() == []  # Survives the bad file


def test_atomic_write_doesnt_leave_tempfiles(fake_home):
    reg = lr.LoopRegistry('tmux_42')
    reg.register(name='poll', kind='monitor')
    leftovers = list(fake_home.glob('loops_tmux_42.json.*'))
    assert leftovers == [], f'leftover tempfiles: {leftovers}'


def test_pause_sidecar_path_is_per_loop(fake_home):
    p1 = lr.loop_pause_path('tmux_42', 'poll-a')
    p2 = lr.loop_pause_path('tmux_42', 'poll-b')
    assert p1 != p2
    assert p1.name == 'loop_paused_tmux_42_poll-a'
    assert p2.name == 'loop_paused_tmux_42_poll-b'


def test_constructor_requires_instance_id(fake_home):
    with pytest.raises(ValueError):
        lr.LoopRegistry('')


def test_unsafe_chars_in_instance_id_sanitized(fake_home):
    reg = lr.LoopRegistry('term/with%punct')
    reg.register(name='poll', kind='monitor')
    assert (fake_home / 'loops_term-withpunct.json').exists()
