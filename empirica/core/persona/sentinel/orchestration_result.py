"""
Orchestration result data structures

OrchestrationResult: Complete result of multi-persona orchestration
ArbitrationResult: Result of conflict arbitration between personas
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, UTC

from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema


@dataclass
class ArbitrationResult:
    """
    Result of conflict arbitration between personas

    When personas disagree on recommended action (e.g., security says
    INVESTIGATE, UX says PROCEED), arbitration resolves the conflict.
    """

    # Final decision
    final_action: str  # "proceed", "investigate", "escalate"
    reasoning: str  # Why this action was chosen
    confidence: float  # Confidence in arbitration decision (0.0-1.0)

    # Individual persona positions
    persona_votes: Dict[str, str]  # {persona_id: action}
    persona_weights: Dict[str, float]  # {persona_id: weight_used_in_decision}

    # Conflict details
    conflicts_found: List[str]  # Descriptions of conflicts
    consensus_level: float  # 0.0 (total disagreement) to 1.0 (full consensus)

    # Arbitration metadata
    arbitration_strategy: str  # Strategy used (majority, weighted, etc.)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "final_action": self.final_action,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "persona_votes": self.persona_votes,
            "persona_weights": self.persona_weights,
            "conflicts_found": self.conflicts_found,
            "consensus_level": self.consensus_level,
            "arbitration_strategy": self.arbitration_strategy,
            "timestamp": self.timestamp
        }


@dataclass
class OrchestrationResult:
    """
    Complete result of multi-persona orchestration

    Contains:
    - Composed assessment (merged from all personas)
    - Individual persona assessments
    - Arbitration result (conflict resolution)
    - Metadata and metrics
    """

    # Core results
    composed_assessment: EpistemicAssessmentSchema  # Merged assessment
    final_action: str  # "proceed", "investigate", "escalate"

    # Individual persona results
    persona_assessments: Dict[str, EpistemicAssessmentSchema]  # {persona_id: assessment}

    # Arbitration
    arbitration_result: ArbitrationResult

    # Orchestration metadata
    personas_used: List[str]
    orchestration_strategy: str  # parallel_consensus, sequential, etc.
    composition_strategy: str  # average, weighted, etc.

    # Agreement metrics
    agreement_score: float  # 0.0-1.0, how much personas agreed
    conflicts_detected: List[str]  # List of conflicting assessments

    # Performance
    execution_time_seconds: float
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    # Optional context
    task: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "composed_assessment": self.composed_assessment.to_dict(),
            "final_action": self.final_action,
            "persona_assessments": {
                pid: assessment.to_dict()
                for pid, assessment in self.persona_assessments.items()
            },
            "arbitration_result": self.arbitration_result.to_dict(),
            "personas_used": self.personas_used,
            "orchestration_strategy": self.orchestration_strategy,
            "composition_strategy": self.composition_strategy,
            "agreement_score": self.agreement_score,
            "conflicts_detected": self.conflicts_detected,
            "execution_time_seconds": self.execution_time_seconds,
            "timestamp": self.timestamp,
            "task": self.task,
            "session_id": self.session_id
        }

    def get_summary(self) -> str:
        """Get human-readable summary of orchestration result"""
        lines = [
            f"Orchestration Result ({len(self.personas_used)} personas)",
            f"  Action: {self.final_action.upper()}",
            f"  Agreement: {self.agreement_score:.2%}",
            f"  Confidence: {self.arbitration_result.confidence:.2%}",
            f"",
            f"Personas:",
        ]

        for persona_id in self.personas_used:
            vote = self.arbitration_result.persona_votes.get(persona_id, "unknown")
            weight = self.arbitration_result.persona_weights.get(persona_id, 0.0)
            lines.append(f"  - {persona_id}: {vote} (weight: {weight:.2f})")

        if self.conflicts_detected:
            lines.append(f"")
            lines.append(f"Conflicts:")
            for conflict in self.conflicts_detected:
                lines.append(f"  - {conflict}")

        lines.append(f"")
        lines.append(f"Arbitration: {self.arbitration_result.reasoning}")

        return "\n".join(lines)
