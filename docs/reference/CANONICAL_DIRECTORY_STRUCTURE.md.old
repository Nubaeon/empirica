# Empirica Canonical Directory Structure

**Version:** 3.0  
**Date:** 2024  
**Purpose:** Definitive reference for Empirica's folder structure, file purposes, and integration points  
**Audience:** All AI agents, developers, and contributors

---

## Overview

This document provides the **canonical** (authoritative) description of Empirica's directory structure. Use this as the single source of truth for:
- Where files are located
- What each file/folder does
- How components integrate
- Where to add new functionality
- Import paths and dependencies

---

## Root Directory Structure

```
empirica/
├── empirica/                          # Core Python package
├── mcp_local/                         # MCP server implementations  
├── docs/                              # Documentation
├── tests/                             # Test suite
├── examples/                          # Working examples
├── scripts/                           # Utility scripts
├── claude-skills/                     # Claude Desktop skills (optional)
├── .empirica/                         # Runtime data (created on first use)
├── .empirica_reflex_logs/             # Reflex frame logs (created on first use)
├── pyproject.toml                     # Package configuration
├── setup.py                           # Package setup
├── requirements.txt                   # Dependencies
└── README.md                          # Main entry point
```

---

## 1. Core Package: `empirica/`

The main Python package containing all core functionality.

### 1.1 Core Epistemic Framework: `empirica/core/`

**Purpose:** Genuine epistemic self-assessment system (no heuristics)

```
empirica/core/
├── canonical/                         # 13-vector canonical assessment
│   ├── __init__.py                    # Exports: CanonicalEpistemicAssessor, EpistemicAssessment, etc.
│   ├── canonical_epistemic_assessment.py  # LLM-powered self-assessment
│   ├── canonical_goal_orchestrator.py     # Goal orchestration (LLM or threshold modes) ⭐ UPDATED
│   ├── git_enhanced_reflex_logger.py      # Git-enhanced logging (Phase 1.5) ⭐ NEW
│   ├── reflex_frame.py                    # Data structures (EpistemicAssessment, VectorState, Action)
│   └── reflex_logger.py                   # Phase-specific JSON logging (legacy)
│
└── metacognitive_cascade/             # CASCADE workflow (7 phases)
    ├── __init__.py
    ├── metacognitive_cascade.py       # Main workflow orchestrator
    ├── investigation_plugin.py        # Plugin interface (user extensions)
    ├── investigation_strategy.py      # Domain-aware investigation
    └── mcp_aware_investigation.py     # MCP tool execution during investigation
```

#### Key Files Explained:

**`canonical/canonical_epistemic_assessment.py`** (841 lines)
- **Class:** `CanonicalEpistemicAssessor`
- **Purpose:** Generates LLM self-assessment prompts, parses responses
- **Key Method:** `async assess(task, context) -> EpistemicAssessment`
- **No Heuristics:** Pure LLM reasoning, no keyword matching
- **Import:** `from empirica.core.canonical import CanonicalEpistemicAssessor`

**`canonical/canonical_goal_orchestrator.py`** ⭐ UPDATED (Nov 2024)
- **Class:** `CanonicalGoalOrchestrator`
- **Purpose:** Goal generation with two modes:
  - **LLM mode** (`use_placeholder=False`): AI reasons about goals via `llm_callback`
  - **Threshold mode** (`use_placeholder=True`): Fast threshold-based goals (default)
- **Key Method:** `generate_goals(conversation_context, epistemic_assessment)`
- **New Parameter:** `llm_callback(prompt: str) -> str` - Function for AI reasoning
- **Example:**
  ```python
  def my_llm(prompt: str) -> str:
      return ai_client.reason(prompt)
  
  orchestrator = create_goal_orchestrator(
      llm_callback=my_llm,
      use_placeholder=False  # Use AI reasoning
  )
  ```
- **Import:** `from empirica.core.canonical import create_goal_orchestrator`

**`canonical/git_enhanced_reflex_logger.py`** ⭐ NEW (Phase 1.5)
- **Class:** `GitEnhancedReflexLogger`
- **Purpose:** ~85% token reduction via git notes integration
- **Features:**
  - Compressed checkpoints (46 tokens vs 1,821 tokens baseline)
  - Git notes storage for epistemic snapshots
  - SQLite fallback when git unavailable
  - Backward compatible with existing reflex logs
