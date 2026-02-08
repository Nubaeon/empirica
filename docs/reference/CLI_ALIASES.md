# CLI Command Aliases

**Generated:** 2026-02-08
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

### Messaging
| Command | Aliases | Description |
|---------|---------|-------------|
| `message-send` | `msg-send` | Send message to AI |
| `message-inbox` | `msg-inbox` | Check inbox |
| `message-read` | `msg-read` | Read specific message |
| `message-reply` | `msg-reply` | Reply to message |

### Project
| Command | Aliases | Description |
|---------|---------|-------------|
| `project-bootstrap` | `pb`, `bootstrap` | Bootstrap project context |
| `project-list` | `pl` | List all projects |
| `project-switch` | `ps` | Switch active project |
| `project-search` | — | Semantic search in project context |
| `project-embed` | — | Embed project artifacts to Qdrant |

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
