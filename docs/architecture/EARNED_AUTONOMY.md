# Earned Autonomy System

**Version:** 1.3.4 | **Status:** Production

---

## Overview

The Earned Autonomy system provides **trust-based graduated control** over AI actions. Instead of binary "allow/block" decisions, Empirica tracks AI performance across domains and adjusts autonomy levels based on demonstrated calibration.

**Core principle:** Trust is earned through consistent, well-calibrated behavior. AIs start with minimal autonomy and graduate to higher levels as they demonstrate reliability.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EARNED AUTONOMY STACK                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │ GraduatedSentinel│◄──│ TrustCalculator │                    │
│  │                 │    │                 │                    │
│  │ • Mode selection│    │ • Domain trust  │                    │
│  │ • Action eval   │    │ • Calibration   │                    │
│  │ • Escalation    │    │ • Suggestions   │                    │
│  │ • De-escalation │    │ • Mistakes      │                    │
│  └────────┬────────┘    └────────┬────────┘                    │
│           │                      │                              │
│           ▼                      ▼                              │
│  ┌─────────────────────────────────────────┐                   │
│  │              Data Sources               │                   │
│  │  • Bayesian beliefs (calibration)       │                   │
│  │  • Suggestions table (accept/reject)    │                   │
│  │  • Mistakes log (recent errors)         │                   │
│  └─────────────────────────────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### TrustLevel

Enum defining graduated trust levels:

| Level | Score Range | Meaning |
|-------|-------------|---------|
| `NONE` | 0.0 | No trust established |
| `LOW` | 0.0 - 0.4 | Human approval for all changes |
| `MEDIUM` | 0.4 - 0.6 | Human approval for significant changes |
| `HIGH` | 0.6 - 0.8 | Autonomous tactical decisions |
| `VERY_HIGH` | 0.8 - 1.0 | Autonomous strategic decisions |

### SentinelMode

Graduated sentinel modes based on earned trust:

| Mode | Description | Gates From |
|------|-------------|------------|
| `CONTROLLER` | Active blocking - human approval for all | TrustLevel.NONE/LOW |
| `OBSERVER` | Passive logging - human for significant | TrustLevel.MEDIUM |
| `ADVISORY` | Suggestions only - autonomous tactical | TrustLevel.HIGH |
| `AUTONOMOUS` | Full autonomy - async review strategic | TrustLevel.VERY_HIGH |

### ActionCategory

Categories for graduated control:

| Category | Examples | Risk Level |
|----------|----------|------------|
| `TRIVIAL` | Formatting, comments, typos | Lowest |
| `TACTICAL` | Bug fixes, small features | Low |
| `STRATEGIC` | Architecture, major features | Medium |
| `CRITICAL` | Security, production, credentials | Highest |

### DomainTrust

Trust assessment for a specific domain (dataclass):

```python
@dataclass
class DomainTrust:
    domain: str
    score: float  # 0.0 - 1.0
    level: TrustLevel
    factors: Dict[str, float]
    suggestions_accepted: int
    suggestions_rejected: int
    recent_mistakes: int
    calibration_accuracy: float
```

### ActionDecision

Result of evaluating an action (dataclass):

```python
@dataclass
class ActionDecision:
    action: str
    category: ActionCategory
    mode: SentinelMode
    allowed: bool
    requires_human: bool
    rationale: str
    trust_level: TrustLevel
    trust_score: float
    auto_applied: bool
    log_entry: Optional[str]
```

### GraduatedProfile

Configuration for autonomy behavior per mode (dataclass):

```python
@dataclass
class GraduatedProfile:
    mode: SentinelMode
    require_human_for: List[ActionCategory]
    log_actions: List[ActionCategory]
    auto_apply: List[ActionCategory]
    confidence_threshold: float
    description: str
```

---

## Trust Calculation

### Formula

```
trust = (
    calibration_accuracy * 0.4 +
    suggestion_success_rate * 0.4 +
    mistake_penalty * 0.2
)
```

### Factors

| Factor | Weight | Source |
|--------|--------|--------|
| Calibration | 40% | Bayesian beliefs (vector-specific accuracy) |
| Suggestions | 40% | Accepted / (Accepted + Rejected) |
| Mistakes | 20% | 1.0 - (recent_mistakes * 0.1), floor 0.0 |

### Domain-Specific Vectors

Different domains map to different epistemic vectors for calibration:

| Domain | Relevant Vectors |
|--------|------------------|
| architecture | coherence, context, clarity |
| testing | completion, do, state |
| performance | change, impact, signal |
| security | uncertainty, know, context |
| documentation | clarity, density, coherence |