- **Metrics:**
  - Baseline session loading: ~1,821 tokens
  - Git-enhanced loading: 46 tokens
  - Reduction: ~85%
- **Import:** `from empirica.core.canonical import GitEnhancedReflexLogger`

**`canonical/reflex_frame.py`** (327 lines)
- **Classes:** `VectorState`, `EpistemicAssessment`, `ReflexFrame`, `Action` enum
- **Purpose:** Data structures for epistemic state
- **Constants:** `CANONICAL_WEIGHTS`, `ENGAGEMENT_THRESHOLD`, `CRITICAL_THRESHOLDS`
- **Vector Format:** Floats (0.0-1.0), no percentages in core
- **Import:** `from empirica.core.canonical.reflex_frame import EpistemicAssessment, Action`

**`metacognitive_cascade/metacognitive_cascade.py`** (1250 lines)
- **Class:** `CanonicalEpistemicCascade`
- **Purpose:** Orchestrates 7-phase CASCADE workflow
- **Phases:** PREFLIGHT → THINK → PLAN → INVESTIGATE → CHECK → ACT → POSTFLIGHT
- **Investigation Loop:** Self-check continues until AI is satisfied
- **Import:** `from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade`

**Integration Point for Profiles:**
```python
# Current usage:
cascade = CanonicalEpistemicCascade(
    max_investigation_rounds=3,  # To be replaced
    action_confidence_threshold=0.70  # To be replaced
)

# Future usage with profiles:
cascade = CanonicalEpistemicCascade(
    profile_name='high_reasoning_collaborative',
    ai_model='claude-sonnet',
    domain='research'
)
```

---

### 1.2 Investigation System: `empirica/investigation/`

**Purpose:** Pluggable investigation strategies and user extensions

```
empirica/investigation/
├── __init__.py
├── investigation_plugin.py            # Plugin interface for user extensions
├── investigation_strategy.py          # Domain-aware strategy pattern
└── advanced_investigation/
    ├── __init__.py
    └── advanced_investigation.py      # Complex multi-step workflows
```

#### Key Files Explained:

**`investigation_plugin.py`** (300 lines)
- **Class:** `InvestigationPlugin`
- **Purpose:** Allows users to add custom investigation tools
- **Example:** JIRA search, database queries, API calls
- **Usage:**
  ```python
  jira_plugin = InvestigationPlugin(
      name='jira_search',
      description='Search JIRA for related issues',
      improves_vectors=['know', 'context', 'state'],
      confidence_gain=0.20,
      executor=jira_search_function
  )
  cascade = CanonicalEpistemicCascade(
      investigation_plugins={'jira': jira_plugin}
  )
  ```

**`investigation_strategy.py`** (510 lines)
- **Classes:** `BaseInvestigationStrategy`, `CodeAnalysisStrategy`, `ResearchStrategy`, etc.
- **Purpose:** Domain-aware tool recommendations (code, research, creative, etc.)
- **Current Issue:** Uses keyword-based domain detection (needs profile integration)
- **Future:** Profile-driven domain detection and tool suggestion modes

**Profile Integration Point:**
```python
# Investigation strategy will use profile settings:
# - profile.strategy.domain_detection (reasoning vs keyword vs declared)
# - profile.investigation.tool_suggestion_mode (light vs guided vs prescribed)
# - profile.investigation.allow_novel_approaches (true/false)
```

---

### 1.3 Configuration System: `empirica/config/` ⭐ NEW

**Purpose:** Profile-based investigation configuration

```
empirica/config/
├── __init__.py
├── investigation_profiles.yaml        # 5 profiles (high_reasoning, autonomous, critical, exploratory, balanced)
├── profile_loader.py                  # Profile loading and selection logic
├── modality_config.yaml               # Modality switcher configuration (optional plugin)
└── credentials_loader.py              # API credentials (optional plugin)
```

#### Key Files Explained:

**`investigation_profiles.yaml`** (418 lines) ⭐ NEW
- **Purpose:** Context-aware investigation constraints
- **Sections:**
  - `universal_constraints` - Sentinel-enforced (engagement gate, timeouts, etc.)
  - `profiles` - 5 pre-configured profiles
  - `profile_selection` - Auto-selection rules (by AI type, domain)
  - `plugin_integration` - How plugins interact with profiles
