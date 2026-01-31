# Empirica CLI Commands - Unified Reference

**Total Commands:** 126
**Framework Version:** 1.4.0
**Generated:** 2026-01-21
**Status:** Production Ready

> **API Reference:** For Python API details, see [API Reference](../../reference/api/README.md). Each API doc includes relevant CLI commands.

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

### 3. Goals & Tasks (16 commands)
- **goals-create** - Create new goal with objective and scope
- **goals-list** - List all goals for a session or project
- **goals-list-all** - List all goals across all sessions
- **goals-complete** - Mark a goal as completed
- **goals-claim** - Claim a goal for work
- **goals-add-subtask** - Add subtask to an existing goal
- **goals-complete-subtask** - Mark a subtask as completed
- **goals-get-subtasks** - Get all subtasks for a goal
- **goals-progress** - Check progress of goals
- **goals-discover** - Discover new goals based on current state
- **goals-ready** - List ready goals for immediate work
- **goals-resume** - Resume work on a paused goal
- **goals-search** - Semantic search across goals and subtasks
- **goals-refresh** - Refresh goal activity timestamp
- **goals-mark-stale** - Mark session goals as stale (for memory compaction)
- **goals-get-stale** - Get list of stale goals

### 4. Project Management (8 commands)
- **project-init** - Initialize new project with configuration
- **project-create** - Create project entity in database
- **project-list** - List all projects
- **project-bootstrap** - Bootstrap project with context and goals
- **project-handoff** - Create AI-to-AI handoff report
- **project-search** - Search across projects
- **project-embed** - Create embeddings for project files
- **doc-check** - Check documentation quality and completeness

### 5. Workspace (5 commands)
- **workspace-init** - Initialize workspace for multi-project work
- **workspace-map** - Map all projects in workspace
- **workspace-overview** - Show overview of all projects in workspace
- **workspace-list** - List workspace projects with filtering by type, tags, hierarchy
- **ecosystem-check** - Check ecosystem topology, dependencies, and file impact

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

### 12. Monitoring (4 commands)
- **monitor** - Start monitoring session
- **check-drift** - Check for behavioral drift
- **efficiency-report** - Generate efficiency metrics
- **calibration-report** - Analyze AI self-assessment calibration

### 13. Skills (3 commands)
- **skill-suggest** - Suggest skills based on current work
- **skill-fetch** - Fetch skill from repository
- **skill-extract** - Extract decision frameworks from skills to meta-agent config

### 14. Agent Commands (7 commands)
- **agent-spawn** - Spawn epistemic sub-agent for investigation
- **agent-report** - Report findings from sub-agent back to parent
- **agent-aggregate** - Aggregate findings from multiple sub-agents
- **agent-discover** - Discover available agent capabilities
- **agent-export** - Export agent state for handoff
- **agent-import** - Import agent state from handoff
- **agent-parallel** - Run parallel investigation with epistemic attention budget

### 15. Persona Commands (4 commands)
- **persona-list** - List available personas for AI identity
- **persona-show** - Show detailed persona configuration
- **persona-promote** - Promote persona traits based on successful patterns
- **persona-find** - Find persona matching task characteristics

### 16. Assessment Commands (4 commands)
- **assess-state** - Assess current epistemic state
- **assess-component** - Assess specific component quality
- **assess-compare** - Compare two assessments side by side
- **assess-directory** - Assess documentation in a directory

### 17. Sentinel Commands (4 commands)
- **sentinel-status** - Show Sentinel gate status and health
- **sentinel-check** - Run Sentinel safety check on current operation
- **sentinel-load-profile** - Load Sentinel safety profile
- **sentinel-orchestrate** - Orchestrate multi-agent workflow with Sentinel gates

### 18. Trajectory Commands (4 commands)
- **trajectory-project** - Project epistemic trajectory based on current learning curve
- **trajectory-show** - Show epistemic trajectories with pattern analysis
- **trajectory-stats** - Show trajectory statistics across sessions
- **trajectory-backfill** - Backfill trajectory data from historic sessions

### 19. MCP Server Commands (5 commands)
- **mcp-start** - Start the Empirica MCP server
- **mcp-stop** - Stop the Empirica MCP server
- **mcp-status** - Show MCP server status
- **mcp-test** - Test MCP server connectivity
- **mcp-list-tools** - List available MCP tools

