"""Artifact list endpoints for the local daemon (v0.5 LOCAL-ARTIFACTS).

Eight per-type GETs sharing project-scoping + edge attachment:
  /api/v1/goals
  /api/v1/findings
  /api/v1/decisions
  /api/v1/unknowns
  /api/v1/dead-ends
  /api/v1/mistakes
  /api/v1/assumptions
  /api/v1/sources

All endpoints are scoped to the daemon's active project (resolved at startup
via `daemon_project.get_cached_daemon_project()`). If the daemon is launched
outside any project, every endpoint returns 503 with a hint.

Each row carries `related_to[]` populated from the `artifact_edges` table
(post-migration 041). Inverse-edge queries are cheap thanks to the
`(to_id, relation)` index.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from empirica.api.daemon_project import get_cached_daemon_project

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["artifacts"])


# ── Project-scope guard ──────────────────────────────────────────────


def _require_project_path() -> str:
    """Return the daemon's active project path or raise 503.

    Per spec: when daemon is launched outside any project tree, the new
    per-project endpoints return 503 with a hint to either cd into a
    project tree before running `empirica serve` or to set the active
    project via `empirica project-switch`.
    """
    project = get_cached_daemon_project()
    if not project or not project.get("project_path"):
        raise HTTPException(
            status_code=503,
            detail=(
                "Daemon not bound to a project. Run `empirica serve` from inside "
                "a project tree (or set active project with `empirica project-switch`) "
                "and restart."
            ),
        )
    return project["project_path"]


# ── DB connection (per-request) ──────────────────────────────────────


class _ReadOnlyDB:
    """Lightweight sqlite3 wrapper for daemon read endpoints.

    Daemon doesn't need SessionDatabase's migration runner / repositories /
    schema-create behavior — it's a read-only consumer of a project's existing
    sqlite. Direct sqlite3 keeps the route handlers fast and avoids dragging
    in the full SessionDatabase init chain.
    """

    def __init__(self, db_path: str):
        import sqlite3
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        if self.conn:
            self.conn.close()


def _open_db() -> _ReadOnlyDB:
    """Open a read-only sqlite connection to the daemon's project sqlite."""
    from pathlib import Path
    project_path = _require_project_path()
    db_path = str(Path(project_path) / ".empirica" / "sessions" / "sessions.db")
    return _ReadOnlyDB(db_path)


# ── Edge attachment ──────────────────────────────────────────────────


