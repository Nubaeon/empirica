"""
OpenRouter API Adapter

Integrates with OpenRouter API for multi-model access.
OpenRouter provides unified API access to multiple LLM providers.

Usage:
    adapter = OpenRouterAdapter({'api_key': 'sk-or-v1-...'})
    response = adapter.call(payload, token_meta)
"""

import requests
import json
import logging
from typing import Dict, Any
from pathlib import Path
from empirica.plugins.modality_switcher.plugin_registry import AdapterPayload, AdapterResponse, AdapterError
from empirica.config.credentials_loader import get_credentials_loader

logger = logging.getLogger(__name__)

# Adapter metadata
ADAPTER_METADATA = {
    'version': '1.0.0',
    'cost_per_token': 0.0,  # Varies by model
    'type': 'api',
    'provider': 'openrouter',
    'description': 'OpenRouter API wrapper for multi-model access',
    'limitations': [
        'Requires API key',
        'Costs vary by model selected',
    ],
    'notes': 'Supports epistemic snapshot context injection. Access multiple models through unified API.'
}


class OpenRouterAdapter:
    """
    Adapter for OpenRouter API calls.
    
    Wraps the OpenRouter API and transforms responses to RESPONSE_SCHEMA format.
    """
    
    def __init__(self, model: str = None, config: Dict[str, Any] = None):
        """
        Initialize OpenRouter adapter.
        
        Args:
            model: Model to use (defaults to config default_model)
            config: Configuration dict with optional:
                   - timeout: Request timeout in seconds (default: 120)
        """
        # Load credentials
        self.loader = get_credentials_loader()
        self.provider_config = self.loader.get_provider_config('openrouter')
        
        if not self.provider_config:
            raise ValueError("OpenRouter credentials not configured")
        
        # Set model (use provided or default)
        self.model = model or self.loader.get_default_model('openrouter')
        
        # Validate model
        if not self.loader.validate_model('openrouter', self.model):
            available = self.loader.get_available_models('openrouter')
            raise ValueError(
                f"Model '{self.model}' not available for OpenRouter. "
                f"Available: {available}"
            )
        
        # Get API credentials
        self.api_key = self.loader.get_api_key('openrouter')
        self.base_url = self.loader.get_base_url('openrouter')
        self.headers = self.loader.get_headers('openrouter')
        
        # Config options
        self.config = config or {}
        self.timeout = self.config.get('timeout', 120)
        self.session = requests.Session()
        
        logger.info(f"✅ OpenRouterAdapter initialized (model: {self.model})")
    
    def health_check(self) -> bool:
        """
        Check if OpenRouter adapter is properly configured.
        
        Returns:
            bool: True if API key is present and valid format
        """
        if not self.api_key:
            logger.error("No API key configured")
            return False
        
        # Check API key format (OpenRouter keys start with sk-or-v1-)
        if not self.api_key.startswith('sk-or-v1-'):
            logger.warning("API key doesn't match expected format (sk-or-v1-...)")
            return False
        
        # Check base URL is set
        if not self.base_url:
            logger.error("No base URL configured")
            return False
        
        logger.debug("✅ OpenRouterAdapter health check: Configured correctly")
        return True
    
    def authenticate(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticate for OpenRouter calls (uses API key).
        
        Args:
            meta: Metadata about auth request
            
        Returns:
            Dict with minimal token metadata
        """
        if not self.api_key:
            logger.error("No API key available for authentication")
            return {
                'token': None,
                'provider': 'openrouter',
                'error': 'No API key configured'
            }
        
        logger.debug("OpenRouterAdapter authenticate: Using API key")
        return {
            'token': self.api_key,
            'provider': 'openrouter',
            'scopes': ['all'],
            'source': 'api-key',
        }
    
    def call(self, payload: AdapterPayload, token_meta: Dict[str, Any]) -> AdapterResponse | AdapterError:
        """
        Execute OpenRouter API call and parse response.
        
        Args:
            payload: Standard adapter payload (supports epistemic snapshots)
            token_meta: Auth token metadata
            
        Returns:
            AdapterResponse with schema-compliant data
        """
        logger.info(f"🤖 OpenRouterAdapter processing: {payload.user_query[:50]}...")
        
        # Phase 4: Increment transfer count if snapshot present
        if payload.epistemic_snapshot:
            payload.epistemic_snapshot.increment_transfer_count()
            logger.info(f"📸 Snapshot transfer #{payload.epistemic_snapshot.transfer_count} to OpenRouter")
        
        if not self.api_key:
            return AdapterError(
                code="no_api_key",
                message="No OpenRouter API key configured",
                provider="openrouter",
                recoverable=False,
                meta={}
            )
        
        try:
            # Phase 4: Get augmented prompt (includes snapshot context if present)
            augmented_query = payload.get_augmented_prompt()
            
            # Build messages
            messages = []
            
            if payload.system and payload.system.strip():
                messages.append({
                    'role': 'system',
                    'content': payload.system
                })
            
            messages.append({
                'role': 'user',
                'content': augmented_query
            })
            
            # Build request
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://empirica.ai',  # Optional, for stats
                'X-Title': 'Empirica'  # Optional, for stats
            }
            
            data = {
                'model': self.model,
                'messages': messages,
                'temperature': payload.temperature,
                'max_tokens': payload.max_tokens
            }
            
            # Execute API call
            logger.debug(f"Calling OpenRouter API: {self.model}")
            
            response = self.session.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                error_msg = response.text or f"HTTP {response.status_code}"
                logger.error(f"OpenRouter API failed: {error_msg}")
                return AdapterError(
                    code="api_error",
                    message=f"OpenRouter API error: {error_msg}",
                    provider="openrouter",
                    recoverable=True,
                    meta={'status_code': response.status_code}
                )
            
            # Parse response
            result = response.json()
            
            if 'choices' not in result or len(result['choices']) == 0:
                return AdapterError(
                    code="invalid_response",
                    message="No choices in OpenRouter response",
                    provider="openrouter",
                    recoverable=True,
                    meta={'result': result}
                )
            
            raw_response = result['choices'][0]['message']['content']
            
            # Transform to RESPONSE_SCHEMA
            adapter_response = self._transform_to_schema(raw_response, payload, result)
            
            logger.debug(f"✅ OpenRouterAdapter response: {adapter_response.decision} (confidence: {adapter_response.confidence})")
            return adapter_response
            
        except requests.exceptions.Timeout:
            logger.error(f"OpenRouter API timed out after {self.timeout}s")
            return AdapterError(
                code="timeout",
                message=f"OpenRouter API timed out after {self.timeout}s",
                provider="openrouter",
                recoverable=True,
                meta={'timeout': self.timeout}
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API request error: {e}")
            return AdapterError(
                code="request_error",
                message=f"OpenRouter API request failed: {str(e)}",
                provider="openrouter",
                recoverable=True,
                meta={}
            )
        except Exception as e:
            logger.error(f"OpenRouterAdapter error: {e}")
            return AdapterError(
                code="unknown",
                message=str(e),
                provider="openrouter",
                recoverable=True,
                meta={}
            )
    
    def _transform_to_schema(self, raw_response: str, payload: AdapterPayload, api_result: Dict) -> AdapterResponse:
        """
        Transform raw OpenRouter response to RESPONSE_SCHEMA.
        
        Args:
            raw_response: Raw text from OpenRouter
            payload: Original payload for context
            api_result: Full API response for metadata
            
        Returns:
            AdapterResponse
        """
        response_lower = raw_response.lower()
        
        # Estimate decision
        if any(word in response_lower for word in ['uncertain', 'unclear', 'more information', 'clarify']):
            decision = "INVESTIGATE"
            confidence = 0.4
        elif any(word in response_lower for word in ['check', 'verify', 'confirm']):
            decision = "CHECK"
            confidence = 0.6
        else:
            decision = "ACT"
            confidence = 0.7
        
        # Generate vector references
        query_words = len(payload.user_query.split())
        response_words = len(raw_response.split())
        
        vector_references = {
            'know': min(1.0, response_words / 100),
            'do': 0.7 if decision == "ACT" else 0.5,
            'context': min(1.0, query_words / 50),
            'clarity': 0.7 if len(raw_response) > 50 else 0.5,
            'coherence': 0.7,
            'signal': 0.6,
            'density': min(1.0, response_words / 200),
            'state': 0.6,
            'change': 0.5,
            'completion': 0.8 if decision == "ACT" else 0.5,
            'impact': 0.6,
        }
        
        suggested_actions = [
            f"Execute based on OpenRouter response",
            "Validate output quality",
            "Monitor for errors"
        ]
        
        if decision != "ACT":
            suggested_actions.insert(0, "Gather more context before proceeding")
        
        # Extract usage info if available
        usage = api_result.get('usage', {})
        
        return AdapterResponse(
            decision=decision,
            confidence=confidence,
            rationale=f"OpenRouter API response ({self.model}): {raw_response[:100]}...",
            vector_references=vector_references,
            suggested_actions=suggested_actions,
            fallback_needed=False,
            provider_meta={
                'provider': 'openrouter',
                'model': self.model,
                'raw_response_length': len(raw_response),
                'response_preview': raw_response[:200],
                'usage': usage,
                'prompt_tokens': usage.get('prompt_tokens', 0),
                'completion_tokens': usage.get('completion_tokens', 0),
                'total_tokens': usage.get('total_tokens', 0),
            }
        )
