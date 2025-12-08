"""
Handoff Commands - Epistemic session handoff reports

Enables session continuity through compressed semantic summaries.
"""

import json
import logging
from typing import Optional, Dict
from ..cli_utils import handle_cli_error

logger = logging.getLogger(__name__)


def handle_handoff_create_command(args):
    """Handle handoff-create command

    Supports two modes:
    1. Epistemic handoff (requires PREFLIGHT/POSTFLIGHT assessments)
    2. Planning handoff (documentation-only, no CASCADE workflow needed)
    """
    try:
        from empirica.core.handoff.report_generator import EpistemicHandoffReportGenerator
        from empirica.core.handoff.storage import HybridHandoffStorage
        from empirica.data.session_database import SessionDatabase

        # Parse arguments
        session_id = args.session_id
        task_summary = args.task_summary
        planning_only = getattr(args, 'planning_only', False)

        # Parse JSON arrays
        key_findings = json.loads(args.key_findings) if isinstance(args.key_findings, str) else args.key_findings
        remaining_unknowns = json.loads(args.remaining_unknowns) if args.remaining_unknowns and isinstance(args.remaining_unknowns, str) else (args.remaining_unknowns or [])
        
        # Auto-convert strings to single-item arrays for better UX
        if isinstance(key_findings, str):
            key_findings = [key_findings]
        if isinstance(remaining_unknowns, str):
            remaining_unknowns = [remaining_unknowns]
        artifacts = json.loads(args.artifacts) if args.artifacts and isinstance(args.artifacts, str) else (args.artifacts or [])

        next_session_context = args.next_session_context

        # Check if CASCADE workflow assessments exist
        db = SessionDatabase()
        preflight = db.get_preflight_assessment(session_id)
        postflight = db.get_postflight_assessment(session_id)
        has_assessments = bool(preflight) and bool(postflight)

        if not has_assessments and not planning_only:
            # User didn't provide --planning-only, but no assessments exist
            print("⚠️  No CASCADE workflow assessments found for this session")
            print()
            print("Two options:")
            print()
            print("Option 1: Create a PLANNING HANDOFF (documentation, no epistemic deltas)")
            print("  $ empirica handoff-create --session-id ... --planning-only [other args]")
            print("  → Stores documentation handoff for multi-session planning")
            print()
            print("Option 2: Create an EPISTEMIC HANDOFF (requires CASCADE workflow)")
            print("  $ empirica preflight --prompt '...'")
            print("  $ [do your work: investigate, act, etc.]")
            print("  $ empirica postflight --prompt '...'")
            print("  $ empirica handoff-create --session-id ... [other args]")
            print("  → Stores epistemic deltas (before/after vectors)")
            print()
            return None

        # Generate handoff report
        generator = EpistemicHandoffReportGenerator()

        if planning_only or not has_assessments:
            # Create planning handoff (no epistemic deltas)
            handoff = generator.generate_planning_handoff(
                session_id=session_id,
                task_summary=task_summary,
                key_findings=key_findings,
                remaining_unknowns=remaining_unknowns,
                next_session_context=next_session_context,
                artifacts_created=artifacts
            )
            handoff_type = "📋 Planning Handoff (documentation)"
        else:
            # Create epistemic handoff (with vector deltas)
            handoff = generator.generate_handoff_report(
                session_id=session_id,
                task_summary=task_summary,
                key_findings=key_findings,
                remaining_unknowns=remaining_unknowns,
                next_session_context=next_session_context,
                artifacts_created=artifacts
            )
            handoff_type = "📊 Epistemic Handoff (with deltas)"

        # Store in BOTH git notes AND database
        storage = HybridHandoffStorage()
        sync_result = storage.store_handoff(session_id, handoff)

        # Warn if partial storage
        if not sync_result['fully_synced']:
            logger.warning(
                f"⚠️ Partial storage: git={sync_result['git_stored']}, "
                f"db={sync_result['db_stored']}"
            )

        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            result = {
                "ok": True,
                "session_id": session_id,
                "handoff_id": handoff['session_id'],
                "handoff_type": "planning" if (planning_only or not has_assessments) else "epistemic",
                "token_count": len(handoff.get('compressed_json', '')) // 4,  # Rough estimate
                "storage": f"git:refs/notes/empirica/handoff/{session_id}",
                "has_epistemic_deltas": has_assessments and not planning_only,
                "epistemic_deltas": handoff.get('epistemic_deltas', {}),
                "calibration_status": handoff.get('calibration_status', 'N/A'),
                "storage_sync": sync_result
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ {handoff_type} created successfully")
            print(f"   Session: {session_id[:8]}...")
            print(f"   Token count: ~{len(handoff.get('compressed_json', '')) // 4} tokens")
            print(f"   Storage: git notes (refs/notes/empirica/handoff/)")
            if has_assessments and not planning_only:
                print(f"   Calibration: {handoff.get('calibration_status', 'N/A')}")
            else:
                print(f"   Type: Documentation-only (no CASCADE workflow assessments)")

        return handoff

    except Exception as e:
        handle_cli_error(e, "Handoff create", getattr(args, 'verbose', False))
        return None


def handle_handoff_query_command(args):
    """Handle handoff-query command"""
    try:
        from empirica.core.handoff.storage import HybridHandoffStorage

        # Parse arguments
        ai_id = getattr(args, 'ai_id', None)
        session_id = getattr(args, 'session_id', None)
        limit = getattr(args, 'limit', 5)

        # Query handoffs
        storage = HybridHandoffStorage()
        
        if session_id:
            # Query by session ID (works from either storage)
            handoff = storage.load_handoff(session_id)
            if handoff:
                handoffs = [handoff]
            else:
                handoffs = []
        elif ai_id:
            # Query by AI ID (uses database index - FAST!)
            handoffs = storage.query_handoffs(ai_id=ai_id, limit=limit)
        else:
            # Get recent handoffs (uses database - FAST!)
            handoffs = storage.query_handoffs(limit=limit)

        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            result = {
                "ok": True,
                "handoffs_count": len(handoffs),
                "handoffs": [
                    {
                        "session_id": h['session_id'],
                        "ai_id": h['ai_id'],
                        "timestamp": h['timestamp'],
                        "task_summary": h['task_summary'],
                        "epistemic_deltas": h['epistemic_deltas'],
                        "key_findings": h['key_findings'],
                        "remaining_unknowns": h['remaining_unknowns'],
                        "next_session_context": h['next_session_context'],
                        "calibration_status": h['calibration_status']
                    }
                    for h in handoffs
                ]
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"📋 Found {len(handoffs)} handoff report(s):")
            for i, h in enumerate(handoffs, 1):
                print(f"\n{i}. Session: {h['session_id'][:8]}...")
                print(f"   AI: {h['ai_id']}")
                print(f"   Task: {h['task_summary'][:60]}...")
                print(f"   Calibration: {h['calibration_status']}")
                print(f"   Token count: ~{len(h.get('compressed_json', '')) // 4}")

        return {"handoffs": handoffs}

    except Exception as e:
        handle_cli_error(e, "Handoff query", getattr(args, 'verbose', False))
        return None


# DELETE THIS - No longer needed!
# Database returns expanded format already
