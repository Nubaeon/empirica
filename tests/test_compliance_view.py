"""Tests for compliance_view — the cockpit's read/write of the last
compliance-report result. write_last_compliance is called from the
compliance-report handler on every run; read_compliance_summary is
called from aggregate_instance_state and produces the cockpit's
render-ready summary.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from empirica.core.cockpit import compliance_view
from empirica.core.cockpit.compliance_view import (
    last_compliance_path,
    read_compliance_summary,
    write_last_compliance,
)


@pytest.fixture
def empirica_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(compliance_view, 'EMPIRICA_DIR', tmp_path)
    return tmp_path


@pytest.fixture
def project(tmp_path):
    p = tmp_path / 'proj'
    (p / '.empirica').mkdir(parents=True)
    return p


def _write_project_yaml(project: Path, **fields) -> None:
    (project / '.empirica' / 'project.yaml').write_text(yaml.safe_dump(fields))


# ─── path + project_id resolution ──────────────────────────────────────────


def test_last_compliance_path_basic(empirica_dir):
    p = last_compliance_path('foo-project')
    assert p == empirica_dir / 'last_compliance_foo-project.json'


def test_last_compliance_path_sanitizes(empirica_dir):
    p = last_compliance_path('foo/proj%')
    assert p is not None
    assert '/' not in p.name
    assert '%' not in p.name


def test_last_compliance_path_none_for_empty():
    assert last_compliance_path(None) is None
    assert last_compliance_path('') is None


# ─── write_last_compliance ─────────────────────────────────────────────────


def test_write_last_compliance_persists_payload(empirica_dir):
    report = {
        'overall': {'status': 'compliant', 'score': 1.0,
                    'checks_passed': 5, 'checks_total': 5},
        'checks': [{'check': 'lint', 'passed': True}],
    }
    path = write_last_compliance('test-project', report)
    assert path is not None
    assert path.exists()
    data = json.loads(path.read_text())
    assert data['_project_id'] == 'test-project'
    assert data['_persisted_at']
    assert data['overall']['score'] == 1.0


def test_write_last_compliance_returns_none_for_empty_project_id(empirica_dir):
    assert write_last_compliance('', {'overall': {}}) is None


def test_write_last_compliance_idempotent(empirica_dir):
    write_last_compliance('p', {'overall': {'score': 0.5}})
    write_last_compliance('p', {'overall': {'score': 0.9}})
    files = list(empirica_dir.glob('last_compliance_*.json'))
    assert len(files) == 1
    assert json.loads(files[0].read_text())['overall']['score'] == 0.9


# ─── read_compliance_summary ───────────────────────────────────────────────


def test_read_compliance_summary_returns_none_for_no_project(empirica_dir):
    assert read_compliance_summary(None) is None
    assert read_compliance_summary('/nonexistent') is None


def test_read_compliance_summary_returns_none_when_no_persisted(empirica_dir, project):
    _write_project_yaml(project, project_id='p1')
    assert read_compliance_summary(project) is None


def test_read_compliance_summary_returns_none_when_no_project_id(empirica_dir, project):
    # project.yaml exists but has no project_id
    _write_project_yaml(project, name='Foo')
    write_last_compliance('p1', {'overall': {'status': 'compliant'}})
    assert read_compliance_summary(project) is None


def test_read_compliance_summary_passing(empirica_dir, project):
    _write_project_yaml(project, project_id='p1')
    write_last_compliance('p1', {
        'overall': {'status': 'compliant', 'score': 1.0,
                    'checks_passed': 11, 'checks_total': 11},
        'checks': [{'check': 'lint', 'passed': True}],
    })
    summary = read_compliance_summary(project)
    assert summary is not None
    assert summary['status'] == 'compliant'
    assert summary['score'] == 1.0
    assert summary['checks_passed'] == 11
    assert summary['checks_total'] == 11
    assert summary['failed_checks'] == []
    assert summary['fresh'] is True
    assert summary['project_id'] == 'p1'


def test_read_compliance_summary_failing_lists_failed_checks(empirica_dir, project):
    _write_project_yaml(project, project_id='p1')
    write_last_compliance('p1', {
        'overall': {'status': 'non_compliant', 'score': 0.7,
                    'checks_passed': 7, 'checks_total': 10},
        'checks': [
            {'check': 'lint', 'passed': False},
            {'check': 'tests', 'passed': True},
            {'check': 'complexity', 'passed': False},
            {'check': 'type_safety', 'passed': False},
        ],
    })
    summary = read_compliance_summary(project)
    assert summary is not None
    assert summary['failed_checks'] == ['lint', 'complexity', 'type_safety']


def test_read_compliance_summary_handles_corrupt_json(empirica_dir, project):
    _write_project_yaml(project, project_id='p1')
    (empirica_dir / 'last_compliance_p1.json').write_text('{ broken')
    assert read_compliance_summary(project) is None


def test_read_compliance_summary_marks_stale_after_fresh_window(empirica_dir, project, monkeypatch):
    """Set a small FRESH_WINDOW and verify the summary marks fresh=False."""
    monkeypatch.setattr(compliance_view, 'FRESH_WINDOW_S', 1)
    _write_project_yaml(project, project_id='p1')
    write_last_compliance('p1', {
        'overall': {'status': 'compliant', 'score': 1.0,
                    'checks_passed': 5, 'checks_total': 5},
        'checks': [],
    })
    # Backdate the persisted_at by 5 seconds
    path = empirica_dir / 'last_compliance_p1.json'
    data = json.loads(path.read_text())
    data['_persisted_at'] = '2020-01-01T00:00:00+00:00'
    path.write_text(json.dumps(data))

    summary = read_compliance_summary(project)
    assert summary is not None
    assert summary['fresh'] is False
    assert summary['age_seconds'] is not None and summary['age_seconds'] > 1
