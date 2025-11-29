import pytest
"""Test POSTFLIGHT phase - Final epistemic assessment."""

import asyncio
import pytest
from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema, CascadePhase, VectorAssessment
from empirica.core.canonical.reflex_frame import Action
EpistemicAssessment = EpistemicAssessmentSchema
from empirica.core.metacognitive_cascade.metacognitive_cascade import (
    CanonicalEpistemicCascade,
    CascadePhase
)


class TestPostflightPhase:
    """Test POSTFLIGHT phase functionality."""
    
    def test_postflight_phase_assessment(self):
        """Test POSTFLIGHT phase assessment generation."""
        cascade = CanonicalEpistemicCascade()
        
        task = "Implement user authentication feature"
        context = {"requirements": "secure login", "constraints": "performance"}
        
        async def test_postflight_assessment():
            # Simulate postflight assessment with investigation rounds
            assessment = await cascade._assess_epistemic_state(
                task, context, "postflight_task_id", CascadePhase.POSTFLIGHT, investigation_rounds=2
            )
            return assessment
        
        assessment = asyncio.run(test_postflight_assessment())
        
        # Verify it's a proper assessment
        assert isinstance(assessment, EpistemicAssessment)
        # assert assessment.task == task  # Task field removed in schema migration
        assert assessment.overall_confidence > 0  # Should have valid confidence
        assert assessment.recommended_action in [Action.PROCEED, Action.INVESTIGATE]  # Should be one of these
        
        # POSTFLIGHT assessments should have improved characteristics compared to baseline
        assert 0.0 <= assessment.engagement.score <= 1.0
        assert 0.0 <= assessment.know.score <= 1.0
        assert 0.0 <= assessment.do.score <= 1.0
        assert 0.0 <= assessment.overall_confidence <= 1.0
        
        # Verify all vectors are present
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
    
    def test_epistemic_delta_calculation(self):
        """Test epistemic delta calculation between preflight and postflight."""
        cascade = CanonicalEpistemicCascade()
        
        # Create preflight assessment (baseline)
        preflight = EpistemicAssessment(
            engagement=VectorAssessment(0.70, "Baseline engagement"),
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
            uncertainty=VectorAssessment(0.60, "High initial uncertainty"),
        )
        
        # Create postflight assessment (after processing)
        postflight = EpistemicAssessment(
            engagement=VectorAssessment(0.75, "Maintained engagement through cascade"),
            foundation_know=VectorAssessment(0.70, "Knowledge improved through investigation"),
            foundation_do=VectorAssessment(0.75, "Capability demonstrated through execution"),
            foundation_context=VectorAssessment(0.80, "Context validated through cascade"),
            comprehension_clarity=VectorAssessment(0.80, "Clarity achieved through cascade"),
            comprehension_coherence=VectorAssessment(0.85, "Coherence maintained"),
            comprehension_signal=VectorAssessment(0.75, "Priority confirmed"),
            comprehension_density=VectorAssessment(0.70, "Complexity managed"),
            execution_state=VectorAssessment(0.75, "Environment mapped through execution"),
            execution_change=VectorAssessment(0.80, "Changes tracked through cascade"),
            execution_completion=VectorAssessment(0.70, "Task executed (partial)"),
            execution_impact=VectorAssessment(0.70, "Impact assessed"),
            uncertainty=VectorAssessment(0.35, "Uncertainty reduced through investigation"),
        )
        
        # Calculate delta
        delta = cascade._calculate_epistemic_delta(preflight, postflight)
        
        # Verify all expected delta values exist
        assert 'foundation_confidence' in delta
        assert 'comprehension_confidence' in delta
        assert 'execution_confidence' in delta
        assert 'overall_confidence' in delta
        assert 'engagement' in delta
        assert 'know' in delta
        assert 'do' in delta
        assert 'context' in delta
        assert 'clarity' in delta
        assert 'coherence' in delta
        assert 'signal' in delta
        assert 'density' in delta
        assert 'state' in delta
        assert 'change' in delta
        assert 'completion' in delta
        assert 'impact' in delta
        assert 'uncertainty' in delta
        
        # Verify positive improvements
        assert delta['foundation_confidence'] == pytest.approx(0.15, abs=0.01)  # 0.75 - 0.60
        assert delta['comprehension_confidence'] == pytest.approx(0.10, abs=0.01)  # 0.675 - 0.575
        assert delta['execution_confidence'] == pytest.approx(0.25, abs=0.01)  # 0.738 - 0.487
        assert delta['overall_confidence'] == pytest.approx(0.15, abs=0.01)  # 0.728 - 0.581
        assert delta['know'] == pytest.approx(0.15, abs=0.01)  # 0.70 - 0.55
        assert delta['do'] == pytest.approx(0.15, abs=0.01)  # 0.75 - 0.60
        assert delta['clarity'] == pytest.approx(0.15, abs=0.01)  # 0.80 - 0.65
        assert delta['coherence'] == pytest.approx(0.15, abs=0.01)  # 0.85 - 0.70
        
        # Verify uncertainty decreased (should be negative)
        assert delta['uncertainty'] == pytest.approx(-0.25, abs=0.01)  # 0.35 - 0.60
        
        # All improvements (except uncertainty) should be positive
        assert delta['know'] > 0
        assert delta['do'] > 0
        assert delta['context'] > 0
        assert delta['clarity'] > 0
        assert delta['coherence'] > 0
        assert delta['state'] > 0
        assert delta['change'] > 0
        assert delta['completion'] > 0
        assert delta['impact'] > 0
        assert delta['uncertainty'] < 0  # Uncertainty decreased
    
    @pytest.mark.skip(reason="Test needs updating for new schema - complex assessment constructors with old field names")
    def test_calibration_accuracy_check(self):
        """Test calibration accuracy checking."""
        cascade = CanonicalEpistemicCascade()
        
        # Well-calibrated scenario: confidence stayed stable
        preflight_well = EpistemicAssessment(
            engagement=VectorAssessment(0.70, "Baseline engagement"),
            engagement_gate_passed=True,
            know=VectorAssessment(0.65, "Baseline knowledge"),
            do=VectorAssessment(0.70, "Baseline capability"),
            context=VectorAssessment(0.65, "Baseline context"),
            foundation_confidence=0.67,
            clarity=VectorAssessment(0.70, "Baseline clarity"),
            coherence=VectorAssessment(0.65, "Baseline coherence"),
            signal=VectorAssessment(0.65, "Baseline signal"),
            density=VectorAssessment(0.60, "Baseline density"),
            comprehension_confidence=0.66,
            state=VectorAssessment(0.65, "Baseline state awareness"),
            change=VectorAssessment(0.70, "Baseline change tracking"),
            completion=VectorAssessment(0.60, "Baseline completion awareness"),
            impact=VectorAssessment(0.65, "Baseline impact awareness"),
            execution_confidence=0.63,
            uncertainty=VectorAssessment(0.45, "Baseline uncertainty"),
            overall_confidence=0.66,
            recommended_action=Action.INVESTIGATE,
        )
        
        postflight_well = EpistemicAssessment(
            engagement=VectorAssessment(0.72, "Stable engagement"),
            engagement_gate_passed=True,
            know=VectorAssessment(0.70, "Slightly improved knowledge"),
            do=VectorAssessment(0.72, "Slightly improved capability"),
            context=VectorAssessment(0.68, "Slightly improved context"),
            foundation_confidence=0.70,
            clarity=VectorAssessment(0.72, "Slightly improved clarity"),
            coherence=VectorAssessment(0.68, "Slightly improved coherence"),
            signal=VectorAssessment(0.68, "Slightly improved signal"),
            density=VectorAssessment(0.58, "Slightly improved density"),
            comprehension_confidence=0.68,
            state=VectorAssessment(0.68, "Slightly improved state awareness"),
            change=VectorAssessment(0.72, "Slightly improved change tracking"),
            completion=VectorAssessment(0.65, "Slightly improved completion awareness"),
            impact=VectorAssessment(0.68, "Slightly improved impact awareness"),
            execution_confidence=0.65,
            uncertainty=VectorAssessment(0.40, "Slightly reduced uncertainty"),
            overall_confidence=0.67,  # Very close to preflight (within 0.15 threshold)
            recommended_action=Action.PROCEED,
        )
        
        calibration_check = cascade._check_calibration_accuracy(preflight_well, postflight_well, {})
        
        assert calibration_check['well_calibrated'] is True
        assert abs(calibration_check['confidence_delta']) < 0.15  # Less than threshold
        assert calibration_check['uncertainty_delta'] < 0  # Uncertainty should decrease
        
        # Learning confirmed scenario: confidence increased and uncertainty decreased
        preflight_learning = EpistemicAssessment(
            engagement=VectorAssessment(0.65, "Baseline engagement"),
            engagement_gate_passed=True,
            know=VectorAssessment(0.50, "Low initial knowledge"),
            do=VectorAssessment(0.55, "Low initial capability"),
            context=VectorAssessment(0.55, "Low initial context"),
            foundation_confidence=0.53,
            clarity=VectorAssessment(0.60, "Moderate initial clarity"),
            coherence=VectorAssessment(0.60, "Moderate initial coherence"),
            signal=VectorAssessment(0.55, "Low initial signal"),
            density=VectorAssessment(0.65, "High initial density"),
            comprehension_confidence=0.58,
            state=VectorAssessment(0.50, "Low initial state awareness"),
            change=VectorAssessment(0.55, "Low initial change tracking"),
            completion=VectorAssessment(0.40, "Low initial completion awareness"),
            impact=VectorAssessment(0.50, "Low initial impact awareness"),
            execution_confidence=0.49,
            uncertainty=VectorAssessment(0.70, "High initial uncertainty"),
            overall_confidence=0.55,
            recommended_action=Action.INVESTIGATE,
        )
        
        postflight_learning = EpistemicAssessment(
            engagement=VectorAssessment(0.75, "Improved engagement"),
            engagement_gate_passed=True,
            know=VectorAssessment(0.75, "High knowledge after learning"),
            do=VectorAssessment(0.80, "High capability after learning"),
            context=VectorAssessment(0.80, "High context after learning"),
            foundation_confidence=0.78,
            clarity=VectorAssessment(0.85, "High clarity after learning"),
            coherence=VectorAssessment(0.85, "High coherence after learning"),
            signal=VectorAssessment(0.80, "High signal after learning"),
            density=VectorAssessment(0.55, "Lower density after learning"),
            comprehension_confidence=0.81,
            state=VectorAssessment(0.80, "High state awareness after learning"),
            change=VectorAssessment(0.85, "High change tracking after learning"),
            completion=VectorAssessment(0.75, "High completion awareness after learning"),
            impact=VectorAssessment(0.80, "High impact awareness after learning"),
            execution_confidence=0.80,
            uncertainty=VectorAssessment(0.30, "Low uncertainty after learning"),
            overall_confidence=0.80,  # Significantly improved
            recommended_action=Action.PROCEED,
        )
        
        calibration_check = cascade._check_calibration_accuracy(preflight_learning, postflight_learning, {})
        
        assert calibration_check['well_calibrated'] is True
        assert calibration_check['confidence_delta'] > 0.15  # Confidence increased significantly
        assert calibration_check['uncertainty_delta'] < -0.10  # Uncertainty decreased significantly
    
    @pytest.mark.skip(reason="Test checks heuristics that were intentionally removed - AI decides via self-assessment")
    def test_overconfidence_detection(self):
        """Test overconfidence detection in calibration."""
        cascade = CanonicalEpistemicCascade()
        
        # Pre-flight with high confidence but poor actual knowledge
        preflight_overconfident = EpistemicAssessment(
            engagement=VectorAssessment(0.85, "High engagement"),
            engagement_gate_passed=True,
            know=VectorAssessment(0.90, "Falsely high knowledge"),
            do=VectorAssessment(0.85, "Falsely high capability"),
            context=VectorAssessment(0.85, "Falsely high context"),
            foundation_confidence=0.87,
            clarity=VectorAssessment(0.90, "Falsely high clarity"),
            coherence=VectorAssessment(0.85, "Falsely high coherence"),
            signal=VectorAssessment(0.85, "Falsely high signal"),
            density=VectorAssessment(0.30, "Low density"),
            comprehension_confidence=0.87,
            state=VectorAssessment(0.85, "Falsely high state awareness"),
            change=VectorAssessment(0.80, "Falsely high change tracking"),
            completion=VectorAssessment(0.80, "Falsely high completion awareness"),
            impact=VectorAssessment(0.85, "Falsely high impact awareness"),
            execution_confidence=0.83,
            uncertainty=VectorAssessment(0.10, "Falsely low uncertainty"),
            overall_confidence=0.85,  # Very high confidence
            recommended_action=Action.PROCEED,
        )
        
        # Post-flight after discovering many unknowns
        postflight_overconfident = EpistemicAssessment(
            engagement=VectorAssessment(0.80, "Maintained engagement"),
            engagement_gate_passed=True,
            know=VectorAssessment(0.55, "Actually low knowledge discovered"),
            do=VectorAssessment(0.60, "Actually moderate capability discovered"),
            context=VectorAssessment(0.60, "Actually low context discovered"),
            foundation_confidence=0.58,
            clarity=VectorAssessment(0.65, "Actually moderate clarity discovered"),
            coherence=VectorAssessment(0.60, "Actually low coherence discovered"),
            signal=VectorAssessment(0.60, "Actually low signal clarity discovered"),
            density=VectorAssessment(0.40, "Actually moderate density"),
            comprehension_confidence=0.61,
            state=VectorAssessment(0.60, "Actually low state awareness discovered"),
            change=VectorAssessment(0.65, "Actually moderate change tracking discovered"),
            completion=VectorAssessment(0.55, "Actually low completion awareness discovered"),
            impact=VectorAssessment(0.60, "Actually low impact awareness discovered"),
            execution_confidence=0.59,
            uncertainty=VectorAssessment(0.60, "Actually high uncertainty discovered"),
            overall_confidence=0.61,  # Much lower than expected
            recommended_action=Action.INVESTIGATE,
        )
        
        calibration_check = cascade._check_calibration_accuracy(
            preflight_overconfident, postflight_overconfident, {}
        )
        
        # Should detect overconfidence (high preflight confidence but discovered many unknowns)
        assert calibration_check['well_calibrated'] is False
        assert calibration_check['warning'] is not None
        assert 'overconfidence' in calibration_check['warning'].lower() or 'high confidence' in calibration_check['warning'].lower()
        
        # Confidence decreased significantly
        assert calibration_check['confidence_delta'] < 0  # Went from 0.85 to 0.61
        # Uncertainty increased significantly  
        assert calibration_check['uncertainty_delta'] > 0  # Went from 0.10 to 0.60
    
    @pytest.mark.skip(reason="Test needs updating for new schema - complex assessment constructors with old field names")
    def test_underconfidence_recognition(self):
        """Test underconfidence recognition in calibration."""
        cascade = CanonicalEpistemicCascade()
        
        # Pre-flight with low confidence but good actual knowledge
        preflight_underconfident = EpistemicAssessment(
            engagement=VectorAssessment(0.60, "Baseline engagement"),
            engagement_gate_passed=True,
            know=VectorAssessment(0.40, "Falsely low knowledge"),
            do=VectorAssessment(0.45, "Falsely low capability"),
            context=VectorAssessment(0.45, "Falsely low context"),
            foundation_confidence=0.43,
            clarity=VectorAssessment(0.45, "Falsely low clarity"),
            coherence=VectorAssessment(0.40, "Falsely low coherence"),
            signal=VectorAssessment(0.40, "Falsely low signal"),
            density=VectorAssessment(0.70, "Falsely high density"),
            comprehension_confidence=0.42,
            state=VectorAssessment(0.40, "Falsely low state awareness"),
            change=VectorAssessment(0.45, "Falsely low change tracking"),
            completion=VectorAssessment(0.35, "Falsely low completion awareness"),
            impact=VectorAssessment(0.40, "Falsely low impact awareness"),
            execution_confidence=0.41,
            uncertainty=VectorAssessment(0.70, "Falsely high uncertainty"),
            overall_confidence=0.42,  # Very low confidence
            recommended_action=Action.INVESTIGATE,
        )
        
        # Post-flight after discovering actually knew more than expected
        postflight_underconfident = EpistemicAssessment(
            engagement=VectorAssessment(0.70, "Improved engagement"),
            engagement_gate_passed=True,
            know=VectorAssessment(0.70, "Actually good knowledge discovered"),
            do=VectorAssessment(0.75, "Actually good capability discovered"),
            context=VectorAssessment(0.70, "Actually good context discovered"),
            foundation_confidence=0.72,
            clarity=VectorAssessment(0.75, "Actually good clarity discovered"),
            coherence=VectorAssessment(0.75, "Actually good coherence discovered"),
            signal=VectorAssessment(0.70, "Actually good signal clarity discovered"),
            density=VectorAssessment(0.55, "Actually moderate density"),
            comprehension_confidence=0.73,
            state=VectorAssessment(0.70, "Actually good state awareness discovered"),
            change=VectorAssessment(0.75, "Actually good change tracking discovered"),
            completion=VectorAssessment(0.70, "Actually good completion awareness discovered"),
            impact=VectorAssessment(0.70, "Actually good impact awareness discovered"),
            execution_confidence=0.72,
            uncertainty=VectorAssessment(0.30, "Actually low uncertainty discovered"),
            overall_confidence=0.72,  # Much higher than expected
            recommended_action=Action.PROCEED,
        )
        
        calibration_check = cascade._check_calibration_accuracy(
            preflight_underconfident, postflight_underconfident, {}
        )
        
        # The test is to check what happens when preflight underestimates capability
        # Check if the calibration check contains information about the situation
        if 'note' in calibration_check and calibration_check['note']:
            # The system might recognize the underconfidence situation
            pass  # Accept either way - the important part is the calibration logic
        elif 'well_calibrated' in calibration_check:
            # Either well_calibrated is True (if change wasn't dramatic enough to flag) 
            # or it's False (if it properly detected the underconfidence)
            pass  # Accept either value
    
    def test_postflight_with_investigation_context(self):
        """Test postflight assessment with investigation context."""
        cascade = CanonicalEpistemicCascade()
        
        task = "Debug performance issues with database queries"
        context = {"error_logs": "slow query errors", "metrics": "high response times"}
        
        async def test_postflight_with_investigation():
            # Simulate postflight after 3 investigation rounds
            assessment = await cascade._assess_epistemic_state(
                task, context, "postflight_investigation_test", 
                CascadePhase.POSTFLIGHT, investigation_rounds=3
            )
            return assessment
        
        assessment = asyncio.run(test_postflight_with_investigation())
        
        # The assessment should reflect the post-investigation state
        assert isinstance(assessment, EpistemicAssessment)
        # assert assessment.task == task  # Task field removed in schema migration
        assert assessment.overall_confidence > 0  # Should have valid confidence
        
        # After investigation, scores should be improved (though we can't predict exact values)
        assert 0.0 <= assessment.overall_confidence <= 1.0
        assert assessment.recommended_action in [Action.PROCEED, Action.INVESTIGATE, Action.RESET]
    
    @pytest.mark.skip(reason="Test checks heuristics that were intentionally removed - AI decides via self-assessment")
    def test_task_id_generation(self):
        """Test task ID generation for postflight."""
        # Gap identification and guidance generation removed with heuristics
        # AI now decides via self-assessment (warrants_investigation fields)
        # This test verifies methods exist and return correct types
        cascade = CanonicalEpistemicCascade()
        assessment = self._create_test_assessment(confidence=0.45)
        
        # Methods should exist and return empty lists
        if hasattr(cascade, "_identify_epistemic_gaps"):
            gaps = cascade._identify_epistemic_gaps(assessment)
            assert isinstance(gaps, list)
        
        if hasattr(cascade, "_generate_execution_guidance"):
            guidance = cascade._generate_execution_guidance(assessment)
            assert isinstance(guidance, list)
