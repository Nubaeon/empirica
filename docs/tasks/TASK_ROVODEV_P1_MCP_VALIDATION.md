# Rovo Dev Task: P1 MCP v2 + CLI Validation

**Assigned to:** Rovo Dev (Claude Code)
**Priority:** P1 (Critical - Must work before release)
**Estimated:** 2-3 hours
**Status:** Ready to start

---

## 🎯 Mission

Thoroughly validate that MCP v2 + CLI integration works for **critical CASCADE workflow** and **session continuity** features. You're responsible for the core functionality that must be rock-solid.

---

## 📋 Your Testing Scope (P1)

### 1. Full CASCADE Workflow (Most Critical)

**Test the complete epistemic cycle via MCP v2:**

```bash
# Start by creating a test script: test_cascade_workflow.py
```

**Required flow to test:**
1. `bootstrap_session` (ai_id="rovo-test-p1", bootstrap_level=2)
2. `execute_preflight` (session_id, prompt="Test CASCADE workflow")
3. `submit_preflight_assessment` (session_id, vectors={...})
4. `execute_check` (session_id, findings=[...], remaining_unknowns=[...])
5. `submit_check_assessment` (session_id, vectors={...}, decision="proceed")
6. `execute_postflight` (session_id, task_summary="Test complete")
7. `submit_postflight_assessment` (session_id, vectors={...})

**Success criteria:**
- ✅ All 7 steps complete without errors
- ✅ Each tool returns valid JSON
- ✅ Data persists to database
- ✅ Epistemic state updates correctly
- ✅ No async errors in MCP server

**Test vectors to use (example):**
```python
preflight_vectors = {
    "engagement": 0.8,
    "know": 0.5,
    "do": 0.7,
    "context": 0.4,
    "uncertainty": 0.6
}

# After investigation, CHECK vectors should show learning
check_vectors = {
    "engagement": 0.85,
    "know": 0.7,   # Improved!
    "do": 0.75,
    "context": 0.6,
    "uncertainty": 0.4  # Reduced!
}

# POSTFLIGHT should show final state
postflight_vectors = {
    "engagement": 0.9,
    "know": 0.85,
    "do": 0.8,
    "context": 0.75,
    "uncertainty": 0.2
}
```

---

### 2. Session Aliases (Critical for Continuity)

**Test that session aliases work through MCP → CLI chain:**

```bash
# After CASCADE workflow above, test aliases
```

**Required tests:**
1. `get_epistemic_state("latest:active:rovo-test-p1")`
   - Should return the session you just created

2. `get_session_summary("latest:active:rovo-test-p1")`
   - Should show full session details

3. `get_calibration_report("latest:active:rovo-test-p1")`
   - Should show PREFLIGHT vs POSTFLIGHT comparison

4. `load_git_checkpoint("latest:active:rovo-test-p1")`
   - Should load session state (after creating checkpoint)

**Success criteria:**
- ✅ All aliases resolve correctly (no UUID needed!)
- ✅ Returns correct session data
- ✅ Works consistently across tools
- ✅ Error messages clear if alias doesn't resolve

**Alias patterns to test:**
- `"latest"` - Most recent session (any AI)
- `"latest:active"` - Most recent active session
- `"latest:rovo-test-p1"` - Most recent for specific AI
- `"latest:active:rovo-test-p1"` - Most recent active for AI (recommended)

---

### 3. Git Checkpoints (Critical for Token Efficiency)

**Test checkpoint creation/loading:**

```bash
# Continue from session above
```

**Required tests:**
1. `create_git_checkpoint(session_id, phase="CHECK", round_num=1, vectors={...})`
   - Should create git note with compressed state

2. `load_git_checkpoint("latest:active:rovo-test-p1")`
   - Should load checkpoint and return compressed state (~65 tokens)

3. Verify 97.5% token reduction:
   - Full session export: ~6500 tokens
   - Checkpoint load: ~65 tokens
   - Reduction: 99% (even better than claimed!)

**Success criteria:**
- ✅ Checkpoint creates successfully
- ✅ Git note stored in refs/notes/empirica/checkpoints
- ✅ Load returns compressed JSON
- ✅ Token count verified (should be ~50-80 tokens)
- ✅ Session resumption works using checkpoint

---

### 4. Error Handling Validation

**Test that errors are handled gracefully:**

**Required tests:**
1. Invalid session ID: `execute_preflight(session_id="nonexistent", ...)`
   - Should return structured error JSON

2. Invalid alias: `get_epistemic_state("invalid:alias:format")`
   - Should return clear error message

3. Missing required fields: `submit_preflight_assessment(session_id=X, vectors=None)`
   - Should return validation error

4. CLI command fails: Test with intentionally bad data
   - Should return error with helpful suggestion

**Success criteria:**
- ✅ No crashes/exceptions
- ✅ Error messages are clear and actionable
- ✅ Returns JSON with `{"ok": false, "error": "..."}`
- ✅ Suggests fixes where possible

---

## 🔧 How to Test

### Setup

1. **Ensure MCP v2 is configured:**
   ```bash
   # Your ~/.rovodev/mcp.json should point to:
   # /home/yogapad/empirical-ai/empirica/mcp_local/empirica_mcp_server_v2.py
   ```