### 20. Concept Commands (4 commands)
- **concept-build** - Build concept index from project memory
- **concept-stats** - Show concept statistics for project
- **concept-top** - Show top concepts by frequency
- **concept-related** - Find semantically related concepts

### 21. Utilities (4 commands)
- **log-token-saving** - Log token savings from compression
- **config** - Configure Empirica settings
- **performance** - Show performance metrics
- **compact-analysis** - Analyze epistemic loss during memory compaction

### 22. Vision (1 command)
- **vision** - Vision processing and analysis

### 23. Epistemics (2 commands)
- **epistemics-list** - List epistemic assessments
- **epistemics-show** - Show detailed epistemic assessment

### 24. User Interface (1 command)
- **chat** - Interactive chat interface

### 25. Release & Docs (2 commands)
- **release-ready** - Check if codebase is ready for release (6-point verification)
- **docs-assess** - Assess documentation coverage using epistemic vectors

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

#### `goals-list-all`
**Purpose:** List all goals across all sessions (project-wide view)
**Usage:** `empirica goals-list-all [options]`
**Options:**
- `--status`: Filter by status (active, completed, all) - default: active
- `--limit`: Maximum goals to show (default: 20)
- `--output`: Output format (json, human)

#### `goals-search`
**Purpose:** Semantic search across goals and subtasks using Qdrant
**Usage:** `empirica goals-search <query> [options]`
**Options:**
- `--project-id`: Project ID (auto-detects if not provided)
- `--type`: Filter by type (goal, subtask)
- `--status`: Filter by status (in_progress, complete, pending)
- `--ai-id`: Filter by AI identifier
- `--limit`: Maximum results (default: 10)
- `--sync`: Sync SQLite goals to Qdrant before searching
- `--output`: Output format (json, human)

#### `goals-refresh`
**Purpose:** Refresh goal activity timestamp (mark as recently active)
**Usage:** `empirica goals-refresh --goal-id <goal_id> [options]`
**Options:**
- `--goal-id`: Goal UUID to refresh (required)
- `--output`: Output format (json, human)

#### `goals-mark-stale`
**Purpose:** Mark session goals as stale (called during memory compaction)
**Usage:** `empirica goals-mark-stale --session-id <session_id> [options]`
**Options:**
- `--session-id`: Session UUID (required)
- `--reason`: Reason for marking stale (default: memory_compact)
- `--output`: Output format (json, human)

#### `goals-get-stale`
**Purpose:** Get list of goals marked as stale
**Usage:** `empirica goals-get-stale [options]`
**Options:**
- `--session-id`: Filter by session ID
- `--project-id`: Filter by project ID
- `--output`: Output format (json, human)

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

#### `workspace-list`
**Purpose:** List workspace projects with filtering by type, tags, and hierarchy
**Usage:** `empirica workspace-list [options]`
**Options:**
- `--type`: Filter by project type (product, application, feature, research, documentation, infrastructure, operations)
- `--tags`: Filter by tags (comma-separated, matches any)
- `--parent`: Show only children of this project ID
- `--tree`: Show hierarchical tree view
- `--output`: Output format (human, json)

#### `ecosystem-check`
**Purpose:** Check ecosystem topology, project dependencies, and file impact analysis
**Usage:** `empirica ecosystem-check [options]`
**Options:**
- `--file`: File or module path to check downstream impact
- `--project`: Project name to show upstream/downstream dependencies
- `--role`: Filter projects by role (core, extension, ecosystem-tool, etc.)
- `--tag`: Filter projects by tag
- `--validate`: Validate ecosystem manifest integrity
- `--manifest`: Path to ecosystem.yaml (auto-detected if not specified)
- `--output`: Output format (human, json)

**Modes:**
- Default: Ecosystem summary (roles, types, roots, leaves, dependency tree)
- `--file F`: Show which downstream projects are affected by changes to file F
- `--project X`: Show upstream dependencies and downstream dependents of project X
- `--role R` / `--tag T`: Filter projects by role or tag
- `--validate`: Check manifest for missing projects, circular deps, undefined references

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

#### `calibration-report`
**Purpose:** Analyze AI self-assessment calibration using vector_trajectories data
**Usage:** `empirica calibration-report [--weeks N] [--output human|json|markdown]`

Measures gap from expected at session END (1.0 for most vectors, 0.0 for uncertainty).
Outputs per-vector bias corrections to ADD to self-assessments.

