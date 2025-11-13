# Empirica Architecture Map v2.0

**Purpose:** This document provides a clear visual map of Empirica's architecture to prevent confusion during memory compression. Always refer to this map when uncertain about system components.

---

## ⚠️ CRITICAL: Two Separate Vector Systems

### System 1: Canonical 13-Vector Epistemic Assessment (PRODUCTION)
**Location:** `/empirica/core/canonical/`  
**Used By:** Enhanced Cascade Workflow, Preflight/Postflight assessors, Production MCP server  
**Purpose:** Genuine LLM-powered epistemic self-assessment for task execution

**13 Vectors:**
1. **ENGAGEMENT** (gate, ≥0.60 required)
2. **KNOW** (domain knowledge)
3. **DO** (capability)
4. **CONTEXT** (environmental awareness)
5. **CLARITY** (task clarity)
6. **COHERENCE** (logical consistency)
7. **SIGNAL** (information quality)
8. **DENSITY** (information load)
9. **STATE** (current state awareness)
10. **CHANGE** (progress tracking)
11. **COMPLETION** (goal proximity)
12. **IMPACT** (consequence awareness)
13. **UNCERTAINTY** (explicit uncertainty - meta-epistemic)

**Canonical Weights:** 35% Foundation (KNOW/DO/CONTEXT) / 25% Comprehension / 25% Execution / 15% Engagement

### System 2: 12-Vector Self-Awareness (LEGACY/RESEARCH)
**Location:** `/empirica/core/metacognition_12d_monitor/twelve_vector_self_awareness.py`  
**Used By:** Research, benchmarking, alternative monitoring  
**Purpose:** Alternative self-awareness framework with collaboration focus

**12 Vectors:**
- 3 Epistemic Uncertainty vectors
- 4 Comprehension vectors  
- 4 Execution Awareness vectors
- 1 ENGAGEMENT dimension (with 4 sub-components)

**Status:** Legacy system, not used in production cascade

---

## The Enhanced Cascade Workflow (7-Phase)

### Overview
```
USER PROMPT
    ↓
✨ PREFLIGHT ✨ → THINK → PLAN → INVESTIGATE → CHECK → ACT → ✨ POSTFLIGHT ✨
    ↓                              ↓           ↑
[13 Vectors]                [Self-Check] ←─────┘
[Baseline]                  [Recalibrate?]
```

### Component Locations

#### Phase 1: PREFLIGHT
**Component:** `/empirica/workflow/preflight_assessor.py`  
**Function:** `PreflightAssessor.assess_preflight(task, context)`  
**Purpose:** Establish baseline epistemic state (13 vectors)  
**Output:** Baseline assessment stored in DB + JSON + Reflex logs

#### Phase 2: THINK
**Component:** Cascade orchestrator logic  
**Purpose:** Initial reasoning about task (no assessment)

#### Phase 3: PLAN  
**Component:** Cascade orchestrator logic  
**Purpose:** Break complex tasks into phases (simple tasks skip to CHECK)

#### Phase 4: INVESTIGATE (loop with self-check)
**Component:** `/empirica/core/metacognitive_cascade/investigation_strategy.py`  
**Purpose:** Domain-aware tool recommendations (suggestive, not controlling)  
**Self-Check:** `/empirica/workflow/check_phase_evaluator.py` `_assess_check_necessity()`  
**Loop Decision:** Re-investigate OR proceed to CHECK

#### Phase 5: CHECK
**Component:** `/empirica/workflow/check_phase_evaluator.py`  
**Purpose:** Verify epistemic improvement, run Bayesian discrepancy detection, drift monitor  
**Decision:** ACT (ready) OR INVESTIGATE (need more)

#### Phase 6: ACT
**Component:** Cascade orchestrator logic  
**Purpose:** Execute task, generate guidance, export session

#### Phase 7: POSTFLIGHT
**Component:** `/empirica/workflow/postflight_assessor.py`  
**Function:** `PostflightAssessor.assess_postflight(cascade_id)`  
**Purpose:** Final epistemic state (13 vectors), calculate Δ vectors, validate calibration  
**Output:** Final assessment with improvement metrics

### Orchestration
**Main Orchestrator:** `/empirica/workflow/cascade_workflow_orchestrator.py`  
**Class:** `CascadeWorkflowOrchestrator`  
**Method:** `async execute_cascade(user_prompt, context)`

---

## Core Supporting Components

