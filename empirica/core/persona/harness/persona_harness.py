"""
PersonaHarness - Runtime container for persona execution

The PersonaHarness wraps the CanonicalEpistemicCascade with persona-specific behavior:
1. Loads PersonaProfile configuration
2. Initializes epistemic state with persona priors
3. Runs CASCADE with persona-specific thresholds and weights
4. Reports progress to Sentinel
5. Handles messages from Sentinel (PROCEED, TERMINATE, etc.)

Usage:
    harness = PersonaHarness("security_expert")
    result = await harness.execute_task(
        task="Review authentication for vulnerabilities",
        git_branch="feature/auth"
    )
"""

import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, UTC

from ..persona_manager import PersonaManager
from ..persona_profile import PersonaProfile
from .communication import (
    PersonaMessage,
    SentinelMessage,
    MessageType,
    send_message,
    receive_message
)

# NEW SCHEMA IMPORTS (Phase 4: Schema Migration)
from empirica.core.schemas.epistemic_assessment import (
    EpistemicAssessmentSchema,
    VectorAssessment
)
# Using EpistemicAssessmentSchema directly

logger = logging.getLogger(__name__)


class PersonaHarness:
    """
    Runtime container for persona execution

    Wraps CASCADE with persona-specific:
    - Priors (initial epistemic state)
    - Thresholds (uncertainty_trigger, confidence_to_proceed)
    - Weights (foundation/comprehension/execution)
    - Focus domains (what to pay attention to)
    - Sentinel communication (progress reporting)
    """

    def __init__(
        self,
        persona_id: str,
        personas_dir: Optional[str] = None,
        sentinel_endpoint: Optional[str] = None,
        enable_sentinel: bool = True
    ):
        """
        Initialize PersonaHarness

        Args:
            persona_id: Persona identifier to load
            personas_dir: Custom persona directory (default: .empirica/personas)
            sentinel_endpoint: Sentinel communication endpoint
            enable_sentinel: Enable Sentinel communication (default: True)
        """
        self.persona_id = persona_id
        self.enable_sentinel = enable_sentinel
        self.sentinel_endpoint = sentinel_endpoint or ".empirica/messages"

        # Load persona configuration
        manager = PersonaManager(personas_dir=personas_dir)
        self.persona = manager.load_persona(persona_id)

        logger.info(f"✓ PersonaHarness initialized: {self.persona.name}")
        logger.info(f"   Type: {self.persona.get_type()}")
        logger.info(f"   Sentinel: {'enabled' if enable_sentinel else 'disabled'}")

        # Load signing identity (Phase 2 integration)
        from empirica.core.identity import AIIdentity

        self.identity = AIIdentity(ai_id=self.persona.signing_identity.identity_name)
        try:
            self.identity.load_keypair()
            logger.info(f"   ✓ Identity loaded: {self.persona.signing_identity.identity_name}")
        except FileNotFoundError:
            logger.warning(f"   ⚠️  Identity not found, generating new keypair")
            self.identity.generate_keypair()
            self.identity.save_keypair()

        # Execution state
        self.current_task = None
        self.cascade_instance = None

    async def execute_task(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        git_branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute task using persona-specific CASCADE

        Args:
            task: Task description
            context: Additional context
            git_branch: Git branch for checkpoints

        Returns:
            Dict with action, confidence, rationale, and findings
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🎭 Persona: {self.persona.name} ({self.persona.get_type()})")
        logger.info(f"📋 Task: {task[:60]}...")
        logger.info(f"{'='*70}\n")

        self.current_task = task

        # Notify Sentinel of task start
        if self.enable_sentinel:
            await self._report_to_sentinel(
                MessageType.STATUS_REPORT,
                {
                    "phase": "STARTED",
                    "task": task,
                    "confidence": self.persona.epistemic_config.priors.get('engagement', 0.7)
                }
            )

        # Build context with persona information
        if context is None:
            context = {}

        context['persona'] = {
            'persona_id': self.persona.persona_id,
            'type': self.persona.get_type(),
            'focus_domains': self.persona.epistemic_config.focus_domains[:5]
        }

        if git_branch:
            context['git_branch'] = git_branch

        try:
            # Initialize CASCADE with persona-specific configuration
            cascade = self._create_persona_cascade()
            self.cascade_instance = cascade

            # Run CASCADE with persona awareness
            result = await cascade.run_epistemic_cascade(task, context)

            # Apply persona-specific interpretation
            interpreted_result = self._interpret_with_persona(result)

            # Report completion to Sentinel
            if self.enable_sentinel:
                await self._report_to_sentinel(
                    MessageType.COMPLETION_REPORT,
                    {
                        "action": interpreted_result['action'],
                        "confidence": interpreted_result['confidence'],
                        "findings": interpreted_result.get('persona_findings', []),
                        "recommendation": interpreted_result.get('persona_recommendation', '')
                    }
                )

            return interpreted_result

        except Exception as e:
            logger.error(f"❌ Persona execution failed: {e}")

            # Report error to Sentinel
            if self.enable_sentinel:
                await self._report_to_sentinel(
                    MessageType.ERROR_REPORT,
                    {
                        "error": str(e),
                        "task": task
                    }
                )

            raise

    def _create_persona_cascade(self):
        """
        Create CASCADE instance with persona-specific configuration

        Overrides:
        - Thresholds (uncertainty_trigger, confidence_to_proceed)
        - Weights (foundation/comprehension/execution/engagement)
        - Investigation strategy based on persona type
        """
        from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

        # Extract persona-specific thresholds
        thresholds = self.persona.epistemic_config.thresholds

        # Create custom investigation profile based on persona
        profile_name = self._select_investigation_profile()

        logger.info(f"   📊 Persona configuration:")
        logger.info(f"      Uncertainty trigger: {thresholds['uncertainty_trigger']:.2f}")
        logger.info(f"      Confidence to proceed: {thresholds['confidence_to_proceed']:.2f}")
        logger.info(f"      Signal quality min: {thresholds['signal_quality_min']:.2f}")
        logger.info(f"      Investigation profile: {profile_name}")

        # Create CASCADE with persona configuration
        cascade = CanonicalEpistemicCascade(
            profile_name=profile_name,
            agent_id=self.persona_id,
            enable_session_db=True,
            enable_git_notes=True,
            session_id=f"persona-{self.persona_id}-{int(datetime.now(UTC).timestamp())}"
        )

        # Override thresholds with persona-specific values
        cascade.action_confidence_threshold = thresholds['confidence_to_proceed']

        # Store persona reference for assessment override
        cascade._persona = self.persona

        # Wrap the assessment method to apply persona priors
        original_assess = cascade._assess_epistemic_state
        cascade._assess_epistemic_state = self._create_persona_aware_assessment(original_assess)

        return cascade

    def _create_persona_aware_assessment(self, original_assess_method):
        """
        Wrap CASCADE assessment to apply persona priors

        This ensures that the persona's domain-specific knowledge is reflected
        in the initial epistemic state.
        """
        async def persona_aware_assessment(task, context, task_id, phase, round_num=None, investigation_rounds=0):
            # Get baseline assessment from CASCADE
            assessment = await original_assess_method(
                task, context, task_id, phase, round_num, investigation_rounds
            )

            # Apply persona priors to baseline assessment
            assessment = self._apply_priors(assessment, phase)

            return assessment

        return persona_aware_assessment

    def _apply_priors(self, assessment: EpistemicAssessmentSchema, phase) -> EpistemicAssessmentSchema:
        """
        Apply persona priors to assessment
        
        Works with EpistemicAssessmentSchema using prefixed field names.
        """
        priors = self.persona.epistemic_config.priors

        # Apply priors based on phase
        if phase.value == 'preflight':
            strength = 1.0
        elif phase.value == 'think':
            strength = 0.8
        else:
            strength = 0.5

        # Blend baseline with persona priors (NEW schema)
        def blend_vector_new(baseline_vector: VectorAssessment, prior_value: float, vector_name: str) -> VectorAssessment:
            """Blend baseline assessment with persona prior (NEW schema)"""
            blended_score = baseline_vector.score * (1 - strength) + prior_value * strength
            rationale = f"{baseline_vector.rationale} [Persona prior: {prior_value:.2f}, strength: {strength:.1f}]"
            return VectorAssessment(
                score=blended_score,
                rationale=rationale,
                evidence=baseline_vector.evidence,
                warrants_investigation=baseline_vector.warrants_investigation,
                investigation_priority=baseline_vector.investigation_priority
            )

        # Apply priors to each vector (NEW field names with prefixes)
        assessment.engagement = blend_vector_new(assessment.engagement, priors['engagement'], 'engagement')
        assessment.foundation_know = blend_vector_new(assessment.foundation_know, priors['know'], 'know')
        assessment.foundation_do = blend_vector_new(assessment.foundation_do, priors['do'], 'do')
        assessment.foundation_context = blend_vector_new(assessment.foundation_context, priors['context'], 'context')
        assessment.comprehension_clarity = blend_vector_new(assessment.comprehension_clarity, priors['clarity'], 'clarity')
        assessment.comprehension_coherence = blend_vector_new(assessment.comprehension_coherence, priors['coherence'], 'coherence')
        assessment.comprehension_signal = blend_vector_new(assessment.comprehension_signal, priors['signal'], 'signal')
        assessment.comprehension_density = blend_vector_new(assessment.comprehension_density, priors['density'], 'density')
        assessment.execution_state = blend_vector_new(assessment.execution_state, priors['state'], 'state')
        assessment.execution_change = blend_vector_new(assessment.execution_change, priors['change'], 'change')
        assessment.execution_completion = blend_vector_new(assessment.execution_completion, priors['completion'], 'completion')
        assessment.execution_impact = blend_vector_new(assessment.execution_impact, priors['impact'], 'impact')
        assessment.uncertainty = blend_vector_new(assessment.uncertainty, priors['uncertainty'], 'uncertainty')

        # NEW schema calculates confidences via methods, no need to set them manually
        logger.debug(f"   🎭 Applied persona priors (strength: {strength:.1f})")
        logger.debug(f"      KNOW: {assessment.foundation_know.score:.2f}")
        
        # Calculate overall confidence using NEW schema method
        tier_confidences = assessment.calculate_tier_confidences()
        logger.debug(f"      Overall: {tier_confidences['overall_confidence']:.2f}")

        return assessment

    # _apply_priors_new renamed to _apply_priors below

    def _select_investigation_profile(self) -> str:
        """
        Select CASCADE investigation profile based on persona type

        Maps persona types to investigation profiles:
        - security → cautious (low threshold, many rounds)
        - ux → balanced
        - performance → autonomous_agent (high threshold, few rounds)
        - architecture → balanced
        - code_review → balanced
        - sentinel → minimal (delegates to personas)
        """
        persona_type = self.persona.get_type()

        profile_map = {
            'security': 'cautious',
            'ux': 'balanced',
            'performance': 'autonomous_agent',
            'architecture': 'balanced',
            'code_review': 'balanced',
            'sentinel': 'minimal'
        }

        return profile_map.get(persona_type, 'balanced')

    def _interpret_with_persona(self, cascade_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret CASCADE result through persona lens

        Adds persona-specific findings and recommendations based on:
        - Focus domains
        - Persona type
        - Domain expertise
        """
        interpreted = cascade_result.copy()

        # Extract findings relevant to persona focus domains
        focus_domains = self.persona.epistemic_config.focus_domains
        persona_type = self.persona.get_type()

        # Generate persona-specific findings
        findings = self._extract_persona_findings(cascade_result, focus_domains)
        interpreted['persona_findings'] = findings

        # Generate persona-specific recommendation
        recommendation = self._generate_persona_recommendation(
            cascade_result, persona_type
        )
        interpreted['persona_recommendation'] = recommendation

        # Add persona metadata
        interpreted['persona_metadata'] = {
            'persona_id': self.persona_id,
            'persona_name': self.persona.name,
            'persona_type': persona_type,
            'focus_domains': focus_domains[:5],
            'confidence_threshold': self.persona.epistemic_config.thresholds['confidence_to_proceed']
        }

        return interpreted

    def _extract_persona_findings(
        self,
        cascade_result: Dict[str, Any],
        focus_domains: list
    ) -> list:
        """
        Extract findings relevant to persona focus domains

        Example for security persona:
        - Looks for security-related keywords in rationale
        - Flags authentication, authorization issues
        - Identifies potential vulnerabilities
        """
        findings = []

        rationale = cascade_result.get('rationale', '').lower()
        guidance = cascade_result.get('execution_guidance', [])

        # Check for focus domain mentions
        for domain in focus_domains:
            if domain.lower() in rationale:
                findings.append(f"Domain '{domain}' mentioned in assessment")

        # Add any execution guidance as findings
        findings.extend(guidance)

        return findings

    def _generate_persona_recommendation(
        self,
        cascade_result: Dict[str, Any],
        persona_type: str
    ) -> str:
        """
        Generate persona-specific recommendation

        Different personas have different recommendation styles:
        - Security: Cautious, emphasizes risks
        - UX: User-focused, emphasizes usability
        - Performance: Metrics-focused, emphasizes optimization
        """
        action = cascade_result['action']
        confidence = cascade_result['confidence']

        if persona_type == 'security':
            if action == 'proceed' and confidence < 0.85:
                return "PROCEED_WITH_CAUTION: Security review should maintain high confidence"
            elif action == 'investigate':
                return "INVESTIGATE_THOROUGHLY: Security requires comprehensive analysis"
            else:
                return f"SECURITY_ASSESSMENT: {action.upper()}"

        elif persona_type == 'ux':
            if action == 'proceed':
                return "PROCEED: User experience considerations addressed"
            else:
                return f"UX_REVIEW: {action.upper()}"

        elif persona_type == 'performance':
            if action == 'proceed':
                return "PROCEED: Performance impact acceptable"
            else:
                return f"PERFORMANCE_REVIEW: {action.upper()}"

        else:
            return f"{persona_type.upper()}_ASSESSMENT: {action.upper()}"

    async def _report_to_sentinel(
        self,
        message_type: MessageType,
        payload: Dict[str, Any]
    ) -> bool:
        """
        Report progress to Sentinel

        Args:
            message_type: Type of message
            payload: Message payload

        Returns:
            bool: True if sent successfully
        """
        try:
            # Create message
            message = PersonaMessage(
                message_type=message_type,
                persona_id=self.persona_id,
                payload=payload
            )

            # Sign message (Phase 2 integration)
            message.sign(self.identity)

            # Send via transport
            success = send_message(
                message,
                transport="file",
                destination=self.sentinel_endpoint
            )

            if success:
                logger.debug(f"   ✓ Reported to Sentinel: {message_type.value}")
            else:
                logger.warning(f"   ⚠️  Failed to report to Sentinel: {message_type.value}")

            return success

        except Exception as e:
            logger.error(f"   ❌ Sentinel reporting failed: {e}")
            return False

    async def check_sentinel_messages(self, timeout: Optional[float] = 0.1) -> Optional[SentinelMessage]:
        """
        Check for messages from Sentinel

        Args:
            timeout: Timeout in seconds (None = blocking, 0.1 = non-blocking)

        Returns:
            SentinelMessage or None
        """
        return receive_message(
            persona_id=self.persona_id,
            transport="file",
            source=self.sentinel_endpoint,
            timeout=timeout
        )

    def get_persona_info(self) -> Dict[str, Any]:
        """Get persona information"""
        return {
            'persona_id': self.persona_id,
            'name': self.persona.name,
            'type': self.persona.get_type(),
            'version': self.persona.version,
            'focus_domains': self.persona.epistemic_config.focus_domains,
            'thresholds': self.persona.epistemic_config.thresholds,
            'weights': self.persona.epistemic_config.weights
        }
