# MCP Tools ↔ CLI Commands Mapping

**Last Updated:** 2025-12-20
**Purpose:** Ensure consistency between MCP server (IDE/GUI) and CLI (terminal/scripts)

---

## Architecture Principle

**MCP is for IDE/GUI, CLI for everything else**

- **MCP tools** = Convenience wrappers for AI coding assistants (Claude Code, Cursor, etc.)
- **CLI commands** = Full-featured interface for all use cases
- **Mapping:** MCP tools should map 1:1 to CLI commands (thin wrapper, no duplicate logic)

---

## Tool Count Summary

| Interface | Tool/Command Count | Status |
|-----------|-------------------|--------|
| **MCP Tools** | 40 | ✅ Complete |
| **CLI Commands** | ~60+ | ⚠️ Missing MCP wrappers for some |

**Gap:** ~20 CLI commands lack MCP tools (see "Missing MCP Tools" section below)

---

## Complete MCP → CLI Mapping

### Stateless Tools (MCP-Only, No CLI)

| MCP Tool | Description | Handler |
|----------|-------------|---------|
| `get_empirica_introduction` | Framework intro | Direct (stateless) |
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
| `execute_postflight` | *(Direct handler)* | ⚠️ Returns context programmatically, no CLI equiv |
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

---

### Handoff Reports

| MCP Tool | CLI Command | Notes |
|----------|-------------|-------|
| `create_handoff_report` | `handoff-create` | ✅ Maps 1:1 |
| `query_handoff_reports` | `handoff-query` | ✅ Maps 1:1 |

---

### Cross-AI Coordination (Phase 1)

| MCP Tool | CLI Command | Notes |
|----------|-------------|-------|
| `discover_goals` | `goals-discover` | ✅ Maps 1:1 |
| `resume_goal` | `goals-resume` | ✅ Maps 1:1 |

---

### Mistakes Tracking

| MCP Tool | CLI Command | Notes |
|----------|-------------|-------|
| `log_mistake` | `mistake-log` | ✅ Maps 1:1 |
| `query_mistakes` | `mistake-query` | ✅ Maps 1:1 |

---

### Cryptographic Trust (Phase 2)

| MCP Tool | CLI Command | Notes |
|----------|-------------|-------|
| `create_identity` | `identity-create` | ✅ Maps 1:1 |
| `list_identities` | `identity-list` | ✅ Maps 1:1 |
| `export_public_key` | `identity-export` | ✅ Maps 1:1 |
| `verify_signature` | `identity-verify` | ✅ Maps 1:1 |

---

### Project-Level Tracking

| MCP Tool | CLI Command | Notes |
|----------|-------------|-------|
| `project_bootstrap` | `project-bootstrap` | ✅ Maps 1:1 |
| `finding_log` | `finding-log` | ✅ Maps 1:1 |
| `unknown_log` | `unknown-log` | ✅ Maps 1:1 |
| `deadend_log` | `deadend-log` | ✅ Maps 1:1 |
| `refdoc_add` | `refdoc-add` | ✅ Maps 1:1 |

---

### Vision Analysis

| MCP Tool | CLI Command | Notes |
|----------|-------------|-------|
| `vision_analyze` | `vision-analyze` | ✅ Maps 1:1 |
| `vision_log` | `vision-log` | ✅ Maps 1:1 |

---

### Metacognitive Edit Guard

| MCP Tool | CLI Command | Notes |
|----------|-------------|-------|
| `edit_with_confidence` | *(Direct handler)* | ⚠️ Python implementation, no CLI equiv |

---

## Missing MCP Tools (CLI Commands Without MCP Wrappers)

These CLI commands exist but lack MCP tool wrappers:

### Configuration & Setup
- `config` - Configuration management
- `project-init` - Initialize new project
- `project-embed` - Embed project documentation for semantic search
- `onboard` - Interactive onboarding

### Session Management
- `sessions-list` - List all sessions
- `sessions-pause` - Pause active session
- `sessions-delete` - Delete session

### Advanced Workflow
- `workflow` - Execute full preflight→work→postflight
- `investigate` - Investigate file/directory/concept

### Investigation Branches
- `create-branch` - Create investigation branch
- `checkpoint-branch` - Checkpoint investigation branch
- `merge-branches` - Merge investigation branches

