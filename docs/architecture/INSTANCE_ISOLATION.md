# Instance Isolation Architecture

**This documentation has been reorganized.**

See the [instance_isolation/](./instance_isolation/) folder:

| Document | Purpose |
|----------|---------|
| [README.md](./instance_isolation/README.md) | Overview and quick reference |
| [ARCHITECTURE.md](./instance_isolation/ARCHITECTURE.md) | Core concepts, file taxonomy, data flow |
| [CLAUDE_CODE.md](./instance_isolation/CLAUDE_CODE.md) | Claude Code users (hooks, automatic sessions) |
| [MCP_AND_CLI.md](./instance_isolation/MCP_AND_CLI.md) | MCP servers, custom CLI, direct terminal usage |
| [KNOWN_ISSUES.md](./instance_isolation/KNOWN_ISSUES.md) | Bug history and debugging |

## Quick Summary

Multiple AI instances can run simultaneously. Empirica isolates them using file-based state:

| Integration | Primary Key | File |
|-------------|-------------|------|
| Claude Code (hooks) | `claude_session_id` | `~/.empirica/active_work_{id}.json` |
| Claude Code (tmux) | `TMUX_PANE` | `~/.empirica/instance_projects/tmux_N.json` |
| MCP / Other CLI | TTY device | `~/.empirica/tty_sessions/pts-N.json` |
| All | Transaction | `{project}/.empirica/active_transaction_{instance}.json` |

**Key principles:**
1. File-based isolation trumps database queries
2. CWD is unreliable - Claude Code resets it
3. Fail explicitly rather than silently use wrong project
4. Hooks own the linkage for Claude Code; CLI owns it for MCP/other
