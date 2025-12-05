"""Session management endpoints"""

import logging
from flask import Blueprint, request, jsonify

bp = Blueprint("sessions", __name__)
logger = logging.getLogger(__name__)


@bp.route("/sessions", methods=["GET"])
def list_sessions():
    """
    List all sessions with filtering and pagination.

    **Query Parameters:**
    - `ai_id`: Filter by AI agent (e.g., "copilot")
    - `since`: ISO timestamp (e.g., "2025-11-01")
    - `limit`: Max results (1-1000, default: 20)
    - `offset`: Pagination offset (default: 0)
    """
    try:
        from empirica.data.session_database import SessionDatabase

        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Get query parameters
        ai_id = request.args.get("ai_id")
        since = request.args.get("since")
        limit = min(int(request.args.get("limit", 20)), 1000)
        offset = int(request.args.get("offset", 0))

        # Build query
        query = "SELECT * FROM sessions WHERE 1=1"
        params = []

        if ai_id:
            query += " AND ai_id = ?"
            params.append(ai_id)

        if since:
            query += " AND start_time >= ?"
            params.append(since)

        # Get total count
        count_query = "SELECT COUNT(*) FROM sessions WHERE 1=1"
        if ai_id:
            count_query += " AND ai_id = ?"
        if since:
            count_query += " AND start_time >= ?"

        count_params = [p for p in params]  # Same params for count
        cursor.execute(count_query, count_params)
        total = cursor.fetchone()[0]

        # Get paginated results
        query += " ORDER BY start_time DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        sessions = []
        for row in rows:
            session = {
                "session_id": row[0],
                "ai_id": row[1],
                "start_time": row[3],
                "end_time": row[4],
                "duration_seconds": row[5] if len(row) > 5 else None,
                "task_summary": row[6] if len(row) > 6 else None,
                "phase": row[7] if len(row) > 7 else None,
                "overall_confidence": row[8] if len(row) > 8 else None,
                "uncertainty": row[9] if len(row) > 9 else None,
                "git_head": None,  # Would fetch from git notes
                "checkpoints_count": 0  # Would count from git notes
            }
            sessions.append(session)

        return jsonify({
            "ok": True,
            "total": total,
            "sessions": sessions
        })

    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        return jsonify({
            "ok": False,
            "error": "database_error",
            "message": str(e),
            "status_code": 500
        }), 500


@bp.route("/sessions/<session_id>", methods=["GET"])
def get_session(session_id: str):
    """
    Retrieve detailed session information including epistemic timeline and git state.

    **Path Parameters:**
    - `session_id`: Session UUID

    **Response includes:**
    - Epistemic vectors (PREFLIGHT → POSTFLIGHT)
    - Git state at session boundaries
    - Checkpoints with signature status
    - Learning deltas
    """
    try:
        from empirica.data.session_database import SessionDatabase

        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Get session info
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()

        if not row:
            return jsonify({
                "ok": False,
                "error": "session_not_found",
                "message": f"Session {session_id} does not exist",
                "status_code": 404
            }), 404

        # Get session data
        session_data = {
            "session_id": row[0],
            "ai_id": row[1],
            "start_time": row[3],
            "end_time": row[4],
            "duration_seconds": int(row[5]) if row[5] else None,
            "task_summary": row[6] if len(row) > 6 else None,
            "overall_confidence": row[8] if len(row) > 8 else None,
            "git_state": {
                "head_commit": "pending",  # Would fetch from git notes
                "commits_since_session_start": 0,
                "files_changed": [],
                "lines_added": 0,
                "lines_removed": 0
            },
            "epistemic_timeline": [],
            "checkpoints": []
        }

        # Get reflexes (epistemic assessments)
        cursor.execute(
            """
            SELECT phase, timestamp, know, do, context, clarity, coherence, signal,
                   density, state, change, completion, impact, engagement, uncertainty
            FROM reflexes
            WHERE session_id = ?
            ORDER BY timestamp ASC
            """,
            (session_id,)
        )

        for reflex in cursor.fetchall():
            timeline_entry = {
                "phase": reflex[0],
                "timestamp": reflex[1],
                "vectors": {
                    "know": reflex[2],
                    "do": reflex[3],
                    "context": reflex[4],
                    "clarity": reflex[5],
                    "coherence": reflex[6],
                    "signal": reflex[7],
                    "density": reflex[8],
                    "state": reflex[9],
                    "change": reflex[10],
                    "completion": reflex[11],
                    "impact": reflex[12],
                    "engagement": reflex[13],
                    "uncertainty": reflex[14]
                }
            }
            session_data["epistemic_timeline"].append(timeline_entry)

        return jsonify({
            "ok": True,
            "session": session_data
        })

    except Exception as e:
        logger.error(f"Error getting session {session_id}: {e}")
        return jsonify({
            "ok": False,
            "error": "database_error",
            "message": str(e),
            "status_code": 500
        }), 500


@bp.route("/sessions/<session_id>/checks", methods=["GET"])
def get_session_checks(session_id: str):
    """Get all CHECK assessments for a session with findings/unknowns"""
    try:
        from empirica.data.session_database import SessionDatabase
        import json
        
        db = SessionDatabase()
        
        # Use new reflexes-based API
        check_vectors = db.get_vectors_by_phase(session_id, phase="CHECK")
        
        checks = []
        for check_data in check_vectors:
            metadata = check_data.get('metadata', {})
            checks.append({
                "check_id": check_data.get('session_id') + "_" + str(check_data.get('round', 1)),
                "timestamp": check_data.get('timestamp'),
                "decision": metadata.get('decision', 'unknown'),
                "confidence": metadata.get('confidence', 0.5),
                "gaps_identified": metadata.get('gaps_identified', []),
                "next_investigation_targets": metadata.get('next_investigation_targets', []),
                "reasoning": check_data.get('reasoning', ''),
                "findings": metadata.get('findings', []),
                "remaining_unknowns": metadata.get('remaining_unknowns', []),
                "investigation_cycle": check_data.get('round', 1)
            })
        
        db.close()
        
        return jsonify({
            "ok": True,
            "session_id": session_id,
            "checks": checks,
            "total": len(checks)
        })
        
    except Exception as e:
        logger.error(f"Error getting checks for session {session_id}: {e}")
        return jsonify({
            "ok": False,
            "error": "database_error",
            "message": str(e)
        }), 500
