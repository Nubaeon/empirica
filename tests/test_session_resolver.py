"""
Tests for session resolver (alias support for session IDs)
"""

import pytest

from empirica.utils.session_resolver import get_latest_session_id, is_session_alias, resolve_session_id


def test_is_session_alias():
    """Test alias detection"""
    assert is_session_alias("latest")
    assert is_session_alias("last")
    assert is_session_alias("latest:active")
    assert is_session_alias("latest:claude-code")
    assert is_session_alias("latest:active:claude-code")

    # UUIDs are not aliases
    assert not is_session_alias("88dbf132-cc7c-4a4b-9b59-77df3b13dbd2")
    assert not is_session_alias("88dbf132")


def test_resolve_full_uuid():
    """Test that full UUIDs pass through unchanged"""
    full_uuid = "88dbf132-cc7c-4a4b-9b59-77df3b13dbd2"
    result = resolve_session_id(full_uuid)
    assert result == full_uuid


def test_resolve_partial_uuid():
    """Test partial UUID resolution (requires database with sessions)"""
    # This test requires at least one session in database
    try:
        result = resolve_session_id("88dbf132")
        # Should return full UUID
        assert len(result) == 36
        assert result.startswith("88dbf132")
        assert "-" in result
    except ValueError:
        # No session found - skip test
        pytest.skip("No sessions in database for partial UUID test")


def test_resolve_latest_alias():
    """Test 'latest' alias resolution (requires database with sessions)"""
    try:
        result = resolve_session_id("latest")
        # Should return full UUID
        assert len(result) == 36
        assert "-" in result
    except ValueError:
        # No sessions found
        pytest.skip("No sessions in database for latest alias test")


def test_resolve_last_alias():
    """Test 'last' alias (synonym for latest)"""
    try:
        latest_result = resolve_session_id("latest")
        last_result = resolve_session_id("last")
        # Should resolve to same session
        assert latest_result == last_result
    except ValueError:
        pytest.skip("No sessions in database")


def test_resolve_latest_active():
    """Test 'latest:active' alias"""
    try:
        result = resolve_session_id("latest:active")
        # Should return full UUID of active session
        assert len(result) == 36
        assert "-" in result
    except ValueError:
        # No active sessions found
        pytest.skip("No active sessions in database")


def test_resolve_latest_with_ai_id():
    """Test 'latest:<ai_id>' alias"""
    try:
        result = resolve_session_id("latest:claude-code")
        # Should return full UUID
        assert len(result) == 36
        assert "-" in result
    except ValueError:
        # No sessions for this AI found
        pytest.skip("No claude-code sessions in database")


def test_resolve_compound_alias():
    """Test compound alias 'latest:active:<ai_id>'"""
    try:
        result = resolve_session_id("latest:active:claude-code")
        # Should return full UUID
        assert len(result) == 36
        assert "-" in result
    except ValueError:
        # No active sessions for this AI found
        pytest.skip("No active claude-code sessions in database")


def test_get_latest_session_id():
    """Test convenience function"""
    try:
        result = get_latest_session_id()
        # Should return full UUID
        assert len(result) == 36
        assert "-" in result
    except ValueError:
        pytest.skip("No sessions in database")


def test_get_latest_session_id_with_filters():
    """Test convenience function with filters"""
    try:
        result = get_latest_session_id(ai_id="claude-code", active_only=True)
        # Should return full UUID
        assert len(result) == 36
        assert "-" in result
    except ValueError:
        pytest.skip("No matching sessions in database")


def test_resolve_invalid_alias():
    """Test that invalid aliases raise ValueError"""
    with pytest.raises(ValueError, match="No session found"):
        # Use an AI ID that definitely doesn't exist
        resolve_session_id("latest:nonexistent-ai-xyz-12345")


