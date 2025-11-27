"""
Sentinel Integration Hooks

Provides integration points for cognitive_vault Sentinel to make
epistemic routing decisions based on checkpoint state.

Key Features:
- Post-checkpoint decision hooks
- Epistemic state evaluation by Sentinel
- Routing decisions (PROCEED, INVESTIGATE, HANDOFF, ESCALATE)
- Python API (no complex protocols)

Design Philosophy:
- Simple, optional hooks (don't block CASCADE if Sentinel unavailable)
- Pure Python API (no HTTP/gRPC overhead)
- Modular (Sentinel can be completely separate service)
"""

import logging
from typing import Dict, Any, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class SentinelDecision(Enum):
    """Sentinel routing decisions"""
    PROCEED = "proceed"           # AI can continue
    INVESTIGATE = "investigate"   # Requires deeper investigation
    HANDOFF = "handoff"          # Route to different AI
    ESCALATE = "escalate"        # Human review needed
    BLOCK = "block"              # Stop immediately


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
    """
    
    # Global registry of evaluator functions
    _evaluators: list[Callable] = []
    
    # Enable/disable Sentinel
    _enabled: bool = False
    
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
        blocking: bool = False
    ) -> Optional[SentinelDecision]:
        """
        Evaluate checkpoint with Sentinel
        
        Args:
            checkpoint_data: Checkpoint from git notes
            blocking: Wait for decision (default: async)
            
        Returns:
            SentinelDecision: Routing decision or None if disabled
        """
        if not cls.is_enabled():
            return None
        
        try:
            # Call all registered evaluators
            decisions = []
            for evaluator in cls._evaluators:
                try:
                    decision = evaluator(checkpoint_data)
                    if isinstance(decision, SentinelDecision):
                        decisions.append(decision)
                except Exception as e:
                    logger.warning(f"Evaluator {evaluator.__name__} failed: {e}")
            
            if not decisions:
                return None
            
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
                    logger.info(f"🛡️ Sentinel decision: {decision_type.value}")
                    return decision_type
            
            return SentinelDecision.PROCEED
            
        except Exception as e:
            logger.error(f"Sentinel evaluation failed: {e}")
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


# Example evaluator for reference
def example_uncertainty_evaluator(checkpoint_data: Dict[str, Any]) -> SentinelDecision:
    """
    Example Sentinel evaluator - routes based on uncertainty
    
    Logic:
    - UNCERTAINTY > 0.8 → INVESTIGATE
    - KNOW < 0.5 and DO < 0.5 → HANDOFF (needs different AI)
    - ENGAGEMENT < 0.6 → ESCALATE (human needed)
    - Otherwise → PROCEED
    """
    vectors = checkpoint_data.get('vectors', {})
    
    uncertainty = vectors.get('uncertainty', 0.5)
    know = vectors.get('know', 0.5)
    do = vectors.get('do', 0.5)
    engagement = vectors.get('engagement', 0.6)
    
    if engagement < 0.6:
        return SentinelDecision.ESCALATE
    
    if uncertainty > 0.8:
        return SentinelDecision.INVESTIGATE
    
    if know < 0.5 and do < 0.5:
        return SentinelDecision.HANDOFF
    
    return SentinelDecision.PROCEED
