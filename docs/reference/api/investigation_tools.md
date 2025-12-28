# Investigation Tools API

**Module:** `empirica.core.investigation.*` and related modules
**Category:** Investigation & Exploration
**Stability:** Production Ready

---

## Overview

The Investigation Tools API provides mechanisms for AI agents to explore, investigate, and validate approaches during the CASCADE workflow. This includes:

- Multi-branch investigation capabilities
- Tool usage tracking
- Branch comparison and merging
- Investigation logging and analysis

---

## Investigation Branch Manager

### `class InvestigationBranchManager`

Manages multiple investigation branches for exploring different approaches simultaneously.

#### `__init__(self, session_id: str, db_path: Optional[str] = None)`

Initialize the investigation branch manager.

**Parameters:**
- `session_id: str` - Session identifier
- `db_path: Optional[str]` - Database path, defaults to standard location

**Example:**
```python
from empirica.core.investigation.branch_manager import InvestigationBranchManager

branch_manager = InvestigationBranchManager(session_id="sess-123")
```

### `create_branch(self, branch_name: str, investigation_path: str, git_branch_name: str, preflight_vectors: Dict[str, float], description: Optional[str] = None) -> str`

Create a new investigation branch.

**Parameters:**
- `branch_name: str` - Human-readable branch name
- `investigation_path: str` - What is being investigated (e.g., 'oauth2', 'database_schema')
- `git_branch_name: str` - Git branch name for this investigation
- `preflight_vectors: Dict[str, float]` - Epistemic vectors at branch start
- `description: Optional[str]` - Optional branch description

**Returns:** `str` - Branch ID

**Example:**
```python
branch_id = branch_manager.create_branch(
    branch_name="OAuth2 Implementation",
    investigation_path="authentication/oauth2-flow",
    git_branch_name="feature/oauth2-investigation",
    preflight_vectors={
        "know": 0.65, "do": 0.55, "context": 0.85, "uncertainty": 0.45
    },
    description="Exploring different OAuth2 implementation approaches"
)
```

### `checkpoint_branch(self, branch_id: str, postflight_vectors: Dict[str, float], tokens_spent: int, time_spent_minutes: int, notes: Optional[str] = None) -> bool`

Checkpoint a branch after investigation work.

**Parameters:**
- `branch_id: str` - Branch identifier
- `postflight_vectors: Dict[str, float]` - Epistemic vectors after investigation
- `tokens_spent: int` - Number of tokens used in investigation
- `time_spent_minutes: int` - Time spent in minutes
- `notes: Optional[str]` - Optional checkpoint notes

**Returns:** `bool` - True if checkpoint successful

**Example:**
```python
success = branch_manager.checkpoint_branch(
    branch_id="branch-456",
    postflight_vectors={
        "know": 0.75, "do": 0.70, "context": 0.88, "uncertainty": 0.30
    },
    tokens_spent=1250,
    time_spent_minutes=45,
    notes="Successfully implemented basic OAuth2 flow with JWT tokens"
)
```

### `evaluate_branch(self, branch_id: str) -> Dict[str, Any]`

Evaluate a branch for potential merging.

**Parameters:**
- `branch_id: str` - Branch identifier

**Returns:** `Dict[str, Any]` - Evaluation results including merge score

**Example:**
```python
evaluation = branch_manager.evaluate_branch(branch_id="branch-456")
print(f"Merge score: {evaluation['merge_score']}")
print(f"Quality: {evaluation['quality']}")
print(f"Rationale: {evaluation['rationale']}")
```

### `merge_branches(self, session_id: str, investigation_round: int = 1, selection_criteria: Optional[Dict[str, float]] = None) -> Dict[str, Any]`

Auto-merge best branch based on epistemic scores.

**Parameters:**
- `session_id: str` - Session identifier
- `investigation_round: int` - Investigation round number, default 1
- `selection_criteria: Optional[Dict[str, float]]` - Weighting for selection criteria

