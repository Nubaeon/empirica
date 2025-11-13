"""Test Reflex Frame data structures and canonical weights."""

import pytest
from datetime import datetime, UTC
from empirica.core.canonical.reflex_frame import (
    VectorState, EpistemicAssessment, ReflexFrame, Action, 
    CANONICAL_WEIGHTS, ENGAGEMENT_THRESHOLD, CRITICAL_THRESHOLDS
)


class TestVectorState:
    """Test VectorState data structure."""
    
    def test_vector_validation(self):
        """Vectors must be 0.0-1.0 range."""
        # Valid range
        valid_vector = VectorState(score=0.5, rationale="Test rationale")
        assert valid_vector.score == 0.5
        
        # Invalid ranges should raise ValueError
        with pytest.raises(ValueError, match="Vector score must be 0.0-1.0"):
            VectorState(score=-0.1, rationale="Test rationale")
        
        with pytest.raises(ValueError, match="Vector score must be 0.0-1.0"):
            VectorState(score=1.1, rationale="Test rationale")
    
    def test_vector_with_evidence(self):
        """Test VectorState with optional evidence."""
        vector = VectorState(score=0.7, rationale="Test rationale", evidence="Supporting evidence")
        assert vector.score == 0.7
        assert vector.rationale == "Test rationale"
        assert vector.evidence == "Supporting evidence"
    
    def test_to_dict(self):
        """Test VectorState to_dict method."""
        vector = VectorState(score=0.6, rationale="Test rationale", evidence="Supporting evidence")
        result = vector.to_dict()
        
        assert result['score'] == 0.6
        assert result['rationale'] == "Test rationale"
        assert result['evidence'] == "Supporting evidence"


