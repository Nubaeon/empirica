# Basic Usage Guide

**Empirica v2.0 - Getting Started**

**Storage Architecture:** See `docs/architecture/STORAGE_ARCHITECTURE_COMPLETE.md`  

---

## Quick Start - Create a Session

The simplest way to use Empirica:

```bash
# Create a session
empirica session-create --ai-id myai --output json

# Returns:
# {
#   "ok": true,
#   "session_id": "abc123...",
#   "ai_id": "myai"
# }
```

Or via Python:

```python
from empirica.data.session_database import SessionDatabase

# Create session
db = SessionDatabase()
session_id = db.create_session(
    ai_id="myai",
    bootstrap_level=1  # 0-4, standard is 1
)
db.close()

print(f"Session created: {session_id}")
```

---

## Your First CASCADE Workflow

```python
from empirica.core.canonical import ReflexLogger

# Create session
from empirica.data.session_database import SessionDatabase
db = SessionDatabase()
session_id = db.create_session(ai_id="hello_empirica")
db.close()

# Initialize CASCADE logger
logger = ReflexLogger(session_id=session_id)

# PREFLIGHT: Assess before starting
preflight_vectors = {
    "engagement": 0.8,
    "know": 0.6,
    "do": 0.7,
    "context": 0.7,
    "clarity": 0.8,
    "coherence": 0.9,
    "signal": 0.8,
    "density": 0.4,
    "state": 0.7,
    "change": 0.8,
    "completion": 0.2,  # Just starting
    "impact": 0.7,
    "uncertainty": 0.4  # Moderate uncertainty
}

logger.log_reflex(
    phase="PREFLIGHT",
    round_num=1,
    vectors=preflight_vectors,
    reasoning="Initial task assessment: understand Empirica basics"
)

# ... Do your work ...

# POSTFLIGHT: Assess after completing
postflight_vectors = preflight_vectors.copy()
postflight_vectors.update({
    "know": 0.85,  # Learned a lot
    "completion": 1.0,  # Task complete
    "uncertainty": 0.15  # Much clearer now
})

logger.log_reflex(
    phase="POSTFLIGHT",
    round_num=1,
    vectors=postflight_vectors,
    reasoning="Task complete: understood Empirica workflow"
)

print(f"✅ CASCADE complete for session: {session_id}")
```

---

## CLI Workflow

```bash
# 1. Create session
SESSION_ID=$(empirica session-create --ai-id myai --output json | jq -r '.session_id')

# 2. Run PREFLIGHT
empirica preflight --session-id $SESSION_ID --prompt "Learn Empirica" --prompt-only

# (AI performs self-assessment)

# 3. Submit PREFLIGHT assessment
empirica preflight-submit \
  --session-id $SESSION_ID \
  --vectors '{"engagement":0.8,"know":0.6,"do":0.7,...}' \
  --reasoning "Starting with moderate knowledge"

# 4. Do your work...

# 5. Run POSTFLIGHT
empirica postflight-submit \
  --session-id $SESSION_ID \
  --vectors '{"engagement":0.9,"know":0.85,"do":0.9,...}' \
  --reasoning "Task complete, learned significantly"

# 6. Get calibration report
empirica sessions-show --session-id $SESSION_ID
```

---

## MCP Tool Usage (Recommended for AI Agents)

```python
# MCP tools handle session creation automatically
from empirica import mcp_client

# Bootstrap creates session in one call
result = mcp_client.bootstrap_session(
    ai_id="myai",
    bootstrap_level=1
)
session_id = result['session_id']

# Execute PREFLIGHT
mcp_client.execute_preflight(
    session_id=session_id,
    prompt="Your task here"
)

# Submit assessment
mcp_client.submit_preflight_assessment(
    session_id=session_id,
    vectors={...},
    reasoning="Your reasoning"
)

# ... work ...

# Execute POSTFLIGHT
mcp_client.execute_postflight(
    session_id=session_id,
    task_summary="What you accomplished"
)
```

---

## Key Concepts

