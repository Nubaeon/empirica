# Empirica Architecture Organization

**Date:** 2025-11-11  
**Version:** 2.0  
**Status:** Production Ready

---

## Directory Structure

```
empirica/
├── empirica/                          # Core package
│   ├── core/                          # Core epistemic framework
│   │   ├── canonical/                 # 12-vector assessment system
│   │   │   ├── canonical_epistemic_assessment.py
│   │   │   └── reflex_frame.py
│   │   └── metacognitive_cascade/    # CASCADE workflow
│   │       └── metacognitive_cascade.py
│   ├── data/                          # Data management
│   │   ├── session_database.py        # SQLite persistence
│   │   └── session_json_handler.py    # JSON export/import
│   ├── bootstraps/                    # Initialization
│   │   └── onboarding_wizard.py       # AI onboarding
│   ├── cli/                           # Command-line interface
│   ├── plugins/                       # Optional extensions
│   │   └── modality_switcher/         # Multi-AI routing
│   └── dashboard/                     # Monitoring tools
│
├── mcp_local/                         # MCP server implementations
│   ├── empirica_mcp_server.py         # Main MCP server (22 tools)
│   ├── code_guidance_mcp_server.py    # Code guidance (optional)
│   └── empirica_tmux_mcp_server.py    # Dashboard MCP (optional)
│
├── examples/                          # Working examples
│   └── reasoning_reconstruction/      # Reasoning extraction examples
│       ├── 01_basic_reconstruction.sh # Extract learning from sessions
│       ├── 02_knowledge_transfer.py   # AI-to-AI knowledge transfer
│       └── README.md                  # Complete guide
│
├── docs/                              # Documentation
│   ├── 01_a_AI_AGENT_START.md         # AI CLI onboarding
│   ├── 01_b_MCP_AI_START.md           # AI MCP onboarding
│   ├── production/                    # Production documentation
│   │   ├── 01_QUICK_START.md
│   │   ├── 04_ARCHITECTURE_OVERVIEW.md
│   │   ├── 12_SESSION_DATABASE.md
│   │   └── SEMANTIC_REASONING_EXTENSION.md  # Optional enterprise
│   └── architecture/                  # Architecture details
│       └── SYSTEM_ARCHITECTURE_DEEP_DIVE.md
│
├── tests/                             # Test suite
│   ├── integration/                   # Integration tests
│   │   └── test_full_cascade.py       # CASCADE validation (10 tests)
│   ├── mcp/                           # MCP server tests
│   │   └── test_mcp_server_startup.py # MCP validation (3 tests)
│   └── coordination/                  # Multi-AI coordination docs
│       ├── CLAUDE_COPILOT_SESSION_COMPLETE.md
│       ├── FINAL_STATUS.md
│       ├── VECTOR_TERMINOLOGY_STANDARDIZED.md
│       └── EXAMPLES_CREATED.md
│
└── README.md                          # Main entry point

```

---

## Core Components

### 1. Epistemic Framework (empirica/core/canonical/)

**Purpose:** 12-vector epistemic assessment system

**Key Files:**
- `canonical_epistemic_assessment.py` - LLM-powered self-assessment
- `reflex_frame.py` - Data structures (EpistemicAssessment, VectorState)

**What it does:**
- Measures epistemic state across 12 vectors
- No heuristics (genuine LLM reasoning)
- Temporal separation (reflex logs)
- Calibration tracking

**Dependencies:** None (pure Python + dataclasses)

---

### 2. CASCADE Workflow (empirica/core/metacognitive_cascade/)

**Purpose:** 7-phase workflow for task execution

**Key File:**
- `metacognitive_cascade.py` - Complete workflow implementation

**Phases:**
1. PREFLIGHT - Baseline assessment
2. THINK - Initial reasoning
3. PLAN - Task breakdown (optional)
4. INVESTIGATE - Knowledge acquisition
5. CHECK - Recalibration
6. ACT - Execution
7. POSTFLIGHT - Final assessment + calibration

**Dependencies:** canonical assessment system

---

### 3. Data Management (empirica/data/)

**Purpose:** Persistence and export/import

**Key Files:**
- `session_database.py` - SQLite database management
- `session_json_handler.py` - JSON serialization

**Schema:**
- `sessions` table - Session metadata
- `cascades` table - CASCADE executions
- `epistemic_assessments` table - All assessments
- `goals` table - Goal tracking

**Storage:**
- Database: `.empirica/sessions/sessions.db`
- Reflex logs: `.empirica_reflex_logs/`
- Auto-initializes on first use

---

### 4. MCP Server (mcp_local/empirica_mcp_server.py)

**Purpose:** IDE integration (Claude Desktop, Cursor, Windsurf, etc.)

**Tools (22 total):**
- `get_empirica_introduction` - Onboarding
- `execute_preflight` / `submit_preflight_assessment`
- `execute_check` / `submit_check_assessment`
- `execute_postflight` / `submit_postflight_assessment`
- `bootstrap_session`, `resume_previous_session`
- `get_epistemic_state`, `get_session_summary`
- `query_ai` - AI-to-AI communication
- And more...

