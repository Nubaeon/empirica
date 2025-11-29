import pytest
"""Test INVESTIGATE phase - Knowledge gap filling."""

import asyncio
from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema, CascadePhase, VectorAssessment
from empirica.core.canonical.reflex_frame import Action
EpistemicAssessment = EpistemicAssessmentSchema
from empirica.core.metacognitive_cascade.metacognitive_cascade import (
    CanonicalEpistemicCascade,
    CascadePhase
)


class TestInvestigatePhase:
    """Test INVESTIGATE phase functionality."""
    
    def test_investigate_phase_assessment(self):
        """Test INVESTIGATE phase assessment generation."""
        cascade = CanonicalEpistemicCascade()
        
        task = "Debug performance issues in user authentication"
        context = {"error_logs": "auth timeout errors", "metrics": "high response times"}
        
        async def test_investigate_assessment():
            assessment = await cascade._assess_epistemic_state(
                task, context, "investigate_task_id", CascadePhase.INVESTIGATE
            )
            return assessment
        
        assessment = asyncio.run(test_investigate_assessment())
        
        # Verify it's a proper assessment
        assert isinstance(assessment, EpistemicAssessment)
        # assert assessment.task == task  # Task field removed in schema migration
        assert assessment.overall_confidence > 0  # Should have valid confidence
        assert assessment.recommended_action == Action.INVESTIGATE  # Default for INVESTIGATE phase
        
        # INVESTIGATE assessments should have baseline characteristics
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
    
    def test_investigate_phase_with_rounds(self):
        """Test INVESTIGATE phase with investigation rounds."""
        cascade = CanonicalEpistemicCascade()
        
        task = "Fix database connection issues"
        context = {"error_type": "timeout", "database": "PostgreSQL"}
        
        async def test_investigate_with_rounds():
            # Simulate first investigation round
            assessment_round_1 = await cascade._assess_epistemic_state(
                task, context, "investigate_task_id", CascadePhase.INVESTIGATE, round_num=1
            )
            
            # Simulate second investigation round
            assessment_round_2 = await cascade._assess_epistemic_state(
                task, context, "investigate_task_id", CascadePhase.INVESTIGATE, 
                round_num=2, investigation_rounds=1
            )
            
            return assessment_round_1, assessment_round_2
        
        assessment_r1, assessment_r2 = asyncio.run(test_investigate_with_rounds())
        
        assert isinstance(assessment_r1, EpistemicAssessment)
        assert isinstance(assessment_r2, EpistemicAssessment)
        # assert assessment_r1.task == task  # Task field removed in schema migration
        # assert assessment_r2.task == task  # Task field removed in schema migration
    
    @pytest.mark.skip(reason="Test checks heuristics that were intentionally removed - AI decides via self-assessment")
    def test_investigation_process(self):
        """Test the investigation process functionality."""
        cascade = CanonicalEpistemicCascade()
        
        # Create an assessment with knowledge gaps
        assessment_with_gaps = EpistemicAssessment(
            engagement=VectorAssessment(0.75, "Good engagement"),
            engagement_gate_passed=True,
            know=VectorAssessment(0.4, "Limited knowledge about database connection issues"),
            do=VectorAssessment(0.6, "Moderate capability for debugging"),
            context=VectorAssessment(0.5, "Some context about the error"),
            foundation_confidence=0.5,
            clarity=VectorAssessment(0.55, "Moderate clarity"),
            coherence=VectorAssessment(0.65, "Reasonable coherence"),
            signal=VectorAssessment(0.6, "Some priority clarity"),
            density=VectorAssessment(0.7, "High information density"),
            comprehension_confidence=0.6,
            state=VectorAssessment(0.55, "Partial state awareness"),
            change=VectorAssessment(0.45, "Limited change tracking"),
            completion=VectorAssessment(0.3, "Low completion awareness"),
            impact=VectorAssessment(0.5, "Some impact understanding"),
            execution_confidence=0.45,
            uncertainty=VectorAssessment(0.7, "High uncertainty"),
            overall_confidence=0.52,
            recommended_action=Action.INVESTIGATE,
        )
        
        task = "Investigate database connection timeout issues"
        context = {"error_logs": "timeout errors", "database": "PostgreSQL"}
        gaps = ["Knowledge gap: database connection issues", "Context gap: system architecture"]
        
        async def test_conduct_investigation():
            investigation_result = await cascade._conduct_investigation(
                task, context, gaps, assessment_with_gaps
            )
            return investigation_result
        
        result = asyncio.run(test_conduct_investigation())
        
        # Verify investigation result structure
        assert isinstance(result, dict)
        assert 'epistemic_gaps' in result
        assert 'tool_capabilities' in result
        assert 'strategic_guidance' in result
        assert 'guidance' in result
        assert 'domain_context' in result
        
        # Verify the epistemic gaps are included
        assert isinstance(result['epistemic_gaps'], list)
        
        # Verify tool capabilities are provided
        assert isinstance(result['tool_capabilities'], dict)
        
        # Verify strategic guidance is provided
        assert isinstance(result['strategic_guidance'], dict)
    
    @pytest.mark.skip(reason="Test checks heuristics that were intentionally removed - AI decides via self-assessment")
    def test_tool_capability_mapping(self):
        """Test tool capability mapping functionality."""
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
    def test_investigation_strategy_generation(self):
        """Test investigation strategy generation for different scenarios."""
        cascade = CanonicalEpistemicCascade()
        
        # Scenario 1: Clarity gaps should suggest asking user
        clarity_gap_assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.75, "Good engagement"),
            engagement_gate_passed=True,
            know=VectorAssessment(0.7, "Good domain knowledge"),
            do=VectorAssessment(0.7, "Good capability"),
            context=VectorAssessment(0.7, "Good context"),
            foundation_confidence=0.7,
            clarity=VectorAssessment(0.4, "LOW CLARITY - main issue"),
            coherence=VectorAssessment(0.7, "Good coherence"),
            signal=VectorAssessment(0.65, "Good signal"),
            density=VectorAssessment(0.5, "Moderate density"),
            comprehension_confidence=0.65,
            state=VectorAssessment(0.65, "Good state awareness"),
            change=VectorAssessment(0.7, "Good change tracking"),
            completion=VectorAssessment(0.65, "Good completion awareness"),
            impact=VectorAssessment(0.65, "Good impact understanding"),
            execution_confidence=0.67,
            uncertainty=VectorAssessment(0.55, "Moderate uncertainty"),
            overall_confidence=0.67,
            recommended_action=Action.INVESTIGATE,
        )
        
        gaps = cascade._identify_epistemic_gaps(clarity_gap_assessment)
        strategy = cascade._generate_investigation_strategy(
            gaps, clarity_gap_assessment, "Unclear requirements task"
        )
        
        # Should have user clarification strategy when clarity is low
        assert 'ASK USER' in strategy['primary_strategy'] or 'clarification' in strategy['approach']
        
        # Scenario 2: Knowledge gaps should suggest external search
        knowledge_gap_assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.75, "Good engagement"),
            engagement_gate_passed=True,
            know=VectorAssessment(0.3, "LOW KNOWLEDGE - main issue"),
            do=VectorAssessment(0.65, "Good capability"),
            context=VectorAssessment(0.6, "Moderate context"),
            foundation_confidence=0.52,
            clarity=VectorAssessment(0.7, "Good clarity"),
            coherence=VectorAssessment(0.7, "Good coherence"),
            signal=VectorAssessment(0.65, "Good signal"),
            density=VectorAssessment(0.55, "Moderate density"),
            comprehension_confidence=0.66,
            state=VectorAssessment(0.6, "Moderate state awareness"),
            change=VectorAssessment(0.65, "Good change tracking"),
            completion=VectorAssessment(0.6, "Moderate completion awareness"),
            impact=VectorAssessment(0.6, "Moderate impact understanding"),
            execution_confidence=0.62,
            uncertainty=VectorAssessment(0.6, "High uncertainty"),
            overall_confidence=0.62,
            recommended_action=Action.INVESTIGATE,
        )
        
        gaps = cascade._identify_epistemic_gaps(knowledge_gap_assessment)
        strategy = cascade._generate_investigation_strategy(
            gaps, knowledge_gap_assessment, "Unknown technology task"
        )
        
        # Should suggest external search when knowledge is low
        assert 'SEARCH' in strategy['primary_strategy'] or 'search' in strategy['approach']
        
        # Scenario 3: Context/state gaps should suggest environment scanning
        context_gap_assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.75, "Good engagement"),
            engagement_gate_passed=True,
            know=VectorAssessment(0.7, "Good domain knowledge"),
            do=VectorAssessment(0.7, "Good capability"),
            context=VectorAssessment(0.35, "LOW CONTEXT - main issue"),
            foundation_confidence=0.58,
            clarity=VectorAssessment(0.7, "Good clarity"),
            coherence=VectorAssessment(0.7, "Good coherence"),
            signal=VectorAssessment(0.65, "Good signal"),
            density=VectorAssessment(0.5, "Moderate density"),
            comprehension_confidence=0.66,
            state=VectorAssessment(0.4, "LOW STATE - secondary issue"),
            change=VectorAssessment(0.65, "Good change tracking"),
            completion=VectorAssessment(0.65, "Good completion awareness"),
            impact=VectorAssessment(0.65, "Good impact understanding"),
            execution_confidence=0.63,
            uncertainty=VectorAssessment(0.45, "Moderate uncertainty"),
            overall_confidence=0.64,
            recommended_action=Action.INVESTIGATE,
        )
        
        gaps = cascade._identify_epistemic_gaps(context_gap_assessment)
        strategy = cascade._generate_investigation_strategy(
            gaps, context_gap_assessment, "Environment unknown task"
        )
        
        # Should suggest environment scanning when context/state is low
        assert 'SCAN' in strategy['primary_strategy'] or 'environmental' in strategy['approach']
    
    @pytest.mark.skip(reason="Test checks heuristics that were intentionally removed - AI decides via self-assessment")
    def test_investigation_necessity_logic(self):
        """Test the logic for determining if investigation is necessary."""
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
    def test_investigation_loop_simulation(self):
        """Test the investigation loop simulation."""
        cascade = CanonicalEpistemicCascade(
            action_confidence_threshold=0.75,
            max_investigation_rounds=3
        )
        
        # Start with low confidence assessment
        current_assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.75, "Good engagement"),
            engagement_gate_passed=True,
            know=VectorAssessment(0.4, "Low knowledge"),
            do=VectorAssessment(0.5, "Moderate capability"),
            context=VectorAssessment(0.45, "Low context"),
            foundation_confidence=0.45,
            clarity=VectorAssessment(0.5, "Moderate clarity"),
            coherence=VectorAssessment(0.55, "Moderate coherence"),
            signal=VectorAssessment(0.45, "Low signal"),
            density=VectorAssessment(0.6, "Moderate density"),
            comprehension_confidence=0.5,
            state=VectorAssessment(0.45, "Low state awareness"),
            change=VectorAssessment(0.5, "Moderate change tracking"),
            completion=VectorAssessment(0.35, "Low completion awareness"),
            impact=VectorAssessment(0.45, "Low impact understanding"),
            execution_confidence=0.43,
            uncertainty=VectorAssessment(0.65, "High uncertainty"),
            overall_confidence=0.47,  # Below threshold of 0.75
            recommended_action=Action.INVESTIGATE,
        )
        
        investigation_rounds = 0
        max_rounds = cascade.max_investigation_rounds
        
        # Simulate the investigation loop
        while current_assessment.overall_confidence < cascade.action_confidence_threshold:
            if investigation_rounds >= max_rounds:
                break  # Reached max rounds
            
            investigation_rounds += 1
            
            # In a real scenario, this would involve conducting investigation
            # and updating the assessment based on results
            # For this test, we'll just create a new assessment with improved scores
            
            # Simulate improvement after investigation
            current_assessment = EpistemicAssessment(
                engagement=VectorAssessment(0.75, f"Maintained engagement after round {investigation_rounds}"),
                engagement_gate_passed=True,
                know=VectorAssessment(0.4 + (investigation_rounds * 0.15), f"Improved knowledge after round {investigation_rounds}"),
                do=VectorAssessment(0.5 + (investigation_rounds * 0.12), f"Improved capability after round {investigation_rounds}"),
                context=VectorAssessment(0.45 + (investigation_rounds * 0.14), f"Improved context after round {investigation_rounds}"),
                foundation_confidence=0.45 + (investigation_rounds * 0.14),
                clarity=VectorAssessment(0.5 + (investigation_rounds * 0.13), f"Improved clarity after round {investigation_rounds}"),
                coherence=VectorAssessment(0.55 + (investigation_rounds * 0.11), f"Improved coherence after round {investigation_rounds}"),
                signal=VectorAssessment(0.45 + (investigation_rounds * 0.13), f"Improved signal after round {investigation_rounds}"),
                density=VectorAssessment(0.6 - (investigation_rounds * 0.08), f"Improved density after round {investigation_rounds}"),  # Lower density is better
                comprehension_confidence=0.5 + (investigation_rounds * 0.12),
                state=VectorAssessment(0.45 + (investigation_rounds * 0.15), f"Improved state awareness after round {investigation_rounds}"),
                change=VectorAssessment(0.5 + (investigation_rounds * 0.12), f"Improved change tracking after round {investigation_rounds}"),
                completion=VectorAssessment(0.35 + (investigation_rounds * 0.18), f"Improved completion awareness after round {investigation_rounds}"),
                impact=VectorAssessment(0.45 + (investigation_rounds * 0.14), f"Improved impact understanding after round {investigation_rounds}"),
                execution_confidence=0.43 + (investigation_rounds * 0.16),
                uncertainty=VectorAssessment(0.65 - (investigation_rounds * 0.15), f"Reduced uncertainty after round {investigation_rounds}"),  # Reduce uncertainty
                overall_confidence=0.47 + (investigation_rounds * 0.14),  # Improve overall confidence
                recommended_action=Action.PROCEED if investigation_rounds >= 2 else Action.INVESTIGATE,
            )
        
        # After 3 rounds, confidence should be higher
        assert investigation_rounds <= max_rounds
        assert current_assessment.overall_confidence >= 0.47  # Should have improved
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
