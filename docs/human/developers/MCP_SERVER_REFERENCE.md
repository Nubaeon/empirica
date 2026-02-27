# Empirica MCP Server Reference (v5.1)

**Last Updated:** 2026-02-18
**Total Tools:** 58
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
- **Tools:** 58 tools (stateless utilities + CLI wrappers)

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

> **Note:** CASCADE phases (PREFLIGHT, CHECK, POSTFLIGHT, POST-TEST) are now **direct submission tools**. Assess your 13 vectors honestly and submit directly - no template generation needed. POST-TEST runs automatically after POSTFLIGHT to collect objective evidence.

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

**Returns:** Calibration metrics including:

```json
{
  "ok": true,
  "session_id": "uuid",
  "calibration": {
    "per_vector": { ... },
    "overall_bias": 0.12,
    "sample_size": 42
  },
  "grounded_verification": {
    "coverage": 0.85,
    "evidence_count": 24,
    "sources": ["pytest", "git", "goals", "artifacts", "issues", "sentinel"],
    "gaps": [
      {
        "vector": "do",
        "self_assessed": 0.9,
        "grounded": 0.72,
        "gap": 0.18,
        "evidence_type": "OBJECTIVE"
      }
    ],
    "track1_vs_track2": {
      "track1_self_referential": { ... },
      "track2_grounded": { ... },
      "divergence": 0.15
    }
  }
}
```

**`grounded_verification` field (v1.5.0):**

The `grounded_verification` field provides **Track 2 (grounded) calibration** data, comparing AI self-assessment against objective evidence:

- **`coverage`** (float): Fraction of vectors with grounded evidence (0.0-1.0)
- **`evidence_count`** (int): Total evidence items collected from all sources
- **`sources`** (array): Active evidence sources used (pytest, git, goals, artifacts, issues, sentinel)
- **`gaps`** (array): Vectors where self-assessment diverges from grounded evidence
  - `vector`: Epistemic vector name
  - `self_assessed`: AI's self-reported score
  - `grounded`: Evidence-based score (quality-weighted: OBJECTIVE=1.0, SEMI_OBJECTIVE=0.7)
  - `gap`: Absolute difference between self-assessed and grounded
  - `evidence_type`: Quality tier of evidence (`OBJECTIVE` or `SEMI_OBJECTIVE`)
- **`track1_vs_track2`** (object): Comparison between self-referential (Track 1) and grounded (Track 2) calibration with divergence metric

**Grounded verification** is automatically triggered after POSTFLIGHT (the POST-TEST phase of the 4-phase CASCADE). Use `calibration-report --grounded` via CLI for the full report, or `calibration-report --trajectory` for trend analysis.

**Use when:** Checking if self-assessment is accurate, comparing self-reported vs evidence-based calibration

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

**Complete tool list (58 tools):**

**For complete MCP ↔ CLI mapping and detailed reference:** See [`MCP_CLI_MAPPING.md`](MCP_CLI_MAPPING.md)

### Documentation (3)
1. `get_empirica_introduction` - Framework introduction
2. `get_workflow_guidance` - CASCADE phase guidance
3. `cli_help` - CLI command help

### Session Management (4)
4. `session_create` - Create session
5. `get_session_summary` - Session overview
6. `get_epistemic_state` - Current epistemic state (13 vectors)
7. `resume_previous_session` - Resume sessions by AI ID

### CASCADE Workflow (3)
8. `submit_preflight_assessment` - Submit PREFLIGHT (13 vectors + reasoning)
9. `submit_check_assessment` - Submit CHECK gate (proceed/investigate)
10. `submit_postflight_assessment` - Submit POSTFLIGHT (triggers grounded verification)

