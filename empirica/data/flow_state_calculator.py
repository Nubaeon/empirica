"""
Flow State Calculator for AI Productivity

Calculates flow state metrics from epistemic vectors to measure AI work effectiveness.
Flow state = optimal productivity characterized by focus, capability, and progress.
"""

from typing import Dict, List, Optional, Tuple


def calculate_flow_score(vectors: Dict[str, float]) -> float:
    """
    Calculate flow state score (0-100) from epistemic vectors.

    Flow state formula:
    - Engagement (25%): Focus and immersion
    - Capability (20%): Combined know + do
    - Clarity (15%): Clear goals
    - Confidence (15%): Low uncertainty
    - Completion (10%): Progress sense
    - Impact (10%): Meaningful work
    - Coherence (5%): Logical flow

    Args:
        vectors: Dict of epistemic vectors (0.0-1.0)

    Returns:
        Flow score (0-100), or 0.0 if insufficient data
    """
    # Required vectors for flow calculation
    required = ['engagement', 'know', 'do', 'clarity', 'uncertainty',
                'completion', 'impact', 'coherence']

    # Check if we have required vectors
    if not all(v in vectors for v in required):
        return 0.0

    # Extract vectors with defaults
    engagement = vectors.get('engagement', 0.5)
    know = vectors.get('know', 0.5)
    do = vectors.get('do', 0.5)
    clarity = vectors.get('clarity', 0.5)
    uncertainty = vectors.get('uncertainty', 0.5)
    completion = vectors.get('completion', 0.5)
    impact = vectors.get('impact', 0.5)
    coherence = vectors.get('coherence', 0.5)

    # Calculate flow score
    capability = (know + do) / 2.0
    confidence = 1.0 - uncertainty

    flow_score = (
        engagement * 0.25 +
        capability * 0.20 +
        clarity * 0.15 +
        confidence * 0.15 +
        completion * 0.10 +
        impact * 0.10 +
        coherence * 0.05
    ) * 100.0

    return round(flow_score, 1)


def classify_flow_state(flow_score: float) -> Tuple[str, str]:
    """
    Classify flow state into categories with emoji.

    Args:
        flow_score: Flow score (0-100)

    Returns:
        Tuple of (state_name, emoji)
    """
    if flow_score >= 80:
        return ("Deep Flow", "🔥")
    elif flow_score >= 65:
        return ("Flow State", "✨")
    elif flow_score >= 50:
        return ("Productive", "⚡")
    elif flow_score >= 35:
        return ("Working", "💼")
    else:
        return ("Struggling", "⚠️")


def identify_flow_blockers(vectors: Dict[str, float], threshold: float = 0.4) -> List[str]:
    """
    Identify what's blocking flow state.

    Args:
        vectors: Epistemic vectors
        threshold: Minimum acceptable value (default: 0.4)

    Returns:
        List of flow blocker messages
    """
    blockers = []

    # Check key flow factors
    if vectors.get('engagement', 0.5) < threshold:
        blockers.append("Low engagement - task may be unclear or uninteresting")

    if vectors.get('know', 0.5) < threshold:
        blockers.append("Low knowledge - need more context/learning")

    if vectors.get('do', 0.5) < threshold:
        blockers.append("Low capability - missing skills or tools")

    if vectors.get('clarity', 0.5) < threshold:
        blockers.append("Low clarity - goals or requirements unclear")

    if vectors.get('uncertainty', 0.5) > 0.6:
        blockers.append("High uncertainty - too many unknowns")

    if vectors.get('completion', 0.5) < 0.3:
        blockers.append("Low completion - task just starting or stalled")

    if vectors.get('impact', 0.5) < threshold:
        blockers.append("Low impact - work doesn't feel meaningful")

    return blockers


def calculate_flow_trend(flow_scores: List[float]) -> Tuple[str, str]:
    """
    Calculate flow trend from recent scores.

    Args:
        flow_scores: List of recent flow scores (oldest to newest)

    Returns:
        Tuple of (trend_description, arrow_emoji)
    """
    if len(flow_scores) < 2:
        return ("Not enough data", "")

    # Calculate trend (simple linear)
    recent_avg = sum(flow_scores[-3:]) / len(flow_scores[-3:])
    older_avg = sum(flow_scores[:-3]) / len(flow_scores[:-3]) if len(flow_scores) > 3 else flow_scores[0]

    delta = recent_avg - older_avg

    if delta > 10:
        return ("Strong improvement", "📈")
    elif delta > 5:
        return ("Improving", "↗️")
    elif delta > -5:
        return ("Stable", "→")
    elif delta > -10:
        return ("Declining", "↘️")
    else:
        return ("Sharp decline", "📉")


def get_flow_triggers() -> List[Dict[str, str]]:
    """
    Get flow state triggers (conditions that enable flow).

    Returns:
        List of trigger dicts with name, description, and vector mapping
    """
    return [
        {
            "name": "Clear goals",
            "description": "Know exactly what to accomplish",
            "vector": "clarity",
            "threshold": 0.7
        },
        {
            "name": "Immediate feedback",
            "description": "Progress is visible and measurable",
            "vector": "completion",
            "threshold": 0.5
        },
        {
            "name": "Challenge-skill balance",
            "description": "Task difficulty matches capability",
            "vector": "do",
            "threshold": 0.6
        },
        {
            "name": "Low distractions",
            "description": "Clear signal, minimal noise",
            "vector": "signal",
            "threshold": 0.6
        },
        {
            "name": "Intrinsic motivation",
            "description": "Work feels meaningful and impactful",
            "vector": "impact",
            "threshold": 0.6
        }
    ]


def check_flow_triggers(vectors: Dict[str, float]) -> Dict[str, bool]:
    """
    Check which flow triggers are present.

    Args:
        vectors: Epistemic vectors

    Returns:
        Dict mapping trigger names to boolean (present/absent)
    """
    triggers = get_flow_triggers()
    results = {}

    for trigger in triggers:
        vector_name = trigger['vector']
        threshold = trigger['threshold']
        value = vectors.get(vector_name, 0.0)
        results[trigger['name']] = value >= threshold

    return results
