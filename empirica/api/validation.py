"""
API Input Validation

Provides validation helpers for API parameters.
Prevents injection attacks, enforces limits, and validates formats.

Usage:
    from empirica.api.validation import validate_session_id, validate_limit

    @app.route("/sessions/<session_id>")
    def get_session(session_id: str):
        if error := validate_session_id(session_id):
            return error
        ...
"""

import re
import logging
from typing import Optional, Tuple, Any
from flask import jsonify

logger = logging.getLogger(__name__)

# Validation patterns
UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)
SAFE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,128}$')
ISO_TIMESTAMP_PATTERN = re.compile(
    r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?)?$'
)

# Limits
MAX_LIMIT = 1000
MAX_STRING_LENGTH = 10000
MAX_SESSION_ID_LENGTH = 64
MAX_AI_ID_LENGTH = 64
MAX_REASONING_LENGTH = 5000


def validation_error(message: str, param: str, status_code: int = 400) -> Tuple[Any, int]:
    """Create standardized validation error response."""
    logger.warning(f"Validation error on {param}: {message}")
    return jsonify({
        "ok": False,
        "error": "validation_error",
        "message": message,
        "param": param,
        "status_code": status_code
    }), status_code


def validate_session_id(session_id: str) -> Optional[Tuple[Any, int]]:
    """
    Validate session ID format.

    Accepts:
    - UUID format: 8-4-4-4-12 hex characters
    - Safe ID format: alphanumeric, underscore, hyphen (max 128 chars)

    Returns:
        None if valid, error response tuple if invalid
    """
    if not session_id:
        return validation_error("Session ID is required", "session_id")

    if len(session_id) > MAX_SESSION_ID_LENGTH:
        return validation_error(
            f"Session ID too long (max {MAX_SESSION_ID_LENGTH} chars)",
            "session_id"
        )

    if not (UUID_PATTERN.match(session_id) or SAFE_ID_PATTERN.match(session_id)):
        return validation_error(
            "Invalid session ID format. Use UUID or alphanumeric characters.",
            "session_id"
        )

    return None


def validate_ai_id(ai_id: str) -> Optional[Tuple[Any, int]]:
    """
    Validate AI ID format.

    Accepts alphanumeric, underscore, hyphen (max 64 chars).

    Returns:
        None if valid, error response tuple if invalid
    """
    if not ai_id:
        return validation_error("AI ID is required", "ai_id")

    if len(ai_id) > MAX_AI_ID_LENGTH:
        return validation_error(
            f"AI ID too long (max {MAX_AI_ID_LENGTH} chars)",
            "ai_id"
        )

    if not SAFE_ID_PATTERN.match(ai_id):
        return validation_error(
            "Invalid AI ID format. Use alphanumeric, underscore, or hyphen.",
            "ai_id"
        )

    return None


def validate_limit(limit: Any, default: int = 20) -> Tuple[int, Optional[Tuple[Any, int]]]:
    """
    Validate and sanitize limit parameter.

    Args:
        limit: Raw limit value (string from query param)
        default: Default value if not provided

    Returns:
        (sanitized_limit, error_response)
        error_response is None if valid
    """
    if limit is None:
        return default, None

    try:
        limit_int = int(limit)
    except (ValueError, TypeError):
        return default, validation_error(
            "Limit must be a positive integer",
            "limit"
        )

    if limit_int < 1:
        return default, validation_error(
            "Limit must be at least 1",
            "limit"
        )

    if limit_int > MAX_LIMIT:
        return MAX_LIMIT, None  # Silently cap at max

    return limit_int, None


def validate_offset(offset: Any, default: int = 0) -> Tuple[int, Optional[Tuple[Any, int]]]:
    """
    Validate and sanitize offset parameter.

    Args:
        offset: Raw offset value
        default: Default value if not provided

    Returns:
        (sanitized_offset, error_response)
    """
    if offset is None:
        return default, None

    try:
        offset_int = int(offset)
    except (ValueError, TypeError):
        return default, validation_error(
            "Offset must be a non-negative integer",
            "offset"
        )

    if offset_int < 0:
        return default, validation_error(
            "Offset must be non-negative",
            "offset"
        )

    return offset_int, None


def validate_timestamp(timestamp: Optional[str]) -> Optional[Tuple[Any, int]]:
    """
    Validate ISO timestamp format.

    Returns:
        None if valid or not provided, error response if invalid
    """
    if not timestamp:
        return None

    if len(timestamp) > 64:
        return validation_error(
            "Timestamp too long",
            "timestamp"
        )

    if not ISO_TIMESTAMP_PATTERN.match(timestamp):
        return validation_error(
            "Invalid timestamp format. Use ISO 8601 (e.g., 2026-02-08T10:00:00Z)",
            "timestamp"
        )

    return None


def validate_string_length(
    value: Optional[str],
    param_name: str,
    max_length: int = MAX_STRING_LENGTH,
    required: bool = False
) -> Optional[Tuple[Any, int]]:
    """
    Validate string length.

    Args:
        value: String to validate
        param_name: Parameter name for error messages
        max_length: Maximum allowed length
        required: Whether the field is required

    Returns:
        None if valid, error response if invalid
    """
    if value is None or value == "":
        if required:
            return validation_error(f"{param_name} is required", param_name)
        return None

    if len(value) > max_length:
        return validation_error(
            f"{param_name} too long (max {max_length} chars)",
            param_name
        )

    return None


def validate_phase(phase: Optional[str]) -> Optional[Tuple[Any, int]]:
    """
    Validate CASCADE phase.

    Returns:
        None if valid or not provided, error response if invalid
    """
    if not phase:
        return None

    valid_phases = {"PREFLIGHT", "CHECK", "POSTFLIGHT", "POST-TEST"}
    if phase.upper() not in valid_phases:
        return validation_error(
            f"Invalid phase. Must be one of: {', '.join(sorted(valid_phases))}",
            "phase"
        )

    return None


def validate_vectors(vectors: Optional[dict]) -> Optional[Tuple[Any, int]]:
    """
    Validate epistemic vectors.

    Returns:
        None if valid, error response if invalid
    """
    if not vectors:
        return validation_error("Vectors are required", "vectors")

    if not isinstance(vectors, dict):
        return validation_error("Vectors must be an object", "vectors")

    valid_vector_names = {
        "know", "uncertainty", "do", "context", "clarity",
        "coherence", "signal", "density", "state", "change",
        "completion", "impact", "engagement"
    }

    for name, value in vectors.items():
        if name not in valid_vector_names:
            return validation_error(
                f"Unknown vector: {name}. Valid vectors: {', '.join(sorted(valid_vector_names))}",
                "vectors"
            )

        try:
            float_val = float(value)
        except (ValueError, TypeError):
            return validation_error(
                f"Vector '{name}' must be a number",
                "vectors"
            )

        if not 0.0 <= float_val <= 1.0:
            return validation_error(
                f"Vector '{name}' must be between 0.0 and 1.0",
                "vectors"
            )

    return None


def sanitize_sql_identifier(identifier: str) -> Optional[str]:
    """
    Sanitize SQL identifier (table/column name).

    Returns sanitized identifier or None if invalid.
    """
    # Only allow alphanumeric and underscore
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
        return None

    # Check against reserved words (basic list)
    reserved = {"select", "insert", "update", "delete", "drop", "table", "from", "where"}
    if identifier.lower() in reserved:
        return None

    return identifier
