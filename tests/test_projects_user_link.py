"""Tests for the defensive user-link POST after projects-bulk-register.

Closes prop_oqijggci4fctlejurnryhomccm (cortex AI, 2026-05-18). Cortex's
`/v1/projects/register` already runs `link_user_to_project` implicitly
on every call; this explicit POST /v1/users/me/projects eliminates the
implicit dependency.
"""

from __future__ import annotations

from unittest.mock import patch

from empirica.cli.command_handlers import projects_commands
from empirica.cli.command_handlers.projects_commands import (
    _link_user_to_project,
    _register_one_project,
)

# ─── _link_user_to_project ─────────────────────────────────────────────


def test_link_user_returns_linked_on_200():
    with patch.object(projects_commands, "_post_project",
                      return_value=(200, {"linked": True})):
        result = _link_user_to_project("https://cortex.example.com",
                                       "uuid-1", "ctx_test", 5.0)
    assert result == {"linked": True, "status": 200}


def test_link_user_returns_linked_on_204():
    with patch.object(projects_commands, "_post_project",
                      return_value=(204, None)):
        result = _link_user_to_project("https://cortex.example.com",
                                       "uuid-1", "ctx_test", 5.0)
    assert result["linked"] is True


def test_link_user_treats_409_as_already_linked():
    """409 from /v1/users/me/projects means 'already linked' — treat as success."""
    with patch.object(projects_commands, "_post_project",
                      return_value=(409, {"reason": "already_linked"})):
        result = _link_user_to_project("https://cortex.example.com",
                                       "uuid-1", "ctx_test", 5.0)
    assert result == {"linked": True, "status": 409}


def test_link_user_returns_unlinked_on_403():
    """Cross-org link rejection — non-fatal, surface the failure."""
    with patch.object(projects_commands, "_post_project",
                      return_value=(403, None)):
        result = _link_user_to_project("https://cortex.example.com",
                                       "uuid-1", "ctx_test", 5.0)
    assert result["linked"] is False
    assert result["status"] == 403


def test_link_user_returns_unlinked_on_network_error():
    import urllib.error
    with patch.object(projects_commands, "_post_project",
                      side_effect=urllib.error.URLError("no route")):
        result = _link_user_to_project("https://cortex.example.com",
                                       "uuid-1", "ctx_test", 5.0)
    assert result["linked"] is False
    assert result["status"] == 0
    assert "network:" in result["reason"]


# ─── _register_one_project link integration ────────────────────────────


def test_register_success_triggers_user_link():
    """200 register response with project_id → user-link POST fires."""
    proj = {"name": "test-proj", "repo_url": "https://github.com/x/y"}

    def fake_post(url, path, payload, api_key, timeout):
        if path == projects_commands.CORTEX_REGISTER_PATH:
            return (201, {"project_id": "uuid-123", "created": True})
        if path == projects_commands.CORTEX_USER_PROJECTS_PATH:
            return (200, {"linked": True})
        return (404, None)

    with patch.object(projects_commands, "_post_project", side_effect=fake_post):
        result = _register_one_project(proj, "https://cortex.example.com",
                                       "ctx_test", 5.0)

    assert result["outcome"] == "registered"
    assert result["project_id"] == "uuid-123"
    assert result["link"] == {"linked": True, "status": 200}


def test_register_409_still_triggers_user_link():
    """409 (already_exists) still attempts user-link — covers re-add-after-unlink."""
    proj = {"name": "test-proj"}

    def fake_post(url, path, payload, api_key, timeout):
        if path == projects_commands.CORTEX_REGISTER_PATH:
            return (409, {"project_id": "uuid-existing"})
        if path == projects_commands.CORTEX_USER_PROJECTS_PATH:
            return (200, {"linked": True})
        return (404, None)

    with patch.object(projects_commands, "_post_project", side_effect=fake_post):
        result = _register_one_project(proj, "https://cortex.example.com",
                                       "ctx_test", 5.0)

    assert result["outcome"] == "skipped"
    assert result["status"] == 409
    assert result["project_id"] == "uuid-existing"
    assert result["link"]["linked"] is True


def test_register_failure_does_not_attempt_link():
    """Non-2xx/409 register response → no link attempt (nothing to link to)."""
    proj = {"name": "test-proj"}
    link_call_count = 0

    def fake_post(url, path, payload, api_key, timeout):
        nonlocal link_call_count
        if path == projects_commands.CORTEX_USER_PROJECTS_PATH:
            link_call_count += 1
        # Both register paths return 500 — exhausted
        return (500, None)

    with patch.object(projects_commands, "_post_project", side_effect=fake_post):
        result = _register_one_project(proj, "https://cortex.example.com",
                                       "ctx_test", 5.0)

    assert result["outcome"] == "failed"
    assert link_call_count == 0
    assert "link" not in result


def test_register_success_without_project_id_records_link_skip():
    """Register success but body has no project_id → link recorded as skipped."""
    proj = {"name": "test-proj"}

    def fake_post(url, path, payload, api_key, timeout):
        if path == projects_commands.CORTEX_REGISTER_PATH:
            # Older cortex without project_id in response (degenerate case)
            return (200, {"created": True})
        return (404, None)

    with patch.object(projects_commands, "_post_project", side_effect=fake_post):
        result = _register_one_project(proj, "https://cortex.example.com",
                                       "ctx_test", 5.0)

    assert result["outcome"] == "registered"
    assert result["link"]["linked"] is False
    assert "no project_id" in result["link"]["reason"]


def test_register_success_link_failure_does_not_flip_outcome():
    """If register succeeds but user-link fails (e.g. cross-org 403),
    the register outcome stays 'registered'. Link failure is surfaced via
    result['link'] but does NOT change the top-level outcome."""
    proj = {"name": "test-proj"}

    def fake_post(url, path, payload, api_key, timeout):
        if path == projects_commands.CORTEX_REGISTER_PATH:
            return (201, {"project_id": "uuid-x"})
        if path == projects_commands.CORTEX_USER_PROJECTS_PATH:
            return (403, {"error": "forbidden"})
        return (404, None)

    with patch.object(projects_commands, "_post_project", side_effect=fake_post):
        result = _register_one_project(proj, "https://cortex.example.com",
                                       "ctx_test", 5.0)

    assert result["outcome"] == "registered"  # NOT flipped to failed
    assert result["link"]["linked"] is False
    assert result["link"]["status"] == 403