**Options:**
- `--weeks N` - Number of weeks to analyze (default: 8)
- `--ai-id ID` - Filter by AI identifier (default: claude-code)
- `--output FORMAT` - Output format: human (default), json, markdown
- `--update-prompt` - Generate copy-paste ready table for system prompts
- `--include-tests` - Include test sessions (normally filtered)
- `--min-samples N` - Minimum samples for confident analysis (default: 10)

**Example:**
```bash
# Human-readable calibration report
empirica calibration-report

# Markdown table for updating system prompts
empirica calibration-report --output markdown

# JSON for programmatic use
empirica calibration-report --output json --weeks 4
```

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

#### `log-token-saving`
**Purpose:** Log token savings from compression
**Usage:** `empirica log-token-saving --session-id <session_id> --tokens-saved <count>`

#### `config`
**Purpose:** Configure Empirica settings
**Usage:** `empirica config --get <setting> | --set <setting>=<value>`

#### `performance`
**Purpose:** Show performance metrics
**Usage:** `empirica performance --session-id <session_id>`

#### `compact-analysis`
**Purpose:** Analyze epistemic loss during memory compaction
**Usage:** `empirica compact-analysis [options]`
**Options:**
- `--include-tests`: Include test sessions (normally filtered)
- `--min-findings`: Minimum findings count to include session (default: 0)
- `--limit`: Maximum compact events to analyze (default: 20)
- `--output`: Output format (json, human)

**Notes:**
Retroactively analyzes pre-compact snapshots vs post-compact assessments to measure knowledge loss and recovery during Claude Code memory compaction.

Data Quality Filtering (default):
- Excludes test sessions (ai_id: test*, *-test, storage-*)
- Requires sessions with actual work evidence (findings/unknowns)
- Filters rapid-fire sessions (< 5 min duration)

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

### Agent Commands

#### `agent-spawn`
**Purpose:** Spawn an epistemic sub-agent for parallel investigation
**Usage:** `empirica agent-spawn --session-id <session_id> --task <task_description> [options]`
**Options:**
- `--session-id`: Parent session ID
- `--task`: Task description for the sub-agent
- `--depth`: Investigation depth (shallow, medium, deep)
- `--output`: Output format (json, human)

#### `agent-report`
**Purpose:** Report findings from sub-agent back to parent session
**Usage:** `empirica agent-report --session-id <session_id> --findings <json> [options]`
**Options:**
- `--session-id`: Sub-agent session ID
- `--findings`: JSON array of findings
- `--unknowns`: JSON array of remaining unknowns
- `--confidence`: Overall confidence score (0.0-1.0)

#### `agent-aggregate`
**Purpose:** Aggregate findings from multiple sub-agents into unified report
**Usage:** `empirica agent-aggregate --parent-session-id <session_id> [options]`
**Options:**
- `--parent-session-id`: Parent session that spawned sub-agents
- `--merge-strategy`: How to merge findings (union, intersection, weighted)
- `--output`: Output format (json, human)

#### `agent-discover`
**Purpose:** Discover available agent capabilities and specializations
**Usage:** `empirica agent-discover [options]`
**Options:**
- `--category`: Filter by capability category
- `--verbose`: Show detailed capability descriptions

#### `agent-export`
**Purpose:** Export agent state for handoff to another system
**Usage:** `empirica agent-export --session-id <session_id> --output-path <path>`

#### `agent-import`
**Purpose:** Import agent state from external handoff file
**Usage:** `empirica agent-import --input-path <path> --session-id <session_id>`

#### `agent-parallel`
**Purpose:** Run parallel investigation with epistemic attention budget allocation
**Usage:** `empirica agent-parallel --session-id <session_id> --task "<task>" [options]`
**Options:**
- `--budget`: Total findings budget across all agents (default: 20)
- `--max-agents`: Maximum parallel agents to spawn (default: 5)
- `--strategy`: Budget allocation strategy (information_gain, uniform, priority)
- `--domains`: Override investigation domains (auto-detected if not specified)
- `--output`: Output format (text, json)

**Description:** Spawns multiple investigation agents in parallel, each assigned a domain
and findings budget. Uses the AttentionBudget system to allocate resources based on
expected information gain. Results are aggregated via `agent-aggregate`.

---

### Persona Commands

#### `persona-list`
**Purpose:** List available personas that define AI identity and behavioral traits
**Usage:** `empirica persona-list [options]`
**Options:**
- `--active-only`: Show only active personas
- `--output`: Output format (json, human)

