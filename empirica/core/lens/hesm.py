"""
HESM — Human Epistemic State Model (per chunk).

Computes 13-vector epistemic state for each incoming chunk by searching
multiple Qdrant collections against the human's profile. Uses the same
13 vectors as Empirica (AI-side) for direct comparison.

Primary vectors for delta scoring (7):
  exposure, comprehension, retention, fluency, integration, uncertainty, interest

Supplementary vectors (6):
  context, clarity, density, velocity, completion, impact

Composite novelty = weighted sum of primary vectors.
Classification: novel (<0.3), partial (0.3-0.7), known (>0.7).
Gap-closing override: chunk matches open unknown → always novel.
"""

import logging
import math
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from empirica.core.lens.profile import HESMState, HumanEpistemicProfile, Unknown

logger = logging.getLogger(__name__)

# Composite novelty weights (primary 7 vectors)
NOVELTY_WEIGHTS = {
    "exposure": 0.25,
    "comprehension": 0.25,
    "retention": 0.15,
    "fluency": 0.05,
    "integration": 0.10,
    "uncertainty": 0.10,
    "interest": 0.10,
}

# Classification thresholds
NOVEL_THRESHOLD = 0.3
KNOWN_THRESHOLD = 0.7
UNKNOWN_MATCH_THRESHOLD = 0.75  # Cosine sim for gap-closing override


@dataclass
class ChunkSearchResults:
    """Search results from multiple collections for one chunk."""
    docs_hits: List[Dict[str, Any]]
    memory_hits: List[Dict[str, Any]]
    eidetic_hits: List[Dict[str, Any]]
    episodic_hits: List[Dict[str, Any]]
    unknown_matches: List[Dict[str, Any]]  # Matched open unknowns
    goal_matches: List[Dict[str, Any]]  # Matched active goals


def compute_hesm(
    profile: HumanEpistemicProfile,
    chunk_text: str,
    search_results: ChunkSearchResults,
) -> HESMState:
    """
    Compute 13-vector HESM for a single chunk against the human's profile.

    Args:
        profile: Human epistemic profile
        chunk_text: The chunk text
        search_results: Multi-collection search results for this chunk

    Returns:
        HESMState with computed vectors
    """
    now = time.time()

    # --- Primary vectors ---

    # 1. Exposure: max similarity in docs collection, with time decay
    exposure = _compute_exposure(search_results.docs_hits, now)

    # 2. Comprehension: combined memory + eidetic similarity
    comprehension = _compute_comprehension(
        search_results.memory_hits, search_results.eidetic_hits
    )

    # 3. Retention: exposure * FSRS-style decay
    retention = _compute_retention(exposure, search_results.docs_hits, now)

    # 4. Fluency: interaction density on topic
    fluency = _compute_fluency(search_results.memory_hits, search_results.eidetic_hits)

    # 5. Integration: cross-collection hit count
    integration = _compute_integration(search_results)

    # 6. Uncertainty: score variance + open unknown match bonus
    uncertainty = _compute_uncertainty(
        search_results, profile.open_unknowns
    )

    # 7. Interest: goal relevance + diminishing returns inverse
    interest = _compute_interest(
        search_results.goal_matches,
        search_results.memory_hits,
    )

    # --- Supplementary vectors ---
    context = min(1.0, profile.total_docs / 50.0) if profile.total_docs else 0.0
    clarity = comprehension * 0.8  # Proxy: comprehension → ability to articulate
    density = min(1.0, len(search_results.memory_hits) / 10.0)
    velocity = 0.0  # Requires temporal sequence
    completion_val = 0.0  # Task-specific
    impact_val = 0.0  # Task-specific

    return HESMState(
        exposure=round(exposure, 3),
        comprehension=round(comprehension, 3),
        fluency=round(fluency, 3),
        context=round(context, 3),
        clarity=round(clarity, 3),
        integration=round(integration, 3),
        interest=round(interest, 3),
        density=round(density, 3),
        retention=round(retention, 3),
        velocity=round(velocity, 3),
        completion=round(completion_val, 3),
        impact=round(impact_val, 3),
        uncertainty=round(uncertainty, 3),
    )


def composite_novelty(hesm: HESMState) -> float:
    """
    Compute composite novelty score from HESM vectors.

    Higher = more known to the human (less novel).
    Invert for novelty: novelty = 1.0 - composite.

    Returns:
        Float 0.0-1.0 where 1.0 = completely known
    """
    vals = hesm.to_dict()
    score = sum(
        NOVELTY_WEIGHTS.get(k, 0.0) * vals.get(k, 0.0)
        for k in NOVELTY_WEIGHTS
    )
    return round(max(0.0, min(1.0, score)), 3)


