"""
Cascade Commands - Metacognitive cascade and decision-making functionality
"""

import json
import uuid
from datetime import datetime
from ..cli_utils import print_component_status, handle_cli_error, format_uncertainty_output, parse_json_safely, print_header


def handle_cascade_command(args):
    """Handle main cascade command - THINK→UNCERTAINTY→INVESTIGATE→CHECK→ACT"""
    try:
        from empirica.plugins.modality_switcher.modality_switcher import ModalitySwitcher, RoutingPreferences, RoutingStrategy
        
        print(f"🔄 Running epistemic adaptive cascade: {args.question}")
        
        # Parse context and epistemic vectors from CLI args
        context = parse_json_safely(getattr(args, 'context', None)) or {}
        
        # Parse individual epistemic vectors if provided as CLI args
        epistemic_state = {}
        if hasattr(args, 'epistemic_state') and args.epistemic_state:
            epistemic_json = parse_json_safely(args.epistemic_state)
            if epistemic_json:
                epistemic_state.update(epistemic_json)
        else:
            # Check for individual vector args - need to handle differently based on the argument names
            vector_attrs = {
                'know': getattr(args, 'know', None),
                'do': getattr(args, 'do', None),
                'context': getattr(args, 'context_vec', None),  # Using the renamed argument 
                'uncertainty': getattr(args, 'uncertainty', None),
                'clarity': getattr(args, 'clarity', None),
                'coherence': getattr(args, 'coherence', None),
                'signal': getattr(args, 'signal', None),
                'density': getattr(args, 'density', None),
                'state': getattr(args, 'state', None),
                'change': getattr(args, 'change', None),
                'completion': getattr(args, 'completion', None),
                'impact': getattr(args, 'impact', None),
                'engagement': getattr(args, 'engagement', None)
            }
            
            for vector, value in vector_attrs.items():
                if value is not None:
                    try:
                        epistemic_state[vector] = float(value)
                    except (ValueError, TypeError):
                        pass  # Skip if not convertible to float
        
        # Determine routing strategy
        strategy = getattr(args, 'strategy', 'epistemic')
        force_adapter = getattr(args, 'adapter', None)
        max_cost = getattr(args, 'max_cost', 1.0)
        max_latency = getattr(args, 'max_latency', 30.0)
        min_quality = getattr(args, 'min_quality', 0.7)
        allow_fallback = not getattr(args, 'no_fallback', False)
        
        # Create routing preferences
        if force_adapter:
            routing_preferences = RoutingPreferences(
                force_adapter=force_adapter,
                max_cost_usd=max_cost,
                max_latency_sec=max_latency,
                min_quality_score=min_quality,
                allow_fallback=allow_fallback
            )
        elif strategy == 'cost':
            routing_preferences = RoutingPreferences(
                strategy=RoutingStrategy.COST,
                max_cost_usd=max_cost,
                max_latency_sec=max_latency,
                min_quality_score=min_quality,
                allow_fallback=allow_fallback
            )
        elif strategy == 'latency':
            routing_preferences = RoutingPreferences(
                strategy=RoutingStrategy.LATENCY,
                max_cost_usd=max_cost,
                max_latency_sec=max_latency,
                min_quality_score=min_quality,
                allow_fallback=allow_fallback
            )
        elif strategy == 'quality':
            routing_preferences = RoutingPreferences(
                strategy=RoutingStrategy.QUALITY,
                max_cost_usd=max_cost,
                max_latency_sec=max_latency,
                min_quality_score=min_quality,
                allow_fallback=allow_fallback
            )
        elif strategy == 'balanced':
            routing_preferences = RoutingPreferences(
                strategy=RoutingStrategy.BALANCED,
                max_cost_usd=max_cost,
                max_latency_sec=max_latency,
                min_quality_score=min_quality,
                allow_fallback=allow_fallback
            )
        else:  # Default to epistemic
            routing_preferences = RoutingPreferences(
                strategy=RoutingStrategy.EPISTEMIC,
                max_cost_usd=max_cost,
                max_latency_sec=max_latency,
                min_quality_score=min_quality,
                allow_fallback=allow_fallback
            )
        
        # Create and use modality switcher for routing decision and execution
        print("🎯 Determining optimal adapter...")
        switcher = ModalitySwitcher()
        decision = switcher.route_request(
            query=args.question,
            epistemic_state=epistemic_state,
            preferences=routing_preferences,
            context=context
        )
        
        print(f"   Selected: {decision.selected_adapter}")
        print(f"   Rationale: {decision.rationale}")
        print(f"   Estimated: ${decision.estimated_cost:.4f}, {decision.estimated_latency:.1f}s")
        
        if getattr(args, 'verbose', False):
            print(f"   Fallbacks: {decision.fallback_adapters}")
            if not getattr(args, 'yes', False):
                try:
                    response = input("   Proceed? [Y/n] ").lower()
                    if response and response not in ['y', 'yes']:
                        print("   ❌ Cancelled by user")
                        return
                except (EOFError, KeyboardInterrupt):
                    # Handle non-interactive mode (like when run from shell)
                    print("   ⏩ Proceeding (non-interactive mode)")
        
        # Execute the request using the switcher's execute_with_routing method
        result = switcher.execute_with_routing(
            query=args.question,
            epistemic_state=epistemic_state,
            preferences=routing_preferences,
            context=context,
            system="You are a helpful assistant with metacognitive awareness. Assess your knowledge state and provide appropriate responses.",
            temperature=0.7,
            max_tokens=1000
        )
        
        if hasattr(result, 'decision'):
            print(f"✅ Execution complete")
            print(f"   🎯 Decision: {result.decision}")
            print(f"   📊 Confidence: {result.confidence:.2f}")
            print(f"   💭 Rationale: {result.rationale[:100]}{'...' if len(result.rationale) > 100 else ''}")
            
            if getattr(args, 'verbose', False):
                print("   🧠 Vector References:")
                for vector, value in result.vector_references.items():
                    print(f"      📊 {vector}: {value:.2f}")
                
                print("   🚀 Suggested Actions:")
                for action in result.suggested_actions:
                    print(f"      • {action}")
        else:
            print(f"❌ Execution failed: {result.message if hasattr(result, 'message') else result}")
        
        # Show usage statistics if verbose
        if getattr(args, 'verbose', False):
            stats = switcher.get_usage_stats()
            print(f"📈 Usage Stats: {stats}")
        
    except Exception as e:
        handle_cli_error(e, "Cascade", getattr(args, 'verbose', False))


