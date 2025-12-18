# Empirica Canonical Directory Structure

**Version:** 4.0  
**Date:** 2025-12-18  
**Purpose:** Authoritative reference for Empirica's workspace structure, reflecting December 2025 cleanup  
**Audience:** AI agents, developers, contributors

---

## Overview

This document is the **single source of truth** for:
- Where files are located in the Empirica workspace
- What each directory/file does
- How components integrate
- Where to add new functionality
- Import paths and dependencies

**Last major cleanup:** December 18, 2025 (moved dev artifacts out, organized slides, added vision module)

---

## Root Directory Structure (Production Workspace)

```
empirica/                                  # Clean production workspace
├── empirica/                              # Core Python package
├── docs/                                  # Documentation (gradual learning path)
├── tests/                                 # Test suite
├── examples/                              # Working examples
├── slides/                                # Presentation assets ⭐ NEW
├── scripts/                               # Production utility scripts
├── mcp_local/                             # MCP server implementations
├── dev_scripts/                           # Development utilities
├── packaging/                             # Distribution packaging
├── forgejo-plugin-empirica/               # Forgejo integration (optional)
├── skill_extractor/                       # Skill extraction tools
├── project_skills/                        # Project-specific skills
├── pydantic_tools/                        # Pydantic utilities
├── vsif-poc/                              # VSIF proof of concept
├── workspace/                             # Workspace utilities
│
├── .empirica/                             # Runtime data (created on first use, gitignored)
├── .empirica_reflex_logs/                 # Reflex logs (gitignored)
│
├── README.md                              # Main entry point
├── CONTRIBUTING.md                        # Contribution guidelines
├── LICENSE                                # MIT license
├── AGENTS.md                              # AI agent specifications
├── DEV_ARTIFACTS_LOCATION.md              # Reference for historical artifacts
├── pyproject.toml                         # Modern Python package config
├── requirements.txt                       # Dependencies
├── pytest.ini                             # Test configuration
├── MANIFEST.in                            # Package manifest
├── Makefile                               # Build automation
├── Dockerfile                             # Container definition
└── docker-compose.yml                     # Multi-service orchestration
```

---

## 1. Core Package: `empirica/`

The main Python package containing all production functionality.

```
empirica/
├── core/                                  # Epistemic framework
├── cli/                                   # Command-line interface
├── data/                                  # Database & storage
├── vision/                                # Vision & content assessment ⭐ NEW
├── workflow/                              # CASCADE workflow (legacy structure)
├── api/                                   # REST API components
├── dashboard/                             # Web dashboard
├── plugins/                               # Plugin system
├── integration/                           # External integrations
├── integrations/                          # Integration modules
├── investigation/                         # Investigation system
├── reasoning/                             # Reasoning components
├── metrics/                               # Metrics & tracking
├── config/                                # Configuration
├── schemas/                               # Data schemas
├── utils/                                 # Utilities
├── components/                            # Shared components
└── __init__.py                            # Package initialization
```

### 1.1 Core Epistemic Framework: `empirica/core/`

**Purpose:** Self-assessment, CASCADE workflow, epistemic tracking

```
empirica/core/
├── canonical/                             # 13-vector assessment system
│   ├── canonical_epistemic_assessment.py  # LLM-powered self-assessment
│   ├── canonical_goal_orchestrator.py     # Goal generation & orchestration
│   ├── git_enhanced_reflex_logger.py      # Compressed git notes logging
│   ├── reflex_frame.py                    # Data structures (EpistemicAssessment, etc.)
│   └── reflex_logger.py                   # Legacy JSON logging
│
└── metacognitive_cascade/                 # CASCADE workflow
    ├── metacognitive_cascade.py           # Main workflow orchestrator
    ├── investigation_plugin.py            # User extension interface
    ├── investigation_strategy.py          # Domain-aware investigation
    └── mcp_aware_investigation.py         # MCP tool execution
```

**Key concepts:**
- **13 epistemic vectors:** engagement, know, do, context, clarity, coherence, signal, density, state, change, completion, impact, uncertainty
- **CASCADE phases:** PREFLIGHT → CHECK → INVESTIGATE → ACT → POSTFLIGHT
- **Git notes integration:** ~85% token reduction via compressed checkpoints

**Import examples:**
```python
from empirica.core.canonical import CanonicalEpistemicAssessor
from empirica.core.canonical import create_goal_orchestrator
from empirica.core.canonical import GitEnhancedReflexLogger
```

### 1.2 Command-Line Interface: `empirica/cli/`

**Purpose:** User-facing CLI commands, argument parsing, output formatting

```
empirica/cli/
├── main.py                                # Entry point (empirica command)
├── commands/                              # Command implementations
│   ├── session_commands.py                # session-create, sessions-list, etc.
│   ├── workflow_commands.py               # preflight, check, postflight, etc.
│   ├── goal_commands.py                   # goals-create, goals-add-subtask, etc.
│   ├── project_commands.py                # project-create, project-bootstrap, etc.
│   ├── checkpoint_commands.py             # checkpoint-create, checkpoint-load, etc.
│   └── ...
├── formatters/                            # Output formatting
│   ├── json_formatter.py                  # --output json
│   └── table_formatter.py                 # Human-readable tables
└── utils/                                 # CLI utilities
```