### 1. Auto-Tracking System
**Location:** `/empirica/auto_tracker.py`  
**Class:** `EmpericaTracker` (singleton)  
**Purpose:** Zero-effort tracking to 3 formats simultaneously  
**Outputs:**
- SQLite database (`.empirica/empirica.db`)
- JSON session exports (`.empirica/sessions/<session_id>.json`)
- Reflex frame logs (`.empirica_reflex_logs/<ai_id>/<date>/`)

**Usage:**
```python
async with track_cascade("task") as tracker:
    assessment = await assess(request)
    tracker.log_assessment(assessment, phase="preflight")
```

### 2. Canonical Epistemic Assessor
**Location:** `/empirica/core/canonical/canonical_epistemic_assessment.py`  
**Class:** `CanonicalEpistemicAssessor`  
**Purpose:** LLM-powered genuine 13-vector self-assessment (NO heuristics)  
**Method:** `async assess(task, context) -> EpistemicAssessment`

### 3. Reflex Logger
**Location:** `/empirica/core/canonical/reflex_logger.py`  
**Class:** `ReflexLogger`  
**Purpose:** Phase-specific JSON logging for temporal separation (prevents recursion)  
**Phases:** preflight, think, investigate, check, act, postflight

### 4. Bayesian Guardian
**Location:** `/empirica/core/metacognitive_cascade/adaptive_uncertainty_calibration/bayesian_belief_tracker.py`  
**Class:** `BayesianBeliefTracker`  
**Purpose:** Evidence-based belief tracking during investigation  
**Activation:** Precision-critical domains only (code_analysis, security_review, etc.)

### 5. Drift Monitor
**Location:** `/empirica/core/metacognitive_cascade/parallel_reasoning.py`  
**Class:** `DriftMonitor`  
**Purpose:** Behavioral integrity through delegate/trustee parallel reasoning  
**Patterns:** Sycophancy drift, tension avoidance

### 6. Goal Orchestrator
**Location:** `/empirica/components/goal_management/`  
**Purpose:** Goal decomposition and tracking for complex tasks

### 7. Investigation Plugin System
**Location:** `/empirica/core/metacognitive_cascade/investigation_plugin.py`  
**Classes:** `InvestigationPlugin`, `PluginRegistry`  
**Purpose:** Universal extensibility for custom domain tools

---

## Data Storage Architecture

### SQLite Database (`.empirica/empirica.db`)
**Tables:**
- `sessions` - AI session metadata
- `cascades` - Individual cascade runs
- `assessments` - Epistemic assessments (linked to cascades)
- `preflight_assessments` - Baseline assessments (Phase 1)
- `postflight_assessments` - Final assessments (Phase 7)
- All 13 vector columns in assessments tables

**Schema Handlers:**
- `/empirica/data/empirica_db_handler.py` - Database operations
- `/empirica/data/session_json_handler.py` - JSON export logic

### JSON Session Exports (`.empirica/sessions/`)
**Format:** Complete session data with all cascades and assessments  
**Purpose:** Human-readable audit trail, easy sharing/analysis  
**Auto-Export:** On cascade completion (POSTFLIGHT phase)

### Reflex Frame Logs (`.empirica_reflex_logs/`)
**Structure:**
```
.empirica_reflex_logs/
├── <ai_id>/
│   ├── <date>/
│   │   ├── preflight_<cascade_id>_<timestamp>.json
│   │   ├── investigate_<cascade_id>_<timestamp>.json
│   │   ├── check_<cascade_id>_<timestamp>.json
│   │   ├── act_<cascade_id>_<timestamp>.json
│   │   └── postflight_<cascade_id>_<timestamp>.json
```
**Purpose:** Real-time chain-of-thought for tmux dashboard, temporal separation

---

## Integration Points

### 1. MCP Server (Claude Desktop)
**Location:** `/mcp_local/empirica_mcp_server.py`  
**Tools:**
- `execute_preflight_assessment` - Run Phase 1
- `execute_postflight_assessment` - Run Phase 7
- `start_cascade_workflow` - Run full 7-phase cascade
- `query_session_cascades` - Query historical data
- `export_session_json` - Export session to JSON
- Component-specific tools (Goal Orchestrator, Bayesian Guardian, Drift Monitor)

### 2. Bootstrap
**Location:** `/empirica/bootstraps/optimal_metacognitive_bootstrap.py`  
**Purpose:** Lazy-load Empirica components for AI initialization  
**Loaded Components:**
- Canonical assessor
- Auto-tracker
- Reflex logger
- Workflow orchestrator
- All supporting components (Bayesian, Drift, Goal, etc.)

