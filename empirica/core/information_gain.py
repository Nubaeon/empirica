"""
Information Gain Estimator - Determine value of additional investigation.

Provides functions to estimate whether spawning more agents or continuing
investigation will yield meaningful epistemic gains. Used by the parallel
orchestrator to decide when to stop spawning agents.

Key concept: Information gain follows diminishing returns. The first agent
investigating a domain yields high gain; subsequent agents yield less.
When expected gain falls below a threshold, it's better to stop.
"""

import logging
import math
from typing import Dict, List

logger = logging.getLogger(__name__)

# Thresholds
DEFAULT_MIN_GAIN = 0.1  # Below this, don't bother spawning
DEFAULT_NOVELTY_FLOOR = 0.2  # Minimum novelty to consider a finding useful
DEFAULT_STALE_ROUNDS = 2  # Rounds without novel findings = stop


def estimate_information_gain(
    domain: str,
    current_vectors: Dict[str, float],
    prior_findings: List[str],
    dead_ends: int = 0,
) -> float:
    """
    Estimate expected information gain from investigating a domain.

    Higher uncertainty + lower knowledge = higher gain.
    More prior findings = diminishing returns.
    Dead ends reduce expected gain.

    Args:
        domain: Investigation domain name
        current_vectors: Current epistemic state vectors
        prior_findings: List of existing findings for this domain
        dead_ends: Count of dead ends in this domain

    Returns:
        Expected information gain (0.0-1.0)
    """
    uncertainty = current_vectors.get("uncertainty", 0.5)
    know = current_vectors.get("know", 0.5)
    context = current_vectors.get("context", 0.5)

    # Base gain: Shannon entropy of uncertainty
    p = max(0.01, min(0.99, uncertainty))
    entropy = -p * math.log2(p) - (1 - p) * math.log2(1 - p)

    # Knowledge gap multiplier
    knowledge_gap = max(0.01, 1.0 - know)

    # Context gap (less context = more to discover)
    context_gap = max(0.01, 1.0 - context)

    # Combined base gain
    base_gain = entropy * (0.6 * knowledge_gap + 0.4 * context_gap)

    # Diminishing returns from prior findings
    dr = diminishing_returns(domain, len(prior_findings))

    # Dead end penalty
    dead_end_factor = max(0.05, 1.0 - (dead_ends * 0.4))

    gain = base_gain * dr * dead_end_factor

    logger.debug(
        f"Information gain for '{domain}': "
        f"base={base_gain:.3f}, dr={dr:.3f}, dead_end={dead_end_factor:.3f}, "
        f"final={gain:.3f}"
    )

    return min(1.0, gain)


def diminishing_returns(domain: str, findings_count: int, rate: float = 0.3) -> float:
    """
    Calculate diminishing returns decay factor.

    Returns a value in (0, 1] where 1 means full returns (no prior findings)
    and values approach 0 as findings accumulate.

    Uses exponential decay: f(n) = e^(-rate * n)

    Args:
        domain: Domain name (for logging)
        findings_count: Number of existing findings
        rate: Decay rate (higher = faster diminishing)

    Returns:
        Decay factor (0.0-1.0)
    """
    factor = math.exp(-rate * findings_count)
    logger.debug(f"Diminishing returns for '{domain}': n={findings_count}, factor={factor:.3f}")
    return factor


def should_spawn_more(
    budget_remaining: int,
    gain_estimate: float,
    rounds_without_novel: int = 0,
    min_gain: float = DEFAULT_MIN_GAIN,
    stale_rounds: int = DEFAULT_STALE_ROUNDS,
) -> bool:
    """
    Determine whether to spawn additional investigation agents.

    Args:
        budget_remaining: Findings budget remaining
        gain_estimate: Expected information gain for next agent
        rounds_without_novel: Consecutive rounds without novel findings
        min_gain: Minimum gain threshold to justify spawning
        stale_rounds: Rounds without novelty before stopping

    Returns:
        True if spawning more agents is worthwhile
    """
    # Hard stop: no budget
    if budget_remaining <= 0:
        logger.info("Stop spawning: budget exhausted")
        return False

    # Hard stop: stale investigation
    if rounds_without_novel >= stale_rounds:
        logger.info(
            f"Stop spawning: {rounds_without_novel} rounds without novel findings "
            f"(threshold: {stale_rounds})"
        )
        return False

    # Gain threshold
    if gain_estimate < min_gain:
        logger.info(
            f"Stop spawning: expected gain {gain_estimate:.3f} below "
            f"threshold {min_gain:.3f}"
        )
        return False

    logger.debug(
        f"Continue spawning: budget={budget_remaining}, gain={gain_estimate:.3f}, "
        f"stale_rounds={rounds_without_novel}"
    )
    return True


def novelty_score(
    finding: str,
    existing_findings: List[str],
    jaccard_threshold: float = 0.7,
) -> float:
    """
    Calculate novelty of a finding relative to existing findings.

    Uses Jaccard similarity on word sets. A finding is novel if it has
    low similarity to all existing findings.

    Args:
        finding: New finding text
        existing_findings: List of existing finding texts
        jaccard_threshold: Similarity above this = not novel

    Returns:
        Novelty score (0.0 = duplicate, 1.0 = completely novel)
    """
    if not existing_findings:
        return 1.0

    finding_words = _tokenize(finding)
    if not finding_words:
        return 0.0

    max_similarity = 0.0
    for existing in existing_findings:
        existing_words = _tokenize(existing)
        if not existing_words:
            continue

        intersection = finding_words & existing_words
        union = finding_words | existing_words
        similarity = len(intersection) / len(union) if union else 0.0
        max_similarity = max(max_similarity, similarity)

    # Novelty is inverse of max similarity
    novelty = 1.0 - max_similarity

    return novelty


def _tokenize(text: str) -> set:
    """Tokenize text into word set for Jaccard comparison."""
    import re
    words = set(re.findall(r'\b\w{3,}\b', text.lower()))
    # Remove very common words
    stop_words = {
        'the', 'and', 'for', 'that', 'this', 'with', 'from', 'are', 'was',
        'were', 'been', 'have', 'has', 'had', 'not', 'but', 'can', 'will',
        'should', 'would', 'could', 'which', 'there', 'their', 'about',
    }
    return words - stop_words
