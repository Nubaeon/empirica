"""
Metacognitive Cascade Package

Canonical epistemic cascade using genuine LLM-powered self-assessment:
THINK → ENGAGEMENT GATE → UNCERTAINTY → INVESTIGATE (loop) → CHECK → ACT

Key Features:
- LLM-powered assessment (no heuristics)
- ENGAGEMENT gate (≥0.60)
- Reflex Frame logging
- Canonical weights (35/25/25/15)
- Domain-aware investigation
"""

from .metacognitive_cascade import (
    CanonicalEpistemicCascade,
    run_canonical_cascade,
    CascadePhase,
    CanonicalCascadeState
)

# Legacy support (deprecated)
EpistemicAdaptiveCascade = CanonicalEpistemicCascade
run_epistemic_cascade = run_canonical_cascade

__all__ = [
    # Canonical (primary)
    'CanonicalEpistemicCascade',
    'run_canonical_cascade',
    'CascadePhase',
    'CanonicalCascadeState',

    # Legacy (deprecated - use canonical versions)
    'EpistemicAdaptiveCascade',
    'run_epistemic_cascade',
]