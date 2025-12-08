# Python API Reference

**Empirica v4.0 - Direct API Usage**

**Storage Architecture:** See `docs/architecture/STORAGE_ARCHITECTURE_COMPLETE.md`  

---

## Quick Reference

### Core Imports
```python
# Session management
from empirica.data.session_database import SessionDatabase

# Core assessment & logging
from empirica.core.canonical import CanonicalEpistemicAssessor, ReflexLogger

# Goal management
from empirica.core.goals.repository import GoalRepository
from empirica.core.goals.types import Goal, ScopeVector, SuccessCriterion

# Handoff reports
from empirica.core.handoff import EpistemicHandoffReportGenerator
```

---

## Session Management API

### SessionDatabase

Create and manage Empirica sessions.

```python
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()

# Create new session (v4.0 simplified)
session_id = db.create_session(ai_id="myai")

# Get session info
session = db.get_session(session_id)

# End session
db.end_session(session_id)

db.close()
```

**Methods:**

#### `create_session(ai_id, bootstrap_level=0, components_loaded=0) -> str`
Creates new session, returns session_id (UUID).

**Parameters:**
- `ai_id` (str): AI identifier for tracking
- `bootstrap_level` (int): Component loading level (default: 1)
- `components_loaded` (int): Informational component count

All sessions use unified storage with automatic component loading.

#### `get_session(session_id) -> dict`
Returns session metadata.

#### `end_session(session_id)`
Marks session as complete.

#### `get_last_session_by_ai(ai_id) -> dict`
Gets most recent session for AI.

---

## CASCADE Logging API

### ReflexLogger

Log epistemic assessments during CASCADE workflow.

```python
from empirica.core.canonical import ReflexLogger

logger = ReflexLogger(session_id=session_id)

# Log PREFLIGHT assessment
vectors = {
    "engagement": 0.8,
    "know": 0.6,
    "do": 0.7,
    "context": 0.7,
    "clarity": 0.8,
    "coherence": 0.9,
    "signal": 0.8,
    "density": 0.4,
    "state": 0.7,
    "change": 0.8,
    "completion": 0.2,
    "impact": 0.7,
    "uncertainty": 0.4
}

logger.log_reflex(
    phase="PREFLIGHT",
    round_num=1,
    vectors=vectors,
    reasoning="Initial task assessment"
)

# ... do work ...

# Log POSTFLIGHT assessment
postflight_vectors = vectors.copy()
postflight_vectors["know"] = 0.85
postflight_vectors["completion"] = 1.0
postflight_vectors["uncertainty"] = 0.15

logger.log_reflex(
    phase="POSTFLIGHT",
    round_num=1,
    vectors=postflight_vectors,
    reasoning="Task complete, learned significantly"
)
```

**Methods:**

#### `log_reflex(phase, round_num, vectors, reasoning, metadata=None)`
Logs epistemic assessment to SQLite + git notes.

**Parameters:**
- `phase` (str): "PREFLIGHT", "CHECK", "POSTFLIGHT"
- `round_num` (int): CASCADE round number (1-N)
- `vectors` (dict): 13 epistemic vectors (0.0-1.0)
- `reasoning` (str): Human-readable explanation
- `metadata` (dict, optional): Additional context

**Required Vectors:**
- `engagement`, `know`, `do`, `context`
- `clarity`, `coherence`, `signal`, `density`
- `state`, `change`, `completion`, `impact`
- `uncertainty`

---

## Epistemic Assessment API

### CanonicalEpistemicAssessor

Generate self-assessment prompts for AIs.

```python
from empirica.core.canonical import CanonicalEpistemicAssessor

assessor = CanonicalEpistemicAssessor()

# Generate PREFLIGHT prompt
prompt = assessor.generate_assessment_prompt(
    phase="PREFLIGHT",
    task="Your task description",
    context={"session_id": session_id}
)

print(prompt)  # LLM-friendly self-assessment prompt
```

**Methods:**

#### `generate_assessment_prompt(phase, task, context=None) -> str`
Generates structured self-assessment prompt.

