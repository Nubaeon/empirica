# Instance Isolation Architecture

**Status:** IMPLEMENTED (as of 2026-02-06)
**Authors:** David, Claude
**Related:** TRANSACTION_CONTINUITY_SPEC.md, Sentinel, CASCADE workflow

---

## 1. Problem Statement

Multiple Claude Code instances can run simultaneously:
- Different tmux panes working on different projects
- All using `ai_id=claude-code` (indistinguishable at session level)
- CWD gets reset by Claude Code unexpectedly
- Statusline, Sentinel, and CLI commands need to know "which project am I working on?"

**Key Insight:** `session_id` alone is meaningless without knowing:
1. Which **instance** (terminal/pane) created it
2. Which **project** it belongs to
3. Which **transaction** is active

---

## 2. Isolation Mechanism: TTY Session Files

### 2.1 The TTY Key

Each terminal has a unique TTY device (e.g., `pts-6`, `pts-2`). This is the isolation key.

```
Terminal 1 (pts-6) → ~/.empirica/tty_sessions/pts-6.json
Terminal 2 (pts-2) → ~/.empirica/tty_sessions/pts-2.json
```

### 2.2 TTY Session File Structure

**Location:** `~/.empirica/tty_sessions/{tty_key}.json`

```json
{
  "claude_session_id": null,
  "empirica_session_id": "2bc1da78-2a28-4745-b75b-f021d563d819",
  "project_path": "/home/yogapad/empirical-ai/empirica",
  "tty_key": "pts-6",
  "timestamp": "2026-02-06T16:18:42.480817",
  "pid": 1900034,
  "ppid": 1899900
}
```

**Fields:**
- `claude_session_id`: Claude Code conversation UUID (null if created from CLI)
- `empirica_session_id`: Session created by `empirica session-create`
- `project_path`: Absolute path to the project this terminal is working on
- `tty_key`: The TTY device name (used as filename)

### 2.3 When TTY Session is Written

1. **`empirica session-create`** - Writes TTY session with new empirica_session_id
2. **`empirica project-switch`** - Updates project_path in TTY session
3. **Hooks** - Can update claude_session_id when available

---

## 3. Transaction Files (Per-Project, Per-Instance)

### 3.1 Instance Suffix

Transaction files use an instance suffix for multi-pane isolation:

```
{project}/.empirica/active_transaction_tmux_4.json   # For tmux pane 4
{project}/.empirica/active_transaction_pts-6.json    # Alternative: TTY-based
{project}/.empirica/active_transaction.json          # Fallback (no suffix)
```

The suffix is determined by `get_instance_id()`:
1. First: `TMUX_PANE` environment variable (e.g., `%4` → `tmux_4`)
2. Fallback: TTY device name (e.g., `pts-6`)

### 3.2 Transaction File Structure

**Location:** `{project}/.empirica/active_transaction_{instance_id}.json`

```json
{
  "transaction_id": "e04ad48e-3c2b-48ef-96be-5ebcf86746c6",
  "session_id": "2bc1da78-2a28-4745-b75b-f021d563d819",
  "preflight_timestamp": 1770391133.159,
  "status": "open",
  "project_path": "/home/yogapad/empirical-ai/empirica",
  "updated_at": 1770391133.159
}
```

**Critical:** The `project_path` field enables cross-CWD operations.

---

## 4. Resolution Priority Chains

### 4.1 Finding the Project DB (`resolve_session_db_path`)

When a command needs to find the database for a session:

```
Priority 1: Transaction file's project_path
    ↓ (if not found)
Priority 2: TTY session's project_path
    ↓ (if not found)
Priority 3: CWD-based detection (get_session_db_path)
```

### 4.2 Statusline Project Detection

```
Priority 1: EMPIRICA_PROJECT_PATH env var
    ↓
Priority 2: TTY session's project_path (get_tty_session)
    ↓
Priority 3: path_resolver (get_empirica_root)
    ↓
Priority 4: Upward search for .empirica/ from CWD
```

### 4.3 Sentinel Transaction Detection

```
Priority 1: get_session_empirica_root(session_id) - looks up session's project
    ↓
Priority 2: CWD-based detection (get_empirica_root)
```

Then reads: `{empirica_root}/active_transaction_{instance_id}.json`

---

