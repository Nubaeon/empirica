"""
CLI Input Validation Models

Pydantic models for validating JSON inputs to CLI commands.
Addresses CWE-20: Improper Input Validation.

Usage:
    from empirica.cli.validation import PreflightInput, validate_json_input

    validated = validate_json_input(raw_json, PreflightInput)
    # validated is now a PreflightInput instance or raises ValidationError
"""

from typing import Dict, Optional, Any, Type, TypeVar, List
from pydantic import BaseModel, Field, field_validator
import json


T = TypeVar('T', bound=BaseModel)


# =============================================================================
# CASCADE Workflow Input Models
# =============================================================================

class VectorValues(BaseModel):
    """Epistemic vector values (0.0-1.0 scale)."""
    know: float = Field(ge=0.0, le=1.0, description="Knowledge level")
    uncertainty: float = Field(ge=0.0, le=1.0, description="Uncertainty level")
    context: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Context understanding")
    engagement: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Engagement level")
    clarity: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Clarity of understanding")
    coherence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Coherence of knowledge")
    signal: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Signal strength")
    density: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Information density")
    state: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Current state")
    change: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Rate of change")
    completion: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Phase-aware completion: NOETIC='Have I learned enough?' PRAXIC='Have I implemented enough?'")
    impact: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Expected impact")
    do: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Execution capability")


class PreflightInput(BaseModel):
    """Input model for preflight-submit command."""
    session_id: str = Field(min_length=1, max_length=100, description="Session identifier")
    vectors: Dict[str, float] = Field(description="Epistemic vector values")
    reasoning: Optional[str] = Field(default="", max_length=5000, description="Reasoning for assessment")
    task_context: Optional[str] = Field(default="", max_length=2000, description="Context for pattern retrieval")

    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """Validate session_id format."""
        if not v or not v.strip():
            raise ValueError('session_id cannot be empty')
        return v.strip()

    @field_validator('vectors')
    @classmethod
    def validate_vectors(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate vector values are in valid range."""
        if not v:
            raise ValueError('vectors cannot be empty')

        valid_keys = {'know', 'uncertainty', 'context', 'engagement', 'clarity',
                      'coherence', 'signal', 'density', 'state', 'change',
                      'completion', 'impact', 'do'}

        for key, value in v.items():
            if key not in valid_keys:
                raise ValueError(f'Unknown vector key: {key}')
            if not isinstance(value, (int, float)):
                raise ValueError(f'Vector {key} must be a number, got {type(value).__name__}')
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f'Vector {key} must be between 0.0 and 1.0, got {value}')

        # Require at least know and uncertainty
        if 'know' not in v or 'uncertainty' not in v:
            raise ValueError('vectors must include at least "know" and "uncertainty"')

        return v


class CheckInput(BaseModel):
    """Input model for check-submit command."""
    session_id: str = Field(min_length=1, max_length=100, description="Session identifier")
    vectors: Optional[Dict[str, float]] = Field(default=None, description="Updated vector values")
    approach: Optional[str] = Field(default="", max_length=2000, description="Planned approach")
    reasoning: Optional[str] = Field(default="", max_length=5000, description="Reasoning for check")

    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """Validate session_id is non-empty."""
        if not v or not v.strip():
            raise ValueError('session_id cannot be empty')
        return v.strip()

    @field_validator('vectors')
    @classmethod
    def validate_vectors(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        """Validate optional vector values are in valid 0.0-1.0 range."""
        if v is None:
            return v
        for key, value in v.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f'Vector {key} must be a number')
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f'Vector {key} must be between 0.0 and 1.0')
        return v


class PostflightInput(BaseModel):
    """Input model for postflight-submit command."""
    session_id: str = Field(min_length=1, max_length=100, description="Session identifier")
    vectors: Dict[str, float] = Field(description="Final epistemic vector values")
    reasoning: Optional[str] = Field(default="", max_length=5000, description="Reasoning for assessment")
    learnings: Optional[str] = Field(default="", max_length=5000, description="Key learnings from session")
    goal_id: Optional[str] = Field(default=None, max_length=100, description="Associated goal ID")

    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """Validate session_id is non-empty."""
        if not v or not v.strip():
            raise ValueError('session_id cannot be empty')
        return v.strip()

    @field_validator('vectors')
    @classmethod
    def validate_vectors(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Validate required vector values are in valid 0.0-1.0 range."""
        if not v:
            raise ValueError('vectors cannot be empty')
        for key, value in v.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f'Vector {key} must be a number')
            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f'Vector {key} must be between 0.0 and 1.0')
        return v


# =============================================================================
# Finding/Unknown Input Models
# =============================================================================

class FindingInput(BaseModel):
    """Input model for finding-log command."""
    session_id: str = Field(min_length=1, max_length=100)
    finding: str = Field(min_length=1, max_length=5000)
    impact: float = Field(ge=0.0, le=1.0, default=0.5)
    domain: Optional[str] = Field(default=None, max_length=100)
    goal_id: Optional[str] = Field(default=None, max_length=100)


class UnknownInput(BaseModel):
    """Input model for unknown-log command."""
    session_id: str = Field(min_length=1, max_length=100)
    unknown: str = Field(min_length=1, max_length=5000)
    impact: float = Field(ge=0.0, le=1.0, default=0.5)
    goal_id: Optional[str] = Field(default=None, max_length=100)


# =============================================================================
# Validation Utilities
# =============================================================================

def validate_json_input(raw_json: str, model: Type[T]) -> T:
    """
    Parse and validate JSON input against a Pydantic model.

    Args:
        raw_json: Raw JSON string
        model: Pydantic model class to validate against

    Returns:
        Validated model instance

    Raises:
        ValueError: If JSON is invalid or validation fails
    """
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

    return model.model_validate(data)


def validate_dict_input(data: Dict[str, Any], model: Type[T]) -> T:
    """
    Validate a dictionary against a Pydantic model.

    Args:
        data: Dictionary to validate
        model: Pydantic model class to validate against

    Returns:
        Validated model instance

    Raises:
        ValueError: If validation fails
    """
    return model.model_validate(data)


def safe_validate(data: Dict[str, Any], model: Type[T]) -> tuple[Optional[T], Optional[str]]:
    """
    Safely validate data, returning (validated, None) or (None, error_message).

    Args:
        data: Dictionary to validate
        model: Pydantic model class

    Returns:
        Tuple of (validated_model, error_message)
    """
    try:
        validated = model.model_validate(data)
        return validated, None
    except Exception as e:
        return None, str(e)
