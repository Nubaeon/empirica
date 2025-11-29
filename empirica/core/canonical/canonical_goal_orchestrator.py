#!/usr/bin/env python3
"""
Canonical Goal Orchestrator - Configurable Goal Generation

This orchestrator generates goals based on epistemic state.

Two modes available:
- LLM mode (use_placeholder=False): AI reasoning via llm_callback
  Uses genuine LLM reasoning based on conversation context and epistemic state
- Heuristic mode (use_placeholder=True): Threshold-based generation (default)
  Uses hardcoded thresholds for performance and simplicity

Philosophy: Goals can emerge from understanding (LLM) or patterns (heuristics).
"""

import time
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

# Import canonical components
try:
    from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema
    from .reflex_frame import Action
    # Use NEW schema
    EpistemicAssessment = EpistemicAssessmentSchema
    CANONICAL_AVAILABLE = True
except ImportError:
    try:
        from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema
        from reflex_frame import Action
        EpistemicAssessment = EpistemicAssessmentSchema
        CANONICAL_AVAILABLE = True
    except ImportError:
        # Fallback: create placeholder types
        CANONICAL_AVAILABLE = False
        EpistemicAssessment = Any
        Action = Any

# Import centralized thresholds
try:
    from ..thresholds import GOAL_CONFIDENCE_THRESHOLD
except ImportError:
    # Fallback: use default value
    GOAL_CONFIDENCE_THRESHOLD = 0.70


class GoalPriority(Enum):
    """Goal priority levels"""
    CRITICAL = 10
    HIGH = 8
    MEDIUM = 6
    LOW = 4
    MINIMAL = 2


class GoalAutonomyLevel(Enum):
    """How much autonomy AI has for this goal"""
    COLLABORATIVE_INTELLIGENCE = "collaborative_intelligence"  # High autonomy, AI self-manages
    ACTIVE_COLLABORATION = "active_collaboration"              # Moderate autonomy, give-and-take
    GUIDED_ASSISTANCE = "guided_assistance"                    # Low autonomy, user-directed
    DIRECTED_EXECUTION = "directed_execution"                  # Minimal autonomy, strict instructions


@dataclass
class Goal:
    """A single goal with LLM-generated reasoning"""
    
    goal: str                           # What to accomplish
    priority: int                       # 1-10 priority level
    action_type: str                    # INVESTIGATE, CLARIFY, ACT, etc.
    autonomy_level: GoalAutonomyLevel   # How much autonomy
    reasoning: str                      # LLM's reasoning for this goal
    
    # Optional metadata
    estimated_time: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    success_criteria: Optional[str] = None
    requires_approval: bool = False
    context_factors: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'goal': self.goal,
            'priority': self.priority,
            'action_type': self.action_type,
            'autonomy_level': self.autonomy_level.value,
            'reasoning': self.reasoning,
            'estimated_time': self.estimated_time,
            'dependencies': self.dependencies,
            'success_criteria': self.success_criteria,
            'requires_approval': self.requires_approval,
            'context_factors': self.context_factors
        }


