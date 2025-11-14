# Mini-Agent Testing Checklist

**For:** Autonomous agent (Minimax or similar)  
**Task:** End-to-end testing of Empirica database + reflex logs integration  
**Reference:** See `END_TO_END_TEST_STATUS.md` for complete details

---

## Pre-Flight Checks

### 1. Verify Installation
```bash
# Check database module
python3 -c "from empirica.data.session_database import SessionDatabase; print('✅ Database OK')"

# Check reflex logger
python3 -c "from empirica.core.canonical.reflex_logger import ReflexLogger; print('✅ Reflex Logger OK')"

# Check MCP server
python3 -c "import sys; sys.path.insert(0, 'mcp_local'); from empirica_mcp_server import main; print('✅ MCP Server OK')"
```

**Expected:** All three print "✅ OK"

---

## Test Sequence

### Test 1: Bootstrap Session

**MCP Call:**
```json
{
  "tool": "bootstrap_session",
  "arguments": {
    "ai_id": "minimax_test",
    "session_type": "testing"
  }
}
```

**Expected Response:**
```json
{
  "ok": true,
  "session_id": "abc-123-...",
  "ai_id": "minimax_test"
}
```

**Verification:**
```bash
# Check database
sqlite3 .empirica/sessions/sessions.db "SELECT session_id, ai_id FROM sessions ORDER BY created_at DESC LIMIT 1;"
```

**Expected:** Session exists with your `session_id`

✅ **PASS** / ❌ **FAIL**: ___________

---

### Test 2: PREFLIGHT Assessment

**Step 2a: Execute PREFLIGHT**
```json
{
  "tool": "execute_preflight",
  "arguments": {
    "session_id": "<session_id_from_test_1>",
    "prompt": "Test task: Analyze simple code function"
  }
}
```

**Expected Response:**
```json
{
  "ok": true,
  "phase": "preflight",
  "self_assessment_prompt": "Assess your epistemic state across 13 vectors..."
}
```

**Step 2b: Submit PREFLIGHT**
```json
{
  "tool": "submit_preflight_assessment",
  "arguments": {
    "session_id": "<session_id>",
    "vectors": {
      "engagement": 0.8,
      "know": 0.6,
      "do": 0.7,
      "context": 0.5,
      "clarity": 0.9,
      "coherence": 0.8,
      "signal": 0.7,
      "density": 0.6,
      "state": 0.5,
      "change": 0.6,
      "completion": 0.4,
      "impact": 0.5,
      "uncertainty": 0.5
    }
  }
}
```

**Expected Response:**
```json
{
  "ok": true,
  "message": "PREFLIGHT assessment logged to database AND reflex logs",
  "assessment_id": "...",
  "reflex_log_path": ".empirica_reflex_logs/2025-11-13/minimax_test/<session_id>/reflex_frame_preflight.json"
}
```

**Verification:**
```bash
# 1. Check database
sqlite3 .empirica/sessions/sessions.db "SELECT assessment_id, reflex_log_path FROM epistemic_assessments WHERE session_id='<session_id>';"

# 2. Check file exists
ls -la .empirica_reflex_logs/2025-11-13/minimax_test/<session_id>/

# 3. Verify file content
cat .empirica_reflex_logs/2025-11-13/minimax_test/<session_id>/reflex_frame_preflight.json | jq '.vectors'
```

**Expected:**
- Database has `assessment_id` and `reflex_log_path`
- Directory exists: `.empirica_reflex_logs/2025-11-13/minimax_test/<session_id>/`
- File exists: `reflex_frame_preflight.json`
- File contains 13 vectors

✅ **PASS** / ❌ **FAIL**: ___________

---

### Test 3: CHECK Assessment

**Step 3a: Execute CHECK**
```json
{
  "tool": "execute_check",
  "arguments": {
    "session_id": "<session_id>",
    "findings": ["Found key insights"],
    "remaining_unknowns": ["Need more context"],
    "confidence_to_proceed": 0.65
  }
}
```

**Expected Response:**
```json
{
  "ok": true,
  "phase": "check",
  "decision": "investigate",
  "confidence": 0.65
}
```

