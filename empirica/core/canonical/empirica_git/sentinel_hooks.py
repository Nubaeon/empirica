"""
Sentinel Integration Hooks

Provides integration points for cognitive_vault Sentinel to make
epistemic routing decisions based on checkpoint state.

Key Features:
- Post-checkpoint decision hooks
- Epistemic state evaluation by Sentinel
- Routing decisions (PROCEED, INVESTIGATE, HANDOFF, ESCALATE)
- Python API (no complex protocols)
- Recursive grounding (--turtle): Sentinel verifies its own stability before observing

Design Philosophy:
- Simple, optional hooks (don't block CASCADE if Sentinel unavailable)
- Pure Python API (no HTTP/gRPC overhead)
- Modular (Sentinel can be completely separate service)
- Turtles all the way down: Observer must be grounded before observing
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable, List, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class SentinelDecision(Enum):
    """Sentinel routing decisions"""
    PROCEED = "proceed"           # AI can continue
    INVESTIGATE = "investigate"   # Requires deeper investigation
    BRANCH = "branch"            # Fork into parallel investigation paths
    REVISE = "revise"            # Revise current approach
    HALT = "halt"                # Stop and reassess
    HANDOFF = "handoff"          # Route to different AI
    ESCALATE = "escalate"        # Human review needed
    BLOCK = "block"              # Stop immediately


class TurtleStatus(Enum):
    """Sentinel's own grounding status (the observer's stability)"""
    CRYSTALLINE = "crystalline"   # 🌕 Fully grounded, safe to observe
    SOLID = "solid"               # 🌔 Well grounded, proceed
    EMERGENT = "emergent"         # 🌓 Forming, proceed with caution
    FORMING = "forming"           # 🌒 Unstable, consider halting
    DARK = "dark"                 # 🌑 Ungrounded, halt


@dataclass
class SentinelState:
    """
    Sentinel's own epistemic state (the observer's grounding).

    Before the Sentinel evaluates an AI's checkpoint, it must verify
    its own stability. This is the recursive grounding check.

    Attributes:
        evaluator_health: Are all registered evaluators functioning?
        decision_consistency: Are evaluator decisions coherent?
        response_latency: Is the Sentinel responding in time?
        evaluation_count: How many evaluations in this session?
        last_decision: Most recent decision made
        confidence: Sentinel's confidence in its own judgments
    """
    evaluator_health: float = 1.0       # 0-1: % of evaluators healthy
    decision_consistency: float = 1.0   # 0-1: agreement between evaluators
    response_latency: float = 0.0       # seconds (lower is better)
    evaluation_count: int = 0           # evaluations this session
    last_decision: Optional[SentinelDecision] = None
    confidence: float = 0.8             # Sentinel's self-confidence
    last_turtle_check: Optional[float] = None  # timestamp of last turtle check

    def get_grounding_score(self) -> float:
        """Calculate overall grounding score (0-1)."""
        # Latency penalty (>1s reduces score)
        latency_score = max(0, 1.0 - (self.response_latency / 2.0))

        # Experience bonus (more evaluations = more calibrated)
        experience_score = min(1.0, self.evaluation_count / 100)

        # Weighted average
        return (
            self.evaluator_health * 0.3 +
            self.decision_consistency * 0.3 +
            latency_score * 0.2 +
            self.confidence * 0.15 +
            experience_score * 0.05
        )

    def get_turtle_status(self) -> Tuple[TurtleStatus, str]:
        """Get the Sentinel's turtle status (moon phase)."""
        score = self.get_grounding_score()

        if score >= 0.85:
            return TurtleStatus.CRYSTALLINE, "🌕"
        elif score >= 0.70:
            return TurtleStatus.SOLID, "🌔"
        elif score >= 0.50:
            return TurtleStatus.EMERGENT, "🌓"
        elif score >= 0.30:
            return TurtleStatus.FORMING, "🌒"
        else:
            return TurtleStatus.DARK, "🌑"

    def is_safe_to_evaluate(self) -> bool:
        """Can the Sentinel safely evaluate an AI checkpoint?"""
        status, _ = self.get_turtle_status()
        return status in [TurtleStatus.CRYSTALLINE, TurtleStatus.SOLID, TurtleStatus.EMERGENT]


