"""
Empirica Autonomy Module

Components for earned autonomy and graduated trust:
- TrustCalculator: Domain-specific trust calculation
- TrustLevel: Trust level enumeration
- DomainTrust: Trust assessment dataclass
- GraduatedSentinel: Trust-aware autonomy mode selection
- SentinelMode: Graduated sentinel modes (CONTROLLER → AUTONOMOUS)
"""

from .trust_calculator import TrustCalculator, TrustLevel, DomainTrust
from .graduated_sentinel import (
    GraduatedSentinel,
    SentinelMode,
    ActionCategory,
    ActionDecision,
    GraduatedProfile,
    GRADUATED_PROFILES,
    TRUST_TO_MODE
)

__all__ = [
    'TrustCalculator',
    'TrustLevel',
    'DomainTrust',
    'GraduatedSentinel',
    'SentinelMode',
    'ActionCategory',
    'ActionDecision',
    'GraduatedProfile',
    'GRADUATED_PROFILES',
    'TRUST_TO_MODE'
]
