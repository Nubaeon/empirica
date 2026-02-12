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
{project}/.empirica/active_transaction_tmux_4.json   # For tmux pane %4
{project}/.empirica/active_transaction_term_pts_6.json  # Alternative: TTY-based
{project}/.empirica/active_transaction_default.json  # Fallback (no TTY/tmux)
```

The suffix is determined by `get_instance_id()`:
1. First: `TMUX_PANE` environment variable (e.g., `%4` → `tmux_4`)
2. Fallback: TTY device name, sanitized (e.g., `/dev/pts/6` → `term_pts_6`)
3. Final fallback: `default` (if no TTY available)

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

### 3.2a Pre-Compact Snapshot Files

Pre-compact hooks capture epistemic state before memory compaction, enabling continuity:

**Location:** `{project}/.empirica/ref-docs/pre_summary_{timestamp}.json`

```json
{
  "session_id": "2f479fcb-3bb4-480f-be97-58368aa1949f",
  "pre_compact_vectors": { "know": 0.75, "uncertainty": 0.25 },
  "active_transaction": {
    "transaction_id": "a023bc81...",
    "status": "open",
    "project_path": "/home/user/empirical-ai/empirica"
  },
  "breadcrumbs": { "findings": 10, "unknowns": 1, "goals": 10 }
}
```

**Written by:** `pre-compact.py` hook (captures state before summary)
**Read by:** `post-compact.py` hook (injects into CHECK gate prompt)

**Key Fields:**
- `active_transaction`: Captured from instance-specific transaction file, survives compaction
- `pre_compact_vectors`: AI's epistemic state BEFORE compaction (compare with post-compact self-assessment)
- `breadcrumbs`: Counts of noetic artifacts available for retrieval

This enables transaction continuity across memory barriers. See TRANSACTION_CONTINUITY_SPEC.md.

---

## 4. Resolution Priority Chains

### 4.1 Sentinel Project Resolution (`resolve_project_root`)

When Sentinel needs to find the correct project (works in hook context):

```
Priority 0: active_work file (~/.empirica/active_work_{claude_session_id}.json)
    ↓ (if not found)
Priority 1: Instance mapping by TMUX_PANE (~/.empirica/instance_projects/tmux_4.json)
    ↓ (if not found)
Priority 2: TTY session by tty command (~/.empirica/tty_sessions/pts-6.json)
    ↓ (if not found)
❌ NO CWD FALLBACK - fails explicitly
```

**Critical Changes (2026-02-07):**
- **CWD fallback REMOVED** - Prevents silent wrong-project mismatches when Claude Code resets CWD
- If all instance-aware mechanisms fail, returns None and Sentinel blocks with explicit error
- Priority 0 (active_work file) is the KEY for multi-instance isolation
- Claude Code provides `session_id` in hook input, which maps to the active_work file
- This works for ALL users, not just tmux users

#### active_work as Dual-Key Hub

The active_work file serves as the central linkage point, storing BOTH structural and temporal keys:

```json
{
  "project_path": "/home/user/empirical-ai/empirica",
  "folder_name": "empirica",
  "empirica_session_id": "2f479fcb-3bb4-480f-be97-58368aa1949f"
}
```

| Field | Purpose | Written By |
|-------|---------|------------|
| `project_path` | Structural key → project database location | `project-switch` |
| `folder_name` | Human-readable project identifier | `project-switch` |
| `empirica_session_id` | Temporal key → active session in that project | `project-switch` |

**Key Insight:** This file is the PRIMARY source of truth after project-switch.
TTY session files and transaction files are secondary. Post-compact hooks read this
file FIRST to recover both project context AND active session.

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
Priority 0a: active_work_{session_id}.json (authoritative after project-switch)
    ↓ (if not found)
Priority 0b: TTY session's project_path (fallback)
    ↓ (if not found)
Priority 1: path_resolver (get_empirica_root)
    ↓ (if not found)
Priority 2: generic active_work.json (LAST RESORT — shared across instances)
    ↓ (if not found)
❌ NO CWD FALLBACK - CWD is unreliable in Claude Code hooks
❌ NO EMPIRICA_PROJECT_PATH env - single env var breaks multi-instance
```