- **Profiles:**
  1. **high_reasoning_collaborative** - Max autonomy (Claude, GPT-4, o1)
  2. **autonomous_agent** - Structured (GPT-3.5, Claude Haiku)
  3. **critical_domain** - Strict compliance (medical, financial, legal)
  4. **exploratory** - Max freedom (research, learning)
  5. **balanced** - Default middle-ground

**`profile_loader.py`** (391 lines) ⭐ NEW
- **Classes:** `InvestigationProfile`, `ProfileLoader`, plus dataclasses
- **Purpose:** Load, select, validate, export/import profiles
- **Key Functions:**
  ```python
  from empirica.config.profile_loader import select_profile, load_profile
  
  # Auto-select based on context
  profile = select_profile(ai_model='claude-sonnet', domain='medical')
  
  # Explicit selection
  profile = load_profile('high_reasoning_collaborative')
  ```

---

### 1.4 Data Management: `empirica/data/`

**Purpose:** Persistence, export/import, tracking

```
empirica/data/
├── __init__.py
├── session_database.py                # SQLite database (sessions, cascades, assessments, goals)
└── session_json_handler.py            # JSON session export/import
```

#### Key Files Explained:

**`session_database.py`** (1100 lines)
- **Class:** `SessionDatabase`
- **Purpose:** SQLite persistence with auto-initialization
- **Schema:**
  - `sessions` - Session metadata
  - `cascades` - CASCADE executions
  - `epistemic_assessments` - All 13-vector assessments (PREFLIGHT, CHECK, POSTFLIGHT)
  - `goals` - Goal tracking
- **Location:** `.empirica/sessions/sessions.db` (auto-created)
- **Recent Fix:** Added `uncertainty`, `uncertainty_rationale`, `uncertainty_evidence` columns

**`session_json_handler.py`** (400 lines)
- **Class:** `SessionJSONHandler`
- **Purpose:** Export sessions to portable JSON files
- **Location:** `.empirica/sessions/<session_id>.json`

**Auto-Tracking Integration:**
```python
from empirica.auto_tracker import EmpericaTracker

tracker = EmpericaTracker()
await tracker.log_assessment(assessment, phase='preflight')
# Automatically writes to:
# - SQLite database
# - JSON session file
# - Reflex frame logs
```

---

### 1.5 CLI: `empirica/cli/`

**Purpose:** Command-line interface for Empirica

```
empirica/cli/
├── __init__.py
├── __main__.py                        # Entry point (python -m empirica.cli)
├── cli_core.py                        # Main CLI logic
├── cli_utils.py                       # Utility functions
├── simple_session_server.py           # Session server for continuity
├── uvl_formatter.py                   # UVL (Universal Vector Language) formatting
└── command_handlers/                  # Command implementations
    ├── __init__.py
    ├── ask_handler.py                 # Ask command (interactive Q&A)
    ├── assessment_commands.py         # Preflight/check/postflight commands
    ├── bootstrap_commands.py          # Session bootstrapping
    ├── cascade_commands.py            # CASCADE workflow commands
    ├── chat_handler.py                # Chat command
    ├── component_commands.py          # Component management
    ├── config_commands.py             # Configuration
    ├── decision_commands.py           # Decision logging
    ├── investigation_commands.py      # Investigation phase commands
    ├── mcp_commands.py                # MCP server commands
    ├── monitor_commands.py            # Dashboard monitoring
    ├── onboard_handler.py             # Onboarding wizard
    ├── performance_commands.py        # Performance analysis
    ├── session_commands.py            # Session management
    └── utility_commands.py            # Miscellaneous utilities
```

#### Profile Integration Point:
```bash
# Future CLI usage:
empirica session-create --profile high_reasoning_collaborative
empirica session-create --ai-model claude-sonnet --domain medical  # Auto-selects profile
empirica profile list  # List available profiles
empirica profile show high_reasoning_collaborative  # Show profile details
```

---

### 1.6 Components: `empirica/components/`

**Purpose:** Optional advanced components

```
empirica/components/
├── __init__.py
├── code_intelligence_analyzer/        # Code analysis (optional)
├── context_validation/                # Context validation (optional)
├── empirical_performance_analyzer/    # Performance tracking (optional)
├── environment_stabilization/         # Environment checks (optional)
├── goal_management/                   # Goal orchestration
│   └── autonomous_goal_orchestrator/
├── intelligent_navigation/            # Workspace navigation (optional)
├── procedural_analysis/               # Procedure analysis (optional)
├── runtime_validation/                # Runtime checks (optional)
├── security_monitoring/               # Security analysis (optional)
├── tool_management/                   # Enhanced tool handling
│   ├── enhanced_bash_tools.py
│   ├── enhanced_file_tools.py
│   ├── epistemic_tool_selector_minimal.py
│   └── meta_mcp_registry.py
└── workspace_awareness/               # Workspace understanding (optional)
```

