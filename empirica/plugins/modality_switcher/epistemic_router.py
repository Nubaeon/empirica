"""
Epistemic Router - Route modality based on epistemic state

Integrates with Empirica's 13-vector assessment + uncertainty to make
intelligent routing decisions.

Decision Philosophy:
- High uncertainty → Local/cheap (investigate first)
- High confidence + high engagement → Premium (collaborate)
- Low coherence → Clarify (don't waste resources)
- Budget depleted → Local only (no premium)
"""

from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass


class Modality(Enum):
    """Available modalities for routing"""
    PREMIUM = "premium"          # Copilot premium / high-capability model
    NON_PREMIUM = "non_premium"  # Standard API calls
    LOCAL = "local"              # Local LLM (ollama, etc)
    VOICE = "voice"              # Voice input/output
    VISION = "vision"            # Vision/image processing
    DEFER = "defer"              # Defer to user
    CLARIFY = "clarify"          # Need clarification first


class Action(Enum):
    """Epistemic actions from assessment"""
    PROCEED = "proceed"
    INVESTIGATE = "investigate"
    CLARIFY = "clarify"
    RESET = "reset"
    STOP = "stop"


@dataclass
class RoutingDecision:
    """Result of routing decision"""
    modality: Modality
    rationale: str
    confidence: float
    estimated_cost_usd: float
    epistemic_state: Dict[str, float]
    fallback_modality: Optional[Modality] = None


