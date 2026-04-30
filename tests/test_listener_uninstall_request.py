"""Tests for listener_uninstall_request module + pause-handler-armed-listener path.

Covers item 4 of PROPOSAL_EVENT_LISTENER.md (uninstall side). Symmetric
mirror of test_loop_uninstall_request.py. The uninstall flow:
empirica listener pause sees an active runtime file → reads
monitor_task_id + curl_pid → writes pending uninstall → owning Claude's
UserPromptSubmit hook surfaces it → owning Claude TaskStops both.
"""

from __future__ import annotations

import json
from argparse import Namespace

import pytest

from empirica.core.cockpit import listener_registry as lr_mod
from empirica.core.cockpit import listener_uninstall_request as uninst_mod
from empirica.core.cockpit import sentinel_pause as sp_mod
from empirica.core.cockpit.listener_registry import (
    ListenerRegistry,
    listener_active_path,
)
from empirica.core.cockpit.listener_uninstall_request import (
    ListenerUninstallRequest,
    consume_pending,
    list_pending,
    pending_path,
    write_pending,
)


@pytest.fixture
def empirica_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(uninst_mod, 'EMPIRICA_DIR', tmp_path)
    monkeypatch.setattr(lr_mod, 'EMPIRICA_DIR', tmp_path)
    monkeypatch.setattr(sp_mod, 'EMPIRICA_DIR', tmp_path)
    return tmp_path


# ─── module unit tests ─────────────────────────────────────────────────────


class TestPendingPath:
    def test_basic(self, empirica_dir):
        p = pending_path('tmux_3', 'inbox')
        assert p == empirica_dir / 'listener_uninstall_pending_tmux_3_inbox.json'


class TestWritePending:
    def test_writes_file(self, empirica_dir):
        path = write_pending(
            instance_id='tmux_42',
            name='outreach',
            monitor_task_id='task_xyz',
            curl_pid=12345,
            requested_by='tmux_99',
        )
        data = json.loads(path.read_text())
        assert data['instance_id'] == 'tmux_42'
        assert data['name'] == 'outreach'
        assert data['monitor_task_id'] == 'task_xyz'
        assert data['curl_pid'] == 12345
        assert data['requested_by'] == 'tmux_99'
        assert data['reason'] == 'pause'

    def test_curl_pid_optional(self, empirica_dir):
        path = write_pending(
            instance_id='tmux_1', name='foo', monitor_task_id='tk',
        )
        data = json.loads(path.read_text())
        assert data['curl_pid'] is None

    def test_idempotent(self, empirica_dir):
        write_pending('tmux_1', 'foo', 'tk1')
        write_pending('tmux_1', 'foo', 'tk2')
        files = list(empirica_dir.glob('listener_uninstall_pending_*.json'))
        assert len(files) == 1
        assert json.loads(files[0].read_text())['monitor_task_id'] == 'tk2'


class TestListAndConsume:
    def test_list_filters_by_instance(self, empirica_dir):
        write_pending('tmux_1', 'a', 'tk-a')
        write_pending('tmux_2', 'b', 'tk-b')
        assert len(list_pending('tmux_1')) == 1
        assert len(list_pending('tmux_2')) == 1

    def test_consume_returns_and_deletes(self, empirica_dir):
        write_pending('tmux_1', 'foo', 'tk-1', curl_pid=42)
        reqs = consume_pending('tmux_1')
        assert len(reqs) == 1
        assert reqs[0].monitor_task_id == 'tk-1'
        assert reqs[0].curl_pid == 42
        assert not list(empirica_dir.glob('listener_uninstall_pending_*.json'))

    def test_consume_handles_corrupt(self, empirica_dir):
        (empirica_dir / 'listener_uninstall_pending_tmux_1_bad.json').write_text('{ broken')
        write_pending('tmux_1', 'good', 'tk')
        reqs = consume_pending('tmux_1')
        assert len(reqs) == 1
        assert reqs[0].name == 'good'


