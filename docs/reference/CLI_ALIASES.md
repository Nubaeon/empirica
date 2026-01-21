# CLI Command Aliases

**Generated:** 2026-01-19
**Purpose:** Quick shortcuts for common Empirica commands

---

## Why Aliases?

Aliases reduce typing for frequently used commands. They're especially useful for AI agents who call these commands programmatically.

---

## Alias Reference

### CASCADE Workflow
| Command | Aliases | Description |
|---------|---------|-------------|
| `preflight-submit` | `pre`, `preflight` | Submit PREFLIGHT assessment |
| `postflight-submit` | `post`, `postflight` | Submit POSTFLIGHT assessment |

### Session Management
| Command | Aliases | Description |
|---------|---------|-------------|
| `session-create` | `sc` | Create new session |
| `sessions-list` | `sl`, `session-list` | List all sessions |
| `sessions-show` | `session-show` | Show session details |
| `sessions-export` | `session-export` | Export session to JSON |
| `sessions-resume` | `sr`, `session-resume` | Resume previous session |

### Goals
| Command | Aliases | Description |
|---------|---------|-------------|
| `goals-create` | `gc`, `goal-create` | Create new goal |
| `goals-list` | `gl`, `goal-list` | List goals |
| `goals-complete` | `goal-complete` | Mark goal complete |
| `goals-progress` | `goal-progress` | Check goal progress |
| `goals-add-subtask` | `goal-add-subtask` | Add subtask to goal |
| `goals-complete-subtask` | `goal-complete-subtask` | Complete a subtask |

### Logging (Breadcrumbs)
| Command | Aliases | Description |
|---------|---------|-------------|
| `finding-log` | `fl` | Log a finding |
| `unknown-log` | `ul` | Log an unknown |
| `deadend-log` | `de` | Log a dead-end |

### Project
| Command | Aliases | Description |
|---------|---------|-------------|
| `project-bootstrap` | `pb`, `bootstrap` | Bootstrap project context |

---

## Usage Examples

```bash
# Instead of:
empirica preflight-submit --session-id abc123 ...

# Use:
empirica pre --session-id abc123 ...

# Quick goal creation:
empirica gc --session-id abc123 --objective "Fix bug"

# Quick finding log:
empirica fl --session-id abc123 --finding "Found root cause"
```

---

## Adding New Aliases

Aliases are defined in two places:
1. **Parser registration:** `empirica/cli/parsers/*.py` - `add_parser(..., aliases=[...])`
2. **Handler mapping:** `empirica/cli/cli_core.py` - `command_handlers` dict

Both must be updated for an alias to work.

---

## See Also

- [CLI Quickstart](../human/end-users/04_QUICKSTART_CLI.md)
- [Full Command Reference](CLI_COMMANDS_COMPLETE.md)
