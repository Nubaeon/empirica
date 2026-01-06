# Canonical Storage - The Foundation Layer

**Module:** `empirica.core.canonical`

The Canonical storage layer provides the foundational persistence mechanisms for Empirica. All epistemic state ultimately flows through these classes to reach SQLite, Git notes, or JSON logs.

## Philosophy

Three-layer atomic writes:
1. **SQLite** - Primary structured data (fast queries)
2. **Git Notes** - Distributed, version-controlled (portability)
3. **JSON Logs** - Human-readable audit trail (debugging)

Every epistemic operation writes to all three layers atomically.

---

## Architecture

```
                   ┌───────────────────────────────────┐
                   │     GitEnhancedReflexLogger       │
                   │     (Unified Storage Interface)    │
                   └───────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
    ┌──────────┐      ┌──────────────┐    ┌──────────┐
    │  SQLite  │      │  Git Notes   │    │   JSON   │
    │ Database │      │   Storage    │    │   Logs   │
    └──────────┘      └──────────────┘    └──────────┘
           │                  │                  │
           ▼                  ▼                  ▼
    sessions.db        refs/notes/        .empirica/logs/
                       empirica/
```

---

## Core Classes

### GitNotesStorage

Low-level git notes storage for epistemic checkpoints.

```python
storage = GitNotesStorage(
    session_id="abc123",
    git_repo_path=Path("."),
    signing_persona=signing_persona  # Optional cryptographic signing
)

# Add checkpoint to git notes
note_sha = storage.add_note({
    "phase": "CHECK",
    "round": 1,
    "vectors": {"know": 0.7, "uncertainty": 0.3},
    "timestamp": time.time()
})
# Creates: refs/notes/empirica/session/{session_id}/CHECK/1

# Retrieve checkpoints
checkpoints = storage.get_checkpoints(
    session_id="abc123",
    phase_filter="CHECK",
    limit=10
)
```

**Namespace hierarchy:**
```
refs/notes/empirica/
├── session/{session_id}/
│   ├── PREFLIGHT/1
│   ├── CHECK/1
│   ├── POSTFLIGHT/1
│   └── ...
├── handoff/{session_id}
├── tasks/{goal_id}
└── ...
```

### GitStateCapture

Captures current git repository state for checkpoint context.

```python
capture = GitStateCapture(repo_path=Path("."))

state = capture.capture_state()
# Returns: {
#     "commit_hash": "abc1234",
#     "branch": "main",
#     "dirty": False,
#     "staged_files": [],
#     "unstaged_files": []
# }
```

### CheckpointStorage

Stores and retrieves epistemic checkpoints with optional signing.

```python
storage = CheckpointStorage(
    db_path=".empirica/sessions/sessions.db",
    signing_enabled=True
)

# Store checkpoint
checkpoint_id = storage.store_checkpoint(
    session_id="abc123",
    phase="CHECK",
    vectors={"know": 0.7, "uncertainty": 0.3},
    reasoning="Gate check for praxic transition",
    metadata={"goal_id": "xyz789"}
)

# Retrieve checkpoint
checkpoint = storage.get_checkpoint(checkpoint_id)

# List session checkpoints
checkpoints = storage.list_checkpoints(
    session_id="abc123",
    phase="CHECK"
)
```

### GitGoalStore

Git-backed storage for goals with cryptographic integrity.

```python
store = GitGoalStore(repo_path=".")

# Store goal in git notes
store.store_goal(
    goal_id="xyz789",
    objective="Implement OAuth2",
    success_criteria=["Tests pass", "Code reviewed"],
    session_id="abc123"
)

# Retrieve goal
goal = store.get_goal("xyz789")

# List session goals
goals = store.list_session_goals("abc123")
```

### VectorState

Data class representing epistemic vector state at a point in time.

```python
@dataclass
class VectorState:
    know: float
    uncertainty: float
    context: float
    clarity: float
    coherence: float
    signal: float
    density: float
    engagement: float
    state: float
    change: float
    completion: float
    impact: float
    timestamp: float
```

### SessionSync

Synchronizes session state across storage layers.

```python
sync = SessionSync(session_id="abc123")

# Sync session to all storage layers
result = sync.sync_all()
# Returns: {'sqlite': True, 'git_notes': True, 'json_logs': True}

# Check sync status
status = sync.check_sync_status()
# Returns: {'in_sync': True, 'last_sync': 1704628800}
```

---

## Sentinel Integration

### SentinelState

Represents Sentinel gate state at CHECK time.

```python
@dataclass
class SentinelState:
    decision: SentinelDecision  # PROCEED, INVESTIGATE, HALT
    vectors: Dict[str, float]
    corrected_vectors: Dict[str, float]
    gate_passed: bool
    reasoning: str
```

### SentinelDecision (Enum)

```python
class SentinelDecision(Enum):
    PROCEED = "proceed"
    INVESTIGATE = "investigate"
    HALT = "halt"
    ESCALATE = "escalate"
```

### TurtleStatus (Enum)

Investigation branch status (multi-agent investigation).

```python
class TurtleStatus(Enum):
    ACTIVE = "active"
    MERGED = "merged"
    ABANDONED = "abandoned"
    BLOCKED = "blocked"
```

### SentinelHooks

Git hooks integration for Sentinel enforcement.

```python
hooks = SentinelHooks(repo_path=".")

# Install pre-commit hook
hooks.install_pre_commit()

# Check if commit should be allowed
allowed = hooks.check_commit(
    commit_message="feat: Add OAuth2 flow",
    vectors={"know": 0.7, "uncertainty": 0.3}
)
```

---

## Storage Paths

| Storage | Path | Purpose |
|---------|------|---------|
| SQLite | `.empirica/sessions/sessions.db` | Primary structured data |
| Git Notes | `refs/notes/empirica/...` | Distributed, version-controlled |
| JSON Logs | `.empirica/logs/*.jsonl` | Human-readable audit trail |
| Lessons | `.empirica/lessons/*.yaml` | Cold storage for lessons |

---

## Git Isomorphism

Every epistemic state maps to a git state:
- Session checkpoints → git notes
- Goals → git notes + database
- Findings → git notes + database + Qdrant

This enables:
- Versioned confidence tracking
- Repo-portable epistemic history
- Audit trail for compliance

---

## Source Files

- `empirica/core/canonical/git_notes_storage.py` - GitNotesStorage
- `empirica/core/canonical/git_state_capture.py` - GitStateCapture
- `empirica/core/canonical/checkpoint_storage.py` - CheckpointStorage
- `empirica/core/canonical/git_enhanced_reflex_logger.py` - Unified logger
- `empirica/core/canonical/empirica_git/goal_store.py` - GitGoalStore
- `empirica/core/canonical/empirica_git/sentinel_hooks.py` - SentinelHooks, SentinelState
- `empirica/core/canonical/empirica_git/session_sync.py` - SessionSync