#### `persona-show`
**Purpose:** Show detailed configuration for a specific persona
**Usage:** `empirica persona-show --persona-id <persona_id>`

#### `persona-promote`
**Purpose:** Promote persona traits based on successful epistemic patterns
**Usage:** `empirica persona-promote --persona-id <persona_id> --trait <trait_name> --evidence <text>`
**Options:**
- `--persona-id`: Persona to update
- `--trait`: Trait to promote (e.g., "caution", "curiosity", "thoroughness")
- `--evidence`: Evidence from session that supports this promotion

#### `persona-find`
**Purpose:** Find persona matching current task characteristics
**Usage:** `empirica persona-find --task <task_description> [options]`
**Options:**
- `--task`: Task description to match
- `--session-id`: Session for context
- `--top-k`: Return top K matching personas

---

### Assessment Commands

#### `assess-state`
**Purpose:** Assess current epistemic state of a session or project
**Usage:** `empirica assess-state --session-id <session_id> [options]`
**Options:**
- `--session-id`: Session to assess
- `--include-history`: Include historical trajectory
- `--output`: Output format (json, human)

#### `assess-component`
**Purpose:** Assess quality of a specific codebase component
**Usage:** `empirica assess-component --path <component_path> [options]`
**Options:**
- `--path`: Path to component (file or directory)
- `--metrics`: Which metrics to include (quality, complexity, coverage)
- `--output`: Output format (json, human)

#### `assess-compare`
**Purpose:** Compare two assessments side by side
**Usage:** `empirica assess-compare --assessment-1 <id1> --assessment-2 <id2>`
**Options:**
- `--assessment-1`: First assessment ID
- `--assessment-2`: Second assessment ID
- `--show-delta`: Highlight differences

#### `assess-directory`
**Purpose:** Assess documentation coverage and quality in a directory
**Usage:** `empirica assess-directory --path <directory_path> [options]`
**Options:**
- `--path`: Directory to assess
- `--recursive`: Include subdirectories
- `--output`: Output format (json, human)

---

### Sentinel Commands

#### `sentinel-status`
**Purpose:** Show Sentinel gate status and overall system health
**Usage:** `empirica sentinel-status [options]`
**Options:**
- `--session-id`: Show status for specific session
- `--verbose`: Include detailed gate history

#### `sentinel-check`
**Purpose:** Run Sentinel safety check on proposed operation
**Usage:** `empirica sentinel-check --operation <operation_json> [options]`
**Options:**
- `--operation`: JSON description of proposed operation
- `--session-id`: Session context
- `--dry-run`: Check without recording result

**Returns:**
- `PROCEED`: Operation is safe to execute
- `HALT`: Operation blocked, requires human review
- `BRANCH`: Operation should spawn investigation first
- `REVISE`: Operation needs modification before proceeding

#### `sentinel-load-profile`
**Purpose:** Load a Sentinel safety profile for current session
**Usage:** `empirica sentinel-load-profile --profile <profile_name> --session-id <session_id>`
**Options:**
- `--profile`: Profile name (conservative, balanced, aggressive)
- `--session-id`: Session to apply profile to

#### `sentinel-orchestrate`
**Purpose:** Orchestrate multi-agent workflow with Sentinel gates between phases
**Usage:** `empirica sentinel-orchestrate --workflow <workflow_json> [options]`
**Options:**
- `--workflow`: JSON workflow definition
- `--session-id`: Parent session
- `--auto-proceed`: Automatically proceed on safe gates (dangerous)

---

### Trajectory Commands

#### `trajectory-project`
**Purpose:** Project epistemic trajectory based on current learning curve
**Usage:** `empirica trajectory-project --session-id <session_id> [options]`
**Options:**
- `--session-id`: Session to analyze
- `--horizon`: How far to project (sessions, hours, tasks)
- `--include-confidence`: Include confidence intervals

#### `trajectory-show`
**Purpose:** Show epistemic trajectories with pattern analysis
**Usage:** `empirica trajectory-show [options]`
**Options:**
- `--session-id`: Filter by session ID
- `--pattern`: Filter by pattern type (breakthrough, dead_end, stable, oscillating, unknown)
- `--limit`: Maximum trajectories to show (default: 10)
- `--output`: Output format (json, human)

#### `trajectory-stats`
**Purpose:** Show trajectory statistics across sessions
**Usage:** `empirica trajectory-stats [options]`
**Options:**
- `--output`: Output format (json, human)

