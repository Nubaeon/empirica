"""
Investigation Commands - Analysis, investigation, and exploration functionality
"""

import os
import json
from ..cli_utils import print_component_status, handle_cli_error, parse_json_safely


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
    """Handle investigation command (consolidates investigate + analyze)"""
    try:
        # Check if this is a comprehensive analysis (replaces old 'analyze' command)
        investigation_type = getattr(args, 'type', 'auto')
        if investigation_type == 'comprehensive':
            # Redirect to comprehensive analysis
            return handle_analyze_command(args)

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

        db = SessionDatabase()

        # Perform epistemic auto-merge
        merge_result = db.merge_branches(
            session_id=session_id,
            investigation_round=investigation_round
        )

        db.close()

        if "error" in merge_result:
            result = {
                "ok": False,
                "error": merge_result["error"]
            }
        else:
            result = {
                "ok": True,
                "winning_branch_id": merge_result["winning_branch_id"],
                "winning_branch_name": merge_result["winning_branch_name"],
                "winning_score": merge_result["winning_score"],
                "merge_decision_id": merge_result["merge_decision_id"],
                "other_branches": merge_result["other_branches"],
                "rationale": merge_result["rationale"],
                "message": f"Auto-merged {merge_result['winning_branch_name']} (score: {merge_result['winning_score']:.4f})"
            }

        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            if result.get("ok"):
                print(f"✅ Epistemic Auto-Merge Complete")
                print(f"   Winner: {merge_result['winning_branch_name']}")
                print(f"   Merge Score: {merge_result['winning_score']:.4f}")
                print(f"   Decision ID: {merge_result['merge_decision_id'][:8]}...")
                print(f"   Evaluated {len(merge_result['other_branches']) + 1} paths")
                print(f"   Rationale: {merge_result['rationale']}")
            else:
                print(f"❌ Merge failed: {result.get('error')}")

        return result

    except Exception as e:
        handle_cli_error(e, "Merge investigation branches", getattr(args, 'verbose', False))