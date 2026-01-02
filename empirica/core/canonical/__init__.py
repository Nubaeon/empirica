"""
Canonical Epistemic Self-Assessment System

Provides genuine LLM-powered metacognitive self-assessment without heuristics or confabulation.

Core Components:
- reflex_frame: Canonical data structures (VectorState, EpistemicAssessment, ReflexFrame)
- reflex_logger: Removed (replaced by GitEnhancedReflexLogger)

NOTE: Goal orchestration moved to empirica/core/goals/ (explicit goals system with subtasks)

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

# reflex_logger removed - use GitEnhancedReflexLogger instead

from .git_enhanced_reflex_logger import GitEnhancedReflexLogger
from .git_state_capture import GitStateCapture
from .git_notes_storage import GitNotesStorage
from .checkpoint_storage import CheckpointStorage

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
    'EpistemicAssessmentSchema',

    # Git-enhanced checkpoint system (refactored)
    'GitEnhancedReflexLogger',
    'GitStateCapture',
    'GitNotesStorage',
    'CheckpointStorage'
]
