"""
Decision Commands - CLI commands for epistemic decision-making with ModalitySwitcher

Provides interactive epistemic assessment and intelligent adapter routing.
"""

import json
import sys
from typing import Dict, Any, Optional

from empirica.plugins.modality_switcher.modality_switcher import (
    ModalitySwitcher,
    RoutingStrategy,
    RoutingPreferences
)
from empirica.plugins.modality_switcher.plugin_registry import AdapterResponse, AdapterError
from ..cli_utils import handle_cli_error


# 13 epistemic vectors with descriptions
EPISTEMIC_VECTORS = [
    ("know", "KNOW", "How well do you understand the problem domain?"),
    ("do", "DO", "Do you have the capability to execute this?"),
    ("context", "CONTEXT", "Do you have sufficient context and background?"),
    ("clarity", "CLARITY", "How clear is your understanding?"),
    ("coherence", "COHERENCE", "How internally consistent is your knowledge?"),
    ("signal", "SIGNAL", "Signal-to-noise ratio in available information?"),
    ("density", "DENSITY", "Information density and relevance?"),
    ("state", "STATE", "Current state assessment confidence?"),
    ("change", "CHANGE", "Expected changes and their predictability?"),
    ("completion", "COMPLETION", "Task completion likelihood estimate?"),
    ("impact", "IMPACT", "Expected impact assessment confidence?"),
    ("engagement", "ENGAGEMENT", "Your engagement and commitment level?"),
    ("uncertainty", "UNCERTAINTY", "Overall uncertainty (inverse of confidence)?"),
]


