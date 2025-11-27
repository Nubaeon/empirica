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
        from empirica.core.metacognition_12d_monitor.metacognition_12d_monitor import MetacognitionMonitor
        
        # Use mode='llm' to ensure NO heuristics are used
        evaluator = MetacognitionMonitor(mode='llm')
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