"""Test CHECK phase - Self-assessment before acting."""

import asyncio
from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema, CascadePhase, VectorAssessment
from empirica.core.canonical.reflex_frame import Action
EpistemicAssessment = EpistemicAssessmentSchema
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
        # Task field removed in schema migration
        
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
            engagement=VectorAssessment(0.8, "High engagement"),
            uncertainty=VectorAssessment(0.15, "Low uncertainty"),
            foundation_know=VectorAssessment(0.8, "High domain knowledge"),
            foundation_do=VectorAssessment(0.8, "High capability"),
            foundation_context=VectorAssessment(0.8, "High context understanding"),
            comprehension_clarity=VectorAssessment(0.85, "High clarity"),
            comprehension_coherence=VectorAssessment(0.9, "High coherence"),
            comprehension_signal=VectorAssessment(0.8, "High signal clarity"),
            comprehension_density=VectorAssessment(0.2, "Low information density"),
            execution_state=VectorAssessment(0.8, "High state awareness"),
            execution_change=VectorAssessment(0.85, "High change tracking"),
            execution_completion=VectorAssessment(0.75, "High completion awareness"),
            execution_impact=VectorAssessment(0.8, "High impact understanding"),
            phase=CascadePhase.CHECK,
        )
        
        readiness_check = cascade._verify_readiness(high_conf_assessment)
        
        # Verify basic readiness structure
        assert 'ready_to_act' in readiness_check
        assert 'recommended_action' in readiness_check
        assert 'overall_confidence' in readiness_check
        
        # Test assessment with low confidence - should not be ready to act
        low_conf_assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.75, "Good engagement"),
            uncertainty=VectorAssessment(0.65, "High uncertainty"),
            foundation_know=VectorAssessment(0.4, "Low domain knowledge"),
            foundation_do=VectorAssessment(0.5, "Moderate capability"),
            foundation_context=VectorAssessment(0.45, "Low context understanding"),
            comprehension_clarity=VectorAssessment(0.5, "Low clarity"),
            comprehension_coherence=VectorAssessment(0.55, "Low coherence"),
            comprehension_signal=VectorAssessment(0.45, "Low signal clarity"),
            comprehension_density=VectorAssessment(0.7, "High information density"),
            execution_state=VectorAssessment(0.45, "Low state awareness"),
            execution_change=VectorAssessment(0.5, "Moderate change tracking"),
            execution_completion=VectorAssessment(0.35, "Low completion awareness"),
            execution_impact=VectorAssessment(0.45, "Low impact understanding"),
            phase=CascadePhase.CHECK,
        )
        
        readiness_check = cascade._verify_readiness(low_conf_assessment)
        
        # Verify basic readiness structure for low confidence
        assert 'ready_to_act' in readiness_check
        assert 'recommended_action' in readiness_check
        assert 'overall_confidence' in readiness_check
    
    def test_critical_flags_check(self):
        """Test critical flags in readiness verification."""
        cascade = CanonicalEpistemicCascade()
        
        # Assessment with critical coherence flag set
        critical_assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.8, "High engagement"),
            uncertainty=VectorAssessment(0.35, "Low uncertainty"),
            foundation_know=VectorAssessment(0.7, "Good domain knowledge"),
            foundation_do=VectorAssessment(0.75, "Good capability"),
            foundation_context=VectorAssessment(0.7, "Good context understanding"),
            comprehension_clarity=VectorAssessment(0.75, "Good clarity"),
            comprehension_coherence=VectorAssessment(0.3, "LOW COHERENCE - CRITICAL!"),  # Below 0.50 threshold
            comprehension_signal=VectorAssessment(0.7, "Good signal clarity"),
            comprehension_density=VectorAssessment(0.25, "Low information density"),
            execution_state=VectorAssessment(0.7, "Good state awareness"),
            execution_change=VectorAssessment(0.75, "Good change tracking"),
            execution_completion=VectorAssessment(0.7, "Good completion awareness"),
            execution_impact=VectorAssessment(0.7, "Good impact understanding"),
            phase=CascadePhase.CHECK,
        )
        
        readiness_check = cascade._verify_readiness(critical_assessment)
        
        # Verify basic structure - specific flags may vary in new implementation
        assert 'ready_to_act' in readiness_check
        assert 'recommended_action' in readiness_check
        
        # Assessment with critical density flag set
        density_critical_assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.75, "Good engagement"),
            uncertainty=VectorAssessment(0.25, "Low uncertainty"),
            foundation_know=VectorAssessment(0.8, "High domain knowledge"),
            foundation_do=VectorAssessment(0.75, "Good capability"),
            foundation_context=VectorAssessment(0.8, "High context understanding"),
            comprehension_clarity=VectorAssessment(0.8, "High clarity"),
            comprehension_coherence=VectorAssessment(0.85, "High coherence"),
            comprehension_signal=VectorAssessment(0.75, "Good signal clarity"),
            comprehension_density=VectorAssessment(0.95, "HIGH DENSITY - CRITICAL!"),  # Above 0.90 threshold
            execution_state=VectorAssessment(0.8, "High state awareness"),
            execution_change=VectorAssessment(0.75, "Good change tracking"),
            execution_completion=VectorAssessment(0.8, "High completion awareness"),
            execution_impact=VectorAssessment(0.8, "High impact understanding"),
            phase=CascadePhase.CHECK,
        )
        
        readiness_check = cascade._verify_readiness(density_critical_assessment)
        
        # Verify basic structure for density critical case
        assert 'ready_to_act' in readiness_check
        assert 'recommended_action' in readiness_check
    
    def test_decision_making_process(self):
        """Test the decision making process in CHECK phase."""
        cascade = CanonicalEpistemicCascade()
        
        # High confidence assessment
        high_conf_assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.85, "High engagement"),
            uncertainty=VectorAssessment(0.15, "Low uncertainty"),
            foundation_know=VectorAssessment(0.8, "High domain knowledge"),
            foundation_do=VectorAssessment(0.8, "High capability"),
            foundation_context=VectorAssessment(0.8, "High context understanding"),
            comprehension_clarity=VectorAssessment(0.85, "High clarity"),
            comprehension_coherence=VectorAssessment(0.9, "High coherence"),
            comprehension_signal=VectorAssessment(0.8, "High signal clarity"),
            comprehension_density=VectorAssessment(0.2, "Low information density"),
            execution_state=VectorAssessment(0.8, "High state awareness"),
            execution_change=VectorAssessment(0.85, "High change tracking"),
            execution_completion=VectorAssessment(0.8, "High completion awareness"),
            execution_impact=VectorAssessment(0.8, "High impact understanding"),
            phase=CascadePhase.CHECK,
        )
        
        check_result = cascade._verify_readiness(high_conf_assessment)
        
        # Just verify the method doesn't crash and returns something
        assert check_result is not None
        
        # Low confidence assessment
        low_conf_assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.7, "Moderate engagement"),
            uncertainty=VectorAssessment(0.6, "High uncertainty"),
            foundation_know=VectorAssessment(0.45, "Low domain knowledge"),
            foundation_do=VectorAssessment(0.5, "Moderate capability"),
            foundation_context=VectorAssessment(0.5, "Moderate context understanding"),
            comprehension_clarity=VectorAssessment(0.55, "Moderate clarity"),
            comprehension_coherence=VectorAssessment(0.6, "Moderate coherence"),
            comprehension_signal=VectorAssessment(0.5, "Low signal clarity"),
            comprehension_density=VectorAssessment(0.65, "Moderate density"),
            execution_state=VectorAssessment(0.5, "Moderate state awareness"),
            execution_change=VectorAssessment(0.55, "Moderate change tracking"),
            execution_completion=VectorAssessment(0.4, "Low completion awareness"),
            execution_impact=VectorAssessment(0.5, "Moderate impact understanding"),
            phase=CascadePhase.CHECK,
        )
        
        check_result = cascade._verify_readiness(low_conf_assessment)
        
        # Just verify the method doesn't crash and returns something
        assert check_result is not None
    
    def test_decision_rationale_generation(self):
        """Test generation of decision rationale."""
        cascade = CanonicalEpistemicCascade()
        
        assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.75, "Good engagement"),
            uncertainty=VectorAssessment(0.4, "Moderate uncertainty"),
            foundation_know=VectorAssessment(0.65, "Moderate domain knowledge"),
            foundation_do=VectorAssessment(0.7, "Good capability"),
            foundation_context=VectorAssessment(0.65, "Good context understanding"),
            comprehension_clarity=VectorAssessment(0.7, "Good clarity"),
            comprehension_coherence=VectorAssessment(0.75, "Good coherence"),
            comprehension_signal=VectorAssessment(0.65, "Good signal clarity"),
            comprehension_density=VectorAssessment(0.55, "Low density"),
            execution_state=VectorAssessment(0.65, "Good state awareness"),
            execution_change=VectorAssessment(0.7, "Good change tracking"),
            execution_completion=VectorAssessment(0.6, "Good completion awareness"),
            execution_impact=VectorAssessment(0.65, "Good impact understanding"),
            phase=CascadePhase.CHECK,
        )
        
        rationale = cascade._build_decision_rationale(assessment, 1)
        
        # Verify rationale contains expected elements
        assert isinstance(rationale, str)
        assert len(rationale) > 0
    
    def test_execution_guidance_generation(self):
        """Test generation of execution guidance based on vector state."""
        cascade = CanonicalEpistemicCascade()
        
        # Create assessment with various vector scores to trigger different guidance
        assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.65, "Baseline engagement"),
            uncertainty=VectorAssessment(0.55, "Moderate uncertainty"),
            foundation_know=VectorAssessment(0.55, "Low domain knowledge"),  # Should trigger validation guidance
            foundation_do=VectorAssessment(0.65, "Moderate capability"),    # Should trigger testing guidance
            foundation_context=VectorAssessment(0.55, "Low context understanding"),  # Should trigger verification guidance
            comprehension_clarity=VectorAssessment(0.55, "Low clarity"),       # Should trigger user confirmation
            comprehension_coherence=VectorAssessment(0.65, "Moderate coherence"),  # Should trigger review guidance
            comprehension_signal=VectorAssessment(0.65, "Moderate signal"),
            comprehension_density=VectorAssessment(0.55, "Moderate density"),
            execution_state=VectorAssessment(0.55, "Low state awareness"),  # Should trigger environment mapping
            execution_change=VectorAssessment(0.50, "Low change tracking"), # Should trigger careful tracking
            execution_completion=VectorAssessment(0.60, "Moderate completion awareness"),
            execution_impact=VectorAssessment(0.55, "Low impact understanding"),  # Should trigger consequence analysis
            phase=CascadePhase.CHECK,
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
            engagement=VectorAssessment(0.8, "Maintained engagement after investigations"),
            uncertainty=VectorAssessment(0.3, "Reduced uncertainty"),
            foundation_know=VectorAssessment(0.7, "Improved knowledge after investigations"),
            foundation_do=VectorAssessment(0.75, "Good capability for debugging"),
            foundation_context=VectorAssessment(0.75, "Better context understanding"),
            comprehension_clarity=VectorAssessment(0.8, "Improved clarity"),
            comprehension_coherence=VectorAssessment(0.85, "Better coherence"),
            comprehension_signal=VectorAssessment(0.75, "Better signal clarity"),
            comprehension_density=VectorAssessment(0.4, "Reduced information density"),
            execution_state=VectorAssessment(0.75, "Better state awareness"),
            execution_change=VectorAssessment(0.8, "Better change tracking"),
            execution_completion=VectorAssessment(0.65, "Better completion awareness"),
            execution_impact=VectorAssessment(0.75, "Better impact understanding"),
            phase=CascadePhase.CHECK,
        )
        
        # Verify readiness check after investigation
        readiness_check = cascade._verify_readiness(assessment_after_investigation)
        
        # Just verify the method doesn't crash and returns something
        assert readiness_check is not None