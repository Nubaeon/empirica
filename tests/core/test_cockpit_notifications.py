"""Tests for project-scoped notifications in the cockpit.

Notifications come from ENP watcher's pending.json (a flat list across
all watched repos). Cockpit scopes them per-project via the `repo`
field. Top-bar count = total unacked across all projects.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from empirica.core.cockpit import enrichment


def _write_pending(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries))


def _patch_pending_path(tmp_path: Path):
    """Return a context manager that swaps ENP_PENDING_PATH to tmp_path."""
    return patch.object(enrichment, 'ENP_PENDING_PATH', tmp_path / 'pending.json')


class TestNotificationsForProject:
    def test_empty_project_path_returns_empty(self):
        assert enrichment.notifications_for_project(None) == []
        assert enrichment.notifications_for_project('') == []

    def test_missing_file_returns_empty(self, tmp_path):
        with _patch_pending_path(tmp_path):
            assert enrichment.notifications_for_project('/some/project') == []

    def test_filters_by_repo(self, tmp_path):
        path = tmp_path / 'pending.json'
        _write_pending(path, [
            {'id': '1', 'repo': '/a', 'title': 'A1', 'received': '2026-04-27T10:00:00Z', 'acknowledged': False},
            {'id': '2', 'repo': '/b', 'title': 'B1', 'received': '2026-04-27T11:00:00Z', 'acknowledged': False},
            {'id': '3', 'repo': '/a', 'title': 'A2', 'received': '2026-04-27T12:00:00Z', 'acknowledged': False},
        ])
        with _patch_pending_path(tmp_path):
            a = enrichment.notifications_for_project('/a')
            b = enrichment.notifications_for_project('/b')
        assert [n.title for n in a] == ['A2', 'A1']  # newest first
        assert [n.title for n in b] == ['B1']

    def test_excludes_acked(self, tmp_path):
        path = tmp_path / 'pending.json'
        _write_pending(path, [
            {'id': '1', 'repo': '/a', 'title': 'open', 'received': '2026-04-27T10:00:00Z', 'acknowledged': False},
            {'id': '2', 'repo': '/a', 'title': 'acked', 'received': '2026-04-27T11:00:00Z', 'acknowledged': True},
        ])
        with _patch_pending_path(tmp_path):
            items = enrichment.notifications_for_project('/a')
        assert [n.title for n in items] == ['open']

    def test_path_normalization_trailing_slash(self, tmp_path):
        path = tmp_path / 'pending.json'
        _write_pending(path, [
            {'id': '1', 'repo': '/home/foo/proj/', 'title': 'X', 'received': '2026-04-27T10:00:00Z', 'acknowledged': False},
        ])
        with _patch_pending_path(tmp_path):
            assert len(enrichment.notifications_for_project('/home/foo/proj')) == 1
            assert len(enrichment.notifications_for_project('/home/foo/proj/')) == 1

    def test_limit_caps_results(self, tmp_path):
        path = tmp_path / 'pending.json'
        _write_pending(path, [
            {'id': str(i), 'repo': '/a', 'title': f't{i}',
             'received': f'2026-04-27T{i:02d}:00:00Z', 'acknowledged': False}
            for i in range(10)
        ])
        with _patch_pending_path(tmp_path):
            items = enrichment.notifications_for_project('/a', limit=3)
        assert len(items) == 3
        # Should be the 3 most recent (t9, t8, t7).
        assert [n.title for n in items] == ['t9', 't8', 't7']

    def test_malformed_json_returns_empty(self, tmp_path):
        path = tmp_path / 'pending.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('not-json{')
        with _patch_pending_path(tmp_path):
            assert enrichment.notifications_for_project('/a') == []


class TestNotificationsTotal:
    def test_zero_when_missing(self, tmp_path):
        with _patch_pending_path(tmp_path):
            assert enrichment.notifications_total() == 0

    def test_counts_unacked_across_projects(self, tmp_path):
        path = tmp_path / 'pending.json'
        _write_pending(path, [
            {'id': '1', 'repo': '/a', 'acknowledged': False},
            {'id': '2', 'repo': '/b', 'acknowledged': False},
            {'id': '3', 'repo': '/a', 'acknowledged': True},
        ])
        with _patch_pending_path(tmp_path):
            assert enrichment.notifications_total() == 2


class TestNotificationSummary:
    def test_no_project_path_returns_zero(self):
        s = enrichment.notification_summary('inst', project_path=None)
        assert s.open_count == 0
        assert s.has_attention is False

    def test_counts_per_project(self, tmp_path):
        path = tmp_path / 'pending.json'
        _write_pending(path, [
            {'id': '1', 'repo': '/a', 'acknowledged': False},
            {'id': '2', 'repo': '/a', 'acknowledged': False},
            {'id': '3', 'repo': '/b', 'acknowledged': False},
        ])
        with _patch_pending_path(tmp_path):
            s = enrichment.notification_summary('inst', project_path='/a')
        assert s.open_count == 2
        assert s.has_attention is True


class TestClearNotifications:
    def test_no_project_path_no_op(self):
        # Doesn't touch the file when no project_path is given.
        assert enrichment.clear_notifications('inst', project_path=None) == 0

    def test_acknowledges_in_place(self, tmp_path):
        path = tmp_path / 'pending.json'
        _write_pending(path, [
            {'id': '1', 'repo': '/a', 'acknowledged': False},
            {'id': '2', 'repo': '/b', 'acknowledged': False},
            {'id': '3', 'repo': '/a', 'acknowledged': False},
        ])
        with _patch_pending_path(tmp_path):
            cleared = enrichment.clear_notifications('inst', project_path='/a')
        assert cleared == 2
        # File rewritten with acks
        result = json.loads(path.read_text())
        acked_for_a = [n for n in result if n['repo'] == '/a']
        assert all(n['acknowledged'] for n in acked_for_a)
        # Other project untouched
        b = next(n for n in result if n['repo'] == '/b')
        assert b['acknowledged'] is False

    def test_idempotent(self, tmp_path):
        path = tmp_path / 'pending.json'
        _write_pending(path, [
            {'id': '1', 'repo': '/a', 'acknowledged': True},
        ])
        with _patch_pending_path(tmp_path):
            assert enrichment.clear_notifications('inst', project_path='/a') == 0


class TestBackwardCompatNotificationsList:
    def test_returns_empty_list(self):
        # Old per-instance signature is now a no-op shim.
        assert enrichment.notifications_list('any-instance') == []
