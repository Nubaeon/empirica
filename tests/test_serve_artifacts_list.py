"""Tests for the per-type list endpoints (v0.5 LOCAL-ARTIFACTS T2).

Each endpoint:
- 503 when daemon isn't bound to a project
- Empty list (200) when project resolves but project_id is None (local-only)
- Real rows when project resolves with project_id
- related_to[] populated from artifact_edges table
- Filters work (status on unknowns/goals, confidence_min on assumptions)
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from empirica.api.serve_app import create_serve_app

# ── Fixtures ──────────────────────────────────────────────────────────


def _make_project_with_db(tmp_path: Path, project_id: str) -> Path:
    """Make a real project tree with .empirica/sessions/sessions.db + artifact tables."""
    proj = tmp_path / f"proj-{project_id[:8]}"
    proj.mkdir()
    (proj / ".empirica").mkdir()
    (proj / ".empirica" / "project.yaml").write_text(
        f"name: test-project\nproject_id: {project_id}\n", encoding="utf-8"
    )
    db_dir = proj / ".empirica" / "sessions"
    db_dir.mkdir()
    db_path = db_dir / "sessions.db"

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    # Minimal subset of the real schema — just enough for the list endpoints
    cursor.executescript("""
        CREATE TABLE project_findings (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            session_id TEXT,
            goal_id TEXT,
            subtask_id TEXT,
            transaction_id TEXT,
            finding TEXT NOT NULL,
            finding_data TEXT,
            subject TEXT,
            impact REAL DEFAULT 0.5,
            epistemic_source TEXT,
            created_timestamp REAL NOT NULL
        );
        CREATE TABLE project_unknowns (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            session_id TEXT,
            goal_id TEXT,
            subtask_id TEXT,
            transaction_id TEXT,
            unknown TEXT NOT NULL,
            unknown_data TEXT,
            is_resolved INTEGER DEFAULT 0,
            resolved_by TEXT,
            resolved_timestamp REAL,
            impact REAL DEFAULT 0.5,
            epistemic_source TEXT,
            created_timestamp REAL NOT NULL
        );
        CREATE TABLE project_dead_ends (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            session_id TEXT,
            goal_id TEXT,
            subtask_id TEXT,
            transaction_id TEXT,
            approach TEXT NOT NULL,
            why_failed TEXT,
            dead_end_data TEXT,
            impact REAL DEFAULT 0.5,
            epistemic_source TEXT,
            created_timestamp REAL NOT NULL
        );
        CREATE TABLE mistakes_made (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            session_id TEXT,
            goal_id TEXT,
            transaction_id TEXT,
            mistake TEXT NOT NULL,
            why_wrong TEXT,
            prevention TEXT,
            mistake_data TEXT,
            epistemic_source TEXT,
            created_timestamp REAL NOT NULL
        );
        CREATE TABLE assumptions (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            session_id TEXT,
            goal_id TEXT,
            transaction_id TEXT,
            assumption TEXT NOT NULL,
            confidence REAL DEFAULT 0.5,
            status TEXT DEFAULT 'unverified',
            resolution_finding_id TEXT,
            epistemic_source TEXT,
            created_timestamp REAL NOT NULL,
            resolved_timestamp REAL
        );
        CREATE TABLE decisions (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            session_id TEXT,
            goal_id TEXT,
            transaction_id TEXT,
            choice TEXT NOT NULL,
            rationale TEXT,
            alternatives TEXT,
            confidence_at_decision REAL,
            reversibility TEXT,
            outcome TEXT,
            regret_score REAL,
            epistemic_source TEXT,
            created_timestamp REAL NOT NULL
        );
        CREATE TABLE epistemic_sources (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            session_id TEXT,
            source_type TEXT,
            source_url TEXT,
            title TEXT,
            description TEXT,
            confidence REAL DEFAULT 0.5,
            epistemic_layer TEXT,
            discovered_by_ai TEXT,
            discovered_at TIMESTAMP NOT NULL
        );
        CREATE TABLE goals (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            session_id TEXT,
            transaction_id TEXT,
            objective TEXT NOT NULL,
            status TEXT DEFAULT 'in_progress',
            is_completed INTEGER DEFAULT 0,
            goal_data TEXT,
            created_timestamp REAL NOT NULL,
            completed_timestamp REAL
        );
        CREATE TABLE artifact_edges (
            from_id    TEXT NOT NULL,
            to_id      TEXT NOT NULL,
            relation   TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            metadata   TEXT,
            PRIMARY KEY (from_id, to_id, relation)
        );
    """)
    conn.commit()
    conn.close()
    return proj


def _insert_finding(db_path: Path, project_id: str, finding: str, **kwargs) -> str:
    art_id = str(uuid.uuid4())
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO project_findings (id, project_id, session_id, finding, finding_data, "
        "impact, epistemic_source, created_timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (art_id, project_id, kwargs.get("session_id", "sess-1"), finding,
         kwargs.get("data", "{}"), kwargs.get("impact", 0.5),
         kwargs.get("epistemic_source"), time.time()),
    )
    conn.commit()
    conn.close()
    return art_id


def _insert_decision(db_path: Path, project_id: str, choice: str) -> str:
    art_id = str(uuid.uuid4())
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO decisions (id, project_id, choice, rationale, "
        "confidence_at_decision, created_timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (art_id, project_id, choice, "because", 0.7, time.time()),
    )
    conn.commit()
    conn.close()
    return art_id


def _insert_edge(db_path: Path, from_id: str, to_id: str, relation: str):
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT OR IGNORE INTO artifact_edges (from_id, to_id, relation) VALUES (?, ?, ?)",
        (from_id, to_id, relation),
    )
    conn.commit()
    conn.close()


@pytest.fixture
def reset_daemon_cache():
    import empirica.api.daemon_project as dp
    dp._cached = False
    dp._cached_project = None
    yield
    dp._cached = False
    dp._cached_project = None


# ── 503 when no project bound ─────────────────────────────────────────


def test_findings_returns_503_when_daemon_not_bound(tmp_path, monkeypatch, reset_daemon_cache):
    bare = tmp_path / "outside-any-project"
    bare.mkdir()

    with patch("empirica.utils.session_resolver.InstanceResolver.project_path", return_value=None):
        monkeypatch.chdir(bare)
        monkeypatch.setenv("PWD", str(bare))
        client = TestClient(create_serve_app())
        response = client.get("/api/v1/findings")

    assert response.status_code == 503


def test_all_per_type_endpoints_503_consistently(tmp_path, monkeypatch, reset_daemon_cache):
    bare = tmp_path / "outside"
    bare.mkdir()

    with patch("empirica.utils.session_resolver.InstanceResolver.project_path", return_value=None):
        monkeypatch.chdir(bare)
        monkeypatch.setenv("PWD", str(bare))
        client = TestClient(create_serve_app())
        for path in ["/api/v1/goals", "/api/v1/findings", "/api/v1/decisions",
                     "/api/v1/unknowns", "/api/v1/dead-ends", "/api/v1/mistakes",
                     "/api/v1/assumptions", "/api/v1/sources"]:
            response = client.get(path)
            assert response.status_code == 503, f"{path} should 503 when no project"


# ── Empty when project resolves but project_id is None (local-only) ──


def test_findings_returns_empty_list_for_local_only_project(tmp_path, monkeypatch, reset_daemon_cache):
    """Project not on Cortex (no project_id) → empty list, not 500."""
    proj = tmp_path / "local-only"
    proj.mkdir()
    (proj / ".empirica").mkdir()
    (proj / ".empirica" / "project.yaml").write_text("name: local\n", encoding="utf-8")

    with patch("empirica.utils.session_resolver.InstanceResolver.project_path", return_value=str(proj)):
        monkeypatch.chdir(proj)
        client = TestClient(create_serve_app())
        response = client.get("/api/v1/findings")

    assert response.status_code == 200
    data = response.json()
    assert data["findings"] == []
    assert data["project_id"] is None


# ── Real rows when project resolves with project_id ──────────────────


def test_findings_returns_rows_for_active_project(tmp_path, monkeypatch, reset_daemon_cache):
    pid = str(uuid.uuid4())
    proj = _make_project_with_db(tmp_path, pid)
    db_path = proj / ".empirica" / "sessions" / "sessions.db"

    f1 = _insert_finding(db_path, pid, "Finding A", impact=0.7)
    f2 = _insert_finding(db_path, pid, "Finding B", impact=0.4)

    with patch("empirica.utils.session_resolver.InstanceResolver.project_path", return_value=str(proj)):
        monkeypatch.chdir(proj)
        client = TestClient(create_serve_app())
        response = client.get("/api/v1/findings")

    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == pid
    assert len(data["findings"]) == 2
    ids = {f["id"] for f in data["findings"]}
    assert ids == {f1, f2}
    # Wire shape per spec
    for f in data["findings"]:
        assert f["type"] == "finding"
        assert "title" in f
        assert "body" in f
        assert "impact" in f
        assert "related_to" in f


def test_findings_respects_limit(tmp_path, monkeypatch, reset_daemon_cache):
    pid = str(uuid.uuid4())
    proj = _make_project_with_db(tmp_path, pid)
    db_path = proj / ".empirica" / "sessions" / "sessions.db"
    for i in range(5):
        _insert_finding(db_path, pid, f"Finding {i}")

    with patch("empirica.utils.session_resolver.InstanceResolver.project_path", return_value=str(proj)):
        monkeypatch.chdir(proj)
        client = TestClient(create_serve_app())
        response = client.get("/api/v1/findings?limit=3")

    assert response.status_code == 200
    assert len(response.json()["findings"]) == 3


def test_findings_only_includes_active_project_rows(tmp_path, monkeypatch, reset_daemon_cache):
    """A finding tagged with another project_id should not be returned."""
    pid_a = str(uuid.uuid4())
    pid_b = str(uuid.uuid4())
    proj = _make_project_with_db(tmp_path, pid_a)
    db_path = proj / ".empirica" / "sessions" / "sessions.db"

    _insert_finding(db_path, pid_a, "mine")
    _insert_finding(db_path, pid_b, "not mine")

    with patch("empirica.utils.session_resolver.InstanceResolver.project_path", return_value=str(proj)):
        monkeypatch.chdir(proj)
        client = TestClient(create_serve_app())
        response = client.get("/api/v1/findings")

    findings = response.json()["findings"]
    assert len(findings) == 1
    assert findings[0]["body"] == "mine"


# ── related_to[] from artifact_edges ─────────────────────────────────


def test_findings_carries_related_to_from_edge_table(tmp_path, monkeypatch, reset_daemon_cache):
    pid = str(uuid.uuid4())
    proj = _make_project_with_db(tmp_path, pid)
    db_path = proj / ".empirica" / "sessions" / "sessions.db"

    f1 = _insert_finding(db_path, pid, "with edges")
    d1 = _insert_decision(db_path, pid, "linked decision")
    _insert_edge(db_path, f1, d1, "evidence")

    with patch("empirica.utils.session_resolver.InstanceResolver.project_path", return_value=str(proj)):
        monkeypatch.chdir(proj)
        client = TestClient(create_serve_app())
        response = client.get("/api/v1/findings")

    findings = response.json()["findings"]
    assert len(findings) == 1
    related = findings[0]["related_to"]
    assert len(related) == 1
    assert related[0] == {"id": d1, "type": "decision", "relation": "evidence"}


def test_related_to_target_type_is_unknown_for_dangling_edges(tmp_path, monkeypatch, reset_daemon_cache):
    """Edge pointing to a non-existent ID → type='unknown' (defensive shape)."""
    pid = str(uuid.uuid4())
    proj = _make_project_with_db(tmp_path, pid)
    db_path = proj / ".empirica" / "sessions" / "sessions.db"

    f1 = _insert_finding(db_path, pid, "with dangling edge")
    _insert_edge(db_path, f1, "ghost-id-not-in-db", "evidence")

    with patch("empirica.utils.session_resolver.InstanceResolver.project_path", return_value=str(proj)):
        monkeypatch.chdir(proj)
        client = TestClient(create_serve_app())
        response = client.get("/api/v1/findings")

    related = response.json()["findings"][0]["related_to"]
    assert related[0]["type"] == "unknown"
    assert related[0]["id"] == "ghost-id-not-in-db"


# ── Filter behavior ──────────────────────────────────────────────────


def test_unknowns_status_filter(tmp_path, monkeypatch, reset_daemon_cache):
    pid = str(uuid.uuid4())
    proj = _make_project_with_db(tmp_path, pid)
    db_path = proj / ".empirica" / "sessions" / "sessions.db"

    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO project_unknowns (id, project_id, unknown, unknown_data, is_resolved, created_timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), pid, "open Q", "{}", 0, time.time()),
    )
    conn.execute(
        "INSERT INTO project_unknowns (id, project_id, unknown, unknown_data, is_resolved, created_timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), pid, "answered", "{}", 1, time.time()),
    )
    conn.commit()
    conn.close()

    with patch("empirica.utils.session_resolver.InstanceResolver.project_path", return_value=str(proj)):
        monkeypatch.chdir(proj)
        client = TestClient(create_serve_app())
        all_resp = client.get("/api/v1/unknowns?status=all")
        open_resp = client.get("/api/v1/unknowns?status=open")
        resolved_resp = client.get("/api/v1/unknowns?status=resolved")

    assert len(all_resp.json()["unknowns"]) == 2
    assert len(open_resp.json()["unknowns"]) == 1
    assert open_resp.json()["unknowns"][0]["body"] == "open Q"
    assert len(resolved_resp.json()["unknowns"]) == 1
    assert resolved_resp.json()["unknowns"][0]["body"] == "answered"


def test_assumptions_confidence_min_filter(tmp_path, monkeypatch, reset_daemon_cache):
    pid = str(uuid.uuid4())
    proj = _make_project_with_db(tmp_path, pid)
    db_path = proj / ".empirica" / "sessions" / "sessions.db"

    conn = sqlite3.connect(str(db_path))
    for assumption, conf in [("high", 0.9), ("mid", 0.5), ("low", 0.2)]:
        conn.execute(
            "INSERT INTO assumptions (id, project_id, assumption, confidence, status, created_timestamp) "
            "VALUES (?, ?, ?, ?, 'unverified', ?)",
            (str(uuid.uuid4()), pid, assumption, conf, time.time()),
        )
    conn.commit()
    conn.close()

    with patch("empirica.utils.session_resolver.InstanceResolver.project_path", return_value=str(proj)):
        monkeypatch.chdir(proj)
        client = TestClient(create_serve_app())
        response = client.get("/api/v1/assumptions?confidence_min=0.6")

    assumptions = response.json()["assumptions"]
    assert len(assumptions) == 1
    assert assumptions[0]["body"] == "high"


def test_goals_status_filter(tmp_path, monkeypatch, reset_daemon_cache):
    pid = str(uuid.uuid4())
    proj = _make_project_with_db(tmp_path, pid)
    db_path = proj / ".empirica" / "sessions" / "sessions.db"

    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO goals (id, project_id, objective, status, is_completed, goal_data, created_timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), pid, "active goal", "in_progress", 0, "{}", time.time()),
    )
    conn.execute(
        "INSERT INTO goals (id, project_id, objective, status, is_completed, goal_data, created_timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), pid, "done goal", "completed", 1, "{}", time.time()),
    )
    conn.execute(
        "INSERT INTO goals (id, project_id, objective, status, is_completed, goal_data, created_timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), pid, "future goal", "planned", 0, "{}", time.time()),
    )
    conn.commit()
    conn.close()

    with patch("empirica.utils.session_resolver.InstanceResolver.project_path", return_value=str(proj)):
        monkeypatch.chdir(proj)
        client = TestClient(create_serve_app())
        active = client.get("/api/v1/goals?status=active").json()["goals"]
        completed = client.get("/api/v1/goals?status=completed").json()["goals"]
        planned = client.get("/api/v1/goals?status=planned").json()["goals"]
        all_g = client.get("/api/v1/goals?status=all").json()["goals"]

    assert {g["objective"] for g in active} == {"active goal", "future goal"}  # in_progress + planned both have is_completed=0
    assert {g["objective"] for g in completed} == {"done goal"}
    assert {g["objective"] for g in planned} == {"future goal"}
    assert len(all_g) == 3


def test_goals_carry_subtasks_inline(tmp_path, monkeypatch, reset_daemon_cache):
    """Per spec: goals embed subtasks[] inline from goal_data JSON."""
    pid = str(uuid.uuid4())
    proj = _make_project_with_db(tmp_path, pid)
    db_path = proj / ".empirica" / "sessions" / "sessions.db"

    goal_data = {"subtasks": [{"id": "s1", "name": "step 1"}, {"id": "s2", "name": "step 2"}]}
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO goals (id, project_id, objective, status, is_completed, goal_data, created_timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), pid, "goal with subtasks", "in_progress", 0,
         json.dumps(goal_data), time.time()),
    )
    conn.commit()
    conn.close()

    with patch("empirica.utils.session_resolver.InstanceResolver.project_path", return_value=str(proj)):
        monkeypatch.chdir(proj)
        client = TestClient(create_serve_app())
        response = client.get("/api/v1/goals?status=active")

    goal = response.json()["goals"][0]
    assert len(goal["subtasks"]) == 2
    assert goal["subtasks"][0]["name"] == "step 1"


# ── Sources endpoint shape ───────────────────────────────────────────


def test_sources_returns_sources_with_url(tmp_path, monkeypatch, reset_daemon_cache):
    pid = str(uuid.uuid4())
    proj = _make_project_with_db(tmp_path, pid)
    db_path = proj / ".empirica" / "sessions" / "sessions.db"

    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO epistemic_sources (id, project_id, source_type, source_url, title, "
        "description, confidence, discovered_at) "
        "VALUES (?, ?, 'doc', 'https://example.com/spec', 'RFC 7519', 'JWT spec', 0.95, datetime('now'))",
        (str(uuid.uuid4()), pid),
    )
    conn.commit()
    conn.close()

    with patch("empirica.utils.session_resolver.InstanceResolver.project_path", return_value=str(proj)):
        monkeypatch.chdir(proj)
        client = TestClient(create_serve_app())
        response = client.get("/api/v1/sources")

    sources = response.json()["sources"]
    assert len(sources) == 1
    assert sources[0]["title"] == "RFC 7519"
    assert sources[0]["url"] == "https://example.com/spec"


# ── Decisions / dead-ends / mistakes — smoke ──────────────────────────


def test_decisions_endpoint_returns_choice_and_rationale(tmp_path, monkeypatch, reset_daemon_cache):
    pid = str(uuid.uuid4())
    proj = _make_project_with_db(tmp_path, pid)
    db_path = proj / ".empirica" / "sessions" / "sessions.db"

    _insert_decision(db_path, pid, "Use SQLite over Postgres")

    with patch("empirica.utils.session_resolver.InstanceResolver.project_path", return_value=str(proj)):
        monkeypatch.chdir(proj)
        client = TestClient(create_serve_app())
        response = client.get("/api/v1/decisions")

    decisions = response.json()["decisions"]
    assert len(decisions) == 1
    assert decisions[0]["choice"] == "Use SQLite over Postgres"
    assert decisions[0]["rationale"] == "because"


def test_dead_ends_endpoint_returns_approach_and_why_failed(tmp_path, monkeypatch, reset_daemon_cache):
    pid = str(uuid.uuid4())
    proj = _make_project_with_db(tmp_path, pid)
    db_path = proj / ".empirica" / "sessions" / "sessions.db"

    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "INSERT INTO project_dead_ends (id, project_id, approach, why_failed, dead_end_data, created_timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), pid, "tried passport.js", "too heavy", "{}", time.time()),
    )
    conn.commit()
    conn.close()

    with patch("empirica.utils.session_resolver.InstanceResolver.project_path", return_value=str(proj)):
        monkeypatch.chdir(proj)
        client = TestClient(create_serve_app())
        response = client.get("/api/v1/dead-ends")

    dead_ends = response.json()["dead_ends"]
    assert len(dead_ends) == 1
    assert dead_ends[0]["body"] == "tried passport.js"
    assert dead_ends[0]["why_failed"] == "too heavy"
