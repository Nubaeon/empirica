"""
Canonical Reflex Frame Data Structures

Core types for Empirica epistemic framework.
Main assessment schema moved to empirica.core.schemas.epistemic_assessment

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

# Import centralized thresholds
from ..thresholds import ENGAGEMENT_THRESHOLD, CRITICAL_THRESHOLDS

# Import NEW schema (this is now THE schema)
from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema


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


# OLD EpistemicAssessment class removed - use EpistemicAssessmentSchema from empirica.core.schemas.epistemic_assessment
# For backwards compatibility during data migration, import and use convert_old_to_new/convert_new_to_old from assessment_converters


# ReflexFrame class removed - OLD schema dependency
# For logging, use EpistemicAssessmentSchema.model_dump() directly
# or create a new ReflexFrame class that uses EpistemicAssessmentSchema if needed


# CANONICAL WEIGHTS (for reference in calculations)
CANONICAL_WEIGHTS = {
    'foundation': 0.35,      # know, do, context
    'comprehension': 0.25,   # clarity, coherence, signal, density
    'execution': 0.25,       # state, change, completion, impact
    'engagement': 0.15       # engagement (gate + weight)
}

# ENGAGEMENT and CRITICAL thresholds now imported from centralized configuration
# See empirica/core/thresholds.py for definitions