### Goal Management
- `goal-analysis` - Analyze goal feasibility
- `goal-claim` - Claim unclaimed goal
- `goal-complete` - Complete entire goal
- `goals-ready` - Check if goals are ready

### Decision & Monitoring
- `decision` - Decision point tracking
- `monitor` - Real-time monitoring
- `sentinel` - Route to Sentinel decision system

### Skills
- `skill-suggest` - Suggest skills for task
- `skill-fetch` - Fetch and normalize skill

### Documentation
- `ask` - Query documentation semantically
- `doc-planner` - Plan documentation structure

### Utility & Performance
- `performance` - Performance analysis/benchmarks
- `component` - Component analysis

### Epistemic Search
- `epistemics-search` - Search epistemic trajectories (Qdrant)
- `epistemics-stats` - Aggregate epistemic learning stats

---

## Inconsistencies & Issues

### ⚠️ Parameter Name Mismatches

MCP uses snake_case, CLI uses kebab-case. Mapping handled in `build_cli_command()`:

| MCP Parameter | CLI Flag | Example |
|---------------|----------|---------|
| `session_id` | `--session-id` | All commands |
| `goal_id` | `--goal-id` | Goal commands |
| `task_id` | `--task-id` | `goals-complete-subtask` |
| `bootstrap_level` | `--bootstrap-level` | `session-create` |
| `remaining_unknowns` | `--remaining-unknowns` | `check` |
| `confidence_to_proceed` | `--confidence` | `check` |
| `root_cause_vector` | `--root-cause-vector` | `mistake-log` |
| `why_wrong` | `--why-wrong` | `mistake-log` |
| `cost_estimate` | `--cost-estimate` | `mistake-log` |
| `key_findings` | `--key-findings` | `handoff-create` |
| `artifacts_created` | `--artifacts` | `handoff-create` |

### ⚠️ Direct Handlers (Bypass CLI)

Some MCP tools handle logic directly instead of routing to CLI:

1. **`create_goal`** - Direct Python handler (AI-centric scope conversion)
2. **`execute_postflight`** - Returns context without baseline (prevents anchoring)
3. **`get_calibration_report`** - Direct Python handler
4. **`edit_with_confidence`** - Metacognitive edit verification (Python only)

**Rationale:** These tools require AI-specific logic (epistemic vector handling, calibration analysis) that's complex to express in CLI flags.

### ⚠️ Skipped Arguments

Some MCP parameters are ignored when mapping to CLI:

| Command | Skipped Parameter | Reason |
|---------|------------------|--------|
| `session-create` | `session_type` | Not used by CLI |
| `check-submit` | `confidence_to_proceed` | CLI uses `decision` instead |
| `checkpoint-create` | `vectors` | Should be in `metadata` |
| `project-bootstrap` | `mode` | MCP-only (future feature) |

---

## Recommended Actions

### 🔴 High Priority

1. **Add MCP wrappers for missing CLI commands** (especially):
   - `sessions-list` - Essential for session management
   - `project-init` - Project setup workflow
   - `epistemics-search` - Qdrant semantic search
   - `epistemics-stats` - Learning analytics

2. **Document why some tools use direct handlers**
   - Clarify when to bypass CLI (epistemic complexity, AI-specific logic)
   - Ensure direct handlers maintain parity with CLI when applicable

### 🟡 Medium Priority

3. **Standardize parameter naming**
   - Consider accepting both snake_case and kebab-case in CLI
   - OR enforce consistent conversion in MCP server

4. **Add integration tests**
   - Verify MCP tool → CLI command mapping for each tool
   - Test parameter conversion edge cases

### 🟢 Low Priority

5. **Add CLI equivalents for MCP-only tools**
   - `get_empirica_introduction` → `empirica introduction`
   - `get_workflow_guidance` → `empirica workflow-help`
   - `cli_help` → Already covered by `empirica --help`

6. **Document MCP-first features**
   - `edit_with_confidence` is MCP-only (IDE integration)
   - Justify why no CLI equivalent needed

---

## Testing Checklist

- [ ] Every MCP tool maps to a CLI command (or has documented reason for direct handler)
- [ ] Parameter conversion tested for all commands
- [ ] JSON output tested for all routed commands
- [ ] Direct handlers maintain behavioral parity with CLI where applicable
- [ ] New CLI commands automatically get MCP wrappers (process documented)

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
