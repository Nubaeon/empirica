"""
Qodo CLI Adapter

Integrates with Qodo CLI for model calls.
Wraps CLI invocations and parses responses into RESPONSE_SCHEMA format.

Usage:
    adapter = QodoAdapter({'cli_path': '/path/to/qodo'})
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
    'cost_per_token': 0.0,  # Pricing varies by backend
    'type': 'cli',
    'provider': 'qodo',
    'description': 'Qodo CLI wrapper for AI-powered code analysis',
    'limitations': [
        'CLI-specific parameter support',
        'System prompts combined with user query',
    ],
    'notes': 'Supports epistemic snapshot context injection'
}


class QodoAdapter:
    """
    Adapter for Qodo CLI calls.
    
    Wraps the Qodo CLI and transforms responses to RESPONSE_SCHEMA format.
    """
    
    def __init__(self, model: str = None, config: Dict[str, Any] = None):
        """
        Initialize Qodo adapter.
        
        Args:
            model: Model to use (defaults to config default_model)
            config: Configuration dict with optional:
                   - cli_path: Path to qodo CLI (default: 'qodo')
                   - timeout: Command timeout in seconds (default: 300)
        """
        # Load credentials
        self.loader = get_credentials_loader()
        self.provider_config = self.loader.get_provider_config('qodo')
        
        if not self.provider_config:
            raise ValueError("Qodo credentials not configured")
        
        # Set model (use provided or default)
        self.model = model or self.loader.get_default_model('qodo')
        
        # Validate model
        if not self.loader.validate_model('qodo', self.model):
            available = self.loader.get_available_models('qodo')
            raise ValueError(
                f"Model '{self.model}' not available for Qodo. "
                f"Available: {available}"
            )
        
        # Get API credentials
        self.api_key = self.loader.get_api_key('qodo')
        self.base_url = self.loader.get_base_url('qodo')
        
        # Config options
        self.config = config or {}
        self.cli_path = self.config.get('cli_path', 'qodo')
        self.timeout = self.config.get('timeout', 300)
        
        logger.info(f"✅ QodoAdapter initialized (model: {self.model})")
    
    def health_check(self) -> bool:
        """
        Check if Qodo CLI is available and working.
        
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
                logger.debug("QodoAdapter health check: OK")
                return True
            
            # Try --help as fallback
            result = subprocess.run(
                [self.cli_path, '--help'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.debug("QodoAdapter health check: OK (via --help)")
                return True
            
            logger.warning(f"Qodo CLI returned code {result.returncode}")
            return False
                
        except FileNotFoundError:
            logger.error(f"Qodo CLI not found at: {self.cli_path}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("Qodo CLI health check timed out")
            return False
        except Exception as e:
            logger.error(f"Qodo health check error: {e}")
            return False
    
    def authenticate(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticate for Qodo calls (uses API key from environment).
        
        Args:
            meta: Metadata about auth request
            
        Returns:
            Dict with minimal token metadata
        """
        logger.debug("QodoAdapter authenticate: Using environment API key")
        return {
            'token': 'qodo-cli-env-auth',
            'provider': 'qodo',
            'scopes': ['all'],
            'source': 'environment',
        }
    
    def call(self, payload: AdapterPayload, token_meta: Dict[str, Any]) -> AdapterResponse | AdapterError:
        """
        Execute Qodo CLI call and parse response.
        
        Args:
            payload: Standard adapter payload (supports epistemic snapshots)
            token_meta: Auth token metadata (unused for CLI)
            
        Returns:
            AdapterResponse with schema-compliant data
        """
        logger.info(f"🤖 QodoAdapter processing: {payload.user_query[:50]}...")
        
        # Phase 4: Increment transfer count if snapshot present
        if payload.epistemic_snapshot:
            payload.epistemic_snapshot.increment_transfer_count()
            logger.info(f"📸 Snapshot transfer #{payload.epistemic_snapshot.transfer_count} to Qodo")
        
        try:
            # Build CLI command
            cmd = [self.cli_path]
            
            # Phase 4: Get augmented prompt (includes snapshot context if present)
            augmented_query = payload.get_augmented_prompt()
            
            # Combine system and user query
            if payload.system and payload.system.strip():
                full_prompt = f"{payload.system}\n\n{augmented_query}"
            else:
                full_prompt = augmented_query
            
            # Add prompt (Qodo may use different flags, adjust as needed)
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
                logger.error(f"Qodo CLI failed: {error_msg}")
                return AdapterError(
                    code="cli_error",
                    message=f"Qodo CLI returned code {result.returncode}: {error_msg}",
                    provider="qodo",
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
            
            logger.debug(f"✅ QodoAdapter response: {response.decision} (confidence: {response.confidence})")
            return response
            
        except subprocess.TimeoutExpired:
            logger.error(f"Qodo CLI timed out after {self.timeout}s")
            return AdapterError(
                code="timeout",
                message=f"Qodo CLI timed out after {self.timeout}s",
                provider="qodo",
                recoverable=True,
                meta={'timeout': self.timeout}
            )
        except FileNotFoundError:
            logger.error(f"Qodo CLI not found: {self.cli_path}")
            return AdapterError(
                code="not_found",
                message=f"Qodo CLI not found at {self.cli_path}",
                provider="qodo",
                recoverable=False,
                meta={'cli_path': self.cli_path}
            )
        except Exception as e:
            logger.error(f"QodoAdapter error: {e}")
            return AdapterError(
                code="unknown",
                message=str(e),
                provider="qodo",
                recoverable=True,
                meta={}
            )
    
    def _transform_to_schema(self, raw_response: str, payload: AdapterPayload) -> AdapterResponse:
        """
        Transform raw Qodo response to RESPONSE_SCHEMA.
        
        Args:
            raw_response: Raw text from Qodo
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
            f"Execute based on Qodo response",
            "Validate output quality",
            "Monitor for errors"
        ]
        
        if decision != "ACT":
            suggested_actions.insert(0, "Gather more context before proceeding")
        
        return AdapterResponse(
            decision=decision,
            confidence=confidence,
            rationale=f"Qodo CLI response: {raw_response[:100]}...",
            vector_references=vector_references,
            suggested_actions=suggested_actions,
            fallback_needed=False,
            provider_meta={
                'provider': 'qodo',
                'cli_path': self.cli_path,
                'raw_response_length': len(raw_response),
                'response_preview': raw_response[:200],
            }
        )
