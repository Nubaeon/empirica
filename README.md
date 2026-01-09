# Empirica

> **Teaching AI to know what it knows—and what it doesn't**

[![Version](https://img.shields.io/badge/version-1.3.0-blue)](https://github.com/Nubaeon/empirica/releases/tag/v1.3.0)
[![PyPI](https://img.shields.io/pypi/v/empirica)](https://pypi.org/project/empirica/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
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

### For Developers: One-Command Install

The installer sets up everything: Claude Code hooks, system prompts, environment configuration, and a demo project.

#### Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/Nubaeon/empirica/main/scripts/install.py | python3 -
```

Or download and run manually:

```bash
wget https://raw.githubusercontent.com/Nubaeon/empirica/main/scripts/install.py
python3 install.py
```

#### Windows (PowerShell)

```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Nubaeon/empirica/main/scripts/install.py" -OutFile "install.py"
python install.py
```

#### What the Installer Does

1. **Installs Empirica** via pip
2. **Sets up Claude Code hooks** for automatic epistemic continuity
3. **Places CLAUDE.md** in the correct location (`~/.claude/CLAUDE.md`)
4. **Configures environment variables** for your shell
5. **Creates a demo project** so you can try it immediately
6. **Optionally sets up Qdrant** for semantic memory (local vector search)

### Manual Installation

If you prefer manual setup:

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

> **⚠️ Important: System Prompt Required**
>
> Empirica requires a system prompt to function correctly. The CLI tools work without it,
> but the full epistemic workflow (CASCADE phases, calibration, Sentinel gates) requires
> the AI to understand the framework.
>
> **For manual installations, copy the system prompt:**
> ```bash
> # Create Claude Code config directory
> mkdir -p ~/.claude
>
> # Copy the system prompt (choose your AI)
> curl -fsSL https://raw.githubusercontent.com/Nubaeon/empirica/main/docs/human/developers/system-prompts/CLAUDE.md \
>   -o ~/.claude/CLAUDE.md
> ```
>
> The installer handles this automatically. See [System Prompts](docs/human/developers/system-prompts/)
> for prompts for other AI assistants (Copilot, etc.).

### Homebrew (macOS)

```bash
brew tap nubaeon/tap
brew install empirica
```

### Docker

```bash
# Standard image (Debian slim, ~414MB)
docker pull nubaeon/empirica:1.3.0

# Security-hardened Alpine image (~276MB, recommended)
docker pull nubaeon/empirica:1.3.0-alpine

# Run
docker run -it -v $(pwd)/.empirica:/data/.empirica nubaeon/empirica:1.3.0 /bin/bash
```

---

## After Installation: Getting Started

Once installed, let Empirica teach you how it works:

### Option 1: Interactive Onboarding (Recommended)

```bash
# Start the guided onboarding experience
empirica onboard
```

This walks you through creating your first session, understanding vectors, and logging your first finding.

### Option 2: Ask the AI to Explain

If you're using Claude Code or another AI with Empirica installed:

```
"Explain how Empirica works using docs-explain"
"What are epistemic vectors and how do I use them?"
"Help me set up Empirica for my project"
```

The AI can query Empirica's documentation semantically and explain concepts tailored to your context.

### Option 3: Explore Documentation

```bash
# Search documentation semantically
empirica docs-explain --topic "epistemic vectors"
empirica docs-explain --topic "CASCADE workflow"
empirica docs-explain --topic "session management"

# List all available topics
empirica docs-list
```

### Option 4: Try the Demo Project

The installer creates a demo project at `~/empirica-demo/`. Navigate there and follow the `WALKTHROUGH.md`:

```bash
cd ~/empirica-demo
cat WALKTHROUGH.md
```

### Expanding Your Own Projects

Once you understand the basics, add epistemic foundations to your existing projects:

```bash
cd your-existing-project
empirica project-init

# Create your first session
empirica session-create --ai-id claude-code --output json

# Start tracking what you know
empirica preflight-submit -
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
| [CASCADE Workflow](docs/architecture/CASCADE_WORKFLOW.md) | The PREFLIGHT → CHECK → POSTFLIGHT loop |
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
[empirica] ⚡79% │ ⚡ PRAXIC │ POSTFLIGHT │ K:80% U:20% │ Δ K:+0.30 U:-0.30 │ ✓ stable
```

**What this tells you:**
- **⚡79%** — Overall epistemic confidence
- **PRAXIC** — AI is in action mode (vs NOETIC = investigation mode)
- **K:80% U:20%** — 80% knowledge, 20% uncertainty
- **Δ K:+0.30** — Gained 30% knowledge this session
- **✓ stable** — No epistemic drift detected

---

## Built With Empirica

Projects using Empirica's epistemic foundations:

| Project | Description | Use Case |
|---------|-------------|----------|
| **[Docpistemic](https://github.com/Nubaeon/docpistemic)** | Epistemic documentation system | Self-aware documentation that tracks what it explains well vs. poorly |
| **[Carapace](https://github.com/Nubaeon/carapace)** | Defensive AI shell | Security-focused AI wrapper with epistemic safety gates |
| **[Empirica CRM](https://github.com/Nubaeon/empirica-crm)** | Customer relationship management | CRM where AI knows its confidence about customer insights |

**Building something with Empirica?** Open an issue to get listed here.

---

## What's New in 1.3.0

- **Qdrant Memory Integration** — Full 4-collection semantic memory system
- **Embedding Providers** — Jina AI, Voyage AI, expanded Ollama support
- **Lessons System** — Cold storage procedural knowledge with cognitive immune decay
- **Cross-Platform Installer** — One-command setup for Linux, macOS, Windows
- **Sentinel Safety Gates** — Human-in-the-loop gates bounding AI autonomy
- **Multi-Agent Spawning** — Spawn epistemic sub-agents for parallel investigation

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
**Version:** 1.3.0

*Built through 600+ sessions of genuine epistemic collaboration between humans and AI.*
