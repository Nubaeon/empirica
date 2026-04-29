"""Tests for the voice_guidance block in PREFLIGHT response.

Covers _build_voice_guidance which surfaces a voice profile when:
  • work_type=comms (auto-prompt to name a profile)
  • voice='<name>' explicit (load and inject the profile)
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from empirica.cli.command_handlers.workflow_commands import _build_voice_guidance


@pytest.fixture
def fake_voice_dirs(tmp_path, monkeypatch):
    """Stage ~/.empirica/voice/ + project-local equivalents for the resolver."""
    home = tmp_path / 'home'
    project = tmp_path / 'project'
    (home / '.empirica' / 'voice').mkdir(parents=True)
    (project / '.empirica' / 'voice').mkdir(parents=True)

    monkeypatch.setattr(Path, 'home', lambda: home)
    monkeypatch.setattr(Path, 'cwd', lambda: project)

    return type('Dirs', (), {
        'global_dir': home / '.empirica' / 'voice',
        'project_dir': project / '.empirica' / 'voice',
    })


def _write_profile(directory: Path, name: str, **fields):
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
    }
    base.update(fields)
    (directory / f'{name}.yaml').write_text(yaml.safe_dump(base))


# ─── neither work_type=comms nor voice ──────────────────────────────────────


class TestVoiceGuidanceOff:
    def test_returns_none_when_neither_set(self, fake_voice_dirs):
        assert _build_voice_guidance(work_type=None, voice=None) is None

    def test_returns_none_for_non_comms_work_type(self, fake_voice_dirs):
        assert _build_voice_guidance(work_type='code', voice=None) is None
        assert _build_voice_guidance(work_type='research', voice=None) is None


# ─── work_type=comms without explicit voice → nudge ─────────────────────────


class TestVoiceGuidanceCommsNudge:
    def test_comms_alone_returns_nudge_block(self, fake_voice_dirs):
        result = _build_voice_guidance(work_type='comms', voice=None)
        assert result is not None
        assert result.get('profile') is None
        assert 'voice list' in result.get('hint', '')

    def test_nudge_does_not_fail_when_no_profiles_exist(self, fake_voice_dirs):
        # Even with empty voice dirs, the comms-only nudge must work.
        result = _build_voice_guidance(work_type='comms', voice=None)
        assert result is not None
        assert 'comms' in result.get('hint', '').lower()


# ─── explicit voice profile load ────────────────────────────────────────────


class TestVoiceGuidanceLoad:
    def test_loads_profile_with_explicit_voice(self, fake_voice_dirs):
        _write_profile(fake_voice_dirs.global_dir, 'alice')
        result = _build_voice_guidance(work_type=None, voice='alice')
        assert result is not None
        assert result['profile'] == 'alice'
        assert result['tendencies_foreground'] == ['terse', 'direct']
        assert result['anti_patterns_suppress'] == ['fluff']
        assert result['register_effective'] == 'casual'  # natural register, no work_type

    def test_comms_plus_voice_picks_email_register(self, fake_voice_dirs):
        # work_type=comms biases register selection toward 'email' platform.
        _write_profile(fake_voice_dirs.global_dir, 'alice')
        result = _build_voice_guidance(work_type='comms', voice='alice')
        assert result['register_effective'] == 'professional'  # from platforms.email
        assert result['depth'] == 'shallow'
        assert result['framing'] == 'action-oriented'

    def test_project_local_overrides_global(self, fake_voice_dirs):
        _write_profile(fake_voice_dirs.global_dir, 'alice', archetype='wrong')
        _write_profile(fake_voice_dirs.project_dir, 'alice', archetype='right')
        result = _build_voice_guidance(work_type='comms', voice='alice')
        # Path field tells us which copy was loaded
        assert str(fake_voice_dirs.project_dir) in result['profile_path']

    def test_unknown_profile_returns_error_block(self, fake_voice_dirs):
        result = _build_voice_guidance(work_type='comms', voice='nonexistent')
        assert result is not None
        assert result.get('profile') is None
        assert result.get('error') == 'profile_not_found'

    def test_missing_natural_register_falls_back_to_unspecified(self, fake_voice_dirs):
        _write_profile(fake_voice_dirs.global_dir, 'alice')
        # Hand-edit yaml to drop natural_register and platforms
        path = fake_voice_dirs.global_dir / 'alice.yaml'
        data = yaml.safe_load(path.read_text())
        data.pop('natural_register', None)
        data.pop('platforms', None)
        path.write_text(yaml.safe_dump(data))
        result = _build_voice_guidance(work_type=None, voice='alice')
        assert result['register_effective'] == 'unspecified'
        assert result['natural_register_fallback'] == 'unspecified'

    def test_voice_set_overrides_no_work_type(self, fake_voice_dirs):
        # voice=alice without work_type still loads (precedence over comms-nudge).
        _write_profile(fake_voice_dirs.global_dir, 'alice')
        result = _build_voice_guidance(work_type=None, voice='alice')
        assert result['profile'] == 'alice'
        # No work_type means no email-register bias
        assert result['register_effective'] == 'casual'


# ─── error tolerance ────────────────────────────────────────────────────────


class TestVoiceGuidanceErrorTolerance:
    def test_corrupt_yaml_returns_error_block(self, fake_voice_dirs):
        bad = fake_voice_dirs.global_dir / 'broken.yaml'
        bad.write_text('::: not valid yaml :::\n  - [unclosed')
        result = _build_voice_guidance(work_type='comms', voice='broken')
        assert result is not None
        # Either "load_failed" or "profile_not_found" depending on parser
        # behavior — either way, no crash and no profile body.
        assert result.get('profile') is None
        assert 'error' in result
