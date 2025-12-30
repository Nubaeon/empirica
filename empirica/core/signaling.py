"""
Empirica Signaling Module - Unified metacognitive signaling for statusline and hooks

This module provides the single source of truth for:
1. Traffic Light calibration (drift levels)
2. Sentinel Gate detection (critical thresholds)
3. Vector state emojis (per-vector health indicators)
4. 3-layer signaling output (basic/default/full)

Used by:
- statusline_empirica.py (CLI statusline)
- post-compact.py hook (memory learning)
- check-drift CLI command

Author: Claude Code
Date: 2025-12-30
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List
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

# Drift level emojis
DRIFT_EMOJIS = {
    DriftLevel.CRYSTALLINE: '🔵',
    DriftLevel.SOLID: '🟢',
    DriftLevel.EMERGENT: '🟡',
    DriftLevel.FLICKER: '🔴',
    DriftLevel.VOID: '⚪',
    DriftLevel.UNKNOWN: '⚪',
}

# Sentinel action emojis
SENTINEL_EMOJIS = {
    SentinelAction.NONE: '',
    SentinelAction.REVISE: '🔄',
    SentinelAction.BRANCH: '🔱',
    SentinelAction.HALT: '⛔',
    SentinelAction.LOCK: '🔒',
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


def get_drift_level(drift_score: Optional[float]) -> DriftLevel:
    """
    Get drift level from score using Traffic Light calibration.

    Args:
        drift_score: Overall drift score (0.0-1.0), or None if unknown

    Returns:
        DriftLevel enum value
    """
    if drift_score is None:
        return DriftLevel.UNKNOWN
    elif drift_score < 0.1:
        return DriftLevel.CRYSTALLINE
    elif drift_score < 0.2:
        return DriftLevel.SOLID
    elif drift_score < 0.3:
        return DriftLevel.EMERGENT
    elif drift_score < 0.4:
        return DriftLevel.FLICKER
    else:
        return DriftLevel.VOID


def get_drift_emoji(drift_score: Optional[float]) -> str:
    """Get emoji for drift level."""
    return DRIFT_EMOJIS[get_drift_level(drift_score)]


def get_drift_label(drift_score: Optional[float]) -> str:
    """Get human-readable label for drift level."""
    return get_drift_level(drift_score).value.capitalize()


def detect_sentinel_action(
    drift_score: Optional[float],
    drift_details: Optional[Dict[str, float]] = None
) -> SentinelAction:
    """
    Detect if a sentinel gate should be triggered.

    Args:
        drift_score: Overall drift score
        drift_details: Per-vector drift values (optional, for pattern detection)

    Returns:
        SentinelAction to take
    """
    if drift_score is None:
        return SentinelAction.NONE

    # Check for dangerous patterns first (LOCK)
    if drift_details:
        know_drift = drift_details.get('know', 0)
        uncertainty_drift = drift_details.get('uncertainty', 0)

        # Pattern: Know dropped significantly AND uncertainty increased
        if know_drift < -0.3 and uncertainty_drift > 0.2:
            return SentinelAction.LOCK

    # Check drift thresholds
    if drift_score >= 0.5:
        return SentinelAction.HALT
    elif drift_score >= 0.4:
        return SentinelAction.BRANCH
    elif drift_score >= 0.3:
        return SentinelAction.REVISE

    return SentinelAction.NONE


def get_sentinel_emoji(action: SentinelAction) -> str:
    """Get emoji for sentinel action."""
    return SENTINEL_EMOJIS.get(action, '')


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


def format_vector_state(vector_name: str, value: Optional[float], show_value: bool = False) -> str:
    """
    Format a single vector's state as emoji string.

    Args:
        vector_name: Name of the vector
        value: Current value (0.0-1.0)
        show_value: If True, include numeric value

    Returns:
        Formatted string like "🧠🟢" or "🧠🟢.70"
    """
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
    show_values: bool = False
) -> str:
    """
    Format multiple vectors as compact emoji string.

    Args:
        vectors: Dict of vector_name -> value
        keys: Which vectors to include (default: key vectors)
        show_values: If True, include numeric values

    Returns:
        Formatted string like "🧠🟢 🎯🟢 📍🟡 💡🟢"
    """
    if keys is None:
        keys = ['know', 'uncertainty', 'context', 'clarity']

    parts = []
    for key in keys:
        if key in vectors:
            parts.append(format_vector_state(key, vectors[key], show_values))

    return ' '.join(parts)


def format_drift_compact(
    drift_score: Optional[float],
    sentinel_action: Optional[SentinelAction] = None,
    show_percentage: bool = True
) -> str:
    """
    Format drift state as compact string.

    Args:
        drift_score: Overall drift score
        sentinel_action: Sentinel action if triggered
        show_percentage: If True, include percentage

    Returns:
        Formatted string like "🔵 5%" or "🔴 35% ⛔ HALT"
    """
    emoji = get_drift_emoji(drift_score)

    if drift_score is not None and show_percentage:
        result = f"{emoji} {drift_score:.0%}"
    else:
        result = f"{emoji} {get_drift_label(drift_score)}"

    if sentinel_action and sentinel_action != SentinelAction.NONE:
        sentinel_emoji = get_sentinel_emoji(sentinel_action)
        result += f" {sentinel_emoji} {sentinel_action.value}"

    return result


@dataclass
class SignalingState:
    """Complete signaling state for statusline/hooks."""
    # CASCADE phase
    phase: Optional[str] = None  # PREFLIGHT, CHECK, POSTFLIGHT

    # Vectors
    vectors: Optional[Dict[str, float]] = None

    # Drift
    drift_score: Optional[float] = None
    drift_details: Optional[Dict[str, float]] = None
    drift_level: DriftLevel = DriftLevel.UNKNOWN

    # Sentinel
    sentinel_action: SentinelAction = SentinelAction.NONE

    # Session info
    session_id: Optional[str] = None
    ai_id: Optional[str] = None

    def format_basic(self) -> str:
        """Basic signaling: just drift."""
        return format_drift_compact(self.drift_score, self.sentinel_action, show_percentage=True)

    def format_default(self) -> str:
        """Default signaling: phase + key vectors + drift."""
        parts = []

        if self.phase:
            parts.append(self.phase)

        if self.vectors:
            parts.append(format_vectors_compact(self.vectors, show_values=False))

        parts.append(format_drift_compact(self.drift_score, self.sentinel_action))

        return ' │ '.join(parts)

    def format_full(self) -> str:
        """Full signaling: everything with values."""
        parts = []

        # Session info
        if self.ai_id and self.session_id:
            parts.append(f"{self.ai_id}@{self.session_id[:4]}")

        if self.phase:
            parts.append(self.phase)

        if self.vectors:
            # All key vectors with values
            all_keys = ['know', 'uncertainty', 'context', 'clarity', 'engagement', 'completion', 'impact']
            parts.append(format_vectors_compact(self.vectors, keys=all_keys, show_values=True))

        parts.append(format_drift_compact(self.drift_score, self.sentinel_action))

        return ' │ '.join(parts)

    def to_dict(self) -> dict:
        """Export as dictionary for JSON serialization."""
        return {
            'phase': self.phase,
            'vectors': self.vectors,
            'drift_score': self.drift_score,
            'drift_details': self.drift_details,
            'drift_level': self.drift_level.value,
            'sentinel_action': self.sentinel_action.value if self.sentinel_action != SentinelAction.NONE else None,
            'session_id': self.session_id,
            'ai_id': self.ai_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'SignalingState':
        """Create from dictionary."""
        drift_score = data.get('drift_score')
        drift_details = data.get('drift_details')

        return cls(
            phase=data.get('phase'),
            vectors=data.get('vectors'),
            drift_score=drift_score,
            drift_details=drift_details,
            drift_level=get_drift_level(drift_score),
            sentinel_action=detect_sentinel_action(drift_score, drift_details),
            session_id=data.get('session_id'),
            ai_id=data.get('ai_id'),
        )


# Cache file path for hook -> statusline communication
DRIFT_CACHE_PATH = ".empirica/drift_state.json"


def write_drift_cache(state: SignalingState, base_path: str = ".") -> bool:
    """
    Write drift state to cache file for statusline to read.

    Args:
        state: SignalingState to cache
        base_path: Base directory (usually project root)

    Returns:
        True if successful
    """
    import json
    from pathlib import Path

    try:
        cache_path = Path(base_path) / DRIFT_CACHE_PATH
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        with open(cache_path, 'w') as f:
            json.dump(state.to_dict(), f, indent=2)

        return True
    except Exception:
        return False


def read_drift_cache(base_path: str = ".") -> Optional[SignalingState]:
    """
    Read drift state from cache file.

    Args:
        base_path: Base directory (usually project root)

    Returns:
        SignalingState if cache exists and is valid, None otherwise
    """
    import json
    from pathlib import Path

    try:
        cache_path = Path(base_path) / DRIFT_CACHE_PATH

        if not cache_path.exists():
            return None

        with open(cache_path, 'r') as f:
            data = json.load(f)

        return SignalingState.from_dict(data)
    except Exception:
        return None
