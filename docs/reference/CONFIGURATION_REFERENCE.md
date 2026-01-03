# Empirica Configuration Reference (v4.0)

**Generated:** 2025-12-16  
**Status:** Complete configuration guide

---

## Overview

Empirica uses a multi-layer configuration system:

1. **System Config** (`.empirica/config.yaml`) - Runtime paths and settings
2. **Project Config** (`.empirica/project.yaml`) - Project structure and subjects
3. **Module Configs** (`empirica/config/*.yaml`) - Feature-specific settings
4. **Module Loaders** (`empirica/config/*.py`) - Configuration loaders

**Total:** 3106 lines of configuration code/data

---

## Table of Contents

1. [System Configuration](#system-configuration)
2. [Project Configuration](#project-configuration)
3. [Module Configurations](#module-configurations)
4. [Configuration Loaders](#configuration-loaders)
5. [Environment Variables](#environment-variables)
6. [Configuration Loading Order](#configuration-loading-order)

---

## System Configuration

**File:** `.empirica/config.yaml`

Core runtime configuration for Empirica.

### Structure

```yaml
version: '2.0'
root: /path/to/.empirica
paths:
  sessions: sessions/sessions.db
  identity: identity/
  messages: messages/
  metrics: metrics/
  personas: personas/
settings:
  auto_checkpoint: true
  git_integration: true
  log_level: info
env_overrides:
  - EMPIRICA_DATA_DIR
  - EMPIRICA_SESSION_DB
```

### Fields

**`version`:** Config schema version (currently `2.0`)

**`root`:** Absolute path to `.empirica` directory

**`paths`:** Relative paths from root for different data types
- `sessions`: SQLite database path
- `identity`: Ed25519 keypairs directory
- `messages`: Agent mail directory
- `metrics`: Performance metrics
- `personas`: AI persona definitions

**`settings`:**
- `auto_checkpoint`: Auto-create git checkpoints (default: `true`)
- `git_integration`: Enable git notes storage (default: `true`)
- `log_level`: Logging level (`debug`, `info`, `warning`, `error`)

**`env_overrides`:** Environment variables that can override config

### Environment Variables

- `EMPIRICA_DATA_DIR`: Override `.empirica` directory location
- `EMPIRICA_SESSION_DB`: Override session database path

---

## Project Configuration

**File:** `.empirica/project.yaml`

Defines project structure, subjects/workstreams, and discovery settings.

### Purpose

- **Subject mapping** - Map code directories to logical subjects
- **Context filtering** - Scope `project-bootstrap` by subject
- **Auto-detection** - Detect current subject from working directory

### Structure

```yaml
project_id: empirica
name: "Empirica Epistemic Framework"
description: "Metacognitive framework for AI agents"

subjects:
  core:
    name: "Core Framework"
    description: "Core epistemic assessment and CASCADE workflow"
    paths:
      - empirica/core/
      - empirica/data/
  
  cli:
    name: "CLI Tools"
    description: "Command-line interface and MCP integration"
    paths:
      - empirica/cli/
      - empirica-mcp/
  
  # ... more subjects ...

default_subject: null  # null = show all subjects
auto_detect:
  enabled: true
  method: "path_match"
```

### Subject Configuration

Each subject defines:

**`name`:** Human-readable subject name

**`description`:** What this subject covers

**`paths`:** Directory paths included in this subject (relative to project root)

### Auto-Detection

When `auto_detect.enabled: true`:
- Empirica detects current subject from working directory
- Matches `cwd` against subject paths
- Scopes `project-bootstrap` to relevant subject only

**Method:** `path_match` - Match current directory to subject paths

**Default subject:** `null` (show all subjects if no match)

### Example: Creating Project Config

```bash
# Copy example
cp .empirica/project.yaml.example .empirica/project.yaml

# Edit subjects to match your project structure
vim .empirica/project.yaml

# Test auto-detection
empirica project-bootstrap --project-id myproject --output json
```

---

## Module Configurations

**Location:** `empirica/config/*.yaml`

Feature-specific configuration files.

### 1. Modality Config (`modality_config.yaml`)

**Purpose:** Configure adapter routing for ModalitySwitcher

**Size:** 118 lines

**Sections:**

#### Adapter Configuration
```yaml
adapters:
  minimax:
    enabled: true
    type: api
    provider: minimax
    model: MiniMax-M2
    base_url: https://api.minimax.io/anthropic
    cost_per_1k_tokens: 0.01
    estimated_latency_sec: 3.0
    quality_score: 0.9
    requires_api_key: true
    api_key_env: MINIMAX_API_KEY
    timeout_sec: 60
    max_retries: 2
    capabilities:
      - text
      - tool_calls
      - streaming
```

**Fields:**
- `enabled`: Enable/disable adapter
- `type`: `api`, `cli`, or `local`
- `cost_per_1k_tokens`: Cost estimation
- `estimated_latency_sec`: Expected response time
- `quality_score`: Quality rating (0.0-1.0)
- `capabilities`: Supported features

#### Routing Configuration
```yaml
routing:
  default_strategy: epistemic  # or 'cost', 'latency', 'quality', 'balanced'
  
  epistemic:
    high_uncertainty_threshold: 0.7
    low_know_threshold: 0.4
    high_confidence_threshold: 0.8
  
  cost:
    default_max_cost_usd: 1.0
    cost_sensitive_threshold: 0.5
  
  fallback:
    enabled: true
    max_attempts: 3
    backoff_multiplier: 2.0
```

**Strategies:**
- `epistemic`: Route based on epistemic state (uncertainty, knowledge)
- `cost`: Route based on cost constraints
- `latency`: Route based on latency requirements
- `quality`: Route based on quality score
- `balanced`: Weighted combination of all factors

#### Monitoring
```yaml
monitoring:
  enabled: true
  track_usage: true
  track_costs: true
  track_latency: true
  export_format: json
  export_path: ~/.empirica/usage_stats.json
```

#### MCP Integration
```yaml
mcp:
  enabled: true
  health_check_interval_sec: 300
  include_health_in_list: true
```

**Environment Override:**
```bash
EMPIRICA_MODALITY_STRATEGY=cost empirica ...
MINIMAX_API_KEY=xxx empirica ...
```

---

### 2. Investigation Profiles (`investigation_profiles.yaml`)

**Purpose:** Define investigation constraints for different AI types and contexts

**Size:** 445 lines

**Philosophy:**
- Universal constraints = governance/security (Sentinel enforcement)
- Profile constraints = context-appropriate guidance
- Plugins = suggestive, not prescriptive

#### Universal Constraints

Applied to ALL profiles:

```yaml
universal_constraints:
  engagement_gate: 0.60       # Below this, AI is disengaged
  coherence_min: 0.50         # Below this, responses incoherent
  density_max: 0.90           # Above this, task overwhelming
  change_min: 0.50            # Below this, task unclear
  max_tool_calls_per_round: 10
  investigation_timeout_seconds: 3600
  log_all_assessments: true
  log_tool_calls: true
```

#### Profiles

**High Reasoning Collaborative:**
```yaml
high_reasoning_collaborative:
  description: "For advanced reasoning models (Claude, GPT-4, o1)"
  
  investigation:
    max_rounds: null                      # No limit
    confidence_threshold: "dynamic"       # AI decides
    confidence_threshold_fallback: 0.60
    tool_suggestion_mode: "light"         # Suggest, don't prescribe
    allow_novel_approaches: true
  
  action_thresholds:
    uncertainty_high: 0.75
    clarity_low: 0.40
    foundation_low: 0.40
    confidence_proceed_min: 0.60
```

**Standard Reasoning:**
```yaml
standard_reasoning:
  description: "For good reasoning models with some constraints"
  
  investigation:
    max_rounds: 5
    confidence_threshold: 0.70
    tool_suggestion_mode: "moderate"
    allow_novel_approaches: true
```

**Basic Instruction Following:**
```yaml
basic_instruction_following:
  description: "For simple models, needs guidance"
  
  investigation:
    max_rounds: 3
    confidence_threshold: 0.80
    tool_suggestion_mode: "prescriptive"
    allow_novel_approaches: false
```

**Domain-Specific Profiles:**
- `security_critical`: High standards, strict constraints
- `exploratory_research`: Maximum freedom, minimal constraints
- `production_deployment`: Balanced constraints, audit focus

#### Profile Selection

**Automatic:**
```python
# Based on AI registry
profile = profile_loader.select_profile(ai_id="claude-opus")
```

**Explicit:**
```bash
empirica preflight --profile high_reasoning_collaborative ...
```

**Environment:**
```bash
EMPIRICA_INVESTIGATION_PROFILE=security_critical empirica ...
```

---

## Configuration Loaders

**Location:** `empirica/config/*.py`

Python modules that load and validate configuration.

### 1. Path Resolver (`path_resolver.py`)

**Size:** 290 lines

**Purpose:** Resolve configuration file paths and create default configs

**Key Functions:**
```python
from empirica.config import path_resolver

# Get config directory
config_dir = path_resolver.get_config_dir()  # ~/.empirica

# Get specific config file
config_path = path_resolver.get_config_path("config.yaml")

# Get project config
project_config = path_resolver.get_project_config_path(project_id="myproject")

# Ensure config exists (creates if missing)
path_resolver.ensure_config_exists()
```

**Creates defaults:**
- `~/.empirica/config.yaml`
- `~/.empirica/sessions/`
- `~/.empirica/identity/`

---

### 2. Project Config Loader (`project_config_loader.py`)

**Size:** 121 lines

**Purpose:** Load and parse `project.yaml`

**Key Functions:**
```python
from empirica.config.project_config_loader import ProjectConfigLoader

loader = ProjectConfigLoader()

# Load project config
config = loader.load_project_config(project_id="empirica")

# Get subject by name
subject = loader.get_subject("core")

# Auto-detect subject from cwd
current_subject = loader.detect_current_subject()

# Get paths for subject
paths = loader.get_subject_paths("core")
```

**Returns:**
```python
{
    "project_id": "empirica",
    "name": "Empirica Epistemic Framework",
    "subjects": {
        "core": {
            "name": "Core Framework",
            "paths": ["empirica/core/", "empirica/data/"]
        }
    }
}
```

---

### 3. Profile Loader (`profile_loader.py`)

**Size:** 405 lines

**Purpose:** Load and apply investigation profiles

**Key Functions:**
```python
from empirica.config.profile_loader import ProfileLoader

loader = ProfileLoader()

# Load all profiles
profiles = loader.load_profiles()

# Get specific profile
profile = loader.get_profile("high_reasoning_collaborative")

# Select profile for AI
profile = loader.select_profile_for_ai(ai_id="claude-opus")

# Get universal constraints
universal = loader.get_universal_constraints()

# Check if action allowed
allowed = loader.is_action_allowed(
    profile=profile,
    action="INVESTIGATE",
    epistemic_state={"uncertainty": 0.8}
)
```

---

### 4. Threshold Loader (`threshold_loader.py`)

**Size:** 426 lines

**Purpose:** Load epistemic thresholds and apply profile constraints

**Key Functions:**
```python
from empirica.config.threshold_loader import ThresholdLoader

loader = ThresholdLoader()

# Get thresholds for profile
thresholds = loader.get_thresholds(profile="high_reasoning_collaborative")

# Check if investigation needed
needs_investigation = loader.check_investigation_needed(
    epistemic_state={"uncertainty": 0.75, "know": 0.5}
)

# Get action recommendation
action = loader.recommend_action(epistemic_state)
```

---

### 5. Modality Config Loader (`modality_config_loader.py`)

**Size:** (Implied by modality_config.yaml usage)

**Purpose:** Load modality switching configuration

---

### 6. Credentials Loader (`credentials_loader.py`)

**Size:** 325 lines

**Purpose:** Load API credentials securely

**Key Functions:**
```python
from empirica.config.credentials_loader import CredentialsLoader

loader = CredentialsLoader()

# Get API key from env
api_key = loader.get_credential("MINIMAX_API_KEY")

# Check if credential exists
has_key = loader.has_credential("MINIMAX_API_KEY")
```

---

### 7. Goal Scope Loader (`goal_scope_loader.py`)

**Size:** 387 lines

**Purpose:** Load and apply goal scope constraints

---

### 8. Memory Gap Policy Loader (`memory_gap_policy_loader.py`)

**Size:** 335 lines

**Purpose:** Load policies for handling memory gaps

---

## Configuration Loading Order

**Startup sequence:**

1. **Path Resolution** (`path_resolver.py`)
   - Find `.empirica` directory
   - Create if missing
   - Load `config.yaml`

2. **System Config** (`config.yaml`)
   - Load runtime settings
   - Apply environment overrides

3. **Project Config** (`project.yaml`)
   - Load if project context detected
   - Auto-detect current subject

4. **Module Configs** (`.yaml` files)
   - Load on-demand when feature used
   - Cache in memory

5. **Environment Variables**
   - Override any config value
   - Highest priority

---

## Environment Variables

**Override priority:** ENV > config.yaml > defaults

### System

- `EMPIRICA_DATA_DIR`: Override `.empirica` location
- `EMPIRICA_SESSION_DB`: Override session database
- `EMPIRICA_LOG_LEVEL`: Override log level (`debug`, `info`, `warning`, `error`)
- `EMPIRICA_WORKSPACE_ROOT`: Set workspace root for multi-project work
- `PYTHONWARNINGS`: Control Python warning display (`ignore`, `default`, `error`)

### Profiles

- `EMPIRICA_INVESTIGATION_PROFILE`: Force investigation profile
- `EMPIRICA_PROFILE_MODE`: Override profile mode
- `EMPIRICA_PERSONALITY`: Set AI personality/persona (`researcher`, `implementer`, `reviewer`, etc.)
- `EMPIRICA_EPISTEMIC_MODE`: Set epistemic mode (`strict`, `balanced`, `exploratory`)

### Modality

- `EMPIRICA_MODALITY_STRATEGY`: Override routing strategy
- `MINIMAX_API_KEY`: MiniMax API key
- `EMPIRICA_DEFAULT_ADAPTER`: Override default adapter

### Sentinel (Safety Gates)

- `SENTINEL_URL`: URL for external Sentinel service (optional)
- `EMPIRICA_ENFORCE_CASCADE_PHASES`: Strictly enforce CASCADE phase ordering (`true`, `false`)

### Vector Search & Embeddings

- `EMPIRICA_ENABLE_EMBEDDINGS`: Enable/disable embedding generation (`true`, `false`)
- `EMPIRICA_OLLAMA_URL`: URL for local Ollama instance (for local embeddings)
- `OPENAI_API_KEY`: API key for OpenAI embeddings

### Credentials

- `EMPIRICA_CREDENTIALS_PATH`: Path to credentials file

### Features

- `EMPIRICA_AUTO_CHECKPOINT`: Enable/disable auto checkpoints (`true`, `false`)
- `EMPIRICA_GIT_INTEGRATION`: Enable/disable git integration
- `EMPIRICA_MODALITY_ENABLED`: Enable/disable modality switching

---

## Usage Examples

### Load System Config

```python
from empirica.config.path_resolver import get_config

config = get_config()
print(config['settings']['auto_checkpoint'])
```

### Load Project Config

```python
from empirica.config.project_config_loader import ProjectConfigLoader

loader = ProjectConfigLoader()
config = loader.load_project_config("empirica")

# Get paths for core subject
core_paths = config['subjects']['core']['paths']
```

### Select Investigation Profile

```python
from empirica.config.profile_loader import ProfileLoader

loader = ProfileLoader()

# Auto-select for AI
profile = loader.select_profile_for_ai("claude-opus")

# Or load specific profile
profile = loader.get_profile("security_critical")
```

### Check Thresholds

```python
from empirica.config.threshold_loader import ThresholdLoader

loader = ThresholdLoader()
thresholds = loader.get_thresholds("high_reasoning_collaborative")

# Check if should investigate
if epistemic_state['uncertainty'] > thresholds['uncertainty_high']:
    action = "INVESTIGATE"
```

---

## Configuration Files Summary

| File | Size | Purpose |
|------|------|---------|
| `.empirica/config.yaml` | ~20 lines | System runtime config |
| `.empirica/project.yaml` | ~60 lines | Project structure |
| `modality_config.yaml` | 118 lines | Adapter routing |
| `investigation_profiles.yaml` | 445 lines | Investigation constraints |
| `ai_registry.json` | 221 lines | AI capability registry |
| **Python Loaders** | 2322 lines | Configuration loading |
| **TOTAL** | **3186 lines** | Complete config system |

---

## Best Practices

### 1. Don't Edit Python Loaders

Loaders are part of Empirica core. Edit YAML/JSON configs instead.

### 2. Use Environment Variables for Secrets

```bash
# Good
export MINIMAX_API_KEY=xxx
empirica session-create --ai-id myai

# Bad (don't commit secrets!)
# vim empirica/config/modality_config.yaml
# api_key: xxx  # NO!
```

### 3. Create Project Config for Multi-Repo Work

```bash
cp .empirica/project.yaml.example .empirica/project.yaml
# Edit subjects to match your project
```

### 4. Override Temporarily with ENV

```bash
# Override for single command
EMPIRICA_INVESTIGATION_PROFILE=security_critical empirica preflight ...

# Override for session
export EMPIRICA_LOG_LEVEL=debug
empirica session-create --ai-id myai
```

---

## Troubleshooting

### Config Not Loading

```bash
# Check config location
empirica config --show-path

# Validate config
empirica config --validate

# Reset to defaults
empirica config --reset
```

### Profile Not Found

```python
# List available profiles
from empirica.config.profile_loader import ProfileLoader
loader = ProfileLoader()
print(loader.list_profiles())
```

### Environment Override Not Working

```bash
# Check override precedence
empirica config --show-effective

# Debug config loading
EMPIRICA_LOG_LEVEL=debug empirica session-create --ai-id test
```

---

## See Also

- [CLI Commands Reference](CLI_COMMANDS_GENERATED.md)
- [Python API Reference](PYTHON_API_GENERATED.md)
- [MCP Server Documentation](MCP_SERVER_GENERATED.md)

---

**Last Updated:** 2025-12-16  
**Configuration System Version:** v4.0  
**Total Lines Documented:** 3186 lines

---

## 9. MCO (Metacognitive Configuration Objects)

**Location:** `empirica/config/mco/`  
**Total Size:** ~3600 lines of YAML configuration  
**Purpose:** Define AI behavior patterns, CASCADE styles, epistemic thresholds, and protocols

### MCO Configuration Files

| File | Lines | Purpose |
|------|-------|---------|
| `protocols.yaml` | 635 | MCP tool usage schemas (CASCADE, goals, handoffs, mistakes) |
| `feedback_loops.yaml` | 493 | Statusline warning responses for drift detection |
| `cascade_styles.yaml` | 422 | 6 CASCADE workflow profiles (default, exploratory, rigorous, rapid, expert, novice) |
| `epistemic_conduct.yaml` | 355 | Bidirectional accountability (AI↔human challenge triggers) |
| `MCO_INDEX.yaml` | 326 | Semantic guide to all MCO objects and relationships |
| `model_profiles.yaml` | 313 | Model-specific bias corrections (per LLM overconfidence patterns) |
| `personas.yaml` | 277 | 6 AI personas (researcher, implementer, reviewer, coordinator, learner, expert) |
| `goal_scopes.yaml` | 254 | Map epistemic vectors → scope vectors (breadth, duration, coordination) |
| `bootstrap_triggers.yaml` | 205 | When to load project breadcrumbs, depth based on uncertainty |
| `confidence_weights.yaml` | 170 | Weight configurations for aggregating 13 epistemic vectors |
| `ask_before_investigate.yaml` | 165 | Thresholds for when AI should ask human vs investigate autonomously |

**Total:** 3,615 lines

### MCO Categories

**1. AI Behavior & Identity**
- `personas.yaml` - Role-based reasoning and specialization
- `cascade_styles.yaml` - Workflow profiles for different task types
- `epistemic_conduct.yaml` - Accountability and transparency rules
- `ask_before_investigate.yaml` - Uncertainty thresholds for asking vs investigating

**2. Epistemic Assessment & Calibration**
- `confidence_weights.yaml` - Vector aggregation for confidence scores
- `model_profiles.yaml` - LLM-specific bias corrections
- `feedback_loops.yaml` - Drift detection and warning responses

**3. Goal Scoping & Work Planning**
- `goal_scopes.yaml` - Epistemic → scope vector mapping
- Includes protocols: `session_continuation`, `web_project_design`

**4. Tool Usage & Protocols**
- `protocols.yaml` - Standardized MCP tool parameter schemas
- Schemas for: `log_mistake`, `preflight_schema`, `check_schema`, `postflight_schema`

**5. Bootstrap & Context Loading**
- `bootstrap_triggers.yaml` - Uncertainty-driven context depth
- Token costs: session_start (~800), check_requery (~50)

**6. Documentation & Reference**
- `MCO_INDEX.yaml` - Master index with relationships and workflows

### MCO Integration with CASCADE

**Session Start:**
```
1. Create session
   MCO used: []
   
2. Load bootstrap (if project exists)
   MCO used: bootstrap_triggers.yaml
   
3. Run PREFLIGHT
   MCO used: personas.yaml, cascade_styles.yaml, confidence_weights.yaml
   
4. Apply bias correction
   MCO used: model_profiles.yaml
```

**CHECK Gate:**
```
1. Assess readiness
   MCO used: ask_before_investigate.yaml, epistemic_conduct.yaml
   Rule: If uncertainty ≥0.65 + context ≥0.50 → ask human first
   
2. Query unknowns (don't reload full bootstrap)
   
3. Submit CHECK
   MCO used: cascade_styles.yaml, protocols.yaml
```

**Goal Creation:**
```
1. Map epistemic → scope
   MCO used: goal_scopes.yaml
   
2. Check protocols
   MCO used: goal_scopes.yaml (session_continuation, web_project_design)
   
3. Create goal
   MCO used: protocols.yaml
```

**Drift Detection:**
```
1. Monitor statusline
   MCO used: feedback_loops.yaml
   
2. Trigger response
   MCO used: feedback_loops.yaml, epistemic_conduct.yaml
   Responses: OVERCONFIDENT → recalibrate, DRIFTING → investigate
```

### Key MCO Concepts

**Personas (6 types):**
- Researcher, Implementer, Reviewer, Coordinator, Learner, Expert
- Influence CASCADE style selection

**CASCADE Styles (6 profiles):**
- Default, Exploratory, Rigorous, Rapid, Expert, Novice
- Different assessment depths and gate thresholds

**Bidirectional Accountability:**
- When AI challenges user (epistemic rigor enforcement)
- When human challenges AI (calibration feedback)

**Uncertainty-Driven Bootstrap:**
- High uncertainty (>0.7): Deep context (~4500 tokens)
- Medium uncertainty (0.5-0.7): Moderate context (~2700 tokens)
- Low uncertainty (<0.5): Minimal context (~1800 tokens)

**Model-Specific Bias Correction:**
- Calibration adjustments per LLM
- Corrects for overconfidence/underconfidence patterns

### Token Costs

| Component | Cost |
|-----------|------|
| Bootstrap (session_start) | ~800 tokens |
| Bootstrap (live mode) | ~2000 tokens |
| CHECK requery | ~50 tokens |
| Full MCO load | ~1500 tokens |
| Targeted MCO load | ~200-400 tokens |

### Example: Ask vs Investigate Threshold

From `ask_before_investigate.yaml`:
```yaml
uncertainty: ≥0.65
context: ≥0.50
→ Ask human first before deep investigation
```

### Example: Goal Scope Mapping

From `goal_scopes.yaml`:
```
Epistemic vectors → Scope vectors:
- KNOW/DO/UNCERTAINTY → breadth (0.0=function, 1.0=codebase)
- Task complexity → duration (0.0=hours, 1.0=months)
- Multi-agent needs → coordination (0.0=solo, 1.0=heavy)
```

### MCO Relationships

```
personas.yaml → cascade_styles.yaml (informs)
cascade_styles.yaml → confidence_weights.yaml (uses)
epistemic_conduct.yaml → ask_before_investigate.yaml (enforces)
bootstrap_triggers.yaml ↔ goal_scopes.yaml (integrates)
model_profiles.yaml → feedback_loops.yaml (corrects)
protocols.yaml ↔ goal_scopes.yaml (validates)
feedback_loops.yaml → epistemic_conduct.yaml (triggers)
```

### MCO Index

The master index (`MCO_INDEX.yaml`) provides:
- Semantic categorization of all configs
- Workflow integration maps
- Query patterns (by concept, use case, question)
- Relationship matrix
- Token cost estimates
- Maintenance procedures

**Query by Concept:**
- "bias-correction" → model_profiles.yaml, confidence_weights.yaml, feedback_loops.yaml
- "gate-thresholds" → cascade_styles.yaml, ask_before_investigate.yaml, goal_scopes.yaml
- "uncertainty-thresholds" → ask_before_investigate.yaml, bootstrap_triggers.yaml, cascade_styles.yaml

**Query by Use Case:**
- "Starting new session" → bootstrap_triggers.yaml, personas.yaml, cascade_styles.yaml
- "CHECK gate decision" → ask_before_investigate.yaml, cascade_styles.yaml, epistemic_conduct.yaml
- "Detecting overconfidence" → model_profiles.yaml, feedback_loops.yaml, epistemic_conduct.yaml

---

## Summary Statistics (Updated)

**Total Configuration Coverage:**

| Layer | Files | Lines | Purpose |
|-------|-------|-------|---------|
| System Config | 1 | ~200 | `.empirica/config.yaml` |
| Project Config | 1 | ~300 | `.empirica/project.yaml` |
| Module Configs | 2 | ~500 | `modality_config.yaml`, `investigation_profiles.yaml` |
| MCO Configs | 11 | 3615 | Metacognitive behavior, CASCADE styles, protocols |
| Config Loaders | 8 | 2186 | Python modules for loading configs |

**Grand Total:** ~6800 lines of configuration across all layers

**Complete Coverage:**
- ✅ System configuration (global settings)
- ✅ Project configuration (per-project settings)
- ✅ Module configuration (modality profiles, investigation strategies)
- ✅ MCO configuration (AI behavior, CASCADE styles, protocols)
- ✅ Python loaders (8 modules documented)
- ✅ Environment variables (precedence and usage)
- ✅ Loading order and precedence rules