### No Bootstrap Ceremony
- **Old way:** Load components, configure system, pre-warm caches
- **New way:** Create session, start working immediately
- Components lazy-load on-demand - no pre-configuration needed

### 13-Vector Canonical System
Every assessment uses the same 13 epistemic vectors:

**TIER 0: Foundation (Can I do this?)**
- KNOW, DO, CONTEXT

**TIER 1: Comprehension (Do I understand?)**
- CLARITY, COHERENCE, SIGNAL, DENSITY

**TIER 2: Execution (Am I doing it right?)**
- STATE, CHANGE, COMPLETION, IMPACT

**Gate:** ENGAGEMENT (≥0.6 required)
**Meta:** UNCERTAINTY (explicit uncertainty tracking)

### CASCADE Workflow
1. **PREFLIGHT** - Assess before starting (genuine self-assessment)
2. **INVESTIGATE** - Fill knowledge gaps (if uncertainty > threshold)
3. **CHECK** - Validate readiness (explicit gate: proceed or investigate more?)
4. **ACT** - Do the work
5. **POSTFLIGHT** - Reflect on learning (measure epistemic growth)

---

## Session Types

```python
# Development session (verbose logging)
db.create_session(ai_id="myai", bootstrap_level=1)

# Production session (minimal logging)
db.create_session(ai_id="myai", bootstrap_level=0)

# Extended metacognitive (full tracking)
db.create_session(ai_id="myai", bootstrap_level=2)
```

**Bootstrap Levels:**
- 0 = Minimal (production)
- 1 = Standard (recommended)
- 2 = Extended (full metacognitive tracking)
- 3-4 = Experimental (research use)

---

## Using Goal Tracking for Complex Tasks

**New in v4.0:** For complex investigations with high uncertainty, use goal tracking to improve decision quality and continuity.

### When to Use Goals

- ✅ **High uncertainty** - Don't fully understand the task
- ✅ **Multi-session work** - Need to hand off investigation state
- ✅ **Complex investigations** - Multiple unknowns to track
- ⚠️ **Simple tasks** - Skip for straightforward work

### Step-by-Step Example: OAuth2 Implementation

```python
from empirica.data.session_database import SessionDatabase
from empirica.core.canonical import ReflexLogger

# 1. Create session
db = SessionDatabase()
session_id = db.create_session(ai_id="oauth_task")

# 2. Run PREFLIGHT - Assess initial state
logger = ReflexLogger(session_id=session_id)
# (AI performs self-assessment)
# Result: uncertainty = 0.6 (high), know = 0.4 (low)
# Decision: Need investigation before implementation

# 3. Create goal to track investigation
goal_id = db.create_goal(
    session_id=session_id,
    objective="Understand OAuth2 authentication flow",
    scope_breadth=0.6,      # Touches multiple modules
    scope_duration=0.4,     # Few hours
    scope_coordination=0.3  # Mostly solo
)

# 4. Create subtask for investigation
subtask_id = db.create_subtask(
    goal_id=goal_id,
    description="Map OAuth2 endpoints and authorization flow",
    importance='critical'
)

# 5. Do investigation work
# Read docs, examine code, test endpoints...

# 6. Update findings as you discover them
db.update_subtask_findings(subtask_id, [
    "Auth endpoint: /oauth/authorize with state param",
    "Token endpoint: /oauth/token (POST only)",
    "PKCE required for public clients",
    "Refresh tokens enabled with 30-day expiry"
])

# 7. Update unknowns (what's still unclear)
db.update_subtask_unknowns(subtask_id, [
    "How does MFA affect the refresh flow?",
    "Best practice for mobile token storage?"
])

# 8. Decide: Ready to implement?
unknowns_summary = db.query_unknowns_summary(session_id)
print(f"Unknowns remaining: {unknowns_summary['total_unknowns']}")
# Output: Unknowns remaining: 2

# 9. Evaluate unknowns for CHECK decision
# - "MFA refresh" - Edge case, low impact, can handle later
# - "Mobile storage" - Out of scope for backend implementation
# Decision: These unknowns are NOT blockers

# 10. Run CHECK with high confidence
# (AI performs self-assessment with evidence)
# confidence = 0.8, unknowns = 2 (non-blocking) → PROCEED

# 11. Do implementation
# Implement OAuth2 with findings from investigation...

# 12. Run POSTFLIGHT
# (AI performs self-assessment, measures learning)

# 13. Include goal tree in handoff
goal_tree = db.get_goal_tree(session_id)
# Next AI session can see exactly what was investigated
# findings: [4 discoveries]
# unknowns: [2 remaining questions with context]
# dead_ends: [paths explored but blocked]

db.close()
```

