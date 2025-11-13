"""
Assessment Commands - Self-awareness, metacognitive assessment, and evaluation
"""

import json
from ..cli_utils import print_component_status, handle_cli_error, format_uncertainty_output, parse_json_safely


def handle_assess_command(args):
    """Handle main assessment command"""
    try:
        from empirica.calibration.adaptive_uncertainty_calibration import AdaptiveUncertaintyCalibration
        
        print(f"🔍 Running uncertainty assessment: {args.query}")
        
        analyzer = UncertaintyAnalyzer()
        context = parse_json_safely(getattr(args, 'context', None))
        
        # Run comprehensive assessment
        result = analyzer.analyze_uncertainty(
            query=args.query,
            context=context,
            detailed=getattr(args, 'detailed', False)
        )
        
        print(f"✅ Assessment complete")
        print(f"   🎯 Overall confidence: {result.get('confidence', 0):.2f}")
        print(f"   📊 Uncertainty level: {result.get('uncertainty_level', 'unknown')}")
        print(f"   🧠 Vector count: {len(result.get('vectors', []))}")
        
        # Display uncertainty vectors
        if result.get('vectors'):
            print(format_uncertainty_output(
                {v['name']: v['value'] for v in result['vectors']},
                verbose=getattr(args, 'verbose', False)
            ))
        
        # Show recommendations if available
        if result.get('recommendations'):
            print("💡 Recommendations:")
            for rec in result['recommendations']:
                print(f"   • {rec}")
        
    except Exception as e:
        handle_cli_error(e, "Assessment", getattr(args, 'verbose', False))


def handle_self_awareness_command(args):
    """Handle self-awareness assessment command"""
    try:
        from empirica.core.metacognition_12d_monitor import ComprehensiveSelfAwarenessAssessment
        
        print("🧠 Running self-awareness assessment...")
        
        evaluator = MetaCognitiveEvaluator()
        
        # Get self-awareness metrics
        result = evaluator.assess_self_awareness(
            include_vectors=getattr(args, 'vectors', True),
            detailed=getattr(args, 'detailed', False)
        )
        
        print(f"✅ Self-awareness assessment complete")
        print(f"   🎯 Awareness level: {result.get('awareness_level', 'unknown')}")
        print(f"   📊 Metacognitive score: {result.get('metacognitive_score', 0):.2f}")
        print(f"   🧠 Vector coherence: {result.get('vector_coherence', 0):.2f}")
        
        # Show vector breakdown if requested
        if getattr(args, 'vectors', True) and result.get('vector_breakdown'):
            print("🔍 Vector breakdown:")
            for vector, score in result['vector_breakdown'].items():
                status = "✅" if score > 0.7 else "⚠️" if score > 0.5 else "❌"
                print(f"   {status} {vector}: {score:.2f}")
        
        # Show insights
        if result.get('insights') and getattr(args, 'verbose', False):
            print("💭 Self-awareness insights:")
            for insight in result['insights']:
                print(f"   • {insight}")
        
    except Exception as e:
        handle_cli_error(e, "Self-awareness assessment", getattr(args, 'verbose', False))


def handle_metacognitive_command(args):
    """Handle metacognitive evaluation command"""
    try:
        from empirica.core.metacognition_12d_monitor import ComprehensiveSelfAwarenessAssessment
        
        print(f"🤔 Running metacognitive evaluation: {args.task}")
        
        evaluator = MetaCognitiveEvaluator()
        context = parse_json_safely(getattr(args, 'context', None))
        
        # Run metacognitive evaluation
        result = evaluator.evaluate_metacognition(
            task=args.task,
            context=context,
            include_reasoning=getattr(args, 'reasoning', True)
        )
        
        print(f"✅ Metacognitive evaluation complete")
        print(f"   🎯 Task: {result.get('task', 'unknown')}")
        print(f"   📊 Metacognitive confidence: {result.get('confidence', 0):.2f}")
        print(f"   🧠 Reasoning quality: {result.get('reasoning_quality', 0):.2f}")
        
        # Show reasoning chain if available
        if getattr(args, 'reasoning', True) and result.get('reasoning_chain'):
            print("🔗 Reasoning chain:")
            for i, step in enumerate(result['reasoning_chain'], 1):
                print(f"   {i}. {step.get('step_type', 'unknown')}: {step.get('content', '')[:80]}...")
        
        # Show metacognitive insights
        if result.get('metacognitive_insights'):
            print("💡 Metacognitive insights:")
            for insight in result['metacognitive_insights']:
                print(f"   • {insight}")
        
        # Show uncertainty assessment if available
        if result.get('uncertainty_assessment'):
            uncertainty_output = format_uncertainty_output(
                result['uncertainty_assessment'],
                verbose=getattr(args, 'verbose', False)
            )
            print(uncertainty_output)
        
    except Exception as e:
        handle_cli_error(e, "Metacognitive evaluation", getattr(args, 'verbose', False))