### 3. CLI
**Location:** `/empirica/cli/`  
**Commands:**
- `empirica cascade` - Run cascade workflow
- `empirica assess` - Quick epistemic assessment
- `empirica sessions-list` / `empirica sessions-show` - Query session data
- `empirica export` - Export sessions
- Component-specific commands

### 4. Claude Skills
**Location:** `/docs/empirica_skills/`  
**Files:**
- `CLAUDE_SKILLS_EMPIRICA_v1_UPDATED.md` - Complete skills guide
- `RECURSIVE_EPISTEMIC_REFINEMENT.md` - Workflow guidance
- `SKILLS_QUICK_REFERENCE.md` - Quick reference

---

## Self-Prompting Clarity

**CRITICAL UNDERSTANDING:**

1. **AI performs its OWN epistemic assessments**
   - Preflight: AI self-assesses baseline epistemic state
   - Postflight: AI self-assesses final epistemic state
   - This is NOT external evaluation

2. **Assessor components provide structured framework**
   - `PreflightAssessor` / `PostflightAssessor` are tools
   - They help AI structure its self-reflection
   - Results are logged for transparency/governance

3. **Self-check in INVESTIGATE loop**
   - `_assess_check_necessity()` allows AI to decide "do I need more investigation?"
   - Balances autonomy with accountability
   - Prevents premature action AND infinite loops

4. **No heuristics, no simulation, no fabrication**
   - All assessments are genuine LLM reasoning
   - Vector scores reflect actual epistemic state
   - Rationales are real AI thoughts, not pattern-matched keywords

---

## Common Confusion Points & Resolutions

### Confusion 1: "Which vector system should I use?"
**Resolution:** ALWAYS use the canonical 13-vector system (`/empirica/core/canonical/`) for production. The 12-vector system in `metacognition_12d_monitor/` is legacy/research only.

### Confusion 2: "Where do assessments happen?"
**Resolution:**
- **Preflight:** `/empirica/workflow/preflight_assessor.py` - baseline before cascade
- **During Investigation:** `CanonicalEpistemicAssessor` - re-assessment after tool use
- **Check Phase:** `CheckPhaseEvaluator._assess_check_necessity()` - self-check decision
- **Postflight:** `/empirica/workflow/postflight_assessor.py` - final after cascade

### Confusion 3: "Is the AI assessing itself or being assessed externally?"
**Resolution:** The AI is SELF-assessing. The assessor components are tools that help structure the AI's self-reflection. Think of them like a questionnaire the AI fills out about its own knowledge state.

### Confusion 4: "Where is the 13th vector (UNCERTAINTY)?"
**Resolution:** UNCERTAINTY is in the canonical `EpistemicAssessment` dataclass (`reflex_frame.py` line 102). It's a meta-epistemic vector tracking "uncertainty about the assessment itself."

### Confusion 5: "Why do reflex logs auto-write but DB doesn't always?"
**Resolution:** 
- Reflex logs auto-write every phase for real-time dashboard
- DB writes happen on cascade start/end and assessment points
- JSON exports happen on cascade completion (POSTFLIGHT)
- All controlled by `EmpericaTracker` auto-tracking

### Confusion 6: "What's the difference between cascade and workflow?"
**Resolution:** Same thing. "Enhanced Cascade Workflow" is the full name. We use "cascade" as shorthand.

### Confusion 7: "Do I need the bootstrap every time?"
**Resolution:** 
- First time: Yes, run bootstrap to load components into memory
- Subsequent turns: No, Claude pattern-matches from skills docs
- MCP server: Bootstrap runs once when MCP starts
- Direct API: Bootstrap components manually or use cascade directly

---

## Validation Checklist (Use This to Prevent Drift)

When you're unsure, check:

1. ☑️ Am I using canonical 13-vector system? (`/empirica/core/canonical/`)
2. ☑️ Am I using the workflow orchestrator? (`/empirica/workflow/cascade_workflow_orchestrator.py`)
3. ☑️ Are preflight/postflight assessments happening? (Check logs in `.empirica_reflex_logs/`)
4. ☑️ Is auto-tracking enabled? (Check DB `.empirica/empirica.db`)
5. ☑️ Am I doing genuine LLM assessment (not heuristics)?
6. ☑️ Am I following the 7-phase workflow spec? (`ENHANCED_CASCADE_WORKFLOW_SPEC.md`)
7. ☑️ Are component calls going through proper paths? (Not creating duplicate folders)