**Note:** active_work_{session_id} file takes precedence because TTY session can be stale after project-switch.
Generic active_work.json is LAST RESORT only — it's shared across all instances and will show
the wrong project in multi-instance setups if higher-priority resolution succeeds elsewhere.

### 4.2a Statusline Phase/Vectors Query

**Critical (2026-02-07):** `get_latest_vectors()` now filters by `transaction_id`:

```
1. Read active_transaction_{instance_id}.json
2. Extract both session_id AND transaction_id
3. Query reflexes table with: WHERE session_id = ? AND transaction_id = ?
```

Without transaction_id filtering, two Claude instances sharing the same session
would see each other's phases (cross-instance phase bleed).

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

### 5.1 Post-Compact Recovery Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Memory Compaction Boundary                       │
│                                                                      │
│  PRE-COMPACT                              POST-COMPACT               │
│  ───────────                              ────────────               │
│  ┌─────────────────┐                     ┌─────────────────┐        │
│  │ pre-compact.py  │                     │ post-compact.py │        │
│  └────────┬────────┘                     └────────┬────────┘        │
│           │                                       │                  │
│           │ 1. Read active_transaction            │ 1. Extract      │
│           │    from instance file                 │    claude_id    │
│           │                                       │    from stdin   │
│           │ 2. Read vectors from DB               │                 │
│           │                                       │ 2. Read         │
│           │ 3. Snapshot breadcrumbs               │    active_work  │
│           │                                       │    _{id}.json   │
│           ▼                                       │                 │
│  ┌─────────────────┐                     │ 3. Load pre_   │        │
│  │ pre_summary_    │─────────────────────┤    summary     │        │
│  │ {timestamp}.json│   (survives)        │    snapshot    │        │
│  └─────────────────┘                     │                 │        │
│                                                  │ 4. Inject       │
│                                                  │    CHECK gate   │
│                                                  │    with tx      │
│                                                  ▼                  │
│                                          ┌─────────────────┐        │
│                                          │ Dynamic context │        │
│                                          │ with transaction│        │
│                                          │ continuity      │        │
│                                          └─────────────────┘        │
└─────────────────────────────────────────────────────────────────────┘
```

**Critical Path:** `claude_session_id` → `active_work` file → `project_path` + `empirica_session_id`

---

## 6. Key Functions

### 6.1 session_resolver.py

| Function | Purpose |
|----------|---------|
| **`get_active_project_path()`** | **CANONICAL** - Get project path (active_work → instance_projects → NO CWD) |
| `get_tty_key()` | Get current terminal's TTY device name |
| `get_tty_session()` | Read TTY session file for current terminal |
| `write_tty_session()` | Write TTY session file (session-create, project-switch) |
| `get_instance_id()` | Get instance suffix: `tmux_{N}` format (e.g., `tmux_4`) |
| `read_active_transaction()` | Read transaction_id (uses `get_active_project_path()`) |
| `clear_active_transaction()` | Clear transaction file (uses `get_active_project_path()`) |
| `write_active_transaction()` | Write transaction file with project_path |
| `get_session_empirica_root()` | Look up session's project from DB |

**CANONICAL FUNCTION (2026-02-07):** `get_active_project_path(claude_session_id=None)` is the
single source of truth for project resolution. All components should use this instead of
implementing their own priority chain. Returns project_path or None (NO CWD fallback).

**Critical (2026-02-07):** `get_instance_id()` returns `tmux_N` format (not `tmux:%N`).
This matches file naming convention: `instance_projects/tmux_4.json`, `active_transaction_tmux_4.json`.
Both `session_resolver.get_instance_id()` and `statusline_cache.get_instance_id()` use the same format.

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

## 6.4 Claude Code Hook Input

Claude Code provides structured JSON to hooks via stdin. This is the source of `session_id` for instance isolation.

**Hook input structure:**
```json
{
  "session_id": "fad66571-1bde-4ee1-aa0d-e9d3dfd8e833",
  "transcript_path": "/home/user/.claude/projects/my-project/fad66571.jsonl",
  "cwd": "/home/user/my-project",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse"
}
```

**Key Fields:**

| Field | Purpose | Used By |
|-------|---------|---------|
| `session_id` | Claude conversation UUID | All hooks - maps to `active_work_{session_id}.json` |
| `transcript_path` | Full transcript file path | Pre-compact (state capture) |
| `cwd` | Working directory | **UNRELIABLE** - do not use for project resolution |
| `permission_mode` | Claude permission level | Sentinel (gate decisions) |
| `hook_event_name` | Hook event type | Conditional hook logic |

**Critical:** The `session_id` field is what enables multi-instance isolation for non-tmux users.
It maps to `~/.empirica/active_work_{session_id}.json` which stores the authoritative project path.

**Note:** The `cwd` field is unreliable because Claude Code can reset it (e.g., after compaction).
Hooks must use `session_id` → `active_work` file → `project_path` resolution chain.

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

#### TTY Staleness Detection (`validate_tty_session()`)

The `validate_tty_session()` function in `session_resolver.py` performs three checks:

1. **PID Check:** `os.kill(pid, 0)` - warns if the original process that created the session is dead
2. **TTY Device Check:** Verifies `/dev/{tty_key}` exists - invalid if TTY device is gone
3. **Timestamp Check:** 4-hour threshold - warns if session is stale (but may still be valid)

**Validation Results:**
- `valid=True`: Session is usable (but may have warnings)
- `valid=False`: Session should be ignored (TTY device doesn't exist)

**Cleanup:**
- **SessionEnd hook:** Cleans up TTY session file on normal exit
- **Crash recovery:** Next session on same TTY overwrites stale file
- **Periodic cleanup:** `cleanup_stale_tty_sessions()` removes files >24h old

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
- [x] Wire `_get_project_id_from_cwd()` in vectors.py to match sentinel's project_id computation
- [x] Pre-compact hooks capture active_transaction in snapshot (Section 3.2a)
- [x] Post-compact hooks inject transaction context from snapshot (Section 5.1)
- [x] active_work file stores both project_path AND empirica_session_id (dual-key hub)

---

## 10. Relationship to TRANSACTION_CONTINUITY_SPEC

**Critical:** Read [TRANSACTION_CONTINUITY_SPEC.md](./TRANSACTION_CONTINUITY_SPEC.md) alongside this document.
They solve related but distinct problems:

| Aspect | TRANSACTION_CONTINUITY_SPEC | This Document |
|--------|----------------------------|---------------|
| Focus | Transactions spanning sessions | Instance isolation |
| Key entity | Transaction | Terminal/Instance |
| Problem | Compaction breaks continuity | Multiple panes bleed |
| Solution | File-based transactions | TTY-keyed files + instance suffix |

**The intersection:** Pre-compact snapshots (Section 3.2a) capture transaction state, and
post-compact recovery (Section 5.1) injects it back. This bridges both concerns:
- Instance isolation ensures the RIGHT transaction is captured (not another pane's)
- Transaction continuity ensures work SURVIVES the compaction boundary

Both are needed for a complete picture:
- **Transaction continuity** = how work survives compaction
- **Instance isolation** = how parallel work stays separate

**Handoff reports** (see TRANSACTION_CONTINUITY_SPEC Section 6) provide additional context
for cross-session continuity, capturing key findings and next steps in structured format.

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

**Implementation detail (code-level flow):**

```python
# In pre-compact.py / post-compact.py main():

