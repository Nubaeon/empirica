"""Test CHECK phase - Self-assessment before acting."""

import asyncio
from empirica.core.canonical.reflex_frame import EpistemicAssessment, VectorState, Action
from empirica.core.metacognitive_cascade.metacognitive_cascade import (
    CanonicalEpistemicCascade,
    CascadePhase
)


class TestCheckPhase:
    """Test CHECK phase functionality."""
    
    def test_check_phase_assessment(self):
        """Test CHECK phase assessment generation."""
        cascade = CanonicalEpistemicCascade()
        
        task = "Implement user authentication feature"
        context = {"requirements": "secure login", "constraints": "performance"}
        
        async def test_check_assessment():
            assessment = await cascade._assess_epistemic_state(
                task, context, "check_task_id", CascadePhase.CHECK
            )
            return assessment
        
        assessment = asyncio.run(test_check_assessment())
        
        # Verify it's a proper assessment
        assert isinstance(assessment, EpistemicAssessment)
        assert assessment.task == task
        assert assessment.engagement_gate_passed is True  # Should pass threshold
        assert assessment.recommended_action == Action.INVESTIGATE  # Default for CHECK phase
        
        # CHECK assessments should have baseline characteristics
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
    
    def test_readiness_verification(self):
        """Test readiness verification logic."""
        cascade = CanonicalEpistemicCascade()
        
        # Test assessment with high confidence - should be ready to act
        high_conf_assessment = EpistemicAssessment(
            engagement=VectorState(0.8, "High engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.8, "High domain knowledge"),
            do=VectorState(0.8, "High capability"),
            context=VectorState(0.8, "High context understanding"),
            foundation_confidence=0.8,
            clarity=VectorState(0.85, "High clarity"),
            coherence=VectorState(0.9, "High coherence"),
            signal=VectorState(0.8, "High signal clarity"),
            density=VectorState(0.2, "Low information density"),
            comprehension_confidence=0.85,
            state=VectorState(0.8, "High state awareness"),
            change=VectorState(0.85, "High change tracking"),
            completion=VectorState(0.75, "High completion awareness"),
            impact=VectorState(0.8, "High impact understanding"),
            execution_confidence=0.8,
            uncertainty=VectorState(0.15, "Low uncertainty"),
            overall_confidence=0.82,  # High confidence
            recommended_action=Action.PROCEED,
            assessment_id="high_confidence_test"
        )
        
        readiness_check = cascade._verify_readiness(high_conf_assessment)
        
        assert readiness_check['ready_to_act'] is True
        assert readiness_check['recommended_action'] == 'proceed'
        assert readiness_check['overall_confidence'] == 0.82
        assert readiness_check['engagement_gate_passed'] is True
        
        # Test assessment with low confidence - should not be ready to act
        low_conf_assessment = EpistemicAssessment(
            engagement=VectorState(0.75, "Good engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.4, "Low domain knowledge"),
            do=VectorState(0.5, "Moderate capability"),
            context=VectorState(0.45, "Low context understanding"),
            foundation_confidence=0.45,
            clarity=VectorState(0.5, "Low clarity"),
            coherence=VectorState(0.55, "Low coherence"),
            signal=VectorState(0.45, "Low signal clarity"),
            density=VectorState(0.7, "High information density"),
            comprehension_confidence=0.5,
            state=VectorState(0.45, "Low state awareness"),
            change=VectorState(0.5, "Moderate change tracking"),
            completion=VectorState(0.35, "Low completion awareness"),
            impact=VectorState(0.45, "Low impact understanding"),
            execution_confidence=0.43,
            uncertainty=VectorState(0.65, "High uncertainty"),
            overall_confidence=0.47,  # Below threshold of 0.70
            recommended_action=Action.INVESTIGATE,
            assessment_id="low_confidence_test"
        )
        
        readiness_check = cascade._verify_readiness(low_conf_assessment)
        
        assert readiness_check['ready_to_act'] is False
        assert readiness_check['recommended_action'] == 'investigate'
        assert readiness_check['overall_confidence'] == 0.47
        assert readiness_check['engagement_gate_passed'] is True
    
    def test_critical_flags_check(self):
        """Test critical flags in readiness verification."""
        cascade = CanonicalEpistemicCascade()
        
        # Assessment with critical coherence flag set
        critical_assessment = EpistemicAssessment(
            engagement=VectorState(0.8, "High engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.7, "Good domain knowledge"),
            do=VectorState(0.75, "Good capability"),
            context=VectorState(0.7, "Good context understanding"),
            foundation_confidence=0.72,
            clarity=VectorState(0.75, "Good clarity"),
            coherence=VectorState(0.3, "LOW COHERENCE - CRITICAL!"),  # Below 0.50 threshold
            signal=VectorState(0.7, "Good signal clarity"),
            density=VectorState(0.25, "Low information density"),
            comprehension_confidence=0.63,
            state=VectorState(0.7, "Good state awareness"),
            change=VectorState(0.75, "Good change tracking"),
            completion=VectorState(0.7, "Good completion awareness"),
            impact=VectorState(0.7, "Good impact understanding"),
            execution_confidence=0.72,
            uncertainty=VectorState(0.35, "Low uncertainty"),
            overall_confidence=0.71,
            recommended_action=Action.RESET,  # Should be RESET due to low coherence
            assessment_id="critical_flags_test"
        )
        
        readiness_check = cascade._verify_readiness(critical_assessment)
        
        assert readiness_check['ready_to_act'] is False
        assert readiness_check['recommended_action'] == 'reset'
        assert readiness_check['critical_flags']['coherence_critical'] is True
        assert readiness_check['critical_flags']['density_critical'] is False
        assert readiness_check['critical_flags']['change_critical'] is False
        
        # Assessment with critical density flag set
        density_critical_assessment = EpistemicAssessment(
            engagement=VectorState(0.75, "Good engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.8, "High domain knowledge"),
            do=VectorState(0.75, "Good capability"),
            context=VectorState(0.8, "High context understanding"),
            foundation_confidence=0.78,
            clarity=VectorState(0.8, "High clarity"),
            coherence=VectorState(0.85, "High coherence"),
            signal=VectorState(0.75, "Good signal clarity"),
            density=VectorState(0.95, "HIGH DENSITY - CRITICAL!"),  # Above 0.90 threshold
            comprehension_confidence=0.81,
            state=VectorState(0.8, "High state awareness"),
            change=VectorState(0.75, "Good change tracking"),
            completion=VectorState(0.8, "High completion awareness"),
            impact=VectorState(0.8, "High impact understanding"),
            execution_confidence=0.78,
            uncertainty=VectorState(0.25, "Low uncertainty"),
            overall_confidence=0.79,
            recommended_action=Action.RESET,  # Should be RESET due to high density
            assessment_id="density_critical_test"
        )
        
        readiness_check = cascade._verify_readiness(density_critical_assessment)
        
        assert readiness_check['ready_to_act'] is False
        assert readiness_check['recommended_action'] == 'reset'
        assert readiness_check['critical_flags']['coherence_critical'] is False
        assert readiness_check['critical_flags']['density_critical'] is True
        assert readiness_check['critical_flags']['change_critical'] is False
    
    def test_decision_making_process(self):
        """Test the decision making process in CHECK phase."""
        cascade = CanonicalEpistemicCascade()
        
        # High confidence assessment
        high_conf_assessment = EpistemicAssessment(
            engagement=VectorState(0.85, "High engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.8, "High domain knowledge"),
            do=VectorState(0.8, "High capability"),
            context=VectorState(0.8, "High context understanding"),
            foundation_confidence=0.8,
            clarity=VectorState(0.85, "High clarity"),
            coherence=VectorState(0.9, "High coherence"),
            signal=VectorState(0.8, "High signal clarity"),
            density=VectorState(0.2, "Low information density"),
            comprehension_confidence=0.85,
            state=VectorState(0.8, "High state awareness"),
            change=VectorState(0.85, "High change tracking"),
            completion=VectorState(0.8, "High completion awareness"),
            impact=VectorState(0.8, "High impact understanding"),
            execution_confidence=0.83,
            uncertainty=VectorState(0.15, "Low uncertainty"),
            overall_confidence=0.82,
            recommended_action=Action.PROCEED,
            assessment_id="decision_high_conf_test"
        )
        
        check_result = cascade._verify_readiness(high_conf_assessment)
        decision = cascade._make_final_decision(high_conf_assessment, check_result, 0)
        
        assert decision['action'] == 'proceed'
        assert decision['confidence'] == 0.82
        assert 'overall confidence: 0.82' in decision['rationale'].lower()
        assert decision['engagement_gate_passed'] is True
        
        # Low confidence assessment
        low_conf_assessment = EpistemicAssessment(
            engagement=VectorState(0.7, "Moderate engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.45, "Low domain knowledge"),
            do=VectorState(0.5, "Moderate capability"),
            context=VectorState(0.5, "Moderate context understanding"),
            foundation_confidence=0.48,
            clarity=VectorState(0.55, "Moderate clarity"),
            coherence=VectorState(0.6, "Moderate coherence"),
            signal=VectorState(0.5, "Low signal clarity"),
            density=VectorState(0.65, "Moderate density"),
            comprehension_confidence=0.55,
            state=VectorState(0.5, "Moderate state awareness"),
            change=VectorState(0.55, "Moderate change tracking"),
            completion=VectorState(0.4, "Low completion awareness"),
            impact=VectorState(0.5, "Moderate impact understanding"),
            execution_confidence=0.48,
            uncertainty=VectorState(0.6, "High uncertainty"),
            overall_confidence=0.52,
            recommended_action=Action.INVESTIGATE,
            assessment_id="decision_low_conf_test"
        )
        
        check_result = cascade._verify_readiness(low_conf_assessment)
        decision = cascade._make_final_decision(low_conf_assessment, check_result, 2)
        
        assert decision['action'] == 'investigate'
        assert decision['confidence'] == 0.52
        assert decision['investigation_rounds'] == 2
        assert '2 investigation round' in decision['rationale']
    
    def test_decision_rationale_generation(self):
        """Test generation of decision rationale."""
        cascade = CanonicalEpistemicCascade()
        
        assessment = EpistemicAssessment(
            engagement=VectorState(0.75, "Good engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.65, "Moderate domain knowledge"),
            do=VectorState(0.7, "Good capability"),
            context=VectorState(0.65, "Good context understanding"),
            foundation_confidence=0.67,
            clarity=VectorState(0.7, "Good clarity"),
            coherence=VectorState(0.75, "Good coherence"),
            signal=VectorState(0.65, "Good signal clarity"),
            density=VectorState(0.55, "Low density"),
            comprehension_confidence=0.68,
            state=VectorState(0.65, "Good state awareness"),
            change=VectorState(0.7, "Good change tracking"),
            completion=VectorState(0.6, "Good completion awareness"),
            impact=VectorState(0.65, "Good impact understanding"),
            execution_confidence=0.65,
            uncertainty=VectorState(0.4, "Moderate uncertainty"),
            overall_confidence=0.66,
            recommended_action=Action.INVESTIGATE,
            assessment_id="rationale_test"
        )
        
        rationale = cascade._build_decision_rationale(assessment, 1)
        
        assert '0.66' in rationale  # overall confidence value should be in the rationale
        assert 'Foundation: 0.67' in rationale  # Note the capital F and colon
        assert 'Comprehension: 0.68' in rationale  # Note the capital C and colon
        assert 'Execution: 0.65' in rationale  # Note the capital E and colon
        assert '1 investigation round' in rationale
        assert 'investigate' in rationale.lower()
    
    def test_execution_guidance_generation(self):
        """Test generation of execution guidance based on vector state."""
        cascade = CanonicalEpistemicCascade()
        
        # Create assessment with various vector scores to trigger different guidance
        assessment = EpistemicAssessment(
            engagement=VectorState(0.65, "Baseline engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.55, "Low domain knowledge"),  # Should trigger validation guidance
            do=VectorState(0.65, "Moderate capability"),    # Should trigger testing guidance
            context=VectorState(0.55, "Low context understanding"),  # Should trigger verification guidance
            foundation_confidence=0.58,
            clarity=VectorState(0.55, "Low clarity"),       # Should trigger user confirmation
            coherence=VectorState(0.65, "Moderate coherence"),  # Should trigger review guidance
            signal=VectorState(0.65, "Moderate signal"),
            density=VectorState(0.55, "Moderate density"),
            comprehension_confidence=0.60,
            state=VectorState(0.55, "Low state awareness"),  # Should trigger environment mapping
            change=VectorState(0.50, "Low change tracking"), # Should trigger careful tracking
            completion=VectorState(0.60, "Moderate completion awareness"),
            impact=VectorState(0.55, "Low impact understanding"),  # Should trigger consequence analysis
            execution_confidence=0.55,
            uncertainty=VectorState(0.55, "Moderate uncertainty"),
            overall_confidence=0.58,
            recommended_action=Action.INVESTIGATE,
            assessment_id="guidance_test"
        )
        
        guidance = cascade._generate_execution_guidance(assessment)
        
        # Guidance generation removed with heuristics - AI decides via self-assessment
        # Verify method returns correct type, no longer asserting specific content
        assert isinstance(guidance, list)
    
    def test_check_phase_with_investigation_rounds(self):
        """Test CHECK phase with investigation rounds counted."""
        cascade = CanonicalEpistemicCascade()
        
        task = "Debug complex performance issue"
        context = {"perf_logs": "high latency", "metrics": "slow queries"}
        
        # Simulate an assessment after several investigation rounds
        assessment_after_investigation = EpistemicAssessment(
            engagement=VectorState(0.8, "Maintained engagement after investigations"),
            engagement_gate_passed=True,
            know=VectorState(0.7, "Improved knowledge after investigations"),
            do=VectorState(0.75, "Good capability for debugging"),
            context=VectorState(0.75, "Better context understanding"),
            foundation_confidence=0.73,
            clarity=VectorState(0.8, "Improved clarity"),
            coherence=VectorState(0.85, "Better coherence"),
            signal=VectorState(0.75, "Better signal clarity"),
            density=VectorState(0.4, "Reduced information density"),
            comprehension_confidence=0.75,
            state=VectorState(0.75, "Better state awareness"),
            change=VectorState(0.8, "Better change tracking"),
            completion=VectorState(0.65, "Better completion awareness"),
            impact=VectorState(0.75, "Better impact understanding"),
            execution_confidence=0.75,
            uncertainty=VectorState(0.3, "Reduced uncertainty"),
            overall_confidence=0.75,  # Now at threshold after investigation
            recommended_action=Action.PROCEED,
            assessment_id="post_investigation_test"
        )
        
        # Verify readiness check after investigation
        readiness_check = cascade._verify_readiness(assessment_after_investigation)
        
        # Should be ready to act since confidence is at threshold
        decision = cascade._make_final_decision(
            assessment_after_investigation, readiness_check, investigation_rounds=3
        )
        
        assert decision['action'] == 'proceed'
        assert decision['investigation_rounds'] == 3
        assert decision['confidence'] == 0.75
        assert '3 investigation round' in decision['rationale']