def handle_decision_command(args):
    """
    Handle decision command with epistemic assessment and ModalitySwitcher routing.
    
    Supports:
    - Interactive epistemic assessment
    - Batch mode from JSON/flags
    - Strategy selection
    - Adapter forcing
    - Model selection
    """
    try:
        # Handle --list-models flag
        if hasattr(args, 'list_models') and args.list_models:
            from empirica.config.credentials_loader import get_credentials_loader
            
            adapter_name = getattr(args, 'adapter', 'qwen')
            loader = get_credentials_loader()
            models = loader.get_available_models(adapter_name)
            default_model = loader.get_default_model(adapter_name)
            
            print(f"\n📋 Available models for {adapter_name}:")
            print("=" * 70)
            for model in models:
                marker = " (default)" if model == default_model else ""
                print(f"  • {model}{marker}")
            print()
            return
        
        print("\n🎯 Empirica Decision Assistant")
        print("=" * 70)
        
        query = args.decision
        print(f"\n📋 Decision Query: {query}")
        
        # Get epistemic state
        if hasattr(args, 'epistemic_state') and args.epistemic_state:
            # Load from JSON file
            epistemic_state = load_epistemic_state_from_file(args.epistemic_state)
            print(f"✅ Loaded epistemic state from {args.epistemic_state}")
        elif hasattr(args, 'know') and args.know is not None:
            # Load from individual flags
            epistemic_state = load_epistemic_state_from_flags(args)
            print(f"✅ Loaded epistemic state from command-line flags")
        else:
            # Interactive assessment
            print("\n" + "=" * 70)
            print("📊 Interactive Epistemic Assessment")
            print("=" * 70)
            print("\nPlease rate each dimension on a scale of 0.0 to 1.0")
            print("(0.0 = none/lowest, 1.0 = complete/highest)\n")
            
            epistemic_state = interactive_epistemic_assessment()
        
        # Determine routing strategy
        strategy = RoutingStrategy.EPISTEMIC  # Default
        if hasattr(args, 'strategy') and args.strategy:
            strategy_map = {
                'epistemic': RoutingStrategy.EPISTEMIC,
                'cost': RoutingStrategy.COST,
                'latency': RoutingStrategy.LATENCY,
                'quality': RoutingStrategy.QUALITY,
                'balanced': RoutingStrategy.BALANCED,
            }
            strategy = strategy_map.get(args.strategy.lower(), RoutingStrategy.EPISTEMIC)
        
        # Build preferences
        preferences = RoutingPreferences(
            strategy=strategy,
            max_cost_usd=getattr(args, 'max_cost', 1.0),
            max_latency_sec=getattr(args, 'max_latency', 30.0),
            min_quality_score=getattr(args, 'min_quality', 0.7),
            force_adapter=getattr(args, 'adapter', None),
            allow_fallback=not getattr(args, 'no_fallback', False)
        )
        
        # Initialize ModalitySwitcher
        switcher = ModalitySwitcher()
        
        # Get model preference if specified
        model = getattr(args, 'model', None)
        
        # Get routing decision
        print("\n" + "=" * 70)
        print("🔄 Routing Analysis")
        print("=" * 70)
        
        context = {"source": "cli", "interactive": True}
        if model:
            context["model"] = model
            print(f"   Model: {model}")
        
        decision = switcher.route_request(
            query=query,
            epistemic_state=epistemic_state,
            preferences=preferences,
            context=context
        )
        
        print(f"\n✅ Selected Adapter: {decision.selected_adapter}")
        print(f"   Strategy: {strategy.value}")
        print(f"   Rationale: {decision.rationale}")
        print(f"   Estimated Cost: ${decision.estimated_cost:.4f}")
        print(f"   Estimated Latency: {decision.estimated_latency:.1f}s")
        print(f"   Fallback Order: {', '.join(decision.fallback_adapters)}")
        
        # Execute with adapter
        print("\n" + "=" * 70)
        print("🤖 Executing Query")
        print("=" * 70)
        
        response = switcher.execute_with_routing(
            query=query,
            epistemic_state=epistemic_state,
            preferences=preferences,
            context=context,  # Use same context with model
            system="You are Empirica, a helpful epistemic reasoning assistant. Provide clear, honest assessments.",
            temperature=0.7,
            max_tokens=500
        )
        
        # Display response
        print("\n" + "=" * 70)
        print("📊 Decision Recommendation")
        print("=" * 70)
        
        if isinstance(response, AdapterError):
            print(f"\n❌ Error: {response.message}")
            print(f"   Code: {response.code}")
            print(f"   Provider: {response.provider}")
            if response.recoverable:
                print("   ⚠️  This error is recoverable - retry may work")
            return
        
        # Display epistemic analysis
        print("\n🧠 Epistemic Analysis:")
        print(f"   Overall Confidence: {1.0 - epistemic_state.get('uncertainty', 0.5):.2f}")
        print(f"   KNOW: {epistemic_state.get('know', 0.5):.2f}")
        print(f"   DO: {epistemic_state.get('do', 0.5):.2f}")
        print(f"   CONTEXT: {epistemic_state.get('context', 0.5):.2f}")
        
        # Display LLM response
        print(f"\n🤖 LLM Response:")
        print(f"   Decision: {response.decision}")
        print(f"   Confidence: {response.confidence:.2f}")
        print(f"   Rationale: {response.rationale[:200]}{'...' if len(response.rationale) > 200 else ''}")
        
        if response.suggested_actions:
            print(f"\n✅ Suggested Actions:")
            for i, action in enumerate(response.suggested_actions[:5], 1):
                print(f"   {i}. {action}")
        
        # Show epistemic vectors from response
        if getattr(args, 'verbose', False) and response.vector_references:
            print(f"\n📊 Epistemic Vectors (from adapter):")
            for key, value in sorted(response.vector_references.items()):
                print(f"   {key:12s}: {value:.2f} {'█' * int(value * 20)}")
        
        # Confirmation prompt (if interactive)
        if not getattr(args, 'yes', False) and sys.stdin.isatty():
            print(f"\n" + "=" * 70)
            proceed = input(f"Proceed with {response.decision}? [Y/n]: ").strip().lower()
            if proceed and proceed != 'y' and proceed != 'yes':
                print("❌ Decision cancelled")
                return
            print("✅ Decision confirmed")
        
        print("\n" + "=" * 70)
        print("✅ Decision Process Complete")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Decision process interrupted")
        sys.exit(1)
    except Exception as e:
        handle_cli_error(e, "Decision", getattr(args, 'verbose', False))