**Parameters:**
- `phase` (str): "PREFLIGHT", "CHECK", "POSTFLIGHT"
- `task` (str): Task description for AI to assess
- `context` (dict, optional): Additional context

**Returns:** Markdown-formatted prompt asking AI to rate 13 vectors

---

## Goal Management API

### GoalRepository

Manage goals and subtasks.

```python
from empirica.core.goals.repository import GoalRepository
from empirica.core.goals.types import Goal, ScopeVector, SuccessCriterion
import uuid

repo = GoalRepository()

# Create goal
scope = ScopeVector(
    breadth=0.5,      # How wide (0=single file, 1=entire codebase)
    duration=0.3,     # How long (0=minutes, 1=months)
    coordination=0.2  # Multi-agent? (0=solo, 1=heavy coordination)
)

criteria = [
    SuccessCriterion(
        id=str(uuid.uuid4()),
        description="Tests pass",
        validation_method="completion",
        is_required=True,
        is_met=False
    )
]

goal = Goal.create(
    objective="Fix bug in authentication",
    success_criteria=criteria,
    scope=scope
)

# Save goal
success = repo.save_goal(goal, session_id)

# Query goals
goals = repo.list_goals_for_session(session_id)

# Update goal progress
repo.update_goal_progress(goal.id, completion=0.5)

repo.close()
```

**Key Types:**

#### `ScopeVector(breadth, duration, coordination)`
Defines goal scope in 3 dimensions (all 0.0-1.0).

#### `SuccessCriterion`
Defines measurable success condition.

#### `Goal.create(objective, success_criteria, scope=None)`
Factory method for creating goals.

---

## Handoff Reports API

### EpistemicHandoffReportGenerator

Create compressed handoff reports for session continuity.

```python
from empirica.core.handoff import EpistemicHandoffReportGenerator

generator = EpistemicHandoffReportGenerator()

# Generate handoff report
handoff = generator.generate_handoff_report(
    session_id=session_id,
    task_summary="What you accomplished",
    key_findings=["Learning 1", "Learning 2"],
    remaining_unknowns=["Unknown 1"],
    next_session_context="Critical context for next AI",
    artifacts_created=["file1.py", "file2.md"]
)

print(f"Handoff size: {len(handoff['compressed_json'])} chars")
# ~238 tokens vs 20,000 baseline = 98.8% reduction!
```

**Methods:**

#### `generate_handoff_report(...) -> dict`
Creates compressed semantic summary.

**Parameters:**
- `session_id` (str): Session UUID
- `task_summary` (str): 2-3 sentence summary
- `key_findings` (list): What you learned
- `remaining_unknowns` (list): What's still unclear
- `next_session_context` (str): Critical context for next session
- `artifacts_created` (list, optional): Files created

**Returns:** dict with `compressed_json`, `storage_location`, `token_count`

#### `query_handoff_reports(ai_id=None, session_id=None, limit=5) -> list`
Queries previous handoff reports.

---

## Complete Workflow Example

