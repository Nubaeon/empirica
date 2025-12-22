# Goals Repository Module

The `empirica.core.goals.repository` module provides database operations for goal persistence and management.

## Classes

### GoalRepository

**Module**: `empirica.core.goals.repository`

**Purpose**: Database operations for Goal persistence with full serialization

**Inherits**: None

**Attributes**:
- `db` (`SessionDatabase`): Database connection instance
- `logger` (`logging.Logger`): Logger instance for debugging

**Methods**:

#### `__init__(db_path: Optional[str] = None)`

**Purpose**: Initialize the goal repository

**Parameters**:
- `db_path` (`Optional[str]`): Optional custom database path. If None, uses default Empirica database.

**Example**:
```python
from empirica.core.goals.repository import GoalRepository

# Initialize with default database
repo = GoalRepository()

# Initialize with custom database path
custom_repo = GoalRepository(db_path="/path/to/custom.db")
```

**Related**: `SessionDatabase` - Underlying database connection

---

#### `get_goal(goal_id: str) -> Optional[Goal]`

**Purpose**: Retrieve a goal by its unique identifier

**Parameters**:
- `goal_id` (`str`): Unique goal identifier

**Returns**:
- `Optional[Goal]`: Goal object if found, None otherwise

**Example**:
```python
# Retrieve a goal by ID
goal = repo.get_goal("ac48c59b-76de-47db-943c-3f557d270435")
if goal:
    print(f"Found goal: {goal.objective}")
else:
    print("Goal not found")
```

**Related**:
- `Goal` - Goal data class
- `save_goal()` - Save a goal to database

---

#### `save_goal(goal: Goal) -> bool`

**Purpose**: Save a goal to the database

**Parameters**:
- `goal` (`Goal`): Goal object to save

**Returns**:
- `bool`: True if save was successful, False otherwise

**Example**:
```python
from empirica.core.goals.types import Goal, ScopeVector
from datetime import datetime

# Create a new goal
goal = Goal(
    id="new-goal-id",
    session_id="current-session",
    objective="Complete documentation",
    scope=ScopeVector(breadth=0.8, duration=0.7, coordination=0.3),
    estimated_complexity=0.6,
    created_timestamp=datetime.now().timestamp(),
    is_completed=False
)

# Save the goal
success = repo.save_goal(goal)
if success:
    print("Goal saved successfully")
else:
    print("Failed to save goal")
```

**Related**:
- `Goal` - Goal data class
- `get_goal()` - Retrieve a saved goal

---

#### `get_session_goals(session_id: str) -> List[Goal]`

**Purpose**: Retrieve all goals for a specific session

**Parameters**:
- `session_id` (`str`): Session identifier

**Returns**:
- `List[Goal]`: List of goals belonging to the session

**Example**:
```python
# Get all goals for current session
goals = repo.get_session_goals("81a9dfd3")
print(f"Found {len(goals)} goals for this session")

for goal in goals:
    print(f"- {goal.objective} (completed: {goal.is_completed})")
```

**Related**:
- `get_goal()` - Get single goal by ID
- `Session` - Session management

---

#### `update_goal_completion(goal_id: str, is_completed: bool) -> bool`

**Purpose**: Update the completion status of a goal

**Parameters**:
- `goal_id` (`str`): Goal identifier
- `is_completed` (`bool`): New completion status

**Returns**:
- `bool`: True if update was successful, False otherwise

**Example**:
```python
# Mark a goal as completed
success = repo.update_goal_completion("goal-id-123", True)
if success:
    print("Goal marked as completed")
```

**Related**:
- `get_goal()` - Retrieve goal to check current status
- `save_goal()` - Full goal updates

---

## Database Schema

The goals repository uses the following database tables:

### `goals` Table

```sql
CREATE TABLE goals (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    objective TEXT NOT NULL,
    scope TEXT NOT NULL,
    estimated_complexity REAL,
    created_timestamp REAL NOT NULL,
    completed_timestamp REAL,
    is_completed BOOLEAN DEFAULT 0,
    goal_data TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
)
```

**Fields**:
- `id`: Unique goal identifier (UUID)
- `session_id`: Session this goal belongs to
- `objective`: Goal description/objective
- `scope`: Serialized scope vector (breadth, duration, coordination)
- `estimated_complexity`: Complexity estimate (0.0-1.0)
- `created_timestamp`: When goal was created (Unix timestamp)
- `completed_timestamp`: When goal was completed (Unix timestamp, nullable)
- `is_completed`: Completion status
- `goal_data`: Full serialized goal data (JSON)

---

## Usage Patterns

### Basic Workflow

```python
from empirica.core.goals.repository import GoalRepository
from empirica.core.goals.types import Goal, ScopeVector
from datetime import datetime

# Initialize repository
repo = GoalRepository()

# Create and save a goal
goal = Goal(
    id="example-goal",
    session_id="current-session",
    objective="Document goals module",
    scope=ScopeVector(breadth=0.5, duration=0.3, coordination=0.1),
    estimated_complexity=0.4,
    created_timestamp=datetime.now().timestamp(),
    is_completed=False
)

repo.save_goal(goal)

# Retrieve the goal
retrieved_goal = repo.get_goal("example-goal")

# Mark as completed
repo.update_goal_completion("example-goal", True)
```

### Session-Based Goal Management

```python
# Get all goals for a session
session_goals = repo.get_session_goals("81a9dfd3")

# Process goals
for goal in session_goals:
    if not goal.is_completed:
        print(f"Incomplete goal: {goal.objective}")
```

---

## Integration with Empirica

The GoalRepository integrates with:

1. **CLI Commands**: Used by `goals-create`, `goals-list`, etc.
2. **Session Management**: Goals are linked to sessions via `session_id`
3. **Validation**: Uses `empirica.core.goals.validation` for data integrity
4. **Types**: Uses `empirica.core.goals.types.Goal` data class

This module provides the persistence layer for Empirica's goal-oriented workflow system.