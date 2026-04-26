"""Tests for empirica.core.cockpit.instance_state.

Builds synthetic state-file layouts under a tmp ~/.empirica/ and a tmp
project dir, then verifies discovery + aggregation produce the expected
shape.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from empirica.core.cockpit import instance_state as ist
from empirica.core.cockpit import loop_registry as lr
from empirica.core.cockpit import sentinel_pause as sp


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Create a tmp ~/.empirica/ + tmp project dir, redirect all modules."""
    fake_home = tmp_path / '.empirica'
    fake_home.mkdir(parents=True)
    (fake_home / 'instance_projects').mkdir()

    project = tmp_path / 'project'
    (project / '.empirica').mkdir(parents=True)

    monkeypatch.setattr(ist, 'EMPIRICA_DIR', fake_home)
    monkeypatch.setattr(lr, 'EMPIRICA_DIR', fake_home)
    monkeypatch.setattr(sp, 'EMPIRICA_DIR', fake_home)
    monkeypatch.setattr(sp, 'GLOBAL_PAUSE_FILE', fake_home / 'sentinel_paused')
    return fake_home, project


def _bind_instance(home: Path, project: Path, instance_id: str) -> None:
    (home / 'instance_projects' / f'{instance_id}.json').write_text(
        json.dumps({'project_path': str(project)})
    )


def _write_transaction(project: Path, instance_id: str, status: str = 'open',
                        praxic_calls: int = 0) -> None:
    suffix = f'_{instance_id}'
    tx = {
        'transaction_id': 'tx-1234-5678',
        'session_id': 'sess-aaaa-bbbb',
        'preflight_timestamp': time.time() - 60,
        'status': status,
        'project_path': str(project),
        'updated_at': time.time(),
        'work_type': 'code',
    }
    (project / '.empirica' / f'active_transaction{suffix}.json').write_text(
        json.dumps(tx)
    )
    if praxic_calls > 0:
        counters = {'praxic_tool_calls': praxic_calls, 'noetic_tool_calls': 1}
        (project / '.empirica' / f'hook_counters{suffix}.json').write_text(
            json.dumps(counters)
        )


def test_discover_empty_returns_empty(env):
    assert ist.discover_instances() == []


def test_discover_via_instance_projects(env):
    home, project = env
    _bind_instance(home, project, 'tmux_5')
    _bind_instance(home, project, 'tmux_7')
    assert ist.discover_instances() == ['tmux_5', 'tmux_7']


def test_discover_via_pause_file(env):
    home, _ = env
    (home / 'sentinel_paused_term_x86').write_text('')
    assert 'term_x86' in ist.discover_instances()


def test_discover_excludes_global_pause_file(env):
    home, _ = env
    (home / 'sentinel_paused').write_text('')
    assert ist.discover_instances() == []


def test_discover_excludes_loop_pause_sidecars(env):
    home, _ = env
    (home / 'loop_paused_tmux_5_some-loop').write_text('')
    # Should ideally not pollute discovery with the loop name as instance_id
    discovered = ist.discover_instances()
    # The implementation skips loop_paused_ via LOOP_PAUSE_PATTERN
    assert 'tmux_5_some-loop' not in discovered


def test_aggregate_phase_noetic(env):
    home, project = env
    _bind_instance(home, project, 'tmux_5')
    _write_transaction(project, 'tmux_5', status='open', praxic_calls=0)
    state = ist.aggregate_instance_state('tmux_5')
    assert state['phase'] == 'noetic'
    assert state['transaction']['id'] == 'tx-1234-5678'
    assert state['state'] == 'active'
    assert state['project_path'] == str(project)


def test_aggregate_phase_praxic(env):
    home, project = env
    _bind_instance(home, project, 'tmux_5')
    _write_transaction(project, 'tmux_5', status='open', praxic_calls=3)
    state = ist.aggregate_instance_state('tmux_5')
    assert state['phase'] == 'praxic'


