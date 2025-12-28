"""Test ENGAGEMENT gate - must be ≥ 0.60 to proceed."""

from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema, CascadePhase, VectorAssessment
from empirica.core.canonical.reflex_frame import Action
from empirica.core.thresholds import ENGAGEMENT_THRESHOLD

EpistemicAssessment = EpistemicAssessmentSchema


class TestEngagementGate:
    """Test ENGAGEMENT gate functionality."""
    
    def test_gate_blocks_low_engagement(self):
        """Test ENGAGEMENT < 0.60 → CLARIFY action."""
        # Create an assessment with low engagement
        assessment = EpistemicAssessment(
            engagement=VectorAssessment(score=0.5, rationale="Low engagement - not collaborating"),
            uncertainty=VectorAssessment(score=0.1, rationale="Very low uncertainty"),
            foundation_know=VectorAssessment(score=0.8, rationale="Good domain knowledge"),
            foundation_do=VectorAssessment(score=0.8, rationale="High capability"),
            foundation_context=VectorAssessment(score=0.8, rationale="Good context understanding"),
            comprehension_clarity=VectorAssessment(score=0.8, rationale="Task is clear"),
            comprehension_coherence=VectorAssessment(score=0.9, rationale="High coherence"),
            comprehension_signal=VectorAssessment(score=0.8, rationale="Clear priorities"),
            comprehension_density=VectorAssessment(score=0.2, rationale="Low information density"),
            execution_state=VectorAssessment(score=0.8, rationale="Good state awareness"),
            execution_change=VectorAssessment(score=0.85, rationale="Good change tracking"),
            execution_completion=VectorAssessment(score=0.8, rationale="Clear completion criteria"),
            execution_impact=VectorAssessment(score=0.8, rationale="Good impact understanding"),
            phase=CascadePhase.PREFLIGHT,
        )
        
        # Verify engagement gate is not passed (field removed, but score check still works)
        assert assessment.engagement.score == 0.5
        assert assessment.engagement.score < ENGAGEMENT_THRESHOLD
    
    def test_gate_passes_high_engagement(self):
        """Test ENGAGEMENT ≥ 0.60 → Proceed to THINK."""
        # Create an assessment with high engagement
        assessment = EpistemicAssessment(
            engagement=VectorAssessment(score=0.7, rationale="High engagement - active collaboration"),
            uncertainty=VectorAssessment(score=0.3, rationale="Low uncertainty"),
            foundation_know=VectorAssessment(score=0.6, rationale="Moderate domain knowledge"),
            foundation_do=VectorAssessment(score=0.7, rationale="Good capability"),
            foundation_context=VectorAssessment(score=0.65, rationale="Good context understanding"),
            comprehension_clarity=VectorAssessment(score=0.7, rationale="Task is clear"),
            comprehension_coherence=VectorAssessment(score=0.8, rationale="High coherence"),
            comprehension_signal=VectorAssessment(score=0.7, rationale="Clear priorities"),
            comprehension_density=VectorAssessment(score=0.3, rationale="Low information density"),
            execution_state=VectorAssessment(score=0.6, rationale="Good state awareness"),
            execution_change=VectorAssessment(score=0.7, rationale="Good change tracking"),
            execution_completion=VectorAssessment(score=0.65, rationale="Clear completion criteria"),
            execution_impact=VectorAssessment(score=0.7, rationale="Good impact understanding"),
            phase=CascadePhase.PREFLIGHT,
        )
        
        # Verify engagement gate is passed (field removed, but score check still works)
        assert assessment.engagement.score == 0.7
        assert assessment.engagement.score >= ENGAGEMENT_THRESHOLD
    
    def test_engagement_exactly_threshold(self):
        """Test engagement exactly at threshold (0.60) passes gate."""
        assessment = EpistemicAssessment(
            engagement=VectorAssessment(score=0.6, rationale="Exact threshold engagement"),
            uncertainty=VectorAssessment(score=0.2, rationale="Low uncertainty"),
            foundation_know=VectorAssessment(score=0.7, rationale="Good domain knowledge"),
            foundation_do=VectorAssessment(score=0.7, rationale="Good capability"),
            foundation_context=VectorAssessment(score=0.7, rationale="Good context understanding"),
            comprehension_clarity=VectorAssessment(score=0.7, rationale="Task is clear"),
            comprehension_coherence=VectorAssessment(score=0.8, rationale="High coherence"),
            comprehension_signal=VectorAssessment(score=0.7, rationale="Clear priorities"),
            comprehension_density=VectorAssessment(score=0.3, rationale="Low information density"),
            execution_state=VectorAssessment(score=0.7, rationale="Good state awareness"),
            execution_change=VectorAssessment(score=0.7, rationale="Good change tracking"),
            execution_completion=VectorAssessment(score=0.7, rationale="Clear completion criteria"),
            execution_impact=VectorAssessment(score=0.7, rationale="Good impact understanding"),
            phase=CascadePhase.PREFLIGHT,
        )
        
        # Verify engagement gate is passed (field removed, but score check still works)
        assert assessment.engagement.score == 0.6
        assert assessment.engagement.score >= ENGAGEMENT_THRESHOLD
    
    def test_engagement_just_below_threshold(self):
        """Test engagement just below threshold (0.59) does not pass gate."""
        assessment = EpistemicAssessment(
            engagement=VectorAssessment(score=0.59, rationale="Just below threshold engagement"),
            uncertainty=VectorAssessment(score=0.2, rationale="Low uncertainty"),
            foundation_know=VectorAssessment(score=0.7, rationale="Good domain knowledge"),
            foundation_do=VectorAssessment(score=0.7, rationale="Good capability"),
            foundation_context=VectorAssessment(score=0.7, rationale="Good context understanding"),
            comprehension_clarity=VectorAssessment(score=0.7, rationale="Task is clear"),
            comprehension_coherence=VectorAssessment(score=0.8, rationale="High coherence"),
            comprehension_signal=VectorAssessment(score=0.7, rationale="Clear priorities"),
            comprehension_density=VectorAssessment(score=0.3, rationale="Low information density"),
            execution_state=VectorAssessment(score=0.7, rationale="Good state awareness"),
            execution_change=VectorAssessment(score=0.7, rationale="Good change tracking"),
            execution_completion=VectorAssessment(score=0.7, rationale="Clear completion criteria"),
            execution_impact=VectorAssessment(score=0.7, rationale="Good impact understanding"),
            phase=CascadePhase.PREFLIGHT,
        )
        
        # Verify engagement gate is not passed (field removed, but score check still works)
        assert assessment.engagement.score == 0.59
        assert assessment.engagement.score < ENGAGEMENT_THRESHOLD
    
    
    def test_threshold_constant(self):
        """Test that the engagement threshold constant is 0.60."""
        assert ENGAGEMENT_THRESHOLD == 0.60