### Noetic Artifacts (7)
11. `finding_log` - Log a finding (what was learned)
12. `unknown_log` - Log an unknown (what's unclear)
13. `deadend_log` - Log a dead-end (approach that failed)
14. `mistake_log` - Log a mistake (with prevention strategy)
15. `assumption_log` - Log unverified assumption (with confidence + domain)
16. `decision_log` - Log decision (with alternatives + reversibility)
17. `unknown_resolve` - Resolve a logged unknown

### Goals & Tasks (6)
18. `create_goal` - Create structured goal with scope vectors
19. `add_subtask` - Add subtask to goal
20. `complete_subtask` - Complete subtask with evidence
21. `get_goal_progress` - Get goal completion progress
22. `get_goal_subtasks` - Get subtask details
23. `list_goals` - List session goals

### Project Context (4)
24. `project_bootstrap` - Load project breadcrumbs (findings, unknowns, dead-ends, goals)
25. `session_snapshot` - Complete session snapshot with learning delta
26. `goals_ready` - Get goals ready to work on (unblocked)
27. `goals_claim` - Claim a goal and create epistemic branch

### Investigation & Analysis (2)
28. `investigate` - Run systematic investigation with epistemic tracking
29. `blindspot_scan` - Scan for unknown unknowns via artifact pattern analysis

### Epistemic Monitoring (3)
30. `epistemics_list` - List all assessments (PREFLIGHT/CHECK/POSTFLIGHT) for session
31. `epistemics_show` - Show detailed assessment, optionally by phase
32. `get_calibration_report` - Calibration metrics (self-ref + grounded)
### Human Copilot & Oversight (6)
34. `monitor` - Real-time monitoring: stats, cost, request history, health
35. `system_status` - Unified system status (/proc-style snapshot)
36. `efficiency_report` - Productivity metrics: learning velocity, CASCADE completeness
37. `issue_list` - List auto-captured issues (bugs, errors, TODOs)
38. `issue_handoff` - Hand off issue to another AI or human
39. `workspace_overview` - Multi-repo epistemic overview

### Workspace & Skills (2)
40. `skill_suggest` - Vector-aware skill/tool recommendations
41. `workspace_map` - Map workspace structure and cross-repo dependencies

### Memory & Continuity (1)
42. `memory_compact` - Compact session for epistemic continuity across context boundaries

### Checkpoints & Handoffs (4)
43. `create_git_checkpoint` - Create compressed checkpoint in git notes
44. `load_git_checkpoint` - Load checkpoint from git notes
45. `create_handoff_report` - Create epistemic handoff report (~90% token reduction)
46. `query_handoff_reports` - Query handoff reports by AI ID/session

### Multi-AI Coordination (2)
47. `discover_goals` - Discover goals from other AIs via git notes
48. `resume_goal` - Resume another AI's goal with epistemic handoff

### Mistakes Tracking (2)
49. `log_mistake` - Log mistake with root cause vector and prevention
50. `query_mistakes` - Query mistakes for patterns and learning

### Identity & Security (4)
51. `create_identity` - Create Ed25519 identity keypair
52. `list_identities` - List all AI identities
53. `export_public_key` - Export public key for sharing
54. `verify_signature` - Verify signed session

### Reference Docs (1)
55. `refdoc_add` - Add reference document to project knowledge base

### Vision (2)
56. `vision_analyze` - Analyze image(s) and extract metadata
57. `vision_log` - Log visual observation to session

### Metacognitive Edit (1)
58. `edit_with_confidence` - Edit with epistemic confidence assessment (4.7x success rate)

---

## Noetic Intent Tools

**Purpose:** Track assumptions and decisions (epistemic intent layer)

### `assumption_log`

Log an unverified assumption with confidence level.

**Parameters:**
- `session_id` (required): Session UUID
- `assumption` (required): The assumption being made
- `confidence` (optional): Confidence in assumption (0.0-1.0)
- `domain` (optional): Domain scope (e.g., "security", "architecture")
- `goal_id` (optional): Related goal UUID

**Returns:** Assumption UUID

**Use when:** Making an unverified belief that should be tracked and validated later

---

### `decision_log`

Log a decision with alternatives considered and rationale.

**Parameters:**
- `session_id` (required): Session UUID
- `choice` (required): The choice made
- `alternatives` (required): Alternatives considered (comma-separated or JSON array)
- `rationale` (required): Why this choice was made
- `confidence` (optional): Confidence in decision (0.0-1.0)
- `reversibility` (optional): `"exploratory"`, `"committal"`, or `"forced"`
- `domain` (optional): Domain scope
- `goal_id` (optional): Related goal UUID

**Returns:** Decision UUID

**Use when:** Making a choice point that should be recorded for audit trail

---

### `unknown_resolve`

Resolve a logged unknown when the answer is found.

**Parameters:**
- `unknown_id` (required): Unknown UUID to resolve
- `resolved_by` (required): How was this unknown resolved?

**Returns:** Confirmation

**Use when:** Investigation answered a previously logged unknown

---

## Session State Tools

**Purpose:** Session snapshots and goal scheduling

### `session_snapshot`

Get complete session snapshot with learning delta, findings, unknowns, mistakes, and active goals.

**Parameters:**
- `session_id` (required): Session UUID

**Returns:** Full session state including epistemic vectors, artifacts, and progress

**Use when:** Need complete session state overview (richer than `get_session_summary`)

---

### `goals_ready`

Get goals that are ready to work on (unblocked by dependencies and epistemic state).

**Parameters:**
- `session_id` (optional): Session UUID

**Returns:** Array of goals that can be started

**Use when:** Deciding which goal to pick up next

---

### `goals_claim`

Claim a goal and create epistemic branch for work.

**Parameters:**
- `goal_id` (required): Goal UUID to claim

**Returns:** Claim confirmation with branch info

**Use when:** Starting work on a specific goal

---

## Investigation Tools

**Purpose:** Systematic investigation and blindspot detection

### `investigate`

Run systematic investigation with epistemic tracking.

**Parameters:**
- `session_id` (required): Session UUID
- `investigation_goal` (required): What to investigate
- `max_rounds` (optional): Max investigation rounds (default: 5)

**Returns:** Investigation results with findings and epistemic state changes

**Use when:** Need structured investigation with automatic artifact logging

---

### `blindspot_scan`

Scan for epistemic blindspots (unknown unknowns) by analyzing artifact patterns.

**Parameters:**
- `project_id` (optional): Project ID (auto-detects)
- `session_id` (optional): Session ID for context
- `max_predictions` (optional): Maximum predictions (default: 10)
- `min_confidence` (optional): Minimum confidence threshold (default: 0.4)

**Returns:** Predicted knowledge gaps based on artifact topology

**Use when:** Starting new work or suspecting hidden unknowns

---

## Epistemic History

**Purpose:** Review assessment history

### `epistemics_list`

List all epistemic assessments (PREFLIGHT, CHECK, POSTFLIGHT) for a session.

**Parameters:**
- `session_id` (required): Session UUID

**Returns:** Array of assessments with timestamps and phases

**Use when:** Reviewing session trajectory

---

### `epistemics_show`

Show detailed epistemic assessment, optionally filtered by phase.

**Parameters:**
- `session_id` (required): Session UUID
- `phase` (optional): Phase filter (`"PREFLIGHT"`, `"CHECK"`, `"POSTFLIGHT"`)

**Returns:** Detailed vector data for matching assessments

**Use when:** Examining specific assessment details

---

## Monitoring & Oversight

**Purpose:** Human copilot tools for oversight and productivity

### `monitor`

Real-time monitoring of AI work — stats, cost analysis, request history, adapter health.

**Parameters:**
- `cost` (optional): Show cost analysis
- `history` (optional): Show recent request history
- `health` (optional): Include adapter health checks
- `project` (optional): Show cost projections
- `verbose` (optional): Show detailed stats

**Returns:** Monitoring dashboard data

**Use when:** Human needs oversight of AI work session

---

### `system_status`

Unified system status — aggregates config, memory, bus, attention, integrity, and gate status.

**Parameters:**
- `session_id` (optional): Session UUID (auto-detects)
- `summary` (optional): Return one-line summary instead of full status

**Returns:** /proc-style system snapshot

**Use when:** Need system health overview

---

### `efficiency_report`

Get productivity metrics — learning velocity, CASCADE completeness, goal completion rate.

**Parameters:**
- `session_id` (required): Session UUID

**Returns:** Efficiency metrics for the session

**Use when:** Evaluating session productivity

---

### `issue_list`

List auto-captured issues for human review.

**Parameters:**
- `session_id` (required): Session UUID
- `status` (optional): Filter: `"new"`, `"investigating"`, `"handoff"`, `"resolved"`, `"wontfix"`
- `category` (optional): Filter: `"bug"`, `"error"`, `"warning"`, `"deprecation"`, `"todo"`, `"performance"`, `"compatibility"`, `"design"`, `"other"`
- `severity` (optional): Filter: `"blocker"`, `"high"`, `"medium"`, `"low"`
- `limit` (optional): Max results (default: 100)

**Returns:** Array of issues with metadata

---

### `issue_handoff`

Hand off an issue to another AI or human.

**Parameters:**
- `session_id` (required): Session UUID
- `issue_id` (required): Issue ID to hand off
- `assigned_to` (required): AI ID or name to assign to

**Returns:** Handoff confirmation

---

### `workspace_overview`

Multi-repo epistemic overview — project health, knowledge state, uncertainty.

**Parameters:**
- `sort_by` (optional): `"activity"`, `"knowledge"`, `"uncertainty"`, `"name"`
- `filter` (optional): `"active"`, `"inactive"`, `"complete"`
- `verbose` (optional): Show detailed info

**Returns:** Workspace-level epistemic summary

---

### `skill_suggest`

Vector-aware skill/tool recommendations for a task.

**Parameters:**
- `task` (optional): Task description
- `session_id` (optional): Session ID for current epistemic vectors
- `project_id` (optional): Project ID for context
- `verbose` (optional): Show detailed suggestions

**Returns:** Recommended skills, agents, and tools based on epistemic state

---

### `workspace_map`

Map workspace structure — repos, relationships, cross-repo dependencies.

**Parameters:**
- `verbose` (optional): Show detailed info

**Returns:** Workspace structure map

---

## Memory Management

**Purpose:** Session compaction for epistemic continuity

### `memory_compact`

Compact session for epistemic continuity across conversation boundaries.

**Parameters:**
- `session_id` (required): Session UUID or alias
- `create_continuation` (optional): Create continuation session (default: true)
- `include_bootstrap` (optional): Load project bootstrap (default: true)
- `checkpoint_current` (optional): Checkpoint current state (default: true)
- `compact_mode` (optional): `"full"`, `"minimal"`, `"context_only"`

**Returns:** Compaction result with continuation session ID

**Use when:** Approaching context limit, need to preserve epistemic state

---

## Vision Tools

**Purpose:** Image analysis with epistemic tracking

### `vision_analyze`

Analyze image(s) and extract metadata.

**Parameters:**
- `image` (optional): Single image path
- `pattern` (optional): Image pattern (e.g., `"slides/*.png"`)
- `session_id` (optional): Session ID to log findings

**Returns:** Image metadata (size, format, aspect ratio)

---

### `vision_log`

Log visual observation to session.

**Parameters:**
- `session_id` (required): Session UUID
- `observation` (required): Visual observation text

**Returns:** Confirmation

**Use when:** Recording observations not captured by `vision_analyze`

---

## Usage Patterns

### Starting a Session

```python
# 1. Create session
result = session_create(ai_id="copilot")
session_id = result["session_id"]

# 2. Load project context (optional)
breadcrumbs = project_bootstrap(project_id="myproject")

# 3. Run PREFLIGHT - assess your 13 vectors and submit directly
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

# Run POSTFLIGHT - assess your 13 vectors and submit directly
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

**Last Updated:** 2026-02-18
**MCP Server:** empirica-v2
**Total Tools:** 58
**Protocol:** MCP (stdio)
