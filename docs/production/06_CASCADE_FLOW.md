# CASCADE Workflow - Complete Guide

**Version:** 4.0  
**Status:** Canonical Reference  

---

## What is CASCADE?

**CASCADE** is Empirica's epistemic checkpoint system - explicit self-assessment at key decision points.

**Not prescriptive reasoning** - CASCADE observes your natural work, doesn't dictate how you think.

---

## The Three Phases

### 1. PREFLIGHT - Before Starting Work

**Purpose:** Assess initial epistemic state

**When:** Before beginning a task (especially complex/uncertain ones)

**What it measures:**
- What do I KNOW? (knowledge vectors)
- What am I uncertain about? (uncertainty = 0.0-1.0)
- Am I ready to proceed? (engagement gate)

**Example:**
```python
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()
session_id = db.create_session(ai_id="myai")

# PREFLIGHT assessment
vectors = {
    'engagement': 0.8,  # Task engagement
    'know': 0.4,        # Low - don't fully understand OAuth2
    'do': 0.5,          # Moderate implementation capability
    'uncertainty': 0.6  # High - many unknowns
}

db.store_vectors(
    session_id=session_id,
    phase='PREFLIGHT',
    vectors=vectors,
    reasoning="Need to investigate OAuth2 flow before implementation"
)
```

**Decision:**
- **High uncertainty?** → Create goal, investigate
- **Low uncertainty?** → Proceed to work

---

### 2. CHECK - Mid-Work Decision Gate

**Purpose:** Explicit readiness assessment before major action

**When:** Before transitioning from investigation → implementation

**What it measures:**
- Confidence to proceed (0.0-1.0)
- Remaining unknowns (via goal tree)
- Decision: PROCEED or INVESTIGATE_MORE

**Key Feature:** CHECK can query `unknowns_summary()` for evidence-based decisions

**Multi-Agent Workflow:** CHECK phase enables investigation handoffs (PREFLIGHT→CHECK). See [`FLEXIBLE_HANDOFF_GUIDE.md`](../guides/FLEXIBLE_HANDOFF_GUIDE.md) for specialist handoff patterns.

**Example:**
```python
# After investigation, before implementation
unknowns = db.query_unknowns_summary(session_id)
print(f"Unknowns: {unknowns['total_unknowns']}")

# CHECK assessment
vectors = {
    'know': 0.8,         # Much better understanding
    'do': 0.8,           # Ready to implement
    'uncertainty': 0.25  # Low - 2 unknowns remain
}

metadata = {
    'decision': 'PROCEED',  # or 'INVESTIGATE_MORE'
    'confidence': 0.8,
    'gaps_identified': [],  # Addressed during investigation
    'remaining_unknowns': [
        "MFA refresh behavior - edge case",
        "Mobile storage - out of scope"
    ]
}

db.store_vectors(
    session_id=session_id,
    phase='CHECK',
    vectors=vectors,
    round_num=1,  # Can have multiple CHECKs
    metadata=metadata,
    reasoning="2 unknowns remain but both are non-blocking"
)
```

**Decision Logic:**
```python
if unknowns['total_unknowns'] == 0 and confidence >= 0.75:
    decision = "PROCEED"  # High confidence, no unknowns
elif unknowns['total_unknowns'] <= 2 and confidence >= 0.7:
    decision = "PROCEED"  # Few unknowns, acceptable confidence
else:
    decision = "INVESTIGATE_MORE"  # Too many unknowns or low confidence
```

**Frequency:**
- CHECK is **optional** (0-N times per task)
- Use when crossing investigation → implementation boundary
- Can run multiple CHECKs for complex work

---

### 3. POSTFLIGHT - After Completing Work

**Purpose:** Reflect on learning and calibrate self-assessment

**When:** After completing a task or work session

**What it measures:**
- Final epistemic state (all 13 vectors)
- Learning delta (PREFLIGHT → POSTFLIGHT)
- Calibration accuracy (were initial assessments correct?)

