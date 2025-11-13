#!/usr/bin/env python3
"""
Empirica ModalitySwitcher - Phase 2

Intelligent routing system that selects the best adapter (MiniMax, Qwen, Local)
based on epistemic state, cost, latency, and quality requirements.

Integrates with:
- PluginRegistry (adapter discovery and management)
- 13-vector epistemic assessment
- AdaptiveUncertaintyCalibration
- Cost/latency optimization

Design Goals:
- Epistemic-driven routing (KNOW/DO/CONTEXT vectors)
- Cost-aware decision making
- Latency optimization
- Rate limiting and fallback handling
- Transparent reasoning

Usage:
    from empirica.core.modality import ModalitySwitcher
    
    switcher = ModalitySwitcher()
    result = switcher.route_request(query, epistemic_state, preferences)
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from empirica.plugins.modality_switcher.register_adapters import get_registry
from empirica.plugins.modality_switcher.plugin_registry import AdapterPayload, AdapterResponse, AdapterError

logger = logging.getLogger(__name__)


class RoutingStrategy(Enum):
    """Available routing strategies"""
    EPISTEMIC = "epistemic"  # Route based on epistemic vectors
    COST = "cost"  # Minimize cost
    LATENCY = "latency"  # Minimize latency  
    QUALITY = "quality"  # Maximize quality
    BALANCED = "balanced"  # Balance all factors


@dataclass
class RoutingDecision:
    """Result of routing decision"""
    selected_adapter: str  # 'minimax', 'qwen', 'local'
    confidence: float  # 0.0-1.0
    rationale: str
    estimated_cost: float  # USD
    estimated_latency: float  # seconds
    fallback_adapters: List[str]  # Ordered list of fallbacks


@dataclass
class RoutingPreferences:
    """User preferences for routing"""
    strategy: RoutingStrategy = RoutingStrategy.BALANCED
    max_cost_usd: float = 1.0
    max_latency_sec: float = 30.0
    min_quality_score: float = 0.7
    force_adapter: Optional[str] = None  # Override routing
    allow_fallback: bool = True


class ModalitySwitcher:
    """
    Intelligent adapter routing based on epistemic state and preferences.
    
    Routes requests to the best adapter (MiniMax, Qwen, Local) considering:
    - Epistemic vectors (KNOW, DO, CONTEXT, UNCERTAINTY)
    - Cost constraints
    - Latency requirements
    - Quality needs
    - Rate limits and availability
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize ModalitySwitcher.
        
        Args:
            config: Optional configuration dict
        """
        self.config = {
            # Adapter cost estimates (USD per 1000 tokens)
            "adapter_costs": {
                "minimax": 0.01,  # API-based, low cost
                "qwen": 0.0,  # CLI-based, free
                "local": 0.0,  # Self-hosted, free
            },
            
            # Adapter latency estimates (seconds for typical request)
            "adapter_latency": {
                "minimax": 3.0,  # API call latency
                "qwen": 30.0,  # CLI overhead
                "local": 10.0,  # Local inference
            },
            
            # Adapter quality scores (0.0-1.0)
            "adapter_quality": {
                "minimax": 0.9,  # High quality API
                "qwen": 0.75,  # Good CLI model
                "local": 0.7,  # Decent local model
            },
            
            # Epistemic routing thresholds
            "high_uncertainty_threshold": 0.7,  # UNCERTAINTY > 0.7
            "low_know_threshold": 0.4,  # KNOW < 0.4
            "high_confidence_threshold": 0.8,  # confidence > 0.8
            
            # Budget management
            "cost_sensitive_threshold": 0.5,  # Route to free if budget low
            
            **(config or {})
        }
        
        # Get plugin registry
        self.registry = get_registry()
        
        # Initialize usage tracking
        self.usage_stats = {
            "minimax": 0,
            "qwen": 0,
            "local": 0,
            "fallbacks": 0,
            "errors": 0,
        }
        
        logger.info("✅ ModalitySwitcher initialized")
    
    def route_request(
        self,
        query: str,
        epistemic_state: Dict[str, float],
        preferences: Optional[RoutingPreferences] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        Route a request to the best adapter based on epistemic state and preferences.
        
        Args:
            query: User query/task
            epistemic_state: Dict with epistemic vectors (know, do, context, uncertainty, etc.)
            preferences: Optional routing preferences
            context: Optional additional context
            
        Returns:
            RoutingDecision with selected adapter and rationale
        """
        preferences = preferences or RoutingPreferences()
        context = context or {}
        
        # Force adapter if specified
        if preferences.force_adapter:
            return self._force_adapter_route(preferences.force_adapter, epistemic_state)
        
        # Route based on strategy
        if preferences.strategy == RoutingStrategy.EPISTEMIC:
            return self._epistemic_route(query, epistemic_state, preferences, context)
        elif preferences.strategy == RoutingStrategy.COST:
            return self._cost_route(query, epistemic_state, preferences, context)
        elif preferences.strategy == RoutingStrategy.LATENCY:
            return self._latency_route(query, epistemic_state, preferences, context)
        elif preferences.strategy == RoutingStrategy.QUALITY:
            return self._quality_route(query, epistemic_state, preferences, context)
        else:  # BALANCED
            return self._balanced_route(query, epistemic_state, preferences, context)
    
    def _epistemic_route(
        self,
        query: str,
        epistemic_state: Dict[str, float],
        preferences: RoutingPreferences,
        context: Dict[str, Any]
    ) -> RoutingDecision:
        """
        Route based on epistemic vectors.
        
        Decision Logic:
        - High UNCERTAINTY → Qwen/Local (exploration phase)
        - Low KNOW → MiniMax (need authoritative knowledge)
        - High confidence + ACT → MiniMax (final quality output)
        - INVESTIGATE → Qwen (iterative refinement)
        """
        uncertainty = epistemic_state.get('uncertainty', 0.5)
        know = epistemic_state.get('know', 0.5)
        do_conf = epistemic_state.get('do', 0.5)
        context_val = epistemic_state.get('context', 0.5)
        
        action = context.get('action', 'ACT')
        
        # High uncertainty → exploration with free models
        if uncertainty >= self.config['high_uncertainty_threshold']:
            adapter = 'qwen'
            rationale = f"High uncertainty ({uncertainty:.2f}) → Qwen for iterative exploration"
            fallbacks = ['local', 'minimax']
        
        # Low knowledge → need authoritative source
        elif know < self.config['low_know_threshold']:
            adapter = 'minimax'
            rationale = f"Low KNOW ({know:.2f}) → MiniMax for authoritative knowledge"
            fallbacks = ['qwen', 'local']
        
        # Investigation phase → iterative model
        elif action == 'INVESTIGATE':
            adapter = 'qwen'
            rationale = f"INVESTIGATE action → Qwen for iterative refinement"
            fallbacks = ['local', 'minimax']
        
        # High confidence finalization → quality output
        elif do_conf >= self.config['high_confidence_threshold'] and action == 'ACT':
            adapter = 'minimax'
            rationale = f"High confidence ({do_conf:.2f}) + ACT → MiniMax for quality output"
            fallbacks = ['qwen', 'local']
        
        # Default: balanced approach
        else:
            adapter = 'qwen'
            rationale = f"Balanced epistemic state → Qwen as default"
            fallbacks = ['minimax', 'local']
        
        return RoutingDecision(
            selected_adapter=adapter,
            confidence=0.8,
            rationale=rationale,
            estimated_cost=self.config['adapter_costs'][adapter],
            estimated_latency=self.config['adapter_latency'][adapter],
            fallback_adapters=fallbacks
        )
    
    def _cost_route(
        self,
        query: str,
        epistemic_state: Dict[str, float],
        preferences: RoutingPreferences,
        context: Dict[str, Any]
    ) -> RoutingDecision:
        """Route to minimize cost (prefer free adapters)."""
        # Cost priority: local (free) > qwen (free) > minimax (paid)
        adapter = 'local'
        rationale = "Cost optimization → Local model (free)"
        fallbacks = ['qwen', 'minimax']
        
        return RoutingDecision(
            selected_adapter=adapter,
            confidence=0.9,
            rationale=rationale,
            estimated_cost=0.0,
            estimated_latency=self.config['adapter_latency'][adapter],
            fallback_adapters=fallbacks
        )
    
    def _latency_route(
        self,
        query: str,
        epistemic_state: Dict[str, float],
        preferences: RoutingPreferences,
        context: Dict[str, Any]
    ) -> RoutingDecision:
        """Route to minimize latency."""
        # Latency priority: minimax (3s) < local (10s) < qwen (30s)
        adapter = 'minimax'
        rationale = "Latency optimization → MiniMax (fastest API)"
        fallbacks = ['local', 'qwen']
        
        return RoutingDecision(
            selected_adapter=adapter,
            confidence=0.9,
            rationale=rationale,
            estimated_cost=self.config['adapter_costs'][adapter],
            estimated_latency=self.config['adapter_latency'][adapter],
            fallback_adapters=fallbacks
        )
    
    def _quality_route(
        self,
        query: str,
        epistemic_state: Dict[str, float],
        preferences: RoutingPreferences,
        context: Dict[str, Any]
    ) -> RoutingDecision:
        """Route to maximize quality."""
        # Quality priority: minimax (0.9) > qwen (0.75) > local (0.7)
        adapter = 'minimax'
        rationale = "Quality optimization → MiniMax (highest quality)"
        fallbacks = ['qwen', 'local']
        
        return RoutingDecision(
            selected_adapter=adapter,
            confidence=0.9,
            rationale=rationale,
            estimated_cost=self.config['adapter_costs'][adapter],
            estimated_latency=self.config['adapter_latency'][adapter],
            fallback_adapters=fallbacks
        )
    
    def _balanced_route(
        self,
        query: str,
        epistemic_state: Dict[str, float],
        preferences: RoutingPreferences,
        context: Dict[str, Any]
    ) -> RoutingDecision:
        """
        Balanced routing considering all factors.
        
        Scoring formula:
        score = quality * 0.4 + (1 - normalized_cost) * 0.3 + (1 - normalized_latency) * 0.3
        """
        scores = {}
        
        for adapter in ['minimax', 'qwen', 'local']:
            quality = self.config['adapter_quality'][adapter]
            cost = self.config['adapter_costs'][adapter]
            latency = self.config['adapter_latency'][adapter]
            
            # Normalize cost and latency (0-1 scale)
            max_cost = max(self.config['adapter_costs'].values())
            max_latency = max(self.config['adapter_latency'].values())
            
            norm_cost = cost / max_cost if max_cost > 0 else 0
            norm_latency = latency / max_latency if max_latency > 0 else 0
            
            # Balanced score
            score = quality * 0.4 + (1 - norm_cost) * 0.3 + (1 - norm_latency) * 0.3
            scores[adapter] = score
        
        # Select best score
        best_adapter = max(scores, key=scores.get)
        best_score = scores[best_adapter]
        
        # Order fallbacks by score
        fallbacks = sorted([a for a in scores if a != best_adapter], key=lambda a: scores[a], reverse=True)
        
        rationale = f"Balanced routing → {best_adapter} (score: {best_score:.2f})"
        
        return RoutingDecision(
            selected_adapter=best_adapter,
            confidence=0.85,
            rationale=rationale,
            estimated_cost=self.config['adapter_costs'][best_adapter],
            estimated_latency=self.config['adapter_latency'][best_adapter],
            fallback_adapters=fallbacks
        )
    
    def _force_adapter_route(
        self,
        adapter_name: str,
        epistemic_state: Dict[str, float]
    ) -> RoutingDecision:
        """Force routing to a specific adapter."""
        if adapter_name not in ['minimax', 'qwen', 'local']:
            raise ValueError(f"Unknown adapter: {adapter_name}")
        
        fallbacks = [a for a in ['minimax', 'qwen', 'local'] if a != adapter_name]
        
        return RoutingDecision(
            selected_adapter=adapter_name,
            confidence=1.0,
            rationale=f"Forced routing to {adapter_name}",
            estimated_cost=self.config['adapter_costs'][adapter_name],
            estimated_latency=self.config['adapter_latency'][adapter_name],
            fallback_adapters=fallbacks
        )
    
    def execute_with_routing(
        self,
        query: str,
        epistemic_state: Dict[str, float],
        preferences: Optional[RoutingPreferences] = None,
        context: Optional[Dict[str, Any]] = None,
        system: str = "You are a helpful assistant",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> AdapterResponse | AdapterError:
        """
        Route request and execute with selected adapter.
        
        Args:
            query: User query
            epistemic_state: Epistemic vectors
            preferences: Routing preferences
            context: Additional context
            system: System prompt
            temperature: Temperature parameter
            max_tokens: Max tokens to generate
            
        Returns:
            AdapterResponse or AdapterError
        """
        # Make routing decision
        decision = self.route_request(query, epistemic_state, preferences, context)
        
        logger.info(f"🎯 Routing Decision: {decision.selected_adapter}")
        logger.info(f"   Rationale: {decision.rationale}")
        logger.info(f"   Estimated: ${decision.estimated_cost:.4f}, {decision.estimated_latency:.1f}s")
        
        # Create payload
        payload = AdapterPayload(
            system=system,
            state_summary=f"Epistemic state: {epistemic_state}",
            user_query=query,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Try selected adapter
        try:
            # Get model from context if specified
            model = context.get('model') if context else None
            
            # Create adapter with model if provided
            if model:
                adapter = self.registry.get_adapter(decision.selected_adapter)(model=model)
                logger.info(f"   Using model: {model}")
            else:
                adapter = self.registry.get_adapter(decision.selected_adapter)
            
            self.usage_stats[decision.selected_adapter] += 1
            
            response = adapter.call(payload, {})
            
            if isinstance(response, AdapterError):
                logger.warning(f"⚠️  {decision.selected_adapter} returned error: {response.message}")
                
                # Try fallback if allowed
                if preferences and preferences.allow_fallback and decision.fallback_adapters:
                    return self._try_fallback(payload, decision.fallback_adapters, context)
                
                return response
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error executing {decision.selected_adapter}: {e}")
            self.usage_stats['errors'] += 1
            
            # Try fallback if allowed
            if preferences and preferences.allow_fallback and decision.fallback_adapters:
                return self._try_fallback(payload, decision.fallback_adapters, context)
            
            return AdapterError(
                code="execution_error",
                message=f"Failed to execute {decision.selected_adapter}: {e}",
                provider=decision.selected_adapter,
                recoverable=True,
                meta={'error': str(e)}
            )
    
    def _try_fallback(
        self,
        payload: AdapterPayload,
        fallback_adapters: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> AdapterResponse | AdapterError:
        """Try fallback adapters in order."""
        # Get model from context if specified
        model = context.get('model') if context else None
        
        for fallback in fallback_adapters:
            try:
                logger.info(f"🔄 Trying fallback: {fallback}")
                
                # Create adapter with model if provided
                if model:
                    adapter = self.registry.get_adapter(fallback)(model=model)
                else:
                    adapter = self.registry.get_adapter(fallback)
                
                self.usage_stats[fallback] += 1
                self.usage_stats['fallbacks'] += 1
                
                response = adapter.call(payload, {})
                
                if not isinstance(response, AdapterError):
                    logger.info(f"✅ Fallback {fallback} succeeded")
                    return response
                
                logger.warning(f"⚠️  Fallback {fallback} also returned error")
                
            except Exception as e:
                logger.error(f"❌ Fallback {fallback} failed: {e}")
                continue
        
        # All fallbacks failed
        return AdapterError(
            code="all_fallbacks_failed",
            message="All adapters failed to respond",
            provider="switcher",
            recoverable=False,
            meta={'tried_adapters': ['primary'] + fallback_adapters}
        )
    
    def get_usage_stats(self) -> Dict[str, int]:
        """Get usage statistics."""
        return dict(self.usage_stats)
    
    def reset_usage_stats(self):
        """Reset usage statistics."""
        self.usage_stats = {k: 0 for k in self.usage_stats}


if __name__ == "__main__":
    # Test routing logic
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 70)
    print("              MODALITYSWITCHER TEST")
    print("=" * 70)
    
    switcher = ModalitySwitcher()
    
    # Test epistemic routing
    test_cases = [
        {
            "name": "High Uncertainty",
            "epistemic_state": {"know": 0.5, "do": 0.5, "uncertainty": 0.8},
            "preferences": RoutingPreferences(strategy=RoutingStrategy.EPISTEMIC),
        },
        {
            "name": "Low Knowledge",
            "epistemic_state": {"know": 0.3, "do": 0.7, "uncertainty": 0.4},
            "preferences": RoutingPreferences(strategy=RoutingStrategy.EPISTEMIC),
        },
        {
            "name": "High Confidence ACT",
            "epistemic_state": {"know": 0.8, "do": 0.9, "uncertainty": 0.2},
            "preferences": RoutingPreferences(strategy=RoutingStrategy.EPISTEMIC),
            "context": {"action": "ACT"},
        },
        {
            "name": "Cost Optimization",
            "epistemic_state": {"know": 0.6, "do": 0.6, "uncertainty": 0.5},
            "preferences": RoutingPreferences(strategy=RoutingStrategy.COST),
        },
        {
            "name": "Latency Optimization",
            "epistemic_state": {"know": 0.6, "do": 0.6, "uncertainty": 0.5},
            "preferences": RoutingPreferences(strategy=RoutingStrategy.LATENCY),
        },
        {
            "name": "Quality Optimization",
            "epistemic_state": {"know": 0.6, "do": 0.6, "uncertainty": 0.5},
            "preferences": RoutingPreferences(strategy=RoutingStrategy.QUALITY),
        },
        {
            "name": "Balanced",
            "epistemic_state": {"know": 0.6, "do": 0.6, "uncertainty": 0.5},
            "preferences": RoutingPreferences(strategy=RoutingStrategy.BALANCED),
        },
    ]
    
    for test in test_cases:
        print(f"\n📋 Test: {test['name']}")
        decision = switcher.route_request(
            "Test query",
            test['epistemic_state'],
            test['preferences'],
            test.get('context', {})
        )
        print(f"   → {decision.selected_adapter}")
        print(f"   Rationale: {decision.rationale}")
        print(f"   Cost: ${decision.estimated_cost:.4f}, Latency: {decision.estimated_latency:.1f}s")
        print(f"   Fallbacks: {decision.fallback_adapters}")
    
    print("\n" + "=" * 70)
    print("                  ✅ TEST COMPLETE")
    print("=" * 70)
