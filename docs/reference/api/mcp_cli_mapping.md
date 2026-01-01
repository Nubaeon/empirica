# MCP ↔ CLI Command Mapping

**Framework Version:** 1.2.1
**Last Updated:** 2025-12-27
**Status:** Production Ready

---

## Overview

This document provides the complete mapping between MCP (Model Context Protocol) tools and CLI commands. The architecture follows the principle that MCP tools are **thin wrappers** around CLI commands, with the CLI serving as the single source of truth.

### Architecture Principle

- **MCP tools** = Convenience wrappers for AI coding assistants (Claude Code, Cursor, etc.)
- **CLI commands** = Full-featured interface for all use cases
- **Mapping:** MCP tools map 1:1 to CLI commands as thin wrappers (no duplicate logic)

---

## Current Status

| Interface | Tool/Command Count | Status |
|-----------|-------------------|--------|
| **MCP Tools** | 40 | ✅ Complete |
| **CLI Commands** | 86 | ⚠️ Some missing MCP wrappers |

**Gap:** ~46 CLI commands lack MCP tools (see "Missing MCP Tools" section below)

---

## Complete MCP → CLI Mapping

### Stateless Tools (MCP-Only, No CLI Equivalent)

| MCP Tool | Description | Handler |
|----------|-------------|---------|
| `get_empirica_introduction` | Framework introduction | Direct (stateless) |
| `get_workflow_guidance` | CASCADE phase guidance | Direct (stateless) |
| `cli_help` | CLI help text | Direct (stateless) |

---

### CASCADE Workflow

| MCP Tool | CLI Command | Notes |
|----------|-------------|-------|
| `session_create` | `session-create` | ✅ Maps 1:1 |
| `execute_preflight` | `preflight --prompt-only` | ✅ Non-blocking prompt return |
| `submit_preflight_assessment` | `preflight-submit` | ✅ Maps 1:1 |
| `execute_check` | `check` | ✅ Maps 1:1 |
| `submit_check_assessment` | `check-submit` | ✅ Maps 1:1 |
| `execute_postflight` | *(Direct handler)* | ⚠️ Returns context programmatically, no CLI equivalent |
| `submit_postflight_assessment` | `postflight-submit` | ✅ Maps 1:1 |

**Note:** `execute_postflight` is handled directly in MCP (returns session context without PREFLIGHT baseline to prevent anchoring). AI then calls `submit_postflight_assessment`.

---

### Goal/Task Management

| MCP Tool | CLI Command | Notes |
|----------|-------------|-------|
| `create_goal` | `goals-create` | ⚠️ Direct handler (AI-centric, no CLI routing) |
| `add_subtask` | `goals-add-subtask` | ✅ Maps 1:1 |
| `complete_subtask` | `goals-complete-subtask` | ✅ Maps 1:1 (uses `task-id` not `subtask-id`) |
| `get_goal_progress` | `goals-progress` | ✅ Maps 1:1 |
| `get_goal_subtasks` | `goals-get-subtasks` | ✅ Maps 1:1 |
| `list_goals` | `goals-list` | ✅ Maps 1:1 |

---

### Session Management

| MCP Tool | CLI Command | Notes |
|----------|-------------|-------|
| `get_epistemic_state` | `sessions-show` | ✅ Maps 1:1 |
| `get_session_summary` | `sessions-show --verbose` | ✅ Maps 1:1 with flag |
| `get_calibration_report` | `calibration` | ⚠️ Direct handler (Python, not CLI routing) |
| `resume_previous_session` | `sessions-resume` | ✅ Maps 1:1 |

---

### Checkpoint System