**Configuration:**
- Uses `.venv-mcp` virtual environment
- Defined in `docs/EMPIRICA_MCP_CONFIG.json`

---

### 5. Examples (examples/reasoning_reconstruction/)

**Purpose:** Demonstrate reasoning reconstruction without semantic layer

**Scripts:**
- `01_basic_reconstruction.sh` - Extract learning from sessions
- `02_knowledge_transfer.py` - Export/import knowledge packages

**What they prove:**
- Reasoning reconstruction works today
- No vector database needed
- Privacy-preserving by default
- Simple deployment

---

## Data Flow

### Session Lifecycle

```
1. Bootstrap
   └─> Create session_id
   └─> Initialize database entry
   
2. PREFLIGHT
   └─> Assess epistemic state
   └─> Log to database (preflight)
   └─> Log to reflex frame (T0)
   
3. Work (THINK → PLAN → INVESTIGATE → CHECK → ACT)
   └─> Multiple assessments
   └─> Each logged with timestamp
   └─> Investigation rounds tracked
   
4. POSTFLIGHT
   └─> Reassess epistemic state
   └─> Log to database (postflight)
   └─> Log to reflex frame (T2)
   └─> Calculate delta: T2 - T0
   └─> Validate calibration
   
5. Export (optional)
   └─> Query database: sessions-export
   └─> Extract learning: examples scripts
   └─> Share knowledge: transfer scripts
```

---

## Storage Architecture

### Database Schema (SQLite)

```sql
-- Session tracking
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    ai_id TEXT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    total_turns INTEGER
);

-- CASCADE executions
CREATE TABLE cascades (
    cascade_id TEXT PRIMARY KEY,
    session_id TEXT,
    task TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    final_confidence REAL,
    investigation_rounds INTEGER,
    calibration_status TEXT,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);

-- Epistemic assessments
CREATE TABLE epistemic_assessments (
    assessment_id TEXT PRIMARY KEY,
    cascade_id TEXT,
    phase TEXT,
    know_score REAL,
    do_score REAL,
    context_score REAL,
    uncertainty_score REAL,
    overall_confidence REAL,
    recommended_action TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY(cascade_id) REFERENCES cascades(cascade_id)
);
```

### Reflex Logs (JSON)

```
.empirica_reflex_logs/
└── <agent_id>/
    └── <date>/
        └── <agent>_<phase>_<timestamp>.json

Example:
{
  "reflex_id": "reflex_abc123",
  "session_id": "session_xyz",
  "timestamp": "2025-11-11T08:00:00Z",
  "phase": "preflight",
  "epistemic_vectors": {
    "know": 0.75,
    "do": 0.80,
    ...
  },
  "reasoning": "Task requires authentication refactor..."
}
```

---

## Extension Points

### 1. Semantic Layer (Optional - Future)

**Location:** Would add to `empirica/semantic/`

**Components:**
- Embedding pipeline (sentence-transformers)
- Vector store integration (Qdrant)
- Query API
- Knowledge transfer protocols

**See:** `docs/production/SEMANTIC_REASONING_EXTENSION.md`

**Status:** Documented architecture, not implemented

---

### 2. Plugins (Optional)

**Location:** `empirica/plugins/`

**Current:**
- `modality_switcher/` - Multi-AI routing (experimental)

**Future:**
- Custom assessment strategies
- Domain-specific vectors
- Integration adapters

---

### 3. Dashboard (Optional)

**Location:** `empirica/dashboard/`

**Current:**
- `snapshot_monitor.py` - Real-time monitoring
- Tmux-based visualization

**Future:**
- Web dashboard
- Real-time visualization
- Multi-session comparison

---

## Testing Architecture

### Test Organization

```
tests/
├── unit/                    # Unit tests (89 tests by Qwen)
│   └── (various)
│
├── integration/             # Integration tests (10 tests by Claude)
│   └── test_full_cascade.py # Complete CASCADE validation
│
├── mcp/                     # MCP server tests (3 tests)
│   └── test_mcp_server_startup.py
│
└── coordination/            # Multi-AI development docs
    ├── CLAUDE_COPILOT_SESSION_COMPLETE.md
    ├── FINAL_STATUS.md
    └── EXAMPLES_CREATED.md
```

### Test Coverage

- **103 tests passing** (89 unit + 10 CASCADE + 3 MCP + 1 CLI)
- **Coverage:** Core workflow fully validated
- **Status:** Production ready

---

## Deployment Architecture

### Minimal Deployment (Core Only)

```bash
# Requirements
- Python 3.8+
- SQLite3 (built-in)
- ~50MB disk space

# Installation
pip install empirica

# Files created on first use
.empirica/
└── sessions/
    └── sessions.db

.empirica_reflex_logs/
└── <agent_id>/
    └── <date>/
        └── *.json
```

**Characteristics:**
- ✅ No external dependencies
- ✅ Local-only storage
- ✅ Privacy-preserving
- ✅ Air-gap compatible
- ✅ Fast and lightweight