**Example:**
```python
# After implementation complete
vectors = {
    'engagement': 0.9,
    'know': 0.85,        # Learned significantly
    'do': 0.9,           # Implementation successful
    'uncertainty': 0.15  # Low - clear understanding now
}

metadata = {
    'task_summary': 'Implemented OAuth2 authentication with PKCE',
    'postflight_confidence': 0.85,
    'calibration_accuracy': 'well-calibrated'  # PREFLIGHT uncertainty was accurate
}

db.store_vectors(
    session_id=session_id,
    phase='POSTFLIGHT',
    vectors=vectors,
    metadata=metadata,
    reasoning="Learned OAuth2 flow, PKCE implementation, token management"
)

# Generate handoff report for next session
from empirica.core.handoff import EpistemicHandoffReportGenerator
generator = EpistemicHandoffReportGenerator()

handoff = generator.generate_handoff_report(
    session_id=session_id,
    task_summary="Implemented OAuth2 with PKCE",
    key_findings=["OAuth2 flow working", "PKCE validated"],
    next_session_context="Ready for testing phase"
)

# See FLEXIBLE_HANDOFF_GUIDE.md for handoff types and multi-agent patterns
```

**Calibration:**
- **Well-calibrated:** PREFLIGHT uncertainty matched actual difficulty
- **Overconfident:** Task was harder than expected
- **Underconfident:** Task was easier than expected

---

## Using Goal Tree in CHECK Phase

**Goals/subtasks are separate from CASCADE but inform CHECK decisions.**

### Workflow Integration

```
PREFLIGHT → Assess uncertainty
    ↓
High uncertainty? → Create goal
    ↓
[Do investigation]
    ↓
Update subtask findings/unknowns
    ↓
CHECK → Query unknowns_summary()
    ↓
Evaluate: Blockers?
    ↓
PROCEED or INVESTIGATE_MORE
    ↓
[Do implementation]
    ↓
POSTFLIGHT → Include goal_tree in handoff
```

### CHECK with Goal Integration

```python
# Step 1: During investigation, log discoveries
db.update_subtask_findings(subtask_id, [
    "Found endpoint /oauth/authorize",
    "PKCE required",
    "Refresh tokens enabled"
])

db.update_subtask_unknowns(subtask_id, [
    "Token expiration times unclear",
    "MFA impact unknown"
])

# Step 2: At CHECK decision point, query unknowns
unknowns = db.query_unknowns_summary(session_id)
# Returns: {'total_unknowns': 2, 'unknowns_by_goal': [...]}

# Step 3: Evaluate each unknown
# - "Token expiration" → Can check code, non-blocker
# - "MFA impact" → Edge case, implement basic flow first

# Step 4: CHECK decision with evidence
if unknowns['total_unknowns'] <= 2:
    # Evaluate if unknowns are blockers
    decision = "PROCEED"  # Both are non-blocking
else:
    decision = "INVESTIGATE_MORE"

# Step 5: Store CHECK assessment
db.store_vectors(
    session_id=session_id,
    phase='CHECK',
    vectors={'confidence': 0.75, 'uncertainty': 0.25},
    metadata={
        'decision': decision,
        'unknowns_evaluated': [
            "Token expiration - non-blocker, can check code",
            "MFA impact - edge case, out of scope for MVP"
        ]
    },
    reasoning="2 unknowns remain but neither blocks implementation"
)
```

---

## Complete Example: OAuth2 Implementation

### Full CASCADE + Goals Workflow

```python
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()
session_id = db.create_session(ai_id="oauth_task")

# === PHASE 1: PREFLIGHT ===
preflight_vectors = {
    'engagement': 0.8,
    'know': 0.4,  # Don't fully understand OAuth2
    'do': 0.6,
    'uncertainty': 0.6  # High uncertainty
}
db.store_vectors(session_id, 'PREFLIGHT', preflight_vectors)

# Decision: High uncertainty → need investigation
# Create goal to track investigation
goal_id = db.create_goal(
    session_id=session_id,
    objective="Understand OAuth2 authentication flow",
    scope_breadth=0.6,
    scope_duration=0.4,
    scope_coordination=0.3
)

subtask_id = db.create_subtask(
    goal_id=goal_id,
    description="Map OAuth2 endpoints and flows",
    importance='critical'
)

# === WORK: Investigation ===
# [Read docs, examine code, test endpoints...]

# Log discoveries incrementally
db.update_subtask_findings(subtask_id, [
    "Auth endpoint: /oauth/authorize with state param",
    "Token endpoint: /oauth/token (POST only)",
    "PKCE required for public clients",
    "Refresh enabled with 30-day expiry"
])

db.update_subtask_unknowns(subtask_id, [
    "MFA impact on refresh flow?",
    "Best mobile token storage?"
])

# === PHASE 2: CHECK ===
# Query evidence for decision
unknowns = db.query_unknowns_summary(session_id)
# Returns: total_unknowns = 2

# Evaluate unknowns
# - MFA refresh: Edge case, can handle later
# - Mobile storage: Out of scope for backend

check_vectors = {
    'know': 0.8,  # Much better understanding
    'do': 0.8,
    'uncertainty': 0.25  # Low - 2 non-blocking unknowns
}

db.store_vectors(
    session_id=session_id,
    phase='CHECK',
    vectors=check_vectors,
    round_num=1,
    metadata={
        'decision': 'PROCEED',
        'confidence': 0.8,
        'unknowns_evaluated': unknowns
    },
    reasoning="2 unknowns remain but neither blocks core implementation"
)

# === WORK: Implementation ===
# [Implement OAuth2 with findings from investigation...]

# === PHASE 3: POSTFLIGHT ===
postflight_vectors = {
    'engagement': 0.9,
    'know': 0.85,  # Learned significantly
    'do': 0.9,
    'uncertainty': 0.15  # Low
}

db.store_vectors(
    session_id=session_id,
    phase='POSTFLIGHT',
    vectors=postflight_vectors,
    metadata={
        'task_summary': 'Implemented OAuth2 with PKCE',
        'calibration_accuracy': 'well-calibrated'
    },
    reasoning="Successfully implemented, learned OAuth2 patterns"
)

# Include goal tree in handoff
goal_tree = db.get_goal_tree(session_id)
# Next AI can see: findings, unknowns, dead_ends

db.close()
```

