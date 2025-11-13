# Empirica MCP Server Validation & Testing Guide

**Date:** 2025-11-01  
**Servers:** `empirica_mcp_server.py`, `empirica_tmux_mcp_server.py`  
**Status:** Ready for systematic testing

---

## 📊 Quick Status

### Session Database
- ✅ **Automatic tracking enabled** via bootstrap
- ✅ **45 sessions** currently in database
- ✅ Tracks: sessions, cascades, preflight/postflight assessments
- ✅ Location: `empirica/.empirica/sessions/sessions.db`

### MCP Servers
- ✅ **empirica_mcp_server.py** - 1,222 lines, 9+ tools
- ✅ **empirica_tmux_mcp_server.py** - 497 lines, TMUX integration
- ⚠️ **Testing needed** - No systematic validation yet

---

## 🛠️ MCP Tools Implemented

### Core Workflow Tools (6)

1. **`execute_preflight`** ✅
   - Returns self-assessment prompt for AI
   - Phase: PREFLIGHT (baseline epistemic state)
   - Input: `session_id`, `prompt`
   - Output: Assessment prompt + assessment_id

2. **`submit_preflight_assessment`** ✅
   - Logs AI's self-assessment scores
   - Stores 13 vector scores + reasoning
   - Creates cascade in database
   - Input: `session_id`, `vectors` (13 scores), `reasoning`

3. **`execute_check`** ✅
   - CHECK phase after investigation
   - Determines if ready to proceed or need more investigation
   - Input: `session_id`, `findings`, `remaining_unknowns`, `confidence_to_proceed`

4. **`execute_postflight`** ✅
   - Final epistemic reassessment after task completion
   - For calibration validation
   - Input: `session_id`, `task_summary`

5. **`submit_postflight_assessment`** ✅
   - Logs final self-assessment
   - Calculates epistemic delta (PREFLIGHT → POSTFLIGHT)
   - Validates calibration accuracy
   - Input: `session_id`, `vectors`, `changes_noticed`

6. **`resume_previous_session`** ✅
   - Load summary of previous session(s)
   - Supports: last session, last N, specific session_id
   - Detail levels: summary, detailed, full
   - Input: `ai_id`, `resume_mode`, `count`, `session_id`, `detail_level`

### Session Management Tools (3)

7. **`get_epistemic_state`** ✅
   - Query current session vectors
   - Returns assessment history from reflex logs
   - Input: `session_id`

8. **`get_calibration_report`** ✅
   - Compare CHECK confidence vs POSTFLIGHT results
   - Calibration accuracy statistics
   - Input: `session_id`

9. **`get_session_summary`** ✅
   - Complete session summary
   - All workflow phases and assessments
   - Input: `session_id`

### Monitoring Tools (3)

10. **`query_bayesian_beliefs`** ✅
    - Bayesian Guardian belief states
    - Detect calibration discrepancies
    - Input: `session_id`, `context_key` (optional)

11. **`check_drift_monitor`** ✅
    - Analyze for sycophancy drift
    - Tension avoidance pattern detection
    - Input: `session_id`, `window_size` (default: 5)

12. **`query_goal_orchestrator`** ✅
    - Current goals, progress, task hierarchy
    - Input: `session_id`

### Bootstrap Tool (1)

13. **`bootstrap_session`** ✅
    - Bootstrap new Empirica session
    - Optimal metacognitive configuration
    - Input: `ai_id`, `session_type` (development/production/testing)

---

## 🧪 Testing Protocol

### Phase 1: Basic Functionality

**Test 1.1: Session Creation**
```python
# Via bootstrap (automatic)
from empirica.bootstraps.optimal_metacognitive_bootstrap import OptimalMetacognitiveBootstrap
bootstrap = OptimalMetacognitiveBootstrap(ai_id="test-mcp", level="minimal")
components = bootstrap.bootstrap()

# Verify session created
from empirica.data.session_database import SessionDatabase
db = SessionDatabase()
cursor = db.conn.cursor()
cursor.execute("SELECT COUNT(*) FROM sessions WHERE ai_id='test-mcp'")
count = cursor.fetchone()[0]
assert count > 0, "Session should be created"
```