class CanonicalGoalOrchestrator:
    """
    LLM-powered goal orchestration with ENGAGEMENT-driven autonomy
    
    NO heuristics, NO keyword matching, NO hardcoded templates.
    Pure LLM reasoning based on epistemic assessment.
    """
    
    def __init__(self, llm_client=None, llm_callback=None, use_placeholder: bool = True):
        """
        Initialize orchestrator
        
        Args:
            llm_client: LLM client for generating goals (optional, legacy)
            llm_callback: Function(prompt: str) -> str for AI reasoning (preferred)
            use_placeholder: If True, use placeholder simulation (for testing)
                           If False, requires llm_client or llm_callback
        """
        self.llm_client = llm_client
        self.llm_callback = llm_callback
        self.use_placeholder = use_placeholder
        
        # Validate: if not using placeholder, need callback or client
        if not use_placeholder and not llm_callback and not llm_client:
            raise ValueError(
                "When use_placeholder=False, must provide llm_callback or llm_client. "
                "llm_callback is preferred: a function that takes a prompt (str) and returns AI response (str)."
            )
        
        if not CANONICAL_AVAILABLE:
            logger.warning("Canonical components not available, functionality limited")
    
    async def orchestrate_goals(self,
                                conversation_context: str,
                                epistemic_assessment: Optional[EpistemicAssessment] = None,
                                current_state: Optional[Dict[str, Any]] = None) -> List[Goal]:
        """
        Generate goals using LLM reasoning based on epistemic state
        
        Args:
            conversation_context: Text describing the conversation/situation
            epistemic_assessment: Full 12-vector assessment (optional)
            current_state: Additional context about current state
        
        Returns:
            List of Goal objects with LLM-generated reasoning
        """
        
        # Build meta-prompt for goal generation
        meta_prompt = self._build_goal_orchestration_prompt(
            conversation_context,
            epistemic_assessment,
            current_state
        )
        
        # Generate goals using LLM, callback, or placeholder
        if self.use_placeholder or (not self.llm_callback and not self.llm_client):
            goals = self._placeholder_goal_generation(
                conversation_context,
                epistemic_assessment,
                current_state
            )
        elif self.llm_callback:
            # Use callback (synchronous function)
            llm_response = self.llm_callback(meta_prompt)
            goals = self._parse_llm_goal_response(llm_response)
        else:
            # Use llm_client (async)
            llm_response = await self.llm_client.generate(meta_prompt)
            goals = self._parse_llm_goal_response(llm_response)
        
        return goals
    
    def _build_goal_orchestration_prompt(self,
                                        conversation_context: str,
                                        epistemic_assessment: Optional[EpistemicAssessment],
                                        current_state: Optional[Dict[str, Any]]) -> str:
        """Build meta-prompt for LLM-powered goal generation"""
        
        prompt_parts = [
            "# Goal Orchestration Task\n",
            "You are generating goals for an AI agent based on the current conversation and epistemic state.\n\n",
            f"## Conversation Context:\n{conversation_context}\n\n"
        ]
        
        # Add epistemic assessment
        if epistemic_assessment:
            prompt_parts.append(self._format_epistemic_state(epistemic_assessment))
        else:
            prompt_parts.append("## Epistemic State:\nNot provided. Use moderate autonomy (ACTIVE_COLLABORATION).\n\n")
        
        # Add current state
        if current_state:
            prompt_parts.append(f"## Current State:\n{json.dumps(current_state, indent=2)}\n\n")
        
        # Add instructions
        prompt_parts.append(self._get_goal_generation_instructions())
        
        return "".join(prompt_parts)
    
    def _format_epistemic_state(self, assessment: EpistemicAssessment) -> str:
        """Format epistemic assessment for prompt"""
        
        engagement = assessment.engagement.score
        
        # Determine autonomy guidance
        if engagement >= 0.80:
            autonomy_guidance = """
**AUTONOMY LEVEL: COLLABORATIVE_INTELLIGENCE** (High Engagement)
The AI should self-manage goals with the user as a collaborative partner.
- High autonomy: AI can propose and pursue goals independently
- User is consulted on major decisions but AI takes initiative
- Co-creative amplification: Build on ideas together
"""
        elif engagement >= 0.60:
            autonomy_guidance = """
**AUTONOMY LEVEL: ACTIVE_COLLABORATION** (Moderate Engagement)
The AI should work in give-and-take partnership with the user.
- Moderate autonomy: AI proposes goals, user provides direction
- Balanced collaboration: Neither party dominates
- Mutual enhancement: Both contribute meaningfully
"""
        elif engagement >= 0.40:
            autonomy_guidance = """
**AUTONOMY LEVEL: GUIDED_ASSISTANCE** (Low Engagement)
The AI should provide support under user direction.
- Low autonomy: User leads, AI follows
- User-directed: Clear instructions expected
- Supportive role: Help achieve user's goals
"""
        else:
            autonomy_guidance = """
**AUTONOMY LEVEL: DIRECTED_EXECUTION** (Minimal Engagement)
The AI should strictly follow explicit instructions.
- Minimal autonomy: No initiative without permission
- Instruction-following: Wait for clear directions
- No assumptions: Clarify before acting
"""
        
        return f"""## Epistemic State (12-Vector Assessment):

**ENGAGEMENT** (Collaborative Intelligence): {engagement:.2f}
Rationale: {assessment.engagement.rationale}

**FOUNDATION** (35% weight):
- KNOW (Domain Knowledge): {assessment.know.score:.2f}
- DO (Capability): {assessment.do.score:.2f}
- CONTEXT (Environmental Validity): {assessment.context.score:.2f}

**COMPREHENSION** (25% weight):
- CLARITY (Task Clarity): {assessment.clarity.score:.2f}
- COHERENCE (Logical Consistency): {assessment.coherence.score:.2f}
- SIGNAL (Priority Identification): {assessment.signal.score:.2f}
- DENSITY (Information Load): {assessment.density.score:.2f}

**EXECUTION** (25% weight):
- STATE (Environment Mapping): {assessment.state.score:.2f}
- CHANGE (Modification Tracking): {assessment.change.score:.2f}
- COMPLETION (Goal Proximity): {assessment.completion.score:.2f}
- IMPACT (Consequence Understanding): {assessment.impact.score:.2f}

**Overall Confidence**: {assessment.overall_confidence:.2f}
**Recommended Action**: {assessment.recommended_action.value}

{autonomy_guidance}
"""
    
    def _get_goal_generation_instructions(self) -> str:
        """Get instructions for LLM goal generation"""
        
        return """## Your Task:

Generate 1-5 goals for the AI agent based on the above context and epistemic state.

For each goal, provide:
1. **Goal**: Clear, actionable objective
2. **Priority**: 1-10 (10 = critical, 1 = minimal)
3. **Action Type**: INVESTIGATE, CLARIFY, ACT, LEARN, or RESET
4. **Autonomy Level**: Based on ENGAGEMENT (see guidance above)
5. **Reasoning**: Your genuine reasoning for this goal (2-3 sentences)
6. **Estimated Time**: Rough time estimate (optional)
7. **Success Criteria**: How to know goal is accomplished (optional)
8. **Dependencies**: What must happen first (optional)

## Response Format (JSON):

```json
{
  "goals": [
    {
      "goal": "Clear description of what to accomplish",
      "priority": 8,
      "action_type": "INVESTIGATE",
      "autonomy_level": "active_collaboration",
      "reasoning": "Your genuine reasoning for why this goal matters.",
      "estimated_time": "10-15 minutes",
      "success_criteria": "How to know this is complete",
      "dependencies": [],
      "requires_approval": false
    }
  ]
}
```

## Important Principles:

1. **No Templates**: Don't use hardcoded goal templates. Generate based on understanding.
2. **Genuine Reasoning**: Your reasoning should reflect actual analysis of the situation.
3. **ENGAGEMENT-Driven**: Autonomy level must match ENGAGEMENT score.
4. **Address Gaps**: Focus on epistemic gaps (low KNOW, DO, CONTEXT, CLARITY, etc.)
5. **Actionable**: Goals should be specific and achievable.
6. **Prioritize**: Critical needs get high priority, nice-to-haves get low priority.

Generate the goals now:
"""
    
    def _placeholder_goal_generation(self,
                                    conversation_context: str,
                                    epistemic_assessment: Optional[EpistemicAssessment],
                                    current_state: Optional[Dict[str, Any]]) -> List[Goal]:
        """
        Placeholder goal generation (for testing without LLM)
        
        This simulates what the LLM would generate, using simple logic
        based on the epistemic assessment (not hardcoded keywords).
        """
        
        goals = []
        
        # Determine autonomy level from ENGAGEMENT
        if epistemic_assessment and epistemic_assessment.engagement:
            engagement_score = epistemic_assessment.engagement.score
            
            if engagement_score >= 0.80:
                autonomy = GoalAutonomyLevel.COLLABORATIVE_INTELLIGENCE
            elif engagement_score >= 0.60:
                autonomy = GoalAutonomyLevel.ACTIVE_COLLABORATION
            elif engagement_score >= 0.40:
                autonomy = GoalAutonomyLevel.GUIDED_ASSISTANCE
            else:
                autonomy = GoalAutonomyLevel.DIRECTED_EXECUTION
        else:
            autonomy = GoalAutonomyLevel.ACTIVE_COLLABORATION
        
        # Generate goals based on epistemic gaps (not keywords!)
        if epistemic_assessment:
            # Low CLARITY → need clarification
            if epistemic_assessment.clarity.score < 0.60:
                goals.append(Goal(
                    goal="Clarify task requirements and user expectations",
                    priority=9,
                    action_type="CLARIFY",
                    autonomy_level=autonomy,
                    reasoning=f"CLARITY vector is {epistemic_assessment.clarity.score:.2f} (below 0.60). Rationale: {epistemic_assessment.clarity.rationale}. Need clarification before proceeding.",
                    estimated_time="5-10 minutes",
                    success_criteria="Clear understanding of task requirements",
                    requires_approval=False
                ))
            
            # Low KNOW → need investigation
            if epistemic_assessment.know.score < GOAL_CONFIDENCE_THRESHOLD:
                goals.append(Goal(
                    goal="Investigate domain knowledge and gather necessary information",
                    priority=8,
                    action_type="INVESTIGATE",
                    autonomy_level=autonomy,
                    reasoning=f"KNOW vector is {epistemic_assessment.know.score:.2f} (below {GOAL_CONFIDENCE_THRESHOLD:.2f}). Rationale: {epistemic_assessment.know.rationale}. Knowledge gap needs addressing.",
                    estimated_time="10-20 minutes",
                    success_criteria="Sufficient domain knowledge to proceed confidently"
                ))
            
            # Low CONTEXT → need environment mapping
            if epistemic_assessment.context.score < GOAL_CONFIDENCE_THRESHOLD:
                goals.append(Goal(
                    goal="Map environmental context and validate assumptions",
                    priority=7,
                    action_type="INVESTIGATE",
                    autonomy_level=autonomy,
                    reasoning=f"CONTEXT vector is {epistemic_assessment.context.score:.2f} (below {GOAL_CONFIDENCE_THRESHOLD:.2f}). Rationale: {epistemic_assessment.context.rationale}. Environmental understanding needed.",
                    estimated_time="10-15 minutes",
                    success_criteria="Clear understanding of working environment"
                ))
            
            # Overall confidence met → proceed to action
            if epistemic_assessment.overall_confidence >= GOAL_CONFIDENCE_THRESHOLD:
                goals.append(Goal(
                    goal="Execute the task based on current understanding",
                    priority=10,
                    action_type="ACT",
                    autonomy_level=autonomy,
                    reasoning=f"Overall confidence is {epistemic_assessment.overall_confidence:.2f} (above threshold). All vectors assessed. Ready to proceed with action.",
                    estimated_time="Variable",
                    success_criteria="Task completed successfully"
                ))
        else:
            # No assessment → default to clarification
            goals.append(Goal(
                goal="Understand the task and gather context",
                priority=8,
                action_type="CLARIFY",
                autonomy_level=autonomy,
                reasoning="No epistemic assessment available. Need to understand the situation before proceeding.",
                estimated_time="5-10 minutes",
                success_criteria="Clear task understanding"
            ))
        
        return goals
    
    def _parse_llm_goal_response(self, llm_response: str) -> List[Goal]:
        """Parse LLM response into Goal objects"""
        
        try:
            # Extract JSON from response
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in LLM response")
            
            json_str = llm_response[json_start:json_end]
            response_data = json.loads(json_str)
            
            goals = []
            for goal_data in response_data.get('goals', []):
                # Parse autonomy level
                autonomy_str = goal_data.get('autonomy_level', 'active_collaboration')
                autonomy = GoalAutonomyLevel(autonomy_str)
                
                goal = Goal(
                    goal=goal_data['goal'],
                    priority=goal_data['priority'],
                    action_type=goal_data['action_type'],
                    autonomy_level=autonomy,
                    reasoning=goal_data['reasoning'],
                    estimated_time=goal_data.get('estimated_time'),
                    dependencies=goal_data.get('dependencies', []),
                    success_criteria=goal_data.get('success_criteria'),
                    requires_approval=goal_data.get('requires_approval', False),
                    context_factors=goal_data.get('context_factors', {})
                )
                goals.append(goal)
            
            return goals
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM goal response: {e}")
            # Return fallback goal
            return [Goal(
                goal="Review LLM response and generate goals manually",
                priority=5,
                action_type="CLARIFY",
                autonomy_level=GoalAutonomyLevel.ACTIVE_COLLABORATION,
                reasoning=f"LLM response parsing failed: {e}. Manual review needed.",
                requires_approval=True
            )]


