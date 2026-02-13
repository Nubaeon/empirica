# Instance Isolation Architecture

Core concepts and file taxonomy for multi-instance isolation.

## File Taxonomy

### 1. Active Work Files (Claude Code)

**Location:** `~/.empirica/active_work_{claude_session_id}.json`
**Key:** Claude Code conversation UUID (from hook stdin)
**Written by:** Hooks (session-init, post-compact)

```json
{
  "project_path": "/home/user/my-project",
  "folder_name": "my-project",
  "claude_session_id": "fad66571-1bde-4ee1-aa0d-e9d3dfd8e833",
  "empirica_session_id": "2bc1da78-2a28-4745-b75b-f021d563d819",
  "source": "post-compact",
  "timestamp": "2026-02-13T01:00:00"
}
```

**Purpose:** Links Claude conversation → project. Primary isolation for Claude Code users.

### 2. Instance Projects (tmux)

**Location:** `~/.empirica/instance_projects/tmux_N.json`
**Key:** `TMUX_PANE` environment variable (e.g., `%4` → `tmux_4`)
**Written by:** Hooks (session-init, post-compact), CLI (project-switch preserves)

```json
{
  "project_path": "/home/user/my-project",
  "claude_session_id": "fad66571-1bde-4ee1-aa0d-e9d3dfd8e833",
  "empirica_session_id": "2bc1da78-2a28-4745-b75b-f021d563d819",
  "timestamp": "2026-02-13T01:00:00"
}
```

**Purpose:** Links tmux pane → project. Works in hook context where TTY unavailable.

### 3. TTY Sessions (CLI/MCP)

**Location:** `~/.empirica/tty_sessions/pts-N.json`
**Key:** TTY device name (from `tty` command)
**Written by:** CLI commands (session-create, project-switch)

```json
{
  "claude_session_id": null,
  "empirica_session_id": "2bc1da78-2a28-4745-b75b-f021d563d819",
  "project_path": "/home/user/my-project",
  "tty_key": "pts-6",
  "timestamp": "2026-02-06T16:18:42",
  "pid": 1900034
}
```

**Purpose:** Links terminal → project. Primary isolation for non-Claude-Code users (MCP, direct CLI).

### 4. Transaction Files (Per-Project)

**Location:** `{project}/.empirica/active_transaction_{instance_id}.json`
**Key:** `instance_id` (e.g., `tmux_4`, `term_pts_6`, `default`)
**Written by:** PREFLIGHT command

```json
{
  "transaction_id": "e04ad48e-3c2b-48ef-96be-5ebcf86746c6",
  "session_id": "2bc1da78-2a28-4745-b75b-f021d563d819",
  "preflight_timestamp": 1770391133.159,
  "status": "open",
  "project_path": "/home/user/my-project"
}
```

**Purpose:** Tracks open epistemic transaction. Survives memory compaction.

---

## Resolution Priority Chains

### Hooks (Sentinel, pre-compact, post-compact)

```
Priority 0: active_work_{claude_session_id}.json
    ↓
Priority 1: instance_projects/tmux_N.json (via TMUX_PANE)
    ↓
❌ NO CWD FALLBACK - fail explicitly
```

### CLI Commands

```
Priority 0: active_work_{claude_session_id}.json (if session_id known)
    ↓
Priority 1: tty_sessions/pts-N.json (via tty command)
    ↓
Priority 2: instance_projects/tmux_N.json (via TMUX_PANE)
    ↓
Priority 3: CWD-based detection (last resort)
```

### Statusline

```
Priority 0: active_work (via stdin session_id from Claude Code)
    ↓
Priority 1: instance_projects (via TMUX_PANE)
    ↓
Priority 2: tty_sessions (via tty command)
    ↓
❌ NO CWD FALLBACK
```

---

## Ownership Model

| Component | Writes | Reads |
|-----------|--------|-------|
| **Hooks** (session-init, post-compact) | `active_work`, `instance_projects` | All |
| **CLI** (session-create, project-switch) | `tty_sessions`, preserves `instance_projects` | All |
| **PREFLIGHT** | `active_transaction` | All |
| **Statusline** | Nothing | All |
| **Sentinel** | Nothing | All |

**Key insight:** Hooks have full context (`claude_session_id` + `TMUX_PANE`). CLI commands
only have `TTY` + maybe `TMUX_PANE`. This asymmetry is why we need multiple file types.

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Claude Code Session                              │
│                                                                      │
│  SessionStart Hook                    Bash Tool (CLI)                │
│  ─────────────────                    ───────────────                │
│  Has: claude_session_id               Has: TMUX_PANE, TTY            │
│       TMUX_PANE (if tmux)             Missing: claude_session_id     │
│                                                                      │
│  Writes:                              Writes:                        │
│  • active_work_{id}.json              • tty_sessions/pts-N.json      │
│  • instance_projects/tmux_N.json      • Preserves instance_projects  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Project Database                                 │
│  {project}/.empirica/sessions/sessions.db                           │
│                                                                      │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────────────────┐ │
│  │  sessions  │  │  reflexes  │  │ active_transaction_tmux_N.json │ │
│  └────────────┘  └────────────┘  └────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Functions

| Function | Location | Purpose |
|----------|----------|---------|
| `get_active_project_path()` | session_resolver.py | **CANONICAL** - project resolution |
| `get_instance_id()` | session_resolver.py | Get `tmux_N` from TMUX_PANE |
| `get_tty_key()` | session_resolver.py | Get TTY device name |
| `read_active_transaction()` | session_resolver.py | Read transaction file |
| `write_tty_session()` | session_resolver.py | Write TTY session file |

---

## Related Documentation

- [TRANSACTION_CONTINUITY_SPEC.md](../TRANSACTION_CONTINUITY_SPEC.md) - How transactions survive compaction
- [CLAUDE_CODE.md](./CLAUDE_CODE.md) - Claude Code specific patterns
- [MCP_AND_CLI.md](./MCP_AND_CLI.md) - MCP/CLI integration patterns