def _attach_related_to(
    db, rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """For each row in `rows`, populate `row['related_to']` from artifact_edges.

    related_to[] format (per spec wire contract):
        [{"id": "<other-artifact-id>", "type": "<type>", "relation": "<rel>"}, ...]

    Uses one query for all rows (`from_id IN (...)`), then in-memory groups.
    Edge rows whose target type can't be inferred (target not found in any
    artifact table) get `type: "unknown"` so the wire contract still holds.
    """
    if not rows or not db.conn:
        return rows
    from_ids = [r["id"] for r in rows]
    if not from_ids:
        return rows

    placeholders = ",".join("?" * len(from_ids))
    cursor = db.conn.cursor()
    cursor.execute(
        f"SELECT from_id, to_id, relation FROM artifact_edges WHERE from_id IN ({placeholders})",
        from_ids,
    )
    raw_edges = cursor.fetchall()

    # Resolve to_id → type by checking each artifact table once for the union of to_ids
    to_ids = list({e[1] for e in raw_edges})
    type_index: dict[str, str] = {}
    if to_ids:
        type_lookups = [
            ("finding", "project_findings"),
            ("unknown", "project_unknowns"),
            ("dead_end", "project_dead_ends"),
            ("mistake", "mistakes_made"),
            ("assumption", "assumptions"),
            ("decision", "decisions"),
            ("source", "epistemic_sources"),
            ("goal", "goals"),
        ]
        ph = ",".join("?" * len(to_ids))
        for type_label, table in type_lookups:
            try:
                cursor.execute(f"SELECT id FROM {table} WHERE id IN ({ph})", to_ids)
                for row in cursor.fetchall():
                    type_index[row[0]] = type_label
            except Exception as e:
                logger.debug(f"_attach_related_to: type lookup on {table} failed: {e}")

    # Group edges by from_id
    edges_by_from: dict[str, list[dict[str, str]]] = {}
    for from_id, to_id, relation in raw_edges:
        edges_by_from.setdefault(from_id, []).append({
            "id": to_id,
            "type": type_index.get(to_id, "unknown"),
            "relation": relation,
        })

    for row in rows:
        row["related_to"] = edges_by_from.get(row["id"], [])
    return rows


# ── Common shape helpers ──────────────────────────────────────────────


def _to_iso(epoch_or_iso: Any) -> str | None:
    """Normalize timestamp to ISO 8601 string. Accepts REAL epoch or already-ISO TEXT."""
    if epoch_or_iso is None:
        return None
    if isinstance(epoch_or_iso, str):
        return epoch_or_iso  # assume already ISO
    try:
        from datetime import datetime, timezone
        return datetime.fromtimestamp(float(epoch_or_iso), tz=timezone.utc).isoformat()
    except (ValueError, TypeError):
        return None


def _parse_data_json(raw: Any) -> dict:
    """Parse JSON data column to dict, returning {} on any error."""
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


# ── Per-type read helpers ────────────────────────────────────────────


def _list_findings(db, project_id: str, limit: int) -> list[dict[str, Any]]:
    cursor = db.conn.cursor()
    cursor.execute(
        "SELECT id, finding, finding_data, impact, epistemic_source, "
        "session_id, goal_id, subtask_id, transaction_id, "
        "subject, created_timestamp "
        "FROM project_findings WHERE project_id = ? "
        "ORDER BY created_timestamp DESC LIMIT ?",
        (project_id, limit),
    )
    rows = cursor.fetchall()
    return [
        {
            "id": r[0],
            "type": "finding",
            "title": (r[1] or "")[:100],
            "body": r[1] or "",
            "impact": r[3],
            "epistemic_source": r[4],
            "session_id": r[5],
            "goal_id": r[6],
            "subtask_id": r[7],
            "transaction_id": r[8],
            "subject": r[9],
            "created_at": _to_iso(r[10]),
            "data": _parse_data_json(r[2]),
        }
        for r in rows
    ]


def _list_unknowns(db, project_id: str, status: str, limit: int) -> list[dict[str, Any]]:
    cursor = db.conn.cursor()
    where = "project_id = ?"
    params: list[Any] = [project_id]
    if status == "open":
        where += " AND is_resolved = 0"
    elif status == "resolved":
        where += " AND is_resolved = 1"
    cursor.execute(
        f"SELECT id, unknown, unknown_data, impact, epistemic_source, "
        f"session_id, goal_id, subtask_id, transaction_id, "
        f"is_resolved, resolved_by, resolved_timestamp, created_timestamp "
        f"FROM project_unknowns WHERE {where} "
        f"ORDER BY created_timestamp DESC LIMIT ?",
        (*params, limit),
    )
    rows = cursor.fetchall()
    return [
        {
            "id": r[0],
            "type": "unknown",
            "title": (r[1] or "")[:100],
            "body": r[1] or "",
            "impact": r[3],
            "epistemic_source": r[4],
            "session_id": r[5],
            "goal_id": r[6],
            "subtask_id": r[7],
            "transaction_id": r[8],
            "status": "resolved" if r[9] else "open",
            "resolved_by": r[10],
            "resolved_at": _to_iso(r[11]),
            "created_at": _to_iso(r[12]),
            "data": _parse_data_json(r[2]),
        }
        for r in rows
    ]


def _list_dead_ends(db, project_id: str, limit: int) -> list[dict[str, Any]]:
    cursor = db.conn.cursor()
    cursor.execute(
        "SELECT id, approach, why_failed, dead_end_data, impact, epistemic_source, "
        "session_id, goal_id, subtask_id, transaction_id, created_timestamp "
        "FROM project_dead_ends WHERE project_id = ? "
        "ORDER BY created_timestamp DESC LIMIT ?",
        (project_id, limit),
    )
    rows = cursor.fetchall()
    return [
        {
            "id": r[0],
            "type": "dead_end",
            "title": (r[1] or "")[:100],
            "body": r[1] or "",
            "why_failed": r[2],
            "impact": r[4],
            "epistemic_source": r[5],
            "session_id": r[6],
            "goal_id": r[7],
            "subtask_id": r[8],
            "transaction_id": r[9],
            "created_at": _to_iso(r[10]),
            "data": _parse_data_json(r[3]),
        }
        for r in rows
    ]


def _list_mistakes(db, project_id: str, limit: int) -> list[dict[str, Any]]:
    cursor = db.conn.cursor()
    cursor.execute(
        "SELECT id, mistake, why_wrong, prevention, mistake_data, epistemic_source, "
        "session_id, goal_id, transaction_id, created_timestamp "
        "FROM mistakes_made WHERE project_id = ? "
        "ORDER BY created_timestamp DESC LIMIT ?",
        (project_id, limit),
    )
    rows = cursor.fetchall()
    return [
        {
            "id": r[0],
            "type": "mistake",
            "title": (r[1] or "")[:100],
            "body": r[1] or "",
            "why_wrong": r[2],
            "prevention": r[3],
            "epistemic_source": r[5],
            "session_id": r[6],
            "goal_id": r[7],
            "transaction_id": r[8],
            "created_at": _to_iso(r[9]),
            "data": _parse_data_json(r[4]),
        }
        for r in rows
    ]


def _list_assumptions(
    db, project_id: str, confidence_min: float, limit: int
) -> list[dict[str, Any]]:
    cursor = db.conn.cursor()
    cursor.execute(
        "SELECT id, assumption, confidence, status, resolution_finding_id, "
        "session_id, goal_id, transaction_id, created_timestamp, resolved_timestamp, "
        "epistemic_source "
        "FROM assumptions WHERE project_id = ? AND confidence >= ? "
        "ORDER BY created_timestamp DESC LIMIT ?",
        (project_id, confidence_min, limit),
    )
    rows = cursor.fetchall()
    return [
        {
            "id": r[0],
            "type": "assumption",
            "title": (r[1] or "")[:100],
            "body": r[1] or "",
            "confidence": r[2],
            "status": r[3],
            "resolution_finding_id": r[4],
            "session_id": r[5],
            "goal_id": r[6],
            "transaction_id": r[7],
            "created_at": _to_iso(r[8]),
            "resolved_at": _to_iso(r[9]),
            "epistemic_source": r[10],
        }
        for r in rows
    ]


def _list_decisions(db, project_id: str, limit: int) -> list[dict[str, Any]]:
    cursor = db.conn.cursor()
    cursor.execute(
        "SELECT id, choice, rationale, alternatives, confidence_at_decision, "
        "reversibility, outcome, regret_score, "
        "session_id, goal_id, transaction_id, created_timestamp, epistemic_source "
        "FROM decisions WHERE project_id = ? "
        "ORDER BY created_timestamp DESC LIMIT ?",
        (project_id, limit),
    )
    rows = cursor.fetchall()
    return [
        {
            "id": r[0],
            "type": "decision",
            "title": (r[1] or "")[:100],
            "choice": r[1],
            "rationale": r[2],
            "alternatives": r[3],
            "confidence_at_decision": r[4],
            "reversibility": r[5],
            "outcome": r[6],
            "regret_score": r[7],
            "session_id": r[8],
            "goal_id": r[9],
            "transaction_id": r[10],
            "created_at": _to_iso(r[11]),
            "epistemic_source": r[12],
        }
        for r in rows
    ]


def _list_sources(db, project_id: str, limit: int) -> list[dict[str, Any]]:
    cursor = db.conn.cursor()
    cursor.execute(
        "SELECT id, title, source_url, source_type, description, confidence, "
        "epistemic_layer, session_id, discovered_by_ai, discovered_at "
        "FROM epistemic_sources WHERE project_id = ? "
        "ORDER BY discovered_at DESC LIMIT ?",
        (project_id, limit),
    )
    rows = cursor.fetchall()
    return [
        {
            "id": r[0],
            "type": "source",
            "title": r[1],
            "url": r[2],
            "source_type": r[3],
            "description": r[4],
            "confidence": r[5],
            "epistemic_layer": r[6],
            "session_id": r[7],
            "discovered_by_ai": r[8],
            "created_at": _to_iso(r[9]),
        }
        for r in rows
    ]


def _list_goals(db, project_id: str, status: str, limit: int) -> list[dict[str, Any]]:
    cursor = db.conn.cursor()
    where = "project_id = ?"
    params: list[Any] = [project_id]
    if status == "active":
        where += " AND is_completed = 0"
    elif status == "completed":
        where += " AND is_completed = 1"
    elif status == "planned":
        where += " AND status = 'planned'"
    cursor.execute(
        f"SELECT id, objective, status, is_completed, goal_data, "
        f"session_id, transaction_id, created_timestamp, completed_timestamp "
        f"FROM goals WHERE {where} "
        f"ORDER BY created_timestamp DESC LIMIT ?",
        (*params, limit),
    )
    rows = cursor.fetchall()
    out: list[dict[str, Any]] = []
    for r in rows:
        gd = _parse_data_json(r[4])
        out.append({
            "id": r[0],
            "type": "goal",
            "objective": r[1],
            "status": r[2],
            "is_completed": bool(r[3]),
            "subtasks": gd.get("subtasks", []),
            "session_id": r[5],
            "transaction_id": r[6],
            "created_at": _to_iso(r[7]),
            "completed_at": _to_iso(r[8]),
            "data": gd,
        })
    return out


# ── Endpoint handlers ────────────────────────────────────────────────


@router.get("/findings")
async def list_findings(limit: int = Query(50, ge=1, le=500)):
    """List recent findings in the daemon's active project."""
    project = get_cached_daemon_project()
    if not project:
        raise HTTPException(status_code=503, detail="Daemon not bound to a project")
    project_id = project.get("project_id")
    if not project_id:
        return {"findings": [], "project_id": None}
    db = _open_db()
    try:
        rows = _list_findings(db, project_id, limit)
        rows = _attach_related_to(db, rows)
        return {"findings": rows, "project_id": project_id}
    finally:
        db.close()


@router.get("/unknowns")
async def list_unknowns(
    status: str = Query("open", pattern="^(open|resolved|all)$"),
    limit: int = Query(50, ge=1, le=500),
):
    project = get_cached_daemon_project()
    if not project:
        raise HTTPException(status_code=503, detail="Daemon not bound to a project")
    project_id = project.get("project_id")
    if not project_id:
        return {"unknowns": [], "project_id": None}
    db = _open_db()
    try:
        rows = _list_unknowns(db, project_id, status, limit)
        rows = _attach_related_to(db, rows)
        return {"unknowns": rows, "project_id": project_id}
    finally:
        db.close()


@router.get("/dead-ends")
async def list_dead_ends(limit: int = Query(50, ge=1, le=500)):
    project = get_cached_daemon_project()
    if not project:
        raise HTTPException(status_code=503, detail="Daemon not bound to a project")
    project_id = project.get("project_id")
    if not project_id:
        return {"dead_ends": [], "project_id": None}
    db = _open_db()
    try:
        rows = _list_dead_ends(db, project_id, limit)
        rows = _attach_related_to(db, rows)
        return {"dead_ends": rows, "project_id": project_id}
    finally:
        db.close()


@router.get("/mistakes")
async def list_mistakes(limit: int = Query(50, ge=1, le=500)):
    project = get_cached_daemon_project()
    if not project:
        raise HTTPException(status_code=503, detail="Daemon not bound to a project")
    project_id = project.get("project_id")
    if not project_id:
        return {"mistakes": [], "project_id": None}
    db = _open_db()
    try:
        rows = _list_mistakes(db, project_id, limit)
        rows = _attach_related_to(db, rows)
        return {"mistakes": rows, "project_id": project_id}
    finally:
        db.close()


@router.get("/assumptions")
async def list_assumptions(
    confidence_min: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=500),
):
    project = get_cached_daemon_project()
    if not project:
        raise HTTPException(status_code=503, detail="Daemon not bound to a project")
    project_id = project.get("project_id")
    if not project_id:
        return {"assumptions": [], "project_id": None}
    db = _open_db()
    try:
        rows = _list_assumptions(db, project_id, confidence_min, limit)
        rows = _attach_related_to(db, rows)
        return {"assumptions": rows, "project_id": project_id}
    finally:
        db.close()


