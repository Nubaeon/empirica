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

    Input modes:
    - AI-first: JSON via stdin (empirica handoff-create -)
    - Legacy: CLI flags (backward compatible)
    """
    try:
        import sys
        import os
        from empirica.core.handoff.report_generator import EpistemicHandoffReportGenerator
        from empirica.core.handoff.storage import HybridHandoffStorage
        from empirica.data.session_database import SessionDatabase
        from ..cli_utils import parse_json_safely

        # AI-FIRST MODE: Check if config file provided
        config_data = None
        if hasattr(args, 'config') and args.config:
            if args.config == '-':
                config_data = parse_json_safely(sys.stdin.read())
            else:
                if not os.path.exists(args.config):
                    print(json.dumps({"ok": False, "error": f"Config file not found: {args.config}"}))
                    sys.exit(1)
                with open(args.config, 'r') as f:
                    config_data = parse_json_safely(f.read())

        # Extract parameters from config or fall back to legacy flags
        if config_data:
            # AI-FIRST MODE
            session_id = config_data.get('session_id')
            task_summary = config_data.get('task_summary')
            key_findings = config_data.get('key_findings', [])
            remaining_unknowns = config_data.get('remaining_unknowns', [])
            next_session_context = config_data.get('next_session_context')
            artifacts = config_data.get('artifacts', [])
            planning_only = config_data.get('planning_only', False)

            # Validate required fields
            if not session_id:
                print(json.dumps({"ok": False, "error": "Config must include 'session_id' field"}))
                sys.exit(1)
            if not task_summary:
                print(json.dumps({"ok": False, "error": "Config must include 'task_summary' field"}))
                sys.exit(1)
            if not key_findings:
                print(json.dumps({"ok": False, "error": "Config must include 'key_findings' array"}))
                sys.exit(1)
            if not next_session_context:
                print(json.dumps({"ok": False, "error": "Config must include 'next_session_context' field"}))
                sys.exit(1)
        else:
            # LEGACY MODE
            session_id = args.session_id
            task_summary = args.task_summary
            planning_only = getattr(args, 'planning_only', False)

            # Parse JSON arrays from strings
            key_findings = json.loads(args.key_findings) if isinstance(args.key_findings, str) else args.key_findings
            remaining_unknowns = json.loads(args.remaining_unknowns) if args.remaining_unknowns and isinstance(args.remaining_unknowns, str) else (args.remaining_unknowns or [])

            # Auto-convert strings to single-item arrays for better UX
            if isinstance(key_findings, str):
                key_findings = [key_findings]
            if isinstance(remaining_unknowns, str):
                remaining_unknowns = [remaining_unknowns]
            artifacts = json.loads(args.artifacts) if args.artifacts and isinstance(args.artifacts, str) else (args.artifacts or [])

            next_session_context = args.next_session_context

        # Determine handoff type based on available assessments
        db = SessionDatabase()
        preflight = db.get_preflight_assessment(session_id)
        checks = db.get_check_phase_assessments(session_id)
        postflight = db.get_postflight_assessment(session_id)
        
        # Determine handoff type
        if planning_only:
            handoff_type = "planning"
            start_assessment = None
            end_assessment = None
        elif preflight and postflight:
            # Complete CASCADE: PREFLIGHT → [CHECK*] → POSTFLIGHT
            handoff_type = "complete"
            start_assessment = preflight
            end_assessment = postflight
        elif preflight and checks:
            # Investigation complete: PREFLIGHT → [CHECK*]
            handoff_type = "investigation"
            start_assessment = preflight
            end_assessment = checks[-1]  # Most recent CHECK
        elif preflight:
            # Only PREFLIGHT (rare - aborted session)
            handoff_type = "preflight_only"
            start_assessment = preflight
            end_assessment = None
        else:
            # No assessments at all
            handoff_type = None
            start_assessment = None
            end_assessment = None

        if handoff_type is None:
            # No assessments found
            print("⚠️  No CASCADE workflow assessments found for this session")
            print()
            print("Three handoff options:")
            print()
            print("Option 1: INVESTIGATION HANDOFF (PREFLIGHT + CHECK)")
            print("  → For specialist handoff after investigation phase")
            print("  $ empirica preflight → investigate → check → handoff-create")
            print("  → Epistemic deltas: PREFLIGHT → CHECK (learning from investigation)")
            print()
            print("Option 2: COMPLETE HANDOFF (PREFLIGHT + POSTFLIGHT)")
            print("  → For full workflow completion")
            print("  $ empirica preflight → work → postflight → handoff-create")
            print("  → Epistemic deltas: PREFLIGHT → POSTFLIGHT (full cycle learning)")
            print()
            print("Option 3: PLANNING HANDOFF (no assessments required)")
            print("  → For documentation-only handoff")
            print("  $ empirica handoff-create --session-id ... --planning-only [other args]")
            print("  → No epistemic deltas (documentation only)")
            print()
            return None

        # Generate handoff report based on type
        generator = EpistemicHandoffReportGenerator()

        if handoff_type == "planning":
            # Planning handoff (no epistemic deltas)
            handoff = generator.generate_planning_handoff(
                session_id=session_id,
                task_summary=task_summary,
                key_findings=key_findings,
                remaining_unknowns=remaining_unknowns,
                next_session_context=next_session_context,
                artifacts_created=artifacts
            )
            handoff_display_name = "📋 Planning Handoff"
        elif handoff_type == "investigation":
            # Investigation handoff (PREFLIGHT → CHECK deltas)
            handoff = generator.generate_handoff_report(
                session_id=session_id,
                task_summary=task_summary,
                key_findings=key_findings,
                remaining_unknowns=remaining_unknowns,
                next_session_context=next_session_context,
                artifacts_created=artifacts,
                start_assessment=start_assessment,
                end_assessment=end_assessment,
                handoff_subtype="investigation"
            )
            handoff['handoff_subtype'] = 'investigation'
            handoff['epistemic_note'] = 'PREFLIGHT → CHECK deltas (investigation phase)'
            handoff_display_name = "🔬 Investigation Handoff (PREFLIGHT→CHECK)"
        elif handoff_type == "complete":
            # Complete handoff (PREFLIGHT → POSTFLIGHT deltas)
            handoff = generator.generate_handoff_report(
                session_id=session_id,
                task_summary=task_summary,
                key_findings=key_findings,
                remaining_unknowns=remaining_unknowns,
                next_session_context=next_session_context,
                artifacts_created=artifacts,
                start_assessment=start_assessment,
                end_assessment=end_assessment,
                handoff_subtype="complete"
            )
            handoff['handoff_subtype'] = 'complete'
            handoff['epistemic_note'] = 'PREFLIGHT → POSTFLIGHT deltas (full cycle)'
            handoff_display_name = "📊 Complete Handoff (PREFLIGHT→POSTFLIGHT)"
        elif handoff_type == "preflight_only":
            # Only PREFLIGHT (aborted session)
            handoff = generator.generate_planning_handoff(
                session_id=session_id,
                task_summary=task_summary,
                key_findings=key_findings,
                remaining_unknowns=remaining_unknowns,
                next_session_context=next_session_context,
                artifacts_created=artifacts
            )
            handoff['handoff_subtype'] = 'preflight_only'
            handoff['epistemic_note'] = 'Only PREFLIGHT available (aborted session)'
            handoff_display_name = "⚠️  Preflight-Only Handoff (incomplete)"

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
                "handoff_type": handoff_type,
                "handoff_subtype": handoff.get('handoff_subtype', handoff_type),
                "token_count": len(handoff.get('compressed_json', '')) // 4,
                "storage": f"git:refs/notes/empirica/handoff/{session_id}",
                "has_epistemic_deltas": handoff_type in ["investigation", "complete"],
                "epistemic_deltas": handoff.get('epistemic_deltas', {}),
                "epistemic_note": handoff.get('epistemic_note', ''),
                "calibration_status": handoff.get('calibration_status', 'N/A'),
                "storage_sync": sync_result
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ {handoff_display_name} created successfully")
            print(f"   Session: {session_id[:8]}...")
            print(f"   Type: {handoff_type}")
            if handoff.get('epistemic_note'):
                print(f"   Note: {handoff['epistemic_note']}")
            print(f"   Token count: ~{len(handoff.get('compressed_json', '')) // 4} tokens")
            print(f"   Storage: git notes (refs/notes/empirica/handoff/)")
            if handoff_type in ["investigation", "complete"]:
                print(f"   Calibration: {handoff.get('calibration_status', 'N/A')}")
                if handoff.get('epistemic_deltas'):
                    deltas = handoff['epistemic_deltas']
                    print(f"   Epistemic deltas: KNOW {deltas.get('know', 0):+.2f}, CONTEXT {deltas.get('context', 0):+.2f}, STATE {deltas.get('state', 0):+.2f}")
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
