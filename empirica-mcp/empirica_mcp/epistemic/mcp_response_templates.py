"""
MCP Response Templates - Machine-Optimized JSON

These templates enrich MCP tool responses with epistemic routing metadata,
vector states, and transparent reasoning. Designed for machine consumption
and structured processing.
"""

from typing import Dict, Any, Optional
from .shared_vector_semantics import assess_readiness, get_vector_definition


def enrich_response_with_epistemic_metadata(
    tool_response: Dict[str, Any],
    routing_decision: Dict[str, Any],
    vectors_before: Dict[str, float],
    vectors_after: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Enrich MCP tool response with epistemic metadata.
    
    Args:
        tool_response: Original tool response from CLI
        routing_decision: Routing decision from VectorRouter
        vectors_before: Vector state before tool execution
        vectors_after: Vector state after tool execution (if available)
    
    Returns:
        Enriched response with epistemic metadata
    """
    enriched = tool_response.copy()
    
    # Add epistemic metadata section
    enriched["_epistemic"] = {
        "routing": {
            "mode": routing_decision.get("recommended_mode"),
            "confidence": routing_decision.get("confidence"),
            "reasoning": routing_decision.get("reasoning")
        },
        "vectors_before": vectors_before,
        "readiness": assess_readiness(vectors_before)
    }
    
    # Add vector delta if after-state available
    if vectors_after:
        deltas = {k: vectors_after[k] - vectors_before.get(k, 0.0) 
                 for k in vectors_after}
        enriched["_epistemic"]["vectors_after"] = vectors_after
        enriched["_epistemic"]["deltas"] = deltas
        enriched["_epistemic"]["learning"] = _analyze_learning(deltas)
    
    return enriched


def _analyze_learning(deltas: Dict[str, float]) -> Dict[str, Any]:
    """Analyze learning from vector deltas"""
    know_gain = deltas.get("know", 0.0)
    uncertainty_reduction = -deltas.get("uncertainty", 0.0)  # Negative delta is good
    
    learning_quality = "none"
    if know_gain > 0.15 and uncertainty_reduction > 0.20:
        learning_quality = "excellent"
    elif know_gain > 0.10 or uncertainty_reduction > 0.15:
        learning_quality = "good"
    elif know_gain > 0.05 or uncertainty_reduction > 0.10:
        learning_quality = "moderate"
    
    return {
        "quality": learning_quality,
        "knowledge_gain": know_gain,
        "uncertainty_reduction": uncertainty_reduction,
        "significant_changes": [k for k, v in deltas.items() if abs(v) >= 0.10]
    }


def format_routing_decision(
    decision: Dict[str, Any],
    request: str,
    vectors: Dict[str, float]
) -> Dict[str, Any]:
    """
    Format routing decision for MCP response.
    
    Args:
        decision: Routing decision from VectorRouter
        request: Original request string
        vectors: Current vector state
    
    Returns:
        Structured routing information
    """
    return {
        "request": request,
        "routing": {
            "mode": decision.get("recommended_mode"),
            "confidence": decision.get("confidence"),
            "context_depth": decision.get("context_depth"),
            "reasoning": decision.get("reasoning")
        },
        "vectors": vectors,
        "thresholds": {
            "ready_confidence": READINESS_THRESHOLDS["ready_confidence"],
            "ready_uncertainty": READINESS_THRESHOLDS["ready_uncertainty"],
            "investigate_threshold": READINESS_THRESHOLDS["investigate_threshold"]
        },
        "assessment": assess_readiness(vectors)
    }


def format_investigation_result(
    findings: list,
    unknowns: list,
    vectors_before: Dict[str, float],
    vectors_after: Dict[str, float]
) -> Dict[str, Any]:
    """
    Format investigation results with epistemic metadata.
    
    Args:
        findings: What was learned
        unknowns: What remains unclear
        vectors_before: Vectors at investigation start
        vectors_after: Vectors at investigation end
    
    Returns:
        Structured investigation summary
    """
    deltas = {k: vectors_after[k] - vectors_before.get(k, 0.0) 
             for k in vectors_after}
    
    return {
        "investigation_summary": {
            "findings_count": len(findings),
            "unknowns_resolved": len([u for u in unknowns if u.get("resolved")]),
            "unknowns_remaining": len([u for u in unknowns if not u.get("resolved")]),
            "learning": _analyze_learning(deltas)
        },
        "findings": findings,
        "unknowns": unknowns,
        "epistemic_trajectory": {
            "before": vectors_before,
            "after": vectors_after,
            "deltas": deltas
        },
        "next_action": _recommend_next_action(vectors_after, unknowns)
    }


def _recommend_next_action(vectors: Dict[str, float], unknowns: list) -> Dict[str, str]:
    """Recommend next action based on post-investigation state"""
    uncertainty = vectors.get("uncertainty", 1.0)
    know = vectors.get("know", 0.0)
    unresolved = len([u for u in unknowns if not u.get("resolved")])
    
    if know >= 0.75 and uncertainty <= 0.30:
        return {
            "action": "proceed",
            "reasoning": "Sufficient confidence and low uncertainty. Ready to implement."
        }
    elif unresolved > 3 and uncertainty > 0.50:
        return {
            "action": "investigate_further",
            "reasoning": f"{unresolved} unknowns remain and uncertainty still high. Continue investigation."
        }
    elif uncertainty > 0.50 and vectors.get("context", 0.0) >= 0.50:
        return {
            "action": "ask_questions",
            "reasoning": "Good context but high uncertainty. Ask specific questions to user."
        }
    else:
        return {
            "action": "proceed_cautiously",
            "reasoning": "Moderate confidence. Proceed but use cautious implementation mode."
        }


def format_cascade_summary(
    preflight_vectors: Dict[str, float],
    postflight_vectors: Dict[str, float],
    findings: list,
    unknowns: list,
    mistakes: list
) -> Dict[str, Any]:
    """
    Format complete CASCADE summary for session handoff.
    
    Args:
        preflight_vectors: Baseline vectors
        postflight_vectors: Final vectors
        findings: All findings logged
        unknowns: All unknowns logged
        mistakes: All mistakes logged
    
    Returns:
        Complete CASCADE summary with learning analysis
    """
    deltas = {k: postflight_vectors[k] - preflight_vectors.get(k, 0.0) 
             for k in postflight_vectors}
    
    return {
        "cascade_summary": {
            "trajectory": {
                "preflight": preflight_vectors,
                "postflight": postflight_vectors,
                "deltas": deltas
            },
            "learning": _analyze_learning(deltas),
            "breadcrumbs": {
                "findings": len(findings),
                "unknowns": len(unknowns),
                "mistakes": len(mistakes)
            }
        },
        "handoff_ready": assess_readiness(postflight_vectors)["ready"],
        "findings": findings,
        "unknowns": [u for u in unknowns if not u.get("resolved")],
        "lessons_learned": mistakes
    }


def format_tool_error_with_epistemic_context(
    error: Exception,
    tool_name: str,
    arguments: Dict[str, Any],
    vectors: Dict[str, float]
) -> Dict[str, Any]:
    """
    Format tool error with epistemic context for debugging.
    
    Args:
        error: Exception that occurred
        tool_name: Name of tool that failed
        arguments: Tool arguments
        vectors: Current epistemic state
    
    Returns:
        Structured error with epistemic context
    """
    return {
        "ok": False,
        "error": {
            "type": type(error).__name__,
            "message": str(error),
            "tool": tool_name,
            "arguments": arguments
        },
        "_epistemic": {
            "vectors_at_failure": vectors,
            "uncertainty": vectors.get("uncertainty"),
            "context_level": vectors.get("context"),
            "debugging_hints": _generate_debugging_hints(vectors, tool_name)
        }
    }


def _generate_debugging_hints(vectors: Dict[str, float], tool_name: str) -> list:
    """Generate debugging hints based on epistemic state"""
    hints = []
    
    if vectors.get("context", 0.0) < 0.4:
        hints.append("Low context - run project-bootstrap to understand system better")
    
    if vectors.get("uncertainty", 1.0) > 0.6:
        hints.append("High uncertainty - consider investigating before retrying")
    
    if "log" in tool_name and vectors.get("know", 0.0) < 0.5:
        hints.append("Logging tools require session context - ensure session is active")
    
    return hints
