# System Utilities API

**Module:** Various utility modules in `empirica.utils.*`
**Category:** System & Infrastructure
**Stability:** Production Ready

---

## Overview

The System Utilities API provides essential infrastructure tools for:

- Branch mapping and Git integration
- Documentation-code integrity checking
- Configuration management
- Migration tools
- Session state management

---

## Branch Mapping System

### `class BranchMapping`

Manages the mapping between Git branches and Empirica goals for AI agents working on multi-branch projects.

#### `__init__(self, repo_root: Optional[str] = None)`

Initialize the branch mapping system.

**Parameters:**
- `repo_root: Optional[str]` - Git repository root, defaults to searching from current directory

**Example:**
```python
from empirica.utils.branch_mapping import BranchMapping

branch_mapper = BranchMapping()
# Or specify a specific repository
branch_mapper = BranchMapping(repo_root="/path/to/project")
```

### `add_mapping(self, branch_name: str, goal_id: str, beads_issue_id: Optional[str] = None, ai_id: Optional[str] = None, session_id: Optional[str] = None) -> bool`

Add a mapping between a Git branch and an Empirica goal.

**Parameters:**
- `branch_name: str` - Git branch name
- `goal_id: str` - Empirica goal UUID
- `beads_issue_id: Optional[str]` - Optional BEADS issue ID
- `ai_id: Optional[str]` - Optional AI identifier
- `session_id: Optional[str]` - Optional session UUID

**Returns:** `bool` - True if mapping added, False if branch already mapped

**Example:**
```python
success = branch_mapper.add_mapping(
    branch_name="feature/user-auth",
    goal_id="goal-123",
    ai_id="claude-sonnet-4",
    beads_issue_id="bd-auth-456"
)

if success:
    print("Branch mapped successfully")
else:
    print("Branch already mapped to another goal")
```

### `get_mapping(self, branch_name: str) -> Optional[Dict]`

Get the mapping for a specific branch.

**Parameters:**
- `branch_name: str` - Git branch name

**Returns:** `Optional[Dict]` - Mapping dictionary or None if not found

**Example:**
```python
mapping = branch_mapper.get_mapping(branch_name="feature/user-auth")
if mapping:
    print(f"Branch maps to goal: {mapping['goal_id']}")
    print(f"AI working on it: {mapping['ai_id']}")
```

### `get_branch_for_goal(self, goal_id: str) -> Optional[str]`

Find which branch is associated with a goal.

**Parameters:**
- `goal_id: str` - Goal identifier

**Returns:** `Optional[str]` - Branch name or None if not found

**Example:**
```python
branch = branch_mapper.get_branch_for_goal(goal_id="goal-123")
if branch:
    print(f"Goal {goal_id} is on branch: {branch}")
```

### `list_active_mappings(self) -> List[Dict]`

List all active branch-goal mappings.

**Returns:** `List[Dict]` - List of mapping dictionaries

**Example:**
```python
mappings = branch_mapper.list_active_mappings()
for mapping in mappings:
    print(f"{mapping['branch_name']} -> {mapping['goal_id']}")
```

### `remove_mapping(self, branch_name: str, archive: bool = True) -> bool`

Remove a branch mapping.

**Parameters:**
- `branch_name: str` - Branch to remove mapping for
- `archive: bool` - If True, archives mapping instead of deleting, default True

**Returns:** `bool` - True if removed, False if not found

**Example:**
```python
# Remove mapping and archive it
removed = branch_mapper.remove_mapping(branch_name="feature/user-auth", archive=True)

# Permanently delete mapping
removed = branch_mapper.remove_mapping(branch_name="feature/user-auth", archive=False)
```

### `get_history(self, limit: int = 50) -> List[Dict]`

Get branch mapping history.

**Parameters:**
- `limit: int` - Maximum number of history items, default 50

**Returns:** `List[Dict]` - List of historical mapping records

**Example:**
```python
history = branch_mapper.get_history(limit=20)
for record in history:
    print(f"{record['timestamp']}: {record['branch_name']} -> {record['goal_id']}")
```

---

## Documentation-Code Integrity Checker

### `class DocCodeIntegrityAnalyzer`

Analyzes integrity between documentation and codebase to ensure consistency.