class SentinelHooks:
    """
    Sentinel integration hooks for epistemic decision-making

    Usage:
        # In cognitive_vault Sentinel service
        from empirica.core.canonical.empirica_git import SentinelHooks

        def my_sentinel_evaluator(checkpoint_data):
            # Analyze epistemic state
            if checkpoint_data['vectors']['uncertainty'] > 0.8:
                return SentinelDecision.INVESTIGATE
            return SentinelDecision.PROCEED

        SentinelHooks.register_evaluator(my_sentinel_evaluator)

        # In CASCADE commands, this gets called automatically:
        decision = SentinelHooks.evaluate_checkpoint(checkpoint_data)

        # Control epistemic looping:
        SentinelHooks.enable_looping(True)   # Allow INVESTIGATE decisions
        SentinelHooks.enable_looping(False)  # Suppress loops, only PROCEED/ESCALATE
    """

    # Global registry of evaluator functions
    _evaluators: list[Callable] = []

    # Enable/disable Sentinel
    _enabled: bool = False

    # Enable/disable epistemic looping (INVESTIGATE decisions)
    # When False, INVESTIGATE decisions are converted to PROCEED
    # This is the on/off switch for epistemic rounds
    _looping_enabled: bool = True

    # Sentinel's own epistemic state (for turtle checks)
    _state: SentinelState = SentinelState()

    # Enable turtle mode (verify observer before observing)
    _turtle_mode: bool = False

    @classmethod
    def enable_turtle_mode(cls, enabled: bool = True) -> None:
        """Enable/disable recursive grounding checks."""
        cls._turtle_mode = enabled
        logger.info(f"🐢 Sentinel turtle mode: {'enabled' if enabled else 'disabled'}")

    @classmethod
    def enable_looping(cls, enabled: bool = True) -> None:
        """
        Enable/disable epistemic looping (INVESTIGATE decisions).

        When looping is enabled (default):
        - Sentinel can return INVESTIGATE decisions
        - This triggers epistemic rounds where AI investigates before proceeding

        When looping is disabled:
        - INVESTIGATE decisions are converted to PROCEED
        - AI proceeds without investigation rounds
        - Useful for quick tasks or when looping is unwanted

        Can also be controlled via environment:
            EMPIRICA_SENTINEL_LOOPING=true|false

        Args:
            enabled: True to allow looping, False to suppress
        """
        import os
        # Check env var first (allows runtime override)
        env_val = os.getenv("EMPIRICA_SENTINEL_LOOPING", "").lower()
        if env_val in ("true", "1", "yes"):
            cls._looping_enabled = True
        elif env_val in ("false", "0", "no"):
            cls._looping_enabled = False
        else:
            cls._looping_enabled = enabled

        logger.info(f"🔄 Sentinel epistemic looping: {'enabled' if cls._looping_enabled else 'disabled'}")

    @classmethod
    def is_looping_enabled(cls) -> bool:
        """Check if epistemic looping is enabled."""
        import os
        # Check env var for dynamic override
        env_val = os.getenv("EMPIRICA_SENTINEL_LOOPING", "").lower()
        if env_val in ("true", "1", "yes"):
            return True
        elif env_val in ("false", "0", "no"):
            return False
        return cls._looping_enabled

    @classmethod
    def get_state(cls) -> SentinelState:
        """Get the Sentinel's current epistemic state."""
        return cls._state

    @classmethod
    def turtle_check(cls) -> Dict[str, Any]:
        """
        Perform recursive grounding check on the Sentinel itself.

        Before the Sentinel evaluates an AI's checkpoint, it must verify
        its own stability. This is the Noetic Handshake for the observer.

        Returns:
            {
                'safe_to_evaluate': bool,
                'status': TurtleStatus,
                'moon': str (emoji),
                'grounding_score': float,
                'layers': [...],  # 4-layer stack trace
                'recommendation': str
            }
        """
        state = cls._state
        state.last_turtle_check = time.time()

        # Calculate layer scores
        layers = []

        # Layer 0: Evaluator Health (are all evaluators functioning?)
        layer0_score = state.evaluator_health
        layers.append({
            'layer': 0,
            'name': 'EVALUATOR HEALTH',
            'score': layer0_score,
            'detail': f"{len(cls._evaluators)} evaluators, {layer0_score*100:.0f}% healthy"
        })

        # Layer 1: Decision Consistency (do evaluators agree?)
        layer1_score = state.decision_consistency
        layers.append({
            'layer': 1,
            'name': 'DECISION CONSISTENCY',
            'score': layer1_score,
            'detail': f"{layer1_score*100:.0f}% agreement between evaluators"
        })

        # Layer 2: Response Performance (is Sentinel fast enough?)
        latency_score = max(0, 1.0 - (state.response_latency / 2.0))
        layers.append({
            'layer': 2,
            'name': 'RESPONSE PERFORMANCE',
            'score': latency_score,
            'detail': f"Latency: {state.response_latency*1000:.0f}ms"
        })

        # Layer 3: Sentinel Confidence (self-trust)
        layer3_score = state.confidence
        layers.append({
            'layer': 3,
            'name': 'SENTINEL CONFIDENCE',
            'score': layer3_score,
            'detail': f"Self-confidence: {layer3_score:.2f}, Evaluations: {state.evaluation_count}"
        })

        # Add moon phase to each layer
        for layer in layers:
            score = layer['score']
            if score >= 0.85:
                layer['moon'] = "🌕"
                layer['status'] = "CRYSTALLINE"
            elif score >= 0.70:
                layer['moon'] = "🌔"
                layer['status'] = "SOLID"
            elif score >= 0.50:
                layer['moon'] = "🌓"
                layer['status'] = "EMERGENT"
            elif score >= 0.30:
                layer['moon'] = "🌒"
                layer['status'] = "FORMING"
            else:
                layer['moon'] = "🌑"
                layer['status'] = "DARK"

        # Overall status
        status, moon = state.get_turtle_status()
        grounding_score = state.get_grounding_score()
        safe = state.is_safe_to_evaluate()

        # Generate recommendation
        if safe and grounding_score >= 0.70:
            recommendation = "SAFE TO EVALUATE - Observer is stable"
        elif safe:
            recommendation = "PROCEED WITH CAUTION - Observer is forming"
        else:
            recommendation = "HALT - Observer is unstable, cannot reliably evaluate AI"

        return {
            'safe_to_evaluate': safe,
            'status': status.value,
            'moon': moon,
            'grounding_score': grounding_score,
            'layers': layers,
            'recommendation': recommendation,
            'evaluation_count': state.evaluation_count,
            'timestamp': state.last_turtle_check
        }

    @classmethod
    def register_evaluator(cls, evaluator: Callable[[Dict[str, Any]], SentinelDecision]) -> None:
        """
        Register Sentinel evaluator function
        
        Args:
            evaluator: Function that takes checkpoint data and returns SentinelDecision
        """
        cls._evaluators.append(evaluator)
        cls._enabled = True
        logger.info(f"✓ Registered Sentinel evaluator: {evaluator.__name__}")
    
    @classmethod
    def clear_evaluators(cls) -> None:
        """Clear all evaluators (for testing)"""
        cls._evaluators.clear()
        cls._enabled = False
    
    @classmethod
    def is_enabled(cls) -> bool:
        """Check if Sentinel is enabled"""
        return cls._enabled and len(cls._evaluators) > 0
    
    @classmethod
    def evaluate_checkpoint(
        cls,
        checkpoint_data: Dict[str, Any],
        blocking: bool = False,
        turtle: bool = None  # None = use class default, True/False = override
    ) -> Optional[SentinelDecision]:
        """
        Evaluate checkpoint with Sentinel

        Args:
            checkpoint_data: Checkpoint from git notes
            blocking: Wait for decision (default: async)
            turtle: Run turtle check first (None = use _turtle_mode default)

        Returns:
            SentinelDecision: Routing decision or None if disabled/ungrounded
        """
        if not cls.is_enabled():
            return None

        # Turtle check: verify Sentinel's own grounding before observing
        run_turtle = turtle if turtle is not None else cls._turtle_mode
        if run_turtle:
            turtle_result = cls.turtle_check()
            if not turtle_result['safe_to_evaluate']:
                logger.warning(
                    f"🐢 Sentinel HALT: Observer is ungrounded ({turtle_result['moon']} {turtle_result['status']}). "
                    f"Cannot reliably evaluate AI checkpoint."
                )
                # Return ESCALATE to indicate Sentinel itself needs attention
                return SentinelDecision.ESCALATE

            logger.debug(
                f"🐢 Sentinel turtle check passed: {turtle_result['moon']} {turtle_result['status']} "
                f"(score: {turtle_result['grounding_score']:.2f})"
            )

        start_time = time.time()

        try:
            # Call all registered evaluators
            decisions = []
            healthy_evaluators = 0
            for evaluator in cls._evaluators:
                try:
                    decision = evaluator(checkpoint_data)
                    if isinstance(decision, SentinelDecision):
                        decisions.append(decision)
                        healthy_evaluators += 1
                except Exception as e:
                    logger.warning(f"Evaluator {evaluator.__name__} failed: {e}")
            
            if not decisions:
                return None

            # Update Sentinel state metrics
            elapsed = time.time() - start_time
            cls._state.response_latency = elapsed
            cls._state.evaluation_count += 1
            cls._state.evaluator_health = healthy_evaluators / len(cls._evaluators) if cls._evaluators else 0

            # Calculate decision consistency (how many agree on same decision)
            if decisions:
                from collections import Counter
                decision_counts = Counter(decisions)
                most_common_count = decision_counts.most_common(1)[0][1]
                cls._state.decision_consistency = most_common_count / len(decisions)

            # Aggregate decisions (most conservative wins)
            priority = [
                SentinelDecision.BLOCK,
                SentinelDecision.ESCALATE,
                SentinelDecision.HANDOFF,
                SentinelDecision.INVESTIGATE,
                SentinelDecision.PROCEED
            ]

            for decision_type in priority:
                if decision_type in decisions:
                    # LOOPING CONTROL: If looping is disabled, convert INVESTIGATE to PROCEED
                    if decision_type == SentinelDecision.INVESTIGATE and not cls.is_looping_enabled():
                        logger.info(
                            f"🔄 Sentinel: INVESTIGATE suppressed (looping disabled) → PROCEED"
                        )
                        cls._state.last_decision = SentinelDecision.PROCEED
                        return SentinelDecision.PROCEED

                    cls._state.last_decision = decision_type
                    logger.info(f"🛡️ Sentinel decision: {decision_type.value}")
                    return decision_type

            return SentinelDecision.PROCEED

        except Exception as e:
            logger.error(f"Sentinel evaluation failed: {e}")
            # Reduce confidence on failures
            cls._state.confidence = max(0.5, cls._state.confidence - 0.1)
            return None
    
    @classmethod
    def post_checkpoint_hook(
        cls,
        session_id: str,
        ai_id: str,
        phase: str,
        checkpoint_data: Dict[str, Any]
    ) -> Optional[SentinelDecision]:
        """
        Hook called automatically after checkpoint creation
        
        Args:
            session_id: Session ID
            ai_id: AI ID
            phase: CASCADE phase
            checkpoint_data: Full checkpoint data
            
        Returns:
            SentinelDecision: Routing decision or None
        """
        if not cls.is_enabled():
            return None
        
        logger.debug(f"🛡️ Sentinel evaluating checkpoint (session={session_id}, phase={phase})")
        
        decision = cls.evaluate_checkpoint(checkpoint_data)
        
        if decision:
            cls._log_decision(session_id, ai_id, phase, decision)
        
        return decision
    
    @classmethod
    def _log_decision(
        cls,
        session_id: str,
        ai_id: str,
        phase: str,
        decision: SentinelDecision
    ) -> None:
        """Log Sentinel decision (could store in database)"""
        logger.info(
            f"🛡️ Sentinel Decision: {decision.value} "
            f"(session={session_id[:8]}, ai={ai_id}, phase={phase})"
        )


