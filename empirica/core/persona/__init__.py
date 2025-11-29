"""
Empirica Phase 3: Multi-Persona Epistemic Intelligence

This module implements specialized AI personas with:
- Epistemic priors (domain-specific starting knowledge)
- Custom thresholds and weights
- Cryptographic signing (Phase 2 integration)
- Sentinel orchestration
- Parallel CASCADE execution
- Epistemic composition (COMPOSE operation)

Components:
- PersonaProfile: Persona configuration and validation
- PersonaManager: Create, load, validate personas
- PersonaHarness: Runtime container for persona execution
- SentinelOrchestrator: Manages multi-persona coordination
- Protocol: Persona <-> Sentinel communication

Usage:
    from empirica.core.persona import PersonaManager, PersonaHarness

    # Create security expert persona
    manager = PersonaManager()
    persona = manager.create_persona(
        persona_id="security_expert",
        name="Security Expert",
        template="builtin:security"
    )
    manager.save_persona(persona)

    # Execute task with persona
    harness = PersonaHarness("security_expert")
    result = await harness.execute_task("Review authentication code")
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
from .harness import (
    PersonaHarness,
    PersonaMessage,
    SentinelMessage,
    MessageType
)

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
    # Runtime
    'PersonaHarness',
    # Communication
    'PersonaMessage',
    'SentinelMessage',
    'MessageType'
]

__version__ = '3.0.0'  # Phase 3