| MCP Tool | CLI Command | Notes |
|----------|-------------|-------|
| `create_git_checkpoint` | `checkpoint-create` | ✅ Maps 1:1 |
| `load_git_checkpoint` | `checkpoint-load` | ✅ Maps 1:1 |
| `list_checkpoints` | `checkpoint-list` | ✅ Maps 1:1 |
| `diff_checkpoints` | `checkpoint-diff` | ✅ Maps 1:1 |
| `sign_checkpoint` | `checkpoint-sign` | ✅ Maps 1:1 |
| `verify_checkpoint` | `checkpoint-verify` | ✅ Maps 1:1 |
| `list_checkpoint_signatures` | `checkpoint-signatures` | ✅ Maps 1:1 |

---

### Handoff Reports

| MCP Tool | CLI Command | Notes |
|----------|-------------|-------|
| `create_handoff_report` | `handoff-create` | ✅ Maps 1:1 |
| `query_handoff_reports` | `handoff-query` | ✅ Maps 1:1 |

---

### Investigation Tools

| MCP Tool | CLI Command | Notes |
|----------|-------------|-------|
| `start_investigation` | `investigate` | ✅ Maps 1:1 |
| `create_investigation_branch` | `investigate-create-branch` | ✅ Maps 1:1 |
| `checkpoint_investigation_branch` | `investigate-checkpoint-branch` | ✅ Maps 1:1 |
| `merge_investigation_branches` | `investigate-merge-branches` | ✅ Maps 1:1 |

---

### Knowledge Management

| MCP Tool | CLI Command | Notes |
|----------|-------------|-------|
| `log_finding` | `finding-log` | ✅ Maps 1:1 |
| `log_unknown` | `unknown-log` | ✅ Maps 1:1 |
| `log_dead_end` | `deadend-log` | ✅ Maps 1:1 |
| `add_reference_doc` | `refdoc-add` | ✅ Maps 1:1 |
| `log_mistake` | `mistake-log` | ✅ Maps 1:1 |
| `query_mistakes` | `mistake-query` | ✅ Maps 1:1 |

---

### Issue Management

| MCP Tool | CLI Command | Notes |
|----------|-------------|-------|
| `list_issues` | `issue-list` | ✅ Maps 1:1 |
| `show_issue` | `issue-show` | ✅ Maps 1:1 |
| `handoff_issue` | `issue-handoff` | ✅ Maps 1:1 |
| `resolve_issue` | `issue-resolve` | ✅ Maps 1:1 |
| `export_issue` | `issue-export` | ✅ Maps 1:1 |
| `issue_stats` | `issue-stats` | ✅ Maps 1:1 |

---

### Project Management

| MCP Tool | CLI Command | Notes |
|----------|-------------|-------|
| `create_project` | `project-create` | ✅ Maps 1:1 |
| `list_projects` | `project-list` | ✅ Maps 1:1 |
| `bootstrap_project` | `project-bootstrap` | ✅ Maps 1:1 |
| `create_project_handoff` | `project-handoff` | ✅ Maps 1:1 |
| `init_workspace` | `workspace-init` | ✅ Maps 1:1 |
| `map_workspace` | `workspace-map` | ✅ Maps 1:1 |
| `overview_workspace` | `workspace-overview` | ✅ Maps 1:1 |

---

### Identity Management

| MCP Tool | CLI Command | Notes |
|----------|-------------|-------|
| `create_identity` | `identity-create` | ✅ Maps 1:1 |
| `list_identities` | `identity-list` | ✅ Maps 1:1 |
| `export_identity` | `identity-export` | ✅ Maps 1:1 |
| `verify_identity` | `identity-verify` | ✅ Maps 1:1 |

---

### Monitoring & Performance

| MCP Tool | CLI Command | Notes |
|----------|-------------|-------|
| `start_monitoring` | `monitor` | ✅ Maps 1:1 |
| `check_drift` | `check-drift` | ✅ Maps 1:1 |
| `efficiency_report` | `efficiency-report` | ✅ Maps 1:1 |

---

### Skills & Utilities

| MCP Tool | CLI Command | Notes |
|----------|-------------|-------|
| `suggest_skills` | `skill-suggest` | ✅ Maps 1:1 |
| `fetch_skill` | `skill-fetch` | ✅ Maps 1:1 |