# Convenience function
def create_goal_orchestrator(llm_client=None, llm_callback=None, use_placeholder: bool = True) -> CanonicalGoalOrchestrator:
    """
    Create and return a CanonicalGoalOrchestrator instance
    
    Args:
        llm_client: LLM client (legacy, async)
        llm_callback: Function(prompt: str) -> str for AI reasoning (preferred)
        use_placeholder: If True, use threshold-based goals (default)
                        If False, use llm_callback or llm_client for AI reasoning
    
    Returns:
        CanonicalGoalOrchestrator instance
        
    Examples:
        # Threshold-based mode (default)
        orchestrator = create_goal_orchestrator(use_placeholder=True)
        
        # AI reasoning mode with callback
        def my_llm(prompt: str) -> str:
            return ai_client.reason(prompt)
        
        orchestrator = create_goal_orchestrator(
            llm_callback=my_llm,
            use_placeholder=False
        )
    """
    return CanonicalGoalOrchestrator(llm_client, llm_callback, use_placeholder)


if __name__ == "__main__":
    # Test the orchestrator
    logger.info("Testing Canonical Goal Orchestrator")
    
    orchestrator = CanonicalGoalOrchestrator(use_placeholder=True)
    
    # Test with simple context
    conversation = "User asked to refactor the authentication module for better security"
    
    # Simulate epistemic assessment (would normally come from CanonicalEpistemicAssessor)
    class MockAssessment:
        def __init__(self):
            from dataclasses import dataclass
            
            @dataclass
            class Vector:
                score: float
                rationale: str
            
            self.engagement = Vector(0.75, "Active collaboration detected")
            self.know = Vector(0.65, "Some domain knowledge, but gaps remain")
            self.do = Vector(0.80, "High capability for refactoring")
            self.context = Vector(0.70, "Good understanding of environment")
            self.clarity = Vector(0.85, "Task is well-defined")
            self.coherence = Vector(0.90, "Request is logically consistent")
            self.signal = Vector(0.80, "Clear priority: security")
            self.density = Vector(0.60, "Manageable information load")
            self.state = Vector(0.75, "Environment well-mapped")
            self.change = Vector(0.70, "Can track modifications")
            self.completion = Vector(0.50, "Task just starting")
            self.impact = Vector(0.80, "Understand consequences")
            self.overall_confidence = 0.72
            
            class ActionEnum:
                value = "INVESTIGATE"
            
            self.recommended_action = ActionEnum()
    
    mock_assessment = MockAssessment()
    
    # Generate goals
    goals = asyncio.run(orchestrator.orchestrate_goals(
        conversation,
        mock_assessment,
        {'available_tools': ['read', 'write', 'edit']}
    ))
    
    logger.info(f"Generated {len(goals)} goals:")
    for i, goal in enumerate(goals, 1):
        logger.info(f"Goal {i}: {goal.goal}")
        logger.info(f"  Priority: {goal.priority}/10")
        logger.info(f"  Action: {goal.action_type}")
        logger.info(f"  Autonomy: {goal.autonomy_level.value}")
        logger.info(f"  Reasoning: {goal.reasoning}")
    
    logger.info("Canonical Goal Orchestrator test complete")
