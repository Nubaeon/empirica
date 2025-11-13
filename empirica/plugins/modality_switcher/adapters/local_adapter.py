"""
Local Adapter - Stub Implementation for Phase 0

Simulates a local LLM adapter (Llama/Mistral) for testing.
This is a stub that returns schema-compliant responses without actual LLM calls.
"""

from typing import Dict, Any
import logging
from empirica.plugins.modality_switcher.plugin_registry import AdapterPayload, AdapterResponse, AdapterError
from empirica.plugins.modality_switcher.auth_manager import AuthManager

logger = logging.getLogger(__name__)

# Adapter metadata (optional)
ADAPTER_METADATA = {
    'version': '0.1.0',
    'cost_per_token': 0.0,
    'type': 'local',
    'description': 'Local LLM adapter (stub for Phase 0 testing)',
}


class LocalAdapter:
    """
    Adapter for local LLM calls (stub implementation).
    
    Phase 0: Returns mock responses for testing.
    Future: Integrate with actual local LLMs (Ollama, llama.cpp, etc.)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize local adapter.
        
        Args:
            config: Optional configuration (model, endpoint, etc.)
        """
        self.config = config or {}
        self.model = self.config.get('model', 'llama-3.2-3b')
        self.endpoint = self.config.get('endpoint', 'http://localhost:11434')
        logger.info(f"🤖 LocalAdapter initialized: model={self.model}")
    
    def health_check(self) -> bool:
        """
        Check if local LLM is reachable.
        
        Returns:
            bool: True if healthy (stub always returns True)
        """
        # Phase 0: Always healthy
        # Future: Actually ping the local LLM endpoint
        logger.debug("LocalAdapter health check: OK (stub)")
        return True
    
    def authenticate(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticate for local calls (no auth needed).
        
        Args:
            meta: Metadata about auth request
            
        Returns:
            Dict with minimal token metadata
        """
        # Local adapter doesn't need real authentication
        # Return a dummy token response
        logger.debug("LocalAdapter authenticate: No auth required for local")
        return {
            'token': 'local-no-auth',
            'provider': 'local',
            'scopes': ['all'],
            'source': 'local',
        }
    
    def call(self, payload: AdapterPayload, token_meta: Dict[str, Any]) -> AdapterResponse | AdapterError:
        """
        Execute local LLM call.
        
        Args:
            payload: Standard adapter payload
            token_meta: Auth token metadata (unused for local)
            
        Returns:
            AdapterResponse with mock data
        """
        logger.info(f"🤖 LocalAdapter processing: {payload.user_query[:50]}...")
        
        try:
            # Phase 0: Return mock response that conforms to RESPONSE_SCHEMA
            response = AdapterResponse(
                decision="ACT",
                confidence=0.75,
                rationale=f"Local LLM processed query (stub response for Phase 0 testing)",
                vector_references={
                    'know': 0.7,
                    'do': 0.8,
                    'context': 0.7,
                    'clarity': 0.8,
                    'coherence': 0.75,
                    'signal': 0.7,
                    'density': 0.65,
                    'state': 0.7,
                    'change': 0.6,
                    'completion': 0.7,
                    'impact': 0.6,
                },
                suggested_actions=[
                    "Execute task with local resources",
                    "Monitor for errors",
                    "Fallback to premium if needed"
                ],
                fallback_needed=False,
                provider_meta={
                    'model': self.model,
                    'endpoint': self.endpoint,
                    'is_stub': True,
                    'tokens_used': len(payload.user_query.split()) * 2,  # Rough estimate
                }
            )
            
            logger.debug(f"✅ LocalAdapter response: {response.decision} (confidence: {response.confidence})")
            return response
            
        except Exception as e:
            logger.error(f"LocalAdapter error: {e}")
            return AdapterError(
                code="unknown",
                message=str(e),
                provider="local",
                recoverable=True,
                meta={'model': self.model}
            )
