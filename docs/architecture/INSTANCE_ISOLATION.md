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

## 2. Isolation Mechanism: Dual Key System

### 2.1 The Problem with TTY Keys in Hook Context

Each terminal has a unique TTY device (e.g., `pts-6`, `pts-2`). However:
- The `tty` command **fails in hook context** (returns "not a tty")
- `TMUX_PANE` environment variable **IS available** in hooks

This creates a key mismatch:
- **CLI context**: TTY key available via `tty` command → use `pts-6`
- **Hook context**: Only TMUX_PANE available → use `tmux_4`

### 2.2 Dual Key Storage

We store project mappings by BOTH keys:

```
CLI access (TTY key):
  ~/.empirica/tty_sessions/pts-6.json

Hook access (TMUX_PANE key):
  ~/.empirica/instance_projects/tmux_4.json
```

Both are written by `write_tty_session()` when the context has both keys available.

### 2.4 Active Work Files (Claude Session ID Key)

For non-tmux users, there's a third key type using Claude's conversation UUID:

```
~/.empirica/active_work_{claude_session_id}.json
```

**Written by:** `project-switch` command
**Contains:** `project_path`, `folder_name`, `empirica_session_id`

This works for ALL users because Claude Code always provides `session_id` in hook input.

### 2.5 TTY Session Files

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

### 4.1 Sentinel Project Resolution (`resolve_project_root`)

When Sentinel needs to find the correct project (works in hook context):

```
Priority 1: Transaction file's project_path (check CWD/.empirica, ~/.empirica)
    ↓ (if not found)
Priority 2: Instance mapping by TMUX_PANE (~/.empirica/instance_projects/tmux_4.json)
    ↓ (if not found)
Priority 3: TTY session by tty command (~/.empirica/tty_sessions/pts-6.json)
    ↓ (if not found)
Priority 4: CWD-based git root detection
```

**Critical:** Priority 2 (instance mapping) is the KEY for multi-instance isolation in hooks.
The `tty` command fails in hook context, but TMUX_PANE is available.

### 4.2 Finding the Project DB (`resolve_session_db_path`)

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
| `get_session_db_path()` | Get sessions.db (instance_projects → workspace.db → CWD → env) |
| `resolve_session_db_path()` | Find DB for session (transaction → instance → TTY → CWD) |

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

### 8.5 Sentinel Blocks `cd && empirica check-submit`

**Symptom:** Sentinel blocks `cd /path && empirica check-submit` even though
`check-submit` is in the Tier 2 whitelist.

**Root cause:** The `&&` operator was caught as a dangerous shell operator BEFORE
checking if any segment is a safe empirica command.

**Fix (2026-02-06):** Added special handling for `&&` chains - if one segment
is a safe empirica command and other segments are safe (cd, etc.), allow it.

---

## 9. Implementation Checklist

- [x] TTY session files (`~/.empirica/tty_sessions/{tty_key}.json`)
- [x] Instance-suffixed transaction files (`active_transaction_{instance_id}.json`)
- [x] `project_path` in transaction files
- [x] `resolve_session_db_path()` uses transaction → TTY → CWD priority
- [x] Statusline uses TTY session's project_path
- [x] `get_session_empirica_root()` for Sentinel cross-project detection
- [x] Removed statusline file caching
- [x] Sentinel uses project resolution priority chain (transaction → instance → TTY → CWD)
- [x] Instance mapping files (`~/.empirica/instance_projects/{tmux_id}.json`) for hook context
- [x] Active work files (`~/.empirica/active_work_{claude_session_id}.json`) for non-tmux users
- [x] Sentinel allows `cd && empirica` command chains
- [x] Wire Sentinel to use Claude session_id from hook input for active_work lookup
- [x] Wire pre-compact.py to use Claude session_id for project resolution
- [x] Wire post-compact.py to use Claude session_id for project resolution
- [x] Wire `get_session_db_path()` to check instance_projects mapping before CWD fallback
- [x] Wire to workspace.db for git repo → project mapping (Priority 2 in resolution chain)

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

### 11.3 Compact Hooks Project Mismatch

**Symptom:** After compaction, empirica commands fail with "Project not found" or wrong project
**Status:** FIXED (2026-02-06)
**Root cause:** `pre-compact.py` and `post-compact.py` used `find_project_root()` which didn't
check Claude session_id. They fell back to hardcoded paths or CWD, picking wrong project.
**Fix:** Added Priority 0 check for `~/.empirica/active_work_{session_id}.json` in both hooks.
Extract `claude_session_id = hook_input.get('session_id')` and pass to find_project_root().

### 11.4 Goal Transaction Linkage

**Symptom:** Goals have NULL transaction_id - no epistemic linkage to transactions
**Status:** FIXED (2026-02-06)
**Root cause:** `save_goal()` didn't accept/insert transaction_id, `goals-create` didn't derive it.
**Fix:** Added transaction_id to save_goal() signature and INSERT, goals-create auto-derives
from active transaction using `read_active_transaction()`.

### 11.5 CLI Commands Using Wrong Database

**Symptom:** CLI commands (check-submit, epistemics-list, etc.) use wrong project database
after project-switch when CWD is in a different project directory.
**Status:** FIXED (2026-02-06)
**Root cause:** `SessionDatabase()` uses `get_session_db_path()` which only had CWD-based
resolution. The fix to `resolve_session_db_path()` wasn't being used by most CLI commands.
**Fix:** Refactored `get_session_db_path()` priority chain:
1. Instance projects mapping (TMUX_PANE-based) - which project this instance is on
2. Workspace.db lookup (git root → trajectory_path) - global registry
3. CWD-based fallback (for unregistered projects)
4. EMPIRICA_SESSION_DB env var (demoted - CI/Docker only, breaks multi-instance)
**File:** `empirica/config/path_resolver.py`
