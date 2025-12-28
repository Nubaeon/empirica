# CASCADE Workflow API

**Module:** `empirica.core.cascade.metacognitive_cascade` and related modules
**Category:** Reasoning & Workflow
**Stability:** Production Ready

---

## Overview

The CASCADE (Continuous Assessment, Synthesis, and Deliberative Epistemic reasoning) workflow is the core reasoning framework for Empirica. It implements a structured epistemic workflow with the following phases:

- **PREFLIGHT** - Initial epistemic assessment
- **THINK** - Strategic planning and approach design
- **PLAN** - Detailed execution planning
- **INVESTIGATE** - Information gathering and exploration
- **CHECK** - Mid-workflow epistemic assessment
- **ACT** - Execution of planned actions
- **POSTFLIGHT** - Final epistemic assessment and learning

The CASCADE system emphasizes genuine self-assessment over heuristic-based evaluation.

---

## Core CASCADE Class

### `class MetacognitiveCascade`

The main CASCADE orchestrator that manages the complete reasoning workflow.

#### `__init__(self, ai_id: str, session_id: str, enable_bayesian: bool = False, enable_drift_monitoring: bool = False)`

Initialize a CASCADE instance.

**Parameters:**
- `ai_id: str` - AI identifier for the cascade
- `session_id: str` - Session identifier this cascade belongs to
- `enable_bayesian: bool` - Enable Bayesian belief updating, default False
- `enable_drift_monitoring: bool` - Enable behavioral drift detection, default False

**Example:**
```python
from empirica.core.cascade.metacognitive_cascade import MetacognitiveCascade

cascade = MetacognitiveCascade(
    ai_id="claude-sonnet-4",
    session_id="sess-123",
    enable_bayesian=True,
    enable_drift_monitoring=True
)
```

### `execute_workflow(self, task: str, context: Dict[str, Any], goal: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`

Execute the complete CASCADE workflow for a task.

**Parameters:**
- `task: str` - Task description
- `context: Dict[str, Any]` - Context dictionary with relevant information
- `goal: Optional[Dict[str, Any]]` - Optional goal definition

**Returns:** `Dict[str, Any]` - Complete workflow results including final action and confidence

**Example:**
```python
context = {
    "project_root": "/path/to/project",
    "files": ["src/auth.py", "tests/auth_test.py"],
    "requirements": ["implement OAuth2", "secure passwords"]
}

result = cascade.execute_workflow(
    task="Implement secure user authentication",
    context=context
)

print(f"Action: {result['final_action']}")
print(f"Confidence: {result['final_confidence']}")
```

---

## Phase-Specific Methods

### `preflight_assessment(self, task: str, context: Dict[str, Any]) -> Dict[str, float]`

Execute preflight epistemic assessment.

**Parameters:**
- `task: str` - Task description to assess
- `context: Dict[str, Any]` - Context for assessment

**Returns:** `Dict[str, float]` - 13-dimensional epistemic vector assessment

**Example:**
```python
vectors = cascade.preflight_assessment(
    task="Refactor authentication module",
    context={
        "files": ["auth.py", "models/user.py"],
        "complexity": "medium",
        "timeline": "2 days"
    }
)

print(f"Knowledge: {vectors['know']:.2f}")
print(f"Capability: {vectors['do']:.2f}")
print(f"Uncertainty: {vectors['uncertainty']:.2f}")
```

### `think_phase(self, task: str, context: Dict[str, Any], preflight_vectors: Dict[str, float]) -> Dict[str, Any]`

Execute strategic thinking phase.

**Parameters:**
- `task: str` - Task to think about
- `context: Dict[str, Any]` - Context information
- `preflight_vectors: Dict[str, float]` - Results from preflight assessment

**Returns:** `Dict[str, Any]` - Thinking results including approach and risks

**Example:**
```python
thinking_result = cascade.think_phase(
    task="Implement OAuth2 flow",
    context=context,
    preflight_vectors=vectors
)

print(f"Approach: {thinking_result['approach']}")
print(f"Risk factors: {thinking_result['risk_factors']}")
```

### `plan_phase(self, task: str, context: Dict[str, Any], thinking_result: Dict[str, Any]) -> Dict[str, Any]`

Create detailed execution plan.

**Parameters:**
- `task: str` - Task to plan
- `context: Dict[str, Any]` - Context information
- `thinking_result: Dict[str, Any]` - Results from think phase

**Returns:** `Dict[str, Any]` - Detailed execution plan

