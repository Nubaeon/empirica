"""Fixtures for cascade unit tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema, VectorAssessment
from empirica.core.canonical.reflex_frame import VectorState, Action
# Alias for backwards compatibility in tests
EpistemicAssessment = EpistemicAssessmentSchema

# NEW SCHEMA IMPORTS (Phase 6: Test mock optimization)
from empirica.core.schemas.epistemic_assessment import (
    EpistemicAssessmentSchema,
    VectorAssessment,
    CascadePhase
)
# Converters removed - using NEW schema directly


@pytest.fixture
def mock_assessor_new():
    """
    NEW: Mock CanonicalEpistemicAssessor that returns NEW schema
    
    This is the optimized version that returns EpistemicAssessmentSchema directly,
    avoiding unnecessary OLD → NEW → OLD conversions in tests.
    """
    mock = AsyncMock()
    
    async def mock_assess_new(task, context, profile=None, phase=CascadePhase.PREFLIGHT, round_num=0):
        """Return a baseline assessment with NEW schema directly."""
        # Create baseline assessment with NEW schema
        assessment = EpistemicAssessmentSchema(
            # GATE
            engagement=VectorAssessment(0.70, "Test: Baseline engagement"),
            
            # FOUNDATION (Tier 0) - with prefixes
            foundation_know=VectorAssessment(0.60, "Test: Baseline knowledge"),
            foundation_do=VectorAssessment(0.65, "Test: Baseline capability"),
            foundation_context=VectorAssessment(0.70, "Test: Baseline context"),
            
            # COMPREHENSION (Tier 1) - with prefixes
            comprehension_clarity=VectorAssessment(0.70, "Test: Baseline clarity"),
            comprehension_coherence=VectorAssessment(0.75, "Test: Baseline coherence"),
            comprehension_signal=VectorAssessment(0.65, "Test: Baseline signal"),
            comprehension_density=VectorAssessment(0.60, "Test: Baseline density"),
            
            # EXECUTION (Tier 2) - with prefixes
            execution_state=VectorAssessment(0.65, "Test: Baseline state"),
            execution_change=VectorAssessment(0.60, "Test: Baseline change"),
            execution_completion=VectorAssessment(0.40, "Test: Baseline completion"),
            execution_impact=VectorAssessment(0.65, "Test: Baseline impact"),
            
            # UNCERTAINTY
            uncertainty=VectorAssessment(0.50, "Test: Baseline uncertainty"),
            
            # METADATA (NEW schema)
            phase=phase,
            round_num=round_num,
            investigation_count=0
        )
        return assessment
    
    # Mock both OLD and NEW methods
    mock.assess.side_effect = mock_assess_new  # For backwards compat
    mock.assess_new = mock_assess_new  # Direct NEW access
    return mock


@pytest.fixture
def mock_assessor():
    """
    Mock CanonicalEpistemicAssessor that returns NEW schema (EpistemicAssessmentSchema)
    
    Now returns NEW schema directly since OLD schema has been removed.
    """
    mock = AsyncMock()
    
    async def mock_assess(task, context, profile=None):
        """Return a baseline assessment with NEW schema."""
        # Create NEW assessment directly
        assessment = EpistemicAssessmentSchema(
            engagement=VectorAssessment(0.70, "Test: Baseline engagement"),
            foundation_know=VectorAssessment(0.60, "Test: Baseline knowledge"),
            foundation_do=VectorAssessment(0.65, "Test: Baseline capability"),
            foundation_context=VectorAssessment(0.70, "Test: Baseline context"),
            comprehension_clarity=VectorAssessment(0.70, "Test: Baseline clarity"),
            comprehension_coherence=VectorAssessment(0.75, "Test: Baseline coherence"),
            comprehension_signal=VectorAssessment(0.65, "Test: Baseline signal"),
            comprehension_density=VectorAssessment(0.60, "Test: Baseline density"),
            execution_state=VectorAssessment(0.65, "Test: Baseline state"),
            execution_change=VectorAssessment(0.60, "Test: Baseline change"),
            execution_completion=VectorAssessment(0.40, "Test: Baseline completion"),
            execution_impact=VectorAssessment(0.65, "Test: Baseline impact"),
            uncertainty=VectorAssessment(0.50, "Test: Baseline uncertainty"),
            phase=CascadePhase.PREFLIGHT,
            round_num=0,
            investigation_count=0
        )
        return assessment
    
    mock.assess.side_effect = mock_assess
    return mock


# OLD mock_assessor_old_deprecated removed - OLD schema no longer exists


@pytest.fixture
def mock_cascade_with_assessor(mock_assessor, monkeypatch):
    """
    Create a CanonicalEpistemicCascade with mocked assessor.
    
    This fixture patches the cascade's assessor to use the mock,
    preventing any LLM calls during testing.
    """
    from empirica.core.metacognitive_cascade.metacognitive_cascade import CanonicalEpistemicCascade
    
    cascade = CanonicalEpistemicCascade(
        enable_bayesian=False,
        enable_drift_monitor=False,
        enable_action_hooks=False,
        enable_session_db=False,
        enable_git_notes=False
    )
    
    # Replace the assessor with our mock
    cascade.assessor = mock_assessor
    
    return cascade
