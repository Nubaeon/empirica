"""
Assessment Commands - Self-awareness, metacognitive assessment, and evaluation
"""

import json
import time
from ..cli_utils import print_component_status, handle_cli_error, format_uncertainty_output, parse_json_safely


def _get_profile_thresholds():
    """Get thresholds from investigation profiles instead of using hardcoded values"""
    try:
        from empirica.config.profile_loader import ProfileLoader
        
        loader = ProfileLoader()
        # Use universal constraints as baseline
        universal = loader.universal_constraints
        
        # Try to get balanced profile as default
        try:
            profile = loader.get_profile('balanced')
            constraints = profile.constraints
            
            return {
                'uncertainty_low': getattr(constraints, 'uncertainty_low_threshold', 0.3),
                'uncertainty_high': getattr(constraints, 'uncertainty_high_threshold', 0.7), 
                'confidence_low': getattr(constraints, 'confidence_low_threshold', 0.5),
                'confidence_high': getattr(constraints, 'confidence_high_threshold', 0.7),
                'engagement_gate': universal.engagement_gate,
                'coherence_min': universal.coherence_min,
            }
        except:
            # Use universal constraints if profile fails
            return {
                'uncertainty_low': 0.3,
                'uncertainty_high': 0.7,
                'confidence_low': 0.5, 
                'confidence_high': 0.7,
                'engagement_gate': universal.engagement_gate,
                'coherence_min': universal.coherence_min,
            }
    except Exception:
        # Final fallback with warning
        print("⚠️ Could not load investigation profiles, using fallback thresholds")
        return {
            'uncertainty_low': 0.3,
            'uncertainty_high': 0.7,
            'confidence_low': 0.5, 
            'confidence_high': 0.7,
            'engagement_gate': 0.6,
            'coherence_min': 0.5,
        }


def handle_assess_command(args):
    """Handle main assessment command"""
    try:
        from empirica.calibration.adaptive_uncertainty_calibration.adaptive_uncertainty_calibration import AdaptiveUncertaintyCalibration
        
        print(f"🔍 Running uncertainty assessment: {args.query}")
        
        analyzer = AdaptiveUncertaintyCalibration()
        context = parse_json_safely(getattr(args, 'context', None))
        
        # Run comprehensive assessment
        decision_context = {
            'task': args.query,
            'context': context or {},
            'detailed': getattr(args, 'detailed', False),
            'timestamp': time.time()
        }
        result = analyzer.assess_uncertainty(decision_context)
        
        print(f"✅ Assessment complete")
        print(f"   🎯 Overall confidence: {result.calibrated_confidence:.2f}")
        print(f"   📊 Decision: {result.decision}")
        print(f"   🧠 Vector count: {len(result.vectors)}")
        print(f"   🎨 UVL Status: {result.uvl_color}")
        
        # Display uncertainty vectors
        if result.vectors:
            thresholds = _get_profile_thresholds()
            print("🔍 Uncertainty vectors:")
            for vector_name, uncertainty in result.vectors.items():
                status = "✅" if uncertainty < thresholds['uncertainty_low'] else "⚠️" if uncertainty < thresholds['uncertainty_high'] else "❌"
                print(f"   {status} {vector_name}: {uncertainty:.2f}")
        
        # Show recommendations if available
        if hasattr(result, 'recommendations') and result.recommendations:
            print("💡 Recommendations:")
            for rec in result.recommendations:
                print(f"   • {rec}")
        
    except Exception as e:
        handle_cli_error(e, "Assessment", getattr(args, 'verbose', False))


def handle_self_awareness_command(args):
    """Handle self-awareness assessment command"""
    try:
        from empirica.core.metacognition_12d_monitor.twelve_vector_self_awareness import TwelveVectorSelfAwareness
        
        print("🧠 Running self-awareness assessment...")
        
        evaluator = TwelveVectorSelfAwareness()
        
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
            thresholds = _get_profile_thresholds()
            print("🔍 Vector breakdown:")
            for vector, score in result['vector_breakdown'].items():
                status = "✅" if score > thresholds['confidence_high'] else "⚠️" if score > thresholds['confidence_low'] else "❌"
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
        from empirica.core.metacognition_12d_monitor.metacognition_12d_monitor import MetacognitionMonitor
        
        print(f"🤔 Running metacognitive evaluation: {args.task}")
        
        # Use mode='llm' to ensure NO heuristics are used
        evaluator = MetacognitionMonitor(mode='llm')
        context = parse_json_safely(getattr(args, 'context', None))
        
        # Run metacognitive evaluation
        result = evaluator.evaluate_metacognition(
            task=args.task,
            context=context or {},
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