**Key feature:** AI-first JSON mode (stdin → JSON output)

**Example:**
```bash
echo '{"ai_id": "claude", "session_type": "development"}' | empirica session-create -
# Output: {"ok": true, "session_id": "uuid", ...}
```

### 1.3 Data Layer: `empirica/data/`

**Purpose:** SQLite database, session storage, project tracking

```
empirica/data/
├── session_database.py                    # SessionDatabase class (main API)
├── schema.sql                             # Database schema
├── migrations/                            # Schema migrations
│   ├── 001_initial_schema.sql
│   ├── 002_add_projects.sql
│   └── ...
└── models/                                # Data models (if using ORM)
```

**Key tables:**
- `sessions` - Session metadata
- `goals` - Goal hierarchy
- `subtasks` - Task breakdown
- `reflexes` - Epistemic assessments (PREFLIGHT, CHECK, POSTFLIGHT)
- `projects` - Project-level tracking
- `breadcrumbs` - Findings, unknowns, dead-ends
- `reference_docs` - Documentation references

**Import:**
```python
from empirica.data.session_database import SessionDatabase
db = SessionDatabase()
session_id = db.create_session(ai_id="my-agent")
```

### 1.4 Vision System: `empirica/vision/` ⭐ NEW

**Purpose:** Epistemic assessment of visual content (slides, websites, videos)

```
empirica/vision/
├── __init__.py                            # Package exports
├── slide_processor.py                     # OCR + epistemic scoring for slides
├── readable_translator.py                 # Human-friendly output (letter grades, etc.)
├── content_critic.py                      # Content improvement suggestions (planned)
└── multimodal_prompts.py                  # Prompt generation for GPT-4V/DALL-E (planned)
```

**Key capabilities:**
- OCR text extraction (tesseract)
- Visual element detection (OpenCV)
- Epistemic scoring (clarity, signal, density, impact)
- Human-readable study guides
- Content improvement prompts (in development)

**Usage:**
```bash
# Process slides
python -m empirica.vision.slide_processor "slides/ledger-*.png"

# Generate study guide
python -m empirica.vision.readable_translator \
    .empirica/slides/assessment_ledger-all.png.json
```

**Import:**
```python
from empirica.vision.slide_processor import SlideProcessor
from empirica.vision.readable_translator import ReadableTranslator
```

---

## 2. Documentation: `docs/`

**Structure:** Gradual learning path (numbered 01-16) + reference docs

```
docs/
├── 01_START_HERE.md                       # Entry point
├── 02_QUICKSTART_CLI.md                   # CLI quick start
├── 03_QUICKSTART_MCP.md                   # MCP integration
├── 04_INSTALLATION.md                     # Installation guide
├── 05_EPISTEMIC_VECTORS_EXPLAINED.md      # Vectors simplified (to be created)
├── 06_TROUBLESHOOTING.md                  # Common issues
├── 07_CASCADE_WORKFLOW.md                 # CASCADE explained (to be created)
├── 08-16 (to be created)                  # Advanced topics
│
├── EMPIRICA_EXPLAINED_SIMPLE.md           # Simple explanation
├── README.md                              # Documentation index
├── SEMANTIC_INDEX.yaml                    # Semantic search index
│
├── reference/                             # Technical references (no numbers)
│   ├── CANONICAL_DIRECTORY_STRUCTURE.md   # This file
│   ├── CLI_COMMANDS_COMPLETE.md           # All CLI commands
│   ├── DATABASE_SCHEMA_GENERATED.md       # Database schema
│   ├── MCP_SERVER_REFERENCE.md            # MCP server API
│   ├── PYTHON_API_GENERATED.md            # Python API reference
│   ├── CONFIGURATION_REFERENCE.md         # Config file format
│   └── STORAGE_LOCATIONS.md               # Where data is stored
│
├── guides/                                # How-to guides
│   └── FIRST_TIME_SETUP.md                # Initial setup
│
├── architecture/                          # Architecture docs
├── integrations/                          # Integration guides
└── system-prompts/                        # System prompts for AI agents
    ├── CANONICAL_SYSTEM_PROMPT.md         # Main system prompt
    └── ...
```

**Design principle:** Gradual complexity (start simple, add depth progressively)

---

## 3. Presentation Assets: `slides/` ⭐ NEW

**Purpose:** Source materials for documentation and presentations

```
slides/
├── README.md                              # Slide documentation
├── ledger-01.png ... ledger-15.png        # Epistemic Ledger deck (15 slides)
├── architecture-01.png ... architecture-13.png  # Architecture deck (13 slides)
└── pdfs/                                  # PDF source documents
    ├── The_AI_Epistemic_Ledger.pdf
    └── Empirica_Reliable_AI_Architecture.pdf
```

**Epistemic assessments available:**
- `.empirica/slides/assessment_ledger-all.png.json`
- `.empirica/slides/assessment_architecture-all.png.json`
- `.empirica/slides/summary_*.md`

**Note:** Slides are versioned for testing/validation purposes

