"""Tests for listener_install_request module + install-request command handler.

Covers item 4 of PROPOSAL_EVENT_LISTENER.md (install side). Symmetric
mirror of test_loop_install_request.py. The install-request flow:
cockpit writes a pending install file → owning instance's UserPromptSubmit
hook surfaces it as a system-reminder → owning Claude runs the
inbox-listener skill → curl + Monitor armed → listener_active_*.json
written by the body.
"""

from __future__ import annotations

import json
from argparse import Namespace

import pytest

from empirica.core.cockpit import listener_install_request as inst_mod
from empirica.core.cockpit import listener_registry as lr_mod
from empirica.core.cockpit import sentinel_pause as sp_mod
from empirica.core.cockpit.listener_install_request import (
    ListenerInstallRequest,
    consume_pending,
    list_pending,
    pending_path,
    render_inbox_listener_prompt,
    write_pending,
)
from empirica.core.cockpit.listener_registry import ListenerRegistry


@pytest.fixture
def empirica_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(inst_mod, 'EMPIRICA_DIR', tmp_path)
    monkeypatch.setattr(lr_mod, 'EMPIRICA_DIR', tmp_path)
    monkeypatch.setattr(sp_mod, 'EMPIRICA_DIR', tmp_path)
    return tmp_path


# ─── path / list / consume ─────────────────────────────────────────────────


class TestPendingPath:
    def test_basic(self, empirica_dir):
        p = pending_path('tmux_3', 'inbox')
        assert p == empirica_dir / 'listener_install_pending_tmux_3_inbox.json'

    def test_sanitizes(self, empirica_dir):
        p = pending_path('tmux/3', 'a/b')
        assert '/' not in p.name


class TestWritePending:
    def test_writes_file_with_payload(self, empirica_dir):
        path = write_pending(
            instance_id='tmux_42',
            name='outreach',
            topic='ntfy:outreach-claude-inbox',
            description='cortex',
            on_wake_template='Process inbox',
            requested_by='tmux_99',
        )
        assert path.exists()
        data = json.loads(path.read_text())
        assert data['instance_id'] == 'tmux_42'
        assert data['name'] == 'outreach'
        assert data['topic'] == 'ntfy:outreach-claude-inbox'
        assert data['description'] == 'cortex'
        assert data['on_wake_template'] == 'Process inbox'
        assert data['requested_by'] == 'tmux_99'
        assert data['requested_at']
        # Substituted prompt template should mention the listener name
        assert 'outreach' in data['prompt_template']
        assert 'ntfy:outreach-claude-inbox' in data['prompt_template']

    def test_idempotent_overwrites(self, empirica_dir):
        write_pending('tmux_1', 'foo', 'ntfy:a')
        write_pending('tmux_1', 'foo', 'ntfy:b')  # rewrite same target
        files = list(empirica_dir.glob('listener_install_pending_*.json'))
        assert len(files) == 1
        assert json.loads(files[0].read_text())['topic'] == 'ntfy:b'


class TestListAndConsume:
    def test_list_filtered_by_instance(self, empirica_dir):
        write_pending('tmux_1', 'a', 'ntfy:1')
        write_pending('tmux_1', 'b', 'ntfy:2')
        write_pending('tmux_2', 'c', 'ntfy:3')
        for_1 = list_pending('tmux_1')
        assert len(for_1) == 2

    def test_consume_returns_and_deletes(self, empirica_dir):
        write_pending('tmux_1', 'foo', 'ntfy:t')
        reqs = consume_pending('tmux_1')
        assert len(reqs) == 1
        assert reqs[0].name == 'foo'
        assert empirica_dir.glob('listener_install_pending_*') is not None
        assert not list(empirica_dir.glob('listener_install_pending_*.json'))

    def test_consume_handles_corrupt(self, empirica_dir):
        (empirica_dir / 'listener_install_pending_tmux_1_bad.json').write_text('{ broken')
        write_pending('tmux_1', 'good', 'ntfy:t')
        reqs = consume_pending('tmux_1')
        assert len(reqs) == 1
        assert reqs[0].name == 'good'


# ─── prompt template rendering ─────────────────────────────────────────────


class TestRenderPrompt:
    def test_substitutes_name_and_topic(self):
        prompt = render_inbox_listener_prompt(
            name='myinbox',
            topic='ntfy:my-channel',
            description='test',
            on_wake_template='Process X',
        )
        assert 'myinbox' in prompt
        assert 'ntfy:my-channel' in prompt
        assert 'Process X' in prompt
        assert '/inbox-listener' in prompt

    def test_default_on_wake_when_empty(self):
        prompt = render_inbox_listener_prompt(name='x', topic='ntfy:t')
        # Should still produce a coherent prompt
        assert 'x' in prompt
        assert 'ntfy:t' in prompt


# ─── dataclass round-trip ──────────────────────────────────────────────────


class TestDataclass:
    def test_to_from_dict(self, tmp_path):
        req = ListenerInstallRequest(
            instance_id='tmux_1', name='foo', topic='ntfy:t',
            description='d', on_wake_template='ow',
            requested_at='2026-04-30T09:00:00+00:00',
            requested_by='tmux_99', prompt_template='[template]',
        )
        path = tmp_path / 'p.json'
        path.write_text(json.dumps(req.to_dict()))
        loaded = ListenerInstallRequest.from_path(path)
        assert loaded is not None
        assert loaded.name == 'foo'
        assert loaded.topic == 'ntfy:t'
        assert loaded.description == 'd'
        assert loaded.on_wake_template == 'ow'

    def test_from_path_corrupt_returns_none(self, tmp_path):
        p = tmp_path / 'bad.json'
        p.write_text('{ broken')
        assert ListenerInstallRequest.from_path(p) is None


# ─── command handler integration ───────────────────────────────────────────


def _ns(**kwargs):
    defaults = {'output': 'json', 'instance': 'tmux_test'}
    defaults.update(kwargs)
    return Namespace(**defaults)


class TestInstallRequestCommand:
    def test_registers_and_writes_pending(self, empirica_dir, capsys):
        from empirica.cli.command_handlers.cockpit_commands import (
            handle_listener_install_request_command,
        )
        rc = handle_listener_install_request_command(_ns(
            name='foo', topic='ntfy:t',
            description='d', on_wake='Process',
        ))
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out['ok'] is True
        assert out['listener']['name'] == 'foo'
        assert out['listener']['topic'] == 'ntfy:t'
        assert 'pending_path' in out

        # Listener registered in target's registry
        reg = ListenerRegistry('tmux_test')
        assert reg.get('foo') is not None
        # Pending install file written
        files = list(empirica_dir.glob('listener_install_pending_*.json'))
        assert len(files) == 1

    def test_requires_instance(self, empirica_dir, capsys):
        from empirica.cli.command_handlers.cockpit_commands import (
            handle_listener_install_request_command,
        )
        rc = handle_listener_install_request_command(Namespace(
            name='foo', topic='ntfy:t',
            description='', on_wake='', instance=None, output='json',
        ))
        assert rc == 1
        out = json.loads(capsys.readouterr().out)
        assert '--instance required' in out['error']

    def test_invalid_topic_rejected(self, empirica_dir, capsys):
        from empirica.cli.command_handlers.cockpit_commands import (
            handle_listener_install_request_command,
        )
        rc = handle_listener_install_request_command(_ns(
            name='foo', topic='not-a-url',
            description='', on_wake='',
        ))
        assert rc == 1
        out = json.loads(capsys.readouterr().out)
        assert 'Invalid topic' in out['error']
