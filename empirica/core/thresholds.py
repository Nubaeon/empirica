"""
Centralized threshold configuration for Empirica.

All hardcoded thresholds should be imported from this module
to ensure consistency and ease of configuration.
"""

# =============================================================================
# ENGAGEMENT THRESHOLDS
# =============================================================================

# Engagement Gate Threshold
ENGAGEMENT_THRESHOLD = 0.60  # Minimum engagement for proceeding with tasks

# =============================================================================
# CRITICAL THRESHOLDS
# =============================================================================

# Critical decision thresholds (below/above these triggers system actions)
CRITICAL_THRESHOLDS = {
    'coherence_min': 0.50,    # Below this: RESET sequence
    'density_max': 0.90,      # Above this: RESET due to overload
    'change_min': 0.50        # Below this: STOP execution
}

# =============================================================================
# EPISTEMIC VECTOR THRESHOLDS
# =============================================================================

# Uncertainty Thresholds
UNCERTAINTY_LOW = 0.70        # Low uncertainty threshold (proceed confidently)
UNCERTAINTY_MODERATE = 0.30   # Moderate uncertainty threshold (proceed with caution)

# Comprehension Thresholds
COMPREHENSION_HIGH = 0.80     # High comprehension threshold
COMPREHENSION_MODERATE = 0.50 # Moderate comprehension threshold

# Execution Thresholds
EXECUTION_HIGH = 0.80         # High execution capability threshold
EXECUTION_MODERATE = 0.60     # Moderate execution capability threshold

# State Mapping Threshold
STATE_MAPPING_THRESHOLD = 0.60  # Minimum state mapping confidence

# Completion Threshold
COMPLETION_THRESHOLD = 0.80     # Minimum completion confidence

# Impact Threshold
IMPACT_THRESHOLD = 0.50         # Minimum impact understanding threshold

# =============================================================================
# COMPONENT-SPECIFIC THRESHOLDS
# =============================================================================

# Clarity and Signal Thresholds
CLARITY_THRESHOLD = 0.50       # Minimum clarity threshold
SIGNAL_THRESHOLD = 0.50        # Minimum signal threshold
COHERENCE_THRESHOLD = 0.50     # Minimum coherence threshold

# Density Overload Threshold
DENSITY_OVERLOAD = 0.90        # Cognitive overload threshold

# =============================================================================
# CONFIDENCE THRESHOLDS
# =============================================================================

# Decision Confidence Thresholds
CONFIDENCE_HIGH = 0.85         # High confidence threshold for decisions
CONFIDENCE_MODERATE = 0.70     # Moderate confidence threshold
CONFIDENCE_LOW = 0.50          # Low confidence threshold

# Goal Orchestrator Confidence
GOAL_CONFIDENCE_THRESHOLD = 0.70  # Threshold for goal orchestrator decisions