class TestGetActiveProjectPath:
    """Tests for get_active_project_path CWD-reliable override (issue #90)."""

    @staticmethod
    def _isolate_home(tmp_path, monkeypatch):
        """Redirect HOME/USERPROFILE to tmp_path so get_instance_id() can't
        read the developer's real ~/.empirica/instance_projects/. Pins an
        isolated instance_id that points at a non-existent file so the
        fallthrough paths return None rather than opportunistic matches."""
        fake_home = tmp_path / 'home'
        fake_home.mkdir(exist_ok=True)
        monkeypatch.setenv('HOME', str(fake_home))
        monkeypatch.setenv('USERPROFILE', str(fake_home))
        monkeypatch.setenv('EMPIRICA_INSTANCE_ID', 'test-isolated')

    def test_cwd_reliable_with_project_yaml(self, tmp_path, monkeypatch):
        """When EMPIRICA_CWD_RELIABLE=true and CWD has .empirica/project.yaml, return CWD."""
        from empirica.utils.session_resolver import get_active_project_path

        self._isolate_home(tmp_path, monkeypatch)
        project_dir = tmp_path / 'project'
        empirica_dir = project_dir / '.empirica'
        empirica_dir.mkdir(parents=True)
        (empirica_dir / 'project.yaml').write_text('project_id: test-123\n')

        monkeypatch.setenv('EMPIRICA_CWD_RELIABLE', 'true')
        monkeypatch.chdir(project_dir)

        result = get_active_project_path()
        assert result == str(project_dir)

    def test_cwd_reliable_without_project_yaml(self, tmp_path, monkeypatch):
        """When EMPIRICA_CWD_RELIABLE=true but no project.yaml, fall through to other sources."""
        from empirica.utils.session_resolver import get_active_project_path

        self._isolate_home(tmp_path, monkeypatch)
        monkeypatch.setenv('EMPIRICA_CWD_RELIABLE', 'true')
        monkeypatch.chdir(tmp_path)

        # No project.yaml guard, no instance_projects file, no active_work — must be None
        result = get_active_project_path()
        assert result is None

    def test_no_cwd_reliable_flag(self, tmp_path, monkeypatch):
        """Without EMPIRICA_CWD_RELIABLE, CWD is never used even with project.yaml."""
        from empirica.utils.session_resolver import get_active_project_path

        self._isolate_home(tmp_path, monkeypatch)
        project_dir = tmp_path / 'project'
        empirica_dir = project_dir / '.empirica'
        empirica_dir.mkdir(parents=True)
        (empirica_dir / 'project.yaml').write_text('project_id: test-123\n')

        monkeypatch.delenv('EMPIRICA_CWD_RELIABLE', raising=False)
        monkeypatch.chdir(project_dir)

        # No flag means CWD check never fires; with isolated HOME the fallthrough
        # finds nothing either, so the result must be None.
        result = get_active_project_path()
        assert result is None

    def test_cwd_reliable_beats_stale_instance_projects(self, tmp_path, monkeypatch):
        """CWD override takes priority over stale instance_projects data."""
        import json

        from empirica.utils.session_resolver import get_active_project_path

        # Set up CWD project
        cwd_project = tmp_path / 'current_project'
        cwd_project.mkdir()
        empirica_dir = cwd_project / '.empirica'
        empirica_dir.mkdir()
        (empirica_dir / 'project.yaml').write_text('project_id: current\n')

        # Set up stale instance_projects pointing to a different project
        stale_project = tmp_path / 'stale_project'
        stale_project.mkdir()
        instance_dir = tmp_path / 'home' / '.empirica' / 'instance_projects'
        instance_dir.mkdir(parents=True)
        (instance_dir / 'win-default.json').write_text(json.dumps({
            'project_path': str(stale_project)
        }))

        monkeypatch.setenv('EMPIRICA_CWD_RELIABLE', 'true')
        monkeypatch.setenv('EMPIRICA_INSTANCE_ID', 'win-default')
        monkeypatch.setenv('HOME', str(tmp_path / 'home'))
        monkeypatch.setenv('USERPROFILE', str(tmp_path / 'home'))
        monkeypatch.chdir(cwd_project)

        result = get_active_project_path()
        assert result == str(cwd_project)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