**Example:**
```python
plan = cascade.plan_phase(
    task="Implement OAuth2 flow",
    context=context,
    thinking_result=thinking_result
)

print(f"Steps: {len(plan['steps'])}")
print(f"Timeline: {plan['estimated_duration']}")
```

### `investigate_phase(self, task: str, plan: Dict[str, Any], max_rounds: int = 5) -> Dict[str, Any]`

Execute investigation phase to gather information and reduce uncertainty.

**Parameters:**
- `task: str` - Task being investigated
- `plan: Dict[str, Any]` - Execution plan to investigate
- `max_rounds: int` - Maximum investigation rounds, default 5

**Returns:** `Dict[str, Any]` - Investigation results with findings and confidence updates

**Example:**
```python
investigation = cascade.investigate_phase(
    task="Implement OAuth2 flow",
    plan=plan,
    max_rounds=3
)

print(f"Findings: {len(investigation['findings'])}")
print(f"Confidence change: {investigation['confidence_delta']}")
```

### `check_phase(self, task: str, current_state: Dict[str, Any], investigation_results: Dict[str, Any]) -> Dict[str, float]`

Execute mid-workflow epistemic check.

**Parameters:**
- `task: str` - Current task
- `current_state: Dict[str, Any]` - Current state including progress
- `investigation_results: Dict[str, Any]` - Results from investigation phase

**Returns:** `Dict[str, float]` - Updated epistemic vectors after check

**Example:**
```python
check_vectors = cascade.check_phase(
    task="Implement OAuth2 flow",
    current_state={"progress": 0.6, "issues_found": []},
    investigation_results=investigation
)

if check_vectors['uncertainty'] > 0.5:
    print("High uncertainty detected - need more investigation")
```

### `act_phase(self, task: str, plan: Dict[str, Any], check_vectors: Dict[str, float]) -> Dict[str, Any]`

Execute the planned actions.

**Parameters:**
- `task: str` - Task to execute
- `plan: Dict[str, Any]` - Execution plan
- `check_vectors: Dict[str, float]` - Current epistemic state

**Returns:** `Dict[str, Any]` - Execution results

**Example:**
```python
act_result = cascade.act_phase(
    task="Implement OAuth2 flow",
    plan=plan,
    check_vectors=check_vectors
)

print(f"Action completed: {act_result['action_taken']}")
print(f"Success: {act_result['success']}")
```

### `postflight_assessment(self, task: str, initial_vectors: Dict[str, float], final_vectors: Dict[str, float], action_result: Dict[str, Any]) -> Dict[str, Any]`

Execute final epistemic assessment and learning capture.

**Parameters:**
- `task: str` - Completed task
- `initial_vectors: Dict[str, float]` - Initial vectors (from preflight)
- `final_vectors: Dict[str, float]` - Final vectors (from act/check)
- `action_result: Dict[str, Any]` - Results from action phase

**Returns:** `Dict[str, Any]` - Complete assessment with learning deltas

**Example:**
```python
postflight = cascade.postflight_assessment(
    task="Implement OAuth2 flow",
    initial_vectors=preflight_vectors,
    final_vectors=check_vectors,
    action_result=act_result
)

print(f"Learning delta: {postflight['knowledge_delta']}")
print(f"Efficiency: {postflight['efficiency_score']}")
```

---

## Investigation Tools Integration

### `register_investigation_tool(self, tool_name: str, tool_function: Callable, tool_purpose: str, target_vector: str)`

Register a custom investigation tool for use during investigation phases.

**Parameters:**
- `tool_name: str` - Unique name for the tool
- `tool_function: Callable` - Function that implements the tool
- `tool_purpose: str` - Brief description of what the tool does
- `target_vector: str` - Which epistemic vector the tool targets (e.g., 'know', 'context', 'uncertainty')

**Example:**
```python
def search_codebase(query: str) -> List[str]:
    # Implementation to search codebase
    pass

cascade.register_investigation_tool(
    tool_name="codebase_search",
    tool_function=search_codebase,
    tool_purpose="Search codebase for relevant patterns",
    target_vector="context"
)
```

### `execute_investigation_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]`

Execute a registered investigation tool.

**Parameters:**
- `tool_name: str` - Name of the tool to execute
- `**kwargs` - Tool-specific parameters

**Returns:** `Dict[str, Any]` - Tool execution results

**Example:**
```python
results = cascade.execute_investigation_tool(
    tool_name="codebase_search",
    query="existing authentication patterns"
)
```

---

## Bayesian Reasoning Integration

### `update_belief(self, vector_name: str, evidence: Dict[str, Any], confidence: float)`

