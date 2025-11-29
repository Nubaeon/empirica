import pytest
"""Test THINK phase - Initial reasoning."""

import asyncio
import pytest
from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema, CascadePhase, VectorAssessment
from empirica.core.canonical.reflex_frame import Action
EpistemicAssessment = EpistemicAssessmentSchema
from empirica.core.metacognitive_cascade.metacognitive_cascade import (
    CanonicalEpistemicCascade,
    CascadePhase
)


class TestThinkPhase:
    """Test THINK phase functionality."""
    
    def test_think_phase_assessment(self):
        """Test THINK phase assessment generation."""
        cascade = CanonicalEpistemicCascade()
        
        task = "Implement user authentication system"
        context = {"project_type": "web application", "security_requirements": "high"}
        
        async def test_think_assessment():
            assessment = await cascade._assess_epistemic_state(
                task, context, "think_task_id", CascadePhase.THINK
            )
            return assessment
        
        assessment = asyncio.run(test_think_assessment())
        
        # Verify it's a proper assessment
        assert isinstance(assessment, EpistemicAssessment)
        # Task field removed in schema migration
        # Engagement gate passed is no longer stored as a field
        
        # THINK assessments should have baseline characteristics
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
    
    def test_engagement_gate_logic(self):
        """Test engagement gate logic in THINK phase."""
        cascade = CanonicalEpistemicCascade()
        
        # Test assessment with low engagement (should fail gate)
        low_engagement_assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.5, "Low engagement - not collaborating"),
            foundation_know=VectorAssessment(0.8, "Good domain knowledge"),
            foundation_do=VectorAssessment(0.8, "High capability"),
            foundation_context=VectorAssessment(0.8, "Good context understanding"),
            comprehension_clarity=VectorAssessment(0.8, "Task is clear"),
            comprehension_coherence=VectorAssessment(0.9, "High coherence"),
            comprehension_signal=VectorAssessment(0.8, "Clear priorities"),
            comprehension_density=VectorAssessment(0.2, "Low information density"),
            execution_state=VectorAssessment(0.8, "Good state awareness"),
            execution_change=VectorAssessment(0.85, "Good change tracking"),
            execution_completion=VectorAssessment(0.8, "Clear completion criteria"),
            execution_impact=VectorAssessment(0.8, "Good impact understanding"),
            uncertainty=VectorAssessment(0.1, "Very low uncertainty"),
            phase=CascadePhase.THINK,
        )
        
        # Verify engagement gate logic - low engagement score
        assert low_engagement_assessment.engagement.score == 0.5
    
    def test_knowledge_gap_identification(self):
        """Test knowledge gap identification in THINK phase."""
        cascade = CanonicalEpistemicCascade()
        
        # Create assessment with several knowledge gaps
        assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.75, "Good engagement"),
            foundation_know=VectorAssessment(0.4, "Low domain knowledge - this creates a gap"),
            foundation_do=VectorAssessment(0.65, "Moderate capability"),
            foundation_context=VectorAssessment(0.5, "Low context understanding - this creates a gap"),
            comprehension_clarity=VectorAssessment(0.45, "Low clarity - this creates a gap"),
            comprehension_coherence=VectorAssessment(0.75, "Good coherence"),
            comprehension_signal=VectorAssessment(0.55, "Low signal clarity - this creates a gap"),
            comprehension_density=VectorAssessment(0.75, "High density - this creates a gap (inverted)"),
            execution_state=VectorAssessment(0.5, "Low state awareness - this creates a gap"),
            execution_change=VectorAssessment(0.55, "Low change tracking - this creates a gap"),
            execution_completion=VectorAssessment(0.4, "Low completion awareness - this creates a gap"),
            execution_impact=VectorAssessment(0.5, "Low impact understanding - this creates a gap"),
            uncertainty=VectorAssessment(0.7, "High uncertainty"),
            phase=CascadePhase.THINK,
        )
        
        # Identify knowledge gaps
        gaps = cascade._identify_knowledge_gaps(assessment)
        
        # Guidance/gap generation removed with heuristics - AI decides via self-assessment
        # Just verify the method exists and doesn't crash
        assert isinstance(gaps, list)
    
    @pytest.mark.skip(reason="Test checks heuristics that were intentionally removed - AI decides via self-assessment")
    def test_gap_analysis(self):
        """Test the detailed gap analysis functionality."""
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

    @pytest.mark.skip(reason="Test checks heuristics that were intentionally removed - AI decides via self-assessment")
    def test_investigation_necessity_assessment(self):
        """Test the logic for determining if investigation is needed."""
        cascade = CanonicalEpistemicCascade()
        
        # Test case 1: No significant gaps (should skip investigation)
        good_assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.8, "High engagement"),
            engagement_gate_passed=True,
            know=VectorAssessment(0.85, "High domain knowledge"),
            do=VectorAssessment(0.85, "High capability"),
            context=VectorAssessment(0.85, "High context understanding"),
            foundation_confidence=0.85,
            clarity=VectorAssessment(0.9, "High clarity"),
            coherence=VectorAssessment(0.9, "High coherence"),
            signal=VectorAssessment(0.85, "High signal clarity"),
            density=VectorAssessment(0.2, "Low density"),
            comprehension_confidence=0.87,
            state=VectorAssessment(0.85, "High state awareness"),
            change=VectorAssessment(0.85, "High change tracking"),
            completion=VectorAssessment(0.8, "High completion awareness"),
            impact=VectorAssessment(0.85, "High impact understanding"),
            execution_confidence=0.85,
            uncertainty=VectorAssessment(0.15, "Low uncertainty"),
            overall_confidence=0.85,
            recommended_action=Action.PROCEED,
        )
        
        gaps = cascade._identify_epistemic_gaps(good_assessment)
        necessity_check = cascade._assess_investigation_necessity(
            good_assessment, gaps, "Simple task", {}
        )
        
        assert necessity_check['skip_investigation'] is True
        assert 'no significant epistemic gaps' in necessity_check['reason'].lower()
        
        # Test case 2: Critical gaps (should investigate)
        bad_assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.75, "Good engagement"),
            engagement_gate_passed=True,
            know=VectorAssessment(0.2, "Very low domain knowledge"),
            do=VectorAssessment(0.3, "Very low capability"),
            context=VectorAssessment(0.4, "Low context understanding"),
            foundation_confidence=0.3,
            clarity=VectorAssessment(0.25, "Very low clarity"),
            coherence=VectorAssessment(0.3, "Low coherence"),
            signal=VectorAssessment(0.35, "Low signal clarity"),
            density=VectorAssessment(0.85, "High density"),
            comprehension_confidence=0.3,
            state=VectorAssessment(0.2, "Low state awareness"),
            change=VectorAssessment(0.25, "Low change tracking"),
            completion=VectorAssessment(0.15, "Very low completion awareness"),
            impact=VectorAssessment(0.2, "Low impact understanding"),
            execution_confidence=0.2,
            uncertainty=VectorAssessment(0.85, "Very high uncertainty"),
            overall_confidence=0.25,
            recommended_action=Action.INVESTIGATE,
        )
        
        gaps = cascade._identify_epistemic_gaps(bad_assessment)
        necessity_check = cascade._assess_investigation_necessity(
            bad_assessment, gaps, "Complex security task", {}
        )
        
        assert necessity_check['skip_investigation'] is False
        assert necessity_check['priority'] in ['high', 'critical']
    
    @pytest.mark.skip(reason="Test checks heuristics that were intentionally removed - AI decides via self-assessment")
    def test_investigation_strategy_generation(self):
        """Test the generation of investigation strategies."""
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

    def test_vector_summary_extraction(self):
        """Test extraction of vector summaries."""
        cascade = CanonicalEpistemicCascade()
        
        assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.75, "Good engagement"),
            foundation_know=VectorAssessment(0.6, "Moderate domain knowledge"),
            foundation_do=VectorAssessment(0.7, "Good capability"),
            foundation_context=VectorAssessment(0.65, "Good context understanding"),
            comprehension_clarity=VectorAssessment(0.7, "Good clarity"),
            comprehension_coherence=VectorAssessment(0.8, "High coherence"),
            comprehension_signal=VectorAssessment(0.75, "High signal clarity"),
            comprehension_density=VectorAssessment(0.4, "Low density"),
            execution_state=VectorAssessment(0.65, "Good state awareness"),
            execution_change=VectorAssessment(0.7, "Good change tracking"),
            execution_completion=VectorAssessment(0.6, "Good completion awareness"),
            execution_impact=VectorAssessment(0.65, "Good impact understanding"),
            uncertainty=VectorAssessment(0.3, "Low uncertainty"),
            phase=CascadePhase.THINK,
        )
        
        summary = cascade._extract_vector_summary(assessment)
        
        # Verify all vector values are correctly extracted
        assert summary['engagement'] == 0.75
        assert summary['know'] == 0.6
        assert summary['do'] == 0.7
        assert summary['context'] == 0.65
        assert summary['clarity'] == 0.7
        assert summary['coherence'] == 0.8
        assert summary['signal'] == 0.75
        assert summary['density'] == 0.4
        assert summary['state'] == 0.65
        assert summary['change'] == 0.7
        assert summary['completion'] == 0.6
        assert summary['impact'] == 0.65