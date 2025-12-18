# Empirica Architecture - Complete Visual Overview

## System Layers (Bottom-Up)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        USER / AI AGENT LAYER                            │
│  (LLM Engine: Claude, GPT-4, Qwen, etc. - uses Empirica for epistemic  │
│   self-awareness via MCP or Python API)                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    INTERFACE LAYER (How to use Empirica)                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │
│  │   MCP Tools      │  │   Empirica CLI   │  │  Python API      │    │
│  │                  │  │                  │  │                  │    │
│  │ • session_create │  │ • session-create │  │ from empirica... │    │
│  │ • preflight      │  │ • preflight      │  │ db = Session...  │    │
│  │ • check          │  │ • check          │  │ db.create_...    │    │
│  │ • finding_log    │  │ • finding-log    │  │ db.log_finding() │    │
│  │ • goals_create   │  │ • goals-create   │  │                  │    │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                CASCADE WORKFLOW (Epistemic Process)                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PREFLIGHT → [CHECK]* → POSTFLIGHT → Δ (Deltas)                       │
│     ↓            ↓           ↓           ↓                             │
│  Assess      Decision    Measure    Calculate                          │
│  baseline    gates       learning    epistemic                         │
│  state       (0-N)       outcome     change                            │
│                                                                         │
│  Each phase uses 13 EPISTEMIC VECTORS:                                 │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │ TIER 0: engagement (gate)                                     │    │
│  │ TIER 1: know, do, context                                     │    │
│  │ TIER 2: clarity, coherence, signal, density                   │    │
│  │ TIER 3: state, change, completion, impact                     │    │
│  │ META:   uncertainty (explicit tracking)                       │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    CORE PROCESSING LAYER                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ EPISTEMIC ASSESSMENT                                            │  │
│  │ • Compute 13-vector state                                       │  │
│  │ • Calculate confidence scores                                   │  │
│  │ • Track uncertainty explicitly                                  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ DELTA COMPUTATION                                               │  │
│  │ • PREFLIGHT vs POSTFLIGHT deltas                                │  │
│  │ • Learning velocity (change per minute)                         │  │
│  │ • Git correlation (epistemic state → code changes)              │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ GOAL ORCHESTRATION                                              │  │
│  │ • Break complex work into subtasks                              │  │
│  │ • Track findings/unknowns/deadends per subtask                  │  │
│  │ • Scope tracking (breadth/duration/coordination)                │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ SENTINEL ORCHESTRATOR (Oversight Layer)                         │  │
│  │ • Multi-persona coordination                                    │  │
│  │ • Arbitration strategies                                        │  │
│  │ • Compliance monitoring                                         │  │
│  │ • SLM trained on Empirica deltas (future)                       │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                   STORAGE LAYER (3-Layer Atomic Write)                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │
│  │   SQLite DB      │  │   Git Notes      │  │   JSON Logs      │    │
│  │                  │  │                  │  │                  │    │
│  │ • sessions       │  │ • Compressed     │  │ • Full reflex    │    │
│  │ • reflexes       │  │   checkpoints    │  │   logs           │    │
│  │ • findings       │  │ • Immutable      │  │ • Human-readable │    │
│  │ • unknowns       │  │   history        │  │ • Backup         │    │
│  │ • deadends       │  │ • Distributed    │  │                  │    │
│  │ • goals          │  │                  │  │                  │    │
│  │ • subtasks       │  │                  │  │                  │    │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘    │
│                                                                         │
│  Atomic Write: SQLite → Git Notes → JSON (graceful degradation)        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      DATA PRODUCTS (What You Get)                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  • Epistemic Deltas (learning measurement)                              │
│  • Git-Epistemic Correlation (commit → epistemic context)               │
│  • Session Handoffs (continuity across sessions)                        │
│  • Calibration Reports (predicted vs actual confidence)                 │
│  • Project Breadcrumbs (findings/unknowns/deadends aggregated)          │
│  • Delta Packages (training data for Sentinel SLM - future)             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Component Breakdown

### 1. INTERFACE LAYER

#### MCP Tools (Model Context Protocol)
```json
{
  "tools": [
    "session_create",
    "preflight", "preflight_submit",
    "check", "check_submit", 
    "postflight", "postflight_submit",
    "finding_log", "unknown_log", "deadend_log",
    "goals_create", "goals_add_subtask",
    "project_bootstrap"
  ]
}
```

**Used by:** Claude Desktop, Rovo Dev, any MCP-compatible LLM

#### Empirica CLI
```bash
empirica session-create --ai-id myai
empirica preflight --prompt "Task description" --prompt-only
empirica preflight-submit --vectors '{...}' --reasoning "..."
empirica finding-log --finding "Discovery" --source file:path/to/evidence.txt
empirica goals-create --objective "Complex task" --scope-breadth 0.6
```

#### Python API
```python
from empirica.data.session_database import SessionDatabase
db = SessionDatabase()
session_id = db.create_session(ai_id="myai")
db.log_finding(project_id, session_id, "Discovery", sources=[...])
```

---

