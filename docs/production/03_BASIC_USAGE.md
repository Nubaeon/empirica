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
from empirica.core.canonical.reflex_logger import ReflexLogger

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

## Next Steps

- **[CASCADE Flow](06_CASCADE_FLOW.md)** - Detailed workflow explanation
- **[Epistemic Vectors](05_EPISTEMIC_VECTORS.md)** - Understanding the 13 vectors
- **[Session Management](12_SESSION_DATABASE.md)** - Advanced session features
- **[Python API](13_PYTHON_API.md)** - Complete Python API reference

---

## Migration from v1.x

### Old (v1.x):
```python
from empirica.bootstraps import ExtendedMetacognitiveBootstrap

bootstrap = ExtendedMetacognitiveBootstrap(level="2")
components = bootstrap.bootstrap()
cascade = components['canonical_cascade']
```

### New (v2.0):
```python
from empirica.data.session_database import SessionDatabase

# Just create a session
db = SessionDatabase()
session_id = db.create_session(ai_id="myai")
db.close()

# Components load on-demand, no pre-loading needed
```

**Key Changes:**
- ❌ No ExtendedMetacognitiveBootstrap class
- ❌ No component pre-loading
- ❌ No bootstrap command
- ✅ Explicit session creation
- ✅ Lazy-loading components
- ✅ Cleaner API