#### `__init__(self, project_root: Optional[str] = None)`

Initialize the integrity analyzer.

**Parameters:**
- `project_root: Optional[str]` - Project root directory, defaults to current directory

**Example:**
```python
from empirica.utils.doc_code_integrity import DocCodeIntegrityAnalyzer

analyzer = DocCodeIntegrityAnalyzer()
```

### `analyze_cli_commands(self) -> Dict[str, List[str]]`

Analyze CLI command integrity between documentation and implementation.

**Returns:** `Dict[str, List[str]]` - Dictionary with:
- `commands_in_docs` - Commands mentioned in documentation
- `commands_in_code` - Commands actually implemented
- `missing_in_code` - Documented but not implemented
- `missing_in_docs` - Implemented but not documented

**Example:**
```python
integrity_report = analyzer.analyze_cli_commands()

print(f"Commands in docs: {len(integrity_report['commands_in_docs'])}")
print(f"Commands in code: {len(integrity_report['commands_in_code'])}")
print(f"Missing in code: {integrity_report['missing_in_code']}")
print(f"Missing in docs: {integrity_report['missing_in_docs']}")
```

### `get_detailed_gaps(self) -> Dict[str, Any]`

Get detailed information about integrity gaps.

**Returns:** `Dict[str, Any]` - Detailed gap analysis with file locations and context

**Example:**
```python
detailed_gaps = analyzer.get_detailed_gaps()
for gap_type, details in detailed_gaps.items():
    print(f"{gap_type}: {len(details)} issues found")
    for detail in details[:3]:  # Show first 3
        print(f"  - {detail['location']}: {detail['issue']}")
```

### `analyze_complete_integrity(self) -> Dict[str, Any]`

Run complete integrity analysis including deprecation and superfluity checks.

**Returns:** `Dict[str, Any]` - Comprehensive integrity report

**Example:**
```python
full_report = analyzer.analyze_complete_integrity()
print(f"Integrity score: {full_report['integrity_score']}")
print(f"Phantom commands: {full_report['phantom_commands']}")
print(f"Missing documentation: {full_report['missing_documentation']}")
```

---

## Configuration Utilities

### `class ConfigManager`

Manages Empirica configuration settings.

#### `__init__(self, config_path: Optional[str] = None)`

Initialize the configuration manager.

**Parameters:**
- `config_path: Optional[str]` - Path to config file, defaults to standard location

**Example:**
```python
from empirica.utils.config_manager import ConfigManager

config_mgr = ConfigManager()
```

### `get_config_value(self, key: str, default: Any = None) -> Any`

Get a configuration value.

**Parameters:**
- `key: str` - Configuration key (dot notation: 'database.path' or 'ai.settings.temperature')
- `default: Any` - Default value if key not found

**Returns:** `Any` - Configuration value

**Example:**
```python
db_path = config_mgr.get_config_value('database.path', './sessions.db')
temperature = config_mgr.get_config_value('ai.settings.temperature', 0.7)
```

### `set_config_value(self, key: str, value: Any) -> bool`

Set a configuration value.

**Parameters:**
- `key: str` - Configuration key
- `value: Any` - Value to set

**Returns:** `bool` - True if successful

**Example:**
```python
success = config_mgr.set_config_value('ai.settings.temperature', 0.5)
```

### `validate_config(self) -> Dict[str, List[str]]`

Validate configuration against schema.

**Returns:** `Dict[str, List[str]]` - Validation results with errors and warnings

**Example:**
```python
validation = config_mgr.validate_config()
if validation['errors']:
    print(f"Configuration errors: {validation['errors']}")
if validation['warnings']:
    print(f"Configuration warnings: {validation['warnings']}")
```

---

## Migration Utilities

### `class MigrationRunner`

Manages database schema migrations.

#### `__init__(self, db_path: str)`

Initialize the migration runner.

**Parameters:**
- `db_path: str` - Path to database file

**Example:**
```python
from empirica.data.migrations.migration_runner import MigrationRunner

migration_runner = MigrationRunner("./sessions.db")
```

### `run_migrations(self, target_version: Optional[str] = None) -> Dict[str, Any]`

Run pending migrations up to target version.

**Parameters:**
- `target_version: Optional[str]` - Target version, runs all if None

