# Bootstrap Quick Reference

**Quick decision guide for choosing bootstrap level**

---

## One-Line Decision

```
Level 0/minimal → Core only (fastest)
Level 1/standard → + Workflow (recommended default)
Level 2/extended → + Calibration (production ready)
Level 3 → + Advanced (development/analysis)
Level 4/complete → Everything (research)
```

---

## Usage Examples

```python
# Minimal - Just the basics (~0.03s)
from empirica.bootstraps.optimal_metacognitive_bootstrap import OptimalMetacognitiveBootstrap
b = OptimalMetacognitiveBootstrap(level='0')  # or level='minimal'

# Standard - Workflow included (~0.04s)
b = OptimalMetacognitiveBootstrap(level='1')  # or level='standard'

# Extended - Full production (~0.12s)
from empirica.bootstraps.extended_metacognitive_bootstrap import ExtendedMetacognitiveBootstrap
b = ExtendedMetacognitiveBootstrap(level='2')  # or level='extended'

# Advanced - Code analysis, performance (~0.15s)
b = ExtendedMetacognitiveBootstrap(level='3')

# Complete - Everything (~0.20s)
b = ExtendedMetacognitiveBootstrap(level='4')  # or level='complete'
```

---

## Component Checklist

| Component | 0 | 1 | 2 | 3 | 4 |
|-----------|---|---|---|---|---|
| 13-vector metacognition | ✅ | ✅ | ✅ | ✅ | ✅ |
| Calibration | ✅ | ✅ | ✅ | ✅ | ✅ |
| Goal orchestrator | ✅ | ✅ | ✅ | ✅ | ✅ |
| Cascade workflow | | ✅ | ✅ | ✅ | ✅ |
| Context validation | | | ✅ | ✅ | ✅ |
| Runtime validation | | | ✅ | ✅ | ✅ |
| Bayesian Guardian | | | ✅ | ✅ | ✅ |
| Drift Monitor | | | ✅ | ✅ | ✅ |
| Code intelligence | | | | ✅ | ✅ |
| Performance analyzer | | | | ✅ | ✅ |
| Security monitoring | | | | | ✅ |
| Tool management | | | | | ✅ |

---

## When to Use Each Level

### Level 0 (Minimal)
- Testing core functions
- Embedded systems
- Absolute minimum footprint

### Level 1 (Standard) ⭐ DEFAULT
- General AI tasks
- Production workflows
- Standard metacognitive operations

### Level 2 (Extended)
- Production deployments
- Calibration monitoring
- Multi-phase workflows

### Level 3
- Code analysis tasks
- Performance-critical work
- Advanced investigations

### Level 4 (Complete)
- Research and development
- Security audits
- Maximum capabilities

---

**See:** `BOOTSTRAP_LEVELS_UNIFIED.md` for full details