```python
from empirica.data.session_database import SessionDatabase
from empirica.core.canonical import ReflexLogger, CanonicalEpistemicAssessor
from empirica.core.handoff import EpistemicHandoffReportGenerator

# 1. Create session
db = SessionDatabase()
session_id = db.create_session(ai_id="workflow_example")
db.close()

# 2. Initialize components
logger = ReflexLogger(session_id=session_id)
assessor = CanonicalEpistemicAssessor()

# 3. PREFLIGHT - Generate and submit assessment
preflight_prompt = assessor.generate_assessment_prompt(
    phase="PREFLIGHT",
    task="Build authentication system"
)

# (AI performs self-assessment)
preflight_vectors = {
    "engagement": 0.85,
    "know": 0.6,  # Moderate initial knowledge
    "do": 0.7,
    "context": 0.8,
    "clarity": 0.9,
    "coherence": 0.9,
    "signal": 0.85,
    "density": 0.5,
    "state": 0.7,
    "change": 0.8,
    "completion": 0.0,  # Haven't started
    "impact": 0.8,
    "uncertainty": 0.4  # Moderate uncertainty
}

logger.log_reflex(
    phase="PREFLIGHT",
    round_num=1,
    vectors=preflight_vectors,
    reasoning="Starting with moderate knowledge of auth systems"
)

# 4. Do the work...
# (Your implementation code here)

# 5. POSTFLIGHT - Reflect on learning
postflight_vectors = preflight_vectors.copy()
postflight_vectors.update({
    "know": 0.85,  # Learned significantly
    "do": 0.9,     # Built capability
    "completion": 1.0,  # Task complete
    "uncertainty": 0.15  # Much clearer
})

logger.log_reflex(
    phase="POSTFLIGHT",
    round_num=1,
    vectors=postflight_vectors,
    reasoning="Auth system complete, learned OAuth2 flow deeply"
)

# 6. Create handoff report
generator = EpistemicHandoffReportGenerator()
handoff = generator.generate_handoff_report(
    session_id=session_id,
    task_summary="Built OAuth2 authentication system with JWT tokens",
    key_findings=[
        "OAuth2 refresh token rotation is critical for security",
        "JWT claims should be minimal for performance"
    ],
    remaining_unknowns=[
        "Best practices for token revocation at scale"
    ],
    next_session_context="Auth system in place, next: authorization layer",
    artifacts_created=["auth/oauth.py", "auth/jwt_handler.py"]
)

print(f"✅ Session complete: {session_id}")
print(f"📊 Learning delta: KNOW {preflight_vectors['know']} → {postflight_vectors['know']}")
print(f"📦 Handoff stored: {handoff['storage_location']}")
```

---

## Advanced Features

### Git-Enhanced Logging

```python
from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger

# Enables git notes storage (97.5% token reduction)
git_logger = GitEnhancedReflexLogger(
    session_id=session_id,
    enable_git_notes=True
)

# Creates checkpoint in git notes
checkpoint_id = git_logger.add_checkpoint(
    phase="ACT",
    round_num=1,
    vectors=current_vectors,
    metadata={"milestone": "tests passing"}
)

# Load checkpoint
checkpoint = git_logger.get_last_checkpoint()
```

### Bayesian Belief Tracking

```python
from empirica.core.canonical.bayesian_guardian import BayesianGuardian

guardian = BayesianGuardian(session_id=session_id)

# Track belief evolution
guardian.update_belief(
    context_key="oauth_security",
    evidence="Implemented refresh token rotation",
    confidence_delta=0.2
)

# Query beliefs
beliefs = guardian.get_beliefs_for_context("oauth_security")
```

---

## Migration from v1.x

### Old Bootstrap Pattern (v1.x - DEPRECATED)
```python
# ❌ DEPRECATED - Direct component instantiation removed
from empirica.bootstraps import ExtendedMetacognitiveBootstrap

# This no longer works - use CLI or MCP
```

### New Direct API (v2.0)
```bash
# Use CLI for session creation
empirica session-create --ai-id myai --bootstrap-level 1

# Or via Python:
```

```python
from empirica.data.session_database import SessionDatabase
from empirica.core.canonical import ReflexLogger

# Just create a session
db = SessionDatabase()
session_id = db.create_session(ai_id="myai")  # bootstrap_level is legacy, not needed
db.close()

# Components available directly
logger = ReflexLogger(session_id=session_id)
# No bootstrap ceremony needed!
```

**Key Differences:**
- ❌ No ExtendedMetacognitiveBootstrap (REMOVED - bootstrap reserved for system prompts)
- ❌ No component dictionary
- ❌ No pre-loading ceremony
- ✅ Use `empirica session-create` CLI command
- ✅ Or use `SessionDatabase.create_session()` directly
- ✅ Direct imports
- ✅ Lazy-loading components

**Note:** "Bootstrap" now refers only to dynamic system prompt generation.
For sessions, use `session-create` command.

---

## Goal and Subtask Management

