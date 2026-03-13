# Known Issues - Instance Isolation

Historical bugs and fixes related to instance isolation. Useful for debugging and understanding design decisions.

---

## Fixed Issues

### 11.1 Sentinel Loop Auto-Closing (2026-02-06)

**Symptom:** Epistemic loops close unexpectedly between commands
**Root cause:** Sentinel used CWD-based `get_empirica_root()` which pointed to wrong project when Claude Code reset CWD.
**Fix:** Added `resolve_project_root()` using priority chain: transaction → instance → TTY → CWD

### 11.2 Compact Hooks Project Mismatch (2026-02-06)

**Symptom:** After compaction, commands fail with "Project not found"
**Root cause:** Hooks didn't check `active_work_{session_id}.json` first.
**Fix:** Added Priority 0 check for active_work file in pre-compact.py and post-compact.py.

### 11.3 Goal Transaction Linkage (2026-02-06)

**Symptom:** Goals have NULL transaction_id
**Root cause:** `save_goal()` didn't accept transaction_id.
**Fix:** Added transaction_id to save_goal() signature; goals-create auto-derives from active transaction.

### 11.4 CLI Commands Using Wrong Database (2026-02-06)

**Symptom:** CLI commands use wrong project database after project-switch
**Root cause:** `get_session_db_path()` only had CWD-based resolution.
**Fix:** Added active_work file to priority chain in path_resolver.py.

### 11.5 Statusline Shows Stale Session Data (2026-02-06)

**Symptom:** Statusline shows 0 goals when database has 23 active goals
**Root cause:** `get_active_session()` prioritized TTY session over active_work file.
**Fix:** Reordered priority: active_work (authoritative) → TTY session (fallback).

### 11.6 PREFLIGHT Writes Transaction to Wrong Project (2026-02-06)

**Symptom:** After project-switch, PREFLIGHT writes to CWD project
**Root cause:** Used `project_path=os.getcwd()` instead of resolving from active_work.
**Fix:** Resolve project_path from active_work file first.

### 11.7 Sentinel Blocks project-switch Without PREFLIGHT (2026-02-06)

**Symptom:** Can't run `project-switch` when no PREFLIGHT exists
**Root cause:** project-switch wasn't in whitelist.
**Fix:** Added to TRANSITION_COMMANDS and TIER1_PREFIXES.

### 11.8 Sentinel "Project Context Changed" After PREFLIGHT (2026-02-06)

**Symptom:** Sentinel blocks commands after project-switch + PREFLIGHT
**Root cause:** project_id format mismatch between vectors.py and sentinel.
**Fix:** Updated vectors.py to use same priority chain as sentinel.

### 11.9 instance_id Format Mismatch (2026-02-07)

**Symptom:** Statusline shows wrong pane's data (cross-pane bleed)
**Root cause:** Two `get_instance_id()` functions returned different formats (`tmux_4` vs `tmux:%4`).
**Fix:** Standardized to `tmux_N` format everywhere.
**Commit:** `dfb5261e`

### 11.10 CWD Fallback Causes Silent Wrong-Project (2026-02-07)

**Symptom:** Commands/hooks silently use wrong project
**Root cause:** All resolution functions fell back to CWD-based detection.
**Fix:** Removed CWD fallback entirely; return None/error if instance-aware mechanisms fail.
**Commit:** `dfb5261e`

### 11.11 Statusline Cross-Instance Phase Bleed (2026-02-07)

**Symptom:** Statusline shows other Claude instance's phase
**Root cause:** `get_latest_vectors()` queried by session_id only, not transaction_id.
**Fix:** Added transaction_id filter to query.
**Commit:** `abb5c430`

### 11.12 Post-Compact Writes Wrong Session to instance_projects (2026-02-13)

**Symptom:** Statusline shows stale CHECK data from different session after compaction
**Root cause:** `_write_active_work_for_new_conversation()` used `empirica_session` from generic lookup instead of transaction's session_id.
**Fix:** Use `active_transaction.get('session_id')` when continuing a transaction.
**Commit:** `f8d9a82f`

### 11.13 Instance Isolation Fails When claude_session_id Unavailable (2026-02-13)

