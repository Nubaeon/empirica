"""
Ask Command Handler - Terminal interface for human users to query AI models

Provides simple question-answering interface that routes through modality switcher.
"""

import sys
from typing import Optional
from empirica.plugins.modality_switcher import ModalitySwitcher, RoutingStrategy, RoutingPreferences
from empirica.data.session_database import SessionDatabase
from empirica.data.session_json_handler import SessionJSONHandler
from ..cli_utils import handle_cli_error
import uuid


def handle_ask_command(args):
    """
    Handle 'empirica ask' command for human users.
    
    Simple query interface that routes through modality switcher to appropriate AI model.
    Optionally tracks conversation in session for history.
    """
    try:
        query = args.query
        
        # Determine routing preferences
        if hasattr(args, 'adapter') and args.adapter:
            # Force specific adapter
            preferences = RoutingPreferences(force_adapter=args.adapter)
            strategy = None
        else:
            # Use routing strategy
            strategy_name = getattr(args, 'strategy', 'epistemic')
            strategy_map = {
                'epistemic': RoutingStrategy.EPISTEMIC,
                'cost': RoutingStrategy.COST,
                'latency': RoutingStrategy.LATENCY,
                'quality': RoutingStrategy.QUALITY,
                'balanced': RoutingStrategy.BALANCED
            }
            strategy = strategy_map.get(strategy_name, RoutingStrategy.EPISTEMIC)
            preferences = RoutingPreferences(strategy=strategy)
        
        # Initialize modality switcher
        switcher = ModalitySwitcher()
        
        # Session tracking (optional)
        session_id = getattr(args, 'session', None) or str(uuid.uuid4())  # Full UUID
        
        if getattr(args, 'verbose', False):
            print(f"🔍 Routing query...")
            print(f"📋 Query: {query}")
            print(f"🆔 Session: {session_id}")
            if hasattr(args, 'adapter') and args.adapter:
                print(f"🎯 Adapter: {args.adapter}")
            else:
                print(f"🎯 Strategy: {strategy_name}")
        
        # Get specific model if requested
        model = getattr(args, 'model', None)
        
        # Execute through modality switcher
        result = switcher.execute_with_routing(
            query=query,
            epistemic_state={},
            preferences=preferences,
            context={'session_id': session_id, 'user_type': 'human', 'model': model},
            system="You are a helpful AI assistant.",
            temperature=getattr(args, 'temperature', 0.7),
            max_tokens=getattr(args, 'max_tokens', 2000)
        )
        
        # Extract response text from AdapterResponse
        if hasattr(result, 'provider_meta') and 'response_full' in result.provider_meta:
            content = result.provider_meta['response_full']
        elif hasattr(result, 'rationale'):
            # Extract from rationale (format: "Provider: actual response...")
            rationale = result.rationale
            if ':' in rationale:
                content = rationale.split(':', 1)[1].strip()
            else:
                content = rationale
        else:
            content = str(result)
        
        # Display response
        print(content)
        
        # Show metadata if verbose
        if getattr(args, 'verbose', False):
            adapter_used = result.decision.selected_adapter if hasattr(result, 'decision') else 'unknown'
            print(f"\n{'─' * 60}")
            print(f"📡 Model: {adapter_used}")
            print(f"🆔 Session: {session_id}")
            if hasattr(result, 'decision'):
                print(f"💰 Estimated cost: ${result.decision.estimated_cost:.4f}")
                print(f"⏱️  Estimated latency: {result.decision.estimated_latency:.1f}s")
        
        # Save to session database if tracking enabled
        if getattr(args, 'save', True):
            try:
                db = SessionDatabase()
                # Store exchange in session
                # (Simplified - full implementation would use proper cascade tracking)
            except Exception as e:
                if getattr(args, 'verbose', False):
                    print(f"\n⚠️  Session save failed: {e}")
        
    except Exception as e:
        handle_cli_error(e, "Ask command", getattr(args, 'verbose', False))
        sys.exit(1)


def _format_response(content: str, max_width: int = 80) -> str:
    """Format response for terminal display"""
    # Simple formatting - could be enhanced with word wrapping, markdown rendering, etc.
    return content
