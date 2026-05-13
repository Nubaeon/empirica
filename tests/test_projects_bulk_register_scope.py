"""Tests for `projects-bulk-register` scope flags (Extension Claude v0.7.8
follow-up + David's flag-decoupling pushback).

Two independent flags:
- `--force-metadata-update` → sets `force_metadata_update: true` in body;
  scope still full manifest (Cortex creates new + safe-updates existing).
- `--only-existing` → filters manifest down to intersection with Cortex's
  registered set (via GET /v1/collections). Independent of force flag.

Common pairing: both flags = refresh metadata on already-registered subset.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from empirica.cli.command_handlers.projects_commands import (
    _fetch_cortex_collections,
)

# ─── _fetch_cortex_collections ─────────────────────────────────────────


def test_fetch_cortex_collections_returns_list_on_success():
    """Successful GET /v1/collections returns the projects list."""
    fake_body = b'{"projects": [{"name": "alpha", "repo_url": "https://x/a"}, {"name": "beta", "repo_url": null}]}'

    class _Resp:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return fake_body

    with patch("urllib.request.urlopen", return_value=_Resp()):
        result = _fetch_cortex_collections("https://cortex.example.com", "sk-test", 10.0)

    assert len(result) == 2
    assert result[0]["name"] == "alpha"


def test_fetch_cortex_collections_returns_empty_on_http_error():
    """HTTPError → empty list (don't break the bulk-register flow)."""
    import urllib.error

    err = urllib.error.HTTPError(url="x", code=404, msg="Not Found", hdrs=None, fp=None)  # type: ignore[arg-type]
    with patch("urllib.request.urlopen", side_effect=err):
        result = _fetch_cortex_collections("https://cortex.example.com", "sk-test", 10.0)
    assert result == []


def test_fetch_cortex_collections_returns_empty_on_network_error():
    """URLError → empty list."""
    import urllib.error

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("conn refused")):
        result = _fetch_cortex_collections("https://cortex.example.com", "sk-test", 10.0)
    assert result == []


def test_fetch_cortex_collections_returns_empty_on_bad_json():
    """Malformed JSON → empty list."""
    class _Resp:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return b"not json"

    with patch("urllib.request.urlopen", return_value=_Resp()):
        result = _fetch_cortex_collections("https://cortex.example.com", "sk-test", 10.0)
    assert result == []


# ─── --only-existing scope filter (independent of --force-metadata-update) ──


def _make_manifest(*names_and_repos: tuple[str, str | None]) -> dict:
    """Build a discover-shaped manifest from (name, repo_url) tuples."""
    return {
        "projects": [
            {"name": name, "path": f"/tmp/{name}", "repo_url": repo}
            for name, repo in names_and_repos
        ]
    }


def _make_args(*, only_existing=False, force_metadata_update=False):
    return SimpleNamespace(
        manifest_path=None, dry_run=False,
        only_existing=only_existing,
        force_metadata_update=force_metadata_update,
        cortex_url="https://cortex.example.com", api_key="sk-test",
        timeout=10.0, output="json", includes=None, excludes=None,
    )


def test_only_existing_intersects_by_name():
    """Discovered: 5. Registered on Cortex: 2 (by name). --only-existing iterates 2."""
    from empirica.cli.command_handlers import projects_commands

    manifest = _make_manifest(
        ("alpha", "https://github.com/x/alpha"),
        ("beta", "https://github.com/x/beta"),
        ("gamma", None),
        ("delta", None),
        ("epsilon", None),
    )
    cortex_rows = [{"name": "alpha"}, {"name": "delta"}]

    posted: list[dict] = []
    def fake_register(project, *args, **kwargs):
        posted.append(project)
        return {"name": project["name"], "outcome": "registered", "status": 200}

    with patch.object(projects_commands, "load_manifest", return_value=manifest), \
         patch.object(projects_commands, "_fetch_cortex_collections", return_value=cortex_rows), \
         patch.object(projects_commands, "_register_one_project", side_effect=fake_register):
        projects_commands.handle_projects_bulk_register_command(_make_args(only_existing=True))

    assert {p["name"] for p in posted} == {"alpha", "delta"}


