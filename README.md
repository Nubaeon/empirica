# Empirica

> **Teaching AI to know what it knows—and what it doesn't**

[![Version](https://img.shields.io/badge/version-1.6.0-blue)](https://github.com/Nubaeon/empirica/releases/tag/v1.6.0)
[![PyPI](https://img.shields.io/pypi/v/empirica)](https://pypi.org/project/empirica/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## What is Empirica?

Empirica is an **epistemic self-awareness framework** that enables AI agents to genuinely understand the boundaries of their own knowledge. Instead of producing confident-sounding responses regardless of actual understanding, AI agents using Empirica can accurately assess what they know, identify gaps, and communicate uncertainty honestly.

**The core insight:** AI systems today lack functional self-awareness. They can't reliably distinguish between "I know this well" and "I'm guessing." Empirica provides the cognitive infrastructure to make this distinction measurable and actionable.

---

## Why This Matters

**The Problem:** AI agents exhibit "confident ignorance"—they generate plausible-sounding responses about topics they don't actually understand. This leads to:

- Hallucinated facts presented as truth
- Wasted time investigating already-explored dead ends
- Knowledge lost between sessions
- No way to tell when an AI is genuinely confident vs. bluffing

**The Solution:** Empirica introduces **epistemic vectors**—quantified measures of knowledge state that AI agents track in real-time. These vectors emerged from observing what information actually matters when assessing cognitive readiness.

---

## The 13 Foundational Vectors

These vectors weren't designed in a vacuum. They **emerged from 600+ real working sessions** across multiple AI systems (Claude, GPT-4, Gemini, Qwen, and others), with Claude serving as the primary development partner due to its reasoning capabilities.

The pattern proved universal: regardless of which AI system we tested, these same dimensions consistently predicted success or failure in complex tasks.

### The Vector Space

| Tier | Vector | What It Measures |
|------|--------|------------------|
| **Gate** | `engagement` | Is the AI actively processing or disengaged? |
| **Foundation** | `know` | Domain knowledge depth (0.7+ = ready to act) |
| | `do` | Execution capability |
| | `context` | Access to relevant information |
| **Comprehension** | `clarity` | How clear is the understanding? |
| | `coherence` | Do the pieces fit together? |
| | `signal` | Signal-to-noise in available information |
| | `density` | Information richness |
| **Execution** | `state` | Current working state |
| | `change` | Rate of progress/change |
| | `completion` | Task completion level |
| | `impact` | Significance of the work |
| **Meta** | `uncertainty` | Explicit doubt tracking (0.35- = ready to act) |

### Why These Vectors?

**Readiness Gate:** Through empirical observation, we found that `know ≥ 0.70` AND `uncertainty ≤ 0.35` reliably predicts successful task execution. Below these thresholds, investigation is needed.

**The Key Insight:** The `uncertainty` vector is explicitly tracked because AI systems naturally underreport doubt. Making it a first-class metric forces honest assessment.

---

## Applications Across Industries

While the vectors emerged from software development work, they map to any domain requiring knowledge assessment:

| Industry | Primary Vectors | Use Case |
|----------|-----------------|----------|
| **Software Development** | know, context, uncertainty, completion | Code review, architecture decisions, debugging |
| **Research & Analysis** | know, clarity, coherence, signal | Literature review, hypothesis testing |
| **Healthcare** | know, uncertainty, impact | Diagnostic confidence, treatment recommendations |
| **Legal** | context, clarity, coherence | Case analysis, precedent research |
| **Education** | know, do, completion | Learning assessment, curriculum design |
| **Finance** | know, uncertainty, impact | Risk assessment, investment analysis |

### Why Software Development First?

Software engineering provides an ideal testbed because:

1. **Measurable outcomes** - Code either works or it doesn't
2. **Complex knowledge states** - Requires synthesizing documentation, code, tests, and context
3. **Session continuity** - Projects span days/weeks with context loss between sessions
4. **Multi-agent potential** - Team collaboration benefits from shared epistemic state

Empirica was battle-tested here before expanding to other domains.

---

## Quick Start

### For End Users

**Visit [getempirica.com](https://getempirica.com)** for the guided setup experience with tutorials and support.

### For Developers

#### Install + Claude Code Integration (Recommended)

```bash
pip install empirica
empirica setup-claude-code
```

`setup-claude-code` is the one-command integration that installs everything Claude Code needs:

- **Plugin** — `empirica-integration` to `~/.claude/plugins/local/` (skills, agents, hooks, scripts)
- **Sentinel hooks** — PreToolUse gates that block praxic tools (Edit/Write/Bash) until CHECK passes
- **Session lifecycle hooks** — SessionStart/SessionEnd for automatic session management, SubagentStart/Stop for delegation tracking, PreCompact for epistemic state persistence across context compaction
- **System prompt** — Empirica prompt as `@include` reference in CLAUDE.md (preserves your existing instructions)
- **StatusLine** — Live metacognitive signal in your terminal (confidence, phase, drift)
- **MCP server** — Installs `empirica-mcp` and configures `.claude/mcp.json`
- **Semantic layer check** — Detects Ollama + nomic-embed-text + Qdrant availability (optional but recommended for cross-session memory)

```bash
# Options
empirica setup-claude-code --force        # Reinstall even if already present
empirica setup-claude-code --skip-mcp     # Skip MCP server setup
empirica setup-claude-code --skip-claude-md  # Keep existing system prompt
```

#### One-Line Installer (Alternative)

The installer handles pip install + Claude Code setup + demo project:

```bash
# Linux / macOS
curl -fsSL https://raw.githubusercontent.com/Nubaeon/empirica/main/scripts/install.py | python3 -

# Windows (PowerShell)
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Nubaeon/empirica/main/scripts/install.py" -OutFile "install.py"
python install.py
```

#### Manual Installation

```bash
# Install from PyPI
pip install empirica

# Or with all features
pip install empirica[all]

# MCP Server (for Claude Desktop, Cursor, etc.)
pip install empirica-mcp

# Initialize in your project
cd your-project
empirica project-init
```

> **Note:** The CLI tools work standalone, but the full epistemic workflow (CASCADE phases,
> calibration, Sentinel gates) requires the AI to have the system prompt loaded.
> `setup-claude-code` handles this automatically. For other AI platforms, see
> [System Prompts](docs/human/developers/system-prompts/) for Copilot, Gemini, Qwen, and Roo Code.

#### Homebrew (macOS)

```bash
brew tap nubaeon/tap
brew install empirica
empirica setup-claude-code  # Don't forget this step
```

#### Docker

```bash
# Standard image (Debian slim, ~414MB)
docker pull nubaeon/empirica:1.6.0

# Security-hardened Alpine image (~276MB, recommended)
docker pull nubaeon/empirica:1.6.0-alpine

# Run
docker run -it -v $(pwd)/.empirica:/data/.empirica nubaeon/empirica:1.6.0 /bin/bash
```

---

## After Installation: Getting Started

### Interactive Onboarding (Recommended)

```bash
empirica onboard
```

Walks you through the full workflow: CASCADE phases, 13 epistemic vectors, noetic/praxic phases, transaction discipline, goal tracking, calibration reports, and all CLI commands with examples.

### Initialize Your Project

```bash
cd your-project
empirica project-init
empirica session-create --ai-id claude-code --output json
```

Then just start working — with Claude Code hooks active, the Sentinel automatically manages the epistemic workflow. Log findings as you discover them, create goals for your tasks, and let the measurement system track your learning.

### Explore Documentation

```bash
# Search documentation semantically
empirica docs-explain --topic "epistemic vectors"
empirica docs-explain --topic "CASCADE workflow"

# Assess documentation coverage
empirica docs-assess
```

### Try the Demo Project

The one-line installer creates a demo project at `~/empirica-demo/`:

```bash
cd ~/empirica-demo
cat WALKTHROUGH.md
```

---

## Documentation

### For Humans

Start here based on your role:

| Role | Start With | Then Read |
|------|------------|-----------|
| **End User** | [Getting Started](docs/human/end-users/01_START_HERE.md) | [Empirica Explained Simply](docs/human/end-users/EMPIRICA_EXPLAINED_SIMPLE.md) |
| **Developer** | [Developer README](docs/human/developers/README.md) | [Claude Code Setup](docs/human/developers/CLAUDE_CODE_SETUP.md) |

**Documentation Structure:**
```
docs/
├── human/                    # Human-readable documentation
│   ├── end-users/            # Installation, concepts, troubleshooting
│   └── developers/           # Integration, system prompts, API
│       └── system-prompts/   # AI system prompts (Claude, Copilot, etc.)
│
└── architecture/             # Technical architecture (for AI context loading)
```

### For AI Integration

If you're integrating Empirica into an AI system:

- **System Prompts:** [docs/human/developers/system-prompts/](docs/human/developers/system-prompts/)
- **MCP Server:** [empirica-mcp/](empirica-mcp/) (Model Context Protocol integration)
- **Architecture Docs:** [docs/architecture/](docs/architecture/) (AI-optimized technical reference)

### Key Guides

| Guide | Purpose |
|-------|---------|
| [Noetic-Praxic Framework](docs/architecture/NOETIC_PRAXIC_FRAMEWORK.md) | The PREFLIGHT → CHECK → POSTFLIGHT loop |
| [Epistemic Vectors Explained](docs/human/end-users/05_EPISTEMIC_VECTORS_EXPLAINED.md) | Deep dive into all 13 vectors |
| [CLI Reference](docs/human/developers/CLI_COMMANDS_UNIFIED.md) | Complete command documentation |
| [Storage Architecture](docs/architecture/STORAGE_ARCHITECTURE_COMPLETE.md) | Four-layer data persistence |

---

## How It Works

### The CASCADE Workflow

Every significant task follows this loop:

```
PREFLIGHT ────────► CHECK ────────► POSTFLIGHT
    │                 │                  │
    │                 │                  │
 Baseline         Decision           Learning
 Assessment        Gate               Delta
    │                 │                  │
 "What do I      "Am I ready      "What did I
  know now?"      to act?"         learn?"
```

**PREFLIGHT:** AI assesses its knowledge state before starting work.
**CHECK:** Sentinel gate validates readiness (know ≥ 0.70, uncertainty ≤ 0.35).
**POSTFLIGHT:** AI measures what it learned, creating a learning delta.

### Learning Compounds Across Sessions

```
Session 1: know=0.40 → know=0.65  (Δ +0.25)
    ↓ (findings persisted)
Session 2: know=0.70 → know=0.85  (Δ +0.15)
    ↓ (compound learning)
Session 3: know=0.82 → know=0.92  (Δ +0.10)
```

Each session starts higher because learnings persist. No more re-investigating the same questions.

---

## Live Metacognitive Signal

With Claude Code hooks enabled, you see epistemic state in your terminal:

```
[empirica] ⚡94% │ 🎯3 ❓12/5 │ POSTFLIGHT │ K:95% U:5% C:92% │ ✓ │ ✓ stable
```

**What this tells you:**
- **⚡94%** — Overall epistemic confidence (⚡ high, 💡 good, 💫 uncertain, 🌑 low)
- **🎯3 ❓12/5** — Open goals (3) and unknowns (12 total, 5 blocking goals)
- **POSTFLIGHT** — CASCADE phase (PREFLIGHT → CHECK → POSTFLIGHT)
- **K:95% U:5% C:92%** — Knowledge, Uncertainty, Context scores
- **✓** / **⚠** / **△** — Learning delta summary (net positive / net negative / neutral)
- **✓ stable** — Drift indicator (✓ stable, ⚠ drifting, ✗ severe)

---

## Built With Empirica

Projects using Empirica's epistemic foundations:

| Project | Description | Use Case |
|---------|-------------|----------|
| **[Docpistemic](https://github.com/Nubaeon/docpistemic)** | Epistemic documentation system | Self-aware documentation that tracks what it explains well vs. poorly |
| **[Carapace](https://github.com/Nubaeon/carapace)** | Defensive AI shell | Security-focused AI wrapper with epistemic safety gates |
**Building something with Empirica?** Open an issue to get listed here.

---

## What's New in 1.6.0

- **Sentinel File-Based Control** — Sentinel enable/disable via `~/.empirica/sentinel_enabled` file flag. Dynamically settable without session restart (env vars required terminal restart)
- **Sentinel Bypass Fix** — System prompt contained bare `export` commands that Claudes would execute, disabling the Sentinel. Replaced with tables + "DO NOT execute" warnings
- **SessionStart Matcher Fix** — `setup-claude-code` generated invalid matchers (`new|fresh`, bare `compact`). Fixed to valid Claude Code values (`startup`, `compact|resume`)
- **MirrorDriftMonitor Removed** — Vestigial drift detection superseded by grounded calibration pipeline. Removed `check-drift` CLI command, MCP tool, and drift module (-562 lines)
- **Transaction Planning Skill** — `/epistemic-transaction` skill gains interactive `plan-transactions` mode: interview → explore → decompose → plan with estimated vectors → execute
- **Phantom Project Fix** — Project ID resolution uses `project.yaml` as authoritative source, preventing self-propagating phantom project IDs

---

## Privacy & Data

**Your data stays local:**

- `.empirica/` — Local SQLite database (gitignored by default)
- `.git/refs/notes/empirica/*` — Epistemic checkpoints (local unless you push)
- Qdrant runs locally if enabled

No cloud dependencies. No telemetry. Your epistemic data is yours.

---

## Community & Support

- **Website:** [getempirica.com](https://getempirica.com)
- **Issues:** [GitHub Issues](https://github.com/Nubaeon/empirica/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Nubaeon/empirica/discussions)

---

## License

MIT License — Maximum adoption, aligned with Empirica's transparency principles.

See [LICENSE](LICENSE) for details.

---

**Author:** David S. L. Van Assche
**Version:** 1.6.0

*Turtles all the way down — built with its own epistemic framework, measuring what it knows at every step.*
