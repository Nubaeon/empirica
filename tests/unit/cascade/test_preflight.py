"""Test PREFLIGHT phase - Baseline epistemic assessment."""

import asyncio
import pytest
from empirica.core.canonical.reflex_frame import EpistemicAssessment, VectorState, Action
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
        assert cascade.action_confidence_threshold == 0.70
        assert cascade.max_investigation_rounds == 3
        assert cascade.agent_id == "cascade"
        assert cascade.assessor is not None
        assert cascade.reflex_logger is not None
    
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
        assert assessment.task == task
        
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
        assert assessment.engagement_gate_passed is True  # Engagement >= 0.60
        assert assessment.foundation_confidence >= 0.60  # Baseline foundation
        assert assessment.comprehension_confidence >= 0.65  # Baseline comprehension
        assert assessment.execution_confidence >= 0.49  # Baseline execution
        
        # Should be set to INVESTIGATE by default
        assert assessment.recommended_action == Action.INVESTIGATE
        
        # Should have moderate uncertainty (exploring new task)
        assert assessment.uncertainty.score >= 0.60
    
    def test_preflight_delta_calculation(self):
        """Test that preflight to postflight delta can be calculated."""
        cascade = CanonicalEpistemicCascade()
        
        # Create two sample assessments
        preflight_assessment = EpistemicAssessment(
            engagement=VectorState(0.70, "Baseline engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.55, "Limited initial knowledge"),
            do=VectorState(0.60, "Capability needs verification"),
            context=VectorState(0.65, "Context understood at surface level"),
            foundation_confidence=0.60,
            clarity=VectorState(0.65, "Initial clarity"),
            coherence=VectorState(0.70, "Basic coherence"),
            signal=VectorState(0.60, "Priority identified"),
            density=VectorState(0.65, "Manageable complexity"),
            comprehension_confidence=0.65,
            state=VectorState(0.60, "Environment not yet mapped"),
            change=VectorState(0.55, "Changes not tracked"),
            completion=VectorState(0.30, "Not yet started"),
            impact=VectorState(0.50, "Impact needs analysis"),
            execution_confidence=0.49,
            uncertainty=VectorState(0.60, "High initial uncertainty"),
            overall_confidence=0.58,
            recommended_action=Action.INVESTIGATE,
            assessment_id="preflight_test"
        )
        
        postflight_assessment = EpistemicAssessment(
            engagement=VectorState(0.75, "Maintained engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.70, "Knowledge improved through investigation"),
            do=VectorState(0.75, "Capability demonstrated"),
            context=VectorState(0.80, "Context validated"),
            foundation_confidence=0.75,
            clarity=VectorState(0.80, "Clarity achieved"),
            coherence=VectorState(0.85, "Coherence maintained"),
            signal=VectorState(0.75, "Priority confirmed"),
            density=VectorState(0.70, "Complexity managed"),
            comprehension_confidence=0.78,
            state=VectorState(0.75, "Environment mapped"),
            change=VectorState(0.80, "Changes tracked"),
            completion=VectorState(0.70, "Task executed"),
            impact=VectorState(0.70, "Impact assessed"),
            execution_confidence=0.74,
            uncertainty=VectorState(0.35, "Uncertainty reduced"),
            overall_confidence=0.73,
            recommended_action=Action.PROCEED,
            assessment_id="postflight_test"
        )
        
        # Calculate delta
        delta = cascade._calculate_epistemic_delta(preflight_assessment, postflight_assessment)
        
        # Verify delta calculation
        assert delta['foundation_confidence'] == pytest.approx(0.15, abs=0.01)  # 0.75 - 0.60
        assert delta['comprehension_confidence'] == pytest.approx(0.13, abs=0.01)  # 0.78 - 0.65
        assert delta['execution_confidence'] == pytest.approx(0.25, abs=0.01)  # 0.74 - 0.49
        assert delta['overall_confidence'] == pytest.approx(0.15, abs=0.01)  # 0.73 - 0.58
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
            engagement=VectorState(0.65, "Baseline engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.55, "Initial knowledge"),
            do=VectorState(0.65, "Baseline capability"),
            context=VectorState(0.60, "Baseline context"),
            foundation_confidence=0.60,
            clarity=VectorState(0.70, "Initial clarity"),
            coherence=VectorState(0.65, "Initial coherence"),
            signal=VectorState(0.60, "Initial signal"),
            density=VectorState(0.65, "Initial density"),
            comprehension_confidence=0.65,
            state=VectorState(0.60, "Initial state awareness"),
            change=VectorState(0.65, "Initial change tracking"),
            completion=VectorState(0.50, "Initial completion awareness"),
            impact=VectorState(0.60, "Initial impact awareness"),
            execution_confidence=0.55,
            uncertainty=VectorState(0.50, "Initial uncertainty"),
            overall_confidence=0.60,
            recommended_action=Action.INVESTIGATE,
            assessment_id="calibration_test_preflight"
        )
        
        postflight = EpistemicAssessment(
            engagement=VectorState(0.70, "Stable engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.65, "Improved knowledge"),
            do=VectorState(0.70, "Improved capability"),
            context=VectorState(0.65, "Improved context"),
            foundation_confidence=0.67,
            clarity=VectorState(0.75, "Improved clarity"),
            coherence=VectorState(0.70, "Improved coherence"),
            signal=VectorState(0.65, "Improved signal"),
            density=VectorState(0.60, "Improved density"),
            comprehension_confidence=0.69,
            state=VectorState(0.65, "Improved state awareness"),
            change=VectorState(0.70, "Improved change tracking"),
            completion=VectorState(0.65, "Improved completion awareness"),
            impact=VectorState(0.65, "Improved impact awareness"),
            execution_confidence=0.65,
            uncertainty=VectorState(0.40, "Reduced uncertainty"),
            overall_confidence=0.66,  # Very close to preflight
            recommended_action=Action.PROCEED,
            assessment_id="calibration_test_postflight"
        )
        
        calibration_check = cascade._check_calibration_accuracy(preflight, postflight, {})
        
        # Should be well-calibrated (confidence stayed stable)
        assert calibration_check['well_calibrated'] is True
        assert abs(calibration_check['confidence_delta']) < 0.15  # Less than 0.15 threshold
        assert calibration_check['uncertainty_delta'] < 0  # Uncertainty decreased
    
    def test_preflight_guidance_generation(self):
        """Test that appropriate guidance is generated for preflight state."""
        cascade = CanonicalEpistemicCascade()
        
        # Create an assessment with some gaps
        assessment = EpistemicAssessment(
            engagement=VectorState(0.75, "Good engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.50, "Low domain knowledge"),
            do=VectorState(0.60, "Moderate capability"),
            context=VectorState(0.55, "Low context understanding"),
            foundation_confidence=0.55,
            clarity=VectorState(0.65, "Moderate clarity"),
            coherence=VectorState(0.70, "Good coherence"),
            signal=VectorState(0.60, "Moderate signal"),
            density=VectorState(0.65, "Moderate density"),
            comprehension_confidence=0.65,
            state=VectorState(0.55, "Low state awareness"),
            change=VectorState(0.60, "Moderate change tracking"),
            completion=VectorState(0.40, "Low completion awareness"),
            impact=VectorState(0.55, "Low impact understanding"),
            execution_confidence=0.50,
            uncertainty=VectorState(0.65, "High uncertainty"),
            overall_confidence=0.55,
            recommended_action=Action.INVESTIGATE,
            assessment_id="guidance_test"
        )
        
        guidance = cascade._generate_execution_guidance(assessment)
        
        # Should have guidance for the identified gaps
        # Guidance/gap generation removed with heuristics - AI decides via self-assessment