"""Session management endpoints

Uses SessionDatabase through the adapter layer.
All row access is dict-based (both SQLite and PostgreSQL adapters return dicts).
All queries use ? placeholders (PostgreSQLAdapter auto-converts to %s).
"""

import logging
import os
from flask import Blueprint, request, jsonify

bp = Blueprint("sessions", __name__)
logger = logging.getLogger(__name__)

# Security: Only expose detailed errors in debug mode
_DEBUG_MODE = os.environ.get("FLASK_DEBUG", "false").lower() == "true"


def _safe_error_message(error: Exception) -> str:
    """Return error message safe for client response."""
    return str(error) if _DEBUG_MODE else "An internal error occurred"


def _get_db():
    """Get shared database instance from app module."""
    from empirica.api.app import get_db
    return get_db()


@bp.route("/sessions", methods=["GET"])
def list_sessions():
    """
    List all sessions with filtering and pagination.

    Query Parameters:
    - ai_id: Filter by AI agent
    - since: ISO timestamp
    - limit: Max results (1-1000, default: 20)
    - offset: Pagination offset (default: 0)
    """
    try:
        db = _get_db()

        ai_id = request.args.get("ai_id")
        since = request.args.get("since")
        limit = min(int(request.args.get("limit", 20)), 1000)
        offset = int(request.args.get("offset", 0))

        # Build WHERE clause
        conditions = ["1=1"]
        params = []

        if ai_id:
            conditions.append("ai_id = ?")
            params.append(ai_id)
        if since:
            conditions.append("start_time >= ?")
            params.append(since)

        where = " AND ".join(conditions)

        # Get total count
        db.adapter.execute(
            f"SELECT COUNT(*) as cnt FROM sessions WHERE {where}",
            tuple(params)
        )
        count_row = db.adapter.fetchone()
        total = count_row["cnt"] if count_row else 0

        # Get paginated results
        db.adapter.execute(
            f"SELECT * FROM sessions WHERE {where} ORDER BY start_time DESC LIMIT ? OFFSET ?",
            tuple(params + [limit, offset])
        )
        rows = db.adapter.fetchall()

        sessions = []
        for row in rows:
            sessions.append({
                "session_id": row.get("session_id"),
                "ai_id": row.get("ai_id"),
                "start_time": str(row.get("start_time", "")),
                "end_time": str(row.get("end_time", "")) if row.get("end_time") else None,
                "total_turns": row.get("total_turns", 0),
                "task_summary": row.get("session_notes"),
                "overall_confidence": row.get("avg_confidence"),
                "git_head": None,
                "checkpoints_count": 0
            })

        return jsonify({
            "ok": True,
            "total": total,
            "sessions": sessions
        })

    except Exception as e:
        logger.error(f"Error listing sessions: {e}", exc_info=True)
        return jsonify({
            "ok": False,
            "error": "database_error",
            "message": _safe_error_message(e),
            "status_code": 500
        }), 500


@bp.route("/sessions/<session_id>", methods=["GET"])
def get_session(session_id: str):
    """Retrieve detailed session information including epistemic timeline."""
    try:
        db = _get_db()

        # Get session info
        db.adapter.execute(
            "SELECT * FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        row = db.adapter.fetchone()

        if not row:
            return jsonify({
                "ok": False,
                "error": "session_not_found",
                "message": f"Session {session_id} does not exist",
                "status_code": 404
            }), 404

        session_data = {
            "session_id": row.get("session_id"),
            "ai_id": row.get("ai_id"),
            "start_time": str(row.get("start_time", "")),
            "end_time": str(row.get("end_time", "")) if row.get("end_time") else None,
            "total_turns": row.get("total_turns", 0),
            "task_summary": row.get("session_notes"),
            "overall_confidence": row.get("avg_confidence"),
            "git_state": {
                "head_commit": "pending",
                "commits_since_session_start": 0,
                "files_changed": [],
                "lines_added": 0,
                "lines_removed": 0
            },
            "epistemic_timeline": [],
            "checkpoints": []
        }

        # Get reflexes (epistemic assessments)
        # Quote "do" since it's a reserved word in PostgreSQL
        db.adapter.execute(
            """SELECT phase, "timestamp", know, "do", context, clarity,
                      coherence, signal, density, state, change, completion,
                      impact, engagement, uncertainty
               FROM reflexes WHERE session_id = ? ORDER BY "timestamp" ASC""",
            (session_id,)
        )

        for reflex in db.adapter.fetchall():
            session_data["epistemic_timeline"].append({
                "phase": reflex.get("phase"),
                "timestamp": reflex.get("timestamp"),
                "vectors": {
                    "know": reflex.get("know"),
                    "do": reflex.get("do"),
                    "context": reflex.get("context"),
                    "clarity": reflex.get("clarity"),
                    "coherence": reflex.get("coherence"),
                    "signal": reflex.get("signal"),
                    "density": reflex.get("density"),
                    "state": reflex.get("state"),
                    "change": reflex.get("change"),
                    "completion": reflex.get("completion"),
                    "impact": reflex.get("impact"),
                    "engagement": reflex.get("engagement"),
                    "uncertainty": reflex.get("uncertainty")
                }
            })

        return jsonify({
            "ok": True,
            "session": session_data
        })

    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}", exc_info=True)
        return jsonify({
            "ok": False,
            "error": "database_error",
            "message": _safe_error_message(e),
            "status_code": 500
        }), 500


@bp.route("/sessions/<session_id>/checks", methods=["GET"])
def get_session_checks(session_id: str):
    """Get all CHECK assessments for a session"""
    try:
        db = _get_db()

        db.adapter.execute(
            """SELECT phase, round, "timestamp", know, "do", context, clarity,
                      coherence, signal, density, state, change, completion,
                      impact, engagement, uncertainty, reasoning, reflex_data
               FROM reflexes WHERE session_id = ? AND phase = 'CHECK'
               ORDER BY "timestamp" ASC""",
            (session_id,)
        )

        checks = []
        for check in db.adapter.fetchall():
            import json
            metadata = {}
            if check.get("reflex_data"):
                try:
                    metadata = json.loads(check["reflex_data"])
                except (json.JSONDecodeError, TypeError):
                    pass

            checks.append({
                "check_id": f"{session_id}_{check.get('round', 1)}",
                "timestamp": check.get("timestamp"),
                "decision": metadata.get("decision", "unknown"),
                "confidence": check.get("know", 0.5),
                "reasoning": check.get("reasoning", ""),
                "investigation_cycle": check.get("round", 1)
            })

        return jsonify({
            "ok": True,
            "session_id": session_id,
            "checks": checks,
            "total": len(checks)
        })

    except Exception as e:
        logger.error(f"Error getting checks for session {session_id}: {e}", exc_info=True)
        return jsonify({
            "ok": False,
            "error": "database_error",
            "message": _safe_error_message(e)
        }), 500
