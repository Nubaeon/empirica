"""Test PREFLIGHT phase - Baseline epistemic assessment."""

import asyncio
import pytest
from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema, CascadePhase, VectorAssessment
from empirica.core.canonical.reflex_frame import Action
EpistemicAssessment = EpistemicAssessmentSchema
from empirica.core.metacognitive_cascade.metacognitive_cascade import (
    CanonicalEpistemicCascade,
    CascadePhase,
    CanonicalCascadeState
)


class TestPreflightPhase:
    """Test PREFLIGHT phase functionality."""
    
    def test_preflight_phase_initialization(self):
        """Test PREFLIGHT phase initialization."""
        cascade = CanonicalEpistemicCascade()
        
        # Verify cascade is properly initialized
        assert cascade.action_confidence_threshold == 0.65
        assert cascade.max_investigation_rounds == 7
        assert cascade.agent_id == "cascade"
        assert cascade.assessor is not None
        # reflex_logger is internal implementation detail, not part of public API
    
    def test_preflight_assessment_generation(self):
        """Test that PREFLIGHT generates baseline epistemic assessment."""
        cascade = CanonicalEpistemicCascade()
        
        # Test the internal assessment method
        task = "Test task for preflight assessment"
        context = {}
        
        async def test_assessment():
            assessment = await cascade._assess_epistemic_state(
                task, context, "test_task_id", CascadePhase.PREFLIGHT
            )
            return assessment
        
        assessment = asyncio.run(test_assessment())
        
        # Verify it's a proper assessment
        assert isinstance(assessment, EpistemicAssessment)
        # Note: task field removed in schema migration - no longer stored
        
        # For PREFLIGHT, should have conservative baseline scores
        assert 0.0 <= assessment.engagement.score <= 1.0
        assert 0.0 <= assessment.know.score <= 1.0
        assert 0.0 <= assessment.do.score <= 1.0
        assert 0.0 <= assessment.context.score <= 1.0
        assert 0.0 <= assessment.overall_confidence <= 1.0
        
        # Verify it has all required vectors
        assert assessment.engagement is not None
        assert assessment.know is not None
        assert assessment.do is not None
        assert assessment.context is not None
        assert assessment.clarity is not None
        assert assessment.coherence is not None
        assert assessment.signal is not None
        assert assessment.density is not None
        assert assessment.state is not None
        assert assessment.change is not None
        assert assessment.completion is not None
        assert assessment.impact is not None
        assert assessment.uncertainty is not None
    
    def test_preflight_assessment_specifics(self):
        """Test PREFLIGHT-specific assessment characteristics."""
        cascade = CanonicalEpistemicCascade()
        
        task = "Preflight test task"
        context = {}
        
        async def test_preflight_assessment():
            assessment = await cascade._assess_epistemic_state(
                task, context, "preflight_task_id", CascadePhase.PREFLIGHT
            )
            return assessment
        
        assessment = asyncio.run(test_preflight_assessment())
        
        # PREFLIGHT assessments should have baseline characteristics
        # Based on the code logic for PREFLIGHT phase
        assert assessment.engagement.score >= 0.70  # Baseline engagement
        assert assessment.foundation_confidence >= 0.60  # Baseline foundation
        assert assessment.comprehension_confidence >= 0.57  # Updated baseline comprehension
        assert assessment.execution_confidence >= 0.48  # Updated baseline execution
        
        # Should be set to INVESTIGATE by default
        assert assessment.recommended_action == Action.INVESTIGATE
        
        # Should have moderate uncertainty (exploring new task)
        assert assessment.uncertainty.score >= 0.50  # Updated baseline uncertainty
    
    def test_preflight_delta_calculation(self):
        """Test that preflight to postflight delta can be calculated."""
        cascade = CanonicalEpistemicCascade()
        
        # Create two sample assessments using new schema format
        preflight_assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.70, "Baseline engagement"),
            uncertainty=VectorAssessment(0.60, "High initial uncertainty"),
            foundation_know=VectorAssessment(0.55, "Limited initial knowledge"),
            foundation_do=VectorAssessment(0.60, "Capability needs verification"),
            foundation_context=VectorAssessment(0.65, "Context understood at surface level"),
            comprehension_clarity=VectorAssessment(0.65, "Initial clarity"),
            comprehension_coherence=VectorAssessment(0.70, "Basic coherence"),
            comprehension_signal=VectorAssessment(0.60, "Priority identified"),
            comprehension_density=VectorAssessment(0.65, "Manageable complexity"),
            execution_state=VectorAssessment(0.60, "Environment not yet mapped"),
            execution_change=VectorAssessment(0.55, "Changes not tracked"),
            execution_completion=VectorAssessment(0.30, "Not yet started"),
            execution_impact=VectorAssessment(0.50, "Impact needs analysis"),
            phase=CascadePhase.PREFLIGHT,
        )
        
        postflight_assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.75, "Maintained engagement"),
            uncertainty=VectorAssessment(0.35, "Uncertainty reduced"),
            foundation_know=VectorAssessment(0.70, "Knowledge improved through investigation"),
            foundation_do=VectorAssessment(0.75, "Capability demonstrated"),
            foundation_context=VectorAssessment(0.80, "Context validated"),
            comprehension_clarity=VectorAssessment(0.80, "Clarity achieved"),
            comprehension_coherence=VectorAssessment(0.85, "Coherence maintained"),
            comprehension_signal=VectorAssessment(0.75, "Priority confirmed"),
            comprehension_density=VectorAssessment(0.70, "Complexity managed"),
            execution_state=VectorAssessment(0.75, "Environment mapped"),
            execution_change=VectorAssessment(0.80, "Changes tracked"),
            execution_completion=VectorAssessment(0.70, "Task executed"),
            execution_impact=VectorAssessment(0.70, "Impact assessed"),
            phase=CascadePhase.POSTFLIGHT,
        )
        
        # Calculate delta
        delta = cascade._calculate_epistemic_delta(preflight_assessment, postflight_assessment)
        
        # Verify delta calculation
        assert delta['foundation_confidence'] == pytest.approx(0.15, abs=0.01)  # 0.75 - 0.60
        assert delta['comprehension_confidence'] == pytest.approx(0.09, abs=0.01)  # ~0.74 - 0.65
        assert delta['execution_confidence'] == pytest.approx(0.25, abs=0.01)  # ~0.74 - 0.49
        assert delta['uncertainty'] == pytest.approx(-0.25, abs=0.01)  # 0.35 - 0.60 (negative = improvement)
        assert delta['know'] == pytest.approx(0.15, abs=0.01)  # 0.70 - 0.55
        assert delta['do'] == pytest.approx(0.15, abs=0.01)  # 0.75 - 0.60
        assert delta['clarity'] == pytest.approx(0.15, abs=0.01)  # 0.80 - 0.65
        
        # All vector improvements should be positive (except uncertainty which should decrease)
        assert delta['know'] > 0
        assert delta['do'] > 0
        assert delta['context'] > 0
        assert delta['clarity'] > 0
        assert delta['coherence'] > 0
        assert delta['uncertainty'] < 0  # Uncertainty should decrease
    
    def test_preflight_calibration_check(self):
        """Test preflight to postflight calibration check."""
        cascade = CanonicalEpistemicCascade()
        
        # Test well-calibrated scenario (confidence stable)
        preflight = EpistemicAssessment(
            engagement=VectorAssessment(0.65, "Baseline engagement"),
            foundation_know=VectorAssessment(0.55, "Initial knowledge"),
            foundation_do=VectorAssessment(0.65, "Baseline capability"),
            foundation_context=VectorAssessment(0.60, "Baseline context"),
            comprehension_clarity=VectorAssessment(0.70, "Initial clarity"),
            comprehension_coherence=VectorAssessment(0.65, "Initial coherence"),
            comprehension_signal=VectorAssessment(0.60, "Initial signal"),
            comprehension_density=VectorAssessment(0.65, "Initial density"),
            execution_state=VectorAssessment(0.60, "Initial state awareness"),
            execution_change=VectorAssessment(0.65, "Initial change tracking"),
            execution_completion=VectorAssessment(0.50, "Initial completion awareness"),
            execution_impact=VectorAssessment(0.60, "Initial impact awareness"),
            uncertainty=VectorAssessment(0.50, "Initial uncertainty"),
            phase=CascadePhase.PREFLIGHT,
        )
        
        postflight = EpistemicAssessment(
            engagement=VectorAssessment(0.70, "Stable engagement"),
            foundation_know=VectorAssessment(0.65, "Improved knowledge"),
            foundation_do=VectorAssessment(0.70, "Improved capability"),
            foundation_context=VectorAssessment(0.65, "Improved context"),
            comprehension_clarity=VectorAssessment(0.75, "Improved clarity"),
            comprehension_coherence=VectorAssessment(0.70, "Improved coherence"),
            comprehension_signal=VectorAssessment(0.65, "Improved signal"),
            comprehension_density=VectorAssessment(0.60, "Improved density"),
            execution_state=VectorAssessment(0.65, "Improved state awareness"),
            execution_change=VectorAssessment(0.70, "Improved change tracking"),
            execution_completion=VectorAssessment(0.65, "Improved completion awareness"),
            execution_impact=VectorAssessment(0.65, "Improved impact awareness"),
            uncertainty=VectorAssessment(0.40, "Reduced uncertainty"),
            phase=CascadePhase.POSTFLIGHT,
        )
        
        calibration_check = cascade._check_calibration_accuracy(preflight, postflight, {})
        
        # Should be well-calibrated (confidence stayed stable)
        assert calibration_check['well_calibrated'] is True
        assert abs(calibration_check['confidence_delta']) < 0.15  # Less than 0.15 threshold
        # Note: uncertainty_delta may not be available in new schema
    
    def test_preflight_guidance_generation(self):
        """Test that appropriate guidance is generated for preflight state."""
        cascade = CanonicalEpistemicCascade()
        
        # Create an assessment with some gaps
        assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.75, "Good engagement"),
            foundation_know=VectorAssessment(0.50, "Low domain knowledge"),
            foundation_do=VectorAssessment(0.60, "Moderate capability"),
            foundation_context=VectorAssessment(0.55, "Low context understanding"),
            comprehension_clarity=VectorAssessment(0.65, "Moderate clarity"),
            comprehension_coherence=VectorAssessment(0.70, "Good coherence"),
            comprehension_signal=VectorAssessment(0.60, "Moderate signal"),
            comprehension_density=VectorAssessment(0.65, "Moderate density"),
            execution_state=VectorAssessment(0.55, "Low state awareness"),
            execution_change=VectorAssessment(0.60, "Moderate change tracking"),
            execution_completion=VectorAssessment(0.40, "Low completion awareness"),
            execution_impact=VectorAssessment(0.55, "Low impact understanding"),
            uncertainty=VectorAssessment(0.65, "High uncertainty"),
            phase=CascadePhase.PREFLIGHT,
        )
        
        guidance = cascade._generate_execution_guidance(assessment)
        
        # Should have guidance for the identified gaps
        # Guidance/gap generation removed with heuristics - AI decides via self-assessment
        # Just verify the method doesn't crash and returns something
        assert guidance is not None