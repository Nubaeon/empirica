# CASCADE Workflow - Complete Guide

**Version:** 4.1  
**Last Updated:** 2025-12-18  
**Status:** Ground truth - verified against actual implementation

---

## What is CASCADE?

**CASCADE** is Empirica's metacognitive workflow that enables AI agents to genuinely assess their knowledge before, during, and after work.

**Pattern:** PREFLIGHT → [CHECK]* → POSTFLIGHT

- **PREFLIGHT:** Assess what you know BEFORE starting
- **CHECK:** Gate decisions during work (0-N times)
- **POSTFLIGHT:** Measure what you ACTUALLY learned

---

## Why CASCADE?

Traditional AI: *"I'll figure it out as I go"* → Hallucinations, false confidence

CASCADE AI: *"I know X, don't know Y, uncertainty is Z"* → Honest, measurable, improvable

**Benefits:**
- ✅ Honest uncertainty tracking
- ✅ Focused investigation (go where knowledge gaps exist)
- ✅ Genuine learning measurement (compare before/after)
- ✅ Session continuity (resume with full context)
- ✅ Calibration scores (predicted vs actual knowledge)

---

## The Workflow

### PREFLIGHT: Before You Start

**Purpose:** Genuine self-assessment of current knowledge

**AI-First JSON Mode:**
```bash
cat > preflight.json <<EOF
{
  "session_id": "your-session-id",
  "vectors": {
    "engagement": 0.8,
    "foundation": {
      "know": 0.6,
      "do": 0.7,
      "context": 0.5
    },
    "comprehension": {
      "clarity": 0.7,
      "coherence": 0.8,
      "signal": 0.6,
      "density": 0.7
    },
    "execution": {
      "state": 0.5,
      "change": 0.4,
      "completion": 0.3,
      "impact": 0.5
    },
    "uncertainty": 0.4
  },
  "reasoning": "Starting OAuth2 implementation. Moderate knowledge of OAuth2 spec, high uncertainty about token refresh implementation."
}
EOF
cat preflight.json | empirica preflight-submit -
```

**Key Principle:** Be HONEST. "I could figure it out" ≠ "I know it"

**The 13 Vectors:**

**Tier 0 (Foundation):**
- `engagement` (0.0-1.0): Gate threshold ≥0.6 (want to work on this?)
- `know` (0.0-1.0): What you ACTUALLY know right now
- `do` (0.0-1.0): Capability to execute
- `context` (0.0-1.0): Understanding of surrounding system

**Tier 1 (Comprehension):**
- `clarity` (0.0-1.0): How clear is the task?
- `coherence` (0.0-1.0): Does it make sense internally?
- `signal` (0.0-1.0): Can you separate signal from noise?
- `density` (0.0-1.0): Information richness

**Tier 2 (Execution):**
- `state` (0.0-1.0): System state understanding
- `change` (0.0-1.0): Confidence in making changes
- `completion` (0.0-1.0): Progress toward completion
- `impact` (0.0-1.0): Expected impact understanding

**Meta:**
- `uncertainty` (0.0-1.0): Explicit uncertainty measurement

---

### WORK: During Implementation

Do your actual work. Use **CHECK gates** as needed for decision points.

---

### CHECK: Gate Decisions (0-N Times)

**Purpose:** Decide whether to proceed or investigate more

**When to use:**
- Before making major architectural decisions
- When uncertainty spikes during work
- After investigation (did I learn enough?)

**AI-First JSON Mode:**
```bash
cat > check.json <<EOF
{
  "session_id": "your-session-id",
  "confidence": 0.75,
  "findings": [
    "Found OAuth2 token endpoint: /oauth/token",
    "Learned about refresh token flow",
    "Discovered PKCE extension requirement"
  ],
  "unknowns": [
    "Token lifetime configuration unclear",
    "Refresh token rotation policy unknown"
  ],
  "cycle": 1
}
EOF
cat check.json | empirica check -
```

**Decision Logic:**
- `confidence >= 0.7` → **proceed** (ready to implement)
- `confidence < 0.7` → **investigate more** (knowledge gap too large)

**Output:**
```json
{
  "ok": true,
  "decision": "proceed",
  "confidence": 0.75,
  "findings_count": 3,
  "unknowns_count": 2
}
```

---

### POSTFLIGHT: After Work

**Purpose:** Measure what you ACTUALLY learned

**AI-First JSON Mode:**
```bash
cat > postflight.json <<EOF
{
  "session_id": "your-session-id",
  "vectors": {
    "engagement": 0.9,
    "foundation": {
      "know": 0.85,
      "do": 0.9,
      "context": 0.8
    },
    "comprehension": {
      "clarity": 0.9,
      "coherence": 0.9,
      "signal": 0.85,
      "density": 0.8
    },
    "execution": {
      "state": 0.9,
      "change": 0.85,
      "completion": 1.0,
      "impact": 0.8
    },
    "uncertainty": 0.15
  },
  "reasoning": "Successfully implemented OAuth2 with PKCE. Learned token refresh patterns, discovered rotation policy. Implementation complete and tested."
}
EOF
cat postflight.json | empirica postflight-submit -
```

**Automatic Calculations:**
```json
{
  "ok": true,
  "deltas": {
    "know": 0.25,
    "uncertainty": -0.25
  },
  "calibration_score": 0.89,
  "learning_efficiency": 0.76
}
```

