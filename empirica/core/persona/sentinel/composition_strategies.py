"""
Composition Strategies - COMPOSE operation for multi-persona assessments

Takes assessments from N personas and produces unified assessment by
merging the 13 epistemic vectors using different strategies.

Available strategies:
- average: Simple average of scores
- weighted_by_confidence: Weight by persona's self-reported confidence
- weighted_by_domain: Weight by persona's domain relevance
- consensus_threshold: Require agreement above threshold
"""

import logging
from typing import Dict, List, Optional
from statistics import mean, stdev

from empirica.core.schemas.epistemic_assessment import (
    EpistemicAssessmentSchema,
    VectorAssessment
)
from empirica.core.persona.persona_profile import PersonaProfile

logger = logging.getLogger(__name__)


def average_composition(
    persona_assessments: Dict[str, EpistemicAssessmentSchema],
    persona_profiles: Optional[Dict[str, PersonaProfile]] = None
) -> EpistemicAssessmentSchema:
    """
    Simple average composition - baseline strategy

    For each vector, take the mean score across all personas and
    concatenate rationales.

    Args:
        persona_assessments: {persona_id: EpistemicAssessmentSchema}
        persona_profiles: Not used in this strategy

    Returns:
        Unified EpistemicAssessmentSchema with averaged scores
    """
    if not persona_assessments:
        raise ValueError("No persona assessments provided")

    personas = list(persona_assessments.keys())
    logger.info(f"Composing {len(personas)} assessments using average strategy")

    def compose_vector(vector_name: str) -> VectorAssessment:
        """Average a single vector across all personas"""
        scores = []
        rationales = []
        evidences = []
        warrants = []
        priorities = []

        for persona_id, assessment in persona_assessments.items():
            vector = getattr(assessment, vector_name)
            scores.append(vector.score)
            rationales.append(f"[{persona_id}] {vector.rationale}")
            if vector.evidence:
                evidences.append(f"[{persona_id}] {vector.evidence}")
            if vector.warrants_investigation:
                warrants.append(persona_id)
            priorities.append(vector.investigation_priority)

        return VectorAssessment(
            score=mean(scores),
            rationale=" | ".join(rationales),
            evidence=" | ".join(evidences) if evidences else None,
            warrants_investigation=len(warrants) > len(personas) / 2,  # Majority
            investigation_priority=int(mean(priorities))
        )

    # Compose all 13 vectors
    return EpistemicAssessmentSchema(
        engagement=compose_vector("engagement"),
        foundation_know=compose_vector("foundation_know"),
        foundation_do=compose_vector("foundation_do"),
        foundation_context=compose_vector("foundation_context"),
        comprehension_clarity=compose_vector("comprehension_clarity"),
        comprehension_coherence=compose_vector("comprehension_coherence"),
        comprehension_signal=compose_vector("comprehension_signal"),
        comprehension_density=compose_vector("comprehension_density"),
        execution_state=compose_vector("execution_state"),
        execution_change=compose_vector("execution_change"),
        execution_completion=compose_vector("execution_completion"),
        execution_impact=compose_vector("execution_impact"),
        uncertainty=compose_vector("uncertainty")
    )


def weighted_by_confidence_composition(
    persona_assessments: Dict[str, EpistemicAssessmentSchema],
    persona_profiles: Dict[str, PersonaProfile]
) -> EpistemicAssessmentSchema:
    """
    Weighted composition by persona confidence

    Weight each persona's contribution by their overall confidence
    (calculated as average of foundation tier scores).

    Personas with higher confidence have more influence on composed result.

    Args:
        persona_assessments: {persona_id: EpistemicAssessmentSchema}
        persona_profiles: {persona_id: PersonaProfile} for calculating weights

    Returns:
        Unified EpistemicAssessmentSchema with confidence-weighted scores
    """
    if not persona_assessments:
        raise ValueError("No persona assessments provided")
    if not persona_profiles:
        logger.warning("No persona profiles provided, falling back to average composition")
        return average_composition(persona_assessments)

    personas = list(persona_assessments.keys())
    logger.info(f"Composing {len(personas)} assessments using confidence-weighted strategy")

    # Calculate weights based on foundation tier confidence
    weights = {}
    for persona_id, assessment in persona_assessments.items():
        tier_confidences = assessment.calculate_tier_confidences()
        foundation_confidence = tier_confidences["foundation_confidence"]
        weights[persona_id] = foundation_confidence

    # Normalize weights to sum to 1.0
    total_weight = sum(weights.values())
    weights = {pid: w / total_weight for pid, w in weights.items()}

    logger.info(f"Persona weights: {weights}")

    def compose_vector_weighted(vector_name: str) -> VectorAssessment:
        """Weighted average of a single vector"""
        weighted_score = 0.0
        rationales = []
        evidences = []
        warrants = []
        priorities = []

        for persona_id, assessment in persona_assessments.items():
            vector = getattr(assessment, vector_name)
            weight = weights[persona_id]

            weighted_score += vector.score * weight
            rationales.append(f"[{persona_id} w={weight:.2f}] {vector.rationale}")

            if vector.evidence:
                evidences.append(f"[{persona_id}] {vector.evidence}")
            if vector.warrants_investigation:
                warrants.append((persona_id, weight))
            priorities.append(vector.investigation_priority * weight)

        # Warrants investigation if weighted votes > 0.5
        warrant_weight = sum(w for _, w in warrants)

        return VectorAssessment(
            score=weighted_score,
            rationale=" | ".join(rationales),
            evidence=" | ".join(evidences) if evidences else None,
            warrants_investigation=warrant_weight > 0.5,
            investigation_priority=int(sum(priorities))
        )

    # Compose all 13 vectors
    return EpistemicAssessmentSchema(
        engagement=compose_vector_weighted("engagement"),
        foundation_know=compose_vector_weighted("foundation_know"),
        foundation_do=compose_vector_weighted("foundation_do"),
        foundation_context=compose_vector_weighted("foundation_context"),
        comprehension_clarity=compose_vector_weighted("comprehension_clarity"),
        comprehension_coherence=compose_vector_weighted("comprehension_coherence"),
        comprehension_signal=compose_vector_weighted("comprehension_signal"),
        comprehension_density=compose_vector_weighted("comprehension_density"),
        execution_state=compose_vector_weighted("execution_state"),
        execution_change=compose_vector_weighted("execution_change"),
        execution_completion=compose_vector_weighted("execution_completion"),
        execution_impact=compose_vector_weighted("execution_impact"),
        uncertainty=compose_vector_weighted("uncertainty")
    )


