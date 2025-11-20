# Mini-agent Task: P2 Goal Management + Session Features Validation

**Assigned to:** Mini-agent (Minimax)
**Priority:** P2 (Important - Nice to have working)
**Estimated:** 2-3 hours
**Status:** Ready to start

---

## 🎯 Mission

Validate that **Goal Management** and **Session Management** features work correctly through MCP v2 + CLI. These are important but not blocking for initial release.

---

## 📋 Your Testing Scope (P2)

### 1. Goal Management Workflow (Most Important for P2)

**Test complete goal lifecycle:**

```bash
# Create test script: test_goal_management.py
```

**Required flow to test:**
1. `bootstrap_session` (ai_id="mini-agent-p2", bootstrap_level=2)
2. `create_goal` (session_id, objective="Test goal management", scope="session_scoped")
3. `add_subtask` (goal_id, description="Subtask 1 - Test creation")
4. `add_subtask` (goal_id, description="Subtask 2 - Test progress tracking")
5. `add_subtask` (goal_id, description="Subtask 3 - Test completion")
6. `complete_subtask` (subtask_id for task 1, evidence="Tested successfully")
7. `get_goal_progress` (goal_id) - Should show 1/3 complete
8. `complete_subtask` (subtask_id for task 2, evidence="Progress tracking works")
9. `get_goal_progress` (goal_id) - Should show 2/3 complete
10. `list_goals` (session_id) - Should show the goal
11. `complete_subtask` (subtask_id for task 3, evidence="All features work")
12. `get_goal_progress` (goal_id) - Should show 3/3 complete (100%)

**Success criteria:**
- ✅ Goal creation succeeds and returns goal_id
- ✅ Subtasks can be added to goal
- ✅ Subtask completion updates progress
- ✅ Progress tracking shows correct percentages (33%, 67%, 100%)
- ✅ list_goals shows all goals for session
- ✅ All operations persist to database

**Test data:**
```python
goal_data = {
    "objective": "Validate goal management system end-to-end",
    "scope": "session_scoped",  # or "project_scoped", "task_specific"
    "success_criteria": ["Creation works", "Subtasks tracked", "Progress accurate"],
    "estimated_complexity": 0.5  # Low complexity test
}

subtask_1 = {
    "description": "Test goal creation via MCP",
    "epistemic_importance": "critical",  # or "high", "medium", "low"
    "estimated_tokens": 500
}

subtask_2 = {
    "description": "Test subtask addition and tracking",
    "epistemic_importance": "high",
    "estimated_tokens": 800
}

subtask_3 = {
    "description": "Test completion and progress calculation",
    "epistemic_importance": "high",
    "estimated_tokens": 600
}
```

---

### 2. Session Management Features

**Test session querying and resumption:**

**Required tests:**

1. **Get Epistemic State:**
   ```python
   get_epistemic_state(session_id)
   # Should return current vectors, phase, completion state
   ```

2. **Get Session Summary:**
   ```python
   get_session_summary(session_id)
   # Should return full session details, history, goals
   ```

3. **Get Calibration Report:**
   ```python
   # First complete a CASCADE workflow with PREFLIGHT and POSTFLIGHT
   get_calibration_report(session_id)
   # Should show PREFLIGHT vs POSTFLIGHT delta, calibration accuracy
   ```

4. **Resume Previous Session:**
   ```python
   resume_previous_session(ai_id="mini-agent-p2", count=1)
   # Should return the session you just created
   ```

**Success criteria:**
- ✅ Epistemic state shows correct current state
- ✅ Session summary includes all details
- ✅ Calibration report shows learning delta
- ✅ Resume returns correct session(s)
- ✅ All JSON output is well-formatted

---

### 3. Multi-Goal Testing

**Test handling multiple goals in one session:**

**Required tests:**
1. Create 3 goals in same session:
   - Goal 1: "Test multi-goal support" (2 subtasks)
   - Goal 2: "Verify goal isolation" (3 subtasks)
   - Goal 3: "Check list_goals output" (1 subtask)

2. Complete subtasks across different goals

3. Verify:
   - `list_goals` shows all 3 goals
   - Progress tracking works per-goal (not mixed)
   - Goals are properly isolated

**Success criteria:**
- ✅ Multiple goals can coexist in one session
- ✅ Subtasks belong to correct goals
- ✅ Progress is tracked independently per goal
- ✅ list_goals output is clear and organized

---

### 4. Goal Adoption Testing (Multi-Agent)

**Test adopting goals created by other AIs:**

**Required tests:**
1. Create a goal as "mini-agent-p2"
2. Have a second session/AI adopt the goal:
   ```python
   # Via Python API (since MCP doesn't have adopt_goal tool yet)
   from empirica.core.goals.repository import GoalRepository

   repo = GoalRepository()
   goal = repo.get_goal(goal_id_from_miniagent)

   # Adopt into new session
   success = repo.save_goal(goal, new_session_id)
   repo.close()
   ```
3. Verify both sessions can see the goal
4. Verify progress updates from either session

**Success criteria:**
- ✅ Goals can be retrieved by ID
- ✅ Goals can be adopted into new sessions
- ✅ Multi-agent collaboration works
- ✅ Progress tracking works across sessions

---

## 🔧 How to Test

### Setup

1. **Bootstrap your test session:**
   ```python
   # Use MCP tool or Python API
   from empirica.bootstraps.optimal_metacognitive_bootstrap import bootstrap_metacognition
   from empirica.data.session_database import SessionDatabase

   config = bootstrap_metacognition("mini-agent-p2", level=2)
   db = SessionDatabase()
   session_id = db.create_session(
       ai_id="mini-agent-p2",
       bootstrap_level=2,
       components_loaded=len(config)
   )
   db.close()
   ```

