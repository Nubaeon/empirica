# Instance Isolation Documentation

Multiple Claude/AI instances can run simultaneously in different terminals or tmux panes.
This folder documents how Empirica keeps them isolated.

## Which doc do I need?

| You are... | Read this |
|------------|-----------|
| Using Claude Code (Anthropic's CLI) | [CLAUDE_CODE.md](./CLAUDE_CODE.md) |
| Building an MCP server or custom CLI | [MCP_AND_CLI.md](./MCP_AND_CLI.md) |
| Debugging isolation issues | [KNOWN_ISSUES.md](./KNOWN_ISSUES.md) |
| Understanding the architecture | [ARCHITECTURE.md](./ARCHITECTURE.md) |

## Quick Summary

**The problem:** Multiple AI instances share `ai_id=claude-code`, making them indistinguishable
at the database level. CWD gets reset unpredictably. Which project am I working on?

**The solution:** File-based isolation using terminal/pane identifiers:

| Integration | Primary Key | File |
|-------------|-------------|------|
| Claude Code (hooks) | `claude_session_id` | `~/.empirica/active_work_{id}.json` |
| Claude Code (tmux) | `TMUX_PANE` | `~/.empirica/instance_projects/tmux_N.json` |
| MCP / Other CLI | TTY device | `~/.empirica/tty_sessions/pts-N.json` |
| All | Transaction | `{project}/.empirica/active_transaction_{instance}.json` |

## Key Principles

1. **File-based isolation** trumps database queries
2. **CWD is unreliable** - Claude Code resets it unpredictably
3. **Fail explicitly** - Better to error than silently use wrong project
4. **Hooks own the linkage** for Claude Code users
5. **TTY is the fallback** for non-Claude-Code integrations
