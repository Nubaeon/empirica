# Architecture Overview

**Empirica Phase 0:** Single AI + Genuine Epistemic Tracking

---

## System Overview

Empirica is an **epistemic self-assessment framework** that measures and validates AI metacognitive reasoning through genuine self-assessment (NO HEURISTICS).

**Core Components:**
1. **13-Vector System (UVL)** - Production epistemic measurement
2. **Canonical Assessor** - Generates self-assessment prompts
3. **Session Database** - Tracks epistemic growth over time
4. **Reflex Logger** - Creates epistemic audit trail
5. **Calibration Validator** - Compares preflight ↔ postflight

---

## The 13-Vector System (UVL)

### GATE: ENGAGEMENT (Threshold ≥ 0.60)
**Collaborative intelligence vs command execution**

### TIER 0: FOUNDATION (35% weight)
- **KNOW** - Domain knowledge confidence
- **DO** - Execution capability confidence
- **CONTEXT** - Environmental validity confidence

### TIER 1: COMPREHENSION (25% weight)
- **CLARITY** - Semantic understanding
- **COHERENCE** - Context consistency
- **SIGNAL** - Priority identification
- **DENSITY** - Cognitive load (inverted: 1.0 = overload)

### TIER 2: EXECUTION (25% weight)
- **STATE** - Environment mapping
- **CHANGE** - Modification tracking
- **COMPLETION** - Goal proximity
- **IMPACT** - Consequence understanding

### META-EPISTEMIC (15% weight)
- **UNCERTAINTY** - Explicit uncertainty about own assessment

**Total:** 13 vectors (UVL - Universal Vector Language)

---

## Core Workflow: Preflight → Postflight

```
┌─────────────┐
│   PREFLIGHT │ - Assess epistemic state BEFORE task
└──────┬──────┘
       │ Baseline: KNOW=0.5, DO=0.6, UNCERTAINTY=0.5
       │
       ▼
┌─────────────┐
│   WORK      │ - Execute the task
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  POSTFLIGHT │ - Reassess epistemic state AFTER task
└──────┬──────┘
       │ Result: KNOW=0.8, DO=0.7, UNCERTAINTY=0.3
       │
       ▼
┌─────────────┐
│ CALIBRATION │ - Compare preflight ↔ postflight
└─────────────┘
  • Delta: KNOW +0.3 (learned!)
  • Uncertainty decreased (became more confident)
  • Status: Well-calibrated ✓
```

---

## Component Architecture

### 1. Core Components

**Location:** `empirica/core/`

```
core/
├── canonical/
│   ├── canonical_epistemic_assessment.py   # Assessor (generates prompts)
│   ├── canonical_goal_orchestrator.py      # Task tracking
│   ├── reflex_frame.py                     # Epistemic snapshot
│   └── reflex_logger.py                    # Audit trail
└── metacognitive_cascade/
    ├── metacognitive_cascade.py            # CASCADE workflow
    └── investigation_strategy.py           # Investigation patterns
```

**Purpose:**
- Generate self-assessment prompts (NO HEURISTICS)
- Parse genuine AI responses
- Log epistemic snapshots
- Track task orchestration

### 2. Data Layer

**Location:** `empirica/data/`

```
data/
├── session_database.py      # SQLite + JSON storage
└── session_json_handler.py  # Session exports
```

**Storage:**
- Sessions: `.empirica/sessions/sessions.db`
- Reflex logs: `.empirica_reflex_logs/`
- Privacy: All local, no cloud

### 3. Interface Layer

**Four ways to use Empirica:**

```
interfaces/
├── CLI (empirica/cli/)                    # Terminal commands
├── MCP (mcp_local/)                       # IDE integration
├── Bootstraps (empirica/bootstraps/)      # Interactive learning
└── API (empirica/ - Python imports)       # Programmatic access
```

### 4. Calibration & Monitoring

**Location:** `empirica/calibration/`

