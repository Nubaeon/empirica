# Empirica - Quick Reference Card

**Status:** ✅ Production Ready
**Version:** 1.0.0
**Last Updated:** 2025-11-05
**Focus:** Single-AI Epistemic Tracking (Worker AI)

---

## What Is This?

Empirica is a **production-ready epistemic tracking system** for AI workers. It enables AI agents to measure and validate their epistemic state without interfering with their internal reasoning.

**Core Principle:** "Measure and validate without interfering"

**Architecture Note:** Empirica focuses on **worker AI epistemic tracking** only. For multi-AI orchestration, see **Cognitive Vault** (governance layer).

**Primary Use:** Single AI with genuine epistemic self-awareness (Tier 1 default: KNOW/DO/CONTEXT tracking)

---

## Quick Start

### 1. Bootstrap the System

```bash
# Minimal bootstrap (core only)
python3 -m empirica.cli bootstrap --level 0

# Standard bootstrap (recommended)
python3 -m empirica.cli bootstrap --level 1

# Extended bootstrap (full system)
python3 -m empirica.cli bootstrap-system --level 3
```

Bootstrap levels:
- `0` / `minimal` - Core metacognition (~0.03s)
- `1` / `standard` - + Cascade workflow (~0.04s) ⭐ DEFAULT
- `2` / `extended` - + Calibration (~0.12s)
- `3` - + Advanced components (~0.15s)
- `4` / `complete` - Everything (~0.20s)

### 2. Run a Cascade (CLI)

```bash
# Basic cascade
python3 -m empirica.cli cascade "Should I refactor this code?"

# With modality switching (route to best AI)
python3 -m empirica.cli cascade "Analyze this codebase" --strategy epistemic

# Force specific adapter
python3 -m empirica.cli cascade "What is 2+2?" --adapter qwen

# With epistemic context levels
python3 -m empirica.cli cascade "Continue investigation" --context-level standard
```

### 3. Run a Cascade (Python)

```python
from empirica.bootstraps.optimal_metacognitive_bootstrap import OptimalMetacognitiveBootstrap

# Bootstrap
bootstrap = OptimalMetacognitiveBootstrap(level='1')
components = bootstrap.bootstrap()

# Run cascade (if loaded)
cascade = components.get('canonical_cascade')
result = await cascade.run_epistemic_cascade(
    task="Refactor the authentication module",
    context={'cwd': '/path/to/project'}
)

print(f"Action: {result['action']}")
print(f"Confidence: {result['confidence']}")
```

### 4. Run via MCP (Claude Desktop)
```json
{
  "tool": "cascade_run_full",
  "arguments": {
    "question": "Your question here",
    "enable_dashboard": true,
    "enable_bayesian": true
  }
}
```

### 5. Use Modality Switcher (Optional Experimental Addon)

**⚠️ Architecture Note:** Modality switcher is **disabled by default**. For production multi-AI orchestration, use **Cognitive Vault** (governance layer). Worker AIs should focus on epistemic tracking, not routing decisions.

**Enable (if desired):**
```bash
export EMPIRICA_ENABLE_MODALITY_SWITCHER=true
```

**Usage:**
```bash
# Use specific adapter
python3 -m empirica.cli decision "Analyze code" --adapter qwen

# Use specific model
python3 -m empirica.cli decision "Generate tests" --adapter qwen --model qwen-coder-turbo

# List available models
python3 -m empirica.cli decision --adapter qwen --list-models

# All available adapters: qwen, minimax, rovodev, gemini, qodo, openrouter, copilot
```

### 6. Epistemic Snapshot Transfer (Cross-AI Context)

```python
from empirica.plugins.modality_switcher.snapshot_provider import EpistemicSnapshotProvider

provider = EpistemicSnapshotProvider()

# Create snapshot
snapshot = provider.create_snapshot_from_session(
    session_id="session_id",
    context_summary_text="Context summary",
    semantic_tags={"domain": "security"},
    cascade_phase="investigate"
)

# Transfer to different AI
# Snapshot reliability degrades ~3% per hop, auto-tracked
```

