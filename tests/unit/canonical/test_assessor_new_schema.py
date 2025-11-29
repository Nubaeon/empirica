"""
Test CanonicalEpistemicAssessor with NEW schema (EpistemicAssessmentSchema).

These tests verify that the new parse_llm_response() method correctly
parses LLM responses and returns the NEW EpistemicAssessmentSchema.
"""

import pytest
import json
from empirica.core.canonical.canonical_epistemic_assessment import CanonicalEpistemicAssessor
from empirica.core.schemas.epistemic_assessment import (
    EpistemicAssessmentSchema,
    VectorAssessment,
    CascadePhase
)
EpistemicAssessment = EpistemicAssessmentSchema  # Alias for backwards compat


@pytest.fixture
def assessor():
    """Create assessor instance."""
    return CanonicalEpistemicAssessor(agent_id="test_agent")


@pytest.fixture
def sample_llm_response():
    """Sample LLM response in expected JSON format."""
    return {
        "engagement": {
            "score": 0.75,
            "rationale": "Good collaborative engagement",
            "evidence": "User provided clear prompt"
        },
        "foundation": {
            "know": {
                "score": 0.60,
                "rationale": "Moderate domain knowledge",
                "evidence": "Familiar with concepts"
            },
            "do": {
                "score": 0.65,
                "rationale": "Good capability",
                "evidence": "Have necessary tools"
            },
            "context": {
                "score": 0.70,
                "rationale": "Good context understanding",
                "evidence": "Requirements clear"
            }
        },
        "comprehension": {
            "clarity": {
                "score": 0.70,
                "rationale": "Clear requirements"
            },
            "coherence": {
                "score": 0.75,
                "rationale": "Coherent understanding"
            },
            "signal": {
                "score": 0.65,
                "rationale": "Good signal quality"
            },
            "density": {
                "score": 0.60,
                "rationale": "Moderate density"
            }
        },
        "execution": {
            "state": {
                "score": 0.65,
                "rationale": "Good state awareness"
            },
            "change": {
                "score": 0.60,
                "rationale": "Tracking changes"
            },
            "completion": {
                "score": 0.40,
                "rationale": "Low completion"
            },
            "impact": {
                "score": 0.65,
                "rationale": "Understanding impact"
            }
        },
        "uncertainty": {
            "score": 0.50,
            "rationale": "Moderate uncertainty"
        }
    }