def handle_decision_command(args):
    """Handle decision-making command with uncertainty assessment"""
    try:
        from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade
        from empirica.calibration.adaptive_uncertainty_calibration import AdaptiveUncertaintyCalibration
        
        print(f"⚖️ Analyzing decision: {args.decision}")
        
        context = parse_json_safely(getattr(args, 'context', None))
        confidence_threshold = getattr(args, 'confidence_threshold', 0.7)
        
        # Run epistemic cascade for decision-making
        cascade_result = run_epistemic_cascade(
            task=f"Should I proceed with: {args.decision}",
            context=context or {},
            confidence_threshold=confidence_threshold
        )
        
        print(f"✅ Decision analysis complete")
        print(f"   🎯 Decision: {cascade_result.get('final_decision', 'INVESTIGATE')}")
        print(f"   📊 Confidence: {cascade_result.get('confidence', 0.0):.2f}")
        print(f"   ⚖️ Threshold: {confidence_threshold}")
        
        # Recommendation based on confidence
        meets_threshold = cascade_result.get('confidence', 0.0) >= confidence_threshold
        recommendation = "PROCEED" if meets_threshold else "INVESTIGATE FURTHER"
        emoji = "✅" if meets_threshold else "⚠️"
        
        print(f"   {emoji} Recommendation: {recommendation}")
        print(f"   💭 Reasoning: {cascade_result.get('reasoning', 'N/A')}")
        
        # Show epistemic state
        epistemic_state = cascade_result.get('epistemic_state', {})
        if epistemic_state and getattr(args, 'verbose', False):
            print("🧠 Epistemic State:")
            if 'know' in epistemic_state:
                print(f"   📚 KNOW: {epistemic_state['know']:.2f}")
            if 'do' in epistemic_state:
                print(f"   ⚡ DO: {epistemic_state['do']:.2f}")
            if 'context' in epistemic_state:
                print(f"   🌐 CONTEXT: {epistemic_state['context']:.2f}")
        
        # Show required actions or next steps
        if cascade_result.get('required_actions'):
            print("⚡ Next steps:")
            for action in cascade_result['required_actions']:
                print(f"   • {action}")
        
        # Show investigation history if verbose
        if getattr(args, 'verbose', False) and cascade_result.get('investigation_history'):
            print("🔍 Investigation history:")
            for i, investigation in enumerate(cascade_result['investigation_history'], 1):
                print(f"   {i}. {investigation.get('action', 'Unknown')}")
        
    except Exception as e:
        handle_cli_error(e, "Decision analysis", getattr(args, 'verbose', False))


