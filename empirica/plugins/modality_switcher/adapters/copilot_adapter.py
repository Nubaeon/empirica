"""
GitHub Copilot CLI Adapter

Integrates with GitHub Copilot CLI for multi-model access.
Provides access to multiple models through a single $10/month subscription.

Models Available:
- claude-sonnet-4.5 (Anthropic Claude 4.5 Sonnet)
- claude-sonnet-4 (Anthropic Claude 4 Sonnet)
- claude-haiku-4.5 (Anthropic Claude 4.5 Haiku)
- gpt-5 (OpenAI GPT-5)

Usage:
    adapter = CopilotAdapter(model='claude-sonnet-4')
    response = adapter.call(payload, token_meta)
"""

import subprocess
import json
import logging
import os
import re
from typing import Dict, Any
from empirica.plugins.modality_switcher.plugin_registry import AdapterPayload, AdapterResponse, AdapterError
from empirica.config.credentials_loader import get_credentials_loader

logger = logging.getLogger(__name__)

# Adapter metadata
ADAPTER_METADATA = {
    'version': '1.0.0',
    'cost_per_token': 0.0,  # Included in $10/month subscription
    'type': 'cli',
    'provider': 'github-copilot',
    'description': 'GitHub Copilot CLI wrapper for multi-model access',
    'limitations': [
        'Requires active GitHub Copilot subscription',
        'CLI must be authenticated (gh auth login)',
        'Token counts are estimates from CLI output',
    ],
    'notes': 'Supports epistemic snapshot context injection. Access to Claude, GPT-5, and more.',
    'available_models': [
        'claude-sonnet-4.5',
        'claude-sonnet-4',
        'claude-haiku-4.5',
        'gpt-5'
    ]
}


