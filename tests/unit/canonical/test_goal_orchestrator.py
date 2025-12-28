"""Test Canonical Goal Orchestrator - LLM-based decomposition."""

import asyncio
from empirica.core.canonical.canonical_goal_orchestrator import (
    CanonicalGoalOrchestrator,
    Goal,
    GoalPriority,
    GoalAutonomyLevel
)
from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema
EpistemicAssessment = EpistemicAssessmentSchema  # Alias for backwards compat
from empirica.core.canonical.reflex_frame import VectorState, Action


class TestCanonicalGoalOrchestrator:
    """Test Goal Orchestrator functionality."""
    
    def test_goal_decomposition(self):
        """Test decomposition of complex goals using LLM reasoning."""
        orchestrator = CanonicalGoalOrchestrator(use_placeholder=True)
        
        conversation_context = "User wants to implement a new feature for user authentication"
        
        # Create a mock epistemic assessment
        assessment = EpistemicAssessment(
            engagement=VectorState(score=0.75, rationale="Active collaboration with user"),
            foundation_know=VectorState(score=0.6, rationale="Some domain knowledge but with gaps"),
            foundation_do=VectorState(score=0.7, rationale="Capable of implementation tasks"),
            foundation_context=VectorState(score=0.65, rationale="Environment context understood but needs more details"),
            comprehension_clarity=VectorState(score=0.75, rationale="Task requirements are clear"),
            comprehension_coherence=VectorState(score=0.8, rationale="Request is logically consistent"),
            comprehension_signal=VectorState(score=0.7, rationale="Clear priority on security aspects"),
            comprehension_density=VectorState(score=0.5, rationale="Manageable information load"),
            execution_state=VectorState(score=0.6, rationale="Environment mapping in progress"),
            execution_change=VectorState(score=0.7, rationale="Can track modifications effectively"),
            execution_completion=VectorState(score=0.5, rationale="Task just beginning"),
            execution_impact=VectorState(score=0.75, rationale="Clear understanding of consequences"),
            uncertainty=VectorState(score=0.3, rationale="Low uncertainty about approach"),
        )
        
        current_state = {
            "available_tools": ["read", "write", "edit"],
            "project_type": "web application",
            "security_requirements": "high"
        }
        
        # Test goal orchestration
        goals = asyncio.run(orchestrator.orchestrate_goals(
            conversation_context,
            assessment,
            current_state
        ))
        
        # Verify goals were generated
        assert len(goals) > 0
        assert all(isinstance(goal, Goal) for goal in goals)
        
        # Verify goals have required fields
        for goal in goals:
            assert goal.goal
            assert isinstance(goal.priority, int)
            assert goal.priority >= 1 and goal.priority <= 10
            assert goal.action_type in ["INVESTIGATE", "CLARIFY", "ACT", "LEARN", "RESET"]
            assert goal.autonomy_level in GoalAutonomyLevel
            assert goal.reasoning
    
    def test_autonomy_level_based_on_engagement(self):
        """Test autonomy level determination based on engagement."""
        orchestrator = CanonicalGoalOrchestrator(use_placeholder=True)
        
        # Test high engagement (should lead to high autonomy)
        high_engagement_assessment = EpistemicAssessment(
            engagement=VectorState(score=0.85, rationale="High collaborative engagement"),
            foundation_know=VectorState(score=0.8, rationale="Good domain knowledge"),
            foundation_do=VectorState(score=0.8, rationale="High capability"),
            foundation_context=VectorState(score=0.8, rationale="Good context understanding"),
            comprehension_clarity=VectorState(score=0.8, rationale="Task is clear"),
            comprehension_coherence=VectorState(score=0.9, rationale="High coherence"),
            comprehension_signal=VectorState(score=0.8, rationale="Clear priorities"),
            comprehension_density=VectorState(score=0.2, rationale="Low information density"),
            execution_state=VectorState(score=0.8, rationale="Good state awareness"),
            execution_change=VectorState(score=0.85, rationale="Good change tracking"),
            execution_completion=VectorState(score=0.8, rationale="Clear completion criteria"),
            execution_impact=VectorState(score=0.8, rationale="Good impact understanding"),
            uncertainty=VectorState(score=0.1, rationale="Very low uncertainty"),
        )
        
        conversation_context = "Complex system architecture improvement"
        high_engagement_goals = asyncio.run(orchestrator.orchestrate_goals(
            conversation_context,
            high_engagement_assessment
        ))
        
        # At least some goals should have high autonomy level
        if high_engagement_goals:
            # For high engagement (0.85), should use COLLABORATIVE_INTELLIGENCE
            high_autonomy_goals = [g for g in high_engagement_goals 
                                   if g.autonomy_level == GoalAutonomyLevel.COLLABORATIVE_INTELLIGENCE]
            assert len(high_autonomy_goals) > 0
        
        # Test low engagement (should lead to low autonomy)
        low_engagement_assessment = EpistemicAssessment(
            engagement=VectorState(score=0.3, rationale="Low collaborative engagement"),
            foundation_know=VectorState(score=0.7, rationale="Good domain knowledge"),
            foundation_do=VectorState(score=0.7, rationale="High capability"),
            foundation_context=VectorState(score=0.7, rationale="Good context understanding"),
            comprehension_clarity=VectorState(score=0.7, rationale="Task is clear"),
            comprehension_coherence=VectorState(score=0.8, rationale="High coherence"),
            comprehension_signal=VectorState(score=0.7, rationale="Clear priorities"),
            comprehension_density=VectorState(score=0.3, rationale="Low information density"),
            execution_state=VectorState(score=0.7, rationale="Good state awareness"),
            execution_change=VectorState(score=0.75, rationale="Good change tracking"),
            execution_completion=VectorState(score=0.7, rationale="Clear completion criteria"),
            execution_impact=VectorState(score=0.7, rationale="Good impact understanding"),
            uncertainty=VectorState(score=0.3, rationale="Moderate uncertainty"),
        )
        
        low_engagement_goals = asyncio.run(orchestrator.orchestrate_goals(
            conversation_context,
            low_engagement_assessment
        ))
        
        # For low engagement (0.3), should use DIRECTED_EXECUTION
        if low_engagement_goals:
            directed_execution_goals = [g for g in low_engagement_goals 
                                       if g.autonomy_level == GoalAutonomyLevel.DIRECTED_EXECUTION]
            assert len(directed_execution_goals) > 0
    
    def test_goal_generation_with_clarity_issues(self):
        """Test goal generation when clarity is low."""
        orchestrator = CanonicalGoalOrchestrator(use_placeholder=True)
        
        # Create assessment with low clarity
        low_clarity_assessment = EpistemicAssessment(
            engagement=VectorState(score=0.7, rationale="Good engagement"),
            foundation_know=VectorState(score=0.8, rationale="Good domain knowledge"),
            foundation_do=VectorState(score=0.8, rationale="High capability"),
            foundation_context=VectorState(score=0.7, rationale="Good context understanding"),
            comprehension_clarity=VectorState(score=0.4, rationale="Task requirements are unclear"),  # Low clarity
            comprehension_coherence=VectorState(score=0.8, rationale="High coherence"),
            comprehension_signal=VectorState(score=0.7, rationale="Clear priorities"),
            comprehension_density=VectorState(score=0.3, rationale="Low information density"),
            execution_state=VectorState(score=0.7, rationale="Good state awareness"),
            execution_change=VectorState(score=0.75, rationale="Good change tracking"),
            execution_completion=VectorState(score=0.7, rationale="Clear completion criteria"),
            execution_impact=VectorState(score=0.8, rationale="Good impact understanding"),
            uncertainty=VectorState(score=0.4, rationale="Some uncertainty due to clarity issues"),
        )
        
        conversation_context = "Unclear requirements for database migration"
        goals = asyncio.run(orchestrator.orchestrate_goals(
            conversation_context,
            low_clarity_assessment
        ))
        
        # Should have goals focused on clarification
        clarification_goals = [g for g in goals 
                              if "clarify" in g.goal.lower() or g.action_type == "CLARIFY"]
        assert len(clarification_goals) > 0
        
        # Verify high priority for clarity-focused goals
        high_priority_clarification = [g for g in clarification_goals if g.priority >= 8]
        assert len(high_priority_clarification) > 0
    
    def test_goal_generation_with_knowledge_gaps(self):
        """Test goal generation when there are knowledge gaps."""
        orchestrator = CanonicalGoalOrchestrator(use_placeholder=True)
        
        # Create assessment with low knowledge
        low_knowledge_assessment = EpistemicAssessment(
            engagement=VectorState(score=0.75, rationale="Good engagement"),
            foundation_know=VectorState(score=0.4, rationale="Limited domain knowledge"),  # Low knowledge
            foundation_do=VectorState(score=0.7, rationale="High capability for investigation"),
            foundation_context=VectorState(score=0.7, rationale="Good context understanding"),
            comprehension_clarity=VectorState(score=0.8, rationale="Task is clear"),
            comprehension_coherence=VectorState(score=0.8, rationale="High coherence"),
            comprehension_signal=VectorState(score=0.7, rationale="Clear priorities"),
            comprehension_density=VectorState(score=0.3, rationale="Low information density"),
            execution_state=VectorState(score=0.7, rationale="Good state awareness"),
            execution_change=VectorState(score=0.75, rationale="Good change tracking"),
            execution_completion=VectorState(score=0.7, rationale="Clear completion criteria"),
            execution_impact=VectorState(score=0.7, rationale="Good impact understanding"),
            uncertainty=VectorState(score=0.5, rationale="High uncertainty due to knowledge gaps"),
        )
        
        conversation_context = "Complex machine learning model implementation"
        goals = asyncio.run(orchestrator.orchestrate_goals(
            conversation_context,
            low_knowledge_assessment
        ))
        
        # Should have goals focused on investigation
        investigation_goals = [g for g in goals 
                              if "investigate" in g.goal.lower() or g.action_type == "INVESTIGATE"]
        assert len(investigation_goals) > 0
    
    def test_goal_generation_without_assessment(self):
        """Test goal generation when no assessment is provided."""
        orchestrator = CanonicalGoalOrchestrator(use_placeholder=True)
        
        conversation_context = "User requested help with a task"
        goals = asyncio.run(orchestrator.orchestrate_goals(
            conversation_context,
            epistemic_assessment=None
        ))
        
        # Should have at least one goal for understanding the task
        assert len(goals) > 0
        understanding_goals = [g for g in goals 
                              if "understand" in g.goal.lower() or "task" in g.goal.lower()]
        assert len(understanding_goals) > 0
    
    def test_placeholder_goal_generation_logic(self):
        """Test the placeholder goal generation logic."""
        orchestrator = CanonicalGoalOrchestrator(use_placeholder=True)
        
        # Test internal placeholder method directly
        conversation_context = "User wants to optimize database queries"
        assessment = EpistemicAssessment(
            engagement=VectorState(score=0.7, rationale="Good engagement"),
            foundation_know=VectorState(score=0.5, rationale="Some knowledge gaps in optimization"),
            foundation_do=VectorState(score=0.6, rationale="Moderate capability"),
            foundation_context=VectorState(score=0.6, rationale="Context partially understood"),
            comprehension_clarity=VectorState(score=0.65, rationale="Task is somewhat clear"),
            comprehension_coherence=VectorState(score=0.7, rationale="Request is coherent"),
            comprehension_signal=VectorState(score=0.6, rationale="Priorities identified"),
            comprehension_density=VectorState(score=0.4, rationale="Manageable information load"),
            execution_state=VectorState(score=0.5, rationale="Environment mapping incomplete"),
            execution_change=VectorState(score=0.6, rationale="Change tracking capability moderate"),
            execution_completion=VectorState(score=0.5, rationale="Completion criteria unclear"),
            execution_impact=VectorState(score=0.65, rationale="Impact understanding moderate"),
            uncertainty=VectorState(score=0.4, rationale="Some uncertainty about best approach"),
        )
        
        current_state = {"database_type": "PostgreSQL", "performance_requirements": "high"}
        
        goals = orchestrator._placeholder_goal_generation(
            conversation_context,
            assessment,
            current_state
        )
        
        assert len(goals) > 0
        for goal in goals:
            assert isinstance(goal, Goal)
            assert goal.goal
            assert goal.priority >= 1 and goal.priority <= 10
            assert goal.autonomy_level in GoalAutonomyLevel
            assert goal.reasoning
    
    def test_goal_structure(self):
        """Test that goals have the correct structure."""
        goal = Goal(
            goal="Implement user authentication system",
            priority=9,
            action_type="ACT",
            autonomy_level=GoalAutonomyLevel.COLLABORATIVE_INTELLIGENCE,
            reasoning="High engagement and confidence allow for autonomous implementation",
            estimated_time="2-3 hours",
            dependencies=["install dependencies"],
            success_criteria="Authentication system works correctly",
            requires_approval=False,
            context_factors={"security": "high", "usability": "important"}
        )
        
        # Test to_dict method
        goal_dict = goal.to_dict()
        
        assert goal_dict['goal'] == "Implement user authentication system"
        assert goal_dict['priority'] == 9
        assert goal_dict['action_type'] == "ACT"
        assert goal_dict['autonomy_level'] == "collaborative_intelligence"
        assert goal_dict['reasoning'] == "High engagement and confidence allow for autonomous implementation"
        assert goal_dict['estimated_time'] == "2-3 hours"
        assert goal_dict['dependencies'] == ["install dependencies"]
        assert goal_dict['success_criteria'] == "Authentication system works correctly"
        assert goal_dict['requires_approval'] is False
        assert goal_dict['context_factors'] == {"security": "high", "usability": "important"}