2. **Test CLI commands directly first:**
   ```bash
   cd /home/yogapad/empirical-ai/empirica

   # Test goal creation
   .venv-mcp/bin/empirica goals-create \
       --session-id <id> \
       --objective "Test goal" \
       --scope session_scoped \
       --output json

   # Test subtask addition
   .venv-mcp/bin/empirica goals-add-subtask \
       --goal-id <id> \
       --description "Test subtask" \
       --output json

   # ... etc
   ```

3. **Then test via MCP protocol:**
   - Use your MCP client configuration
   - Call tools via MCP protocol
   - Verify JSON responses

---

## 📊 Deliverables

### 1. Test Results Document

Create: `P2_VALIDATION_RESULTS.md`

**Include:**
- ✅ Goal Management: Create → Add subtasks → Complete → Progress
- ✅ Session Management: State, summary, calibration, resume
- ✅ Multi-Goal: 3 goals in 1 session tested
- ✅ Goal Adoption: Cross-session goal sharing tested
- ✅ Any issues found with descriptions
- ✅ Performance metrics

**Example format:**
```markdown
# P2 Validation Results

## Goal Management Workflow
- ✅ create_goal: PASS (returned goal_id: abc123...)
- ✅ add_subtask: PASS (3 subtasks added)
- ✅ complete_subtask: PASS (marked complete, progress updated)
- ✅ get_goal_progress: PASS (33% → 67% → 100%)
- ✅ list_goals: PASS (showed all goals)

## Session Management
- ✅ get_epistemic_state: PASS (returned current vectors)
- ✅ get_session_summary: PASS (full details)
- ⚠️ get_calibration_report: NEEDS CASCADE FIRST
- ✅ resume_previous_session: PASS (found 1 session)

## Multi-Goal Testing
- ✅ Created 3 goals in 1 session
- ✅ Each tracks progress independently
- ✅ list_goals shows all clearly

## Issues Found
1. **Goals-create returns simulated goal_id (not real database ID)**
   - Severity: High
   - Impact: Can't test full workflow
   - Fix: Update CLI command to save to database
   - Status: Needs fixing
```

### 2. Code Fixes (If Needed)

Your CLI commands might be simulating responses rather than hitting the database. Check files:
- `empirica/cli/command_handlers/goal_commands.py`
- `empirica/cli/command_handlers/workflow_commands.py`

If they use "simulated-goal-id" or similar, fix them to:
1. Actually call the Python API
2. Save to database
3. Return real IDs

### 3. Epistemic Assessment

**PREFLIGHT:**
- KNOW: Familiarity with goal management system?
- DO: Confidence testing thoroughly?
- UNCERTAINTY: What's unclear about goals/sessions?

**POSTFLIGHT:**
- What did you learn about the goal architecture?
- Were there surprises?
- Calibration: Predicted vs actual difficulty?

---

## 🚨 Potential Issues to Watch For

### Issue 1: CLI commands might be simulated
**Check:** `empirica/cli/command_handlers/goal_commands.py`

Look for lines like:
```python
result = {
    "ok": True,
    "goal_id": "simulated-goal-id-" + str(hash(objective) % 10000),
    # ...
}
```

If you see "simulated", the commands aren't hitting the database!

**Fix:**
```python
from empirica.core.goals.repository import GoalRepository
from empirica.core.goals.types import Goal, GoalScope

repo = GoalRepository()

# Create real goal
goal = Goal.create(
    objective=objective,
    scope=GoalScope[scope.upper()],
    # ...
)

# Save to database with session
goal_id = repo.save_goal(goal, session_id)
repo.close()

result = {
    "ok": True,
    "goal_id": goal_id,  # Real UUID!
    # ...
}
```

### Issue 2: Subtask IDs might not persist
**Check:** If subtask_id is simulated, completion won't work

**Fix:** Use `TaskRepository` to save real subtasks to database

### Issue 3: Progress calculation might not work
**Check:** `get_goal_progress` needs real data to calculate

**Fix:** Ensure goals/subtasks are in database, then query them

---

## ✅ Success Criteria

**P2 validation is complete when:**

1. ✅ Full goal management workflow works (create → subtasks → complete → progress)
2. ✅ Session management tools return correct data
3. ✅ Multi-goal support verified (3 goals in 1 session)
4. ✅ Goal adoption tested (cross-session sharing)
5. ✅ All tests documented in P2_VALIDATION_RESULTS.md
6. ✅ Any bugs found are fixed (especially simulation → real DB)
7. ✅ Performance is good (<500ms per tool)

**When done:**
- Commit P2_VALIDATION_RESULTS.md
- Commit any code fixes to CLI commands
- Report: "P2 validation complete - Goal management verified"
- Flag any P2 issues found (not blocking release)

---

## 💡 Tips

**Testing Strategy:**
1. Test CLI commands directly first (easier debugging)
2. Check if commands use simulation vs real database
3. Fix simulation issues before testing via MCP
4. Test happy path, then edge cases

**Debugging:**
- Check database directly: `.empirica/sessions/sessions.db`
- Use Python API to verify data saved
- Check CLI command source code if behavior is unexpected
- Test with `--verbose` flag for details

**Time Management:**
- Goal management workflow: 1 hour
- Session management: 45 min
- Multi-goal testing: 30 min
- Goal adoption: 30 min
- Code fixes + documentation: 1 hour

---

**Questions?** Check:
- `empirica/core/goals/repository.py` - Goal persistence API
- `empirica/core/tasks/repository.py` - Subtask persistence API
- `MCP_V2_TESTING_STATUS.md` - Overall testing plan
- `TASK_ROVODEV_P1_MCP_VALIDATION.md` - Example from P1

**Ready to start?** Begin with goal management workflow (most important for P2).
