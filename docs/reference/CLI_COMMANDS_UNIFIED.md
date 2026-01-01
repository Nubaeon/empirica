# Empirica CLI Commands - Unified Reference

**Total Commands:** 86
**Framework Version:** 1.2.1
**Generated:** 2025-12-28
**Status:** Production Ready

---

## Command Categories

### 1. Session Management (7 commands)
- **session-create** - Create new AI session with metadata
- **sessions-list** - List all sessions for an AI or project
- **sessions-show** - Show detailed information for a session
- **sessions-export** - Export session data to JSON
- **sessions-resume** - Resume a previous session
- **session-snapshot** - Create epistemic snapshot of current session
- **memory-compact** - Compact session memory and optimize storage

### 2. CASCADE Workflow (7 commands)
- **preflight** - Execute preflight epistemic assessment
- **preflight-submit** - Submit preflight assessment results
- **check** - Execute epistemic check during workflow
- **check-submit** - Submit check assessment results
- **postflight** - Execute postflight epistemic assessment
- **postflight-submit** - Submit postflight assessment results
- **workflow** - Execute complete CASCADE workflow (preflight→think→plan→investigate→act→postflight)

### 3. Goals & Tasks (11 commands)
- **goals-create** - Create new goal with objective and scope
- **goals-list** - List all goals for a session or project
- **goals-complete** - Mark a goal as completed
- **goals-claim** - Claim a goal for work
- **goals-add-subtask** - Add subtask to an existing goal
- **goals-complete-subtask** - Mark a subtask as completed
- **goals-get-subtasks** - Get all subtasks for a goal
- **goals-progress** - Check progress of goals
- **goals-discover** - Discover new goals based on current state
- **goals-ready** - List ready goals for immediate work
- **goals-resume** - Resume work on a paused goal

### 4. Project Management (8 commands)
- **project-init** - Initialize new project with configuration
- **project-create** - Create project entity in database
- **project-list** - List all projects
- **project-bootstrap** - Bootstrap project with context and goals
- **project-handoff** - Create AI-to-AI handoff report
- **project-search** - Search across projects
- **project-embed** - Create embeddings for project files
- **doc-check** - Check documentation quality and completeness

### 5. Workspace (3 commands)
- **workspace-init** - Initialize workspace for multi-project work
- **workspace-map** - Map all projects in workspace
- **workspace-overview** - Show overview of all projects in workspace

### 6. Checkpoints (7 commands)
- **checkpoint-create** - Create checkpoint from current state
- **checkpoint-load** - Load from a previous checkpoint
- **checkpoint-list** - List all available checkpoints
- **checkpoint-diff** - Show differences between checkpoints
- **checkpoint-sign** - Cryptographically sign a checkpoint
- **checkpoint-verify** - Verify checkpoint signature integrity
- **checkpoint-signatures** - List all checkpoint signatures

### 7. Identity (4 commands)
- **identity-create** - Create new AI identity with cryptographic keys
- **identity-export** - Export AI identity for sharing
- **identity-list** - List available AI identities
- **identity-verify** - Verify AI identity authenticity

### 8. Handoffs (2 commands)
- **handoff-create** - Create AI-to-AI handoff
- **handoff-query** - Query for available handoffs

### 9. Logging (9 commands)
- **finding-log** - Log new finding discovered during work
- **unknown-log** - Log unknown or unresolved question
- **unknown-resolve** - Mark unknown as resolved with explanation
- **deadend-log** - Log dead end or failed approach
- **refdoc-add** - Add reference documentation
- **mistake-log** - Log mistake made during work
- **mistake-query** - Query for logged mistakes
- **act-log** - Log action taken with confidence score
- **investigate-log** - Log investigation activities

### 10. Issue Capture (6 commands)
- **issue-list** - List all captured issues
- **issue-show** - Show details of a specific issue
- **issue-handoff** - Handoff issue to another AI
- **issue-resolve** - Resolve an issue with solution
- **issue-export** - Export issues to external system
- **issue-stats** - Show statistics about issues

### 11. Investigation (4 commands)
- **investigate** - Start investigation workflow
- **investigate-create-branch** - Create investigation branch
- **investigate-checkpoint-branch** - Checkpoint investigation branch
- **investigate-merge-branches** - Merge investigation branches

### 12. Monitoring (3 commands)
- **monitor** - Start monitoring session
- **check-drift** - Check for behavioral drift
- **efficiency-report** - Generate efficiency metrics