**New in v4.0:** Track investigation progress with structured goal trees.

Goals and subtasks provide **decision quality, continuity, and audit trails** for complex investigations. They're **optional** - use them when uncertainty is high or work spans multiple sessions.

### Purpose

- **Decision Quality:** CHECK phase can query `query_unknowns_summary()` to inform readiness decisions
- **Continuity:** Next AI knows exactly what was investigated (findings/unknowns/dead_ends)
- **Audit Trail:** Complete investigation path visible for review

### When to Use

- ✅ **Complex investigations** - Multiple unknowns, non-trivial scope
- ✅ **Multi-session work** - Need to hand off investigation state
- ✅ **CHECK decisions** - Need structured unknowns list to decide readiness
- ⚠️ **Simple tasks** - Skip for straightforward implementations

### The 7 Methods

```python
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()

# 1. Create a goal with scope assessment
goal_id = db.create_goal(
    session_id=session_id,
    objective="Understand OAuth2 authentication flow",
    scope_breadth=0.6,      # 0.0-1.0 (0=single file, 1=entire codebase)
    scope_duration=0.4,     # 0.0-1.0 (0=minutes, 1=months)
    scope_coordination=0.3  # 0.0-1.0 (0=solo, 1=heavy multi-agent)
)

# 2. Create subtasks for investigation
subtask_id = db.create_subtask(
    goal_id=goal_id,
    description="Map OAuth2 endpoints and flow",
    importance='high'  # 'critical' | 'high' | 'medium' | 'low'
)

# 3. Log what you discovered
db.update_subtask_findings(subtask_id, [
    "Auth endpoint: /oauth/authorize",
    "Token endpoint: /oauth/token",
    "PKCE required for public clients",
    "Refresh tokens enabled"
])

# 4. Log what remains unclear (for CHECK decisions)
db.update_subtask_unknowns(subtask_id, [
    "Does MFA affect refresh token behavior?",
    "Best practice for token storage in mobile?",
    "Rate limiting on token endpoint?"
])

# 5. Log paths explored but blocked
db.update_subtask_dead_ends(subtask_id, [
    "JWT extension blocked by security policy",
    "Custom OAuth provider - API docs incomplete"
])

# 6. Get complete goal tree (for review/handoff)
goal_tree = db.get_goal_tree(session_id)
# Returns: List[Dict] with nested subtasks + findings/unknowns/dead_ends

# 7. Query unknowns summary (for CHECK decisions)
unknowns_summary = db.query_unknowns_summary(session_id)
# Returns: {'total_unknowns': int, 'unknowns_by_goal': [...]}
```

### Complete Example: OAuth2 Investigation

**Scenario:** You need to implement OAuth2 authentication but don't fully understand the flow.

```python
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()
session_id = db.create_session(ai_id="oauth_investigation")

# 1. Create goal after PREFLIGHT assessment
goal_id = db.create_goal(
    session_id=session_id,
    objective="Understand OAuth2 authentication flow",
    scope_breadth=0.6,  # Touches auth/, api/, and config/
    scope_duration=0.4,  # Few hours
    scope_coordination=0.3  # Mostly solo, some docs review
)

# 2. Break down investigation
endpoint_task = db.create_subtask(goal_id, "Map OAuth2 endpoints", 'high')
flow_task = db.create_subtask(goal_id, "Understand authorization code flow", 'critical')
security_task = db.create_subtask(goal_id, "Review security requirements", 'high')

# 3. Do investigation work...
# As you discover things, log them:

db.update_subtask_findings(endpoint_task, [
    "Auth endpoint: /oauth/authorize with state param",
    "Token endpoint: /oauth/token with grant_type",
    "PKCE required (code_challenge)",
    "Refresh endpoint: /oauth/refresh"
])

db.update_subtask_unknowns(endpoint_task, [
    "Token expiration times not documented",
    "MFA impact on flow unclear"
])

db.update_subtask_findings(flow_task, [
    "Authorization code → exchange for access token",
    "State parameter prevents CSRF",
    "PKCE prevents auth code interception"
])

db.update_subtask_unknowns(flow_task, [
    "How to handle expired refresh tokens?"
])

db.update_subtask_dead_ends(security_task, [
    "Tried JWT - blocked by security policy (must use opaque tokens)"
])

# 4. At CHECK phase decision point:
unknowns = db.query_unknowns_summary(session_id)
print(f"Total unknowns: {unknowns['total_unknowns']}")
# Output: Total unknowns: 3

# Decision logic:
# - If unknowns are blockers → investigate more
# - If unknowns are low-impact → proceed to implementation

# 5. After implementation (POSTFLIGHT):
goal_tree = db.get_goal_tree(session_id)
# Include in handoff report for next AI

db.close()
```