def test_only_existing_intersects_by_repo_url():
    """Match by repo_url even when local slug differs from Cortex's name."""
    from empirica.cli.command_handlers import projects_commands

    manifest = _make_manifest(
        ("local-alpha-renamed", "https://github.com/x/alpha"),
        ("local-beta", "https://github.com/x/beta-different"),
    )
    cortex_rows = [{"name": "alpha-cortex-name", "repo_url": "https://github.com/x/alpha"}]

    posted: list[dict] = []
    def fake_register(project, *args, **kwargs):
        posted.append(project)
        return {"name": project["name"], "outcome": "registered", "status": 200}

    with patch.object(projects_commands, "load_manifest", return_value=manifest), \
         patch.object(projects_commands, "_fetch_cortex_collections", return_value=cortex_rows), \
         patch.object(projects_commands, "_register_one_project", side_effect=fake_register):
        projects_commands.handle_projects_bulk_register_command(_make_args(only_existing=True))

    assert {p["name"] for p in posted} == {"local-alpha-renamed"}


def test_without_only_existing_iterates_all():
    """No --only-existing → full manifest iterated (existing behavior)."""
    from empirica.cli.command_handlers import projects_commands

    manifest = _make_manifest(("alpha", None), ("beta", None), ("gamma", None))

    posted: list[dict] = []
    def fake_register(project, *args, **kwargs):
        posted.append(project)
        return {"name": project["name"], "outcome": "registered", "status": 200}

    with patch.object(projects_commands, "load_manifest", return_value=manifest), \
         patch.object(projects_commands, "_fetch_cortex_collections") as mock_fetch, \
         patch.object(projects_commands, "_register_one_project", side_effect=fake_register):
        projects_commands.handle_projects_bulk_register_command(_make_args())
        mock_fetch.assert_not_called()

    assert {p["name"] for p in posted} == {"alpha", "beta", "gamma"}


def test_only_existing_empty_intersection_bails():
    """Empty intersection → bail with hint, no POSTs."""
    from empirica.cli.command_handlers import projects_commands

    manifest = _make_manifest(("alpha", None), ("beta", None))
    cortex_rows = [{"name": "totally-different"}]

    posted: list[dict] = []
    def fake_register(project, *args, **kwargs):
        posted.append(project)
        return {"name": project["name"], "outcome": "registered", "status": 200}

    with patch.object(projects_commands, "load_manifest", return_value=manifest), \
         patch.object(projects_commands, "_fetch_cortex_collections", return_value=cortex_rows), \
         patch.object(projects_commands, "_register_one_project", side_effect=fake_register):
        projects_commands.handle_projects_bulk_register_command(_make_args(only_existing=True))

    assert posted == []


def test_dry_run_with_only_existing_shows_filtered_set(capsys):
    """David's bug: `bulk-register --only-existing --dry-run` should show
    the INTERSECTION as "would register", not the full discovered set."""
    from empirica.cli.command_handlers import projects_commands

    manifest = _make_manifest(
        ("alpha", None), ("beta", None), ("gamma", None),
        ("delta", None), ("epsilon", None),
    )
    cortex_rows = [{"name": "alpha"}, {"name": "gamma"}]

    args = SimpleNamespace(
        manifest_path=None, dry_run=True, only_existing=True,
        force_metadata_update=False,
        cortex_url="https://cortex.example.com", api_key="sk-test",
        timeout=10.0, output="json", includes=None, excludes=None,
    )

    with patch.object(projects_commands, "load_manifest", return_value=manifest), \
         patch.object(projects_commands, "_fetch_cortex_collections", return_value=cortex_rows):
        projects_commands.handle_projects_bulk_register_command(args)

    out = capsys.readouterr().out
    import json
    payload = json.loads(out)
    # Should show only the intersection (2 of 5), not the full manifest
    assert len(payload["results"]) == 2
    assert {r["name"] for r in payload["results"]} == {"alpha", "gamma"}
    assert payload["dry_run"] is True


