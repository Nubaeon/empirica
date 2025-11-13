"""
Rovodev Adapter - Atlassian Rovo Dev CLI Integration

Uses Rovo Dev CLI server mode for programmatic access to Rovo Dev.
Provides 20M tokens/day for free!

Key Features:
- Server mode API (HTTP REST)
- Stream-based responses
- Session management
- Tool execution support
- Free 20M tokens/day

Usage:
    adapter = RovodevAdapter()
    response = adapter.call(payload, token_meta)
"""

import os
import json
import logging
import subprocess
import time
import requests
from typing import Dict, Any, Optional
from pathlib import Path
from empirica.config.credentials_loader import get_credentials_loader

logger = logging.getLogger(__name__)

# Adapter metadata
ADAPTER_METADATA = {
    'version': '1.0.0',
    'cost_per_token': 0.0,  # FREE! 20M tokens/day
    'type': 'cli_server',
    'provider': 'atlassian',
    'model': 'Rovo Dev',
    'description': 'Atlassian Rovo Dev CLI adapter using server mode',
    'capabilities': ['text', 'code_analysis', 'file_operations', 'tool_calls'],
    'limitations': [
        'Requires ACLI authentication',
        'Server mode runs on localhost',
        '20M free tokens/day limit'
    ],
    'notes': 'Uses HTTP REST API via acli rovodev serve'
}


