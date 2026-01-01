# Empirica Documentation

**Current Version:** 1.2.1
**Status:** Production Ready

---

## Quick Navigation

### 📖 Getting Started

- **[01_START_HERE.md](01_START_HERE.md)** - Complete getting started guide
- **[04_INSTALLATION.md](04_INSTALLATION.md)** - Installation instructions
- **[06_TROUBLESHOOTING.md](06_TROUBLESHOOTING.md)** - Common issues and solutions
- **[EMPIRICA_EXPLAINED_SIMPLE.md](EMPIRICA_EXPLAINED_SIMPLE.md)** - Plain-language overview

### 🧠 Core Concepts

- **[NOETIC_PRAXIC_FRAMEWORK.md](architecture/NOETIC_PRAXIC_FRAMEWORK.md)** - Understanding the dual-phase workflow
- **[CASCADE Workflow](architecture/CHECK_SEMANTICS_FORMALIZATION.md)** - Core workflow patterns
- **[Epistemic Vectors](architecture/EPISTEMIC_VECTOR_INTERPRETER.md)** - 13-dimensional vector space

### 📚 Documentation Categories

#### [Reference Documentation](reference/)
- **[CLI Commands Reference](reference/CLI_COMMANDS_UNIFIED.md)** - Complete unified command reference
- **[Python API Reference](reference/api/)** - Modular API documentation
- **[Database Schema Reference](reference/DATABASE_SCHEMA_UNIFIED.md)** - Complete schema documentation

#### [Architecture Documentation](architecture/)
- **[Storage Architecture](architecture/STORAGE_ARCHITECTURE_COMPLETE.md)** - Data persistence design
- **[CLI Design Philosophy](architecture/CLI_DESIGN_PHILOSOPHY.md)** - Context-aware architecture
- **[Memory Compact Spec](architecture/MEMORY_COMPACT_SPEC.md)** - Session continuity

#### [Guides](guides/)
- **[First Time Setup](guides/FIRST_TIME_SETUP.md)** - Initial configuration guide
- **[Session-Goal Workflow](guides/SESSION_GOAL_WORKFLOW.md)** - Managing sessions and goals
- **[MCP Installation](guides/MCP_INSTALLATION.md)** - MCP setup and configuration
- **[Auto Issue Capture](guides/AUTO_ISSUE_CAPTURE_GUIDE.md)** - Issue tracking automation
- **[Multi-Session Learning](guides/MULTI_SESSION_LEARNING.md)** - Cross-session knowledge

#### [Integrations](integrations/)
- **[BEADS Git Bridge](integrations/BEADS_GIT_BRIDGE.md)** - Git integration for AI agents
- **[BEADS Integration Design](integrations/BEADS_INTEGRATION_DESIGN.md)** - Integration architecture

#### [System Prompts](system-prompts/)
- **[CANONICAL_CORE.md](system-prompts/CANONICAL_CORE.md)** - AI-agnostic source of truth
- **[CLAUDE.md](system-prompts/CLAUDE.md)** - Claude-specific prompt
- **[Architecture README](system-prompts/README.md)** - Multi-AI prompt management

### 🔍 Discovery

- **[Semantic Index](SEMANTIC_INDEX.yaml)** - Find docs by concept, tag, or question
- **[Feature Status](FEATURE_STATUS.md)** - Current feature implementation status

---

## Documentation Structure

```
docs/
├── 01_START_HERE.md                  # Getting started
├── 04_INSTALLATION.md                # Installation
├── 06_TROUBLESHOOTING.md             # Troubleshooting
├── EMPIRICA_EXPLAINED_SIMPLE.md      # Plain-language overview
├── FEATURE_STATUS.md                 # Feature status
├── README.md                         # This file
├── SEMANTIC_INDEX.yaml               # Concept search
│
├── reference/                        # Technical references
│   ├── CLI_COMMANDS_UNIFIED.md       # CLI reference
│   ├── DATABASE_SCHEMA_UNIFIED.md    # Database schema
│   └── api/                          # Python API docs
│
├── architecture/                     # System design
│   ├── NOETIC_PRAXIC_FRAMEWORK.md    # Dual-phase workflow
│   ├── STORAGE_ARCHITECTURE_COMPLETE.md
│   └── ...
│
├── guides/                           # Step-by-step guides
│   ├── FIRST_TIME_SETUP.md
│   ├── SESSION_GOAL_WORKFLOW.md
│   └── ...
│
├── integrations/                     # External integrations
│   └── BEADS_*.md
│
├── system-prompts/                   # AI configuration
│   ├── CANONICAL_CORE.md             # Source of truth
│   ├── CLAUDE.md, QWEN.md, etc.      # Model-specific
│   └── model_deltas/                 # Model additions
│
└── _archive/                         # Archived documentation
```

---

## Contributing to Documentation

### For Generated Docs (CLI, API, Schema):

**Don't edit manually!** They're auto-generated.

Instead:
1. Make changes to the source code
2. Regenerate docs with scripts in `dev_scripts/doc_regeneration/`
3. Commit both code + generated docs

### For Conceptual Docs:

Edit freely! These explain concepts, philosophy, and design decisions.

### For System Prompts:

1. Edit `system-prompts/CANONICAL_CORE.md` for all AIs
2. Edit `system-prompts/model_deltas/<model>.md` for specific AIs
3. Run `python3 scripts/sync_system_prompts.py` to regenerate

---

## Support

**Questions about the system?**
- Read: [Canonical Core Prompt](system-prompts/CANONICAL_CORE.md)
- Check: [CLI Commands Reference](reference/CLI_COMMANDS_UNIFIED.md)
- Search: [Semantic Index](SEMANTIC_INDEX.yaml)

**Found a bug in docs?**
- If in generated docs → bug is in source code, fix there
- If in conceptual docs → edit directly and submit PR

---

**System Status:** Production Ready ✅
**Documentation Coverage:** Active maintenance
**Version:** 1.2.1