**Step 3b: Submit CHECK**
```json
{
  "tool": "submit_check_assessment",
  "arguments": {
    "session_id": "<session_id>",
    "vectors": {
      "engagement": 0.8,
      "know": 0.7,
      "do": 0.7,
      "context": 0.6,
      "clarity": 0.9,
      "coherence": 0.8,
      "signal": 0.7,
      "density": 0.6,
      "state": 0.6,
      "change": 0.7,
      "completion": 0.5,
      "impact": 0.6,
      "uncertainty": 0.4
    },
    "decision": "proceed",
    "reasoning": "Sufficient knowledge gained",
    "investigation_cycle": 1
  }
}
```

**Expected Response:**
```json
{
  "ok": true,
  "message": "CHECK assessment logged with reflex export",
  "check_id": "...",
  "decision": "proceed"
}
```

**Verification:**
```bash
# 1. Check database
sqlite3 .empirica/sessions/sessions.db "SELECT check_id, decision FROM check_phase_assessments WHERE session_id='<session_id>';"

# 2. Check reflex log exists
ls -la .empirica_reflex_logs/2025-11-13/minimax_test/<session_id>/reflex_frame_check.json

# 3. Verify content
cat .empirica_reflex_logs/2025-11-13/minimax_test/<session_id>/reflex_frame_check.json | jq '.vectors'
```

**Expected:**
- Database has `check_id` and `decision`
- File exists: `reflex_frame_check.json`
- File contains vectors

**NOTE:** `check_phase_assessments` table doesn't have `reflex_log_path` column (known minor gap)

✅ **PASS** / ❌ **FAIL**: ___________

---

### Test 4: POSTFLIGHT Assessment

**Step 4a: Execute POSTFLIGHT**
```json
{
  "tool": "execute_postflight",
  "arguments": {
    "session_id": "<session_id>",
    "task_summary": "Completed code analysis task"
  }
}
```

**Expected Response:**
```json
{
  "ok": true,
  "phase": "postflight",
  "self_assessment_prompt": "Reassess your epistemic state...",
  "calibration_note": "System will calculate epistemic delta"
}
```

**Step 4b: Submit POSTFLIGHT**
```json
{
  "tool": "submit_postflight_assessment",
  "arguments": {
    "session_id": "<session_id>",
    "vectors": {
      "engagement": 0.9,
      "know": 0.8,
      "do": 0.8,
      "context": 0.7,
      "clarity": 0.9,
      "coherence": 0.9,
      "signal": 0.8,
      "density": 0.7,
      "state": 0.7,
      "change": 0.8,
      "completion": 0.9,
      "impact": 0.7,
      "uncertainty": 0.3
    },
    "changes_noticed": "Learned function structure and purpose. Uncertainty decreased from 0.5 to 0.3."
  }
}
```

**Expected Response:**
```json
{
  "ok": true,
  "message": "POSTFLIGHT assessment logged to database AND reflex logs",
  "calibration_result": {
    "calibration": "well_calibrated",
    "delta_uncertainty": -0.2,
    "postflight_confidence": 0.8
  },
  "reflex_log_path": ".empirica_reflex_logs/2025-11-13/minimax_test/<session_id>/reflex_frame_postflight.json"
}
```

**Verification:**
```bash
# 1. Check database
sqlite3 .empirica/sessions/sessions.db "SELECT assessment_id, calibration_accuracy, reflex_log_path FROM postflight_assessments WHERE session_id='<session_id>';"

# 2. Check file exists
ls -la .empirica_reflex_logs/2025-11-13/minimax_test/<session_id>/reflex_frame_postflight.json

# 3. Verify content
cat .empirica_reflex_logs/2025-11-13/minimax_test/<session_id>/reflex_frame_postflight.json | jq '.'

# 4. Verify all files created
ls -la .empirica_reflex_logs/2025-11-13/minimax_test/<session_id>/
```

**Expected:**
- Database has `assessment_id`, `calibration_accuracy`, and `reflex_log_path`
- File exists: `reflex_frame_postflight.json`
- Calibration calculated correctly
- All 3 files exist: `preflight`, `check`, `postflight`

✅ **PASS** / ❌ **FAIL**: ___________

---

### Test 5: Calibration Verification

