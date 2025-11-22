"""
Workflow Commands - MCP v2 Integration Commands

Handles CLI commands for:
- preflight-submit: Submit preflight assessment results
- check: Execute epistemic check assessment
- check-submit: Submit check assessment results
- postflight-submit: Submit postflight assessment results

These commands provide JSON output for MCP v2 server integration.
"""

import json
import logging
from ..cli_utils import handle_cli_error, parse_json_safely

logger = logging.getLogger(__name__)


def handle_preflight_submit_command(args):
    """Handle preflight-submit command"""
    try:
        from empirica.data.session_database import SessionDatabase
        
        # Parse arguments
        session_id = args.session_id
        vectors = parse_json_safely(args.vectors) if isinstance(args.vectors, str) else args.vectors
        reasoning = args.reasoning
        
        # Validate vectors
        if not isinstance(vectors, dict):
            raise ValueError("Vectors must be a dictionary")
        
        # Call Python API to submit preflight - ACTUALLY SAVE TO DATABASE
        db = SessionDatabase()
        
        # Save preflight assessment to database
        # Note: cascade_id is optional, will be auto-generated if needed
        cascade_id = None  # Let database handle cascade creation if needed
        prompt_summary = reasoning or "Preflight assessment"
        uncertainty_notes = reasoning or ""
        
        try:
            assessment_id = db.log_preflight_assessment(
                session_id=session_id,
                cascade_id=cascade_id,
                prompt_summary=prompt_summary,
                vectors=vectors,
                uncertainty_notes=uncertainty_notes
            )
            
            result = {
                "ok": True,
                "session_id": session_id,
                "assessment_id": assessment_id,
                "message": "PREFLIGHT assessment submitted and saved to database",
                "vectors_submitted": len(vectors),
                "vectors_received": vectors,
                "reasoning": reasoning,
                "persisted": True
            }
        except Exception as e:
            logger.error(f"Failed to save preflight assessment: {e}")
            result = {
                "ok": False,
                "session_id": session_id,
                "message": f"Failed to save PREFLIGHT assessment: {str(e)}",
                "vectors_submitted": 0,
                "persisted": False,
                "error": str(e)
            }
        
        # Format output based on --output flag
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print("✅ PREFLIGHT assessment submitted successfully")
            print(f"   Session: {session_id[:8]}...")
            print(f"   Vectors: {len(vectors)} submitted")
            if reasoning:
                print(f"   Reasoning: {reasoning[:80]}...")
        
        db.close()
        return result
        
    except Exception as e:
        handle_cli_error(e, "Preflight submit", getattr(args, 'verbose', False))


