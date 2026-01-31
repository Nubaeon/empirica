"""Learning delta and commit epistemic endpoints

Uses SessionDatabase through the adapter layer.
All queries use ? placeholders (auto-converted for PostgreSQL).
"""

import json
import logging
from flask import Blueprint, jsonify

bp = Blueprint("deltas", __name__)
logger = logging.getLogger(__name__)


def _get_db():
    from empirica.api.app import get_db
    return get_db()


@bp.route("/sessions/<session_id>/deltas", methods=["GET"])
def get_session_deltas(session_id: str):
    """
    Get epistemic changes from PREFLIGHT to POSTFLIGHT.

    Returns deltas for each epistemic vector and learning velocity.
    """
    try:
        db = _get_db()
        vector_cols = """know, "do", context, clarity, coherence, signal,
                         density, state, change, completion, impact, engagement, uncertainty"""

        # Get PREFLIGHT
        db.adapter.execute(
            f'SELECT {vector_cols} FROM reflexes WHERE session_id = ? AND phase = \'PREFLIGHT\' ORDER BY "timestamp" ASC LIMIT 1',
            (session_id,)
        )
        preflight = db.adapter.fetchone()

        if not preflight:
            return jsonify({
                "ok": False,
                "error": "no_preflight",
                "message": "Session has no PREFLIGHT assessment"
            }), 404

        # Get POSTFLIGHT
        db.adapter.execute(
            f'SELECT {vector_cols} FROM reflexes WHERE session_id = ? AND phase = \'POSTFLIGHT\' ORDER BY "timestamp" DESC LIMIT 1',
            (session_id,)
        )
        postflight = db.adapter.fetchone()

        if not postflight:
            return jsonify({
                "ok": False,
                "error": "no_postflight",
                "message": "Session has no POSTFLIGHT assessment"
            }), 404

        # Calculate deltas
        vector_names = [
            "know", "do", "context", "clarity", "coherence", "signal",
            "density", "state", "change", "completion", "impact", "engagement", "uncertainty"
        ]

        deltas = {}
        for name in vector_names:
            pre = float(preflight.get(name, 0) or 0)
            post = float(postflight.get(name, 0) or 0)
            deltas[name] = {
                "preflight": round(pre, 2),
                "postflight": round(post, 2),
                "delta": round(post - pre, 2)
            }

        # Get session duration
        db.adapter.execute(
            "SELECT start_time, end_time FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        session = db.adapter.fetchone()
        duration_seconds = 3600  # Default 1hr placeholder
        if session and session.get("end_time") and session.get("start_time"):
            try:
                from datetime import datetime
                start = datetime.fromisoformat(str(session["start_time"]))
                end = datetime.fromisoformat(str(session["end_time"]))
                duration_seconds = max(1, int((end - start).total_seconds()))
            except (ValueError, TypeError):
                pass

        return jsonify({
            "ok": True,
            "session_id": session_id,
            "deltas": deltas,
            "learning_velocity": {
                "know_per_minute": round(deltas["know"]["delta"] / (duration_seconds / 60), 4),
                "overall_per_minute": round(
                    sum(deltas[k]["delta"] for k in vector_names) / len(vector_names) / (duration_seconds / 60), 4
                )
            }
        })

    except Exception as e:
        logger.error(f"Error getting deltas: {e}")
        return jsonify({
            "ok": False,
            "error": "database_error",
            "message": str(e),
            "status_code": 500
        }), 500


@bp.route("/commits/<commit_sha>/epistemic", methods=["GET"])
def get_commit_epistemic(commit_sha: str):
    """
    Get epistemic state associated with a specific git commit.

    Queries the reflexes table for the session that was active at commit time,
    using git notes data populated by the sync pipeline (empirica rebuild --from-notes).

    Returns epistemic vectors, confidence label, and learning delta.
    """
    try:
        db = _get_db()

        # Check if commit_epistemics table exists (created by sync pipeline)
        if db.adapter.table_exists("commit_epistemics"):
            db.adapter.execute(
                "SELECT * FROM commit_epistemics WHERE commit_sha = ?",
                (commit_sha,)
            )
            row = db.adapter.fetchone()

            if row:
                investigated = []
                not_investigated = []
                if row.get("investigated"):
                    try:
                        investigated = json.loads(row["investigated"])
                    except (json.JSONDecodeError, TypeError):
                        pass
                if row.get("not_investigated"):
                    try:
                        not_investigated = json.loads(row["not_investigated"])
                    except (json.JSONDecodeError, TypeError):
                        pass

                know = float(row.get("know", 0) or 0)
                uncertainty = float(row.get("uncertainty", 0) or 0)

                if know >= 0.8 and uncertainty <= 0.2:
                    confidence_label = "high"
                elif know >= 0.6 and uncertainty <= 0.4:
                    confidence_label = "moderate"
                elif know >= 0.4:
                    confidence_label = "low"
                else:
                    confidence_label = "very_low"

                return jsonify({
                    "ok": True,
                    "commit_sha": commit_sha,
                    "commit_message": row.get("commit_message", ""),
                    "epistemic_context": {
                        "session_id": row.get("session_id", ""),
                        "ai_id": row.get("ai_id", ""),
                        "know": know,
                        "uncertainty": uncertainty,
                        "completion": float(row.get("completion", 0) or 0),
                        "impact": float(row.get("impact", 0) or 0),
                        "context": float(row.get("context", 0) or 0),
                        "clarity": float(row.get("clarity", 0) or 0),
                        "coherence": float(row.get("coherence", 0) or 0),
                        "investigated": investigated,
                        "not_investigated": not_investigated,
                        "confidence_basis": row.get("confidence_basis", "empirica_vectors"),
                        "confidence_label": confidence_label,
                        "risk_assessment": row.get("risk_assessment", "unknown")
                    },
                    "learning_delta": {
                        "know": float(row.get("learning_delta_know", 0) or 0),
                        "do": float(row.get("learning_delta_do", 0) or 0),
                        "overall": float(row.get("learning_delta_overall", 0) or 0)
                    }
                })

        # No data found
        return jsonify({
            "ok": False,
            "error": "no_epistemic_data",
            "commit_sha": commit_sha,
            "message": "No epistemic data for this commit. Push git notes and run rebuild."
        }), 404

    except Exception as e:
        logger.error(f"Error getting commit epistemic for {commit_sha}: {e}")
        return jsonify({
            "ok": False,
            "error": "database_error",
            "message": str(e),
            "status_code": 500
        }), 500