class EpistemicRouter:
    """
    Routes requests based on 13-vector epistemic assessment
    
    Uses:
    - ENGAGEMENT (gate): Must be ≥ 0.60
    - KNOW: Domain knowledge
    - DO: Capability  
    - CONTEXT: Situational awareness
    - CLARITY: Task clarity
    - COHERENCE: Logical consistency
    - SIGNAL: Information quality
    - DENSITY: Information load
    - STATE: Current understanding
    - CHANGE: Progress confidence
    - COMPLETION: Goal proximity
    - IMPACT: Consequence awareness
    - UNCERTAINTY: Explicit meta-epistemic tracking
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize router
        
        Args:
            config: Configuration dict with thresholds and preferences
        """
        self.config = {
            # Budget thresholds
            "budget_low_threshold_usd": 5.0,
            "budget_critical_threshold_usd": 1.0,
            
            # Epistemic thresholds
            "engagement_gate": 0.60,
            "low_confidence_threshold": 0.45,
            "high_confidence_threshold": 0.75,
            "high_uncertainty_threshold": 0.80,
            "low_uncertainty_threshold": 0.30,
            "high_engagement_threshold": 0.80,
            
            # Critical thresholds
            "coherence_critical": 0.50,
            "density_critical": 0.90,
            
            # Cost estimates (USD per 1000 tokens)
            "premium_cost_per_1k": 0.02,
            "non_premium_cost_per_1k": 0.005,
            "local_cost_per_1k": 0.0,
            
            # Preferences
            "prefer_local_for_investigation": True,
            "use_premium_for_high_stakes": True,
            "allow_premium_when_urgent": True,
            
            **(config or {})
        }
    
    def route(self, 
              epistemic_assessment: Dict[str, Any],
              budget_remaining_usd: float,
              request_tokens: int = 2000,
              force_modality: Optional[Modality] = None) -> RoutingDecision:
        """
        Route request based on epistemic state and budget
        
        Args:
            epistemic_assessment: 13-vector assessment with scores + rationales
            budget_remaining_usd: Remaining budget in USD
            request_tokens: Estimated request size in tokens
            force_modality: Force a specific modality (override routing)
            
        Returns:
            RoutingDecision with modality, rationale, and metadata
        """
        # Extract key vectors
        engagement = epistemic_assessment.get('engagement', 0.0)
        know = epistemic_assessment.get('know', 0.0)
        do = epistemic_assessment.get('do', 0.0)
        clarity = epistemic_assessment.get('clarity', 0.0)
        coherence = epistemic_assessment.get('coherence', 0.0)
        overall_confidence = epistemic_assessment.get('overall_confidence', 0.0)
        uncertainty = epistemic_assessment.get('uncertainty', 0.5)
        recommended_action = epistemic_assessment.get('recommended_action', 'proceed')
        
        # Force modality if requested
        if force_modality:
            return self._create_decision(
                force_modality,
                f"Forced modality: {force_modality.value}",
                overall_confidence,
                self._estimate_cost(force_modality, request_tokens),
                epistemic_assessment
            )
        
        # GATE CHECK: Engagement must be ≥ 0.60
        if engagement < self.config['engagement_gate']:
            return self._create_decision(
                Modality.CLARIFY,
                f"ENGAGEMENT gate failed ({engagement:.2f} < 0.60). Request clarification.",
                0.0,
                0.0,
                epistemic_assessment
            )
        
        # CRITICAL FLAGS: Coherence or density issues
        if coherence < self.config['coherence_critical']:
            return self._create_decision(
                Modality.CLARIFY,
                f"COHERENCE critical ({coherence:.2f} < 0.50). Task incoherent, need clarification.",
                0.0,
                0.0,
                epistemic_assessment
            )
        
        # BUDGET DEPLETION: Force local if no budget
        if budget_remaining_usd <= self.config['budget_critical_threshold_usd']:
            return self._create_decision(
                Modality.LOCAL,
                f"Budget depleted ({budget_remaining_usd:.2f} USD). Local only.",
                overall_confidence,
                0.0,
                epistemic_assessment,
                fallback=Modality.DEFER
            )
        
        # HIGH UNCERTAINTY: Investigate with local/cheap
        if uncertainty >= self.config['high_uncertainty_threshold']:
            if self.config['prefer_local_for_investigation']:
                return self._create_decision(
                    Modality.LOCAL,
                    f"High UNCERTAINTY ({uncertainty:.2f} ≥ 0.80). Investigate locally first.",
                    overall_confidence,
                    0.0,
                    epistemic_assessment
                )
            else:
                return self._create_decision(
                    Modality.NON_PREMIUM,
                    f"High UNCERTAINTY ({uncertainty:.2f} ≥ 0.80). Use non-premium for investigation.",
                    overall_confidence,
                    self._estimate_cost(Modality.NON_PREMIUM, request_tokens),
                    epistemic_assessment,
                    fallback=Modality.LOCAL
                )
        
        # HIGH CONFIDENCE + HIGH ENGAGEMENT: Premium collaboration
        if (overall_confidence >= self.config['high_confidence_threshold'] and
            engagement >= self.config['high_engagement_threshold']):
            if budget_remaining_usd >= self.config['budget_low_threshold_usd']:
                return self._create_decision(
                    Modality.PREMIUM,
                    f"High confidence ({overall_confidence:.2f}) + high engagement ({engagement:.2f}). Premium collaboration justified.",
                    overall_confidence,
                    self._estimate_cost(Modality.PREMIUM, request_tokens),
                    epistemic_assessment,
                    fallback=Modality.NON_PREMIUM
                )
        
        # ACTION-BASED ROUTING
        action_modality = self._route_by_action(
            recommended_action,
            overall_confidence,
            uncertainty,
            budget_remaining_usd,
            request_tokens,
            epistemic_assessment
        )
        
        if action_modality:
            return action_modality
        
        # DEFAULT: Non-premium for general tasks
        return self._create_decision(
            Modality.NON_PREMIUM,
            f"Default routing: moderate confidence ({overall_confidence:.2f}), moderate uncertainty ({uncertainty:.2f}).",
            overall_confidence,
            self._estimate_cost(Modality.NON_PREMIUM, request_tokens),
            epistemic_assessment,
            fallback=Modality.LOCAL
        )
    
    def _route_by_action(self, 
                         action: str,
                         confidence: float,
                         uncertainty: float,
                         budget: float,
                         tokens: int,
                         assessment: Dict[str, Any]) -> Optional[RoutingDecision]:
        """Route based on recommended action"""
        
        if action == 'investigate':
            # Investigate: prefer local/cheap
            if self.config['prefer_local_for_investigation']:
                return self._create_decision(
                    Modality.LOCAL,
                    f"Action=INVESTIGATE. Local investigation preferred.",
                    confidence,
                    0.0,
                    assessment
                )
            else:
                return self._create_decision(
                    Modality.NON_PREMIUM,
                    f"Action=INVESTIGATE. Non-premium for investigation.",
                    confidence,
                    self._estimate_cost(Modality.NON_PREMIUM, tokens),
                    assessment,
                    fallback=Modality.LOCAL
                )
        
        elif action == 'proceed' and confidence >= self.config['high_confidence_threshold']:
            # High-confidence action: premium if budget allows
            if budget >= self.config['budget_low_threshold_usd'] and self.config['use_premium_for_high_stakes']:
                return self._create_decision(
                    Modality.PREMIUM,
                    f"Action=PROCEED with high confidence ({confidence:.2f}). Premium for execution.",
                    confidence,
                    self._estimate_cost(Modality.PREMIUM, tokens),
                    assessment,
                    fallback=Modality.NON_PREMIUM
                )
        
        elif action == 'clarify':
            return self._create_decision(
                Modality.CLARIFY,
                "Action=CLARIFY. Need user clarification.",
                0.0,
                0.0,
                assessment
            )
        
        return None
    
    def _estimate_cost(self, modality: Modality, tokens: int) -> float:
        """Estimate cost for modality and token count"""
        cost_per_1k = {
            Modality.PREMIUM: self.config['premium_cost_per_1k'],
            Modality.NON_PREMIUM: self.config['non_premium_cost_per_1k'],
            Modality.LOCAL: self.config['local_cost_per_1k'],
            Modality.VOICE: self.config['non_premium_cost_per_1k'],  # Similar to non-premium
            Modality.VISION: self.config['premium_cost_per_1k'],  # Similar to premium
        }.get(modality, 0.0)
        
        return (tokens / 1000) * cost_per_1k
    
    def _create_decision(self,
                        modality: Modality,
                        rationale: str,
                        confidence: float,
                        cost: float,
                        epistemic_state: Dict[str, Any],
                        fallback: Optional[Modality] = None) -> RoutingDecision:
        """Create a RoutingDecision object"""
        return RoutingDecision(
            modality=modality,
            rationale=rationale,
            confidence=confidence,
            estimated_cost_usd=cost,
            epistemic_state=epistemic_state,
            fallback_modality=fallback
        )


