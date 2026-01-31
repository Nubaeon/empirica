"""
Epistemic MCP Module

Vector-programmed MCP server components:
- EpistemicStateMachine: 13-vector state tracking
- VectorRouter: Vector-driven behavior routing
- PersonalityProfile: Different routing thresholds
- EpistemicModes: Behavioral implementations
"""

from .state_machine import EpistemicStateMachine, VectorState
from .router import VectorRouter, RoutingDecision
from .personality import (
    PersonalityProfile,
    CAUTIOUS_RESEARCHER,
    PRAGMATIC_IMPLEMENTER,
    BALANCED_ARCHITECT,
    ADAPTIVE_LEARNER,
    get_personality,
    list_personalities
)
from .modes import EpistemicModes
from .tool_router import ToolRouter, ToolRecommendation, RoutingAdvice

__all__ = [
    "EpistemicStateMachine",
    "VectorState",
    "VectorRouter",
    "RoutingDecision",
    "PersonalityProfile",
    "CAUTIOUS_RESEARCHER",
    "PRAGMATIC_IMPLEMENTER",
    "BALANCED_ARCHITECT",
    "ADAPTIVE_LEARNER",
    "get_personality",
    "list_personalities",
    "EpistemicModes",
    "ToolRouter",
    "ToolRecommendation",
    "RoutingAdvice",
]
