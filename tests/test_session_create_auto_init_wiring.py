"""Tests for session-create --auto-init wiring the project_path through to
instance_projects (ecodex prop_zwfsl26r7fc7ddj6oemkfcwa44).

Bug: _handle_auto_init created the project but never persisted project_path
to a location the resolver chain could see. _write_tty_session then called
R.project_path() (which returned None for the brand-new project) and silently
no-op'd. Subsequent commands hit 'Cannot resolve project path.'

Fix: _handle_auto_init returns the just-created project_path; the main flow
forwards it to _write_tty_session via project_path_override.
"""

from __future__ import annotations

from argparse import Namespace
from unittest.mock import MagicMock, patch

from empirica.cli.command_handlers.session_create import (
    _handle_auto_init,
    _write_tty_session,
)


def test_handle_auto_init_returns_project_path_when_init_runs(tmp_path, monkeypatch):
    """When --auto-init creates the project, the third tuple element is the git_root."""
    monkeypatch.chdir(tmp_path)
    args = Namespace(auto_init=True)

    fake_git_root = tmp_path
    # Simulate "config.yaml doesn't exist yet" → auto-init will run project_init
    init_result = {"project_id": "uuid-1234", "git_root": str(fake_git_root)}

    with (
        patch("empirica.config.path_resolver.get_git_root", return_value=fake_git_root),
        patch(
            "empirica.cli.command_handlers.project_init.handle_project_init_command",
            return_value=init_result,
        ),
    ):
        performed, project_id, project_path = _handle_auto_init(
            args, output_format="json", project_id=None
        )

    assert performed is True
    assert project_id == "uuid-1234"
    assert project_path == str(fake_git_root)


def test_handle_auto_init_returns_path_even_when_already_initialized(tmp_path, monkeypatch):
    """If .empirica/config.yaml already exists, auto-init is a no-op but the
    project_path is still returned so _write_tty_session can wire instance_projects."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".empirica").mkdir()
    (tmp_path / ".empirica" / "config.yaml").write_text("version: 2\n")
    args = Namespace(auto_init=True)

    with patch("empirica.config.path_resolver.get_git_root", return_value=tmp_path):
        performed, project_id, project_path = _handle_auto_init(
            args, output_format="json", project_id="existing-uuid"
        )

    # No init ran, but the path is still surfaced (auto_init_performed=False)
    assert performed is False
    assert project_id == "existing-uuid"
    assert project_path == str(tmp_path)


def test_handle_auto_init_no_flag_returns_none_path():
    """Without --auto-init, the third element is None."""
    args = Namespace(auto_init=False)

    performed, project_id, project_path = _handle_auto_init(
        args, output_format="json", project_id="some-uuid"
    )

    assert performed is False
    assert project_id == "some-uuid"
    assert project_path is None


def test_write_tty_session_uses_override_when_provided():
    """When project_path_override is set, it bypasses the resolver entirely."""
    with patch(
        "empirica.cli.command_handlers.session_create.R"
    ) as resolver_mock:
        resolver_mock.project_path.return_value = None  # resolver can't find it
        resolver_mock.tty_write = MagicMock()

        _write_tty_session("session-uuid-abc", project_path_override="/new/project/path")

    # Resolver was bypassed
    resolver_mock.project_path.assert_not_called()
    # tty_write got the override path
    resolver_mock.tty_write.assert_called_once_with(
        empirica_session_id="session-uuid-abc",
        project_path="/new/project/path",
    )


def test_write_tty_session_falls_back_to_resolver_when_no_override():
    """Backward-compat: with no override, the resolver chain is consulted."""
    with patch(
        "empirica.cli.command_handlers.session_create.R"
    ) as resolver_mock:
        resolver_mock.project_path.return_value = "/resolved/by/chain"
        resolver_mock.tty_write = MagicMock()

        _write_tty_session("session-uuid-def")

    resolver_mock.project_path.assert_called_once()
    resolver_mock.tty_write.assert_called_once_with(
        empirica_session_id="session-uuid-def",
        project_path="/resolved/by/chain",
    )


def test_write_tty_session_skips_when_resolver_returns_none_and_no_override():
    """If neither override nor resolver provides a path, tty_write is skipped (no-op)."""
    with patch(
        "empirica.cli.command_handlers.session_create.R"
    ) as resolver_mock:
        resolver_mock.project_path.return_value = None
        resolver_mock.tty_write = MagicMock()

        _write_tty_session("session-uuid-ghi")

    resolver_mock.tty_write.assert_not_called()
