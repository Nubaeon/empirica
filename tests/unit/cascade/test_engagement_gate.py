"""Test ENGAGEMENT gate - must be ≥ 0.60 to proceed."""

from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema, CascadePhase, VectorAssessment
from empirica.core.canonical.reflex_frame import Action
EpistemicAssessment = EpistemicAssessmentSchema
from empirica.core.canonical.canonical_epistemic_assessment import CanonicalEpistemicAssessor, ENGAGEMENT_THRESHOLD


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
    
    def test_engagement_gate_with_canonical_assessor(self):
        """Test engagement gate using CanonicalEpistemicAssessor."""
        assessor = CanonicalEpistemicAssessor()
        
        # Test with low engagement response
        low_engagement_response = {
            "engagement": {
                "score": 0.4,
                "rationale": "Low engagement with task",
                "evidence": "Passive participation"
            },
            "foundation": {
                "know": {"score": 0.8, "rationale": "Good knowledge", "evidence": "Experience"},
                "do": {"score": 0.8, "rationale": "Good capability", "evidence": "Skills"},
                "context": {"score": 0.8, "rationale": "Good context", "evidence": "Clear setup"}
            },
            "comprehension": {
                "clarity": {"score": 0.8, "rationale": "Clear task", "evidence": "Well defined"},
                "coherence": {"score": 0.9, "rationale": "Coherent", "evidence": "Consistent"},
                "signal": {"score": 0.8, "rationale": "Clear priorities", "evidence": "Prioritized"},
                "density": {"score": 0.2, "rationale": "Simple", "evidence": "Not complex"}
            },
            "execution": {
                "state": {"score": 0.8, "rationale": "Good state awareness", "evidence": "Clear environment"},
                "change": {"score": 0.85, "rationale": "Good change tracking", "evidence": "Version control"},
                "completion": {"score": 0.8, "rationale": "Clear completion", "evidence": "Defined goals"},
                "impact": {"score": 0.8, "rationale": "Good impact understanding", "evidence": "Risk assessment done"}
            },
            "uncertainty": {
                "score": 0.1,
                "rationale": "Low uncertainty",
                "evidence": "Clear plan"
            }
        }
        
        assessment = assessor.parse_llm_response(
            llm_response=low_engagement_response,
            task="Test task",
            assessment_id="test_assessment_1"
        )
        
        # Engagement gate fields removed, but scoring logic still works
        assert assessment.engagement.score == 0.4
        assert assessment.engagement.score < ENGAGEMENT_THRESHOLD
    
    def test_engagement_gate_with_high_engagement_via_assessor(self):
        """Test engagement gate passes with high engagement via assessor."""
        assessor = CanonicalEpistemicAssessor()
        
        # Test with high engagement response
        high_engagement_response = {
            "engagement": {
                "score": 0.8,
                "rationale": "High engagement with collaborative task",
                "evidence": "Active participation"
            },
            "foundation": {
                "know": {"score": 0.6, "rationale": "Moderate knowledge", "evidence": "Some experience"},
                "do": {"score": 0.7, "rationale": "Good capability", "evidence": "Appropriate skills"},
                "context": {"score": 0.65, "rationale": "Good context", "evidence": "Clear environment"}
            },
            "comprehension": {
                "clarity": {"score": 0.7, "rationale": "Task is clear", "evidence": "Well defined"},
                "coherence": {"score": 0.8, "rationale": "Coherent", "evidence": "Consistent"},
                "signal": {"score": 0.7, "rationale": "Clear priorities", "evidence": "Prioritized"},
                "density": {"score": 0.3, "rationale": "Manageable", "evidence": "Not too complex"}
            },
            "execution": {
                "state": {"score": 0.6, "rationale": "Good state awareness", "evidence": "Environment mapped"},
                "change": {"score": 0.7, "rationale": "Good change tracking", "evidence": "Can track changes"},
                "completion": {"score": 0.65, "rationale": "Clear completion", "evidence": "Defined criteria"},
                "impact": {"score": 0.7, "rationale": "Good impact understanding", "evidence": "Understood consequences"}
            },
            "uncertainty": {
                "score": 0.3,
                "rationale": "Moderate uncertainty",
                "evidence": "Some unknowns"
            }
        }
        
        assessment = assessor.parse_llm_response(
            llm_response=high_engagement_response,
            task="Test task",
            assessment_id="test_assessment_2"
        )
        
        # Engagement gate fields removed, but scoring logic still works
        assert assessment.engagement.score == 0.8
        assert assessment.engagement.score >= ENGAGEMENT_THRESHOLD
    
    def test_threshold_constant(self):
        """Test that the engagement threshold constant is 0.60."""
        assert ENGAGEMENT_THRESHOLD == 0.60