### Run Tests
```bash
cd semantic_self_aware_kit
python3 test_canonical_cascade.py
```

---

## System Components

### Core (Always Active)
1. **Canonical Assessment** - LLM-powered 12-vector self-assessment
2. **Reflex Frame Logger** - Temporal separation (prevents recursion)
3. **Metacognitive Cascade** - THINK → UNCERTAINTY → INVESTIGATE → CHECK → ACT

### Optional Features
4. **Investigation System** - Strategic guidance (domain-aware)
5. **Plugin System** - Custom tool integration
6. **Bayesian Guardian** - Evidence-based calibration (selective activation)
7. **Drift Monitor** - Behavioral integrity (sycophancy/tension detection)
8. **Action Hooks** - Real-time dashboard updates

### Modality Switcher (Optional Experimental Addon - Disabled by Default)
9. **Epistemic Snapshots** - Cross-AI context transfer (95% compression, 94% fidelity)
10. **Multi-Adapter System** - 7 adapters, 15+ models
11. **Domain Vectors** - Domain-specific epistemic dimensions
12. **Credentials Manager** - Centralized API key management

**Note:** Modality switcher is experimental. For production multi-AI orchestration, use **Cognitive Vault** (governance layer).

---

## Modality Switcher - Multi-AI Routing (Optional Experimental Addon)

**Status:** Disabled by default | **Recommendation:** Use Cognitive Vault for production multi-AI orchestration

**Enable:** `export EMPIRICA_ENABLE_MODALITY_SWITCHER=true`

**See:** `docs/EMPIRICA_SINGLE_AI_FOCUS.md` for architecture details

### Available Adapters (7)

| Adapter | Models | Auth Method | Use Case |
|---------|--------|-------------|----------|
| **qwen** | qwen-coder-plus, qwen-coder-turbo, qwen-max, qwen-plus | API key | Code generation, analysis |
| **minimax** | abab6.5s-chat, abab6.5-chat, abab5.5-chat | API key + group_id | Chinese/English, research |
| **rovodev** | claude-3-5-sonnet, claude-3-opus | API key | Complex reasoning |
| **gemini** | gemini-2.0-flash-exp, gemini-1.5-pro | Query param | Free tier, fast |
| **qodo** | gpt-4, gpt-3.5-turbo | API key | OpenAI access |
| **openrouter** | anthropic/claude-3.5-sonnet, openai/gpt-4-turbo | API key | Multi-provider |
| **copilot** | claude-sonnet-4, gpt-5, grok-fast-1 | CLI | $10/month premium |

### Credentials Setup

**Location:** `.empirica/credentials.yaml`

```yaml
version: "1.0"
providers:
  qwen:
    api_key: "${QWEN_API_KEY}"  # Or paste directly
    base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
    default_model: "qwen-coder-plus"
    available_models: ["qwen-coder-plus", "qwen-coder-turbo"]
    headers:
      Authorization: "Bearer ${api_key}"

  minimax:
    api_key: "${MINIMAX_API_KEY}"
    group_id: "${MINIMAX_GROUP_ID}"
    # ... see template for complete config
```

**Setup:**
```bash
# Copy template
cp .empirica/credentials.yaml.template .empirica/credentials.yaml

# Edit with your keys
nano .empirica/credentials.yaml

# Or migrate from dotfiles
python3 scripts/migrate_credentials.py
```

### Epistemic Snapshot Protocol

**What:** Universal context compression for cross-AI transfer
**Compression:** 10,000 tokens → 500 tokens (95%)
**Fidelity:** 94% information retention
**Degradation:** ~3% reliability loss per hop
**Refresh:** Auto-recommended when reliability < 75%

**Metrics Tracked:**
- Transfer count (number of hops)
- Reliability (90% initial, degrades ~3% per hop)
- Compression ratio
- Fidelity score
- Information loss estimate

---

## Key Files