### 13. Skills (2 commands)
- **skill-suggest** - Suggest skills based on current work
- **skill-fetch** - Fetch skill from repository

### 14. Utilities (4 commands)
- **goal-analysis** - Analyze goal completion patterns
- **log-token-saving** - Log token savings from compression
- **config** - Configure Empirica settings
- **performance** - Show performance metrics

### 15. Vision (1 command)
- **vision** - Vision processing and analysis

### 16. Epistemics (2 commands)
- **epistemics-list** - List epistemic assessments
- **epistemics-show** - Show detailed epistemic assessment

### 17. User Interface (1 command)
- **chat** - Interactive chat interface

---

## Command Details

### Session Management Commands

#### `session-create`
**Purpose:** Create a new AI session with metadata tracking
**Usage:** `empirica session-create --ai-id <ai_identifier> [options]`
**Options:**
- `--ai-id`: AI identifier for the session
- `--user-id`: Optional user identifier
- `--project-id`: Optional project association

#### `sessions-list`
**Purpose:** List all sessions with filtering options
**Usage:** `empirica sessions-list [options]`
**Options:**
- `--ai-id`: Filter by AI identifier
- `--limit`: Limit number of results
- `--status`: Filter by session status

#### `sessions-show`
**Purpose:** Show detailed information for a specific session
**Usage:** `empirica sessions-show --session-id <session_id>`

#### `sessions-export`
**Purpose:** Export session data to JSON format
**Usage:** `empirica sessions-export --session-id <session_id> --output <file_path>`

#### `sessions-resume`
**Purpose:** Resume a previous session with context restoration
**Usage:** `empirica sessions-resume --session-id <session_id>`

#### `session-snapshot`
**Purpose:** Create an epistemic snapshot of current session state
**Usage:** `empirica session-snapshot --session-id <session_id>`

#### `memory-compact`
**Purpose:** Compact session memory and optimize storage
**Usage:** `empirica memory-compact --session-id <session_id>`

---

### CASCADE Workflow Commands

#### `preflight`
**Purpose:** Execute preflight epistemic assessment before work begins
**Usage:** `empirica preflight <task_description> [options]`
**Options:**
- `--session-id`: Session ID (auto-generated if not provided)
- `--ai-id`: AI identifier
- `--prompt-only`: Return only the self-assessment prompt (no waiting)
- `--assessment-json`: Genuine AI self-assessment JSON
- `--output`: Output format (human, json)

#### `preflight-submit`
**Purpose:** Submit preflight assessment results
**Usage:** `empirica preflight-submit --session-id <session_id> --vectors <json>`

#### `check`
**Purpose:** Execute epistemic check during workflow
**Usage:** `empirica check --session-id <session_id> [options]`
**Options:**
- `--findings`: Investigation findings as JSON array
- `--unknowns`: Remaining unknowns as JSON array
- `--confidence`: Confidence score (0.0-1.0)

#### `check-submit`
**Purpose:** Submit check assessment results
**Usage:** `empirica check-submit --session-id <session_id> --vectors <json> --decision <decision>`

#### `postflight`
**Purpose:** Execute postflight epistemic assessment after work completes
**Usage:** `empirica postflight --session-id <session_id> --vectors <json> [options]`
**Options:**
- `--reasoning`: Description of what changed from preflight
- `--output`: Output format

#### `postflight-submit`
**Purpose:** Submit postflight assessment results
**Usage:** `empirica postflight-submit --session-id <session_id> --vectors <json>`

#### `workflow`
**Purpose:** Execute complete CASCADE workflow
**Usage:** `empirica workflow <task_description> [options]`
**Options:**
- `--session-id`: Session ID (auto-generated if not provided)
- `--auto`: Skip manual pauses between phases

---

### Goals & Tasks Commands

#### `goals-create`
**Purpose:** Create new goal with objective and scope
**Usage:** `empirica goals-create --objective <text> --scope <text> [options]`
**Options:**
- `--session-id`: Associated session ID
- `--estimated-complexity`: Estimated complexity score (0.0-1.0)

#### `goals-list`
**Purpose:** List all goals with filtering options
**Usage:** `empirica goals-list [options]`
**Options:**
- `--session-id`: Filter by session ID
- `--completed`: Show only completed goals
- `--status`: Filter by status (in_progress, complete, blocked)