**Returns:** `Dict[str, Any]` - Merge decision results

**Example:**
```python
merge_result = branch_manager.merge_branches(
    session_id="sess-123",
    investigation_round=2,
    selection_criteria={
        "learning_delta": 0.4,    # Weight for knowledge gained
        "efficiency": 0.3,        # Weight for resource usage
        "alignment": 0.3          # Weight for goal alignment
    }
)

print(f"Winning branch: {merge_result['winning_branch_id']}")
print(f"Decision rationale: {merge_result['decision_rationale']}")
```

### `get_branch_comparison(self, session_id: str) -> List[Dict[str, Any]]`

Get comparison of all branches for a session.

**Parameters:**
- `session_id: str` - Session identifier

**Returns:** `List[Dict[str, Any]]` - List of branch comparison dictionaries

**Example:**
```python
comparisons = branch_manager.get_branch_comparison(session_id="sess-123")
for comp in comparisons:
    print(f"Branch: {comp['branch_name']}")
    print(f"  Learning: {comp['learning_delta']}")
    print(f"  Efficiency: {comp['efficiency_score']}")
    print(f"  Merge score: {comp['merge_score']}")
```

---

## Investigation Tool Tracker

### `class InvestigationToolTracker`

Tracks usage and effectiveness of investigation tools.

#### `__init__(self, db_path: Optional[str] = None)`

Initialize the tool tracker.

**Parameters:**
- `db_path: Optional[str]` - Database path, defaults to standard location

**Example:**
```python
from empirica.core.investigation.tool_tracker import InvestigationToolTracker

tool_tracker = InvestigationToolTracker()
```

### `log_tool_execution(self, cascade_id: str, round_number: int, tool_name: str, tool_purpose: str, target_vector: str, success: bool, confidence_gain: float, information_gained: str, duration_ms: int, tool_parameters: Optional[Dict[str, Any]] = None) -> str`

Log execution of an investigation tool.

**Parameters:**
- `cascade_id: str` - CASCADE identifier
- `round_number: int` - Investigation round number
- `tool_name: str` - Name of the tool executed
- `tool_purpose: str` - Purpose of the tool
- `target_vector: str` - Which epistemic vector the tool targets
- `success: bool` - Whether the tool execution was successful
- `confidence_gain: float` - Confidence gained from tool use
- `information_gained: str` - Description of information gained
- `duration_ms: int` - Execution duration in milliseconds
- `tool_parameters: Optional[Dict[str, Any]]` - Optional parameters used

**Returns:** `str` - Tool execution ID

**Example:**
```python
execution_id = tool_tracker.log_tool_execution(
    cascade_id="cascade-789",
    round_number=1,
    tool_name="codebase_search",
    tool_purpose="Find existing authentication patterns",
    target_vector="context",
    success=True,
    confidence_gain=0.15,
    information_gained="Found 3 existing auth implementations with different approaches",
    duration_ms=245,
    tool_parameters={"query": "authentication", "file_types": ["py", "js"]}
)
```

### `get_tool_effectiveness(self, tool_name: str, time_window_days: int = 30) -> Dict[str, float]`

Get effectiveness metrics for a tool over time.

**Parameters:**
- `tool_name: str` - Tool name to analyze
- `time_window_days: int` - Time window in days, default 30

**Returns:** `Dict[str, float]` - Effectiveness metrics

**Example:**
```python
effectiveness = tool_tracker.get_tool_effectiveness(tool_name="codebase_search")
print(f"Success rate: {effectiveness['success_rate']}")
print(f"Average confidence gain: {effectiveness['avg_confidence_gain']}")
print(f"Information quality: {effectiveness['information_quality']}")
```

### `suggest_best_tool(self, current_vectors: Dict[str, float], task_context: str, available_tools: Optional[List[str]] = None) -> Dict[str, Any]`

Suggest the best tool based on current epistemic state and task.

