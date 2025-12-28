"""
End-to-end integration tests for schema migration.

Tests verify that the NEW schema works correctly with real components
(not mocked) and that conversions work in realistic scenarios.
"""

import pytest
import asyncio
from empirica.core.metacognitive_cascade.metacognitive_cascade import CanonicalEpistemicCascade, CascadePhase
from empirica.core.persona.harness.persona_harness import PersonaHarness
from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema, CascadePhase as NewCascadePhase
from empirica.core.schemas.assessment_converters import convert_old_to_new, convert_new_to_old


class TestSchemaConversionIntegration:
    """Test schema conversions in realistic scenarios."""
    
    def test_old_to_new_to_old_preserves_data(self):
        """Test round-trip conversion preserves critical data."""
        from empirica.core.canonical.reflex_frame import EpistemicAssessment, VectorState, Action
        
        # Create OLD assessment
        old = EpistemicAssessment(
            assessment_id="test_123",
            task="Integration test task",
            engagement=VectorState(0.75, "Good engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.60, "Baseline knowledge"),
            do=VectorState(0.65, "Good capability"),
            context=VectorState(0.70, "Good context"),
            foundation_confidence=0.65,
            clarity=VectorState(0.70, "Clear task"),
            coherence=VectorState(0.75, "Coherent"),
            signal=VectorState(0.65, "Good signal"),
            density=VectorState(0.60, "Manageable"),
            comprehension_confidence=0.675,
            state=VectorState(0.65, "State known"),
            change=VectorState(0.60, "Tracking change"),
            completion=VectorState(0.40, "Early"),
            impact=VectorState(0.65, "Impact known"),
            execution_confidence=0.575,
            uncertainty=VectorState(0.50, "Moderate"),
            overall_confidence=0.65,
            recommended_action=Action.INVESTIGATE
        )
        
        # Convert OLD → NEW → OLD
        new = convert_old_to_new(old)
        old_again = convert_new_to_old(new)
        
        # Verify critical data preserved
        assert old_again.engagement.score == old.engagement.score
        assert old_again.know.score == old.know.score
        assert old_again.do.score == old.do.score
        assert old_again.engagement.rationale == old.engagement.rationale
        assert old_again.know.rationale == old.know.rationale
    
    def test_new_assessment_calculates_confidences(self):
        """Test NEW schema confidence calculation."""
        from empirica.core.schemas.epistemic_assessment import VectorAssessment
        
        assessment = EpistemicAssessmentSchema(
            engagement=VectorAssessment(0.75, "Test"),
            foundation_know=VectorAssessment(0.60, "Test"),
            foundation_do=VectorAssessment(0.65, "Test"),
            foundation_context=VectorAssessment(0.70, "Test"),
            comprehension_clarity=VectorAssessment(0.70, "Test"),
            comprehension_coherence=VectorAssessment(0.75, "Test"),
            comprehension_signal=VectorAssessment(0.65, "Test"),
            comprehension_density=VectorAssessment(0.60, "Test"),
            execution_state=VectorAssessment(0.65, "Test"),
            execution_change=VectorAssessment(0.60, "Test"),
            execution_completion=VectorAssessment(0.40, "Test"),
            execution_impact=VectorAssessment(0.65, "Test"),
            uncertainty=VectorAssessment(0.50, "Test"),
            phase=NewCascadePhase.PREFLIGHT,
            round_num=0
        )
        
        # Calculate confidences
        tier_confidences = assessment.calculate_tier_confidences()
        
        # Verify calculated
        assert 'foundation_confidence' in tier_confidences
        assert 'comprehension_confidence' in tier_confidences
        assert 'execution_confidence' in tier_confidences
        assert 'overall_confidence' in tier_confidences
        
        # Verify reasonable values
        assert 0.0 <= tier_confidences['overall_confidence'] <= 1.0


class TestCASCADEIntegration:
    """Test CASCADE with NEW schema internally."""
    
    @pytest.mark.asyncio
    async def test_cascade_uses_new_schema_internally(self):
        """Test that CASCADE uses NEW schema via wrapper."""
        cascade = CanonicalEpistemicCascade(
            enable_bayesian=False,
            enable_drift_monitor=False,
            enable_action_hooks=False,
            enable_session_db=False,
            enable_git_notes=False
        )
        
        # Call internal NEW method
        new_assessment = await cascade._assess_epistemic_state_new(
            task="Integration test",
            context={},
            task_id="test_id",
            phase=CascadePhase.PREFLIGHT,
            round_num=0
        )
        
        # Verify it's NEW schema
        assert isinstance(new_assessment, EpistemicAssessmentSchema)
        assert hasattr(new_assessment, 'foundation_know')
        assert hasattr(new_assessment, 'comprehension_clarity')
        assert hasattr(new_assessment, 'execution_state')
    
    @pytest.mark.asyncio
    async def test_cascade_wrapper_returns_old_schema(self):
        """Test that CASCADE wrapper returns OLD schema for backwards compat."""
        from empirica.core.canonical.reflex_frame import EpistemicAssessment
        
        cascade = CanonicalEpistemicCascade(
            enable_bayesian=False,
            enable_drift_monitor=False,
            enable_action_hooks=False,
            enable_session_db=False,
            enable_git_notes=False
        )
        
        # Call wrapper method
        old_assessment = await cascade._assess_epistemic_state(
            task="Integration test",
            context={},
            task_id="test_id",
            phase=CascadePhase.PREFLIGHT,
            round_num=0
        )
        
        # Verify it's OLD schema (for backwards compat)
        assert isinstance(old_assessment, EpistemicAssessment)
        assert hasattr(old_assessment, 'know')  # OLD field name
        assert hasattr(old_assessment, 'clarity')  # OLD field name
        assert hasattr(old_assessment, 'state')  # OLD field name


class TestAssessorIntegration:
    """Test Assessor with NEW schema."""
    
    def test_assessor_has_new_method(self):
        """Test that assessor has parse_llm_response_new method."""
        assessor = CanonicalEpistemicAssessor()
        
        # Verify NEW method exists
        assert hasattr(assessor, 'parse_llm_response_new')
        assert callable(assessor.parse_llm_response_new)
    
    def test_assessor_old_method_still_works(self):
        """Test that OLD method still exists for backwards compat."""
        assessor = CanonicalEpistemicAssessor()
        
        # Verify OLD method still exists
        assert hasattr(assessor, 'parse_llm_response')
        assert callable(assessor.parse_llm_response)


class TestPersonaHarnessIntegration:
    """Test PersonaHarness with NEW schema."""
    
    def test_persona_harness_has_new_method(self):
        """Test that PersonaHarness class has _apply_priors_new method."""
        # Verify NEW method exists on the class (don't need to instantiate)
        assert hasattr(PersonaHarness, '_apply_priors_new')
        assert callable(getattr(PersonaHarness, '_apply_priors_new'))


class TestEndToEndFlow:
    """Test complete flow with all components."""
    
    @pytest.mark.asyncio
    async def test_complete_cascade_flow_works(self):
        """Test that complete CASCADE flow works end-to-end."""
        from empirica.core.canonical.reflex_frame import EpistemicAssessment
        
        # Create CASCADE with minimal config
        cascade = CanonicalEpistemicCascade(
            enable_bayesian=False,
            enable_drift_monitor=False,
            enable_action_hooks=False,
            enable_session_db=False,
            enable_git_notes=False
        )
        
        # Run assessment (uses NEW internally, returns OLD)
        assessment = await cascade._assess_epistemic_state(
            task="End-to-end test",
            context={'test': True},
            task_id="e2e_test",
            phase=CascadePhase.PREFLIGHT
        )
        
        # Verify we got OLD schema back (backwards compat)
        assert isinstance(assessment, EpistemicAssessment)
        
        # Verify all vectors present (OLD names)
        assert hasattr(assessment, 'engagement')
        assert hasattr(assessment, 'know')
        assert hasattr(assessment, 'do')
        assert hasattr(assessment, 'context')
        assert hasattr(assessment, 'clarity')
        assert hasattr(assessment, 'coherence')
        assert hasattr(assessment, 'signal')
        assert hasattr(assessment, 'density')
        assert hasattr(assessment, 'state')
        assert hasattr(assessment, 'change')
        assert hasattr(assessment, 'completion')
        assert hasattr(assessment, 'impact')
        assert hasattr(assessment, 'uncertainty')
        
        # Verify scores are valid
        assert 0.0 <= assessment.engagement.score <= 1.0
        assert 0.0 <= assessment.know.score <= 1.0
        assert 0.0 <= assessment.overall_confidence <= 1.0


# Mark slow tests
pytestmark = pytest.mark.integration
