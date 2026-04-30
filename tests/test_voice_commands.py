"""Tests for empirica.cli.command_handlers.voice_commands."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

# ─── fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_voice_dirs(tmp_path, monkeypatch):
    """Stage a fake home with ~/.empirica/voice/ + a project-local override.

    Returns dict: {global_dir, project_dir, project_root}.
    Patches Path.cwd() and Path.home() so _voice_dirs() resolves to these.
    """
    home = tmp_path / 'home'
    project = tmp_path / 'project'
    (home / '.empirica' / 'voice').mkdir(parents=True)
    (project / '.empirica' / 'voice').mkdir(parents=True)

    def _fake_home() -> Path:
        return home

    def _fake_cwd() -> Path:
        return project

    monkeypatch.setattr(Path, 'home', _fake_home)
    monkeypatch.setattr(Path, 'cwd', _fake_cwd)

    return SimpleNamespace(
        global_dir=home / '.empirica' / 'voice',
        project_dir=project / '.empirica' / 'voice',
        project_root=project,
    )


def _write_profile(directory: Path, name: str, **fields):
    """Write a minimal yaml profile."""
    import yaml
    base = {
        'creator_id': name,
        'name': name,
        'archetype': 'test',
        'natural_register': 'casual',
        'tendencies': ['terse', 'direct'],
        'anti_patterns': ['fluff'],
        'platforms': {
            'email': {'register': 'professional', 'depth': 'shallow', 'framing': 'action-oriented'},
        },
        'voice_stats': {'total_samples': 10, 'sources': {'reddit': {'samples': 10}}},
    }
    base.update(fields)
    (directory / f'{name}.yaml').write_text(yaml.safe_dump(base))


# ─── voice list ─────────────────────────────────────────────────────────────


class TestVoiceList:
    def test_empty_when_no_profiles(self, tmp_voice_dirs, capsys):
        from empirica.cli.command_handlers.voice_commands import handle_voice_list_command
        args = SimpleNamespace(output='human')
        rc = handle_voice_list_command(args)
        assert rc == 0
        out = capsys.readouterr().out
        assert 'No voice profiles found' in out

    def test_lists_global_profiles(self, tmp_voice_dirs, capsys):
        from empirica.cli.command_handlers.voice_commands import handle_voice_list_command
        _write_profile(tmp_voice_dirs.global_dir, 'alice')
        _write_profile(tmp_voice_dirs.global_dir, 'bob')
        args = SimpleNamespace(output='human')
        handle_voice_list_command(args)
        out = capsys.readouterr().out
        assert 'alice' in out
        assert 'bob' in out
        assert 'global' in out

    def test_project_local_shadows_global(self, tmp_voice_dirs, capsys):
        from empirica.cli.command_handlers.voice_commands import handle_voice_list_command
        _write_profile(tmp_voice_dirs.global_dir, 'alice', archetype='global-version')
        _write_profile(tmp_voice_dirs.project_dir, 'alice', archetype='project-version')
        args = SimpleNamespace(output='human')
        handle_voice_list_command(args)
        out = capsys.readouterr().out
        # Project-local wins; only one alice entry, scope=project
        assert out.count('alice') == 1
        assert 'project' in out
        assert 'project-version' in out  # archetype col confirms which won

    def test_json_output(self, tmp_voice_dirs, capsys):
        from empirica.cli.command_handlers.voice_commands import handle_voice_list_command
        _write_profile(tmp_voice_dirs.global_dir, 'alice')
        args = SimpleNamespace(output='json')
        handle_voice_list_command(args)
        data = json.loads(capsys.readouterr().out)
        assert len(data['profiles']) == 1
        assert data['profiles'][0]['name'] == 'alice'
        assert data['profiles'][0]['scope'] == 'global'


# ─── voice show ─────────────────────────────────────────────────────────────


class TestVoiceShow:
    def test_missing_profile_returns_error(self, tmp_voice_dirs, capsys):
        from empirica.cli.command_handlers.voice_commands import handle_voice_show_command
        args = SimpleNamespace(name='nonexistent', output='human')
        rc = handle_voice_show_command(args)
        assert rc == 1
        err = capsys.readouterr().err
        assert "not found" in err

    def test_shows_global_profile(self, tmp_voice_dirs, capsys):
        from empirica.cli.command_handlers.voice_commands import handle_voice_show_command
        _write_profile(tmp_voice_dirs.global_dir, 'alice')
        args = SimpleNamespace(name='alice', output='human')
        rc = handle_voice_show_command(args)
        assert rc == 0
        out = capsys.readouterr().out
        assert 'Profile: alice' in out
        assert 'terse' in out  # tendency
        assert 'fluff' in out  # anti-pattern

    def test_project_local_override(self, tmp_voice_dirs, capsys):
        from empirica.cli.command_handlers.voice_commands import handle_voice_show_command
        _write_profile(tmp_voice_dirs.global_dir, 'alice', archetype='wrong-one')
        _write_profile(tmp_voice_dirs.project_dir, 'alice', archetype='right-one')
        args = SimpleNamespace(name='alice', output='human')
        handle_voice_show_command(args)
        out = capsys.readouterr().out
        assert 'right-one' in out
        assert 'wrong-one' not in out

    def test_json_output_includes_full_profile(self, tmp_voice_dirs, capsys):
        from empirica.cli.command_handlers.voice_commands import handle_voice_show_command
        _write_profile(tmp_voice_dirs.global_dir, 'alice')
        args = SimpleNamespace(name='alice', output='json')
        handle_voice_show_command(args)
        data = json.loads(capsys.readouterr().out)
        assert data['name'] == 'alice'
        assert data['profile']['tendencies'] == ['terse', 'direct']


# ─── voice apply ────────────────────────────────────────────────────────────


class TestVoiceApply:
    def test_email_register_resolves_from_platforms(self, tmp_voice_dirs, capsys):
        from empirica.cli.command_handlers.voice_commands import handle_voice_apply_command
        _write_profile(tmp_voice_dirs.global_dir, 'alice')
        args = SimpleNamespace(name='alice', register='email', output='human')
        rc = handle_voice_apply_command(args)
        assert rc == 0
        out = capsys.readouterr().out
        assert 'professional' in out  # email register from platforms config
        assert 'shallow' in out  # depth
        assert 'action-oriented' in out  # framing

    def test_unknown_register_falls_back_to_natural(self, tmp_voice_dirs, capsys):
        from empirica.cli.command_handlers.voice_commands import handle_voice_apply_command
        _write_profile(tmp_voice_dirs.global_dir, 'alice', natural_register='formal')
        args = SimpleNamespace(name='alice', register='hieroglyphs', output='human')
        handle_voice_apply_command(args)
        out = capsys.readouterr().out
        assert 'formal' in out  # fell back to natural_register

    def test_no_register_uses_natural(self, tmp_voice_dirs, capsys):
        from empirica.cli.command_handlers.voice_commands import handle_voice_apply_command
        _write_profile(tmp_voice_dirs.global_dir, 'alice', natural_register='terse')
        args = SimpleNamespace(name='alice', register=None, output='human')
        handle_voice_apply_command(args)
        out = capsys.readouterr().out
        assert 'terse' in out

    def test_json_output_structure(self, tmp_voice_dirs, capsys):
        from empirica.cli.command_handlers.voice_commands import handle_voice_apply_command
        _write_profile(tmp_voice_dirs.global_dir, 'alice')
        args = SimpleNamespace(name='alice', register='email', output='json')
        handle_voice_apply_command(args)
        data = json.loads(capsys.readouterr().out)
        assert data['profile'] == 'alice'
        assert data['register_requested'] == 'email'
        assert data['register_effective'] == 'professional'
        assert data['tendencies_foreground'] == ['terse', 'direct']
        assert data['anti_patterns_suppress'] == ['fluff']

    def test_missing_profile_returns_error(self, tmp_voice_dirs, capsys):
        from empirica.cli.command_handlers.voice_commands import handle_voice_apply_command
        args = SimpleNamespace(name='ghost', register='email', output='human')
        rc = handle_voice_apply_command(args)
        assert rc == 1


# ─── group dispatcher ───────────────────────────────────────────────────────


class TestVoiceGroupDispatcher:
    def test_missing_action_returns_usage(self, capsys):
        from empirica.cli.command_handlers.voice_commands import handle_voice_group_command
        args = SimpleNamespace(voice_action=None)
        rc = handle_voice_group_command(args)
        assert rc == 2
        err = capsys.readouterr().err
        assert 'usage:' in err

    def test_unknown_action_returns_error(self, capsys):
        from empirica.cli.command_handlers.voice_commands import handle_voice_group_command
        args = SimpleNamespace(voice_action='nonsense')
        rc = handle_voice_group_command(args)
        assert rc == 2
        err = capsys.readouterr().err
        assert 'unknown' in err

    def test_routes_list(self, tmp_voice_dirs, capsys):
        from empirica.cli.command_handlers.voice_commands import handle_voice_group_command
        args = SimpleNamespace(voice_action='list', output='human')
        rc = handle_voice_group_command(args)
        assert rc == 0
