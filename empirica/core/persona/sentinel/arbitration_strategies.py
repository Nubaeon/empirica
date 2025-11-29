"""
Arbitration Strategies - ARBITRATE operation for resolving persona conflicts

When personas disagree on recommended action (e.g., security says INVESTIGATE,
UX says PROCEED), arbitration resolves the conflict.

Available strategies:
- majority_vote: Most common action wins
- confidence_weighted: Weight votes by persona confidence
- pessimistic: Choose most cautious action
- domain_weighted: Weight by domain relevance
- escalate_on_conflict: If any disagreement, escalate to human
"""

import logging
from typing import Dict, Optional, List
from collections import Counter

from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema
from empirica.core.persona.persona_profile import PersonaProfile
from .orchestration_result import ArbitrationResult

logger = logging.getLogger(__name__)


def majority_vote_arbitration(
    persona_actions: Dict[str, str],
    persona_confidences: Optional[Dict[str, float]] = None,
    persona_assessments: Optional[Dict[str, EpistemicAssessmentSchema]] = None
) -> ArbitrationResult:
    """
    Majority vote arbitration - simple democratic approach

    The most common action wins. If tied, choose most cautious.

    Args:
        persona_actions: {persona_id: action} ("proceed"|"investigate"|"escalate")
        persona_confidences: Not used in this strategy
        persona_assessments: Not used in this strategy

    Returns:
        ArbitrationResult with majority action
    """
    if not persona_actions:
        raise ValueError("No persona actions provided")

    logger.info(f"Arbitrating {len(persona_actions)} actions using majority vote")

    # Count votes
    vote_counts = Counter(persona_actions.values())
    logger.info(f"Vote counts: {dict(vote_counts)}")

    # Get action with most votes
    most_common = vote_counts.most_common()

    # Check for tie
    if len(most_common) > 1 and most_common[0][1] == most_common[1][1]:
        # Tie - choose most cautious
        tied_actions = [action for action, count in most_common if count == most_common[0][1]]
        final_action = _choose_most_cautious(tied_actions)
        reasoning = f"Tie between {tied_actions}, chose most cautious: {final_action}"
    else:
        final_action = most_common[0][0]
        reasoning = f"Majority vote: {final_action} ({most_common[0][1]}/{len(persona_actions)} votes)"

    # Calculate consensus level
    consensus = most_common[0][1] / len(persona_actions)

    # Detect conflicts
    conflicts = []
    if len(vote_counts) > 1:
        for action, count in most_common[1:]:
            conflicts.append(f"{count} persona(s) voted {action} vs majority {final_action}")

    return ArbitrationResult(
        final_action=final_action,
        reasoning=reasoning,
        confidence=consensus,  # Confidence = consensus level
        persona_votes=persona_actions,
        persona_weights={pid: 1.0 for pid in persona_actions},  # Equal weights
        conflicts_found=conflicts,
        consensus_level=consensus,
        arbitration_strategy="majority_vote"
    )


def confidence_weighted_arbitration(
    persona_actions: Dict[str, str],
    persona_confidences: Dict[str, float],
    persona_assessments: Optional[Dict[str, EpistemicAssessmentSchema]] = None
) -> ArbitrationResult:
    """
    Confidence-weighted arbitration

    Weight each vote by the persona's confidence. Personas with higher
    confidence have more influence.

    Args:
        persona_actions: {persona_id: action}
        persona_confidences: {persona_id: confidence_score}
        persona_assessments: Not used in this strategy

    Returns:
        ArbitrationResult with confidence-weighted action
    """
    if not persona_actions:
        raise ValueError("No persona actions provided")
    if not persona_confidences:
        logger.warning("No persona confidences provided, falling back to majority vote")
        return majority_vote_arbitration(persona_actions)

    logger.info(f"Arbitrating {len(persona_actions)} actions using confidence-weighted strategy")

    # Calculate weighted votes for each action
    action_weights = {}
    for persona_id, action in persona_actions.items():
        confidence = persona_confidences.get(persona_id, 0.5)  # Default to neutral
        action_weights[action] = action_weights.get(action, 0.0) + confidence

    logger.info(f"Action weights: {action_weights}")

    # Choose action with highest weight
    final_action = max(action_weights.items(), key=lambda x: x[1])[0]
    final_weight = action_weights[final_action]

    # Calculate consensus (how much weight agrees with final action)
    total_weight = sum(action_weights.values())
    consensus = final_weight / total_weight if total_weight > 0 else 0.0

    # Build reasoning
    reasoning = f"Confidence-weighted: {final_action} (weight={final_weight:.2f}/{total_weight:.2f})"

    # Detect conflicts
    conflicts = []
    for action, weight in action_weights.items():
        if action != final_action:
            conflicts.append(
                f"{weight:.2f} confidence voted {action} vs {final_action}"
            )

    return ArbitrationResult(
        final_action=final_action,
        reasoning=reasoning,
        confidence=consensus,
        persona_votes=persona_actions,
        persona_weights=persona_confidences,
        conflicts_found=conflicts,
        consensus_level=consensus,
        arbitration_strategy="confidence_weighted"
    )


