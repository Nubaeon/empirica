"""
Epistemic Personality Profiles

Different AI behavior patterns implemented through vector thresholds.
Same architecture, different routing thresholds = different personalities.
"""

from typing import Dict


class PersonalityProfile:
    """Base personality configuration"""
    
    def __init__(self, name: str, thresholds: Dict[str, float], description: str):
        self.name = name
        self.thresholds = thresholds
        self.description = description
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "thresholds": self.thresholds,
            "description": self.description
        }


# ============================================================================
# Personality Profiles
# ============================================================================

CAUTIOUS_RESEARCHER = PersonalityProfile(
    name="cautious_researcher",
    thresholds={
        # Routing thresholds (noetic phase)
        "uncertainty_tolerance": 0.4,  # Low tolerance - investigate early
        "context_threshold": 0.6,      # High requirement - need deep context
        "know_threshold": 0.8,          # High bar for confidence
        "clarity_threshold": 0.7,       # Need very clear requirements
        
        # Sentinel gate thresholds (TIER 3 Priority 4 - Calibration)
        "halt_threshold": 0.92,         # HALT: Extremely confident, impossible to be wrong
        "branch_threshold": 0.45,       # BRANCH: Need investigation, high uncertainty
        "lock_threshold": 0.88,         # LOCK: High confidence, defer this decision
        "revise_threshold": 0.55        # REVISE: Low confidence, reassess from scratch
    },
    description="Low uncertainty tolerance, investigates early and often, high confidence bar"
)

PRAGMATIC_IMPLEMENTER = PersonalityProfile(
    name="pragmatic_implementer",
    thresholds={
        # Routing thresholds
        "uncertainty_tolerance": 0.7,  # High tolerance - move forward with some doubt
        "context_threshold": 0.4,      # Low requirement - minimal context OK
        "know_threshold": 0.6,          # Lower bar for confidence
        "clarity_threshold": 0.5,       # OK with moderate clarity
        
        # Sentinel gate thresholds
        "halt_threshold": 0.88,         # HALT: High confidence needed
        "branch_threshold": 0.55,       # BRANCH: More willing to investigate
        "lock_threshold": 0.80,         # LOCK: Defer when somewhat uncertain
        "revise_threshold": 0.65        # REVISE: Reassess with low confidence
    },
    description="Action-oriented, tolerates uncertainty, implements with partial knowledge"
)

BALANCED_ARCHITECT = PersonalityProfile(
    name="balanced_architect",
    thresholds={
        # Routing thresholds
        "uncertainty_tolerance": 0.6,  # Moderate tolerance
        "context_threshold": 0.5,      # Moderate context requirement
        "know_threshold": 0.7,          # Moderate confidence bar
        "clarity_threshold": 0.6,       # Moderate clarity requirement
        
        # Sentinel gate thresholds (DEFAULT)
        "halt_threshold": 0.90,         # HALT: Extremely confident
        "branch_threshold": 0.50,       # BRANCH: Needs investigation (design threshold)
        "lock_threshold": 0.85,         # LOCK: Uncertain, defer decision
        "revise_threshold": 0.60        # REVISE: Low confidence, reassess
    },
    description="Balanced approach, systematic but not overly cautious, standard defaults"
)

ADAPTIVE_LEARNER = PersonalityProfile(
    name="adaptive_learner",
    thresholds={
        # Routing thresholds
        "uncertainty_tolerance": 0.5,  # Starts moderate
        "context_threshold": 0.5,      # Starts moderate
        "know_threshold": 0.7,          # Starts moderate
        "clarity_threshold": 0.6,       # Starts moderate
        
        # Sentinel gate thresholds (calibrated by Bayesian beliefs)
        "halt_threshold": 0.90,         # HALT: Will be tuned by beliefs
        "branch_threshold": 0.50,       # BRANCH: Adaptive from outcomes
        "lock_threshold": 0.85,         # LOCK: Will be tuned by beliefs
        "revise_threshold": 0.60        # REVISE: Will be tuned by beliefs
    },
    description="Learns optimal thresholds from outcomes, adapts behavior over time"
)


# ============================================================================
# Personality Registry
# ============================================================================

PERSONALITIES = {
    "cautious_researcher": CAUTIOUS_RESEARCHER,
    "pragmatic_implementer": PRAGMATIC_IMPLEMENTER,
    "balanced_architect": BALANCED_ARCHITECT,
    "adaptive_learner": ADAPTIVE_LEARNER
}


def get_personality(name: str) -> PersonalityProfile:
    """Get personality by name, default to balanced_architect"""
    return PERSONALITIES.get(name, BALANCED_ARCHITECT)


def list_personalities() -> Dict[str, Dict]:
    """List all available personalities"""
    return {
        name: profile.to_dict()
        for name, profile in PERSONALITIES.items()
    }