---

### Full Deployment (With MCP)

```bash
# Additional requirements
- MCP-compatible IDE (Claude Desktop, Cursor, etc.)
- mcp package: pip install mcp

# Configuration
.empirica_mcp/
├── config.json              # MCP server config
└── .venv-mcp/               # Isolated Python environment

# Server
mcp_local/empirica_mcp_server.py  # 22 tools available
```

---

### Enterprise Deployment (With Semantic Extension - Future)

```bash
# Additional requirements
- Vector database (Qdrant/Pinecone/Weaviate)
- Embedding model (sentence-transformers)
- ~500MB-2GB additional storage

# Installation
pip install empirica[semantic]

# Configuration
EMPIRICA_ENABLE_SEMANTIC=true
EMPIRICA_VECTOR_DB=qdrant://localhost:6333
```

**Status:** Architecture documented, not implemented

---

## Documentation Organization

### User Documentation

**Entry Points:**
- `README.md` - Main overview
- `docs/01_a_AI_AGENT_START.md` - AI CLI onboarding
- `docs/01_b_MCP_AI_START.md` - AI MCP onboarding

**Production Guides:**
- `docs/production/01_QUICK_START.md`
- `docs/production/02_INSTALLATION.md`
- `docs/production/03_BASIC_USAGE.md`
- `docs/production/04_ARCHITECTURE_OVERVIEW.md`

**Examples:**
- `examples/reasoning_reconstruction/README.md`

---

### Developer Documentation

**Architecture:**
- `docs/architecture/SYSTEM_ARCHITECTURE_DEEP_DIVE.md`
- `docs/ARCHITECTURE_ORGANIZATION.md` (this file)

**API Reference:**
- Code docstrings (all modules)
- Type hints (Python 3.8+)

**Development:**
- `tests/coordination/` - Multi-AI development logs
- `CONTRIBUTING.md` - Contribution guidelines

---

### Enterprise Documentation

**Core:**
- `docs/production/12_SESSION_DATABASE.md` - Database management
- `examples/reasoning_reconstruction/README.md` - Reasoning extraction

**Optional Extensions:**
- `docs/production/SEMANTIC_REASONING_EXTENSION.md` - Future architecture

---

## Key Architectural Decisions

### 1. Separation of Core and Extensions

**Decision:** Keep core lightweight, extensions optional

**Rationale:**
- Privacy-first (local-only by default)
- Simple deployment
- No vendor lock-in
- Extensible when needed

**Result:** ✅ Core is 100% self-contained

---

### 2. Temporal Separation via Reflex Logs

**Decision:** Log assessments to separate JSON files

**Rationale:**
- Prevents self-referential recursion
- Creates immutable temporal trail
- Enables later reconstruction
- Proves genuine learning

**Result:** ✅ Temporal separation validated

---

### 3. Database + Files Hybrid

**Decision:** SQLite for queries, JSON for temporal logs

**Rationale:**
- SQL for structured queries
- JSON for reasoning preservation
- Both human-readable
- Both portable

**Result:** ✅ Best of both worlds

---

### 4. No Heuristics in Core

**Decision:** Genuine LLM reasoning only

**Rationale:**
- No pattern matching
- No keyword counting
- No simulated awareness
- Trust LLM capabilities

**Result:** ✅ Philosophically consistent

---

### 5. MCP as Optional Layer

**Decision:** CLI-first, MCP as convenience

**Rationale:**
- CLI works everywhere
- MCP adds IDE integration
- Neither required for core functionality
- Maximum flexibility

**Result:** ✅ Multiple access methods

---

## Migration Paths

### From v1.0 to v2.0

**Changes:**
- 12-vector system (was 11)
- Canonical architecture (was mixed)
- MCP server redesigned
- Database auto-initialization

**Migration:** Manual (breaking changes)

---

### From v2.0 to v2.1 (Semantic Extension)

**Changes:**
- Optional semantic layer
- Backward compatible
- Opt-in configuration

**Migration:** No changes required (fully backward compatible)

---

## Maintenance Guidelines

### Adding New Features

**Core changes:** Minimize, focus on stability

**Extensions:** Add as plugins or optional modules

**Examples:** Add to `examples/` directory

**Docs:** Update relevant sections

---

### Database Schema Changes

**Process:**
1. Add migration script
2. Update SessionDatabase class
3. Document schema version
4. Test with existing data

**Principle:** Never break existing sessions

---

### MCP Tool Changes

**Process:**
1. Update tool definition in `list_tools()`
2. Update handler in `call_tool()`
3. Update tests
4. Update MCP documentation

**Principle:** Backward compatible additions only

---

## Summary

**Architecture Characteristics:**
- ✅ Modular (core + extensions)
- ✅ Privacy-first (local by default)
- ✅ Lightweight (minimal dependencies)
- ✅ Extensible (plugin architecture)
- ✅ Testable (103 tests passing)
- ✅ Documented (comprehensive guides)
- ✅ Production-ready (v2.0)

**Ready for deployment!** 🚀