Update Bayesian belief for a specific epistemic vector.

**Parameters:**
- `vector_name: str` - Name of the vector to update (e.g., 'know', 'do', 'uncertainty')
- `evidence: Dict[str, Any]` - New evidence for the update
- `confidence: float` - Confidence in the evidence (0.0-1.0)

**Example:**
```python
# Update belief about knowledge after reading documentation
cascade.update_belief(
    vector_name="know",
    evidence={"source": "auth_spec.pdf", "content_type": "requirement"},
    confidence=0.85
)
```

### `get_belief_state(self, vector_name: str) -> Dict[str, float]`

Get current belief state for a vector.

**Parameters:**
- `vector_name: str` - Name of the vector

**Returns:** `Dict[str, float]` - Current belief parameters (mean, variance, etc.)

**Example:**
```python
belief_state = cascade.get_belief_state("know")
print(f"Mean: {belief_state['mean']}, Variance: {belief_state['variance']}")
```

---

## Drift Monitoring

### `check_for_drift(self) -> Dict[str, Any]`

Check for behavioral drift since the last check.

**Returns:** `Dict[str, Any]` - Drift analysis results

**Example:**
```python
drift_report = cascade.check_for_drift()
if drift_report['detected']:
    print(f"Drift severity: {drift_report['severity']}")
    print(f"Recommendation: {drift_report['recommendation']}")
```

### `reset_drift_counters(self)`

Reset drift monitoring counters.

**Example:**
```python
# Call after making intentional changes to approach
cascade.reset_drift_counters()
```

---

## Epistemic Validation

### `validate_epistemic_consistency(self, vectors_a: Dict[str, float], vectors_b: Dict[str, float], threshold: float = 0.1) -> Dict[str, Any]`

Validate consistency between two epistemic state vectors.

**Parameters:**
- `vectors_a: Dict[str, float]` - First vector set
- `vectors_b: Dict[str, float]` - Second vector set
- `threshold: float` - Maximum allowable difference, default 0.1

**Returns:** `Dict[str, Any]` - Consistency analysis

**Example:**
```python
consistency = cascade.validate_epistemic_consistency(
    preflight_vectors, 
    postflight_vectors,
    threshold=0.15
)

if not consistency['consistent']:
    print(f"Inconsistencies found: {consistency['differences']}")
```

### `calculate_epistemic_delta(self, initial: Dict[str, float], final: Dict[str, float]) -> Dict[str, float]`

Calculate the epistemic delta between two states.

**Parameters:**
- `initial: Dict[str, float]` - Initial epistemic state
- `final: Dict[str, float]` - Final epistemic state

**Returns:** `Dict[str, float]` - Delta values for each vector

**Example:**
```python
delta = cascade.calculate_epistemic_delta(
    initial=preflight_vectors,
    final=postflight_vectors
)

print(f"Knowledge gain: {delta['know']}")
print(f"Uncertainty reduction: {delta['uncertainty']}")
```

---

## Utility Methods

### `get_cascade_state(self) -> Dict[str, Any]`

Get current CASCADE state for persistence or debugging.

**Returns:** `Dict[str, Any]` - Complete cascade state

**Example:**
```python
state = cascade.get_cascade_state()
# Save state for later resumption
```

### `restore_cascade_state(self, state: Dict[str, Any])`

Restore CASCADE to a previous state.

**Parameters:**
- `state: Dict[str, Any]` - State dictionary from get_cascade_state()

**Example:**
```python
# Restore from saved state
cascade.restore_cascade_state(saved_state)
```

---

## Best Practices

1. **Use genuine self-assessment** - The CASCADE framework relies on honest epistemic self-evaluation rather than heuristic proxies.

2. **Maintain epistemic hygiene** - Regularly update beliefs based on new evidence and check for consistency.

3. **Leverage investigation tools** - Register and use appropriate tools to reduce uncertainty during investigation phases.

4. **Monitor for drift** - Enable drift monitoring to catch behavioral inconsistencies early.

5. **Capture learning deltas** - Use postflight assessments to capture what was learned and how to improve.

6. **Set appropriate thresholds** - Adjust confidence and uncertainty thresholds based on task requirements.

---

## Error Handling

Methods typically raise:
- `ValueError` for invalid parameters
- `RuntimeError` for workflow state issues
- `TypeError` for incorrect data types
- Custom exceptions for specific cascade issues

---

**Module Location:** `empirica/core/cascade/metacognitive_cascade.py`
**API Stability:** Stable
**Last Updated:** 2025-12-27