def test_plain_dry_run_does_not_require_cortex_config():
    """`bulk-register --dry-run` (no scope flags) should not require
    CORTEX_REMOTE_URL or CORTEX_API_KEY — it's just previewing."""
    from empirica.cli.command_handlers import projects_commands

    manifest = _make_manifest(("alpha", None), ("beta", None))

    args = SimpleNamespace(
        manifest_path=None, dry_run=True, only_existing=False,
        force_metadata_update=False,
        cortex_url=None, api_key=None,  # neither set
        timeout=10.0, output="json", includes=None, excludes=None,
    )

    with patch.object(projects_commands, "load_manifest", return_value=manifest), \
         patch.object(projects_commands, "_fetch_cortex_collections") as mock_fetch, \
         patch.dict("os.environ", {}, clear=False) as _:
        # Remove cortex env vars too
        import os
        for k in ("CORTEX_REMOTE_URL", "CORTEX_URL", "CORTEX_API_KEY"):
            os.environ.pop(k, None)
        # Should succeed without raising/exiting
        projects_commands.handle_projects_bulk_register_command(args)
        mock_fetch.assert_not_called()


# ─── --force-metadata-update independence ──────────────────────────────


def test_force_metadata_update_alone_iterates_all():
    """--force-metadata-update WITHOUT --only-existing → full manifest,
    each POST carries the force flag in body. Preserves the use case
    where someone wants register-new + refresh-old in one pass."""
    from empirica.cli.command_handlers import projects_commands

    manifest = _make_manifest(("alpha", None), ("beta", None), ("gamma", None))

    posted: list[tuple[dict, bool]] = []
    def fake_register(project, *args, **kwargs):
        posted.append((project, kwargs.get("force_metadata_update", False)))
        return {"name": project["name"], "outcome": "registered", "status": 200}

    with patch.object(projects_commands, "load_manifest", return_value=manifest), \
         patch.object(projects_commands, "_fetch_cortex_collections") as mock_fetch, \
         patch.object(projects_commands, "_register_one_project", side_effect=fake_register):
        projects_commands.handle_projects_bulk_register_command(
            _make_args(force_metadata_update=True),
        )
        # Without --only-existing, no need to query Cortex for intersection
        mock_fetch.assert_not_called()

    assert {p[0]["name"] for p in posted} == {"alpha", "beta", "gamma"}
    # Every POST carries force_metadata_update=True
    assert all(force for _, force in posted)


def test_both_flags_compose_for_common_use_case():
    """--only-existing --force-metadata-update → refresh metadata on the
    registered subset. David's main use case."""
    from empirica.cli.command_handlers import projects_commands

    manifest = _make_manifest(
        ("alpha", None), ("beta", None),
        ("gamma", None), ("delta", None),
    )
    cortex_rows = [{"name": "alpha"}, {"name": "gamma"}]

    posted: list[tuple[dict, bool]] = []
    def fake_register(project, *args, **kwargs):
        posted.append((project, kwargs.get("force_metadata_update", False)))
        return {"name": project["name"], "outcome": "registered", "status": 200}

    with patch.object(projects_commands, "load_manifest", return_value=manifest), \
         patch.object(projects_commands, "_fetch_cortex_collections", return_value=cortex_rows), \
         patch.object(projects_commands, "_register_one_project", side_effect=fake_register):
        projects_commands.handle_projects_bulk_register_command(
            _make_args(only_existing=True, force_metadata_update=True),
        )

    # Only 2 POSTed (intersection), both with force flag
    assert {p[0]["name"] for p in posted} == {"alpha", "gamma"}
    assert all(force for _, force in posted)
