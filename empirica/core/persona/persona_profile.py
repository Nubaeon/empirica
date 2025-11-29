"""
Persona Profile - Core dataclass for Phase 3

Defines the structure of an AI persona with:
- Epistemic priors (starting knowledge state)
- Thresholds (when to investigate, when to act)
- Weights (how to compute composite confidence)
- Focus domains (areas of expertise)
- Capabilities (what persona can do)
- Sentinel configuration (how to manage)
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from datetime import datetime, UTC

@dataclass
class SigningIdentityConfig:
    """Configuration for persona's cryptographic identity (Phase 2 integration)"""
    user_id: str
    identity_name: str
    public_key: str
    reputation_score: float = 0.5

    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class EpistemicConfig:
    """Epistemic configuration for a persona"""

    # Prior epistemic state (13 vectors)
    priors: Dict[str, float]

    # Decision thresholds
    thresholds: Dict[str, float] = field(default_factory=lambda: {
        "uncertainty_trigger": 0.4,
        "confidence_to_proceed": 0.75,
        "signal_quality_min": 0.6,
        "engagement_gate": 0.6
    })

    # Tier weights (must sum to 1.0)
    weights: Dict[str, float] = field(default_factory=lambda: {
        "foundation": 0.35,
        "comprehension": 0.25,
        "execution": 0.25,
        "engagement": 0.15
    })

    # Focus domains (areas of expertise)
    focus_domains: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate epistemic config"""
        # Validate priors has all 13 vectors
        required_vectors = [
            "engagement", "know", "do", "context",
            "clarity", "coherence", "signal", "density",
            "state", "change", "completion", "impact", "uncertainty"
        ]

        for vector in required_vectors:
            if vector not in self.priors:
                raise ValueError(f"Missing required vector in priors: {vector}")

            value = self.priors[vector]
            if not (0.0 <= value <= 1.0):
                raise ValueError(f"Vector {vector} must be in [0.0, 1.0], got {value}")

        # Validate weights sum to 1.0 (within epsilon)
        weight_sum = sum(self.weights.values())
        if not (0.99 <= weight_sum <= 1.01):
            raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")

    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class CapabilitiesConfig:
    """What this persona can/cannot do"""
    can_spawn_subpersonas: bool = False
    can_call_external_tools: bool = True
    can_modify_code: bool = True
    can_read_files: bool = True
    requires_human_approval: bool = False
    max_investigation_depth: int = 5
    restricted_operations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class EscalationTrigger:
    """Condition that triggers Sentinel intervention"""
    condition: str  # e.g., "uncertainty > 0.8"
    action: str     # notify, pause, handoff, escalate, terminate
    priority: str = "medium"  # low, medium, high, critical

    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class SentinelConfig:
    """How Sentinel should manage this persona"""
    reporting_frequency: str = "per_phase"  # per_phase, per_round, on_completion, realtime
    escalation_triggers: List[EscalationTrigger] = field(default_factory=list)
    timeout_minutes: int = 60
    max_cost_usd: float = 10.0
    requires_sentinel_approval_before_act: bool = False

    def to_dict(self) -> Dict:
        result = asdict(self)
        # Convert escalation triggers
        result['escalation_triggers'] = [t.to_dict() for t in self.escalation_triggers]
        return result

@dataclass
class PersonaMetadata:
    """Metadata about the persona"""
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    parent_persona: Optional[str] = None
    derived_from: Optional[str] = None
    verified_sessions: int = 0

    def __post_init__(self):
        """Set timestamps if not provided"""
        if self.created_at is None:
            self.created_at = datetime.now(UTC).isoformat()
        if self.modified_at is None:
            self.modified_at = self.created_at

    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class PersonaProfile:
    """
    Complete persona profile for Phase 3 multi-persona intelligence

    A persona is a specialized AI agent with:
    - Domain-specific epistemic priors (starting knowledge)
    - Custom thresholds and weights
    - Focus areas (what to investigate)
    - Capabilities (what it can do)
    - Signing identity (cryptographic provenance)

    Example:
        profile = PersonaProfile(
            persona_id="security_expert",
            name="Security Expert",
            version="1.0.0",
            signing_identity=SigningIdentityConfig(
                user_id="david",
                identity_name="security_expert",
                public_key="abc123..."
            ),
            epistemic_config=EpistemicConfig(
                priors={
                    "engagement": 0.85,
                    "know": 0.90,        # High security knowledge
                    "do": 0.85,
                    "context": 0.75,
                    "clarity": 0.80,
                    "coherence": 0.80,
                    "signal": 0.75,
                    "density": 0.70,
                    "state": 0.75,
                    "change": 0.70,
                    "completion": 0.05,  # Starting task
                    "impact": 0.80,
                    "uncertainty": 0.15  # Low uncertainty in domain
                },
                thresholds={
                    "uncertainty_trigger": 0.30,     # Very cautious
                    "confidence_to_proceed": 0.85    # High bar
                },
                focus_domains=[
                    "security", "authentication", "authorization",
                    "encryption", "vulnerabilities", "threats"
                ]
            )
        )
    """

    # Required fields
    persona_id: str
    name: str
    version: str
    signing_identity: SigningIdentityConfig
    epistemic_config: EpistemicConfig

    # Optional fields
    capabilities: CapabilitiesConfig = field(default_factory=CapabilitiesConfig)
    sentinel_config: SentinelConfig = field(default_factory=SentinelConfig)
    metadata: PersonaMetadata = field(default_factory=PersonaMetadata)

    def __post_init__(self):
        """Validate persona profile"""
        # Validate persona_id format
        import re
        if not re.match(r'^[a-z0-9_-]+$', self.persona_id):
            raise ValueError(f"persona_id must be lowercase alphanumeric with _ or -, got: {self.persona_id}")

        # Validate version format (semver)
        if not re.match(r'^\d+\.\d+\.\d+$', self.version):
            raise ValueError(f"version must be semantic version (x.y.z), got: {self.version}")

        # Validate public key format (64 hex chars for Ed25519)
        if not re.match(r'^[0-9a-f]{64}$', self.signing_identity.public_key):
            raise ValueError(f"public_key must be 64 hex chars (Ed25519), got length: {len(self.signing_identity.public_key)}")

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "persona_id": self.persona_id,
            "name": self.name,
            "version": self.version,
            "signing_identity": self.signing_identity.to_dict(),
            "epistemic_config": self.epistemic_config.to_dict(),
            "capabilities": self.capabilities.to_dict(),
            "sentinel_config": self.sentinel_config.to_dict(),
            "metadata": self.metadata.to_dict()
        }

    @classmethod
    def _parse_sentinel_config(cls, sentinel_data: Dict) -> 'SentinelConfig':
        """Parse sentinel config from dictionary"""
        # Extract escalation_triggers separately to avoid double-pass
        escalation_triggers = [
            EscalationTrigger(**t)
            for t in sentinel_data.get('escalation_triggers', [])
        ]

        # Remove from dict to avoid passing twice
        sentinel_data_copy = sentinel_data.copy()
        sentinel_data_copy.pop('escalation_triggers', None)

        return SentinelConfig(
            **sentinel_data_copy,
            escalation_triggers=escalation_triggers
        )

    @classmethod
    def from_dict(cls, data: Dict) -> 'PersonaProfile':
        """Load persona profile from dictionary"""
        return cls(
            persona_id=data['persona_id'],
            name=data['name'],
            version=data['version'],
            signing_identity=SigningIdentityConfig(**data['signing_identity']),
            epistemic_config=EpistemicConfig(**data['epistemic_config']),
            capabilities=CapabilitiesConfig(**data.get('capabilities', {})),
            sentinel_config=cls._parse_sentinel_config(data.get('sentinel_config', {})),
            metadata=PersonaMetadata(**data.get('metadata', {}))
        )

    def get_type(self) -> str:
        """Get persona type based on focus domains"""
        domains = self.epistemic_config.focus_domains

        if any(d in domains for d in ['security', 'vulnerabilities', 'threats']):
            return 'security'
        elif any(d in domains for d in ['usability', 'ux', 'accessibility']):
            return 'ux'
        elif any(d in domains for d in ['performance', 'optimization', 'latency']):
            return 'performance'
        elif any(d in domains for d in ['architecture', 'patterns', 'design']):
            return 'architecture'
        elif any(d in domains for d in ['code', 'review', 'quality']):
            return 'code_review'
        else:
            return 'general'
