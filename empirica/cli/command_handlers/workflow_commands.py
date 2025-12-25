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
    """Handle preflight-submit command - AI-first with config file support"""
    try:
        import time
        import uuid
        import sys
        import os
        from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
        from empirica.data.session_database import SessionDatabase

        # AI-FIRST MODE: Check if config file provided as positional argument
        config_data = None
        if hasattr(args, 'config') and args.config:
            # Read config from file or stdin
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
            # AI-FIRST MODE: Use config file
            session_id = config_data.get('session_id')
            vectors = config_data.get('vectors')
            reasoning = config_data.get('reasoning', '')
            output_format = 'json'  # AI-first always uses JSON output

            # Validate required fields
            if not session_id or not vectors:
                print(json.dumps({
                    "ok": False,
                    "error": "Config file must include 'session_id' and 'vectors' fields",
                    "hint": "See /tmp/preflight_config_example.json for schema"
                }))
                sys.exit(1)
        else:
            # LEGACY MODE: Use CLI flags
            session_id = args.session_id
            vectors = parse_json_safely(args.vectors) if isinstance(args.vectors, str) else args.vectors
            reasoning = args.reasoning
            output_format = getattr(args, 'output', 'json')  # Default to JSON

            # Validate required fields for legacy mode
            if not session_id or not vectors:
                print(json.dumps({
                    "ok": False,
                    "error": "Legacy mode requires --session-id and --vectors flags",
                    "hint": "For AI-first mode, use: empirica preflight-submit config.json"
                }))
                sys.exit(1)

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
                    "git_notes": checkpoint_id is not None and checkpoint_id != "",
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

        # Format output (AI-first = JSON by default)
        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            # Human-readable output (legacy)
            if result['ok']:
                print("✅ PREFLIGHT assessment submitted successfully")
                print(f"   Session: {session_id[:8]}...")
                print(f"   Vectors: {len(vectors)} submitted")
                print(f"   Storage: Database + Git Notes")
                if reasoning:
                    print(f"   Reasoning: {reasoning[:80]}...")
            else:
                print(f"❌ {result.get('message', 'Failed to submit PREFLIGHT assessment')}")

        return result

    except Exception as e:
        handle_cli_error(e, "Preflight submit", getattr(args, 'verbose', False))