class CopilotAdapter:
    """
    Adapter for GitHub Copilot CLI calls.
    
    Wraps the Copilot CLI and transforms responses to RESPONSE_SCHEMA format.
    Provides multi-model access through single subscription.
    """
    
    def __init__(self, model: str = None, config: Dict[str, Any] = None):
        """
        Initialize Copilot adapter.
        
        Args:
            model: Model to use (defaults to config default_model)
            config: Configuration dict with optional:
                   - cli_path: Path to copilot CLI (default: 'copilot')
                   - timeout: Command timeout in seconds (default: 60)
        """
        # Load credentials
        self.loader = get_credentials_loader()
        self.provider_config = self.loader.get_provider_config('copilot')
        
        if not self.provider_config:
            raise ValueError("Copilot credentials not configured")
        
        # Set model (use provided or default)
        self.model = model or self.loader.get_default_model('copilot')
        
        # Validate model
        if not self.loader.validate_model('copilot', self.model):
            available = self.loader.get_available_models('copilot')
            raise ValueError(
                f"Model '{self.model}' not available for Copilot. "
                f"Available: {available}"
            )
        
        # Config options (Copilot uses CLI auth, no API key needed)
        self.config = config or {}
        self.cli_path = self.config.get('cli_path', 'copilot')
        self.timeout = self.config.get('timeout', 60)
        
        logger.info(f"✅ CopilotAdapter initialized (model: {self.model})")
    
    def health_check(self) -> bool:
        """
        Check if Copilot CLI is available and working.
        
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
                version = result.stdout.strip()
                logger.debug(f"CopilotAdapter health check: OK (version: {version})")
                return True
            
            logger.warning(f"Copilot CLI returned code {result.returncode}")
            return False
                
        except FileNotFoundError:
            logger.error(f"Copilot CLI not found at: {self.cli_path}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("Copilot CLI health check timed out")
            return False
        except Exception as e:
            logger.error(f"Copilot health check error: {e}")
            return False
    
    def authenticate(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticate for Copilot calls (uses GitHub authentication).
        
        Args:
            meta: Metadata about auth request
            
        Returns:
            Dict with minimal token metadata
        """
        logger.debug("CopilotAdapter authenticate: Using GitHub authentication")
        return {
            'token': 'copilot-cli-github-auth',
            'provider': 'github-copilot',
            'scopes': ['all'],
            'source': 'github-cli',
        }
    
    def call(self, payload: AdapterPayload, token_meta: Dict[str, Any]) -> AdapterResponse | AdapterError:
        """
        Execute Copilot CLI call and parse response.
        
        Args:
            payload: Standard adapter payload (supports epistemic snapshots)
            token_meta: Auth token metadata (unused for CLI)
            
        Returns:
            AdapterResponse with schema-compliant data
        """
        logger.info(f"🤖 CopilotAdapter processing: {payload.user_query[:50]}...")
        
        # Phase 4: Increment transfer count if snapshot present
        if payload.epistemic_snapshot:
            payload.epistemic_snapshot.increment_transfer_count()
            logger.info(f"📸 Snapshot transfer #{payload.epistemic_snapshot.transfer_count} to Copilot ({self.model})")
        
        try:
            # Build CLI command
            cmd = [
                self.cli_path,
                '--model', self.model,
                '--allow-all-tools',  # Required for non-interactive mode
                '--no-color',  # Disable color output for easier parsing
                '--prompt'
            ]
            
            # Phase 4: Get augmented prompt (includes snapshot context if present)
            augmented_query = payload.get_augmented_prompt()
            
            # Combine system and user query
            if payload.system and payload.system.strip():
                full_prompt = f"{payload.system}\n\n{augmented_query}"
            else:
                full_prompt = augmented_query
            
            # Add prompt as final argument
            cmd.append(full_prompt)
            
            # Execute
            logger.debug(f"Executing Copilot CLI: model={self.model}")
            
            env = {
                **os.environ,
                'COPILOT_ALLOW_ALL': '1'  # Environment variable for non-interactive mode
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
                logger.error(f"Copilot CLI failed: {error_msg}")
                return AdapterError(
                    code="cli_error",
                    message=f"Copilot CLI returned code {result.returncode}: {error_msg}",
                    provider="github-copilot",
                    recoverable=True,
                    meta={'returncode': result.returncode, 'model': self.model}
                )
            
            # Parse response
            output = result.stdout.strip()
            
            # Extract actual response (before usage stats)
            # Copilot CLI outputs response followed by usage stats
            response_lines = []
            in_response = True
            
            for line in output.split('\n'):
                # Stop at usage statistics
                if 'Total usage' in line or 'Total duration' in line or 'Usage by model' in line:
                    in_response = False
                    continue
                
                if in_response and line.strip():
                    response_lines.append(line)
            
            raw_response = '\n'.join(response_lines).strip()
            
            # Extract token usage from output (if available)
            token_usage = self._parse_token_usage(output)
            
            # Transform to RESPONSE_SCHEMA
            response = self._transform_to_schema(raw_response, payload, token_usage)
            
            logger.debug(f"✅ CopilotAdapter response: {response.decision} (confidence: {response.confidence})")
            return response
            
        except subprocess.TimeoutExpired:
            logger.error(f"Copilot CLI timed out after {self.timeout}s")
            return AdapterError(
                code="timeout",
                message=f"Copilot CLI timed out after {self.timeout}s",
                provider="github-copilot",
                recoverable=True,
                meta={'timeout': self.timeout, 'model': self.model}
            )
        except FileNotFoundError:
            logger.error(f"Copilot CLI not found: {self.cli_path}")
            return AdapterError(
                code="not_found",
                message=f"Copilot CLI not found at {self.cli_path}. Install: npm install -g @githubnext/github-copilot-cli",
                provider="github-copilot",
                recoverable=False,
                meta={'cli_path': self.cli_path}
            )
        except Exception as e:
            logger.error(f"CopilotAdapter error: {e}")
            return AdapterError(
                code="unknown",
                message=str(e),
                provider="github-copilot",
                recoverable=True,
                meta={'model': self.model}
            )
    
    def _parse_token_usage(self, output: str) -> Dict[str, int]:
        """
        Parse token usage from Copilot CLI output.
        
        Example output:
            claude-sonnet-4      23.0k input, 10 output, 0 cache read, 0 cache write
        
        Args:
            output: Full CLI output
            
        Returns:
            Dict with input_tokens, output_tokens, total_tokens
        """
        usage = {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}
        
        try:
            # Look for usage line matching the model
            for line in output.split('\n'):
                if self.model in line:
                    # Extract tokens: "23.0k input, 10 output"
                    # Parse input tokens
                    input_match = re.search(r'([\d.]+)k?\s+input', line)
                    if input_match:
                        value = float(input_match.group(1))
                        # Convert k to actual number
                        if 'k' in input_match.group(0):
                            value *= 1000
                        usage['input_tokens'] = int(value)
                    
                    # Parse output tokens
                    output_match = re.search(r'([\d.]+)k?\s+output', line)
                    if output_match:
                        value = float(output_match.group(1))
                        # Convert k to actual number
                        if 'k' in output_match.group(0):
                            value *= 1000
                        usage['output_tokens'] = int(value)
                    
                    usage['total_tokens'] = usage['input_tokens'] + usage['output_tokens']
                    break
        except Exception as e:
            logger.warning(f"Failed to parse token usage: {e}")
        
        return usage
    
    def _transform_to_schema(self, raw_response: str, payload: AdapterPayload, token_usage: Dict[str, int]) -> AdapterResponse:
        """
        Transform raw Copilot response to RESPONSE_SCHEMA.
        
        Args:
            raw_response: Raw text from Copilot
            payload: Original payload for context
            token_usage: Parsed token usage stats
            
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
            f"Execute based on Copilot ({self.model}) response",
            "Validate output quality",
            "Monitor for errors"
        ]
        
        if decision != "ACT":
            suggested_actions.insert(0, "Gather more context before proceeding")
        
        return AdapterResponse(
            decision=decision,
            confidence=confidence,
            rationale=f"Copilot CLI ({self.model}) response: {raw_response[:100]}...",
            vector_references=vector_references,
            suggested_actions=suggested_actions,
            fallback_needed=False,
            provider_meta={
                'provider': 'github-copilot',
                'model': self.model,
                'cli_path': self.cli_path,
                'raw_response_length': len(raw_response),
                'response_preview': raw_response[:200],
                'token_usage': token_usage,
                'input_tokens': token_usage.get('input_tokens', 0),
                'output_tokens': token_usage.get('output_tokens', 0),
                'total_tokens': token_usage.get('total_tokens', 0),
            }
        )
