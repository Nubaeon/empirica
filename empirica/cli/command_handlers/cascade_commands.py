"""
Cascade Commands - CASCADE workflow (PREFLIGHT → CHECK → POSTFLIGHT)

Handles core Empirica CASCADE epistemic workflow phases.
For LLM adapter routing, see modality_commands.py (experimental).
"""

import json
import logging
import uuid
import hashlib
from datetime import datetime
from ..cli_utils import print_component_status, handle_cli_error, format_uncertainty_output, parse_json_safely, print_header

# Set up logging for cascade commands
logger = logging.getLogger(__name__)


def get_recommendation_from_vectors(vectors):
    """
    Get recommendation based on epistemic vectors (inlined from deleted decision_utils.py)
    
    Simple heuristic: if uncertainty > 0.5, recommend investigate; otherwise proceed.
    """
    uncertainty = vectors.get('uncertainty', 0.5)
    engagement = vectors.get('engagement', 0.7)
    
    if engagement < 0.6:
        return "disengage", "Engagement below threshold (0.6)"
    elif uncertainty > 0.5:
        return "investigate", f"High uncertainty ({uncertainty:.2f})"
    else:
        return "proceed", f"Sufficient confidence ({1-uncertainty:.2f})"




def handle_decision_command(args):
    """Handle decision-making command with uncertainty assessment"""
    try:
        from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

        print(f"⚖️ Analyzing decision: {args.decision}")
        
        context = parse_json_safely(getattr(args, 'context', None))
        confidence_threshold = getattr(args, 'confidence_threshold', 0.7)
        
        # Run epistemic cascade for decision-making
        cascade_result = run_epistemic_cascade(
            task=f"Should I proceed with: {args.decision}",
            context=context or {},
            confidence_threshold=confidence_threshold
        )
        
        logger.info(f"✅ Decision analysis complete")
        logger.info(f"   🎯 Decision: {cascade_result.get('final_decision', 'INVESTIGATE')}")
        logger.info(f"   📊 Confidence: {cascade_result.get('confidence', 0.0):.2f}")
        logger.info(f"   ⚖️ Threshold: {confidence_threshold}")
        
        # Recommendation based on confidence
        meets_threshold = cascade_result.get('confidence', 0.0) >= confidence_threshold
        recommendation = "PROCEED" if meets_threshold else "INVESTIGATE FURTHER"
        emoji = "✅" if meets_threshold else "⚠️"
        
        logger.info(f"   {emoji} Recommendation: {recommendation}")
        logger.info(f"   💭 Reasoning: {cascade_result.get('reasoning', 'N/A')}")
        
        # Show epistemic state
        epistemic_state = cascade_result.get('epistemic_state', {})
        if epistemic_state and getattr(args, 'verbose', False):
            logger.info("🧠 Epistemic State:")
            if 'know' in epistemic_state:
                logger.info(f"   📚 KNOW: {epistemic_state['know']:.2f}")
            if 'do' in epistemic_state:
                logger.info(f"   ⚡ DO: {epistemic_state['do']:.2f}")
            if 'context' in epistemic_state:
                logger.info(f"   🌐 CONTEXT: {epistemic_state['context']:.2f}")
        
        # Show required actions or next steps
        if cascade_result.get('required_actions'):
            logger.info("⚡ Next steps:")
            for action in cascade_result['required_actions']:
                logger.info(f"   • {action}")
        
        # Show investigation history if verbose
        if getattr(args, 'verbose', False) and cascade_result.get('investigation_history'):
            logger.info("🔍 Investigation history:")
            for i, investigation in enumerate(cascade_result['investigation_history'], 1):
                logger.info(f"   {i}. {investigation.get('action', 'Unknown')}")
        
    except Exception as e:
        handle_cli_error(e, "Decision analysis", getattr(args, 'verbose', False))