#### `goals-complete`
**Purpose:** Mark a goal as completed
**Usage:** `empirica goals-complete --goal-id <goal_id>`

#### `goals-claim`
**Purpose:** Claim a goal for work
**Usage:** `empirica goals-claim --goal-id <goal_id> --claimer-id <ai_id>`

#### `goals-add-subtask`
**Purpose:** Add subtask to an existing goal
**Usage:** `empirica goals-add-subtask --goal-id <goal_id> --description <text> [options]`
**Options:**
- `--epistemic-importance`: Importance level (low, medium, high)
- `--estimated-tokens`: Estimated token usage

#### `goals-complete-subtask`
**Purpose:** Mark a subtask as completed
**Usage:** `empirica goals-complete-subtask --subtask-id <subtask_id> --evidence <text>`

#### `goals-get-subtasks`
**Purpose:** Get all subtasks for a goal
**Usage:** `empirica goals-get-subtasks --goal-id <goal_id>`

#### `goals-progress`
**Purpose:** Check progress of goals
**Usage:** `empirica goals-progress --goal-id <goal_id>`

#### `goals-discover`
**Purpose:** Discover new goals based on current state
**Usage:** `empirica goals-discover --session-id <session_id>`

#### `goals-ready`
**Purpose:** List ready goals for immediate work
**Usage:** `empirica goals-ready [options]`
**Options:**
- `--session-id`: Filter by session ID
- `--limit`: Limit number of results

#### `goals-resume`
**Purpose:** Resume work on a paused goal
**Usage:** `empirica goals-resume --goal-id <goal_id>`

---

### Project Management Commands

#### `project-init`
**Purpose:** Initialize new project with configuration
**Usage:** `empirica project-init --name <project_name> [options]`
**Options:**
- `--description`: Project description
- `--repos`: Comma-separated list of repository URLs

#### `project-create`
**Purpose:** Create project entity in database
**Usage:** `empirica project-create --name <project_name>`

#### `project-list`
**Purpose:** List all projects
**Usage:** `empirica project-list`

#### `project-bootstrap`
**Purpose:** Bootstrap project with context and goals
**Usage:** `empirica project-bootstrap [options]`
**Options:**
- `--project-id`: Specific project ID to bootstrap
- `--output`: Output format (json, human)

#### `project-handoff`
**Purpose:** Create AI-to-AI handoff report
**Usage:** `empirica project-handoff --project-id <project_id>`

#### `project-search`
**Purpose:** Search across projects
**Usage:** `empirica project-search --query <search_term>`

#### `project-embed`
**Purpose:** Create embeddings for project files
**Usage:** `empirica project-embed --project-id <project_id>`

#### `doc-check`
**Purpose:** Check documentation quality and completeness
**Usage:** `empirica doc-check --project-id <project_id>`

---

### Workspace Commands

#### `workspace-init`
**Purpose:** Initialize workspace for multi-project work
**Usage:** `empirica workspace-init --name <workspace_name>`

#### `workspace-map`
**Purpose:** Map all projects in workspace
**Usage:** `empirica workspace-map`

#### `workspace-overview`
**Purpose:** Show overview of all projects in workspace
**Usage:** `empirica workspace-overview`

---

### Checkpoint Commands

#### `checkpoint-create`
**Purpose:** Create checkpoint from current state
**Usage:** `empirica checkpoint-create --session-id <session_id> [options]`
**Options:**
- `--name`: Checkpoint name
- `--description`: Checkpoint description

#### `checkpoint-load`
**Purpose:** Load from a previous checkpoint
**Usage:** `empirica checkpoint-load --checkpoint-id <checkpoint_id>`

#### `checkpoint-list`
**Purpose:** List all available checkpoints
**Usage:** `empirica checkpoint-list --session-id <session_id>`

#### `checkpoint-diff`
**Purpose:** Show differences between checkpoints
**Usage:** `empirica checkpoint-diff --checkpoint-id-1 <id1> --checkpoint-id-2 <id2>`

#### `checkpoint-sign`
**Purpose:** Cryptographically sign a checkpoint
**Usage:** `empirica checkpoint-sign --checkpoint-id <checkpoint_id>`

#### `checkpoint-verify`
**Purpose:** Verify checkpoint signature integrity
**Usage:** `empirica checkpoint-verify --checkpoint-id <checkpoint_id>`

