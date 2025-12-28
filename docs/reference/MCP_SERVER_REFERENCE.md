# Empirica MCP Server Reference (v5.0)

**Last Updated:** 2025-12-20
**Total Tools:** 40
**Architecture:** Thin wrappers around CLI commands

---

## Overview

The Empirica MCP (Model Context Protocol) server exposes Empirica functionality through standardized tool interface for AI assistants.

**Architecture Principle:** MCP tools are **thin wrappers** around CLI commands - the CLI is the single source of truth.

**Server Details:**
- **Package:** `empirica-mcp` (PyPI)
- **Command:** `empirica-mcp`
- **Protocol:** MCP (Model Context Protocol)
- **Transport:** stdio
- **Tools:** 40 tools (3 stateless + 37 CLI wrappers)

**For complete MCP ↔ CLI mapping:** See [`api/mcp_cli_mapping.md`](api/mcp_cli_mapping.md)

---

## Table of Contents

1. [Setup & Configuration](#setup--configuration)
2. [Documentation Tools](#documentation-tools)
3. [Session Management](#session-management)
4. [CASCADE Workflow](#cascade-workflow)
5. [Goals & Tasks](#goals--tasks)
6. [Continuity & Handoffs](#continuity--handoffs)
7. [Multi-AI Coordination](#multi-ai-coordination)
8. [Identity & Security](#identity--security)
9. [Project Tracking](#project-tracking)
10. [Metacognitive Editing](#metacognitive-editing)
11. [Tool Reference](#tool-reference)

---

## Setup & Configuration

### Installation

Install the MCP server package:

```bash
pip install empirica-mcp
```

### MCP Server Config

**For Claude Desktop/VS Code/Cursor/Windsurf:**

```json
{
  "mcpServers": {
    "empirica": {
      "command": "empirica-mcp"
    }
  }
}
```

**That's it!** No paths, no environment variables needed. The MCP server automatically:
- Finds `empirica` installation via PATH
- Uses repo-local `./.empirica/` for data storage
- Loads project context from git repository

### Advanced Configuration

**Custom data directory (optional):**

```json
{
  "mcpServers": {
    "empirica": {
      "command": "empirica-mcp",
      "env": {
        "EMPIRICA_DATA_DIR": "/custom/path/.empirica"
      }
    }
  }
}
```

### Testing the Server

```bash
# Verify installation
which empirica-mcp

# Test server directly (Ctrl+C to exit)
empirica-mcp
```

---

## Documentation Tools

**Purpose:** Get help and guidance

### `get_empirica_introduction`

Get comprehensive introduction to Empirica framework.

**No parameters**

**Returns:** Complete Empirica introduction including:
- Philosophy and principles
- CASCADE workflow
- Core concepts
- Quick start guide

**Use when:** Starting with Empirica, need overview

---

### `get_workflow_guidance`

Get workflow guidance for CASCADE phases.

**Parameters:**
- `phase` (optional): Specific phase (`PREFLIGHT`, `CHECK`, `ACT`, `POSTFLIGHT`)

**Returns:** Phase-specific guidance

**Use when:** Need help with specific CASCADE phase

---

### `cli_help`

Get help for Empirica CLI commands.

**No parameters**

**Returns:** CLI command reference

**Use when:** Need CLI syntax help

---

## Session Management

**Purpose:** Create and manage sessions

### `session_create`

Create new Empirica session with metacognitive configuration.

**Parameters:**
- `ai_id` (required): AI agent identifier (e.g., `"copilot"`, `"rovo"`)
- `session_type` (optional): Session type (`"development"`, `"production"`, `"testing"`)
- `bootstrap_level` (optional): Bootstrap level (0-4 or named level)

**Returns:**
```json
{
  "ok": true,
  "session_id": "uuid-string",
  "ai_id": "copilot",
  "message": "Session created successfully"
}
```

**Example:**
```python
session_create(ai_id="copilot", session_type="development")
```

**Use when:** Starting new work session

---

### `get_session_summary`

Get complete session summary.

**Parameters:**
- `session_id` (required): Session UUID or alias

**Returns:** Session metadata, epistemic state, goals, etc.

**Use when:** Need complete session overview

---

### `get_epistemic_state`

Get current epistemic state for session.

**Parameters:**
- `session_id` (required): Session UUID or alias

**Returns:** Current 13-vector epistemic state

**Use when:** Check current knowledge/confidence levels

---

### `resume_previous_session`

Resume previous session(s).

**Parameters:**
- `ai_id` (required): AI identifier
- `count` (optional): Number of sessions to resume (default: 1)

**Returns:** Session context for resumed sessions

**Use when:** Continuing work from previous session

---

## CASCADE Workflow

**Purpose:** Epistemic self-assessment workflow

### `execute_preflight`

Execute PREFLIGHT epistemic assessment before task engagement.

**Parameters:**
- `session_id` (required): Session UUID or alias
- `prompt` (required): Task description to assess

**Returns:** Self-assessment prompt as JSON (non-blocking)

**Flow:**
1. AI receives assessment prompt
2. AI performs genuine self-assessment
3. AI calls `submit_preflight_assessment` with 13 vectors

**Use when:** Starting new task, need baseline assessment

---

### `submit_preflight_assessment`

Submit PREFLIGHT self-assessment scores.

**Parameters:**
- `session_id` (required): Session UUID
- `vectors` (required): 13 epistemic vectors (0.0-1.0)
  - `engagement`, `know`, `do`, `context`
  - `clarity`, `coherence`, `signal`, `density`
  - `state`, `change`, `completion`, `impact`
  - `uncertainty`
- `reasoning` (required): Explanation of assessment

**Returns:** Confirmation of submission

**Example:**
```python
submit_preflight_assessment(
    session_id="uuid",
    vectors={
        "engagement": 0.8,
        "know": 0.6,
        "do": 0.7,
        "context": 0.5,
        "clarity": 0.7,
        "coherence": 0.8,
        "signal": 0.6,
        "density": 0.5,
        "state": 0.6,
        "change": 0.7,
        "completion": 0.0,
        "impact": 0.5,
        "uncertainty": 0.6
    },
    reasoning="Moderate baseline knowledge, high uncertainty about X"
)
```

---

### `execute_check`

Execute CHECK phase assessment after investigation.

**Parameters:**
- `session_id` (required): Session UUID or alias
- `findings` (required): Array of investigation findings
- `remaining_unknowns` (required): Array of remaining unknowns
- `confidence_to_proceed` (required): Confidence score (0.0-1.0)

**Returns:** CHECK assessment prompt

**Flow:**
1. AI provides findings/unknowns
2. System assesses readiness
3. AI calls `submit_check_assessment` with decision

**Use when:** Completed investigation, deciding whether to proceed

---

### `submit_check_assessment`

Submit CHECK phase assessment.

**Parameters:**
- `session_id` (required): Session UUID
- `vectors` (required): Updated epistemic vectors
- `decision` (required): `"proceed"` or `"investigate"`
- `reasoning` (optional): Explanation

**Returns:** Confirmation + decision validation

**Use when:** After CHECK execution, making gate decision

---

### `execute_postflight`

Execute POSTFLIGHT pure self-assessment after task completion.

**Parameters:**
- `session_id` (required): Session UUID or alias
- `task_summary` (required): Summary of ALL work completed

**Returns:** Session context (WITHOUT baseline vectors)

**Purpose:** Assess CURRENT state genuinely; system calculates deltas

---

### `submit_postflight_assessment`

Submit POSTFLIGHT pure self-assessment.

**Parameters:**
- `session_id` (required): Session UUID
- `vectors` (required): CURRENT epistemic state (13 vectors)
- `reasoning` (required): What changed from PREFLIGHT

**Important:** Rate CURRENT state only. Do NOT claim deltas. System calculates learning automatically.

**Use when:** After completing work, measuring learning

---

## Goals & Tasks

**Purpose:** Track work structure and progress

### `create_goal`

Create new structured goal.

**Parameters:**
- `session_id` (required): Session UUID
- `objective` (required): Goal description
- `scope` (optional): Scope vectors
  - `breadth` (0.0-1.0): How wide (0=function, 1=codebase)
  - `duration` (0.0-1.0): Time (0=minutes, 1=months)
  - `coordination` (0.0-1.0): Collaboration (0=solo, 1=heavy)
- `success_criteria` (optional): Array of success criteria
- `estimated_complexity` (optional): Complexity (0.0-1.0)

**Returns:**
```json
{
  "ok": true,
  "goal_id": "uuid",
  "beads_issue_id": "bd-xxx" // if BEADS enabled
}
```

**Use when:** Starting multi-session work

---

### `add_subtask`

Add subtask to existing goal.

**Parameters:**
- `goal_id` (required): Goal UUID
- `description` (required): Subtask description
- `importance` (optional): `"critical"`, `"high"`, `"medium"`, `"low"`
- `dependencies` (optional): Array of dependency UUIDs
- `estimated_tokens` (optional): Token estimate

**Returns:** Subtask UUID

---

### `complete_subtask`

Mark subtask as complete.

**Parameters:**
- `task_id` (required): Subtask UUID (note: parameter is task_id not subtask_id)
- `evidence` (optional): Completion evidence (commit, file, etc.)

**Returns:** Confirmation

---

### `get_goal_progress`

Get goal completion progress.

**Parameters:**
- `goal_id` (required): Goal UUID

**Returns:**
```json
{
  "completion_percentage": 75.0,
  "completed_subtasks": 3,
  "total_subtasks": 4
}
```

---

### `get_goal_subtasks`

Get detailed subtask information for a goal.

**Parameters:**
- `goal_id` (required): Goal UUID

**Returns:** Array of subtasks with status, description, evidence

**Use when:** Need subtask details for resumption

---

### `list_goals`

List goals for session.

**Parameters:**
- `session_id` (required): Session UUID or alias

**Returns:** Array of goals with progress

---

## Continuity & Handoffs

**Purpose:** Session resumption and knowledge transfer

### `create_git_checkpoint`

Create compressed checkpoint in git notes.

**Parameters:**
- `session_id` (required): Session UUID
- `phase` (required): Current phase
- `vectors` (optional): Current epistemic vectors
- `metadata` (optional): Additional metadata
- `round_num` (optional): Round number

**Returns:** Checkpoint UUID

**Storage:** Git notes at `refs/notes/empirica/checkpoints/{session_id}`

**Token savings:** ~97.5% (65 tokens vs 2600 baseline)

---

### `load_git_checkpoint`

Load latest checkpoint from git notes.

**Parameters:**
- `session_id` (required): Session UUID or alias (e.g., `"latest:active:ai-id"`)

**Returns:** Checkpoint data (vectors, metadata, phase)

**Use when:** Resuming work from checkpoint

---

### `create_handoff_report`

Create epistemic handoff report for session continuity.

**Parameters:**
- `session_id` (required): Session UUID
- `task_summary` (required): What was accomplished (2-3 sentences)
- `key_findings` (required): Array of validated learnings
- `next_session_context` (required): Critical context for next session
- `remaining_unknowns` (optional): What's still unclear
- `artifacts_created` (optional): Files created

**Returns:** Handoff report UUID

**Storage:** Git notes at `refs/notes/empirica/handoff/{session_id}`

**Token savings:** ~98.8% (238 tokens vs 20k baseline)

**Use when:** Ending session, enabling efficient resumption

---

### `query_handoff_reports`

Query handoff reports by AI ID or session ID.

**Parameters:**
- `ai_id` (optional): Filter by AI identifier
- `session_id` (optional): Specific session UUID
- `limit` (optional): Number of results (default: 5)

**Returns:** Array of handoff reports with findings/unknowns

**Use when:** Resuming work, need breadcrumbs

---

## Multi-AI Coordination

**Purpose:** Goal discovery and coordination across AIs

### `discover_goals`

Discover goals from other AIs via git notes (Phase 1).

**Parameters:**
- `from_ai_id` (optional): Filter by AI creator
- `session_id` (optional): Filter by session

**Returns:** Array of discoverable goals

**Use when:** Looking for work to collaborate on

---

### `resume_goal`

Resume another AI's goal with epistemic handoff (Phase 1).

**Parameters:**
- `goal_id` (required): Goal UUID to resume
- `ai_id` (required): Your AI identifier

**Returns:** Goal context + handoff data

**Use when:** Taking over another AI's work

---

## Identity & Security

**Purpose:** Cryptographic identity management

### `create_identity`

Create new AI identity with Ed25519 keypair (Phase 2).

**Parameters:**
- `ai_id` (required): AI identifier
- `overwrite` (optional): Overwrite existing (default: false)

**Returns:** Public key

**Storage:** `~/.empirica/identity/{ai_id}/`

---

### `list_identities`

List all AI identities (Phase 2).

**No parameters**

**Returns:** Array of AI identities with public keys

---

### `export_public_key`

Export public key for sharing (Phase 2).

**Parameters:**
- `ai_id` (required): AI identifier

**Returns:** PEM-encoded public key

---

### `verify_signature`

Verify signed session (Phase 2).

**Parameters:**
- `session_id` (required): Session UUID to verify

**Returns:** Verification result (valid/invalid, signer)

---

## Project Tracking

**Purpose:** Multi-repo/long-term project tracking

### `project_bootstrap`

Bootstrap project context with epistemic breadcrumbs.

**Parameters:**
- `project_id` (required): Project UUID
- `mode` (optional): `"session_start"` (fast) or `"live"` (complete)

**Returns:** Breadcrumbs (~800 tokens):
- Recent findings (what was learned)
- Unresolved unknowns (what to investigate - breadcrumbs!)
- Dead ends (what didn't work)
- Recent mistakes (root causes + prevention)
- Reference docs (what to read/update)
- Incomplete work (pending goals + progress)

**Token savings:** ~92% (800 vs 10k manual reconstruction)

**Use when:** Starting session, need project context

---

### `finding_log`

Log a project finding (what was learned/discovered).

**Parameters:**
- `project_id` (required): Project UUID
- `session_id` (required): Session UUID
- `finding` (required): What was learned
- `goal_id` (optional): Related goal UUID
- `subtask_id` (optional): Related subtask UUID

**Returns:** Finding UUID

**Use when:** Discovered something important

---

### `unknown_log`

Log a project unknown (what's still unclear).

**Parameters:**
- `project_id` (required): Project UUID
- `session_id` (required): Session UUID
- `unknown` (required): What is unclear
- `goal_id` (optional): Related goal
- `subtask_id` (optional): Related subtask

**Returns:** Unknown UUID

**Use when:** Identified gap in knowledge (breadcrumb!)

---

### `deadend_log`

Log a project dead end (what didn't work).

**Parameters:**
- `project_id` (required): Project UUID
- `session_id` (required): Session UUID
- `approach` (required): Approach that was attempted
- `why_failed` (required): Why it didn't work
- `goal_id` (optional): Related goal
- `subtask_id` (optional): Related subtask

**Returns:** Dead end UUID

**Use when:** Tried approach that failed (save others time!)

---

### `refdoc_add`

Add a reference document to project knowledge base.

**Parameters:**
- `project_id` (required): Project UUID
- `doc_path` (required): Path to documentation file
- `doc_type` (optional): Type (`"guide"`, `"reference"`, `"example"`, `"config"`)
- `description` (optional): What's in the doc

**Returns:** Reference doc UUID

**Use when:** Found useful doc, make it discoverable

---

## Metacognitive Editing

**Purpose:** Prevent edit failures through confidence assessment

### `edit_with_confidence`

Edit file with metacognitive confidence assessment.

**Prevents 80% of edit failures** by assessing epistemic state BEFORE edit.

**Parameters:**
- `file_path` (required): Path to file to edit
- `old_str` (required): String to replace (exact match)
- `new_str` (required): Replacement string
- `context_source` (optional): How recent was file read?
  - `"view_output"`: Just read this turn (high confidence)
  - `"fresh_read"`: Read 1-2 turns ago (medium confidence)
  - `"memory"`: Stale/never read (triggers re-read)
- `session_id` (optional): Session for calibration tracking

**Returns:**
```json
{
  "ok": true,
  "strategy": "atomic_edit",  // or "bash_fallback", "re_read_first"
  "confidence": 0.92,
  "reasoning": "High confidence: fresh context, unique pattern"
}
```

**Epistemic signals assessed:**
1. **CONTEXT** - Freshness (view_output > fresh_read > memory)
2. **UNCERTAINTY** - Whitespace confidence
3. **SIGNAL** - Pattern uniqueness
4. **CLARITY** - Truncation risk

**Strategy selection:**
- Confidence ≥0.70 → `atomic_edit` (direct edit)
- Confidence ≥0.40 → `bash_fallback` (sed/awk)
- Confidence <0.40 → `re_read_first` (re-read file)

**Benefits:**
- 4.7x higher success rate (94% vs 20%)
- 4x faster (30s vs 2-3 min with retries)
- Transparent reasoning
- Calibration tracking (improves over time)

**Use when:** Editing files (ALWAYS use instead of direct edit)

---

### `get_calibration_report`

Get calibration report for session.

**Parameters:**
- `session_id` (required): Session UUID

**Returns:** Calibration metrics (predicted vs actual confidence)

**Use when:** Checking if self-assessment is accurate

---

### `log_mistake`

Log a mistake for learning and future prevention.

**Parameters:**
- `session_id` (required): Session UUID
- `mistake` (required): What was done wrong
- `why_wrong` (required): Why it was wrong
- `cost_estimate` (optional): Time wasted (e.g., `"2 hours"`)
- `root_cause_vector` (optional): Epistemic vector that caused mistake
  - `"KNOW"`, `"DO"`, `"CONTEXT"`, `"CLARITY"`, etc.
- `prevention` (optional): How to prevent in future
- `goal_id` (optional): Related goal

**Returns:** Mistake UUID

**Use when:** Made a mistake, want to learn from it

---

### `query_mistakes`

Query logged mistakes for learning.

**Parameters:**
- `session_id` (optional): Filter by session
- `goal_id` (optional): Filter by goal
- `limit` (optional): Max results (default: 10)

**Returns:** Array of mistakes with patterns

**Use when:** Checking for repeat failures, learning patterns

---

## Tool Reference

**Complete tool list (40 tools):**

**For complete MCP ↔ CLI mapping and detailed reference:** See [`MCP_CLI_MAPPING.md`](MCP_CLI_MAPPING.md)

**High-level categories:**

### Documentation
1. `get_empirica_introduction` - Framework introduction
2. `get_workflow_guidance` - CASCADE guidance
3. `cli_help` - CLI command help

### Session Management
4. `session_create` - Create session
5. `get_session_summary` - Session overview
6. `get_epistemic_state` - Current epistemic state
7. `resume_previous_session` - Resume sessions

### CASCADE Workflow
8. `execute_preflight` - PREFLIGHT assessment
9. `submit_preflight_assessment` - Submit PREFLIGHT
10. `execute_check` - CHECK gate
11. `submit_check_assessment` - Submit CHECK
12. `execute_postflight` - POSTFLIGHT assessment
13. `submit_postflight_assessment` - Submit POSTFLIGHT

### Goals & Tasks
14. `create_goal` - Create goal
15. `add_subtask` - Add subtask
16. `complete_subtask` - Complete subtask
17. `get_goal_progress` - Get progress
18. `get_goal_subtasks` - Get subtask details
19. `list_goals` - List session goals

### Continuity
20. `create_git_checkpoint` - Create checkpoint
21. `load_git_checkpoint` - Load checkpoint
22. `create_handoff_report` - Create handoff
23. `query_handoff_reports` - Query handoffs

### Multi-AI
24. `discover_goals` - Discover goals from other AIs
25. `resume_goal` - Resume another AI's goal

### Identity
26. `create_identity` - Create Ed25519 identity
27. `list_identities` - List identities
28. `export_public_key` - Export public key
29. `verify_signature` - Verify signature

### Project Tracking
30. `project_bootstrap` - Load project breadcrumbs
31. `finding_log` - Log finding
32. `unknown_log` - Log unknown
33. `deadend_log` - Log dead end
34. `refdoc_add` - Add reference doc

### Metacognitive
35. `edit_with_confidence` - Smart file editing
36. `get_calibration_report` - Calibration metrics
37. `log_mistake` - Log mistake
38. `query_mistakes` - Query mistakes

---

## Usage Patterns

### Starting a Session

```python
# 1. Create session
result = session_create(ai_id="copilot")
session_id = result["session_id"]

# 2. Load project context (optional)
breadcrumbs = project_bootstrap(project_id="myproject")

# 3. Run PREFLIGHT
preflight = execute_preflight(
    session_id=session_id,
    prompt="Implement OAuth2 authentication"
)

# 4. Submit assessment
submit_preflight_assessment(
    session_id=session_id,
    vectors={...},
    reasoning="..."
)
```

### During Work

```python
# Create goal
goal = create_goal(
    session_id=session_id,
    objective="Implement OAuth2",
    scope={"breadth": 0.3, "duration": 0.4, "coordination": 0.1}
)

# Add subtasks
add_subtask(goal_id=goal["goal_id"], description="Setup provider")
add_subtask(goal_id=goal["goal_id"], description="Implement flow")

# Edit files
edit_with_confidence(
    file_path="auth/oauth.py",
    old_str="def login():\n    pass",
    new_str="def login():\n    return oauth_flow()",
    context_source="view_output"
)

# Log findings
finding_log(
    project_id="myproject",
    session_id=session_id,
    finding="OAuth2 requires PKCE for public clients"
)
```

### Ending Session

```python
# Complete subtasks
complete_subtask(task_id="uuid", evidence="auth/oauth.py:45-120")

# Run POSTFLIGHT
execute_postflight(
    session_id=session_id,
    task_summary="Implemented OAuth2 with PKCE"
)

submit_postflight_assessment(
    session_id=session_id,
    vectors={...},  # Current state
    reasoning="Learned: PKCE required, token refresh needs secure storage"
)

# Create handoff
create_handoff_report(
    session_id=session_id,
    task_summary="OAuth2 authentication complete",
    key_findings=["PKCE prevents token theft", "Refresh rotation required"],
    remaining_unknowns=["Token revocation at scale"],
    next_session_context="Auth system in place, next: authorization layer"
)
```

### Resuming Work

```python
# Query handoffs
handoffs = query_handoff_reports(ai_id="copilot", limit=1)

# Or load checkpoint
checkpoint = load_git_checkpoint(session_id="latest:active:copilot")

# Resume session
resume_previous_session(ai_id="copilot", count=1)
```

---

## Server Configuration

**Location:** MCP client config (e.g., `claude_desktop_config.json`)

**Minimal config:**
```json
{
  "mcpServers": {
    "empirica": {
      "command": "python",
      "args": ["/path/to/empirica/mcp_local/empirica_mcp_server.py"]
    }
  }
}
```

**With environment:**
```json
{
  "mcpServers": {
    "empirica": {
      "command": "python",
      "args": ["/path/to/empirica/mcp_local/empirica_mcp_server.py"],
      "env": {
        "EMPIRICA_DATA_DIR": "/path/to/.empirica",
        "PYTHONPATH": "/path/to/empirica",
        "EMPIRICA_LOG_LEVEL": "info"
      }
    }
  }
}
```

---

## Troubleshooting

### Server Not Starting

```bash
# Test server directly
python mcp_local/empirica_mcp_server.py

# Check logs
tail -f ~/.empirica/mcp_server.log

# Validate config
empirica config --validate
```

### Tools Not Showing

```bash
# Check MCP client logs
# Claude Desktop: ~/Library/Logs/Claude/
# VS Code: Output panel -> MCP

# Restart MCP client
# Tools reload on client restart
```

### Session Aliases Not Working

```python
# Valid aliases
"latest"                 # Most recent session (any AI)
"latest:active"          # Most recent active session
"latest:active:copilot"  # Most recent active for copilot

# Test alias resolution
get_session_summary(session_id="latest:active:copilot")
```

---

## See Also

- [CLI Commands Reference](CLI_COMMANDS_GENERATED.md)
- [Python API Reference](PYTHON_API_GENERATED.md)
- [Configuration Reference](CONFIGURATION_REFERENCE.md)
- [Canonical System Prompt](../system-prompts/CANONICAL_SYSTEM_PROMPT.md)

---

**Last Updated:** 2025-12-16  
**MCP Server:** empirica-v2  
**Total Tools:** 38  
**Protocol:** MCP (stdio)
