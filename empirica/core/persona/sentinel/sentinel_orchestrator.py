"""
SentinelOrchestrator - Multi-persona coordination for Empirica

Coordinates multiple PersonaHarness instances to perform multi-perspective
epistemic assessment with COMPOSE and ARBITRATE operations.

Usage:
    orchestrator = SentinelOrchestrator(
        sentinel_id="multi-persona-review",
        composition_strategy="weighted_by_confidence",
        arbitration_strategy="confidence_weighted"
    )

    result = await orchestrator.orchestrate_task(
        task="Review authentication for security and usability",
        personas=["security", "ux"],
        context={"session_id": "abc123"}
    )
"""

import logging
import asyncio
import time
from typing import Dict, List, Optional, Any
from pathlib import Path

from empirica.core.persona.harness.persona_harness import PersonaHarness
from empirica.core.persona.persona_manager import PersonaManager
from empirica.core.persona.persona_profile import PersonaProfile
from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema

from .orchestration_result import OrchestrationResult, ArbitrationResult
from .composition_strategies import get_composition_strategy
from .arbitration_strategies import get_arbitration_strategy

logger = logging.getLogger(__name__)


class SentinelOrchestrator:
    """
    Multi-persona orchestration for epistemic assessment

    Coordinates PersonaHarness instances to get multi-perspective assessment,
    then composes and arbitrates results using COMPOSE and ARBITRATE operations.

    Attributes:
        sentinel_id: Identifier for this orchestrator instance
        composition_strategy: Strategy for merging assessments
        arbitration_strategy: Strategy for resolving conflicts
        personas_dir: Directory for persona configurations
        session_id: Empirica session ID for tracking
    """

    def __init__(
        self,
        sentinel_id: str,
        composition_strategy: str = "weighted_by_confidence",
        arbitration_strategy: str = "confidence_weighted",
        personas_dir: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        Initialize SentinelOrchestrator

        Args:
            sentinel_id: Identifier for this orchestrator instance
            composition_strategy: How to merge assessments
                ("average", "weighted_by_confidence", "weighted_by_domain")
            arbitration_strategy: How to resolve conflicts
                ("majority_vote", "confidence_weighted", "pessimistic", etc.)
            personas_dir: Custom persona directory (default: .empirica/personas)
            session_id: Empirica session ID for tracking
        """
        self.sentinel_id = sentinel_id
        self.composition_strategy_name = composition_strategy
        self.arbitration_strategy_name = arbitration_strategy
        self.personas_dir = personas_dir
        self.session_id = session_id

        # Get strategy functions
        self.composition_strategy = get_composition_strategy(composition_strategy)
        self.arbitration_strategy = get_arbitration_strategy(arbitration_strategy)

        # Persona manager for loading personas
        self.persona_manager = PersonaManager(personas_dir=personas_dir)

        logger.info(f"✓ SentinelOrchestrator initialized: {sentinel_id}")
        logger.info(f"   Composition: {composition_strategy}")
        logger.info(f"   Arbitration: {arbitration_strategy}")

    async def orchestrate_task(
        self,
        task: str,
        personas: List[str],
        context: Optional[Dict[str, Any]] = None,
        execution_mode: str = "parallel"
    ) -> OrchestrationResult:
        """
        Execute task across multiple personas

        Main orchestration workflow:
        1. Validate personas exist
        2. Create PersonaHarness for each
        3. Execute task (parallel or sequential)
        4. Collect EpistemicAssessmentSchema from each
        5. COMPOSE: Merge assessments
        6. ARBITRATE: Resolve conflicts
        7. Return unified result

        Args:
            task: Task description
            personas: List of persona IDs (e.g., ["security", "ux"])
            context: Optional context (session_id, git_branch, etc.)
            execution_mode: "parallel" or "sequential"

        Returns:
            OrchestrationResult with composed assessment and arbitration

        Raises:
            ValueError: If personas list is empty or persona not found
        """
        if not personas:
            raise ValueError("No personas provided for orchestration")

        start_time = time.time()
        context = context or {}

        logger.info(f"🎯 Orchestrating task across {len(personas)} personas")
        logger.info(f"   Task: {task[:100]}...")
        logger.info(f"   Personas: {personas}")
        logger.info(f"   Execution mode: {execution_mode}")

        # Step 1: Load persona profiles
        persona_profiles = self._load_persona_profiles(personas)

        # Step 2: Create PersonaHarness instances
        persona_harnesses = self._create_persona_harnesses(personas)

        # Step 3: Execute tasks
        if execution_mode == "parallel":
            persona_assessments = await self._execute_parallel(
                persona_harnesses, task, context
            )
        elif execution_mode == "sequential":
            persona_assessments = await self._execute_sequential(
                persona_harnesses, task, context
            )
        else:
            raise ValueError(f"Unknown execution mode: {execution_mode}")

        # Step 4: COMPOSE - Merge assessments
        logger.info(f"📊 COMPOSE: Merging {len(persona_assessments)} assessments")
        composed_assessment = self._compose_assessments(
            persona_assessments,
            persona_profiles,
            task,
            context
        )

        # Step 5: Determine persona actions and confidences
        persona_actions, persona_confidences = self._extract_actions_and_confidences(
            persona_assessments
        )

        # Step 6: ARBITRATE - Resolve conflicts
        logger.info(f"⚖️  ARBITRATE: Resolving potential conflicts")
        arbitration_result = self._arbitrate_conflicts(
            persona_actions,
            persona_confidences,
            persona_assessments,
            persona_profiles,
            task,
            context
        )

        # Step 7: Calculate agreement metrics
        agreement_score = self._calculate_agreement_score(persona_actions)
        conflicts = self._detect_conflicts(persona_actions)

        # Build final result
        execution_time = time.time() - start_time

        result = OrchestrationResult(
            composed_assessment=composed_assessment,
            final_action=arbitration_result.final_action,
            persona_assessments=persona_assessments,
            arbitration_result=arbitration_result,
            personas_used=personas,
            orchestration_strategy=execution_mode,
            composition_strategy=self.composition_strategy_name,
            agreement_score=agreement_score,
            conflicts_detected=conflicts,
            execution_time_seconds=execution_time,
            task=task,
            session_id=self.session_id or context.get("session_id")
        )

        logger.info(f"✓ Orchestration complete in {execution_time:.2f}s")
        logger.info(f"   Final action: {result.final_action}")
        logger.info(f"   Agreement: {agreement_score:.2%}")
        logger.info(f"   Conflicts: {len(conflicts)}")

        return result

    def _load_persona_profiles(self, personas: List[str]) -> Dict[str, PersonaProfile]:
        """Load persona profiles for all personas"""
        profiles = {}
        for persona_id in personas:
            try:
                profiles[persona_id] = self.persona_manager.load_persona(persona_id)
            except Exception as e:
                raise ValueError(f"Failed to load persona '{persona_id}': {e}")
        return profiles

    def _create_persona_harnesses(self, personas: List[str]) -> Dict[str, PersonaHarness]:
        """Create PersonaHarness instances for all personas"""
        harnesses = {}
        for persona_id in personas:
            harnesses[persona_id] = PersonaHarness(
                persona_id=persona_id,
                personas_dir=self.personas_dir,
                enable_sentinel=False  # Disable for orchestration
            )
        return harnesses

    async def _execute_parallel(
        self,
        persona_harnesses: Dict[str, PersonaHarness],
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, EpistemicAssessmentSchema]:
        """
        Execute personas in parallel using asyncio

        Note: Currently PersonaHarness.execute_task may not be async,
        so we wrap in asyncio.to_thread or similar. For now, we'll
        simulate async execution.
        """
        logger.info(f"🔄 Executing {len(persona_harnesses)} personas in parallel")

        # TODO: Once PersonaHarness.execute_task is async, use asyncio.gather
        # For now, execute sequentially but keep the async interface
        assessments = {}
        for persona_id, harness in persona_harnesses.items():
            logger.info(f"   Executing {persona_id}...")
            # Mock execution for now - will be replaced with real PersonaHarness call
            assessment = await self._execute_persona_task(harness, task, context)
            assessments[persona_id] = assessment

        return assessments

    async def _execute_sequential(
        self,
        persona_harnesses: Dict[str, PersonaHarness],
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, EpistemicAssessmentSchema]:
        """Execute personas sequentially"""
        logger.info(f"🔄 Executing {len(persona_harnesses)} personas sequentially")

        assessments = {}
        for persona_id, harness in persona_harnesses.items():
            logger.info(f"   Executing {persona_id}...")
            assessment = await self._execute_persona_task(harness, task, context)
            assessments[persona_id] = assessment

            # In sequential mode, could pass previous results to next persona
            # context['previous_assessments'] = assessments

        return assessments

    async def _execute_persona_task(
        self,
        harness: PersonaHarness,
        task: str,
        context: Dict[str, Any]
    ) -> EpistemicAssessmentSchema:
        """
        Execute task for a single persona

        TODO: Call harness.execute_task() when ready.
        For now, return mock assessment based on persona priors.
        """
        # Mock implementation - will be replaced with real execution
        # return await harness.execute_task(task=task, context=context)

        # For now, create mock assessment from persona priors
        persona = harness.persona
        priors = persona.epistemic_config.priors

        from empirica.core.schemas.epistemic_assessment import VectorAssessment

        def mock_vector(name: str, prior_score: float) -> VectorAssessment:
            return VectorAssessment(
                score=prior_score,
                rationale=f"Mock {persona.persona_id} assessment for {name}",
                evidence=None,
                warrants_investigation=prior_score < 0.5,
                investigation_priority=5 if prior_score < 0.5 else 0
            )

        return EpistemicAssessmentSchema(
            engagement=mock_vector("engagement", priors["engagement"]),
            foundation_know=mock_vector("know", priors["know"]),
            foundation_do=mock_vector("do", priors["do"]),
            foundation_context=mock_vector("context", priors["context"]),
            comprehension_clarity=mock_vector("clarity", priors["clarity"]),
            comprehension_coherence=mock_vector("coherence", priors["coherence"]),
            comprehension_signal=mock_vector("signal", priors["signal"]),
            comprehension_density=mock_vector("density", priors["density"]),
            execution_state=mock_vector("state", priors["state"]),
            execution_change=mock_vector("change", priors["change"]),
            execution_completion=mock_vector("completion", priors["completion"]),
            execution_impact=mock_vector("impact", priors["impact"]),
            uncertainty=mock_vector("uncertainty", priors["uncertainty"])
        )

    def _compose_assessments(
        self,
        persona_assessments: Dict[str, EpistemicAssessmentSchema],
        persona_profiles: Dict[str, PersonaProfile],
        task: str,
        context: Dict[str, Any]
    ) -> EpistemicAssessmentSchema:
        """Apply composition strategy to merge assessments"""
        if self.composition_strategy_name == "weighted_by_domain":
            return self.composition_strategy(
                persona_assessments,
                persona_profiles,
                task=task,
                context=context
            )
        elif self.composition_strategy_name == "weighted_by_confidence":
            return self.composition_strategy(
                persona_assessments,
                persona_profiles
            )
        else:  # average
            return self.composition_strategy(persona_assessments)

    def _extract_actions_and_confidences(
        self,
        persona_assessments: Dict[str, EpistemicAssessmentSchema]
    ) -> tuple[Dict[str, str], Dict[str, float]]:
        """Extract recommended actions and confidences from assessments"""
        persona_actions = {}
        persona_confidences = {}

        for persona_id, assessment in persona_assessments.items():
            # Determine action based on assessment
            action = assessment.determine_action()
            persona_actions[persona_id] = action

            # Calculate confidence (average of foundation tier)
            tier_confidences = assessment.calculate_tier_confidences()
            confidence = tier_confidences["foundation_confidence"]
            persona_confidences[persona_id] = confidence

        return persona_actions, persona_confidences

    def _arbitrate_conflicts(
        self,
        persona_actions: Dict[str, str],
        persona_confidences: Dict[str, float],
        persona_assessments: Dict[str, EpistemicAssessmentSchema],
        persona_profiles: Dict[str, PersonaProfile],
        task: str,
        context: Dict[str, Any]
    ) -> ArbitrationResult:
        """Apply arbitration strategy to resolve conflicts"""
        if self.arbitration_strategy_name == "domain_weighted":
            return self.arbitration_strategy(
                persona_actions,
                persona_confidences,
                persona_assessments,
                persona_profiles,
                task=task,
                context=context
            )
        elif self.arbitration_strategy_name in ["confidence_weighted"]:
            return self.arbitration_strategy(
                persona_actions,
                persona_confidences,
                persona_assessments
            )
        else:  # majority_vote, pessimistic, escalate_on_conflict
            return self.arbitration_strategy(
                persona_actions,
                persona_confidences,
                persona_assessments
            )

    def _calculate_agreement_score(self, persona_actions: Dict[str, str]) -> float:
        """Calculate agreement score (0.0-1.0) based on action consensus"""
        if not persona_actions:
            return 0.0

        from collections import Counter
        vote_counts = Counter(persona_actions.values())
        most_common_count = vote_counts.most_common(1)[0][1]

        return most_common_count / len(persona_actions)

    def _detect_conflicts(self, persona_actions: Dict[str, str]) -> List[str]:
        """Detect and describe conflicts between personas"""
        if len(set(persona_actions.values())) <= 1:
            return []  # No conflict if all agree

        from collections import Counter
        vote_counts = Counter(persona_actions.values())

        conflicts = []
        for action, count in vote_counts.items():
            personas = [pid for pid, act in persona_actions.items() if act == action]
            conflicts.append(f"{count}/{len(persona_actions)} personas voted {action}: {personas}")

        return conflicts