**Note:** Most components are optional/experimental. Core functionality doesn't depend on them.

---

### 1.7 Plugins: `empirica/plugins/`

**Purpose:** Optional extensions (not required for core functionality)

```
empirica/plugins/
├── __init__.py
├── base_plugin.py                     # Plugin base class
├── dashboard_spawner.py               # Dashboard launcher
└── modality_switcher/                 # Multi-AI routing (optional)
    ├── __init__.py
    ├── modality_switcher.py           # Main plugin
    ├── config_loader.py
    ├── epistemic_router.py            # Route tasks to different AIs
    ├── genuine_self_assessment.py
    ├── snapshot_provider.py
    ├── thinking_analyzer.py
    ├── usage_monitor.py
    ├── adapters/                      # AI adapters (Gemini, Qwen, OpenRouter, etc.)
    │   ├── gemini_adapter.py
    │   ├── qwen_adapter.py
    │   ├── openrouter_adapter.py
    │   ├── minimax_adapter.py
    │   ├── copilot_adapter.py
    │   ├── rovodev_adapter.py
    │   └── local_adapter.py
    └── domain_vectors_custom/         # Custom domain vectors
        └── example_chemistry.py
```

**Modality Switcher:** Optional plugin for routing tasks to different AI models based on epistemic assessment.

---

### 1.8 Dashboard: `empirica/dashboard/`

**Purpose:** Real-time monitoring (optional)

```
empirica/dashboard/
├── __init__.py
├── cascade_monitor.py                 # CASCADE workflow visualization
└── snapshot_monitor.py                # Real-time epistemic state
```

**Display Format:**
- Input: Floats (0.0-1.0) from core
- Processing: Threshold-based coloring (≥0.90 green, ≥0.80 yellow, etc.)
- Output: Visual bars and indicators

---

### 1.9 Calibration: `empirica/calibration/`

**Purpose:** Advanced calibration systems (optional/experimental)

```
empirica/calibration/
├── __init__.py
├── parallel_reasoning.py              # Drift monitor (sycophancy detection)
└── adaptive_uncertainty_calibration/  # Bayesian guardian
    ├── __init__.py
    ├── adaptive_uncertainty_calibration.py
    └── bayesian_belief_tracker.py
```

**Status:** Experimental. Future integration with Sentinel for governance.

---

### 1.10 Bootstraps: `empirica/bootstraps/`

**Purpose:** Session initialization and onboarding

```
empirica/bootstraps/
├── __init__.py
├── onboarding_wizard.py               # Interactive AI onboarding
├── optimal_metacognitive_bootstrap.py # Optimal session setup
└── extended_metacognitive_bootstrap.py # Extended setup
```

---

### 1.11 Cognitive Benchmarking: `empirica/cognitive_benchmarking/`

**Purpose:** AI capability assessment (experimental)

```
empirica/cognitive_benchmarking/
├── __init__.py
├── README.md
├── SUMMARY.md
├── erb/                               # Epistemic Reasoning Benchmark
│   ├── epistemic_reasoning_benchmark.py
│   ├── preflight_assessor.py
│   ├── check_phase_evaluator.py
│   ├── postflight_assessor.py
│   └── cascade_workflow_orchestrator.py
├── cloud_adapters/                    # Cloud AI adapters for testing
│   └── unified_cloud_adapter.py
└── results/                           # Benchmark results
```

**Purpose:** Assess AI epistemic reasoning capability. Used to determine if AI should use high_reasoning profile vs autonomous profile.

---

### 1.12 Metrics: `empirica/metrics/`

**Purpose:** Token efficiency and performance tracking ⭐ NEW (Phase 1.5)

```
empirica/metrics/
├── __init__.py
└── token_efficiency.py                # Token reduction metrics and reporting
```

**`token_efficiency.py`**
- **Class:** `TokenEfficiencyMetrics`
- **Purpose:** Measure and validate Phase 1.5 token reduction
- **Features:**
  - Baseline vs optimized token counting
  - Efficiency calculations (~85% measured)
  - Report generation for validation