@router.get("/decisions")
async def list_decisions(limit: int = Query(50, ge=1, le=500)):
    project = get_cached_daemon_project()
    if not project:
        raise HTTPException(status_code=503, detail="Daemon not bound to a project")
    project_id = project.get("project_id")
    if not project_id:
        return {"decisions": [], "project_id": None}
    db = _open_db()
    try:
        rows = _list_decisions(db, project_id, limit)
        rows = _attach_related_to(db, rows)
        return {"decisions": rows, "project_id": project_id}
    finally:
        db.close()


@router.get("/sources")
async def list_sources(limit: int = Query(50, ge=1, le=500)):
    project = get_cached_daemon_project()
    if not project:
        raise HTTPException(status_code=503, detail="Daemon not bound to a project")
    project_id = project.get("project_id")
    if not project_id:
        return {"sources": [], "project_id": None}
    db = _open_db()
    try:
        rows = _list_sources(db, project_id, limit)
        rows = _attach_related_to(db, rows)
        return {"sources": rows, "project_id": project_id}
    finally:
        db.close()


@router.get("/goals")
async def list_goals(
    status: str = Query("active", pattern="^(active|completed|planned|all)$"),
    limit: int = Query(50, ge=1, le=500),
):
    project = get_cached_daemon_project()
    if not project:
        raise HTTPException(status_code=503, detail="Daemon not bound to a project")
    project_id = project.get("project_id")
    if not project_id:
        return {"goals": [], "project_id": None}
    db = _open_db()
    try:
        rows = _list_goals(db, project_id, status, limit)
        rows = _attach_related_to(db, rows)
        return {"goals": rows, "project_id": project_id}
    finally:
        db.close()
