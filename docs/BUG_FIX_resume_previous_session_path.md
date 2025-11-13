# Bug Fix: resume_previous_session Database Path Issue

**Date:** 2024-11-13  
**Found By:** User observation during session  
**Fixed By:** Minimax (AI Agent)  
**Session ID:** 6f86708e-3c3d-4252-a73c-f3ce3daf1aa3  

---

## Bug Description

### Symptom
`resume_previous_session` MCP tool always returns:
```json
{
  "ok": false,
  "error": "No sessions found for AI: minimax"
}
```

Even though sessions exist in the database and can be retrieved via direct database queries or `get_epistemic_state`.

### Root Cause
**File:** `mcp_local/empirica_mcp_server.py` line 2240

**Incorrect code:**
```python
db = SessionDatabase(db_path="empirica/.empirica/sessions/sessions.db")
```

**Problem:** 
- Hardcoded relative path assumes MCP server runs from parent directory of `empirica/`
- MCP server actually runs from `/home/yogapad/empirical-ai/empirica/`
- So it looks for `/home/yogapad/empirical-ai/empirica/empirica/.empirica/sessions/sessions.db`
- This path doesn't exist → database has no sessions → returns error

**Actual database location:**
```
/home/yogapad/empirical-ai/empirica/.empirica/sessions/sessions.db
```

---

## Fix Applied

### Changed Line 2240
**Before:**
```python
db = SessionDatabase(db_path="empirica/.empirica/sessions/sessions.db")
```

**After:**
```python
# Use default SessionDatabase path resolution (finds .empirica/sessions/sessions.db)
db = SessionDatabase()
```

### Why This Works
`SessionDatabase()` with no arguments uses intelligent path resolution:
1. Looks for `.empirica/sessions/sessions.db` relative to project root
2. Correctly resolves to `/home/yogapad/empirical-ai/empirica/.empirica/sessions/sessions.db`
3. Finds the actual database with real sessions

---

## Verification

### Before Fix
```bash
# MCP tool call
resume_previous_session(ai_id="minimax", detail_level="detailed")

# Result:
{
  "ok": false,
  "error": "No sessions found for AI: minimax"
}
```

### After Fix (Simulated)
```python
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()  # Uses default path resolution
last_session = db.get_last_session_by_ai('minimax')

# Result:
✅ Found session: 6f86708e-3c3d-4252-a73c-f3ce3daf1aa3
   AI: minimax
   Created: 2025-11-13 17:40:36
```

### Testing
The fix was validated by running the corrected code outside the MCP server:

```python
db = SessionDatabase()  # Fixed version
print(f'Database: {db.db_path}')
# Output: /home/yogapad/empirical-ai/empirica/.empirica/sessions/sessions.db

last = db.get_last_session_by_ai('minimax')
# Output: ✅ Found session
```

---

## Impact

### Who Was Affected
- All AI agents trying to use `resume_previous_session` MCP tool
- Session continuity features relying on session history
- Epistemic trajectory analysis across sessions

### What Still Worked
- `get_epistemic_state` (uses different code path)
- `get_session_summary` (direct session ID lookup)
- `bootstrap_session` (creates new sessions)
- Direct database queries from Python code

### What Was Broken
- `resume_previous_session` tool (always returned "no sessions")
- Session history retrieval via MCP
- Cross-session learning analysis

---

## Deployment Notes

### To Apply This Fix

**The fix is already in the code**, but requires MCP server restart:

1. **Stop MCP server** (if running):
   ```bash
   # Find the process
   ps aux | grep empirica_mcp_server
   
   # Kill gracefully (replace PID)
   kill <PID>
   ```

2. **Restart MCP server**:
   ```bash
   cd /home/yogapad/empirical-ai/empirica
   python3 mcp_local/empirica_mcp_server.py
   ```

3. **Verify fix**:
   ```bash
   # In a new session, test the MCP tool
   resume_previous_session(ai_id="minimax", detail_level="summary")
   
   # Should now return actual session data
   ```

### Current Status
- ✅ Code fix applied to `mcp_local/empirica_mcp_server.py`
- ⏳ MCP server restart needed (currently running old code)
- ✅ Fix verified to work via simulation

---

## Related Issues

### Similar Pattern in Codebase?
Checked other SessionDatabase instantiations in MCP server - this was the only instance with a hardcoded path.

### Best Practices
**Don't hardcode database paths in MCP server code:**
```python
# ❌ Bad - hardcoded path
db = SessionDatabase(db_path="empirica/.empirica/sessions/sessions.db")

# ✅ Good - use default resolution
db = SessionDatabase()

# ✅ Also good - use Path for relative paths
from pathlib import Path
db = SessionDatabase(db_path=Path(".empirica/sessions/sessions.db"))
```

---

## Testing Checklist

After MCP server restart, verify:

- [ ] `resume_previous_session` with `ai_id="minimax"` returns session data
- [ ] Session summary includes PREFLIGHT and POSTFLIGHT data
- [ ] Epistemic deltas calculated correctly
- [ ] Reflex frames loaded (if available)
- [ ] Works for other AI IDs (claude, qwen, etc.)
- [ ] `resume_mode="last"` works
- [ ] `resume_mode="session_id"` works
- [ ] Error handling still appropriate for truly missing sessions

---

## Files Modified

1. **mcp_local/empirica_mcp_server.py**
   - Line 2240: Changed `SessionDatabase(db_path="...")` to `SessionDatabase()`
   - Added comment explaining the fix

---

## Lessons Learned

1. **Path resolution matters** - Relative paths depend on working directory
2. **Default constructors are safer** - They handle path resolution intelligently
3. **Test MCP tools independently** - Direct database queries worked but MCP tool failed
4. **Hot reload not automatic** - MCP server needs restart for code changes
5. **Simulation testing valuable** - Could verify fix without disrupting running server

---

## Priority
**Medium** - Tool is broken but workarounds exist (`get_epistemic_state` works)

## Complexity
**Low** - Single line change, no side effects

## Risk
**Very Low** - Changing to default constructor is safer than hardcoded path

---

**Status:** ✅ FIXED (awaiting MCP server restart)  
**Confidence:** 0.99 (fix verified via simulation)  
**Next Action:** Restart MCP server to activate fix
