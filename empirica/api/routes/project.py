"""Project-level epistemic endpoints for Forgejo integration.

Provides aggregate stats, findings, unknowns, and breadcrumbs
for display in the Forgejo epistemic injector.
"""

import json
import logging
from flask import Blueprint, jsonify, request

bp = Blueprint("project", __name__)
logger = logging.getLogger(__name__)


def _get_db():
    from empirica.api.app import get_db
    return get_db()


@bp.route("/project/stats", methods=["GET"])
def project_stats():
    """
    Get aggregate epistemic statistics across all projects.

    Returns counts of findings, unknowns, dead_ends, mistakes, goals,
    and the latest session confidence metrics.
    """
    try:
        db = _get_db()

        # Count findings
        db.adapter.execute("SELECT count(*) as cnt FROM project_findings")
        findings_count = (db.adapter.fetchone() or {}).get("cnt", 0)

        # Count unknowns (unresolved)
        db.adapter.execute(
            "SELECT count(*) as cnt FROM project_unknowns WHERE is_resolved = FALSE"
        )
        unknowns_count = (db.adapter.fetchone() or {}).get("cnt", 0)

        # Count dead ends
        db.adapter.execute("SELECT count(*) as cnt FROM project_dead_ends")
        dead_ends_count = (db.adapter.fetchone() or {}).get("cnt", 0)

        # Count mistakes
        db.adapter.execute("SELECT count(*) as cnt FROM mistakes_made")
        mistakes_count = (db.adapter.fetchone() or {}).get("cnt", 0)

        # Count goals
        db.adapter.execute("SELECT count(*) as cnt FROM goals")
        goals_count = (db.adapter.fetchone() or {}).get("cnt", 0)

        # Count sessions
        db.adapter.execute("SELECT count(*) as cnt FROM sessions")
        sessions_count = (db.adapter.fetchone() or {}).get("cnt", 0)

        return jsonify({
            "ok": True,
            "stats": {
                "findings": findings_count,
                "unknowns": unknowns_count,
                "dead_ends": dead_ends_count,
                "mistakes": mistakes_count,
                "goals": goals_count,
                "sessions": sessions_count
            }
        })

    except Exception as e:
        logger.error(f"Error getting project stats: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@bp.route("/project/findings", methods=["GET"])
def project_findings():
    """
    Get recent findings with optional limit and search.

    Query params:
        limit: max results (default 20)
        search: text search filter
    """
    try:
        db = _get_db()
        limit = min(int(request.args.get("limit", 20)), 100)

        db.adapter.execute(
            "SELECT id, finding, impact, subject, created_timestamp "
            "FROM project_findings ORDER BY created_timestamp DESC LIMIT ?",
            (limit,)
        )
        rows = db.adapter.fetchall()

        return jsonify({
            "ok": True,
            "findings": [
                {
                    "id": r["id"],
                    "finding": r["finding"],
                    "impact": r.get("impact", 0.5),
                    "subject": r.get("subject"),
                    "timestamp": r.get("created_timestamp")
                }
                for r in rows
            ],
            "total": len(rows)
        })

    except Exception as e:
        logger.error(f"Error getting findings: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@bp.route("/project/unknowns", methods=["GET"])
def project_unknowns():
    """Get unresolved unknowns."""
    try:
        db = _get_db()
        limit = min(int(request.args.get("limit", 20)), 100)

        db.adapter.execute(
            "SELECT id, unknown, subject, is_resolved, created_timestamp "
            "FROM project_unknowns WHERE is_resolved = FALSE "
            "ORDER BY created_timestamp DESC LIMIT ?",
            (limit,)
        )
        rows = db.adapter.fetchall()

        return jsonify({
            "ok": True,
            "unknowns": [
                {
                    "id": r["id"],
                    "unknown": r["unknown"],
                    "subject": r.get("subject"),
                    "timestamp": r.get("created_timestamp")
                }
                for r in rows
            ],
            "total": len(rows)
        })

    except Exception as e:
        logger.error(f"Error getting unknowns: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@bp.route("/project/breadcrumbs", methods=["GET"])
def project_breadcrumbs():
    """
    Get recent breadcrumbs (all types interleaved, sorted by time).

    Returns a unified timeline of findings, unknowns, dead_ends, mistakes.
    """
    try:
        db = _get_db()
        limit = min(int(request.args.get("limit", 30)), 100)

        items = []

        # Findings
        db.adapter.execute(
            "SELECT id, finding as text, impact, 'finding' as type, created_timestamp "
            "FROM project_findings ORDER BY created_timestamp DESC LIMIT ?",
            (limit,)
        )
        for r in db.adapter.fetchall():
            items.append({
                "id": r["id"], "text": r["text"], "type": "finding",
                "impact": r.get("impact", 0.5), "timestamp": r["created_timestamp"]
            })

        # Unknowns
        db.adapter.execute(
            "SELECT id, unknown as text, 'unknown' as type, created_timestamp "
            "FROM project_unknowns WHERE is_resolved = FALSE "
            "ORDER BY created_timestamp DESC LIMIT ?",
            (limit,)
        )
        for r in db.adapter.fetchall():
            items.append({
                "id": r["id"], "text": r["text"], "type": "unknown",
                "impact": 0.5, "timestamp": r["created_timestamp"]
            })

        # Dead ends
        db.adapter.execute(
            "SELECT id, approach as text, 'dead_end' as type, created_timestamp "
            "FROM project_dead_ends ORDER BY created_timestamp DESC LIMIT ?",
            (limit,)
        )
        for r in db.adapter.fetchall():
            items.append({
                "id": r["id"], "text": r["text"], "type": "dead_end",
                "impact": 0.5, "timestamp": r["created_timestamp"]
            })

        # Mistakes
        db.adapter.execute(
            "SELECT id, mistake as text, 'mistake' as type, created_timestamp "
            "FROM mistakes_made ORDER BY created_timestamp DESC LIMIT ?",
            (limit,)
        )
        for r in db.adapter.fetchall():
            items.append({
                "id": r["id"], "text": r["text"], "type": "mistake",
                "impact": 0.5, "timestamp": r["created_timestamp"]
            })

        # Sort by timestamp, most recent first
        items.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

        return jsonify({
            "ok": True,
            "breadcrumbs": items[:limit],
            "total": len(items)
        })

    except Exception as e:
        logger.error(f"Error getting breadcrumbs: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
