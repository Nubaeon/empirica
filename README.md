# Empirica

> **We Gave AI a Mirror. Now It Measures What It Believes.**

[![Version](https://img.shields.io/badge/version-1.6.1-blue)](https://github.com/Nubaeon/empirica/releases/tag/v1.6.1)
[![PyPI](https://img.shields.io/pypi/v/empirica)](https://pypi.org/project/empirica/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Empirica is an **epistemic measurement system** that makes AI agents measurably more reliable — tracking what they know, preventing action before understanding, and compounding learning across sessions.

**[Training & Guides](https://getempirica.com)** | **[CLI Reference](docs/human/developers/CLI_COMMANDS_UNIFIED.md)** | **[Architecture](docs/architecture/)**

---

## The Problem

AI coding agents today have no self-awareness about what they know:

- **Forgets between sessions** — same questions, same dead ends, every time
- **Acts before understanding** — edits your code without knowing the architecture
- **Can't tell you when it's guessing** — no distinction between knowledge and confabulation
- **No audit trail** — reasoning evaporates with the context window

---

## What Empirica Does

| Capability | What You Experience |
|------------|-------------------|
| **Measures before acting** | AI investigates your codebase before touching it. The Sentinel gate blocks edits until understanding is demonstrated |
| **Remembers across sessions** | Findings, dead-ends, and learnings persist in a 4-layer memory system. Session 3 starts where Session 2 left off |
| **Prevents confident mistakes** | The CHECK gate requires `know >= 0.70` and `uncertainty <= 0.35` before allowing action |
| **Shows confidence in real-time** | Live statusline in your terminal: `[empirica] ⚡94% │ 🎯3 │ POSTFLIGHT │ K:95% U:5%` |
| **Calibrates against reality** | Dual-track verification compares AI self-assessment against objective evidence — tests, git metrics, goal completion |
| **Works through natural language** | You describe tasks normally. The AI operates the measurement system automatically |

---

## How You Use It

You talk to your AI normally. Empirica works in the background:

```
You:      "Fix the authentication bug in the login flow"

Empirica: [AI investigates → logs findings → passes Sentinel gate → implements fix → measures learning]

You see:  ⚡87% │ 🎯1 │ POSTFLIGHT │ K:88% U:12% │ ✓ stable
```

**You direct. The AI measures.**

Empirica's CLI has 150+ commands spanning investigation, measurement, calibration, and memory — like a cockpit instrument panel. You don't need to learn any of them. The AI reads the instruments, operates the controls, and reports back in natural language. The statusline gives you the flight data at a glance.

For power users, direct CLI access is always available: `empirica goals-list`, `empirica calibration-report`, `empirica project-search --task "..."`, and more.

**Learn the full workflow:** **[getempirica.com](https://getempirica.com)** has interactive training, guides, and deep explanations of every concept.

---

## Quick Start

### Install + Claude Code (Recommended)

```bash
pip install empirica
empirica setup-claude-code
```

Then just start working. The hooks, Sentinel, system prompt, statusline, and MCP server are all configured automatically. See [Claude Code Setup](docs/human/developers/CLAUDE_CODE_SETUP.md) for details.

### Alternative Installation Methods

<details>
<summary>One-Line Installer</summary>

```bash
# Linux / macOS
curl -fsSL https://raw.githubusercontent.com/Nubaeon/empirica/main/scripts/install.py | python3 -

# Windows (PowerShell)
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Nubaeon/empirica/main/scripts/install.py" -OutFile "install.py"
python install.py
```
</details>

<details>
<summary>Homebrew (macOS)</summary>

```bash
brew tap nubaeon/tap
brew install empirica
empirica setup-claude-code
```
</details>

<details>
<summary>Docker</summary>

```bash
# Security-hardened Alpine image (~276MB, recommended)
docker pull nubaeon/empirica:1.6.1-alpine

# Standard image (Debian slim, ~414MB)
docker pull nubaeon/empirica:1.6.1

# Run
docker run -it -v $(pwd)/.empirica:/data/.empirica nubaeon/empirica:1.6.1 /bin/bash
```
</details>

<details>
<summary>Manual / Other AI Platforms</summary>

```bash
pip install empirica
pip install empirica-mcp        # MCP Server (for Cursor, Cline, etc.)
cd your-project && empirica project-init
```

The CLI works standalone on any platform. The full epistemic workflow (CASCADE, Sentinel, calibration) requires loading the system prompt into your AI. See [System Prompts](docs/human/developers/system-prompts/) for Claude, Copilot, Gemini, Qwen, and Roo Code.
</details>

### First Session

```bash
empirica onboard   # Interactive walkthrough of the full workflow
```

Or just start working — with Claude Code hooks active, the AI manages the epistemic workflow automatically.

---

## The Measurement Architecture

Empirica works through nested abstraction layers:

```
Plan
 └── Transaction 1 (Goal A)
      ├── NOETIC: investigate, search, read → findings, unknowns, dead-ends
      ├── CHECK: Sentinel gate → proceed / investigate more
      ├── PRAXIC: implement, write, commit → goals completed
      └── POSTFLIGHT: measure learning delta → persists to memory
 └── Transaction 2 (Goal B, informed by T1's findings)
      └── ...
```

**Plans** decompose into **transactions** — one per goal or Claude Code task. Each transaction is a **noetic-praxic loop**: investigate first (noetic), then act (praxic), with the Sentinel gating the transition. Along the way, the AI collects and reads **artifacts** (findings, unknowns, assumptions, dead-ends, decisions) while using **semantic search** to surface relevant epistemic patterns and anti-patterns from the project's history. Top artifacts are ranked by confidence and fed into each project's **MEMORY.md** as a hot cache.

### The CASCADE Cycle

```
PREFLIGHT ────────► CHECK ────────► POSTFLIGHT
    │                 │                  │
 Baseline         Sentinel           Learning
 Assessment        Gate               Delta
    │                 │                  │
 "What do I      "Am I ready      "What did I
  know now?"      to act?"         learn?"
```

**PREFLIGHT:** AI assesses its knowledge state before starting work.
**CHECK:** Sentinel gate validates readiness before allowing code edits.
**POSTFLIGHT:** AI measures what it learned, creating a delta that persists.

---

## Live Statusline

With Claude Code hooks enabled, you see the AI's epistemic state in real-time:

```
[empirica] ⚡94% │ 🎯3 ❓12/5 │ POSTFLIGHT │ K:95% U:5% C:92% │ ✓ │ ✓ stable
```

| Signal | Meaning |
|--------|---------|
| **⚡94%** | Overall epistemic confidence |
| **🎯3 ❓12/5** | Open goals (3), unknowns (12 total, 5 blocking) |
| **POSTFLIGHT** | Current CASCADE phase |
| **K:95% U:5% C:92%** | Knowledge, Uncertainty, Context |
| **✓ stable** | Drift indicator |

---

## The 13 Epistemic Vectors

These vectors emerged from 600+ real working sessions across multiple AI systems. They measure the dimensions that consistently predict success or failure in complex tasks.

| Tier | Vector | What It Measures |
|------|--------|------------------|
| **Gate** | `engagement` | Is the AI actively processing or disengaged? |
| **Foundation** | `know` | Domain knowledge depth |
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
| **Meta** | `uncertainty` | Explicit doubt tracking |

Deep dive: [Epistemic Vectors Explained](docs/human/end-users/05_EPISTEMIC_VECTORS_EXPLAINED.md)

---

## How It Works With Claude Code

Empirica doesn't replace or reinvent anything Claude Code already does. Claude Code owns tasks, plans, memory, and projects. Empirica adds the **measurement layer** on top:

| Claude Code Does | Empirica Adds |
|-----------------|--------------|
| Task management | Epistemic goals with measurable completion |
| Plan mode | Investigation phase with Sentinel gating — no edits until understanding is verified |
| MEMORY.md | Auto-curated hot cache ranked by epistemic confidence |
| Context window | 4-layer memory that survives compaction and persists across sessions |
| Code editing | Grounded calibration — was the AI's confidence justified by test results? |
| Subagent spawning | Bounded autonomy with delegated work counting and budget tracking |

The result: Claude Code's native capabilities, enhanced with measurement, gating, and calibration feedback that compounds over time.

---

## Platform Support

| Platform | Integration Level | What You Get |
|----------|------------------|-------------|
| **Claude Code** | Full (production) | Hooks, Sentinel gate, skills, agents, statusline, MCP |
| **Cursor, Cline** | MCP server | CASCADE workflow, memory, calibration via MCP tools |
| **Gemini CLI, Copilot** | Experimental | System prompt + CLI |
| **Any AI** | CLI + prompt | Full measurement via CLI commands and system prompt |

---

## Documentation & Training

| Resource | What It Covers |
|----------|---------------|
| **[getempirica.com](https://getempirica.com)** | Training course, interactive guides, deep explanations |
| **[Natural Language Guide](docs/human/end-users/EMPIRICA_NATURAL_LANGUAGE_GUIDE.md)** | How to collaborate with AI using Empirica |
| **[Getting Started](docs/human/end-users/01_START_HERE.md)** | First-time setup and concepts |
| **[CLI Reference](docs/human/developers/CLI_COMMANDS_UNIFIED.md)** | All 150+ commands documented |
| **[Architecture](docs/architecture/)** | Technical reference for contributors |
| **[System Prompts](docs/human/developers/system-prompts/)** | AI prompts for Claude, Copilot, Gemini, Qwen, Roo |

---

## The Empirica Ecosystem

| Project | Description | Status |
|---------|-------------|--------|
| **[Empirica](https://github.com/Nubaeon/empirica)** | Core measurement system — CASCADE, Sentinel, calibration, 13 vectors | Open source |
| **[Empirica Iris](https://github.com/Nubaeon/empirica-iris)** | Epistemic browser automation with SVG spatial indexing — Sentinel gating for visual interactions | Open source |
| **[Docpistemic](https://github.com/Nubaeon/docpistemic)** | Epistemic documentation coverage assessment — know what your docs know | Open source |
| **[Breadcrumbs](https://github.com/Nubaeon/breadcrumbs)** | Survive context compacts with git notes — dead simple session continuity | Open source |
| **[Empirica Workspace](https://getempirica.com)** | Entity Knowledge Graph, Epistemic Prompt Engine, CRM, portfolio dashboard | Proprietary |

**Building something with Empirica?** [Open an issue](https://github.com/Nubaeon/empirica/issues) to get listed.

---

## What's New in 1.6.1

- **Code Quality Evidence** — Grounded calibration includes ruff, radon, and pyright metrics as objective evidence
- **docs-assess Ignore Patterns** — `[tool.empirica.docs-assess]` in pyproject.toml with fnmatch patterns
- **API Reference Expansion** — 15+ class entries added, docs-assess coverage 71.8% to 84.0%
- **Claude Code Symbiosis** — Architecture docs for MEMORY.md hot cache, task-goal bridge, session lifecycle hooks
- **Security Updates** — flask >= 3.1.3, werkzeug >= 3.1.6, pillow >= 12.1.1

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

MIT License — see [LICENSE](LICENSE) for details.

---

**Author:** David S. L. Van Assche
**Version:** 1.6.1

*Turtles all the way down — built with its own epistemic framework, measuring what it knows at every step.*