---

## Missing MCP Tools

The following CLI commands currently lack MCP tool equivalents:

### Session Management
- `sessions-list` - List all sessions
- `sessions-export` - Export session data
- `session-snapshot` - Create session snapshot
- `memory-compact` - Compact session memory

### CASCADE Workflow
- `workflow` - Execute complete CASCADE workflow
- `preflight-submit` - Submit preflight assessment
- `check-submit` - Submit check assessment
- `postflight-submit` - Submit postflight assessment

### Goals & Tasks
- `goals-claim` - Claim a goal for work
- `goals-ready` - List ready goals
- `goals-discover` - Discover new goals
- `goals-resume` - Resume work on a goal
- `goals-complete` - Complete a goal

### Investigation Tools
- `investigate-log` - Log investigation activities

### Project Management
- `project-init` - Initialize project
- `project-search` - Search projects
- `project-embed` - Create project embeddings
- `doc-check` - Check documentation quality

### Checkpoint System
- `checkpoint-load` - Load checkpoint (duplicate with create_git_checkpoint?)
- `checkpoint-list` - List checkpoints (duplicate with list_checkpoints?)

### Knowledge Management
- `act-log` - Log action taken

### Utilities
- `goal-analysis` - Analyze goal completion patterns
- `log-token-saving` - Log token savings
- `config` - Configuration management
- `performance` - Performance metrics
- `vision` - Vision processing
- `chat` - Chat interface

### Epistemics
- `epistemics-list` - List epistemic assessments
- `epistemics-show` - Show detailed assessment

---

## Direct Handlers (No CLI Routing)

Some MCP tools handle logic directly in Python rather than routing to CLI:

### Rationale for Direct Handlers
- **Epistemic complexity:** Goal scope vectors, calibration analysis require complex Python logic
- **AI-specific:** POSTFLIGHT baseline hiding (prevents anchoring) is MCP-specific concern
- **Performance:** Direct Python faster than CLI subprocess for simple lookups

### Direct Handler Tools
- `execute_postflight` - Returns session context programmatically
- `create_goal` - AI-centric goal creation
- `get_calibration_report` - Complex calibration analysis

---

## Architecture Decision Records

### Why Direct Handlers?
**Decision:** Some MCP tools bypass CLI routing and handle logic directly in Python.

**Rationale:**
- **Epistemic complexity:** Goal scope vectors, calibration analysis require complex Python logic
- **AI-specific:** POSTFLIGHT baseline hiding (prevents anchoring) is MCP-specific concern
- **Performance:** Direct Python faster than CLI subprocess for simple lookups

**Trade-off:** Increases code duplication, but necessary for AI-centric features.

### Why MCP Tool Count < CLI Command Count?
**Decision:** Not all CLI commands need MCP wrappers.

**Rationale:**
- MCP targets **AI coding assistants** (Claude Code, Cursor) - not all CLI commands relevant
- Some commands are **admin/setup** (not needed during coding sessions)
- Some commands are **advanced/experimental** (wait for user demand before adding)

**When to add MCP tool:**
- Core workflow command (CASCADE, goals, sessions)
- Frequently used by AI agents
- Simplifies AI interaction (reduces token usage)

---

## Future Improvements

1. **Auto-generate MCP tools from CLI definitions** (reduce duplication)
2. **Unified parameter schema** (share between MCP and CLI)
3. **MCP tool usage analytics** (identify which tools need CLI equivalents)
4. **Bidirectional sync** (CLI changes auto-update MCP schemas)

---

## References

- MCP Server: `empirica-mcp/empirica_mcp/server.py`
- CLI Core: `empirica/cli/cli_core.py`
- Tool Mapping: `build_cli_command()` in MCP server (line 1327)
- Parameter Mapping: `arg_map` in MCP server (line 1396)