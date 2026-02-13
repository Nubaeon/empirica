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
**Fix:**
- post-compact: Always write instance_projects even without claude_session_id
- project-switch: Log warning when claude_session_id unavailable
**Key insight:** instance_id is PRIMARY isolation key; claude_session_id is supplementary.
**Commit:** `23f79366`

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
