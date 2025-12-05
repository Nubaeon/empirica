# Python API Reference

**Empirica v2.0 - Direct API Usage**

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

# Create new session
session_id = db.create_session(
    ai_id="myai",              # AI identifier
    bootstrap_level=1,         # 0-4, default 1
    components_loaded=6        # Component count (informational)
)

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
- `bootstrap_level` (int): 0-4, indicates session type
- `components_loaded` (int): Informational component count

**Bootstrap Levels:**
- `0`: Minimal (production)
- `1`: Standard (recommended)
- `2`: Extended (full metacognitive tracking)
- `3-4`: Experimental

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
from empirica.core.canonical.reflex_logger import ReflexLogger

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
from empirica.core.canonical.reflex_logger import ReflexLogger
from empirica.core.canonical import CanonicalEpistemicAssessor
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
# ❌ DEPRECATED - Bootstrap classes removed (bootstrap reserved for system prompts)
from empirica.bootstraps import ExtendedMetacognitiveBootstrap

bootstrap = ExtendedMetacognitiveBootstrap(level="2", ai_id="myai")
components = bootstrap.bootstrap()
cascade = components['canonical_cascade']
assessor = components['canonical_assessor']
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
session_id = db.create_session(ai_id="myai", bootstrap_level=1)
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