---

## Usage

### Basic Usage

```python
from empirica.core.autonomy import GraduatedSentinel

# Initialize with domain
sentinel = GraduatedSentinel(
    session_id="abc-123",
    domain="architecture"
)

# Get current mode based on trust
mode = sentinel.get_effective_mode()
# Returns: SentinelMode.OBSERVER (if trust is MEDIUM)

# Evaluate an action
decision = sentinel.evaluate_action({
    "action": "refactor authentication module",
    "target": "auth/",
    "metadata": {"files_affected": 5}
})

# Check decision
if decision.requires_human:
    print(f"Human approval needed: {decision.rationale}")
elif decision.auto_applied:
    print(f"Auto-applied: {decision.rationale}")
```

### TrustCalculator Usage

```python
from empirica.core.autonomy import TrustCalculator

calculator = TrustCalculator(project_id="proj-123")

# Get trust for specific domain
trust = calculator.get_domain_trust("architecture")
print(f"Domain: {trust.domain}")
print(f"Score: {trust.score:.2f}")
print(f"Level: {trust.level.value}")
print(f"Factors: {trust.factors}")

# Get all domain trust
all_trust = calculator.get_all_domain_trust()
for domain, trust in all_trust.items():
    print(f"{domain}: {trust.level.value} ({trust.score:.2f})")
```

### CLI Usage

```bash
# Check current trust and mode
empirica autonomy-status --domain architecture --output json

# Get escalation thresholds
empirica autonomy-status --show-thresholds

# Log a suggestion (builds trust)
empirica suggestion-log --domain architecture \
    --suggestion "Refactor auth module" \
    --confidence 0.85

# Review suggestion outcome (affects trust)
empirica suggestion-review --suggestion-id <id> --outcome accepted
```

---

## Escalation & De-escalation

### Escalation Requirements

To graduate to the next trust level:

| From | To | Required Score | Additional Requirements |
|------|-----|----------------|------------------------|
| CONTROLLER | OBSERVER | 0.4 | 3+ suggestions, >70% acceptance |
| OBSERVER | ADVISORY | 0.6 | >80% acceptance, 0 recent mistakes |
| ADVISORY | AUTONOMOUS | 0.8 | >85% calibration, 0 critical mistakes (7d) |

### De-escalation Triggers

Trust can be reduced when:

- **High rejection rate:** >50% suggestions rejected (5+ total)
- **Multiple mistakes:** 3+ recent mistakes in domain
- **Low calibration:** Calibration accuracy <40%
- **Score drop:** Trust score falls below mode floor

### Mode Floors

Minimum scores to maintain each mode:

| Mode | Floor |
|------|-------|
| CONTROLLER | 0.0 |
| OBSERVER | 0.3 |
| ADVISORY | 0.5 |
| AUTONOMOUS | 0.7 |

---

## Environment Variables

| Variable | Values | Effect |
|----------|--------|--------|
| `EMPIRICA_SENTINEL_MODE` | controller, observer, advisory, autonomous | Override trust-based mode |

---

## Integration Points

### With Sentinel

The GraduatedSentinel integrates with the base Sentinel for consistent oversight:

```python
# Standard Sentinel mode (environment-based)
export EMPIRICA_SENTINEL_MODE=observer

# Graduated Sentinel (trust-based, overrides above)
sentinel = GraduatedSentinel(session_id, domain="architecture")
# Mode determined by domain trust, not environment
```

### With Bayesian Beliefs

Calibration accuracy comes from Bayesian beliefs:

```python
# Trust calculator reads from .breadcrumbs.yaml
calibration:
  bias_corrections:
    know: "+0.10"
    uncertainty: "-0.05"
    completion: "+0.68"
```

### With CASCADE Workflow

Trust affects CHECK gate behavior:

- **Low trust:** CHECK requires more evidence before PROCEED
- **High trust:** CHECK allows faster progression with less evidence

---

## Files

| File | Purpose |
|------|---------|
| `empirica/core/autonomy/trust_calculator.py` | TrustCalculator, TrustLevel, DomainTrust |
| `empirica/core/autonomy/graduated_sentinel.py` | GraduatedSentinel, SentinelMode, ActionCategory, ActionDecision, GraduatedProfile |
| `empirica/cli/command_handlers/autonomy_commands.py` | CLI handlers |
| `empirica/cli/parsers/autonomy_parsers.py` | CLI argument parsers |

---

**Website:** [getempirica.com](https://getempirica.com)