**Parameters:**
- `current_vectors: Dict[str, float]` - Current epistemic vectors
- `task_context: str` - Current task context
- `available_tools: Optional[List[str]]` - Optional list of available tools (all if None)

**Returns:** `Dict[str, Any]` - Tool suggestion with reasoning

**Example:**
```python
suggestion = tool_tracker.suggest_best_tool(
    current_vectors={
        "know": 0.4, "context": 0.6, "uncertainty": 0.7
    },
    task_context="implementing OAuth2 flow with JWT tokens"
)

print(f"Suggested tool: {suggestion['tool_name']}")
print(f"Expected gain: {suggestion['expected_confidence_gain']}")
print(f"Reasoning: {suggestion['reasoning']}")
```

---

## Investigation Logger

### `class InvestigationLogger`

Logs investigation activities and outcomes.

#### `__init__(self, session_id: str, db_path: Optional[str] = None)`

Initialize the investigation logger.

**Parameters:**
- `session_id: str` - Session identifier
- `db_path: Optional[str]` - Database path, defaults to standard location

**Example:**
```python
from empirica.core.investigation.logger import InvestigationLogger

investigation_logger = InvestigationLogger(session_id="sess-123")
```

### `log_investigation_round(self, cascade_id: str, round_number: int, tools_used: List[str], findings: List[str], confidence_before: float, confidence_after: float, summary: str, detailed_notes: Optional[str] = None) -> str`

Log an investigation round with results.

**Parameters:**
- `cascade_id: str` - CASCADE identifier
- `round_number: int` - Investigation round number
- `tools_used: List[str]` - List of tools used in this round
- `findings: List[str]` - List of findings from investigation
- `confidence_before: float` - Confidence before investigation
- `confidence_after: float` - Confidence after investigation
- `summary: str` - Brief summary of round
- `detailed_notes: Optional[str]` - Optional detailed notes

**Returns:** `str` - Investigation round ID

**Example:**
```python
round_id = investigation_logger.log_investigation_round(
    cascade_id="cascade-789",
    round_number=2,
    tools_used=["codebase_search", "documentation_lookup"],
    findings=[
        "Found existing JWT implementation pattern",
        "Discovered security vulnerability in current approach"
    ],
    confidence_before=0.55,
    confidence_after=0.72,
    summary="Improved understanding of JWT security patterns"
)
```

### `get_investigation_insights(self, session_id: str, time_window_days: int = 7) -> Dict[str, Any]`

Get insights from investigation activities.

**Parameters:**
- `session_id: str` - Session identifier
- `time_window_days: int` - Time window for analysis, default 7

**Returns:** `Dict[str, Any]` - Investigation insights

**Example:**
```python
insights = investigation_logger.get_investigation_insights(session_id="sess-123")
print(f"Most effective tools: {insights['top_performing_tools']}")
print(f"Common patterns: {insights['common_patterns']}")
print(f"Improvement rate: {insights['confidence_improvement_rate']}")
```

---

## Advanced Investigation Features

### `register_custom_investigation_tool(self, tool_name: str, tool_function: Callable, tool_purpose: str, target_vector: str, expected_confidence_gain: float, resource_cost: str = 'low')`

Register a custom investigation tool.

**Parameters:**
- `tool_name: str` - Unique tool name
- `tool_function: Callable` - Function implementing the tool
- `tool_purpose: str` - Brief description of purpose
- `target_vector: str` - Which epistemic vector the tool targets
- `expected_confidence_gain: float` - Expected confidence improvement
- `resource_cost: str` - Resource cost ('low', 'medium', 'high'), default 'low'

**Example:**
```python
def custom_code_analyzer(file_paths: List[str], pattern: str) -> Dict[str, Any]:
    # Implementation of custom code analysis tool
    pass

investigation_logger.register_custom_investigation_tool(
    tool_name="custom_code_analyzer",
    tool_function=custom_code_analyzer,
    tool_purpose="Analyze code for specific patterns",
    target_vector="know",
    expected_confidence_gain=0.25,
    resource_cost="medium"
)
```

