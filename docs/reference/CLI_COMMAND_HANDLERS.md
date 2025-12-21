# CLI Command Handlers Reference

This document provides comprehensive documentation for Empirica's CLI command handlers.

## Goals Commands

### `handle_goals_list_command`

**Module**: `empirica.cli.command_handlers.goal_commands`

**Purpose**: Handle the `goals-list` CLI command to list goals with optional filtering

**CLI Command**: `empirica goals-list [--session-id SESSION_ID] [--completed] [--scope-*-min/max SCOPE_VALUES]`

**Parameters**:
- `args` (`argparse.Namespace`): Parsed command line arguments

**Arguments Processed**:
- `session_id` (`str`, optional): Filter goals by session ID
- `completed` (`bool`, optional): Filter by completion status
- `scope_breadth_min/max` (`float`, optional): Filter by scope breadth range (0.0-1.0)
- `scope_duration_min/max` (`float`, optional): Filter by scope duration range (0.0-1.0)
- `scope_coordination_min/max` (`float`, optional): Filter by scope coordination range (0.0-1.0)

**Functionality**:
1. Parses command line arguments
2. Creates GoalRepository and TaskRepository instances
3. Retrieves goals based on filters
4. Displays goals in formatted output

**Example Usage**:
```bash
# List all goals for current session
empirica goals-list --session-id 81a9dfd3

# List incomplete goals with medium scope
empirica goals-list --session-id 81a9dfd3 --scope-breadth-min 0.4 --scope-breadth-max 0.7

# List all completed goals
empirica goals-list --completed
```

**Related**:
- `GoalRepository.get_session_goals()` - Database method for retrieving goals
- `TaskRepository` - Task management for subtasks
- `goals-create` - Create new goals
- `goals-progress` - Check goal progress

**Error Handling**:
- Validates session ID format
- Handles database connection errors
- Provides user-friendly error messages

---

### `handle_goals_create_command`

**Module**: `empirica.cli.command_handlers.goal_commands`

**Purpose**: Handle the `goals-create` CLI command to create new goals

**CLI Command**: `empirica goals-create [--session-id SESSION_ID] [--objective OBJECTIVE] [config_file]`

**Parameters**:
- `args` (`argparse.Namespace`): Parsed command line arguments

**Arguments Processed**:
- `session_id` (`str`, optional): Session ID for the goal
- `objective` (`str`, optional): Goal objective text
- `config` (`str`, optional): JSON config file path or "-" for stdin

**Functionality**:
1. Parses goal configuration (JSON file or CLI args)
2. Validates goal data using validation module
3. Creates goal in database via GoalRepository
4. Returns goal creation result

**Example Usage**:
```bash
# Create goal from JSON config
empirica goals-create goal_config.json

# Create goal with CLI arguments
empirica goals-create --session-id 81a9dfd3 --objective "Complete documentation"

# Create goal from stdin
cat goal_config.json | empirica goals-create -
```

**Related**:
- `GoalRepository.save_goal()` - Save goal to database
- `validate_goal_input()` - Goal validation
- `goals-list` - List created goals
- `goals-add-subtask` - Add subtasks to goals

**Configuration Format**:
```json
{
    "session_id": "session-uuid",
    "objective": "Goal description",
    "scope": {"breadth": 0.8, "duration": 0.7, "coordination": 0.3},
    "estimated_complexity": 0.6,
    "success_criteria": [
        {"description": "Complete task", "threshold": 1.0}
    ]
}
```

---

### `handle_goals_progress_command`

**Module**: `empirica.cli.command_handlers.goal_commands`

**Purpose**: Handle the `goals-progress` CLI command to check goal completion progress

**CLI Command**: `empirica goals-progress --goal-id GOAL_ID`

**Parameters**:
- `args` (`argparse.Namespace`): Parsed command line arguments

**Arguments Processed**:
- `goal_id` (`str`, required): Goal UUID to check progress

