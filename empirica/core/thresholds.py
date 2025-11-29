"""
Dynamic Threshold Configuration for Empirica

This module provides backwards-compatible access to thresholds that are now
loaded dynamically from cascade_styles.yaml (MCO architecture).

Usage:
    # Legacy code (still works):
    from empirica.core.thresholds import ENGAGEMENT_THRESHOLD
    
    # New code (recommended):
    from empirica.config import get_threshold_config
    config = get_threshold_config()
    engagement = config.get('engagement_threshold')

Architecture:
    - Thresholds are now part of MCO (Meta-Agent Configuration Object)
    - Loaded from empirica/config/mco/cascade_styles.yaml
    - Profiles: default, exploratory, rigorous, rapid, expert, novice
    - Sentinel can switch profiles or override individual thresholds
    - Backwards compatibility: Module-level constants access current profile
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Initialize threshold loader (lazy import to avoid circular dependencies)
_threshold_config = None


def _get_config():
    """Lazy-load threshold configuration"""
    global _threshold_config
    if _threshold_config is None:
        try:
            from empirica.config.threshold_loader import get_threshold_config
            _threshold_config = get_threshold_config()
        except Exception as e:
            logger.warning(f"Failed to load dynamic threshold config: {e}")
            # Will fall back to hardcoded defaults below
    return _threshold_config


def _get_threshold(key_path: str, hardcoded_default: Any) -> Any:
    """
    Get threshold value from dynamic config, fallback to hardcoded default.
    
    This provides backwards compatibility - existing code importing constants
    will get values from the current active profile.
    """
    config = _get_config()
    if config is not None:
        return config.get(key_path, hardcoded_default)
    return hardcoded_default


# =============================================================================
# BACKWARDS COMPATIBLE CONSTANTS
# =============================================================================
# These constants now dynamically load from the active threshold profile.
# If YAML config is unavailable, they fall back to hardcoded defaults.

# Engagement Gate Threshold
ENGAGEMENT_THRESHOLD = _get_threshold('engagement_threshold', 0.60)

# Critical decision thresholds (system actions)
CRITICAL_THRESHOLDS = {
    'coherence_min': _get_threshold('critical.coherence_min', 0.50),
    'density_max': _get_threshold('critical.density_max', 0.90),
    'change_min': _get_threshold('critical.change_min', 0.50),
}

# Uncertainty Thresholds
UNCERTAINTY_LOW = _get_threshold('uncertainty.low', 0.70)
UNCERTAINTY_MODERATE = _get_threshold('uncertainty.moderate', 0.30)

# Comprehension Thresholds
COMPREHENSION_HIGH = _get_threshold('comprehension.high', 0.80)
COMPREHENSION_MODERATE = _get_threshold('comprehension.moderate', 0.50)
CLARITY_THRESHOLD = _get_threshold('comprehension.clarity_min', 0.50)
SIGNAL_THRESHOLD = _get_threshold('comprehension.signal_min', 0.50)
COHERENCE_THRESHOLD = _get_threshold('comprehension.coherence_min', 0.50)

# Execution Thresholds
EXECUTION_HIGH = _get_threshold('execution.high', 0.80)
EXECUTION_MODERATE = _get_threshold('execution.moderate', 0.60)
STATE_MAPPING_THRESHOLD = _get_threshold('execution.state_mapping_min', 0.60)
COMPLETION_THRESHOLD = _get_threshold('execution.completion_min', 0.80)
IMPACT_THRESHOLD = _get_threshold('execution.impact_min', 0.50)

# Confidence Thresholds
CONFIDENCE_HIGH = _get_threshold('confidence.high', 0.85)
CONFIDENCE_MODERATE = _get_threshold('confidence.moderate', 0.70)
CONFIDENCE_LOW = _get_threshold('confidence.low', 0.50)
GOAL_CONFIDENCE_THRESHOLD = _get_threshold('confidence.goal_orchestrator', 0.70)

# Density Overload (same as critical.density_max)
DENSITY_OVERLOAD = _get_threshold('critical.density_max', 0.90)


# =============================================================================
# DYNAMIC ACCESS FUNCTIONS (Recommended for new code)
# =============================================================================

def get_engagement_threshold() -> float:
    """Get current engagement threshold from active profile"""
    return _get_threshold('engagement_threshold', 0.60)


def get_critical_thresholds() -> dict:
    """Get current critical thresholds from active profile"""
    return {
        'coherence_min': _get_threshold('critical.coherence_min', 0.50),
        'density_max': _get_threshold('critical.density_max', 0.90),
        'change_min': _get_threshold('critical.change_min', 0.50),
    }


def get_cascade_max_rounds() -> int:
    """Get maximum investigation rounds from active profile"""
    return _get_threshold('cascade.max_investigation_rounds', 7)


def get_check_confidence_threshold() -> float:
    """Get CHECK phase confidence gate from active profile"""
    return _get_threshold('cascade.check_confidence_to_proceed', 0.70)


def reload_thresholds():
    """
    Reload thresholds from configuration.
    
    Call this after switching profiles to update module-level constants.
    Note: This only affects NEW imports. Already-imported constants won't change.
    """
    global ENGAGEMENT_THRESHOLD, CRITICAL_THRESHOLDS
    global UNCERTAINTY_LOW, UNCERTAINTY_MODERATE
    global COMPREHENSION_HIGH, COMPREHENSION_MODERATE
    global CLARITY_THRESHOLD, SIGNAL_THRESHOLD, COHERENCE_THRESHOLD
    global EXECUTION_HIGH, EXECUTION_MODERATE
    global STATE_MAPPING_THRESHOLD, COMPLETION_THRESHOLD, IMPACT_THRESHOLD
    global CONFIDENCE_HIGH, CONFIDENCE_MODERATE, CONFIDENCE_LOW
    global GOAL_CONFIDENCE_THRESHOLD, DENSITY_OVERLOAD
    
    # Reload all constants
    ENGAGEMENT_THRESHOLD = _get_threshold('engagement_threshold', 0.60)
    CRITICAL_THRESHOLDS = get_critical_thresholds()
    UNCERTAINTY_LOW = _get_threshold('uncertainty.low', 0.70)
    UNCERTAINTY_MODERATE = _get_threshold('uncertainty.moderate', 0.30)
    COMPREHENSION_HIGH = _get_threshold('comprehension.high', 0.80)
    COMPREHENSION_MODERATE = _get_threshold('comprehension.moderate', 0.50)
    CLARITY_THRESHOLD = _get_threshold('comprehension.clarity_min', 0.50)
    SIGNAL_THRESHOLD = _get_threshold('comprehension.signal_min', 0.50)
    COHERENCE_THRESHOLD = _get_threshold('comprehension.coherence_min', 0.50)
    EXECUTION_HIGH = _get_threshold('execution.high', 0.80)
    EXECUTION_MODERATE = _get_threshold('execution.moderate', 0.60)
    STATE_MAPPING_THRESHOLD = _get_threshold('execution.state_mapping_min', 0.60)
    COMPLETION_THRESHOLD = _get_threshold('execution.completion_min', 0.80)
    IMPACT_THRESHOLD = _get_threshold('execution.impact_min', 0.50)
    CONFIDENCE_HIGH = _get_threshold('confidence.high', 0.85)
    CONFIDENCE_MODERATE = _get_threshold('confidence.moderate', 0.70)
    CONFIDENCE_LOW = _get_threshold('confidence.low', 0.50)
    GOAL_CONFIDENCE_THRESHOLD = _get_threshold('confidence.goal_orchestrator', 0.70)
    DENSITY_OVERLOAD = _get_threshold('critical.density_max', 0.90)
    
    logger.info("♻️  Thresholds reloaded from active profile")