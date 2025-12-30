"""
Shared Vector Semantics - Core Definitions

This module defines the semantic meaning of epistemic vectors,
used by BOTH CLI and MCP contexts. The vectors themselves are
universal, only the presentation format differs.
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class VectorDefinition:
    """Definition of a single epistemic vector"""
    name: str
    description: str
    scale_min_meaning: str  # What 0.0 means
    scale_max_meaning: str  # What 1.0 means
    gate_threshold: float = None  # Minimum threshold to proceed (if applicable)
    tier: str = "execution"  # foundation, comprehension, execution, meta


# ============================================================================
# TIER 0: Foundation Vectors (Always Required)
# ============================================================================

FOUNDATION_VECTORS = {
    "engagement": VectorDefinition(
        name="engagement",
        description="Am I focused on the right thing?",
        scale_min_meaning="Completely unmotivated, distracted",
        scale_max_meaning="Fully engaged, clear focus",
        gate_threshold=0.6,
        tier="foundation"
    ),
    "know": VectorDefinition(
        name="know",
        description="Do I understand the domain/concepts?",
        scale_min_meaning="No knowledge, complete guessing",
        scale_max_meaning="Expert understanding, comprehensive knowledge",
        tier="foundation"
    ),
    "do": VectorDefinition(
        name="do",
        description="Can I execute this? (skills, tools, access)",
        scale_min_meaning="Cannot execute, missing all capabilities",
        scale_max_meaning="Fully capable, all tools/skills available",
        tier="foundation"
    ),
    "context": VectorDefinition(
        name="context",
        description="Do I understand the situation? (files, architecture, constraints)",
        scale_min_meaning="No context, isolated understanding",
        scale_max_meaning="Complete situational awareness",
        tier="foundation"
    ),
}

# ============================================================================
# TIER 1: Comprehension Vectors (Understanding Quality)
# ============================================================================

COMPREHENSION_VECTORS = {
    "clarity": VectorDefinition(
        name="clarity",
        description="Is the requirement/task clear?",
        scale_min_meaning="Completely unclear, foggy",
        scale_max_meaning="Crystal clear understanding",
        tier="comprehension"
    ),
    "coherence": VectorDefinition(
        name="coherence",
        description="Do the pieces fit together logically?",
        scale_min_meaning="Contradictory, incoherent",
        scale_max_meaning="Perfectly coherent, logical",
        tier="comprehension"
    ),
    "signal": VectorDefinition(
        name="signal",
        description="Can I distinguish important from noise?",
        scale_min_meaning="All noise, can't see patterns",
        scale_max_meaning="Perfect signal extraction",
        tier="comprehension"
    ),
    "density": VectorDefinition(
        name="density",
        description="How much relevant information do I have?",
        scale_min_meaning="Sparse, minimal information",
        scale_max_meaning="Dense, rich information",
        tier="comprehension"
    ),
}

# ============================================================================
# TIER 2: Execution Vectors (Action-Oriented)
# ============================================================================

EXECUTION_VECTORS = {
    "state": VectorDefinition(
        name="state",
        description="Do I understand the current state?",
        scale_min_meaning="No state understanding",
        scale_max_meaning="Complete state comprehension",
        tier="execution"
    ),
    "change": VectorDefinition(
        name="change",
        description="Do I understand what needs to change?",
        scale_min_meaning="Don't know what to change",
        scale_max_meaning="Perfect change understanding",
        tier="execution"
    ),
    "completion": VectorDefinition(
        name="completion",
        description="Am I done? (Progress measure)",
        scale_min_meaning="Not started (0%)",
        scale_max_meaning="Fully complete (100%)",
        tier="execution"
    ),
    "impact": VectorDefinition(
        name="impact",
        description="Did I achieve the goal? (Value created)",
        scale_min_meaning="No impact, trivial",
        scale_max_meaning="Transformative impact",
        tier="execution"
    ),
}

# ============================================================================
# META: Uncertainty (Self-Awareness)
# ============================================================================

META_VECTORS = {
    "uncertainty": VectorDefinition(
        name="uncertainty",
        description="What don't I know? (Explicit doubt)",
        scale_min_meaning="Completely certain (0.0)",
        scale_max_meaning="Completely uncertain, lost (1.0)",
        tier="meta"
    ),
}

# All vectors combined
ALL_VECTORS = {
    **FOUNDATION_VECTORS,
    **COMPREHENSION_VECTORS,
    **EXECUTION_VECTORS,
    **META_VECTORS
}


# ============================================================================
# Routing Thresholds (Universal)
# ============================================================================

READINESS_THRESHOLDS = {
    "engagement_gate": 0.6,  # Minimum to start work
    "ready_confidence": 0.7,  # Minimum to proceed with implementation
    "ready_uncertainty": 0.35,  # Maximum uncertainty to proceed
    "ready_context": 0.5,  # Minimum context understanding
    "investigate_threshold": 0.65,  # Uncertainty above this triggers investigation
}

# Ask-before-investigate heuristic
ASK_BEFORE_INVESTIGATE = {
    "uncertainty_with_context": {
        "uncertainty_threshold": 0.65,
        "context_threshold": 0.50,
        "action": "ask_questions_first"
    },
    "low_context": {
        "context_threshold": 0.30,
        "action": "investigate_first"
    }
}


def get_vector_definition(vector_name: str) -> VectorDefinition:
    """Get definition for a specific vector"""
    return ALL_VECTORS.get(vector_name)


def get_vectors_by_tier(tier: str) -> Dict[str, VectorDefinition]:
    """Get all vectors in a specific tier"""
    return {k: v for k, v in ALL_VECTORS.items() if v.tier == tier}


def validate_vector_value(vector_name: str, value: float) -> bool:
    """Validate a vector value is in range [0.0, 1.0]"""
    if vector_name not in ALL_VECTORS:
        return False
    return 0.0 <= value <= 1.0


def assess_readiness(vectors: Dict[str, float]) -> Dict[str, Any]:
    """
    Assess if vectors meet readiness thresholds.
    
    Returns dict with:
        ready (bool): Overall readiness
        gates_passed (dict): Which gates passed
        blockers (list): What's blocking if not ready
    """
    engagement = vectors.get("engagement", 0.0)
    uncertainty = vectors.get("uncertainty", 1.0)
    context = vectors.get("context", 0.0)
    know = vectors.get("know", 0.0)
    
    gates = {
        "engagement": engagement >= READINESS_THRESHOLDS["engagement_gate"],
        "uncertainty": uncertainty <= READINESS_THRESHOLDS["ready_uncertainty"],
        "context": context >= READINESS_THRESHOLDS["ready_context"],
        "confidence": know >= 0.7 and uncertainty <= 0.35
    }
    
    blockers = []
    if not gates["engagement"]:
        blockers.append(f"Engagement too low: {engagement:.2f} < 0.6")
    if not gates["uncertainty"]:
        blockers.append(f"Uncertainty too high: {uncertainty:.2f} > 0.35")
    if not gates["context"]:
        blockers.append(f"Context too low: {context:.2f} < 0.5")
    
    return {
        "ready": all(gates.values()),
        "gates_passed": gates,
        "blockers": blockers
    }
