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
from ..validation import PreflightInput, CheckInput, PostflightInput, safe_validate
from empirica.core.canonical.empirica_git.sentinel_hooks import SentinelHooks, SentinelDecision, auto_enable_sentinel
from empirica.utils.session_resolver import resolve_session_id

# Auto-enable Sentinel with default evaluator on module load
auto_enable_sentinel()

logger = logging.getLogger(__name__)


def _check_bootstrap_status(session_id: str) -> dict:
    """
    Check if project-bootstrap has been run for this session.

    Returns:
        {
            "has_bootstrap": bool,
            "project_id": str or None,
            "session_exists": bool
        }
    """
    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Check if session exists and has project_id
        cursor.execute("""
            SELECT session_id, project_id FROM sessions
            WHERE session_id = ?
        """, (session_id,))
        row = cursor.fetchone()
        db.close()

        if not row:
            return {
                "has_bootstrap": False,
                "project_id": None,
                "session_exists": False
            }

        project_id = row[1] if row else None
        return {
            "has_bootstrap": project_id is not None,
            "project_id": project_id,
            "session_exists": True
        }
    except Exception as e:
        return {
            "has_bootstrap": False,
            "project_id": None,
            "session_exists": False,
            "error": str(e)
        }


def _auto_bootstrap(session_id: str) -> dict:
    """
    Auto-run project-bootstrap for a session.

    Returns:
        {"ok": bool, "project_id": str, "message": str}
    """
    import subprocess
    try:
        result = subprocess.run(
            ['empirica', 'project-bootstrap', '--session-id', session_id, '--output', 'json'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                return {
                    "ok": True,
                    "project_id": output.get('project_id'),
                    "message": "Auto-bootstrap completed"
                }
            except json.JSONDecodeError:
                return {"ok": True, "project_id": None, "message": "Bootstrap ran (non-JSON output)"}
        else:
            return {"ok": False, "error": result.stderr[:500]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


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
            # AI-FIRST MODE: Use config file with Pydantic validation
            validated, error = safe_validate(config_data, PreflightInput)
            if error:
                print(json.dumps({
                    "ok": False,
                    "error": f"Invalid input: {error}",
                    "hint": "Required: session_id (str), vectors (dict with know, uncertainty)"
                }))
                sys.exit(1)

            session_id = validated.session_id
            vectors = validated.vectors
            reasoning = validated.reasoning or ''
            task_context = validated.task_context or ''
            output_format = 'json'  # AI-first always uses JSON output
        else:
            # LEGACY MODE: Use CLI flags
            session_id = args.session_id
            vectors = parse_json_safely(args.vectors) if isinstance(args.vectors, str) else args.vectors
            reasoning = args.reasoning
            task_context = getattr(args, 'task_context', '') or ''  # For pattern retrieval
            output_format = getattr(args, 'output', 'json')  # Default to JSON

            # Validate required fields for legacy mode
            if not session_id or not vectors:
                print(json.dumps({
                    "ok": False,
                    "error": "Legacy mode requires --session-id and --vectors flags",
                    "hint": "For AI-first mode, use: empirica preflight-submit config.json"
                }))
                sys.exit(1)

            # Validate vectors with Pydantic in legacy mode too
            legacy_data = {'session_id': session_id, 'vectors': vectors, 'reasoning': reasoning}
            validated, error = safe_validate(legacy_data, PreflightInput)
            if error:
                print(json.dumps({
                    "ok": False,
                    "error": f"Invalid vectors: {error}",
                    "hint": "Vectors must include 'know' and 'uncertainty' (0.0-1.0)"
                }))
                sys.exit(1)
            vectors = validated.vectors  # Use validated vectors

        # Resolve partial session IDs to full UUIDs
        try:
            session_id = resolve_session_id(session_id)
        except ValueError as e:
            print(json.dumps({
                "ok": False,
                "error": f"Invalid session_id: {e}",
                "hint": "Use full UUID, partial UUID (8+ chars), or 'latest'"
            }))
            sys.exit(1)

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

            # Get project_id for pattern retrieval
            project_id = None
            try:
                cursor = db.conn.cursor()
                cursor.execute("SELECT project_id FROM sessions WHERE session_id = ?", (session_id,))
                row = cursor.fetchone()
                project_id = row[0] if row else None
            except Exception:
                pass

            db.close()

            # PATTERN RETRIEVAL: Load relevant patterns based on task_context
            # This arms the AI with lessons, dead_ends, and findings BEFORE starting work
            patterns = None
            if task_context and project_id:
                try:
                    from empirica.core.qdrant.pattern_retrieval import retrieve_task_patterns
                    patterns = retrieve_task_patterns(project_id, task_context)
                    if patterns and any(patterns.values()):
                        logger.debug(f"Retrieved patterns: {len(patterns.get('lessons', []))} lessons, "
                                   f"{len(patterns.get('dead_ends', []))} dead_ends, "
                                   f"{len(patterns.get('relevant_findings', []))} findings")
                except Exception as e:
                    logger.debug(f"Pattern retrieval failed (optional): {e}")

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
                } if SentinelHooks.is_enabled() else None,
                "patterns": patterns if patterns and any(patterns.values()) else None
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
        import os
        from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
        from empirica.data.session_database import SessionDatabase

        # AI-FIRST MODE: Check if config provided as positional argument
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
        else:
            # Try to load from stdin if available (legacy mode)
            try:
                if not sys.stdin.isatty():
                    config_data = parse_json_safely(sys.stdin.read())
            except:
                pass

        # Extract parameters from args or config
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

        # PATTERN MATCHING: Check current approach against known failures
        # This is REACTIVE validation - surfacing warnings before proceeding
        pattern_warnings = None
        if project_id:
            try:
                from empirica.core.qdrant.pattern_retrieval import check_against_patterns

                # Get approach from config or checkpoint metadata
                current_approach = None
                if config_data:
                    current_approach = config_data.get('approach') or config_data.get('reasoning')
                if not current_approach and checkpoints:
                    current_approach = checkpoints[0].get('metadata', {}).get('reasoning')

                pattern_warnings = check_against_patterns(
                    project_id,
                    current_approach or "",
                    current_vectors
                )

                if pattern_warnings and pattern_warnings.get('has_warnings'):
                    # Add warnings to suggestions
                    if pattern_warnings.get('dead_end_matches'):
                        for de in pattern_warnings['dead_end_matches']:
                            suggestions.append(f"⚠️ Similar to dead end: {de.get('approach', '')[:50]}... (why: {de.get('why_failed', '')[:50]})")
                    if pattern_warnings.get('mistake_risk'):
                        suggestions.append(f"⚠️ {pattern_warnings['mistake_risk']}")

                    logger.debug(f"Pattern warnings: {len(pattern_warnings.get('dead_end_matches', []))} dead_end matches")
            except Exception as e:
                logger.debug(f"Pattern matching failed (optional): {e}")

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
            "pattern_warnings": pattern_warnings if pattern_warnings and pattern_warnings.get('has_warnings') else None,
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
            approach = config_data.get('approach', reasoning)  # Fallback to reasoning
            output_format = config_data.get('output', 'json')  # Default to JSON for AI-first
        else:
            session_id = args.session_id
            vectors = parse_json_safely(args.vectors) if isinstance(args.vectors, str) else args.vectors
            decision = args.decision
            reasoning = args.reasoning
            approach = getattr(args, 'approach', reasoning)  # Fallback to reasoning
            output_format = getattr(args, 'output', 'human')
        cycle = getattr(args, 'cycle', 1)  # Default to 1 if not provided

        # Resolve partial session IDs to full UUIDs
        try:
            session_id = resolve_session_id(session_id)
        except ValueError as e:
            print(json.dumps({
                "ok": False,
                "error": f"Invalid session_id: {e}",
                "hint": "Use full UUID, partial UUID (8+ chars), or 'latest'"
            }))
            sys.exit(1)

        # BOOTSTRAP GATE: Ensure project context is loaded before CHECK
        # Without bootstrap, CHECK vectors are hollow (same bug as PREFLIGHT-before-bootstrap)
        bootstrap_status = _check_bootstrap_status(session_id)
        bootstrap_result = None
        reground_reason = None

        # Parse vectors early to check for reground triggers
        _vectors_for_check = vectors
        if isinstance(_vectors_for_check, str):
            _vectors_for_check = parse_json_safely(_vectors_for_check)
        if isinstance(_vectors_for_check, dict) and 'vectors' in _vectors_for_check:
            _vectors_for_check = _vectors_for_check['vectors']

        # VECTOR-BASED REGROUND: Re-bootstrap if vectors indicate drift/uncertainty
        # This ensures long-running sessions stay grounded
        context_val = _vectors_for_check.get('context', 0.7) if isinstance(_vectors_for_check, dict) else 0.7
        uncertainty_val = _vectors_for_check.get('uncertainty', 0.3) if isinstance(_vectors_for_check, dict) else 0.3

        needs_reground = False
        if not bootstrap_status.get('has_bootstrap'):
            needs_reground = True
            reground_reason = "initial bootstrap"
        elif context_val < 0.5:
            needs_reground = True
            reground_reason = f"low context ({context_val:.2f} < 0.50)"
        elif uncertainty_val > 0.6:
            needs_reground = True
            reground_reason = f"high uncertainty ({uncertainty_val:.2f} > 0.60)"

        if needs_reground:
            # Auto-run bootstrap to ensure CHECK has context
            import sys as _sys
            print(f"🔄 Auto-running project-bootstrap ({reground_reason})...", file=_sys.stderr)
            bootstrap_result = _auto_bootstrap(session_id)

            if bootstrap_result.get('ok'):
                print(f"✅ Bootstrap complete: project_id={bootstrap_result.get('project_id')}", file=_sys.stderr)
            else:
                # Bootstrap failed - warn but don't block (graceful degradation)
                print(f"⚠️  Bootstrap failed: {bootstrap_result.get('error', 'unknown')}", file=_sys.stderr)
                print("   CHECK will proceed but vectors may be hollow.", file=_sys.stderr)

        # AUTO-INCREMENT ROUND: Get next round from CHECK history
        # Also retrieve previous CHECK vectors for diminishing returns detection
        previous_check_vectors = []
        try:
            from empirica.data.session_database import SessionDatabase
            db = SessionDatabase()
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM reflexes
                WHERE session_id = ? AND phase = 'CHECK'
            """, (session_id,))
            check_count = cursor.fetchone()[0]
            round_num = check_count + 1  # Next round

            # DIMINISHING RETURNS: Get last 3 CHECK vectors for delta analysis
            # Note: reflexes table stores vectors as individual columns, not JSON
            if check_count > 0:
                cursor.execute("""
                    SELECT engagement, know, do, context, clarity, coherence,
                           signal, density, state, change, completion, impact, uncertainty
                    FROM reflexes
                    WHERE session_id = ? AND phase = 'CHECK'
                    ORDER BY timestamp DESC
                    LIMIT 3
                """, (session_id,))
                rows = cursor.fetchall()
                vector_names = ['engagement', 'know', 'do', 'context', 'clarity', 'coherence',
                               'signal', 'density', 'state', 'change', 'completion', 'impact', 'uncertainty']
                for row in rows:
                    prev_vectors = {}
                    for i, name in enumerate(vector_names):
                        if row[i] is not None:
                            prev_vectors[name] = row[i]
                    if prev_vectors:  # Only add if we got any vectors
                        previous_check_vectors.append(prev_vectors)
            db.close()
        except Exception:
            round_num = getattr(args, 'round', 1)  # Fallback to arg or 1

        # Normalize vectors into a flat dict of 13 canonical keys.
        # Accepts:
        # - flat dict: {engagement, know, do, ... uncertainty}
        # - structured dict: {engagement, foundation:{know,do,context}, comprehension:{clarity,...}, execution:{state,...}, uncertainty}
        # - wrapped dict: {vectors: {...}}
        # - JSON string (AI-first inputs)
        if isinstance(vectors, str):
            vectors = parse_json_safely(vectors)

        if isinstance(vectors, dict) and 'vectors' in vectors and isinstance(vectors.get('vectors'), dict):
            vectors = vectors['vectors']

        if isinstance(vectors, dict) and any(k in vectors for k in ('foundation', 'comprehension', 'execution')):
            flat = {}
            # keep engagement/uncertainty if present
            for k in ('engagement', 'uncertainty'):
                if k in vectors:
                    flat[k] = vectors[k]
            # flatten groups
            flat.update((vectors.get('foundation') or {}))
            flat.update((vectors.get('comprehension') or {}))
            flat.update((vectors.get('execution') or {}))
            vectors = flat

        # Validate inputs
        if not isinstance(vectors, dict):
            raise ValueError("Vectors must be a dictionary")

        # AUTO-COMPUTE DECISION from vectors if not provided
        # Readiness gate (from CLAUDE.md): know >= 0.70 AND uncertainty <= 0.35
        # Apply bias corrections: uncertainty +0.10, know -0.05
        know = vectors.get('know', 0.5)
        uncertainty = vectors.get('uncertainty', 0.5)
        corrected_know = know - 0.05  # AI overestimates knowing
        corrected_uncertainty = uncertainty + 0.10  # AI underestimates doubt

        # DIMINISHING RETURNS DETECTION: Analyze if investigation is still improving
        # Key insight: Speed and correctness are ALIGNED when calibration is good.
        # If investigation stops improving know/reducing uncertainty, proceeding IS correct.
        diminishing_returns = {
            "detected": False,
            "rounds_analyzed": 0,
            "know_deltas": [],
            "uncertainty_deltas": [],
            "reason": None,
            "recommend_proceed": False
        }

        if len(previous_check_vectors) >= 2:
            # Compute deltas between consecutive rounds (newest first)
            # previous_check_vectors[0] = last round, [1] = round before that, etc.
            for i in range(len(previous_check_vectors)):
                if i == 0:
                    # Current vs last round
                    prev_know = previous_check_vectors[i].get('know', 0.5)
                    prev_uncertainty = previous_check_vectors[i].get('uncertainty', 0.5)
                    delta_know = know - prev_know
                    delta_uncertainty = uncertainty - prev_uncertainty  # Negative is good
                    diminishing_returns["know_deltas"].append(delta_know)
                    diminishing_returns["uncertainty_deltas"].append(delta_uncertainty)
                elif i < len(previous_check_vectors):
                    # Between previous rounds
                    curr = previous_check_vectors[i - 1]
                    prev = previous_check_vectors[i]
                    delta_know = curr.get('know', 0.5) - prev.get('know', 0.5)
                    delta_uncertainty = curr.get('uncertainty', 0.5) - prev.get('uncertainty', 0.5)
                    diminishing_returns["know_deltas"].append(delta_know)
                    diminishing_returns["uncertainty_deltas"].append(delta_uncertainty)

            diminishing_returns["rounds_analyzed"] = len(previous_check_vectors) + 1

            # Detect diminishing returns: if last 2 rounds show minimal improvement
            if len(diminishing_returns["know_deltas"]) >= 2:
                recent_know_deltas = diminishing_returns["know_deltas"][:2]
                recent_uncertainty_deltas = diminishing_returns["uncertainty_deltas"][:2]

                # Minimal improvement threshold
                DELTA_THRESHOLD = 0.05  # Less than 5% improvement per round

                know_stagnant = all(abs(d) < DELTA_THRESHOLD for d in recent_know_deltas)
                uncertainty_stagnant = all(d >= -DELTA_THRESHOLD for d in recent_uncertainty_deltas)  # Not decreasing

                if know_stagnant and uncertainty_stagnant:
                    diminishing_returns["detected"] = True
                    diminishing_returns["reason"] = f"know stagnant ({recent_know_deltas}), uncertainty not decreasing ({recent_uncertainty_deltas})"

                    # Recommend proceed if baseline is reasonable (know >= 0.60, uncertainty <= 0.45)
                    # Relaxed thresholds because investigation has plateaued
                    if know >= 0.60 and uncertainty <= 0.45:
                        diminishing_returns["recommend_proceed"] = True
                        diminishing_returns["reason"] += " - baseline adequate, investigation plateaued"
                    else:
                        diminishing_returns["reason"] += " - baseline insufficient for proceed override"

        # Compute decision with diminishing returns factored in
        computed_decision = None
        if corrected_know >= 0.70 and corrected_uncertainty <= 0.35:
            computed_decision = "proceed"
        elif diminishing_returns["recommend_proceed"]:
            # Override: investigation plateaued with adequate baseline
            computed_decision = "proceed"
            logger.info(f"CHECK decision override: proceed due to diminishing returns ({diminishing_returns['reason']})")
        else:
            computed_decision = "investigate"

        # AUTOPILOT MODE: Check if decisions should be binding (enforced)
        # When enabled, CHECK decisions are requirements, not suggestions
        # Controlled by EMPIRICA_AUTOPILOT_MODE env var (default: false)
        autopilot_mode = os.getenv('EMPIRICA_AUTOPILOT_MODE', 'false').lower() in ('true', '1', 'yes')
        decision_binding = autopilot_mode  # Binding when autopilot is enabled

        # Use computed decision if none provided OR if autopilot is enforcing
        if not decision or (autopilot_mode and decision != computed_decision):
            if autopilot_mode and decision and decision != computed_decision:
                logger.info(f"AUTOPILOT override: {decision} → {computed_decision} (autopilot enforcement)")
            decision = computed_decision
            logger.info(f"CHECK auto-computed decision: {decision} (know={know:.2f}→{corrected_know:.2f}, uncertainty={uncertainty:.2f}→{corrected_uncertainty:.2f})")

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
            
            # NOTE: Bayesian belief updates during CHECK were REMOVED (2026-01-21)
            # Reason: CHECK-phase updates polluted calibration data by recording mid-session
            # observations without proper PREFLIGHT→POSTFLIGHT baseline comparison.
            # Calibration now uses vector_trajectories table which captures clean start/end vectors.
            # POSTFLIGHT still does proper belief updates with PREFLIGHT comparison (see postflight_submit).
            
            # Wire CHECK phase hooks (TIER 3 Priority 3)
            # Capture fresh epistemic state before and after CHECK
            try:
                import subprocess
                
                # Pre-CHECK hook: Capture state BEFORE checkpoint storage
                # (Note: In real flow, pre_check would run BEFORE check-submit)
                # For now, document that this should be called by orchestration layer
                
                # Post-CHECK hook: Capture state AFTER checkpoint for comparison
                if decision and decision.lower() != 'pending':
                    try:
                        result = subprocess.run(
                            ['empirica', 'check-drift', '--trigger', 'post_check', 
                             '--session-id', session_id],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if result.returncode == 0:
                            logger.info(f"Post-CHECK hook executed for {session_id}")
                    except subprocess.TimeoutExpired:
                        logger.warning("Post-CHECK hook timed out")
                    except Exception as e:
                        logger.warning(f"Post-CHECK hook failed: {e}")
            except Exception as e:
                # Hook failures are non-critical
                logger.warning(f"CHECK phase hooks error: {e}")

            # SENTINEL HOOK: Evaluate checkpoint for routing decisions
            # CHECK phase is especially important for Sentinel - it gates noetic→praxic transition
            sentinel_decision = None
            sentinel_override = False
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

                # SENTINEL OVERRIDE: Feed Sentinel decision back to override AI decision
                # NOTE: When autopilot is binding, autopilot takes precedence over Sentinel
                if sentinel_decision and not decision_binding:
                    sentinel_map = {
                        SentinelDecision.PROCEED: "proceed",
                        SentinelDecision.INVESTIGATE: "investigate",
                        SentinelDecision.BRANCH: "investigate",  # Branch implies more investigation needed
                        SentinelDecision.HALT: "investigate",  # Halt = stop and reassess
                        SentinelDecision.REVISE: "investigate",  # Revise = need more work
                    }
                    if sentinel_decision in sentinel_map:
                        new_decision = sentinel_map[sentinel_decision]
                        if new_decision != decision:
                            logger.info(f"Sentinel override: {decision} → {new_decision} (sentinel={sentinel_decision.value})")
                            decision = new_decision
                            sentinel_override = True
                elif sentinel_decision and decision_binding:
                    logger.info(f"Autopilot binding active - Sentinel override blocked (sentinel wanted: {sentinel_decision.value})")

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

            # EPISTEMIC SNAPSHOTS: Capture CHECK phase vectors for calibration analysis
            # Added 2026-01-21 to provide CHECK data for vector_trajectories analysis
            # Previously only POSTFLIGHT was captured, missing CHECK as intermediate data point
            snapshot_created = False
            snapshot_id = None
            try:
                from empirica.data.snapshot_provider import EpistemicSnapshotProvider
                from empirica.data.epistemic_snapshot import ContextSummary
                from empirica.data.session_database import SessionDatabase

                db = SessionDatabase()
                snapshot_provider = EpistemicSnapshotProvider()

                # Build context summary from CHECK state
                check_confidence = 1.0 - uncertainty
                context_summary = ContextSummary(
                    semantic={"phase": "CHECK", "decision": decision, "confidence": check_confidence},
                    narrative=reasoning or f"CHECK round {round_num}: {decision}",
                    evidence_refs=[checkpoint_id] if checkpoint_id else []
                )

                # Create snapshot - this auto-links to previous snapshot (PREFLIGHT)
                snapshot = snapshot_provider.create_snapshot_from_session(
                    session_id=session_id,
                    context_summary=context_summary,
                    cascade_phase="CHECK",
                    domain_vectors={"round": round_num, "decision": decision} if round_num else None
                )

                # Set vectors
                snapshot.vectors = vectors
                # No delta for CHECK - deltas are POSTFLIGHT-PREFLIGHT only

                # Save to epistemic_snapshots table
                snapshot_provider.save_snapshot(snapshot)
                snapshot_id = snapshot.snapshot_id
                snapshot_created = True

                logger.debug(f"Created CHECK epistemic snapshot {snapshot_id} for session {session_id}")

                db.close()
            except Exception as e:
                # Snapshot creation is non-fatal
                logger.debug(f"CHECK epistemic snapshot creation skipped: {e}")

            result = {
                "ok": True,
                "session_id": session_id,
                "checkpoint_id": checkpoint_id,
                "decision": decision,
                "round": round_num,
                "cycle": cycle,
                "vectors_count": len(vectors),
                "reasoning": reasoning,
                "auto_checkpoint_created": auto_checkpoint_created,
                "persisted": True,
                "storage_layers": {
                    "sqlite": True,
                    "git_notes": checkpoint_id is not None and checkpoint_id != "",
                    "json_logs": True,
                    "epistemic_snapshots": snapshot_created
                },
                "snapshot": {
                    "created": snapshot_created,
                    "snapshot_id": snapshot_id,
                    "note": "CHECK vectors captured for calibration analysis"
                } if snapshot_created else None,
                "bootstrap": {
                    "had_context": bootstrap_status.get('has_bootstrap', False),
                    "auto_run": bootstrap_result is not None,
                    "reground_reason": reground_reason,
                    "project_id": bootstrap_result.get('project_id') if bootstrap_result else bootstrap_status.get('project_id')
                },
                "metacog": {
                    "computed_decision": computed_decision,
                    "raw_vectors": {"know": know, "uncertainty": uncertainty},
                    "corrected_vectors": {"know": corrected_know, "uncertainty": corrected_uncertainty},
                    "readiness_gate": "know>=0.70 AND uncertainty<=0.35 (after bias correction)",
                    "gate_passed": computed_decision == "proceed",
                    "diminishing_returns": diminishing_returns,
                    "autopilot": {
                        "enabled": autopilot_mode,
                        "binding": decision_binding,
                        "note": "When binding=true, decision is enforced (not suggestive). Set EMPIRICA_AUTOPILOT_MODE=true to enable."
                    }
                },
                "sentinel": {
                    "enabled": SentinelHooks.is_enabled(),
                    "decision": sentinel_decision.value if sentinel_decision else None,
                    "override_applied": sentinel_override,
                    "note": "Sentinel feeds back to override AI decision"
                } if SentinelHooks.is_enabled() else None
            }

            # AUTO-POSTFLIGHT TRIGGER: Check if goal completion detected
            # Uses completion and impact vectors to determine if a goal was completed
            # This closes the epistemic loop automatically without user intervention
            # Controlled by EMPIRICA_AUTO_POSTFLIGHT env var (default: true)
            auto_postflight_enabled = os.getenv('EMPIRICA_AUTO_POSTFLIGHT', 'true').lower() == 'true'

            if not auto_postflight_enabled:
                result["auto_postflight"] = {"triggered": False, "disabled": True, "reason": "EMPIRICA_AUTO_POSTFLIGHT=false"}
            else:
                goal_completion = _check_goal_completion(vectors)
                result["goal_completion"] = goal_completion

                if goal_completion.get("triggered"):
                    import sys as _sys
                    print(f"🎯 Goal completion detected: {goal_completion.get('reason')}", file=_sys.stderr)
                    print("📊 Auto-triggering POSTFLIGHT to capture learning delta...", file=_sys.stderr)

                    postflight_result = _auto_postflight(
                        session_id=session_id,
                        vectors=vectors,
                        trigger_reason=goal_completion.get('reason', 'completion threshold met')
                    )

                    result["auto_postflight"] = {
                        "triggered": True,
                        "success": postflight_result.get("ok", False),
                        "reason": goal_completion.get("reason")
                    }

                    if postflight_result.get("ok"):
                        print("✅ Auto-POSTFLIGHT captured successfully", file=_sys.stderr)
                    else:
                        print(f"⚠️  Auto-POSTFLIGHT failed: {postflight_result.get('error', 'unknown')}", file=_sys.stderr)
                else:
                    result["auto_postflight"] = {"triggered": False}

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


def _check_goal_completion(vectors: dict, calibration_adjustments: dict = None) -> dict:
    """
    Check if vectors indicate goal completion.

    Thresholds (raw, before calibration):
    - completion >= 0.7 (we underestimate by +0.14, so 0.7 raw ≈ 0.84 actual)
    - impact >= 0.5 (if present)

    Returns:
        {
            "triggered": bool,
            "raw_completion": float,
            "calibrated_completion": float,
            "raw_impact": float,
            "reason": str
        }
    """
    completion = vectors.get('completion', 0.0)
    impact = vectors.get('impact', 0.0)

    # Apply calibration adjustment if available
    completion_adj = 0.14  # Default from historical data
    if calibration_adjustments and 'completion' in calibration_adjustments:
        completion_adj = calibration_adjustments['completion']

    calibrated_completion = completion + completion_adj

    # Thresholds
    COMPLETION_THRESHOLD = 0.7  # Raw threshold
    IMPACT_THRESHOLD = 0.5

    triggered = completion >= COMPLETION_THRESHOLD and impact >= IMPACT_THRESHOLD

    reason = None
    if triggered:
        reason = f"Goal completion detected (completion={completion:.2f}→{calibrated_completion:.2f}, impact={impact:.2f})"
    elif completion >= COMPLETION_THRESHOLD:
        reason = f"High completion but low impact (completion={completion:.2f}, impact={impact:.2f})"
    elif impact >= IMPACT_THRESHOLD:
        reason = f"High impact but low completion (completion={completion:.2f}, impact={impact:.2f})"

    return {
        "triggered": triggered,
        "raw_completion": completion,
        "calibrated_completion": calibrated_completion,
        "raw_impact": impact,
        "reason": reason
    }


def _auto_postflight(session_id: str, vectors: dict, trigger_reason: str) -> dict:
    """
    Auto-submit POSTFLIGHT when goal completion is detected.

    This closes the epistemic loop automatically without user intervention.
    """
    import subprocess

    # Build POSTFLIGHT payload
    payload = {
        "session_id": session_id,
        "vectors": vectors,
        "learnings": [f"Auto-POSTFLIGHT triggered: {trigger_reason}"],
        "delta_summary": "Auto-captured on goal completion detection"
    }

    try:
        result = subprocess.run(
            ['empirica', 'postflight-submit', '-'],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                return {"ok": True, "output": output}
            except json.JSONDecodeError:
                return {"ok": True, "output": result.stdout[:500]}
        else:
            return {"ok": False, "error": result.stderr[:500]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


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

        # Resolve partial session IDs to full UUIDs
        try:
            session_id = resolve_session_id(session_id)
        except ValueError as e:
            print(json.dumps({
                "ok": False,
                "error": f"Invalid session_id: {e}",
                "hint": "Use full UUID, partial UUID (8+ chars), or 'latest'"
            }))
            sys.exit(1)

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

            # BAYESIAN BELIEF UPDATE: Update AI priors based on PREFLIGHT → POSTFLIGHT deltas
            # NOTE: Primary calibration source is vector_trajectories table (clean start/end vectors).
            # This bayesian update is secondary - kept for backward compatibility and .breadcrumbs.yaml export.
            belief_updates = {}
            calibration_exported = False
            try:
                if preflight_vectors:
                    from empirica.core.bayesian_beliefs import BayesianBeliefManager

                    db = SessionDatabase()
                    belief_manager = BayesianBeliefManager(db)

                    # Get cascade_id and ai_id for this session
                    cursor = db.conn.cursor()
                    cursor.execute("""
                        SELECT cascade_id FROM cascades
                        WHERE session_id = ?
                        ORDER BY started_at DESC LIMIT 1
                    """, (session_id,))
                    cascade_row = cursor.fetchone()
                    cascade_id = cascade_row[0] if cascade_row else str(uuid.uuid4())

                    # Get ai_id for calibration export
                    cursor.execute("SELECT ai_id FROM sessions WHERE session_id = ?", (session_id,))
                    ai_row = cursor.fetchone()
                    ai_id = ai_row[0] if ai_row else 'claude-code'

                    # Update beliefs with PREFLIGHT → POSTFLIGHT comparison
                    belief_updates = belief_manager.update_beliefs(
                        cascade_id=cascade_id,
                        session_id=session_id,
                        preflight_vectors=preflight_vectors,
                        postflight_vectors=vectors
                    )

                    if belief_updates:
                        logger.debug(f"Updated Bayesian beliefs for {len(belief_updates)} vectors")

                        # BREADCRUMBS CALIBRATION EXPORT: Write to .breadcrumbs.yaml for instant session-start
                        # This creates a calibration cache layer - no DB queries needed at startup
                        try:
                            from empirica.core.bayesian_beliefs import export_calibration_to_breadcrumbs
                            calibration_exported = export_calibration_to_breadcrumbs(ai_id, db)
                            if calibration_exported:
                                logger.debug(f"Exported calibration to .breadcrumbs.yaml for {ai_id}")
                        except Exception as cal_e:
                            logger.debug(f"Calibration export to breadcrumbs skipped: {cal_e}")

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

            # EPISODIC MEMORY: Create session narrative from POSTFLIGHT data (Qdrant)
            episodic_stored = False
            try:
                db = SessionDatabase()
                session = db.get_session(session_id)
                if session and session.get('project_id'):
                    from empirica.core.qdrant.vector_store import embed_episodic
                    import uuid as uuid_mod

                    project_id = session['project_id']

                    # Get project findings/unknowns for narrative richness (optional)
                    try:
                        findings = db.get_project_findings(project_id, limit=5)
                        unknowns = db.get_project_unknowns(project_id, resolved=False, limit=5)
                    except Exception:
                        findings = []
                        unknowns = []

                    # Determine outcome from deltas
                    outcome = "success" if deltas.get("know", 0) > 0.1 else (
                        "partial" if deltas.get("completion", 0) > 0 else "abandoned"
                    )

                    # Build narrative from reasoning and context
                    narrative = reasoning or f"Session completed with learning delta: {deltas}"

                    # Create episodic memory entry (session narrative with temporal decay)
                    episodic_stored = embed_episodic(
                        project_id=project_id,
                        episode_id=str(uuid_mod.uuid4()),
                        narrative=narrative,
                        episode_type="session_arc",
                        session_id=session_id,
                        ai_id=session.get('ai_id', 'claude-code'),
                        goal_id=session.get('current_goal_id'),
                        learning_delta=deltas,
                        outcome=outcome,
                        key_moments=[f.get('finding', '')[:100] for f in findings[:3]] if findings else [],
                        tags=[session.get('ai_id', 'claude-code')],
                        timestamp=time.time(),
                    )
                    if episodic_stored:
                        logger.debug(f"Created episodic memory for session {session_id[:8]}")
                db.close()
            except Exception as e:
                # Episodic storage is optional (requires Qdrant)
                logger.debug(f"Episodic memory creation skipped: {e}")

            # AUTO-EMBED: Sync this session's findings to Qdrant for hot memory retrieval
            # This is incremental (just this session) vs full project-embed
            memory_synced = 0
            try:
                from empirica.core.qdrant.vector_store import upsert_memory, init_collections, _check_qdrant_available

                db = SessionDatabase()
                session = db.get_session(session_id)
                if _check_qdrant_available() and session and session.get('project_id'):
                    project_id = session['project_id']
                    init_collections(project_id)

                    # Get recent project findings/unknowns (session-specific filtering not available)
                    try:
                        session_findings = db.get_project_findings(project_id, limit=10)
                        session_unknowns = db.get_project_unknowns(project_id, resolved=False, limit=10)
                    except Exception:
                        session_findings = []
                        session_unknowns = []

                    # Build memory items
                    mem_items = []
                    mid = 2_000_000 + hash(session_id) % 100000  # Offset to avoid collisions

                    for f in session_findings:
                        mem_items.append({
                            'id': mid,
                            'text': f.get('finding', ''),
                            'type': 'finding',
                            'session_id': f.get('session_id', session_id),
                            'goal_id': f.get('goal_id'),
                            'timestamp': f.get('created_timestamp'),
                        })
                        mid += 1

                    for u in session_unknowns:
                        mem_items.append({
                            'id': mid,
                            'text': u.get('unknown', ''),
                            'type': 'unknown',
                            'session_id': u.get('session_id', session_id),
                            'goal_id': u.get('goal_id'),
                            'timestamp': u.get('created_timestamp'),
                            'is_resolved': u.get('is_resolved', False)
                        })
                        mid += 1

                    if mem_items:
                        upsert_memory(project_id, mem_items)
                        memory_synced = len(mem_items)
                        logger.debug(f"Auto-embedded {memory_synced} memory items to Qdrant")
                db.close()
            except Exception as e:
                # Memory sync is optional (requires Qdrant)
                logger.debug(f"Memory sync skipped: {e}")

            # EPISTEMIC SNAPSHOT: Create replay-capable snapshot with delta chain
            # This enables session replay by storing explicit deltas + previous_snapshot_id links
            snapshot_created = False
            snapshot_id = None
            try:
                from empirica.data.snapshot_provider import EpistemicSnapshotProvider
                from empirica.data.epistemic_snapshot import ContextSummary

                # Get session for ai_id
                db = SessionDatabase()
                session = db.get_session(session_id)

                if session:
                    # Create snapshot provider (uses its own tracker/db connection)
                    snapshot_provider = EpistemicSnapshotProvider()

                    # Build context summary from reasoning
                    context_summary = ContextSummary(
                        semantic={"phase": "POSTFLIGHT", "confidence": postflight_confidence},
                        narrative=reasoning or "Session completed",
                        evidence_refs=[checkpoint_id] if checkpoint_id else []
                    )

                    # Create snapshot - this auto-links to previous snapshot via previous_snapshot_id
                    snapshot = snapshot_provider.create_snapshot_from_session(
                        session_id=session_id,
                        context_summary=context_summary,
                        cascade_phase="POSTFLIGHT",
                        domain_vectors={"deltas": deltas} if deltas else None
                    )

                    # Override vectors with actual POSTFLIGHT vectors (not preflight from db)
                    snapshot.vectors = vectors
                    snapshot.delta = deltas

                    # Save to epistemic_snapshots table
                    snapshot_provider.save_snapshot(snapshot)
                    snapshot_id = snapshot.snapshot_id
                    snapshot_created = True

                    logger.debug(f"Created epistemic snapshot {snapshot_id} for session {session_id}")

                db.close()
            except Exception as e:
                # Snapshot creation is non-fatal
                logger.debug(f"Epistemic snapshot creation skipped: {e}")

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
                    "bayesian_beliefs": len(belief_updates) > 0 if belief_updates else False,
                    "breadcrumbs_calibration": calibration_exported,
                    "episodic_memory": episodic_stored,
                    "epistemic_snapshots": snapshot_created,
                    "qdrant_memory": memory_synced > 0
                },
                "breadcrumbs": {
                    "calibration_exported": calibration_exported,
                    "note": "Calibration written to .breadcrumbs.yaml for instant session-start availability"
                } if calibration_exported else None,
                "memory_synced": memory_synced,
                "snapshot": {
                    "created": snapshot_created,
                    "snapshot_id": snapshot_id,
                    "note": "Snapshot enables session replay with delta chains"
                } if snapshot_created else None,
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