def handle_check_command(args):
    """Handle check command - AI-first with config file support"""
    try:
        import time
        import uuid
        import sys
        import os
        from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
        from empirica.cli.command_handlers.decision_utils import calculate_decision

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
            findings = config_data.get('findings', [])
            unknowns = config_data.get('unknowns', [])
            confidence = config_data.get('confidence')
            cycle = config_data.get('cycle', 1)
            verbose = config_data.get('verbose', False)
            output_format = 'json'

            # Validate required fields
            if not session_id or confidence is None:
                print(json.dumps({
                    "ok": False,
                    "error": "Config file must include 'session_id' and 'confidence' fields",
                    "hint": "See /tmp/check_config_example.json for schema"
                }))
                sys.exit(1)
        else:
            # LEGACY MODE
            session_id = args.session_id
            findings = parse_json_safely(args.findings) if isinstance(args.findings, str) else args.findings
            unknowns = parse_json_safely(args.unknowns) if isinstance(args.unknowns, str) else args.unknowns
            confidence = args.confidence
            cycle = getattr(args, 'cycle', 1)
            verbose = getattr(args, 'verbose', False)
            output_format = getattr(args, 'output', 'json')

            # Validate required fields for legacy mode
            if not session_id or confidence is None:
                print(json.dumps({
                    "ok": False,
                    "error": "Legacy mode requires --session-id and --confidence flags",
                    "hint": "For AI-first mode, use: empirica check config.json"
                }))
                sys.exit(1)

        # Auto-convert strings to single-item arrays for better UX (defensive parsing)
        if isinstance(findings, str):
            findings = [findings]
        elif not isinstance(findings, list):
            # If parse_json_safely returned None or invalid type, wrap in list
            findings = [str(findings)] if findings else []
        
        if isinstance(unknowns, str):
            unknowns = [unknowns]
        elif not isinstance(unknowns, list):
            # If parse_json_safely returned None or invalid type, wrap in list
            unknowns = [str(unknowns)] if unknowns else []

        # Validate inputs (now more defensive)
        if not isinstance(findings, list):
            raise ValueError(f"Findings must be a list, got {type(findings)}")
        if not isinstance(unknowns, list):
            raise ValueError(f"Unknowns must be a list, got {type(unknowns)}")
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

        # Format output (AI-first = JSON by default)
        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            # Human-readable output (legacy)
            if result['ok']:
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
            else:
                print(f"❌ {result.get('message', 'Failed to create CHECK assessment')}")

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
                    "git_notes": checkpoint_id is not None and checkpoint_id != "",
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
    Flattens nested dicts to extract individual vector values.
    
    Args:
        vectors: Dict containing vector data (simple or nested)
    
    Returns:
        Dict with all vector names mapped to numeric values
    
    Example:
        Input: {"engagement": 0.85, "foundation": {"know": 0.75, "do": 0.80}}
        Output: {"engagement": 0.85, "know": 0.75, "do": 0.80}
    """
    extracted = {}
    
    for key, value in vectors.items():
        if isinstance(value, dict):
            # Nested structure - recursively extract all sub-vectors
            for nested_key, nested_value in value.items():
                numeric_value = _extract_numeric_value(nested_value)
                if numeric_value is not None:
                    extracted[nested_key] = numeric_value
                else:
                    # Fallback to default if extraction fails
                    extracted[nested_key] = 0.5
        else:
            # Simple value - extract directly
            numeric_value = _extract_numeric_value(value)
            if numeric_value is not None:
                extracted[key] = numeric_value
            else:
                # Fallback to default if extraction fails
                extracted[key] = 0.5
    
    return extracted

def handle_postflight_submit_command(args):
    """Handle postflight-submit command - AI-first with config file support"""
    try:
        import time
        import uuid
        import sys
        import os
        from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
        from empirica.data.session_database import SessionDatabase

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
            vectors = config_data.get('vectors')
            reasoning = config_data.get('reasoning', '')
            output_format = 'json'

            # Validate required fields
            if not session_id or not vectors:
                print(json.dumps({
                    "ok": False,
                    "error": "Config file must include 'session_id' and 'vectors' fields",
                    "hint": "See /tmp/postflight_config_example.json for schema"
                }))
                sys.exit(1)
        else:
            # LEGACY MODE
            session_id = args.session_id
            vectors = parse_json_safely(args.vectors) if isinstance(args.vectors, str) else args.vectors
            reasoning = args.reasoning
            output_format = getattr(args, 'output', 'json')

            # Validate required fields for legacy mode
            if not session_id or not vectors:
                print(json.dumps({
                    "ok": False,
                    "error": "Legacy mode requires --session-id and --vectors flags",
                    "hint": "For AI-first mode, use: empirica postflight-submit config.json"
                }))
                sys.exit(1)

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

            # PURE POSTFLIGHT: Calculate deltas from previous checkpoint (system-driven)
            # AI assesses CURRENT state only, system calculates growth independently
            deltas = {}
            calibration_issues = []
            
            try:
                # Get preflight checkpoint from git notes or SQLite for delta calculation
                preflight_checkpoint = logger_instance.get_last_checkpoint(phase="PREFLIGHT")
                
                # Fallback: Query SQLite reflexes table directly if git notes unavailable
                if not preflight_checkpoint:
                    db = SessionDatabase()
                    cursor = db.conn.cursor()
                    cursor.execute("""
                        SELECT engagement, know, do, context, clarity, coherence, signal, density,
                               state, change, completion, impact, uncertainty
                        FROM reflexes
                        WHERE session_id = ? AND phase = 'PREFLIGHT'
                        ORDER BY timestamp DESC LIMIT 1
                    """, (session_id,))
                    preflight_row = cursor.fetchone()
                    db.close()
                    
                    if preflight_row:
                        vector_names = ["engagement", "know", "do", "context", "clarity", "coherence", 
                                       "signal", "density", "state", "change", "completion", "impact", "uncertainty"]
                        preflight_vectors = {name: preflight_row[i] for i, name in enumerate(vector_names)}
                    else:
                        preflight_vectors = None
                elif 'vectors' in preflight_checkpoint:
                    preflight_vectors = preflight_checkpoint['vectors']
                else:
                    preflight_vectors = None
                
                if preflight_vectors:

                    # Calculate deltas (system calculates growth, not AI's claimed growth)
                    for key in vectors:
                        if key in preflight_vectors:
                            pre_val = preflight_vectors.get(key, 0.5)
                            post_val = vectors.get(key, 0.5)
                            delta = post_val - pre_val
                            deltas[key] = round(delta, 3)
                            
                            # Note: Within-session vector decreases removed
                            # (PREFLIGHT→POSTFLIGHT decreases are calibration corrections, not memory gaps)
                            # True memory gap detection requires cross-session comparison:
                            # Previous session POSTFLIGHT → Current session PREFLIGHT
                            # This requires forced session restart before context fills and using
                            # handoff-query/project-bootstrap to measure retention
                            
                            # CALIBRATION ISSUE DETECTION: Identify mismatches
                            # If KNOW increased but DO decreased, might indicate learning without practice
                            if key == "know" and delta > 0.2:
                                do_delta = deltas.get("do", 0)
                                if do_delta < -0.1:
                                    calibration_issues.append({
                                        "pattern": "know_up_do_down",
                                        "description": "Knowledge increased but capability decreased - possible theoretical learning without application"
                                    })
                            
                            # If completion high but uncertainty also high, misalignment
                            if key == "completion" and post_val > 0.8:
                                uncertainty_post = vectors.get("uncertainty", 0.5)
                                if uncertainty_post > 0.5:
                                    calibration_issues.append({
                                        "pattern": "completion_high_uncertainty_high",
                                        "description": "High completion with high uncertainty - possible overconfidence or incomplete self-assessment"
                                    })
                else:
                    logger.warning("No PREFLIGHT checkpoint found - cannot calculate deltas or detect memory gaps")
                    
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
                    "deltas": deltas,
                    "calibration_issues": calibration_issues
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

            # EPISTEMIC TRAJECTORY STORAGE: Store learning deltas to Qdrant (if available)
            trajectory_stored = False
            try:
                db = SessionDatabase()
                session = db.get_session(session_id)
                if session and session.get('project_id'):
                    from empirica.core.epistemic_trajectory import store_trajectory
                    trajectory_stored = store_trajectory(session['project_id'], session_id, db)
                    if trajectory_stored:
                        logger.debug(f"Stored epistemic trajectory to Qdrant for session {session_id}")
            except Exception as e:
                # Trajectory storage is optional (requires Qdrant)
                logger.debug(f"Epistemic trajectory storage skipped: {e}")

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
                "calibration_issues_detected": len(calibration_issues),
                "calibration_issues": calibration_issues if calibration_issues else None,
                "auto_checkpoint_created": True,
                "persisted": True,
                "storage_layers": {
                    "sqlite": True,
                    "git_notes": checkpoint_id is not None and checkpoint_id != "",
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

        # Format output (AI-first = JSON by default)
        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            # Human-readable output (legacy)
            if result['ok']:
                print("✅ POSTFLIGHT assessment submitted successfully")
                print(f"   Session: {session_id[:8]}...")
                print(f"   Vectors: {len(vectors)} submitted")
                print(f"   Storage: Database + Git Notes")
                print(f"   Calibration: {calibration_accuracy}")
                if reasoning:
                    print(f"   Reasoning: {reasoning[:80]}...")
                if deltas:
                    print(f"   Learning deltas: {len(deltas)} vectors changed")

                # CALIBRATION ISSUE WARNINGS
                if calibration_issues:
                    print(f"\n⚠️  Calibration issues detected: {len(calibration_issues)}")
                    for issue in calibration_issues:
                        print(f"   • {issue['pattern']}: {issue['description']}")
            else:
                print(f"❌ {result.get('message', 'Failed to submit POSTFLIGHT assessment')}")

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

                    # Show documentation requirements
                    try:
                        from empirica.core.docs.doc_planner import compute_doc_plan
                        doc_plan = compute_doc_plan(project_id, session_id=session_id)
                        if doc_plan and doc_plan.get('suggested_updates'):
                            print(f"\n📄 Documentation Requirements:")
                            print(f"   Completeness: {doc_plan['doc_completeness_score']}/1.0")
                            print(f"   Suggested updates:")
                            for update in doc_plan['suggested_updates'][:3]:
                                print(f"     • {update['doc_path']}")
                                print(f"       Reason: {update['reason']}")
                    except Exception:
                        pass
                else:
                    db.close()
            except Exception:
                pass

        return result

    except Exception as e:
        handle_cli_error(e, "Postflight submit", getattr(args, 'verbose', False))
