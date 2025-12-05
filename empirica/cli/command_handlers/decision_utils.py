"""Decision logic utilities - Single source of truth

Includes:
- Basic decision logic (calculate_decision, get_recommendation_from_vectors)
- Cognitive load assessment from feedback loops config
- Epistemic vector feedback loop responses
"""

import yaml
import logging
import os

logger = logging.getLogger(__name__)


def load_feedback_loops_config() -> dict:
    """
    Load feedback loops configuration from YAML.

    Returns:
        Dict with feedback loops config, or empty dict if file not found
    """
    config_path = os.path.join(
        os.path.dirname(__file__),
        "../../config/mco/feedback_loops.yaml"
    )

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            return config or {}
    except FileNotFoundError:
        logger.warning(f"Feedback loops config not found at {config_path}")
        return {}
    except Exception as e:
        logger.warning(f"Failed to load feedback loops config: {e}")
        return {}


def get_agent_feedback_loop_config(ai_id: str) -> dict:
    """
    Get feedback loop configuration for a specific AI agent.

    Loads the agent-specific config, falling back to defaults as needed.

    Args:
        ai_id: Agent identifier (e.g., 'claude-code', 'claude-sonnet')

    Returns:
        Dict with agent's feedback loop configuration
    """
    config = load_feedback_loops_config()
    feedback_loops = config.get('feedback_loops', {})

    # Try agent-specific config first
    if ai_id in feedback_loops:
        return feedback_loops[ai_id]

    # Fall back to global default
    return feedback_loops.get('global_default', {})


def evaluate_cognitive_load(density: float, ai_id: str = None) -> dict:
    """
    Evaluate cognitive load based on DENSITY vector and feedback loop config.

    Uses actual DENSITY epistemic measurement, not heuristics.

    Args:
        density: DENSITY epistemic vector (0.0-1.0)
        ai_id: Agent identifier for agent-specific thresholds

    Returns:
        Dict with:
        - level: 'sustainable', 'high', or 'overwhelmed'
        - severity: 'info', 'warning', or 'critical'
        - checkpoint_recommended: bool
        - checkpoint_when: 'none', 'after_phase', or 'immediately'
        - actions: list of recommended actions
        - message: human-readable description
    """
    # Get agent-specific thresholds
    if ai_id:
        agent_config = get_agent_feedback_loop_config(ai_id)
        cognitive_load_cfg = agent_config.get('cognitive_load_response', {})
        thresholds = cognitive_load_cfg.get('thresholds', {})
    else:
        thresholds = {}

    # Use agent-specific or default thresholds
    sustainable_threshold = thresholds.get('sustainable', 0.60)
    high_threshold = thresholds.get('high', 0.75)
    overwhelmed_threshold = thresholds.get('overwhelmed', 0.90)

    # Determine load level
    if density > overwhelmed_threshold:
        level = 'overwhelmed'
        severity = 'critical'
        checkpoint_when = 'immediately'
        checkpoint_recommended = True
        actions = ['create_emergency_checkpoint', 'halt_act_phase']
        message = f"COGNITIVE OVERLOAD: DENSITY {density:.2f} > {overwhelmed_threshold}"

    elif density > high_threshold:
        level = 'high'
        severity = 'warning'
        checkpoint_when = 'after_current_phase'
        checkpoint_recommended = True
        actions = ['suggest_checkpoint', 'highlight_in_statusline']
        message = f"HIGH COGNITIVE LOAD: DENSITY {density:.2f} > {high_threshold}"

    else:
        level = 'sustainable'
        severity = 'info'
        checkpoint_when = 'none'
        checkpoint_recommended = False
        actions = []
        message = f"SUSTAINABLE LOAD: DENSITY {density:.2f} <= {sustainable_threshold}"

    return {
        'level': level,
        'severity': severity,
        'checkpoint_recommended': checkpoint_recommended,
        'checkpoint_when': checkpoint_when,
        'actions': actions,
        'message': message,
        'density': density
    }


def get_cognitive_load_decision_impact(density: float, ai_id: str = None) -> dict:
    """
    Determine how cognitive load should affect CHECK phase decision gate.

    Args:
        density: DENSITY epistemic vector (0.0-1.0)
        ai_id: Agent identifier for agent-specific config

    Returns:
        Dict with:
        - decision_impact: 'proceed', 'proceed_with_caution', 'recommend_investigate'
        - confidence_adjustment: float to add/subtract from confidence gate
        - message: explanation for statusline
    """
    load_assessment = evaluate_cognitive_load(density, ai_id)

    if load_assessment['level'] == 'overwhelmed':
        return {
            'decision_impact': 'recommend_investigate',
            'confidence_adjustment': -0.20,
            'message': 'Cognitive overload - Recommend returning to INVESTIGATE phase'
        }
    elif load_assessment['level'] == 'high':
        return {
            'decision_impact': 'proceed_with_caution',
            'confidence_adjustment': -0.10,
            'message': 'High cognitive load - CHECK gate raised to 0.75+ confidence'
        }
    else:
        return {
            'decision_impact': 'proceed',
            'confidence_adjustment': 0.0,
            'message': None
        }


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
