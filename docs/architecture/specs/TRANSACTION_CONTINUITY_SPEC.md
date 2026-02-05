# Epistemic Transaction Continuity Spec

**Status:** DRAFT
**Authors:** David, Claude
**Date:** 2026-02-05
**Related:** Sentinel, CASCADE workflow, Session management

---

## 1. Problem Statement

### 1.1 Core Challenge
Epistemic transactions (PREFLIGHT → work → POSTFLIGHT) are the unit of measurement in Empirica. However, transactions can span multiple sessions because:
- **Sessions are context-bounded**: When Claude Code's context fills, compaction creates a new session
- **CWD is unreliable**: Claude Code resets CWD, so path-based detection fails
- **Tmux pane IDs bleed**: Instance detection via tmux is fragile

### 1.2 Requirements
1. A transaction opened in Session A must be closeable from Session B (post-compact)
2. Multiple parallel transactions (different projects) must coexist
3. No reliance on CWD or tmux pane detection
4. The Sentinel must enforce transaction boundaries correctly across sessions

---

## 2. Key Concepts

### 2.1 Terminology

| Term | Definition |
|------|------------|
| **Session** | Temporal window bounded by context compaction. Has a UUID. |
| **Transaction** | Epistemic measurement cycle: PREFLIGHT → work → POSTFLIGHT. Has a UUID. |
| **Project** | Git repository with `.empirica/` directory. Has a UUID and path. |

### 2.2 Scope Relationships

```
Project (structural, permanent)
    └── contains multiple Transactions (measurement, can span sessions)
            └── touched by multiple Sessions (temporal, compact-bounded)
```

- **Transactions belong to Projects**, not Sessions
- **Sessions touch Transactions**, but don't own them
- A Transaction can span 1-N Sessions (due to compaction)
- A Session can touch 0-1 Transactions per Project

---

## 3. Data Structures

### 3.1 Transaction File (per-project)

**Location:** `{project}/.empirica/active_transaction.json`

```json
{
  "transaction_id": "uuid-of-transaction",
  "project_path": "/absolute/path/to/project/.empirica",
  "preflight_session_id": "uuid-of-session-that-opened",
  "preflight_timestamp": 1234567890.123,
  "status": "open | closed",
  "sessions": ["session-A", "session-B"],
  "updated_at": 1234567890.456,
  "postflight_timestamp": null,
  "postflight_session_id": null
}
```

**Notes:**
- One file per project (not per session)
- `sessions` array tracks all sessions that touched this transaction
- `status: "open"` means PREFLIGHT done, POSTFLIGHT pending

### 3.2 Session Table Extensions

```sql
-- Existing sessions table gets new columns
ALTER TABLE sessions ADD COLUMN active_transaction_id TEXT;
ALTER TABLE sessions ADD COLUMN transaction_project_path TEXT;
```

This allows querying: "Which transaction is this session working on?"

### 3.3 Handoff Report Extensions

The handoff report (created at compact time) should include:

```json
{
  "task_summary": "...",
  "key_findings": [...],
  "active_transaction": {
    "transaction_id": "uuid",
    "project_path": "/path/to/.empirica",
    "status": "open",
    "preflight_vectors": { "know": 0.7, "uncertainty": 0.3, ... }
  },
  "next_session_context": "Continue transaction uuid in project X"
}
```

---

## 4. Flows

### 4.1 PREFLIGHT Flow

```
AI runs: empirica preflight-submit -

1. Generate transaction_id (UUID)
2. Resolve project path:
   - Try get_session_empirica_root(session_id)
   - Fallback to get_empirica_root() (git root)
3. Write transaction file to {project}/.empirica/active_transaction.json:
   - transaction_id, project_path, session_id, timestamp, status="open"
4. Update session record:
   - Set active_transaction_id = transaction_id
   - Set transaction_project_path = project_path
5. Return response with prominent transaction info:
   {
     "transaction_id": "...",
     "project_path": "...",
     "message": "Transaction opened. Include in handoff if compacting."
   }
```

### 4.2 POSTFLIGHT Flow

```
AI runs: empirica postflight-submit [--transaction-id TX] [--project-path PATH] -

1. Resolve transaction location:
   a. If --transaction-id and --project-path provided: use those (explicit)
   b. Else if session has active_transaction_id: use session's stored values
   c. Else try get_session_empirica_root(session_id)
   d. Else fallback to get_empirica_root()

2. Read transaction file from resolved path
3. Verify transaction exists and status="open"
4. Update transaction file:
   - status = "closed"
   - postflight_timestamp = now
   - postflight_session_id = current session
   - Add current session to sessions array
5. Clear session's active_transaction_id
6. Return response confirming closure
```

### 4.3 Compact/Handoff Flow

```
Context approaching limit, AI prepares for compact:

1. Check for open transaction:
   - Read session's active_transaction_id
   - Or scan {project}/.empirica/active_transaction.json

2. If open transaction exists:
   a. Include in handoff report:
      - transaction_id
      - project_path
      - preflight vectors (for context)
   b. Log finding: "Transaction {id} open, will continue post-compact"

3. Create handoff report with transaction context

4. Post-compact, new session starts:
   a. AI reads handoff, sees active transaction
   b. AI notes: "Continuing transaction {id} from project {path}"
   c. When ready for POSTFLIGHT, AI uses explicit flags:
      empirica postflight-submit --transaction-id TX --project-path PATH -
```

### 4.4 Sentinel Enforcement Flow

