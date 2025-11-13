"""
AuthManager - Phase 0

Client for Sentinel/Cognitive Vault credential management.
Handles token requests and graceful fallback when Sentinel unavailable.

Usage:
    auth = AuthManager()
    token_meta = auth.get_token("openai", scopes=["chat"], reason="User query")
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
import time

logger = logging.getLogger(__name__)


@dataclass
class TokenRequest:
    """Request for authentication token"""
    provider: str
    scopes: List[str]
    reason: str
    requester: str = "empirica-mcp"
    meta: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.meta is None:
            self.meta = {}


@dataclass
class TokenResponse:
    """Response containing authentication token"""
    token: str
    provider: str
    scopes: List[str]
    expires_at: Optional[float] = None
    token_type: str = "Bearer"
    meta: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.meta is None:
            self.meta = {}
    
    def is_expired(self) -> bool:
        """Check if token is expired"""
        if self.expires_at is None:
            return False
        return time.time() >= self.expires_at


class AuthManager:
    """
    Manages authentication tokens via Sentinel/Cognitive Vault.
    
    Phase 0: Graceful fallback to environment variables when Sentinel unavailable.
    Future: Full integration with Sentinel API for device flow, approvals, etc.
    """
    
    def __init__(self, sentinel_url: Optional[str] = None, fallback_mode: str = "env"):
        """
        Initialize AuthManager.
        
        Args:
            sentinel_url: URL of Sentinel service (default: http://localhost:8765)
            fallback_mode: Fallback when Sentinel unavailable ("env" or "error")
        """
        self.sentinel_url = sentinel_url or os.getenv("SENTINEL_URL", "http://localhost:8765")
        self.fallback_mode = fallback_mode
        self.sentinel_available = False
        self._token_cache: Dict[str, TokenResponse] = {}
        
        # Check if Sentinel is available
        self._check_sentinel_availability()
    
    def _check_sentinel_availability(self):
        """Check if Sentinel service is reachable"""
        try:
            # Try to import requests (needed for Sentinel API calls)
            import requests
            
            # Try to ping Sentinel health endpoint
            response = requests.get(f"{self.sentinel_url}/health", timeout=2)
            if response.status_code == 200:
                self.sentinel_available = True
                logger.info(f"✅ Sentinel available at {self.sentinel_url}")
                return
        except Exception as e:
            logger.debug(f"Sentinel not available: {e}")
        
        self.sentinel_available = False
        if self.fallback_mode == "env":
            logger.info(f"⚠️  Sentinel unavailable, using environment variable fallback")
        else:
            logger.warning(f"⚠️  Sentinel unavailable, auth will fail")
    
    def get_token(
        self,
        provider: str,
        scopes: Optional[List[str]] = None,
        reason: str = "Model call",
        force_refresh: bool = False
    ) -> TokenResponse:
        """
        Get authentication token for a provider.
        
        Args:
            provider: Provider identifier (e.g., "openai", "anthropic")
            scopes: Required scopes (e.g., ["chat", "embeddings"])
            reason: Human-readable reason for token request
            force_refresh: Force new token even if cached
            
        Returns:
            TokenResponse with token and metadata
            
        Raises:
            AuthenticationError: If unable to obtain token
        """
        if scopes is None:
            scopes = ["default"]
        
        # Check cache first
        cache_key = f"{provider}:{':'.join(sorted(scopes))}"
        if not force_refresh and cache_key in self._token_cache:
            cached = self._token_cache[cache_key]
            if not cached.is_expired():
                logger.debug(f"🔐 Using cached token for {provider}")
                return cached
        
        # Try Sentinel first
        if self.sentinel_available:
            try:
                token_response = self._request_from_sentinel(provider, scopes, reason)
                self._token_cache[cache_key] = token_response
                return token_response
            except Exception as e:
                logger.error(f"Sentinel token request failed: {e}")
                # Fall through to fallback
        
        # Fallback to environment variables
        if self.fallback_mode == "env":
            token_response = self._request_from_env(provider, scopes)
            self._token_cache[cache_key] = token_response
            return token_response
        
        raise AuthenticationError(f"Unable to obtain token for {provider}")
    
    def _request_from_sentinel(
        self,
        provider: str,
        scopes: List[str],
        reason: str
    ) -> TokenResponse:
        """
        Request token from Sentinel API.
        
        Args:
            provider: Provider identifier
            scopes: Required scopes
            reason: Reason for request
            
        Returns:
            TokenResponse
            
        Raises:
            Exception: If request fails
        """
        import requests
        
        request_data = asdict(TokenRequest(
            provider=provider,
            scopes=scopes,
            reason=reason
        ))
        
        response = requests.post(
            f"{self.sentinel_url}/auth/token",
            json=request_data,
            timeout=10
        )
        
        if response.status_code != 200:
            raise Exception(f"Sentinel returned {response.status_code}: {response.text}")
        
        data = response.json()
        logger.info(f"🔐 Obtained token from Sentinel for {provider}")
        
        return TokenResponse(
            token=data['token'],
            provider=provider,
            scopes=scopes,
            expires_at=data.get('expires_at'),
            token_type=data.get('token_type', 'Bearer'),
            meta=data.get('meta', {})
        )
    
    def _request_from_env(
        self,
        provider: str,
        scopes: List[str]
    ) -> TokenResponse:
        """
        Get token from environment variables (fallback).
        
        Looks for environment variables like:
        - OPENAI_API_KEY
        - ANTHROPIC_API_KEY
        - {PROVIDER}_API_KEY
        
        Args:
            provider: Provider identifier
            scopes: Required scopes (unused in env fallback)
            
        Returns:
            TokenResponse
            
        Raises:
            AuthenticationError: If env var not found
        """
        # Common provider -> env var mappings
        env_var_map = {
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY',
            'claude': 'ANTHROPIC_API_KEY',
            'gemini': 'GEMINI_API_KEY',
            'google': 'GEMINI_API_KEY',
            'qwen': 'QWEN_API_KEY',
            'copilot': 'GITHUB_TOKEN',
        }
        
        # Try mapped env var first
        env_var = env_var_map.get(provider.lower())
        if env_var is None:
            # Try generic pattern
            env_var = f"{provider.upper()}_API_KEY"
        
        token = os.getenv(env_var)
        
        if token is None:
            raise AuthenticationError(
                f"No token found for {provider}. "
                f"Set {env_var} environment variable or start Sentinel."
            )
        
        logger.info(f"🔐 Using environment variable {env_var} for {provider}")
        
        return TokenResponse(
            token=token,
            provider=provider,
            scopes=scopes,
            expires_at=None,  # Env tokens don't expire
            token_type='Bearer',
            meta={'source': 'environment'}
        )
    
    def revoke_token(self, provider: str):
        """
        Revoke cached token for provider.
        
        Args:
            provider: Provider identifier
        """
        # Remove all cached tokens for this provider
        keys_to_remove = [k for k in self._token_cache if k.startswith(f"{provider}:")]
        for key in keys_to_remove:
            del self._token_cache[key]
        
        logger.info(f"🔐 Revoked cached tokens for {provider}")
        
        # If Sentinel available, notify it
        if self.sentinel_available:
            try:
                import requests
                requests.post(
                    f"{self.sentinel_url}/auth/revoke",
                    json={'provider': provider},
                    timeout=5
                )
                logger.info(f"🔐 Notified Sentinel of token revocation for {provider}")
            except Exception as e:
                logger.debug(f"Failed to notify Sentinel of revocation: {e}")
    
    def clear_cache(self):
        """Clear all cached tokens"""
        self._token_cache.clear()
        logger.info("🔐 Cleared token cache")


class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass


# Convenience function for backward compatibility
def get_token(provider: str, scopes: Optional[List[str]] = None, reason: str = "Model call") -> TokenResponse:
    """
    Get authentication token for a provider.
    
    This is a convenience function that creates a singleton AuthManager instance.
    
    Args:
        provider: Provider identifier
        scopes: Required scopes
        reason: Reason for request
        
    Returns:
        TokenResponse
    """
    global _auth_manager_singleton
    
    if '_auth_manager_singleton' not in globals():
        _auth_manager_singleton = AuthManager()
    
    return _auth_manager_singleton.get_token(provider, scopes, reason)