---

## 4. Test Suite: `tests/`

**Purpose:** Automated testing (pytest)

```
tests/
├── unit/                                  # Unit tests
│   ├── test_epistemic_assessment.py
│   ├── test_cascade_workflow.py
│   ├── test_session_database.py
│   └── ...
├── integration/                           # Integration tests
│   ├── test_cli_workflow.py
│   ├── test_mcp_integration.py
│   └── ...
├── fixtures/                              # Test data
└── conftest.py                            # Pytest configuration
```

**Run tests:**
```bash
pytest tests/
pytest tests/unit/
pytest tests/integration/
```

---

## 5. MCP Server: `mcp_local/`

**Purpose:** Model Context Protocol server implementation

```
mcp_local/
├── empirica_mcp_server.py                 # Main MCP server
└── tools/                                 # MCP tool implementations (if separated)
```

**Usage:**
- Claude Desktop integration
- Cline integration  
- Other MCP-compatible tools

**Configuration:** `docs/EMPIRICA_MCP_CONFIG.json`

---

## 6. Runtime Data: `.empirica/` (gitignored)

**Purpose:** User data, session storage, cached assessments

```
.empirica/
├── sessions/                              # Session data
│   └── {session_id}/
│       ├── metadata.json
│       ├── reflexes/                      # Epistemic assessments
│       └── ...
├── projects/                              # Project data
├── slides/                                # Processed slide assessments ⭐ NEW
│   ├── assessment_*.json
│   └── summary_*.md
├── credentials.yaml                       # API keys (user creates)
└── empirica.db                            # SQLite database
```

**Note:** This directory is created on first use and excluded from git

---

## 7. Import Patterns

### Common Imports:
```python
# Core epistemic framework
from empirica.core.canonical import CanonicalEpistemicAssessor
from empirica.core.canonical import create_goal_orchestrator
from empirica.core.metacognitive_cascade import MetacognitiveCascade

# Database
from empirica.data.session_database import SessionDatabase

# Vision system
from empirica.vision.slide_processor import SlideProcessor
from empirica.vision.readable_translator import ReadableTranslator

# CLI (for custom commands)
from empirica.cli.commands import session_commands
```

### Database Usage:
```python
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()

# Create session
session_id = db.create_session(ai_id="my-agent")

# Create goal
goal_id = db.create_goal(
    session_id=session_id,
    objective="Implement feature X"
)

# Log finding
db.log_finding(
    session_id=session_id,
    project_id=project_id,
    finding="Discovered that..."
)

db.close()
```

---

## 8. Where to Add New Functionality

| Feature Type | Location | Example |
|-------------|----------|---------|
| New CLI command | `empirica/cli/commands/` | `my_commands.py` |
| New epistemic vector | `empirica/core/canonical/` | Update `reflex_frame.py` |
| New investigation strategy | `empirica/investigation/` | Implement `InvestigationStrategy` |
| New content processor | `empirica/vision/` | `video_processor.py` |
| New MCP tool | `mcp_local/` | Add tool to server |
| New plugin | `empirica/plugins/` | Implement plugin interface |
| New documentation | `docs/` | Follow numbering convention |

---

## 9. Key Files Reference

| File | Purpose |
|------|---------|
| `empirica/core/canonical/canonical_epistemic_assessment.py` | LLM-powered self-assessment |
| `empirica/data/session_database.py` | Main database API |
| `empirica/cli/main.py` | CLI entry point |
| `empirica/vision/slide_processor.py` | Vision assessment engine |
| `docs/SEMANTIC_INDEX.yaml` | Documentation search index |
| `docs/reference/CLI_COMMANDS_COMPLETE.md` | Complete CLI reference |
| `.empirica/empirica.db` | SQLite database (runtime) |

---

## 10. Changes from Version 3.0

**December 2025 Cleanup:**

✅ **Added:**
- `slides/` directory with presentation assets
- `empirica/vision/` module for content assessment
- Human-readable vision output system
- DEV_ARTIFACTS_LOCATION.md for historical reference

✅ **Workspace cleanup:**
- Root directory: 60+ files → 12 essential files
- Organized presentation materials
- Cleaned directory structure

✅ **Updated:**
- This document (CANONICAL_DIRECTORY_STRUCTURE.md)
- Documentation structure (gradual learning path 01-16)

---

## 11. Quick Reference

**Start here:**
- Read: `docs/01_START_HERE.md`
- Install: `docs/04_INSTALLATION.md`
- Quick start: `docs/02_QUICKSTART_CLI.md`

**For developers:**
- Structure: This document
- API: `docs/reference/PYTHON_API_GENERATED.md`
- CLI: `docs/reference/CLI_COMMANDS_COMPLETE.md`
- Database: `docs/reference/DATABASE_SCHEMA_GENERATED.md`

**For AI agents:**
- System prompt: `docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md`
- MCP config: `docs/EMPIRICA_MCP_CONFIG.json`
- Agent specs: `AGENTS.md`

---

**Version History:**
- v4.0 (2025-12-18): December cleanup, vision module, streamlined workspace
- v3.0 (2024): Previous version