```
Sentinel intercepts praxic tool use:

1. Get current session_id (existing logic)
2. Find active transaction:
   a. Read session's transaction_project_path
   b. Read transaction file from that path
   c. If no session binding, try get_empirica_root() as fallback

3. Check transaction status:
   - If no transaction file: require PREFLIGHT
   - If status="closed": require new PREFLIGHT
   - If status="open": check vectors, allow if passing gate

4. Enforce boundaries:
   - Praxic actions only allowed within open transaction
   - Transition commands (session-create, project-switch) always allowed
```

---

## 5. Edge Cases

### 5.1 Compact Without POSTFLIGHT

**Scenario:** Transaction opened, work done, compact happens before POSTFLIGHT

**Handling:**
- Transaction file persists (file-based, survives compact)
- Handoff includes transaction context
- New session continues, eventually runs POSTFLIGHT
- Transaction spans multiple sessions (by design)

### 5.2 Multiple Projects, Multiple Transactions

**Scenario:** Working on empirica and empirica-outreach simultaneously

**Handling:**
- Each project has its own `active_transaction.json`
- Each session tracks ONE active transaction (its primary project)
- Parallel sessions can have different active transactions
- No conflict because transaction files are project-scoped

### 5.3 Orphaned Transaction

**Scenario:** Transaction opened, session abandoned (no compact, no POSTFLIGHT)

**Handling:**
- Transaction file remains with status="open"
- Next session in same project will find it
- Options:
  a. Auto-close stale transactions (>24h old)
  b. Warn user about orphaned transaction
  c. Require explicit `empirica transaction-close --orphaned`

### 5.4 Session Created in Wrong Project

**Scenario:** Post-compact, new session created but CWD was different project

**Handling:**
- Handoff contains explicit project_path
- AI uses `--project-path` flag on POSTFLIGHT
- Session's `transaction_project_path` may differ from session's own project
- This is fine: session is just the executor, transaction belongs to project

### 5.5 POSTFLIGHT Without PREFLIGHT

**Scenario:** AI tries to run POSTFLIGHT but no transaction is open

**Handling:**
- Check transaction file: if missing or status="closed", reject
- Return error: "No open transaction. Run PREFLIGHT first."
- Sentinel should have blocked praxic work anyway

---

## 6. Implementation Status

### 6.1 Completed

- [x] Transaction file structure (`active_transaction.json`)
- [x] `write_active_transaction_json()` in session_resolver
- [x] `read_active_transaction_json()` in session_resolver
- [x] `close_active_transaction_json()` in session_resolver
- [x] `get_session_empirica_root()` in session_resolver
- [x] PREFLIGHT writes transaction file (via session's project)
- [x] POSTFLIGHT closes transaction file (via session's project)
- [x] Sentinel reads transaction file for enforcement

### 6.2 TODO

- [x] Add `--transaction-id` and `--project-path` flags to POSTFLIGHT (2026-02-05)
- [ ] Add `active_transaction_id` and `transaction_project_path` columns to sessions table
- [ ] Update PREFLIGHT to write to session record
- [ ] Update POSTFLIGHT to read from session record (with flag override)
- [ ] Update handoff report to include active transaction context
- [x] Update post-compact hook to use project path from pre-compact snapshot (2026-02-05)
- [ ] Add `empirica transaction-status` command (debugging)
- [ ] Add orphaned transaction detection/cleanup
- [ ] Update Sentinel to use session's stored transaction path

---

## 7. CLI Interface

### 7.1 PREFLIGHT (existing, enhanced output)

```bash
empirica preflight-submit -
# Input: JSON with session_id, vectors, reasoning
# Output: JSON with transaction_id, project_path prominently displayed
```

### 7.2 POSTFLIGHT (enhanced with flags)

```bash
# Normal (uses session's stored transaction)
empirica postflight-submit -

# Explicit (for cross-session continuity)
empirica postflight-submit \
  --transaction-id abc-123 \
  --project-path /path/to/.empirica \
  -
```

### 7.3 Transaction Status (new)

```bash
# Check current transaction state
empirica transaction-status [--session-id ID] [--project-path PATH]

# Output:
{
  "transaction_id": "...",
  "status": "open",
  "project": "empirica",
  "project_path": "/home/user/empirica/.empirica",
  "preflight_session": "session-A",
  "sessions_touched": ["session-A", "session-B"],
  "age_seconds": 3600
}
```

### 7.4 Transaction Close (new, for orphans)

```bash
# Force-close orphaned transaction
empirica transaction-close --orphaned --project-path /path/to/.empirica
```

---

## 8. Sentinel Integration

### 8.1 Transaction-Aware Enforcement

The Sentinel should:

1. **Find transaction via session binding first:**
   ```python
   # Preferred: session knows its transaction
   cursor.execute("""
       SELECT transaction_project_path FROM sessions
       WHERE session_id = ?
   """, (session_id,))
   ```

2. **Fallback to project detection:**
   ```python
   # If no session binding, try session's project
   session_empirica_root = get_session_empirica_root(session_id)
   # Then try CWD as last resort
   if not session_empirica_root:
       session_empirica_root = get_empirica_root()
   ```

3. **Read and enforce transaction state:**
   ```python
   tx = _read_active_transaction(session_empirica_root)
   if not tx or tx['status'] != 'open':
       respond("deny", "No open transaction. Run PREFLIGHT.")
   ```

---

## 9. Summary

**The AI is the continuity mechanism.**

- Transactions belong to projects (file-based)
- Sessions track which transaction they're working on (database)
- Compaction creates handoffs that include transaction context (summary)
- Post-compact, AI explicitly continues the transaction (flags)
- Sentinel enforces boundaries using session's stored transaction path

This design:
- ✅ No CWD dependency
- ✅ No tmux detection
- ✅ Survives compaction
- ✅ Supports parallel projects
- ✅ Explicit over implicit
