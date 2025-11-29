"""Test PLAN phase - Optional task breakdown."""

import asyncio
from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema, VectorAssessment
from empirica.core.canonical.reflex_frame import Action
from empirica.core.metacognitive_cascade.metacognitive_cascade import (
    CanonicalEpistemicCascade,
    CascadePhase  # OLD enum with PLAN phase
)

EpistemicAssessment = EpistemicAssessmentSchema


class TestPlanPhase:
    """Test PLAN phase functionality."""
    
    def test_plan_phase_assessment(self):
        """Test PLAN phase assessment generation."""
        cascade = CanonicalEpistemicCascade()
        
        task = "Refactor authentication module with security improvements"
        context = {"project_type": "web application", "security_requirements": "high"}
        
        async def test_plan_assessment():
            assessment = await cascade._assess_epistemic_state(
                task, context, "plan_task_id", CascadePhase.PLAN
            )
            return assessment
        
        assessment = asyncio.run(test_plan_assessment())
        
        # Verify it's a proper assessment
        assert isinstance(assessment, EpistemicAssessment)
        # assert assessment.task == task  # Task field removed in schema migration
        assert assessment.overall_confidence > 0  # Should have valid confidence
        assert assessment.recommended_action == Action.INVESTIGATE  # Default for PLAN phase
        
        # PLAN assessments should have baseline characteristics
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
    
    def test_plan_phase_optional_behavior(self):
        """Test that PLAN phase is optional and only used for complex tasks."""
        cascade = CanonicalEpistemicCascade()
        
        # The PLAN phase is part of the cascade workflow but is only executed
        # when tasks are complex enough to require breakdown. For simple tasks,
        # the cascade would move directly from THINK to INVESTIGATE.
        
        # Create an assessment for a complex task
        complex_task = "Implement a comprehensive user management system with role-based access control, audit logging, and multi-factor authentication"
        
        async def test_complex_task_assessment():
            assessment = await cascade._assess_epistemic_state(
                complex_task, {}, "complex_task_id", CascadePhase.PLAN
            )
            return assessment
        
        assessment = asyncio.run(test_complex_task_assessment())
        
        assert isinstance(assessment, EpistemicAssessment)
        # assert assessment.task == complex_task  # Task field removed in schema migration
        
        # The plan phase assessment should still be valid
        assert assessment.overall_confidence > 0  # Should have valid confidence
    
    def test_plan_phase_context_handling(self):
        """Test PLAN phase context processing."""
        cascade = CanonicalEpistemicCascade()
        
        task = "Create API for user management"
        context = {
            "project_type": "web API",
            "languages": ["Python", "JavaScript"],
            "frameworks": ["FastAPI", "React"],
            "existing_components": ["database", "auth module"],
            "constraints": ["performance", "security"]
        }
        
        async def test_plan_with_context():
            assessment = await cascade._assess_epistemic_state(
                task, context, "plan_with_context", CascadePhase.PLAN
            )
            return assessment
        
        assessment = asyncio.run(test_plan_with_context())
        
        # Verify the assessment was created properly with context
        assert isinstance(assessment, EpistemicAssessment)
        # assert assessment.task == task  # Task field removed in schema migration
        
        # The context should have been processed and used in the assessment generation
        # Context factors affect the baseline scores but they should still be reasonable
        assert 0.0 <= assessment.engagement.score <= 1.0
        assert 0.0 <= assessment.know.score <= 1.0
        assert 0.0 <= assessment.do.score <= 1.0
        assert 0.0 <= assessment.context.score <= 1.0
        assert 0.0 <= assessment.overall_confidence <= 1.0
    
    def test_plan_phase_task_complexity_classification(self):
        """Test how PLAN phase handles different task complexities."""
        cascade = CanonicalEpistemicCascade()
        
        # Simple task
        simple_task = "Fix a typo in the README"
        
        async def test_simple_task():
            assessment = await cascade._assess_epistemic_state(
                simple_task, {}, "simple_task", CascadePhase.PLAN
            )
            return assessment
        
        simple_assessment = asyncio.run(test_simple_task())
        assert isinstance(simple_assessment, EpistemicAssessment)
        
        # Complex task
        complex_task = "Implement a scalable microservices architecture with event sourcing and CQRS pattern for high-frequency trading platform"
        
        async def test_complex_task():
            assessment = await cascade._assess_epistemic_state(
                complex_task, {}, "complex_task", CascadePhase.PLAN
            )
            return assessment
        
        complex_assessment = asyncio.run(test_complex_task())
        assert isinstance(complex_assessment, EpistemicAssessment)
        
        # Both should be valid assessments, but complex tasks might have different
        # characteristics in terms of uncertainty and knowledge gaps
        assert simple_assessment.overall_confidence > 0  # Should have valid confidence
        assert complex_assessment.overall_confidence > 0  # Should have valid confidence
    
    def test_plan_phase_integration_with_think(self):
        """Test PLAN phase integration with preceding THINK phase."""
        cascade = CanonicalEpistemicCascade()
        
        # Simulate a task that would benefit from planning after THINK phase
        task = "Migrate legacy monolith to microservices architecture"
        
        # This assessment would typically come from the THINK phase
        think_assessment = EpistemicAssessment(
            engagement=VectorAssessment(0.75, "Good engagement"),
            foundation_know=VectorAssessment(0.4, "Limited knowledge about microservices migration"),
            foundation_do=VectorAssessment(0.6, "Moderate capability for architecture work"),
            foundation_context=VectorAssessment(0.5, "Some context about current system"),
            comprehension_clarity=VectorAssessment(0.55, "Moderate clarity on requirements"),
            comprehension_coherence=VectorAssessment(0.65, "Some coherence in understanding"),
            comprehension_signal=VectorAssessment(0.6, "Some clarity on priorities"),
            comprehension_density=VectorAssessment(0.7, "High information density"),
            execution_state=VectorAssessment(0.55, "Partial state awareness"),
            execution_change=VectorAssessment(0.45, "Limited change tracking ability"),
            execution_completion=VectorAssessment(0.3, "Low completion awareness"),
            execution_impact=VectorAssessment(0.5, "Some impact understanding"),
            uncertainty=VectorAssessment(0.7, "High uncertainty"),
        )
        
        # In a real cascade, the PLAN phase would use information from the THINK phase
        # For testing, we just verify the PLAN phase assessment is valid
        async def test_plan_assessment_with_prior_knowledge():
            plan_assessment = await cascade._assess_epistemic_state(
                task, {}, "plan_phase", CascadePhase.PLAN
            )
            return plan_assessment
        
        plan_assessment = asyncio.run(test_plan_assessment_with_prior_knowledge())
        
        assert isinstance(plan_assessment, EpistemicAssessment)
        assert plan_assessment.engagement_gate_passed is True
        assert 0.0 <= plan_assessment.overall_confidence <= 1.0