# Core Session Management API

**Module:** `empirica.data.session_database.SessionDatabase`
**Category:** Core Infrastructure
**Stability:** Production Ready

---

## Overview

The `SessionDatabase` class provides the central database interface for all Empirica session data. It manages:

- Session lifecycle (creation, tracking, completion)
- CASCADE execution tracking
- Epistemic vector storage and retrieval
- Project association and linking
- Git-native checkpointing

---

## Class: SessionDatabase

### Constructor

#### `__init__(self, db_path: Optional[str] = None)`

Initialize the session database.

**Parameters:**
- `db_path: Optional[str]` - Path to SQLite database file. If None, uses default location.

**Example:**
```python
from empirica.data.session_database import SessionDatabase

# Use default database location
db = SessionDatabase()

# Use custom database location
db = SessionDatabase(db_path="./custom/sessions.db")
```

---

## Session Management Methods

### `create_session(self, ai_id: str, bootstrap_level: int = 0, components_loaded: int = 0, user_id: Optional[str] = None, subject: Optional[str] = None) -> str`

Create a new AI session.

**Parameters:**
- `ai_id: str` - AI identifier for the session
- `bootstrap_level: int` - Bootstrap level (0-4 or minimal/standard/complete), default 0
- `components_loaded: int` - Number of components loaded, default 0
- `user_id: Optional[str]` - Optional user identifier
- `subject: Optional[str]` - Optional subject/workstream identifier for filtering

**Returns:** `str` - Session ID (UUID string)

**Example:**
```python
session_id = db.create_session(ai_id="claude-sonnet-4", bootstrap_level=2)
```

### `end_session(self, session_id: str, avg_confidence: Optional[float] = None, drift_detected: bool = False, notes: Optional[str] = None)`

Mark a session as ended.

**Parameters:**
- `session_id: str` - Session identifier to end
- `avg_confidence: Optional[float]` - Average confidence during session
- `drift_detected: bool` - Whether behavioral drift was detected
- `notes: Optional[str]` - Optional notes about session completion

**Example:**
```python
db.end_session(session_id="abc-123", avg_confidence=0.78, notes="Completed initial setup")
```

### `get_session(self, session_id: str) -> Optional[Dict]`

Get session data by ID.

**Parameters:**
- `session_id: str` - Session identifier

**Returns:** `Optional[Dict]` - Session data dictionary or None if not found

**Example:**
```python
session_data = db.get_session(session_id="abc-123")
if session_data:
    print(f"AI: {session_data['ai_id']}")
```

### `get_all_sessions(self, ai_id: Optional[str] = None, limit: int = 50) -> List[Dict]`

List all sessions, optionally filtered by AI ID.

**Parameters:**
- `ai_id: Optional[str]` - Optional AI identifier to filter by
- `limit: int` - Maximum number of sessions to return, default 50

**Returns:** `List[Dict]` - List of session dictionaries

**Example:**
```python
# Get all sessions for a specific AI
sessions = db.get_all_sessions(ai_id="claude-sonnet-4", limit=10)

# Get recent sessions
recent_sessions = db.get_all_sessions(limit=20)
```

### `get_session_summary(self, session_id: str, detail_level: str = 'summary') -> Optional[Dict]`

Generate comprehensive session summary for resume/handoff.

**Parameters:**
- `session_id: str` - Session to summarize
- `detail_level: str` - Detail level ('summary', 'detailed', or 'full'), default 'summary'

**Returns:** `Optional[Dict]` - Session summary dictionary or None

**Example:**
```python
summary = db.get_session_summary(session_id="abc-123", detail_level="detailed")
```

---

## CASCADE Management Methods

### `create_cascade(self, session_id: str, task: str, context: Dict[str, Any], goal_id: Optional[str] = None, goal: Optional[Dict[str, Any]] = None) -> str`

Create a new CASCADE execution record.

**Parameters:**
- `session_id: str` - Session identifier
- `task: str` - Task description
- `context: Dict[str, Any]` - Context dictionary
- `goal_id: Optional[str]` - Optional goal identifier
- `goal: Optional[Dict[str, Any]]` - Optional full goal object

**Returns:** `str` - Cascade ID (UUID string)

**Example:**
```python
cascade_id = db.create_cascade(
    session_id="abc-123",
    task="Implement user authentication system",
    context={"repo": "/path/to/project", "deadline": "2025-01-15"}
)
```

### `complete_cascade(self, cascade_id: str, final_action: str, final_confidence: float, investigation_rounds: int, duration_ms: int, engagement_gate_passed: bool, bayesian_active: bool = False, drift_monitored: bool = False)`

Mark a CASCADE as completed with final results.

**Parameters:**
- `cascade_id: str` - Cascade identifier
- `final_action: str` - Final action taken
- `final_confidence: float` - Final confidence score
- `investigation_rounds: int` - Number of investigation rounds performed
- `duration_ms: int` - Duration in milliseconds
- `engagement_gate_passed: bool` - Whether engagement gate was passed
- `bayesian_active: bool` - Whether Bayesian reasoning was active, default False
- `drift_monitored: bool` - Whether drift was monitored, default False

**Example:**
```python
db.complete_cascade(
    cascade_id="xyz-789",
    final_action="Authentication system implemented",
    final_confidence=0.85,
    investigation_rounds=3,
    duration_ms=120000,
    engagement_gate_passed=True
)
```

### `get_session_cascades(self, session_id: str) -> List[Dict]`

Get all cascades for a session.

**Parameters:**
- `session_id: str` - Session identifier

