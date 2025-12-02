# 🧠 Empirica - Metacognitive Framework for AI Agents

> Genuine epistemic self-awareness with measurable calibration

[![Status](https://img.shields.io/badge/status-beta-yellow)]()
[![Version](https://img.shields.io/badge/version-1.0.0--beta-green)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

**98% token reduction** • **Multi-agent coordination** • **Production validated** • **November 2025**

## What is Empirica?

Empirica enables AI agents to assess their own knowledge, track epistemic growth, and make calibrated decisions. Not just metrics—**genuine self-awareness with measurable calibration**.

**Proven through 73 sessions** across multiple AI agents with validated results:
- 🧠 **Self-referential goal generation** - AI reasons about its own goals
- 📉 **97.5% token reduction** - Git-enhanced context loading (Phase 1.5)
- 📊 **13-vector epistemic assessment** - Comprehensive self-evaluation
- ✅ **Well-calibrated growth** - Predictions match reality

**This is empirically testable.** Epistemic growth is measurable and reproducible.

---

> ⚠️ **Schema Migration in Progress** (60% complete - Jan 2025)  
> We're migrating to `EpistemicAssessmentSchema` with improved field naming.  
> **All changes are backwards compatible** - existing code continues to work!  
> 
> **Field changes**: `know` → `foundation_know`, `clarity` → `comprehension_clarity`, etc.  
> See [NEW Schema Guide](docs/reference/NEW_SCHEMA_GUIDE.md) | [Migration Status](docs/wip/schema-migration/PROGRESS_60_PERCENT.md)

---

## ✨ Key Features

### 🧠 Self-Referential Goal Generation
AI agents can now reason about their own goals using `llm_callback`:
```python
def my_ai(prompt: str) -> str:
    return ai_client.reason(prompt)

components = bootstrap_metacognition("agent", "minimal", llm_callback=my_ai)
```
No hardcoded thresholds—genuine reasoning about context and needs.

### 📉 Git-Enhanced Context Loading (Phase 1.5)
**97.5% token reduction** through git notes integration:
- Baseline: ~1,821 tokens (full session history)
- Optimized: 46 tokens (git checkpoint)
- Validated in production with measurable results

### 📊 13-Vector Epistemic Assessment
Complete self-evaluation framework:
- **Foundation:** KNOW, DO, CONTEXT
- **Comprehension:** CLARITY, COHERENCE, SIGNAL, DENSITY
- **Execution:** STATE, CHANGE, COMPLETION, IMPACT
- **Meta:** ENGAGEMENT, UNCERTAINTY
- **Calibration:** Overall confidence tracking

### 🔄 CASCADE Workflow
**Session Structure:**
- **PRE assessment** → Session start, epistemic baseline
- **Implicit CASCADE** → think → investigate → act (natural workflow)
- **CHECK assessments** → Decision points (0-N times: "ready to proceed?")
- **POST assessment** → Session end, calibration measurement

**Benefits:**
- Measurable learning (PRE→POST deltas)
- Well-calibrated predictions
- Transparent decision trails

### 📈 Advanced Calibration Tools
- **Bayesian Beliefs Tracker** - Evidence-based belief updating with confidence intervals
- **Drift Monitor** - Detect overconfidence patterns in long-running sessions
- **Investigation Plugins** - Extensible strategies for domain-specific exploration
- **Learning Deltas** - Track epistemic growth (e.g., KNOW: 0.70→0.95, UNCERTAINTY: 0.45→0.10)

### 🗄️ Triple Storage Architecture
- **Git Notes** - Compressed checkpoints (97.5% token reduction: 46 vs 1,821 tokens)
- **SQLite Database** - Full audit trail with queryable epistemic state
- **Handoff Reports** - Semantic summaries (98% token reduction: ~400 vs 20,000 tokens)
- **JSON Exports** - Portable session data for analysis

### 🤝 Multi-Agent Coordination
- **Goal Orchestration** - Create, track, and share goals across AI agents
- **Task Decomposition** - Break goals into subtasks with epistemic importance ratings
- **Epistemic Snapshots** - Transfer full context between agents efficiently
- **Session Continuity** - Resume work across days/weeks with preserved state

### 🔗 MCP Server Integration
21 tools for epistemic tracking, goal orchestration, and session management.

## Who Uses Empirica?

**🤖 AI agents** (Claude, GPT, Gemini, etc.) - You're the primary user  
**👤 Developers** in critical domains - Healthcare, finance, research, engineering  
**🏢 Teams** requiring AI transparency - Audit trails, calibration metrics, decision logs

⚠️ **Not for casual use** - Requires genuine epistemic engagement

## Why Empirica for Complex Projects?

### 📊 Real-World Results
- **13-cascade session** (170 minutes) - All phases "good" calibration, 3 bugs found & fixed
- **Documentation overhaul** - 350+ files organized, 247MB cleaned, zero hallucinations
- **Multi-agent coordination** - RovoDev + mini-agent working on shared goals
- **Token efficiency** - 98% reduction enables practical multi-agent workflows

### 🎯 For Large Projects (100+ hours)
- **Track drift** - Detect when AI becomes overconfident over time
- **Multi-cascade continuity** - Resume work after weeks with full context
- **Shared epistemic state** - Multiple agents coordinate via queryable database
- **Audit everything** - Full history of decisions, confidence changes, learning deltas

### 🤖 For AI Agents
- **Know vs. Guess** - Explicit uncertainty prevents confident mistakes
- **Measurable growth** - See learning deltas (KNOW before/after)
- **Systematic investigation** - Replaces random exploration with structured inquiry
- **Resume efficiently** - 98% token savings on session handoffs

### 👥 For Humans
- **Trust through transparency** - See exactly what AI knows/doesn't know
- **Queryable confidence** - Check AI's uncertainty at any time
- **Calibration tracking** - Measure if AI's confidence matches reality
- **Multi-agent orchestration** - Coordinate AI teams on complex work

## 🚀 The Vision: Sentinel + Empirica OS

Empirica is evolving into a complete **epistemic operating system**:

**📖 Read the vision:**
- **[VISION_EMPIRICA_SENTINEL_SYSTEM.md](VISION_EMPIRICA_SENTINEL_SYSTEM.md)** - Complete end-state vision, business model, and 6-phase roadmap
- **[ARCHITECTURE_SENTINEL_INTEGRATION.md](ARCHITECTURE_SENTINEL_INTEGRATION.md)** - Technical architecture with component interfaces and data models
- **[SESSION_COMPLETE_VISION_CAPTURE.md](SESSION_COMPLETE_VISION_CAPTURE.md)** - How the vision emerged, feasibility analysis, Phase 0 planning

**What's Coming:**
- **Sentinel**: Small Language Model trained on epistemic deltas, chooses optimal model automatically
- **Model Switching**: Transparent routing based on epistemic state (not user choice)
- **Epistemic Distillation**: Large models generate learning signals, Sentinel learns over time
- **Cognitive Vault**: Enterprise key management, compliance, security integration
- **Bayesian Guardian**: Probabilistic safety verification, uncertainty-grounded access control

**Why It Matters:**
- No vendor lock-in (swap models anytime)
- Right tool automatically selected (cost + quality optimized)
- Learning preserved across model switches
- Complete reproducibility (git-backed everything)
- Measurable calibration (epistemic vectors traceable)

**Timeline:** MVP (Empirica + Sentinel v0.1) in 2-3 months. All pieces exist, just need integration.

---

## Quick Start

### 🤖 For AI Agents
```bash
empirica bootstrap --level 2  # Initialize with standard components
empirica --help  # View available commands
```
*10-minute interactive learning experience*

**Then:** [`docs/01_a_AI_AGENT_START.md`](docs/01_a_AI_AGENT_START.md)

**Interested in the bigger vision?** Start with [`VISION_EMPIRICA_SENTINEL_SYSTEM.md`](VISION_EMPIRICA_SENTINEL_SYSTEM.md)

### 👤 For Human Developers

**Installation:**
```bash
git clone https://github.com/Nubaeon/empirica.git
cd empirica
cp .env.example .env  # Configure environment (API keys optional)
pip install -e .
```

**Basic usage:**
```python
from empirica.bootstraps import bootstrap_metacognition

# Simple mode (threshold-based goals)
components = bootstrap_metacognition("my-ai", "minimal")

# AI reasoning mode (self-referential goals)
def my_llm(prompt: str) -> str:
    return ai_client.reason(prompt)

components = bootstrap_metacognition(
    ai_id="my-ai",
    level="minimal", 
    llm_callback=my_llm  # AI generates its own goals!
)
```

**Then:** [`docs/02_INSTALLATION.md`](docs/02_INSTALLATION.md) → [`docs/03_CLI_QUICKSTART.md`](docs/03_CLI_QUICKSTART.md)

## Core Workflow

```
PREFLIGHT → Assess what you know/don't know
    ↓
  ACT   → Execute task with awareness
    ↓
POSTFLIGHT → Calibrate: Were you overconfident? Underconfident?
```

**Example:**
```bash
# Before task: Assess your epistemic state
SESSION=$(empirica preflight "debug authentication issue" --quiet)

# Do the work...

# After task: Measure what you learned
empirica postflight $SESSION --summary "fixed OAuth token validation"

# System shows:
# - Epistemic delta (what you actually learned)
# - Calibration quality (predictions vs reality)
```

## Philosophy

**No heuristics.** No calibration shortcuts. No fake confidence scores.

Empirica helps AIs demonstrate *genuine epistemic self-awareness*:
- **What do I actually know?** (evidence-based)
- **What can I actually do?** (capabilities)
- **What am I uncertain about?** (unknowns)
- **What context am I missing?** (blind spots)

High uncertainty is **good** when appropriate. Acknowledge what you don't know.

## Documentation

**Start here:**
- 🤖 [AI Agent Quick Start](docs/01_a_AI_AGENT_START.md) - Command-line onboarding for AI agents
- 🔌 [MCP AI Start](docs/01_b_MCP_AI_START.md) - IDE integration (Claude Desktop, Cursor, etc.)

**Production guides:**
- 🚀 [Quick Start](docs/production/01_QUICK_START.md)
- 📦 [Installation](docs/production/02_INSTALLATION.md)  
- 🎯 [Basic Usage](docs/production/03_BASIC_USAGE.md)
- 🏗️ [Architecture Overview](docs/production/04_ARCHITECTURE_OVERVIEW.md)

**Practical examples:**
- 🔍 [Reasoning Reconstruction](examples/reasoning_reconstruction/) - Extract learning insights from sessions
- 📦 [Knowledge Transfer](examples/reasoning_reconstruction/) - Share knowledge between AI agents
- ✅ Works today with core Empirica (no additional dependencies)

**See [`docs/`](docs/) and [`docs/production/`](docs/production/) for complete documentation.**

## Installation

```bash
# Clone repository
git clone https://github.com/Nubaeon/empirica.git
cd empirica

# Install
pip install -e .

# Initialize framework
empirica bootstrap --level 2

# View available commands
empirica --help
```

**Requirements:** Python 3.10+

**For MCP integration:** See [`docs/04_MCP_QUICKSTART.md`](docs/04_MCP_QUICKSTART.md)

## Example: Real Epistemic Assessment

```bash
# AI agent assesses task before starting
$ empirica preflight "refactor authentication module"

📋 Task: refactor authentication module
🧠 Assessing epistemic state...

Vectors:
  KNOW:        0.75  (Proficient in auth patterns)
  DO:          0.65  (Can refactor with testing)
  CONTEXT:     0.55  (Need to see current implementation)
  UNCERTAINTY: 0.45  (Moderate - depends on tech stack)
  CLARITY:     0.80  (Clear goal, fuzzy scope)

⚠️  Recommendation: INVESTIGATE first (CONTEXT low)
🔍 Suggested actions:
   - Review current auth implementation
   - Check test coverage
   - Identify dependencies

Session: abc123 (saved)
```

After completing the work:

```bash
$ empirica postflight abc123 --summary "OAuth2 refactor complete"

📊 Calibration Report:

Epistemic Delta:
  KNOW:    0.75 → 0.85  (+0.10)  Learned OAuth2 edge cases
  DO:      0.65 → 0.80  (+0.15)  Successful refactor
  CONTEXT: 0.55 → 0.90  (+0.35)  Full codebase understanding

Calibration Quality: WELL-CALIBRATED ✅
  - Predicted uncertainty matched actual learning
  - Appropriate investigation phase
  - Accurate capability assessment

Session saved with calibration metrics.
```

## Use Cases

### Critical Domain Decision Making
- Healthcare AI requiring "I don't know" acknowledgment
- Financial systems with audit requirements
- Research AI with epistemic rigor
- Engineering decisions with safety implications

### AI Transparency
- Show users what AI knows vs doesn't know
- Demonstrate genuine vs confabulated confidence
- Provide audit trails for AI decisions
- Track calibration over time

### Development Workflows
- Pre-task risk assessment
- Post-task learning measurement
- Investigation loop management
- Session continuity across interruptions

## Core Principles

✅ **NO HEURISTICS** - Genuine self-assessment only  
✅ **BE HONEST** - Acknowledge what you don't know  
✅ **TRACK LEARNING** - Preflight → postflight shows growth  
✅ **VALIDATE CALIBRATION** - Were your predictions accurate?  
✅ **EVIDENCE-BASED** - No pattern matching shortcuts

## License

[LICENSE TYPE] - See [LICENSE](LICENSE) file

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## Support

- **📖 Documentation:** [`docs/README.md`](docs/README.md)
- **🔧 Troubleshooting:** [`docs/06_TROUBLESHOOTING.md`](docs/06_TROUBLESHOOTING.md)
- **💬 Questions:** Open an issue or check [docs/production/](docs/production/) for guides

---

**Questions?** Start with [`docs/01_a_AI_AGENT_START.md`](docs/01_a_AI_AGENT_START.md) (AI) or [`docs/00_START_HERE.md`](docs/00_START_HERE.md) (Human)

## Enterprise & Research

**Reasoning Reconstruction (Available Now):**
- Extract epistemic learning from sessions
- Generate audit trails with temporal proofs
- Transfer knowledge between AI agents
- Privacy-preserving analysis options

See [`examples/reasoning_reconstruction/`](examples/reasoning_reconstruction/) for working scripts and documentation.

**Semantic Extension (Optional):**
- Vector embeddings for semantic search
- Multi-agent knowledge graphs
- Advanced decision reconstruction
- Enterprise-scale deployments

See [`docs/production/SEMANTIC_REASONING_EXTENSION.md`](docs/production/SEMANTIC_REASONING_EXTENSION.md) for architecture and roadmap.

**Key principle:** Core Empirica is complete. Semantic extension adds convenience, not capability.

