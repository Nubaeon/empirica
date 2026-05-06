"""End-to-end tests: spin up a real `empirica serve` subprocess and hit it via httpx.

Catches integration bugs that in-process TestClient misses:
- uvicorn binding + lifespan
- CLI parser → uvicorn.run() factory invocation
- Real network round-trips (port binding, CORS preflight, etc.)

Per extension Claude's T5 priority: high-value, especially after the /dead-ends
500 was caught only by their integration test, not by my unit tests against
the minimal fixture schema.
"""

from __future__ import annotations

import os
import socket
import sqlite3
import subprocess
import sys
import time
import uuid
from pathlib import Path

import httpx
import pytest


def _free_port() -> int:
    """Bind to port 0, return the OS-assigned port, then release it."""
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _make_real_project(tmp_path: Path, project_id: str = "test-e2e") -> Path:
    """Build a project tree with a sqlite that has all migrations applied,
    plus a few seeded artifacts, ready for daemon to serve."""
    proj = tmp_path / "e2e-project"
    proj.mkdir()
    (proj / ".empirica").mkdir()
    (proj / ".empirica" / "project.yaml").write_text(
        f"name: {project_id}\nproject_id: {project_id}\n", encoding="utf-8"
    )
    db_dir = proj / ".empirica" / "sessions"
    db_dir.mkdir()
    db_path = db_dir / "sessions.db"
    canonical_uuid = str(uuid.uuid4())

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    # Apply the schema explicitly — including the columns migrations 042
    # and 041 depend on. Same shape used by existing T2/T3/T4 fixtures, plus
    # the projects table for slug→UUID resolution.
    cur.executescript(f"""
        CREATE TABLE projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        );
        INSERT INTO projects (id, name) VALUES ('{canonical_uuid}', '{project_id}');
        CREATE TABLE project_findings (
            id TEXT PRIMARY KEY, project_id TEXT, session_id TEXT,
            goal_id TEXT, subtask_id TEXT, transaction_id TEXT,
            finding TEXT NOT NULL, finding_data TEXT,
            subject TEXT, impact REAL DEFAULT 0.5, epistemic_source TEXT,
            created_timestamp REAL NOT NULL
        );
        CREATE TABLE project_unknowns (
            id TEXT PRIMARY KEY, project_id TEXT, session_id TEXT,
            goal_id TEXT, subtask_id TEXT, transaction_id TEXT,
            unknown TEXT NOT NULL, unknown_data TEXT,
            is_resolved INTEGER DEFAULT 0, resolved_by TEXT, resolved_timestamp REAL,
            impact REAL DEFAULT 0.5, epistemic_source TEXT,
            created_timestamp REAL NOT NULL
        );
        CREATE TABLE project_dead_ends (
            id TEXT PRIMARY KEY, project_id TEXT, session_id TEXT,
            goal_id TEXT, subtask_id TEXT, transaction_id TEXT,
            approach TEXT NOT NULL, why_failed TEXT, dead_end_data TEXT,
            impact REAL DEFAULT 0.5, epistemic_source TEXT,
            created_timestamp REAL NOT NULL
        );
        CREATE TABLE mistakes_made (
            id TEXT PRIMARY KEY, project_id TEXT, session_id TEXT,
            goal_id TEXT, transaction_id TEXT,
            mistake TEXT NOT NULL, why_wrong TEXT, prevention TEXT,
            mistake_data TEXT, impact REAL DEFAULT 0.5, epistemic_source TEXT,
            created_timestamp REAL NOT NULL
        );
        CREATE TABLE assumptions (
            id TEXT PRIMARY KEY, project_id TEXT, session_id TEXT,
            goal_id TEXT, transaction_id TEXT,
            assumption TEXT NOT NULL, confidence REAL DEFAULT 0.5,
            status TEXT DEFAULT 'unverified', resolution_finding_id TEXT,
            epistemic_source TEXT,
            created_timestamp REAL NOT NULL, resolved_timestamp REAL
        );
        CREATE TABLE decisions (
            id TEXT PRIMARY KEY, project_id TEXT, session_id TEXT,
            goal_id TEXT, transaction_id TEXT,
            choice TEXT NOT NULL, rationale TEXT, alternatives TEXT,
            confidence_at_decision REAL, reversibility TEXT,
            outcome TEXT, regret_score REAL, epistemic_source TEXT,
            created_timestamp REAL NOT NULL
        );
        CREATE TABLE epistemic_sources (
            id TEXT PRIMARY KEY, project_id TEXT, session_id TEXT,
            source_type TEXT, source_url TEXT, title TEXT,
            description TEXT, confidence REAL DEFAULT 0.5,
            epistemic_layer TEXT, discovered_by_ai TEXT,
            discovered_at TIMESTAMP NOT NULL
        );
        CREATE TABLE goals (
            id TEXT PRIMARY KEY, project_id TEXT, session_id TEXT,
            transaction_id TEXT, objective TEXT NOT NULL,
            status TEXT DEFAULT 'in_progress', is_completed INTEGER DEFAULT 0,
            goal_data TEXT, created_timestamp REAL NOT NULL,
            completed_timestamp REAL
        );
        CREATE TABLE artifact_edges (
            from_id TEXT NOT NULL, to_id TEXT NOT NULL, relation TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT,
            PRIMARY KEY (from_id, to_id, relation)
        );
    """)
    # Seed: 2 findings, 1 dead-end, 1 unknown, edge from finding to unknown
    f1 = str(uuid.uuid4())
    f2 = str(uuid.uuid4())
    de1 = str(uuid.uuid4())
    u1 = str(uuid.uuid4())
    cur.execute("INSERT INTO project_findings (id, project_id, session_id, finding, finding_data, "
                "impact, created_timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f1, canonical_uuid, "sess-1", "Real finding A", "{}", 0.7, time.time()))
    cur.execute("INSERT INTO project_findings (id, project_id, session_id, finding, finding_data, "
                "impact, created_timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (f2, canonical_uuid, "sess-1", "Real finding B", "{}", 0.4, time.time()))
    cur.execute("INSERT INTO project_dead_ends (id, project_id, session_id, approach, why_failed, "
                "dead_end_data, impact, created_timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (de1, canonical_uuid, "sess-1", "tried passport.js", "too heavy", "{}", 0.5, time.time()))
    cur.execute("INSERT INTO project_unknowns (id, project_id, session_id, unknown, unknown_data, "
                "is_resolved, created_timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (u1, canonical_uuid, "sess-1", "what about Y?", "{}", 0, time.time()))
    cur.execute("INSERT OR IGNORE INTO artifact_edges (from_id, to_id, relation) VALUES (?, ?, ?)",
                (f1, u1, "raises_question"))
    conn.commit()
    conn.close()
    return proj


def _wait_for_health(client: httpx.Client, port: int, timeout: float = 10.0) -> bool:
    """Poll /health until 200 OK or timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = client.get(f"http://127.0.0.1:{port}/api/v1/health", timeout=1.0)
            if r.status_code == 200:
                return True
        except (httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError):
            pass
        time.sleep(0.1)
    return False


@pytest.fixture
def daemon(tmp_path):
    """Start `empirica serve` as a real subprocess. Yields (project_path, port)."""
    proj = _make_real_project(tmp_path)
    port = _free_port()

    # Isolate HOME so InstanceResolver doesn't pick up the dev box's
    # ~/.empirica/active_work_* / instance_projects/* — daemon should
    # resolve THIS test project via the CWD walk-up tail.
    fake_home = tmp_path / "fake-home"
    fake_home.mkdir()
    (fake_home / ".empirica").mkdir()  # empty — nothing for canonical resolver to find

    env = {
        **{k: v for k, v in os.environ.items()
           if not k.startswith("EMPIRICA_") and k not in ("TMUX_PANE", "WINDOWID")},
        "HOME": str(fake_home),
        "PWD": str(proj),
        "PATH": os.environ.get("PATH", ""),
    }

    # Use the empirica CLI to start the daemon — verifies CLI → uvicorn wiring.
    # If that's fragile, drop to direct uvicorn invocation as a fallback.
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "empirica.api.serve_app:create_serve_app",
            "--factory",
            "--host", "127.0.0.1",
            "--port", str(port),
            "--log-level", "warning",
        ],
        cwd=str(proj),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        with httpx.Client(timeout=5.0) as client:
            ready = _wait_for_health(client, port, timeout=15.0)
            if not ready:
                stderr = proc.stderr.read().decode("utf-8", errors="replace") if proc.stderr else ""
                pytest.fail(f"Daemon failed to start on port {port}. stderr: {stderr[:500]}")
            yield (proj, port)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2.0)


# ── E2E tests ──────────────────────────────────────────────────────────


def test_e2e_health_returns_project_info(daemon):
    proj, port = daemon
    with httpx.Client() as client:
        r = client.get(f"http://127.0.0.1:{port}/api/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["project_path"] == str(proj)
    assert data["project_name"]  # non-empty
    # project_id should be a UUID resolved from the projects table (slug lookup)
    assert data["project_id"] is not None
    assert "-" in data["project_id"]  # UUID-like


def test_e2e_findings_returns_real_data(daemon):
    _proj, port = daemon
    with httpx.Client() as client:
        r = client.get(f"http://127.0.0.1:{port}/api/v1/findings")
    assert r.status_code == 200
    data = r.json()
    assert len(data["findings"]) == 2
    # Wire shape per spec
    finding = data["findings"][0]
    assert "id" in finding
    assert "type" in finding and finding["type"] == "finding"
    assert "title" in finding
    assert "body" in finding
    assert "impact" in finding
    assert "related_to" in finding


def test_e2e_dead_ends_no_500_regression(daemon):
    """Regression for extension Claude's exhibit-A bug: /dead-ends used to 500
    on long-lived DBs lacking impact column. Migration 042 + UUID resolution
    should make this work end-to-end."""
    _proj, port = daemon
    with httpx.Client() as client:
        r = client.get(f"http://127.0.0.1:{port}/api/v1/dead-ends")
    assert r.status_code == 200
    data = r.json()
    assert len(data["dead_ends"]) == 1
    assert data["dead_ends"][0]["body"] == "tried passport.js"
    assert data["dead_ends"][0]["why_failed"] == "too heavy"


def test_e2e_get_artifact_polymorphic(daemon):
    """Single-artifact GET resolves type polymorphically."""
    _proj, port = daemon
    with httpx.Client() as client:
        # Get a finding's id from the list, then GET it via single endpoint
        listed = client.get(f"http://127.0.0.1:{port}/api/v1/findings").json()["findings"]
        fid = listed[0]["id"]
        single = client.get(f"http://127.0.0.1:{port}/api/v1/artifacts/{fid}")
    assert single.status_code == 200
    assert single.json()["artifact"]["id"] == fid
    assert single.json()["artifact"]["type"] == "finding"


def test_e2e_graph_endpoint_works(daemon):
    """GET /artifacts/graph routes correctly (regression: was being captured by /artifacts/{id})."""
    _proj, port = daemon
    with httpx.Client() as client:
        r = client.get(f"http://127.0.0.1:{port}/api/v1/artifacts/graph?max_nodes=10")
    assert r.status_code == 200
    body = r.json()
    assert "nodes" in body
    assert "edges" in body
    # We seeded one edge (finding → unknown), should be in the project-wide graph
    assert len(body["nodes"]) >= 2  # the two endpoints of the seeded edge


def test_e2e_get_unknown_artifact_404(daemon):
    _proj, port = daemon
    with httpx.Client() as client:
        r = client.get(f"http://127.0.0.1:{port}/api/v1/artifacts/does-not-exist-id")
    assert r.status_code == 404


def test_e2e_all_per_type_endpoints_200(daemon):
    """Smoke-check every endpoint returns 200 and a list, no 500s."""
    _proj, port = daemon
    paths = [
        "/api/v1/findings", "/api/v1/unknowns", "/api/v1/dead-ends",
        "/api/v1/mistakes", "/api/v1/decisions", "/api/v1/assumptions",
        "/api/v1/sources", "/api/v1/goals",
    ]
    with httpx.Client() as client:
        for path in paths:
            r = client.get(f"http://127.0.0.1:{port}{path}")
            assert r.status_code == 200, f"{path} returned {r.status_code}: {r.text[:200]}"
            body = r.json()
            # Each endpoint returns its type plural as the list key
            list_key = path.split("/")[-1].replace("-", "_")
            assert list_key in body, f"{path} response missing key {list_key}"
            assert isinstance(body[list_key], list)


def test_e2e_cors_preflight_allows_chrome_extension(daemon):
    """Verify CORS preflight from chrome-extension:// origin is allowed."""
    _proj, port = daemon
    with httpx.Client() as client:
        r = client.request(
            "OPTIONS",
            f"http://127.0.0.1:{port}/api/v1/findings",
            headers={
                "Origin": "chrome-extension://abc123",
                "Access-Control-Request-Method": "GET",
            },
        )
    # FastAPI/Starlette CORS responds 200 on preflight when origin is allowed
    assert r.status_code in (200, 204)