### `execute_registered_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]`

Execute a registered investigation tool.

**Parameters:**
- `tool_name: str` - Name of tool to execute
- `**kwargs` - Tool-specific parameters

**Returns:** `Dict[str, Any]` - Tool execution results

**Example:**
```python
results = investigation_logger.execute_registered_tool(
    tool_name="custom_code_analyzer",
    file_paths=["src/auth.py", "src/models/user.py"],
    pattern="password"
)

print(f"Analysis complete: {results['success']}")
print(f"Findings: {results['findings']}")
```

---

## Investigation Analytics

### `get_investigation_efficiency(self, session_id: str, cascade_id: Optional[str] = None) -> Dict[str, float]`

Get investigation efficiency metrics.

**Parameters:**
- `session_id: str` - Session identifier
- `cascade_id: Optional[str]` - Optional CASCADE filter

**Returns:** `Dict[str, float]` - Efficiency metrics

**Example:**
```python
efficiency = investigation_logger.get_investigation_efficiency(session_id="sess-123")
print(f"Tokens per confidence point: {efficiency['tokens_per_confidence_point']}")
print(f"Time per investigation: {efficiency['time_per_investigation']}")
print(f"Success rate: {efficiency['success_rate']}")
```

### `identify_investigation_patterns(self, session_id: str, min_frequency: int = 2) -> List[Dict[str, Any]]`

Identify recurring investigation patterns.

**Parameters:**
- `session_id: str` - Session identifier
- `min_frequency: int` - Minimum frequency to include pattern, default 2

**Returns:** `List[Dict[str, Any]]` - List of identified patterns

**Example:**
```python
patterns = investigation_logger.identify_investigation_patterns(session_id="sess-123")
for pattern in patterns:
    print(f"Pattern: {pattern['description']}")
    print(f"Frequency: {pattern['frequency']}")
    print(f"Effectiveness: {pattern['effectiveness']}")
```

---

## Utility Methods

### `cleanup_old_investigations(self, days_old: int = 30) -> int`

Clean up old investigation data to save space.

**Parameters:**
- `days_old: int` - Minimum age in days, default 30

**Returns:** `int` - Number of records cleaned up

**Example:**
```python
cleaned = investigation_logger.cleanup_old_investigations(days_old=60)
print(f"Cleaned up {cleaned} old investigation records")
```

### `export_investigation_data(self, session_id: str, format: str = 'json') -> str`

Export investigation data in specified format.

**Parameters:**
- `session_id: str` - Session identifier
- `format: str` - Export format ('json', 'csv', 'markdown'), default 'json'

**Returns:** `str` - Exported data string

**Example:**
```python
export_data = investigation_logger.export_investigation_data(
    session_id="sess-123",
    format="markdown"
)
# Save export_data to file for analysis
```

---

## Best Practices

1. **Use appropriate branching** - Create branches for genuinely different approaches, not minor variations.

2. **Checkpoint regularly** - Save state at meaningful investigation milestones.

3. **Track tool effectiveness** - Monitor which tools provide the best information gain.

4. **Log sufficient detail** - Include enough context to understand investigation outcomes.

5. **Evaluate objectively** - Use quantitative metrics when comparing branches.

6. **Clean up when appropriate** - Remove old investigation data that's no longer needed.

7. **Register custom tools thoughtfully** - Consider target vectors and resource costs.

8. **Analyze patterns** - Look for recurring investigation patterns to improve efficiency.

---

## Error Handling

Methods typically raise:
- `ValueError` for invalid parameters
- `sqlite3.Error` for database issues
- `KeyError` when referenced entities don't exist
- `RuntimeError` for state-related issues
- `NotImplementedError` for unimplemented custom tools

---

**Module Location:** `empirica/core/investigation/`
**API Stability:** Stable
**Last Updated:** 2025-12-27