**Query Calibration:**
```json
{
  "tool": "get_calibration_report",
  "arguments": {
    "session_id": "<session_id>"
  }
}
```

**Expected Response:**
```json
{
  "ok": true,
  "session_id": "...",
  "calibration": "well_calibrated",
  "preflight_uncertainty": 0.5,
  "postflight_uncertainty": 0.3,
  "delta_uncertainty": -0.2,
  "knowledge_delta": 0.2,
  "interpretation": "Uncertainty decreased and knowledge increased - well calibrated"
}
```

**Verification:**
```bash
# Compare PREFLIGHT vs POSTFLIGHT
sqlite3 .empirica/sessions/sessions.db <<EOF
SELECT 
  'PREFLIGHT' as phase,
  know, uncertainty 
FROM epistemic_assessments 
WHERE session_id='<session_id>';

SELECT 
  'POSTFLIGHT' as phase,
  know, uncertainty, calibration_accuracy 
FROM postflight_assessments 
WHERE session_id='<session_id>';
EOF
```

**Expected:**
- Calibration calculation matches
- Delta values correct

✅ **PASS** / ❌ **FAIL**: ___________

---

## Final Verification

### Complete Directory Structure
```bash
# Check all files created
find .empirica_reflex_logs -type f -name "*.json" | grep "<session_id>"
```

**Expected Output:**
```
.empirica_reflex_logs/2025-11-13/minimax_test/<session_id>/reflex_frame_preflight.json
.empirica_reflex_logs/2025-11-13/minimax_test/<session_id>/reflex_frame_check.json
.empirica_reflex_logs/2025-11-13/minimax_test/<session_id>/reflex_frame_postflight.json
```

### Database Integrity Check
```bash
sqlite3 .empirica/sessions/sessions.db <<EOF
.mode column
.headers on

-- Session
SELECT session_id, ai_id, created_at 
FROM sessions 
WHERE session_id='<session_id>';

-- PREFLIGHT
SELECT assessment_id, know, uncertainty, reflex_log_path 
FROM epistemic_assessments 
WHERE session_id='<session_id>';

-- CHECK
SELECT check_id, confidence, decision 
FROM check_phase_assessments 
WHERE session_id='<session_id>';

-- POSTFLIGHT
SELECT assessment_id, know, uncertainty, calibration_accuracy, reflex_log_path 
FROM postflight_assessments 
WHERE session_id='<session_id>';
EOF
```

**Expected:**
- All tables have data
- `reflex_log_path` populated for PREFLIGHT and POSTFLIGHT
- Calibration calculated

✅ **PASS** / ❌ **FAIL**: ___________

---

## Test Results Summary

**Test 1 - Bootstrap:** ________ (PASS/FAIL)  
**Test 2 - PREFLIGHT:** ________ (PASS/FAIL)  
**Test 3 - CHECK:** ________ (PASS/FAIL)  
**Test 4 - POSTFLIGHT:** ________ (PASS/FAIL)  
**Test 5 - Calibration:** ________ (PASS/FAIL)  
**Final Verification:** ________ (PASS/FAIL)

**Overall Status:** ________ (PASS/FAIL)

---

## Issue Reporting Template

**If any test fails, report:**

```markdown
## Test Failure Report

**Test:** [Test number and name]

**Expected:**
[What should have happened]

**Actual:**
[What actually happened]

**Error Message:**
[Copy full error message]

**Verification Commands Run:**
[Commands you ran to verify]

**Files Created:**
[List files that were/weren't created]

**Database State:**
[Output of database queries]

**Request:** [What you need from Claude]
```

---

## Success Criteria

**All tests pass when:**
1. ✅ Session created in database
2. ✅ PREFLIGHT assessment in database + reflex log
3. ✅ CHECK assessment in database + reflex log
4. ✅ POSTFLIGHT assessment in database + reflex log
5. ✅ Calibration calculated correctly
6. ✅ All 3 reflex log files exist at correct paths
7. ✅ Database `reflex_log_path` columns populated

**If all criteria met:** Report success + move to next phase (profile system testing)

---

**Ready to Execute:** Yes ✅  
**Estimated Time:** 10-15 minutes  
**Next Phase:** Profile system implementation (Phase 2)
