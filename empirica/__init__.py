"""
Empirica - Metacognitive Reasoning Framework

A production-ready system for AI epistemic self-awareness and reasoning validation.

Core Philosophy: "Measure and validate without interfering"

Key Features:
- 13D epistemic monitoring with Explicit Uncertainty vector
- Enhanced cascade workflow (PREFLIGHT → Think → Plan → Investigate → Check → Act → POSTFLIGHT)
- Evidence-based Bayesian calibration
- Behavioral drift detection
- Session database (SQLite + JSON exports)
- Universal plugin extensibility

Version: 1.0.6
"""

__version__ = "1.0.6"
__author__ = "Empirica Project"

# Core imports
try:
    from empirica.core.canonical import ReflexLogger
    from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade
except ImportError as e:
    print(f"Warning: Core imports failed: {e}")
    pass

# Data imports
try:
    from empirica.data.session_database import SessionDatabase
    from empirica.data.session_json_handler import SessionJSONHandler
except ImportError as e:
    print(f"Warning: Data imports failed: {e}")
    pass

__all__ = [
    # Core components
    'CanonicalEpistemicCascade',
    'ReflexLogger',
    'SessionDatabase',
    'SessionJSONHandler',
]