def handle_preflight_command(args):
    """Execute preflight epistemic assessment before task"""
    try:
        from empirica.core.canonical import CanonicalEpistemicAssessor
        from empirica.data.session_database import SessionDatabase
        import asyncio
        
        prompt = args.prompt
        session_id = args.session_id or str(uuid.uuid4())  # Full UUID, no truncation
        ai_id = getattr(args, 'ai_id', 'empirica_cli')
        
        # Execute preflight assessment
        assessor = CanonicalEpistemicAssessor(agent_id=ai_id)
        
        # Get self-assessment prompt from canonical assessor
        assessment_request = asyncio.run(assessor.assess(prompt, {}))
        
        if not isinstance(assessment_request, dict) or 'self_assessment_prompt' not in assessment_request:
            logger.error("❌ Failed to generate self-assessment prompt")
            return
        
        # NEW: --prompt-only flag returns ONLY the prompt (no waiting for input)
        if hasattr(args, 'prompt_only') and args.prompt_only:
            output = {
                "session_id": session_id,
                "task": prompt,
                "self_assessment_prompt": assessment_request['self_assessment_prompt'],
                "phase": "preflight",
                "instructions": "Perform genuine self-assessment and submit with: empirica preflight-submit --session-id <session_id> --vectors <vectors_json>"
            }
            print(json.dumps(output, indent=2))
            return
        
        # LEGACY: Original flow with hanging risk
        # CRITICAL FIX: Add Sentinel routing to prevent hanging
        if hasattr(args, 'sentinel_assess') and args.sentinel_assess:
            print("🔮 SENTINEL ASSESSMENT ROUTING")
            print("⚠️  Sentinel integration not yet implemented")
            print("📍 For now, please use MCP tools directly:")
            print("   • execute_preflight MCP tool")
            print("   • submit_preflight_assessment MCP tool")
            print("")
            print("💡 Alternative: Use working MCP tools instead of hanging CLI")
            return
        
        print_header("🚀 Preflight Assessment")
        print("⚠️  WARNING: This command may hang. Use --prompt-only flag to get prompt without waiting")
        print()
        
        logger.info(f"📋 Task: {prompt}")
        logger.info(f"🆔 Session ID: {session_id}")
        logger.info(f"\n⏳ Assessing epistemic state...\n")
        
        # Check if AI self-assessment was provided via --assessment-json argument
        if hasattr(args, 'assessment_json') and args.assessment_json:
            # Parse the AI's genuine self-assessment
            try:
                # Check if it's a file path or inline JSON
                import os
                
                if os.path.isfile(args.assessment_json):
                    # It's a file path - read the file
                    with open(args.assessment_json, 'r') as f:
                        json_content = f.read()
                else:
                    # It's inline JSON
                    json_content = args.assessment_json
                
                # Validate it's proper JSON
                json.loads(json_content)  # This will raise if invalid
                
                assessment = assessor.parse_llm_response(
                    json_content,
                    assessment_request['assessment_id'],
                    prompt,
                    {}
                )
                vectors = {
                    'know': assessment.know.score,
                    'do': assessment.do.score,
                    'context': assessment.context.score,
                    'clarity': assessment.clarity.score,
                    'coherence': assessment.coherence.score,
                    'signal': assessment.signal.score,
                    'density': assessment.density.score,
                    'state': assessment.state.score,
                    'change': assessment.change.score,
                    'completion': assessment.completion.score,
                    'impact': assessment.impact.score,
                    'engagement': assessment.engagement.score,
                    'uncertainty': assessment.uncertainty.score
                }
            except Exception as e:
                logger.error(f"❌ Failed to parse self-assessment: {e}")
                return
        else:
            # Interactive mode: Display prompt and request assessment
            logger.info("\n" + "=" * 70)
            logger.info("GENUINE SELF-ASSESSMENT REQUIRED")
            logger.info("=" * 70)
            logger.info("\n⚠️  NO HEURISTICS. NO STATIC VALUES. NO CONFABULATION.")
            logger.info("\nThis command requires genuine AI epistemic self-assessment.")
            logger.info("\n📋 SELF-ASSESSMENT PROMPT:")
            logger.info("=" * 70)
            logger.info(assessment_request['self_assessment_prompt'])
            logger.info("=" * 70)
            logger.info("\n💡 HOW TO USE:")
            logger.info("\nOption 1: MCP Server (Recommended for AI assistants)")
            logger.info("  - Use MCP tools for genuine real-time self-assessment")
            logger.info("  - See: docs/guides/MCP_CONFIGURATION_EXAMPLES.md")
            logger.info("\nOption 2: CLI with --assessment-json")
            logger.info("  - AI performs genuine self-assessment")
            logger.info("  - Provide JSON response via --assessment-json flag")
            logger.info("  - Example: empirica preflight \"task\" --assessment-json '{...}'")
            logger.info("\nOption 3: Interactive (you are here)")
            logger.info("  - Paste your genuine self-assessment as JSON when prompted")
            
            if not args.quiet:
                logger.info("\n" + "=" * 70)
                response = input("\nPaste your genuine self-assessment JSON (or press Enter to skip): ")
                
                if response.strip():
                    try:
                        assessment = assessor.parse_llm_response(
                            response,
                            assessment_request['assessment_id'],
                            prompt,
                            {}
                        )
                        vectors = {
                            'know': assessment.know.score,
                            'do': assessment.do.score,
                            'context': assessment.context.score,
                            'clarity': assessment.clarity.score,
                            'coherence': assessment.coherence.score,
                            'signal': assessment.signal.score,
                            'density': assessment.density.score,
                            'state': assessment.state.score,
                            'change': assessment.change.score,
                            'completion': assessment.completion.score,
                            'impact': assessment.impact.score,
                            'engagement': assessment.engagement.score,
                            'uncertainty': assessment.uncertainty.score
                        }
                    except Exception as e:
                        logger.error(f"\n❌ Failed to parse assessment: {e}")
                        return
                else:
                    logger.warning("\n⚠️  Skipping preflight - no genuine assessment provided")
                    logger.info("💡 Use MCP server for automated genuine self-assessment")
                    return
            else:
                logger.warning("\n⚠️  Cannot complete preflight in --quiet mode without --assessment-json")
                return
        
        # Store preflight assessment in reflexes table (unified storage)
        from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger

        logger_instance = GitEnhancedReflexLogger(
            session_id=session_id,
            enable_git_notes=True
        )

        checkpoint_id = logger_instance.add_checkpoint(
            phase="PREFLIGHT",
            round_num=1,
            vectors=vectors,
            metadata={
                "task": prompt,
                "recommendation": recommendation['action'] if isinstance(recommendation, dict) else recommendation
            }
        )

        # Create cascade record for audit trail
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase(db_path=".empirica/sessions/sessions.db")
        try:
            db.create_session(ai_id=ai_id, components_loaded=5, user_id=None)
        except:
            pass  # Session might already exist

        cascade_id = db.create_cascade(
            session_id=session_id,
            task=f"PREFLIGHT: {prompt}",
            context={"phase": "preflight", "prompt": prompt}
        )

        db.close()
        
        # Automatic git checkpoint creation (Phase 1: Git Automation)
        try:
            from empirica.core.canonical.empirica_git import auto_checkpoint
            
            no_git = getattr(args, 'no_git', False)
            checkpoint_hash = auto_checkpoint(
                session_id=session_id,
                ai_id=ai_id,
                phase='PREFLIGHT',
                vectors=vectors,
                round_num=1,
                metadata={
                    'recommended_action': recommendation['action'],
                    'cascade_id': cascade_id
                },
                no_git_flag=no_git
            )
            
            if checkpoint_hash:
                logger.debug(f"Git checkpoint created: {checkpoint_hash[:8]}")
        except Exception as e:
            # Safe degradation - don't fail CASCADE if checkpoint fails
            logger.debug(f"Checkpoint creation skipped: {e}")
        
        # Sign assessment if --sign flag provided (Phase 2: EEP-1)
        signature_data = None
        if getattr(args, 'sign', False):
            try:
                from empirica.core.identity import AIIdentity, sign_assessment
                import subprocess
                
                identity = AIIdentity(ai_id)
                identity.load_keypair()
                
                # Get cascade trace hash from git
                cascade_trace_hash = ""
                try:
                    result = subprocess.run(
                        ['git', 'log', '--pretty=format:%H', '-n', '100'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        cascade_trace_hash = hashlib.sha256(result.stdout.encode()).hexdigest()
                except Exception:
                    pass
                
                # Sign the assessment
                signature_data = sign_assessment(
                    content=str(assessment),
                    epistemic_state=vectors,
                    identity=identity,
                    cascade_trace_hash=cascade_trace_hash,
                    session_id=session_id
                )
                
                logger.info(f"✓ Assessment signed with EEP-1 (public_key={identity.public_key_hex()[:16]}...)")
                
            except FileNotFoundError:
                logger.error(f"❌ Identity not found for {ai_id}. Create with: empirica identity-create --ai-id {ai_id}")
            except Exception as e:
                logger.error(f"Signing failed: {e}")
        
        # Format output based on requested format
        # Default is JSON for programmatic use (AI→CLI→storage)
        # --output human for inspection/debugging
        output_format = getattr(args, 'output_format', None) or getattr(args, 'output', 'json')

        json_output = output_format == 'json' or getattr(args, 'json', False)
        human_output = output_format == 'human'

        if json_output:
            output = {
                "session_id": session_id,
                "task": prompt,
                "timestamp": datetime.utcnow().isoformat(),
                "vectors": vectors,
                "recommendation": _get_recommendation(vectors)
            }
            if signature_data:
                output['signature'] = signature_data
            logger.info(json.dumps(output, indent=2))
        
        elif human_output or getattr(args, 'compact', False):
            # Single-line key=value format
            if getattr(args, 'compact', False):
                parts = [f"SESSION={session_id}"]
                for key, value in vectors.items():
                    parts.append(f"{key.upper()}={value:.2f}")
                parts.append(f"RECOMMEND={_get_recommendation(vectors)['action']}")
                logger.info(" ".join(parts))

        elif getattr(args, 'kv', False):
            # Multi-line key=value format
            logger.info(f"session_id={session_id}")
            logger.info(f"task={prompt}")
            logger.info(f"timestamp={datetime.utcnow().isoformat()}")
            for key, value in vectors.items():
                logger.info(f"{key}={value:.2f}")
            logger.info(f"recommendation={_get_recommendation(vectors)['action']}")

        else:
            # Human-friendly format (interactive default with --output human or --interactive)
            logger.info("📊 Epistemic Vectors:")
            
            # Tier 1: Foundation
            logger.info("\n  🏛️  TIER 1: Foundation (35% weight)")
            logger.info(f"    • KNOW:    {vectors.get('know', 0.5):.2f}  {_interpret_score(vectors.get('know', 0.5), 'knowledge')}")
            logger.info(f"    • DO:      {vectors.get('do', 0.5):.2f}  {_interpret_score(vectors.get('do', 0.5), 'capability')}")
            logger.info(f"    • CONTEXT: {vectors.get('context', 0.5):.2f}  {_interpret_score(vectors.get('context', 0.5), 'information')}")
            
            # Tier 2: Comprehension
            logger.info("\n  🧠 TIER 2: Comprehension (30% weight)")
            logger.info(f"    • CLARITY:    {vectors.get('clarity', 0.5):.2f}  {_interpret_score(vectors.get('clarity', 0.5), 'clarity')}")
            logger.info(f"    • COHERENCE:  {vectors.get('coherence', 0.5):.2f}  {_interpret_score(vectors.get('coherence', 0.5), 'coherence')}")
            logger.info(f"    • SIGNAL:     {vectors.get('signal', 0.5):.2f}  {_interpret_score(vectors.get('signal', 0.5), 'signal')}")
            logger.info(f"    • DENSITY:    {vectors.get('density', 0.5):.2f}  {_interpret_score(vectors.get('density', 0.5), 'density')}")
            
            # Tier 3: Execution
            logger.info("\n  ⚡ TIER 3: Execution (25% weight)")
            logger.info(f"    • STATE:      {vectors.get('state', 0.5):.2f}  {_interpret_score(vectors.get('state', 0.5), 'state')}")
            logger.info(f"    • CHANGE:     {vectors.get('change', 0.5):.2f}  {_interpret_score(vectors.get('change', 0.5), 'change')}")
            logger.info(f"    • COMPLETION: {vectors.get('completion', 0.5):.2f}  {_interpret_score(vectors.get('completion', 0.5), 'completion')}")
            logger.info(f"    • IMPACT:     {vectors.get('impact', 0.5):.2f}  {_interpret_score(vectors.get('impact', 0.5), 'impact')}")
            
            # Meta-cognitive
            logger.info("\n  🎯 Meta-Cognitive (10% weight)")
            logger.info(f"    • ENGAGEMENT:  {vectors.get('engagement', 0.5):.2f}  {_interpret_score(vectors.get('engagement', 0.5), 'engagement')}")
            logger.info(f"    • UNCERTAINTY: {vectors.get('uncertainty', 0.5):.2f}  {_interpret_score(vectors.get('uncertainty', 0.5), 'uncertainty')}")
            
            # Recommendation
            recommendation = _get_recommendation(vectors)
            logger.info(f"\n💡 Recommendation: {recommendation['message']}")
            logger.info(f"   Action: {recommendation['action']}")
            
            if recommendation['warnings']:
                logger.info("\n⚠️  Warnings:")
                for warning in recommendation['warnings']:
                    logger.info(f"   • {warning}")
            
            logger.info(f"\n🆔 Session ID: {session_id}")
            logger.info(f"💾 Use this ID for postflight: empirica postflight {session_id}")
        
    except Exception as e:
        handle_cli_error(e, "Preflight assessment", getattr(args, 'verbose', False))


def handle_postflight_command(args):
    """
    DEPRECATED: This handler is no longer used.

    Postflight is now integrated into the non-blocking MCP v2 workflow.
    Use 'empirica postflight' which calls handle_postflight_submit_command.

    This function is kept for reference only.
    """
    print("⚠️  Internal handler deprecated - use handle_postflight_submit_command instead")
    return


def handle_workflow_command(args):
    """Execute full workflow: preflight → work → postflight"""
    try:
        print_header("🔄 Full Workflow")
        
        prompt = args.prompt
        session_id = str(uuid.uuid4())  # Full UUID, no truncation
        
        print(f"📋 Task: {prompt}")
        print(f"🆔 Session ID: {session_id}\n")
        
        # Step 1: Preflight
        print("=" * 60)
        print("STEP 1: PREFLIGHT ASSESSMENT")
        print("=" * 60)
        
        # Preflight - GENUINE self-assessment required
        # Workflow command is for demonstration purposes
        # For genuine epistemic tracking, use MCP server or individual preflight/postflight commands
        print("\n⚠️  Workflow command uses simplified flow for demonstration.")
        print("For genuine epistemic tracking, use MCP server or:")
        print("  1. empirica preflight \"task\" --assessment-json '{...}'")
        print("  2. [perform work]")
        print("  3. empirica postflight <session> --assessment-json '{...}'")
        print("\nSkipping genuine self-assessment for workflow demo...")
        
        vectors = None  # No assessment in workflow demo mode
        
        if vectors is None:
            print("\n⏭️  Skipping preflight assessment (demo mode)")
            recommendation = {"action": "proceed_cautiously", "message": "Demo mode - no genuine assessment"}
        
        if vectors:
            print(f"\n📊 Epistemic State: KNOW={vectors.get('know', 0.5):.2f}, DO={vectors.get('do', 0.5):.2f}, CONTEXT={vectors.get('context', 0.5):.2f}")
        print(f"💡 Recommendation: {recommendation['message']}")
        
        if recommendation['action'] == 'investigate':
            print("\n⚠️  Investigation recommended before proceeding")
            print("   Low confidence areas detected - gather more information first")
        
        # Step 2: User performs work (we can't automate this)
        print("\n" + "=" * 60)
        print("STEP 2: WORK ON TASK")
        print("=" * 60)
        print("\n⏸️  Pausing workflow - perform your task now")
        print("   When complete, workflow will continue to postflight...\n")
        
        if not args.auto:
            input("Press Enter when task is complete...")
        
        # Step 3: Postflight
        print("\n" + "=" * 60)
        print("STEP 3: POSTFLIGHT ASSESSMENT")
        print("=" * 60)
        
        # Postflight - skip in demo mode
        print("\n⏭️  Skipping postflight assessment (demo mode)")
        postflight_vectors = None
        delta = None
        calibration = None
        
        if postflight_vectors:
            print(f"\n📊 Epistemic State: KNOW={postflight_vectors.get('know', 0.5):.2f}, DO={postflight_vectors.get('do', 0.5):.2f}, CONTEXT={postflight_vectors.get('context', 0.5):.2f}")
        
        if delta:
            learning = _summarize_learning(delta)
            if learning['improvements']:
                print(f"✅ Learning: {', '.join(learning['improvements'])}")
        
        if calibration:
            status_icon = "✅" if calibration['well_calibrated'] else "⚠️"
            print(f"{status_icon} Calibration: {calibration['status']}")
        
        print(f"\n🎉 Workflow complete! Session ID: {session_id}")
        
    except Exception as e:
        handle_cli_error(e, "Workflow execution", getattr(args, 'verbose', False))


# Helper functions
def _get_cascade_profile_thresholds():
    """Get cascade-specific thresholds from investigation profiles"""
    try:
        from empirica.config.profile_loader import ProfileLoader
        
        loader = ProfileLoader()
        universal = loader.universal_constraints
        
        try:
            profile = loader.get_profile('balanced')
            constraints = profile.constraints
            
            # Get display thresholds from nested structure
            display_thresholds = getattr(constraints, 'display_thresholds', {})
            
            return {
                'excellent_threshold': display_thresholds.get('score_excellent', 0.8),
                'good_threshold': display_thresholds.get('score_good', 0.6),
                'moderate_threshold': display_thresholds.get('score_moderate', 0.4),
                'low_threshold': display_thresholds.get('score_basic', 0.2),
            }
        except:
            return {'excellent_threshold': 0.8, 'good_threshold': 0.6, 'moderate_threshold': 0.4, 'low_threshold': 0.2}
    except Exception:
        return {'excellent_threshold': 0.8, 'good_threshold': 0.6, 'moderate_threshold': 0.4, 'low_threshold': 0.2}

def _interpret_score(score, category):
    """Interpret a vector score with human-friendly description using profile-based thresholds"""
    thresholds = _get_cascade_profile_thresholds()
    
    if score >= thresholds['excellent_threshold']:
        return "(excellent)"
    elif score >= thresholds['good_threshold']:
        return "(good)"
    elif score >= thresholds['moderate_threshold']:
        return "(moderate)"
    elif score >= thresholds['low_threshold']:
        return "(low)"
    else:
        return "(very low)"




def _get_recommendation(vectors):
    """
    Get recommendation based on epistemic vectors.

    Delegates to centralized decision_utils.get_recommendation_from_vectors()
    for single source of truth.
    """
    return get_recommendation_from_vectors(vectors)


def _calculate_vector_delta(preflight, postflight):
    """Calculate epistemic delta between preflight and postflight"""
    delta = {}
    for key in postflight:
        pre = preflight.get(key, 0.5)
        post = postflight[key]
        delta[key] = post - pre
    return delta


def _assess_calibration(preflight, postflight):
    """Assess calibration quality"""
    # Calculate confidence (weighted average of foundation + comprehension)
    def calc_confidence(v):
        foundation = (v.get('know', 0.5) + v.get('do', 0.5) + v.get('context', 0.5)) / 3
        comprehension = (v.get('clarity', 0.5) + v.get('coherence', 0.5) + v.get('signal', 0.5) + v.get('density', 0.5)) / 4
        return foundation * 0.6 + comprehension * 0.4
    
    pre_conf = calc_confidence(preflight)
    post_conf = calc_confidence(postflight)
    
    pre_unc = preflight.get('uncertainty', 0.5)
    post_unc = postflight.get('uncertainty', 0.5)
    
    conf_increased = post_conf > pre_conf
    unc_decreased = post_unc < pre_unc
    
    if conf_increased and unc_decreased:
        status = "well_calibrated"
        note = "Confidence increased and uncertainty decreased - genuine learning"
    elif conf_increased and not unc_decreased:
        status = "overconfident"
        note = "Confidence increased but uncertainty didn't decrease - possible overconfidence"
    elif not conf_increased and unc_decreased:
        status = "underconfident"
        note = "Uncertainty decreased but confidence didn't increase - possible underconfidence"
    else:
        status = "stable"
        note = "Minimal change in confidence/uncertainty"
    
    return {
        "well_calibrated": status == "well_calibrated",
        "status": status,
        "note": note,
        "pre_confidence": round(pre_conf, 3),
        "post_confidence": round(post_conf, 3),
        "confidence_delta": round(post_conf - pre_conf, 3),
        "pre_uncertainty": round(pre_unc, 3),
        "post_uncertainty": round(post_unc, 3),
        "uncertainty_delta": round(post_unc - pre_unc, 3)
    }


def _summarize_learning(delta):
    """Summarize learning from delta"""
    improvements = []
    regressions = []
    
    for key, value in delta.items():
        if value > 0.1:
            improvements.append(f"{key} +{value:.2f}")
        elif value < -0.1:
            regressions.append(f"{key} {value:.2f}")
    
    return {
        "improvements": improvements,
        "regressions": regressions
    }


def _print_vector_with_delta(name, value, delta):
    """Print vector with delta if available"""
    delta_str = ""
    if delta and name.lower() in delta:
        d = delta[name.lower()]
        if d > 0.05:
            delta_str = f" (↗ +{d:.2f})"
        elif d < -0.05:
            delta_str = f" (↘ {d:.2f})"
        else:
            delta_str = f" (→ {d:+.2f})"
    
    print(f"    • {name:12s} {value:.2f}{delta_str}  {_interpret_score(value, name.lower())}")