def interactive_epistemic_assessment() -> Dict[str, float]:
    """
    Conduct interactive epistemic assessment for all 13 vectors.
    
    Returns:
        Dict mapping vector names to scores (0.0-1.0)
    """
    epistemic_state = {}
    
    for i, (key, name, description) in enumerate(EPISTEMIC_VECTORS, 1):
        print(f"\n📊 Assessment {i}/13: {name}")
        print("-" * 70)
        print(f"{description}")
        print(f"0.0 (none/lowest) ←{'─' * 20}●{'─' * 20}→ 1.0 (complete/highest)")
        
        while True:
            try:
                value_str = input(f"Enter score [0.0-1.0] (or 's' to skip): ").strip()
                
                if value_str.lower() == 's':
                    # Default to 0.5 for skipped
                    value = 0.5
                    print(f"⏭️  Skipped - using default: {value:.2f}")
                    break
                
                value = float(value_str)
                
                if 0.0 <= value <= 1.0:
                    break
                else:
                    print("⚠️  Please enter a value between 0.0 and 1.0")
            except ValueError:
                print("⚠️  Invalid input. Please enter a number between 0.0 and 1.0, or 's' to skip")
        
        epistemic_state[key] = value
    
    print("\n" + "=" * 70)
    print("✅ Epistemic Assessment Complete")
    print("=" * 70)
    
    return epistemic_state


def load_epistemic_state_from_file(filepath: str) -> Dict[str, float]:
    """Load epistemic state from JSON file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Validate all 13 vectors present
        missing = [key for key, _, _ in EPISTEMIC_VECTORS if key not in data]
        if missing:
            print(f"⚠️  Warning: Missing vectors in file: {missing}")
            print(f"   Using default value 0.5 for missing vectors")
            for key in missing:
                data[key] = 0.5
        
        return data
        
    except FileNotFoundError:
        raise FileNotFoundError(f"Epistemic state file not found: {filepath}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in epistemic state file: {e}")


def load_epistemic_state_from_flags(args) -> Dict[str, float]:
    """Load epistemic state from command-line flags."""
    epistemic_state = {}
    
    for key, _, _ in EPISTEMIC_VECTORS:
        if hasattr(args, key) and getattr(args, key) is not None:
            epistemic_state[key] = getattr(args, key)
        else:
            # Default to 0.5 for missing
            epistemic_state[key] = 0.5
    
    return epistemic_state


def handle_decision_batch_command(args):
    """
    Handle batch decision processing from file.
    
    Expected format:
    [
        {"query": "...", "epistemic_state": {...}},
        {"query": "...", "epistemic_state": {...}}
    ]
    """
    try:
        print("\n📦 Batch Decision Processing")
        print("=" * 70)
        
        # Load batch file
        with open(args.batch_file, 'r') as f:
            batch_data = json.load(f)
        
        print(f"✅ Loaded {len(batch_data)} decisions from {args.batch_file}")
        
        switcher = ModalitySwitcher()
        results = []
        
        for i, item in enumerate(batch_data, 1):
            print(f"\n📋 Processing {i}/{len(batch_data)}: {item['query'][:50]}...")
            
            response = switcher.execute_with_routing(
                query=item['query'],
                epistemic_state=item['epistemic_state'],
                preferences=RoutingPreferences(
                    strategy=RoutingStrategy.EPISTEMIC
                ),
                context={"source": "cli_batch", "batch_index": i}
            )
            
            if isinstance(response, AdapterResponse):
                print(f"   ✅ {response.decision} (confidence: {response.confidence:.2f})")
                results.append({
                    "query": item['query'],
                    "decision": response.decision,
                    "confidence": response.confidence,
                    "rationale": response.rationale
                })
            else:
                print(f"   ❌ Error: {response.message}")
                results.append({
                    "query": item['query'],
                    "error": response.message
                })
        
        # Save results
        output_file = args.output or args.batch_file.replace('.json', '_results.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ Batch processing complete")
        print(f"   Results saved to: {output_file}")
        
    except Exception as e:
        handle_cli_error(e, "Batch Decision", getattr(args, 'verbose', False))