**Symptom:** `instance_projects` has `claude_session_id: null`
**Root cause:** CLI commands via Bash can't access claude_session_id (only in hook stdin).
**Fix (partial):**
- post-compact: Always write instance_projects even without claude_session_id
- project-switch: Log warning when claude_session_id unavailable
**Key insight:** instance_id is PRIMARY isolation key; claude_session_id is supplementary.
**Commit:** `23f79366`

### 11.14 project-switch Reverted by Self-Heal in get_active_project_path (2026-02-19)

**Symptom:** `empirica project-switch <project>` runs successfully but Sentinel and
statusline still see the old project. `instance_projects` shows
`"source": "self-heal-from-active_work"` — the self-heal overwrote the switch.

**Root cause (regression):** Commit `55b2e4ac` (Feb 9) flipped the priority in
`get_active_project_path()` from instance_projects-first (correct, `a3f74a33` Feb 7)
to active_work-first. It also added a self-heal that overwrote `instance_projects`
from `active_work` when they disagreed.

After project-switch:
- `instance_projects` correctly points to new project (CLI just wrote it)
- `active_work` still points to old project (CLI can't update it — no claude_session_id)
- Next hook (Sentinel) calls `get_active_project_path(claude_session_id)` → reads
  stale `active_work` → self-heals `instance_projects` BACK to old project

The commit's comment "active_work (set by project-switch, user intent)" was incorrect —
project-switch CANNOT write active_work because it doesn't know claude_session_id.

**Fix:** Reverted to instance_projects-first priority. Removed self-heal entirely.
`instance_projects` is the most current source because it's writable by both hooks
AND project-switch CLI. `active_work` is fallback for non-TMUX only.

**Also committed (safe, additive):**
1. `_update_active_work()`: Added TTY session fallback for instance_id resolution
2. `session-init hook`: Propagates `claude_session_id` to TTY session file

**Commit:** `f9d607ed` (TTY fallback), pending (priority fix)

### 11.15 Transaction File Deleted After POSTFLIGHT Breaks Compact (2026-02-21)

**Symptom:** After POSTFLIGHT closes a loop, compaction loses project context. post-compact
writes `active_work` pointing to wrong project. Sentinel blocks with "No PREFLIGHT".

**Root cause:** `clear_active_transaction()` deleted the transaction file immediately after
POSTFLIGHT. When compaction occurred, post-compact had no transaction file to read for
project context. It fell back to stale `active_work` data from a previous session.

**The problem sequence:**
1. POSTFLIGHT closes loop → `status="closed"` → file deleted
2. User continues work in same project (no new PREFLIGHT yet)
3. Compaction occurs
4. post-compact calls `_find_project_root()` → no transaction file exists
5. Falls back to stale `active_work` from old session → wrong project
6. Writes new `active_work` with wrong `project_path`
7. User's next PREFLIGHT attempt blocked because project context is wrong

**Fix:** Transaction files now persist as "project anchors" until overwritten by next PREFLIGHT.
1. `workflow_commands.py`: Removed `clear_active_transaction()` call from POSTFLIGHT handler
2. `sentinel-gate.py`: No longer deletes closed transactions (was backup purge)
3. `post-compact.py`: Uses closed transactions for project resolution (fallback to open)

**Design principle:** Closed transaction file serves two purposes:
- Open (`status="open"`): Active gating by Sentinel
- Closed (`status="closed"`): Project anchor for post-compact resolution

The file is only overwritten when a new PREFLIGHT starts a new transaction.

**Commit:** pending

### 11.16 Auto-POSTFLIGHT From CHECK Doesn't Close Transaction File (2026-02-22)

**Symptom:** CHECK auto-triggers POSTFLIGHT on goal completion. Epistemic snapshot
written to DB, but transaction file stays `status="open"`. Statusline/Sentinel
still see an open transaction.

**Root cause:** POSTFLIGHT handler used a custom project resolution chain
(TTY→active_work→CWD) instead of canonical `get_active_project_path()`.

The failure path (historical — auto-POSTFLIGHT removed in 1.6.4):
1. CHECK called `_auto_postflight()` → spawned `empirica postflight-submit -` subprocess
2. Subprocess inherits `TMUX_PANE` (instance_id resolves correctly)
3. TTY session has `claude_session_id=None` (by design — CLI can't access it)
4. Without claude_session_id, can't find `active_work_{id}.json` → `resolved_project_path=None`
5. Falls back to `Path.cwd()` — **violates NO CWD FALLBACK rule**
6. If CWD is wrong (post-compact, Claude reset), can't find `.empirica/` → silent fail
7. DB snapshot written (uses session_id, not project_path) but transaction file untouched

**Fix:** Replace custom resolution with `get_active_project_path()`:
- P0: `instance_projects/tmux_N.json` (always available when TMUX_PANE set)
- P1: `active_work_{claude_session_id}.json` (fallback for non-TMUX)
- No CWD fallback

**Commit:** `72149c86`

### 11.17 Pytest Subprocess Tests Pollute Live Database (2026-02-22)

**Symptom:** Running `pytest` creates test sessions and goals in the live `sessions.db`.
`goals-list` shows dozens of "Test AI-first goal creation [...]" entries after test runs.

**Root cause:** `test_ai_agent_workflow.py` uses `subprocess.run(['empirica', ...])` which
inherits the parent environment. The subprocess resolves the database via:

1. `get_active_context()` → finds `instance_projects/tmux_N.json` → live project path
2. `get_session_db_path()` → returns live `sessions.db`
3. `resolve_session_db_path()` → also returns live `sessions.db`

`EMPIRICA_SESSION_DB` env var existed but was priority 3 (last) in `get_session_db_path()`
and not checked at all in `resolve_session_db_path()`. The live DB always won.

**Fix (3 parts):**

1. **`path_resolver.py`:** Moved `EMPIRICA_SESSION_DB` to priority 0 in both
   `get_session_db_path()` and `resolve_session_db_path()`. When explicitly set,
   it now wins over all instance-aware resolution. This also fixes the Docker use case
   documented in `README.md` (which previously didn't actually work if the container
   had a git repo).

2. **`test_ai_agent_workflow.py`:** Added `isolated_env` fixture that creates a temp
   `sessions.db` and passes `EMPIRICA_SESSION_DB` via subprocess env. Tests now write
   to the temp DB. TMUX_PANE is preserved so project path resolution still works.

3. **Priority chain update:**
   ```
   get_session_db_path():
     0. EMPIRICA_SESSION_DB (explicit override)
     1. Unified context (transaction → active_work → TTY → instance_projects)
     2. workspace.db lookup
     3. Git root based

   resolve_session_db_path():
     0. EMPIRICA_SESSION_DB (explicit override)
     1. instance_projects mapping
     2. TTY session
     3. get_session_db_path() fallthrough
   ```

**Verified:** After fix, running `pytest` twice produced 0 new test goals/sessions in live DB.

**Commit:** pending

### 11.18 SessionStart Hook Matchers Never Matched (2026-02-22)

**Symptom:** Instance isolation breaks when CWD-based resolution diverges from
project-switch binding. `session-init.py` never fires on new conversations.

**Root cause:** `~/.claude/settings.json` SessionStart hook matchers used invalid
trigger values:
- `"new|fresh"` → never matches (Claude Code triggers: `startup`, `resume`, `clear`, `compact`)
- `"compact"` → missed `resume` trigger (continued conversations)

This meant:
1. `session-init.py` **never fired via hooks** — only via manual invocation
2. `post-compact.py` only ran on compaction, not on conversation resume
3. `ewm-protocol-loader.py` only loaded on compaction events

**Why it appeared to work:** `post-compact.py` (on `"compact"` matcher) correctly
writes `instance_projects` and `active_work` files. Since most long sessions involve
compaction, isolation files were eventually created. `project-switch` also writes them.
The gap only showed when a fresh conversation started in a different CWD than the
bound project — `session-init` should have written the isolation files at startup
but never did.

**Fix:** Updated `~/.claude/settings.json` matchers:
```json
"SessionStart": [
  { "matcher": "compact|resume", "hooks": [...post-compact, ewm-protocol-loader...] },
  { "matcher": "startup",        "hooks": [...session-init, ewm-protocol-loader...] }
]
```

**Claude Code SessionStart triggers (authoritative):**
| Trigger | When |
|---------|------|
| `startup` | New conversation begins |
| `resume` | Existing conversation continued |
| `clear` | After `/clear` command |
| `compact` | After auto/manual context compaction |

**Prevention:** Verify hook trigger values against platform documentation, not intuition.

**Commit:** applied to `~/.claude/settings.json` (not in git — user config file)

### 11.19 Ghost Session Propagation in post-compact (2026-02-25)

**Symptom:** Statusline shows `[empirica-web:inactive]` despite hooks running successfully.
`instance_projects` and `active_work` reference a session_id that doesn't exist in any database.

**Root cause:** Session `7b56baa5` was created (likely in a different DB or deleted during cleanup)
but all isolation files still referenced it. When post-compact ran on `resume`:

1. `_get_empirica_session()` read `active_work` → found ghost session `7b56baa5`
2. `_get_session_phase_state("7b56baa5")` queried local DB → zero reflexes found
3. Zero reflexes → `is_complete = False` → routed to CHECK_GATE (not NEW_SESSION)
4. CHECK_GATE path does NOT create a new session — just re-propagates the ghost ID
5. Statusline queries `WHERE session_id = '7b56baa5' AND end_time IS NULL` → not found → "inactive"

**The self-reinforcing loop:** Each resume/compact re-reads the ghost from active_work,
fails to find it in DB, misinterprets as "mid-work incomplete session", and writes it back.
The ghost persists across unlimited compaction cycles.

**Fix:** Added ghost session detection in post-compact.py `main()`. After resolving
`empirica_session` from active_work, verify it exists in the local DB via
`SELECT 1 FROM sessions WHERE session_id = ?`. If not found, create a new session
and update all isolation files — bypassing the normal phase-state routing.

**Prevention:** Session existence check before using session_id from file-based state.
File-based state can reference sessions that no longer exist (cleanup, DB restore,
cross-DB creation). Always verify against the authoritative source (the database).

**Commit:** applied to `~/.claude/plugins/local/empirica-integration/hooks/post-compact.py`

---

## By Design (Not Bugs)

### Orphaned Transaction After tmux Restart (2026-02-12)

**Scenario:** tmux dies, new session has different pane IDs, old transaction can't be found.

**Why NOT auto-recovered:**
- Different Claude sessions shouldn't inherit each other's transactions
- Auto-pickup could cause wrong-context pollution
- tmux failure is rare and requires human intervention anyway

**Recovery:**
```bash
# Option 1: Adopt the transaction
empirica transaction-adopt --from tmux_4

# Option 2: Abandon it
rm {project}/.empirica/active_transaction_tmux_4.json

# Option 3: Close it properly
empirica postflight-submit --session-id <old_session_id> ...
```

### project-switch Triggers POSTFLIGHT

**Behavior:** `project-switch` auto-triggers POSTFLIGHT on source project.
**Status:** By design - loops should close when switching projects.

---

## Common Failure Patterns

### CWD Reset by Claude Code

**Symptom:** Commands fail because they look in wrong project
**Fix:** Use TTY/instance session's project_path, not CWD

### Stale TTY Session

**Symptom:** Terminal closed and reopened, old session data used
**Fix:** `write_tty_session()` on session-create overwrites stale data

### Wrong Instance's Transaction

**Symptom:** Pane A sees pane B's transaction
**Fix:** Instance suffix on transaction files (`active_transaction_tmux_4.json`)

### Sentinel Blocks `cd && empirica check-submit`

**Symptom:** Sentinel blocks command chains with `&&`
**Fix:** Added special handling for `&&` chains with safe empirica commands

---

## Debugging Checklist

1. **Check instance_id format:** Should be `tmux_N` everywhere
2. **Check file exists:** `ls ~/.empirica/instance_projects/tmux_*.json`
3. **Check session matches:** Compare session_id in instance_projects vs active_transaction
4. **Check project_path:** Is it pointing to the right project?
5. **Check transaction status:** Is it `"open"` or closed?

```bash
# Quick diagnostic
echo "=== Instance Projects ===" && cat ~/.empirica/instance_projects/tmux_*.json 2>/dev/null
echo "=== Active Transaction ===" && cat .empirica/active_transaction_*.json 2>/dev/null
echo "=== TTY Session ===" && cat ~/.empirica/tty_sessions/$(tty | tr '/' '-' | sed 's/^-//').json 2>/dev/null
```
