"""
Canonical Epistemic Self-Assessment System

Provides genuine LLM-powered metacognitive self-assessment without heuristics or confabulation.

Core Components:
- reflex_frame: Canonical data structures (VectorState, EpistemicAssessment, ReflexFrame)
- reflex_logger: Temporal logging to JSON files (prevents recursion)
- canonical_goal_orchestrator: Goal decomposition and orchestration

NOTE: EpistemicAssessor moved to empirica-sentinel repo (separate module for orchestration/heuristics)

Key Principles:
1. Genuine reasoning: LLM self-assessment, not keyword matching
2. Temporal separation: Log to JSON, act on logs in next pass
3. Clear terminology: epistemic weights ≠ internal weights
4. ENGAGEMENT gate: ≥0.60 required before proceeding
5. Canonical weights: 35/25/25/15 (foundation/comprehension/execution/engagement)
"""

from .reflex_frame import (
    VectorState,
    Action,
    CANONICAL_WEIGHTS
)

# Import centralized thresholds
from ..thresholds import ENGAGEMENT_THRESHOLD, CRITICAL_THRESHOLDS

# OLD EpistemicAssessment and ReflexFrame removed - use EpistemicAssessmentSchema
# For backwards compatibility during migration, import from schemas
from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema
# Alias for backwards compatibility (will be removed after all code is updated)
EpistemicAssessment = EpistemicAssessmentSchema

from .reflex_logger import (
    ReflexLogger,
    log_assessment,
    log_assessment_sync
)

__all__ = [
    # Data Structures
    'VectorState',
    'EpistemicAssessment',  # Alias for EpistemicAssessmentSchema (backwards compat)
    'Action',

    # Constants
    'CANONICAL_WEIGHTS',
    'ENGAGEMENT_THRESHOLD',
    'CRITICAL_THRESHOLDS',

    # Logger
    'ReflexLogger',
    'log_assessment',
    'log_assessment_sync',
    
    # NEW schema (main export)
    'EpistemicAssessmentSchema'
]
