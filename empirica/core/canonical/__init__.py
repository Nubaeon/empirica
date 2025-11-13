"""
Canonical Epistemic Self-Assessment System

Provides genuine LLM-powered metacognitive self-assessment without heuristics or confabulation.

Core Components:
- reflex_frame: Canonical data structures (VectorState, EpistemicAssessment, ReflexFrame)
- reflex_logger: Temporal logging to JSON files (prevents recursion)
- canonical_epistemic_assessment: LLM-powered assessor (no heuristics)

Key Principles:
1. Genuine reasoning: LLM self-assessment, not keyword matching
2. Temporal separation: Log to JSON, act on logs in next pass
3. Clear terminology: epistemic weights ≠ internal weights
4. ENGAGEMENT gate: ≥0.60 required before proceeding
5. Canonical weights: 35/25/25/15 (foundation/comprehension/execution/engagement)
"""

from .reflex_frame import (
    VectorState,
    EpistemicAssessment,
    ReflexFrame,
    Action,
    CANONICAL_WEIGHTS,
    ENGAGEMENT_THRESHOLD,
    CRITICAL_THRESHOLDS
)

from .reflex_logger import (
    ReflexLogger,
    log_assessment,
    log_assessment_sync
)

from .canonical_epistemic_assessment import (
    CanonicalEpistemicAssessor
)

__all__ = [
    # Data Structures
    'VectorState',
    'EpistemicAssessment',
    'ReflexFrame',
    'Action',

    # Constants
    'CANONICAL_WEIGHTS',
    'ENGAGEMENT_THRESHOLD',
    'CRITICAL_THRESHOLDS',

    # Logger
    'ReflexLogger',
    'log_assessment',
    'log_assessment_sync',

    # Assessor
    'CanonicalEpistemicAssessor'
]
