"""Test Canonical Goal Orchestrator - LLM-based decomposition."""

import asyncio
from empirica.core.canonical.canonical_goal_orchestrator import (
    CanonicalGoalOrchestrator,
    Goal,
    GoalPriority,
    GoalAutonomyLevel
)
from empirica.core.canonical.reflex_frame import EpistemicAssessment, VectorState, Action


class TestCanonicalGoalOrchestrator:
    """Test Goal Orchestrator functionality."""
    
    def test_goal_decomposition(self):
        """Test decomposition of complex goals using LLM reasoning."""
        orchestrator = CanonicalGoalOrchestrator(use_placeholder=True)
        
        conversation_context = "User wants to implement a new feature for user authentication"
        
        # Create a mock epistemic assessment
        assessment = EpistemicAssessment(
            engagement=VectorState(score=0.75, rationale="Active collaboration with user"),
            engagement_gate_passed=True,
            know=VectorState(score=0.6, rationale="Some domain knowledge but with gaps"),
            do=VectorState(score=0.7, rationale="Capable of implementation tasks"),
            context=VectorState(score=0.65, rationale="Environment context understood but needs more details"),
            foundation_confidence=0.65,
            clarity=VectorState(score=0.75, rationale="Task requirements are clear"),
            coherence=VectorState(score=0.8, rationale="Request is logically consistent"),
            signal=VectorState(score=0.7, rationale="Clear priority on security aspects"),
            density=VectorState(score=0.5, rationale="Manageable information load"),
            comprehension_confidence=0.7,
            state=VectorState(score=0.6, rationale="Environment mapping in progress"),
            change=VectorState(score=0.7, rationale="Can track modifications effectively"),
            completion=VectorState(score=0.5, rationale="Task just beginning"),
            impact=VectorState(score=0.75, rationale="Clear understanding of consequences"),
            execution_confidence=0.65,
            uncertainty=VectorState(score=0.3, rationale="Low uncertainty about approach"),
            overall_confidence=0.65,
            recommended_action=Action.PROCEED,
            assessment_id="test_orchestrator"
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
            engagement_gate_passed=True,
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
            recommended_action=Action.PROCEED,
            assessment_id="high_engagement_test"
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
            engagement_gate_passed=False,
            know=VectorState(score=0.7, rationale="Good domain knowledge"),
            do=VectorState(score=0.7, rationale="High capability"),
            context=VectorState(score=0.7, rationale="Good context understanding"),
            foundation_confidence=0.7,
            clarity=VectorState(score=0.7, rationale="Task is clear"),
            coherence=VectorState(score=0.8, rationale="High coherence"),
            signal=VectorState(score=0.7, rationale="Clear priorities"),
            density=VectorState(score=0.3, rationale="Low information density"),
            comprehension_confidence=0.7,
            state=VectorState(score=0.7, rationale="Good state awareness"),
            change=VectorState(score=0.75, rationale="Good change tracking"),
            completion=VectorState(score=0.7, rationale="Clear completion criteria"),
            impact=VectorState(score=0.7, rationale="Good impact understanding"),
            execution_confidence=0.7,
            uncertainty=VectorState(score=0.3, rationale="Moderate uncertainty"),
            overall_confidence=0.7,
            recommended_action=Action.CLARIFY,
            assessment_id="low_engagement_test"
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
            engagement_gate_passed=True,
            know=VectorState(score=0.8, rationale="Good domain knowledge"),
            do=VectorState(score=0.8, rationale="High capability"),
            context=VectorState(score=0.7, rationale="Good context understanding"),
            foundation_confidence=0.75,
            clarity=VectorState(score=0.4, rationale="Task requirements are unclear"),  # Low clarity
            coherence=VectorState(score=0.8, rationale="High coherence"),
            signal=VectorState(score=0.7, rationale="Clear priorities"),
            density=VectorState(score=0.3, rationale="Low information density"),
            comprehension_confidence=0.65,
            state=VectorState(score=0.7, rationale="Good state awareness"),
            change=VectorState(score=0.75, rationale="Good change tracking"),
            completion=VectorState(score=0.7, rationale="Clear completion criteria"),
            impact=VectorState(score=0.8, rationale="Good impact understanding"),
            execution_confidence=0.75,
            uncertainty=VectorState(score=0.4, rationale="Some uncertainty due to clarity issues"),
            overall_confidence=0.72,
            recommended_action=Action.CLARIFY,
            assessment_id="low_clarity_test"
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
            engagement_gate_passed=True,
            know=VectorState(score=0.4, rationale="Limited domain knowledge"),  # Low knowledge
            do=VectorState(score=0.7, rationale="High capability for investigation"),
            context=VectorState(score=0.7, rationale="Good context understanding"),
            foundation_confidence=0.6,
            clarity=VectorState(score=0.8, rationale="Task is clear"),
            coherence=VectorState(score=0.8, rationale="High coherence"),
            signal=VectorState(score=0.7, rationale="Clear priorities"),
            density=VectorState(score=0.3, rationale="Low information density"),
            comprehension_confidence=0.7,
            state=VectorState(score=0.7, rationale="Good state awareness"),
            change=VectorState(score=0.75, rationale="Good change tracking"),
            completion=VectorState(score=0.7, rationale="Clear completion criteria"),
            impact=VectorState(score=0.7, rationale="Good impact understanding"),
            execution_confidence=0.65,
            uncertainty=VectorState(score=0.5, rationale="High uncertainty due to knowledge gaps"),
            overall_confidence=0.65,
            recommended_action=Action.INVESTIGATE,
            assessment_id="low_knowledge_test"
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
            engagement_gate_passed=True,
            know=VectorState(score=0.5, rationale="Some knowledge gaps in optimization"),
            do=VectorState(score=0.6, rationale="Moderate capability"),
            context=VectorState(score=0.6, rationale="Context partially understood"),
            foundation_confidence=0.55,
            clarity=VectorState(score=0.65, rationale="Task is somewhat clear"),
            coherence=VectorState(score=0.7, rationale="Request is coherent"),
            signal=VectorState(score=0.6, rationale="Priorities identified"),
            density=VectorState(score=0.4, rationale="Manageable information load"),
            comprehension_confidence=0.6,
            state=VectorState(score=0.5, rationale="Environment mapping incomplete"),
            change=VectorState(score=0.6, rationale="Change tracking capability moderate"),
            completion=VectorState(score=0.5, rationale="Completion criteria unclear"),
            impact=VectorState(score=0.65, rationale="Impact understanding moderate"),
            execution_confidence=0.55,
            uncertainty=VectorState(score=0.4, rationale="Some uncertainty about best approach"),
            overall_confidence=0.58,
            recommended_action=Action.INVESTIGATE,
            assessment_id="placeholder_test"
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