- **Import:** `from empirica.metrics import TokenEfficiencyMetrics`

---

### 1.13 Integration: `empirica/integration/`

**Purpose:** Integration hooks (future)

```
empirica/integration/
├── __init__.py
└── empirica_action_hooks.py           # Action hooks for extensions
```

---

## 2. MCP Server: `mcp_local/`

**Purpose:** IDE integration via Model Context Protocol

```
mcp_local/
├── __init__.py
├── empirica_mcp_server.py             # Main MCP server (22 tools)
├── code_guidance_mcp_server.py        # Code guidance (optional)
├── empirica_tmux_mcp_server.py        # Dashboard MCP (optional)
├── start_empirica_mcp.sh              # Startup script
└── archive/                           # Archived documentation
```

### MCP Server Tools (22 total):

**Session Management:**
- `create_session` - Initialize new session (replaces bootstrap_session)
- `resume_previous_session` - Resume prior session
- `get_session_summary` - Get session details
- `get_epistemic_state` - Query current epistemic vectors

**Assessment Workflow:**
- `execute_preflight` - Start PREFLIGHT assessment
- `submit_preflight_assessment` - Submit PREFLIGHT vectors
- `execute_check` - Start CHECK assessment
- `submit_check_assessment` - Submit CHECK vectors
- `execute_postflight` - Start POSTFLIGHT assessment
- `submit_postflight_assessment` - Submit POSTFLIGHT vectors

**Monitoring & Analysis:**
- `get_calibration_report` - Get calibration accuracy
- `query_bayesian_beliefs` - Query belief states
- `check_drift_monitor` - Check for sycophancy drift
- `query_goal_orchestrator` - Query goals

**Utility:**
- `get_empirica_introduction` - Onboarding for first-time AIs
- `get_workflow_guidance` - Phase-specific guidance
- `cli_help` - CLI command help
- `execute_cli_command` - Execute any CLI command
- `query_ai` - AI-to-AI communication
- `generate_goals` - Goal generation
- `create_cascade` - Create new cascade

**Profile Integration Point:**
```python
# MCP tool usage:
create_session(
    ai_id="claude_agent",
    profile="high_reasoning_collaborative",  # Optional
    ai_model="claude-sonnet",                # Optional
    domain="research"                        # Optional
)
```

---

## 3. Documentation: `docs/`

**Purpose:** Comprehensive documentation for all users

```
docs/
├── 00_START_HERE.md                   # Entry point for humans
├── 01_a_AI_AGENT_START.md             # Entry point for AI agents (CLI)
├── 01_b_MCP_AI_START.md               # Entry point for AI agents (MCP)
├── 02_INSTALLATION.md                 # Installation guide
├── 03_CLI_QUICKSTART.md               # CLI quick start
├── 04_MCP_QUICKSTART.md               # MCP quick start
├── 05_ARCHITECTURE.md                 # High-level architecture
├── 06_TROUBLESHOOTING.md              # Common issues
├── ARCHITECTURE_ORGANIZATION.md       # [TO BE ARCHIVED]
├── EMPIRICA_MCP_CONFIG.json           # MCP configuration example
├── ONBOARDING_GUIDE.md                # Onboarding guide
│
├── reference/                         # Reference documentation
│   ├── ARCHITECTURE_MAP.md            # [TO BE REFACTORED]
│   ├── DIRECTORY_STRUCTURE.md         # [TO BE ARCHIVED - merged into CANONICAL]
│   ├── CANONICAL_DIRECTORY_STRUCTURE.md  # ⭐ THIS DOCUMENT
│   ├── ARCHITECTURE_OVERVIEW.md       # ⭐ NEW - System architecture
│   ├── BOOTSTRAP_QUICK_REFERENCE.md
│   ├── CHANGELOG.md
│   ├── COMPLETE_ARCHITECTURE_REFERENCE.md
│   ├── EMPIRICA_CASCADE_WORKFLOW_SPECIFICATION.md
│   └── QUICK_REFERENCE.md
│
├── production/                        # Production documentation
│   ├── 00_COMPLETE_SUMMARY.md
│   ├── 01_QUICK_START.md
│   ├── 04_ARCHITECTURE_OVERVIEW.md
│   ├── 05_EPISTEMIC_VECTORS.md
│   ├── 06_CASCADE_FLOW.md
│   ├── 12_SESSION_DATABASE.md
│   └── ...  (22 total docs)
│
├── guides/                            # User guides
│   ├── CLI_WORKFLOW_COMMANDS_COMPLETE.md
│   ├── CRITICAL_NO_HEURISTICS_PRINCIPLE.md
│   ├── INVESTIGATION_PROFILES.md      # ⭐ NEW - Profile system guide
│   └── ...
│
├── skills/                            # Empirica skills documentation
│   └── SKILL.md
│
└── archive/                           # Archived documentation
    └── [Old docs moved here]
```

