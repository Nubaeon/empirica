"""
Investigation Commands - Analysis, investigation, and exploration functionality
"""

import os
import json
from ..cli_utils import print_component_status, handle_cli_error, parse_json_safely


def handle_investigate_command(args):
    """Handle investigation command for analyzing files, directories, or concepts"""
    try:
        from empirica.components.code_intelligence_analyzer import CodeIntelligenceAnalyzer
        from empirica.components.workspace_awareness import WorkspaceNavigator
        
        target = args.target
        print(f"🔍 Investigating: {target}")
        
        # Determine investigation type
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
    """Handle general analysis command"""
    try:
        from empirica.components.empirical_performance_analyzer import EmpiricalPerformanceAnalyzer
        
        print(f"📊 Analyzing: {args.subject}")
        
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
            print("📏 Analysis dimensions:")
            for dimension, score in result['dimensions'].items():
                status = "✅" if score > 0.7 else "⚠️" if score > 0.5 else "❌"
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
        from empirica.core.metacognition_12d_monitor import ComprehensiveSelfAwarenessAssessment
        
        evaluator = MetaCognitiveEvaluator()
        context_data = parse_json_safely(context)
        
        result = evaluator.investigate_concept(concept, context_data)
        
        return {
            "type": "concept",
            "summary": result.get('summary', f"Investigation of concept: {concept}"),
            "findings": result.get('insights', []),
            "metrics": result.get('confidence_metrics', {}),
            "recommendations": result.get('recommendations', [])
        }
        
    except Exception as e:
        return {"error": str(e), "type": "concept"}