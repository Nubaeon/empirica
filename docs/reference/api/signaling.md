# Signaling API

**Module:** `empirica.core.signaling`
**Category:** Metacognitive Signaling
**Stability:** Stable

---

## Overview

Unified metacognitive signaling for statusline, hooks, and UI. Single source of truth for drift levels, sentinel actions, cognitive phases, and vector health.

---

## Enums

### DriftLevel

Traffic light calibration levels for epistemic drift detection.

```python
from empirica.core.signaling import DriftLevel

class DriftLevel(Enum):
    CRYSTALLINE = "crystalline"  # Delta < 0.1 - Ground truth
    SOLID = "solid"              # 0.1 <= Delta < 0.2 - Working knowledge
    EMERGENT = "emergent"        # 0.2 <= Delta < 0.3 - Forming understanding
    FLICKER = "flicker"          # 0.3 <= Delta < 0.4 - Active uncertainty
    VOID = "void"                # Delta >= 0.4 - Unknown territory
    UNKNOWN = "unknown"          # No data
```

| Level | Delta Range | Emoji | Meaning |
|-------|-------------|-------|---------|
| CRYSTALLINE | < 0.1 | :large_blue_circle: | Ground truth |
| SOLID | 0.1 - 0.2 | :green_circle: | Working knowledge |
| EMERGENT | 0.2 - 0.3 | :yellow_circle: | Forming understanding |
| FLICKER | 0.3 - 0.4 | :red_circle: | Active uncertainty |
| VOID | >= 0.4 | :white_circle: | Unknown territory |

---

### SentinelAction

Sentinel gate actions for critical drift thresholds.

```python
from empirica.core.signaling import SentinelAction

class SentinelAction(Enum):
    NONE = None
    REVISE = "REVISE"    # 0.3+ drift - reassess
    BRANCH = "BRANCH"    # 0.4+ drift - consider branching
    HALT = "HALT"        # 0.5+ drift - stop and review
    LOCK = "LOCK"        # Dangerous pattern (know + uncertainty)
```

---

### CognitivePhase

Cognitive phase inferred from vectors (emergent, not prescribed).

```python
from empirica.core.signaling import CognitivePhase

class CognitivePhase(Enum):
    NOETIC = "NOETIC"        # Investigating - know low or uncertainty high
    THRESHOLD = "THRESHOLD"  # At gate - ready but not acting
    PRAXIC = "PRAXIC"        # Executing - know high, uncertainty low
```

---

### VectorHealth

Health state for individual vectors.

```python
from empirica.core.signaling import VectorHealth

class VectorHealth(Enum):
    GOOD = "good"          # Vector in healthy range
    STRONG = "strong"      # Vector solid but not optimal
    MODERATE = "moderate"  # Vector in middle range
    WEAK = "weak"          # Vector low but not critical
    CRITICAL = "critical"  # Vector in problematic range
    VOID = "void"          # No data
```

| Health | Emoji | Description |
|--------|-------|-------------|
| GOOD | :green_circle: | Optimal |
| STRONG | :full_moon: | Solid, near optimal |
| MODERATE | :first_quarter_moon: | Middle range |
| WEAK | :waning_crescent_moon: | Low but not critical |
| CRITICAL | :red_circle: | Problematic |
| VOID | :new_moon: | No data |

---

## Functions

### format_vectors_compact

Format multiple vectors as a compact string for statusline display.

```python
from empirica.core.signaling import format_vectors_compact

vectors = {'know': 0.85, 'uncertainty': 0.15, 'context': 0.8}
compact = format_vectors_compact(vectors)  # "K:85% U:15% C:80%"
```

---

## Vector Configuration

Global configuration for all 13 epistemic vectors.

```python
from empirica.core.signaling import VECTOR_CONFIGS, VectorConfig

# Access config for a vector
know_config = VECTOR_CONFIGS['know']
# VectorConfig(emoji=':brain:', name='Knowledge', good_threshold=0.7, warning_threshold=0.4, inverted=False)

uncertainty_config = VECTOR_CONFIGS['uncertainty']
# VectorConfig(emoji=':dart:', name='Certainty', good_threshold=0.3, warning_threshold=0.6, inverted=True)
```

**Note:** `inverted=True` means lower is better (uncertainty, density, change, impact).

---

## Implementation Files

- `empirica/core/signaling.py` - Enums, VECTOR_CONFIGS, format_vectors_compact

---

**API Stability:** Stable
**Last Updated:** 2026-03-01