**Functionality**:
1. Validates goal ID format
2. Retrieves goal from database
3. Calculates completion percentage
4. Displays progress information

**Example Usage**:
```bash
# Check progress of specific goal
empirica goals-progress --goal-id ac48c59b-76de-47db-943c-3f557d270435

# Expected output:
# ✅ Goal progress retrieved
# Goal: ac48c59b...
# Completion: 50.0%
# Progress: 2/4 subtasks
```

**Related**:
- `GoalRepository.get_goal()` - Retrieve goal data
- `goals-list` - List all goals
- `goals-complete-subtask` - Mark subtasks as complete

---

## Configuration Commands

### `handle_config_set_command`

**Module**: `empirica.cli.command_handlers.config_commands`

**Purpose**: Handle the `config-set` CLI command to set configuration values

**CLI Command**: `empirica config-set --key KEY --value VALUE [--scope SCOPE]`

**Parameters**:
- `args` (`argparse.Namespace`): Parsed command line arguments

**Arguments Processed**:
- `key` (`str`, required): Configuration key to set
- `value` (`str`, required): Configuration value
- `scope` (`str`, optional): Configuration scope (global, project, session)

**Functionality**:
1. Parses configuration key and value
2. Validates configuration scope
3. Updates configuration in appropriate store
4. Persists configuration changes

**Example Usage**:
```bash
# Set global configuration
empirica config-set --key default_ai --value claude-sonnet --scope global

# Set project-specific configuration
empirica config-set --key embeddings_provider --value local --scope project

# Set session configuration
empirica config-set --key verbose_output --value true --scope session
```

**Related**:
- `config-show` - Display current configuration
- `config-get` - Get specific configuration value
- `ProjectConfig` - Project configuration management

---

## Utility Commands

### `handle_sessions_list_command`

**Module**: `empirica.cli.command_handlers.utility_commands`

**Purpose**: Handle the `sessions-list` CLI command to list Empirica sessions

**CLI Command**: `empirica sessions-list [--limit LIMIT] [--ai-id AI_ID]`

**Parameters**:
- `args` (`argparse.Namespace`): Parsed command line arguments

**Arguments Processed**:
- `limit` (`int`, optional): Maximum number of sessions to display
- `ai_id` (`str`, optional): Filter by AI identifier

**Functionality**:
1. Queries session database
2. Applies filters (AI ID, limit)
3. Formats session information
4. Displays session list with metadata

**Example Usage**:
```bash
# List all sessions
empirica sessions-list

# List sessions for specific AI
empirica sessions-list --ai-id claude-copilot

# List limited number of sessions
empirica sessions-list --limit 10
```

**Output Format**:
```
🎯 📋 Empirica Sessions
======================

📊 Found N sessions:

⏳ session_id_short
   🤖 AI: ai-identifier
   📅 Started: timestamp
   🏁 Ended: status
   🔄 Cascades: count
```

**Related**:
- `sessions-show` - Detailed session information
- `session-create` - Create new session
- `SessionDatabase.get_all_sessions()` - Database method

---

## Error Handling Pattern

All CLI command handlers follow a consistent error handling pattern:

```python
def handle_*_command(args):
    """Command description"""
    try:
        # Command logic
        from module import Class
        
        # Parse arguments
        param = getattr(args, 'param_name', default_value)
        
        # Business logic
        repo = Class()
        result = repo.method(param)
        
        # Output results
        print(f"✅ Success: {result}")
        
    except Exception as e:
        handle_cli_error(e, "Command name", getattr(args, 'verbose', False))
```

**Error Handling Features**:
- Consistent error messages
- Verbose mode support
- Graceful degradation
- User-friendly output

---

## Additional CLI Command Handlers

### `handle_sessions_export_command`

**Module**: `empirica.cli.command_handlers.utility_commands`

**Purpose**: Handle the `sessions-export` CLI command to export session data

**CLI Command**: `empirica sessions-export --session-id SESSION_ID --format FORMAT --output FILE`

