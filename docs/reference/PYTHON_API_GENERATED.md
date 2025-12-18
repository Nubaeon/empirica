# Empirica Python API Reference (v4.0)

**Generated from code:** 2025-12-16
**Total modules:** 3
**Total classes:** 3
**Total functions:** 3

---

## Table of Contents

- [session_database](#session-database)
- [branch_mapping](#branch-mapping)
- [doc_code_integrity](#doc-code-integrity)

---

## session_database

**Module:** `data/session_database.py`

**1 classes**

### `SessionDatabase`

**Module:** `data/session_database.py`

Central SQLite database for all session data

**Methods:**

#### `__init__(self, db_path: Optional[str] = None)`

**Parameters:**

- `db_path: Optional = None`

#### `add_epistemic_source(self, project_id: str, source_type: str, title: str, session_id: Optional[str] = None, source_url: Optional[str] = None, description: Optional[str] = None, confidence: float = 0.5, epistemic_layer: Optional[str] = None, supports_vectors: Optional[Dict[str, float]] = None, related_findings: Optional[List[str]] = None, discovered_by_ai: Optional[str] = None, source_metadata: Optional[Dict] = None) -> str`

Add an epistemic source to ground project knowledge

Args:
    project_id: Project identifier
    source_type: Type of source ('url', 'doc', 'code_ref', 'paper', 'api_doc', 'git_commit', 'chat_transcript', 'epistemic_snapshot')
    title: Source title
    session_id: Optional session that discovered this source
    source_url: Optional URL or path
    description: Optional description
    confidence: Confidence in this source (0.0-1.0, default 0.5)
    epistemic_layer: Optional layer ('noetic', 'epistemic', 'action')
    supports_vectors: Optional dict of epistemic vectors this source supports
    related_findings: Optional list of finding IDs
    discovered_by_ai: Optional AI identifier
    source_metadata: Optional metadata dict
    
Returns:
    source_id: UUID string

**Parameters:**

- `project_id: str`
- `source_type: str`
- `title: str`
- `session_id: Optional = None`
- `source_url: Optional = None`
- `description: Optional = None`
- `confidence: float = 0.5`
- `epistemic_layer: Optional = None`
- `supports_vectors: Optional = None`
- `related_findings: Optional = None`
- `discovered_by_ai: Optional = None`
- `source_metadata: Optional = None`

**Returns:** `str`

#### `add_reference_doc(self, project_id: str, doc_path: str, doc_type: Optional[str] = None, description: Optional[str] = None) -> str`

Add a reference document to project (delegates to BreadcrumbRepository)

**Parameters:**

- `project_id: str`
- `doc_path: str`
- `doc_type: Optional = None`
- `description: Optional = None`

**Returns:** `str`

#### `aggregate_project_learning_deltas(self, project_id: str) -> Dict[str, float]`

Compute total epistemic learning across all project sessions (delegates to ProjectRepository)

**Parameters:**

- `project_id: str`

**Returns:** `Dict`

#### `bootstrap_project_breadcrumbs(self, project_id: str, mode: str = 'session_start', project_root: str = None, check_integrity: bool = False, task_description: str = None, epistemic_state: Dict[str, float] = None, context_to_inject: bool = False, subject: Optional[str] = None) -> Dict`

Generate epistemic breadcrumbs for starting a new session on existing project.

Args:
    project_id: Project identifier (UUID or project name)
    mode: "session_start" (fast, recent items) or "live" (complete, all items)
    project_root: Optional path to project root (defaults to cwd)
    check_integrity: If True, analyze doc-code integrity (adds ~2s)
    task_description: Task description for context load balancing (optional)
    epistemic_state: Epistemic vectors (uncertainty, know, do, etc.) for intelligent routing (optional)
    context_to_inject: If True, generate markdown context string for AI prompt injection (optional)

Returns quick context: findings, unknowns, dead_ends, mistakes, decisions, incomplete work, suggested skills.

**Parameters:**

- `project_id: str`
- `mode: str = 'session_start'`
- `project_root: str = None`
- `check_integrity: bool = False`
- `task_description: str = None`
- `epistemic_state: Dict = None`
- `context_to_inject: bool = False`
- `subject: Optional = None`

**Returns:** `Dict`

#### `calculate_branch_merge_score(self, branch_id: str) -> Dict`

Calculate epistemic merge score for a branch (delegates to BranchRepository)

Score = (learning_delta × quality × confidence) / cost_penalty
Where: confidence = 1 - uncertainty (uncertainty is a DAMPENER)

Returns:
    Dict with merge_score, quality, and rationale

**Parameters:**

- `branch_id: str`

**Returns:** `Dict`

#### `checkpoint_branch(self, branch_id: str, postflight_vectors: Dict, tokens_spent: int, time_spent_minutes: int) -> bool`

Checkpoint a branch after investigation (delegates to BranchRepository)

Args:
    branch_id: Branch ID
    postflight_vectors: Epistemic vectors after investigation
    tokens_spent: Tokens used in investigation
    time_spent_minutes: Time spent in investigation

Returns:
    Success boolean

**Parameters:**

- `branch_id: str`
- `postflight_vectors: Dict`
- `tokens_spent: int`
- `time_spent_minutes: int`

**Returns:** `bool`

#### `close(self)`

Close database connection

#### `complete_cascade(self, cascade_id: str, final_action: str, final_confidence: float, investigation_rounds: int, duration_ms: int, engagement_gate_passed: bool, bayesian_active: bool = False, drift_monitored: bool = False)`

Mark cascade as completed with final results

**Parameters:**

- `cascade_id: str`
- `final_action: str`
- `final_confidence: float`
- `investigation_rounds: int`
- `duration_ms: int`
- `engagement_gate_passed: bool`
- `bayesian_active: bool = False`
- `drift_monitored: bool = False`

#### `complete_subtask(self, subtask_id: str, evidence: str)`

Mark subtask as completed with evidence (delegates to GoalRepository)

Args:
    subtask_id: Subtask UUID
    evidence: Evidence of completion (e.g., "Documented in design doc", "PR merged")

**Parameters:**

- `subtask_id: str`
- `evidence: str`

#### `create_branch(self, session_id: str, branch_name: str, investigation_path: str, git_branch_name: str, preflight_vectors: Dict) -> str`

Create a new investigation branch (delegates to BranchRepository)

Args:
    session_id: Session UUID
    branch_name: Human-readable branch name
    investigation_path: What is being investigated (e.g., 'oauth2')
    git_branch_name: Git branch name
    preflight_vectors: Epistemic vectors at branch start

Returns:
    Branch ID

**Parameters:**

- `session_id: str`
- `branch_name: str`
- `investigation_path: str`
- `git_branch_name: str`
- `preflight_vectors: Dict`

**Returns:** `str`

#### `create_cascade(self, session_id: str, task: str, context: Dict[str, Any], goal_id: Optional[str] = None, goal: Optional[Dict[str, Any]] = None) -> str`

Create cascade record, return cascade_id

Args:
    session_id: Session identifier
    task: Task description
    context: Context dictionary
    goal_id: Optional goal identifier
    goal: Optional full goal object

**Parameters:**

- `session_id: str`
- `task: str`
- `context: Dict`
- `goal_id: Optional = None`
- `goal: Optional = None`

**Returns:** `str`

#### `create_goal(self, session_id: str, objective: str, scope_breadth: float = None, scope_duration: float = None, scope_coordination: float = None) -> str`

Create a new goal for this session (delegates to GoalRepository)

Args:
    session_id: Session UUID
    objective: What are you trying to accomplish?
    scope_breadth: 0.0-1.0 (0=single file, 1=entire codebase)
    scope_duration: 0.0-1.0 (0=minutes, 1=months)
    scope_coordination: 0.0-1.0 (0=solo, 1=heavy multi-agent)

Returns:
    goal_id (UUID string)

**Parameters:**

- `session_id: str`
- `objective: str`
- `scope_breadth: float = None`
- `scope_duration: float = None`
- `scope_coordination: float = None`

**Returns:** `str`

#### `create_project(self, name: str, description: Optional[str] = None, repos: Optional[List[str]] = None) -> str`

Create a new project (delegates to ProjectRepository)

Args:
    name: Project name (e.g., "Empirica Core")
    description: Project description
    repos: List of repository names (e.g., ["empirica", "empirica-dev"])

Returns:
    project_id: UUID string

**Parameters:**

- `name: str`
- `description: Optional = None`
- `repos: Optional = None`

**Returns:** `str`

#### `create_project_handoff(self, project_id: str, project_summary: str, key_decisions: Optional[List[str]] = None, patterns_discovered: Optional[List[str]] = None, remaining_work: Optional[List[str]] = None) -> str`

Create project-level handoff report (delegates to ProjectRepository)

**Parameters:**

- `project_id: str`
- `project_summary: str`
- `key_decisions: Optional = None`
- `patterns_discovered: Optional = None`
- `remaining_work: Optional = None`

**Returns:** `str`

#### `create_session(self, ai_id: str, bootstrap_level: int = 0, components_loaded: int = 0, user_id: Optional[str] = None, subject: Optional[str] = None) -> str`

Create new session, return session_id.

Args:
    ai_id: AI identifier (required)
    bootstrap_level: Bootstrap level (0-4 or minimal/standard/complete) - default 0
    components_loaded: Number of components loaded - default 0 (components created on-demand)
    user_id: Optional user identifier
    subject: Optional subject/workstream identifier for filtering
    
Returns:
    session_id: UUID string

**Parameters:**

- `ai_id: str`
- `bootstrap_level: int = 0`
- `components_loaded: int = 0`
- `user_id: Optional = None`
- `subject: Optional = None`

**Returns:** `str`

#### `create_subtask(self, goal_id: str, description: str, importance: str = 'medium') -> str`

Create a subtask within a goal (delegates to GoalRepository)

Args:
    goal_id: Parent goal UUID
    description: What are you investigating/implementing?
    importance: 'critical' | 'high' | 'medium' | 'low'

Returns:
    subtask_id (UUID string)

**Parameters:**

- `goal_id: str`
- `description: str`
- `importance: str = 'medium'`

**Returns:** `str`

#### `end_session(self, session_id: str, avg_confidence: Optional[float] = None, drift_detected: bool = False, notes: Optional[str] = None)`

Mark session as ended

**Parameters:**

- `session_id: str`
- `avg_confidence: Optional = None`
- `drift_detected: bool = False`
- `notes: Optional = None`

#### `get_all_sessions(self, ai_id: Optional[str] = None, limit: int = 50) -> List[Dict]`

List all sessions, optionally filtered by ai_id

Args:
    ai_id: Optional AI identifier to filter by
    limit: Maximum number of sessions to return (default 50)

Returns:
    List of session dictionaries

**Parameters:**

- `ai_id: Optional = None`
- `limit: int = 50`

**Returns:** `List`

#### `get_cascade_assessments(self, cascade_id: str) -> List[Dict]`

DEPRECATED: Use reflexes table queries instead.

Get all assessments for a cascade from reflexes table.

**Parameters:**

- `cascade_id: str`

**Returns:** `List`

#### `get_check_phase_assessments(self, session_id: str) -> List[Dict]`

DEPRECATED: Use get_vectors_by_phase(session_id, phase='CHECK') instead.

This method redirects to reflexes table for backward compatibility.

**Parameters:**

- `session_id: str`

**Returns:** `List`

#### `get_check_vectors(self, session_id: str, cycle: Optional[int] = None) -> List[Dict]`

Get CHECK phase vectors, optionally filtered by cycle

**Parameters:**

- `session_id: str`
- `cycle: Optional = None`

**Returns:** `List`

#### `get_checkpoint_diff(self, session_id: str, threshold: float = 0.15) -> Dict`

Calculate vector differences between current state and last checkpoint (Phase 2).

Args:
    session_id: Session identifier
    threshold: Significance threshold for reporting changes

Returns:
    Dict with vector diffs and significant changes

**Parameters:**

- `session_id: str`
- `threshold: float = 0.15`

**Returns:** `Dict`

#### `get_epistemic_sources(self, project_id: str, session_id: Optional[str] = None, source_type: Optional[str] = None, min_confidence: float = 0.0, limit: Optional[int] = None) -> List[Dict]`

Get epistemic sources for a project

Args:
    project_id: Project identifier
    session_id: Optional filter by session
    source_type: Optional filter by type
    min_confidence: Minimum confidence threshold (default 0.0)
    limit: Optional limit on results
    
Returns:
    List of source dictionaries

**Parameters:**

- `project_id: str`
- `session_id: Optional = None`
- `source_type: Optional = None`
- `min_confidence: float = 0.0`
- `limit: Optional = None`

**Returns:** `List`

#### `get_findings_by_commit(self, commit_sha: str) -> List[Dict]`

Get all findings from a specific git commit

**Parameters:**

- `commit_sha: str`

**Returns:** `List`

#### `get_findings_by_file(self, filename: str, session_id: Optional[str] = None) -> List[Dict]`

Get all findings mentioning a specific file

**Parameters:**

- `filename: str`
- `session_id: Optional = None`

**Returns:** `List`

#### `get_git_checkpoint(self, session_id: str, phase: Optional[str] = None) -> Optional[Dict]`

Retrieve checkpoint from git notes with SQLite fallback (Phase 2).

Priority:
1. Try git notes first (via GitEnhancedReflexLogger)
2. Fall back to SQLite reflexes if git unavailable

Args:
    session_id: Session identifier
    phase: Optional phase filter (PREFLIGHT, CHECK, POSTFLIGHT)

Returns:
    Checkpoint dict or None if not found

**Parameters:**

- `session_id: str`
- `phase: Optional = None`

**Returns:** `Optional`

#### `get_goal_tree(self, session_id: str) -> List[Dict]`

Get complete goal tree for a session (delegates to GoalRepository)

Returns list of goals with nested subtasks

Args:
    session_id: Session UUID

Returns:
    List of goal dicts, each with 'subtasks' list

**Parameters:**

- `session_id: str`

**Returns:** `List`

#### `get_last_session_by_ai(self, ai_id: str) -> Optional[Dict]`

Get most recent session for an AI agent

**Parameters:**

- `ai_id: str`

**Returns:** `Optional`

#### `get_latest_project_handoff(self, project_id: str) -> Optional[Dict]`

Get the most recent project handoff (delegates to ProjectRepository)

**Parameters:**

- `project_id: str`

**Returns:** `Optional`

#### `get_latest_vectors(self, session_id: str, phase: Optional[str] = None) -> Optional[Dict]`

Get the latest epistemic vectors for a session from the reflexes table

Args:
    session_id: Session identifier
    phase: Optional phase filter

Returns:
    Dictionary with vectors, metadata, timestamp, etc. or None if not found

**Parameters:**

- `session_id: str`
- `phase: Optional = None`

**Returns:** `Optional`

#### `get_mistakes(self, session_id: Optional[str] = None, goal_id: Optional[str] = None, limit: int = 10) -> List[Dict]`

Retrieve logged mistakes (delegates to BreadcrumbRepository)

Args:
    session_id: Optional filter by session
    goal_id: Optional filter by goal
    limit: Maximum number of results

Returns:
    List of mistake dictionaries

**Parameters:**

- `session_id: Optional = None`
- `goal_id: Optional = None`
- `limit: int = 10`

**Returns:** `List`

#### `get_postflight_assessment(self, session_id: str) -> Optional[Dict]`

DEPRECATED: Use get_latest_vectors(session_id, phase='POSTFLIGHT') instead.

This method redirects to reflexes table for backward compatibility.

**Parameters:**

- `session_id: str`

**Returns:** `Optional`

#### `get_postflight_vectors(self, session_id: str) -> Optional[Dict]`

Get latest POSTFLIGHT vectors for session (convenience method)

**Parameters:**

- `session_id: str`

**Returns:** `Optional`

#### `get_preflight_assessment(self, session_id: str) -> Optional[Dict]`

DEPRECATED: Use get_latest_vectors(session_id, phase='PREFLIGHT') instead.

This method redirects to reflexes table for backward compatibility.

**Parameters:**

- `session_id: str`

**Returns:** `Optional`

#### `get_preflight_vectors(self, session_id: str) -> Optional[Dict]`

Get latest PREFLIGHT vectors for session (convenience method)

**Parameters:**

- `session_id: str`

**Returns:** `Optional`

#### `get_project(self, project_id: str) -> Optional[Dict]`

Get project data (delegates to ProjectRepository)

**Parameters:**

- `project_id: str`

**Returns:** `Optional`

#### `get_project_dead_ends(self, project_id: str, limit: Optional[int] = None, subject: Optional[str] = None) -> List[Dict]`

Get all dead ends for a project (delegates to BreadcrumbRepository)

**Parameters:**

- `project_id: str`
- `limit: Optional = None`
- `subject: Optional = None`

**Returns:** `List`

#### `get_project_findings(self, project_id: str, limit: Optional[int] = None, subject: Optional[str] = None) -> List[Dict]`

Get all findings for a project (delegates to BreadcrumbRepository)

**Parameters:**

- `project_id: str`
- `limit: Optional = None`
- `subject: Optional = None`

**Returns:** `List`

#### `get_project_reference_docs(self, project_id: str) -> List[Dict]`

Get all reference docs for a project (delegates to BreadcrumbRepository)

**Parameters:**

- `project_id: str`

**Returns:** `List`

#### `get_project_sessions(self, project_id: str) -> List[Dict]`

Get all sessions for a project (delegates to ProjectRepository)

**Parameters:**

- `project_id: str`

**Returns:** `List`

#### `get_project_unknowns(self, project_id: str, resolved: Optional[bool] = None, subject: Optional[str] = None) -> List[Dict]`

Get unknowns for a project (delegates to BreadcrumbRepository)

**Parameters:**

- `project_id: str`
- `resolved: Optional = None`
- `subject: Optional = None`

**Returns:** `List`

#### `get_session(self, session_id: str) -> Optional[Dict]`

Get session data

**Parameters:**

- `session_id: str`

**Returns:** `Optional`

#### `get_session_cascades(self, session_id: str) -> List[Dict]`

Get all cascades for a session

**Parameters:**

- `session_id: str`

**Returns:** `List`

#### `get_session_snapshot(self, session_id: str) -> Optional[Dict]`

Get git-native session snapshot showing where you left off

Args:
    session_id: Session identifier
    
Returns:
    Dictionary with git state, epistemic trajectory, learning delta, goals, sources

**Parameters:**

- `session_id: str`

**Returns:** `Optional`

#### `get_session_summary(self, session_id: str, detail_level: str = 'summary') -> Optional[Dict]`

Generate comprehensive session summary for resume/handoff

Args:
    session_id: Session to summarize
    detail_level: 'summary', 'detailed', or 'full'

Returns:
    Dictionary with session metadata, epistemic delta, accomplishments, etc.

**Parameters:**

- `session_id: str`
- `detail_level: str = 'summary'`

**Returns:** `Optional`

#### `get_vectors_by_phase(self, session_id: str, phase: str) -> List[Dict]`

Get all vectors for a specific phase

**Parameters:**

- `session_id: str`
- `phase: str`

**Returns:** `List`

#### `link_session_to_project(self, session_id: str, project_id: str)`

Link a session to a project (delegates to ProjectRepository)

**Parameters:**

- `session_id: str`
- `project_id: str`

#### `list_git_checkpoints(self, session_id: str, limit: int = 10, phase: Optional[str] = None) -> List[Dict]`

List all checkpoints for session from git notes (Phase 2).

Args:
    session_id: Session identifier
    limit: Maximum number of checkpoints to return
    phase: Optional phase filter

Returns:
    List of checkpoint dicts

**Parameters:**

- `session_id: str`
- `limit: int = 10`
- `phase: Optional = None`

**Returns:** `List`

#### `log_act_phase(self, session_id: str, cascade_id: Optional[str], action_type: str, action_rationale: Optional[str] = None, final_confidence: Optional[float] = None, goal_id: Optional[str] = None) -> str`

Log ACT phase decision for transparency and audit trail

**Parameters:**

- `session_id: str`
- `cascade_id: Optional`
- `action_type: str`
- `action_rationale: Optional = None`
- `final_confidence: Optional = None`
- `goal_id: Optional = None`

**Returns:** `str`

#### `log_bayesian_belief(self, cascade_id: str, vector_name: str, mean: float, variance: float, evidence_count: int, prior_mean: float, prior_variance: float)`

Track Bayesian belief updates

**Parameters:**

- `cascade_id: str`
- `vector_name: str`
- `mean: float`
- `variance: float`
- `evidence_count: int`
- `prior_mean: float`
- `prior_variance: float`

#### `log_check_phase_assessment(self, session_id: str, cascade_id: Optional[str], investigation_cycle: int, confidence: float, decision: str, gaps: List[str], next_targets: List[str], notes: str = '', vectors: Optional[Dict[str, float]] = None, findings: Optional[List[str]] = None, remaining_unknowns: Optional[List[str]] = None) -> str`

DEPRECATED: Use store_vectors() instead.

This method redirects to store_vectors() for backward compatibility.

**Parameters:**

- `session_id: str`
- `cascade_id: Optional`
- `investigation_cycle: int`
- `confidence: float`
- `decision: str`
- `gaps: List`
- `next_targets: List`
- `notes: str = ''`
- `vectors: Optional = None`
- `findings: Optional = None`
- `remaining_unknowns: Optional = None`

**Returns:** `str`

#### `log_dead_end(self, project_id: str, session_id: str, approach: str, why_failed: str, goal_id: Optional[str] = None, subtask_id: Optional[str] = None, subject: Optional[str] = None) -> str`

Log a project dead end (delegates to BreadcrumbRepository)

**Parameters:**

- `project_id: str`
- `session_id: str`
- `approach: str`
- `why_failed: str`
- `goal_id: Optional = None`
- `subtask_id: Optional = None`
- `subject: Optional = None`

**Returns:** `str`

#### `log_divergence(self, cascade_id: str, turn_number: int, delegate: str, trustee: str, divergence_score: float, divergence_reason: str, synthesis_needed: bool, synthesis_data: Optional[Dict] = None)`

Track delegate vs trustee divergence

**Parameters:**

- `cascade_id: str`
- `turn_number: int`
- `delegate: str`
- `trustee: str`
- `divergence_score: float`
- `divergence_reason: str`
- `synthesis_needed: bool`
- `synthesis_data: Optional = None`

#### `log_epistemic_assessment(self, cascade_id: str, assessment: Any, phase: str)`

DEPRECATED: Use store_vectors() instead.

This method is kept for backward compatibility with canonical structures.

**Parameters:**

- `cascade_id: str`
- `assessment: Any`
- `phase: str`

#### `log_finding(self, project_id: str, session_id: str, finding: str, goal_id: Optional[str] = None, subtask_id: Optional[str] = None, subject: Optional[str] = None) -> str`

Log a project finding (what was learned/discovered)

**Parameters:**

- `project_id: str`
- `session_id: str`
- `finding: str`
- `goal_id: Optional = None`
- `subtask_id: Optional = None`
- `subject: Optional = None`

**Returns:** `str`

#### `log_investigation_round(self, session_id: str, cascade_id: Optional[str], round_number: int, tools_mentioned: Optional[str] = None, findings: Optional[str] = None, confidence_before: Optional[float] = None, confidence_after: Optional[float] = None, summary: Optional[str] = None) -> str`

Log investigation round for transparency

**Parameters:**

- `session_id: str`
- `cascade_id: Optional`
- `round_number: int`
- `tools_mentioned: Optional = None`
- `findings: Optional = None`
- `confidence_before: Optional = None`
- `confidence_after: Optional = None`
- `summary: Optional = None`

**Returns:** `str`

#### `log_mistake(self, session_id: str, mistake: str, why_wrong: str, cost_estimate: Optional[str] = None, root_cause_vector: Optional[str] = None, prevention: Optional[str] = None, goal_id: Optional[str] = None) -> str`

Log a mistake for learning (delegates to BreadcrumbRepository)

Args:
    session_id: Session identifier
    mistake: What was done wrong
    why_wrong: Explanation of why it was wrong
    cost_estimate: Estimated time/effort wasted (e.g., "2 hours")
    root_cause_vector: Epistemic vector that caused the mistake (e.g., "KNOW", "CONTEXT")
    prevention: How to prevent this mistake in the future
    goal_id: Optional goal identifier this mistake relates to

Returns:
    mistake_id: UUID string

**Parameters:**

- `session_id: str`
- `mistake: str`
- `why_wrong: str`
- `cost_estimate: Optional = None`
- `root_cause_vector: Optional = None`
- `prevention: Optional = None`
- `goal_id: Optional = None`

**Returns:** `str`

#### `log_postflight_assessment(self, session_id: str, cascade_id: Optional[str], task_summary: str, vectors: Dict[str, float], postflight_confidence: float, calibration_accuracy: str, learning_notes: str = '') -> str`

DEPRECATED: Use store_vectors() instead.

This method redirects to store_vectors() for backward compatibility.

**Parameters:**

- `session_id: str`
- `cascade_id: Optional`
- `task_summary: str`
- `vectors: Dict`
- `postflight_confidence: float`
- `calibration_accuracy: str`
- `learning_notes: str = ''`

**Returns:** `str`

#### `log_preflight_assessment(self, session_id: str, cascade_id: Optional[str], prompt_summary: str, vectors: Dict[str, float], uncertainty_notes: str = '') -> str`

DEPRECATED: Use store_vectors() instead.

This method redirects to store_vectors() for backward compatibility.

**Parameters:**

- `session_id: str`
- `cascade_id: Optional`
- `prompt_summary: str`
- `vectors: Dict`
- `uncertainty_notes: str = ''`

**Returns:** `str`

#### `log_tool_execution(self, cascade_id: str, round_number: int, tool_name: str, tool_purpose: str, target_vector: str, success: bool, confidence_gain: float, information: Dict, duration_ms: int)`

Track investigation tool usage

**Parameters:**

- `cascade_id: str`
- `round_number: int`
- `tool_name: str`
- `tool_purpose: str`
- `target_vector: str`
- `success: bool`
- `confidence_gain: float`
- `information: Dict`
- `duration_ms: int`

#### `log_unknown(self, project_id: str, session_id: str, unknown: str, goal_id: Optional[str] = None, subtask_id: Optional[str] = None, subject: Optional[str] = None) -> str`

Log a project unknown (what's still unclear)

**Parameters:**

- `project_id: str`
- `session_id: str`
- `unknown: str`
- `goal_id: Optional = None`
- `subtask_id: Optional = None`
- `subject: Optional = None`

**Returns:** `str`

#### `merge_branches(self, session_id: str, investigation_round: int = 1) -> Dict`

Auto-merge best branch based on epistemic scores (delegates to BranchRepository)

Returns:
    Dict with winning_branch_id, merge_decision_id, rationale

**Parameters:**

- `session_id: str`
- `investigation_round: int = 1`

**Returns:** `Dict`

#### `query_unknowns_summary(self, session_id: str) -> Dict`

Get summary of all unknowns in a session (delegates to GoalRepository)

Args:
    session_id: Session UUID

Returns:
    Dict with total_unknowns count and breakdown by goal

**Parameters:**

- `session_id: str`

**Returns:** `Dict`

#### `resolve_project_id(self, project_id_or_name: str) -> Optional[str]`

Resolve project name or UUID to UUID (delegates to ProjectRepository)

**Parameters:**

- `project_id_or_name: str`

**Returns:** `Optional`

#### `resolve_unknown(self, unknown_id: str, resolved_by: str)`

Mark an unknown as resolved (delegates to BreadcrumbRepository)

**Parameters:**

- `unknown_id: str`
- `resolved_by: str`

#### `store_epistemic_delta(self, cascade_id: str, delta: Dict[str, float])`

Store epistemic delta (PREFLIGHT vs POSTFLIGHT) for calibration tracking

Args:
    cascade_id: Cascade identifier
    delta: Dictionary of epistemic changes (e.g., {'know': +0.15, 'uncertainty': -0.20})

**Parameters:**

- `cascade_id: str`
- `delta: Dict`

#### `store_vectors(self, session_id: str, phase: str, vectors: Dict[str, float], cascade_id: Optional[str] = None, round_num: int = 1, metadata: Optional[Dict] = None, reasoning: Optional[str] = None)`

Store epistemic vectors in the reflexes table

Args:
    session_id: Session identifier
    phase: Current phase (PREFLIGHT, CHECK, ACT, POSTFLIGHT)
    vectors: Dictionary of 13 epistemic vectors
    cascade_id: Optional cascade identifier
    round_num: Current round number

**Parameters:**

- `session_id: str`
- `phase: str`
- `vectors: Dict`
- `cascade_id: Optional = None`
- `round_num: int = 1`
- `metadata: Optional = None`
- `reasoning: Optional = None`

#### `update_cascade_phase(self, cascade_id: str, phase: str, completed: bool = True)`

Mark cascade phase as completed

**Parameters:**

- `cascade_id: str`
- `phase: str`
- `completed: bool = True`

#### `update_subtask_dead_ends(self, subtask_id: str, dead_ends: List[str])`

Update dead ends for a subtask (delegates to GoalRepository)

Args:
    subtask_id: Subtask UUID
    dead_ends: List of dead end strings (e.g., "Attempted X - blocked by Y")

**Parameters:**

- `subtask_id: str`
- `dead_ends: List`

#### `update_subtask_findings(self, subtask_id: str, findings: List[str])`

Update findings for a subtask (delegates to GoalRepository)

Args:
    subtask_id: Subtask UUID
    findings: List of finding strings

**Parameters:**

- `subtask_id: str`
- `findings: List`

#### `update_subtask_unknowns(self, subtask_id: str, unknowns: List[str])`

Update unknowns for a subtask (delegates to GoalRepository)

Args:
    subtask_id: Subtask UUID
    unknowns: List of unknown strings

**Parameters:**

- `subtask_id: str`
- `unknowns: List`

---

## branch_mapping

**Module:** `integrations/branch_mapping.py`

**1 classes**

### `BranchMapping`

**Module:** `integrations/branch_mapping.py`

Manages branch-to-goal mapping in .empirica/branch_mapping.json

**Methods:**

#### `__init__(self, repo_root: Optional[str] = None)`

Initialize branch mapping manager.

Args:
    repo_root: Git repository root. If None, searches from cwd.

**Parameters:**

- `repo_root: Optional = None`

#### `add_mapping(self, branch_name: str, goal_id: str, beads_issue_id: Optional[str] = None, ai_id: Optional[str] = None, session_id: Optional[str] = None) -> bool`

Add a branch-to-goal mapping.

Args:
    branch_name: Git branch name
    goal_id: Empirica goal UUID
    beads_issue_id: Optional BEADS issue ID
    ai_id: Optional AI identifier
    session_id: Optional session UUID
    
Returns:
    True if mapping added, False if branch already mapped

**Parameters:**

- `branch_name: str`
- `goal_id: str`
- `beads_issue_id: Optional = None`
- `ai_id: Optional = None`
- `session_id: Optional = None`

**Returns:** `bool`

#### `get_branch_for_goal(self, goal_id: str) -> Optional[str]`

Find branch associated with a goal.

**Parameters:**

- `goal_id: str`

**Returns:** `Optional`

#### `get_history(self, limit: int = 50) -> List[Dict]`

Get branch mapping history.

**Parameters:**

- `limit: int = 50`

**Returns:** `List`

#### `get_mapping(self, branch_name: str) -> Optional[Dict]`

Get mapping for a branch.

**Parameters:**

- `branch_name: str`

**Returns:** `Optional`

#### `list_active_mappings(self) -> List[Dict]`

List all active branch mappings.

**Returns:** `List`

#### `remove_mapping(self, branch_name: str, archive: bool = True) -> bool`

Remove a branch mapping.

Args:
    branch_name: Branch to remove
    archive: If True, moves to history instead of deleting
    
Returns:
    True if removed, False if not found

**Parameters:**

- `branch_name: str`
- `archive: bool = True`

**Returns:** `bool`

---

**1 functions**

#### `get_branch_mapping(repo_root: Optional[str] = None) -> temp_module.BranchMapping`

Get branch mapping instance.

Args:
    repo_root: Optional git repository root
    
Returns:
    BranchMapping instance

**Parameters:**

- `repo_root: Optional = None`

**Returns:** `BranchMapping`

---

## doc_code_integrity

**Module:** `utils/doc_code_integrity.py`

**1 classes**

### `DocCodeIntegrityAnalyzer`

**Module:** `utils/doc_code_integrity.py`

Analyze integrity between documentation and codebase

**Methods:**

#### `__init__(self, project_root: Optional[str] = None)`

**Parameters:**

- `project_root: Optional = None`

#### `analyze_cli_commands(self) -> Dict`

Phase 1: Analyze CLI command integrity

Returns dict with:
- commands_in_docs: Commands mentioned in documentation
- commands_in_code: Commands actually implemented
- missing_code: Documented but not implemented
- missing_docs: Implemented but not documented

**Returns:** `Dict`

#### `get_detailed_gaps(self) -> Dict`

Get detailed information about integrity gaps

Returns structured report with file locations and context

**Returns:** `Dict`

---

**2 functions**

#### `analyze_complete_integrity(project_root: Optional[str] = None) -> Dict`

Run complete integrity analysis including deprecation and superfluity

Returns comprehensive integrity report

**Parameters:**

- `project_root: Optional = None`

**Returns:** `Dict`

---

#### `analyze_project_integrity(project_root: Optional[str] = None) -> Dict`

Convenience function to run full integrity analysis

Returns:
    Dict with integrity analysis results

**Parameters:**

- `project_root: Optional = None`

**Returns:** `Dict`

---

---

## Notes

- **Generated documentation:** This file is auto-generated from the codebase.
- **100% accuracy:** Every API listed here exists in the current codebase.
- **Public APIs only:** Private methods (starting with `_`) are excluded.

**To regenerate this documentation:**
```bash
cd dev_scripts/doc_regeneration
python3 extract_python_api.py
python3 generate_python_api_markdown.py
```

**Last updated:** 2025-12-16 20:39:28 UTC
