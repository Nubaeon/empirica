"""
Config Validator - JSON Schema validation for AI-first CLI

Validates config files against JSON schemas and provides helpful error messages.
"""

import json
import os
from typing import Dict, Optional, Tuple


def validate_config(config_data: dict, schema_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate config against JSON schema.

    Args:
        config_data: Config dictionary to validate
        schema_name: Schema name (e.g., 'preflight_config', 'check_config')

    Returns:
        (is_valid, error_message)
    """
    try:
        # Try to import jsonschema (optional dependency)
        try:
            import jsonschema
            from jsonschema import validate, ValidationError
        except ImportError:
            # If jsonschema not installed, skip validation (graceful degradation)
            return True, None

        # Load schema file
        schema_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'schemas')
        schema_path = os.path.join(schema_dir, f'{schema_name}.json')

        if not os.path.exists(schema_path):
            # Schema file doesn't exist, skip validation
            return True, None

        with open(schema_path, 'r') as f:
            schema = json.load(f)

        # Validate
        try:
            validate(instance=config_data, schema=schema)
            return True, None
        except ValidationError as e:
            # Build helpful error message
            error_path = ' → '.join(str(p) for p in e.path) if e.path else 'root'
            error_msg = f"Validation error at {error_path}: {e.message}"

            # Add hint about which field is problematic
            if e.validator == 'required':
                missing = e.message.split("'")[1] if "'" in e.message else "unknown"
                error_msg += f"\n\nHint: Missing required field '{missing}'"
            elif e.validator == 'type':
                expected = e.validator_value
                error_msg += f"\n\nHint: Expected type '{expected}'"
            elif e.validator in ['minimum', 'maximum']:
                error_msg += f"\n\nHint: Value must be between 0.0 and 1.0"
            elif e.validator == 'pattern':
                error_msg += f"\n\nHint: Expected UUID format (e.g., '12345678-1234-1234-1234-123456789abc')"

            return False, error_msg

    except Exception as e:
        # Validation error - don't fail command, just warn
        return True, f"Warning: Could not validate config: {str(e)}"


def print_validation_error(error_message: str, schema_name: str):
    """Print formatted validation error with helpful info."""
    print(json.dumps({
        "ok": False,
        "error": "Config validation failed",
        "details": error_message,
        "hint": f"Check your config against schema: empirica/schemas/{schema_name}.json",
        "example": f"See /tmp/{schema_name.replace('_config', '')}_config_example.json for correct format"
    }, indent=2))


# Schema name mapping for commands
SCHEMA_MAP = {
    'preflight-submit': 'preflight_config',
    'check': 'check_config',
    'postflight-submit': 'postflight_config',
    'session-create': 'session_config',
    'goals-create': 'goal_config',
    'finding-log': 'finding_config',
    'unknown-log': 'unknown_config',
    'deadend-log': 'deadend_config'
}


def get_schema_name(command: str) -> Optional[str]:
    """Get schema name for a command."""
    return SCHEMA_MAP.get(command)