**Parameters**:
- `args` (`argparse.Namespace`): Parsed command line arguments

**Arguments Processed**:
- `session_id` (`str`, required): Session ID to export
- `format` (`str`, optional): Export format (json, yaml, markdown)
- `output` (`str`, optional): Output file path

**Functionality**:
1. Retrieves session data from database
2. Formats data according to specified format
3. Exports to file or stdout
4. Includes goals, findings, and metadata

**Example Usage**:
```bash
# Export session to JSON file
empirica sessions-export --session-id 81a9dfd3 --format json --output session_data.json

# Export to markdown for documentation
empirica sessions-export --session-id 81a9dfd3 --format markdown > session_report.md

# Export to stdout
empirica sessions-export --session-id 81a9dfd3 --format yaml
```

**Related**:
- `sessions-list` - List available sessions
- `sessions-show` - Show session details
- `SessionDatabase.export_session()` - Database export method

---

### `handle_goals_complete_command`

**Module**: `empirica.cli.command_handlers.goal_complete_command`

**Purpose**: Handle the `goals-complete` CLI command to mark goals as complete

**CLI Command**: `empirica goals-complete --goal-id GOAL_ID [--reason REASON] [--run-postflight]`

**Parameters**:
- `args` (`argparse.Namespace`): Parsed command line arguments

**Arguments Processed**:
- `goal_id` (`str`, required): Goal UUID to complete
- `reason` (`str`, optional): Completion reason
- `run_postflight` (`bool`, optional): Run POSTFLIGHT assessment

**Functionality**:
1. Validates goal exists and is not already complete
2. Updates goal completion status in database
3. Optionally runs POSTFLIGHT assessment
4. Creates completion record with timestamp

**Example Usage**:
```bash
# Complete a goal
empirica goals-complete --goal-id ac48c59b-76de-47db-943c-3f557d270435 --reason "Documentation completed"

# Complete with POSTFLIGHT
empirica goals-complete --goal-id goal-id-123 --run-postflight --reason "All subtasks finished"
```

**Related**:
- `goals-list` - List goals
- `goals-progress` - Check goal progress
- `postflight` - Run POSTFLIGHT assessment

**Note**: This command was fixed to use `get_goal()` instead of `get_by_id()`

---

### `handle_config_show_command`

**Module**: `empirica.cli.command_handlers.config_commands`

**Purpose**: Handle the `config-show` CLI command to display current configuration

**CLI Command**: `empirica config-show [--scope SCOPE] [--key KEY]`

**Parameters**:
- `args` (`argparse.Namespace`): Parsed command line arguments

**Arguments Processed**:
- `scope` (`str`, optional): Configuration scope (global, project, session)
- `key` (`str`, optional): Specific configuration key to show

**Functionality**:
1. Retrieves configuration from appropriate scope
2. Filters by key if specified
3. Formats configuration for display
4. Shows configuration source and precedence

**Example Usage**:
```bash
# Show all configuration
empirica config-show

# Show project-specific configuration
empirica config-show --scope project

# Show specific configuration value
empirica config-show --key default_ai
```

**Related**:
- `config-set` - Set configuration values
- `config-get` - Get specific configuration value
- `ProjectConfig` - Configuration management

---

### `handle_unknown_log_command`

**Module**: `empirica.cli.command_handlers.project_commands`

**Purpose**: Handle the `unknown-log` CLI command to log unresolved questions

**CLI Command**: `empirica unknown-log --session-id SESSION_ID --unknown UNKNOWN_TEXT [--context CONTEXT]`

**Parameters**:
- `args` (`argparse.Namespace`): Parsed command line arguments

**Arguments Processed**:
- `session_id` (`str`, required): Session ID
- `unknown` (`str`, required): Unknown/question text
- `context` (`str`, optional): Additional context

**Functionality**:
1. Validates session exists
2. Creates unknown record in database
3. Links to session for context
4. Adds timestamp and metadata