### Benefits Demonstrated

**Decision Quality:**
- CHECK decision informed by structured unknowns list
- Evidence-based readiness: "2 unknowns, both low-impact → PROCEED"
- Avoids premature implementation

**Continuity:**
- Next AI knows: What was found, what's unclear, what failed
- No duplicate investigation
- Can pick up exactly where you left off

**Audit Trail:**
- Complete investigation path visible
- Findings, unknowns, and dead_ends all recorded
- Reviewable decision-making process

### Without vs With Goal Tracking

**Without Goals (Implicit Investigation):**
```
PREFLIGHT → [investigate somehow] → CHECK (unclear evidence) → ACT
Result: Uncertainty about readiness, no handoff record
```

**With Goals (Structured Investigation):**
```
PREFLIGHT → Create goal/subtasks → [investigate + log] → 
CHECK (query unknowns) → Evidence-based decision → ACT → 
POSTFLIGHT (goal tree in handoff)
Result: Clear readiness evidence, complete handoff record
```

### Integration with CASCADE Workflow

**Understand the relationship:**

1. **PREFLIGHT** - Assess initial uncertainty
   - High uncertainty? → Create goal to track investigation

2. **Investigation** (between PREFLIGHT and CHECK)
   - Create subtasks as needed
   - Update findings/unknowns incrementally
   - NOT a formal CASCADE phase - just natural work

3. **CHECK** - Explicit readiness gate
   - Query `query_unknowns_summary()`
   - Evaluate: Are unknowns blockers?
   - Evidence-based decision: PROCEED or INVESTIGATE_MORE

4. **ACT** - Do the implementation
   - Can reference findings from goal tree

5. **POSTFLIGHT** - Reflect on learning
   - Include `get_goal_tree()` in handoff report
   - Next session has complete investigation record

**Key Point:** Goals are created and updated DURING work, not as a separate pre-planning phase.

---

## Next Steps

- **[CASCADE Flow](06_CASCADE_FLOW.md)** - Detailed workflow explanation
- **[Epistemic Vectors](05_EPISTEMIC_VECTORS.md)** - Understanding the 13 vectors
- **[Session Management](12_SESSION_DATABASE.md)** - Advanced session features
- **[Python API](13_PYTHON_API.md)** - Complete Python API reference

---

## Migration from v1.x

### Old (v1.x - DEPRECATED):
```python
# ❌ DEPRECATED - Bootstrap classes removed
from empirica.bootstraps import ExtendedMetacognitiveBootstrap

bootstrap = ExtendedMetacognitiveBootstrap(level="2")
components = bootstrap.bootstrap()
cascade = components['canonical_cascade']
```

### New (v2.0):
```bash
# Use CLI for session creation
empirica session-create --ai-id myai --bootstrap-level 1

# Or via Python:
```

```python
from empirica.data.session_database import SessionDatabase

# Just create a session
db = SessionDatabase()
session_id = db.create_session(ai_id="myai", bootstrap_level=1)
db.close()

# Components load on-demand, no pre-loading needed
```

**Key Changes:**
- ❌ No ExtendedMetacognitiveBootstrap class (REMOVED - bootstrap reserved for system prompts)
- ❌ No component pre-loading
- ❌ No bootstrap command for sessions
- ✅ Use `empirica session-create` CLI command
- ✅ Or use `SessionDatabase.create_session()` directly
- ✅ Lazy-loading components
- ✅ Cleaner API

**Note:** "Bootstrap" is now reserved exclusively for dynamic system prompt generation. 
For session creation, use `session-create` command or `SessionDatabase.create_session()`.

