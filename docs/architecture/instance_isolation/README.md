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

1. **Hooks write, everything else reads.** Hooks have full context (claude_session_id + TMUX_PANE). CLI, Sentinel, statusline are readers. Exception: `project-switch` writes to `instance_projects` as a signal.
2. **instance_projects is the most current source** — writable by both hooks AND project-switch. `active_work` is fallback for non-TMUX only.
3. **Never self-heal between files.** If they disagree after project-switch, that's expected. instance_projects has the newer data.
4. **CWD is unreliable** — Claude Code resets it unpredictably.
5. **Fail explicitly** — return None rather than silently using wrong project.
6. **TTY is the fallback** for non-Claude-Code integrations.

---

## Automated Workflows & Containers

For truly isolated automated workflows (CI/CD, parallel batch processing, scheduled jobs),
**containers are essential** — not just for isolation but for security hardening.

Empirica's file-based isolation works for interactive use cases (tmux panes, terminals).
For automated scenarios where you need:

- **Process isolation** - No shared filesystem state
- **Security hardening** - Untrusted code execution
- **Reproducible environments** - Consistent starting conditions
- **Parallel scaling** - Multiple identical workers

Use containerization (Docker, Podman, etc.):

```bash
# Example: Run Empirica in isolated container
docker run -v /path/to/project:/workspace \
  -e EMPIRICA_SESSION_DB=/workspace/.empirica/sessions/sessions.db \
  empirica-worker empirica preflight-submit ...
```

This is out of scope for Empirica itself — use your infrastructure tooling.
The key point: Empirica's isolation is for **interactive multi-instance**, not
**security boundaries**.
