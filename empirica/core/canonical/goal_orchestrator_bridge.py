#!/usr/bin/env python3
"""
Goal Orchestrator Bridge

Bridges canonical_goal_orchestrator (LLM-driven goal generation) with
new Goal Architecture (structured goal management).

Purpose:
- canonical_goal_orchestrator: AI generates goals from conversation + epistemic state
- Goal Architecture: Structured storage, tracking, git notes
- This bridge: Converts LLM-generated goals into structured Goal objects

Flow:
  1. AI agent calls orchestrate_goals() → LLM generates goals
  2. Bridge converts to structured Goal objects
  3. Saves to database with success criteria
  4. Returns goal IDs for tracking
"""

import logging
import uuid
from typing import List, Dict, Any, Optional

from .canonical_goal_orchestrator import Goal as LLMGoal, CanonicalGoalOrchestrator
from empirica.core.goals.types import Goal, SuccessCriterion, ScopeVector
from empirica.core.goals.repository import GoalRepository

logger = logging.getLogger(__name__)


class GoalOrchestratorBridge:
    """
    Bridge between LLM-driven goal generation and structured goal management
    
    Allows autonomous agents to generate goals via LLM, then track them
    with the new structured architecture.
    """
    
    def __init__(
        self,
        orchestrator: CanonicalGoalOrchestrator,
        db_path: Optional[str] = None
    ):
        """
        Initialize bridge
        
        Args:
            orchestrator: Canonical goal orchestrator instance
            db_path: Optional database path
        """
        self.orchestrator = orchestrator
        self.goal_repo = GoalRepository(db_path=db_path)
    
    async def orchestrate_and_save(
        self,
        conversation_context: str,
        session_id: str,
        epistemic_assessment: Optional[Any] = None,
        current_state: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate goals via LLM and save to structured architecture
        
        Args:
            conversation_context: Conversation context for LLM
            session_id: Session UUID to associate goals with
            epistemic_assessment: Optional epistemic assessment
            current_state: Optional current state dict
            
        Returns:
            List of dicts with goal_id and original LLM goal data
        """
        # Generate goals via LLM
        llm_goals = await self.orchestrator.orchestrate_goals(
            conversation_context,
            epistemic_assessment,
            current_state
        )
        
        # Convert and save each goal
        saved_goals = []
        
        for llm_goal in llm_goals:
            # Convert to structured Goal
            structured_goal = self._convert_to_structured_goal(llm_goal)
            
            # Save to database
            success = self.goal_repo.save_goal(structured_goal, session_id)
            
            if success:
                saved_goals.append({
                    'goal_id': structured_goal.id,
                    'objective': structured_goal.objective,
                    'priority': llm_goal.priority,
                    'action_type': llm_goal.action_type,
                    'autonomy_level': llm_goal.autonomy_level.value,
                    'reasoning': llm_goal.reasoning
                })
                
                logger.info(
                    f"Saved LLM-generated goal: {structured_goal.id[:8]} - "
                    f"{structured_goal.objective[:50]}..."
                )
            else:
                logger.warning(f"Failed to save goal: {llm_goal.goal}")
        
        return saved_goals
    
    def _convert_to_structured_goal(self, llm_goal: LLMGoal) -> Goal:
        """
        Convert LLM-generated Goal to structured Goal
        
        Args:
            llm_goal: Goal from canonical_goal_orchestrator
            
        Returns:
            Structured Goal object
        """
        # Create success criterion from LLM goal's success_criteria
        success_criteria = []
        
        if llm_goal.success_criteria:
            success_criteria.append(
                SuccessCriterion(
                    id=str(uuid.uuid4()),
                    description=llm_goal.success_criteria,
                    validation_method="completion",
                    is_required=True
                )
            )
        else:
            # Default success criterion
            success_criteria.append(
                SuccessCriterion(
                    id=str(uuid.uuid4()),
                    description="Goal objective achieved",
                    validation_method="completion",
                    is_required=True
                )
            )
        
        # Determine scope from priority
        if llm_goal.priority >= 8:
            scope = ScopeVector(breadth=0.9, duration=0.9, coordination=0.8)  # Project-wide
        elif llm_goal.priority >= 6:
            scope = ScopeVector(breadth=0.6, duration=0.7, coordination=0.4)  # Session-scoped
        else:
            scope = ScopeVector(breadth=0.3, duration=0.2, coordination=0.1)  # Task-specific
        
        # Create structured goal
        structured_goal = Goal.create(
            objective=llm_goal.goal,
            success_criteria=success_criteria,
            scope=scope,
            estimated_complexity=self._map_priority_to_complexity(llm_goal.priority),
            metadata={
                'llm_generated': True,
                'action_type': llm_goal.action_type,
                'autonomy_level': llm_goal.autonomy_level.value,
                'reasoning': llm_goal.reasoning,
                'original_priority': llm_goal.priority,
                'requires_approval': llm_goal.requires_approval,
                'estimated_time': llm_goal.estimated_time,
                'dependencies': llm_goal.dependencies,
                'context_factors': llm_goal.context_factors
            }
        )
        
        return structured_goal
    
    def _map_priority_to_complexity(self, priority: int) -> float:
        """
        Map LLM priority (1-10) to complexity (0.0-1.0)
        
        Args:
            priority: Priority level 1-10
            
        Returns:
            Complexity 0.0-1.0
        """
        # Higher priority often means higher complexity
        # But not always linear - use a curve
        if priority >= 9:
            return 0.9
        elif priority >= 7:
            return 0.7
        elif priority >= 5:
            return 0.5
        elif priority >= 3:
            return 0.3
        else:
            return 0.2
    
    def close(self):
        """Close repository connections"""
        self.goal_repo.close()


def create_orchestrator_with_bridge(
    llm_callback=None,
    use_placeholder: bool = True,
    db_path: Optional[str] = None
) -> GoalOrchestratorBridge:
    """
    Create goal orchestrator with bridge to new architecture
    
    Args:
        llm_callback: LLM callback function
        use_placeholder: Use placeholder mode
        db_path: Optional database path
        
    Returns:
        GoalOrchestratorBridge instance
    """
    orchestrator = CanonicalGoalOrchestrator(
        llm_callback=llm_callback,
        use_placeholder=use_placeholder
    )
    
    return GoalOrchestratorBridge(orchestrator, db_path)
