# Empirica Documentation

**Current Version:** 1.0.6
**Status:** Production Ready

---

## Quick Navigation

### 📖 Getting Started

**Start here for accurate, up-to-date information:**

- **[01_START_HERE.md](01_START_HERE.md)** - Complete getting started guide
- **[02_QUICKSTART_CLI.md](02_QUICKSTART_CLI.md)** - CLI workflow basics
- **[03_QUICKSTART_MCP.md](03_QUICKSTART_MCP.md)** - MCP integration guide
- **[04_INSTALLATION.md](04_INSTALLATION.md)** - Installation instructions
- **[05_EPISTEMIC_VECTORS_EXPLAINED.md](05_EPISTEMIC_VECTORS_EXPLAINED.md)** - Core concepts
- **[06_TROUBLESHOOTING.md](06_TROUBLESHOOTING.md)** - Common issues and solutions

### 🧠 Core Concepts

**Understand the "why" behind Empirica:**

- **[Epistemic Health Documentation](EPISTEMIC_HEALTH_DOCUMENTATION.md)** - Understanding epistemic vectors
- **[Epistemic Fact Checking Spec](EPISTEMIC_FACT_CHECKING_SPEC.md)** - Verification protocols
- **[Cascade Workflow](CASCADE_WORKFLOW.md)** - Core workflow patterns
- **[Complete Overview](EMPIRICA_COMPLETE_OVERVIEW.md)** - Comprehensive system overview

### 📚 Documentation Categories

#### [Reference Documentation](reference/) - Generated and curated technical references
- **[CLI Commands Reference](reference/CLI_COMMANDS_UNIFIED.md)** - Complete unified command reference
- **[Python API Reference](reference/api/)** - Modular API documentation by category:
  - **[Core Session Management](reference/api/core_session_management.md)** - Session and vector management
  - **[Goals & Tasks](reference/api/goals_tasks.md)** - Goal and task management
  - **[CASCADE Workflow](reference/api/cascade_workflow.md)** - Epistemic reasoning workflow
  - **[Project Management](reference/api/project_management.md)** - Project and handoff management
  - **[Investigation Tools](reference/api/investigation_tools.md)** - Investigation and branching tools
  - **[Epistemic Tracking](reference/api/epistemic_tracking.md)** - Epistemic state tracking
  - **[Knowledge Management](reference/api/knowledge_management.md)** - Knowledge artifacts and sources
  - **[System Utilities](reference/api/system_utilities.md)** - System and utility functions
- **[Database Schema Reference](reference/DATABASE_SCHEMA_UNIFIED.md)** - Complete unified schema documentation
- **[Epistemic Health Quick Reference](reference/EPISTEMIC_HEALTH_QUICK_REFERENCE.md)** - One-page reference card

#### [Architecture Documentation](architecture/) - System design and implementation details
- **[Complete Architecture](architecture/EMPIRICA_COMPLETE_ARCHITECTURE.md)** - Full system architecture
- **[System Overview](architecture/EMPIRICA_SYSTEM_OVERVIEW.md)** - High-level system view
- **[Storage Architecture](architecture/STORAGE_ARCHITECTURE_COMPLETE.md)** - Data persistence design
- **[Doc-Code Intelligence](architecture/DOC_CODE_INTELLIGENCE.md)** - Documentation integrity system
- **[Metacognitive Cascade](reference/epistemic/METACOGNITIVE_CASCADE.md)** - Epistemic workflow engine

#### [Guides](guides/) - Step-by-step instructions and best practices
- **[Auto Issue Capture Guide](guides/AUTO_ISSUE_CAPTURE_GUIDE.md)** - Issue tracking automation
- **[Bootstrap Output Guide](guides/BOOTSTRAP_OUTPUT_VISUAL_GUIDE.md)** - Understanding project bootstrap
- **[MCP Configuration](guides/MCP_CONFIGURATION_UPDATED.md)** - MCP setup and configuration
- **[Session-Goal Workflow](guides/SESSION_GOAL_WORKFLOW.md)** - Managing sessions and goals
- **[First Time Setup](guides/FIRST_TIME_SETUP.md)** - Initial configuration guide