### Must Read
- `docs/EMPIRICA_SINGLE_AI_FOCUS.md` - **⭐ Main product documentation** (single-AI focus)
- `docs/HOW_TO_RESUME_SESSION.md` - Session resumption guide for AIs
- `docs/production/01_QUICK_START.md` - Getting started guide
- `docs/production/SYSTEM_ARCHITECTURE_DEEP_DIVE.md` - Complete technical overview

### Architecture
- `docs/ARCHITECTURE_UPDATE_2025-11-05.md` - Separation of concerns architecture
- `docs/EMPIRICA_UNWIRING_COMPLETE.md` - Modality switcher made optional

### Core Implementation
- `semantic_self_aware_kit/canonical/` - Data structures
- `semantic_self_aware_kit/metacognitive_cascade/metacognitive_cascade.py` - Main cascade (1,655 lines)
- `semantic_self_aware_kit/parallel_reasoning.py` - Drift monitoring

### Integration
- `semantic_self_aware_kit/mcp_local/empirica_mcp_server.py` - MCP server
- `semantic_self_aware_kit/test_canonical_cascade.py` - Test suite

---

## 12 Epistemic Vectors

### GATE: ENGAGEMENT (≥0.60 required)
Collaborative intelligence quality

### TIER 0: FOUNDATION (35% weight)
- **KNOW** - Domain knowledge
- **DO** - Capability
- **CONTEXT** - Environmental validity

### TIER 1: COMPREHENSION (25% weight)
- **CLARITY** - Task clarity
- **COHERENCE** - Logical consistency
- **SIGNAL** - Priority identification
- **DENSITY** - Information load (inverted)

### TIER 2: EXECUTION (25% weight)
- **STATE** - Environment mapping
- **CHANGE** - Modification tracking
- **COMPLETION** - Goal proximity
- **IMPACT** - Consequence understanding

---

## Cascade Flow

```
THINK
  ↓ Generate meta-prompt, classify domain
UNCERTAINTY
  ↓ 12-vector assessment, check ENGAGEMENT gate
INVESTIGATE (loop until confidence met)
  ↓ Strategic guidance, tool recommendations
CHECK
  ↓ Bayesian discrepancies, drift detection
ACT
  ↓ Final decision with confidence
```

---

## Configuration

### Basic
```python
cascade = CanonicalEpistemicCascade()  # Use defaults
```

### Production
```python
cascade = CanonicalEpistemicCascade(
    action_confidence_threshold=0.75,    # Higher threshold
    max_investigation_rounds=3,          # Balance quality/speed
    enable_bayesian=True,                # Evidence tracking
    enable_drift_monitor=True,           # Behavioral integrity
    enable_action_hooks=False            # No dashboard in production
)
```

### With Plugins
```python
from metacognitive_cascade.investigation_plugin import InvestigationPlugin

plugin = InvestigationPlugin(
    name='custom_tool',
    description='What it does',
    execute_fn=lambda ctx: my_function(ctx),
    improves_vectors=['know', 'context'],
    confidence_gain=0.25
)

cascade = CanonicalEpistemicCascade(
    investigation_plugins={'custom_tool': plugin}
)
```

---

## Critical Thresholds

| Threshold | Value | Action |
|-----------|-------|--------|
| ENGAGEMENT gate | ≥0.60 | Required to proceed |
| Coherence critical | <0.50 | RESET (task incoherent) |
| Density critical | >0.90 | RESET (cognitive overload) |
| Change critical | <0.50 | STOP (cannot progress) |
| Action confidence | ≥0.70 | Proceed with action (configurable) |

---

## Bayesian Guardian

### When Active
- **Precision-critical domains:** code_analysis, bug_diagnosis, security_review, architecture
- **Low clarity:** clarity < 0.5
- **Discrepancies detected:** overconfidence signals

### When Dormant
- **Creative domains:** design, writing, brainstorm, ideation
- **High clarity:** clear tasks in general domains

---

## Drift Monitoring

### Patterns Detected
1. **Sycophancy drift:** Delegate weight increasing over time (threshold: +0.15)
2. **Tension avoidance:** Acknowledging tensions less frequently (threshold: 2:1 ratio)