#### `checkpoint-signatures`
**Purpose:** List all checkpoint signatures
**Usage:** `empirica checkpoint-signatures --checkpoint-id <checkpoint_id>`

---

### Identity Commands

#### `identity-create`
**Purpose:** Create new AI identity with cryptographic keys
**Usage:** `empirica identity-create --ai-id <ai_identifier>`

#### `identity-export`
**Purpose:** Export AI identity for sharing
**Usage:** `empirica identity-export --ai-id <ai_identifier>`

#### `identity-list`
**Purpose:** List available AI identities
**Usage:** `empirica identity-list`

#### `identity-verify`
**Purpose:** Verify AI identity authenticity
**Usage:** `empirica identity-verify --identity-file <file_path>`

---

### Handoff Commands

#### `handoff-create`
**Purpose:** Create AI-to-AI handoff
**Usage:** `empirica handoff-create --session-id <session_id>`

#### `handoff-query`
**Purpose:** Query for available handoffs
**Usage:** `empirica handoff-query --project-id <project_id>`

---

### Logging Commands

#### `finding-log`
**Purpose:** Log new finding discovered during work
**Usage:** `empirica finding-log --finding <text> [options]`
**Options:**
- `--session-id`: Associated session ID
- `--project-id`: Associated project ID
- `--goal-id`: Associated goal ID

#### `unknown-log`
**Purpose:** Log unknown or unresolved question
**Usage:** `empirica unknown-log --unknown <text> [options]`
**Options:**
- `--session-id`: Associated session ID
- `--project-id`: Associated project ID
- `--goal-id`: Associated goal ID

#### `unknown-resolve`
**Purpose:** Mark an unknown as resolved with explanation of how it was resolved
**Usage:** `empirica unknown-resolve --unknown-id <uuid> --resolved-by <text> [options]`
**Options:**
- `--unknown-id`: UUID of the unknown to resolve (required)
- `--resolved-by`: Description of how the unknown was resolved (required)
- `--output`: Output format (json, human) - default: json
- `--verbose`: Show detailed operation info

**Example:**
```bash
# JSON output (default, AI-first)
empirica unknown-resolve \
  --unknown-id "73a93233-0999-455b-83e5-5cd50d4c1e95" \
  --resolved-by "Token refresh uses 24hr sliding window per OAuth2 spec"

# Human-readable output
empirica unknown-resolve \
  --unknown-id "bd0bb320-38a0-45f6-ba9d-0f782c5843c2" \
  --resolved-by "Design confirmed via architecture review" \
  --output human
```

**Workflow:**
1. Log unknown: `empirica unknown-log --session-id <ID> --unknown "Token refresh timing unclear"`
2. Investigate and discover answer through research/testing
3. Resolve: `empirica unknown-resolve --unknown-id <ID> --resolved-by "Explanation of resolution"`

**Database Impact:**
- Sets `is_resolved = TRUE` in project_unknowns table
- Populates `resolved_by` field with explanation
- Records `resolved_timestamp` as current Unix timestamp

**Pattern:** Follows same design as `issue-resolve` - separate create (unknown-log) vs update (unknown-resolve) operations

#### `deadend-log`
**Purpose:** Log dead end or failed approach
**Usage:** `empirica deadend-log --approach <text> --why-failed <text> [options]`
**Options:**
- `--session-id`: Associated session ID
- `--project-id`: Associated project ID
- `--goal-id`: Associated goal ID

#### `refdoc-add`
**Purpose:** Add reference documentation
**Usage:** `empirica refdoc-add --doc-path <path> --description <text> [options]`

#### `mistake-log`
**Purpose:** Log mistake made during work
**Usage:** `empirica mistake-log --mistake <text> --why-wrong <text> [options]`

#### `mistake-query`
**Purpose:** Query for logged mistakes
**Usage:** `empirica mistake-query --session-id <session_id>`

#### `act-log`
**Purpose:** Log action taken with confidence score
**Usage:** `empirica act-log --action-type <type> --rationale <text> [options]`

#### `investigate-log`
**Purpose:** Log investigation activities
**Usage:** `empirica investigate-log --activity <text> [options]`

---

### Issue Capture Commands

#### `issue-list`
**Purpose:** List all captured issues
**Usage:** `empirica issue-list [options]`
**Options:**
- `--status`: Filter by status (open, closed, in_progress)
- `--severity`: Filter by severity (low, medium, high, critical)