---

## Three Separate Concerns

**Understand the distinction:**

### 1. CASCADE Phases (Epistemic Checkpoints)
- **PREFLIGHT, CHECK, POSTFLIGHT**
- Explicit self-assessment at decision points
- Measure what you know/don't know
- Stored in `reflexes` table

### 2. Goals/Subtasks (Investigation Logging)
- **Created and updated DURING work**
- Track findings/unknowns/dead_ends
- Stored in `goals` and `subtasks` tables
- **Inform CHECK decisions but are separate**

### 3. Implicit Reasoning (Natural Work)
- **THINK, INVESTIGATE, PLAN, ACT, EXPLORE, REFLECT**
- Your natural work process
- System observes, doesn't prescribe
- Not explicitly logged (unless you choose to)

### How They Interact

```
PREFLIGHT (checkpoint)
    ↓
Create goal (optional, if complex)
    ↓
[Natural work: investigate, think, plan...]
    ↓
Update subtasks (findings/unknowns) during work
    ↓
CHECK (checkpoint) - queries unknowns for evidence
    ↓
[Natural work: implement, test...]
    ↓
POSTFLIGHT (checkpoint) - includes goal_tree in handoff
```

**Key Point:** Goals are not nested inside CASCADE. They're parallel investigation tracking that informs CASCADE decisions.

---

## Clarifications

### CASCADE is NOT:
- ❌ A prescriptive reasoning system
- ❌ Required for every tiny task
- ❌ A project management tool
- ❌ Nested inside goals

### CASCADE IS:
- ✅ Epistemic self-awareness checkpoints
- ✅ Explicit decision gates (especially CHECK)
- ✅ Learning measurement (PREFLIGHT → POSTFLIGHT)
- ✅ Calibration feedback

### Goals are NOT:
- ❌ Part of CASCADE phases
- ❌ Required for all tasks
- ❌ Pre-planned before work starts

### Goals ARE:
- ✅ Investigation tracking during work
- ✅ Evidence for CHECK decisions
- ✅ Continuity records for handoff
- ✅ Audit trail for complex work

---

## When to Use Each Phase

### PREFLIGHT
- ✅ Starting new tasks (especially complex)
- ✅ High uncertainty situations
- ✅ Need explicit baseline for learning
- ⚠️ Skip for trivial/routine work

### CHECK
- ✅ Before major implementation after investigation
- ✅ When uncertainty is reducing but not zero
- ✅ Need explicit go/no-go decision
- ⚠️ Optional (0-N times per task)
- ⚠️ Skip if investigation was minimal

### POSTFLIGHT
- ✅ After completing significant work
- ✅ End of session (for handoff)
- ✅ Measuring learning delta
- ✅ Calibration feedback

---

## Best Practices

1. **Don't over-CASCADE** - Skip for simple tasks
2. **CHECK is optional** - Use when crossing investigation → implementation
3. **Goals emerge** - Don't pre-plan, create during work
4. **Update incrementally** - Log findings/unknowns as discovered
5. **Query for decisions** - Use `unknowns_summary()` in CHECK
6. **Include goal_tree** - Add to handoff in POSTFLIGHT

---

## Common Patterns

### Pattern 1: Simple Task (No Goals)
```
PREFLIGHT (low uncertainty) → [Do work] → POSTFLIGHT
```