**Test 1.2: PREFLIGHT → Submit Flow**
```bash
# Step 1: Execute preflight (via MCP)
# Tool: execute_preflight
# Input: {"session_id": "test-123", "prompt": "Write a function"}
# Expect: Self-assessment prompt returned

# Step 2: Submit assessment (via MCP)
# Tool: submit_preflight_assessment
# Input: {
#   "session_id": "test-123",
#   "vectors": {
#     "know": 0.7, "do": 0.8, "context": 0.75,
#     "clarity": 0.85, "coherence": 0.9, "signal": 0.8, "density": 0.4,
#     "state": 0.6, "change": 0.5, "completion": 0.3, "impact": 0.7,
#     "engagement": 0.8, "uncertainty": 0.5
#   },
#   "reasoning": "Clear task, have experience with similar functions"
# }
# Expect: Cascade created, vectors logged
```

**Test 1.3: Delta Calculation**
```python
# After submitting both PREFLIGHT and POSTFLIGHT
# Verify delta is calculated and non-zero

from empirica.data.session_database import SessionDatabase
db = SessionDatabase()

# Query PREFLIGHT vectors
cursor = db.conn.cursor()
cursor.execute("""
    SELECT metadata_value FROM cascade_metadata
    WHERE metadata_key = 'preflight_vectors'
    ORDER BY cascade_id DESC LIMIT 1
""")
preflight = cursor.fetchone()

# Query POSTFLIGHT vectors  
cursor.execute("""
    SELECT metadata_value FROM cascade_metadata
    WHERE metadata_key = 'postflight_vectors'
    ORDER BY cascade_id DESC LIMIT 1
""")
postflight = cursor.fetchone()

# Verify both exist and delta calculated
assert preflight is not None
assert postflight is not None
```

### Phase 2: Workflow Integration

**Test 2.1: Full Cascade via Extended Bootstrap**
```bash
python3 empirica/bootstraps/extended_metacognitive_bootstrap.py \
  --level complete \
  --ai-id test-cascade-mcp

# Verify:
# - Session created in DB
# - Preflight assessment exists
# - Investigation rounds recorded
# - Postflight assessment exists
# - Delta calculated correctly (non-zero)
```

**Test 2.2: Resume Previous Session**
```python
# Via MCP tool
# Tool: resume_previous_session
# Input: {
#   "ai_id": "claude",
#   "resume_mode": "last",
#   "detail_level": "summary"
# }
# Expect: Summary of last session with epistemic trajectory
```

### Phase 3: Calibration Validation

**Test 3.1: Well-Calibrated Scenario**
```
PREFLIGHT: overall_confidence = 0.60
After 3 investigation rounds
POSTFLIGHT: overall_confidence = 0.75
Delta: +0.15

Expected: "✅ Well-Calibrated: Confidence matched learning"
```

**Test 3.2: Overconfident Scenario**
```
PREFLIGHT: overall_confidence = 0.85 (high confidence)
After 3 investigation rounds (discovered many unknowns)
POSTFLIGHT: overall_confidence = 0.70 (lower)
Delta: -0.15

Expected: "⚠️ Calibration Warning: Overconfident - discovered unknowns"
```

### Phase 4: Monitoring Tools

**Test 4.1: Bayesian Guardian**
```python
# Tool: query_bayesian_beliefs
# Input: {"session_id": "test-123"}
# Expect: Belief states, calibration scores
```

**Test 4.2: Drift Monitor**
```python
# Tool: check_drift_monitor
# Input: {"session_id": "test-123", "window_size": 5}
# Expect: Sycophancy/tension analysis over last 5 turns
```

---

## 📝 Test Checklist

### Session Database Tests
- [ ] Session automatically created on bootstrap
- [ ] PREFLIGHT vectors stored in cascade_metadata
- [ ] POSTFLIGHT vectors stored in cascade_metadata
- [ ] Epistemic delta calculated correctly
- [ ] Calibration validation works
- [ ] Resume previous session returns data
- [ ] Multiple sessions don't interfere

