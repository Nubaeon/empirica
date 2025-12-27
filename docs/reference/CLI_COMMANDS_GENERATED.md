# Empirica CLI Commands Reference (v4.0)

**Generated from code:** 2025-12-16
**Total commands:** 67
**Source:** `cli_core.py`

---

## Table of Contents

- [Session Management](#session-management)
- [CASCADE Workflow](#cascade-workflow)
- [Goals & Tasks](#goals-and-tasks)
- [Investigation](#investigation)
- [Project Tracking](#project-tracking)
- [Checkpoints & Handoffs](#checkpoints-and-handoffs)
- [Identity & Security](#identity-and-security)
- [Configuration](#configuration)
- [Monitoring](#monitoring)
- [Utilities](#utilities)

---

## Session Management

**6 commands**

### `sessions-list`

List all sessions

**Usage:**
```bash
empirica sessions-list [OPTIONS]
```

**Arguments:**

- `--limit`: **Optional** | Type: integer | Default: `50` |   
  Maximum sessions to show
- `--verbose`: **Optional** | Flag (default: `False`) |   
  Show detailed info
- `--output`: **Optional** | Type: string | Default: `text` | Choices: `text`, `json` |   
  Output format

**Handler:** `handle_sessions_list_command`

---

### `sessions-show`

Show detailed session info

**Usage:**
```bash
empirica sessions-show [OPTIONS]
```

**Arguments:**

- `session_id` (positional): **Optional** | Type: string |   
  Session ID or alias (latest, latest:active, latest:<ai_id>, latest:active:<ai_id>)
- `--session-id`: **Optional** | Type: string |   
  Session ID (alternative to positional argument)
- `--verbose`: **Optional** | Flag (default: `False`) |   
  Show all vectors and cascades
- `--output`: **Optional** | Type: string | Default: `text` | Choices: `text`, `json` |   
  Output format

**Handler:** `handle_sessions_show_command`

---

### `session-snapshot`

Show session snapshot (where you left off)

**Usage:**
```bash
empirica session-snapshot
```

**Arguments:**

- `session_id` (positional): **Optional** | Type: string |   
  Session ID or alias
- `--output`: **Optional** | Type: string | Default: `text` | Choices: `text`, `json` |   
  Output format

**Handler:** `handle_session_snapshot_command`

---

### `sessions-export`

Export session to JSON

**Usage:**
```bash
empirica sessions-export
```

**Arguments:**

- `session_id` (positional): **Optional** | Type: string |   
  Session ID or alias (latest, latest:active, latest:<ai_id>)
- `--session-id`: **Optional** | Type: string |   
  Session ID (alternative to positional argument)
- `--output`: **Optional** | Type: string |   
  Output file path (default: session_<id>.json)

**Handler:** `handle_sessions_export_command`

---

### `sessions-resume`

Resume previous sessions

**Usage:**
```bash
empirica sessions-resume
```

**Arguments:**

- `--ai-id`: **Optional** | Type: string |   
  Filter by AI ID
- `--count`: **Optional** | Type: integer | Default: `1` |   
  Number of sessions to retrieve
- `--detail-level`: **Optional** | Type: string | Default: `summary` | Choices: `summary`, `detailed`, `full` |   
  Detail level
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_sessions_resume_command`

---

### `session-create`

Create new session (AI-first: use config file, Legacy: use flags)

**Usage:**
```bash
empirica session-create
```

**Arguments:**

- `config` (positional): **Optional** | Type: string |   
  JSON config file path or "-" for stdin (AI-first mode)
- `--ai-id`: **Optional** | Type: string |   
  AI agent identifier (legacy)
- `--user-id`: **Optional** | Type: string |   
  User identifier (legacy)
- `--bootstrap-level`: **Optional** | Type: integer | Default: `1` |   
  Bootstrap level (0-4) (legacy)
- `--subject`: **Optional** | Type: string |   
  Subject/workstream identifier (auto-detected from directory if omitted)
- `--output`: **Optional** | Type: string | Default: `json` | Choices: `default`, `json` |   
  Output format (default: json for AI)

**Handler:** `handle_session_create_command`

---

## CASCADE Workflow

**7 commands**

### `preflight`

Execute preflight epistemic assessment

**Usage:**
```bash
empirica preflight [OPTIONS]
```

**Arguments:**

- `prompt` (positional): **Optional** | Type: string |   
  Task description to assess
- `--session-id`: **Optional** | Type: string |   
  Optional session ID (auto-generated if not provided)
- `--ai-id`: **Optional** | Type: string | Default: `empirica_cli` |   
  AI identifier for session tracking
- `--no-git`: **Optional** | Flag (default: `False`) |   
  Disable automatic git checkpoint creation
- `--sign`: **Optional** | Flag (default: `False`) |   
  Sign assessment with AI keypair (Phase 2: EEP-1)
- `--prompt-only`: **Optional** | Flag (default: `False`) |   
  Return ONLY the self-assessment prompt as JSON (no waiting, for genuine AI assessment)
- `--assessment-json`: **Optional** | Type: string |   
  Genuine AI self-assessment JSON (required for genuine assessment)
- `--sentinel-assess`: **Optional** | Flag (default: `False`) |   
  Route to Sentinel assessment system (future feature)
- `--json`: **Optional** | Type: string |   
  Output as JSON (deprecated, use --output json)
- `--output`: **Optional** | Type: string | Default: `json` | Choices: `human`, `json` |   
  Output format (default: json for programmatic use; --output human for inspection)
- `--sentinel`: **Optional** | Flag (default: `False`) |   
  Route to Sentinel for interactive decision-making (future: Sentinel assessment routing)
- `--compact`: **Optional** | Flag (default: `False`) |   
  Output as single-line key=value (human format only)
- `--kv`: **Optional** | Flag (default: `False`) |   
  Output as multi-line key=value (human format only)
- `--verbose`: **Optional** | Flag (default: `False`) |   
  Show detailed assessment (human format only)
- `--quiet`: **Optional** | Flag (default: `False`) |   
  Quiet mode (requires --assessment-json)

**Handler:** `handle_preflight_command`

---

### `workflow`

Execute full preflight→work→postflight workflow

**Usage:**
```bash
empirica workflow [OPTIONS]
```

**Arguments:**

- `prompt` (positional): **Optional** | Type: string |   
  Task description
- `--auto`: **Optional** | Flag (default: `False`) |   
  Skip manual pause between steps
- `--verbose`: **Optional** | Flag (default: `False`) |   
  Show detailed workflow steps

**Handler:** `handle_workflow_command`

---

### `preflight-submit`

Submit preflight assessment (AI-first: use config file, Legacy: use flags)

**Usage:**
```bash
empirica preflight-submit
```

**Arguments:**

- `config` (positional): **Optional** | Type: string |   
  JSON config file path or "-" for stdin (AI-first mode)
- `--session-id`: **Optional** | Type: string |   
  Session ID (legacy)
- `--vectors`: **Optional** | Type: string |   
  Epistemic vectors as JSON string or dict (legacy)
- `--reasoning`: **Optional** | Type: string |   
  Reasoning for assessment scores (legacy)
- `--output`: **Optional** | Type: string | Default: `json` | Choices: `default`, `json` |   
  Output format (default: json for AI)

**Handler:** `handle_preflight_submit_command`

---

### `check`

Execute epistemic check (AI-first: use config file, Legacy: use flags)

**Usage:**
```bash
empirica check [OPTIONS]
```

**Arguments:**

- `config` (positional): **Optional** | Type: string |   
  JSON config file path or "-" for stdin (AI-first mode)
- `--session-id`: **Optional** | Type: string |   
  Session ID (legacy)
- `--findings`: **Optional** | Type: string |   
  Investigation findings as JSON array (legacy)
- `--unknowns`: **Optional** | Type: string |   
  Remaining unknowns as JSON array (legacy)
- `--remaining-unknowns`: **Optional** | Type: string |   
  Alias for --unknowns (legacy)
- `--confidence`: **Optional** | Type: float |   
  Confidence score (0.0-1.0) (legacy)
- `--output`: **Optional** | Type: string | Default: `json` | Choices: `default`, `json` |   
  Output format (default: json for AI)
- `--verbose`: **Optional** | Flag (default: `False`) |   
  Show detailed analysis

**Handler:** `handle_check_command`

---

### `check-submit`

Submit check assessment results

**Usage:**
```bash
empirica check-submit --session-id <VALUE> --vectors <VALUE> --decision <VALUE>
```

**Arguments:**

- `--session-id`: **Required** | Type: string |   
  Session ID
- `--vectors`: **Required** | Type: string |   
  Epistemic vectors as JSON string or dict
- `--decision`: **Required** | Type: string | Choices: `proceed`, `investigate`, `proceed_with_caution` |   
  Decision made
- `--reasoning`: **Optional** | Type: string |   
  Reasoning for decision
- `--cycle`: **Optional** | Type: integer |   
  Investigation cycle number
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_check_submit_command`

---

### `postflight`

Submit postflight epistemic assessment results

**Usage:**
```bash
empirica postflight --session-id <VALUE> --vectors <VALUE>
```

**Arguments:**

- `--session-id`: **Required** | Type: string |   
  Session ID
- `--vectors`: **Required** | Type: string |   
  Epistemic vectors as JSON string or dict (reassessment of same 13 dimensions as preflight)
- `--reasoning`: **Optional** | Type: string |   
  Task summary or description of learning/changes from preflight
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_postflight_submit_command`

---

### `postflight-submit`

Submit postflight assessment (AI-first: use config file, Legacy: use flags)

**Usage:**
```bash
empirica postflight-submit
```

**Arguments:**

- `config` (positional): **Optional** | Type: string |   
  JSON config file path or "-" for stdin (AI-first mode)
- `--session-id`: **Optional** | Type: string |   
  Session ID (legacy)
- `--vectors`: **Optional** | Type: string |   
  Epistemic vectors as JSON string or dict (legacy)
- `--reasoning`: **Optional** | Type: string |   
  Description of what changed from preflight (legacy)
- `--changes`: **Optional** | Type: string |   
  Alias for --reasoning (deprecated, use --reasoning)
- `--output`: **Optional** | Type: string | Default: `json` | Choices: `default`, `json` |   
  Output format (default: json for AI)

**Handler:** `handle_postflight_submit_command`

---

## Goals & Tasks

**11 commands**

### `goals-create`

Create new goal (AI-first: use config file, Legacy: use flags)

**Usage:**
```bash
empirica goals-create [OPTIONS]
```

**Arguments:**

- `config` (positional): **Optional** | Type: string |   
  JSON config file path or "-" for stdin (AI-first mode)
- `--session-id`: **Optional** | Type: string |   
  Session ID (legacy)
- `--ai-id`: **Optional** | Type: string | Default: `empirica_cli` |   
  AI identifier (legacy)
- `--objective`: **Optional** | Type: string |   
  Goal objective text (legacy)
- `--scope-breadth`: **Optional** | Type: float | Default: `0.3` |   
  Goal breadth (0.0-1.0, how wide the goal spans)
- `--scope-duration`: **Optional** | Type: float | Default: `0.2` |   
  Goal duration (0.0-1.0, expected lifetime)
- `--scope-coordination`: **Optional** | Type: float | Default: `0.1` |   
  Goal coordination (0.0-1.0, multi-agent coordination needed)
- `--success-criteria`: **Optional** | Type: string |   
  Success criteria as JSON array (or "-" to read from stdin)
- `--success-criteria-file`: **Optional** | Type: string |   
  Read success criteria from file (avoids shell quoting issues)
- `--estimated-complexity`: **Optional** | Type: float |   
  Complexity estimate (0.0-1.0)
- `--constraints`: **Optional** | Type: string |   
  Constraints as JSON object
- `--metadata`: **Optional** | Type: string |   
  Metadata as JSON object
- `--use-beads`: **Optional** | Flag (default: `False`) |   
  Create BEADS issue and link to goal
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_goals_create_command`

---

### `goals-add-subtask`

Add subtask to existing goal

**Usage:**
```bash
empirica goals-add-subtask --goal-id <VALUE> --description <VALUE> [OPTIONS]
```

**Arguments:**

- `--goal-id`: **Required** | Type: string |   
  Goal UUID
- `--description`: **Required** | Type: string |   
  Subtask description
- `--importance`: **Optional** | Type: string | Default: `medium` | Choices: `critical`, `high`, `medium`, `low` |   
  Epistemic importance
- `--dependencies`: **Optional** | Type: string |   
  Dependencies as JSON array
- `--estimated-tokens`: **Optional** | Type: integer |   
  Estimated token usage
- `--use-beads`: **Optional** | Flag (default: `False`) |   
  Create BEADS subtask and link to goal
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_goals_add_subtask_command`

---

### `goals-complete-subtask`

Mark subtask as complete

**Usage:**
```bash
empirica goals-complete-subtask --task-id <VALUE>
```

**Arguments:**

- `--task-id`: **Required** | Type: string |   
  Subtask UUID
- `--evidence`: **Optional** | Type: string |   
  Completion evidence (commit hash, file path, etc.)
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_goals_complete_subtask_command`

---

### `goals-progress`

Get goal completion progress

**Usage:**
```bash
empirica goals-progress --goal-id <VALUE>
```

**Arguments:**

- `--goal-id`: **Required** | Type: string |   
  Goal UUID
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_goals_progress_command`

---

### `goals-get-subtasks`

Get detailed subtask information

**Usage:**
```bash
empirica goals-get-subtasks --goal-id <VALUE>
```

**Arguments:**

- `--goal-id`: **Required** | Type: string |   
  Goal UUID
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_goals_get_subtasks_command`

---

### `goals-list`

List goals

**Usage:**
```bash
empirica goals-list [OPTIONS]
```

**Arguments:**

- `--session-id`: **Optional** | Type: string |   
  Filter by session ID
- `--scope-breadth-min`: **Optional** | Type: float |   
  Filter by minimum breadth (0.0-1.0)
- `--scope-breadth-max`: **Optional** | Type: float |   
  Filter by maximum breadth (0.0-1.0)
- `--scope-duration-min`: **Optional** | Type: float |   
  Filter by minimum duration (0.0-1.0)
- `--scope-duration-max`: **Optional** | Type: float |   
  Filter by maximum duration (0.0-1.0)
- `--scope-coordination-min`: **Optional** | Type: float |   
  Filter by minimum coordination (0.0-1.0)
- `--scope-coordination-max`: **Optional** | Type: float |   
  Filter by maximum coordination (0.0-1.0)
- `--completed`: **Optional** | Flag (default: `False`) |   
  Filter by completion status
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_goals_list_command`

---

### `goals-ready`

Query ready work (BEADS + epistemic filtering)

**Usage:**
```bash
empirica goals-ready --session-id <VALUE>
```

**Arguments:**

- `--session-id`: **Required** | Type: string |   
  Session UUID
- `--min-confidence`: **Optional** | Type: float | Default: `0.7` |   
  Minimum confidence threshold (0.0-1.0)
- `--max-uncertainty`: **Optional** | Type: float | Default: `0.3` |   
  Maximum uncertainty threshold (0.0-1.0)
- `--min-priority`: **Optional** | Type: integer |   
  Minimum BEADS priority (1, 2, or 3)
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_goals_ready_command`

---

### `goals-discover`

Discover goals from other AIs via git

**Usage:**
```bash
empirica goals-discover
```

**Arguments:**

- `--from-ai-id`: **Optional** | Type: string |   
  Filter by AI creator
- `--session-id`: **Optional** | Type: string |   
  Filter by session
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_goals_discover_command`

---

### `goals-resume`

Resume another AI's goal

**Usage:**
```bash
empirica goals-resume
```

**Arguments:**

- `goal_id` (positional): **Optional** | Type: string |   
  Goal ID to resume
- `--ai-id`: **Optional** | Type: string | Default: `empirica_cli` |   
  Your AI identifier
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_goals_resume_command`

---

### `goals-claim`

Claim goal, create git branch, link to BEADS

**Usage:**
```bash
empirica goals-claim --goal-id <VALUE> [OPTIONS]
```

**Arguments:**

- `--goal-id`: **Required** | Type: string |   
  Goal UUID to claim
- `--create-branch`: **Optional** | Flag (default: `True`) |   
  Create git branch (default: True)
- `--no-branch`: **Optional** | Flag (default: `True`) |   
  Skip branch creation
- `--run-preflight`: **Optional** | Flag (default: `False`) |   
  Run PREFLIGHT after claiming
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_goals_claim_command`

---

### `goals-complete`

Complete goal, merge branch, close BEADS issue

**Usage:**
```bash
empirica goals-complete --goal-id <VALUE> [OPTIONS]
```

**Arguments:**

- `--goal-id`: **Required** | Type: string |   
  Goal UUID to complete
- `--run-postflight`: **Optional** | Flag (default: `False`) |   
  Run POSTFLIGHT before completing
- `--merge-branch`: **Optional** | Flag (default: `False`) |   
  Merge git branch to main
- `--delete-branch`: **Optional** | Flag (default: `False`) |   
  Delete branch after merge
- `--create-handoff`: **Optional** | Flag (default: `False`) |   
  Create handoff report
- `--reason`: **Optional** | Type: string | Default: `completed` |   
  Completion reason (for BEADS)
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_goals_complete_command`

---

## Investigation

**6 commands**

### `investigate`

Investigate file/directory/concept

**Usage:**
```bash
empirica investigate [OPTIONS]
```

**Arguments:**

- `target` (positional): **Optional** | Type: string |   
  Target to investigate
- `--type`: **Optional** | Type: string | Default: `auto` | Choices: `auto`, `file`, `directory`, `concept`, `comprehensive` |   
  Investigation type. Use "comprehensive" for deep analysis (replaces analyze command)
- `--context`: **Optional** | Type: string |   
  JSON context data
- `--detailed`: **Optional** | Flag (default: `False`) |   
  Show detailed investigation
- `--verbose`: **Optional** | Flag (default: `False`) |   
  Show detailed investigation

**Handler:** `handle_investigate_command`

---

### `investigate-create-branch`

Create parallel investigation branch (epistemic auto-merge)

**Usage:**
```bash
empirica investigate-create-branch --session-id <VALUE> --investigation-path <VALUE> [OPTIONS]
```

**Arguments:**

- `--session-id`: **Required** | Type: string |   
  Session ID
- `--investigation-path`: **Required** | Type: string |   
  What is being investigated (e.g., oauth2)
- `--description`: **Optional** | Type: string |   
  Description of investigation
- `--preflight-vectors`: **Optional** | Type: string |   
  Epistemic vectors at branch start (JSON)
- `--output`: **Optional** | Type: string | Default: `text` | Choices: `text`, `json` |   
  Output format
- `--verbose`: **Optional** | Flag (default: `False`) |   
  Verbose output

**Handler:** `handle_investigate_create_branch_command`

---

### `investigate-checkpoint-branch`

Checkpoint branch after investigation

**Usage:**
```bash
empirica investigate-checkpoint-branch --branch-id <VALUE> --postflight-vectors <VALUE> [OPTIONS]
```

**Arguments:**

- `--branch-id`: **Required** | Type: string |   
  Branch ID
- `--postflight-vectors`: **Required** | Type: string |   
  Epistemic vectors after investigation (JSON)
- `--tokens-spent`: **Optional** | Type: string |   
  Tokens spent in investigation
- `--time-spent`: **Optional** | Type: string |   
  Time spent in investigation (minutes)
- `--output`: **Optional** | Type: string | Default: `text` | Choices: `text`, `json` |   
  Output format
- `--verbose`: **Optional** | Flag (default: `False`) |   
  Verbose output

**Handler:** `handle_investigate_checkpoint_branch_command`

---

### `investigate-merge-branches`

Auto-merge best branch based on epistemic scores

**Usage:**
```bash
empirica investigate-merge-branches --session-id <VALUE> [OPTIONS]
```

**Arguments:**

- `--session-id`: **Required** | Type: string |   
  Session ID
- `--round`: **Optional** | Type: string |   
  Investigation round number
- `--output`: **Optional** | Type: string | Default: `text` | Choices: `text`, `json` |   
  Output format
- `--verbose`: **Optional** | Flag (default: `False`) |   
  Verbose output

**Handler:** `handle_investigate_merge_branches_command`

---

### `investigate-log`

Log investigation findings during INVESTIGATE phase

**Usage:**
```bash
empirica investigate-log --session-id <VALUE> --findings <VALUE> [OPTIONS]
```

**Arguments:**

- `--session-id`: **Required** | Type: string |   
  Session ID
- `--findings`: **Required** | Type: string |   
  JSON array of findings discovered
- `--evidence`: **Optional** | Type: string |   
  JSON object with evidence (file paths, line numbers, etc.)
- `--verbose`: **Optional** | Flag (default: `False`) |   
  Verbose output

**Handler:** `handle_investigate_log_command`

---

### `act-log`

Log actions taken during ACT phase

**Usage:**
```bash
empirica act-log --session-id <VALUE> --actions <VALUE> [OPTIONS]
```

**Arguments:**

- `--session-id`: **Required** | Type: string |   
  Session ID
- `--actions`: **Required** | Type: string |   
  JSON array of actions taken
- `--artifacts`: **Optional** | Type: string |   
  JSON array of files modified/created
- `--goal-id`: **Optional** | Type: string |   
  Goal UUID being worked on
- `--verbose`: **Optional** | Flag (default: `False`) |   
  Verbose output

**Handler:** `handle_act_log_command`

---

## Project Tracking

**10 commands**

### `project-create`

Create a new project for multi-repo tracking

**Usage:**
```bash
empirica project-create --name <VALUE>
```

**Arguments:**

- `--name`: **Required** | Type: string |   
  Project name
- `--description`: **Optional** | Type: string |   
  Project description
- `--repos`: **Optional** | Type: string |   
  JSON array of repository names (e.g., '["empirica", "empirica-dev"]')
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_project_create_command`

---

### `project-handoff`

Create project-level handoff report

**Usage:**
```bash
empirica project-handoff --project-id <VALUE> --summary <VALUE>
```

**Arguments:**

- `--project-id`: **Required** | Type: string |   
  Project UUID
- `--summary`: **Required** | Type: string |   
  Project summary
- `--key-decisions`: **Optional** | Type: string |   
  JSON array of key decisions
- `--patterns`: **Optional** | Type: string |   
  JSON array of patterns discovered
- `--remaining-work`: **Optional** | Type: string |   
  JSON array of remaining work
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_project_handoff_command`

---

### `project-list`

List all projects

**Usage:**
```bash
empirica project-list
```

**Arguments:**

- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_project_list_command`

---

### `project-bootstrap`

Show epistemic breadcrumbs for project

**Usage:**
```bash
empirica project-bootstrap --project-id <VALUE> [OPTIONS]
```

**Arguments:**

- `--project-id`: **Required** | Type: string |   
  Project UUID
- `--subject`: **Optional** | Type: string |   
  Subject/workstream to filter by (auto-detected from directory if omitted)
- `--check-integrity`: **Optional** | Flag (default: `False`) |   
  Analyze doc-code integrity (adds ~2s)
- `--context-to-inject`: **Optional** | Flag (default: `False`) |   
  Generate markdown context for AI prompt injection
- `--task-description`: **Optional** | Type: string |   
  Task description for context load balancing
- `--epistemic-state`: **Optional** | Type: string |   
  Epistemic vectors from PREFLIGHT as JSON string (e.g., '{"uncertainty":0.8,"know":0.3}')
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_project_bootstrap_command`

---

### `project-search`

Semantic search for relevant docs/memory by task description

**Usage:**
```bash
empirica project-search
```

**Handler:** `handle_project_search_command`

---

### `project-embed`

Embed project docs & memory into Qdrant for semantic search

**Usage:**
```bash
empirica project-embed --project-id <VALUE>
```

**Arguments:**

- `--project-id`: **Required** | Type: string |   
  Project UUID
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_project_embed_command`

---

### `finding-log`

Log a project finding (what was learned/discovered)

**Usage:**
```bash
empirica finding-log --project-id <VALUE> --session-id <VALUE> --finding <VALUE>
```

**Arguments:**

- `--project-id`: **Required** | Type: string |   
  Project UUID
- `--session-id`: **Required** | Type: string |   
  Session UUID
- `--finding`: **Required** | Type: string |   
  What was learned/discovered
- `--goal-id`: **Optional** | Type: string |   
  Optional goal UUID
- `--subtask-id`: **Optional** | Type: string |   
  Optional subtask UUID
- `--subject`: **Optional** | Type: string |   
  Subject/workstream identifier (auto-detected from directory if omitted)
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_finding_log_command`

---

### `unknown-log`

Log a project unknown (what's still unclear)

**Usage:**
```bash
empirica unknown-log --project-id <VALUE> --session-id <VALUE> --unknown <VALUE>
```

**Arguments:**

- `--project-id`: **Required** | Type: string |   
  Project UUID
- `--session-id`: **Required** | Type: string |   
  Session UUID
- `--unknown`: **Required** | Type: string |   
  What is unclear/unknown
- `--goal-id`: **Optional** | Type: string |   
  Optional goal UUID
- `--subtask-id`: **Optional** | Type: string |   
  Optional subtask UUID
- `--subject`: **Optional** | Type: string |   
  Subject/workstream identifier (auto-detected from directory if omitted)
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_unknown_log_command`

---

### `deadend-log`

Log a project dead end (what didn't work)

**Usage:**
```bash
empirica deadend-log --project-id <VALUE> --session-id <VALUE> --approach <VALUE> --why-failed <VALUE>
```

**Arguments:**

- `--project-id`: **Required** | Type: string |   
  Project UUID
- `--session-id`: **Required** | Type: string |   
  Session UUID
- `--approach`: **Required** | Type: string |   
  What approach was tried
- `--why-failed`: **Required** | Type: string |   
  Why it failed
- `--goal-id`: **Optional** | Type: string |   
  Optional goal UUID
- `--subtask-id`: **Optional** | Type: string |   
  Optional subtask UUID
- `--subject`: **Optional** | Type: string |   
  Subject/workstream identifier (auto-detected from directory if omitted)
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_deadend_log_command`

---

### `refdoc-add`

Add a reference document to project

**Usage:**
```bash
empirica refdoc-add --project-id <VALUE> --doc-path <VALUE>
```

**Arguments:**

- `--project-id`: **Required** | Type: string |   
  Project UUID
- `--doc-path`: **Required** | Type: string |   
  Document path
- `--doc-type`: **Optional** | Type: string |   
  Document type (architecture, guide, api, design)
- `--description`: **Optional** | Type: string |   
  Document description
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_refdoc_add_command`

---

## Checkpoints & Handoffs

**9 commands**

### `checkpoint-create`

Create git checkpoint for session (Phase 1.5/2.0)

**Usage:**
```bash
empirica checkpoint-create --session-id <VALUE> --phase <VALUE> --round <VALUE>
```

**Arguments:**

- `--session-id`: **Required** | Type: string |   
  Session ID
- `--phase`: **Required** | Type: string | Choices: `PREFLIGHT`, `CHECK`, `ACT`, `POSTFLIGHT` |   
  Workflow phase
- `--round`: **Required** | Type: integer |   
  Round number
- `--metadata`: **Optional** | Type: string |   
  JSON metadata (optional)

**Handler:** `handle_checkpoint_create_command`

---

### `checkpoint-load`

Load latest checkpoint for session

**Usage:**
```bash
empirica checkpoint-load --session-id <VALUE>
```

**Arguments:**

- `--session-id`: **Required** | Type: string |   
  Session ID
- `--max-age`: **Optional** | Type: integer | Default: `24` |   
  Max age in hours (default: 24)
- `--phase`: **Optional** | Type: string |   
  Filter by specific phase (optional)
- `--output`: **Optional** | Type: string | Default: `table` | Choices: `table`, `json` |   
  Output format (also accepts --output json)
- `--format`: **Optional** | Type: string | Choices: `json`, `table` |   
  Output format (deprecated, use --output)

**Handler:** `handle_checkpoint_load_command`

---

### `checkpoint-list`

List checkpoints for session

**Usage:**
```bash
empirica checkpoint-list
```

**Arguments:**

- `--session-id`: **Optional** | Type: string |   
  Session ID (optional, lists all if omitted)
- `--limit`: **Optional** | Type: integer | Default: `10` |   
  Maximum checkpoints to show
- `--phase`: **Optional** | Type: string |   
  Filter by phase (optional)

**Handler:** `handle_checkpoint_list_command`

---

### `checkpoint-diff`

Show vector differences from last checkpoint

**Usage:**
```bash
empirica checkpoint-diff --session-id <VALUE>
```

**Arguments:**

- `--session-id`: **Required** | Type: string |   
  Session ID
- `--threshold`: **Optional** | Type: float | Default: `0.15` |   
  Significance threshold
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_checkpoint_diff_command`

---

### `checkpoint-sign`

Sign checkpoint with AI identity (Phase 2 - Crypto)

**Usage:**
```bash
empirica checkpoint-sign --session-id <VALUE> --phase <VALUE> --round <VALUE> --ai-id <VALUE>
```

**Arguments:**

- `--session-id`: **Required** | Type: string |   
  Session ID
- `--phase`: **Required** | Type: string | Choices: `PREFLIGHT`, `CHECK`, `ACT`, `POSTFLIGHT` |   
  Workflow phase
- `--round`: **Required** | Type: integer |   
  Round number
- `--ai-id`: **Required** | Type: string |   
  AI identity to sign with
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_checkpoint_sign_command`

---

### `checkpoint-verify`

Verify signed checkpoint (Phase 2 - Crypto)

**Usage:**
```bash
empirica checkpoint-verify --session-id <VALUE> --phase <VALUE> --round <VALUE>
```

**Arguments:**

- `--session-id`: **Required** | Type: string |   
  Session ID
- `--phase`: **Required** | Type: string | Choices: `PREFLIGHT`, `CHECK`, `ACT`, `POSTFLIGHT` |   
  Workflow phase
- `--round`: **Required** | Type: integer |   
  Round number
- `--ai-id`: **Optional** | Type: string |   
  AI identity (uses embedded public key if omitted)
- `--public-key`: **Optional** | Type: string |   
  Public key hex (overrides AI ID)
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_checkpoint_verify_command`

---

### `checkpoint-signatures`

List all signed checkpoints (Phase 2 - Crypto)

**Usage:**
```bash
empirica checkpoint-signatures
```

**Arguments:**

- `--session-id`: **Optional** | Type: string |   
  Filter by session ID (optional)
- `--ai-id`: **Optional** | Type: string |   
  AI identity (only needed if no local identities exist)
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_checkpoint_signatures_command`

---

### `handoff-create`

Create handoff report: epistemic (with CASCADE deltas) or planning (documentation-only)

**Usage:**
```bash
empirica handoff-create --session-id <VALUE> --task-summary <VALUE> --key-findings <VALUE> --next-session-context <VALUE> [OPTIONS]
```

**Arguments:**

- `--session-id`: **Required** | Type: string |   
  Session UUID
- `--task-summary`: **Required** | Type: string |   
  What was accomplished (2-3 sentences)
- `--summary`: **Optional** | Type: string |   
  Alias for --task-summary
- `--key-findings`: **Required** | Type: string |   
  JSON array of findings
- `--findings`: **Optional** | Type: string |   
  Alias for --key-findings
- `--remaining-unknowns`: **Optional** | Type: string |   
  JSON array of unknowns (optional)
- `--unknowns`: **Optional** | Type: string |   
  Alias for --remaining-unknowns
- `--next-session-context`: **Required** | Type: string |   
  Critical context for next session
- `--artifacts`: **Optional** | Type: string |   
  JSON array of files created (optional)
- `--planning-only`: **Optional** | Flag (default: `False`) |   
  Create planning handoff (no CASCADE workflow required) instead of epistemic handoff
- `--output`: **Optional** | Type: string | Default: `text` | Choices: `text`, `json` |   
  Output format

**Handler:** `handle_handoff_create_command`

---

### `handoff-query`

Query handoff reports

**Usage:**
```bash
empirica handoff-query
```

**Arguments:**

- `--session-id`: **Optional** | Type: string |   
  Specific session UUID
- `--ai-id`: **Optional** | Type: string |   
  Filter by AI ID
- `--limit`: **Optional** | Type: integer | Default: `5` |   
  Number of results (default: 5)
- `--output`: **Optional** | Type: string | Default: `text` | Choices: `text`, `json` |   
  Output format

**Handler:** `handle_handoff_query_command`

---

## Identity & Security

**4 commands**

### `identity-create`

Create new AI identity with Ed25519 keypair

**Usage:**
```bash
empirica identity-create --ai-id <VALUE> [OPTIONS]
```

**Arguments:**

- `--ai-id`: **Required** | Type: string |   
  AI identifier
- `--overwrite`: **Optional** | Flag (default: `False`) |   
  Overwrite existing identity
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_identity_create_command`

---

### `identity-list`

List all AI identities

**Usage:**
```bash
empirica identity-list
```

**Arguments:**

- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_identity_list_command`

---

### `identity-export`

Export public key for sharing

**Usage:**
```bash
empirica identity-export --ai-id <VALUE>
```

**Arguments:**

- `--ai-id`: **Required** | Type: string |   
  AI identifier
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_identity_export_command`

---

### `identity-verify`

Verify signed session

**Usage:**
```bash
empirica identity-verify
```

**Arguments:**

- `session_id` (positional): **Optional** | Type: string |   
  Session ID to verify
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_identity_verify_command`

---

## Configuration

**2 commands**

### `config`

Configuration management

**Usage:**
```bash
empirica config [OPTIONS]
```

**Arguments:**

- `key` (positional): **Optional** | Type: string |   
  Configuration key (dot notation, e.g., routing.default_strategy)
- `value` (positional): **Optional** | Type: string |   
  Value to set (if key provided)
- `--init`: **Optional** | Flag (default: `False`) |   
  Initialize configuration (replaces config-init)
- `--validate`: **Optional** | Flag (default: `False`) |   
  Validate configuration (replaces config-validate)
- `--section`: **Optional** | Type: string |   
  Show specific section (e.g., routing, adapters)
- `--format`: **Optional** | Type: string | Default: `yaml` | Choices: `yaml`, `json` |   
  Output format
- `--force`: **Optional** | Flag (default: `False`) |   
  Overwrite existing config (with --init)
- `--verbose`: **Optional** | Flag (default: `False`) |   
  Show detailed output

**Handler:** `handle_config_command`

---

### `monitor`

Monitoring dashboard and statistics

**Usage:**
```bash
empirica monitor [OPTIONS]
```

**Arguments:**

- `--export`: **Optional** | Type: string |   
  Export data to file (replaces monitor-export)
- `--reset`: **Optional** | Flag (default: `False`) |   
  Reset statistics (replaces monitor-reset)
- `--cost`: **Optional** | Flag (default: `False`) |   
  Show cost analysis (replaces monitor-cost)
- `--history`: **Optional** | Flag (default: `False`) |   
  Show recent request history
- `--health`: **Optional** | Flag (default: `False`) |   
  Include adapter health checks
- `--project`: **Optional** | Flag (default: `False`) |   
  Show cost projections (with --cost)
- `--format`: **Optional** | Type: string | Default: `json` | Choices: `json`, `csv` |   
  Export format (with --export)
- `--yes`: **Optional** | Flag (default: `False`) |   
  Skip confirmation (with --reset)
- `--verbose`: **Optional** | Flag (default: `False`) |   
  Show detailed stats

**Handler:** `handle_monitor_command`

---

## Monitoring

**1 commands**

### `check-drift`

Detect epistemic drift by comparing current state to historical baselines

**Usage:**
```bash
empirica check-drift --session-id <VALUE> [OPTIONS]
```

**Arguments:**

- `--session-id`: **Required** | Type: string |   
  Session UUID to check for drift
- `--threshold`: **Optional** | Type: float | Default: `0.2` |   
  Drift threshold (default: 0.2)
- `--lookback`: **Optional** | Type: integer | Default: `5` |   
  Number of checkpoints to analyze (default: 5)
- `--output`: **Optional** | Type: string | Default: `human` | Choices: `human`, `json` |   
  Output format
- `--verbose`: **Optional** | Flag (default: `False`) |   
  Show detailed output

**Handler:** `handle_check_drift_command`

---

## Utilities

**11 commands**

### `performance`

Analyze performance or run benchmarks

**Usage:**
```bash
empirica performance [OPTIONS]
```

**Arguments:**

- `--benchmark`: **Optional** | Flag (default: `False`) |   
  Run performance benchmarks (replaces benchmark command)
- `--target`: **Optional** | Type: string | Default: `system` |   
  Performance analysis target
- `--type`: **Optional** | Type: string | Default: `comprehensive` |   
  Benchmark/analysis type
- `--iterations`: **Optional** | Type: integer | Default: `10` |   
  Number of iterations (for benchmarks)
- `--memory`: **Optional** | Flag (default: `True`) |   
  Include memory analysis
- `--context`: **Optional** | Type: string |   
  JSON context data
- `--detailed`: **Optional** | Flag (default: `False`) |   
  Show detailed metrics
- `--verbose`: **Optional** | Flag (default: `False`) |   
  Show detailed results

**Handler:** `handle_performance_command`

---

### `skill-suggest`

Suggest skills for a task

**Usage:**
```bash
empirica skill-suggest [OPTIONS]
```

**Arguments:**

- `--task`: **Optional** | Type: string |   
  Task description to suggest skills for
- `--project-id`: **Optional** | Type: string |   
  Project ID for context-aware suggestions
- `--output`: **Optional** | Type: string | Default: `json` | Choices: `human`, `json` |   
  Output format
- `--verbose`: **Optional** | Flag (default: `False`) |   
  Show detailed suggestions

**Handler:** `handle_skill_suggest_command`

---

### `skill-fetch`

Fetch and normalize a skill

**Usage:**
```bash
empirica skill-fetch --name <VALUE> [OPTIONS]
```

**Arguments:**

- `--name`: **Required** | Type: string |   
  Skill name
- `--url`: **Optional** | Type: string |   
  URL to fetch skill from (markdown)
- `--file`: **Optional** | Type: string |   
  Local .skill archive file to load
- `--tags`: **Optional** | Type: string |   
  Comma-separated tags for the skill
- `--output`: **Optional** | Type: string | Default: `json` | Choices: `human`, `json` |   
  Output format
- `--verbose`: **Optional** | Flag (default: `False`) |   
  Show detailed output

**Handler:** `handle_skill_fetch_command`

---

### `goal-analysis`

Analyze goal feasibility

**Usage:**
```bash
empirica goal-analysis [OPTIONS]
```

**Arguments:**

- `goal` (positional): **Optional** | Type: string |   
  Goal to analyze
- `--context`: **Optional** | Type: string |   
  JSON context data
- `--verbose`: **Optional** | Flag (default: `False`) |   
  Show detailed analysis

**Handler:** `handle_goal_analysis_command`

---

### `efficiency-report`

Generate token efficiency report (Phase 1.5/2.0)

**Usage:**
```bash
empirica efficiency-report --session-id <VALUE>
```

**Arguments:**

- `--session-id`: **Required** | Type: string |   
  Session ID
- `--format`: **Optional** | Type: string | Default: `markdown` | Choices: `json`, `markdown`, `csv` |   
  Report format
- `--output`: **Optional** | Type: string |   
  Save to file (optional)

**Handler:** `handle_efficiency_report_command`

---

### `mistake-log`

Log a mistake for learning and future prevention

**Usage:**
```bash
empirica mistake-log --session-id <VALUE> --mistake <VALUE> --why-wrong <VALUE>
```

**Arguments:**

- `--session-id`: **Required** | Type: string |   
  Session UUID
- `--mistake`: **Required** | Type: string |   
  What was done wrong
- `--why-wrong`: **Required** | Type: string |   
  Explanation of why it was wrong
- `--cost-estimate`: **Optional** | Type: string |   
  Estimated time/effort wasted (e.g., "2 hours")
- `--root-cause-vector`: **Optional** | Type: string |   
  Epistemic vector that caused the mistake (e.g., "KNOW", "CONTEXT")
- `--prevention`: **Optional** | Type: string |   
  How to prevent this mistake in the future
- `--goal-id`: **Optional** | Type: string |   
  Optional goal identifier this mistake relates to
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_mistake_log_command`

---

### `mistake-query`

Query logged mistakes

**Usage:**
```bash
empirica mistake-query
```

**Arguments:**

- `--session-id`: **Optional** | Type: string |   
  Filter by session UUID
- `--goal-id`: **Optional** | Type: string |   
  Filter by goal UUID
- `--limit`: **Optional** | Type: integer | Default: `10` |   
  Number of results (default: 10)
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_mistake_query_command`

---

### `doc-check`

Compute documentation completeness and suggest updates

**Usage:**
```bash
empirica doc-check --project-id <VALUE> --project-id <VALUE> --task <VALUE>
```

**Arguments:**

- `--project-id`: **Required** | Type: string |   
  Project UUID
- `--session-id`: **Optional** | Type: string |   
  Optional session UUID for context
- `--goal-id`: **Optional** | Type: string |   
  Optional goal UUID for context
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format
- `--project-id`: **Required** | Type: string |   
  Project UUID
- `--task`: **Required** | Type: string |   
  Task description to search for
- `--type`: **Optional** | Type: string | Default: `all` | Choices: `all`, `docs`, `memory` |   
  Result type (default: all)
- `--limit`: **Optional** | Type: integer | Default: `5` |   
  Number of results to return (default: 5)
- `--output`: **Optional** | Type: string | Default: `default` | Choices: `default`, `json` |   
  Output format

**Handler:** `handle_doc_check_command`

---

### `onboard`

Interactive introduction to Empirica

**Usage:**
```bash
empirica onboard
```

**Handler:** `handle_onboard_command`

---

### `ask`

Ask a question (simple query interface for human users)

**Usage:**
```bash
empirica ask [OPTIONS]
```

**Arguments:**

- `query` (positional): **Optional** | Type: string |   
  Question to ask
- `--adapter`: **Optional** | Type: string |   
  Force specific adapter (qwen, minimax, gemini, etc.)
- `--model`: **Optional** | Type: string |   
  Force specific model (e.g., qwen-coder-turbo)
- `--strategy`: **Optional** | Type: string | Default: `epistemic` | Choices: `epistemic`, `cost`, `latency`, `quality`, `balanced` |   
  Routing strategy (default: epistemic)
- `--session`: **Optional** | Type: string |   
  Session ID for conversation tracking (auto-generated if not provided)
- `--temperature`: **Optional** | Type: float | Default: `0.7` |   
  Sampling temperature (0.0-1.0)
- `--max-tokens`: **Optional** | Type: integer | Default: `2000` |   
  Maximum response tokens
- `--no-save`: **Optional** | Flag (default: `True`) |   
  Don't save to session database
- `--verbose`: **Optional** | Flag (default: `False`) |   
  Show routing details

**Handler:** `handle_ask_command`

---

### `chat`

Interactive chat session (REPL for human users)

**Usage:**
```bash
empirica chat [OPTIONS]
```

**Arguments:**

- `--adapter`: **Optional** | Type: string |   
  Force specific adapter
- `--model`: **Optional** | Type: string |   
  Force specific model
- `--strategy`: **Optional** | Type: string | Default: `epistemic` | Choices: `epistemic`, `cost`, `latency`, `quality`, `balanced` |   
  Routing strategy
- `--session`: **Optional** | Type: string |   
  Session ID (creates new if doesn't exist)
- `--resume`: **Optional** | Type: string |   
  Resume existing session by ID
- `--no-save`: **Optional** | Flag (default: `True`) |   
  Don't save conversation
- `--verbose`: **Optional** | Flag (default: `False`) |   
  Show routing details

**Handler:** `handle_chat_command`

---

---

## Notes

- **Generated documentation:** This file is auto-generated from the codebase.
- **100% accuracy:** Every command listed here exists in the current codebase.
- **No phantom commands:** Commands not listed here do not exist.

**To regenerate this documentation:**
```bash
cd dev_scripts/doc_regeneration
python3 extract_cli_commands.py
python3 generate_cli_markdown.py
```

**Last updated:** 2025-12-16 20:33:14 UTC