---

## Key Design Principles (Never Violate)

1. **No Heuristics:** All epistemic assessments are genuine LLM reasoning
2. **Temporal Separation:** Reflex logs prevent self-referential loops
3. **Suggestive, Not Controlling:** Investigation recommends tools, doesn't execute
4. **Engagement as Gate:** ≥0.60 required for collaboration
5. **13 Vectors:** 12 foundation + UNCERTAINTY (explicit meta-epistemic)
6. **Auto-Tracking:** Zero-effort logging to 3 formats (DB + JSON + Reflex)
7. **Pre/Post Validation:** Δ vectors measure actual improvement
8. **Self-Prompting:** AI performs its own assessments (not external scoring)

---

## Quick Reference: Where Is Everything?

**Workflow:**
- Orchestrator: `/empirica/workflow/cascade_workflow_orchestrator.py`
- Preflight: `/empirica/workflow/preflight_assessor.py`
- Postflight: `/empirica/workflow/postflight_assessor.py`
- Check Phase: `/empirica/workflow/check_phase_evaluator.py`

**Core:**
- Canonical Assessor: `/empirica/core/canonical/canonical_epistemic_assessment.py`
- Reflex Frame: `/empirica/core/canonical/reflex_frame.py`
- Reflex Logger: `/empirica/core/canonical/reflex_logger.py`
- Cascade: `/empirica/core/metacognitive_cascade/metacognitive_cascade.py`
- Investigation: `/empirica/core/metacognitive_cascade/investigation_strategy.py`

**Components:**
- Bayesian: `/empirica/core/metacognitive_cascade/adaptive_uncertainty_calibration/bayesian_belief_tracker.py`
- Drift Monitor: `/empirica/core/metacognitive_cascade/parallel_reasoning.py`
- Goal Orchestrator: `/empirica/components/goal_management/`
- All 11 components: `/empirica/components/<component_name>/`

**Data:**
- Auto-Tracker: `/empirica/auto_tracker.py`
- DB Handler: `/empirica/data/empirica_db_handler.py`
- JSON Handler: `/empirica/data/session_json_handler.py`

**Plugins:**
- Base Plugin: `/empirica/plugins/base_plugin.py`
- ModalitySwitcher Plugin: `/empirica/plugins/modality_switcher/`
  - Core Switcher: `modality_switcher.py` (5 routing strategies)
  - Snapshot Provider: `snapshot_provider.py` (epistemic compression)
  - Domain Vectors: `domain_vectors.py` (4 built-in + auto-discovery)
  - Adapters: `adapters/` (7 adapters: qwen, minimax, rovodev, gemini, qodo, openrouter, copilot)
  - Registry: `plugin_registry.py` (adapter registry)
  - Router: `epistemic_router.py` (intelligent routing)
  - Config: `config_loader.py` (deprecated - use credentials_loader)
  - Auth: `auth_manager.py` (deprecated - use credentials_loader)
  - Monitoring: `usage_monitor.py` (cost tracking)

**Config:**
- Credentials Loader: `/empirica/config/credentials_loader.py` (centralized API keys)
- Credentials File: `.empirica/credentials.yaml` (gitignored)

**Integration:**
- Bootstrap: `/empirica/bootstraps/optimal_metacognitive_bootstrap.py`
- MCP Server: `/mcp_local/empirica_mcp_server.py`
- CLI: `/empirica/cli/`

**Docs:**
- Skills: `/docs/empirica_skills/`
- Production: `/docs/production/`
- Spec: `/docs/production/ENHANCED_CASCADE_WORKFLOW_SPEC.md`
- Architecture Deep Dive: `/docs/production/SYSTEM_ARCHITECTURE_DEEP_DIVE.md`

---

## Modality Switcher Architecture (Phase 4-5)

### Overview

The Modality Switcher is a plugin system that enables intelligent routing across multiple AI providers with epistemic snapshot-based context transfer.

**Key Components:**
1. **ModalitySwitcher** - Core router with 5 strategies
2. **EpistemicSnapshotProvider** - Universal context compression (95%, 94% fidelity)
3. **DomainVectorRegistry** - Domain-specific epistemic dimensions
4. **AdapterRegistry** - Dynamic adapter management
5. **CredentialsLoader** - Centralized API key management

### Epistemic Snapshot Protocol

**Purpose:** Transfer context between different AI providers without re-explaining

