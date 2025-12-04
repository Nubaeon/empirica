"""Decision logic utilities - Single source of truth"""


def calculate_decision(confidence: float) -> str:
    """
    Determine next action based on confidence assessment.

    Args:
        confidence: Confidence score (0.0-1.0)

    Returns:
        Decision string: "proceed", "investigate", or "proceed_with_caution"
    """
    if confidence >= 0.7:
        return "proceed"
    elif confidence <= 0.3:
        return "investigate"
    else:
        return "proceed_with_caution"


def get_recommendation_from_vectors(vectors: dict) -> dict:
    """
    Get recommendation based on epistemic vectors (multi-factor decision).

    Used when multiple epistemic vectors are available for nuanced decisions.

    Args:
        vectors: Dict with epistemic vector scores (know, do, context, uncertainty, etc.)

    Returns:
        Dict with 'action', 'message', and 'warnings' keys
    """
    know = vectors.get('know', 0.5)
    do = vectors.get('do', 0.5)
    context = vectors.get('context', 0.5)
    uncertainty = vectors.get('uncertainty', 0.5)

    avg_foundation = (know + do + context) / 3.0

    warnings = []

    if know < 0.5:
        warnings.append("Low domain knowledge - consider research/investigation")
    if do < 0.5:
        warnings.append("Low task capability - proceed with caution or seek guidance")
    if context < 0.5:
        warnings.append("Insufficient context - gather more information")
    if uncertainty > 0.7:
        warnings.append("High uncertainty - investigation strongly recommended")

    if avg_foundation >= 0.7 and uncertainty < 0.5:
        return {
            "action": "proceed",
            "message": "Proceed with confidence",
            "warnings": warnings
        }
    elif avg_foundation >= 0.5:
        return {
            "action": "proceed_cautiously",
            "message": "Proceed with moderate supervision",
            "warnings": warnings
        }
    else:
        return {
            "action": "investigate",
            "message": "Investigation recommended before proceeding",
            "warnings": warnings
        }
