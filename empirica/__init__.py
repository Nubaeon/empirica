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

Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Empirica Project"

# Core imports
try:
    from empirica.core.canonical import CanonicalEpistemicAssessor, ReflexLogger
    from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade
except ImportError:
    pass

# Data imports
try:
    from empirica.data.session_database import SessionDatabase
    from empirica.data.session_json_handler import SessionJSONHandler
except ImportError:
    pass

# Workflow imports (new enhanced cascade)
try:
    from empirica.workflow.preflight_assessor import PreflightAssessor
    from empirica.workflow.postflight_assessor import PostflightAssessor
    from empirica.workflow.check_phase_evaluator import CheckPhaseEvaluator
    from empirica.workflow.cascade_workflow_orchestrator import (
        CascadeWorkflowOrchestrator,
        WorkflowGuide
    )
except ImportError:
    pass

__all__ = [
    # Core components
    'CanonicalEpistemicAssessor',
    'CanonicalEpistemicCascade',
    'ReflexLogger',
    'SessionDatabase',
    'SessionJSONHandler',
    # Enhanced workflow
    'PreflightAssessor',
    'PostflightAssessor',
    'CheckPhaseEvaluator',
    'CascadeWorkflowOrchestrator',
    'WorkflowGuide',
]