#### `trajectory-backfill`
**Purpose:** Backfill trajectory data from historic sessions
**Usage:** `empirica trajectory-backfill [options]`
**Options:**
- `--min-phases`: Minimum phases required (default: 2)
- `--analyze`: Run pattern analysis after backfill
- `--output`: Output format (json, human)

---

### MCP Server Commands

#### `mcp-start`
**Purpose:** Start the Empirica MCP server
**Usage:** `empirica mcp-start [options]`
**Options:**
- `--verbose, -v`: Show detailed output

#### `mcp-stop`
**Purpose:** Stop the Empirica MCP server
**Usage:** `empirica mcp-stop [options]`
**Options:**
- `--verbose, -v`: Show detailed output

#### `mcp-status`
**Purpose:** Show MCP server status and process info
**Usage:** `empirica mcp-status [options]`
**Options:**
- `--verbose, -v`: Show detailed process info

#### `mcp-test`
**Purpose:** Test MCP server connectivity
**Usage:** `empirica mcp-test [options]`
**Options:**
- `--verbose, -v`: Show detailed output

#### `mcp-list-tools`
**Purpose:** List available MCP tools exposed by the server
**Usage:** `empirica mcp-list-tools [options]`
**Options:**
- `--verbose, -v`: Show usage examples
- `--show-all`: Include disabled/optional tools

---

### Concept Commands

#### `concept-build`
**Purpose:** Build concept index from project memory (findings, unknowns, etc.)
**Usage:** `empirica concept-build [options]`
**Options:**
- `--project-id`: Project ID (auto-detects if not provided)
- `--overwrite`: Overwrite existing concept data
- `--output`: Output format (json, human)

#### `concept-stats`
**Purpose:** Show concept statistics for project
**Usage:** `empirica concept-stats [options]`
**Options:**
- `--project-id`: Project ID (auto-detects if not provided)
- `--output`: Output format (json, human)

#### `concept-top`
**Purpose:** Show top concepts by frequency
**Usage:** `empirica concept-top [options]`
**Options:**
- `--project-id`: Project ID (auto-detects if not provided)
- `--limit`: Maximum concepts to show (default: 20)
- `--output`: Output format (json, human)

#### `concept-related`
**Purpose:** Find semantically related concepts
**Usage:** `empirica concept-related <search_term> [options]`
**Options:**
- `--project-id`: Project ID (auto-detects if not provided)
- `--limit`: Maximum related concepts to show (default: 10)
- `--output`: Output format (json, human)

---

### Skills Commands (Extended)

#### `skill-extract`
**Purpose:** Extract decision frameworks from skill definitions to meta-agent config
**Usage:** `empirica skill-extract --skill-dir <path> --output-file <path> [options]`
**Options:**
- `--skill-dir`: Single skill directory to extract
- `--skills-dir`: Directory containing multiple skills
- `--output-file`: Output meta-agent config file (default: meta-agent-config.yaml)
- `--verbose`: Show extraction details

---

### Release & Documentation Commands

#### `release-ready`
**Purpose:** Check if codebase is ready for release using 6-point epistemic verification
**Usage:** `empirica release-ready [options]`
**Options:**
- `--output`: Output format (json, human)
- `--verbose`: Show detailed check results

**Checks performed:**
1. **Version sync** - Verify version consistency across files
2. **Architecture assessment** - Epistemic assessment of codebase structure
3. **PyPI packages** - Check package configuration
4. **Privacy/security** - Scan for credential exposure
5. **Documentation** - Verify documentation coverage
6. **Git status** - Check for uncommitted changes

**Output:** Moon phase indicators for each check status

#### `docs-assess`
**Purpose:** Assess documentation coverage and quality using epistemic vectors
**Usage:** `empirica docs-assess --path <directory> [options]`
**Options:**
- `--path`: Directory to assess (default: current directory)
- `--output`: Output format (json, human)
- `--recursive`: Include subdirectories
- `--include-private`: Include private/internal docs

**Returns:**
- `know`: Documentation knowledge completeness (0.0-1.0)
- `uncertainty`: Documentation gaps (0.0-1.0)
- `coverage`: Percentage of features documented
- `recommendations`: Specific documentation gaps to address

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

**Generated from:** empirica --help output (2026-01-21)
**Total Commands:** 126
**Framework Version:** 1.4.0