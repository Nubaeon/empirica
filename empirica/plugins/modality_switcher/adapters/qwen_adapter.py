"""
Qwen CLI Adapter - Phase 1

Integrates with Qwen CLI for model calls.
Wraps CLI invocations and parses responses into RESPONSE_SCHEMA format.

Usage:
    adapter = QwenAdapter(model='qwen-coder-turbo')
    response = adapter.call(payload, token_meta)
"""

import subprocess
import json
import logging
import os
from typing import Dict, Any
from empirica.plugins.modality_switcher.plugin_registry import AdapterPayload, AdapterResponse, AdapterError
from empirica.plugins.modality_switcher.auth_manager import AuthManager
from empirica.config.credentials_loader import get_credentials_loader

logger = logging.getLogger(__name__)

# Adapter metadata
ADAPTER_METADATA = {
    'version': '1.0.1',
    'cost_per_token': 0.0,  # Free for self-hosted
    'type': 'cli',
    'provider': 'qwen',
    'description': 'Qwen CLI wrapper for local Qwen models',
    'limitations': [
        'Qwen CLI does not support --temperature parameter',
        'Qwen CLI does not support --max-tokens parameter',
        'System prompts combined with user query in single prompt',
    ],
    'notes': 'Updated to use Qwen-specific CLI arguments. For full control, consider using Qwen API directly.'
}


