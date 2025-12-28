"""
goals-ready command handler

Combines BEADS ready work detection with Empirica epistemic filtering.
Returns tasks that are both dependency-ready AND epistemically-ready.
"""

import json
import logging
import sys
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def handle_goals_ready_command(args):
    """Query BEADS ready work + filter by Empirica epistemic criteria
    
    Returns tasks that are:
    1. Dependency-ready (BEADS: no open blockers)
    2. Epistemically-ready (Empirica: confidence/uncertainty thresholds)
    """
    try:
        from empirica.integrations.beads import BeadsAdapter
        from empirica.data.session_database import SessionDatabase
        
        # Session ID is optional - auto-detect active session if not provided
        session_id = getattr(args, 'session_id', None)
        min_confidence = getattr(args, 'min_confidence', 0.7)
        max_uncertainty = getattr(args, 'max_uncertainty', 0.3)
        min_priority = getattr(args, 'min_priority', None)
        output_format = getattr(args, 'output', 'json')

        # Initialize adapters
        beads = BeadsAdapter()
        db = SessionDatabase()

        # Auto-detect active session if not provided
        if not session_id:
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT session_id FROM sessions
                WHERE end_time IS NULL
                ORDER BY start_time DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                session_id = row['session_id']
                if getattr(args, 'verbose', False):
                    print(f"📍 Auto-detected active session: {session_id[:8]}...", file=sys.stderr)
            else:
                result = {
                    "ok": False,
                    "error": "No active session found",
                    "hint": "Create a session: empirica session-create --ai-id <YOUR_AI_ID>"
                }
                if output_format == 'json':
                    print(json.dumps(result, indent=2))
                else:
                    print("❌ No active session found")
                    print("   Hint: Create a session: empirica session-create --ai-id <YOUR_AI_ID>")
                db.close()
                return 0
        
        ready_work = []
        
        # Check if BEADS available
        if not beads.is_available():
            result = {
                "ok": False,
                "error": "BEADS not available",
                "hint": "Install bd CLI or use goals without --use-beads",
                "ready_work": []
            }
            
            if output_format == 'json':
                print(json.dumps(result, indent=2))
            else:
                print("❌ BEADS not available")
                print("   Hint: Install bd CLI: curl -fsSL https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.sh | bash")
            
            db.close()
            # Return 0 to indicate success
            return 0
        
        # Query BEADS for ready work
        beads_ready = beads.get_ready_work(limit=50, priority=min_priority)
        
        if not beads_ready:
            result = {
                "ok": True,
                "ready_work": [],
                "message": "No ready work found in BEADS"
            }
            
            if output_format == 'json':
                print(json.dumps(result, indent=2))
            else:
                print("📭 No ready work found")
            
            db.close()
            # Return 0 to indicate success
            return 0
        
        # Map BEADS issues to Empirica goals
        for beads_issue in beads_ready:
            beads_id = beads_issue.get('id')
            
            # Find Empirica goal with this beads_issue_id
            cursor = db.conn.execute("""
                SELECT id, objective, scope, status
                FROM goals
                WHERE beads_issue_id = ? AND session_id = ?
            """, (beads_id, session_id))
            
            goal_row = cursor.fetchone()
            
            if not goal_row:
                # BEADS issue not linked to Empirica goal
                continue
            
            goal_id = goal_row[0]
            objective = goal_row[1]
            scope_json = goal_row[2]
            status = goal_row[3]
            
            # Parse scope
            scope = json.loads(scope_json) if scope_json else {}
            
            # Get epistemic state from latest CHECK or PREFLIGHT
            cursor = db.conn.execute("""
                SELECT phase, engagement, know, do, context, clarity, coherence, 
                       signal, density, state, change, completion, impact, uncertainty
                FROM reflexes
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (session_id,))
            
            reflex_row = cursor.fetchone()
            
            epistemic_ready = True
            last_confidence = None
            last_uncertainty = None
            why_not_ready = None
            
            if reflex_row:
                # Build vectors dict from individual columns
                vectors = {
                    'engagement': reflex_row[1],
                    'know': reflex_row[2],
                    'do': reflex_row[3],
                    'context': reflex_row[4],
                    'clarity': reflex_row[5],
                    'coherence': reflex_row[6],
                    'signal': reflex_row[7],
                    'density': reflex_row[8],
                    'state': reflex_row[9],
                    'change': reflex_row[10],
                    'completion': reflex_row[11],
                    'impact': reflex_row[12],
                    'uncertainty': reflex_row[13]
                }
                phase = reflex_row[0]
                
                # Extract epistemic state
                last_confidence = vectors.get('know', 0.5)
                last_uncertainty = vectors.get('uncertainty', 0.5)
                
                # Check epistemic readiness
                if last_confidence < min_confidence:
                    epistemic_ready = False
                    why_not_ready = f"Confidence too low ({last_confidence:.2f} < {min_confidence})"
                
                if last_uncertainty > max_uncertainty:
                    epistemic_ready = False
                    why_not_ready = f"Uncertainty too high ({last_uncertainty:.2f} > {max_uncertainty})"
            else:
                # No epistemic data available - assume not ready
                epistemic_ready = False
                why_not_ready = "No PREFLIGHT/CHECK data available"
            
            # Build ready work item
            ready_item = {
                "goal_id": goal_id,
                "beads_issue_id": beads_id,
                "objective": objective,
                "priority": beads_issue.get('priority', 2),
                "no_blockers": True,  # BEADS already filtered for this
                "epistemic_ready": epistemic_ready,
                "last_check_confidence": last_confidence,
                "preflight_uncertainty": last_uncertainty,
                "scope": scope,
                "status": status
            }
            
            if epistemic_ready:
                ready_item["why_ready"] = "High confidence, low uncertainty, no blockers"
            else:
                ready_item["why_not_ready"] = why_not_ready
            
            ready_work.append(ready_item)
        
        # Filter to only epistemically-ready items
        epistemically_ready_work = [item for item in ready_work if item["epistemic_ready"]]
        
        result = {
            "ok": True,
            "ready_work": epistemically_ready_work,
            "total_beads_ready": len(beads_ready),
            "total_mapped_to_goals": len(ready_work),
            "epistemically_ready_count": len(epistemically_ready_work),
            "filters": {
                "min_confidence": min_confidence,
                "max_uncertainty": max_uncertainty,
                "min_priority": min_priority
            }
        }
        
        # Format output
        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"📋 Ready Work (Dependency + Epistemic)")
            print(f"   BEADS ready: {len(beads_ready)}")
            print(f"   Mapped to goals: {len(ready_work)}")
            print(f"   Epistemically ready: {len(epistemically_ready_work)}")
            print()
            
            if epistemically_ready_work:
                for item in epistemically_ready_work:
                    print(f"✅ {item['beads_issue_id']}: {item['objective']}")
                    print(f"   Priority: {item['priority']}, Confidence: {item['last_check_confidence']:.2f}, Uncertainty: {item['preflight_uncertainty']:.2f}")
                    print(f"   Why ready: {item['why_ready']}")
                    print()
            else:
                print("📭 No epistemically-ready work found")
                print("   (Tasks may have BEADS blockers cleared but epistemic confidence too low)")
        
        db.close()
        print(json.dumps(result, indent=2))
        return 0
        
    except Exception as e:
        logger.error(f"goals-ready error: {e}", exc_info=True)
        result = {
            "ok": False,
            "error": str(e)
        }
        print(json.dumps(result, indent=2))
        return 1