# Example usage
if __name__ == "__main__":
    router = EpistemicRouter()
    
    # Example: High uncertainty assessment
    assessment_uncertain = {
        'engagement': 0.75,
        'know': 0.3,
        'do': 0.6,
        'clarity': 0.7,
        'coherence': 0.8,
        'overall_confidence': 0.45,
        'uncertainty': 0.85,  # High uncertainty!
        'recommended_action': 'investigate'
    }
    
    decision = router.route(assessment_uncertain, budget_remaining_usd=20.0)
    print(f"Decision: {decision.modality.value}")
    print(f"Rationale: {decision.rationale}")
    print(f"Cost: ${decision.estimated_cost_usd:.4f}")
    print()
    
    # Example: High confidence assessment
    assessment_confident = {
        'engagement': 0.85,
        'know': 0.8,
        'do': 0.85,
        'clarity': 0.9,
        'coherence': 0.9,
        'overall_confidence': 0.82,
        'uncertainty': 0.2,  # Low uncertainty
        'recommended_action': 'proceed'
    }
    
    decision2 = router.route(assessment_confident, budget_remaining_usd=20.0)
    print(f"Decision: {decision2.modality.value}")
    print(f"Rationale: {decision2.rationale}")
    print(f"Cost: ${decision2.estimated_cost_usd:.4f}")