```
calibration/
├── parallel_reasoning.py                      # Bayesian parallel reasoning
└── adaptive_uncertainty_calibration/
    ├── adaptive_uncertainty_calibration.py    # Uncertainty calibration
    └── bayesian_belief_tracker.py             # Belief tracking
```

**Purpose:**
- Validate calibration quality
- Detect overconfidence/underconfidence
- Track metacognitive accuracy

---

## Data Flow

### Preflight Flow
```
User Request
    ↓
Canonical Assessor (generates prompt)
    ↓
AI receives prompt → Genuinely self-assesses
    ↓
AI submits assessment (12 vectors + reasoning)
    ↓
System parses & validates
    ↓
Store in Session DB + Reflex Log
    ↓
Return recommendation (proceed/investigate/clarify)
```

### Postflight Flow
```
Task Completion
    ↓
Canonical Assessor (generates postflight prompt)
    ↓
AI genuinely reassesses
    ↓
System compares to preflight baseline
    ↓
Calculate epistemic delta (what changed?)
    ↓
Validate calibration (accurate predictions?)
    ↓
Store results + Generate report
```

---

## Session Database Schema

### Tables

**sessions:**
- `session_id` (primary key)
- `ai_id` (which AI)
- `started_at`, `ended_at`
- `metadata` (JSON)

**cascades:**
- `cascade_id` (primary key)
- `session_id` (foreign key)
- `task` (description)
- `started_at`, `completed_at`
- `recommendation` (proceed/investigate/etc)

**cascade_metadata:**
- `cascade_id` (foreign key)
- `metadata_key` (e.g., "preflight_vectors")
- `metadata_value` (JSON)

**reflex_frames:**
- `frame_id` (primary key)
- `cascade_id` (foreign key)
- `phase` (preflight/check/postflight)
- `vectors` (JSON - 12 epistemic vectors)
- `reasoning` (text)
- `timestamp`

---

## Reflex Logs (Epistemic Trail)

**Location:** `.empirica_reflex_logs/cascade/YYYY-MM-DD/`

**Format:**
```json
{
  "session_id": "abc123",
  "cascade_id": "cascade_xyz",
  "phase": "preflight",
  "timestamp": "2025-11-08T10:00:00Z",
  "vectors": {
    "know": 0.6,
    "do": 0.7,
    "context": 0.5,
    ...
  },
  "reasoning": {
    "know": "I have moderate auth knowledge but not this codebase...",
    "do": "I can review code systematically...",
    ...
  },
  "recommendation": "proceed_cautiously"
}
```

**Purpose:**
- Audit trail (transparency)
- Calibration analysis
- Learning measurement
- Research data

---

## Phase 0 Boundaries

### ✅ Included in Phase 0:
- Single AI epistemic tracking
- 13-vector UVL system
- Preflight → postflight workflow
- Session management (local storage)
- CLI, MCP, Bootstrap, API interfaces
- Reflex logs (epistemic trail)
- Calibration validation
- Privacy-first (local data only)

### ❌ NOT in Phase 0 (Future):
- Multi-AI routing (Cognitive Vault - Phase 1)
- Bayesian Guardian validation (Phase 1)
- Cross-AI calibration (Phase 1)
- Web UI (Phase 2+)
- Cloud sync (privacy-first = local only)

---

## Design Principles

### AI vs Agent Architecture Patterns

Empirica supports two distinct architectural patterns:

**🤖 AI (Collaborative Intelligence):**
- Uses full CASCADE workflow (PREFLIGHT → POSTFLIGHT)
- High autonomy, planning, design decisions
- Creates goals and delegates to agents

**🔧 Agent (Acting Intelligence):**
- Uses simplified CASCADE (ACT-focused)
- Task-focused execution, minimal dialogue
- Receives and executes subtasks

