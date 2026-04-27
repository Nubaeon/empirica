"""Tests for the empirica tui (compact Textual cockpit).

Uses textual's headless `App.run_test()`. Layout under test is the v1.4
compact design: 6-col table (stat/name/phase/S/L/N), 4 action buttons
(P sent / L loops / S stop / N notif), no kill button (CLI-only), no
right-detail pane, single statusline + recent strip at the bottom.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest_plugins = ['pytest_asyncio']


@pytest.fixture
def cockpit_env(tmp_path, monkeypatch):
    fake_home = tmp_path / '.empirica'
    fake_home.mkdir()
    (fake_home / 'instance_projects').mkdir()
    (fake_home / 'tty_sessions').mkdir()

    project = tmp_path / 'project'
    (project / '.empirica').mkdir(parents=True)

    from empirica.core.cockpit import (
        enrichment,
        instance_actions,
        instance_state,
        loop_registry,
        sentinel_pause,
    )

    monkeypatch.setattr(sentinel_pause, 'EMPIRICA_DIR', fake_home)
    monkeypatch.setattr(sentinel_pause, 'GLOBAL_PAUSE_FILE', fake_home / 'sentinel_paused')
    monkeypatch.setattr(instance_state, 'EMPIRICA_DIR', fake_home)
    monkeypatch.setattr(instance_actions, 'EMPIRICA_DIR', fake_home)
    monkeypatch.setattr(instance_actions, 'TTY_SESSIONS_DIR', fake_home / 'tty_sessions')
    monkeypatch.setattr(loop_registry, 'EMPIRICA_DIR', fake_home)
    monkeypatch.setattr(enrichment, 'EMPIRICA_DIR', fake_home)
    monkeypatch.setattr(
        enrichment, 'ENP_PENDING_PATH', fake_home / 'enp' / 'pending.json',
    )
    return fake_home, project


def _bind_instance(home: Path, project: Path, instance_id: str) -> None:
    (home / 'instance_projects' / f'{instance_id}.json').write_text(
        json.dumps({'project_path': str(project)})
    )


# ─── mount + structure ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tui_mounts_compact_widgets(cockpit_env):
    from empirica.cli.tui import CockpitApp
    from textual.widgets import Button, DataTable, Static

    app = CockpitApp(include_dead=True)
    async with app.run_test(headless=True, size=(54, 20)) as pilot:
        await pilot.pause(); await pilot.pause()

        assert app.query_one('#inst-table', DataTable) is not None
        assert app.query_one('#summary', Static) is not None
        assert app.query_one('#statusline', Static) is not None
        # v1.6: portrait layout — recent strip replaced with goals + notif
        assert app.query_one('#goals', Static) is not None
        assert app.query_one('#notif', Static) is not None
        for btn_id in ('btn-sent', 'btn-loops', 'btn-stop', 'btn-notif'):
            assert app.query_one(f'#{btn_id}', Button) is not None, btn_id


@pytest.mark.asyncio
async def test_tui_has_no_kill_button(cockpit_env):
    """Kill is CLI-only by design; the TUI should not expose it."""
    from empirica.cli.tui import CockpitApp
    from textual.css.query import NoMatches

    app = CockpitApp(include_dead=True)
    async with app.run_test(headless=True, size=(54, 20)) as pilot:
        await pilot.pause(); await pilot.pause()
        with pytest.raises(NoMatches):
            app.query_one('#btn-kill')


@pytest.mark.asyncio
async def test_table_has_six_columns(cockpit_env):
    from empirica.cli.tui import CockpitApp
    from textual.widgets import DataTable

    app = CockpitApp(include_dead=True)
    async with app.run_test(headless=True, size=(54, 20)) as pilot:
        await pilot.pause(); await pilot.pause()
        table = app.query_one('#inst-table', DataTable)
        col_labels = [c.label.plain for c in table.columns.values()]
        # v1.6: shortened headers for portrait fit (s/ph/S/L/N)
        assert col_labels == ['s', 'name', 'ph', 'S', 'L', 'N']


# ─── data loading ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tui_loads_instances(cockpit_env):
    from empirica.cli.tui import CockpitApp

    home, project = cockpit_env
    _bind_instance(home, project, 'tmux_42')
    _bind_instance(home, project, 'tmux_99')

    app = CockpitApp(include_dead=True)
    async with app.run_test(headless=True, size=(54, 20)) as pilot:
        await pilot.pause(); await pilot.pause()
        ids = sorted(i['instance_id'] for i in app.payload['instances'])
        assert ids == ['tmux_42', 'tmux_99']


# ─── toggle sentinel ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_p_toggles_sentinel(cockpit_env):
    """`p` toggles: pauses if not paused, resumes if paused."""
    from empirica.cli.tui import CockpitApp

    home, project = cockpit_env
    _bind_instance(home, project, 'tmux_42')

    app = CockpitApp(include_dead=True)
    async with app.run_test(headless=True, size=(54, 20)) as pilot:
        await pilot.pause(); await pilot.pause()

        # First press: pauses
        await pilot.press('p')
        await pilot.pause()
        assert (home / 'sentinel_paused_tmux_42').exists()

        # Second press: resumes
        await pilot.press('p')
        await pilot.pause()
        assert not (home / 'sentinel_paused_tmux_42').exists()


@pytest.mark.asyncio
async def test_btn_sent_toggles_sentinel(cockpit_env):
    from empirica.cli.tui import CockpitApp

    home, project = cockpit_env
    _bind_instance(home, project, 'tmux_42')

    app = CockpitApp(include_dead=True)
    async with app.run_test(headless=True, size=(54, 20)) as pilot:
        await pilot.pause(); await pilot.pause()
        await pilot.click('#btn-sent')
        await pilot.pause()
        assert (home / 'sentinel_paused_tmux_42').exists()


# ─── toggle loops ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_l_pauses_all_loops_when_any_unpaused(cockpit_env):
    from empirica.cli.tui import CockpitApp
    from empirica.core.cockpit import LoopRegistry

    home, project = cockpit_env
    _bind_instance(home, project, 'tmux_42')
    reg = LoopRegistry('tmux_42')
    reg.register(name='loop-a', kind='monitor')
    reg.register(name='loop-b', kind='monitor')

    app = CockpitApp(include_dead=True)
    async with app.run_test(headless=True, size=(54, 20)) as pilot:
        await pilot.pause(); await pilot.pause()
        await pilot.press('l')
        await pilot.pause()

        from empirica.core.cockpit import is_loop_paused
        assert is_loop_paused('tmux_42', 'loop-a')
        assert is_loop_paused('tmux_42', 'loop-b')


@pytest.mark.asyncio
async def test_l_resumes_all_loops_when_all_paused(cockpit_env):
    from empirica.cli.tui import CockpitApp
    from empirica.core.cockpit import LoopRegistry, is_loop_paused, set_loop_paused

    home, project = cockpit_env
    _bind_instance(home, project, 'tmux_42')
    reg = LoopRegistry('tmux_42')
    reg.register(name='loop-a', kind='monitor')
    reg.register(name='loop-b', kind='monitor')
    set_loop_paused('tmux_42', 'loop-a', True)
    set_loop_paused('tmux_42', 'loop-b', True)

    app = CockpitApp(include_dead=True)
    async with app.run_test(headless=True, size=(54, 20)) as pilot:
        await pilot.pause(); await pilot.pause()
        await pilot.press('l')
        await pilot.pause()

        assert not is_loop_paused('tmux_42', 'loop-a')
        assert not is_loop_paused('tmux_42', 'loop-b')


# ─── stop ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stop_calls_stop_instance(cockpit_env, monkeypatch):
    from empirica.cli.tui import CockpitApp
    from empirica.core.cockpit import instance_actions

    captured: list[str] = []
    monkeypatch.setattr(
        'empirica.cli.tui.cockpit_app.stop_instance',
        lambda iid, **k: (captured.append(iid),
                          instance_actions.StopResult(iid, True, 'stub', 'tmux-send-keys'))[1],
    )

    home, project = cockpit_env
    _bind_instance(home, project, 'tmux_42')

    app = CockpitApp(include_dead=True)
    async with app.run_test(headless=True, size=(54, 20)) as pilot:
        await pilot.pause(); await pilot.pause()
        await pilot.press('s')
        await pilot.pause()

        assert captured == ['tmux_42']


# ─── notifications (placeholder) ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_n_clears_notifications(cockpit_env):
    """`n` keybinding marks the project's pending notifications as acked.

    New scope (post per-project refactor): notifications live in
    ~/.empirica/enp/pending.json keyed by repo path. Clear acks the
    entries whose repo matches the selected instance's project_path.
    """
    from empirica.cli.tui import CockpitApp

    home, project = cockpit_env
    _bind_instance(home, project, 'tmux_42')
    # Open transaction so the instance has a project_path resolved.
    import time
    suffix = '_tmux_42'
    tx = {
        'transaction_id': 'tx-1', 'session_id': 's-1',
        'preflight_timestamp': time.time(),
        'status': 'open', 'project_path': str(project),
    }
    (project / '.empirica').mkdir(exist_ok=True)
    (project / '.empirica' / f'active_transaction{suffix}.json').write_text(json.dumps(tx))

    enp_dir = home / 'enp'
    enp_dir.mkdir()
    pending_path = enp_dir / 'pending.json'
    pending_path.write_text(json.dumps([
        {'id': 'a', 'repo': str(project), 'title': 'open', 'acknowledged': False},
        {'id': 'b', 'repo': '/other', 'title': 'other', 'acknowledged': False},
    ]))

    app = CockpitApp(include_dead=True)
    async with app.run_test(headless=True, size=(54, 20)) as pilot:
        await pilot.pause(); await pilot.pause()
        await pilot.press('n')
        await pilot.pause()

        result = json.loads(pending_path.read_text())
        for n in result:
            if n['repo'] == str(project):
                assert n['acknowledged'] is True
            else:
                assert n['acknowledged'] is False


# ─── ask state phase ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_phase_ask_when_asking_flag_present(cockpit_env):
    """Phase shows 'ask ⚠' when ~/.empirica/asking_{id} flag exists."""
    from empirica.cli.tui import CockpitApp
    from textual.widgets import DataTable

    home, project = cockpit_env
    _bind_instance(home, project, 'tmux_42')
    # Create transaction so phase isn't no-transaction
    import time
    suffix = '_tmux_42'
    tx = {
        'transaction_id': 'tx-1', 'session_id': 's-1',
        'preflight_timestamp': time.time(),
        'status': 'open', 'project_path': str(project),
    }
    (project / '.empirica' / f'active_transaction{suffix}.json').write_text(json.dumps(tx))
    # Trigger ask
    (home / 'asking_tmux_42').write_text('')

    app = CockpitApp(include_dead=True)
    async with app.run_test(headless=True, size=(54, 20)) as pilot:
        await pilot.pause(); await pilot.pause()
        table = app.query_one('#inst-table', DataTable)
        for row_key in table.rows:
            if str(row_key.value) == 'tmux_42':
                row = table.get_row(row_key)
                # v1.6: phase column is shortened — 'ask⚠' with no space
                phase_cell = str(row[2])
                assert 'ask' in phase_cell, f'expected ask phase, got {phase_cell!r}'
                return
        pytest.fail('tmux_42 row not found')


# ─── v1.6 statusline + open goals ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_statusline_format_includes_conf_and_goals(cockpit_env):
    """Statusline format: k:X c:Y conf:Z% goals:N (when vectors available)."""
    from empirica.cli.tui import CockpitApp
    from textual.widgets import Static
    from rich.console import Console
    import sqlite3
    import time

    home, project = cockpit_env
    _bind_instance(home, project, 'tmux_42')
    # Create the project DB with a snapshot the cockpit can read.
    db_dir = project / '.empirica' / 'sessions'
    db_dir.mkdir(parents=True, exist_ok=True)
    db = db_dir / 'sessions.db'
    conn = sqlite3.connect(db)
    conn.executescript("""
        CREATE TABLE epistemic_snapshots (
            snapshot_id TEXT PRIMARY KEY, session_id TEXT NOT NULL,
            ai_id TEXT NOT NULL, timestamp TEXT NOT NULL,
            cascade_phase TEXT, cascade_id TEXT,
            vectors TEXT NOT NULL, delta TEXT, previous_snapshot_id TEXT,
            context_summary TEXT, evidence_refs TEXT, db_session_ref TEXT,
            domain_vectors TEXT
        );
        CREATE TABLE goals (
            id TEXT PRIMARY KEY, session_id TEXT NOT NULL,
            objective TEXT NOT NULL, scope TEXT NOT NULL,
            created_timestamp REAL NOT NULL, completed_timestamp REAL,
            is_completed BOOLEAN DEFAULT 0, goal_data TEXT NOT NULL,
            status TEXT DEFAULT 'in_progress'
        );
    """)
    import json as _json
    conn.execute(
        "INSERT INTO epistemic_snapshots (snapshot_id, session_id, ai_id, timestamp, vectors) "
        "VALUES (?, ?, ?, ?, ?)",
        ('snap-1', 's-1', 'cc', '2026-04-27T10:00:00+00:00',
         _json.dumps({'know': 0.8, 'uncertainty': 0.2, 'context': 0.7, 'completion': 0.3})),
    )
    conn.execute(
        "INSERT INTO goals (id, session_id, objective, scope, created_timestamp, goal_data, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ('g-1', 's-1', 'finish cockpit v1.6', '{}', time.time(), '{}', 'in_progress'),
    )
    conn.execute(
        "INSERT INTO goals (id, session_id, objective, scope, created_timestamp, goal_data, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        ('g-2', 's-1', 'wire ENP integration', '{}', time.time(), '{}', 'in_progress'),
    )
    conn.commit()
    conn.close()

    # Stub the active_transaction so session_id flows through.
    tx = {
        'transaction_id': 'tx-1', 'session_id': 's-1',
        'preflight_timestamp': time.time(),
        'status': 'open', 'project_path': str(project),
    }
    (project / '.empirica' / 'active_transaction_tmux_42.json').write_text(_json.dumps(tx))

    app = CockpitApp(include_dead=True)
    async with app.run_test(headless=True, size=(40, 24)) as pilot:
        await pilot.pause(); await pilot.pause()
        sl = app.query_one('#statusline', Static)
        c = Console(width=40, file=open('/dev/null', 'w'))
        with c.capture() as cap:
            c.print(sl.render())
        text = cap.get().strip()
        assert 'k:0.80' in text, text
        assert 'c:0.70' in text, text
        assert 'conf:' in text, text
        assert 'goals:2' in text, text


@pytest.mark.asyncio
async def test_open_goals_widget_shows_goals(cockpit_env):
    """Open goals widget lists open goals, not phase events."""
    from empirica.cli.tui import CockpitApp
    from textual.widgets import Static
    from rich.console import Console
    import sqlite3, time

    home, project = cockpit_env
    _bind_instance(home, project, 'tmux_42')
    db_dir = project / '.empirica' / 'sessions'
    db_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_dir / 'sessions.db')
    conn.executescript("""
        CREATE TABLE sessions (
            session_id TEXT PRIMARY KEY, project_id TEXT
        );
        CREATE TABLE epistemic_snapshots (
            snapshot_id TEXT PRIMARY KEY, session_id TEXT NOT NULL,
            ai_id TEXT NOT NULL, timestamp TEXT NOT NULL,
            vectors TEXT NOT NULL
        );
        CREATE TABLE goals (
            id TEXT PRIMARY KEY, session_id TEXT NOT NULL,
            objective TEXT NOT NULL, scope TEXT NOT NULL,
            created_timestamp REAL NOT NULL, goal_data TEXT NOT NULL,
            is_completed BOOLEAN DEFAULT 0,
            project_id TEXT,
            status TEXT DEFAULT 'in_progress'
        );
    """)
    conn.execute("INSERT INTO sessions VALUES (?, ?)", ('s-1', 'p-1'))
    conn.execute(
        "INSERT INTO goals VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ('g-1', 's-1', 'distinctive goal A', '{}', time.time(), '{}', 0, 'p-1', 'in_progress'),
    )
    conn.commit()
    conn.close()

    tx = {'transaction_id': 'tx-1', 'session_id': 's-1',
          'preflight_timestamp': time.time(), 'status': 'open',
          'project_path': str(project)}
    import json as _json
    (project / '.empirica' / 'active_transaction_tmux_42.json').write_text(_json.dumps(tx))

    app = CockpitApp(include_dead=True)
    async with app.run_test(headless=True, size=(40, 24)) as pilot:
        await pilot.pause(); await pilot.pause()
        goals_w = app.query_one('#goals', Static)
        c = Console(width=40, file=open('/dev/null', 'w'))
        with c.capture() as cap:
            c.print(goals_w.render())
        text = cap.get().strip()
        assert 'distinctive goal A' in text, text


@pytest.mark.asyncio
async def test_no_recent_widget(cockpit_env):
    """v1.6 dropped the recent-events widget — confirm it's gone."""
    from empirica.cli.tui import CockpitApp
    from textual.css.query import NoMatches

    app = CockpitApp(include_dead=True)
    async with app.run_test(headless=True, size=(40, 24)) as pilot:
        await pilot.pause(); await pilot.pause()
        with pytest.raises(NoMatches):
            app.query_one('#recent')
