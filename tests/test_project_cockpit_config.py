"""Tests for project_cockpit_config — reads cockpit.loops + cockpit.listeners
from a project's .empirica/project.yaml. Used by the TUI to auto-install
canonical loops/listeners on first L/E click against an empty registry.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from empirica.core.cockpit.project_cockpit_config import (
    project_listeners,
    project_loops,
    project_yaml_path,
)


def _make_project(tmp_path: Path, content: dict | str) -> Path:
    project = tmp_path / 'proj'
    (project / '.empirica').mkdir(parents=True)
    p = project / '.empirica' / 'project.yaml'
    if isinstance(content, dict):
        p.write_text(yaml.safe_dump(content))
    else:
        p.write_text(content)
    return project


# ─── path helper ───────────────────────────────────────────────────────────


def test_project_yaml_path():
    assert project_yaml_path('/some/proj') == Path('/some/proj/.empirica/project.yaml')


# ─── project_loops ─────────────────────────────────────────────────────────


class TestProjectLoops:
    def test_none_path(self):
        assert project_loops(None) == []

    def test_missing_file(self, tmp_path):
        assert project_loops(tmp_path / 'nope') == []

    def test_no_cockpit_block(self, tmp_path):
        project = _make_project(tmp_path, {'project_id': 'x', 'project_name': 'foo'})
        assert project_loops(project) == []

    def test_empty_cockpit_block(self, tmp_path):
        project = _make_project(tmp_path, {'cockpit': {}})
        assert project_loops(project) == []

    def test_no_loops_key(self, tmp_path):
        project = _make_project(tmp_path, {'cockpit': {'listeners': []}})
        assert project_loops(project) == []

    def test_loops_not_a_list(self, tmp_path):
        project = _make_project(tmp_path, {'cockpit': {'loops': 'not-a-list'}})
        assert project_loops(project) == []

    def test_happy_path(self, tmp_path):
        project = _make_project(tmp_path, {
            'cockpit': {
                'loops': [
                    {
                        'name': 'foo-poll', 'kind': 'cron',
                        'cron': '*/15 * * * *', 'description': 'foo',
                    },
                    {'name': 'bar-poll', 'kind': 'interval', 'interval': '5m'},
                ]
            }
        })
        loops = project_loops(project)
        assert len(loops) == 2
        assert loops[0]['name'] == 'foo-poll'
        assert loops[1]['kind'] == 'interval'

    def test_filters_entries_without_name(self, tmp_path):
        project = _make_project(tmp_path, {
            'cockpit': {
                'loops': [
                    {'name': 'good', 'kind': 'cron'},
                    {'kind': 'cron'},  # no name — skipped
                    'just-a-string',  # not a dict — skipped
                    {'name': '', 'kind': 'cron'},  # empty name — skipped
                ]
            }
        })
        loops = project_loops(project)
        assert len(loops) == 1
        assert loops[0]['name'] == 'good'

    def test_corrupt_yaml_returns_empty(self, tmp_path):
        project = _make_project(tmp_path, '{ broken: yaml :: not parseable')
        assert project_loops(project) == []

    def test_yaml_top_level_not_dict_returns_empty(self, tmp_path):
        # YAML that parses to a list, not a dict
        project = _make_project(tmp_path, '- one\n- two\n')
        assert project_loops(project) == []


# ─── project_listeners ─────────────────────────────────────────────────────


class TestProjectListeners:
    def test_none_path(self):
        assert project_listeners(None) == []

    def test_missing_file(self, tmp_path):
        assert project_listeners(tmp_path / 'nope') == []

    def test_happy_path(self, tmp_path):
        project = _make_project(tmp_path, {
            'cockpit': {
                'listeners': [
                    {
                        'name': 'foo-inbox',
                        'topic': 'ntfy:foo-channel',
                        'description': 'foo inbox',
                        'on_wake': 'Process new mail',
                    },
                ]
            }
        })
        listeners = project_listeners(project)
        assert len(listeners) == 1
        assert listeners[0]['topic'] == 'ntfy:foo-channel'

    def test_requires_both_name_and_topic(self, tmp_path):
        project = _make_project(tmp_path, {
            'cockpit': {
                'listeners': [
                    {'name': 'good', 'topic': 'ntfy:t'},
                    {'name': 'no-topic'},  # missing topic — skipped
                    {'topic': 'ntfy:t'},  # missing name — skipped
                ]
            }
        })
        listeners = project_listeners(project)
        assert len(listeners) == 1
        assert listeners[0]['name'] == 'good'

    def test_listeners_not_a_list(self, tmp_path):
        project = _make_project(tmp_path, {
            'cockpit': {'listeners': {'not': 'a list'}}
        })
        assert project_listeners(project) == []