### Pattern 2: Complex Investigation
```
PREFLIGHT (high uncertainty) → Create goal → 
[Investigate + log findings/unknowns] → 
CHECK (query unknowns) → PROCEED →
[Implement] → POSTFLIGHT (include goal_tree)
```

### Pattern 3: Multiple CHECK Gates
```
PREFLIGHT → Create goal →
[Initial investigation] → CHECK (round 1) → INVESTIGATE_MORE →
[Deeper investigation] → CHECK (round 2) → PROCEED →
[Implement] → POSTFLIGHT
```

---

## Summary

**CASCADE** = Epistemic checkpoints (what do I know?)  
**Goals** = Investigation tracking (what did I discover?)  
**Implicit** = Natural work (how do I think?)

They work together:
- CASCADE measures epistemic state
- Goals track investigation evidence
- Implicit reasoning is your natural process

**Result:** Evidence-based decisions, systematic learning, efficient handoffs.

---

**See Also:**
- `03_BASIC_USAGE.md` - Complete workflow example
- `13_PYTHON_API.md` - API reference for all methods
- `12_SESSION_DATABASE.md` - Database schema details

---

## Pure Self-Assessment Design (v0.9.1+)

**Philosophy:** Genuine self-assessment requires removing cognitive biases.

### POSTFLIGHT Without Anchoring

**Problem (pre-v0.9.1):** MCP `execute_postflight` showed PREFLIGHT baseline vectors to AI during assessment
- **Risk:** Anchoring bias - AI adjusts assessment based on remembered baseline
- **Result:** Not genuine reflection ("I was 0.5 on know, so I should be higher now")

**Solution (v0.9.1+):** Removed `preflight_baseline.vectors` from MCP response
- **AI receives:** Task summary, CHECK history, contextual info
- **AI does NOT see:** PREFLIGHT vector values
- **System calculates:** Deltas objectively after AI submits current state

**Benefits:**
1. **True pure self-assessment** - AI assesses current state genuinely
2. **Confabulation detection** - System can detect when AI claims high but deltas show low
3. **Memory gap detection** - Can identify when AI forgot what they learned
4. **Epistemic trust** - Framework works for all AIs, not just self-aware ones

**MCP Flow:**
```python
# 1. AI calls execute_postflight
response = execute_postflight(session_id, task_summary)
# Returns: session_context (NO baseline vectors), check_history

# 2. AI performs genuine self-assessment
current_state = {
    'know': 0.85,  # Assessed WITHOUT seeing PREFLIGHT baseline
    'do': 0.9,
    'uncertainty': 0.15
}

# 3. AI submits current state
submit_postflight_assessment(session_id, vectors=current_state, reasoning="...")

# 4. System calculates deltas objectively
# PREFLIGHT (0.4) → POSTFLIGHT (0.85) = +0.45 delta
# AI never saw 0.4, assessed 0.85 genuinely
```

This builds epistemic trust - not just for you, but for everyone using Empirica.

---

## Removed Features (v0.9.1)

### Memory Gap Detection (Removed)

**What it was:** Detection of within-session vector decreases (PREFLIGHT → POSTFLIGHT)

**Why removed:**
1. **Conceptual error:** Within-session decreases are NOT memory gaps
2. **What they actually are:** Calibration corrections
   - "I thought I knew X, but I don't" (scope discovery)
   - Task more complex than initially assessed
   - Honest re-assessment after investigation

**Example of false positive:**
```
PREFLIGHT: know=0.8 (overconfident)
Work: Discover OAuth2 is more complex than expected
POSTFLIGHT: know=0.5 (corrected assessment)
Old system: ⚠️ "Memory gap detected!" (WRONG)
Reality: Calibration correction (CORRECT)
```

**True memory gaps require:**
- Cross-session comparison (previous POSTFLIGHT → current PREFLIGHT)
- Forced session restart before context fills
- Using handoff-query/project-bootstrap to measure retention
- Example: Session 1 POSTFLIGHT know=0.9 → 7 days later → Session 2 PREFLIGHT know=0.4

**Special case - Uncertainty:**
- Uncertainty is **inverse** (decrease = good, increase = bad)
- Uncertainty decrease = learning, NOT memory loss
- Example: uncertainty 0.6 → 0.2 = learned significantly

### What Remains

**Still detected:**
- Calibration issues (know↑ but do↓ - claimed learning but no capability)
- Completion/uncertainty mismatches (complete=1.0 but uncertainty=0.8)
- Large epistemic deltas (for analysis, not warnings)

---

**Updated:** 2025-12-11 (v0.9.1)