class TestEpistemicAssessment:
    """Test Epistemic Assessment structure."""
    
    def test_canonical_weights(self):
        """Test foundation, comprehension, execution, engagement weights."""
        assert CANONICAL_WEIGHTS['foundation'] == 0.35
        assert CANONICAL_WEIGHTS['comprehension'] == 0.25
        assert CANONICAL_WEIGHTS['execution'] == 0.25
        assert CANONICAL_WEIGHTS['engagement'] == 0.15
    
    def test_engagement_gate_threshold(self):
        """Test ENGAGEMENT threshold is 0.60."""
        assert ENGAGEMENT_THRESHOLD == 0.60
    
    def test_critical_thresholds(self):
        """Test critical thresholds."""
        assert CRITICAL_THRESHOLDS['coherence_min'] == 0.50
        assert CRITICAL_THRESHOLDS['density_max'] == 0.90
        assert CRITICAL_THRESHOLDS['change_min'] == 0.50
    
    def test_engagement_gate_initialization(self):
        """Test engagement gate computation."""
        # High engagement should pass
        assessment = EpistemicAssessment(
            engagement=VectorState(score=0.7, rationale="High engagement"),
            engagement_gate_passed=True,
            know=VectorState(score=0.5, rationale="Test"),
            do=VectorState(score=0.5, rationale="Test"),
            context=VectorState(score=0.5, rationale="Test"),
            foundation_confidence=0.6,
            clarity=VectorState(score=0.6, rationale="Test"),
            coherence=VectorState(score=0.7, rationale="Test"),
            signal=VectorState(score=0.6, rationale="Test"),
            density=VectorState(score=0.3, rationale="Test"),
            comprehension_confidence=0.6,
            state=VectorState(score=0.5, rationale="Test"),
            change=VectorState(score=0.7, rationale="Test"),
            completion=VectorState(score=0.6, rationale="Test"),
            impact=VectorState(score=0.5, rationale="Test"),
            execution_confidence=0.6,
            uncertainty=VectorState(score=0.3, rationale="Test"),
            overall_confidence=0.6,
            recommended_action=Action.PROCEED,
            assessment_id="test_id"
        )
        
        assert assessment.engagement_gate_passed is True
        assert assessment.engagement.score == 0.7
    
    def test_critical_flags_computation(self):
        """Test critical flags based on thresholds."""
        # Test coherence critical flag
        assessment = EpistemicAssessment(
            engagement=VectorState(score=0.7, rationale="Test"),
            engagement_gate_passed=True,
            know=VectorState(score=0.5, rationale="Test"),
            do=VectorState(score=0.5, rationale="Test"),
            context=VectorState(score=0.5, rationale="Test"),
            foundation_confidence=0.6,
            clarity=VectorState(score=0.6, rationale="Test"),
            coherence=VectorState(score=0.4, rationale="Low coherence"),
            signal=VectorState(score=0.6, rationale="Test"),
            density=VectorState(score=0.3, rationale="Test"),
            comprehension_confidence=0.6,
            state=VectorState(score=0.5, rationale="Test"),
            change=VectorState(score=0.7, rationale="Test"),
            completion=VectorState(score=0.6, rationale="Test"),
            impact=VectorState(score=0.5, rationale="Test"),
            execution_confidence=0.6,
            uncertainty=VectorState(score=0.3, rationale="Test"),
            overall_confidence=0.6,
            recommended_action=Action.PROCEED,
            assessment_id="test_id"
        )
        
        assert assessment.coherence_critical is True
        
        # Test density critical flag
        assessment = EpistemicAssessment(
            engagement=VectorState(score=0.7, rationale="Test"),
            engagement_gate_passed=True,
            know=VectorState(score=0.5, rationale="Test"),
            do=VectorState(score=0.5, rationale="Test"),
            context=VectorState(score=0.5, rationale="Test"),
            foundation_confidence=0.6,
            clarity=VectorState(score=0.6, rationale="Test"),
            coherence=VectorState(score=0.7, rationale="Test"),
            signal=VectorState(score=0.6, rationale="Test"),
            density=VectorState(score=0.95, rationale="High density"),
            comprehension_confidence=0.6,
            state=VectorState(score=0.5, rationale="Test"),
            change=VectorState(score=0.7, rationale="Test"),
            completion=VectorState(score=0.6, rationale="Test"),
            impact=VectorState(score=0.5, rationale="Test"),
            execution_confidence=0.6,
            uncertainty=VectorState(score=0.3, rationale="Test"),
            overall_confidence=0.6,
            recommended_action=Action.PROCEED,
            assessment_id="test_id"
        )
        
        assert assessment.density_critical is True
        
        # Test change critical flag
        assessment = EpistemicAssessment(
            engagement=VectorState(score=0.7, rationale="Test"),
            engagement_gate_passed=True,
            know=VectorState(score=0.5, rationale="Test"),
            do=VectorState(score=0.5, rationale="Test"),
            context=VectorState(score=0.5, rationale="Test"),
            foundation_confidence=0.6,
            clarity=VectorState(score=0.6, rationale="Test"),
            coherence=VectorState(score=0.7, rationale="Test"),
            signal=VectorState(score=0.6, rationale="Test"),
            density=VectorState(score=0.3, rationale="Test"),
            comprehension_confidence=0.6,
            state=VectorState(score=0.5, rationale="Test"),
            change=VectorState(score=0.4, rationale="Low change"),
            completion=VectorState(score=0.6, rationale="Test"),
            impact=VectorState(score=0.5, rationale="Test"),
            execution_confidence=0.6,
            uncertainty=VectorState(score=0.3, rationale="Test"),
            overall_confidence=0.6,
            recommended_action=Action.PROCEED,
            assessment_id="test_id"
        )
        
        assert assessment.change_critical is True
    
    def test_confidence_validation(self):
        """Test that confidence scores must be 0.0-1.0."""
        with pytest.raises(ValueError, match="All confidence scores must be 0.0-1.0"):
            EpistemicAssessment(
                engagement=VectorState(score=0.7, rationale="Test"),
                engagement_gate_passed=True,
                know=VectorState(score=0.5, rationale="Test"),
                do=VectorState(score=0.5, rationale="Test"),
                context=VectorState(score=0.5, rationale="Test"),
                foundation_confidence=1.5,  # Invalid
                clarity=VectorState(score=0.6, rationale="Test"),
                coherence=VectorState(score=0.7, rationale="Test"),
                signal=VectorState(score=0.6, rationale="Test"),
                density=VectorState(score=0.3, rationale="Test"),
                comprehension_confidence=0.6,
                state=VectorState(score=0.5, rationale="Test"),
                change=VectorState(score=0.7, rationale="Test"),
                completion=VectorState(score=0.6, rationale="Test"),
                impact=VectorState(score=0.5, rationale="Test"),
                execution_confidence=0.6,
                uncertainty=VectorState(score=0.3, rationale="Test"),
                overall_confidence=0.6,
                recommended_action=Action.PROCEED,
                assessment_id="test_id"
            )
    
    def test_to_dict(self):
        """Test EpistemicAssessment to_dict method."""
        assessment = EpistemicAssessment(
            engagement=VectorState(score=0.7, rationale="Test rationale"),
            engagement_gate_passed=True,
            know=VectorState(score=0.5, rationale="Test"),
            do=VectorState(score=0.6, rationale="Test"),
            context=VectorState(score=0.7, rationale="Test"),
            foundation_confidence=0.6,
            clarity=VectorState(score=0.6, rationale="Test"),
            coherence=VectorState(score=0.7, rationale="Test"),
            signal=VectorState(score=0.6, rationale="Test"),
            density=VectorState(score=0.3, rationale="Test"),
            comprehension_confidence=0.6,
            state=VectorState(score=0.5, rationale="Test"),
            change=VectorState(score=0.7, rationale="Test"),
            completion=VectorState(score=0.6, rationale="Test"),
            impact=VectorState(score=0.5, rationale="Test"),
            execution_confidence=0.6,
            uncertainty=VectorState(score=0.3, rationale="Test"),
            overall_confidence=0.6,
            recommended_action=Action.PROCEED,
            assessment_id="test_id"
        )
        
        result = assessment.to_dict()
        
        assert result['assessment_id'] == 'test_id'
        assert result['engagement']['score'] == 0.7
        assert result['engagement_gate_passed'] is True
        assert result['foundation']['confidence'] == 0.6
        assert result['recommended_action'] == 'proceed'
        assert result['critical_flags']['coherence_critical'] is False


