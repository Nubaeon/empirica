# Epistemic Vectors: Complete Reference

## The 13-Vector System

Empirica tracks 13 dimensions of epistemic state, organized into tiers:

### Tier 0: Gate
| Vector | Description | Low (0.3) | High (0.8) |
|--------|-------------|-----------|------------|
| **ENGAGEMENT** | Focus/commitment to task | Distracted, low priority | Fully engaged, high priority |

### Tier 1: Foundation (What You Know)
| Vector | Description | Low (0.3) | High (0.8) |
|--------|-------------|-----------|------------|
| **KNOW** | Domain understanding | New to this, unfamiliar | Deep expertise |
| **DO** | Execution capability | Can't do this reliably | Proven track record |
| **CONTEXT** | Information sufficiency | Missing key details | Full picture |

### Tier 2: Comprehension (How Well You Understand)
| Vector | Description | Low (0.3) | High (0.8) |
|--------|-------------|-----------|------------|
| **CLARITY** | Understanding of the ask | Vague, ambiguous | Crystal clear |
| **COHERENCE** | Internal consistency | Contradictions present | Logically sound |
| **SIGNAL** | Quality of evidence | Noisy, unreliable | Strong, validated |
| **DENSITY** | Information richness | Sparse, gaps | Rich, complete |

### Tier 3: Execution (Getting Work Done)
| Vector | Description | Low (0.3) | High (0.8) |
|--------|-------------|-----------|------------|
| **STATE** | Current progress | Just starting | Near completion |
| **CHANGE** | Rate of progress | Stuck, slow | Rapid advancement |
| **COMPLETION** | Path to goal clarity | Unclear how to finish | Clear path forward |
| **IMPACT** | Expected outcome quality | Low value | High value |

### Meta
| Vector | Description | Low (0.3) | High (0.8) |
|--------|-------------|-----------|------------|
| **UNCERTAINTY** | Meta-uncertainty | Very confident | Very uncertain |

## Simplified 4-Vector System

For most tasks, use these 4 core vectors:

```
KNOW: Domain understanding
DO: Can I execute?
CONTEXT: Do I have enough info?
UNCERTAINTY: How uncertain am I?
```

Add CLARITY when requirements are vague.

**Why simplified works:** The 4-vector system captures 80% of epistemic state while keeping overhead minimal.

## Rating Guidelines

### Scale Interpretation

| Score | Meaning | Example |
|-------|---------|---------|
| 0.0-0.2 | Very low / Almost none | Complete novice, no information |
| 0.3-0.4 | Low | Some exposure, missing key pieces |
| 0.5 | Moderate | Functional understanding, gaps present |
| 0.6-0.7 | Good | Solid foundation, minor gaps |
| 0.8-0.9 | High | Deep understanding, few unknowns |
| 1.0 | Complete / Certain | Expert level, no gaps |

### Common Patterns

**Starting a new domain:**
```json
{
  "know": 0.3,
  "uncertainty": 0.7,
  "context": 0.4,
  "clarity": 0.8
}
```

**Familiar task in known codebase:**
```json
{
  "know": 0.8,
  "uncertainty": 0.2,
  "context": 0.7,
  "clarity": 0.9
}
```

**Vague requirements, familiar domain:**
```json
{
  "know": 0.7,
  "uncertainty": 0.5,
  "context": 0.5,
  "clarity": 0.4
}
```

## Bias Corrections

Historical analysis shows common biases. Apply these corrections:

| Vector | Typical Bias | Correction |
|--------|--------------|------------|
| UNCERTAINTY | -0.23 (overestimate confidence) | Add +0.10 to your estimate |
| KNOW | +0.24 (underestimate knowledge) | Subtract -0.05 from estimate |
| DO | +0.44 (underestimate capability) | Consider past successes |

**Readiness gate:** know >= 0.70 AND uncertainty <= 0.35

## Vector Interactions

Vectors influence each other:

- Low CONTEXT → Higher UNCERTAINTY
- Low CLARITY → Lower effective KNOW
- High UNCERTAINTY → Lower COMPLETION confidence
- Low SIGNAL → Lower COHERENCE possible

## When to Update Vectors

Update your vectors when:
- You learn something significant (finding)
- You discover a gap (unknown)
- You hit a dead end
- Requirements change
- Context shifts

Don't update for minor progress - save it for meaningful state changes.

## Anti-Patterns

**Heuristic scoring:** Don't use fixed rules like "always start at 0.5"
**Optimistic bias:** Don't inflate scores to appear confident
**Static assessment:** Don't keep the same scores throughout a task
**Ignoring uncertainty:** High uncertainty is data, not failure

## Example Assessment Flow

```
Task: "Implement rate limiting for API endpoints"

Initial PREFLIGHT:
- KNOW: 0.6 (understand rate limiting concepts)
- UNCERTAINTY: 0.5 (haven't seen this codebase's patterns)
- CONTEXT: 0.4 (don't know existing middleware)
- CLARITY: 0.85 (requirements are clear)

After INVESTIGATE:
- KNOW: 0.75 (found existing throttling middleware)
- UNCERTAINTY: 0.3 (understand the patterns now)
- CONTEXT: 0.8 (read middleware and config)
- CLARITY: 0.9 (confirmed requirements with examples)

Final POSTFLIGHT:
- KNOW: 0.85 (implemented and tested)
- UNCERTAINTY: 0.15 (confident in solution)
- CONTEXT: 0.9 (understand full flow)
- CLARITY: 0.95 (edge cases handled)

Learning delta: +0.25 KNOW, -0.35 UNCERTAINTY
```
