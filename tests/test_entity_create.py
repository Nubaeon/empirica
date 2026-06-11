"""Tests for the idempotent contact mint (entity-create CLI + /api/v1/entities).

Identity resolution order: email match → deterministic slug → hash-suffixed
slug on genuine collision. Re-calling with the same identity must return the
same entity_id with created=False (the mesh idempotent-ask convention applied
to the mint write).
"""

from __future__ import annotations

import json
import sqlite3
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from empirica.cli.command_handlers.entity_commands import (
    _slugify,
    handle_entity_create_command,
    mint_contact,
)
from empirica.data.repositories.workspace_db import (
    WorkspaceDBRepository,
    _ensure_workspace_schema,
)


@pytest.fixture
def repo(tmp_path):
    # check_same_thread=False: the HTTP tests run the route in
    # TestClient's worker thread against this fixture connection.
    conn = sqlite3.connect(str(tmp_path / "workspace.db"), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _ensure_workspace_schema(conn)
    r = WorkspaceDBRepository(conn)
    yield r
    r.close()


# ── slugify ────────────────────────────────────────────────────────────


def test_slugify_basic():
    # isalnum() keeps unicode letters — readable ids survive umlauts
    assert _slugify("Georg Müller") == "georg-müller"
    assert _slugify("  ACME GmbH & Co. KG ") == "acme-gmbh-co-kg"
    assert _slugify("---") == ""


# ── mint identity resolution ───────────────────────────────────────────


def test_mint_creates_readable_slug_id(repo):
    result = mint_contact("Georg Tester", company_name="NLE", repo=repo)
    assert result["ok"] and result["created"] is True
    assert result["entity_id"] == "c-georg-tester-nle"
    row = repo.get_entity("contact", "c-georg-tester-nle")
    assert row["display_name"] == "Georg Tester"
    assert row["source_table"] == "contacts"


def test_mint_is_idempotent_on_slug(repo):
    first = mint_contact("Georg Tester", company_name="NLE", repo=repo)
    second = mint_contact("Georg Tester", company_name="NLE", repo=repo)
    assert second["entity_id"] == first["entity_id"]
    assert second["created"] is False
    assert second["matched_by"] == "slug"


def test_mint_email_match_wins_over_slug(repo):
    mint_contact("Georg Tester", email="georg@nle.example", repo=repo)
    # Different name spelling, same email → same contact
    result = mint_contact("G. Tester", email="Georg@NLE.example ", repo=repo)
    assert result["created"] is False
    assert result["matched_by"] == "email"
    assert result["entity_id"] == "c-georg-tester"


def test_mint_same_slug_different_email_disambiguates(repo):
    a = mint_contact("Alex Kim", email="alex@one.example", repo=repo)
    b = mint_contact("Alex Kim", email="alex@two.example", repo=repo)
    assert a["entity_id"] == "c-alex-kim"
    assert b["created"] is True
    assert b["entity_id"].startswith("c-alex-kim-")
    assert b["entity_id"] != a["entity_id"]
    # Re-minting the second identity returns the suffixed id (no-op)
    b2 = mint_contact("Alex Kim", email="alex@two.example", repo=repo)
    assert b2["entity_id"] == b["entity_id"]
    assert b2["created"] is False


def test_mint_metadata_persisted(repo):
    mint_contact(
        "Georg Tester", email="g@x.example", phone="+43 1 234",
        role="CEO", company_name="NLE",
        extra_metadata={"source": "crm-mcp"}, repo=repo,
    )
    row = repo.get_entity("contact", "c-georg-tester-nle")
    meta = json.loads(row["metadata"])
    assert meta["email"] == "g@x.example"
    assert meta["phone"] == "+43 1 234"
    assert meta["role"] == "CEO"
    assert meta["company_name"] == "NLE"
    assert meta["source"] == "crm-mcp"


def test_mint_requires_name(repo):
    assert mint_contact("", repo=repo)["ok"] is False
    assert mint_contact("   ", repo=repo)["ok"] is False


# ── CLI handler ────────────────────────────────────────────────────────


def _make_args(**overrides):
    defaults = {
        "type": "contact", "name": "CLI Person", "email": None,
        "phone": None, "role": None, "company": None,
        "description": None, "metadata": None,
        "output": "json", "verbose": False,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_cli_creates_and_reports_json(repo, capsys):
    with patch(
        "empirica.cli.command_handlers.entity_commands.WorkspaceDBRepository.open",
        return_value=repo,
    ):
        # repo's context-manager exit closes it — guard with a no-op wrapper
        repo.__enter__ = lambda *a: repo
        repo.__exit__ = lambda *a: False
        with pytest.raises(SystemExit) as exc:
            handle_entity_create_command(_make_args(email="cli@x.example"))
    assert exc.value.code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] and out["created"] is True
    assert out["entity_id"] == "c-cli-person"


def test_cli_rejects_non_contact_type(capsys):
    with pytest.raises(SystemExit) as exc:
        handle_entity_create_command(_make_args(type="organization"))
    assert exc.value.code == 1


# ── HTTP endpoint ──────────────────────────────────────────────────────


def test_http_endpoint_mints_and_is_idempotent(repo):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from empirica.api.routes.entities import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    def fake_mint(**kwargs):
        return mint_contact(repo=repo, **kwargs)

    with patch(
        "empirica.cli.command_handlers.entity_commands.mint_contact",
        side_effect=fake_mint,
    ):
        body = {"type": "contact", "name": "HTTP Person",
                "email": "http@x.example", "company_name": "NLE"}
        r1 = client.post("/api/v1/entities", json=body)
        assert r1.status_code == 200
        assert r1.json()["created"] is True
        assert r1.json()["entity_id"] == "c-http-person-nle"

        r2 = client.post("/api/v1/entities", json=body)
        assert r2.status_code == 200
        assert r2.json()["created"] is False
        assert r2.json()["entity_id"] == r1.json()["entity_id"]


def test_http_endpoint_rejects_non_contact():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from empirica.api.routes.entities import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    r = client.post("/api/v1/entities", json={"type": "project", "name": "x"})
    assert r.status_code == 422