---

## 4. Tests: `tests/`

**Purpose:** Test suite for validation

```
tests/
├── __init__.py
├── conftest.py                        # Pytest configuration
├── test_phase0_plugin_registry.py     # Plugin tests
│
├── unit/                              # Unit tests
│   ├── canonical/                     # Canonical system tests
│   │   ├── test_epistemic_assessor.py
│   │   ├── test_goal_orchestrator.py
│   │   ├── test_reflex_frame.py
│   │   └── test_reflex_logger.py
│   ├── cascade/                       # CASCADE workflow tests
│   │   ├── test_preflight.py
│   │   ├── test_check.py
│   │   ├── test_postflight.py
│   │   └── ...
│   ├── data/                          # Data layer tests
│   │   ├── test_session_database.py
│   │   └── test_json_handler.py
│   └── config/                        # ⭐ NEW - Profile system tests
│       ├── test_profile_loader.py
│       └── test_profile_selection.py
│
├── integration/                       # Integration tests
│   ├── test_cascade_with_tracking.py
│   ├── test_complete_workflow.py
│   ├── test_e2e_cascade.py
│   ├── test_full_cascade.py
│   ├── test_mcp_workflow.py
│   └── test_profile_cascade.py        # ⭐ NEW - Profile integration tests
│
├── mcp/                               # MCP server tests
│   ├── test_mcp_server_startup.py
│   └── test_mcp_tools.py
│
└── coordination/                      # Multi-AI coordination docs
    ├── README.md
    ├── FINAL_STATUS.md
    └── ...
```

---

## 5. Examples: `examples/`

**Purpose:** Working examples and demonstrations

```
examples/
└── reasoning_reconstruction/          # Knowledge transfer examples
    ├── 01_basic_reconstruction.sh     # Extract learning from sessions
    ├── 02_knowledge_transfer.py       # AI-to-AI knowledge transfer
    └── README.md
```

---

## 6. Runtime Data: `.empirica/` (auto-created)

**Purpose:** Runtime data storage (created on first use)

```
.empirica/
├── sessions/                          # Session storage
│   ├── sessions.db                    # SQLite database
│   └── <session_id>.json              # JSON session exports
└── config/                            # Runtime configuration
    └── user_preferences.json          # User preferences (optional)
```

**Auto-Initialization:** Created automatically on first use, no manual setup needed.

---

## 7. Reflex Logs: `.empirica_reflex_logs/` (auto-created)

**Purpose:** Temporal separation logs (prevents recursion)

```
.empirica_reflex_logs/
└── <ai_id>/                           # Per-AI agent logs
    └── <date>/                        # Per-date logs
        ├── preflight_<timestamp>.json
        ├── investigate_<timestamp>.json
        ├── check_<timestamp>.json
        └── postflight_<timestamp>.json
```

**Purpose:** Separates current reasoning from historical reasoning, preventing self-referential loops.

---

## Import Path Reference

### Core Imports:

```python
# Canonical epistemic assessment
from empirica.core.canonical import (
    CanonicalEpistemicAssessor,
    EpistemicAssessment,
    VectorState,
    Action,
    CANONICAL_WEIGHTS,
    ENGAGEMENT_THRESHOLD
)

# CASCADE workflow
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

# Reflex frame structures
from empirica.core.canonical.reflex_frame import ReflexFrame

# Profile system ⭐ NEW
from empirica.config.profile_loader import (
    select_profile,
    load_profile,
    get_profile_loader,
    InvestigationProfile
)

# Data management
from empirica.data.session_database import SessionDatabase
from empirica.data.session_json_handler import SessionJSONHandler

# Auto-tracking
from empirica.auto_tracker import EmpericaTracker

# Investigation plugins
from empirica.investigation.investigation_plugin import InvestigationPlugin
from empirica.investigation.investigation_strategy import (
    BaseInvestigationStrategy,
    CodeAnalysisStrategy,
    Domain
)
```