def weighted_by_domain_composition(
    persona_assessments: Dict[str, EpistemicAssessmentSchema],
    persona_profiles: Dict[str, PersonaProfile],
    task: str = "",
    context: Optional[Dict] = None
) -> EpistemicAssessmentSchema:
    """
    Weighted composition by domain relevance

    Weight each persona by how relevant their focus domains are to the task.
    For example, for "implement caching", performance persona gets higher weight.

    Args:
        persona_assessments: {persona_id: EpistemicAssessmentSchema}
        persona_profiles: {persona_id: PersonaProfile} with focus_domains
        task: Task description for domain matching
        context: Optional context for domain matching

    Returns:
        Unified EpistemicAssessmentSchema with domain-weighted scores
    """
    if not persona_assessments:
        raise ValueError("No persona assessments provided")
    if not persona_profiles:
        logger.warning("No persona profiles provided, falling back to average composition")
        return average_composition(persona_assessments)

    personas = list(persona_assessments.keys())
    logger.info(f"Composing {len(personas)} assessments using domain-weighted strategy")

    # Calculate domain relevance weights (simple keyword matching for now)
    task_lower = task.lower()
    weights = {}

    for persona_id, profile in persona_profiles.items():
        # Count how many focus domains appear in task
        relevance = 0
        for domain in profile.epistemic_config.focus_domains:
            if domain.lower() in task_lower:
                relevance += 1

        # If no domain match, give minimum weight (don't exclude completely)
        weights[persona_id] = max(0.1, relevance)

    # Normalize weights to sum to 1.0
    total_weight = sum(weights.values())
    weights = {pid: w / total_weight for pid, w in weights.items()}

    logger.info(f"Domain relevance weights: {weights}")

    # Use same weighted composition logic as confidence-weighted
    def compose_vector_weighted(vector_name: str) -> VectorAssessment:
        """Weighted average of a single vector"""
        weighted_score = 0.0
        rationales = []
        evidences = []
        warrants = []
        priorities = []

        for persona_id, assessment in persona_assessments.items():
            vector = getattr(assessment, vector_name)
            weight = weights[persona_id]

            weighted_score += vector.score * weight
            rationales.append(f"[{persona_id} w={weight:.2f}] {vector.rationale}")

            if vector.evidence:
                evidences.append(f"[{persona_id}] {vector.evidence}")
            if vector.warrants_investigation:
                warrants.append((persona_id, weight))
            priorities.append(vector.investigation_priority * weight)

        warrant_weight = sum(w for _, w in warrants)

        return VectorAssessment(
            score=weighted_score,
            rationale=" | ".join(rationales),
            evidence=" | ".join(evidences) if evidences else None,
            warrants_investigation=warrant_weight > 0.5,
            investigation_priority=int(sum(priorities))
        )

    # Compose all 13 vectors
    return EpistemicAssessmentSchema(
        engagement=compose_vector_weighted("engagement"),
        foundation_know=compose_vector_weighted("foundation_know"),
        foundation_do=compose_vector_weighted("foundation_do"),
        foundation_context=compose_vector_weighted("foundation_context"),
        comprehension_clarity=compose_vector_weighted("comprehension_clarity"),
        comprehension_coherence=compose_vector_weighted("comprehension_coherence"),
        comprehension_signal=compose_vector_weighted("comprehension_signal"),
        comprehension_density=compose_vector_weighted("comprehension_density"),
        execution_state=compose_vector_weighted("execution_state"),
        execution_change=compose_vector_weighted("execution_change"),
        execution_completion=compose_vector_weighted("execution_completion"),
        execution_impact=compose_vector_weighted("execution_impact"),
        uncertainty=compose_vector_weighted("uncertainty")
    )


# Strategy registry
COMPOSITION_STRATEGIES = {
    "average": average_composition,
    "weighted_by_confidence": weighted_by_confidence_composition,
    "weighted_by_domain": weighted_by_domain_composition,
}


def get_composition_strategy(strategy_name: str):
    """Get composition strategy function by name"""
    if strategy_name not in COMPOSITION_STRATEGIES:
        raise ValueError(
            f"Unknown composition strategy: {strategy_name}. "
            f"Available: {list(COMPOSITION_STRATEGIES.keys())}"
        )
    return COMPOSITION_STRATEGIES[strategy_name]
