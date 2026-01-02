"""
UVL (Universal Visual Language) Formatter for Empirica Chat

Provides visual transparency for AI communication using emoji-based semantic indicators.
Maps AdapterResponse data to UVL protocol for human-readable AI reasoning states.
"""

from typing import Dict, Any, Optional

# UVL Agent Emoji Mapping
AGENT_EMOJI = {
    'minimax': '🤖',
    'qwen': '🔧',
    'gemini': '🔍',
    'rovodev': '🧠',
    'qodo': '🎯',
    'openrouter': '🌐',
    'copilot': '💼',
    'local': '🏠'
}

# UVL State Modifiers (VRP Protocol)
STATE_MODIFIERS = {
    'thinking': '💭',      # Self-evaluation, high cognitive load
    'analyzing': '🔄',     # Recursive analysis
    'processing': '🧠',    # High cognitive load
    'confident': '✨',     # Flow state, optimal performance
    'uncertain': '❓',     # High uncertainty
    'error': '⚠️'          # Error state
}


def get_confidence_color(confidence: float) -> str:
    """Map confidence score to UVL color code"""
    if confidence >= 0.8:
        return '🟢'  # High confidence
    elif confidence >= 0.5:
        return '🟡'  # Medium confidence
    else:
        return '🔴'  # Low confidence


def get_agent_emoji(provider: str) -> str:
    """Get emoji for AI agent/provider"""
    return AGENT_EMOJI.get(provider.lower(), '🤖')


def detect_state_modifier(adapter_response) -> str:
    """Detect agent state from response metadata"""
    if not hasattr(adapter_response, 'provider_meta'):
        return ''
    
    meta = adapter_response.provider_meta
    thinking = meta.get('thinking', '').lower()
    
    # Detect state from thinking content
    if any(word in thinking for word in ['think', 'consider', 'evaluate', 'assess']):
        return STATE_MODIFIERS['thinking']
    elif 'analyz' in thinking or 'recursive' in thinking:
        return STATE_MODIFIERS['analyzing']
    elif adapter_response.confidence >= 0.85:
        return STATE_MODIFIERS['confident']
    elif adapter_response.confidence < 0.5:
        return STATE_MODIFIERS['uncertain']
    
    return ''