**Example Usage**:
```bash
# Log an unknown
empirica unknown-log --session-id 81a9dfd3 --unknown "How does persona reputation affect decision-making?"

# Log with context
empirica unknown-log --session-id 81a9dfd3 --unknown "What's the optimal threshold for documentation tasks?" --context "Phase 2 documentation work"
```

**Related**:
- `unknown-log` - Log unknowns
- `finding-log` - Log findings
- `deadend-log` - Log dead ends

---

### `handle_deadend_log_command`

**Module**: `empirica.cli.command_handlers.project_commands`

**Purpose**: Handle the `deadend-log` CLI command to log unsuccessful approaches

**CLI Command**: `empirica deadend-log --session-id SESSION_ID --approach APPROACH --reason REASON`

**Parameters**:
- `args` (`argparse.Namespace`): Parsed command line arguments

**Arguments Processed**:
- `session_id` (`str`, required): Session ID
- `approach` (`str`, required): Approach that didn't work
- `reason` (`str`, required): Why it failed

**Functionality**:
1. Validates session exists
2. Creates deadend record with approach and reason
3. Stores in database for future reference
4. Helps avoid repeating unsuccessful approaches

**Example Usage**:
```bash
# Log a dead end
empirica deadend-log --session-id 81a9dfd3 --approach "Automatic documentation generation" --reason "Generated docs were too generic and lacked examples"

# Log with detailed reason
empirica deadend-log --session-id 81a9dfd3 --approach "Heuristic-based assessment" --reason "Produced inconsistent results and was rejected by sentinel"
```

**Related**:
- `finding-log` - Log successful findings
- `unknown-log` - Log unresolved questions
- `mistake-log` - Log mistakes made

---

### `handle_goal_analysis_command`

**Module**: `empirica.cli.command_handlers.utility_commands`

**Purpose**: Handle the `goal-analysis` CLI command to analyze goal patterns

**CLI Command**: `empirica goal-analysis --session-id SESSION_ID [--metric METRIC]`

**Parameters**:
- `args` (`argparse.Namespace`): Parsed command line arguments

**Arguments Processed**:
- `session_id` (`str`, required): Session ID
- `metric` (`str`, optional): Specific metric to analyze (completion, complexity, duration)

**Functionality**:
1. Retrieves session goals from database
2. Analyzes goal patterns and metrics
3. Provides insights on goal management
4. Suggests improvements

**Example Usage**:
```bash
# Analyze all goal metrics
empirica goal-analysis --session-id 81a9dfd3

# Analyze completion patterns
empirica goal-analysis --session-id 81a9dfd3 --metric completion

# Analyze complexity distribution
empirica goal-analysis --session-id 81a9dfd3 --metric complexity
```

**Related**:
- `goals-list` - List session goals
- `goals-progress` - Check goal progress
- `GoalRepository.get_analysis()` - Database analysis method

---

## Development Guidelines

### Creating New Command Handlers

1. **File Location**: Place in appropriate submodule of `empirica/cli/command_handlers/`
2. **Naming**: Use `handle_<command>_command` pattern
3. **Registration**: Add to main CLI parser in `cli_core.py`
4. **Documentation**: Include comprehensive docstring
5. **Error Handling**: Use `handle_cli_error()` helper

### Best Practices

- **Argument Parsing**: Use `getattr(args, 'param', default)` for optional args
- **Imports**: Import inside try block to avoid circular dependencies
- **Output**: Use emoji and consistent formatting
- **Validation**: Validate inputs before processing
- **Logging**: Use appropriate log levels

---

## Integration with Empirica Architecture

CLI command handlers integrate with:

1. **Repositories**: Database operations via repository pattern
2. **Validation**: Input validation modules
3. **Configuration**: Configuration management system
4. **Logging**: Centralized logging system
5. **Error Handling**: Consistent error management

This modular design ensures separation of concerns and maintainability.