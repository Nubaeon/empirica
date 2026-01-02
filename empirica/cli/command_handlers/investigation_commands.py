"""
Investigation Commands - Analysis, investigation, and exploration functionality
"""

import os
import json
from ..cli_utils import print_component_status, handle_cli_error, parse_json_safely


def _get_recalibration_attempts(session_id: str) -> int:
    """
    Get the number of recalibration attempts in this session.
    
    Prevents infinite INVESTIGATE loops by tracking how many times
    we've tried to recalibrate after drift detection.
    
    Returns: Number of attempts (0 if session not found)
    """
    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()
        session_data = db.get_session(session_id)
        
        if not session_data:
            return 0
        
        # Count CHECK commands with 'investigate' decision in this session
        # This is tracked in the reflexes table
        from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
        git_logger = GitEnhancedReflexLogger(session_id=session_id, enable_git_notes=True)
        checkpoints = git_logger.list_checkpoints(limit=100)
        
        investigate_count = 0
        for checkpoint in checkpoints:
            if checkpoint and checkpoint.get('metadata', {}).get('decision') == 'investigate':
                investigate_count += 1
        
        return investigate_count
    except Exception:
        return 0


def _get_profile_thresholds():
    """Get thresholds from investigation profiles instead of using hardcoded values"""
    try:
        from empirica.config.profile_loader import ProfileLoader
        
        loader = ProfileLoader()
        universal = loader.universal_constraints
        
        try:
            profile = loader.get_profile('balanced')
            constraints = profile.constraints
            
            return {
                'confidence_low': getattr(constraints, 'confidence_low_threshold', 0.5),
                'confidence_high': getattr(constraints, 'confidence_high_threshold', 0.7),
                'engagement_gate': universal.engagement_gate,
                'coherence_min': universal.coherence_min,
            }
        except:
            return {
                'confidence_low': 0.5, 
                'confidence_high': 0.7,
                'engagement_gate': universal.engagement_gate,
                'coherence_min': universal.coherence_min,
            }
    except Exception:
        return {
            'confidence_low': 0.5, 
            'confidence_high': 0.7,
            'engagement_gate': 0.6,
            'coherence_min': 0.5,
        }