**Returns:** `Dict[str, Any]` - Migration results

**Example:**
```python
results = migration_runner.run_migrations(target_version="1.0.5")
print(f"Migrated from {results['from_version']} to {results['to_version']}")
print(f"Applied {len(results['applied_migrations'])} migrations")
```

### `get_current_schema_version(self) -> str`

Get current schema version.

**Returns:** `str` - Current version string

**Example:**
```python
current_version = migration_runner.get_current_schema_version()
print(f"Current schema version: {current_version}")
```

### `check_pending_migrations(self) -> List[Dict[str, str]]`

Check for pending migrations.

**Returns:** `List[Dict[str, str]]` - List of pending migration dictionaries

**Example:**
```python
pending = migration_runner.check_pending_migrations()
if pending:
    print(f"Pending migrations: {len(pending)}")
    for migration in pending:
        print(f"  - {migration['version']}: {migration['description']}")
```

---

## Session Utilities

### `class SessionUtils`

Utility functions for session management.

#### `__init__(self, db_path: Optional[str] = None)`

Initialize session utilities.

**Parameters:**
- `db_path: Optional[str]` - Database path, defaults to standard location

**Example:**
```python
from empirica.utils.session_utils import SessionUtils

session_utils = SessionUtils()
```

### `get_session_summary(self, session_id: str, detail_level: str = 'summary') -> Optional[Dict]`

Get comprehensive session summary.

**Parameters:**
- `session_id: str` - Session identifier
- `detail_level: str` - Detail level ('summary', 'detailed', 'full'), default 'summary'

**Returns:** `Optional[Dict]` - Session summary or None if not found

**Example:**
```python
summary = session_utils.get_session_summary(
    session_id="sess-123",
    detail_level="detailed"
)

if summary:
    print(f"AI: {summary['ai_id']}")
    print(f"Duration: {summary['duration_seconds']}s")
    print(f"Epistemic delta: {summary['epistemic_delta']}")
```

### `find_similar_sessions(self, session_id: str, similarity_threshold: float = 0.7) -> List[Dict]`

Find sessions similar to the given session based on goals and context.

**Parameters:**
- `session_id: str` - Reference session
- `similarity_threshold: float` - Minimum similarity threshold, default 0.7

**Returns:** `List[Dict]` - List of similar session dictionaries

**Example:**
```python
similar = session_utils.find_similar_sessions(
    session_id="sess-123",
    similarity_threshold=0.8
)

for sess in similar:
    print(f"Similar session: {sess['session_id']} - {sess['task_similarity']:.2f}")
```

### `export_session_artifacts(self, session_id: str, export_path: str, include_vectors: bool = True, include_logs: bool = True) -> bool`

Export session artifacts to a directory.

**Parameters:**
- `session_id: str` - Session identifier
- `export_path: str` - Path to export directory
- `include_vectors: bool` - Include epistemic vectors, default True
- `include_logs: bool` - Include logs, default True

**Returns:** `bool` - True if export successful

**Example:**
```python
success = session_utils.export_session_artifacts(
    session_id="sess-123",
    export_path="./exports/session-123",
    include_vectors=True,
    include_logs=True
)
```

---

## Git Integration Utilities

### `class GitIntegration`

Provides enhanced Git integration for Empirica's epistemic tracking.

#### `__init__(self, repo_path: Optional[str] = None)`

Initialize Git integration.

**Parameters:**
- `repo_path: Optional[str]` - Git repository path, defaults to current directory

**Example:**
```python
from empirica.utils.git_integration import GitIntegration

git_integrator = GitIntegration()
```

### `create_epistemic_checkpoint(self, session_id: str, phase: str, vectors: Dict[str, float], message: Optional[str] = None) -> Optional[str]`

Create an epistemic checkpoint as a Git commit with vector data.

**Parameters:**
- `session_id: str` - Session identifier
- `phase: str` - Current phase ('PREFLIGHT', 'CHECK', 'POSTFLIGHT')
- `vectors: Dict[str, float]` - Epistemic vectors
- `message: Optional[str]` - Optional commit message

**Returns:** `Optional[str]` - Commit hash or None if failed