class RovodevAdapter:
    """
    Adapter for Atlassian Rovo Dev CLI via server mode.
    
    Uses `acli rovodev serve` to start an HTTP server and communicate via REST API.
    """
    
    def __init__(self, model: str = None, config: Dict[str, Any] = None):
        """
        Initialize Rovodev adapter.
        
        Args:
            model: Model to use (defaults to config default_model)
            config: Configuration dict with optional:
                   - port: Server port (default: 8123)
                   - auto_start: Auto-start server (default: True)
                   - timeout: Request timeout (default: 60)
        """
        # Load credentials
        self.loader = get_credentials_loader()
        self.provider_config = self.loader.get_provider_config('rovodev')
        
        if not self.provider_config:
            raise ValueError("Rovodev credentials not configured")
        
        # Set model (use provided or default)
        self.model = model or self.loader.get_default_model('rovodev')
        
        # Validate model
        if not self.loader.validate_model('rovodev', self.model):
            available = self.loader.get_available_models('rovodev')
            raise ValueError(
                f"Model '{self.model}' not available for Rovodev. "
                f"Available: {available}"
            )
        
        # Get API credentials
        self.api_key = self.loader.get_api_key('rovodev')
        self.base_api_url = self.loader.get_base_url('rovodev')
        self.headers = self.loader.get_headers('rovodev')
        
        # Config options for CLI server mode
        self.config = config or {}
        self.port = self.config.get('port', 8123)
        self.base_url = f"http://localhost:{self.port}"
        self.timeout = self.config.get('timeout', 60)
        self.auto_start = self.config.get('auto_start', True)
        
        self.server_process = None
        self.server_started = False
        
        logger.info(f"✅ RovodevAdapter initialized (model: {self.model}, port: {self.port})")
    
    def _start_server(self):
        """Start Rovo Dev server in background."""
        if self.server_started:
            return True
        
        try:
            # Check if server already running
            try:
                response = requests.get(f"{self.base_url}/healthcheck", timeout=2)
                if response.status_code == 200:
                    logger.info("✅ Rovo Dev server already running")
                    self.server_started = True
                    return True
            except:
                pass
            
            # Start server
            logger.info(f"🚀 Starting Rovo Dev server on port {self.port}...")
            
            # Start in background
            self.server_process = subprocess.Popen(
                ['acli', 'rovodev', 'serve', str(self.port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            
            # Wait for server to start (up to 10 seconds)
            for i in range(20):
                time.sleep(0.5)
                try:
                    response = requests.get(f"{self.base_url}/healthcheck", timeout=2)
                    if response.status_code == 200:
                        logger.info(f"✅ Rovo Dev server started successfully")
                        self.server_started = True
                        return True
                except:
                    continue
            
            logger.error("❌ Failed to start Rovo Dev server")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error starting Rovo Dev server: {e}")
            return False
    
    def _stop_server(self):
        """Stop Rovo Dev server."""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                logger.info("✅ Rovo Dev server stopped")
            except:
                self.server_process.kill()
        
        self.server_started = False
    
    def health_check(self) -> bool:
        """
        Check if Rovo Dev server is accessible.
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            # Try to start server if configured
            if self.auto_start and not self.server_started:
                if not self._start_server():
                    return False
            
            # Check health endpoint
            response = requests.get(
                f"{self.base_url}/healthcheck",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.debug(f"✅ Rovo Dev health: {data}")
                return data.get('status') == 'healthy'
            
            return False
            
        except Exception as e:
            logger.warning(f"❌ Rovo Dev health check failed: {e}")
            return False
    
    def authenticate(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Authenticate with Rovo Dev.
        
        Note: Authentication is handled by ACLI auth system.
        This just verifies the server is accessible.
        
        Args:
            meta: Metadata about the auth request
            
        Returns:
            Dict with token metadata
        """
        # Start server if not running
        if self.auto_start and not self.server_started:
            if not self._start_server():
                raise RuntimeError("Failed to start Rovo Dev server. Ensure 'acli rovodev auth' is configured.")
        
        # Verify health
        if not self.health_check():
            raise RuntimeError("Rovo Dev server not accessible. Check ACLI authentication.")
        
        logger.info(f"✅ RovodevAdapter authenticated")
        
        return {
            "provider": "rovodev",
            "model": "Rovo Dev",
            "authenticated": True,
            "server_url": self.base_url,
            "free_tokens": "20M/day"
        }
    
    def call(
        self, 
        payload: Any,  # AdapterPayload
        token_meta: Dict[str, Any]
    ):
        """
        Execute Rovo Dev query via server mode.
        
        Args:
            payload: Standard adapter payload (supports epistemic snapshots)
            token_meta: Authentication token metadata
            
        Returns:
            AdapterResponse on success, AdapterError on failure
        """
        try:
            # Import here to avoid circular dependency
            from empirica.core.modality.plugin_registry import AdapterResponse, AdapterError
            
            # Phase 4: Increment transfer count if snapshot present
            if payload.epistemic_snapshot:
                payload.epistemic_snapshot.increment_transfer_count()
                logger.info(f"📸 Snapshot transfer #{payload.epistemic_snapshot.transfer_count} to RovoDev")
            
            # Ensure server is running
            if not self.server_started:
                self.authenticate(token_meta)
            
            # Phase 4: Get augmented prompt (includes snapshot context if present)
            augmented_query = payload.get_augmented_prompt()
            
            # Build message
            query = augmented_query
            if payload.system:
                query = f"{payload.system}\n\n{augmented_query}"
            
            logger.debug(f"📡 Calling Rovo Dev: {query[:100]}...")
            
            # Step 1: Set chat message
            set_response = requests.post(
                f"{self.base_url}/v3/set_chat_message",
                json={
                    "message": query,
                    "enable_deep_plan": False
                },
                timeout=10
            )
            
            if set_response.status_code != 200:
                return AdapterError(
                    code="api_error",
                    message=f"Failed to set chat message: {set_response.status_code}",
                    provider="rovodev",
                    recoverable=True,
                    meta={'status_code': set_response.status_code}
                )
            
            # Step 2: Stream response
            stream_response = requests.get(
                f"{self.base_url}/v3/stream_chat",
                stream=True,
                timeout=self.timeout
            )
            
            if stream_response.status_code != 200:
                return AdapterError(
                    code="api_error",
                    message=f"Failed to stream chat: {stream_response.status_code}",
                    provider="rovodev",
                    recoverable=True,
                    meta={'status_code': stream_response.status_code}
                )
            
            # Collect response from stream
            response_text = ""
            full_response_data = []
            
            for line in stream_response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            full_response_data.append(data)
                            
                            # Extract text content
                            if isinstance(data, dict):
                                if 'text' in data:
                                    response_text += data['text']
                                elif 'content' in data:
                                    response_text += data['content']
                        except json.JSONDecodeError:
                            continue
            
            if not response_text:
                response_text = "Rovo Dev completed the task (no text response)"
            
            # Transform to RESPONSE_SCHEMA
            adapter_response = self._transform_to_schema(
                response_text=response_text,
                full_data=full_response_data,
                payload=payload
            )
            
            logger.debug(f"✅ Rovo Dev response: {adapter_response.decision} (confidence: {adapter_response.confidence:.2f})")
            return adapter_response
            
        except requests.Timeout:
            logger.error(f"⏱️  Rovo Dev timeout after {self.timeout}s")
            return AdapterError(
                code="timeout",
                message=f"Rovo Dev request timed out after {self.timeout}s",
                provider="rovodev",
                recoverable=True,
                meta={'timeout': self.timeout}
            )
        except Exception as e:
            logger.error(f"❌ Rovo Dev error: {e}")
            return AdapterError(
                code="unknown",
                message=f"Unexpected error: {e}",
                provider="rovodev",
                recoverable=True,
                meta={'error': str(e)}
            )
    
    def _transform_to_schema(
        self, 
        response_text: str,
        full_data: list,
        payload: Any
    ):
        """
        Transform Rovo Dev response to RESPONSE_SCHEMA.
        
        Args:
            response_text: Collected text from stream
            full_data: Full stream data
            payload: Original payload
            
        Returns:
            AdapterResponse with 13 epistemic vectors
        """
        from empirica.core.modality.plugin_registry import AdapterResponse
        
        # Heuristic decision classification
        response_lower = response_text.lower()
        
        # Estimate decision based on response content
        if any(word in response_lower for word in ['uncertain', 'unclear', 'investigate', 'need more']):
            decision = "INVESTIGATE"
            base_confidence = 0.5
        elif any(word in response_lower for word in ['verify', 'check', 'confirm']):
            decision = "CHECK"
            base_confidence = 0.65
        elif any(word in response_lower for word in ['done', 'completed', 'created', 'updated', 'fixed']):
            decision = "ACT"
            base_confidence = 0.8
        else:
            decision = "ACT"
            base_confidence = 0.7
        
        # Adjust confidence based on response quality
        response_words = len(response_text.split())
        if response_words > 100:
            confidence = min(0.95, base_confidence + 0.1)
        elif response_words > 50:
            confidence = base_confidence
        else:
            confidence = max(0.5, base_confidence - 0.1)
        
        # Generate 13 epistemic vectors (heuristic Phase 1)
        vector_references = {
            # Foundation Layer
            'know': min(1.0, response_words / 150),
            'do': 0.9 if decision == "ACT" else 0.6,  # Rovo Dev is action-oriented
            'context': 0.85,  # Has full file system context
            
            # Comprehension Layer
            'clarity': 0.8 if response_words > 50 else 0.6,
            'coherence': 0.85,  # Rovo Dev is coherent
            'signal': 0.8,
            'density': min(1.0, response_words / 200),
            
            # Execution Layer
            'state': 0.8,
            'change': 0.7 if decision == "ACT" else 0.5,
            'completion': 0.85 if decision == "ACT" else 0.6,
            'impact': 0.75,
            
            # Meta Layer
            'engagement': 0.9,  # Rovo Dev is highly engaged
            'uncertainty': 1.0 - confidence
        }
        
        # Generate suggested actions
        suggested_actions = []
        if decision == "INVESTIGATE":
            suggested_actions = [
                "Gather more information",
                "Analyze requirements",
                "Review documentation"
            ]
        elif decision == "CHECK":
            suggested_actions = [
                "Verify the changes",
                "Review the output",
                "Test the solution"
            ]
        else:  # ACT
            suggested_actions = [
                "Review Rovo Dev's work",
                "Test the changes",
                "Commit if satisfied"
            ]
        
        # Provider metadata
        provider_meta = {
            'provider': 'rovodev',
            'model': 'Rovo Dev',
            'server_url': self.base_url,
            'response_length': len(response_text),
            'stream_events': len(full_data),
            'cost': 0.0,  # FREE!
            'free_tokens': '20M/day'
        }
        
        return AdapterResponse(
            decision=decision,
            confidence=confidence,
            rationale=f"Rovo Dev: {response_text[:200]}...",
            vector_references=vector_references,
            suggested_actions=suggested_actions,
            fallback_needed=False,
            provider_meta=provider_meta
        )
    
    def __del__(self):
        """Cleanup: stop server if we started it."""
        if self.auto_start and self.server_process:
            self._stop_server()


if __name__ == "__main__":
    # Test Rovodev adapter
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 70)
    print("              ROVODEV ADAPTER TEST")
    print("=" * 70)
    
    adapter = RovodevAdapter()
    
    # Test health check
    print("\n🧪 Test 1: Health Check")
    healthy = adapter.health_check()
    print(f"   {'✅' if healthy else '❌'} Health: {healthy}")
    
    if healthy:
        # Test authentication
        print("\n🧪 Test 2: Authentication")
        try:
            auth = adapter.authenticate({})
            print(f"   ✅ Authenticated: {auth}")
        except Exception as e:
            print(f"   ❌ Auth failed: {e}")
    
    print("\n" + "=" * 70)
    print("                  ✅ TEST COMPLETE")
    print("=" * 70)
