# 🧠 Empirica - Epistemic Vector-Based Functional Self-Awareness Framework

> **AI agents that know what they know—and what they don't**

[![Version](https://img.shields.io/badge/version-1.2.0-blue)](https://github.com/Nubaeon/empirica/releases/tag/v1.2.0)
[![PyPI](https://img.shields.io/pypi/v/empirica)](https://pypi.org/project/empirica/)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)](https://github.com/Nubaeon/empirica/blob/main/LICENSE)
[![Docker](https://img.shields.io/badge/docker-nubaeon%2Fempirica-blue)](https://hub.docker.com/r/nubaeon/empirica)

## What's New in 1.2.0

- **🔧 MCP Server with 57 Tools** - Full Model Context Protocol integration with epistemic middleware
- **👥 9 Human Copilot Tools** - Enhanced human oversight (monitor, check-drift, issue-handoff, etc.)
- **🌙 3-Layer Signaling System** - Moon phase indicators for drift detection (basic/default/full)
- **🚦 Sentinel Gates** - Automatic safety gates (HALT/BRANCH/REVISE/LOCK) for memory drift
- **🔄 Memory Compact Hooks** - Seamless Claude Code integration with pre/post compact hooks
- **📊 Unified Statusline** - Real-time epistemic status with vector health indicators

## What is Empirica?

**Empirica is an epistemic self-awareness framework for AI agents** that enables genuine self-assessment, systematic learning tracking, and effective multi-agent collaboration.

Unlike traditional AI tools that rely on static prompts or heuristic-based evaluation, Empirica provides **13-dimensional epistemic vector tracking** that allows AI agents to know what they know (and don't know) with measurable precision.

### Core Philosophy: Epistemic Self-Awareness

**The Problem:** AI agents often exhibit "confident ignorance" - they confidently generate responses about topics they don't actually understand.

**The Solution:** Empirica enables **genuine epistemic self-assessment** through:

1. **13-Dimensional Vector Space** - Track knowledge, capability, context, and uncertainty across multiple dimensions
2. **CASCADE Workflow** - Structured reasoning process with explicit epistemic gates
3. **Dynamic Context Loading** - Resume work with compressed project memory
4. **Multi-Agent Coordination** - Seamless handoffs between AI agents

### Key Features

- ✅ **Honest uncertainty tracking**: "I don't know" becomes a measured response
- ✅ **Focused investigation**: Direct effort where knowledge gaps exist
- ✅ **Genuine learning measurement**: Track what you learned, not just what you did
- ✅ **Session continuity**: Resume work across sessions without losing context
- ✅ **Multi-agent coordination**: Share epistemic state across AI teams

**Result:** AI you can trust—not because it's always right, but because **it knows when it might be wrong**.

## 🚀 Quick Start

### Installation

#### PyPI (Recommended)

```bash
# Core installation
pip install empirica

# With API/dashboard features
pip install empirica[api]

# With vector search
pip install empirica[vector]

# Everything
pip install empirica[all]
```

#### Docker

```bash
# Pull the latest image
docker pull nubaeon/empirica:1.2.0

# Run a command
docker run -it nubaeon/empirica:1.2.0 empirica --help

# Interactive session with persistent data
docker run -it -v $(pwd)/.empirica:/data/.empirica nubaeon/empirica:1.2.0 /bin/bash
```

#### From Source

```bash
# Latest stable release
pip install git+https://github.com/Nubaeon/empirica.git@v1.2.0

# Development branch
pip install git+https://github.com/Nubaeon/empirica.git@develop
```

### Initialize a New Project

```bash
# Navigate to your git repository
cd your-project
git init

# Initialize Empirica
empirica project-init
```

### Your First Session

```bash
# AI-first JSON mode (recommended for AI agents)
echo '{"ai_id": "myagent", "session_type": "development"}' | empirica session-create -
```

## 🎯 Core Workflow: CASCADE

Empirica uses **CASCADE** - a metacognitive workflow with explicit epistemic phases:

```bash
# 1. PREFLIGHT: Assess what you know BEFORE starting
cat > preflight.json <<EOF
{
  "session_id": "abc-123",
  "vectors": {
    "engagement": 0.8,
    "foundation": {"know": 0.6, "do": 0.7, "context": 0.5},
    "comprehension": {"clarity": 0.7, "coherence": 0.8, "signal": 0.6, "density": 0.7},
    "execution": {"state": 0.5, "change": 0.4, "completion": 0.3, "impact": 0.5},
    "uncertainty": 0.4
  },
  "reasoning": "Starting with moderate knowledge of OAuth2..."
}
EOF
cat preflight.json | empirica preflight-submit -

# 2. WORK: Do your actual implementation
#    Use CHECK gates as needed for decision points

# 3. POSTFLIGHT: Measure what you ACTUALLY learned
cat > postflight.json <<EOF
{
  "session_id": "abc-123",
  "vectors": {
    "engagement": 0.9,
    "foundation": {"know": 0.85, "do": 0.9, "context": 0.8},
    "comprehension": {"clarity": 0.9, "coherence": 0.9, "signal": 0.85, "density": 0.8},
    "execution": {"state": 0.9, "change": 0.85, "completion": 1.0, "impact": 0.8},
    "uncertainty": 0.15
  },
  "reasoning": "Successfully implemented OAuth2, learned token refresh patterns"
}
EOF
cat postflight.json | empirica postflight-submit -
```

**Result:** Quantified learning (know: +0.25, uncertainty: -0.25)

## ✨ Key Features

### 📊 Epistemic Self-Assessment (13 Vectors)

Track knowledge across 3 tiers:
- **Tier 0 (Foundation):** engagement, know, do, context
- **Tier 1 (Comprehension):** clarity, coherence, signal, density
- **Tier 2 (Execution):** state, change, completion, impact
- **Meta:** uncertainty (explicit tracking)

### 🎯 Goal-Driven Task Management

```bash
# Create goals with epistemic scope
echo '{
  "session_id": "abc-123",
  "objective": "Implement OAuth2 authentication",
  "scope": {
    "breadth": 0.6,
    "duration": 0.4,
    "coordination": 0.3
  },
  "success_criteria": ["Auth works", "Tests pass"],
  "estimated_complexity": 0.65
}' | empirica goals-create -
```

### 🔄 Session Continuity

```bash
# Load project context dynamically (~800 tokens)
empirica project-bootstrap --project-id <PROJECT_ID>
```

### 🤝 Multi-Agent Coordination

**Share epistemic state via git notes:**
```bash
# Push your epistemic checkpoints
git push origin refs/notes/empirica/*

# Pull team member's state
git fetch origin refs/notes/empirica/*:refs/notes/empirica/*
```

## 📦 Optional Integrations

### BEADS Issue Tracking

**Install BEADS** (separate Rust project):
```bash
cargo install beads
```

### MCP Server (Model Context Protocol)

**For AI tools that support MCP:**
```bash
# Install MCP server
pip install empirica-mcp

# Run server
empirica-mcp
```

**Features:** 57 tools including 9 Human Copilot tools for enhanced human oversight.

### Claude Code Integration

**Automatic epistemic continuity across memory compacts:**
```bash
# Install plugin (bundled with Empirica)
./scripts/install_claude_plugin.sh
```

### Vector Search (Qdrant)

```bash
pip install empirica[vector]

# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Embed docs
empirica project-embed --project-id <PROJECT_ID>

# Search
empirica project-search --project-id <PROJECT_ID> --task "oauth2"
```

## 📚 Documentation

### Getting Started
- 📖 [First-Time Setup](https://github.com/Nubaeon/empirica/blob/main/docs/guides/FIRST_TIME_SETUP.md)
- 🚀 [Empirica Explained Simply](https://github.com/Nubaeon/empirica/blob/main/docs/EMPIRICA_EXPLAINED_SIMPLE.md)

### Guides
- 🎯 [CASCADE Workflow](https://github.com/Nubaeon/empirica/blob/main/docs/CASCADE_WORKFLOW.md)
- 📊 [Epistemic Vectors](https://github.com/Nubaeon/empirica/blob/main/docs/archive/v3/production/05_EPISTEMIC_VECTORS.md)

### Reference
- 📋 [CLI Commands](https://github.com/Nubaeon/empirica/blob/main/docs/reference/CLI_COMMANDS_COMPLETE.md)
- 🗄️ [Database Schema](https://github.com/Nubaeon/empirica/blob/main/docs/reference/DATABASE_SCHEMA_GENERATED.md)

## 🔒 Privacy & Data Isolation

**Your data is isolated per-repo:**
- ✅ `.empirica/` - Local SQLite database (gitignored)
- ✅ `.git/refs/notes/empirica/*` - Epistemic checkpoints (local by default)
- ✅ `.beads/` - BEADS database (gitignored)

## 🛠️ Development

### Running Tests

```bash
# Core tests
pytest tests/

# Integration tests
pytest tests/integration/
```

### Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📊 System Requirements

- **Python:** 3.11+
- **Git:** Required for epistemic checkpoints
- **Optional:** Docker (for Qdrant), Rust/Cargo (for BEADS)

## 🎓 Learn More

### Research & Concepts
- [Why Empirica?](https://github.com/Nubaeon/empirica/blob/main/WHY_EMPIRICA.md)
- [Epistemic Architecture](https://github.com/Nubaeon/empirica/blob/main/docs/architecture/EMPIRICA_COMPLETE_ARCHITECTURE.md)

### Use Cases
- Research & Development
- Multi-Agent Teams
- Long-Running Projects
- Training Data Generation
- Epistemic Audit Trails

## 🔗 Related Projects

- **[Empirica MCP](./empirica-mcp/)** - Model Context Protocol server for Empirica integration
- **[Empirica EPRE](https://github.com/Nubaeon/empirica-epre)** - Epistemic Pattern Recognition Engine

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/Nubaeon/empirica/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Nubaeon/empirica/discussions)
- **Documentation:** [docs/](https://github.com/Nubaeon/empirica/tree/main/docs)

## 📜 License

MIT License - Maximum adoption, trust-aligned with Empirica's transparency principles.

See [LICENSE](LICENSE) for details.

---

**Built with genuine epistemic transparency** 🧠✨