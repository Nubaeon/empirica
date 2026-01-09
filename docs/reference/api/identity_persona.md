# Identity & Persona API

**Module:** `empirica.core.identity`, `empirica.core.persona`
**Category:** AI Configuration
**Stability:** Beta

---

## Overview

Identity and Persona systems configure AI behavior, epistemic priors, and capability boundaries.

---

## AIIdentity

Cryptographic identity for AI agents (signing, attribution).

```python
from empirica.core.identity.ai_identity import AIIdentity

identity = AIIdentity(
    ai_id="claude-code",
    model="claude-opus-4-5-20251101",
    public_key="ed25519:...",
    capabilities=["read", "write", "execute"],
    trust_level=0.9
)

# Sign a checkpoint
signature = identity.sign(checkpoint_data)

# Verify attribution
is_valid = identity.verify(checkpoint_data, signature)
```

---

## PersonaMetadata

Metadata describing an AI persona's configuration.

```python
from empirica.core.persona.persona_profile import PersonaMetadata

@dataclass
class PersonaMetadata:
    name: str                    # e.g., "Implementation Lead"
    ai_id: str                   # e.g., "claude-code"
    version: str
    created_at: datetime
    updated_at: datetime
    author: str                  # Human who created the persona
    description: str
    use_cases: List[str]         # When to use this persona
```

---

## EpistemicConfig

Epistemic configuration for a persona - priors, thresholds, weights.

```python
from empirica.core.persona.persona_profile import EpistemicConfig

config = EpistemicConfig(
    priors={
        "engagement": 0.8, "know": 0.5, "do": 0.6, "context": 0.4,
        "clarity": 0.5, "coherence": 0.5, "signal": 0.6, "density": 0.5,
        "state": 0.5, "change": 0.5, "completion": 0.2, "impact": 0.5,
        "uncertainty": 0.6
    },
    thresholds={
        "uncertainty_trigger": 0.4,    # When to investigate
        "confidence_to_proceed": 0.75, # When to act
        "signal_quality_min": 0.6,     # Minimum signal
        "engagement_gate": 0.6         # Minimum engagement
    },
    weights={
        "foundation": 0.35,    # know, do, context
        "comprehension": 0.25, # clarity, coherence, signal, density
        "execution": 0.25,     # state, change, completion, impact
        "engagement": 0.15     # engagement
    },
    focus_domains=["software-development", "documentation"]
)
```

---

## CapabilitiesConfig

What a persona can and cannot do.

```python
from empirica.core.persona.persona_profile import CapabilitiesConfig

capabilities = CapabilitiesConfig(
    can_spawn_subpersonas=False,
    can_call_external_tools=True,
    can_modify_code=True,
    can_read_files=True,
    requires_human_approval=False,
    max_investigation_depth=5,
    restricted_operations=["delete_files", "push_to_main"]
)
```

---

## EscalationTrigger

Conditions that trigger Sentinel intervention.

```python
from empirica.core.persona.persona_profile import EscalationTrigger

trigger = EscalationTrigger(
    condition="uncertainty > 0.8",
    action="escalate",  # notify, pause, handoff, escalate, terminate
    priority="high"     # low, medium, high, critical
)
```

---

## Implementation Files

- `empirica/core/identity/ai_identity.py` - AIIdentity (cryptographic identity)
- `empirica/core/persona/persona_profile.py` - PersonaMetadata, EpistemicConfig, CapabilitiesConfig, EscalationTrigger

---

**API Stability:** Beta
**Last Updated:** 2026-01-09