# 1. Extract claude_session_id from hook input
hook_input = json.loads(sys.stdin.read())
claude_session_id = hook_input.get('session_id')  # Claude Code provides this

# 2. Check active_work file FIRST (Priority 0)
active_work_path = Path.home() / '.empirica' / f'active_work_{claude_session_id}.json'
if active_work_path.exists():
    work_data = json.load(active_work_path.open())
    project_path = work_data.get('project_path')  # Authoritative
    empirica_session_id = work_data.get('empirica_session_id')

# 3. Fall back to other resolution methods only if Priority 0 fails
```

**Files modified:**
- `plugins/claude-code-integration/hooks/pre-compact.py`
- `plugins/claude-code-integration/hooks/post-compact.py`

**Related:** Section 3.2a (Pre-Compact Snapshot Files), Section 5.1 (Post-Compact Recovery Flow)

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
0. active_work file (set by project-switch, instance-aware via claude_session_id)
1. Workspace.db lookup (git root → trajectory_path) - global registry
2. CWD-based fallback (for unregistered projects)
3. EMPIRICA_SESSION_DB env var (demoted - CI/Docker only, breaks multi-instance)
**File:** `empirica/config/path_resolver.py`

### 11.6 Statusline Shows Stale Session Data

**Symptom:** Statusline shows 0 goals when database has 23 active goals. Wrong phase shown.
**Status:** FIXED (2026-02-06)
**Root cause:** `get_active_session()` prioritized TTY session's `empirica_session_id` over
the active_work file. TTY session can be stale after project-switch.
**Fix:** Reordered priority in `get_active_session()`:
- Priority 0a: active_work file (authoritative, updated by project-switch)
- Priority 0b: TTY session (fallback if active_work not available)
**File:** `plugins/claude-code-integration/scripts/statusline_empirica.py`

### 11.7 PREFLIGHT Writes Transaction to Wrong Project

**Symptom:** After project-switch, PREFLIGHT writes transaction file to CWD project instead
of the switched project. Sentinel then sees "Project context changed" error.
**Status:** FIXED (2026-02-06)
**Root cause:** `preflight-submit` used `project_path=os.getcwd()` when calling
`write_active_transaction()`. CWD doesn't change with project-switch.
**Fix:** Changed to resolve project_path from active_work file first, then fall back to CWD.
**File:** `empirica/cli/command_handlers/workflow_commands.py`

### 11.8 Sentinel Blocks project-switch Without PREFLIGHT

**Symptom:** Can't run `empirica project-switch` when no PREFLIGHT exists.
**Status:** FIXED (2026-02-06)
**Root cause:** project-switch wasn't in TRANSITION_COMMANDS or TIER1_PREFIXES whitelist.
**Fix:** Added `empirica project-switch` and `empirica project-list` to both lists.
**File:** `plugins/claude-code-integration/hooks/sentinel-gate.py`

### 11.9 Sentinel "Project Context Changed" After PREFLIGHT

**Symptom:** After project-switch and PREFLIGHT, Sentinel blocks commands with "Project context
changed. Run PREFLIGHT for new project" even though PREFLIGHT was just submitted.
**Status:** FIXED (2026-02-06)
**Root cause:** project_id format mismatch:
- PREFLIGHT stores project_id in reflexes table using `_get_project_id_from_cwd()` in vectors.py
- Sentinel's `_get_current_project_id()` was updated to check active_work file first
- These computed different hashes: vectors.py used git remote URL, sentinel used active_work project_path
**Fix:** Updated `_get_project_id_from_cwd()` in vectors.py to use same priority chain as sentinel:
1. active_work file (hash of project_path) - instance-aware, set by project-switch
2. Git remote origin URL hash (fallback)
3. Git toplevel path hash (fallback)
**File:** `empirica/data/repositories/vectors.py`

### 11.10 instance_id Format Mismatch (2026-02-07)

**Symptom:** Statusline shows wrong pane's data (cross-pane bleed).
**Status:** FIXED
**Root cause:** Two `get_instance_id()` functions returned different formats:
- `statusline_cache.get_instance_id()` → `tmux_4`
- `session_resolver.get_instance_id()` → `tmux:%4`
Files are named `tmux_4.json`, so the session_resolver version couldn't find them.
**Fix:** Changed `session_resolver.get_instance_id()` to return `tmux_{pane.lstrip('%')}` format.
**Commit:** `dfb5261e`
**Files:** `empirica/utils/session_resolver.py`

### 11.11 CWD Fallback Causes Silent Wrong-Project (2026-02-07)

**Symptom:** Commands/hooks silently use wrong project when instance-aware mechanisms fail.
**Status:** FIXED
**Root cause:** All resolution functions (`resolve_project_root`, `_get_current_project_id`,
`find_project_root` in hooks) fell back to CWD-based git detection when instance-aware
mechanisms failed. CWD can be reset by Claude Code to a different project.
**Fix:** Removed CWD fallback entirely from:
- `sentinel-gate.py`: `resolve_project_root()`, `_get_current_project_id()`
- `pre-compact.py`: `find_project_root()`
- `post-compact.py`: `find_project_root()`
Now returns None/exits with error if instance-aware mechanisms fail.
**Commit:** `dfb5261e`
**Files:** All sentinel and compact hooks

### 11.12 Statusline Cross-Instance Phase Bleed (2026-02-07)

**Symptom:** Statusline shows other Claude instance's phase (e.g., CHECK instead of PREFLIGHT).
**Status:** FIXED
**Root cause:** `get_latest_vectors()` queried reflexes by `session_id` only. When two Claude
instances share the same session, the latest phase from ANY transaction was returned.
**Fix:** Added `transaction_id` parameter to `get_latest_vectors()`. Caller extracts
`transaction_id` from instance-specific `active_transaction_{instance_id}.json` and passes it.
Query now: `WHERE session_id = ? AND transaction_id = ?`
**Commit:** `abb5c430`
**Files:** `plugins/claude-code-integration/scripts/statusline_empirica.py`

### 11.13 Orphaned Transaction After tmux Restart (2026-02-12)

**Symptom:** After tmux session dies/freezes and is restarted, the AI in the new tmux session
cannot find the previous transaction. The old transaction becomes "orphaned."

**Status:** BY DESIGN (requires human intervention)

**Scenario:**
1. Claude working in tmux pane `%4` with open transaction in `active_transaction_tmux_4.json`
2. tmux session freezes or is killed
3. User restarts tmux → new pane IDs (e.g., `%7`)
4. New Claude Code session starts with new `claude_session_id`
5. New session creates new `active_work_{new_claude_session_id}.json`
6. On compact, post-compact.py looks for `active_transaction_tmux_7.json` (doesn't exist)
7. Old transaction in `tmux_4` is orphaned

**Why auto-recovery is NOT done:**
- Different Claude sessions should NOT inherit each other's transactions
- Auto-picking up an old transaction could cause wrong-context pollution
- The new AI has no epistemic continuity with the old one (different conversation)
- tmux failure is rare and requires human intervention anyway

**Expected behavior:**
- Post-compact fails to find the old transaction
- AI is prompted for new PREFLIGHT (fresh start)
- Old transaction file remains on disk until manually cleaned up

**Recovery options:**
1. **Adopt the transaction (recommended):**
   ```bash
   # Adopt orphaned transaction from old instance to current instance
   empirica transaction-adopt --from tmux_4 --dry-run  # Preview first
   empirica transaction-adopt --from tmux_4            # Actually adopt
   ```
   This renames the transaction file and updates instance mappings.

2. **Abandon old transaction:** Delete `{project}/.empirica/active_transaction_tmux_4.json`
3. **Manually close:** Run `empirica postflight-submit` with the old session_id
4. **Clean up stale transactions:** `find ~/.empirica -name 'active_transaction_*.json' -mtime +1 -delete`

**Files involved:**
- `claude-code-integration/hooks/post-compact.py` - instance_id-keyed handoff lookup
- `claude-code-integration/hooks/pre-compact.py` - instance_id-keyed handoff write

---

## 12. Summary: Instance Isolation Key Insights

1. **File-based isolation** trumps database queries for multi-instance support
2. **Transaction files** are the real unit of work (sessions became containers)
3. **CWD is unreliable** - Claude Code resets it unpredictably
4. **Fail explicitly** - Better to error than silently use wrong project
5. **Instance ID format matters** - Consistent `tmux_N` across all components
6. **Transaction-scoped queries** - Always filter by `transaction_id` when available
7. **Pane ID changes orphan transactions** - tmux restart requires human intervention