### 2. CASCADE WORKFLOW

```
PREFLIGHT (Baseline)
    ↓
  [WORK + CHECK gates (0-N times)]
    ↓
POSTFLIGHT (Final)
    ↓
DELTA COMPUTATION
```

**Purpose:** Measure epistemic state before/after work, track learning

**13 Epistemic Vectors:**
```python
{
  # TIER 0: Foundation (engagement is gate ≥ 0.6)
  "engagement": 0.8,  # Task clarity and commitment
  
  # TIER 1: Foundation Confidence
  "know": 0.65,       # Domain knowledge
  "do": 0.70,         # Practical capability
  "context": 0.58,    # Environmental understanding
  
  # TIER 2: Comprehension Confidence  
  "clarity": 0.85,    # Request clarity
  "coherence": 0.80,  # Logical consistency
  "signal": 0.75,     # Signal-to-noise
  "density": 0.40,    # Info density (inverted - low is good)
  
  # TIER 3: Execution Confidence
  "state": 0.70,      # Current state understanding
  "change": 0.65,     # Change tracking ability
  "completion": 0.60, # Path to completion
  "impact": 0.55,     # Consequence prediction
  
  # META: Explicit Uncertainty
  "uncertainty": 0.45 # Known unknowns
}
```

---

### 3. STORAGE ARCHITECTURE

**3-Layer Atomic Write (Graceful Degradation):**

```python
def atomic_write(data):
    """Writes to all 3 layers with graceful degradation"""
    # Layer 1: SQLite (REQUIRED - fails if this fails)
    sqlite_success = write_to_sqlite(data)
    if not sqlite_success:
        raise Exception("Critical: SQLite write failed")
    
    # Layer 2: Git Notes (BEST-EFFORT - warns if fails)
    try:
        write_to_git_notes(compress(data))
    except Exception as e:
        logger.warning(f"Git notes write failed: {e}")
    
    # Layer 3: JSON Logs (BEST-EFFORT - warns if fails)
    try:
        write_to_json_logs(data)
    except Exception as e:
        logger.warning(f"JSON log write failed: {e}")
```

**Why 3 Layers:**
1. **SQLite:** Fast queries, structured data, transactions
2. **Git Notes:** Immutable history, distributed, compression
3. **JSON:** Human-readable, portable, backup

---

### 4. DELTA COMPUTATION

**Purpose:** Measure learning (epistemic change over time)

```python
# PREFLIGHT state
preflight = {
    "know": 0.35,
    "uncertainty": 0.75
}

# POSTFLIGHT state (after investigation)
postflight = {
    "know": 0.80,
    "uncertainty": 0.25
}

# Delta computation
delta = {
    "know": +0.45,         # Knowledge increased
    "uncertainty": -0.50,  # Uncertainty reduced (learning!)
    "velocity": {
        "know_per_minute": 0.015,  # Learning rate
        "duration_seconds": 1800
    }
}
```

**Git Correlation:**
```json
{
  "commit_sha": "abc123",
  "epistemic_context": {
    "know": 0.80,
    "uncertainty": 0.25,
    "investigated": ["API authentication", "OAuth2 flows"],
    "confidence_basis": "investigated and tested"
  },
  "files_changed": ["auth.py", "oauth_handler.py"],
  "epistemic_delta": {
    "know": +0.45,
    "uncertainty": -0.50
  }
}
```

---

### 5. SENTINEL / COGNITIVE VAULT

**Sentinel Orchestrator:**
```python
class SentinelOrchestrator:
    """
    Multi-persona coordination for oversight and compliance.
    
    Components:
    - Persona profiles (roles with specific perspectives)
    - Arbitration strategies (how personas decide together)
    - Composition strategies (how to combine persona outputs)
    """
```

**Current Status:**
- ✅ Core orchestration implemented
- ✅ Multi-persona coordination
- 🚧 Cognitive Vault integration (in progress)
- 🔮 SLM trained on delta packages (future)

**Future Vision:**
```
Cognitive Vault = Sentinel SLM trained on Empirica delta packages

Training data:
- Thousands of CASCADE deltas (PREFLIGHT → POSTFLIGHT)
- Git-epistemic correlations (code changes → learning patterns)
- Calibration data (predicted vs actual confidence)
- Multi-session patterns (how epistemic state evolves)

Output:
- Small language model (~7B params) specialized in epistemic assessment
- Runs locally for privacy
- Provides real-time epistemic oversight
- Detects contamination, drift, uncertainty spikes
```

---

### 6. DATA FLOW (End-to-End)

