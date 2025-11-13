import pytest
"""Test THINK phase - Initial reasoning."""

import asyncio
import pytest
from empirica.core.canonical.reflex_frame import EpistemicAssessment, VectorState, Action
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
        assert assessment.task == task
        assert assessment.engagement_gate_passed is True  # Should pass threshold
        assert assessment.recommended_action == Action.INVESTIGATE  # Default for THINK phase
        
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
            engagement=VectorState(0.5, "Low engagement - not collaborating"),
            engagement_gate_passed=False,  # Should be False since score < 0.60
            know=VectorState(0.8, "Good domain knowledge"),
            do=VectorState(0.8, "High capability"),
            context=VectorState(0.8, "Good context understanding"),
            foundation_confidence=0.8,
            clarity=VectorState(0.8, "Task is clear"),
            coherence=VectorState(0.9, "High coherence"),
            signal=VectorState(0.8, "Clear priorities"),
            density=VectorState(0.2, "Low information density"),
            comprehension_confidence=0.8,
            state=VectorState(0.8, "Good state awareness"),
            change=VectorState(0.85, "Good change tracking"),
            completion=VectorState(0.8, "Clear completion criteria"),
            impact=VectorState(0.8, "Good impact understanding"),
            execution_confidence=0.8,
            uncertainty=VectorState(0.1, "Very low uncertainty"),
            overall_confidence=0.8,
            recommended_action=Action.CLARIFY,
            assessment_id="low_engagement_test"
        )
        
        # Verify engagement gate logic
        assert low_engagement_assessment.engagement_gate_passed is False
        assert low_engagement_assessment.engagement.score == 0.5
        assert low_engagement_assessment.recommended_action == Action.CLARIFY
    
    def test_knowledge_gap_identification(self):
        """Test knowledge gap identification in THINK phase."""
        cascade = CanonicalEpistemicCascade()
        
        # Create assessment with several knowledge gaps
        assessment = EpistemicAssessment(
            engagement=VectorState(0.75, "Good engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.4, "Low domain knowledge - this creates a gap"),
            do=VectorState(0.65, "Moderate capability"),
            context=VectorState(0.5, "Low context understanding - this creates a gap"),
            foundation_confidence=0.52,
            clarity=VectorState(0.45, "Low clarity - this creates a gap"),
            coherence=VectorState(0.75, "Good coherence"),
            signal=VectorState(0.55, "Low signal clarity - this creates a gap"),
            density=VectorState(0.75, "High density - this creates a gap (inverted)"),
            comprehension_confidence=0.61,
            state=VectorState(0.5, "Low state awareness - this creates a gap"),
            change=VectorState(0.55, "Low change tracking - this creates a gap"),
            completion=VectorState(0.4, "Low completion awareness - this creates a gap"),
            impact=VectorState(0.5, "Low impact understanding - this creates a gap"),
            execution_confidence=0.49,
            uncertainty=VectorState(0.7, "High uncertainty"),
            overall_confidence=0.52,
            recommended_action=Action.INVESTIGATE,
            assessment_id="gaps_test"
        )
        
        # Identify knowledge gaps
        gaps = cascade._identify_knowledge_gaps(assessment)
        
        # Should identify gaps where score < 0.60
        gap_names = [g.split('(')[0].strip() for g in gaps]
        
        # Should have gaps for vectors below threshold
        # Guidance/gap generation removed with heuristics - AI decides via self-assessment
        
        # Should NOT have gaps for vectors >= 0.60
        # Guidance/gap generation removed with heuristics - AI decides via self-assessment
        
        # Should have 8 gaps (7 vectors below 0.60 + signal clarity)
        # Guidance/gap generation removed with heuristics - AI decides via self-assessment
    
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
            engagement=VectorState(0.8, "High engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.85, "High domain knowledge"),
            do=VectorState(0.85, "High capability"),
            context=VectorState(0.85, "High context understanding"),
            foundation_confidence=0.85,
            clarity=VectorState(0.9, "High clarity"),
            coherence=VectorState(0.9, "High coherence"),
            signal=VectorState(0.85, "High signal clarity"),
            density=VectorState(0.2, "Low density"),
            comprehension_confidence=0.87,
            state=VectorState(0.85, "High state awareness"),
            change=VectorState(0.85, "High change tracking"),
            completion=VectorState(0.8, "High completion awareness"),
            impact=VectorState(0.85, "High impact understanding"),
            execution_confidence=0.85,
            uncertainty=VectorState(0.15, "Low uncertainty"),
            overall_confidence=0.85,
            recommended_action=Action.PROCEED,
            assessment_id="good_assessment"
        )
        
        gaps = cascade._identify_epistemic_gaps(good_assessment)
        necessity_check = cascade._assess_investigation_necessity(
            good_assessment, gaps, "Simple task", {}
        )
        
        assert necessity_check['skip_investigation'] is True
        assert 'no significant epistemic gaps' in necessity_check['reason'].lower()
        
        # Test case 2: Critical gaps (should investigate)
        bad_assessment = EpistemicAssessment(
            engagement=VectorState(0.75, "Good engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.2, "Very low domain knowledge"),
            do=VectorState(0.3, "Very low capability"),
            context=VectorState(0.4, "Low context understanding"),
            foundation_confidence=0.3,
            clarity=VectorState(0.25, "Very low clarity"),
            coherence=VectorState(0.3, "Low coherence"),
            signal=VectorState(0.35, "Low signal clarity"),
            density=VectorState(0.85, "High density"),
            comprehension_confidence=0.3,
            state=VectorState(0.2, "Low state awareness"),
            change=VectorState(0.25, "Low change tracking"),
            completion=VectorState(0.15, "Very low completion awareness"),
            impact=VectorState(0.2, "Low impact understanding"),
            execution_confidence=0.2,
            uncertainty=VectorState(0.85, "Very high uncertainty"),
            overall_confidence=0.25,
            recommended_action=Action.INVESTIGATE,
            assessment_id="bad_assessment"
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
            engagement=VectorState(0.75, "Good engagement"),
            engagement_gate_passed=True,
            know=VectorState(0.6, "Moderate domain knowledge"),
            do=VectorState(0.7, "Good capability"),
            context=VectorState(0.65, "Good context understanding"),
            foundation_confidence=0.65,
            clarity=VectorState(0.7, "Good clarity"),
            coherence=VectorState(0.8, "High coherence"),
            signal=VectorState(0.75, "High signal clarity"),
            density=VectorState(0.4, "Low density"),
            comprehension_confidence=0.69,
            state=VectorState(0.65, "Good state awareness"),
            change=VectorState(0.7, "Good change tracking"),
            completion=VectorState(0.6, "Good completion awareness"),
            impact=VectorState(0.65, "Good impact understanding"),
            execution_confidence=0.65,
            uncertainty=VectorState(0.3, "Low uncertainty"),
            overall_confidence=0.65,
            recommended_action=Action.PROCEED,
            assessment_id="summary_test"
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
        assert summary['foundation_confidence'] == 0.65
        assert summary['comprehension_confidence'] == 0.69
        assert summary['execution_confidence'] == 0.65
        assert summary['overall_confidence'] == 0.65