def classify_chunk(
    hesm: HESMState,
    unknown_match: bool = False,
    goal_match: bool = False,
) -> str:
    """
    Classify chunk based on HESM composite.

    Returns:
        "novel", "partial", "known", or "gap_closing"
    """
    # Gap-closing override
    if unknown_match:
        return "gap_closing"

    score = composite_novelty(hesm)
    if score < NOVEL_THRESHOLD:
        return "novel"
    elif score > KNOWN_THRESHOLD:
        return "known"
    else:
        return "partial"


# --- Vector computation helpers ---

def _compute_exposure(docs_hits: List[Dict], now: float) -> float:
    """Exposure = max similarity in docs, with time decay."""
    if not docs_hits:
        return 0.0

    max_sim = 0.0
    best_ts = now

    for hit in docs_hits:
        sim = hit.get("score", 0.0)
        if sim > max_sim:
            max_sim = sim
            best_ts = hit.get("timestamp", now)

    # Time decay: 30-day half-life
    if isinstance(best_ts, str):
        try:
            best_ts = float(best_ts)
        except (ValueError, TypeError):
            best_ts = now

    age_days = max(0, (now - best_ts) / 86400)
    decay = math.exp(-age_days / 30.0)

    return max_sim * decay


def _compute_comprehension(
    memory_hits: List[Dict],
    eidetic_hits: List[Dict],
) -> float:
    """Comprehension = weighted max of memory and eidetic similarity."""
    max_memory = max((h.get("score", 0.0) for h in memory_hits), default=0.0)
    max_eidetic = max((h.get("score", 0.0) for h in eidetic_hits), default=0.0)
    return max(max_memory * 0.6, max_eidetic * 0.4)


def _compute_retention(
    exposure: float,
    docs_hits: List[Dict],
    now: float,
) -> float:
    """Retention = exposure * FSRS-style decay from best match timestamp."""
    if not docs_hits or exposure == 0.0:
        return 0.0

    best_ts = now
    max_sim = 0.0
    for hit in docs_hits:
        sim = hit.get("score", 0.0)
        if sim > max_sim:
            max_sim = sim
            best_ts = hit.get("timestamp", now)

    if isinstance(best_ts, str):
        try:
            best_ts = float(best_ts)
        except (ValueError, TypeError):
            best_ts = now

    age_days = max(0, (now - best_ts) / 86400)
    # FSRS-inspired: stability starts at 1 day, decays
    half_life = 30.0
    decay = math.exp(-age_days / half_life)
    return exposure * decay


def _compute_fluency(
    memory_hits: List[Dict],
    eidetic_hits: List[Dict],
) -> float:
    """Fluency = interaction density proxy from hit count."""
    total_hits = len(memory_hits) + len(eidetic_hits)
    expected = 5  # Expected hits for full fluency
    return min(1.0, total_hits / expected)


def _compute_integration(search_results: ChunkSearchResults) -> float:
    """Integration = fraction of collections with hits."""
    total_collections = 4  # docs, memory, eidetic, episodic
    hits = 0
    if search_results.docs_hits:
        hits += 1
    if search_results.memory_hits:
        hits += 1
    if search_results.eidetic_hits:
        hits += 1
    if search_results.episodic_hits:
        hits += 1
    return hits / total_collections


def _compute_uncertainty(
    search_results: ChunkSearchResults,
    open_unknowns: List[Unknown],
) -> float:
    """
    Uncertainty = score variance + open unknown match bonus.

    Low consistency across collections → high uncertainty.
    If chunk matches an open unknown → uncertainty goes UP (value increases).
    """
    scores = []
    for hits in [search_results.docs_hits, search_results.memory_hits,
                 search_results.eidetic_hits]:
        if hits:
            scores.append(max(h.get("score", 0.0) for h in hits))
        else:
            scores.append(0.0)

    if not any(scores):
        return 0.8  # High uncertainty when no data

    mean = sum(scores) / len(scores)
    variance = sum((s - mean) ** 2 for s in scores) / len(scores)
    inconsistency = min(1.0, variance * 4)  # Scale up

    # Unknown match bonus: matching an open unknown = higher value
    unknown_bonus = 0.2 if search_results.unknown_matches else 0.0

    return min(1.0, (1.0 - mean) * 0.6 + inconsistency * 0.2 + unknown_bonus)


def _compute_interest(
    goal_matches: List[Dict],
    memory_hits: List[Dict],
) -> float:
    """Interest = goal relevance + diminishing returns inverse."""
    goal_sim = max((g.get("score", 0.0) for g in goal_matches), default=0.0)

    # Diminishing returns: fewer memory hits = more interest (novel territory)
    if memory_hits:
        dr_inv = max(0.0, 1.0 - len(memory_hits) / 10.0)
    else:
        dr_inv = 1.0  # Completely novel = high interest

    return max(goal_sim, dr_inv * 0.5)