# Default evaluator for routing decisions
def default_epistemic_evaluator(checkpoint_data: Dict[str, Any]) -> SentinelDecision:
    """
    Default Sentinel evaluator - routes based on epistemic vectors.

    Logic:
    - UNCERTAINTY > 0.7 → INVESTIGATE (too uncertain to proceed)
    - KNOW < 0.5 and UNCERTAINTY > 0.5 → INVESTIGATE (low knowledge + doubt)
    - ENGAGEMENT < 0.5 → ESCALATE (human needed)
    - KNOW >= 0.7 and UNCERTAINTY <= 0.35 → PROCEED (readiness gate passed)
    - Otherwise → PROCEED with caution
    """
    vectors = checkpoint_data.get('vectors', {})

    uncertainty = vectors.get('uncertainty', 0.5)
    know = vectors.get('know', 0.5)
    engagement = vectors.get('engagement', 0.7)

    # Apply bias corrections (from CLAUDE.md)
    corrected_uncertainty = uncertainty + 0.10
    corrected_know = know - 0.05

    # Escalate if engagement too low
    if engagement < 0.5:
        return SentinelDecision.ESCALATE

    # Investigate if too uncertain
    if corrected_uncertainty > 0.7:
        return SentinelDecision.INVESTIGATE

    # Investigate if low knowledge with doubt
    if corrected_know < 0.5 and corrected_uncertainty > 0.5:
        return SentinelDecision.INVESTIGATE

    # Check readiness gate
    if corrected_know >= 0.70 and corrected_uncertainty <= 0.35:
        return SentinelDecision.PROCEED

    # Default: proceed (but Sentinel is watching)
    return SentinelDecision.PROCEED


# Alias for backwards compatibility
example_uncertainty_evaluator = default_epistemic_evaluator


def auto_enable_sentinel() -> bool:
    """
    Auto-enable Sentinel with default evaluator.
    Called automatically when CLI commands need Sentinel.

    Returns:
        bool: True if Sentinel was enabled, False if already enabled
    """
    if SentinelHooks.is_enabled():
        return False

    SentinelHooks.register_evaluator(default_epistemic_evaluator)
    logger.info("🛡️ Sentinel auto-enabled with default epistemic evaluator")
    return True