```
1. User creates session
   └→ SQLite: sessions table
   └→ Git Notes: session checkpoint
   └→ JSON: session_*.json

2. User runs PREFLIGHT assessment
   └→ LLM generates 13-vector self-assessment
   └→ Empirica stores in reflexes table
   └→ Git Notes: compressed checkpoint
   └→ JSON: full reflex log

3. User works (logs findings/unknowns)
   └→ SQLite: findings/unknowns tables
   └→ Each log entry includes timestamp, session context

4. User runs CHECK gates (optional, 0-N times)
   └→ Decision: proceed or investigate more
   └→ Stored in reflexes table

5. User runs POSTFLIGHT assessment
   └→ Final 13-vector assessment
   └→ Delta computation (PREFLIGHT vs POSTFLIGHT)
   └→ Learning velocity calculated
   └→ Git correlation (if git repo)

6. User queries deltas
   └→ API: /sessions/<id>/deltas
   └→ Returns learning metrics
   └→ Shows epistemic growth

7. User creates handoff for next session
   └→ Compressed summary (~90% token reduction)
   └→ Key findings, unknowns, next steps
   └→ Epistemic deltas included
```

---

## Key Innovations

### 1. Git Isomorphism
**Every epistemic event maps to git primitives:**
- Session = Branch
- PREFLIGHT/CHECK/POSTFLIGHT = Commits
- Findings/Unknowns = Tags/Notes
- Deltas = Diffs (epistemic, not code)

### 2. 3-Layer Storage
**Atomic write with graceful degradation:**
- SQLite (fast queries) + Git Notes (immutable history) + JSON (portability)

### 3. Explicit Uncertainty
**13th vector tracks known unknowns:**
- Not hidden in confidence scores
- Triggers investigation when high
- Measured reduction shows learning

### 4. Delta Packages (Future)
**Training data for Sentinel SLM:**
- CASCADE deltas from thousands of sessions
- Git-epistemic correlations
- Calibration patterns
- → Train specialized epistemic oversight model

---

## Use Cases

### For Developers
```bash
# Before starting work
empirica preflight --prompt "Implement OAuth2" --prompt-only
# → Honest self-assessment: know=0.4, uncertainty=0.7
# → Triggers investigation before coding

# After investigation
empirica check --findings '["Learned OAuth2 flows"]' --confidence 0.75
# → Decision: proceed with implementation

# After work
empirica postflight
# → Measure: know=0.85, uncertainty=0.2
# → Δknow=+0.45, Δuncertainty=-0.5 (learning proven!)
```

### For Security Research (Your Use Case)
```bash
# Create security disclosure tracking
empirica session-create --ai-id rovodev --project-id cognitive-vault-research

# Log findings with evidence
empirica finding-log \
  --finding "accountType: ANONYMOUS proves shared pooling" \
  --source file:evidence/04_log_excerpts.txt:15-23 \
  --source screenshot:evidence/contamination.png

# Track across multiple vendors
empirica project-bootstrap --project-id cognitive-vault-research --subject atlassian-rovo
# → Shows only Atlassian findings/unknowns (scoped context)
```

### For Multi-Agent Coordination
```python
# Agent A works on frontend
session_a = db.create_session(ai_id="agent_a", project_id="webapp")
db.log_finding(project_id, session_a, "API endpoint: /auth/login")

# Agent B works on backend  
session_b = db.create_session(ai_id="agent_b", project_id="webapp")
# Bootstrap to see Agent A's findings
findings = db.get_project_findings(project_id="webapp")
# → Sees: "API endpoint: /auth/login" from Agent A
```

---

## Standardized Data Formats

### JSON (Reflex Logs)
```json
{
  "session_id": "abc-123",
  "phase": "PREFLIGHT",
  "timestamp": "2025-12-15T14:30:00Z",
  "vectors": {
    "engagement": 0.80,
    "know": 0.65,
    ...
    "uncertainty": 0.45
  },
  "reasoning": "Starting with moderate knowledge..."
}
```

### SQLite Schema
```sql
CREATE TABLE reflexes (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    phase TEXT,  -- PREFLIGHT, CHECK, POSTFLIGHT
    engagement REAL, know REAL, do REAL, ...
    uncertainty REAL,
    timestamp DATETIME
);

CREATE TABLE findings (
    id TEXT PRIMARY KEY,
    project_id TEXT,
    session_id TEXT,
    finding TEXT,
    timestamp DATETIME
);
```

### Git Notes Format
```
refs/empirica/sessions/abc-123/reflexes/preflight-001

Compressed JSON (base64):
eyJzZXNzaW9uX2lkIjoiYWJjLTEyMyIs...
```

---

## Future: Cognitive Vault Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   COGNITIVE VAULT                           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Sentinel SLM (~7B params)                          │  │
│  │  Trained on Empirica delta packages                 │  │
│  │                                                     │  │
│  │  Input: Current epistemic state (13 vectors)       │  │
│  │  Output:                                            │  │
│  │    • Contamination detection                        │  │
│  │    • Drift alerts                                   │  │
│  │    • Uncertainty spike warnings                     │  │
│  │    • Calibration corrections                        │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Training Data Sources:                                     │
│  • 10,000+ CASCADE deltas from production use               │
│  • Git-epistemic correlations                               │
│  • Calibration patterns (predicted vs actual)               │
│  • Multi-session epistemic trajectories                     │
│                                                             │
│  Runs locally (privacy-first), provides real-time oversight │
└─────────────────────────────────────────────────────────────┘
```

---

This is Empirica: **Epistemic infrastructure for AI agents.**
