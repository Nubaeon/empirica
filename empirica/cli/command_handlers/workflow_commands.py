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
        import time
        import uuid
        from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
        from empirica.data.session_database import SessionDatabase

        # Parse arguments
        session_id = args.session_id
        vectors = parse_json_safely(args.vectors) if isinstance(args.vectors, str) else args.vectors
        reasoning = args.reasoning

        # Validate vectors
        if not isinstance(vectors, dict):
            raise ValueError("Vectors must be a dictionary")

        # Extract all numeric values from vectors (handle both simple and nested formats)
        extracted_vectors = _extract_all_vectors(vectors)
        vectors = extracted_vectors

        # Use GitEnhancedReflexLogger for proper 3-layer storage (SQLite + Git Notes + JSON)
        try:
            logger_instance = GitEnhancedReflexLogger(
                session_id=session_id,
                enable_git_notes=True  # Enable git notes for cross-AI features
            )

            # Add checkpoint - this writes to ALL 3 storage layers
            checkpoint_id = logger_instance.add_checkpoint(
                phase="PREFLIGHT",
                round_num=1,
                vectors=vectors,
                metadata={
                    "reasoning": reasoning,
                    "prompt": reasoning or "Preflight assessment"
                }
            )

            # JUST create CASCADE record for historical tracking (this remains)
            db = SessionDatabase()
            cascade_id = str(uuid.uuid4())
            now = time.time()

            # Create CASCADE record
            db.conn.execute("""
                INSERT INTO cascades
                (cascade_id, session_id, task, started_at)
                VALUES (?, ?, ?, ?)
            """, (cascade_id, session_id, "PREFLIGHT assessment", now))

            db.conn.commit()
            db.close()

            result = {
                "ok": True,
                "session_id": session_id,
                "checkpoint_id": checkpoint_id,
                "message": "PREFLIGHT assessment submitted to database and git notes",
                "vectors_submitted": len(vectors),
                "vectors_received": vectors,
                "reasoning": reasoning,
                "persisted": True,
                "storage_layers": {
                    "sqlite": True,
                    "git_notes": checkpoint_id is not None,
                    "json_logs": True
                }
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
            print(f"   Storage: Database + Git Notes")
            if reasoning:
                print(f"   Reasoning: {reasoning[:80]}...")

        return result

    except Exception as e:
        handle_cli_error(e, "Preflight submit", getattr(args, 'verbose', False))


def handle_check_command(args):
    """Handle check command - creates unified storage assessment with real vectors"""
    try:
        import time
        import uuid
        from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
        from empirica.cli.command_handlers.decision_utils import calculate_decision

        # Parse arguments
        session_id = args.session_id
        findings = parse_json_safely(args.findings) if isinstance(args.findings, str) else args.findings
        unknowns = parse_json_safely(args.unknowns) if isinstance(args.unknowns, str) else args.unknowns
        confidence = args.confidence
        cycle = getattr(args, 'cycle', 1)
        verbose = getattr(args, 'verbose', False)

        # Auto-convert strings to single-item arrays for better UX
        if isinstance(findings, str):
            findings = [findings]
        if isinstance(unknowns, str):
            unknowns = [unknowns]

        # Validate inputs
        if not isinstance(findings, list):
            raise ValueError("Findings must be a list")
        if not isinstance(unknowns, list):
            raise ValueError("Unknowns must be a list")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

        # Extract actual vectors from args or infer from confidence
        if hasattr(args, 'vectors') and args.vectors:
            vectors = parse_json_safely(args.vectors) if isinstance(args.vectors, str) else args.vectors
        else:
            # If no vectors provided, infer from confidence
            uncertainty = 1.0 - confidence
            vectors = {
                'engagement': 0.75,
                'know': confidence,
                'do': confidence,
                'context': confidence * 0.9,
                'clarity': confidence * 0.95,
                'coherence': confidence * 0.92,
                'signal': confidence * 0.88,
                'density': confidence * 0.85,
                'state': confidence,
                'change': confidence * 0.80,
                'completion': confidence * 0.70,
                'impact': confidence * 0.75,
                'uncertainty': uncertainty
            }

        # Use unified storage via GitEnhancedReflexLogger
        logger_instance = GitEnhancedReflexLogger(
            session_id=session_id,
            enable_git_notes=True
        )

        decision = calculate_decision(confidence)

        checkpoint_id = logger_instance.add_checkpoint(
            phase="CHECK",
            round_num=cycle,
            vectors=vectors,
            metadata={
                "findings": findings,
                "unknowns": unknowns,
                "findings_count": len(findings),
                "unknowns_count": len(unknowns),
                "confidence": confidence,
                "decision": decision
            }
        )

        result = {
            "ok": True,
            "session_id": session_id,
            "checkpoint_id": checkpoint_id,
            "findings_count": len(findings),
            "unknowns_count": len(unknowns),
            "confidence": confidence,
            "decision": decision,
            "cycle": cycle,
            "timestamp": time.time()
        }

        # Add findings and unknowns to result
        if verbose:
            result["findings"] = findings
            result["unknowns"] = unknowns

        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print("✅ CHECK assessment created and stored")
            print(f"   Session: {session_id[:8]}...")
            print(f"   Cycle: {cycle}")
            print(f"   Confidence: {confidence:.2f}")
            print(f"   Decision: {decision.upper()}")
            print(f"   Storage: SQLite + Git Notes + JSON")
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
        from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
        
        # Parse arguments
        session_id = args.session_id
        vectors = parse_json_safely(args.vectors) if isinstance(args.vectors, str) else args.vectors
        decision = args.decision
        reasoning = args.reasoning
        cycle = getattr(args, 'cycle', None) or 1  # Handle None case
        
        # Validate inputs
        if not isinstance(vectors, dict):
            raise ValueError("Vectors must be a dictionary")
        
        # Use GitEnhancedReflexLogger for proper 3-layer storage (SQLite + Git Notes + JSON)
        try:
            logger_instance = GitEnhancedReflexLogger(
                session_id=session_id,
                enable_git_notes=True  # Enable git notes for cross-AI features
            )
            
            # Calculate confidence from uncertainty (inverse relationship)
            uncertainty = vectors.get('uncertainty', 0.5)
            confidence = 1.0 - uncertainty
            
            # Extract gaps (areas with low scores)
            gaps = []
            for key, value in vectors.items():
                if isinstance(value, (int, float)) and value < 0.5:
                    gaps.append(f"{key}: {value:.2f}")
            
            # Add checkpoint - this writes to ALL 3 storage layers
            checkpoint_id = logger_instance.add_checkpoint(
                phase="CHECK",
                round_num=cycle,
                vectors=vectors,
                metadata={
                    "decision": decision,
                    "reasoning": reasoning,
                    "confidence": confidence,
                    "gaps": gaps,
                    "cycle": cycle
                }
            )

            # AUTO-CHECKPOINT: Create git checkpoint if uncertainty > 0.5 (risky decision)
            # This preserves context if AI needs to investigate further
            auto_checkpoint_created = False
            if uncertainty > 0.5:
                try:
                    import subprocess
                    subprocess.run(
                        [
                            "empirica", "checkpoint-create",
                            "--session-id", session_id,
                            "--phase", "CHECK",
                            "--round", str(cycle),
                            "--metadata", json.dumps({
                                "auto_checkpoint": True,
                                "reason": "risky_decision",
                                "uncertainty": uncertainty,
                                "decision": decision,
                                "gaps": gaps
                            })
                        ],
                        capture_output=True,
                        timeout=10
                    )
                    auto_checkpoint_created = True
                except Exception as e:
                    # Auto-checkpoint failure is not fatal, but log it
                    logger.warning(f"Auto-checkpoint after CHECK (uncertainty > 0.5) failed (non-fatal): {e}")

            result = {
                "ok": True,
                "session_id": session_id,
                "checkpoint_id": checkpoint_id,
                "decision": decision,
                "cycle": cycle,
                "vectors_count": len(vectors),
                "reasoning": reasoning,
                "auto_checkpoint_created": auto_checkpoint_created,
                "persisted": True,
                "storage_layers": {
                    "sqlite": True,
                    "git_notes": checkpoint_id is not None,
                    "json_logs": True
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to save check assessment: {e}")
            result = {
                "ok": False,
                "session_id": session_id,
                "message": f"Failed to save CHECK assessment: {str(e)}",
                "persisted": False,
                "error": str(e)
            }
        
        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print("✅ CHECK assessment submitted successfully")
            print(f"   Session: {session_id[:8]}...")
            print(f"   Decision: {decision.upper()}")
            print(f"   Cycle: {cycle}")
            print(f"   Vectors: {len(vectors)} submitted")
            print(f"   Storage: SQLite + Git Notes + JSON")
            if reasoning:
                print(f"   Reasoning: {reasoning[:80]}...")
        
        return result
        
    except Exception as e:
        handle_cli_error(e, "Check submit", getattr(args, 'verbose', False))


def _extract_numeric_value(value):
    """
    Extract numeric value from vector data.

    Handles two formats:
    - Simple float: 0.85
    - Nested dict: {"score": 0.85, "rationale": "...", "evidence": "..."}

    Returns:
        float or None if value cannot be extracted
    """
    if isinstance(value, (int, float)):
        return float(value)
    elif isinstance(value, dict):
        # Extract 'score' key if present
        if 'score' in value:
            return float(value['score'])
        # Fallback: try to get any numeric value
        for k, v in value.items():
            if isinstance(v, (int, float)):
                return float(v)
    return None



def _extract_numeric_value(value):
    """
    Extract numeric value from vector data.

    Handles multiple formats:
    - Simple float: 0.85
    - Nested dict: {"score": 0.85, "rationale": "...", "evidence": "..."}
    - String numbers: "0.85"

    Returns:
        float or None if value cannot be extracted
    """
    if isinstance(value, (int, float)):
        return float(value)
    elif isinstance(value, dict):
        # Extract 'score' key if present
        if 'score' in value:
            return float(value['score'])
        # Extract 'value' key as fallback
        if 'value' in value:
            return float(value['value'])
        # Try to find any numeric value in nested structure
        for k, v in value.items():
            if isinstance(v, (int, float)):
                return float(v)
            elif isinstance(v, str) and v.replace('.', '').replace('-', '').isdigit():
                try:
                    return float(v)
                except ValueError:
                    continue
        # Try to convert entire dict to float if it looks like a single number
        for v in value.values():
            if isinstance(v, (int, float)):
                return float(v)
    elif isinstance(value, str):
        # Try to convert string to float
        try:
            return float(value)
        except ValueError:
            pass
    return None


def _extract_all_vectors(vectors):
    """
    Extract all numeric values from vectors dict, handling nested structures.
    
    Args:
        vectors: Dict containing vector data (simple or nested)
    
    Returns:
        Dict with all vector names mapped to numeric values
    """
    extracted = {}
    
    for key, value in vectors.items():
        numeric_value = _extract_numeric_value(value)
        if numeric_value is not None:
            extracted[key] = numeric_value
        else:
            # Fallback to default if extraction fails
            extracted[key] = 0.5
    
    return extracted

def handle_postflight_submit_command(args):
    """Handle postflight-submit command"""
    try:
        import time
        import uuid
        from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
        from empirica.data.session_database import SessionDatabase

        # Parse arguments
        session_id = args.session_id
        vectors = parse_json_safely(args.vectors) if isinstance(args.vectors, str) else args.vectors
        reasoning = args.reasoning  # Unified parameter name

        # Validate vectors
        if not isinstance(vectors, dict):
            raise ValueError("Vectors must be a dictionary")

        # Extract all numeric values from vectors (handle both simple and nested formats)
        extracted_vectors = _extract_all_vectors(vectors)
        vectors = extracted_vectors

        # Use GitEnhancedReflexLogger for proper 3-layer storage (SQLite + Git Notes + JSON)
        try:
            logger_instance = GitEnhancedReflexLogger(
                session_id=session_id,
                enable_git_notes=True  # Enable git notes for cross-AI features
            )

            # Calculate postflight confidence (inverse of uncertainty)
            uncertainty = vectors.get('uncertainty', 0.5)
            postflight_confidence = 1.0 - uncertainty

            # Determine calibration accuracy
            completion = vectors.get('completion', 0.5)
            if abs(completion - postflight_confidence) < 0.2:
                calibration_accuracy = "good"
            elif abs(completion - postflight_confidence) < 0.4:
                calibration_accuracy = "moderate"
            else:
                calibration_accuracy = "poor"

            # Try to calculate deltas from previous checkpoint
            deltas = {}
            try:
                # Get preflight checkpoint from git notes for delta calculation
                preflight_checkpoint = logger_instance.get_last_checkpoint(phase="PREFLIGHT")
                if preflight_checkpoint and 'vectors' in preflight_checkpoint:
                    preflight_vectors = preflight_checkpoint['vectors']

                    for key in vectors:
                        if key in preflight_vectors:
                            pre_val = preflight_vectors.get(key, 0.5)
                            post_val = vectors.get(key, 0.5)
                            deltas[key] = round(post_val - pre_val, 3)
            except Exception as e:
                logger.debug(f"Delta calculation failed: {e}")
                # Delta calculation is optional

            # Add checkpoint - this writes to ALL 3 storage layers atomically
            checkpoint_id = logger_instance.add_checkpoint(
                phase="POSTFLIGHT",
                round_num=1,
                vectors=vectors,
                metadata={
                    "reasoning": reasoning,
                    "task_summary": reasoning or "Task completed",
                    "postflight_confidence": postflight_confidence,
                    "calibration_accuracy": calibration_accuracy,
                    "deltas": deltas
                }
            )

            # AUTO-CHECKPOINT: Create git checkpoint after POSTFLIGHT (wired in, not optional)
            # This ensures learning is always preserved for next AI session
            try:
                import subprocess
                subprocess.run(
                    [
                        "empirica", "checkpoint-create",
                        "--session-id", session_id,
                        "--phase", "POSTFLIGHT",
                        "--metadata", json.dumps({
                            "auto_checkpoint": True,
                            "learning_delta": deltas,
                            "calibration": calibration_accuracy
                        })
                    ],
                    capture_output=True,
                    timeout=10
                )
            except Exception as e:
                # Auto-checkpoint failure is not fatal, but log it
                logger.warning(f"Auto-checkpoint after POSTFLIGHT failed (non-fatal): {e}")

            result = {
                "ok": True,
                "session_id": session_id,
                "checkpoint_id": checkpoint_id,
                "message": "POSTFLIGHT assessment submitted to database and git notes",
                "vectors_submitted": len(vectors),
                "reasoning": reasoning,
                "postflight_confidence": postflight_confidence,
                "calibration_accuracy": calibration_accuracy,
                "deltas": deltas,
                "auto_checkpoint_created": True,
                "persisted": True,
                "storage_layers": {
                    "sqlite": True,
                    "git_notes": checkpoint_id is not None,
                    "json_logs": True
                }
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

        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print("✅ POSTFLIGHT assessment submitted successfully")
            print(f"   Session: {session_id[:8]}...")
            print(f"   Vectors: {len(vectors)} submitted")
            print(f"   Storage: Database + Git Notes")
            print(f"   Calibration: {calibration_accuracy}")
            if reasoning:
                print(f"   Reasoning: {reasoning[:80]}...")
            if deltas:
                print(f"   Learning deltas: {len(deltas)} vectors changed")

            # Show project context for next session
            try:
                db = SessionDatabase()
                # Get session and project info
                cursor = db.conn.cursor()
                cursor.execute("""
                    SELECT project_id FROM sessions WHERE session_id = ?
                """, (session_id,))
                row = cursor.fetchone()
                if row and row['project_id']:
                    project_id = row['project_id']
                    breadcrumbs = db.bootstrap_project_breadcrumbs(project_id, mode="session_start")
                    db.close()

                    if "error" not in breadcrumbs:
                        print(f"\n📚 Project Context (for next session):")
                        if breadcrumbs.get('findings'):
                            print(f"   Recent findings recorded: {len(breadcrumbs['findings'])}")
                        if breadcrumbs.get('unknowns'):
                            unresolved = [u for u in breadcrumbs['unknowns'] if not u['is_resolved']]
                            if unresolved:
                                print(f"   Unresolved unknowns: {len(unresolved)}")
                        if breadcrumbs.get('available_skills'):
                            print(f"   Available skills: {len(breadcrumbs['available_skills'])}")
                else:
                    db.close()
            except Exception:
                pass

        return result

    except Exception as e:
        handle_cli_error(e, "Postflight submit", getattr(args, 'verbose', False))
