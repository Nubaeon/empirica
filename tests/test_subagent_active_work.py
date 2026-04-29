"""Tests for the subagent active_work fix (#95 Issue 1).

Covers:
  • subagent-start writes active_work_<subagent_uuid>.json with is_subagent=true
  • subagent-stop deletes that file
  • Schema/contents are correct (so the resolver chain finds child_session_id)

The hook entry-points themselves (which read stdin and orchestrate) are
covered by the integration of these helpers into main(); these tests
target the helpers directly so they're hermetic.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Stage a fake ~ so active_work writes to a controlled path."""
    home = tmp_path / 'home'
    (home / '.empirica').mkdir(parents=True)
    monkeypatch.setattr(Path, 'home', lambda: home)
    return home


def _load_subagent_start():
    """Import the canonical subagent-start hook as a module."""
    plugin_dir = Path(__file__).parent.parent / 'empirica' / 'plugins' / 'claude-code-integration' / 'hooks'
    sys.path.insert(0, str(plugin_dir))
    try:
        if 'subagent_start' in sys.modules:
            del sys.modules['subagent_start']
        # File is named 'subagent-start.py' (hyphen) — load via importlib spec
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'subagent_start',
            plugin_dir / 'subagent-start.py',
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.path.pop(0)


def _load_subagent_stop():
    plugin_dir = Path(__file__).parent.parent / 'empirica' / 'plugins' / 'claude-code-integration' / 'hooks'
    sys.path.insert(0, str(plugin_dir))
    try:
        if 'subagent_stop' in sys.modules:
            del sys.modules['subagent_stop']
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'subagent_stop',
            plugin_dir / 'subagent-stop.py',
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.path.pop(0)


# ─── _write_subagent_active_work ────────────────────────────────────────────


class TestWriteSubagentActiveWork:
    def test_writes_file_with_is_subagent_flag(self, fake_home):
        mod = _load_subagent_start()
        ok = mod._write_subagent_active_work(
            subagent_claude_session_id='sub-claude-uuid-001',
            child_session_id='child-empirica-001',
            parent_claude_session_id='parent-claude-001',
            parent_session_id='parent-empirica-001',
            agent_name='Explore',
        )
        assert ok is True

        path = fake_home / '.empirica' / 'active_work_sub-claude-uuid-001.json'
        assert path.exists()
        data = json.loads(path.read_text())
        assert data['is_subagent'] is True
        assert data['claude_session_id'] == 'sub-claude-uuid-001'
        assert data['empirica_session_id'] == 'child-empirica-001'
        assert data['parent_empirica_session_id'] == 'parent-empirica-001'
        assert data['agent_name'] == 'Explore'
        assert data['source'] == 'subagent-start'

    def test_file_permission_is_user_only(self, fake_home):
        mod = _load_subagent_start()
        mod._write_subagent_active_work(
            subagent_claude_session_id='sub-001',
            child_session_id='child-001',
            parent_claude_session_id=None,
            parent_session_id='parent-001',
            agent_name='general-purpose',
        )
        path = fake_home / '.empirica' / 'active_work_sub-001.json'
        # 0o600 user-only (owner read/write, no group/other)
        mode = path.stat().st_mode & 0o777
        assert mode == 0o600

    def test_returns_false_when_session_id_missing(self, fake_home):
        mod = _load_subagent_start()
        ok = mod._write_subagent_active_work(
            subagent_claude_session_id='',
            child_session_id='child-001',
            parent_claude_session_id=None,
            parent_session_id='parent-001',
            agent_name='Explore',
        )
        assert ok is False
        # No file written
        assert not list((fake_home / '.empirica').glob('active_work_*.json'))


# ─── _cleanup_subagent_active_work ──────────────────────────────────────────


class TestCleanupSubagentActiveWork:
    def test_deletes_existing_file(self, fake_home):
        # Pre-seed the file (as if SubagentStart had written it)
        path = fake_home / '.empirica' / 'active_work_sub-uuid-002.json'
        path.write_text(json.dumps({'is_subagent': True}))
        assert path.exists()

        mod = _load_subagent_stop()
        mod._cleanup_subagent_active_work('sub-uuid-002')
        assert not path.exists()

    def test_silent_when_file_absent(self, fake_home):
        # No file exists; cleanup should not raise
        mod = _load_subagent_stop()
        mod._cleanup_subagent_active_work('never-written-uuid')  # no exception

    def test_silent_when_session_id_none(self, fake_home):
        mod = _load_subagent_stop()
        mod._cleanup_subagent_active_work(None)  # no exception

    def test_does_not_delete_unrelated_active_work(self, fake_home):
        # A parent's active_work (different uuid) should be untouched
        parent_path = fake_home / '.empirica' / 'active_work_parent-uuid.json'
        parent_path.write_text(json.dumps({'is_subagent': False}))

        mod = _load_subagent_stop()
        mod._cleanup_subagent_active_work('different-subagent-uuid')

        assert parent_path.exists()  # untouched
