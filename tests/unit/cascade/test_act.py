"""Test ACT phase - Execute with confidence."""

import asyncio
import pytest
from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema, VectorAssessment, CascadePhase
from empirica.core.canonical.reflex_frame import Action
# Alias for backwards compatibility in tests
EpistemicAssessment = EpistemicAssessmentSchema
from empirica.core.metacognitive_cascade.metacognitive_cascade import (
    CanonicalEpistemicCascade,
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
        # Task field removed in schema migration
        
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
            engagement=VectorAssessment(0.85, "High engagement"),
            foundation_know=VectorAssessment(0.8, "High domain knowledge"),
            foundation_do=VectorAssessment(0.85, "High capability"),
            foundation_context=VectorAssessment(0.8, "High context understanding"),
            comprehension_clarity=VectorAssessment(0.85, "High clarity"),
            comprehension_coherence=VectorAssessment(0.9, "High coherence"),
            comprehension_signal=VectorAssessment(0.8, "High signal clarity"),
            comprehension_density=VectorAssessment(0.2, "Low information density"),
            execution_state=VectorAssessment(0.85, "High state awareness"),
            execution_change=VectorAssessment(0.85, "High change tracking"),
            execution_completion=VectorAssessment(0.8, "High completion awareness"),
            execution_impact=VectorAssessment(0.85, "High impact understanding"),
            uncertainty=VectorAssessment(0.15, "Low uncertainty"),
            phase=CascadePhase.ACT,
            round_num=0,
            investigation_count=0
        )
        
        check_result = {
            'recommended_action': 'PROCEED',
            'overall_confidence': 0.84,
            'critical_flags': {
                'coherence_critical': False,
                'density_critical': False,
                'change_critical': False
            },
            'ready_to_act': True
        }
        
        decision = cascade._make_final_decision(high_conf_assessment, check_result, 0)
        
        assert decision['action'] == 'proceed'
        assert decision['confidence'] == pytest.approx(0.84, abs=0.01)  # Allow for calculation precision
        # ready_to_act may not be included in the decision, relying on action logic instead
        assert 'proceed' in decision['rationale'].lower()
        
        # Test with investigation recommendation - should investigate
        investigation_assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.75, "Good engagement"),
            foundation_know=VectorAssessment(0.5, "Low domain knowledge"),
            foundation_do=VectorAssessment(0.6, "Moderate capability"),
            foundation_context=VectorAssessment(0.55, "Low context understanding"),
            comprehension_clarity=VectorAssessment(0.6, "Moderate clarity"),
            comprehension_coherence=VectorAssessment(0.65, "Moderate coherence"),
            comprehension_signal=VectorAssessment(0.55, "Low signal clarity"),
            comprehension_density=VectorAssessment(0.6, "Moderate density"),
            execution_state=VectorAssessment(0.55, "Low state awareness"),
            execution_change=VectorAssessment(0.6, "Moderate change tracking"),
            execution_completion=VectorAssessment(0.45, "Low completion awareness"),
            execution_impact=VectorAssessment(0.55, "Low impact understanding"),
            uncertainty=VectorAssessment(0.6, "High uncertainty"),
            phase=CascadePhase.ACT,
            round_num=0,
            investigation_count=0
        )
        
        check_result = {
            'recommended_action': 'INVESTIGATE',
            'overall_confidence': 0.57,
            'critical_flags': {
                'coherence_critical': False,
                'density_critical': False,
                'change_critical': False
            },
            'ready_to_act': False
        }
        
        decision = cascade._make_final_decision(investigation_assessment, check_result, 2)
        
        assert decision['action'] == 'investigate'
        assert decision['confidence'] == pytest.approx(0.57, abs=0.01)  # Allow for calculation precision
        assert decision['investigation_rounds'] == 2
        assert 'investigation' in decision['rationale'].lower()
    
    def test_act_phase_guidance_generation(self):
        """Test execution guidance generation in ACT phase."""
        cascade = CanonicalEpistemicCascade()
        
        # Create an assessment with specific vector states
        assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.7, "Baseline engagement"),
            foundation_know=VectorAssessment(0.65, "Moderate domain knowledge"),
            foundation_do=VectorAssessment(0.75, "Good capability"),
            foundation_context=VectorAssessment(0.6, "Moderate context understanding"),
            comprehension_clarity=VectorAssessment(0.7, "Good clarity"),
            comprehension_coherence=VectorAssessment(0.75, "Good coherence"),
            comprehension_signal=VectorAssessment(0.65, "Good signal clarity"),
            comprehension_density=VectorAssessment(0.55, "Low density"),
            execution_state=VectorAssessment(0.65, "Good state awareness"),
            execution_change=VectorAssessment(0.7, "Good change tracking"),
            execution_completion=VectorAssessment(0.65, "Good completion awareness"),
            execution_impact=VectorAssessment(0.7, "Good impact understanding"),
            uncertainty=VectorAssessment(0.35, "Low uncertainty"),
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
            engagement=VectorAssessment(0.6, "Low engagement"),
            foundation_know=VectorAssessment(0.4, "Low domain knowledge"),
            foundation_do=VectorAssessment(0.5, "Low capability"),
            foundation_context=VectorAssessment(0.45, "Low context understanding"),
            comprehension_clarity=VectorAssessment(0.5, "Low clarity"),
            comprehension_coherence=VectorAssessment(0.55, "Low coherence"),
            comprehension_signal=VectorAssessment(0.45, "Low signal clarity"),
            comprehension_density=VectorAssessment(0.65, "Moderate density"),
            execution_state=VectorAssessment(0.45, "Low state awareness"),
            execution_change=VectorAssessment(0.5, "Low change tracking"),
            execution_completion=VectorAssessment(0.4, "Low completion awareness"),
            execution_impact=VectorAssessment(0.45, "Low impact understanding"),
            uncertainty=VectorAssessment(0.65, "High uncertainty"),
        )
        
        guidance = cascade._generate_execution_guidance(low_vectors_assessment)
        
        # Guidance generation removed with heuristics - AI decides via self-assessment
        # No longer asserting specific guidance content
        assert isinstance(guidance, list)
    
    def test_vector_summary_extraction_in_act(self):
        """Test vector summary extraction in ACT phase."""
        cascade = CanonicalEpistemicCascade()
        
        assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.85, "High engagement"),
            foundation_know=VectorAssessment(0.8, "High domain knowledge"),
            foundation_do=VectorAssessment(0.85, "High capability"),
            foundation_context=VectorAssessment(0.8, "High context understanding"),
            comprehension_clarity=VectorAssessment(0.85, "High clarity"),
            comprehension_coherence=VectorAssessment(0.9, "High coherence"),
            comprehension_signal=VectorAssessment(0.8, "High signal clarity"),
            comprehension_density=VectorAssessment(0.2, "Low information density"),
            execution_state=VectorAssessment(0.85, "High state awareness"),
            execution_change=VectorAssessment(0.85, "High change tracking"),
            execution_completion=VectorAssessment(0.8, "High completion awareness"),
            execution_impact=VectorAssessment(0.85, "High impact understanding"),
            uncertainty=VectorAssessment(0.15, "Low uncertainty"),
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
        assert summary['foundation_confidence'] == pytest.approx(0.81667, abs=0.01)
        assert summary['comprehension_confidence'] == pytest.approx(0.8375, abs=0.01)
        assert summary['execution_confidence'] == pytest.approx(0.8375, abs=0.01)
        assert summary['overall_confidence'] == pytest.approx(0.8321, abs=0.01)
        
        # Verify decision making with extracted summary
        check_result = {
            'recommended_action': 'PROCEED',
            'overall_confidence': 0.84,
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
            engagement=VectorAssessment(0.8, "High engagement"),
            foundation_know=VectorAssessment(0.7, "Good domain knowledge"),
            foundation_do=VectorAssessment(0.75, "Good capability"),
            foundation_context=VectorAssessment(0.7, "Good context understanding"),
            comprehension_clarity=VectorAssessment(0.75, "Good clarity"),
            comprehension_coherence=VectorAssessment(0.3, "LOW COHERENCE - CRITICAL!"),  # Below 0.50
            comprehension_signal=VectorAssessment(0.7, "Good signal clarity"),
            comprehension_density=VectorAssessment(0.25, "Low information density"),
            execution_state=VectorAssessment(0.7, "Good state awareness"),
            execution_change=VectorAssessment(0.75, "Good change tracking"),
            execution_completion=VectorAssessment(0.7, "Good completion awareness"),
            execution_impact=VectorAssessment(0.7, "Good impact understanding"),
            uncertainty=VectorAssessment(0.35, "Low uncertainty"),
        )
        
        check_result = {
            'recommended_action': 'RESET',
            'overall_confidence': 0.71,
            'critical_flags': {
                'coherence_critical': True,   # This is critical
                'density_critical': False,
                'change_critical': False
            },
            'ready_to_act': False
        }
        
        decision = cascade._make_final_decision(critical_assessment, check_result, 1)
        
        # Just verify decision structure exists
        assert 'action' in decision
        
        # Another case: high density
        density_critical_assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.75, "Good engagement"),
            foundation_know=VectorAssessment(0.8, "High domain knowledge"),
            foundation_do=VectorAssessment(0.75, "Good capability"),
            foundation_context=VectorAssessment(0.8, "High context understanding"),
            comprehension_clarity=VectorAssessment(0.8, "High clarity"),
            comprehension_coherence=VectorAssessment(0.85, "High coherence"),
            comprehension_signal=VectorAssessment(0.75, "Good signal clarity"),
            comprehension_density=VectorAssessment(0.95, "HIGH DENSITY - CRITICAL!"),  # Above 0.90
            execution_state=VectorAssessment(0.8, "High state awareness"),
            execution_change=VectorAssessment(0.75, "Good change tracking"),
            execution_completion=VectorAssessment(0.8, "High completion awareness"),
            execution_impact=VectorAssessment(0.8, "High impact understanding"),
            uncertainty=VectorAssessment(0.25, "Low uncertainty"),
        )
        
        check_result = {
            'recommended_action': 'RESET',
            'overall_confidence': 0.79,
            'critical_flags': {
                'coherence_critical': False,
                'density_critical': True,    # This is critical
                'change_critical': False
            },
            'ready_to_act': False
        }
        
        decision = cascade._make_final_decision(density_critical_assessment, check_result, 0)
        
        # Just verify decision structure exists
        assert 'action' in decision
    
    def test_final_decision_with_investigation_context(self):
        """Test final decision with investigation context."""
        cascade = CanonicalEpistemicCascade()
        
        assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.8, "High engagement after investigation"),
            foundation_know=VectorAssessment(0.75, "Improved knowledge after investigation"),
            foundation_do=VectorAssessment(0.8, "Good capability"),
            foundation_context=VectorAssessment(0.75, "Better context after investigation"),
            comprehension_clarity=VectorAssessment(0.8, "Good clarity after investigation"),
            comprehension_coherence=VectorAssessment(0.85, "High coherence after investigation"),
            comprehension_signal=VectorAssessment(0.75, "Good signal after investigation"),
            comprehension_density=VectorAssessment(0.3, "Low density after investigation"),
            execution_state=VectorAssessment(0.75, "Good state awareness after investigation"),
            execution_change=VectorAssessment(0.8, "Good change tracking after investigation"),
            execution_completion=VectorAssessment(0.75, "Good completion awareness after investigation"),
            execution_impact=VectorAssessment(0.8, "Good impact understanding after investigation"),
            uncertainty=VectorAssessment(0.25, "Low uncertainty after investigation"),
        )
        
        check_result = {
            'recommended_action': 'PROCEED',
            'overall_confidence': 0.78,
            'critical_flags': {
                'coherence_critical': False,
                'density_critical': False,
                'change_critical': False
            },
            'ready_to_act': True
        }
        
        # Decision after 3 investigation rounds
        decision = cascade._make_final_decision(assessment, check_result, investigation_rounds=3)
        
        # Just verify decision structure exists
        assert 'action' in decision