### Check Phase Alerts
- ⚠️ Sycophancy detected → Increase trustee weight
- ⚠️ Tension avoidance → Force tension analysis

---

## Documentation Map

### Essential (Read First)
- `docs/SESSION_HANDOFF.md` - Current status
- `docs/production/01_QUICK_START.md` - Get started
- `docs/production/SYSTEM_ARCHITECTURE_DEEP_DIVE.md` - Technical deep dive

### Features
- `docs/production/05_EPISTEMIC_VECTORS.md` - Understanding vectors
- `docs/production/08_BAYESIAN_GUARDIAN.md` - Evidence tracking
- `docs/production/09_DRIFT_MONITOR.md` - Behavioral integrity
- `docs/production/10_PLUGIN_SYSTEM.md` - Custom tools

### Integration
- `docs/production/12_MCP_INTEGRATION.md` - Claude Desktop setup
- `docs/production/22_FAQ.md` - Common questions

### Session History
- `docs/SESSION_SUMMARY_2025_10_27.md` - Latest session
- `docs/FINAL_INTEGRATION_STATUS.md` - Complete status

---

## Common Commands

### Test System
```bash
python3 semantic_self_aware_kit/test_canonical_cascade.py
```

### Start Dashboard
```bash
cd tmux_dashboard
./start_agi_dashboard.sh
```

### Run MCP Server
```bash
python3 semantic_self_aware_kit/mcp_local/empirica_mcp_server.py
```

### Query Reflex Frames
```python
from canonical import ReflexLogger

logger = ReflexLogger()
frames = logger.get_frames_by_phase('uncertainty', date='2025-10-27')
```

### Modality Switcher Commands

```bash
# List all available models for an adapter
python3 -m empirica.cli decision --adapter qwen --list-models

# Use specific adapter and model
python3 -m empirica.cli decision "Your question" --adapter qwen --model qwen-coder-turbo

# Test adapter functionality
python3 -m empirica.cli decision "Say hello in 10 words" --adapter minimax

# Check credentials loaded
python3 empirica/config/credentials_loader.py

# Migrate from dotfiles to credentials.yaml
python3 scripts/migrate_credentials.py
```

### Snapshot Management

```python
from empirica.plugins.modality_switcher.snapshot_provider import EpistemicSnapshotProvider

provider = EpistemicSnapshotProvider()

# Create snapshot
snapshot = provider.create_snapshot_from_session(
    session_id="session_123",
    context_summary_text="Summary of current context",
    semantic_tags={"domain": "security", "severity": "high"},
    cascade_phase="investigate"
)

# Save snapshot
provider.save_snapshot(snapshot)

# Load snapshot
loaded = provider.get_snapshot(snapshot.snapshot_id)

# Check metrics
print(f"Reliability: {snapshot.estimate_memory_reliability():.1%}")
print(f"Transfer count: {snapshot.transfer_count}")
print(f"Should refresh: {snapshot.should_refresh()}")
```

---

## Production Checklist

- ✅ LLM endpoint configured
- ✅ Python 3.8+ installed
- ✅ Dependencies installed (`pip install -r requirements.txt`)
- ✅ Confidence threshold tuned for domain
- ✅ Investigation rounds configured
- ✅ Bayesian activation appropriate for domain
- ✅ Monitoring/logging configured

---

## Need Help?

1. **Start here:** `docs/production/01_QUICK_START.md`
2. **Understand system:** `docs/production/SYSTEM_ARCHITECTURE_DEEP_DIVE.md`
3. **Check FAQ:** `docs/production/22_FAQ.md`
4. **Review examples:** `test_canonical_cascade.py`
5. **Session history:** `docs/SESSION_HANDOFF.md`

---

## System Statistics

- **Total Components:** 8 major systems
- **Total Code:** ~3,500+ lines
- **Documentation:** 11 production docs
- **Test Coverage:** All major features
- **Status:** ✅ Production Ready

---

**Quick Reference v1.0.0 - System Ready for Production** 🚀
