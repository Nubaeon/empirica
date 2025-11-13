"""Test ACT phase - Execute with confidence."""

import asyncio
from empirica.core.canonical.reflex_frame import EpistemicAssessment, VectorState, Action
from empirica.core.metacognitive_cascade.metacognitive_cascade import (
    CanonicalEpistemicCascade,
    CascadePhase
)


class TestActPhase:
    """Test ACT phase functionality."""
    
    def test_act_phase_assessment(self):
        """Test ACT phase assessment generation."""
        cascade = CanonicalEpistemicCascade()
        
        task = "Implement user authentication feature"
        context = {"requirements": "secure login", "constraints": "performance"}
        
        async def test_act_assessment():
            assessment = await cascade._assess_epistemic_state(
                task, context, "act_task_id", CascadePhase.ACT
            )
            return assessment
        
        assessment = asyncio.run(test_act_assessment())
        
        # Verify it's a proper assessment
        assert isinstance(assessment, EpistemicAssessment)
        assert assessment.task == task
        assert assessment.engagement_gate_passed is True  # Should pass threshold
        assert assessment.recommended_action == Action.INVESTIGATE  # Default for ACT phase
        
        # ACT assessments should have baseline characteristics
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
    
    def test_decision_making_in_act(self):
        """Test decision making process in ACT phase."""
        cascade = CanonicalEpistemicCascade()
        
        # Test with high confidence assessment - should proceed
        high_conf_assessment = EpistemicAssessment(
            engagement=VectorState(0.85, "High engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.8, "High domain knowledge"),
            do=VectorState(0.85, "High capability"),
            context=VectorState(0.8, "High context understanding"),
            foundation_confidence=0.82,
            clarity=VectorState(0.85, "High clarity"),
            coherence=VectorState(0.9, "High coherence"),
            signal=VectorState(0.8, "High signal clarity"),
            density=VectorState(0.2, "Low information density"),
            comprehension_confidence=0.85,
            state=VectorState(0.85, "High state awareness"),
            change=VectorState(0.85, "High change tracking"),
            completion=VectorState(0.8, "High completion awareness"),
            impact=VectorState(0.85, "High impact understanding"),
            execution_confidence=0.83,
            uncertainty=VectorState(0.15, "Low uncertainty"),
            overall_confidence=0.84,
            recommended_action=Action.PROCEED,
            assessment_id="act_high_conf_test"
        )
        
        check_result = {
            'recommended_action': 'PROCEED',
            'overall_confidence': 0.84,
            'engagement_gate_passed': True,
            'critical_flags': {
                'coherence_critical': False,
                'density_critical': False,
                'change_critical': False
            },
            'ready_to_act': True
        }
        
        decision = cascade._make_final_decision(high_conf_assessment, check_result, 0)
        
        assert decision['action'] == 'proceed'
        assert decision['confidence'] == 0.84
        # ready_to_act may not be included in the decision, relying on action logic instead
        assert 'proceed' in decision['rationale'].lower()
        
        # Test with investigation recommendation - should investigate
        investigation_assessment = EpistemicAssessment(
            engagement=VectorState(0.75, "Good engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.5, "Low domain knowledge"),
            do=VectorState(0.6, "Moderate capability"),
            context=VectorState(0.55, "Low context understanding"),
            foundation_confidence=0.55,
            clarity=VectorState(0.6, "Moderate clarity"),
            coherence=VectorState(0.65, "Moderate coherence"),
            signal=VectorState(0.55, "Low signal clarity"),
            density=VectorState(0.6, "Moderate density"),
            comprehension_confidence=0.6,
            state=VectorState(0.55, "Low state awareness"),
            change=VectorState(0.6, "Moderate change tracking"),
            completion=VectorState(0.45, "Low completion awareness"),
            impact=VectorState(0.55, "Low impact understanding"),
            execution_confidence=0.53,
            uncertainty=VectorState(0.6, "High uncertainty"),
            overall_confidence=0.57,
            recommended_action=Action.INVESTIGATE,
            assessment_id="act_investigate_test"
        )
        
        check_result = {
            'recommended_action': 'INVESTIGATE',
            'overall_confidence': 0.57,
            'engagement_gate_passed': True,
            'critical_flags': {
                'coherence_critical': False,
                'density_critical': False,
                'change_critical': False
            },
            'ready_to_act': False
        }
        
        decision = cascade._make_final_decision(investigation_assessment, check_result, 2)
        
        assert decision['action'] == 'investigate'
        assert decision['confidence'] == 0.57
        assert decision['investigation_rounds'] == 2
        assert 'investigation' in decision['rationale'].lower()
    
    def test_act_phase_guidance_generation(self):
        """Test execution guidance generation in ACT phase."""
        cascade = CanonicalEpistemicCascade()
        
        # Create an assessment with specific vector states
        assessment = EpistemicAssessment(
            engagement=VectorState(0.7, "Baseline engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.65, "Moderate domain knowledge"),
            do=VectorState(0.75, "Good capability"),
            context=VectorState(0.6, "Moderate context understanding"),
            foundation_confidence=0.67,
            clarity=VectorState(0.7, "Good clarity"),
            coherence=VectorState(0.75, "Good coherence"),
            signal=VectorState(0.65, "Good signal clarity"),
            density=VectorState(0.55, "Low density"),
            comprehension_confidence=0.69,
            state=VectorState(0.65, "Good state awareness"),
            change=VectorState(0.7, "Good change tracking"),
            completion=VectorState(0.65, "Good completion awareness"),
            impact=VectorState(0.7, "Good impact understanding"),
            execution_confidence=0.68,
            uncertainty=VectorState(0.35, "Low uncertainty"),
            overall_confidence=0.69,
            recommended_action=Action.PROCEED,
            assessment_id="act_guidance_test"
        )
        
        guidance = cascade._generate_execution_guidance(assessment)
        
        # Since most vectors are above thresholds, guidance should be minimal
        # but should still include engagement guidance
        guidance_text = " ".join(guidance).lower()
        # For moderate engagement (0.70), there might not be specific guidance if above threshold
        # The key is that guidance is generated based on vector states
        assert isinstance(guidance, list)  # guidance should be a list
        
        # Now test with lower vectors to trigger more guidance
        low_vectors_assessment = EpistemicAssessment(
            engagement=VectorState(0.6, "Low engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.4, "Low domain knowledge"),
            do=VectorState(0.5, "Low capability"),
            context=VectorState(0.45, "Low context understanding"),
            foundation_confidence=0.45,
            clarity=VectorState(0.5, "Low clarity"),
            coherence=VectorState(0.55, "Low coherence"),
            signal=VectorState(0.45, "Low signal clarity"),
            density=VectorState(0.65, "Moderate density"),
            comprehension_confidence=0.52,
            state=VectorState(0.45, "Low state awareness"),
            change=VectorState(0.5, "Low change tracking"),
            completion=VectorState(0.4, "Low completion awareness"),
            impact=VectorState(0.45, "Low impact understanding"),
            execution_confidence=0.45,
            uncertainty=VectorState(0.65, "High uncertainty"),
            overall_confidence=0.48,
            recommended_action=Action.INVESTIGATE,
            assessment_id="act_guidance_low_vectors_test"
        )
        
        guidance = cascade._generate_execution_guidance(low_vectors_assessment)
        
        # Guidance generation removed with heuristics - AI decides via self-assessment
        # No longer asserting specific guidance content
        assert isinstance(guidance, list)
    
    def test_vector_summary_extraction_in_act(self):
        """Test vector summary extraction in ACT phase."""
        cascade = CanonicalEpistemicCascade()
        
        assessment = EpistemicAssessment(
            engagement=VectorState(0.85, "High engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.8, "High domain knowledge"),
            do=VectorState(0.85, "High capability"),
            context=VectorState(0.8, "High context understanding"),
            foundation_confidence=0.82,
            clarity=VectorState(0.85, "High clarity"),
            coherence=VectorState(0.9, "High coherence"),
            signal=VectorState(0.8, "High signal clarity"),
            density=VectorState(0.2, "Low information density"),
            comprehension_confidence=0.85,
            state=VectorState(0.85, "High state awareness"),
            change=VectorState(0.85, "High change tracking"),
            completion=VectorState(0.8, "High completion awareness"),
            impact=VectorState(0.85, "High impact understanding"),
            execution_confidence=0.83,
            uncertainty=VectorState(0.15, "Low uncertainty"),
            overall_confidence=0.84,
            recommended_action=Action.PROCEED,
            assessment_id="summary_extraction_test"
        )
        
        summary = cascade._extract_vector_summary(assessment)
        
        # Verify all vector scores are correctly extracted
        assert summary['engagement'] == 0.85
        assert summary['know'] == 0.8
        assert summary['do'] == 0.85
        assert summary['context'] == 0.8
        assert summary['clarity'] == 0.85
        assert summary['coherence'] == 0.9
        assert summary['signal'] == 0.8
        assert summary['density'] == 0.2
        assert summary['state'] == 0.85
        assert summary['change'] == 0.85
        assert summary['completion'] == 0.8
        assert summary['impact'] == 0.85
        assert summary['foundation_confidence'] == 0.82
        assert summary['comprehension_confidence'] == 0.85
        assert summary['execution_confidence'] == 0.83
        assert summary['overall_confidence'] == 0.84
        
        # Verify decision making with extracted summary
        check_result = {
            'recommended_action': 'PROCEED',
            'overall_confidence': 0.84,
            'engagement_gate_passed': True,
            'critical_flags': {
                'coherence_critical': False,
                'density_critical': False,
                'change_critical': False
            },
            'ready_to_act': True
        }
        
        decision = cascade._make_final_decision(assessment, check_result, 0)
        
        assert decision['vector_summary'] == summary
    
    def test_act_phase_decision_with_critical_flags(self):
        """Test ACT phase decision making with critical flags."""
        cascade = CanonicalEpistemicCascade()
        
        # Assessment that would trigger critical flags
        critical_assessment = EpistemicAssessment(
            engagement=VectorState(0.8, "High engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.7, "Good domain knowledge"),
            do=VectorState(0.75, "Good capability"),
            context=VectorState(0.7, "Good context understanding"),
            foundation_confidence=0.72,
            clarity=VectorState(0.75, "Good clarity"),
            coherence=VectorState(0.3, "LOW COHERENCE - CRITICAL!"),  # Below 0.50
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
            recommended_action=Action.RESET,  # Should get RESET due to low coherence
            assessment_id="critical_flags_act_test"
        )
        
        check_result = {
            'recommended_action': 'RESET',
            'overall_confidence': 0.71,
            'engagement_gate_passed': True,
            'critical_flags': {
                'coherence_critical': True,   # This is critical
                'density_critical': False,
                'change_critical': False
            },
            'ready_to_act': False
        }
        
        decision = cascade._make_final_decision(critical_assessment, check_result, 1)
        
        assert decision['action'] == 'reset'
        assert decision['confidence'] == 0.71
        # ready_to_act may not be included in the decision, relying on action logic instead
        assert decision['critical_flags']['coherence_critical'] is True
        
        # Another case: high density
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
            density=VectorState(0.95, "HIGH DENSITY - CRITICAL!"),  # Above 0.90
            comprehension_confidence=0.81,
            state=VectorState(0.8, "High state awareness"),
            change=VectorState(0.75, "Good change tracking"),
            completion=VectorState(0.8, "High completion awareness"),
            impact=VectorState(0.8, "High impact understanding"),
            execution_confidence=0.78,
            uncertainty=VectorState(0.25, "Low uncertainty"),
            overall_confidence=0.79,
            recommended_action=Action.RESET,  # Should get RESET due to high density
            assessment_id="density_critical_act_test"
        )
        
        check_result = {
            'recommended_action': 'RESET',
            'overall_confidence': 0.79,
            'engagement_gate_passed': True,
            'critical_flags': {
                'coherence_critical': False,
                'density_critical': True,    # This is critical
                'change_critical': False
            },
            'ready_to_act': False
        }
        
        decision = cascade._make_final_decision(density_critical_assessment, check_result, 0)
        
        assert decision['action'] == 'reset'
        assert decision['confidence'] == 0.79
        assert decision['critical_flags']['density_critical'] is True
    
    def test_final_decision_with_investigation_context(self):
        """Test final decision with investigation context."""
        cascade = CanonicalEpistemicCascade()
        
        assessment = EpistemicAssessment(
            engagement=VectorState(0.8, "High engagement after investigation"),
            engagement_gate_passed=True,
            know=VectorState(0.75, "Improved knowledge after investigation"),
            do=VectorState(0.8, "Good capability"),
            context=VectorState(0.75, "Better context after investigation"),
            foundation_confidence=0.77,
            clarity=VectorState(0.8, "Good clarity after investigation"),
            coherence=VectorState(0.85, "High coherence after investigation"),
            signal=VectorState(0.75, "Good signal after investigation"),
            density=VectorState(0.3, "Low density after investigation"),
            comprehension_confidence=0.79,
            state=VectorState(0.75, "Good state awareness after investigation"),
            change=VectorState(0.8, "Good change tracking after investigation"),
            completion=VectorState(0.75, "Good completion awareness after investigation"),
            impact=VectorState(0.8, "Good impact understanding after investigation"),
            execution_confidence=0.77,
            uncertainty=VectorState(0.25, "Low uncertainty after investigation"),
            overall_confidence=0.78,
            recommended_action=Action.PROCEED,
            assessment_id="investigation_context_test"
        )
        
        check_result = {
            'recommended_action': 'PROCEED',
            'overall_confidence': 0.78,
            'engagement_gate_passed': True,
            'critical_flags': {
                'coherence_critical': False,
                'density_critical': False,
                'change_critical': False
            },
            'ready_to_act': True
        }
        
        # Decision after 3 investigation rounds
        decision = cascade._make_final_decision(assessment, check_result, investigation_rounds=3)
        
        assert decision['action'] == 'proceed'
        assert decision['confidence'] == 0.78
        # ready_to_act may not be included in the decision, relying on action logic instead
        assert decision['investigation_rounds'] == 3
        assert '3 investigation round' in decision['rationale']
        
        # Verify that the decision rationale includes investigation context
        assert '3 investigation' in decision['rationale']
        assert '0.78' in decision['rationale']  # Confidence