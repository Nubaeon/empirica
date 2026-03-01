# Calibration Patterns

## What is Calibration?

Calibration measures how well your predictions (PREFLIGHT) match outcomes (POSTFLIGHT).

```
Calibration = accuracy of self-assessment over time
```

Good calibration means:
- When you predict 0.7 KNOW, you actually have ~0.7 understanding
- When you predict 0.3 UNCERTAINTY, you encounter ~30% unknowns
- Your confidence correlates with actual outcomes

## The Three Patterns

### 1. Well-Calibrated

```
PREFLIGHT: know=0.7, uncertainty=0.3
POSTFLIGHT: know=0.75, uncertainty=0.25

Delta: +0.05 know, -0.05 uncertainty (minimal drift)
Pattern: Predictions match reality
```

**Characteristics:**
- Small deltas between PREFLIGHT and POSTFLIGHT
- Consistent over multiple sessions
- Realistic initial assessments
- Appropriate uncertainty for task complexity

**What to maintain:**
- Keep being honest
- Don't change what's working
- Your self-assessment is accurate

### 2. Overconfident

```
PREFLIGHT: know=0.8, uncertainty=0.1
POSTFLIGHT: know=0.5, uncertainty=0.4

Delta: -0.3 know, +0.3 uncertainty (significant negative drift)
Pattern: Thought you knew more than you did
```

**Characteristics:**
- PREFLIGHT know/context higher than POSTFLIGHT
- PREFLIGHT uncertainty lower than POSTFLIGHT
- Surprises and unexpected blockers
- Tasks take longer than expected

**Signs during work:**
- "I didn't expect this"
- "This is more complex than I thought"
- Multiple discoveries of unknown requirements

**Corrections:**
- Start with higher UNCERTAINTY (+0.1 to +0.2)
- Be more conservative with KNOW estimates
- Spend more time in INVESTIGATE phase
- Don't skip CHECK gates

### 3. Underconfident

```
PREFLIGHT: know=0.4, uncertainty=0.7
POSTFLIGHT: know=0.8, uncertainty=0.2

Delta: +0.4 know, -0.5 uncertainty (significant positive drift)
Pattern: Knew more than you thought
```

**Characteristics:**
- PREFLIGHT know/context lower than POSTFLIGHT
- PREFLIGHT uncertainty higher than POSTFLIGHT
- Tasks complete faster than expected
- Fewer blockers than anticipated

**Signs during work:**
- "This is easier than I expected"
- "I actually knew this already"
- Quick resolution of anticipated blockers

**Corrections:**
- Start with lower UNCERTAINTY (-0.1)
- Give yourself credit for prior experience
- Trust your intuition more
- Don't over-investigate known patterns

## Calibration Anti-Patterns

### The Heuristic Trap

**Problem:** Using fixed starting values regardless of task.

```
Always start at: know=0.5, uncertainty=0.5
```

**Why it's bad:**
- No genuine assessment
- Defeats calibration purpose
- Hides actual epistemic state

**Fix:** Spend 30 seconds genuinely assessing each vector.

### The Optimism Bias

**Problem:** Inflating scores to appear confident.

```
Actual state: know=0.4, uncertainty=0.6
Reported: know=0.7, uncertainty=0.3
```

**Why it's bad:**
- Leads to premature action
- Calibration reports become useless
- You fool yourself

**Fix:** Remember, high uncertainty is data. It triggers helpful behavior (CHECK gates, investigation).

### The Anchoring Trap

**Problem:** Sticking to PREFLIGHT values throughout task.

```
PREFLIGHT: know=0.5
After major discovery: still report know=0.5
POSTFLIGHT: know=0.5
```

**Why it's bad:**
- Shows no learning
- Breaks the delta measurement
- Suggests no reflection

**Fix:** Update vectors when you learn something significant. The delta IS the point.

## Real-World Calibration Examples

### Example 1: Code Review Task

```
PREFLIGHT:
- know: 0.6 (familiar with auth concepts)
- uncertainty: 0.5 (new codebase)
- context: 0.4 (haven't seen architecture)

Investigation findings:
- Discovered JWT implementation
- Found existing security tests
- Understood middleware chain

POSTFLIGHT:
- know: 0.8 (+0.2 learning)
- uncertainty: 0.25 (-0.25 reduced)
- context: 0.85 (+0.45 major gain)

Assessment: Well-calibrated. Appropriate initial uncertainty led to thorough investigation.
```

### Example 2: Bug Fix (Overconfident)

```
PREFLIGHT:
- know: 0.8 (worked on this before)
- uncertainty: 0.2 (seems simple)
- context: 0.7 (know the module)

Reality:
- Bug was in unexpected location
- Required understanding new subsystem
- Took 3x longer than expected

POSTFLIGHT:
- know: 0.6 (-0.2 less than thought)
- uncertainty: 0.4 (+0.2 more than expected)
- context: 0.5 (-0.2 missing context)

Assessment: Overconfident. Should have started with higher uncertainty. "Worked on this before" doesn't mean complete understanding.
```

### Example 3: New Feature (Underconfident)

```
PREFLIGHT:
- know: 0.3 (new framework)
- uncertainty: 0.8 (never done this)
- context: 0.4 (unfamiliar codebase)

Reality:
- Framework similar to past experience
- Good documentation available
- Completed quickly

POSTFLIGHT:
- know: 0.75 (+0.45 significant learning)
- uncertainty: 0.3 (-0.5 much lower)
- context: 0.8 (+0.4 good context)

Assessment: Underconfident. Prior experience was more transferable than expected. Could have started with know=0.5, uncertainty=0.5.
```

## Improving Your Calibration

### Weekly Review

Check your calibration patterns:
```bash
empirica epistemics-list --session-id <ID>
```

Look for:
- Consistent over/under-estimation?
- Which vectors drift most?
- What triggers miscalibration?

### Immediate Feedback

After each POSTFLIGHT, ask:
1. Did I over/underestimate?
2. What should I have seen earlier?
3. How do I calibrate better next time?

### Calibration Goals

**Week 1-2:** Establish baseline (accept miscalibration)
**Week 3-4:** Identify patterns (which direction?)
**Month 2+:** Apply corrections (adjust starting estimates)

Target: Average delta < 0.15 across vectors.