#### [Integrations](integrations/) - External system integration guides
- **[BEADS Git Bridge](integrations/BEADS_GIT_BRIDGE.md)** - Git integration for AI agents
- **[BEADS Integration Design](integrations/BEADS_INTEGRATION_DESIGN.md)** - Integration architecture

#### [System Prompts](../docs/system-prompts/) - AI agent configuration and prompts
- **[Canonical System Prompt](../docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md)** - Core AI behavior
- **[Claude Configuration](../docs/system-prompts/CLAUDE.md)** - Claude-specific setup
- **[Gemini Configuration](../docs/system-prompts/GEMINI.md)** - Gemini-specific setup

### 🔍 Discovery

- **[Semantic Index](SEMANTIC_INDEX.yaml)** - Find docs by concept, tag, or question
- **[Documentation Index](reference/EMPIRICA_DOCUMENTATION_INDEX.md)** - Complete documentation map

---

## Documentation Structure

```
docs/
├── 01_START_HERE.md                  # Getting started
├── 02_QUICKSTART_CLI.md              # CLI basics
├── 03_QUICKSTART_MCP.md              # MCP integration
├── 04_INSTALLATION.md                # Installation
├── 05_EPISTEMIC_VECTORS_EXPLAINED.md # Core concepts
├── 06_TROUBLESHOOTING.md             # Troubleshooting
├── README.md                         # This file
├── SEMANTIC_INDEX.yaml               # Concept search
│
├── reference/                        # Technical references
│   ├── CLI_COMMANDS_COMPLETE.md      # Complete command reference
│   ├── PYTHON_API_GENERATED.md       # Python API
│   ├── DATABASE_SCHEMA_GENERATED.md  # Database schema
│   ├── EPISTEMIC_HEALTH_QUICK_REFERENCE.md # Quick reference
│   └── epistemic/                    # Epistemic theory
│       ├── UNIFIED_EPISTEMIC_THEORY.md
│       ├── UNIFIED_EPISTEMIC_VECTORS.md
│       └── METACOGNITIVE_CASCADE.md
│
├── architecture/                     # System design
│   ├── EMPIRICA_COMPLETE_ARCHITECTURE.md
│   ├── DOC_CODE_INTELLIGENCE.md
│   └── ...
│
├── guides/                           # Step-by-step guides
│   ├── AUTO_ISSUE_CAPTURE_GUIDE.md
│   ├── BOOTSTRAP_OUTPUT_VISUAL_GUIDE.md
│   └── ...
│
├── integrations/                     # External integrations
│   └── BEADS_GIT_BRIDGE.md
│
├── system-prompts/                   # AI configuration (in parent dir)
│
└── _archive/                         # Archived documentation
    └── ...
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

### For New Features:

1. Implement in code
2. Update relevant documentation
3. Add examples and use cases

---

## Documentation Integrity

Check documentation integrity:

```bash
empirica project-bootstrap --check-integrity --output json
```

**Current status:**
- Generated docs: 100% accurate (auto-synced with code)
- Conceptual docs: Maintained with code changes
- Overall: Production ready

---

## Support

**Questions about the system?**
- Read: [Canonical System Prompt](../system-prompts/CANONICAL_SYSTEM_PROMPT.md) (comprehensive)
- Check: Generated reference docs (100% accurate)
- Search: [Semantic Index](SEMANTIC_INDEX.yaml) (find by concept)

**Found a bug in docs?**
- If in generated docs → bug is in source code, fix there
- If in conceptual docs → edit directly and submit PR

---

**System Status:** Production Ready ✅
**Documentation Coverage:** Complete
**Maintenance:** Active