---

## Ask-Before-Investigate Pattern

**When uncertainty is high, should you ask or investigate first?**

**Ask first if:**
- `uncertainty >= 0.65` AND `context >= 0.50`
- Rationale: You have enough context to ask specific questions

**Investigate first if:**
- `context < 0.30`
- Rationale: Not enough context to ask meaningful questions

**Example:**
```
uncertainty=0.7, context=0.6 → Ask specific questions
uncertainty=0.8, context=0.2 → Investigate/explore first
```

---

## Session-Based Auto-Linking

**New in v4.1:** Findings/unknowns/deadends auto-link to active goal

When you log a finding without specifying `goal_id`, Empirica automatically:
1. Checks if session has an active goal (`is_completed = 0`)
2. Links the finding to that goal
3. Improves data quality without manual effort

**Example:**
```bash
# No goal_id needed - auto-links to active goal!
echo '{
  "project_id": "your-project",
  "session_id": "your-session",
  "finding": "Learned token refresh patterns"
}' | empirica finding-log -
```

---

## Legacy CLI (Still Supported)

```bash
# PREFLIGHT
empirica preflight-submit \
  --session-id <ID> \
  --vectors '{"engagement":0.8,...}' \
  --reasoning "..." \
  --output json

# CHECK
empirica check \
  --session-id <ID> \
  --confidence 0.75 \
  --findings "..." \
  --unknowns "..." \
  --output json

# POSTFLIGHT
empirica postflight-submit \
  --session-id <ID> \
  --vectors '{"engagement":0.9,...}' \
  --reasoning "..." \
  --output json
```

---

## Common Patterns

### Pattern 1: Quick Task

```bash
# 1. PREFLIGHT (2 min - assess baseline)
cat preflight.json | empirica preflight-submit -

# 2. WORK (30 min - actual implementation)

# 3. POSTFLIGHT (2 min - measure learning)
cat postflight.json | empirica postflight-submit -
```

**Total overhead:** 4 minutes for learning measurement

### Pattern 2: Complex Investigation

```bash
# 1. PREFLIGHT (initial assessment)
cat preflight.json | empirica preflight-submit -

# 2. INVESTIGATE (explore unknowns)

# 3. CHECK (decision point)
cat check1.json | empirica check -
# Decision: investigate_more

# 4. MORE INVESTIGATION

# 5. CHECK (second gate)
cat check2.json | empirica check -
# Decision: proceed

# 6. IMPLEMENT

# 7. POSTFLIGHT (measure total learning)
cat postflight.json | empirica postflight-submit -
```

### Pattern 3: Multi-Session Work

```bash
# Session 1 (Day 1)
PREFLIGHT → Work → POSTFLIGHT

# Session 2 (Day 2)
project-bootstrap --project-id <ID>  # Load context
PREFLIGHT → Work → POSTFLIGHT

# Compare learning across sessions!
```

---

## What Gets Stored

CASCADE assessments are stored in **3 layers** (atomic write):

1. **SQLite** (`reflexes` table): Queryable, structured
2. **Git Notes** (`refs/notes/empirica/cascades/*`): Version controlled
3. **JSON Logs** (`.empirica/reflexes/*.json`): Human-readable

**Why 3 layers?**
- SQLite: Fast queries, analytics
- Git Notes: History, shareability, git-isomorphic
- JSON: Debugging, portability

---

## Calibration Scores

**Empirica measures prediction accuracy:**

```
calibration_score = 1 - |predicted_difficulty - actual_difficulty|
```

**Example:**
- PREFLIGHT: "This will be hard" (know=0.6)
- POSTFLIGHT: "It was hard" (know=0.65, completion=1.0)
- Calibration: **0.95** (excellent prediction!)

**Over time:** Learn to predict your own performance accurately

---

## Common Mistakes

### ❌ Mistake 1: Optimistic PREFLIGHT
```json
{"know": 0.9, "uncertainty": 0.1}
```
*"I totally know OAuth2!"*

**Reality:** Struggled, took 2x longer, many unknowns

**Fix:** Be honest. High uncertainty is GOOD - it triggers investigation

### ❌ Mistake 2: Skipping PREFLIGHT
**Result:** No learning delta, no calibration score, incomplete epistemic record

**Fix:** Always start with PREFLIGHT, even for "quick" tasks

### ❌ Mistake 3: Copy-Paste Vectors
**Result:** Useless data, no genuine self-assessment

**Fix:** Actually think about each vector. "What do I ACTUALLY know right now?"

---

## Best Practices

✅ **Be honest:** Rate what you KNOW, not what you hope to learn

✅ **Use CHECK gates:** Don't push through high uncertainty - investigate!

✅ **Compare deltas:** Look at PREFLIGHT → POSTFLIGHT changes

✅ **Track calibration:** Are you good at predicting your own performance?

✅ **Log findings:** Auto-linking makes this effortless

✅ **Resume with context:** Use `project-bootstrap` to load state

---

## Further Reading

- [Epistemic Vectors Explained](05_EPISTEMIC_VECTORS_EXPLAINED.md)
- [First-Time Setup](guides/FIRST_TIME_SETUP.md)
- [System Prompt (v4.1)](../system-prompts/CANONICAL_SYSTEM_PROMPT.md)
- [Python API Reference](reference/PYTHON_API_GENERATED.md)

---

**Built with genuine epistemic transparency** 🧠✨