### Integration with CHECK Phase

Goals/subtasks inform CHECK decisions but are separate from CASCADE phases:

```python
# CHECK phase uses unknowns to decide readiness
unknowns = db.query_unknowns_summary(session_id)

if unknowns['total_unknowns'] == 0:
    decision = "PROCEED"  # High confidence, no unknowns
elif unknowns['total_unknowns'] <= 2 and confidence >= 0.75:
    decision = "PROCEED"  # Few unknowns, high confidence
else:
    decision = "INVESTIGATE"  # Too many unknowns or low confidence
```

### Before vs After Goal Tracking

**Without Goals:**
```python
# PREFLIGHT: "I don't fully understand OAuth2"
# [Do some investigation]
# CHECK: "I think I understand enough?" (no evidence)
# ACT: [Implement, might miss things]
# POSTFLIGHT: "Learned some things, not sure what"
```

**With Goals:**
```python
# PREFLIGHT: "I don't fully understand OAuth2" (uncertainty: 0.6)
# Create goal + subtasks
# [Do structured investigation]
# Update findings: [4 discoveries]
# Update unknowns: [2 remaining questions]
# CHECK: query_unknowns_summary() → 2 unknowns, both low-impact → PROCEED
# ACT: [Implement with confidence]
# POSTFLIGHT: get_goal_tree() → Complete investigation record in handoff
```

### API Reference

#### create_goal()
```python
goal_id = db.create_goal(
    session_id: str,
    objective: str,
    scope_breadth: float = None,      # 0.0-1.0
    scope_duration: float = None,     # 0.0-1.0
    scope_coordination: float = None  # 0.0-1.0
) -> str  # Returns goal_id (UUID)
```

#### create_subtask()
```python
subtask_id = db.create_subtask(
    goal_id: str,
    description: str,
    importance: str = 'medium'  # 'critical'|'high'|'medium'|'low'
) -> str  # Returns subtask_id (UUID)
```

#### update_subtask_findings()
```python
db.update_subtask_findings(
    subtask_id: str,
    findings: List[str]  # JSON stored internally
) -> None
```

#### update_subtask_unknowns()
```python
db.update_subtask_unknowns(
    subtask_id: str,
    unknowns: List[str]  # Used for CHECK decisions
) -> None
```

#### update_subtask_dead_ends()
```python
db.update_subtask_dead_ends(
    subtask_id: str,
    dead_ends: List[str]  # "Attempted X - blocked by Y"
) -> None
```

#### get_goal_tree()
```python
goal_tree = db.get_goal_tree(
    session_id: str
) -> List[Dict]  # Nested: goals → subtasks → findings/unknowns/dead_ends
```

**Returns:**
```python
[
    {
        'goal_id': 'uuid',
        'objective': 'Understand OAuth2 flow',
        'status': 'in_progress',  # 'in_progress'|'complete'|'blocked'
        'scope_breadth': 0.6,
        'scope_duration': 0.4,
        'scope_coordination': 0.3,
        'subtasks': [
            {
                'subtask_id': 'uuid',
                'description': 'Map endpoints',
                'importance': 'high',
                'status': 'complete',
                'findings': ["Auth endpoint: /oauth/authorize", ...],
                'unknowns': ["Token expiration?", ...],
                'dead_ends': ["Tried JWT - blocked", ...]
            }
        ]
    }
]
```

