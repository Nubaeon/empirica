"""
Gemini CLI Adapter

Integrates with Gemini CLI for model calls.
Wraps CLI invocations and parses responses into RESPONSE_SCHEMA format.

Usage:
    adapter = GeminiAdapter({'cli_path': '/path/to/gemini'})
    response = adapter.call(payload, token_meta)
"""

import subprocess
import json
import logging
import os
from typing import Dict, Any
from empirica.plugins.modality_switcher.plugin_registry import AdapterPayload, AdapterResponse, AdapterError
from empirica.config.credentials_loader import get_credentials_loader

logger = logging.getLogger(__name__)

# Adapter metadata
ADAPTER_METADATA = {
    'version': '1.0.0',
    'cost_per_token': 0.00025,  # Approximate Gemini pricing
    'type': 'cli',
    'provider': 'gemini',
    'description': 'Gemini CLI wrapper for Google Gemini models',
    'limitations': [
        'CLI-specific parameter support',
        'System prompts combined with user query',
    ],
    'notes': 'Supports epistemic snapshot context injection'
}


class GeminiAdapter:
    """
    Adapter for Gemini CLI calls.
    
    Wraps the Gemini CLI and transforms responses to RESPONSE_SCHEMA format.
    """
    
    def __init__(self, model: str = None, config: Dict[str, Any] = None):
        """
        Initialize Gemini adapter.
        
        Args:
            model: Model to use (defaults to config default_model)
            config: Configuration dict with optional:
                   - cli_path: Path to gemini CLI (default: 'gemini')
                   - timeout: Command timeout in seconds (default: 300)
        """
        # Load credentials
        self.loader = get_credentials_loader()
        self.provider_config = self.loader.get_provider_config('gemini')
        
        if not self.provider_config:
            raise ValueError("Gemini credentials not configured")
        
        # Set model (use provided or default)
        self.model = model or self.loader.get_default_model('gemini')
        
        # Validate model
        if not self.loader.validate_model('gemini', self.model):
            available = self.loader.get_available_models('gemini')
            raise ValueError(
                f"Model '{self.model}' not available for Gemini. "
                f"Available: {available}"
            )
        
        # Get API credentials
        self.api_key = self.loader.get_api_key('gemini')
        self.base_url = self.loader.get_base_url('gemini')
        
        # Config options
        self.config = config or {}
        self.cli_path = self.config.get('cli_path', 'gemini')
        self.timeout = self.config.get('timeout', 300)
        
        logger.info(f"✅ GeminiAdapter initialized (model: {self.model})")
    
    def health_check(self) -> bool:
        """
        Check if Gemini CLI is available and working.
        
        Returns:
            bool: True if healthy
        """
        try:
            result = subprocess.run(
                [self.cli_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.debug("GeminiAdapter health check: OK")
                return True
            
            # Try --help as fallback
            result = subprocess.run(
                [self.cli_path, '--help'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.debug("GeminiAdapter health check: OK (via --help)")
                return True
            
            logger.warning(f"Gemini CLI returned code {result.returncode}")
            return False
                
        except FileNotFoundError:
            logger.error(f"Gemini CLI not found at: {self.cli_path}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("Gemini CLI health check timed out")
            return False
        except Exception as e:
            logger.error(f"Gemini health check error: {e}")
            return False
    
    def authenticate(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticate for Gemini calls (uses API key from environment).
        
        Args:
            meta: Metadata about auth request
            
        Returns:
            Dict with minimal token metadata
        """
        logger.debug("GeminiAdapter authenticate: Using environment API key")
        return {
            'token': 'gemini-cli-env-auth',
            'provider': 'gemini',
            'scopes': ['all'],
            'source': 'environment',
        }
    
    def call(self, payload: AdapterPayload, token_meta: Dict[str, Any]) -> AdapterResponse | AdapterError:
        """
        Execute Gemini CLI call and parse response.
        
        Args:
            payload: Standard adapter payload (supports epistemic snapshots)
            token_meta: Auth token metadata (unused for CLI)
            
        Returns:
            AdapterResponse with schema-compliant data
        """
        logger.info(f"🤖 GeminiAdapter processing: {payload.user_query[:50]}...")
        
        # Phase 4: Increment transfer count if snapshot present
        if payload.epistemic_snapshot:
            payload.epistemic_snapshot.increment_transfer_count()
            logger.info(f"📸 Snapshot transfer #{payload.epistemic_snapshot.transfer_count} to Gemini")
        
        try:
            # Build CLI command
            cmd = [self.cli_path]
            
            # Add model if specified
            if self.model:
                cmd.extend(['--model', self.model])
            
            # Phase 4: Get augmented prompt (includes snapshot context if present)
            augmented_query = payload.get_augmented_prompt()
            
            # Combine system and user query
            if payload.system and payload.system.strip():
                full_prompt = f"{payload.system}\n\n{augmented_query}"
            else:
                full_prompt = augmented_query
            
            # Add prompt
            cmd.append(full_prompt)
            
            # Execute
            logger.debug(f"Executing: {' '.join(cmd[:2])}...")
            
            env = {
                **os.environ,
                'CI': 'true',
                'TERM': 'dumb'
            }
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                stdin=subprocess.DEVNULL,
                env=env
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                logger.error(f"Gemini CLI failed: {error_msg}")
                return AdapterError(
                    code="cli_error",
                    message=f"Gemini CLI returned code {result.returncode}: {error_msg}",
                    provider="gemini",
                    recoverable=True,
                    meta={'returncode': result.returncode}
                )
            
            # Parse response
            output = result.stdout.strip()
            
            # Try to parse as JSON
            try:
                parsed = json.loads(output)
                if isinstance(parsed, dict) and 'response' in parsed:
                    raw_response = parsed['response']
                else:
                    raw_response = output
            except json.JSONDecodeError:
                raw_response = output
            
            # Transform to RESPONSE_SCHEMA
            response = self._transform_to_schema(raw_response, payload)
            
            logger.debug(f"✅ GeminiAdapter response: {response.decision} (confidence: {response.confidence})")
            return response
            
        except subprocess.TimeoutExpired:
            logger.error(f"Gemini CLI timed out after {self.timeout}s")
            return AdapterError(
                code="timeout",
                message=f"Gemini CLI timed out after {self.timeout}s",
                provider="gemini",
                recoverable=True,
                meta={'timeout': self.timeout}
            )
        except FileNotFoundError:
            logger.error(f"Gemini CLI not found: {self.cli_path}")
            return AdapterError(
                code="not_found",
                message=f"Gemini CLI not found at {self.cli_path}",
                provider="gemini",
                recoverable=False,
                meta={'cli_path': self.cli_path}
            )
        except Exception as e:
            logger.error(f"GeminiAdapter error: {e}")
            return AdapterError(
                code="unknown",
                message=str(e),
                provider="gemini",
                recoverable=True,
                meta={}
            )
    
    def _transform_to_schema(self, raw_response: str, payload: AdapterPayload) -> AdapterResponse:
        """
        Transform raw Gemini response to RESPONSE_SCHEMA.
        
        Args:
            raw_response: Raw text from Gemini
            payload: Original payload for context
            
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
            f"Execute based on Gemini response",
            "Validate output quality",
            "Monitor for errors"
        ]
        
        if decision != "ACT":
            suggested_actions.insert(0, "Gather more context before proceeding")
        
        return AdapterResponse(
            decision=decision,
            confidence=confidence,
            rationale=f"Gemini CLI response: {raw_response[:100]}...",
            vector_references=vector_references,
            suggested_actions=suggested_actions,
            fallback_needed=False,
            provider_meta={
                'provider': 'gemini',
                'cli_path': self.cli_path,
                'model': self.model or 'auto',
                'raw_response_length': len(raw_response),
                'response_preview': raw_response[:200],
            }
        )