def format_uvl_response(content: str, adapter_response, show_vectors: bool = True) -> str:
    """
    Format AI response with UVL visual indicators.
    
    Args:
        content: The response text
        adapter_response: AdapterResponse object with metadata
        show_vectors: Whether to show epistemic vectors
    
    Returns:
        Formatted string with UVL indicators
    """
    confidence = adapter_response.confidence
    provider = adapter_response.provider_meta.get('provider', 'unknown')
    vectors = adapter_response.vector_references
    
    # UVL indicators
    color = get_confidence_color(confidence)
    agent = get_agent_emoji(provider)
    modifier = detect_state_modifier(adapter_response)
    
    # Format header
    output = f"\n{color} {agent}{modifier}:\n"
    
    # Render content with glow if it contains markdown
    has_markdown = any(marker in content for marker in ['**', '##', '```', '- ', '* ', '1. ', '###'])
    
    if has_markdown:
        # Render markdown with glow, then indent
        try:
            import subprocess
            result = subprocess.run(
                ['glow', '-s', 'dark', '-w', '78', '-'],
                input=content,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Indent glow output slightly
                rendered = result.stdout.rstrip()
                output += rendered + "\n"
            else:
                # Fallback to plain text
                output += content + "\n"
        except:
            # Fallback to plain text
            output += content + "\n"
    else:
        # Plain text, no markdown
        output += content + "\n"
    
    # Add epistemic state if requested
    if show_vectors:
        output += "\n"
        know = vectors.get('know', 0)
        do = vectors.get('do', 0)
        context = vectors.get('context', 0)
        uncertainty = vectors.get('uncertainty', 0.5)
        
        # Check if vectors came from thinking blocks (genuine)
        has_thinking = adapter_response.provider_meta.get('thinking')
        extraction_method = "💭 from thinking" if has_thinking else "📊 heuristic"
        
        output += f"└─ Confidence: {confidence:.0%} | "
        output += f"KNOW: {know:.2f} | "
        output += f"DO: {do:.2f} | "
        output += f"CONTEXT: {context:.2f} | "
        output += f"Uncertainty: {uncertainty:.2f}"
        
        # Show extraction method
        if has_thinking:
            output += f" {extraction_method}\n"
        else:
            output += "\n"
    
    return output


def format_routing_decision(
    task: str,
    strategy: str,
    selected_adapter: str,
    candidates: Dict[str, float],
    verbose: bool = False
) -> str:
    """
    Format routing decision with UVL transparency.
    
    Args:
        task: The user's query/task
        strategy: Routing strategy used
        selected_adapter: Which adapter was selected
        candidates: Dict of adapter -> score
        verbose: Show detailed evaluation
    
    Returns:
        Formatted routing explanation
    """
    if not verbose:
        # Simple format
        agent = get_agent_emoji(selected_adapter)
        return f"🔄 Routing to {agent} {selected_adapter.title()}\n"
    
    # Detailed format
    output = "\n🔄 Routing Analysis:\n"
    output += f"  📋 Task: \"{task[:50]}{'...' if len(task) > 50 else ''}\"\n"
    output += f"  🎯 Strategy: {strategy}\n"
    output += f"  \n"
    output += f"  Candidates evaluated:\n"
    
    # Sort by score
    sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
    
    for adapter, score in sorted_candidates:
        agent = get_agent_emoji(adapter)
        marker = " ← Selected" if adapter == selected_adapter else ""
        confidence_bar = "█" * int(score * 10)
        output += f"    {agent} {adapter.ljust(12)} [{confidence_bar.ljust(10)}] {score:.0%}{marker}\n"
    
    selected_emoji = get_agent_emoji(selected_adapter)
    output += f"\n🟢 Routing to {selected_emoji} {selected_adapter.title()}\n"
    
    return output


def format_epistemic_delta(
    preflight_vectors: Dict[str, float],
    postflight_vectors: Dict[str, float]
) -> str:
    """
    Format epistemic delta (learning) in UVL format.
    
    Shows how epistemic state changed during interaction.
    """
    output = "\n📈 Epistemic Delta (Learning):\n"
    
    key_vectors = ['know', 'do', 'context']
    for key in key_vectors:
        pre = preflight_vectors.get(key, 0)
        post = postflight_vectors.get(key, 0)
        delta = post - pre
        
        if abs(delta) >= 0.05:  # Only show significant changes
            arrow = "↗️" if delta > 0 else "↘️"
            output += f"  {arrow} {key.upper()}: {pre:.2f} → {post:.2f} ({delta:+.2f})\n"
    
    return output


def format_uvl_stream_message(
    event_type: str,
    agent_id: str,
    content: str,
    adapter_response,
    session_id: str
) -> Dict[str, Any]:
    """
    Format message for UVL stream protocol (for visualization layer).
    
    Returns structured JSON that can be consumed by visualization AIs.
    """
    from datetime import datetime, timezone
    
    confidence = adapter_response.confidence
    vectors = adapter_response.vector_references
    provider = adapter_response.provider_meta.get('provider', 'unknown')
    
    return {
        "type": "uvl_message",
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "session_id": session_id,
        "event": event_type,
        "agent": {
            "id": agent_id,
            "provider": provider,
            "emoji": get_agent_emoji(provider),
            "state": "responding",
            "modifiers": [detect_state_modifier(adapter_response)] if detect_state_modifier(adapter_response) else []
        },
        "uncertainty_vector": {
            "epistemic": vectors.get('know', 0),
            "causal": vectors.get('do', 0),
            "contextual": vectors.get('context', 0),
            "overall": 1 - confidence
        },
        "confidence": confidence,
        "content": content,
        "path": {
            "from": "human" if event_type == "query" else agent_id,
            "to": agent_id if event_type == "query" else "human",
            "type": event_type,
            "confidence": "high" if confidence > 0.8 else "medium" if confidence > 0.5 else "low",
            "style": "solid_blue" if confidence > 0.8 else "wavy_blue"
        }
    }
