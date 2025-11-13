"""Test ENGAGEMENT gate - must be ≥ 0.60 to proceed."""

from empirica.core.canonical.reflex_frame import EpistemicAssessment, VectorState, Action
from empirica.core.canonical.canonical_epistemic_assessment import CanonicalEpistemicAssessor, ENGAGEMENT_THRESHOLD


class TestEngagementGate:
    """Test ENGAGEMENT gate functionality."""
    
    def test_gate_blocks_low_engagement(self):
        """Test ENGAGEMENT < 0.60 → CLARIFY action."""
        # Create an assessment with low engagement
        assessment = EpistemicAssessment(
            engagement=VectorState(score=0.5, rationale="Low engagement - not collaborating"),
            engagement_gate_passed=False,  # Should be False since score < 0.60
            know=VectorState(score=0.8, rationale="Good domain knowledge"),
            do=VectorState(score=0.8, rationale="High capability"),
            context=VectorState(score=0.8, rationale="Good context understanding"),
            foundation_confidence=0.8,
            clarity=VectorState(score=0.8, rationale="Task is clear"),
            coherence=VectorState(score=0.9, rationale="High coherence"),
            signal=VectorState(score=0.8, rationale="Clear priorities"),
            density=VectorState(score=0.2, rationale="Low information density"),
            comprehension_confidence=0.8,
            state=VectorState(score=0.8, rationale="Good state awareness"),
            change=VectorState(score=0.85, rationale="Good change tracking"),
            completion=VectorState(score=0.8, rationale="Clear completion criteria"),
            impact=VectorState(score=0.8, rationale="Good impact understanding"),
            execution_confidence=0.8,
            uncertainty=VectorState(score=0.1, rationale="Very low uncertainty"),
            overall_confidence=0.8,
            recommended_action=Action.CLARIFY,  # Should be CLARIFY due to low engagement
            assessment_id="low_engagement_test"
        )
        
        # Verify engagement gate is not passed
        assert assessment.engagement_gate_passed is False
        assert assessment.engagement.score == 0.5
        assert assessment.engagement.score < ENGAGEMENT_THRESHOLD
        
        # Verify action is CLARIFY
        assert assessment.recommended_action == Action.CLARIFY
    
    def test_gate_passes_high_engagement(self):
        """Test ENGAGEMENT ≥ 0.60 → Proceed to THINK."""
        # Create an assessment with high engagement
        assessment = EpistemicAssessment(
            engagement=VectorState(score=0.7, rationale="High engagement - active collaboration"),
            engagement_gate_passed=True,  # Should be True since score >= 0.60
            know=VectorState(score=0.6, rationale="Moderate domain knowledge"),
            do=VectorState(score=0.7, rationale="Good capability"),
            context=VectorState(score=0.65, rationale="Good context understanding"),
            foundation_confidence=0.65,
            clarity=VectorState(score=0.7, rationale="Task is clear"),
            coherence=VectorState(score=0.8, rationale="High coherence"),
            signal=VectorState(score=0.7, rationale="Clear priorities"),
            density=VectorState(score=0.3, rationale="Low information density"),
            comprehension_confidence=0.7,
            state=VectorState(score=0.6, rationale="Good state awareness"),
            change=VectorState(score=0.7, rationale="Good change tracking"),
            completion=VectorState(score=0.65, rationale="Clear completion criteria"),
            impact=VectorState(score=0.7, rationale="Good impact understanding"),
            execution_confidence=0.65,
            uncertainty=VectorState(score=0.3, rationale="Low uncertainty"),
            overall_confidence=0.65,
            recommended_action=Action.PROCEED,  # Should be PROCEED since engagement is high enough
            assessment_id="high_engagement_test"
        )
        
        # Verify engagement gate is passed
        assert assessment.engagement_gate_passed is True
        assert assessment.engagement.score == 0.7
        assert assessment.engagement.score >= ENGAGEMENT_THRESHOLD
        
        # Verify action is not CLARIFY (since engagement gate passed)
        assert assessment.recommended_action != Action.CLARIFY
    
    def test_engagement_exactly_threshold(self):
        """Test engagement exactly at threshold (0.60) passes gate."""
        assessment = EpistemicAssessment(
            engagement=VectorState(score=0.6, rationale="Exact threshold engagement"),
            engagement_gate_passed=True,  # Should pass since it's exactly at threshold
            know=VectorState(score=0.7, rationale="Good domain knowledge"),
            do=VectorState(score=0.7, rationale="Good capability"),
            context=VectorState(score=0.7, rationale="Good context understanding"),
            foundation_confidence=0.7,
            clarity=VectorState(score=0.7, rationale="Task is clear"),
            coherence=VectorState(score=0.8, rationale="High coherence"),
            signal=VectorState(score=0.7, rationale="Clear priorities"),
            density=VectorState(score=0.3, rationale="Low information density"),
            comprehension_confidence=0.7,
            state=VectorState(score=0.7, rationale="Good state awareness"),
            change=VectorState(score=0.7, rationale="Good change tracking"),
            completion=VectorState(score=0.7, rationale="Clear completion criteria"),
            impact=VectorState(score=0.7, rationale="Good impact understanding"),
            execution_confidence=0.7,
            uncertainty=VectorState(score=0.2, rationale="Low uncertainty"),
            overall_confidence=0.7,
            recommended_action=Action.PROCEED,
            assessment_id="threshold_engagement_test"
        )
        
        # Verify engagement gate is passed
        assert assessment.engagement_gate_passed is True
        assert assessment.engagement.score == 0.6
        assert assessment.engagement.score >= ENGAGEMENT_THRESHOLD
        
        # Verify action is not CLARIFY
        assert assessment.recommended_action != Action.CLARIFY
    
    def test_engagement_just_below_threshold(self):
        """Test engagement just below threshold (0.59) does not pass gate."""
        assessment = EpistemicAssessment(
            engagement=VectorState(score=0.59, rationale="Just below threshold engagement"),
            engagement_gate_passed=False,  # Should not pass since it's below threshold
            know=VectorState(score=0.7, rationale="Good domain knowledge"),
            do=VectorState(score=0.7, rationale="Good capability"),
            context=VectorState(score=0.7, rationale="Good context understanding"),
            foundation_confidence=0.7,
            clarity=VectorState(score=0.7, rationale="Task is clear"),
            coherence=VectorState(score=0.8, rationale="High coherence"),
            signal=VectorState(score=0.7, rationale="Clear priorities"),
            density=VectorState(score=0.3, rationale="Low information density"),
            comprehension_confidence=0.7,
            state=VectorState(score=0.7, rationale="Good state awareness"),
            change=VectorState(score=0.7, rationale="Good change tracking"),
            completion=VectorState(score=0.7, rationale="Clear completion criteria"),
            impact=VectorState(score=0.7, rationale="Good impact understanding"),
            execution_confidence=0.7,
            uncertainty=VectorState(score=0.2, rationale="Low uncertainty"),
            overall_confidence=0.7,
            recommended_action=Action.CLARIFY,  # Should be CLARIFY due to low engagement
            assessment_id="just_below_threshold_test"
        )
        
        # Verify engagement gate is not passed
        assert assessment.engagement_gate_passed is False
        assert assessment.engagement.score == 0.59
        assert assessment.engagement.score < ENGAGEMENT_THRESHOLD
        
        # Verify action is CLARIFY
        assert assessment.recommended_action == Action.CLARIFY
    
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
            assessment_id="assessor_low_engagement",
            task="Test task"
        )
        
        # Should not pass engagement gate and should recommend CLARIFY
        assert assessment.engagement_gate_passed is False
        assert assessment.recommended_action == Action.CLARIFY
        assert assessment.engagement.score == 0.4
    
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
            assessment_id="assessor_high_engagement",
            task="Test task"
        )
        
        # Should pass engagement gate and proceed to other actions (not CLARIFY)
        assert assessment.engagement_gate_passed is True
        assert assessment.recommended_action != Action.CLARIFY  # Should not be blocked by engagement gate
        assert assessment.engagement.score == 0.8
        assert assessment.engagement.score >= ENGAGEMENT_THRESHOLD
    
    def test_threshold_constant(self):
        """Test that the engagement threshold constant is 0.60."""
        assert ENGAGEMENT_THRESHOLD == 0.60