class TestDataclass:
    def test_round_trip(self, tmp_path):
        req = ListenerUninstallRequest(
            instance_id='tmux_1', name='foo',
            monitor_task_id='tk', curl_pid=42,
            requested_at='2026-04-30T09:00:00+00:00',
            requested_by='tmux_99', reason='pause',
        )
        p = tmp_path / 'p.json'
        p.write_text(json.dumps(req.to_dict()))
        loaded = ListenerUninstallRequest.from_path(p)
        assert loaded is not None
        assert loaded.curl_pid == 42

    def test_from_path_corrupt(self, tmp_path):
        p = tmp_path / 'bad.json'
        p.write_text('{ broken')
        assert ListenerUninstallRequest.from_path(p) is None

    def test_curl_pid_null_in_json(self, tmp_path):
        p = tmp_path / 'p.json'
        p.write_text(json.dumps({
            'instance_id': 'tmux_1', 'name': 'foo',
            'monitor_task_id': 'tk', 'curl_pid': None,
        }))
        loaded = ListenerUninstallRequest.from_path(p)
        assert loaded is not None
        assert loaded.curl_pid is None


# ─── pause-handler integration ─────────────────────────────────────────────


def _ns(**kwargs):
    defaults = {'output': 'json', 'instance': 'tmux_test'}
    defaults.update(kwargs)
    return Namespace(**defaults)


def _arm_listener(empirica_dir, name='foo', monitor_task_id='tk-monitor',
                   curl_pid=12345):
    """Set up a listener as if the body had armed it: register + write
    listener_active_*.json runtime metadata."""
    reg = ListenerRegistry('tmux_test')
    reg.register(name=name, topic='ntfy:t')
    active = listener_active_path('tmux_test', name)
    active.write_text(json.dumps({
        'monitor_task_id': monitor_task_id,
        'curl_task_id': 'tk-curl',
        'curl_pid': curl_pid,
        'armed_at': '2026-04-30T09:00:00+00:00',
    }))


class TestPauseHandlerWithActiveListener:
    def test_armed_listener_writes_pending_uninstall(self, empirica_dir, capsys):
        from empirica.cli.command_handlers.cockpit_commands import (
            handle_listener_pause_command,
        )
        _arm_listener(empirica_dir, name='foo',
                      monitor_task_id='tk-monitor', curl_pid=12345)

        rc = handle_listener_pause_command(_ns(name='foo'))
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out['ok'] is True
        assert out['paused'] is True
        assert out['monitor_task_id'] == 'tk-monitor'
        assert out['curl_pid'] == 12345
        assert out['uninstall_pending_path'] is not None

        # Pending uninstall file written
        files = list(empirica_dir.glob('listener_uninstall_pending_*.json'))
        assert len(files) == 1
        data = json.loads(files[0].read_text())
        assert data['monitor_task_id'] == 'tk-monitor'
        assert data['curl_pid'] == 12345

    def test_disarmed_listener_no_pending(self, empirica_dir, capsys):
        """Listener registered but no active runtime file — pause is
        advisory only, no pending uninstall written."""
        from empirica.cli.command_handlers.cockpit_commands import (
            handle_listener_pause_command,
        )
        reg = ListenerRegistry('tmux_test')
        reg.register(name='foo', topic='ntfy:t')

        rc = handle_listener_pause_command(_ns(name='foo'))
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out['paused'] is True
        assert out['uninstall_pending_path'] is None
        assert not list(empirica_dir.glob('listener_uninstall_pending_*.json'))

    def test_corrupt_active_file_falls_back_to_advisory(self, empirica_dir, capsys):
        """If listener_active_*.json is unparseable, pause flag is still
        set but no pending uninstall is written (degrades gracefully —
        body pause-check at next wake is the backstop)."""
        from empirica.cli.command_handlers.cockpit_commands import (
            handle_listener_pause_command,
        )
        reg = ListenerRegistry('tmux_test')
        reg.register(name='foo', topic='ntfy:t')
        active = listener_active_path('tmux_test', 'foo')
        active.write_text('{ broken json')

        rc = handle_listener_pause_command(_ns(name='foo'))
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out['paused'] is True
        assert out['uninstall_pending_path'] is None
