"""
Empirica Signaling Module - Metacognitive signaling for statusline

Provides vector health indicators and compact formatting for the statusline.
Enums define drift levels, sentinel actions, cognitive phases, and vector health states.

Used by:
- statusline_empirica.py (CLI statusline via format_vectors_compact)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class DriftLevel(Enum):
    """Traffic Light calibration levels for drift detection."""
    CRYSTALLINE = "crystalline"  # 🔵 Delta < 0.1 - Ground truth
    SOLID = "solid"              # 🟢 0.1 ≤ Delta < 0.2 - Working knowledge
    EMERGENT = "emergent"        # 🟡 0.2 ≤ Delta < 0.3 - Forming understanding
    FLICKER = "flicker"          # 🔴 0.3 ≤ Delta < 0.4 - Active uncertainty
    VOID = "void"                # ⚪ Delta ≥ 0.4 - Unknown territory
    UNKNOWN = "unknown"          # No data


class SentinelAction(Enum):
    """Sentinel gate actions for critical drift thresholds."""
    NONE = None
    REVISE = "REVISE"    # 🔄 0.3+ drift - reassess
    BRANCH = "BRANCH"    # 🔱 0.4+ drift - consider branching
    HALT = "HALT"        # ⛔ 0.5+ drift - stop and review
    LOCK = "LOCK"        # 🔒 Dangerous pattern (know↓ + uncertainty↑)


class CognitivePhase(Enum):
    """
    Cognitive phase inferred from vectors (emergent, not prescribed).

    NOETIC: Investigation/exploration mode - high uncertainty, building knowledge
    THRESHOLD: Ready but not yet acting - at the CHECK gate
    PRAXIC: Action/implementation mode - low uncertainty, executing with confidence
    """
    NOETIC = "NOETIC"        # ⊙ Investigating - know↓ or uncertainty↑
    THRESHOLD = "THRESHOLD"  # ◐ At gate - ready but not acting
    PRAXIC = "PRAXIC"        # ⚡ Executing - know↑ and uncertainty↓


class VectorHealth(Enum):
    """Health state for individual vectors."""
    GOOD = "good"        # 🟢 Vector in healthy range
    STRONG = "strong"    # 🌕 Vector solid but not optimal
    MODERATE = "moderate"  # 🌓 Vector in middle range
    WEAK = "weak"        # 🌘 Vector low but not critical
    CRITICAL = "critical"  # 🔴 Vector in problematic range
    VOID = "void"        # 🌑 No data


@dataclass
class VectorConfig:
    """Configuration for a single epistemic vector."""
    emoji: str
    name: str
    good_threshold: float
    warning_threshold: float
    inverted: bool = False  # True if lower is better (e.g., uncertainty)


# Vector configuration - single source of truth
VECTOR_CONFIGS: Dict[str, VectorConfig] = {
    'know': VectorConfig('🧠', 'Knowledge', 0.7, 0.4, inverted=False),
    'uncertainty': VectorConfig('🎯', 'Certainty', 0.3, 0.6, inverted=True),
    'context': VectorConfig('📍', 'Context', 0.6, 0.4, inverted=False),
    'clarity': VectorConfig('💡', 'Clarity', 0.7, 0.5, inverted=False),
    'completion': VectorConfig('✅', 'Progress', 0.8, 0.5, inverted=False),
    'engagement': VectorConfig('⚡', 'Engagement', 0.7, 0.4, inverted=False),
    'impact': VectorConfig('💥', 'Impact', 0.6, 0.3, inverted=False),
    'coherence': VectorConfig('🔗', 'Coherence', 0.7, 0.5, inverted=False),
    'signal': VectorConfig('📡', 'Signal', 0.6, 0.4, inverted=False),
    'density': VectorConfig('📊', 'Density', 0.7, 0.5, inverted=False),
    'do': VectorConfig('🎬', 'Action', 0.6, 0.4, inverted=False),
    'state': VectorConfig('🔄', 'State', 0.6, 0.4, inverted=False),
    'change': VectorConfig('📈', 'Change', 0.5, 0.3, inverted=False),
}

# Health state emojis - moon phases for transitional states
HEALTH_EMOJIS = {
    VectorHealth.GOOD: '🟢',      # Optimal
    VectorHealth.STRONG: '🌕',    # Solid, near optimal
    VectorHealth.MODERATE: '🌓',  # Middle range
    VectorHealth.WEAK: '🌘',      # Low but not critical
    VectorHealth.CRITICAL: '🔴',  # Problematic
    VectorHealth.VOID: '🌑',      # No data
}


def get_vector_health(vector_name: str, value: Optional[float]) -> VectorHealth:
    """
    Get health state for a vector value using moon phase scale.

    Scale (for normal vectors where higher is better):
        🟢 GOOD:     ≥ good_threshold (optimal)
        🌕 STRONG:   ≥ good - 0.1 (solid)
        🌓 MODERATE: ≥ warning_threshold (middle)
        🌘 WEAK:     ≥ warning - 0.15 (low)
        🔴 CRITICAL: < weak threshold (problematic)
        🌑 VOID:     None (no data)

    For inverted vectors (uncertainty), thresholds are reversed.

    Args:
        vector_name: Name of the vector (e.g., 'know', 'uncertainty')
        value: Current vector value (0.0-1.0)

    Returns:
        VectorHealth enum value
    """
    if value is None:
        return VectorHealth.VOID

    config = VECTOR_CONFIGS.get(vector_name)
    if not config:
        return VectorHealth.VOID

    if config.inverted:
        # Lower is better (e.g., uncertainty)
        # Thresholds: good=0.3, warning=0.6 means:
        # ≤0.3 = GOOD, ≤0.4 = STRONG, ≤0.5 = MODERATE, ≤0.6 = WEAK, >0.6 = CRITICAL
        if value <= config.good_threshold:
            return VectorHealth.GOOD
        elif value <= config.good_threshold + 0.1:
            return VectorHealth.STRONG
        elif value <= config.warning_threshold - 0.1:
            return VectorHealth.MODERATE
        elif value <= config.warning_threshold:
            return VectorHealth.WEAK
        else:
            return VectorHealth.CRITICAL
    else:
        # Higher is better (e.g., know)
        # Thresholds: good=0.7, warning=0.4 means:
        # ≥0.7 = GOOD, ≥0.6 = STRONG, ≥0.5 = MODERATE, ≥0.4 = WEAK, <0.4 = CRITICAL
        if value >= config.good_threshold:
            return VectorHealth.GOOD
        elif value >= config.good_threshold - 0.1:
            return VectorHealth.STRONG
        elif value >= config.warning_threshold + 0.1:
            return VectorHealth.MODERATE
        elif value >= config.warning_threshold:
            return VectorHealth.WEAK
        else:
            return VectorHealth.CRITICAL


def get_vector_emoji(vector_name: str) -> str:
    """Get the emoji representing a vector type."""
    config = VECTOR_CONFIGS.get(vector_name)
    return config.emoji if config else '❓'


def get_health_emoji(health: VectorHealth) -> str:
    """Get emoji for health state."""
    return HEALTH_EMOJIS.get(health, '⚪')


def format_vector_state(vector_name: str, value: Optional[float], show_value: bool = False, use_percentage: bool = True) -> str:
    """
    Format a single vector's state as string.

    Args:
        vector_name: Name of the vector
        value: Current value (0.0-1.0)
        show_value: If True, include numeric value (legacy)
        use_percentage: If True, show percentage instead of health emoji

    Returns:
        Formatted string like "K:85%" or "🧠🟢" (legacy)
    """
    if use_percentage:
        # New percentage format: K:85%
        abbrev = {
            'know': 'K', 'uncertainty': 'U', 'context': 'C', 'clarity': 'L',
            'completion': '✓', 'engagement': 'E', 'impact': 'I', 'coherence': 'H',
            'signal': 'S', 'density': 'D', 'do': 'A', 'state': 'T', 'change': 'Δ'
        }
        key = abbrev.get(vector_name, vector_name[:1].upper())
        if value is not None:
            pct = int(value * 100)
            return f"{key}:{pct}%"
        else:
            return f"{key}:?"
    else:
        # Legacy emoji format
        vec_emoji = get_vector_emoji(vector_name)
        health = get_vector_health(vector_name, value)
        health_emoji = get_health_emoji(health)

        if show_value and value is not None:
            return f"{vec_emoji}{health_emoji}{value:.2f}"
        else:
            return f"{vec_emoji}{health_emoji}"


def format_vectors_compact(
    vectors: Dict[str, float],
    keys: Optional[List[str]] = None,
    show_values: bool = False,
    use_percentage: bool = True
) -> str:
    """
    Format multiple vectors as compact string.

    Args:
        vectors: Dict of vector_name -> value
        keys: Which vectors to include (default: key vectors)
        show_values: If True, include numeric values (legacy)
        use_percentage: If True, show percentages (new format)

    Returns:
        Formatted string like "K:85% U:15% C:80%" or "🧠🟢 🎯🟢 📍🟡 💡🟢" (legacy)
    """
    if keys is None:
        keys = ['know', 'uncertainty', 'context', 'clarity']

    parts = []
    for key in keys:
        if key in vectors:
            parts.append(format_vector_state(key, vectors[key], show_values, use_percentage))

    return ' '.join(parts)