class TestReflexFrame:
    """Test Reflex Frame structure."""
    
    def test_reflex_frame_creation(self):
        """Test ReflexFrame creation and initialization."""
        assessment = EpistemicAssessment(
            engagement=VectorState(score=0.7, rationale="Test"),
            engagement_gate_passed=True,
            know=VectorState(score=0.5, rationale="Test"),
            do=VectorState(score=0.6, rationale="Test"),
            context=VectorState(score=0.7, rationale="Test"),
            foundation_confidence=0.6,
            clarity=VectorState(score=0.6, rationale="Test"),
            coherence=VectorState(score=0.7, rationale="Test"),
            signal=VectorState(score=0.6, rationale="Test"),
            density=VectorState(score=0.3, rationale="Test"),
            comprehension_confidence=0.6,
            state=VectorState(score=0.5, rationale="Test"),
            change=VectorState(score=0.7, rationale="Test"),
            completion=VectorState(score=0.6, rationale="Test"),
            impact=VectorState(score=0.5, rationale="Test"),
            execution_confidence=0.6,
            uncertainty=VectorState(score=0.3, rationale="Test"),
            overall_confidence=0.6,
            recommended_action=Action.PROCEED,
            assessment_id="test_id"
        )
        
        frame = ReflexFrame(
            frame_id="frame_123",
            timestamp=datetime.now(UTC).isoformat(),
            self_aware_flag=True,
            epistemic_assessment=assessment
        )
        
        assert frame.frame_id == "frame_123"
        assert frame.epistemic_assessment == assessment
    
    def test_reflex_frame_from_assessment(self):
        """Test ReflexFrame creation from assessment."""
        assessment = EpistemicAssessment(
            engagement=VectorState(score=0.7, rationale="Test"),
            engagement_gate_passed=True,
            know=VectorState(score=0.5, rationale="Test"),
            do=VectorState(score=0.6, rationale="Test"),
            context=VectorState(score=0.7, rationale="Test"),
            foundation_confidence=0.6,
            clarity=VectorState(score=0.6, rationale="Test"),
            coherence=VectorState(score=0.7, rationale="Test"),
            signal=VectorState(score=0.6, rationale="Test"),
            density=VectorState(score=0.3, rationale="Test"),
            comprehension_confidence=0.6,
            state=VectorState(score=0.5, rationale="Test"),
            change=VectorState(score=0.7, rationale="Test"),
            completion=VectorState(score=0.6, rationale="Test"),
            impact=VectorState(score=0.5, rationale="Test"),
            execution_confidence=0.6,
            uncertainty=VectorState(score=0.3, rationale="Test"),
            overall_confidence=0.6,
            recommended_action=Action.PROCEED,
            assessment_id="test_id"
        )
        
        frame = ReflexFrame.from_assessment(
            assessment=assessment,
            frame_id="frame_123",
            task="Test task"
        )
        
        assert frame.frame_id == "frame_123"
        assert frame.epistemic_assessment == assessment
        assert frame.task == "Test task"
        assert frame.self_aware_flag is True
    
    def test_to_dict_serialization(self):
        """Test ReflexFrame to_dict method."""
        assessment = EpistemicAssessment(
            engagement=VectorState(score=0.7, rationale="Test"),
            engagement_gate_passed=True,
            know=VectorState(score=0.5, rationale="Test"),
            do=VectorState(score=0.6, rationale="Test"),
            context=VectorState(score=0.7, rationale="Test"),
            foundation_confidence=0.6,
            clarity=VectorState(score=0.6, rationale="Test"),
            coherence=VectorState(score=0.7, rationale="Test"),
            signal=VectorState(score=0.6, rationale="Test"),
            density=VectorState(score=0.3, rationale="Test"),
            comprehension_confidence=0.6,
            state=VectorState(score=0.5, rationale="Test"),
            change=VectorState(score=0.7, rationale="Test"),
            completion=VectorState(score=0.6, rationale="Test"),
            impact=VectorState(score=0.5, rationale="Test"),
            execution_confidence=0.6,
            uncertainty=VectorState(score=0.3, rationale="Test"),
            overall_confidence=0.6,
            recommended_action=Action.PROCEED,
            assessment_id="test_id"
        )
        
        frame = ReflexFrame(
            frame_id="frame_123",
            timestamp="2023-01-01T00:00:00Z",
            self_aware_flag=True,
            epistemic_assessment=assessment,
            task="Test task",
            context={"test": "context"},
            meta_state_vector={"think": 0.5, "uncertainty": 0.2}
        )
        
        result = frame.to_dict()
        
        assert result['frameId'] == 'frame_123'
        assert result['timestamp'] == '2023-01-01T00:00:00Z'
        assert result['selfAwareFlag'] is True
        assert result['epistemicVector']['engagement'] == 0.7
        assert result['epistemicVector']['engagement_gate_passed'] is True
        assert result['epistemicVector']['know'] == 0.5
        assert result['epistemicVector']['do'] == 0.6
        assert result['metaStateVector']['think'] == 0.5
        assert result['task'] == 'Test task'
        assert result['context'] == {"test": "context"}
        assert result['recommendedAction'] == 'proceed'
        assert result['criticalFlags']['coherence_critical'] is False
    
    def test_to_json_serialization(self):
        """Test ReflexFrame to_json method."""
        assessment = EpistemicAssessment(
            engagement=VectorState(score=0.7, rationale="Test"),
            engagement_gate_passed=True,
            know=VectorState(score=0.5, rationale="Test"),
            do=VectorState(score=0.6, rationale="Test"),
            context=VectorState(score=0.7, rationale="Test"),
            foundation_confidence=0.6,
            clarity=VectorState(score=0.6, rationale="Test"),
            coherence=VectorState(score=0.7, rationale="Test"),
            signal=VectorState(score=0.6, rationale="Test"),
            density=VectorState(score=0.3, rationale="Test"),
            comprehension_confidence=0.6,
            state=VectorState(score=0.5, rationale="Test"),
            change=VectorState(score=0.7, rationale="Test"),
            completion=VectorState(score=0.6, rationale="Test"),
            impact=VectorState(score=0.5, rationale="Test"),
            execution_confidence=0.6,
            uncertainty=VectorState(score=0.3, rationale="Test"),
            overall_confidence=0.6,
            recommended_action=Action.PROCEED,
            assessment_id="test_id"
        )
        
        frame = ReflexFrame(
            frame_id="frame_123",
            timestamp="2023-01-01T00:00:00Z",
            self_aware_flag=True,
            epistemic_assessment=assessment
        )
        
        json_str = frame.to_json()
        
        # Should not raise an exception
        assert isinstance(json_str, str)
        assert '"frameId": "frame_123"' in json_str