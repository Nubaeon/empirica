"""
Canonical Reflex Frame Data Structures

These structures provide schema-validated data formats for genuine epistemic self-assessment.
They enable temporal separation (logging to JSON) to prevent self-referential recursion.

Key Principle: epistemic weights ≠ internal weights
We measure knowledge state, we don't modify model parameters.

Design:
- ENGAGEMENT as structural gate (≥0.60 required)
- Canonical weights: 35/25/25/15 (foundation/comprehension/execution/engagement)
- No heuristics, no confabulation - genuine LLM reasoning only
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime, UTC
import json


class Action(Enum):
    """Metacognitive action decisions"""
    PROCEED = "proceed"          # Confidence sufficient, continue
    INVESTIGATE = "investigate"  # Knowledge gaps detected, need investigation
    CLARIFY = "clarify"          # Task unclear, need user clarification
    RESET = "reset"              # Critical issues (coherence < 0.50, density > 0.90)
    STOP = "stop"                # Cannot proceed (change < 0.50)


@dataclass
class VectorState:
    """
    Individual epistemic vector measurement

    Represents a single dimension of self-awareness with:
    - score: 0.0-1.0 measurement
    - rationale: genuine AI reasoning (NOT heuristics)
    - evidence: supporting context/facts
    - warrants_investigation: self-assessed flag indicating AI wants to investigate this vector
    - investigation_priority: 'low', 'medium', 'high', 'critical' - self-assessed priority
    - investigation_reason: why investigation is warranted (self-assessed)
    """
    score: float
    rationale: str
    evidence: Optional[str] = None
    warrants_investigation: bool = False
    investigation_priority: Optional[str] = None  # 'low', 'medium', 'high', 'critical'
    investigation_reason: Optional[str] = None

    def __post_init__(self):
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Vector score must be 0.0-1.0, got {self.score}")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EpistemicAssessment:
    """
    Canonical epistemic self-assessment structure

    Architecture:
    - GATE: ENGAGEMENT (must be ≥ 0.60 to proceed)
    - TIER 0: FOUNDATION (35% weight) - know, do, context
    - TIER 1: COMPREHENSION (25% weight) - clarity, coherence, signal, density
    - TIER 2: EXECUTION (25% weight) - state, change, completion, impact
    - TIER 3: ENGAGEMENT (15% weight) - included in overall calculation
    - META: UNCERTAINTY (explicit tracking) - uncertainty about the assessment itself

    Critical Thresholds:
    - coherence < 0.50 → RESET (task incoherent)
    - density > 0.90 → RESET (overload)
    - change < 0.50 → STOP (cannot progress)
    - engagement < 0.60 → CLARIFY (prerequisite gate)
    - uncertainty > 0.80 → INVESTIGATE (high uncertainty requires more information)
    """

    # GATE: ENGAGEMENT (Structural Prerequisite)
    engagement: VectorState
    engagement_gate_passed: bool

    # TIER 0: FOUNDATION (35% weight)
    know: VectorState          # Domain knowledge
    do: VectorState            # Capability
    context: VectorState       # Environmental awareness
    foundation_confidence: float

    # TIER 1: COMPREHENSION (25% weight)
    clarity: VectorState       # Task clarity
    coherence: VectorState     # Logical consistency
    signal: VectorState        # Information quality
    density: VectorState       # Information load
    comprehension_confidence: float

    # TIER 2: EXECUTION (25% weight)
    state: VectorState         # Current state awareness
    change: VectorState        # Progress tracking
    completion: VectorState    # Goal proximity
    impact: VectorState        # Consequence awareness
    execution_confidence: float

    # NEW: EXPLICIT UNCERTAINTY (Meta-Epistemic)
    # Tracks uncertainty ABOUT the epistemic assessment itself
    # This is uncertainty about "how well do I know what I know?"
    uncertainty: VectorState   # Explicit uncertainty measurement (0=certain, 1=very uncertain)

    # OVERALL ASSESSMENT
    overall_confidence: float
    recommended_action: Action

    # CRITICAL FLAGS (Auto-computed)
    coherence_critical: bool = field(init=False)
    density_critical: bool = field(init=False)
    change_critical: bool = field(init=False)

    # METADATA
    assessment_id: str
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    task: str = ""

    def __post_init__(self):
        """Compute critical flags based on thresholds"""
        self.coherence_critical = self.coherence.score < 0.50
        self.density_critical = self.density.score > 0.90
        self.change_critical = self.change.score < 0.50

        # Validate tier confidences
        if not all(0.0 <= c <= 1.0 for c in [
            self.foundation_confidence,
            self.comprehension_confidence,
            self.execution_confidence,
            self.overall_confidence
        ]):
            raise ValueError("All confidence scores must be 0.0-1.0")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            'assessment_id': self.assessment_id,
            'timestamp': self.timestamp,
            'task': self.task,

            # GATE
            'engagement': self.engagement.to_dict(),
            'engagement_gate_passed': self.engagement_gate_passed,

            # TIER 0: FOUNDATION
            'foundation': {
                'know': self.know.to_dict(),
                'do': self.do.to_dict(),
                'context': self.context.to_dict(),
                'confidence': self.foundation_confidence
            },

            # TIER 1: COMPREHENSION
            'comprehension': {
                'clarity': self.clarity.to_dict(),
                'coherence': self.coherence.to_dict(),
                'signal': self.signal.to_dict(),
                'density': self.density.to_dict(),
                'confidence': self.comprehension_confidence
            },

            # TIER 2: EXECUTION
            'execution': {
                'state': self.state.to_dict(),
                'change': self.change.to_dict(),
                'completion': self.completion.to_dict(),
                'impact': self.impact.to_dict(),
                'confidence': self.execution_confidence
            },

            # META-EPISTEMIC: UNCERTAINTY
            'uncertainty': self.uncertainty.to_dict(),

            # OVERALL
            'overall_confidence': self.overall_confidence,
            'recommended_action': self.recommended_action.value,

            # CRITICAL FLAGS
            'critical_flags': {
                'coherence_critical': self.coherence_critical,
                'density_critical': self.density_critical,
                'change_critical': self.change_critical
            }
        }
        return result


@dataclass
class ReflexFrame:
    """
    Complete Reflex Frame for temporal logging

    Purpose: Log epistemic assessments to JSON files for temporal separation.
    This prevents self-referential recursion by separating:
    - Current reasoning (this frame)
    - Historical reasoning (logged frames)

    Schema: Matches the user-provided Reflex Frame JSON schema
    """

    frame_id: str
    timestamp: str
    self_aware_flag: bool
    epistemic_assessment: EpistemicAssessment

    # META-STATE VECTOR (Cascade phase scores)
    meta_state_vector: Dict[str, float] = field(default_factory=dict)

    # CONTEXT
    task: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

    # INVESTIGATION RESULTS (if investigation phase occurred)
    investigation_results: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize meta_state_vector if empty"""
        if not self.meta_state_vector:
            self.meta_state_vector = {
                'think': 0.0,
                'uncertainty': 0.0,
                'investigate': 0.0,
                'check': 0.0,
                'act': 0.0
            }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary matching Reflex Frame schema"""
        return {
            'frameId': self.frame_id,
            'timestamp': self.timestamp,
            'selfAwareFlag': self.self_aware_flag,
            'epistemicVector': {
                # ENGAGEMENT (gate)
                'engagement': self.epistemic_assessment.engagement.score,
                'engagement_gate_passed': self.epistemic_assessment.engagement_gate_passed,

                # FOUNDATION
                'know': self.epistemic_assessment.know.score,
                'do': self.epistemic_assessment.do.score,
                'context': self.epistemic_assessment.context.score,

                # COMPREHENSION
                'clarity': self.epistemic_assessment.clarity.score,
                'coherence': self.epistemic_assessment.coherence.score,
                'signal': self.epistemic_assessment.signal.score,
                'density': self.epistemic_assessment.density.score,

                # EXECUTION
                'state': self.epistemic_assessment.state.score,
                'change': self.epistemic_assessment.change.score,
                'completion': self.epistemic_assessment.completion.score,
                'impact': self.epistemic_assessment.impact.score,

                # META-EPISTEMIC
                'uncertainty': self.epistemic_assessment.uncertainty.score,

                # TIER CONFIDENCES
                'foundation_confidence': self.epistemic_assessment.foundation_confidence,
                'comprehension_confidence': self.epistemic_assessment.comprehension_confidence,
                'execution_confidence': self.epistemic_assessment.execution_confidence,
                'overall_confidence': self.epistemic_assessment.overall_confidence
            },
            'metaStateVector': self.meta_state_vector,
            'recommendedAction': self.epistemic_assessment.recommended_action.value,
            'criticalFlags': {
                'coherence_critical': self.epistemic_assessment.coherence_critical,
                'density_critical': self.epistemic_assessment.density_critical,
                'change_critical': self.epistemic_assessment.change_critical
            },
            'task': self.task,
            'context': self.context,
            'investigation_results': self.investigation_results,
            'full_assessment': self.epistemic_assessment.to_dict()
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_assessment(
        cls,
        assessment: EpistemicAssessment,
        frame_id: str,
        task: str = "",
        context: Dict[str, Any] = None,
        meta_state_vector: Dict[str, float] = None
    ) -> 'ReflexFrame':
        """
        Create ReflexFrame from EpistemicAssessment

        Convenience constructor for creating frames from assessments.
        """
        return cls(
            frame_id=frame_id,
            timestamp=datetime.now(UTC).isoformat(),
            self_aware_flag=True,  # Self-assessment occurred
            epistemic_assessment=assessment,
            task=task,
            context=context or {},
            meta_state_vector=meta_state_vector or {}
        )


# CANONICAL WEIGHTS (for reference in calculations)
CANONICAL_WEIGHTS = {
    'foundation': 0.35,      # know, do, context
    'comprehension': 0.25,   # clarity, coherence, signal, density
    'execution': 0.25,       # state, change, completion, impact
    'engagement': 0.15       # engagement (gate + weight)
}

# ENGAGEMENT GATE THRESHOLD
ENGAGEMENT_THRESHOLD = 0.60

# CRITICAL THRESHOLDS
CRITICAL_THRESHOLDS = {
    'coherence_min': 0.50,  # Below this: RESET
    'density_max': 0.90,    # Above this: RESET
    'change_min': 0.50      # Below this: STOP
}