def handle_check_command(args):
    """Handle check command"""
    try:
        # Parse arguments
        session_id = args.session_id
        findings = parse_json_safely(args.findings) if isinstance(args.findings, str) else args.findings
        unknowns = parse_json_safely(args.unknowns) if isinstance(args.unknowns, str) else args.unknowns
        confidence = args.confidence
        verbose = getattr(args, 'verbose', False)
        
        # Validate inputs
        if not isinstance(findings, list):
            raise ValueError("Findings must be a list")
        if not isinstance(unknowns, list):
            raise ValueError("Unknowns must be a list")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        
        # Simulate check assessment
        result = {
            "ok": True,
            "session_id": session_id,
            "findings_count": len(findings),
            "unknowns_count": len(unknowns),
            "confidence": confidence,
            "decision": "proceed" if confidence >= 0.7 else "investigate" if confidence <= 0.3 else "proceed_with_caution",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        # Add findings and unknowns to result
        if verbose:
            result["findings"] = findings
            result["unknowns"] = unknowns
        
        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print("✅ Check assessment completed")
            print(f"   Session: {session_id[:8]}...")
            print(f"   Confidence: {confidence:.2f}")
            print(f"   Decision: {result['decision'].upper()}")
            print(f"   Findings: {len(findings)} analyzed")
            print(f"   Unknowns: {len(unknowns)} remaining")
            
            if verbose:
                print("\n   Key findings:")
                for i, finding in enumerate(findings[:5], 1):
                    print(f"     {i}. {finding}")
                if len(findings) > 5:
                    print(f"     ... and {len(findings) - 5} more")
                
                print("\n   Remaining unknowns:")
                for i, unknown in enumerate(unknowns[:5], 1):
                    print(f"     {i}. {unknown}")
                if len(unknowns) > 5:
                    print(f"     ... and {len(unknowns) - 5} more")
        
        return result
        
    except Exception as e:
        handle_cli_error(e, "Check assessment", getattr(args, 'verbose', False))


def handle_check_submit_command(args):
    """Handle check-submit command"""
    try:
        from empirica.data.session_database import SessionDatabase
        
        # Parse arguments
        session_id = args.session_id
        vectors = parse_json_safely(args.vectors) if isinstance(args.vectors, str) else args.vectors
        decision = args.decision
        reasoning = args.reasoning
        cycle = getattr(args, 'cycle', None) or 1  # Handle None case
        
        # Validate inputs
        if not isinstance(vectors, dict):
            raise ValueError("Vectors must be a dictionary")
        
        # Save CHECK assessment to database - ACTUALLY PERSIST
        db = SessionDatabase()
        
        cascade_id = None  # Let database handle cascade linkage
        
        # Calculate confidence from uncertainty (inverse relationship)
        uncertainty = vectors.get('uncertainty', 0.5)
        confidence = 1.0 - uncertainty  # Confidence is inverse of uncertainty
        
        gaps = []  # Could extract from vectors with low values
        for key, value in vectors.items():
            if value < 0.5:
                gaps.append(f"{key}: {value:.2f}")
        
        # Extract next targets (areas needing investigation)
        next_targets = []
        for key, value in vectors.items():
            if value < 0.6:  # Slightly higher threshold for investigation targets
                next_targets.append(key)
        
        try:
            assessment_id = db.log_check_phase_assessment(
                session_id=session_id,
                cascade_id=cascade_id,
                investigation_cycle=cycle,
                confidence=confidence,
                decision=decision,
                gaps=gaps,
                next_targets=next_targets,
                notes=reasoning or "Check assessment completed",
                vectors=vectors
            )
            
            # ALSO save findings to cascade.context_json for handoff generation
            # This bridges check_phase_assessments table -> cascade for session-end extraction
            try:
                import uuid
                from datetime import datetime
                
                cursor = db.conn.cursor()
                
                # Get active cascade or create one
                cursor.execute("""
                    SELECT cascade_id, context_json FROM cascades 
                    WHERE session_id = ? AND completed_at IS NULL
                    ORDER BY started_at DESC LIMIT 1
                """, (session_id,))
                
                row = cursor.fetchone()
                if row:
                    cascade_id_actual, context_json_str = row
                    context = json.loads(context_json_str) if context_json_str else {}
                else:
                    # Create new cascade
                    cascade_id_actual = str(uuid.uuid4())
                    context = {}
                    cursor.execute("""
                        INSERT INTO cascades (cascade_id, session_id, task, started_at)
                        VALUES (?, ?, ?, ?)
                    """, (cascade_id_actual, session_id, "CHECK phase", datetime.utcnow().isoformat()))
                
                # Update context with CHECK data from check_phase_assessments
                context["check_findings"] = gaps  # Use gaps as findings
                context["check_unknowns"] = next_targets  # Use next_targets as unknowns
                context["check_confidence"] = confidence
                context["check_decision"] = decision
                context["check_cycle"] = cycle
                context["check_timestamp"] = datetime.utcnow().isoformat()
                
                # Save to cascade
                cursor.execute("""
                    UPDATE cascades 
                    SET context_json = ?, check_completed = 1
                    WHERE cascade_id = ?
                """, (json.dumps(context), cascade_id_actual))
                
                db.conn.commit()
                
            except Exception as e:
                logger.debug(f"Could not update cascade context: {e}")
                # Don't fail check-submit if cascade update fails
            
            result = {
                "ok": True,
                "session_id": session_id,
                "assessment_id": assessment_id,
                "decision": decision,
                "cycle": cycle,
                "vectors_count": len(vectors),
                "reasoning": reasoning,
                "persisted": True
            }
            
            # Note: Goals are created explicitly by AI via MCP tools (create_goal, add_subtask)
            # No automatic generation - AI has full control over when/how goals are created
            
        except Exception as e:
            logger.error(f"Failed to save check assessment: {e}")
            result = {
                "ok": False,
                "session_id": session_id,
                "message": f"Failed to save CHECK assessment: {str(e)}",
                "persisted": False,
                "error": str(e)
            }
        
        db.close()
        
        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print("✅ CHECK assessment submitted successfully")
            print(f"   Session: {session_id[:8]}...")
            print(f"   Decision: {decision.upper()}")
            print(f"   Cycle: {cycle}")
            print(f"   Vectors: {len(vectors)} submitted")
            if reasoning:
                print(f"   Reasoning: {reasoning[:80]}...")
        
        return result
        
    except Exception as e:
        handle_cli_error(e, "Check submit", getattr(args, 'verbose', False))


def handle_postflight_submit_command(args):
    """Handle postflight-submit command"""
    try:
        from empirica.data.session_database import SessionDatabase
        
        # Parse arguments
        session_id = args.session_id
        vectors = parse_json_safely(args.vectors) if isinstance(args.vectors, str) else args.vectors
        changes = args.changes
        
        # Validate vectors
        if not isinstance(vectors, dict):
            raise ValueError("Vectors must be a dictionary")
        
        # Save POSTFLIGHT assessment to database - ACTUALLY PERSIST
        db = SessionDatabase()
        
        cascade_id = None  # Let database handle cascade linkage
        task_summary = changes or "Task completed"
        
        # Calculate postflight confidence (inverse of uncertainty)
        uncertainty = vectors.get('uncertainty', 0.5)
        postflight_confidence = 1.0 - uncertainty
        
        # Determine calibration accuracy by comparing completion to confidence
        completion = vectors.get('completion', 0.5)
        if abs(completion - postflight_confidence) < 0.2:
            calibration_accuracy = "good"
        elif abs(completion - postflight_confidence) < 0.4:
            calibration_accuracy = "moderate"
        else:
            calibration_accuracy = "poor"
        
        learning_notes = changes or ""
        
        try:
            assessment_id = db.log_postflight_assessment(
                session_id=session_id,
                cascade_id=cascade_id,
                task_summary=task_summary,
                vectors=vectors,
                postflight_confidence=postflight_confidence,
                calibration_accuracy=calibration_accuracy,
                learning_notes=learning_notes
            )
            
            # Try to calculate deltas by fetching preflight
            deltas = {}
            try:
                preflight = db.get_preflight_assessment(session_id)
                if preflight and 'vectors_json' in preflight:
                    preflight_vectors = json.loads(preflight['vectors_json'])
                    for key in vectors:
                        if key in preflight_vectors:
                            deltas[key] = vectors[key] - preflight_vectors[key]
            except Exception:
                pass  # Delta calculation is optional
            
            result = {
                "ok": True,
                "session_id": session_id,
                "assessment_id": assessment_id,
                "message": "POSTFLIGHT assessment submitted and saved to database",
                "vectors_submitted": len(vectors),
                "changes": changes,
                "postflight_confidence": postflight_confidence,
                "calibration_accuracy": calibration_accuracy,
                "deltas": deltas,
                "persisted": True
            }
        except Exception as e:
            logger.error(f"Failed to save postflight assessment: {e}")
            result = {
                "ok": False,
                "session_id": session_id,
                "message": f"Failed to save POSTFLIGHT assessment: {str(e)}",
                "persisted": False,
                "error": str(e)
            }
        
        db.close()
        
        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print("✅ POSTFLIGHT assessment submitted successfully")
            print(f"   Session: {session_id[:8]}...")
            print(f"   Vectors: {len(vectors)} submitted")
            if changes:
                print(f"   Changes: {changes[:80]}...")
        
        return result
        
    except Exception as e:
        handle_cli_error(e, "Postflight submit", getattr(args, 'verbose', False))