---

## Where to Add New Functionality

### Adding a New Investigation Plugin:
1. Create plugin using `InvestigationPlugin` class
2. No file changes needed - plugins are registered at runtime
3. Example:
   ```python
   custom_plugin = InvestigationPlugin(
       name='my_tool',
       description='My custom investigation tool',
       improves_vectors=['know', 'context'],
       confidence_gain=0.15,
       executor=my_function
   )
   ```

### Adding a New Investigation Strategy:
1. Location: `empirica/investigation/investigation_strategy.py`
2. Inherit from `BaseInvestigationStrategy`
3. Implement `recommend_tools()` method
4. Register in strategy factory

### Adding a New Profile:
1. Location: `empirica/config/investigation_profiles.yaml`
2. Add new profile under `profiles:` section
3. Follow existing profile structure
4. No code changes needed

### Adding a New MCP Tool:
1. Location: `mcp_local/empirica_mcp_server.py`
2. Add tool method with `@mcp.tool()` decorator
3. Update tool count in comments
4. Document in `docs/production/20_TOOL_CATALOG.md`

### Adding a New Component:
1. Location: `empirica/components/<component_name>/`
2. Create `__init__.py` and main module file
3. Add imports to `empirica/components/__init__.py`
4. Document integration points

---

## Dependencies

### Core Dependencies:
- Python 3.8+
- Standard library (json, sqlite3, dataclasses, etc.)
- No external dependencies for core functionality

### Optional Dependencies:
- `click` - CLI interface
- `pyyaml` - YAML configuration
- `aiohttp` - Async HTTP (for MCP server)
- `pytest` - Testing
- Various cloud AI SDKs (for modality switcher)

---

## File Naming Conventions

### Python Modules:
- `snake_case.py` - All lowercase with underscores
- `__init__.py` - Package initialization
- `test_*.py` - Test files

### Documentation:
- `UPPERCASE_WITH_UNDERSCORES.md` - Major documents
- `lowercase_with_underscores.md` - Minor documents
- `01_PREFIX_NAME.md` - Numbered sequence documents

### Configuration:
- `lowercase_config.yaml` - YAML configuration
- `lowercase_config.json` - JSON configuration

---

## Version History

### v3.0 (Current)
- Added profile system (`empirica/config/`)
- Unified directory structure documentation
- Clarified investigation system architecture
- Added comprehensive import reference

### v2.0
- Separated canonical (13-vector) from legacy systems
- Added CASCADE workflow
- Improved documentation structure

### v1.0
- Initial structure
- Basic epistemic assessment
- Simple CASCADE workflow

---

## Notes for AI Agents

1. **Vector Format:** Always use floats (0.0-1.0), never percentages in core code
2. **Profile System:** Use profiles for context-aware constraints, not hardcoded values
3. **Investigation Plugins:** User-provided tools that SUGGEST, don't PRESCRIBE
4. **Temporal Separation:** Reflex logs prevent self-referential recursion
5. **Auto-Tracking:** Database, JSON, and reflex logs populated simultaneously
6. **No Heuristics:** Genuine LLM reasoning only, no keyword matching in canonical system

---

## Quick Reference: Key Locations

| What | Where |
|------|-------|
| Epistemic assessment | `empirica/core/canonical/canonical_epistemic_assessment.py` |
| CASCADE workflow | `empirica/core/metacognitive_cascade/metacognitive_cascade.py` |
| Data structures | `empirica/core/canonical/reflex_frame.py` |
| Database | `empirica/data/session_database.py` |
| MCP server | `mcp_local/empirica_mcp_server.py` |
| CLI | `empirica/cli/cli_core.py` |
| Profiles | `empirica/config/investigation_profiles.yaml` |
| Profile loader | `empirica/config/profile_loader.py` |
| Investigation plugins | `empirica/investigation/investigation_plugin.py` |
| Investigation strategy | `empirica/investigation/investigation_strategy.py` |
| Tests | `tests/` |
| Documentation | `docs/` |

---

## Support

For questions about the directory structure:
- Check this document first (canonical reference)
- See `docs/reference/ARCHITECTURE_OVERVIEW.md` for system architecture
- See `docs/01_a_AI_AGENT_START.md` for AI agent onboarding
- See `docs/production/` for detailed production documentation

