# Instance Isolation for Claude Code Users

This doc covers instance isolation when using Empirica with Claude Code (Anthropic's official CLI).

## How It Works

Claude Code provides hooks that fire on specific events. These hooks receive `session_id`
(Claude's conversation UUID) via stdin, enabling instance isolation.

### Automatic Session Management

**Sessions are created automatically.** Do NOT run `session-create` manually.

| Event | Hook | What Happens |
|-------|------|--------------|
| New conversation | `session-init.py` | Creates Empirica session, writes `active_work` + `instance_projects` |
| Memory compaction | `post-compact.py` | Continues transaction OR creates new session, writes isolation files |
| Tool use | `sentinel-gate.py` | Reads isolation files to find correct project |

### File Ownership

Hooks write these files (you don't need to):

```
~/.empirica/active_work_{claude_session_id}.json    # Links conversation → project
~/.empirica/instance_projects/tmux_N.json           # Links tmux pane → project (if tmux)
```

### The claude_session_id Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Claude Code starts conversation                              │
│                                                              │
│ SessionStart hook fires                                      │
│ ─────────────────────                                        │
│ stdin: {"session_id": "fad66571-...", ...}                  │
│                                                              │
│ Hook:                                                        │
│ 1. Creates Empirica session                                  │
│ 2. Writes active_work_{session_id}.json                     │
│ 3. Writes instance_projects/tmux_N.json (if tmux)           │
│                                                              │
│ All subsequent hooks/commands can resolve project            │
└─────────────────────────────────────────────────────────────┘
```

### Hook Input Structure

Claude Code provides structured JSON to hooks via stdin:

```json
{
  "session_id": "fad66571-1bde-4ee1-aa0d-e9d3dfd8e833",
  "transcript_path": "/home/user/.claude/projects/my-project/fad66571.jsonl",
  "cwd": "/home/user/my-project",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse"
}
```

| Field | Purpose | Notes |
|-------|---------|-------|
| `session_id` | Claude conversation UUID | Maps to `active_work_{id}.json` |
| `transcript_path` | Full transcript file path | Used by pre-compact for state capture |
| `cwd` | Working directory | **UNRELIABLE** - do not use for project resolution |
| `permission_mode` | Claude permission level | Used by Sentinel for gate decisions |
| `hook_event_name` | Hook event type | Conditional hook logic |

**Critical:** The `cwd` field is unreliable because Claude Code can reset it (e.g., after
compaction). Hooks must use `session_id` → `active_work` file → `project_path` resolution.

---

## Multi-Pane tmux Setup

If you run multiple Claude Code instances in tmux panes:

```
┌─────────────────┬─────────────────┐
│ Pane %4         │ Pane %5         │
│ empirica/       │ my-project/     │
│                 │                 │
│ tmux_4.json     │ tmux_5.json     │
│ points to       │ points to       │
│ empirica/       │ my-project/     │
└─────────────────┴─────────────────┘
```

Each pane gets its own:
- `instance_projects/tmux_N.json`
- `active_transaction_tmux_N.json` (in project dir)

The `TMUX_PANE` environment variable (`%4`, `%5`) is available in hooks AND Bash tool calls.

---

## Transaction Continuity Across Compaction

When Claude's context window fills up, memory compaction occurs:

```
Before Compaction              After Compaction
────────────────────           ────────────────────
pre-compact.py fires           post-compact.py fires
  ↓                              ↓
Captures:                      Reads snapshot:
• active_transaction           • Finds open transaction
• epistemic vectors            • Writes active_work (new session_id)
• breadcrumbs                  • Writes instance_projects
  ↓                              ↓
pre_summary_{ts}.json          Transaction continues!
```

**Key:** The transaction survives compaction via file-based state, not database.

---

## Common Issues

### "Active session in project" Error

You tried to run `session-create` but a session already exists.

**Fix:** Don't run `session-create`. Sessions are automatic.

### Statusline Shows Wrong Phase

The statusline is querying the wrong session.

**Cause:** `instance_projects` has wrong `empirica_session_id` after compaction.

**Fix:** This was fixed in commit `f8d9a82f`. Update your plugin.

### Can't Find Transaction After tmux Restart

tmux died and new panes have different IDs (e.g., `%7` instead of `%4`).

**Fix:** Adopt the orphaned transaction:
```bash
empirica transaction-adopt --from tmux_4
```

---

## Debugging

### Check Current State

```bash
# What does Claude Code think the session is?
cat ~/.empirica/active_work_*.json | jq .

# What does tmux pane think?
cat ~/.empirica/instance_projects/tmux_$(echo $TMUX_PANE | tr -d '%').json

# What transaction is open?
cat .empirica/active_transaction_tmux_*.json
```

### Check Hook Logs

```bash
# Sentinel logs
cat ~/.claude/plugins/local/empirica-integration/hooks/.empirica_reflex_logs/*.log

# Post-compact output is in Claude's response
```

---

## Related

- [ARCHITECTURE.md](./ARCHITECTURE.md) - Full file taxonomy
- [KNOWN_ISSUES.md](./KNOWN_ISSUES.md) - Bug history and fixes
