"""
MiniMax-M2 API Adapter - Phase 1

Integrates with MiniMax-M2 API using Anthropic SDK.
Provides API-based epistemic reasoning for modality switching.

Usage:
    adapter = MinimaxAdapter()
    response = adapter.call(payload, token_meta)
"""

import os
import json
import logging
from typing import Dict, Any
from empirica.plugins.modality_switcher.plugin_registry import AdapterPayload, AdapterResponse, AdapterError
from empirica.config.credentials_loader import get_credentials_loader

logger = logging.getLogger(__name__)

# Try to import anthropic, gracefully handle if not installed
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("⚠️  anthropic package not installed. Install with: pip install anthropic")

# Adapter metadata
ADAPTER_METADATA = {
    'version': '1.0.0',
    'cost_per_token': 0.00001,  # Estimated, adjust based on actual pricing
    'type': 'api',
    'provider': 'minimax',
    'model': 'MiniMax-M2',
    'description': 'MiniMax-M2 API adapter using Anthropic SDK',
    'capabilities': ['text', 'tool_calls', 'streaming'],
    'limitations': [
        'No image/document input support',
        'Requires MINIMAX_API_KEY environment variable',
    ],
    'notes': 'API-based adapter using Anthropic SDK for clean integration'
}


class MinimaxAdapter:
    """
    Adapter for MiniMax API calls via Anthropic SDK.
    
    Implements the AdapterInterface protocol for modality switching.
    """
    
    def __init__(self, model: str = None, config: Dict[str, Any] = None):
        """
        Initialize MiniMax adapter.
        
        Args:
            model: Model to use (defaults to config default_model)
            config: Configuration dict with optional:
                   - timeout: Request timeout in seconds (default: 60)
                   - max_retries: Max retry attempts (default: 2)
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic package required. Install with: pip install anthropic")
        
        # Load credentials
        self.loader = get_credentials_loader()
        self.provider_config = self.loader.get_provider_config('minimax')
        
        if not self.provider_config:
            raise ValueError("MiniMax credentials not configured")
        
        # Set model (use provided or default)
        self.model = model or self.loader.get_default_model('minimax')
        
        # Validate model
        if not self.loader.validate_model('minimax', self.model):
            available = self.loader.get_available_models('minimax')
            raise ValueError(
                f"Model '{self.model}' not available for MiniMax. "
                f"Available: {available}"
            )
        
        # Get API credentials
        self.api_key = self.loader.get_api_key('minimax')
        self.base_url = self.loader.get_base_url('minimax')
        self.headers = self.loader.get_headers('minimax')
        
        # Config options
        self.config = config or {}
        self.timeout = self.config.get('timeout', 60)
        self.max_retries = self.config.get('max_retries', 2)
        self.client = None
        
        logger.info(f"✅ MinimaxAdapter initialized (model: {self.model})")
    
    def health_check(self) -> bool:
        """
        Check if MiniMax adapter is properly configured.
        
        Returns:
            bool: True if API key and base URL are present
        """
        # Check if API key is available
        if not self.api_key:
            logger.warning("❌ MiniMax API key not configured")
            return False
        
        # Check if base URL is set
        if not self.base_url:
            logger.warning("❌ MiniMax base URL not configured")
            return False
        
        # Check if model is set
        if not self.model:
            logger.warning("❌ MiniMax model not configured")
            return False
        
        logger.debug("✅ MinimaxAdapter health check: Configured correctly")
        return True
    
    def authenticate(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticate with MiniMax API.
        
        Args:
            meta: Metadata about the auth request
            
        Returns:
            Dict with token metadata
            
        Raises:
            ValueError if API key not found
        """
        if not self.api_key:
            raise ValueError("MiniMax API key not configured")
        
        # Initialize client
        self.client = anthropic.Anthropic(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
            max_retries=self.max_retries
        )
        
        logger.info(f"✅ MinimaxAdapter authenticated")
        
        return {
            "provider": "minimax",
            "model": self.model,
            "authenticated": True,
            "base_url": self.base_url
        }
    
    def call(
        self, 
        payload: AdapterPayload, 
        token_meta: Dict[str, Any]
    ) -> AdapterResponse | AdapterError:
        """
        Execute MiniMax-M2 API call.
        
        Args:
            payload: Standard adapter payload (supports epistemic snapshots)
            token_meta: Authentication token metadata
            
        Returns:
            AdapterResponse on success, AdapterError on failure
        """
        try:
            # Phase 4: Increment transfer count if snapshot present
            if payload.epistemic_snapshot:
                payload.epistemic_snapshot.increment_transfer_count()
                logger.info(f"📸 Snapshot transfer #{payload.epistemic_snapshot.transfer_count} to [MiniMax-{self.model}]")
            
            # Ensure authenticated
            if not self.client:
                self.authenticate(token_meta)
            
            # Phase 4: Get augmented prompt (includes snapshot context if present)
            augmented_query = payload.get_augmented_prompt()
            
            # Build messages
            messages = [
                {"role": "user", "content": augmented_query}
            ]
            
            # Make API call
            logger.debug(f"📡 Calling MiniMax-M2 API: {payload.user_query[:50]}...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=payload.max_tokens,
                temperature=payload.temperature,
                system=payload.system,
                messages=messages
            )
            
            # Extract response text
            response_text = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, 'text'):
                        response_text += block.text
            
            # Transform to RESPONSE_SCHEMA
            adapter_response = self._transform_to_schema(
                response_text=response_text,
                usage=response.usage if hasattr(response, 'usage') else None,
                payload=payload
            )
            
            logger.debug(f"✅ MiniMax response: {adapter_response.decision} (confidence: {adapter_response.confidence:.2f})")
            return adapter_response
            
        except anthropic.RateLimitError as e:
            logger.error(f"🚫 MiniMax rate limit: {e}")
            return AdapterError(
                code="rate_limit",
                message=f"MiniMax rate limit exceeded: {e}",
                provider="minimax",
                recoverable=True,
                meta={'error_type': 'rate_limit'}
            )
        except anthropic.AuthenticationError as e:
            logger.error(f"🔐 MiniMax auth error: {e}")
            return AdapterError(
                code="unauthorized",
                message=f"MiniMax authentication failed: {e}",
                provider="minimax",
                recoverable=False,
                meta={'error_type': 'auth'}
            )
        except anthropic.APIError as e:
            logger.error(f"❌ MiniMax API error: {e}")
            return AdapterError(
                code="api_error",
                message=f"MiniMax API error: {e}",
                provider="minimax",
                recoverable=True,
                meta={'error_type': 'api'}
            )
        except Exception as e:
            logger.error(f"💥 MiniMax unexpected error: {e}")
            return AdapterError(
                code="unknown",
                message=f"Unexpected error: {e}",
                provider="minimax",
                recoverable=True,
                meta={'error_type': 'unknown'}
            )
    
    def _transform_to_schema(
        self, 
        response_text: str,
        usage: Any,
        payload: AdapterPayload
    ) -> AdapterResponse:
        """
        Transform MiniMax response to RESPONSE_SCHEMA.
        
        Phase 1: Heuristic-based transformation (similar to Qwen adapter).
        Future Phase 2: Use structured prompting or second LLM call for extraction.
        
        Args:
            response_text: Raw text from MiniMax-M2
            usage: Usage statistics from API
            payload: Original payload for context
            
        Returns:
            AdapterResponse with 13 epistemic vectors
        """
        # Phase 1: Heuristic decision classification
        response_lower = response_text.lower()
        
        # Estimate decision based on response content
        if any(word in response_lower for word in ['uncertain', 'unclear', 'more information', 'need to know', 'investigate']):
            decision = "INVESTIGATE"
            base_confidence = 0.4
        elif any(word in response_lower for word in ['verify', 'check', 'confirm', 'validate']):
            decision = "CHECK"
            base_confidence = 0.6
        elif any(word in response_lower for word in ['cannot', "can't", 'unable', 'insufficient']):
            decision = "VERIFY"
            base_confidence = 0.5
        else:
            decision = "ACT"
            base_confidence = 0.7
        
        # Adjust confidence based on response quality
        response_words = len(response_text.split())
        query_words = len(payload.user_query.split())
        
        # More detailed response = higher confidence
        if response_words > 100:
            confidence = min(0.95, base_confidence + 0.15)
        elif response_words > 50:
            confidence = min(0.90, base_confidence + 0.10)
        else:
            confidence = base_confidence
        
        # Generate 13 epistemic vectors
        # Phase 1: Heuristic estimation based on response characteristics
        vector_references = {
            # Foundation Layer
            'know': min(1.0, response_words / 150),  # Knowledge demonstrated
            'do': 0.8 if decision == "ACT" else 0.5,  # Capability confidence
            'context': min(1.0, query_words / 40),  # Context sufficiency
            
            # Comprehension Layer
            'clarity': 0.8 if response_words > 50 else 0.6,  # Response clarity
            'coherence': 0.75,  # Assume coherent for MiniMax-M2
            'signal': 0.7 if response_words > 30 else 0.5,  # Signal-to-noise
            'density': min(1.0, response_words / 200),  # Information density
            
            # Execution Layer
            'state': 0.7 if decision in ["ACT", "CHECK"] else 0.5,  # Current state
            'change': 0.6 if decision == "ACT" else 0.4,  # Expected changes
            'completion': 0.85 if decision == "ACT" else 0.5,  # Task completion
            'impact': 0.7 if decision == "ACT" else 0.5,  # Expected impact
            
            # Meta Layer
            'engagement': 0.8 if response_words > 50 else 0.6,  # Engagement level
            'uncertainty': 1.0 - confidence,  # Explicit uncertainty
        }
        
        # Generate suggested actions based on decision
        suggested_actions = []
        if decision == "INVESTIGATE":
            suggested_actions = [
                "Gather more information before proceeding",
                "Search documentation or knowledge base",
                "Clarify requirements with user"
            ]
        elif decision == "CHECK":
            suggested_actions = [
                "Verify assumptions and constraints",
                "Review related documentation",
                "Validate approach with stakeholders"
            ]
        elif decision == "VERIFY":
            suggested_actions = [
                "Confirm available resources",
                "Check prerequisites are met",
                "Validate feasibility"
            ]
        else:  # ACT
            suggested_actions = [
                "Execute based on MiniMax-M2 response",
                "Monitor execution progress",
                "Validate output quality"
            ]
        
        # Build provider metadata
        provider_meta = {
            'provider': 'minimax',
            'model': self.model,
            'raw_response_length': len(response_text),
            'response_preview': response_text[:200],
        }
        
        # Add usage stats if available
        if usage:
            provider_meta['input_tokens'] = getattr(usage, 'input_tokens', 0)
            provider_meta['output_tokens'] = getattr(usage, 'output_tokens', 0)
        
        return AdapterResponse(
            decision=decision,
            confidence=confidence,
            rationale=f"MiniMax-M2 analysis: {response_text[:150]}...",
            vector_references=vector_references,
            suggested_actions=suggested_actions,
            fallback_needed=False,
            provider_meta=provider_meta
        )
