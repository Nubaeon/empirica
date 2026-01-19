"""
Autonomy Commands

CLI command handlers for earned autonomy features:
- suggestion-log: Log AI suggestions with domain and confidence
- suggestion-list: List suggestions by status
- suggestion-review: Review and accept/reject suggestions
- trust-status: Show domain-specific trust levels

These commands support the graduated autonomy system where AI earns
more decision-making authority through demonstrated calibration.
"""

import json
import time
import uuid
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def handle_suggestion_log_command(args):
    """
    Handle suggestion-log command - log an AI suggestion for review.

    Suggestions track AI recommendations that require human review.
    Accepted suggestions boost domain-specific authority.
    Rejected suggestions (with reasons) improve calibration.

    Usage:
        empirica suggestion-log --session-id <ID> --suggestion "..." --domain architecture --confidence 0.8
    """
    try:
        from empirica.data.session_database import SessionDatabase
        from empirica.cli.utils.project_resolver import resolve_project_id

        session_id = args.session_id
        suggestion = args.suggestion
        domain = getattr(args, 'domain', None)
        confidence = getattr(args, 'confidence', 0.7)
        rationale = getattr(args, 'rationale', None)
        output_format = getattr(args, 'output', 'text')

        # Validate required fields
        if not session_id or not suggestion:
            result = {
                "ok": False,
                "error": "Required: --session-id and --suggestion",
                "hint": "Example: empirica suggestion-log --session-id <ID> --suggestion 'Refactor X to Y' --domain architecture --confidence 0.8"
            }
            if output_format == 'json':
                print(json.dumps(result, indent=2))
            else:
                print(f"❌ {result['error']}")
                print(f"💡 {result['hint']}")
            return result

        # Validate confidence range
        if not 0.0 <= confidence <= 1.0:
            result = {"ok": False, "error": f"Confidence must be 0.0-1.0, got {confidence}"}
            if output_format == 'json':
                print(json.dumps(result, indent=2))
            else:
                print(f"❌ {result['error']}")
            return result

        db = SessionDatabase()

        # Resolve project_id from session
        project_id = None
        cursor = db.conn.cursor()
        cursor.execute("SELECT project_id FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        if row and row['project_id']:
            project_id = row['project_id']

        # Generate suggestion ID
        suggestion_id = str(uuid.uuid4())

        # Build suggestion data
        suggestion_data = {
            "suggestion": suggestion,
            "domain": domain,
            "confidence": confidence,
            "rationale": rationale,
            "created_at": time.time()
        }

        # Insert suggestion
        cursor.execute("""
            INSERT INTO suggestions (
                id, session_id, project_id, suggestion, domain, confidence,
                rationale, status, created_timestamp, suggestion_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
        """, (
            suggestion_id,
            session_id,
            project_id,
            suggestion,
            domain,
            confidence,
            rationale,
            time.time(),
            json.dumps(suggestion_data)
        ))

        db.conn.commit()
        db.close()

        result = {
            "ok": True,
            "suggestion_id": suggestion_id,
            "session_id": session_id,
            "project_id": project_id,
            "domain": domain,
            "confidence": confidence,
            "status": "pending",
            "message": "Suggestion logged for review"
        }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Suggestion logged: {suggestion_id[:8]}...")
            print(f"   Domain: {domain or 'general'}")
            print(f"   Confidence: {confidence:.2f}")
            print(f"   Status: pending")
            if rationale:
                print(f"   Rationale: {rationale[:60]}...")

        return result

    except Exception as e:
        logger.exception("Error in suggestion-log command")
        result = {"ok": False, "error": str(e)}
        if getattr(args, 'output', 'text') == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ Error: {e}")
        return result


def handle_suggestion_list_command(args):
    """
    Handle suggestion-list command - list suggestions by status.

    Usage:
        empirica suggestion-list --session-id <ID>
        empirica suggestion-list --status pending
        empirica suggestion-list --domain architecture
    """
    try:
        from empirica.data.session_database import SessionDatabase

        session_id = getattr(args, 'session_id', None)
        project_id = getattr(args, 'project_id', None)
        status = getattr(args, 'status', None)
        domain = getattr(args, 'domain', None)
        limit = getattr(args, 'limit', 20)
        output_format = getattr(args, 'output', 'text')

        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Build query
        query = "SELECT * FROM suggestions WHERE 1=1"
        params = []

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        if domain:
            query += " AND domain = ?"
            params.append(domain)

        query += " ORDER BY created_timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        suggestions = []
        for row in rows:
            suggestions.append({
                "id": row['id'],
                "suggestion": row['suggestion'],
                "domain": row['domain'],
                "confidence": row['confidence'],
                "status": row['status'],
                "created_timestamp": row['created_timestamp'],
                "reviewed_by": row['reviewed_by'],
                "review_outcome": row['review_outcome']
            })

        db.close()

        result = {
            "ok": True,
            "suggestions": suggestions,
            "count": len(suggestions)
        }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            if not suggestions:
                print("📋 No suggestions found")
            else:
                print(f"📋 Suggestions ({len(suggestions)}):\n")
                for s in suggestions:
                    status_emoji = {"pending": "⏳", "accepted": "✅", "rejected": "❌", "modified": "🔄"}.get(s['status'], "❓")
                    print(f"  {status_emoji} [{s['id'][:8]}] {s['suggestion'][:60]}...")
                    print(f"     Domain: {s['domain'] or 'general'} | Confidence: {s['confidence']:.2f} | Status: {s['status']}")
                    print()

        return result

    except Exception as e:
        logger.exception("Error in suggestion-list command")
        result = {"ok": False, "error": str(e)}
        if getattr(args, 'output', 'text') == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ Error: {e}")
        return result


def handle_trust_status_command(args):
    """
    Handle trust-status command - show domain-specific trust levels.

    Usage:
        empirica trust-status
        empirica trust-status --domain architecture
    """
    try:
        from empirica.core.autonomy.trust_calculator import TrustCalculator

        domain = getattr(args, 'domain', None)
        project_id = getattr(args, 'project_id', None)
        output_format = getattr(args, 'output', 'text')

        calculator = TrustCalculator(project_id=project_id)

        if domain:
            # Get trust for specific domain
            trust = calculator.get_domain_trust(domain)
            trusts = {domain: trust}
        else:
            # Get all domain trusts
            trusts = calculator.get_all_domain_trust()

        calculator.close()

        # Format result
        result = {
            "ok": True,
            "domains": {}
        }

        for name, trust in trusts.items():
            result["domains"][name] = {
                "score": round(trust.score, 3),
                "level": trust.level.value,
                "factors": {k: round(v, 3) for k, v in trust.factors.items()},
                "suggestions_accepted": trust.suggestions_accepted,
                "suggestions_rejected": trust.suggestions_rejected,
                "recent_mistakes": trust.recent_mistakes,
                "calibration_accuracy": round(trust.calibration_accuracy, 3)
            }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print("🔐 Domain Trust Status\n")
            for name, data in result["domains"].items():
                level_emoji = {
                    "none": "⚫",
                    "low": "🔴",
                    "medium": "🟡",
                    "high": "🟢",
                    "very_high": "💚"
                }.get(data["level"], "❓")

                display_name = "Overall" if name == "_overall" else name.title()
                print(f"  {level_emoji} {display_name}: {data['level'].upper()} ({data['score']:.1%})")
                print(f"     Calibration: {data['calibration_accuracy']:.1%} | "
                      f"Suggestions: {data['suggestions_accepted']}✓ {data['suggestions_rejected']}✗ | "
                      f"Mistakes: {data['recent_mistakes']}")
                print()

        return result

    except Exception as e:
        logger.exception("Error in trust-status command")
        result = {"ok": False, "error": str(e)}
        if getattr(args, 'output', 'text') == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ Error: {e}")
        return result


def handle_suggestion_review_command(args):
    """
    Handle suggestion-review command - accept, reject, or modify a suggestion.

    Usage:
        empirica suggestion-review --suggestion-id <ID> --outcome accepted
        empirica suggestion-review --suggestion-id <ID> --outcome rejected --notes "Reason..."
    """
    try:
        from empirica.data.session_database import SessionDatabase

        suggestion_id = args.suggestion_id
        outcome = args.outcome  # accepted, rejected, modified
        notes = getattr(args, 'notes', None)
        reviewed_by = getattr(args, 'reviewed_by', 'human')
        output_format = getattr(args, 'output', 'text')

        # Validate outcome
        valid_outcomes = ['accepted', 'rejected', 'modified']
        if outcome not in valid_outcomes:
            result = {"ok": False, "error": f"Outcome must be one of: {valid_outcomes}"}
            if output_format == 'json':
                print(json.dumps(result, indent=2))
            else:
                print(f"❌ {result['error']}")
            return result

        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Update suggestion
        cursor.execute("""
            UPDATE suggestions
            SET status = 'reviewed',
                review_outcome = ?,
                review_notes = ?,
                reviewed_by = ?,
                reviewed_timestamp = ?
            WHERE id = ?
        """, (outcome, notes, reviewed_by, time.time(), suggestion_id))

        if cursor.rowcount == 0:
            result = {"ok": False, "error": f"Suggestion not found: {suggestion_id}"}
            if output_format == 'json':
                print(json.dumps(result, indent=2))
            else:
                print(f"❌ {result['error']}")
            db.close()
            return result

        db.conn.commit()
        db.close()

        result = {
            "ok": True,
            "suggestion_id": suggestion_id,
            "outcome": outcome,
            "reviewed_by": reviewed_by,
            "message": f"Suggestion {outcome}"
        }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            emoji = {"accepted": "✅", "rejected": "❌", "modified": "🔄"}[outcome]
            print(f"{emoji} Suggestion {suggestion_id[:8]}... {outcome}")
            if notes:
                print(f"   Notes: {notes}")

        return result

    except Exception as e:
        logger.exception("Error in suggestion-review command")
        result = {"ok": False, "error": str(e)}
        if getattr(args, 'output', 'text') == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ Error: {e}")
        return result


def handle_autonomy_status_command(args):
    """
    Handle autonomy-status command - show graduated Sentinel mode and escalation path.

    Usage:
        empirica autonomy-status --session-id <ID>
        empirica autonomy-status --domain architecture
    """
    try:
        from empirica.core.autonomy import GraduatedSentinel

        session_id = getattr(args, 'session_id', None)
        domain = getattr(args, 'domain', None)
        project_id = getattr(args, 'project_id', None)
        output_format = getattr(args, 'output', 'text')

        sentinel = GraduatedSentinel(
            session_id=session_id or "status-check",
            domain=domain,
            project_id=project_id
        )

        # Get status info
        requirements = sentinel.get_mode_requirements()
        escalation = sentinel.get_escalation_thresholds()

        sentinel.close()

        result = {
            "ok": True,
            "mode": requirements,
            "escalation": escalation
        }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            mode = requirements["mode"]
            score = requirements["trust_score"]
            level = requirements["trust_level"]
            domain_name = requirements["domain"]

            mode_emoji = {
                "controller": "🔒",
                "observer": "👁️",
                "advisory": "💡",
                "autonomous": "🚀"
            }.get(mode, "❓")

            print(f"\n{mode_emoji} Graduated Sentinel Status")
            print("=" * 50)
            print(f"\n  Domain: {domain_name}")
            print(f"  Trust Level: {level.upper()} ({score:.1%})")
            print(f"  Active Mode: {mode.upper()}")
            print(f"  Description: {requirements['description']}")

            if requirements.get("override_active"):
                print(f"\n  ⚠️  Mode overridden by environment variable")

            print(f"\n  📋 Mode Requirements:")
            print(f"     Human approval: {', '.join(requirements['requires_human_for']) or 'none'}")
            print(f"     Logged actions: {', '.join(requirements['logs_but_allows']) or 'none'}")
            print(f"     Auto-applies:   {', '.join(requirements['auto_applies']) or 'none'}")
            print(f"     Confidence threshold: {requirements['confidence_threshold']:.0%}")

            # Escalation path
            if escalation["next_mode"]:
                print(f"\n  📈 Escalation to {escalation['next_mode'].upper()}:")
                print(f"     Required score: {escalation['required_score']:.0%}")
                print(f"     Current gap:    {escalation['gap']:.1%}")
                print(f"     Progress:       {'▓' * int(escalation['progress'] * 10)}{'░' * (10 - int(escalation['progress'] * 10))} {escalation['progress']:.0%}")
                print(f"\n     💡 Hints:")
                for hint in escalation["hints"]:
                    print(f"        • {hint}")
            else:
                print(f"\n  🏆 Maximum autonomy level reached!")

            print()

        return result

    except Exception as e:
        logger.exception("Error in autonomy-status command")
        result = {"ok": False, "error": str(e)}
        if getattr(args, 'output', 'text') == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ Error: {e}")
        return result


def handle_evaluate_action_command(args):
    """
    Handle evaluate-action command - check if an action would be allowed.

    Usage:
        empirica evaluate-action --action "refactor authentication" --domain security
        empirica evaluate-action --action "fix typo" --confidence 0.9
    """
    try:
        from empirica.core.autonomy import GraduatedSentinel

        action = args.action
        domain = getattr(args, 'domain', None)
        project_id = getattr(args, 'project_id', None)
        confidence = getattr(args, 'confidence', 0.7)
        target = getattr(args, 'target', None)
        output_format = getattr(args, 'output', 'text')

        sentinel = GraduatedSentinel(
            session_id="action-eval",
            domain=domain,
            project_id=project_id
        )

        action_context = {
            "action": action,
            "target": target or "",
            "metadata": {}
        }

        decision = sentinel.evaluate_action(action_context, ai_confidence=confidence)
        sentinel.close()

        result = {
            "ok": True,
            "action": decision.action,
            "category": decision.category.value,
            "mode": decision.mode.value,
            "allowed": decision.allowed,
            "requires_human": decision.requires_human,
            "auto_applied": decision.auto_applied,
            "rationale": decision.rationale,
            "trust_level": decision.trust_level.value,
            "trust_score": decision.trust_score
        }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            emoji = "✅" if decision.allowed else "❌"
            category_emoji = {
                "trivial": "📝",
                "tactical": "🔧",
                "strategic": "🏗️",
                "critical": "⚠️"
            }.get(decision.category.value, "❓")

            print(f"\n{emoji} Action Evaluation")
            print("=" * 50)
            print(f"\n  Action: {action}")
            print(f"  Category: {category_emoji} {decision.category.value.upper()}")
            print(f"  Mode: {decision.mode.value.upper()} (trust: {decision.trust_score:.1%})")
            print(f"\n  Decision: {'ALLOWED' if decision.allowed else 'BLOCKED'}")
            if decision.requires_human:
                print(f"  ⚡ Requires human approval")
            if decision.auto_applied:
                print(f"  🤖 Would be auto-applied")
            print(f"\n  Rationale: {decision.rationale}")
            print()

        return result

    except Exception as e:
        logger.exception("Error in evaluate-action command")
        result = {"ok": False, "error": str(e)}
        if getattr(args, 'output', 'text') == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"❌ Error: {e}")
        return result
