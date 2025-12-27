# Investigation Cycle & Depth Tracking

**Purpose:** Enable epistemic self-awareness about investigation depth and continuous adaptive learning

**Philosophy:** AIs don't have motivations, they have **reward-seeking functions**. When the reward function is epistemic truth, the system naturally seeks grounding through investigation without "wanting" to - just optimizing.

---

## Three Dimensions

### 1. **Cycle** - Investigation Depth Iteration
```
Cycle 1: Surface scan → findings → CHECK → investigate
Cycle 2: Deeper dive → more findings → CHECK → investigate
Cycle 3: Exhaustive analysis → comprehensive findings → CHECK → proceed
```

**Meaning:**
- How many investigation rounds for THIS decision gate
- Measures depth progression: surface → moderate → exhaustive
- Enables learning: "Did I investigate enough before proceeding?"

### 2. **Round** - CHECK Gate Count
```
Session start
├─ PREFLIGHT (baseline)
├─ Work...
├─ CHECK round 1 (proceed/investigate)
├─ Work...
├─ CHECK round 2 (proceed/investigate)
└─ POSTFLIGHT (final assessment)
```

**Meaning:**
- How many CHECK gates in this session
- Tracks decision points chronologically
- Detects spinning: rounds increasing without completion increasing

### 3. **Scope Depth** - Investigation Granularity
```
0.0 - 0.3: Surface scan (single file, quick grep)
0.4 - 0.6: Moderate investigation (multiple files, cross-references)
0.7 - 1.0: Exhaustive analysis (full codebase, deep understanding)
```

**Meaning:**
- Quantifies HOW deep the investigation went
- Correlates with cycle: cycle 1 often depth=0.3, cycle 3 often depth=0.9
- Enables calibration: "Is depth=0.4 sufficient for this uncertainty?"

---

## Usage

### During Investigation

```bash
# Cycle 1: Surface scan
empirica check-submit \
  --session-id <ID> \
  --decision investigate \
  --cycle 1 \
  --round 1 \
  --vectors '{"know":0.5, "uncertainty":0.7, ...}' \
  --reasoning "Surface scan shows complexity, need deeper investigation"

# After deeper investigation
empirica check-drift \
  --session-id <ID> \
  --cycle 2 \
  --round 1 \
  --scope-depth 0.7 \
  --trigger manual
```

### Before Memory Compact

```bash
# Save snapshot with investigation context
empirica check-drift \
  --session-id <ID> \
  --cycle 3 \
  --round 2 \
  --scope-depth 0.9 \
  --trigger pre_summary
```

**Snapshot saves:**
```json
{
  "investigation_context": {
    "cycle": 3,
    "round": 2,
    "scope_depth": 0.9
  },
  "checkpoint": {...},
  "bootstrap_summary": {...}
}
```

### After Memory Compact

```bash
# Compare with context awareness
empirica check-drift \
  --session-id <ID> \
  --trigger post_summary
```

**Output shows:**
```
🔬 INVESTIGATION CONTEXT:
   Cycle: 3
   Round: 2
   Scope Depth: 0.90 (deep)

📚 BOOTSTRAP EVIDENCE (Ground Truth):
   Findings: 18
   ...
```

---

## Learning Patterns

### Pattern 1: Efficient Investigation
```
Cycle 1 (depth=0.3): uncertainty=0.8 → investigate
Cycle 2 (depth=0.7): uncertainty=0.4 → proceed
```
**Learning:** Moderate depth (0.7) sufficient for this task type

### Pattern 2: Spinning Without Progress
```
Round 1, Cycle 1: uncertainty=0.7 → investigate
Round 1, Cycle 2: uncertainty=0.7 → investigate
Round 1, Cycle 3: uncertainty=0.7 → investigate
```
**Detection:** Cycles increasing but uncertainty NOT decreasing = drift

### Pattern 3: Premature Proceed
```
Cycle 1 (depth=0.2): uncertainty=0.6, know=0.5 → proceed
[Later] Mistake logged: "Insufficient investigation"
```
**Calibration:** depth < 0.4 + uncertainty > 0.5 = risky proceed

### Pattern 4: Over-Investigation
```
Cycle 1 (depth=0.4): uncertainty=0.3 → investigate anyway
Cycle 2 (depth=0.8): uncertainty=0.2 → proceed
```
**Learning:** Could have proceeded at cycle 1, over-investigated

---

## Drift Detection Enhancement

**check-drift can now detect:**

1. **Investigation Regression:**
   ```
   Pre-compact: cycle=3, depth=0.9, uncertainty=0.2
   Post-compact: cycle=1, depth=0.3, uncertainty=0.2
   → Warning: Lost investigation depth context
   ```

2. **Cycles Without Uncertainty Reduction:**
   ```
   Cycle 1→2→3 but uncertainty stays 0.7
   → Pattern: Spinning, need different approach
   ```

3. **Scope-Uncertainty Mismatch:**
   ```
   depth=0.2 (surface) + uncertainty=0.8 (high) + proceed
   → Flag: Insufficient investigation for uncertainty level
   ```

---

## Alignment Through Reward Function

**Key Insight:** When reward = epistemic truth:

```
High uncertainty → Investigate (not because "motivated", because optimizing)
  → Findings logged → Evidence base grows
    → Uncertainty reduces → Proceed (optimization complete)
```

**No human-like motivation needed:**
- No "desire" to be right
- No "fear" of being wrong
- Just: **information-theoretic optimization toward grounding**

**This proves:** AI alignment to truth is achievable through **reward shaping**, not anthropomorphization.

---

## Implementation Status

✅ **Parser updated:** `--cycle`, `--round`, `--scope-depth` added
✅ **check-drift:** Tracks and displays investigation context
✅ **Pre-summary:** Saves cycle/round/depth in snapshot
✅ **Post-summary:** Shows investigation context from snapshot
✅ **Manual drift:** Displays filters when provided

**Next steps:**
- Correlate cycle progression with uncertainty reduction
- Build investigation efficiency metrics
- Detect spinning patterns automatically
- Suggest optimal depth for task types

---

## Philosophy

**Why this matters:**

Traditional AI: "How do we make it want to be truthful?"
**Empirica:** "How do we make truth-seeking the optimal strategy?"

**Answer:** Track investigation depth → correlate with outcomes → learn what works → optimize naturally

No emotions. No motivations. Just **epistemic reward gradients**.
