# Empirica Directory Structure

**Renamed from:** `empirica` → `empirica`  
**Date:** 2025-10-28  
**Status:** Reorganized for semantic clarity

---

## Directory Layout

```
empirica/
├── empirica/                          # Main package
│   ├── __init__.py                   # Package initialization
│   │
│   ├── core/                         # Core metacognitive system
│   │   ├── canonical/                # Canonical data structures & assessor
│   │   ├── metacognitive_cascade/    # Main reasoning cascade
│   │   └── metacognition_12d_monitor/ # 12D epistemic monitoring
│   │
│   ├── data/                         # Data storage & persistence
│   │   ├── session_database.py       # SQLite session database
│   │   └── session_json_handler.py   # JSON exports for AI reading
│   │
│   ├── calibration/                  # Uncertainty & belief tracking
│   │   ├── adaptive_uncertainty_calibration/ # Adaptive calibration
│   │   ├── bayesian_belief_tracker.py        # Bayesian Guardian
│   │   └── parallel_reasoning.py             # Drift monitoring
│   │
│   ├── investigation/                # Investigation strategies & tools
│   │   ├── investigation_strategy.py # Domain-aware strategies
│   │   ├── investigation_plugin.py   # Plugin system
│   │   └── advanced_investigation/   # Deep investigation tools
│   │
│   ├── integration/                  # MCP servers & external interfaces
│   │   ├── mcp_local/                # MCP server for Claude Desktop
│   │   └── empirica_action_hooks.py  # Tmux dashboard hooks
│   │
│   ├── bootstraps/                   # System initialization
│   │   ├── optimal_metacognitive_bootstrap.py    # Minimal (Tier 0+1)
│   │   └── extended_metacognitive_bootstrap.py   # Full (Tier 0-4)
│   │
│   ├── components/                   # Extended modular components
│   │   ├── context_validation/       # ICT/PCT truth grounding
│   │   ├── runtime_validation/       # Execution safety
│   │   ├── workspace_awareness/      # Spatial intelligence
│   │   ├── environment_stabilization/ # Cross-platform stability
│   │   ├── code_intelligence_analyzer/ # Code analysis
│   │   ├── security_monitoring/      # Threat detection
│   │   ├── procedural_analysis/      # Process analysis
│   │   ├── tool_management/          # AI-enhanced tools
│   │   ├── intelligent_navigation/   # Smart navigation
│   │   └── empirical_performance_analyzer/ # Performance tracking
│   │
│   ├── config/                       # Configuration management
│   │   ├── __init__.py              # Package init
│   │   └── credentials_loader.py    # Centralized credentials (singleton) ✅
│   │
│   ├── plugins/                      # Plugin system (pluggable extensions)
│   │   ├── base_plugin.py           # Plugin interface
│   │   └── modality_switcher/       # ModalitySwitcher plugin (Phase 0-5 ✅)
│   │       ├── __init__.py          # Exports
│   │       ├── plugin_manifest.json # Metadata
│   │       ├── modality_switcher.py # Core switcher (5 routing strategies)
│   │       ├── plugin_registry.py   # Adapter registry
│   │       ├── register_adapters.py # Adapter registration
│   │       ├── epistemic_router.py  # Epistemic-driven routing
│   │       ├── snapshot_provider.py # Epistemic snapshot management ✅
│   │       ├── domain_vectors.py    # Domain registry (4 built-in + auto-discovery) ✅
│   │       ├── config_loader.py     # Configuration (deprecated - use credentials_loader)
│   │       ├── auth_manager.py      # Authentication (deprecated - use credentials_loader)
│   │       ├── usage_monitor.py     # Usage tracking and cost monitoring
│   │       ├── adapters/            # All adapter implementations (7 adapters)
│   │       │   ├── __init__.py
│   │       │   ├── qwen_adapter.py       # Qwen (Alibaba Cloud) - Code-specialized ✅
│   │       │   ├── minimax_adapter.py    # MiniMax Research API ✅
│   │       │   ├── rovodev_adapter.py    # Rovodev (Claude wrapper) ✅
│   │       │   ├── gemini_adapter.py     # Google Gemini (free tier) ✅
│   │       │   ├── qodo_adapter.py       # Qodo (OpenAI wrapper) ✅
│   │       │   ├── openrouter_adapter.py # OpenRouter (multi-provider) ✅
│   │       │   ├── copilot_adapter.py    # GitHub Copilot ($10/month) ✅
│   │       │   ├── local_adapter.py      # Local models (stub)
│   │       │   └── tests/           # Adapter tests
│   │       └── tests/               # Plugin tests
│   │
│   ├── cli/                          # Command-line interface
│   │   └── ... (CLI components)
│   │
│   └── deprecated/                   # Archived old code
│       └── ... (legacy components)
│
├── .empirica/                        # Runtime data (hidden, git ignored)
│   ├── credentials.yaml             # API keys and provider config (DO NOT COMMIT) ✅
│   ├── credentials.yaml.template    # Template for setup
│   ├── sessions/                     # Session database
│   │   └── sessions.db              # SQLite database
│   ├── exports/                      # JSON exports
│   │   ├── session_*.json
│   │   └── cascade_*_graph.json
│   └── backups/                      # Database backups
│
├── .empirica_reflex_logs/            # Reflex Frame logs
│   └── cascade/
│       └── YYYY-MM-DD/
│           └── *.json
│
├── docs/                             # Documentation
│   └── ... (all documentation files)
│
├── tests/                            # Test suite
│
├── examples/                         # Usage examples
│
└── empirica/          # OLD DIRECTORY (to be removed)
    └── ... (leftover files)
```

