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
from empirica.core.canonical.empirica_git.sentinel_hooks import SentinelHooks, SentinelDecision

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

            # Add checkpoint - this writes to ALL 3 storage layers (round auto-increments)
            checkpoint_id = logger_instance.add_checkpoint(
                phase="PREFLIGHT",
                vectors=vectors,
                metadata={
                    "reasoning": reasoning,
                    "prompt": reasoning or "Preflight assessment"
                }
            )

            # SENTINEL HOOK: Evaluate checkpoint for routing decisions
            sentinel_decision = None
            if SentinelHooks.is_enabled():
                sentinel_decision = SentinelHooks.post_checkpoint_hook(
                    session_id=session_id,
                    ai_id=None,  # Will be fetched from session
                    phase="PREFLIGHT",
                    checkpoint_data={
                        "vectors": vectors,
                        "reasoning": reasoning,
                        "checkpoint_id": checkpoint_id
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

            # BAYESIAN CALIBRATION: Load calibration adjustments based on historical performance
            # This informs the AI about its known biases from past sessions
            calibration_adjustments = {}
            calibration_report = None
            try:
                from empirica.core.bayesian_beliefs import BayesianBeliefManager

                # Get AI ID from session
                cursor = db.conn.cursor()
                cursor.execute("SELECT ai_id FROM sessions WHERE session_id = ?", (session_id,))
                row = cursor.fetchone()
                ai_id = row[0] if row else 'unknown'

                if ai_id != 'unknown':
                    belief_manager = BayesianBeliefManager(db)
                    calibration_adjustments = belief_manager.get_calibration_adjustments(ai_id)
                    calibration_report = belief_manager.get_calibration_report(ai_id)

                    if calibration_adjustments:
                        logger.debug(f"Loaded calibration adjustments for {len(calibration_adjustments)} vectors")
            except Exception as e:
                logger.debug(f"Calibration loading failed (non-fatal): {e}")

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
                },
                "calibration": {
                    "adjustments": calibration_adjustments if calibration_adjustments else None,
                    "total_evidence": calibration_report.get('total_evidence', 0) if calibration_report else 0,
                    "summary": calibration_report.get('calibration_summary') if calibration_report else None,
                    "note": "Adjustments show historical bias (+ = underestimate, - = overestimate)"
                } if calibration_adjustments or calibration_report else None,
                "sentinel": {
                    "enabled": SentinelHooks.is_enabled(),
                    "decision": sentinel_decision.value if sentinel_decision else None
                } if SentinelHooks.is_enabled() else None
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

        # Return None to avoid exit code issues and duplicate output
        return None

    except Exception as e:
        handle_cli_error(e, "Preflight submit", getattr(args, 'verbose', False))


def handle_check_command(args):
    """
    Handle CHECK command - Evidence-based mid-session grounding

    Auto-loads:
    - PREFLIGHT baseline vectors
    - Current checkpoint (latest assessment)
    - Accumulated findings/unknowns

    Returns:
    - Evidence-based decision suggestion
    - Drift analysis from baseline
    - Reasoning for suggestion
    """
    try:
        import time
        import sys
        from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
        from empirica.data.session_database import SessionDatabase

        # Try to load from stdin if available
        config_data = None
        try:
            if not sys.stdin.isatty():
                config_data = parse_json_safely(sys.stdin.read())
        except:
            pass

        # Extract parameters from args or stdin config
        session_id = getattr(args, 'session_id', None) or (config_data.get('session_id') if config_data else None)
        cycle = getattr(args, 'cycle', None) or (config_data.get('cycle') if config_data else None)
        round_num = getattr(args, 'round', None) or (config_data.get('round') if config_data else None)
        output_format = getattr(args, 'output', 'json') or (config_data.get('output', 'json') if config_data else 'json')
        verbose = getattr(args, 'verbose', False) or (config_data.get('verbose', False) if config_data else False)
        
        # Extract explicit confidence from input (GATE CHECK uses stated confidence, not derived)
        explicit_confidence = config_data.get('confidence') if config_data else None

        if not session_id:
            print(json.dumps({
                "ok": False,
                "error": "session_id is required"
            }))
            sys.exit(1)

        db = SessionDatabase()
        git_logger = GitEnhancedReflexLogger(session_id=session_id, enable_git_notes=True)

        # 1. Load PREFLIGHT baseline
        preflight = db.get_preflight_vectors(session_id)
        if not preflight:
            print(json.dumps({
                "ok": False,
                "error": "No PREFLIGHT found for session",
                "hint": "Run PREFLIGHT first to establish baseline"
            }))
            sys.exit(1)

        # Extract vectors from preflight (it's a dict with 'vectors' key)
        baseline_vectors = preflight.get('vectors', preflight) if isinstance(preflight, dict) else preflight

        # 2. Load current checkpoint (latest assessment)
        checkpoints = git_logger.list_checkpoints(limit=1)
        if not checkpoints:
            # For first CHECK, baseline = current
            current_vectors = baseline_vectors
            drift = 0.0
            deltas = {k: 0.0 for k in baseline_vectors.keys() if isinstance(baseline_vectors.get(k), (int, float))}
        else:
            current_checkpoint = checkpoints[0]
            current_vectors = current_checkpoint.get('vectors', {})

            # 3. Calculate drift from baseline
            deltas = {}
            drift_sum = 0.0
            drift_count = 0

            for key in ['know', 'uncertainty', 'engagement', 'impact', 'completion']:
                if key in baseline_vectors and key in current_vectors:
                    delta = current_vectors[key] - baseline_vectors[key]
                    deltas[key] = delta
                    drift_sum += abs(delta)
                    drift_count += 1

            drift = drift_sum / drift_count if drift_count > 0 else 0.0

        # 4. Auto-load findings/unknowns from database using BreadcrumbRepository
        try:
            # Get project_id from session
            session_data = db.get_session(session_id)
            project_id = session_data.get('project_id') if session_data else None

            if project_id:
                # Use BreadcrumbRepository to query findings/unknowns
                findings_list = db.breadcrumbs.get_project_findings(project_id)
                unknowns_list = db.breadcrumbs.get_project_unknowns(project_id, resolved=False)

                # Extract just the finding/unknown text for display
                findings = [{"finding": f.get('finding', ''), "impact": f.get('impact')}
                           for f in findings_list]
                unknowns = [u.get('unknown', '') for u in unknowns_list]
            else:
                findings = []
                unknowns = []
        except Exception as e:
            logger.warning(f"Could not load findings/unknowns: {e}")
            findings = []
            unknowns = []

        # 5. Generate evidence-based suggestion
        findings_count = len(findings)
        unknowns_count = len(unknowns)
        completion = current_vectors.get('completion', 0.0)
        uncertainty = current_vectors.get('uncertainty', 0.5)

        # Calculate confidence (use explicit if provided, else derive from uncertainty)
        confidence = explicit_confidence if explicit_confidence is not None else (1.0 - uncertainty)

        # GATE LOGIC: Primary decision based on confidence threshold (≥0.70)
        # Secondary validation based on evidence (drift, unknowns)
        suggestions = []

        if confidence >= 0.70:
            # PROCEED path - confidence threshold met
            if drift > 0.3 or unknowns_count > 5:
                # High evidence of gaps - warn but allow proceed
                decision = "proceed"
                strength = "moderate"
                reasoning = f"Confidence ({confidence:.2f}) meets threshold, but {unknowns_count} unknowns and drift ({drift:.2f}) suggest caution"
                suggestions.append("Confidence threshold met - you may proceed")
                suggestions.append(f"Be aware: {unknowns_count} unknowns remain and drift is {drift:.2f}")
            else:
                # Clean proceed
                decision = "proceed"
                strength = "strong"
                reasoning = f"Confidence ({confidence:.2f}) ≥ 0.70 threshold, low drift ({drift:.2f}), {unknowns_count} unknowns"
                suggestions.append("Evidence supports proceeding to action phase")
        else:
            # INVESTIGATE path - confidence below threshold
            if unknowns_count > 5 or drift > 0.3:
                # Strong evidence backing the low confidence
                decision = "investigate"
                strength = "strong"
                reasoning = f"Confidence ({confidence:.2f}) < 0.70 threshold + {unknowns_count} unknowns and drift ({drift:.2f}) - investigation required"
                suggestions.append("Confidence below threshold - investigate before proceeding")
                suggestions.append(f"Address {unknowns_count} unknowns to increase confidence")
            else:
                # Low confidence but low evidence - possible calibration issue
                decision = "investigate"
                strength = "moderate"
                reasoning = f"Confidence ({confidence:.2f}) < 0.70 threshold, but only {unknowns_count} unknowns and drift ({drift:.2f}) - investigate to validate"
                suggestions.append("Confidence below threshold - investigate or recalibrate")
                suggestions.append("Evidence doesn't fully explain low confidence")

        # Determine drift level
        if drift > 0.3:
            drift_level = "high"
        elif drift > 0.1:
            drift_level = "medium"
        else:
            drift_level = "low"

        # 6. Create checkpoint with new assessment
        checkpoint_id = git_logger.add_checkpoint(
            phase="CHECK",
            round_num=cycle or 1,
            vectors=current_vectors,
            metadata={
                "decision": decision,
                "suggestion_strength": strength,
                "drift": drift,
                "findings_count": findings_count,
                "unknowns_count": unknowns_count,
                "reasoning": reasoning
            }
        )

        # 7. Build result
        # Use explicit confidence if provided (GATE CHECK), else derive from uncertainty
        confidence_value = explicit_confidence if explicit_confidence is not None else (1.0 - uncertainty)
        
        result = {
            "ok": True,
            "session_id": session_id,
            "checkpoint_id": checkpoint_id,
            "decision": decision,
            "suggestion_strength": strength,
            "confidence": confidence_value,
            "drift_analysis": {
                "overall_drift": drift,
                "drift_level": drift_level,
                "baseline": baseline_vectors,
                "current": current_vectors,
                "deltas": deltas
            },
            "evidence": {
                "findings_count": findings_count,
                "unknowns_count": unknowns_count
            },
            "investigation_progress": {
                "cycle": cycle,
                "round": round_num,
                "total_checkpoints": len(git_logger.list_checkpoints(limit=100))
            },
            "recommendation": {
                "type": "suggestive",
                "message": reasoning,
                "suggestions": suggestions,
                "note": "This is an evidence-based suggestion. Override if task context warrants it."
            },
            "timestamp": time.time()
        }

        # Include full evidence if verbose
        if verbose:
            result["evidence"]["findings"] = findings
            result["evidence"]["unknowns"] = unknowns

        # Output
        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            # Human-readable output
            print(f"\n🔍 CHECK - Mid-Session Grounding")
            print("=" * 70)
            print(f"Session: {session_id}")
            print(f"Decision: {decision.upper()} ({strength} suggestion)")
            print(f"\n📊 Drift Analysis:")
            print(f"   Overall drift: {drift:.2%} ({drift_level})")
            print(f"   Know: {deltas.get('know', 0):+.2f}")
            print(f"   Uncertainty: {deltas.get('uncertainty', 0):+.2f}")
            print(f"   Completion: {deltas.get('completion', 0):+.2f}")
            print(f"\n📚 Evidence:")
            print(f"   Findings: {findings_count}")
            print(f"   Unknowns: {unknowns_count}")
            print(f"\n💡 Recommendation:")
            print(f"   {reasoning}")
            for suggestion in suggestions:
                print(f"   • {suggestion}")

    except Exception as e:
        handle_cli_error(e, "CHECK", getattr(args, 'verbose', False))




def handle_check_submit_command(args):
    """Handle check-submit command"""
    try:
        import sys
        import os
        import json
        from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
        
        # AI-FIRST MODE: Check if config provided
        config_data = None
        if hasattr(args, 'config') and args.config:
            if args.config == '-':
                config_data = parse_json_safely(sys.stdin.read())
            else:
                if not os.path.exists(args.config):
                    import json
                    print(json.dumps({"ok": False, "error": f"Config file not found: {args.config}"}))
                    sys.exit(1)
                with open(args.config, 'r') as f:
                    config_data = parse_json_safely(f.read())
        
        # Parse arguments from config or CLI
        if config_data:
            session_id = config_data.get('session_id')
            vectors = config_data.get('vectors')
            decision = config_data.get('decision')
            reasoning = config_data.get('reasoning', '')
            output_format = config_data.get('output', 'json')  # Default to JSON for AI-first
        else:
            session_id = args.session_id
            vectors = parse_json_safely(args.vectors) if isinstance(args.vectors, str) else args.vectors
            decision = args.decision
            reasoning = args.reasoning
            output_format = getattr(args, 'output', 'human')
        cycle = getattr(args, 'cycle', 1)  # Default to 1 if not provided
        round_num = getattr(args, 'round', 1)  # Default to 1 if not provided, don't depend on cycle
        
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
                round_num=round_num,
                vectors=vectors,
                metadata={
                    "decision": decision,
                    "reasoning": reasoning,
                    "confidence": confidence,
                    "gaps": gaps,
                    "cycle": cycle,
                    "round": round_num
                }
            )

            # SENTINEL HOOK: Evaluate checkpoint for routing decisions
            # CHECK phase is especially important for Sentinel - it gates noetic→praxic transition
            sentinel_decision = None
            if SentinelHooks.is_enabled():
                sentinel_decision = SentinelHooks.post_checkpoint_hook(
                    session_id=session_id,
                    ai_id=None,
                    phase="CHECK",
                    checkpoint_data={
                        "vectors": vectors,
                        "decision": decision,
                        "reasoning": reasoning,
                        "confidence": confidence,
                        "gaps": gaps,
                        "cycle": cycle,
                        "round": round_num,
                        "checkpoint_id": checkpoint_id
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
                            "--round", str(round_num),
                            "--metadata", json.dumps({
                                "auto_checkpoint": True,
                                "reason": "risky_decision",
                                "uncertainty": uncertainty,
                                "decision": decision,
                                "gaps": gaps,
                                "cycle": cycle,
                                "round": round_num
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
                },
                "sentinel": {
                    "enabled": SentinelHooks.is_enabled(),
                    "decision": sentinel_decision.value if sentinel_decision else None,
                    "note": "Sentinel can override AI decision (PROCEED→INVESTIGATE, etc.)"
                } if SentinelHooks.is_enabled() else None
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
        if output_format == 'json':
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

        # Return None to avoid exit code issues and duplicate output
        return None
        
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

            # Add checkpoint - this writes to ALL 3 storage layers atomically (round auto-increments)
            checkpoint_id = logger_instance.add_checkpoint(
                phase="POSTFLIGHT",
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

            # SENTINEL HOOK: Evaluate checkpoint for routing decisions
            # POSTFLIGHT is final assessment - Sentinel can flag calibration issues or recommend handoff
            sentinel_decision = None
            if SentinelHooks.is_enabled():
                sentinel_decision = SentinelHooks.post_checkpoint_hook(
                    session_id=session_id,
                    ai_id=None,
                    phase="POSTFLIGHT",
                    checkpoint_data={
                        "vectors": vectors,
                        "reasoning": reasoning,
                        "postflight_confidence": postflight_confidence,
                        "calibration_accuracy": calibration_accuracy,
                        "deltas": deltas,
                        "calibration_issues": calibration_issues,
                        "checkpoint_id": checkpoint_id
                    }
                )

            # NOTE: Removed auto-checkpoint after POSTFLIGHT
            # POSTFLIGHT already writes to all 3 storage layers (SQLite + Git Notes + JSON)
            # Creating an additional checkpoint was creating duplicate entries with default values
            # The GitEnhancedReflexLogger.add_checkpoint() call above is sufficient

            # BAYESIAN BELIEF UPDATE: Update AI calibration priors based on PREFLIGHT → POSTFLIGHT deltas
            # This enables the AI to learn from its own performance over time
            belief_updates = {}
            try:
                if preflight_vectors:
                    from empirica.core.bayesian_beliefs import BayesianBeliefManager

                    db = SessionDatabase()
                    belief_manager = BayesianBeliefManager(db)

                    # Get cascade_id for this session
                    cursor = db.conn.cursor()
                    cursor.execute("""
                        SELECT cascade_id FROM cascades
                        WHERE session_id = ?
                        ORDER BY started_at DESC LIMIT 1
                    """, (session_id,))
                    cascade_row = cursor.fetchone()
                    cascade_id = cascade_row[0] if cascade_row else str(uuid.uuid4())

                    # Update beliefs with PREFLIGHT → POSTFLIGHT comparison
                    belief_updates = belief_manager.update_beliefs(
                        cascade_id=cascade_id,
                        session_id=session_id,
                        preflight_vectors=preflight_vectors,
                        postflight_vectors=vectors
                    )

                    if belief_updates:
                        logger.debug(f"Updated Bayesian beliefs for {len(belief_updates)} vectors")

                    db.close()
            except Exception as e:
                logger.debug(f"Bayesian belief update failed (non-fatal): {e}")

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
                "bayesian_beliefs_updated": len(belief_updates) if belief_updates else 0,
                "auto_checkpoint_created": True,
                "persisted": True,
                "storage_layers": {
                    "sqlite": True,
                    "git_notes": checkpoint_id is not None and checkpoint_id != "",
                    "json_logs": True,
                    "bayesian_beliefs": len(belief_updates) > 0 if belief_updates else False
                },
                "sentinel": {
                    "enabled": SentinelHooks.is_enabled(),
                    "decision": sentinel_decision.value if sentinel_decision else None,
                    "note": "Session complete. Sentinel can recommend handoff or flag issues."
                } if SentinelHooks.is_enabled() else None
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

        # Return None to avoid exit code issues and duplicate output
        return None

    except Exception as e:
        handle_cli_error(e, "Postflight submit", getattr(args, 'verbose', False))