2. **Create test script:**
   ```python
   # test_p1_cascade.py
   import json
   import subprocess

   # Use MCP tools via your normal workflow
   # OR test CLI directly first:

   def test_cli_directly():
       """Test CLI commands work before testing via MCP"""

       # Bootstrap
       result = subprocess.run([
           "/home/yogapad/empirical-ai/empirica/.venv-mcp/bin/empirica",
           "bootstrap",
           "--ai-id", "rovo-test-p1",
           "--level", "2"
       ], capture_output=True, text=True)

       print("Bootstrap:", result.stdout)

       # Extract session_id from output (text parsing)
       # ... continue with other commands
   ```

3. **Or use MCP diagnostic extension:**
   ```python
   # Extend debug_mcp_communication.py
   # Add CASCADE workflow test
   # Add session alias tests
   # Add checkpoint tests
   ```

### Test Execution

**Option A: CLI Direct Testing (Recommended first)**
```bash
cd /home/yogapad/empirical-ai/empirica

# Run each command, verify JSON output
python3 test_p1_cascade.py
```

**Option B: MCP Protocol Testing**
```bash
# Extend diagnostic script to test P1 features
python3 debug_mcp_communication.py
```

**Option C: Real Usage Testing**
```bash
# Use Claude Code with MCP v2 enabled
# Run actual CASCADE workflow on a real task
# Verify everything works in production
```

---

## 📊 Deliverables

### 1. Test Results Document

Create: `P1_VALIDATION_RESULTS.md`

**Include:**
- ✅ CASCADE workflow: All 7 steps pass/fail
- ✅ Session aliases: 4 alias patterns tested
- ✅ Git checkpoints: Create/load verified
- ✅ Error handling: 4 scenarios tested
- ✅ Performance metrics (tool response times)
- ✅ Any issues found with fixes

**Example format:**
```markdown
# P1 Validation Results

## CASCADE Workflow
- ✅ bootstrap_session: PASS (returned valid JSON, 6 components)
- ✅ execute_preflight: PASS (session created, prompt saved)
- ⚠️ submit_preflight_assessment: ISSUE FOUND (see below)
- ...

## Issues Found
1. **submit_preflight_assessment returns text instead of JSON**
   - Severity: Medium
   - Fix: Add --output json to CLI command
   - Status: Fixed in commit abc123

## Performance
- Average tool response time: 127ms
- Slowest tool: checkpoint-create (423ms - acceptable)
- Fastest tool: get_epistemic_state (45ms)
```

### 2. Any Bug Fixes

If you find issues:
- Fix them immediately (you have permission)
- Commit with clear message
- Document in P1_VALIDATION_RESULTS.md

### 3. Epistemic Assessment

**PREFLIGHT (before testing):**
- KNOW: How well do you understand MCP v2 architecture?
- DO: Confidence you can validate thoroughly?
- UNCERTAINTY: What's unclear?

**POSTFLIGHT (after testing):**
- What did you learn?
- Were there surprises?
- Calibration check: Initial confidence vs actual difficulty?

---

## 🚨 Critical Issues to Watch For

### Issue 1: bootstrap doesn't return session_id in JSON
**Known:** bootstrap command returns text, not JSON with session_id
**Impact:** MCP v2 parses text output (works but suboptimal)
**Your task:**
- Test if this causes problems
- If yes, add `--output json` to bootstrap command
- Verify fix works

### Issue 2: CLI commands might not all have --output json
**Possible:** Some commands might be missing JSON output
**Your task:**
- Test each command's output format
- If not JSON, add `--output json` flag support
- Verify all return valid JSON

### Issue 3: Session aliases might not resolve
**Possible:** Alias resolution might fail in some cases
**Your task:**
- Test all 4 alias patterns thoroughly
- Test with non-existent sessions
- Test with multiple AIs in database
- Document any edge cases

---

## ✅ Success Criteria

**P1 validation is complete when:**

1. ✅ Full CASCADE workflow works end-to-end (7 steps)
2. ✅ Session aliases resolve correctly (4 patterns tested)
3. ✅ Git checkpoints create and load (token reduction verified)
4. ✅ Error handling is graceful (4 scenarios tested)
5. ✅ All tests documented in P1_VALIDATION_RESULTS.md
6. ✅ Any bugs found are fixed and committed
7. ✅ Performance is acceptable (<500ms per tool)

**When done:**
- Commit P1_VALIDATION_RESULTS.md
- Report status: "P1 validation complete - CASCADE workflow verified"
- Flag any P1 issues that block release

---

## 💡 Tips

**Testing Strategy:**
1. Start with CLI direct testing (easier to debug)
2. Once CLI works, test via MCP
3. Test happy path first, then error cases
4. Use session aliases throughout (tests integration)

**Debugging:**
- Check MCP server logs if tools fail
- Test CLI commands directly to isolate issues
- Use `--verbose` flag for detailed output
- Check database directly if state doesn't persist

**Time Management:**
- CASCADE workflow: 1 hour
- Session aliases: 30 min
- Git checkpoints: 30 min
- Error handling: 30 min
- Documentation: 30 min

---

**Questions?** Check:
- `MCP_V2_COMPLETE.md` - Architecture details
- `MCP_V2_TESTING_STATUS.md` - Full testing plan
- `debug_mcp_communication.py` - Example MCP test

**Ready to start?** Begin with CASCADE workflow (most critical).