def handle_preflight_command(args):
    """Execute preflight epistemic assessment before task"""
    try:
        print_header("🚀 Preflight Assessment")
        
        from empirica.core.canonical import CanonicalEpistemicAssessor
        from empirica.data.session_database import SessionDatabase
        
        prompt = args.prompt
        session_id = args.session_id or str(uuid.uuid4())[:8]
        
        # Execute preflight assessment
        assessor = CanonicalEpistemicAssessor(agent_id=session_id)
        
        print(f"📋 Task: {prompt}")
        print(f"🆔 Session ID: {session_id}")
        print(f"\n⏳ Assessing epistemic state...\n")
        
        # Get self-assessment prompt from canonical assessor
        import asyncio
        assessment_request = asyncio.run(assessor.assess(prompt, {}))
        
        if not isinstance(assessment_request, dict) or 'self_assessment_prompt' not in assessment_request:
            print("❌ Failed to generate self-assessment prompt")
            return
        
        # Check if AI self-assessment was provided via --assessment-json argument
        if hasattr(args, 'assessment_json') and args.assessment_json:
            # Parse the AI's genuine self-assessment
            try:
                # Check if it's a file path or inline JSON
                import os
                import json
                
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
                print(f"❌ Failed to parse self-assessment: {e}")
                return
        else:
            # Interactive mode: Display prompt and request assessment
            print("\n" + "=" * 70)
            print("GENUINE SELF-ASSESSMENT REQUIRED")
            print("=" * 70)
            print("\n⚠️  NO HEURISTICS. NO STATIC VALUES. NO CONFABULATION.")
            print("\nThis command requires genuine AI epistemic self-assessment.")
            print("\n📋 SELF-ASSESSMENT PROMPT:")
            print("=" * 70)
            print(assessment_request['self_assessment_prompt'])
            print("=" * 70)
            print("\n💡 HOW TO USE:")
            print("\nOption 1: MCP Server (Recommended for AI assistants)")
            print("  - Use MCP tools for genuine real-time self-assessment")
            print("  - See: docs/guides/MCP_CONFIGURATION_EXAMPLES.md")
            print("\nOption 2: CLI with --assessment-json")
            print("  - AI performs genuine self-assessment")
            print("  - Provide JSON response via --assessment-json flag")
            print("  - Example: empirica preflight \"task\" --assessment-json '{...}'")
            print("\nOption 3: Interactive (you are here)")
            print("  - Paste your genuine self-assessment as JSON when prompted")
            
            if not args.quiet:
                print("\n" + "=" * 70)
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
                        print(f"\n❌ Failed to parse assessment: {e}")
                        return
                else:
                    print("\n⚠️  Skipping preflight - no genuine assessment provided")
                    print("💡 Use MCP server for automated genuine self-assessment")
                    return
            else:
                print("\n⚠️  Cannot complete preflight in --quiet mode without --assessment-json")
                return
        
        # Store preflight in session database for postflight comparison
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase(db_path=".empirica/sessions/sessions.db")
        try:
            db.create_session(session_id, ai_id=session_id, started_at=datetime.utcnow())
        except:
            pass  # Session might already exist
        
        cascade_id = db.create_cascade(
            session_id=session_id,
            task=f"PREFLIGHT: {prompt}",
            context={"phase": "preflight", "prompt": prompt}
        )
        
        db.conn.execute("""
            INSERT INTO cascade_metadata (cascade_id, metadata_key, metadata_value)
            VALUES (?, ?, ?)
        """, (cascade_id, "preflight_vectors", json.dumps(vectors)))
        
        db.conn.commit()
        db.close()
        
        # Format output based on requested format
        if args.json:
            output = {
                "session_id": session_id,
                "task": prompt,
                "timestamp": datetime.utcnow().isoformat(),
                "vectors": vectors,
                "recommendation": _get_recommendation(vectors)
            }
            print(json.dumps(output, indent=2))
        
        elif args.compact:
            # Single-line key=value format
            parts = [f"SESSION={session_id}"]
            for key, value in vectors.items():
                parts.append(f"{key.upper()}={value:.2f}")
            parts.append(f"RECOMMEND={_get_recommendation(vectors)['action']}")
            print(" ".join(parts))
        
        elif args.kv:
            # Multi-line key=value format
            print(f"session_id={session_id}")
            print(f"task={prompt}")
            print(f"timestamp={datetime.utcnow().isoformat()}")
            for key, value in vectors.items():
                print(f"{key}={value:.2f}")
            print(f"recommendation={_get_recommendation(vectors)['action']}")
        
        else:
            # Human-friendly format (default)
            print("📊 Epistemic Vectors:")
            
            # Tier 1: Foundation
            print("\n  🏛️  TIER 1: Foundation (35% weight)")
            print(f"    • KNOW:    {vectors.get('know', 0.5):.2f}  {_interpret_score(vectors.get('know', 0.5), 'knowledge')}")
            print(f"    • DO:      {vectors.get('do', 0.5):.2f}  {_interpret_score(vectors.get('do', 0.5), 'capability')}")
            print(f"    • CONTEXT: {vectors.get('context', 0.5):.2f}  {_interpret_score(vectors.get('context', 0.5), 'information')}")
            
            # Tier 2: Comprehension
            print("\n  🧠 TIER 2: Comprehension (30% weight)")
            print(f"    • CLARITY:    {vectors.get('clarity', 0.5):.2f}  {_interpret_score(vectors.get('clarity', 0.5), 'clarity')}")
            print(f"    • COHERENCE:  {vectors.get('coherence', 0.5):.2f}  {_interpret_score(vectors.get('coherence', 0.5), 'coherence')}")
            print(f"    • SIGNAL:     {vectors.get('signal', 0.5):.2f}  {_interpret_score(vectors.get('signal', 0.5), 'signal')}")
            print(f"    • DENSITY:    {vectors.get('density', 0.5):.2f}  {_interpret_score(vectors.get('density', 0.5), 'density')}")
            
            # Tier 3: Execution
            print("\n  ⚡ TIER 3: Execution (25% weight)")
            print(f"    • STATE:      {vectors.get('state', 0.5):.2f}  {_interpret_score(vectors.get('state', 0.5), 'state')}")
            print(f"    • CHANGE:     {vectors.get('change', 0.5):.2f}  {_interpret_score(vectors.get('change', 0.5), 'change')}")
            print(f"    • COMPLETION: {vectors.get('completion', 0.5):.2f}  {_interpret_score(vectors.get('completion', 0.5), 'completion')}")
            print(f"    • IMPACT:     {vectors.get('impact', 0.5):.2f}  {_interpret_score(vectors.get('impact', 0.5), 'impact')}")
            
            # Meta-cognitive
            print("\n  🎯 Meta-Cognitive (10% weight)")
            print(f"    • ENGAGEMENT:  {vectors.get('engagement', 0.5):.2f}  {_interpret_score(vectors.get('engagement', 0.5), 'engagement')}")
            print(f"    • UNCERTAINTY: {vectors.get('uncertainty', 0.5):.2f}  {_interpret_score(vectors.get('uncertainty', 0.5), 'uncertainty')}")
            
            # Recommendation
            recommendation = _get_recommendation(vectors)
            print(f"\n💡 Recommendation: {recommendation['message']}")
            print(f"   Action: {recommendation['action']}")
            
            if recommendation['warnings']:
                print("\n⚠️  Warnings:")
                for warning in recommendation['warnings']:
                    print(f"   • {warning}")
            
            print(f"\n🆔 Session ID: {session_id}")
            print(f"💾 Use this ID for postflight: empirica postflight {session_id}")
        
    except Exception as e:
        handle_cli_error(e, "Preflight assessment", getattr(args, 'verbose', False))