**Returns:** `List[Dict]` - List of cascade dictionaries

**Example:**
```python
cascades = db.get_session_cascades(session_id="abc-123")
for cascade in cascades:
    print(f"Cascade: {cascade['task']} - Confidence: {cascade['final_confidence']}")
```

---

## Epistemic Vector Methods

### `store_vectors(self, session_id: str, phase: str, vectors: Dict[str, float], cascade_id: Optional[str] = None, round_num: int = 1, metadata: Optional[Dict] = None, reasoning: Optional[str] = None)`

Store epistemic vectors in the reflexes table.

**Parameters:**
- `session_id: str` - Session identifier
- `phase: str` - Current phase ('PREFLIGHT', 'CHECK', 'ACT', 'POSTFLIGHT')
- `vectors: Dict[str, float]` - Dictionary of 13 epistemic vectors
- `cascade_id: Optional[str]` - Optional cascade identifier
- `round_num: int` - Current round number, default 1
- `metadata: Optional[Dict]` - Optional metadata dictionary
- `reasoning: Optional[str]` - Optional reasoning explanation

**Example:**
```python
vectors = {
    "engagement": 0.85,
    "know": 0.72,
    "do": 0.68,
    "context": 0.91,
    "clarity": 0.75,
    "coherence": 0.82,
    "signal": 0.79,
    "density": 0.65,
    "state": 0.77,
    "change": 0.88,
    "completion": 0.60,
    "impact": 0.74,
    "uncertainty": 0.23
}

db.store_vectors(
    session_id="abc-123",
    phase="PREFLIGHT",
    vectors=vectors,
    reasoning="High uncertainty due to unfamiliar authentication patterns"
)
```

### `get_latest_vectors(self, session_id: str, phase: Optional[str] = None) -> Optional[Dict]`

Get the latest epistemic vectors for a session.

**Parameters:**
- `session_id: str` - Session identifier
- `phase: Optional[str]` - Optional phase filter

**Returns:** `Optional[Dict]` - Latest vectors dictionary or None

**Example:**
```python
latest_vectors = db.get_latest_vectors(session_id="abc-123", phase="POSTFLIGHT")
if latest_vectors:
    print(f"Knowledge gain: {latest_vectors['vectors']['know']}")
```

### `get_vectors_by_phase(self, session_id: str, phase: str) -> List[Dict]`

Get all vectors for a specific phase.

**Parameters:**
- `session_id: str` - Session identifier
- `phase: str` - Phase name ('PREFLIGHT', 'CHECK', 'POSTFLIGHT', etc.)

**Returns:** `List[Dict]` - List of vector records

**Example:**
```python
check_vectors = db.get_vectors_by_phase(session_id="abc-123", phase="CHECK")
for vector_record in check_vectors:
    print(f"Round {vector_record['round']}: Confidence {vector_record['vectors']['know']}")
```

---

## Project Management Methods

### `create_project(self, name: str, description: Optional[str] = None, repos: Optional[List[str]] = None) -> str`

Create a new project.

**Parameters:**
- `name: str` - Project name (e.g., "Empirica Core")
- `description: Optional[str]` - Project description
- `repos: Optional[List[str]]` - List of repository names

**Returns:** `str` - Project ID (UUID string)

**Example:**
```python
project_id = db.create_project(
    name="User Authentication Module",
    description="Implement secure user authentication system",
    repos=["https://github.com/example/auth-service"]
)
```

### `link_session_to_project(self, session_id: str, project_id: str)`

Link a session to a project.

**Parameters:**
- `session_id: str` - Session identifier
- `project_id: str` - Project identifier

**Example:**
```python
db.link_session_to_project(session_id="abc-123", project_id="xyz-789")
```

### `get_project_sessions(self, project_id: str) -> List[Dict]`

Get all sessions for a project.

**Parameters:**
- `project_id: str` - Project identifier

**Returns:** `List[Dict]` - List of session dictionaries

**Example:**
```python
project_sessions = db.get_project_sessions(project_id="xyz-789")
print(f"Project has {len(project_sessions)} sessions")
```

---

## Utility Methods

### `close(self)`

Close the database connection.

**Example:**
```python
db.close()
```

### `get_session_snapshot(self, session_id: str) -> Optional[Dict]`

Get git-native session snapshot showing where you left off.

**Parameters:**
- `session_id: str` - Session identifier

**Returns:** `Optional[Dict]` - Snapshot dictionary with git state, epistemic trajectory, etc.

**Example:**
```python
snapshot = db.get_session_snapshot(session_id="abc-123")
if snapshot:
    print(f"Last git state: {snapshot['git_state']}")
```

---

## Best Practices

1. **Always close the database connection** when done:
   ```python
   try:
       db = SessionDatabase()
       # ... use db ...
   finally:
       db.close()
   # Or use context manager if available
   ```

2. **Use appropriate detail levels** for summaries based on your needs:
   - `'summary'` for quick overviews
   - `'detailed'` for handoffs
   - `'full'` for complete analysis

3. **Include meaningful metadata** when storing vectors to enable better analysis later.

4. **Link sessions to projects** to enable cross-session analysis and continuity.

---

## Error Handling

The SessionDatabase methods typically raise standard exceptions:
- `sqlite3.Error` for database-related issues
- `ValueError` for invalid parameters
- `FileNotFoundError` if database file cannot be accessed

---

**Module Location:** `empirica/data/session_database.py`
**API Stability:** Stable
**Last Updated:** 2025-12-27