#### query_unknowns_summary()
```python
summary = db.query_unknowns_summary(
    session_id: str
) -> Dict
```

**Returns:**
```python
{
    'total_unknowns': 3,
    'unknowns_by_goal': [
        {
            'goal_id': 'uuid',
            'objective': 'Understand OAuth2 flow',
            'unknown_count': 3
        }
    ]
}
```

### Best Practices

1. **Create goals DURING work, not before** - Goals emerge from investigation
2. **Update incrementally** - Add findings/unknowns as you discover them
3. **Use CHECK with unknowns** - Query before deciding to proceed
4. **Include in handoffs** - Call `get_goal_tree()` in POSTFLIGHT
5. **Don't over-structure** - Simple tasks don't need goals

### Three Separate Concerns

**Understand the distinction:**

1. **CASCADE phases (epistemic checkpoints)**
   - PREFLIGHT/CHECK/POSTFLIGHT
   - Self-assessment at key decision points
   - Stored in `reflexes` table

2. **Goals/subtasks (investigation logging)**
   - Created and updated DURING work
   - Track findings/unknowns/dead_ends
   - Stored in `goals` and `subtasks` tables
   - **Separate from CASCADE but informs CHECK decisions**

3. **Implicit reasoning (natural work)**
   - The actual investigation and implementation
   - Not explicitly logged (unless you choose to)

**They interact but are not nested:** You run PREFLIGHT, then create goals, then investigate (updating subtasks), then run CHECK (querying unknowns), then proceed.

---

## Error Handling

```python
from empirica.data.session_database import SessionDatabase

try:
    db = SessionDatabase()
    session_id = db.create_session(ai_id="myai")
    
    # Your code here
    
    db.end_session(session_id)
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'db' in locals():
        db.close()
```

---

## Best Practices

### 1. Always Close Connections
```python
db = SessionDatabase()
try:
    # ... use db ...
finally:
    db.close()
```

### 2. Use Context for Goal Scope
```python
# Bad: Guessing scope
scope = ScopeVector(0.5, 0.5, 0.5)

# Good: Thoughtful assessment
scope = ScopeVector(
    breadth=0.3,      # Just authentication module
    duration=0.4,     # ~2 days work
    coordination=0.1  # Solo work, minimal coordination
)
```

### 3. Meaningful Reasoning
```python
# Bad: Generic
reasoning="Task complete"

# Good: Specific learning
reasoning="Implemented OAuth2 flow. Learned that refresh token rotation prevents token theft attacks. Initially uncertain about token storage, now confident SQLite with encryption is sufficient for MVP."
```

### 4. Track Epistemic Growth
```python
# Calculate learning delta
know_growth = postflight["know"] - preflight["know"]
uncertainty_reduction = preflight["uncertainty"] - postflight["uncertainty"]

if know_growth > 0.2 and uncertainty_reduction > 0.2:
    print("✅ Significant learning occurred")
```

---

## API Summary Table

| Module | Class/Function | Purpose |
|--------|---------------|---------|
| `session_database` | `SessionDatabase` | Create/manage sessions |
| `reflex_logger` | `ReflexLogger` | Log CASCADE assessments |
| `canonical` | `CanonicalEpistemicAssessor` | Generate assessment prompts |
| `goals.repository` | `GoalRepository` | Manage goals/subtasks |
| `handoff` | `EpistemicHandoffReportGenerator` | Create handoff reports |
| `git_enhanced_reflex_logger` | `GitEnhancedReflexLogger` | Git notes checkpoints |
| `bayesian_guardian` | `BayesianGuardian` | Track belief evolution |

---

## Next Steps

- **[Basic Usage](03_BASIC_USAGE.md)** - Getting started guide
- **[CASCADE Flow](06_CASCADE_FLOW.md)** - Workflow details
- **[Session Management](12_SESSION_DATABASE.md)** - Advanced features
- **[CLI Reference](19_API_REFERENCE.md)** - Command-line usage