def test_aggregate_phase_closed(env):
    home, project = env
    _bind_instance(home, project, 'tmux_5')
    _write_transaction(project, 'tmux_5', status='closed', praxic_calls=5)
    state = ist.aggregate_instance_state('tmux_5')
    assert state['phase'] == 'closed'


def test_aggregate_no_transaction(env):
    home, project = env
    _bind_instance(home, project, 'tmux_5')
    state = ist.aggregate_instance_state('tmux_5')
    assert state['phase'] == 'no-transaction'
    assert state['transaction'] is None


def test_aggregate_includes_sentinel_pause(env):
    home, project = env
    _bind_instance(home, project, 'tmux_5')
    sp.pause_sentinel('tmux_5', reason='maintenance')
    state = ist.aggregate_instance_state('tmux_5')
    assert state['sentinel']['paused'] is True
    assert state['sentinel']['scope'] == 'instance'
    assert state['sentinel']['reason'] == 'maintenance'


def test_aggregate_includes_loops_with_pause_state(env):
    home, project = env
    _bind_instance(home, project, 'tmux_5')
    reg = lr.LoopRegistry('tmux_5')
    reg.register(name='poll-a', kind='cron', cron='*/5 * * * *')
    reg.register(name='poll-b', kind='monitor')
    lr.set_loop_paused('tmux_5', 'poll-b', True)

    state = ist.aggregate_instance_state('tmux_5')
    assert set(state['loops'].keys()) == {'poll-a', 'poll-b'}
    assert state['loops']['poll-a']['paused'] is False
    assert state['loops']['poll-b']['paused'] is True


def test_aggregate_all_summary_counts(env):
    home, project = env
    _bind_instance(home, project, 'tmux_5')
    _write_transaction(project, 'tmux_5', status='open')
    _bind_instance(home, project, 'tmux_7')
    _write_transaction(project, 'tmux_7', status='closed')
    reg = lr.LoopRegistry('tmux_5')
    reg.register(name='poll', kind='monitor')

    payload = ist.aggregate_all()
    assert payload['summary']['instances'] == 2
    assert payload['summary']['loops_registered'] == 1
    assert payload['summary']['loops_paused'] == 0
    assert payload['summary']['active_tx'] == 1


def test_state_symbol_no_claude_when_abandoned(env):
    home, _ = env
    # Old pause file with no transaction → looks abandoned
    old_file = home / 'sentinel_paused_old-instance'
    old_file.write_text('')
    import os
    very_old = time.time() - (40 * 24 * 60 * 60)  # 40 days ago
    os.utime(old_file, (very_old, very_old))
    state = ist.aggregate_instance_state('old-instance')
    assert state['state'] == 'no-claude'


def test_instance_label_falls_back_to_project_basename(env):
    """No manual label + bound to project → label is project basename
    (matches what statusline shows)."""
    home, project = env
    _bind_instance(home, project, 'tmux_5')
    state = ist.aggregate_instance_state('tmux_5')
    assert state['label'] == project.name  # 'project' (basename of tmp_path/project)


def test_instance_label_falls_back_to_id_when_no_project(env):
    """No project binding + no manual label → fall through to instance_id."""
    state = ist.aggregate_instance_state('tmux_5')
    assert state['label'] == 'tmux_5'


def test_instance_label_read_from_file(env):
    home, project = env
    _bind_instance(home, project, 'tmux_5')
    (home / 'instance_label_tmux_5').write_text('outreach\nignored\n')
    state = ist.aggregate_instance_state('tmux_5')
    assert state['label'] == 'outreach'


def test_instance_label_manual_overrides_project_basename(env):
    """Manual label > project basename — explicit user override wins."""
    home, project = env
    _bind_instance(home, project, 'tmux_5')
    (home / 'instance_label_tmux_5').write_text('custom-name\n')
    state = ist.aggregate_instance_state('tmux_5')
    assert state['label'] == 'custom-name'