**Example:**
```python
commit_hash = git_integrator.create_epistemic_checkpoint(
    session_id="sess-123",
    phase="POSTFLIGHT",
    vectors={
        "know": 0.85, "do": 0.78, "context": 0.92, "uncertainty": 0.15
    },
    message="POSTFLIGHT: Completed auth module implementation"
)
```

### `get_epistemic_history(self, limit: int = 50) -> List[Dict[str, Any]]`

Get epistemic history from Git commits.

**Parameters:**
- `limit: int` - Maximum number of commits to return, default 50

**Returns:** `List[Dict[str, Any]]` - List of epistemic checkpoints from commits

**Example:**
```python
history = git_integrator.get_epistemic_history(limit=20)
for checkpoint in history:
    print(f"Commit {checkpoint['commit_hash'][:8]}: {checkpoint['phase']} - {checkpoint['vectors']['know']:.2f} know")
```

### `restore_from_checkpoint(self, commit_hash: str) -> bool`

Restore session state from a Git checkpoint.

**Parameters:**
- `commit_hash: str` - Git commit hash

**Returns:** `bool` - True if restoration successful

**Example:**
```python
success = git_integrator.restore_from_checkpoint(commit_hash="a1b2c3d4")
if success:
    print("Session state restored from checkpoint")
```

---

## Performance Utilities

### `class PerformanceMonitor`

Monitors and tracks performance metrics.

#### `__init__(self, session_id: str)`

Initialize performance monitoring for a session.

**Parameters:**
- `session_id: str` - Session identifier

**Example:**
```python
from empirica.utils.performance_monitor import PerformanceMonitor

perf_monitor = PerformanceMonitor(session_id="sess-123")
```

### `start_measurement(self, operation_name: str) -> str`

Start timing an operation.

**Parameters:**
- `operation_name: str` - Name of the operation

**Returns:** `str` - Measurement ID

**Example:**
```python
measurement_id = perf_monitor.start_measurement("database_query")
# ... perform operation ...
result = perf_monitor.stop_measurement(measurement_id)
print(f"Operation took {result['duration_ms']}ms")
```

### `stop_measurement(self, measurement_id: str) -> Dict[str, Any]`

Stop timing an operation and return results.

**Parameters:**
- `measurement_id: str` - ID from start_measurement

**Returns:** `Dict[str, Any]` - Performance results

**Example:**
```python
results = perf_monitor.stop_measurement(measurement_id="measure-123")
print(f"Duration: {results['duration_ms']}ms")
print(f"Memory used: {results['memory_delta_bytes']} bytes")
```

### `get_performance_report(self) -> Dict[str, Any]`

Get overall performance report for the session.

**Returns:** `Dict[str, Any]` - Performance metrics

**Example:**
```python
report = perf_monitor.get_performance_report()
print(f"Average operation time: {report['avg_operation_time_ms']}ms")
print(f"Peak memory usage: {report['peak_memory_mb']}MB")
```

---

## Best Practices

1. **Use branch mapping consistently** - Always map branches to goals to maintain traceability.

2. **Validate configurations** - Regularly validate configuration against schema to prevent runtime errors.

3. **Run migrations safely** - Always backup before running schema migrations.

4. **Monitor performance** - Use performance utilities to identify bottlenecks.

5. **Export session artifacts** - Regularly export important session data for backup and analysis.

6. **Maintain Git integration** - Use epistemic checkpoints to maintain continuity across Git commits.

7. **Check integrity regularly** - Run doc-code integrity checks to maintain consistency.

8. **Handle errors gracefully** - All utility methods return appropriate success/failure indicators.

---

## Error Handling

Methods typically raise:
- `ValueError` for invalid parameters
- `FileNotFoundError` when files don't exist
- `PermissionError` for access issues
- `RuntimeError` for operational failures
- `sqlite3.Error` for database issues
- `git.exc.GitCommandError` for Git operations

---

**Module Locations:** 
- `empirica/utils/branch_mapping.py`
- `empirica/utils/doc_code_integrity.py` 
- `empirica/utils/config_manager.py`
- `empirica/data/migrations/migration_runner.py`
- `empirica/utils/session_utils.py`
- `empirica/utils/git_integration.py`
- `empirica/utils/performance_monitor.py`

**API Stability:** Stable
**Last Updated:** 2025-12-27