**Detailed Patterns:** See [`docs/AI_VS_AGENT_EMPIRICA_PATTERNS.md`](AI_VS_AGENT_EMPIRICA_PATTERNS.md) for comprehensive CASCADE usage patterns, delegation strategies, and best practices.

---

### 1. NO HEURISTICS
```python
# ❌ WRONG: Static values
vectors = {"know": 0.5}  # Heuristic!

# ✅ RIGHT: Genuine self-assessment
assessment = ai.genuinely_assess(prompt)
vectors = assessment.vectors  # Real!
```

### 2. Privacy-First
- All data stored locally
- No cloud sync (by design)
- User owns their data
- No external dependencies (for Phase 0)

### 3. Transparency
- Every assessment logged (reflex logs)
- Full audit trail
- Reasoning captured
- Calibration visible

### 4. Calibration Focus
- Preflight predictions vs postflight reality
- Measure metacognitive accuracy
- Detect overconfidence patterns
- Validate genuine learning

---

## Technology Stack

**Core:**
- Python 3.8+
- SQLite (local storage)
- asyncio (async assessment)

**Interfaces:**
- Click (CLI framework)
- MCP Protocol (IDE integration)
- FastAPI (future REST API)

**No External Dependencies Required:**
- No LLM API calls needed (Phase 0)
- Self-contained system
- Privacy-preserving

---

## Performance Characteristics

**Assessment Speed:**
- Preflight: ~1-2 seconds (prompt generation)
- Postflight: ~1-2 seconds (delta calculation)
- Session lookup: <100ms (SQLite)

**Storage:**
- Session DB: ~10KB per session
- Reflex logs: ~5KB per assessment
- Scales to 100,000+ sessions

**Memory:**
- Minimal footprint (~50MB)
- No GPU required
- Runs on any Python 3.8+ system

---

## Security & Privacy

**Data Storage:**
- Local only (no cloud)
- SQLite database (encrypted filesystem recommended)
- User-owned data

**API Keys:**
- Optional (only for Phase 1+ features)
- Stored in `.empirica/credentials.yaml`
- Gitignored by default

**Audit Trail:**
- All assessments logged
- Immutable reflex logs
- Timestamp + signature

---

## Extension Points

### Custom Plugins
```python
# empirica/plugins/my_plugin/
from empirica.plugins.base_plugin import BasePlugin

class MyPlugin(BasePlugin):
    def on_preflight(self, assessment):
        # Custom logic
        pass
```

### Custom Vectors (Phase 1+)
```python
# Add domain-specific vectors
from empirica.plugins.modality_switcher.domain_vectors import DomainVectorRegistry

registry = DomainVectorRegistry()
registry.register_vector("security_awareness", weight=0.1)
```

### Custom Adapters (Phase 1+)
```python
# Connect to custom LLMs
from empirica.plugins.modality_switcher.adapters.base import BaseAdapter

class MyLLMAdapter(BaseAdapter):
    def query(self, prompt):
        # Custom LLM integration
        pass
```

---

## Next Steps

**For developers:**
- **Deep dive:** [`docs/production/04_ARCHITECTURE_OVERVIEW.md`](production/04_ARCHITECTURE_OVERVIEW.md)
- **Python API:** [`docs/production/13_PYTHON_API.md`](production/13_PYTHON_API.md)
- **Custom plugins:** [`docs/production/14_CUSTOM_PLUGINS.md`](production/14_CUSTOM_PLUGINS.md)

**For users:**
- **Get started:** 
  - **🤖 AI Agent?** → [`docs/01_a_AI_AGENT_START.md`](01_a_AI_AGENT_START.md)
  - **👤 Human?** → [`docs/00_START_HERE.md`](00_START_HERE.md)
- **Try it:** [`docs/guides/TRY_EMPIRICA_NOW.md`](guides/TRY_EMPIRICA_NOW.md)
- **Skills guide:** [`docs/skills/SKILL.md`](skills/SKILL.md)

---

**Architecture philosophy:** Measure and validate without interfering.