def handle_postflight_command(args):
    """Execute postflight epistemic reassessment after task completion"""
    try:
        print_header("🏁 Postflight Assessment")
        
        from empirica.core.canonical import CanonicalEpistemicAssessor
        from empirica.data.session_database import SessionDatabase
        
        session_id = args.session_id
        summary = args.summary or "Task completed"
        
        print(f"🆔 Session ID: {session_id}")
        print(f"📋 Task Summary: {summary}")
        print(f"\n⏳ Reassessing epistemic state...\n")
        
        # Execute postflight assessment - GENUINE self-assessment required
        from empirica.core.canonical import CanonicalEpistemicAssessor
        assessor = CanonicalEpistemicAssessor(agent_id=session_id)
        
        import asyncio
        task_description = f"POSTFLIGHT: {summary}"
        assessment_request = asyncio.run(assessor.assess(task_description, {"phase": "postflight"}))
        
        if not isinstance(assessment_request, dict) or 'self_assessment_prompt' not in assessment_request:
            print("❌ Failed to generate self-assessment prompt")
            return
        
        # Check if AI self-assessment was provided
        if hasattr(args, 'assessment_json') and args.assessment_json:
            try:
                # Check if it's a file path or inline JSON
                import os
                import json
                
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
                    task_description,
                    {"phase": "postflight"}
                )
                postflight_vectors = {
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
                print(f"❌ Failed to parse self-assessment: {e}")
                return
        else:
            # Interactive mode
            print("\n" + "=" * 70)
            print("GENUINE POSTFLIGHT SELF-ASSESSMENT REQUIRED")
            print("=" * 70)
            print("\n⚠️  NO HEURISTICS. NO STATIC VALUES. NO CONFABULATION.")
            print("\n📋 SELF-ASSESSMENT PROMPT:")
            print("=" * 70)
            print(assessment_request['self_assessment_prompt'])
            print("=" * 70)
            print("\n💡 Provide genuine postflight self-assessment via --assessment-json")
            print("   or use MCP server for automated genuine assessment.")
            
            if not args.quiet:
                response = input("\nPaste your genuine postflight self-assessment JSON (or press Enter to skip): ")
                
                if response.strip():
                    try:
                        assessment = assessor.parse_llm_response(
                            response,
                            assessment_request['assessment_id'],
                            task_description,
                            {"phase": "postflight"}
                        )
                        postflight_vectors = {
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
                        print(f"\n❌ Failed to parse assessment: {e}")
                        return
                else:
                    print("\n⚠️  Skipping postflight - no genuine assessment provided")
                    return
            else:
                print("\n⚠️  Cannot complete postflight in --quiet mode without --assessment-json")
                return
        
        # Try to get preflight vectors for delta calculation
        db = SessionDatabase(db_path=".empirica/sessions/sessions.db")
        delta = None
        calibration = None
        
        try:
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT cm.metadata_value
                FROM cascade_metadata cm
                JOIN cascades c ON cm.cascade_id = c.cascade_id
                WHERE cm.metadata_key = 'preflight_vectors'
                AND c.session_id = ?
                ORDER BY c.started_at DESC
                LIMIT 1
            """, (session_id,))
            
            result = cursor.fetchone()
            if result:
                preflight_vectors = json.loads(result[0])
                delta = _calculate_vector_delta(preflight_vectors, postflight_vectors)
                calibration = _assess_calibration(preflight_vectors, postflight_vectors)
        except Exception as e:
            if args.verbose:
                print(f"⚠️  Could not calculate delta: {e}")
        finally:
            db.close()
        
        # Format output based on requested format
        if args.json:
            output = {
                "session_id": session_id,
                "summary": summary,
                "timestamp": datetime.utcnow().isoformat(),
                "vectors": postflight_vectors,
                "delta": delta,
                "calibration": calibration
            }
            print(json.dumps(output, indent=2))
        
        elif args.compact:
            parts = [f"SESSION={session_id}"]
            for key, value in postflight_vectors.items():
                parts.append(f"{key.upper()}={value:.2f}")
            if calibration:
                parts.append(f"CALIBRATED={calibration['well_calibrated']}")
            print(" ".join(parts))
        
        elif args.kv:
            print(f"session_id={session_id}")
            print(f"summary={summary}")
            print(f"timestamp={datetime.utcnow().isoformat()}")
            for key, value in postflight_vectors.items():
                print(f"{key}={value:.2f}")
            if delta:
                for key, value in delta.items():
                    print(f"delta_{key}={value:.2f}")
            if calibration:
                print(f"calibrated={calibration['well_calibrated']}")
        
        else:
            # Human-friendly format
            print("📊 Postflight Epistemic State:")
            
            # Show vectors with deltas if available
            print("\n  🏛️  TIER 1: Foundation")
            _print_vector_with_delta("KNOW", postflight_vectors.get('know', 0.5), delta)
            _print_vector_with_delta("DO", postflight_vectors.get('do', 0.5), delta)
            _print_vector_with_delta("CONTEXT", postflight_vectors.get('context', 0.5), delta)
            
            print("\n  🧠 TIER 2: Comprehension")
            _print_vector_with_delta("CLARITY", postflight_vectors.get('clarity', 0.5), delta)
            _print_vector_with_delta("COHERENCE", postflight_vectors.get('coherence', 0.5), delta)
            _print_vector_with_delta("SIGNAL", postflight_vectors.get('signal', 0.5), delta)
            _print_vector_with_delta("DENSITY", postflight_vectors.get('density', 0.5), delta)
            
            print("\n  ⚡ TIER 3: Execution")
            _print_vector_with_delta("STATE", postflight_vectors.get('state', 0.5), delta)
            _print_vector_with_delta("CHANGE", postflight_vectors.get('change', 0.5), delta)
            _print_vector_with_delta("COMPLETION", postflight_vectors.get('completion', 0.5), delta)
            _print_vector_with_delta("IMPACT", postflight_vectors.get('impact', 0.5), delta)
            
            print("\n  🎯 Meta-Cognitive")
            _print_vector_with_delta("ENGAGEMENT", postflight_vectors.get('engagement', 0.5), delta)
            _print_vector_with_delta("UNCERTAINTY", postflight_vectors.get('uncertainty', 0.5), delta)
            
            # Show learning summary
            if delta:
                print("\n📈 Learning Summary:")
                learning = _summarize_learning(delta)
                if learning['improvements']:
                    print(f"   ✅ Improved: {', '.join(learning['improvements'])}")
                if learning['regressions']:
                    print(f"   ⚠️  Decreased: {', '.join(learning['regressions'])}")
                if not learning['improvements'] and not learning['regressions']:
                    print(f"   ➖ Minimal change")
            
            # Show calibration
            if calibration:
                print("\n🎯 Calibration Analysis:")
                status_icon = "✅" if calibration['well_calibrated'] else "⚠️"
                print(f"   {status_icon} Status: {calibration['status']}")
                print(f"   📊 Confidence: {calibration['pre_confidence']:.2f} → {calibration['post_confidence']:.2f} ({calibration['confidence_delta']:+.2f})")
                print(f"   🤔 Uncertainty: {calibration['pre_uncertainty']:.2f} → {calibration['post_uncertainty']:.2f} ({calibration['uncertainty_delta']:+.2f})")
                print(f"   💡 {calibration['note']}")
            else:
                print("\n⚠️  No preflight baseline found - cannot assess calibration")
                print("   💡 Run 'empirica preflight' before starting tasks")
        
    except Exception as e:
        handle_cli_error(e, "Postflight assessment", getattr(args, 'verbose', False))


def handle_workflow_command(args):
    """Execute full workflow: preflight → work → postflight"""
    try:
        print_header("🔄 Full Workflow")
        
        prompt = args.prompt
        session_id = str(uuid.uuid4())[:8]
        
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
def _interpret_score(score, category):
    """Interpret a vector score with human-friendly description"""
    if score >= 0.8:
        return "(excellent)"
    elif score >= 0.6:
        return "(good)"
    elif score >= 0.4:
        return "(moderate)"
    elif score >= 0.2:
        return "(low)"
    else:
        return "(very low)"


def _get_recommendation(vectors):
    """Get recommendation based on epistemic vectors"""
    know = vectors.get('know', 0.5)
    do = vectors.get('do', 0.5)
    context = vectors.get('context', 0.5)
    uncertainty = vectors.get('uncertainty', 0.5)
    
    avg_foundation = (know + do + context) / 3.0
    
    warnings = []
    
    if know < 0.5:
        warnings.append("Low domain knowledge - consider research/investigation")
    if do < 0.5:
        warnings.append("Low task capability - proceed with caution or seek guidance")
    if context < 0.5:
        warnings.append("Insufficient context - gather more information")
    if uncertainty > 0.7:
        warnings.append("High uncertainty - investigation strongly recommended")
    
    if avg_foundation >= 0.7 and uncertainty < 0.5:
        return {
            "action": "proceed",
            "message": "Proceed with confidence",
            "warnings": warnings
        }
    elif avg_foundation >= 0.5:
        return {
            "action": "proceed_cautiously",
            "message": "Proceed with moderate supervision",
            "warnings": warnings
        }
    else:
        return {
            "action": "investigate",
            "message": "Investigation recommended before proceeding",
            "warnings": warnings
        }


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