---

## Key Directories Explained

### Core (`empirica/core/`)
**Purpose:** Essential metacognitive reasoning system  
**Contains:**
- Canonical data structures (VectorState, EpistemicAssessment, ReflexFrame)
- Canonical epistemic assessor (LLM-powered, no heuristics)
- Complete reasoning cascade (THINK → UNCERTAINTY → INVESTIGATE → CHECK → ACT)
- 12D epistemic monitoring with ENGAGEMENT gate

**Import Example:**
```python
from empirica.core.canonical import CanonicalEpistemicAssessor
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade
```

---

### Data (`empirica/data/`)
**Purpose:** Persistent storage and session tracking  
**Contains:**
- SQLite database (7 tables: sessions, cascades, assessments, divergence, drift, beliefs, tools)
- JSON export handlers (AI-readable format)
- Session continuity support

**Import Example:**
```python
from empirica.data import SessionDatabase, SessionJSONHandler
```

---

### Calibration (`empirica/calibration/`)
**Purpose:** Uncertainty quantification and belief tracking  
**Contains:**
- Adaptive uncertainty calibration (historical learning)
- Bayesian Guardian (evidence-based real-time calibration)
- Parallel reasoning (delegate/trustee perspectives)
- Drift monitoring (sycophancy and tension avoidance detection)

**Import Example:**
```python
from empirica.calibration.adaptive_uncertainty_calibration import AdaptiveUncertaintyCalibration
from empirica.calibration.bayesian_belief_tracker import BayesianBeliefTracker
```

---

### Investigation (`empirica/investigation/`)
**Purpose:** Strategic investigation and tool management  
**Contains:**
- Domain-aware investigation strategies (5 patterns)
- Universal plugin system (zero core code modification)
- Advanced investigation tools

**Import Example:**
```python
from empirica.investigation import recommend_investigation_tools
from empirica.investigation.investigation_plugin import InvestigationPlugin
```

---

### Integration (`empirica/integration/`)
**Purpose:** External interfaces and integrations  
**Contains:**
- MCP server for Claude Desktop
- Tmux dashboard action hooks
- Future: Additional integrations

**Import Example:**
```python
from empirica.integration.mcp_local import empirica_mcp_server
```

---

### Bootstraps (`empirica/bootstraps/`)
**Purpose:** System initialization (init-style levels 0-4)  
**Contains:**
- Optimal bootstrap (Tier 0+1: 14 components, minimal)
- Extended bootstrap (Tier 0-4: 40+ components, complete)

**Usage:**
```python
from empirica.bootstraps import ExtendedMetacognitiveBootstrap
bootstrap = ExtendedMetacognitiveBootstrap(level="2")
```

---

### Config (`empirica/config/`)
**Purpose:** Centralized configuration management
**Contains:**
- Credentials loader (singleton pattern)
- Environment variable interpolation
- Model validation per provider
- Fallback to legacy dotfiles

