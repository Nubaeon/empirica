"""
API Authentication Middleware

Provides API key authentication for Flask routes.
Supports both header-based and query parameter authentication.

Configuration:
    EMPIRICA_API_KEY: Required API key (set in environment)
    EMPIRICA_API_AUTH_ENABLED: Enable/disable auth (default: true in production)

Usage:
    from empirica.api.auth import require_api_key

    @app.route("/api/v1/protected")
    @require_api_key
    def protected_endpoint():
        return jsonify({"ok": True})
"""

import os
import hmac
import secrets
import logging
from functools import wraps
from typing import Optional, Callable

from flask import request, jsonify, g

logger = logging.getLogger(__name__)

# Auth configuration
_AUTH_ENABLED: Optional[bool] = None
_API_KEY: Optional[str] = None


def _is_auth_enabled() -> bool:
    """Check if API authentication is enabled."""
    global _AUTH_ENABLED
    if _AUTH_ENABLED is None:
        # Default: disabled for local-first usage
        # Enable explicitly for cloud/remote deployments
        env_value = os.environ.get("EMPIRICA_API_AUTH_ENABLED", "").lower()

        if env_value == "true":
            _AUTH_ENABLED = True
            logger.info("API authentication ENABLED via EMPIRICA_API_AUTH_ENABLED")
        else:
            _AUTH_ENABLED = False

    return _AUTH_ENABLED


def _get_api_key() -> Optional[str]:
    """Get configured API key."""
    global _API_KEY
    if _API_KEY is None:
        _API_KEY = os.environ.get("EMPIRICA_API_KEY")
        if _API_KEY and len(_API_KEY) < 32:
            logger.warning("EMPIRICA_API_KEY is shorter than recommended (32+ chars)")
    return _API_KEY


def generate_api_key(length: int = 32) -> str:
    """
    Generate a secure random API key.

    Args:
        length: Key length in bytes (default 32, produces 64 hex chars)

    Returns:
        Hex-encoded random key
    """
    return secrets.token_hex(length)


def validate_api_key(provided_key: str) -> bool:
    """
    Validate an API key using constant-time comparison.

    Args:
        provided_key: Key provided by client

    Returns:
        True if key is valid
    """
    expected_key = _get_api_key()
    if not expected_key:
        logger.error("No EMPIRICA_API_KEY configured")
        return False

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(provided_key, expected_key)


def extract_api_key() -> Optional[str]:
    """
    Extract API key from request.

    Checks in order:
    1. X-API-Key header
    2. Authorization: Bearer <key>
    3. api_key query parameter (not recommended for production)

    Returns:
        API key if found, None otherwise
    """
    # Check X-API-Key header (preferred)
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return api_key

    # Check Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]

    # Check query parameter (fallback, logs warning)
    api_key = request.args.get("api_key")
    if api_key:
        logger.warning(
            f"API key provided via query parameter for {request.path} - "
            "use X-API-Key header instead"
        )
        return api_key

    return None


def require_api_key(f: Callable) -> Callable:
    """
    Decorator to require API key authentication.

    Usage:
        @app.route("/api/v1/sessions")
        @require_api_key
        def list_sessions():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Skip auth if disabled
        if not _is_auth_enabled():
            return f(*args, **kwargs)

        # Check if API key is configured
        if not _get_api_key():
            logger.error("API authentication enabled but EMPIRICA_API_KEY not set")
            return jsonify({
                "ok": False,
                "error": "server_configuration_error",
                "message": "API authentication not configured",
                "status_code": 500
            }), 500

        # Extract and validate key
        provided_key = extract_api_key()

        if not provided_key:
            return jsonify({
                "ok": False,
                "error": "authentication_required",
                "message": "API key required. Provide via X-API-Key header.",
                "status_code": 401
            }), 401

        if not validate_api_key(provided_key):
            logger.warning(f"Invalid API key attempt for {request.path}")
            return jsonify({
                "ok": False,
                "error": "invalid_api_key",
                "message": "Invalid API key",
                "status_code": 403
            }), 403

        return f(*args, **kwargs)

    return decorated


def optional_api_key(f: Callable) -> Callable:
    """
    Decorator for optional API key authentication.

    Sets g.authenticated = True/False based on key presence.
    Does not reject unauthenticated requests.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        g.authenticated = False

        if not _is_auth_enabled():
            g.authenticated = True
            return f(*args, **kwargs)

        provided_key = extract_api_key()
        if provided_key and validate_api_key(provided_key):
            g.authenticated = True

        return f(*args, **kwargs)

    return decorated


class APIKeyMiddleware:
    """
    WSGI middleware for API key authentication.

    Applies to all routes matching a prefix.

    Usage:
        app.wsgi_app = APIKeyMiddleware(app.wsgi_app, prefix="/api/v1")
    """

    def __init__(self, app, prefix: str = "/api/v1"):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")

        # Only apply to matching prefix
        if not path.startswith(self.prefix):
            return self.app(environ, start_response)

        # Skip if auth disabled
        if not _is_auth_enabled():
            return self.app(environ, start_response)

        # Check for API key
        api_key = None

        # Check X-API-Key header
        api_key = environ.get("HTTP_X_API_KEY")

        # Check Authorization header
        if not api_key:
            auth_header = environ.get("HTTP_AUTHORIZATION", "")
            if auth_header.startswith("Bearer "):
                api_key = auth_header[7:]

        # Validate
        if not api_key or not validate_api_key(api_key):
            status = "401 Unauthorized" if not api_key else "403 Forbidden"
            response_body = b'{"ok": false, "error": "authentication_required"}'
            response_headers = [
                ("Content-Type", "application/json"),
                ("Content-Length", str(len(response_body)))
            ]
            start_response(status, response_headers)
            return [response_body]

        return self.app(environ, start_response)
