# API Reference - Complete

**Empirica v4.0 - Complete Python API Documentation**

**Date:** 2025-12-08  
**Status:** Production-ready  
**Storage Architecture:** See `docs/architecture/STORAGE_ARCHITECTURE_COMPLETE.md`

---

## Table of Contents

1. [SessionDatabase](#sessiondatabase) - Core session and epistemic data management
2. [CanonicalEpistemicAssessor](#canonicepistemicassessor) - 13-vector self-assessment
3. [MetacognitiveCascade](#metacognitivecascade) - CASCADE workflow orchestration
4. [HandoffReportGenerator](#handoffreportgenerator) - Session continuity

---

## SessionDatabase

**Location:** `empirica/data/session_database.py`

```python
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()  # Uses default: .empirica/sessions/sessions.db
# Or specify path:
db = SessionDatabase(db_path="/custom/path/sessions.db")
```

### Session Management

#### `create_session(ai_id, bootstrap_level=1, components_loaded=6) -> str`

Create new Empirica session.

```python
session_id = db.create_session(ai_id="myai")
# Returns: "4e7abfa2-8838-4635-a8f3-be2ea8f15449"
```

**Parameters:**
- `ai_id` (str): AI agent identifier
- `bootstrap_level` (int): Component loading level (default: 1)
- `components_loaded` (int): Number of components (default: 6)

**Returns:** str - Session UUID

All sessions use unified storage with automatic component loading.

---

#### `get_session(session_id) -> Dict`

Get session metadata.

```python
session = db.get_session(session_id)
# Returns: {'session_id': ..., 'ai_id': ..., 'start_time': ..., ...}
```

**Returns:** Dict with keys:
- `session_id` (str): Session UUID
- `ai_id` (str): AI identifier
- `start_time` (str): ISO timestamp
- `end_time` (Optional[str]): ISO timestamp if ended
- `bootstrap_level` (int): Legacy field
- `components_loaded` (int): Number of components

---

#### `get_all_sessions(limit=50) -> List[Dict]`

List all sessions (most recent first).

```python
sessions = db.get_all_sessions(limit=10)
# Returns: [{'session_id': ..., 'ai_id': ..., ...}, ...]
```

---

#### `get_last_session_by_ai(ai_id) -> Optional[Dict]`

Get most recent session for specific AI.

```python
last_session = db.get_last_session_by_ai("myai")
```

---

#### `end_session(session_id)`

Mark session as ended (sets `end_time`).

```python
db.end_session(session_id)
```

---

### CASCADE Workflow (Reflexes Table)

All CASCADE phases (PREFLIGHT, CHECK, POSTFLIGHT) write to unified `reflexes` table.

#### `log_preflight_assessment(session_id, vectors, reasoning, metadata=None)`

Store PREFLIGHT assessment.

```python
db.log_preflight_assessment(
    session_id=session_id,
    vectors={
        'engagement': 0.8, 'know': 0.6, 'do': 0.7, 'context': 0.65,
        'clarity': 0.7, 'coherence': 0.75, 'signal': 0.6, 'density': 0.5,
        'state': 0.5, 'change': 0.4, 'completion': 0.0, 'impact': 0.3,
        'uncertainty': 0.6
    },
    reasoning="Starting with moderate domain knowledge, high uncertainty about X",
    metadata={'task': 'Investigate OAuth2 flow'}
)
```

**Parameters:**
- `vectors` (Dict[str, float]): 13 epistemic vectors (0.0-1.0)
- `reasoning` (str): Why you scored yourself this way
- `metadata` (Optional[Dict]): Additional context

**Storage:** `reflexes` table + git notes + JSON (atomic 3-layer write)

---

#### `log_check_phase_assessment(session_id, vectors, decision, reasoning, findings, unknowns, confidence_to_proceed, cycle=1, metadata=None)`

Store CHECK phase assessment (decision gate).

```python
db.log_check_phase_assessment(
    session_id=session_id,
    vectors={...},  # 13 vectors after investigation
    decision='proceed',  # or 'investigate', 'proceed_with_caution'
    reasoning="Sufficient understanding of OAuth2 flow, ready to implement",
    findings=["Found authorization endpoint at /oauth/authorize", "Token TTL is 3600s"],
    unknowns=["Refresh token rotation policy unclear"],
    confidence_to_proceed=0.85,
    cycle=1
)
```

**Parameters:**
- `decision` (str): 'proceed' | 'investigate' | 'proceed_with_caution'
- `findings` (List[str]): What you discovered
- `unknowns` (List[str]): What's still unclear
- `confidence_to_proceed` (float): 0.0-1.0

**Storage:** `reflexes` table (phase='CHECK')

---

#### `log_postflight_assessment(session_id, vectors, reasoning, metadata=None)`

Store POSTFLIGHT assessment (measure learning).

```python
db.log_postflight_assessment(
    session_id=session_id,
    vectors={
        'engagement': 0.9, 'know': 0.85, 'do': 0.9, 'context': 0.9,
        'clarity': 0.95, 'coherence': 0.9, 'signal': 0.85, 'density': 0.8,
        'state': 0.9, 'change': 0.85, 'completion': 0.95, 'impact': 0.8,
        'uncertainty': 0.15
    },
    reasoning="Successfully implemented OAuth2 flow, all edge cases handled",
    metadata={'calibration_accuracy': 'well_calibrated'}
)
```

**Calibration:** Include `metadata['calibration_accuracy']` with values:
- `'well_calibrated'`: Confidence matched actual learning
- `'overconfident'`: Claimed more than you learned
- `'underconfident'`: Learned more than you expected

---

#### `get_latest_vectors(session_id, phase=None) -> Optional[Dict]`

Get most recent epistemic vectors for session.

```python
# Get latest PREFLIGHT
preflight = db.get_latest_vectors(session_id, phase='PREFLIGHT')
# Returns: {'vectors': {...}, 'reasoning': '...', 'timestamp': '...'}

# Get latest any phase
latest = db.get_latest_vectors(session_id)
```

---

#### `get_vectors_by_phase(session_id, phase) -> List[Dict]`

Get all assessments for specific phase (e.g., all CHECK cycles).

```python
checks = db.get_vectors_by_phase(session_id, phase='CHECK')
# Returns: [{'vectors': ..., 'cycle': 1, ...}, {'vectors': ..., 'cycle': 2, ...}]
```

---

#### `get_checkpoint_diff(session_id, threshold=0.15) -> Dict`

Compare latest vectors against previous checkpoint.

```python
diff = db.get_checkpoint_diff(session_id, threshold=0.15)
# Returns: {
#   'significant_changes': {'know': 0.25, 'uncertainty': -0.30},
#   'timestamp': '...',
#   'checkpoint_found': True
# }
```

---

### Goals & Subtasks (v4.0 - Complex Work Tracking)

#### `create_goal(session_id, objective, scope_breadth, scope_duration, scope_coordination=0.1, success_criteria=None, estimated_complexity=None, constraints=None, metadata=None) -> str`

Create investigation goal (use when uncertainty > 0.6).

```python
goal_id = db.create_goal(
    session_id=session_id,
    objective="Investigate OAuth2 implementation patterns in codebase",
    scope_breadth=0.6,  # 0.0-1.0, how wide (single file vs entire system)
    scope_duration=0.4,  # 0.0-1.0, expected lifetime (hours vs weeks)
    scope_coordination=0.1,  # 0.0-1.0, multi-agent coordination needed
    success_criteria=["All OAuth2 endpoints documented", "Token flow validated"],
    estimated_complexity=0.7
)
# Returns: "a3f8d4e2-..."
```

**Scope Vectors:**
- `breadth` (float): How wide the goal spans (0.1 = single file, 0.9 = entire system)
- `duration` (float): Expected lifetime (0.1 = 1 hour, 0.9 = weeks)
- `coordination` (float): Multi-agent coordination needed (0.1 = solo, 0.9 = orchestrated)

---

#### `create_subtask(goal_id, description, importance='medium', dependencies=None, estimated_tokens=None) -> str`

Add subtask to goal (use for investigation steps).

```python
subtask_id = db.create_subtask(
    goal_id=goal_id,
    description="Map all OAuth2 API endpoints",
    importance='high',  # critical | high | medium | low
    dependencies=[],
    estimated_tokens=2000
)
```

---

#### `complete_subtask(task_id, evidence=None)`

Mark subtask complete.

```python
db.complete_subtask(task_id, evidence="Commit abc123: Documented OAuth2 endpoints")
```

---

#### `update_subtask_findings(task_id, findings: List[str])`

Log discoveries incrementally (for CHECK decision).

```python
db.update_subtask_findings(subtask_id, [
    "Authorization endpoint: /oauth/authorize",
    "Token endpoint: /oauth/token",
    "Token TTL: 3600s"
])
```

---

#### `update_subtask_unknowns(task_id, unknowns: List[str])`

Track what's still unclear (for CHECK decision).

```python
db.update_subtask_unknowns(subtask_id, [
    "Refresh token rotation policy unclear",
    "Rate limiting configuration unknown"
])
```

---

#### `update_subtask_dead_ends(task_id, dead_ends: List[str])`

Track investigation paths that didn't work (save future effort).

```python
db.update_subtask_dead_ends(subtask_id, [
    "Tried /oauth/v1 endpoints - deprecated",
    "OAuth1.0 signatures not used"
])
```

---

#### `query_unknowns_summary(session_id) -> List[str]`

Get all remaining unknowns across all goals (for CHECK decision).

```python
unknowns = db.query_unknowns_summary(session_id)
# Returns: ["Refresh token rotation unclear", "Rate limiting unknown"]
```

**Use case:** CHECK phase - decide whether to proceed or investigate more.

---

#### `get_goal_tree(goal_id) -> Dict`

Get goal with all subtasks and progress.

```python
tree = db.get_goal_tree(goal_id)
# Returns: {
#   'goal': {...},
#   'subtasks': [{...}, {...}],
#   'completion_percentage': 66.67
# }
```

---

### Legacy CASCADE Tables (Deprecated in v4.0)

#### `create_cascade(session_id, phase) -> int`

**DEPRECATED:** Use `reflexes` table via `log_*_assessment()` methods instead.

#### `get_cascade_assessments(session_id, phase) -> List[Dict]`

**DEPRECATED:** Use `get_vectors_by_phase(session_id, phase)` instead.

---

### Git Checkpoints

#### `get_git_checkpoint(session_id, phase, round_num) -> Optional[Dict]`

Load checkpoint from git notes.

```python
checkpoint = db.get_git_checkpoint(session_id, phase='CHECK', round_num=1)
```

---

#### `list_git_checkpoints(session_id=None, limit=10) -> List[Dict]`

List available checkpoints.

```python
checkpoints = db.list_git_checkpoints(session_id=session_id)
```

---

### Investigation Logging (ACT Phase)

#### `log_act_phase(session_id, actions, artifacts=None, goal_id=None)`

Log actions taken during work execution.

```python
db.log_act_phase(
    session_id=session_id,
    actions=["Implemented OAuth2 authorization flow", "Added token validation"],
    artifacts=["src/auth/oauth.py", "tests/test_oauth.py"],
    goal_id=goal_id
)
```

**Storage:** `reflexes` table (phase='ACT')

---

#### `log_investigation_round(session_id, round_num, findings, unknowns, strategy, confidence)`

Log investigation cycle (for CHECK tracking).

```python
db.log_investigation_round(
    session_id=session_id,
    round_num=1,
    findings=["Found authorization endpoint"],
    unknowns=["Token rotation policy unclear"],
    strategy='code_analysis',
    confidence=0.7
)
```

---

### Session Summaries

#### `get_session_summary(session_id) -> Dict`

Get complete session overview (all phases, goals, deltas).

```python
summary = db.get_session_summary(session_id)
# Returns: {
#   'session': {...},
#   'preflight': {...},
#   'checks': [...],
#   'postflight': {...},
#   'goals': [...],
#   'epistemic_delta': {...}
# }
```

---

### Utility Methods

#### `close()`

Close database connection.

```python
db.close()
```

**Note:** Use context manager for automatic cleanup:

```python
from empirica.data.session_database import SessionDatabase

with SessionDatabase() as db:
    session_id = db.create_session(ai_id="myai")
    # ... work ...
# Automatically closed
```

---

## CanonicalEpistemicAssessor

**Location:** `empirica/core/canonical/canonical_epistemic_assessment.py`

```python
from empirica.core.canonical.canonical_epistemic_assessment import CanonicalEpistemicAssessor

assessor = CanonicalEpistemicAssessor(
    session_id=session_id,
    confidence_threshold=0.70,
    max_investigation_rounds=3
)
```

### Methods

#### `execute_preflight(prompt: str) -> Dict`

Generate PREFLIGHT self-assessment prompt.

```python
result = assessor.execute_preflight("Implement OAuth2 authorization flow")
# Returns: {
#   'session_id': '...',
#   'prompt': 'ASSESS YOUR CURRENT EPISTEMIC STATE...',
#   'phase': 'PREFLIGHT'
# }
```

**AI Integration:** Send `result['prompt']` to AI for genuine self-assessment.

---

#### `submit_preflight_assessment(vectors: Dict, reasoning: str) -> Dict`

Submit AI's self-assessment.

```python
result = assessor.submit_preflight_assessment(
    vectors={'engagement': 0.8, 'know': 0.6, ...},
    reasoning="Starting with moderate knowledge..."
)
# Returns: {'ok': True, 'decision': 'proceed', 'engagement_gate_passed': True}
```

---

#### `execute_check(findings: List[str], unknowns: List[str], confidence_to_proceed: float) -> Dict`

Execute CHECK phase (decision gate).

```python
result = assessor.execute_check(
    findings=["Found OAuth2 endpoints", "Token TTL is 3600s"],
    unknowns=["Refresh token rotation unclear"],
    confidence_to_proceed=0.85
)
# Returns: {
#   'decision': 'proceed',  # or 'investigate'
#   'reasoning': '...',
#   'confidence': 0.85
# }
```

---

#### `execute_postflight(task_summary: str) -> Dict`

Generate POSTFLIGHT self-assessment prompt.

```python
result = assessor.execute_postflight("Implemented OAuth2 flow with token validation")
```

---

## MetacognitiveCascade

**Location:** `empirica/core/metacognitive_cascade/metacognitive_cascade.py`

**DEPRECATED in v4.0:** Use direct `SessionDatabase` methods instead.

The CASCADE workflow is now managed directly through:
- `log_preflight_assessment()`
- `log_check_phase_assessment()`
- `log_postflight_assessment()`

---

## HandoffReportGenerator

**Location:** `empirica/core/handoff/report_generator.py`

```python
from empirica.core.handoff.report_generator import EpistemicHandoffReportGenerator

generator = EpistemicHandoffReportGenerator()
```

### Methods

#### `generate_handoff_report(session_id, task_summary, key_findings, remaining_unknowns, next_session_context, artifacts_created=None) -> Dict`

Generate epistemic handoff (requires CASCADE workflow).

```python
report = generator.generate_handoff_report(
    session_id=session_id,
    task_summary="Investigated OAuth2 implementation patterns",
    key_findings=["Found all endpoints", "Token flow validated"],
    remaining_unknowns=["Rate limiting unclear"],
    next_session_context="Ready to implement rate limiting logic",
    artifacts_created=["docs/oauth2_analysis.md"]
)
# Returns: {
#   'session_id': '...',
#   'epistemic_deltas': {...},
#   'calibration_status': 'well_calibrated',
#   'compressed_json': '...',
#   'markdown': '...'
# }
```

**Storage:** Dual (git notes + database)

**Query:** `empirica handoff-query --session-id <ID>`

---

#### `generate_planning_handoff(session_id, task_summary, key_findings, remaining_unknowns, next_session_context, artifacts_created=None) -> Dict`

Generate planning handoff (no CASCADE required).

```python
report = generator.generate_planning_handoff(
    session_id=session_id,
    task_summary="Planned OAuth2 implementation approach",
    key_findings=["Identified 3 integration points", "Chose PKCE flow"],
    remaining_unknowns=["Performance impact unknown"],
    next_session_context="Begin implementation in next session"
)
```

**Use case:** Documentation-only handoffs, multi-session planning.

---

## Storage Architecture

**Primary:** SQLite database (`.empirica/sessions/sessions.db`)

**Tables:**
- `sessions` - Session metadata
- `reflexes` - **Unified CASCADE storage** (PREFLIGHT, CHECK, POSTFLIGHT, ACT)
- `goals` - Investigation goals
- `subtasks` - Goal breakdown
- `handoff_reports` - Session continuity

**Secondary:** Git notes (distributed, repo-portable)

**Tertiary:** JSON files (`.empirica/sessions/<session_id>.json`)

**Atomic Writes:** All CASCADE phases write to all 3 layers simultaneously.

---

## CLI Integration

All Python API methods have CLI equivalents:

```bash
# Session management
empirica session-create --ai-id myai

# CASCADE workflow
empirica preflight "Task description" --prompt-only
empirica preflight-submit --session-id <ID> --vectors '{...}' --reasoning "..."
empirica check --session-id <ID> --findings '[...]' --unknowns '[...]' --confidence 0.85
empirica check-submit --session-id <ID> --vectors '{...}' --decision proceed
empirica postflight <ID> --prompt-only
empirica postflight-submit --session-id <ID> --vectors '{...}' --reasoning "..."

# Goals
empirica goals-create --session-id <ID> --objective "..." --scope-breadth 0.6 --scope-duration 0.4
empirica goals-add-subtask --goal-id <ID> --description "..." --importance high
empirica goals-complete-subtask --task-id <ID> --evidence "Commit abc123"

# Handoffs
empirica handoff-create --session-id <ID> --task-summary "..." --key-findings '[...]' --remaining-unknowns '[...]' --next-session-context "..."
empirica handoff-query --session-id <ID> --output json
```

---

## Complete Example Workflow

```python
from empirica.data.session_database import SessionDatabase

# 1. Create session
db = SessionDatabase()
session_id = db.create_session(ai_id="myai")

# 2. PREFLIGHT assessment
db.log_preflight_assessment(
    session_id=session_id,
    vectors={'engagement': 0.8, 'know': 0.6, 'do': 0.7, 'context': 0.65,
             'clarity': 0.7, 'coherence': 0.75, 'signal': 0.6, 'density': 0.5,
             'state': 0.5, 'change': 0.4, 'completion': 0.0, 'impact': 0.3,
             'uncertainty': 0.6},
    reasoning="Starting with moderate knowledge, high uncertainty"
)

# 3. Create goal (high uncertainty triggers this)
goal_id = db.create_goal(
    session_id=session_id,
    objective="Investigate OAuth2 implementation",
    scope_breadth=0.6,
    scope_duration=0.4
)

# 4. Add subtasks
subtask_id = db.create_subtask(
    goal_id=goal_id,
    description="Map OAuth2 endpoints",
    importance='high'
)

# 5. Log findings incrementally
db.update_subtask_findings(subtask_id, ["Found /oauth/authorize endpoint"])
db.update_subtask_unknowns(subtask_id, ["Token rotation unclear"])

# 6. CHECK phase (decision gate)
unknowns = db.query_unknowns_summary(session_id)
db.log_check_phase_assessment(
    session_id=session_id,
    vectors={'know': 0.75, 'uncertainty': 0.35, ...},
    decision='proceed',
    reasoning="Sufficient understanding to proceed",
    findings=["Found all endpoints", "Token TTL is 3600s"],
    unknowns=unknowns,
    confidence_to_proceed=0.85,
    cycle=1
)

# 7. ACT phase (do work)
db.log_act_phase(
    session_id=session_id,
    actions=["Implemented OAuth2 flow"],
    artifacts=["src/auth/oauth.py"],
    goal_id=goal_id
)

# 8. Complete subtask
db.complete_subtask(subtask_id, evidence="Commit abc123")

# 9. POSTFLIGHT assessment
db.log_postflight_assessment(
    session_id=session_id,
    vectors={'engagement': 0.9, 'know': 0.85, 'do': 0.9, 'context': 0.9,
             'clarity': 0.95, 'coherence': 0.9, 'signal': 0.85, 'density': 0.8,
             'state': 0.9, 'change': 0.85, 'completion': 0.95, 'impact': 0.8,
             'uncertainty': 0.15},
    reasoning="Successfully implemented OAuth2 flow",
    metadata={'calibration_accuracy': 'well_calibrated'}
)

# 10. Create handoff
from empirica.core.handoff.report_generator import EpistemicHandoffReportGenerator
generator = EpistemicHandoffReportGenerator()
report = generator.generate_handoff_report(
    session_id=session_id,
    task_summary="Implemented OAuth2 authorization flow",
    key_findings=["Flow complete", "All edge cases handled"],
    remaining_unknowns=["Rate limiting configuration"],
    next_session_context="Ready to implement rate limiting"
)

# 11. End session
db.end_session(session_id)
db.close()
```

---

## Next Steps

- **CLI Reference:** See `docs/reference/command-reference.md` for all 49 commands
- **Storage Architecture:** See `docs/architecture/STORAGE_ARCHITECTURE_COMPLETE.md`
- **CASCADE Workflow:** See `docs/production/06_CASCADE_FLOW.md`
- **Goals System:** See `docs/guides/GOAL_TREE_USAGE_GUIDE.md`

---

**Generated:** 2025-12-08  
**Version:** Empirica v4.0  
**Status:** Production-ready
