"""
Empirica Persona System - Epistemic Vector Profiles

Personas are defined as epistemic vector configurations:
- Priors: Starting knowledge/confidence in domain
- Thresholds: Gates for uncertainty, confidence, signal quality
- Weights: Balance between foundation/comprehension/execution/engagement
- Focus domains: Semantic tags for domain expertise

Personas are stored as JSON files in .empirica/personas/ and loaded
via system prompts or MCP configuration. No runtime harness needed.

Components:
- PersonaProfile: Persona configuration schema
- PersonaManager: Create, load, validate personas from JSON files
- Validation: Schema validation for persona profiles

Usage:
    from empirica.core.persona import PersonaManager

    # Load security expert persona
    manager = PersonaManager()
    persona = manager.load_persona("security_expert")

    # Use persona config in PREFLIGHT vectors
    priors = persona.epistemic_config.priors
"""

from .persona_profile import (
    PersonaProfile,
    EpistemicConfig,
    SigningIdentityConfig,
    CapabilitiesConfig,
    SentinelConfig,
    PersonaMetadata
)
from .persona_manager import PersonaManager
from .validation import validate_persona_profile, ValidationError

__all__ = [
    # Core
    'PersonaProfile',
    'EpistemicConfig',
    'SigningIdentityConfig',
    'CapabilitiesConfig',
    'SentinelConfig',
    'PersonaMetadata',
    # Management
    'PersonaManager',
    'validate_persona_profile',
    'ValidationError',
]

__version__ = '4.0.0'  # Phase 4 - Simplified (harness/sentinel removed)