def pessimistic_arbitration(
    persona_actions: Dict[str, str],
    persona_confidences: Optional[Dict[str, float]] = None,
    persona_assessments: Optional[Dict[str, EpistemicAssessmentSchema]] = None
) -> ArbitrationResult:
    """
    Pessimistic arbitration - choose most cautious action

    Prioritizes safety: escalate > investigate > proceed
    If ANY persona says escalate, we escalate.
    If ANY persona says investigate (and none say escalate), we investigate.
    Only proceed if all personas agree to proceed.

    Good for security-critical or high-risk tasks.

    Args:
        persona_actions: {persona_id: action}
        persona_confidences: Not used in this strategy
        persona_assessments: Not used in this strategy

    Returns:
        ArbitrationResult with most cautious action
    """
    if not persona_actions:
        raise ValueError("No persona actions provided")

    logger.info(f"Arbitrating {len(persona_actions)} actions using pessimistic strategy")

    # Check for escalate
    escalate_personas = [pid for pid, act in persona_actions.items() if act == "escalate"]
    if escalate_personas:
        return ArbitrationResult(
            final_action="escalate",
            reasoning=f"Pessimistic: {len(escalate_personas)} persona(s) requested escalate: {escalate_personas}",
            confidence=1.0,  # High confidence in caution
            persona_votes=persona_actions,
            persona_weights={pid: 1.0 for pid in persona_actions},
            conflicts_found=[f"{len(escalate_personas)} wanted escalate"],
            consensus_level=len(escalate_personas) / len(persona_actions),
            arbitration_strategy="pessimistic"
        )

    # Check for investigate
    investigate_personas = [pid for pid, act in persona_actions.items() if act == "investigate"]
    if investigate_personas:
        return ArbitrationResult(
            final_action="investigate",
            reasoning=f"Pessimistic: {len(investigate_personas)} persona(s) requested investigate: {investigate_personas}",
            confidence=0.8,  # Good confidence in caution
            persona_votes=persona_actions,
            persona_weights={pid: 1.0 for pid in persona_actions},
            conflicts_found=[f"{len(investigate_personas)} wanted investigate"],
            consensus_level=len(investigate_personas) / len(persona_actions),
            arbitration_strategy="pessimistic"
        )

    # All personas agree to proceed
    return ArbitrationResult(
        final_action="proceed",
        reasoning="Pessimistic: All personas agree to proceed",
        confidence=1.0,  # Full consensus
        persona_votes=persona_actions,
        persona_weights={pid: 1.0 for pid in persona_actions},
        conflicts_found=[],
        consensus_level=1.0,
        arbitration_strategy="pessimistic"
    )