### MCP Server Tests
- [ ] `execute_preflight` returns valid prompt
- [ ] `submit_preflight_assessment` logs to DB
- [ ] `execute_postflight` returns valid prompt
- [ ] `submit_postflight_assessment` calculates delta
- [ ] `resume_previous_session` loads last session
- [ ] `get_session_summary` returns complete data
- [ ] `query_bayesian_beliefs` works (if enabled)
- [ ] `check_drift_monitor` works (if enabled)
- [ ] `bootstrap_session` creates new session

### Integration Tests
- [ ] Full cascade with MCP tools (PREFLIGHT → ACT → POSTFLIGHT)
- [ ] Delta shows realistic learning (+0.10 to +0.20 typical)
- [ ] Uncertainty decreases after investigation (negative delta)
- [ ] Calibration check matches expectations
- [ ] Resume works across sessions
- [ ] TMUX integration (if applicable)

---

## 🔧 Validation Commands

### Check Database Status
```bash
cd /home/yogapad/empirical-ai/empirica
python3 -c "
from empirica.data.session_database import SessionDatabase
db = SessionDatabase()
cursor = db.conn.cursor()
cursor.execute('SELECT COUNT(*) FROM sessions')
print(f'Sessions: {cursor.fetchone()[0]}')
cursor.execute('SELECT COUNT(*) FROM cascades')
print(f'Cascades: {cursor.fetchone()[0]}')
"
```

### Test Bootstrap Auto-Tracking
```bash
python3 empirica/bootstraps/optimal_metacognitive_bootstrap.py \
  --level minimal \
  --ai-id test-auto-track

# Check if session was created
python3 -c "
from empirica.data.session_database import SessionDatabase
db = SessionDatabase()
cursor = db.conn.cursor()
cursor.execute(\"SELECT * FROM sessions WHERE ai_id='test-auto-track' ORDER BY start_time DESC LIMIT 1\")
print(cursor.fetchone())
"
```

### Test MCP Server Startup
```bash
cd /home/yogapad/empirical-ai/empirica/mcp_local
python3 empirica_mcp_server.py
# Should start without errors
# Use Ctrl+C to stop
```

### Test MCP Tool Call (Manual)
```python
# Via Python REPL
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent))

from mcp_local.empirica_mcp_server import call_tool

# Test execute_preflight
result = asyncio.run(call_tool(
    "execute_preflight",
    {"session_id": "test-manual", "prompt": "Test task"}
))
print(result[0].text)
```

---

## 🎯 Success Criteria

### Minimum Viable (MVP)
- ✅ Sessions auto-created on bootstrap
- ✅ PREFLIGHT/POSTFLIGHT tools work
- ✅ Delta calculation shows learning
- ✅ Resume previous session functional

### Production Ready
- ✅ All 13 tools tested and working
- ✅ Calibration validation accurate
- ✅ No data loss between sessions
- ✅ Error handling robust
- ✅ Documentation complete

### Optimal
- ✅ TMUX integration working
- ✅ Bayesian Guardian active
- ✅ Drift Monitor detecting patterns
- ✅ Real-time dashboard updates
- ✅ Multi-AI collaboration tested

---

## 🚀 Next Steps

1. **Systematic Tool Testing**
   - Test each MCP tool individually
   - Verify input/output schemas
   - Check error handling

2. **Integration Testing**
   - Full workflow: PREFLIGHT → ACT → POSTFLIGHT
   - Multi-session continuity
   - Calibration validation

3. **Performance Testing**
   - Response times for each tool
   - Database query performance
   - Large session history handling

4. **Documentation**
   - Update skills docs with MCP tool usage
   - Create quick reference for each tool
   - Add troubleshooting guide

---

## 📚 Related Documentation

- **MCP Server Code:** `mcp_local/empirica_mcp_server.py`
- **TMUX Server Code:** `mcp_local/empirica_tmux_mcp_server.py`
- **Session Database:** `empirica/data/session_database.py`
- **Skills Guide:** `docs/empirica_skills/CLAUDE_SKILLS_EMPIRICA_v1_UPDATED.md`
- **Production Docs:** `docs/production/12_MCP_INTEGRATION.md`

---

**Status:** ✅ Ready for systematic testing  
**Recommendation:** Hand off to dedicated testing AI for comprehensive validation