#### `issue-show`
**Purpose:** Show details of a specific issue
**Usage:** `empirica issue-show --issue-id <issue_id>`

#### `issue-handoff`
**Purpose:** Handoff issue to another AI
**Usage:** `empirica issue-handoff --issue-id <issue_id> --recipient <ai_id>`

#### `issue-resolve`
**Purpose:** Resolve an issue with solution
**Usage:** `empirica issue-resolve --issue-id <issue_id> --solution <text>`

#### `issue-export`
**Purpose:** Export issues to external system
**Usage:** `empirica issue-export --format <json,csv>`

#### `issue-stats`
**Purpose:** Show statistics about issues
**Usage:** `empirica issue-stats`

---

### Investigation Commands

#### `investigate`
**Purpose:** Start investigation workflow
**Usage:** `empirica investigate --session-id <session_id> --query <text>`

#### `investigate-create-branch`
**Purpose:** Create investigation branch
**Usage:** `empirica investigate-create-branch --session-id <session_id> --branch-name <name>`

#### `investigate-checkpoint-branch`
**Purpose:** Checkpoint investigation branch
**Usage:** `empirica investigate-checkpoint-branch --branch-id <branch_id>`

#### `investigate-merge-branches`
**Purpose:** Merge investigation branches
**Usage:** `empirica investigate-merge-branches --session-id <session_id> --branch-ids <id1,id2>`

---

### Monitoring Commands

#### `monitor`
**Purpose:** Start monitoring session
**Usage:** `empirica monitor --session-id <session_id>`

#### `check-drift`
**Purpose:** Check for behavioral drift
**Usage:** `empirica check-drift --session-id <session_id>`

#### `efficiency-report`
**Purpose:** Generate efficiency metrics
**Usage:** `empirica efficiency-report --session-id <session_id>`

---

### Skills Commands

#### `skill-suggest`
**Purpose:** Suggest skills based on current work
**Usage:** `empirica skill-suggest --context <text>`

#### `skill-fetch`
**Purpose:** Fetch skill from repository
**Usage:** `empirica skill-fetch --skill-id <skill_id>`

---

### Utilities Commands

#### `goal-analysis`
**Purpose:** Analyze goal completion patterns
**Usage:** `empirica goal-analysis --session-id <session_id>`

#### `log-token-saving`
**Purpose:** Log token savings from compression
**Usage:** `empirica log-token-saving --session-id <session_id> --tokens-saved <count>`

#### `config`
**Purpose:** Configure Empirica settings
**Usage:** `empirica config --get <setting> | --set <setting>=<value>`

#### `performance`
**Purpose:** Show performance metrics
**Usage:** `empirica performance --session-id <session_id>`

---

### Vision Commands

#### `vision`
**Purpose:** Vision processing and analysis
**Usage:** `empirica vision --image-path <path> --prompt <text>`

---

### Epistemics Commands

#### `epistemics-list`
**Purpose:** List epistemic assessments
**Usage:** `empirica epistemics-list --session-id <session_id>`

#### `epistemics-show`
**Purpose:** Show detailed epistemic assessment
**Usage:** `empirica epistemics-show --assessment-id <assessment_id>`

---

### User Interface Commands

#### `chat`
**Purpose:** Interactive chat interface
**Usage:** `empirica chat --session-id <session_id>`

---

## Global Options

All commands support these global options:

- `--verbose, -v`: Enable verbose output (shows DB path, execution time, etc.)
- `--config CONFIG`: Path to configuration file
- `--version`: Show program's version number

**Global Flags (must come BEFORE command name):**
```
empirica [--version] [--verbose] <command> [args]
```

**Examples:**
```
empirica session-create --ai-id myai      # Create session
empirica --verbose sessions-list          # Show debug info
empirica preflight-submit --session-id xyz # PREFLIGHT
empirica --verbose check --session-id xyz # CHECK with debugging
```

---

## Command Philosophy

**AI-First Design:** All commands are designed for AI agents to use autonomously, with structured JSON output and consistent error handling.

**Epistemic Self-Awareness:** Commands capture epistemic state at each step, enabling genuine self-assessment rather than heuristic-based evaluation.

**Modular Architecture:** Commands are organized in logical modules that can be extended independently while maintaining consistency.

---

**Generated from:** empirica --help output (2025-12-28)
**Total Commands:** 86
**Framework Version:** 1.2.1