class QwenAdapter:
    """
    Adapter for Qwen CLI calls.
    
    Wraps the Qwen CLI and transforms responses to RESPONSE_SCHEMA format.
    """
    
    def __init__(self, model: str = None, config: Dict[str, Any] = None):
        """
        Initialize Qwen adapter.
        
        Args:
            model: Model to use (defaults to config default_model)
            config: Configuration dict with optional:
                   - cli_path: Path to qwen CLI (default: 'qwen')
                   - timeout: Command timeout in seconds (default: 300)
        """
        # Load credentials
        self.loader = get_credentials_loader()
        self.provider_config = self.loader.get_provider_config('qwen')
        
        if not self.provider_config:
            raise ValueError("Qwen credentials not configured")
        
        # Set model (use provided or default)
        self.model = model or self.loader.get_default_model('qwen')
        
        # Validate model
        if not self.loader.validate_model('qwen', self.model):
            available = self.loader.get_available_models('qwen')
            raise ValueError(
                f"Model '{self.model}' not available for Qwen. "
                f"Available: {available}"
            )
        
        # Get config values
        self.config = config or {}
        self.cli_path = self.config.get('cli_path', 'qwen')
        self.timeout = self.config.get('timeout', 300)
        self.api_key = self.loader.get_api_key('qwen')
        self.base_url = self.loader.get_base_url('qwen')
        
        logger.info(f"✅ QwenAdapter initialized (model: {self.model})")
    
    def health_check(self) -> bool:
        """
        Check if Qwen CLI is available and working.
        
        Returns:
            bool: True if healthy
        """
        try:
            # Try --version first, fall back to --help
            result = subprocess.run(
                [self.cli_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.debug("QwenAdapter health check: OK")
                return True
            
            # Try --help as fallback
            result = subprocess.run(
                [self.cli_path, '--help'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.debug("QwenAdapter health check: OK (via --help)")
                return True
            
            logger.warning(f"Qwen CLI returned code {result.returncode}")
            return False
                
        except FileNotFoundError:
            logger.error(f"Qwen CLI not found at: {self.cli_path}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("Qwen CLI health check timed out")
            return False
        except Exception as e:
            logger.error(f"Qwen health check error: {e}")
            return False
    
    def authenticate(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticate for Qwen calls (local CLI, no auth needed).
        
        Args:
            meta: Metadata about auth request
            
        Returns:
            Dict with minimal token metadata
        """
        logger.debug("QwenAdapter authenticate: No auth required for local CLI")
        return {
            'token': 'qwen-cli-no-auth',
            'provider': 'qwen',
            'scopes': ['all'],
            'source': 'local-cli',
        }
    
    def call(self, payload: AdapterPayload, token_meta: Dict[str, Any]) -> AdapterResponse | AdapterError:
        """
        Execute Qwen CLI call and parse response.
        
        Args:
            payload: Standard adapter payload (supports epistemic snapshots)
            token_meta: Auth token metadata (unused for local CLI)
            
        Returns:
            AdapterResponse with schema-compliant data
        """
        logger.info(f"🤖 QwenAdapter processing: {payload.user_query[:50]}...")
        
        # Phase 4: Increment transfer count if snapshot present
        if payload.epistemic_snapshot:
            payload.epistemic_snapshot.increment_transfer_count()
            logger.info(f"📸 Snapshot transfer #{payload.epistemic_snapshot.transfer_count} to [Qwen-{self.model}]")
        
        try:
            # Build CLI command - Qwen-specific syntax
            cmd = [self.cli_path]
            
            # Add model if specified
            if self.model:
                cmd.extend(['--model', self.model])
            
            # Add output format as JSON for better parsing
            cmd.extend(['--output-format', 'json'])
            
            # Disable tools and prevent interactive prompts
            # Try multiple strategies to prevent Qwen CLI from waiting for input
            cmd.extend(['--approval-mode', 'yolo'])  # Auto-approve (don't wait for user)
            # Alternative: 'never' to disable all actions, or 'plan' to just plan
            
            # Phase 4: Get augmented prompt (includes snapshot context if present)
            augmented_query = payload.get_augmented_prompt()
            
            # Combine system and user query
            # Qwen CLI doesn't have separate --system flag
            if payload.system and payload.system.strip():
                full_prompt = f"{payload.system}\n\n{augmented_query}"
            else:
                full_prompt = augmented_query
            
            # Add prompt using -p flag
            cmd.extend(['-p', full_prompt])
            
            # Note: Qwen CLI doesn't support --temperature or --max-tokens
            # These would need to be configured via model config or API
            
            # Execute with stdin redirected to prevent interactive prompts
            logger.debug(f"Executing: {' '.join(cmd[:4])}...")
            
            # Environment variables to disable interactivity
            env = {
                **os.environ,
                'QWEN_NO_INTERACTIVE': '1',
                'CI': 'true',  # Many CLIs disable prompts in CI
                'TERM': 'dumb'  # Prevent fancy terminal features
            }
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                stdin=subprocess.DEVNULL,  # Prevent reading from stdin
                env=env
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                logger.error(f"Qwen CLI failed: {error_msg}")
                return AdapterError(
                    code="cli_error",
                    message=f"Qwen CLI returned code {result.returncode}: {error_msg}",
                    provider="qwen",
                    recoverable=True,
                    meta={'returncode': result.returncode}
                )
            
            # Parse response
            output = result.stdout.strip()
            
            # Try to parse as JSON (if Qwen supports structured output)
            try:
                parsed = json.loads(output)
                # If Qwen returns structured data, use it
                if isinstance(parsed, dict) and 'response' in parsed:
                    raw_response = parsed['response']
                else:
                    raw_response = output
            except json.JSONDecodeError:
                # Plain text response
                raw_response = output
            
            # Transform to RESPONSE_SCHEMA
            # Phase 1: Use heuristics to estimate decision/confidence
            response = self._transform_to_schema(raw_response, payload)
            
            logger.debug(f"✅ QwenAdapter response: {response.decision} (confidence: {response.confidence})")
            return response
            
        except subprocess.TimeoutExpired:
            logger.error(f"Qwen CLI timed out after {self.timeout}s")
            return AdapterError(
                code="timeout",
                message=f"Qwen CLI timed out after {self.timeout}s",
                provider="qwen",
                recoverable=True,
                meta={'timeout': self.timeout}
            )
        except FileNotFoundError:
            logger.error(f"Qwen CLI not found: {self.cli_path}")
            return AdapterError(
                code="not_found",
                message=f"Qwen CLI not found at {self.cli_path}",
                provider="qwen",
                recoverable=False,
                meta={'cli_path': self.cli_path}
            )
        except Exception as e:
            logger.error(f"QwenAdapter error: {e}")
            return AdapterError(
                code="unknown",
                message=str(e),
                provider="qwen",
                recoverable=True,
                meta={}
            )
    
    def _transform_to_schema(self, raw_response: str, payload: AdapterPayload) -> AdapterResponse:
        """
        Transform raw Qwen response to RESPONSE_SCHEMA.
        
        Phase 1: Simple heuristic-based transformation.
        Future: Use PersonaEnforcer for proper validation.
        
        Args:
            raw_response: Raw text from Qwen
            payload: Original payload for context
            
        Returns:
            AdapterResponse
        """
        # Heuristics for decision and confidence
        # Phase 1: Simple keyword-based estimation
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
        
        # Generate vector references (heuristic)
        # Phase 1: Based on response characteristics
        query_words = len(payload.user_query.split())
        response_words = len(raw_response.split())
        
        vector_references = {
            'know': min(1.0, response_words / 100),  # More words = more knowledge shown
            'do': 0.7 if decision == "ACT" else 0.5,
            'context': min(1.0, query_words / 50),
            'clarity': 0.7 if len(raw_response) > 50 else 0.5,
            'coherence': 0.7,  # Assume coherent for now
            'signal': 0.6,
            'density': min(1.0, response_words / 200),
            'state': 0.6,
            'change': 0.5,
            'completion': 0.8 if decision == "ACT" else 0.5,
            'impact': 0.6,
        }
        
        # Generate suggested actions
        suggested_actions = [
            f"Execute based on Qwen response",
            "Validate output quality",
            "Monitor for errors"
        ]
        
        if decision != "ACT":
            suggested_actions.insert(0, "Gather more context before proceeding")
        
        return AdapterResponse(
            decision=decision,
            confidence=confidence,
            rationale=f"Qwen CLI response (transformed): {raw_response[:100]}...",
            vector_references=vector_references,
            suggested_actions=suggested_actions,
            fallback_needed=False,
            provider_meta={
                'provider': 'qwen',
                'cli_path': self.cli_path,
                'model': self.model or 'auto',
                'raw_response_length': len(raw_response),
                'response_preview': raw_response[:200],
            }
        )