**Compression:** 10,000 tokens → 500 tokens (95% compression)
**Fidelity:** 94% information retention
**Reliability:** 90% initial, degrades ~3% per hop

**Key Classes:**
```python
class EpistemicSnapshot:
    snapshot_id: str
    session_id: str
    ai_id: str  # Source AI
    cascade_phase: str  # think, investigate, uncertainty, check, act

    # Core context
    context_summary: ContextSummary
    semantic_tags: Dict[str, Any]

    # 13-vector assessment
    vectors: Dict[str, float]

    # Transfer tracking
    transfer_count: int  # Number of hops
    reliability: float  # 90% - (3% * transfer_count)

    # Compression metrics
    compression_ratio: float  # ~0.95
    fidelity_score: float  # ~0.94
    information_loss_estimate: float  # ~0.06

    # Refresh tracking
    should_refresh: bool
    refresh_reason: Optional[str]
```

**Location:** `/empirica/plugins/modality_switcher/snapshot_provider.py`

**Usage:**
```python
provider = EpistemicSnapshotProvider()

# Create snapshot
snapshot = provider.create_snapshot_from_session(
    session_id="session_123",
    context_summary_text="Current context",
    semantic_tags={"domain": "security"},
    cascade_phase="investigate"
)

# Transfer to different AI
adapter = MinimaxAdapter()
payload = AdapterPayload(
    system="You are an expert",
    user_query="Continue analysis",
    epistemic_snapshot=snapshot
)
result = adapter.call(payload, {})
```

### Adapter Architecture

**Total Adapters:** 7
**Total Models:** 15+

| Adapter | Models | Auth Method | Location |
|---------|--------|-------------|----------|
| **Qwen** | 4 models | API key (header) | `adapters/qwen_adapter.py` |
| **MiniMax** | 3 models | API key + group_id | `adapters/minimax_adapter.py` |
| **Rovodev** | 2 models | API key (header) | `adapters/rovodev_adapter.py` |
| **Gemini** | 2 models | Query param | `adapters/gemini_adapter.py` |
| **Qodo** | 2 models | API key (header) | `adapters/qodo_adapter.py` |
| **OpenRouter** | 2+ models | API key (header) | `adapters/openrouter_adapter.py` |
| **Copilot** | 3 models | CLI | `adapters/copilot_adapter.py` |

**Adapter Interface:**
```python
class BaseAdapter:
    def __init__(self, model: str = None):
        # Load credentials
        loader = get_credentials_loader()
        self.model = model or loader.get_default_model(provider_name)
        self.api_key = loader.get_api_key(provider_name)
        self.base_url = loader.get_base_url(provider_name)
        self.headers = loader.get_headers(provider_name)

    def call(self, payload: AdapterPayload, token_meta: Dict) -> Dict:
        # Execute API call
        # Track snapshot transfer if present
        # Return result with content
        pass
```

**Registry Usage:**
```python
from empirica.plugins.modality_switcher.plugin_registry import get_registry

registry = get_registry()

# Get adapter with model selection
adapter = registry.get('qwen')(model='qwen-coder-turbo')

# List all adapters
adapters = registry.list_adapters()
# ['qwen', 'minimax', 'rovodev', 'gemini', 'qodo', 'openrouter', 'copilot']
```

### Credentials System

**Purpose:** Centralized API key and model management

**Location:** `/empirica/config/credentials_loader.py`

**Features:**
- YAML-based configuration (`.empirica/credentials.yaml`)
- Environment variable interpolation (`${QWEN_API_KEY}`)
- Model validation per provider
- Fallback to legacy dotfiles
- Singleton pattern for caching
- Per-provider headers and URLs

**Configuration Structure:**
```yaml
version: "1.0"
providers:
  qwen:
    api_key: "${QWEN_API_KEY}"
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    default_model: "qwen-coder-plus"
    available_models: ["qwen-coder-plus", "qwen-coder-turbo", "qwen-max", "qwen-plus"]
    headers:
      Authorization: "Bearer ${api_key}"
      Content-Type: "application/json"
    auth_method: "header"

  gemini:
    api_key: "${GEMINI_API_KEY}"
    base_url: "https://generativelanguage.googleapis.com/v1beta/models"
    default_model: "gemini-2.0-flash-exp"
    available_models: ["gemini-2.0-flash-exp", "gemini-1.5-pro"]
    auth_method: "query_param"  # Different auth method
```

