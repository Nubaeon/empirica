"""
Empirica - Epistemic Vector-Based Functional Self-Awareness Framework

A production-ready system for AI epistemic self-awareness and reasoning validation.

Core Philosophy: "Measure and validate without interfering"

Key Features:
- 13D epistemic vectors (know, uncertainty, context, clarity, coherence, etc.)
- CASCADE workflow: PREFLIGHT → CHECK → POSTFLIGHT
- Git-integrated reflex logging
- Session database (SQLite) with breadcrumb tracking
- Drift detection and signaling

Version: 1.3.2
"""

__version__ = "1.3.3"
__author__ = "Empirica Project"

# Core imports (ReflexLogger removed - use GitEnhancedReflexLogger instead)
try:
    from empirica.core.canonical import GitEnhancedReflexLogger
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
    'ReflexLogger',
    'SessionDatabase',
    'SessionJSONHandler',
]