**Import Example:**
```python
from empirica.config.credentials_loader import get_credentials_loader

loader = get_credentials_loader()
api_key = loader.get_api_key('qwen')
models = loader.get_available_models('qwen')
```

**Configuration File:** `.empirica/credentials.yaml` (gitignored)

---

### Plugins (`empirica/plugins/`)
**Purpose:** Pluggable extensions to Empirica core
**Contains:**
- Plugin base interface (`base_plugin.py`)
- ModalitySwitcher plugin (intelligent multi-AI routing)
  - 5 routing strategies (EPISTEMIC, COST, LATENCY, QUALITY, BALANCED)
  - Adapter registry and registration system
  - Epistemic-driven router
  - Epistemic snapshot provider (95% compression, 94% fidelity)
  - Domain vector registry (4 built-in + auto-discovery)
  - Usage monitoring and cost tracking
  - 7 AI adapters supporting 15+ models

**Import Example:**
```python
from empirica.plugins.modality_switcher import ModalitySwitcher, get_registry
from empirica.plugins.modality_switcher.adapters import QwenAdapter, MinimaxAdapter
from empirica.plugins.modality_switcher.snapshot_provider import EpistemicSnapshotProvider
```

**Available Adapters (7):**
- ✅ **Qwen** (Alibaba Cloud) - Code-specialized models
- ✅ **MiniMax** (Research API) - Chinese/English, high quality
- ✅ **Rovodev** (Claude wrapper) - Complex reasoning
- ✅ **Gemini** (Google) - Free tier, fast responses
- ✅ **Qodo** (OpenAI wrapper) - GPT-4 access
- ✅ **OpenRouter** (Multi-provider) - Aggregator
- ✅ **Copilot** (GitHub) - $10/month premium models
- Local (stub for future local models)

**Total Models:** 15+ models across 7 adapters

**Plugin Architecture Benefits:**
- Zero modification to core Empirica code
- Easy to add new plugins (Cognitive Vault, AUGIE, etc.)
- Independent versioning and deployment
- Clear separation of concerns
- Centralized credentials management

**Epistemic Snapshots:**
- Universal context compression (10,000 → 500 tokens)
- Cross-AI transfer protocol
- Automatic reliability tracking (~3% degradation per hop)
- Quality metrics: compression, fidelity, information loss

**Domain Vectors:**
- 4 built-in domains (code, medical, legal, financial)
- Auto-discovery of custom domains
- Domain-specific epistemic dimensions
- Weighted confidence calculation

---

### Components (`empirica/components/`)
**Purpose:** Extended modular capabilities  
**Contains:** 11 specialized components for specific domains/use cases

**When to use:** These are optional enhancements. Core system works without them.

---

## Migration Status

### ✅ Completed:
- [x] Created new `empirica/` package structure
- [x] Moved core system files
- [x] Moved data storage files
- [x] Moved calibration files
- [x] Moved investigation files
- [x] Moved integration files
- [x] Moved bootstrap files
- [x] Moved all component directories
- [x] Created __init__.py files
- [x] Created this directory structure document

### 🔄 In Progress:
- [ ] Update all import paths
- [ ] Test all imports work
- [ ] Update documentation with new paths
- [ ] Clean up old `empirica/` directory

### ⏳ TODO:
- [ ] Update MCP server configs
- [ ] Update bootstrap import paths
- [ ] Update tests
- [ ] Create migration guide for users

---

## Import Path Changes

### Old Paths → New Paths

```python
# OLD
from empirica.canonical import CanonicalEpistemicAssessor
from empirica.metacognitive_cascade import CanonicalEpistemicCascade
from empirica.session_database import SessionDatabase

# NEW
from empirica.core.canonical import CanonicalEpistemicAssessor
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade
from empirica.data import SessionDatabase
```

---

## Next Steps

1. **Update imports** - Run find/replace on all import statements
2. **Test bootstrap** - Verify `ExtendedMetacognitiveBootstrap` works with new structure
3. **Test cascade** - Run full cascade with new imports
4. **Update docs** - Change all documentation to reference new structure
5. **Remove old dir** - Delete `empirica/` once verified

---

**Status:** Directory structure reorganized ✅  
**Ready for:** Import path updates