def handle_investigate_command(args):
    """Handle investigation command (consolidates investigate + analyze)
    
    For NOETIC RECALIBRATION:
    - If session-id provided, automatically load project-bootstrap first
    - Bootstrap provides context anchor (findings, unknowns, goals)
    - Investigation then rebuilds understanding from that anchor
    """
    try:
        # Check if this is a comprehensive analysis (replaces old 'analyze' command)
        investigation_type = getattr(args, 'type', 'auto')
        if investigation_type == 'comprehensive':
            # Redirect to comprehensive analysis
            return handle_analyze_command(args)

        # For NOETIC RECALIBRATION: Load bootstrap context if session provided
        session_id = getattr(args, 'session_id', None)
        bootstrap_context = {}
        recalibration_attempt = 0
        
        if session_id:
            # Check recalibration attempt count to prevent infinite loops
            recalibration_attempt = _get_recalibration_attempts(session_id)
            
            if recalibration_attempt >= 3:
                print(f"⚠️  Recalibration attempt limit reached ({recalibration_attempt})")
                print(f"   Consider: pausing investigation, taking a snapshot, or starting fresh")
                print(f"   Further investigation may not resolve drift")
                return None
            
            try:
                import subprocess
                result = subprocess.run(
                    ['empirica', 'project-bootstrap', '--session-id', session_id, '--output', 'json'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    bootstrap_data = json.loads(result.stdout)
                    bootstrap_context = bootstrap_data.get('breadcrumbs', {})
                    print(f"📦 Loaded context anchor from bootstrap (attempt {recalibration_attempt + 1}/3)")
                    print(f"   Findings: {len(bootstrap_context.get('findings', []))}")
                    print(f"   Unknowns: {len(bootstrap_context.get('unknowns', []))}")
                    print(f"   Goals: {len(bootstrap_context.get('goals', []))}")
            except Exception as e:
                # Bootstrap failure is non-fatal
                pass

        from empirica.components.code_intelligence_analyzer import CodeIntelligenceAnalyzer
        from empirica.components.workspace_awareness import WorkspaceNavigator

        target = args.target
        print(f"🔍 Investigating: {target}")

        # Determine investigation type
        if investigation_type == 'auto':
            # Auto-detect based on target
            if os.path.exists(target):
                if os.path.isfile(target):
                    result = _investigate_file(target, getattr(args, 'verbose', False))
                elif os.path.isdir(target):
                    result = _investigate_directory(target, getattr(args, 'verbose', False))
                else:
                    result = {"error": "Target exists but is neither file nor directory"}
            else:
                # Treat as concept investigation
                result = _investigate_concept(target, getattr(args, 'context', None), getattr(args, 'verbose', False))
        elif investigation_type == 'file':
            result = _investigate_file(target, getattr(args, 'verbose', False))
        elif investigation_type == 'directory':
            result = _investigate_directory(target, getattr(args, 'verbose', False))
        elif investigation_type == 'concept':
            result = _investigate_concept(target, getattr(args, 'context', None), getattr(args, 'verbose', False))
        else:
            result = {"error": f"Unknown investigation type: {investigation_type}"}
        
        # Display results
        print(f"✅ Investigation complete")
        print(f"   🎯 Target: {target}")
        print(f"   📊 Type: {result.get('type', 'unknown')}")
        
        if result.get('summary'):
            print(f"   📝 Summary: {result['summary']}")
        
        if result.get('findings'):
            print("🔍 Key findings:")
            for finding in result['findings'][:5]:  # Show top 5
                print(f"   • {finding}")
        
        if result.get('metrics'):
            print("📊 Metrics:")
            for metric, value in result['metrics'].items():
                print(f"   • {metric}: {value}")
        
        if result.get('recommendations'):
            print("💡 Recommendations:")
            for rec in result['recommendations']:
                print(f"   • {rec}")
        
        if result.get('error'):
            print(f"❌ Investigation error: {result['error']}")

        # Format output based on requested format
        output_format = getattr(args, 'output', 'default')
        if output_format == 'json':
            print(json.dumps(result, indent=2))

        # Return None to avoid exit code issues and duplicate output
        return None

    except Exception as e:
        handle_cli_error(e, "Investigation", getattr(args, 'verbose', False))


def handle_analyze_command(args):
    """Handle comprehensive analysis (called from investigate --type=comprehensive)"""
    try:
        from empirica.components.empirical_performance_analyzer import EmpiricalPerformanceAnalyzer

        # Support both 'subject' (old analyze) and 'target' (new investigate)
        subject = getattr(args, 'subject', None) or getattr(args, 'target', 'unknown')
        print(f"📊 Analyzing: {subject}")
        
        analyzer = EmpiricalPerformanceAnalyzer()
        context = parse_json_safely(getattr(args, 'context', None))
        
        # Run comprehensive analysis
        result = analyzer.analyze(
            subject=args.subject,
            context=context,
            analysis_type=getattr(args, 'type', 'general'),
            detailed=getattr(args, 'detailed', False)
        )
        
        print(f"✅ Analysis complete")
        print(f"   🎯 Subject: {args.subject}")
        print(f"   📊 Analysis type: {result.get('analysis_type', 'general')}")
        print(f"   🏆 Score: {result.get('score', 0):.2f}")
        
        # Show analysis dimensions
        if result.get('dimensions'):
            thresholds = _get_profile_thresholds()
            print("📏 Analysis dimensions:")
            for dimension, score in result['dimensions'].items():
                status = "✅" if score > thresholds['confidence_high'] else "⚠️" if score > thresholds['confidence_low'] else "❌"
                print(f"   {status} {dimension}: {score:.2f}")
        
        # Show insights
        if result.get('insights'):
            print("💭 Insights:")
            for insight in result['insights']:
                print(f"   • {insight}")
        
        # Show detailed breakdown if requested
        if getattr(args, 'detailed', False) and result.get('detailed_breakdown'):
            print("🔍 Detailed breakdown:")
            for category, details in result['detailed_breakdown'].items():
                print(f"   📂 {category}:")
                if isinstance(details, dict):
                    for key, value in details.items():
                        print(f"     • {key}: {value}")
                else:
                    print(f"     {details}")

        # Format output based on requested format
        output_format = getattr(args, 'output', 'default')
        if output_format == 'json':
            print(json.dumps(result, indent=2))

        # Return None to avoid exit code issues and duplicate output
        return None

    except Exception as e:
        handle_cli_error(e, "Analysis", getattr(args, 'verbose', False))


def _investigate_file(file_path: str, verbose: bool = False) -> dict:
    """Investigate a specific file"""
    try:
        from empirica.components.code_intelligence_analyzer import CodeIntelligenceAnalyzer
        
        analyzer = CodeIntelligenceAnalyzer()
        result = analyzer.analyze_file(file_path)
        
        return {
            "type": "file",
            "summary": result.get('summary', f"Analysis of {os.path.basename(file_path)}"),
            "findings": result.get('key_findings', []),
            "metrics": result.get('metrics', {}),
            "recommendations": result.get('recommendations', [])
        }
        
    except Exception as e:
        return {"error": str(e), "type": "file"}


def _investigate_directory(dir_path: str, verbose: bool = False) -> dict:
    """Investigate a directory structure"""
    try:
        from empirica.components.workspace_awareness import WorkspaceNavigator
        
        workspace = WorkspaceAwareness()
        result = workspace.analyze_directory(dir_path)
        
        return {
            "type": "directory",
            "summary": result.get('summary', f"Analysis of {os.path.basename(dir_path)}"),
            "findings": result.get('structure_insights', []),
            "metrics": result.get('metrics', {}),
            "recommendations": result.get('recommendations', [])
        }
        
    except Exception as e:
        return {"error": str(e), "type": "directory"}


def _investigate_concept(concept: str, context: str = None, verbose: bool = False) -> dict:
    """Investigate a concept or abstract idea"""
    try:
        # NOTE: EpistemicAssessor moved to empirica-sentinel repo
        context_data = parse_json_safely(context)
        
        # Use available method or create mock result
        result = {
            'summary': f"Concept investigation: {concept}",
            'insights': [f"Analyzing concept: {concept}"],
            'confidence_metrics': {'analysis_depth': 0.7},
            'recommendations': ['Further investigation recommended']
        }
        
        return {
            "type": "concept",
            "summary": result.get('summary', f"Investigation of concept: {concept}"),
            "findings": result.get('insights', []),
            "metrics": result.get('confidence_metrics', {}),
            "recommendations": result.get('recommendations', [])
        }
        
    except Exception as e:
        return {"error": str(e), "type": "concept"}


# ========== Epistemic Branching Commands ==========

def handle_investigate_create_branch_command(args):
    """Handle investigate-create-branch command - Create parallel investigation path"""
    try:
        from empirica.data.session_database import SessionDatabase

        session_id = args.session_id
        investigation_path = args.investigation_path
        description = getattr(args, 'description', None)
        preflight_vectors_str = args.preflight_vectors or "{}"

        # Parse epistemic vectors
        preflight_vectors = parse_json_safely(preflight_vectors_str)
        if not isinstance(preflight_vectors, dict):
            raise ValueError("Preflight vectors must be a JSON dict")

        db = SessionDatabase()

        # Generate branch names
        branch_name = f"investigate-{investigation_path}"
        git_branch_name = f"feature/investigate-{investigation_path}"

        # Create branch in database
        branch_id = db.create_branch(
            session_id=session_id,
            branch_name=branch_name,
            investigation_path=investigation_path,
            git_branch_name=git_branch_name,
            preflight_vectors=preflight_vectors
        )

        db.close()

        result = {
            "ok": True,
            "branch_id": branch_id,
            "branch_name": branch_name,
            "git_branch_name": git_branch_name,
            "investigation_path": investigation_path,
            "message": f"Created investigation branch: {git_branch_name}"
        }

        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Investigation branch created")
            print(f"   Branch: {git_branch_name}")
            print(f"   Path: {investigation_path}")
            print(f"   ID: {branch_id[:8]}...")
            if description:
                print(f"   Description: {description}")

        return result

    except Exception as e:
        handle_cli_error(e, "Create investigation branch", getattr(args, 'verbose', False))


def handle_investigate_checkpoint_branch_command(args):
    """Handle investigate-checkpoint-branch command - Checkpoint branch after investigation"""
    try:
        from empirica.data.session_database import SessionDatabase

        branch_id = args.branch_id
        postflight_vectors_str = args.postflight_vectors or "{}"
        tokens_spent = int(args.tokens_spent or 0)
        time_spent = int(args.time_spent or 0)

        # Parse vectors
        postflight_vectors = parse_json_safely(postflight_vectors_str)
        if not isinstance(postflight_vectors, dict):
            raise ValueError("Postflight vectors must be a JSON dict")

        db = SessionDatabase()

        # Checkpoint the branch
        success = db.checkpoint_branch(
            branch_id=branch_id,
            postflight_vectors=postflight_vectors,
            tokens_spent=tokens_spent,
            time_spent_minutes=time_spent
        )

        # Calculate merge score
        if success:
            score_data = db.calculate_branch_merge_score(branch_id)

        db.close()

        result = {
            "ok": success,
            "branch_id": branch_id,
            "tokens_spent": tokens_spent,
            "time_spent_minutes": time_spent,
            "merge_score": score_data.get('merge_score', 0),
            "quality": score_data.get('quality', 0),
            "confidence": score_data.get('confidence', 0),
            "message": f"Branch checkpointed with merge score: {score_data.get('merge_score', 0):.4f}"
        }

        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Branch checkpointed successfully")
            print(f"   Merge Score: {score_data.get('merge_score', 0):.4f}")
            print(f"   Quality: {score_data.get('quality', 0):.4f}")
            print(f"   Confidence: {score_data.get('confidence', 0):.4f}")
            print(f"   Uncertainty (dampener): {score_data.get('uncertainty_dampener', 0):.4f}")
            print(f"   Tokens spent: {tokens_spent}")
            print(f"   Time spent: {time_spent} minutes")

        return result

    except Exception as e:
        handle_cli_error(e, "Checkpoint investigation branch", getattr(args, 'verbose', False))


def handle_investigate_merge_branches_command(args):
    """Handle investigate-merge-branches command - Auto-merge best branch based on epistemic scores"""
    try:
        from empirica.data.session_database import SessionDatabase

        session_id = args.session_id
        investigation_round = int(getattr(args, 'round', 1) or 1)
        tag_losers = getattr(args, 'tag_losers', False)

        db = SessionDatabase()

        # Perform epistemic auto-merge
        merge_result = db.merge_branches(
            session_id=session_id,
            investigation_round=investigation_round
        )

        if "error" in merge_result:
            db.close()
            result = {
                "ok": False,
                "error": merge_result["error"]
            }
        else:
            # Tag losing branches as dead ends if --tag-losers flag
            dead_ends_logged = 0
            dead_ends_embedded = 0
            if tag_losers and merge_result.get("other_branches"):
                winning_name = merge_result["winning_branch_name"]
                winning_score = merge_result["winning_score"]
                winning_branch_id = merge_result["winning_branch_id"]

                # Get project_id for Qdrant embedding
                project_id = None
                try:
                    cursor = db.conn.cursor()
                    cursor.execute("SELECT project_id FROM sessions WHERE session_id = ?", (session_id,))
                    row = cursor.fetchone()
                    if row:
                        project_id = row[0]
                except Exception:
                    pass

                for loser in merge_result["other_branches"]:
                    loser_name = loser.get("branch_name", "unknown")
                    loser_score = loser.get("score", 0)
                    loser_branch_id = loser.get("branch_id")
                    score_diff = winning_score - loser_score
                    approach = f"Investigation branch: {loser_name}"
                    why_failed = (f"Lost epistemic merge to {winning_name} (score diff: {score_diff:.4f}). "
                                  f"Branch score: {loser_score:.4f} vs winner: {winning_score:.4f}")

                    # Log as dead end to database
                    dead_end_id = db.log_project_dead_end(
                        project_id=None,  # Will be resolved from session
                        session_id=session_id,
                        approach=approach,
                        why_failed=why_failed,
                        goal_id=None,
                        subtask_id=None
                    )
                    dead_ends_logged += 1

                    # Also embed to Qdrant for similarity search
                    if project_id:
                        try:
                            from empirica.core.qdrant.vector_store import embed_dead_end_with_branch_context
                            embedded = embed_dead_end_with_branch_context(
                                project_id=project_id,
                                dead_end_id=str(dead_end_id) if dead_end_id else f"{session_id}_{loser_branch_id}",
                                approach=approach,
                                why_failed=why_failed,
                                session_id=session_id,
                                branch_id=loser_branch_id,
                                winning_branch_id=winning_branch_id,
                                score_diff=score_diff,
                                preflight_vectors=loser.get("preflight_vectors"),
                                postflight_vectors=loser.get("postflight_vectors")
                            )
                            if embedded:
                                dead_ends_embedded += 1
                        except ImportError:
                            pass  # Qdrant not available

            db.close()

            result = {
                "ok": True,
                "winning_branch_id": merge_result["winning_branch_id"],
                "winning_branch_name": merge_result["winning_branch_name"],
                "winning_score": merge_result["winning_score"],
                "merge_decision_id": merge_result["merge_decision_id"],
                "other_branches": merge_result["other_branches"],
                "rationale": merge_result["rationale"],
                "message": f"Auto-merged {merge_result['winning_branch_name']} (score: {merge_result['winning_score']:.4f})",
                "dead_ends_logged": dead_ends_logged if tag_losers else None,
                "dead_ends_embedded": dead_ends_embedded if tag_losers else None
            }

        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            if result.get("ok"):
                print(f"Epistemic Auto-Merge Complete")
                print(f"   Winner: {merge_result['winning_branch_name']}")
                print(f"   Merge Score: {merge_result['winning_score']:.4f}")
                print(f"   Decision ID: {merge_result['merge_decision_id'][:8]}...")
                print(f"   Evaluated {len(merge_result['other_branches']) + 1} paths")
                print(f"   Rationale: {merge_result['rationale']}")
                if tag_losers and dead_ends_logged > 0:
                    embedded_info = f" ({dead_ends_embedded} embedded to Qdrant)" if dead_ends_embedded > 0 else ""
                    print(f"   Dead ends logged: {dead_ends_logged}{embedded_info}")
            else:
                print(f"Merge failed: {result.get('error')}")

        return result

    except Exception as e:
        handle_cli_error(e, "Merge investigation branches", getattr(args, 'verbose', False))


def handle_investigate_multi_command(args):
    """
    Multi-persona parallel investigation with epistemic auto-merge.

    Spawns parallel epistemic agents with different persona priors,
    then aggregates results using merge scoring.

    Usage:
        empirica investigate-multi --task "Review auth code" --personas security,ux --session-id <ID>
    """
    try:
        from empirica.data.session_database import SessionDatabase
        from empirica.core.agents import EpistemicAgentConfig, spawn_epistemic_agent
        from empirica.core.persona import PersonaManager

        session_id = args.session_id
        task = args.task
        personas_str = args.personas
        context = getattr(args, 'context', None)
        strategy = getattr(args, 'aggregate_strategy', 'epistemic-score')
        output_format = getattr(args, 'output', 'human')

        # Parse personas
        persona_ids = [p.strip() for p in personas_str.split(',')]

        # Load personas
        manager = PersonaManager()
        loaded_personas = {}
        for pid in persona_ids:
            try:
                loaded_personas[pid] = manager.load_persona(pid)
            except FileNotFoundError:
                # Fall back to general persona with modified name
                loaded_personas[pid] = None  # Will use default

        # Spawn agents for each persona
        db = SessionDatabase()
        branches = {}

        for pid in persona_ids:
            config = EpistemicAgentConfig(
                session_id=session_id,
                task=task,
                persona_id=pid,
                persona=loaded_personas.get(pid),
                investigation_path=f"multi-{pid}",
                parent_context=context
            )
            result = spawn_epistemic_agent(config, execute_fn=None)
            branches[pid] = {
                "branch_id": result.branch_id,
                "persona_id": pid,
                "preflight_vectors": result.preflight_vectors,
                "prompt": result.output
            }

        # Build response
        response = {
            "ok": True,
            "session_id": session_id,
            "task": task,
            "personas": persona_ids,
            "branches": branches,
            "aggregate_strategy": strategy,
            "next_steps": [
                f"Execute each agent's prompt (see branches[persona_id].prompt)",
                f"Report results: empirica agent-report --branch-id <ID> --postflight '<json>'",
                f"Aggregate: empirica agent-aggregate --session-id {session_id}"
            ]
        }

        db.close()

        # Output
        if output_format == 'json':
            # Don't include full prompts in JSON output (too verbose)
            json_response = {**response}
            for pid in json_response['branches']:
                json_response['branches'][pid]['prompt'] = f"[{len(branches[pid]['prompt'])} chars - use --output human to see]"
            print(json.dumps(json_response, indent=2))
        else:
            print(f"✅ Multi-Persona Investigation Started")
            print(f"   Task: {task}")
            print(f"   Personas: {', '.join(persona_ids)}")
            print(f"   Strategy: {strategy}")
            print(f"\n📋 Branches Created:")
            for pid, branch in branches.items():
                print(f"\n   [{pid}] Branch: {branch['branch_id'][:8]}...")
                print(f"   Priors: know={branch['preflight_vectors'].get('know', 0.5):.2f}, uncertainty={branch['preflight_vectors'].get('uncertainty', 0.5):.2f}")

            print(f"\n📝 Next Steps:")
            print(f"   1. Execute each agent prompt (shown below)")
            print(f"   2. Report: empirica agent-report --branch-id <ID> --postflight '<json>'")
            print(f"   3. Aggregate: empirica agent-aggregate --session-id {session_id}")

            # Show prompts
            for pid, branch in branches.items():
                print(f"\n{'='*60}")
                print(f"PROMPT FOR [{pid}] (branch: {branch['branch_id'][:8]}...)")
                print(f"{'='*60}")
                print(branch['prompt'][:1500] + "..." if len(branch['prompt']) > 1500 else branch['prompt'])

        return 0

    except Exception as e:
        handle_cli_error(e, "Multi-persona investigation", getattr(args, 'verbose', False))