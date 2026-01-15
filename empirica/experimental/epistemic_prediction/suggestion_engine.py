"""
Phase 5: Proactive Suggestion Engine

Surfaces actionable recommendations during CASCADE phases.
Integrates gap detection and prediction into workflow.

STATUS: Stub - Implementation pending
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum


class SuggestionType(Enum):
    """Types of proactive suggestions"""
    EXPLORE = "explore"           # Suggested area to investigate
    PERSIST = "persist"           # Encouragement to continue current approach
    PIVOT = "pivot"               # Suggestion to change direction
    GAP_ALERT = "gap_alert"       # Missing knowledge detected
    PATTERN_MATCH = "pattern"     # Current work matches known pattern
    CONVERGENT = "convergent"     # Previously rejected path now relevant


class CascadePhase(Enum):
    """CASCADE phases where suggestions can be injected"""
    PREFLIGHT = "preflight"
    CHECK = "check"
    POSTFLIGHT = "postflight"


class Urgency(Enum):
    """How urgently the suggestion should be surfaced"""
    IMMEDIATE = "immediate"   # Show right now
    NEXT_PHASE = "next_phase"  # Show at next CASCADE phase
    EVENTUAL = "eventual"     # Show when convenient


@dataclass
class Suggestion:
    """A proactive suggestion for the AI"""
    suggestion_id: str
    suggestion_type: SuggestionType
    phase: CascadePhase  # When to surface
    urgency: Urgency
    title: str
    content: str
    reasoning: str  # Why this suggestion
    confidence: float
    evidence: List[str]  # Supporting data
    actionable: bool = True
    dismissed: bool = False


@dataclass
class SuggestionContext:
    """Context for generating suggestions"""
    session_id: str
    project_id: str
    current_phase: CascadePhase
    current_vectors: Dict[str, float]
    recent_findings: List[str]
    active_unknowns: List[str]
    trajectory_pattern: Optional[str]
    tags: List[str]


class SuggestionEngine:
    """
    Generates contextual suggestions during CASCADE phases.

    Usage:
        engine = SuggestionEngine(project_id, gap_detector, sequence_tracker)

        # During PREFLIGHT
        suggestions = engine.generate_preflight_suggestions(context)

        # During CHECK
        suggestions = engine.generate_check_suggestions(context)

        # During POSTFLIGHT
        suggestions = engine.generate_postflight_suggestions(context)
    """

    def __init__(
        self,
        project_id: str,
        gap_detector=None,
        sequence_tracker=None,
        trajectory_tracker=None,
        concept_graph=None
    ):
        self.project_id = project_id
        self.gap_detector = gap_detector
        self.sequence_tracker = sequence_tracker
        self.trajectory_tracker = trajectory_tracker
        self.concept_graph = concept_graph
        self._suggestion_generators: Dict[CascadePhase, List[Callable]] = {
            CascadePhase.PREFLIGHT: [],
            CascadePhase.CHECK: [],
            CascadePhase.POSTFLIGHT: [],
        }

    def register_generator(
        self,
        phase: CascadePhase,
        generator: Callable[[SuggestionContext], List[Suggestion]]
    ):
        """Register a custom suggestion generator"""
        self._suggestion_generators[phase].append(generator)

    def generate_preflight_suggestions(
        self,
        context: SuggestionContext
    ) -> List[Suggestion]:
        """
        PREFLIGHT suggestions:
        - "Based on patterns, you'll likely need to understand X"
        - "Similar tasks required knowledge of Y before proceeding"
        - "Gap detected: Previous work on Z incomplete"
        """
        # TODO: Implement preflight suggestions
        raise NotImplementedError("Phase 5 implementation pending")

    def generate_check_suggestions(
        self,
        context: SuggestionContext
    ) -> List[Suggestion]:
        """
        CHECK suggestions:
        - "Your trajectory matches pre-breakthrough pattern, persist"
        - "Warning: This matches dead-end pattern, consider pivot"
        - "Gap detected: You understand A and C but not B"
        - "Convergent path: Your rejected_alternative X is now relevant"
        """
        # TODO: Implement check suggestions
        raise NotImplementedError("Phase 5 implementation pending")

    def generate_postflight_suggestions(
        self,
        context: SuggestionContext
    ) -> List[Suggestion]:
        """
        POSTFLIGHT suggestions:
        - "Your learning matches pattern P, next likely step: Z"
        - "Consider: This finding connects to earlier unknown U"
        - "Recommendation: Explore related cluster C"
        """
        # TODO: Implement postflight suggestions
        raise NotImplementedError("Phase 5 implementation pending")

    def rank_suggestions(
        self,
        suggestions: List[Suggestion],
        max_suggestions: int = 3
    ) -> List[Suggestion]:
        """
        Rank suggestions by:
        - Confidence
        - Urgency
        - Relevance to current task
        - Actionability
        """
        # TODO: Implement ranking algorithm
        raise NotImplementedError("Phase 5 implementation pending")

    def format_for_cascade(
        self,
        suggestions: List[Suggestion],
        phase: CascadePhase
    ) -> str:
        """Format suggestions for CASCADE phase output"""
        # TODO: Implement formatting
        raise NotImplementedError("Phase 5 implementation pending")

    def dismiss_suggestion(self, suggestion_id: str):
        """Mark a suggestion as dismissed (don't show again)"""
        # TODO: Implement dismissal tracking
        raise NotImplementedError("Phase 5 implementation pending")

    def get_suggestion_effectiveness(self) -> Dict[str, float]:
        """Track how often suggestions are followed and successful"""
        # TODO: Implement effectiveness tracking
        raise NotImplementedError("Phase 5 implementation pending")


# Suggestion templates by phase
SUGGESTION_TEMPLATES = {
    CascadePhase.PREFLIGHT: {
        "prerequisite_knowledge": "Based on similar tasks, you'll likely need to understand {concept}",
        "gap_warning": "Gap detected: Previous work on {topic} appears incomplete",
        "pattern_hint": "This task matches pattern '{pattern}' - typically requires {steps}",
    },
    CascadePhase.CHECK: {
        "breakthrough_imminent": "Your trajectory matches pre-breakthrough pattern. Persist through current uncertainty.",
        "dead_end_warning": "Warning: This matches dead-end pattern. Consider pivoting from {approach}.",
        "missing_middle": "Gap detected: You understand {A} and {C} but may be missing {B}.",
        "convergent_path": "Convergent discovery: Your earlier rejected approach '{rejected}' may now be relevant.",
    },
    CascadePhase.POSTFLIGHT: {
        "next_step": "Your learning matches pattern '{pattern}'. Next likely step: {next_step}",
        "connection": "This finding connects to earlier unknown: {unknown}",
        "cluster_explore": "Recommendation: Explore related concepts in {cluster}",
    },
}


# Confidence thresholds for surfacing suggestions
CONFIDENCE_THRESHOLDS = {
    Urgency.IMMEDIATE: 0.8,    # High confidence required
    Urgency.NEXT_PHASE: 0.6,   # Medium confidence
    Urgency.EVENTUAL: 0.4,     # Lower threshold for eventual
}