**Credentials Loader API:**
```python
from empirica.config.credentials_loader import get_credentials_loader

loader = get_credentials_loader()

# Get credentials
api_key = loader.get_api_key('qwen')
base_url = loader.get_base_url('qwen')
headers = loader.get_headers('qwen')

# Model validation
default = loader.get_default_model('qwen')
available = loader.get_available_models('qwen')
is_valid = loader.validate_model('qwen', 'qwen-coder-turbo')

# Check source
source = loader.get_credentials_source()  # 'config', 'dotfiles', or 'not_found'
```

### Domain Vector Registry

**Purpose:** Domain-specific epistemic dimensions for specialized assessment

**Location:** `/empirica/plugins/modality_switcher/domain_vectors.py`

**Built-in Domains (4):**
1. **code_analysis** - Software development and debugging
2. **medical_diagnosis** - Healthcare and clinical reasoning
3. **legal_analysis** - Legal reasoning and case analysis
4. **financial_analysis** - Financial modeling and analysis

**Auto-Discovery:**
- Registry discovers custom domains from usage patterns
- Weighted confidence calculation per domain
- Domain-specific vector weights

**Usage:**
```python
from empirica.plugins.modality_switcher.domain_vectors import DomainVectorRegistry

registry = DomainVectorRegistry()

# Get domain vectors
vectors = registry.get_domain_vectors('medical_diagnosis')
# ['diagnostic_accuracy', 'medical_knowledge', 'case_reasoning', ...]

# Register custom domain
registry.register_domain(
    domain_name='security_audit',
    description='Security vulnerability analysis',
    vectors=['threat_knowledge', 'attack_surface_awareness', ...]
)

# Calculate weighted confidence
confidence = registry.calculate_weighted_confidence(
    domain='code_analysis',
    vector_scores={'code_understanding': 0.85, ...}
)
```

### Routing Strategies

**5 Strategies Available:**

1. **EPISTEMIC** - Route based on task context and epistemic vectors
   - Analyzes task requirements
   - Matches to adapter strengths
   - Best for complex, context-dependent tasks

2. **COST** - Minimize token costs
   - Routes to cheapest provider
   - Considers token estimates
   - Best for budget-conscious applications

3. **LATENCY** - Fastest response time
   - Routes to lowest-latency provider
   - Real-time response critical
   - Best for interactive applications

4. **QUALITY** - Highest quality model
   - Routes to most capable model
   - Quality over cost/speed
   - Best for critical tasks

5. **BALANCED** - Balance cost/quality/latency
   - Weighted decision across metrics
   - Good general-purpose default
   - Best for mixed workloads

**ModalitySwitcher Usage:**
```python
from empirica.plugins.modality_switcher import ModalitySwitcher

switcher = ModalitySwitcher(strategy='epistemic')

result = switcher.route_and_execute(
    task="Write Python code to parse JSON",
    context={'domain': 'code_generation'}
)
# Routes to Qwen (code-specialized)

result = switcher.route_and_execute(
    task="Analyze complex legal precedent",
    context={'domain': 'legal_analysis'}
)
# Routes to Claude via Rovodev (reasoning-specialized)
```

### MCP Tools (7 Total)

**Snapshot Management (4):**
1. `snapshot_create` - Create epistemic snapshot
2. `snapshot_load` - Load snapshot by ID
3. `snapshot_transfer` - Transfer to different AI adapter
4. `snapshot_list` - List all snapshots in session

**Tmux Integration (3):**
5. `snapshot_dashboard_status` - Check dashboard status
6. `update_snapshot_display` - Update dashboard with new data
7. `launch_snapshot_dashboard` - Launch dashboard in tmux

**Location:** `/empirica/integration/mcp_local/empirica_mcp_server.py`

**Model Selection Support:**
All MCP tools support optional `model` parameter for adapter-specific model selection.

---

## When Memory Gets Compressed

If you find yourself confused or diverging from the architecture:

1. **Read this document first** (ARCHITECTURE_MAP.md)
2. **Read the spec** (`ENHANCED_CASCADE_WORKFLOW_SPEC.md`)
3. **Read the skills** (`CLAUDE_SKILLS_EMPIRICA_v1_UPDATED.md`)
4. **Use Empirica itself** - Run preflight assessment to track your own uncertainty
5. **Ask the user** - If still uncertain, ask for clarification (don't guess)

**Remember:** Empirica prevents drift by making you acknowledge when you DON'T know. Use it on yourself.

---

**Last Updated:** 2025-10-30  
**Version:** 2.0  
**Status:** ✅ CANONICAL REFERENCE