## 5. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Terminal (pts-6)                            │
│                                                                 │
│  ┌─────────────────────┐     ┌─────────────────────┐           │
│  │ empirica session-   │     │ empirica preflight- │           │
│  │ create              │     │ submit              │           │
│  └──────────┬──────────┘     └──────────┬──────────┘           │
│             │                           │                       │
│             ▼                           ▼                       │
│  ┌─────────────────────┐     ┌─────────────────────────────┐   │
│  │ TTY Session File    │     │ Transaction File            │   │
│  │ ~/.empirica/        │     │ {project}/.empirica/        │   │
│  │ tty_sessions/       │     │ active_transaction_         │   │
│  │ pts-6.json          │     │ tmux_4.json                 │   │
│  │                     │     │                             │   │
│  │ {                   │     │ {                           │   │
│  │   empirica_session  │◄────│   session_id: ...           │   │
│  │   project_path ─────┼────►│   project_path: ...         │   │
│  │ }                   │     │   status: "open"            │   │
│  └─────────────────────┘     │ }                           │   │
│             │                └─────────────────────────────┘   │
│             │                           │                       │
│             ▼                           ▼                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Project Database: {project}/.empirica/sessions/sessions.db│  │
│  │                                                          │   │
│  │ ┌──────────┐  ┌──────────┐  ┌──────────┐                │   │
│  │ │ sessions │  │ reflexes │  │ cascades │                │   │
│  │ └──────────┘  └──────────┘  └──────────┘                │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Key Functions

### 6.1 session_resolver.py

| Function | Purpose |
|----------|---------|
| `get_tty_key()` | Get current terminal's TTY device name |
| `get_tty_session()` | Read TTY session file for current terminal |
| `write_tty_session()` | Write TTY session file (session-create, project-switch) |
| `get_instance_id()` | Get instance suffix (tmux pane or TTY) |
| `write_active_transaction()` | Write transaction file with project_path |
| `get_session_empirica_root()` | Look up session's project from DB |

### 6.2 path_resolver.py

| Function | Purpose |
|----------|---------|
| `get_empirica_root()` | Find .empirica/ from CWD or config |
| `get_session_db_path()` | Get path to sessions.db (CWD-based) |
| `resolve_session_db_path()` | Find DB for session (transaction → TTY → CWD) |

### 6.3 statusline_cache.py

| Function | Purpose |
|----------|---------|
| `get_instance_id()` | Same as session_resolver (shared logic) |

---

## 7. Caching Strategy

**Decision (2026-02-06):** Removed file-based statusline caching.

**Rationale:**
- Statusline only refreshes on PREFLIGHT/CHECK/POSTFLIGHT (not every second)
- DB queries are fast (local SQLite)
- Cache caused stale data bugs when projects changed
- Single source of truth (DB) is simpler and more reliable

**What remains:**
- TTY session files (not cache, actual session linkage)
- Transaction files (not cache, transaction state)

---

## 8. Common Failure Modes & Fixes

### 8.1 CWD Reset by Claude Code

**Symptom:** Commands fail because they look in wrong project
**Fix:** Use TTY session's project_path, not CWD

### 8.2 Stale TTY Session

**Symptom:** Terminal closed, reopened, old session data used
**Fix:** `write_tty_session()` on session-create overwrites stale data

### 8.3 Wrong Instance's Transaction

**Symptom:** Pane A sees pane B's transaction
**Fix:** Instance suffix on transaction files (`active_transaction_tmux_4.json`)

### 8.4 Statusline Shows Wrong Project

**Symptom:** Statusline shows empirica-outreach but working on empirica
**Fix:** Statusline reads TTY session's project_path, not CWD

---

## 9. Implementation Checklist

- [x] TTY session files (`~/.empirica/tty_sessions/{tty_key}.json`)
- [x] Instance-suffixed transaction files (`active_transaction_{instance_id}.json`)
- [x] `project_path` in transaction files
- [x] `resolve_session_db_path()` uses transaction → TTY → CWD priority
- [x] Statusline uses TTY session's project_path
- [x] `get_session_empirica_root()` for Sentinel cross-project detection
- [x] Removed statusline file caching
- [x] Sentinel uses project resolution priority chain (transaction → TTY → CWD)
- [ ] Wire to workspace.db for git repo → project mapping (future)

---

## 10. Relationship to TRANSACTION_CONTINUITY_SPEC

This document complements TRANSACTION_CONTINUITY_SPEC.md:

| Aspect | TRANSACTION_CONTINUITY_SPEC | This Document |
|--------|----------------------------|---------------|
| Focus | Transactions spanning sessions | Instance isolation |
| Key entity | Transaction | Terminal/Instance |
| Problem | Compaction breaks continuity | Multiple panes bleed |
| Solution | File-based transactions | TTY-keyed files + instance suffix |

Both are needed for a complete picture:
- **Transaction continuity** = how work survives compaction
- **Instance isolation** = how parallel work stays separate

---

## 11. Known Issues (2026-02-06)

### 11.1 Sentinel Loop Auto-Closing

**Symptom:** Epistemic loops close unexpectedly between commands
**Status:** FIXED (2026-02-06)
**Root cause:** Sentinel was using `get_empirica_root()` (CWD-based) which pointed to wrong
project when Claude Code reset CWD. This caused it to read wrong database/loop state.
**Fix:** Added `resolve_project_root()` using priority chain: transaction file → TTY session → CWD

### 11.2 project-switch Triggers POSTFLIGHT

**Behavior:** `empirica project-switch` auto-triggers POSTFLIGHT on source project
**Status:** By design, but may need refinement
**Impact:** Loops close when switching projects