class TestAssessorNewSchema:
    """Test assessor with NEW schema."""
    
    def test_parse_llm_response_returns_new_schema(self, assessor, sample_llm_response):
        """Test that parse_llm_response returns EpistemicAssessmentSchema."""
        assessment = assessor.parse_llm_response(
            llm_response=sample_llm_response,
            assessment_id="test_123",
            task="Test task",
            phase=CascadePhase.PREFLIGHT,
            round_num=0
        )
        
        # Verify it's the NEW schema type
        assert isinstance(assessment, EpistemicAssessmentSchema)
    
    def test_all_vectors_parsed(self, assessor, sample_llm_response):
        """Test that all 13 vectors are parsed correctly."""
        assessment = assessor.parse_llm_response(
            llm_response=sample_llm_response,
            assessment_id="test_123",
            task="Test task",
            phase=CascadePhase.PREFLIGHT
        )
        
        # Check all vectors exist and are VectorAssessment type
        assert isinstance(assessment.engagement, VectorAssessment)
        assert isinstance(assessment.foundation_know, VectorAssessment)
        assert isinstance(assessment.foundation_do, VectorAssessment)
        assert isinstance(assessment.foundation_context, VectorAssessment)
        assert isinstance(assessment.comprehension_clarity, VectorAssessment)
        assert isinstance(assessment.comprehension_coherence, VectorAssessment)
        assert isinstance(assessment.comprehension_signal, VectorAssessment)
        assert isinstance(assessment.comprehension_density, VectorAssessment)
        assert isinstance(assessment.execution_state, VectorAssessment)
        assert isinstance(assessment.execution_change, VectorAssessment)
        assert isinstance(assessment.execution_completion, VectorAssessment)
        assert isinstance(assessment.execution_impact, VectorAssessment)
        assert isinstance(assessment.uncertainty, VectorAssessment)
    
    def test_scores_preserved(self, assessor, sample_llm_response):
        """Test that scores are preserved from LLM response."""
        assessment = assessor.parse_llm_response(
            llm_response=sample_llm_response,
            assessment_id="test_123",
            task="Test task",
            phase=CascadePhase.PREFLIGHT
        )
        
        assert assessment.engagement.score == 0.75
        assert assessment.foundation_know.score == 0.60
        assert assessment.foundation_do.score == 0.65
        assert assessment.foundation_context.score == 0.70
        assert assessment.comprehension_clarity.score == 0.70
        assert assessment.comprehension_coherence.score == 0.75
        assert assessment.comprehension_signal.score == 0.65
        assert assessment.comprehension_density.score == 0.60
        assert assessment.execution_state.score == 0.65
        assert assessment.execution_change.score == 0.60
        assert assessment.execution_completion.score == 0.40
        assert assessment.execution_impact.score == 0.65
        assert assessment.uncertainty.score == 0.50
    
    def test_rationale_preserved(self, assessor, sample_llm_response):
        """Test that rationale text is preserved."""
        assessment = assessor.parse_llm_response(
            llm_response=sample_llm_response,
            assessment_id="test_123",
            task="Test task",
            phase=CascadePhase.PREFLIGHT
        )
        
        assert assessment.engagement.rationale == "Good collaborative engagement"
        assert assessment.foundation_know.rationale == "Moderate domain knowledge"
        assert assessment.foundation_do.rationale == "Good capability"
    
    def test_evidence_preserved(self, assessor, sample_llm_response):
        """Test that evidence is preserved when provided."""
        assessment = assessor.parse_llm_response(
            llm_response=sample_llm_response,
            assessment_id="test_123",
            task="Test task",
            phase=CascadePhase.PREFLIGHT
        )
        
        assert assessment.engagement.evidence == "User provided clear prompt"
        assert assessment.foundation_know.evidence == "Familiar with concepts"
        assert assessment.foundation_do.evidence == "Have necessary tools"
    
    def test_evidence_none_when_missing(self, assessor, sample_llm_response):
        """Test that evidence is None when not provided."""
        assessment = assessor.parse_llm_response(
            llm_response=sample_llm_response,
            assessment_id="test_123",
            task="Test task",
            phase=CascadePhase.PREFLIGHT
        )
        
        # Clarity doesn't have evidence in sample
        assert assessment.comprehension_clarity.evidence is None
    
    def test_metadata_fields(self, assessor, sample_llm_response):
        """Test that metadata fields are set correctly."""
        assessment = assessor.parse_llm_response(
            llm_response=sample_llm_response,
            assessment_id="test_123",
            task="Test task",
            phase=CascadePhase.CHECK,
            round_num=2
        )
        
        assert assessment.phase == CascadePhase.CHECK
        assert assessment.round_num == 2
        assert assessment.investigation_count == 0  # Default
    
    def test_parses_string_json(self, assessor, sample_llm_response):
        """Test that it can parse JSON from string."""
        json_string = json.dumps(sample_llm_response)
        
        assessment = assessor.parse_llm_response(
            llm_response=json_string,
            assessment_id="test_123",
            task="Test task",
            phase=CascadePhase.PREFLIGHT
        )
        
        assert isinstance(assessment, EpistemicAssessmentSchema)
        assert assessment.engagement.score == 0.75
    
    def test_parses_markdown_wrapped_json(self, assessor, sample_llm_response):
        """Test that it can extract JSON from markdown code blocks."""
        json_string = json.dumps(sample_llm_response, indent=2)
        markdown_wrapped = f"Here's my assessment:\n\n```json\n{json_string}\n```\n\nThat's my analysis."
        
        assessment = assessor.parse_llm_response(
            llm_response=markdown_wrapped,
            assessment_id="test_123",
            task="Test task",
            phase=CascadePhase.PREFLIGHT
        )
        
        assert isinstance(assessment, EpistemicAssessmentSchema)
        assert assessment.engagement.score == 0.75
    
    def test_tier_confidence_calculation(self, assessor, sample_llm_response):
        """Test that tier confidences can be calculated from NEW schema."""
        assessment = assessor.parse_llm_response(
            llm_response=sample_llm_response,
            assessment_id="test_123",
            task="Test task",
            phase=CascadePhase.PREFLIGHT
        )
        
        # NEW schema should have calculate_tier_confidences() method
        tier_confidences = assessment.calculate_tier_confidences()
        
        assert 'foundation_confidence' in tier_confidences
        assert 'comprehension_confidence' in tier_confidences
        assert 'execution_confidence' in tier_confidences
        assert 'overall_confidence' in tier_confidences
    
    def test_action_determination(self, assessor, sample_llm_response):
        """Test that action can be determined from NEW schema."""
        assessment = assessor.parse_llm_response(
            llm_response=sample_llm_response,
            assessment_id="test_123",
            task="Test task",
            phase=CascadePhase.PREFLIGHT
        )
        
        # NEW schema should have determine_action() method
        action = assessment.determine_action()
        
        assert action in ['proceed', 'investigate', 'escalate']
    
    def test_missing_field_raises_error(self, assessor):
        """Test that missing required fields raise ValueError."""
        incomplete_response = {
            "engagement": {
                "score": 0.75,
                "rationale": "Test"
            }
            # Missing foundation, comprehension, execution, uncertainty
        }
        
        with pytest.raises(ValueError, match="Missing or invalid field"):
            assessor.parse_llm_response(
                llm_response=incomplete_response,
                assessment_id="test_123",
                task="Test task",
                phase=CascadePhase.PREFLIGHT
            )
    
    def test_invalid_json_raises_error(self, assessor):
        """Test that invalid JSON raises ValueError."""
        invalid_json = "This is not JSON {invalid}"
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            assessor.parse_llm_response(
                llm_response=invalid_json,
                assessment_id="test_123",
                task="Test task",
                phase=CascadePhase.PREFLIGHT
            )


class TestBackwardsCompatibility:
    """Test that OLD parse_llm_response still works."""
    
    def test_old_method_still_works(self, assessor, sample_llm_response):
        """Test that parse_llm_response (NEW schema) works."""
        
        assessment = assessor.parse_llm_response(
            llm_response=sample_llm_response,
            assessment_id="test_123",
            task="Test task"
        )
        
        # Should return OLD schema
        assert isinstance(assessment, EpistemicAssessment)
        assert assessment.engagement.score == 0.75
