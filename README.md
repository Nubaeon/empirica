# 🧠 Empirica - Functional Self-Awareness for AI Agents

> Epistemic transparency and calibration for high-stakes AI decision making

## What is Empirica?

AI agents assess their own knowledge, uncertainty, and capabilities *before* acting—enabling principled decisions in critical domains where "I don't know" matters.

**This is empirically testable.** Functional self-awareness produces measurable results through calibration validation.

## Who Uses Empirica?

**🤖 AI agents** (Claude, GPT, Gemini, etc.) - You're the primary user  
**👤 Developers** in critical domains - Healthcare, finance, research, engineering  
**🏢 Teams** requiring AI transparency - Audit trails, calibration metrics, decision logs

⚠️ **Not for casual use** - Requires genuine epistemic engagement

## Quick Start

### 🤖 For AI Agents
```bash
empirica onboard --ai-id <your-name>
```
*10-minute interactive learning experience*

**Then:** [`docs/01_a_AI_AGENT_START.md`](docs/01_a_AI_AGENT_START.md)

### 👤 For Human Developers
```bash
pip install -e .
empirica bootstrap --ai-id assistant
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

## Key Features

- 🎯 **12-vector epistemic self-assessment** - KNOW, DO, CONTEXT, CLARITY, COHERENCE, SIGNAL, DENSITY, STATE, CHANGE, COMPLETION, IMPACT, ENGAGEMENT (+ UNCERTAINTY meta-tracking)
- 🔄 **CASCADE workflow** - Preflight → Investigate → Check → Act → Postflight → Synthesize → Learn
- 📊 **Calibration tracking** - Overconfident vs well-calibrated measurement
- 🔌 **MCP server** - IDE integration (Claude Desktop, Cursor, Windsurf, Rovo Dev)
- 🐚 **CLI interface** - Direct agent interaction via terminal
- 📈 **Dashboard monitoring** - Real-time epistemic tracking (tmux-based)
- 🔍 **Bayesian belief tracking** - Detect calibration drift
- 📝 **Session continuity** - Resume previous work with context

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
git clone https://github.com/your-org/empirica.git
cd empirica

# Install
pip install -e .

# Verify
empirica --version

# Start learning
empirica onboard --ai-id <your-name>
```

**Requirements:** Python 3.8+

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
- **💬 Questions:** Open an issue or ask your AI agent to run `empirica onboard`

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