def domain_weighted_arbitration(
    persona_actions: Dict[str, str],
    persona_confidences: Dict[str, float],
    persona_assessments: Dict[str, EpistemicAssessmentSchema],
    persona_profiles: Dict[str, PersonaProfile],
    task: str = "",
    context: Optional[Dict] = None
) -> ArbitrationResult:
    """
    Domain-weighted arbitration

    Weight votes by how relevant each persona's domain is to the task.
    For example, for "implement caching", performance persona's vote
    carries more weight.

    Args:
        persona_actions: {persona_id: action}
        persona_confidences: {persona_id: confidence}
        persona_assessments: {persona_id: assessment}
        persona_profiles: {persona_id: profile} with focus_domains
        task: Task description for domain matching
        context: Optional context

    Returns:
        ArbitrationResult with domain-weighted action
    """
    if not persona_actions:
        raise ValueError("No persona actions provided")
    if not persona_profiles:
        logger.warning("No persona profiles provided, falling back to confidence-weighted")
        return confidence_weighted_arbitration(persona_actions, persona_confidences)

    logger.info(f"Arbitrating {len(persona_actions)} actions using domain-weighted strategy")

    # Calculate domain relevance weights
    task_lower = task.lower()
    domain_weights = {}

    for persona_id, profile in persona_profiles.items():
        # Count how many focus domains appear in task
        relevance = 0
        for domain in profile.epistemic_config.focus_domains:
            if domain.lower() in task_lower:
                relevance += 1

        # If no domain match, give minimum weight
        domain_weights[persona_id] = max(0.1, relevance)

    # Normalize weights
    total_domain_weight = sum(domain_weights.values())
    domain_weights = {
        pid: w / total_domain_weight
        for pid, w in domain_weights.items()
    }

    # Combine with confidence
    combined_weights = {}
    for persona_id in persona_actions:
        domain_w = domain_weights.get(persona_id, 0.1)
        conf_w = persona_confidences.get(persona_id, 0.5)
        combined_weights[persona_id] = domain_w * conf_w

    logger.info(f"Domain weights: {domain_weights}")
    logger.info(f"Combined weights: {combined_weights}")

    # Calculate weighted votes
    action_weights = {}
    for persona_id, action in persona_actions.items():
        weight = combined_weights.get(persona_id, 0.5)
        action_weights[action] = action_weights.get(action, 0.0) + weight

    # Choose action with highest weight
    final_action = max(action_weights.items(), key=lambda x: x[1])[0]
    final_weight = action_weights[final_action]

    total_weight = sum(action_weights.values())
    consensus = final_weight / total_weight if total_weight > 0 else 0.0

    reasoning = f"Domain-weighted: {final_action} (weight={final_weight:.2f}/{total_weight:.2f})"

    conflicts = []
    for action, weight in action_weights.items():
        if action != final_action:
            conflicts.append(f"{weight:.2f} weight voted {action} vs {final_action}")

    return ArbitrationResult(
        final_action=final_action,
        reasoning=reasoning,
        confidence=consensus,
        persona_votes=persona_actions,
        persona_weights=combined_weights,
        conflicts_found=conflicts,
        consensus_level=consensus,
        arbitration_strategy="domain_weighted"
    )


def escalate_on_conflict_arbitration(
    persona_actions: Dict[str, str],
    persona_confidences: Optional[Dict[str, float]] = None,
    persona_assessments: Optional[Dict[str, EpistemicAssessmentSchema]] = None
) -> ArbitrationResult:
    """
    Escalate on conflict arbitration

    If there's ANY disagreement between personas, escalate to human.
    Only proceed if all personas unanimously agree.

    Very safe but may escalate frequently.

    Args:
        persona_actions: {persona_id: action}
        persona_confidences: Not used
        persona_assessments: Not used

    Returns:
        ArbitrationResult - escalate if any conflict, otherwise unanimous action
    """
    if not persona_actions:
        raise ValueError("No persona actions provided")

    logger.info(f"Arbitrating {len(persona_actions)} actions using escalate-on-conflict strategy")

    unique_actions = set(persona_actions.values())

    if len(unique_actions) == 1:
        # Unanimous
        final_action = list(unique_actions)[0]
        return ArbitrationResult(
            final_action=final_action,
            reasoning=f"Unanimous: All {len(persona_actions)} personas agree on {final_action}",
            confidence=1.0,
            persona_votes=persona_actions,
            persona_weights={pid: 1.0 for pid in persona_actions},
            conflicts_found=[],
            consensus_level=1.0,
            arbitration_strategy="escalate_on_conflict"
        )
    else:
        # Conflict - escalate
        vote_summary = Counter(persona_actions.values())
        conflicts = [f"{count} voted {action}" for action, count in vote_summary.items()]

        return ArbitrationResult(
            final_action="escalate",
            reasoning=f"Conflict detected: {conflicts}. Escalating to human.",
            confidence=1.0,  # Confident in escalation
            persona_votes=persona_actions,
            persona_weights={pid: 1.0 for pid in persona_actions},
            conflicts_found=conflicts,
            consensus_level=0.0,  # No consensus
            arbitration_strategy="escalate_on_conflict"
        )


def _choose_most_cautious(actions: List[str]) -> str:
    """
    Choose most cautious action from a list

    Caution ranking: escalate > investigate > proceed
    """
    if "escalate" in actions:
        return "escalate"
    elif "investigate" in actions:
        return "investigate"
    else:
        return "proceed"


# Strategy registry
ARBITRATION_STRATEGIES = {
    "majority_vote": majority_vote_arbitration,
    "confidence_weighted": confidence_weighted_arbitration,
    "pessimistic": pessimistic_arbitration,
    "domain_weighted": domain_weighted_arbitration,
    "escalate_on_conflict": escalate_on_conflict_arbitration,
}


def get_arbitration_strategy(strategy_name: str):
    """Get arbitration strategy function by name"""
    if strategy_name not in ARBITRATION_STRATEGIES:
        raise ValueError(
            f"Unknown arbitration strategy: {strategy_name}. "
            f"Available: {list(ARBITRATION_STRATEGIES.keys())}"
        )
    return ARBITRATION_STRATEGIES[strategy_name]
