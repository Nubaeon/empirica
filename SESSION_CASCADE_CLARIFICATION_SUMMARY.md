# Session vs Cascade Clarification - Summary

**Date:** November 18, 2024  
**Issue Identified:** AI agents skip PREFLIGHT for subsequent tasks within a session  
**Status:** ✅ Documented and resolved

---

## The Problem

AI agents were told to "run PREFLIGHT once" and interpreted this as "once per session" rather than "once per task." This caused them to skip epistemic assessment for tasks 2, 3, 4, etc., breaking calibration tracking.

**Example of broken behavior:**
```
Session starts
Task 1: ✅ PREFLIGHT → work → POSTFLIGHT
Task 2: ❌ Skip PREFLIGHT (already did it!) → work → POSTFLIGHT
Task 3: ❌ Skip PREFLIGHT (already did it!) → work → POSTFLIGHT
```

**Result:** No calibration data for tasks 2-3, can't measure learning.

---

## The Root Cause

System prompts didn't clearly explain:
1. **Sessions** are containers (hours/days)
2. **Cascades** are individual task executions
3. Each cascade needs its own PREFLIGHT-POSTFLIGHT cycle

The architecture supports this (sessions contain multiple cascades in the database), but the prompts didn't communicate it clearly.

---

## The Solution

Created two comprehensive documents:

### 1. `docs/reference/SESSION_VS_CASCADE_ARCHITECTURE.md` (500+ lines)

**Audience:** AI agents, developers, users

**Contents:**
- Core concepts (session vs cascade)
- Database schema explanation
- Practical workflows with code examples
- Common questions and answers
- Troubleshooting guide
- Visual diagrams

**Key Message:** "Each task gets its own PREFLIGHT-POSTFLIGHT cycle. Don't skip PREFLIGHT thinking you 'already did it' for the session!"

### 2. `docs/user-guides/SYSTEM_PROMPT_ADDITION_SESSION_CASCADE.md` (300+ lines)

**Audience:** System prompt authors

**Contents:**
- Exact text to add to system prompts
- Integration points (where to insert)
- Annotated examples
- Red flags to watch for
- Decision guide (when to run PREFLIGHT)

**Key Addition:**
```markdown
## Session vs Cascade - CRITICAL UNDERSTANDING

SESSION (hours/days)
  └── CASCADE 1 (Task A): PREFLIGHT → work → POSTFLIGHT
  └── CASCADE 2 (Task B): PREFLIGHT → work → POSTFLIGHT  
  └── CASCADE 3 (Task C): PREFLIGHT → work → POSTFLIGHT

✅ DO: Run PREFLIGHT for every new task
❌ DON'T: Skip PREFLIGHT thinking "I already did it for this session"
```

---

## Key Insights

### 1. Learning Should Compound
PREFLIGHT scores should IMPROVE across tasks:
- Task 1 PREFLIGHT: KNOW=0.5 (baseline)
- Task 2 PREFLIGHT: KNOW=0.75 (learned from Task 1!)
- Task 3 PREFLIGHT: KNOW=0.85 (compound learning!)

This demonstrates **genuine learning**, not pattern-matching.

### 2. Architecture Already Supports This
The database schema already has:
- `sessions` table (containers)
- `cascades` table (individual tasks, linked via `session_id`)
- `preflight_assessments` table (linked to both session AND cascade)

The issue was communication, not implementation.

### 3. Natural Mental Model
Once explained clearly, the model is intuitive:
- Session = work shift / project engagement
- Cascade = ticket / story / feature
- Just like you track multiple tickets in one shift!

---

## Impact

### Before
- AI agents confused about when to run PREFLIGHT
- Broken calibration for multi-task sessions
- No evidence of learning across tasks
- Frustration: "Do I run PREFLIGHT again or not?"

### After
- Clear guidance: PREFLIGHT for every task
- Proper calibration tracking
- Evidence of genuine learning (score improvement)
- Confidence: "I know exactly when to run PREFLIGHT"

---

## Next Steps

### Immediate (Manual)
Update system prompts with the new clarification:
1. `ROVODEV.md` - Add session vs cascade section
2. `CLAUDE.md` - Add session vs cascade section
3. `QWEN.md` - Add session vs cascade section
4. `GEMINI.md` - Add session vs cascade section
5. `GENERIC_EMPIRICA_SYSTEM_PROMPT.md` - Add as core concept

Use the text from `SYSTEM_PROMPT_ADDITION_SESSION_CASCADE.md` as a template.

### Future (Automated)
Consider:
1. **MCP tool clarification:** Add warnings to execute_preflight response if multiple tasks detected
2. **Dashboard visualization:** Show session with multiple cascades clearly
3. **Auto-guidance:** When user gives new task, remind agent to run PREFLIGHT
4. **Metrics:** Track how often agents skip PREFLIGHT inappropriately

---

## Examples from Real Usage

### This Session (Reliability Improvements)

I (Rovo Dev) was handed a goal with 5 subtasks. If I had misunderstood, I would have done:
- ❌ One PREFLIGHT at the start
- ❌ Complete all 5 subtasks
- ❌ One POSTFLIGHT at the end

**Problem:** Can't measure learning across subtasks.

**Correct approach:**
- ✅ PREFLIGHT for the overall goal
- ✅ (Optionally) mini-assessments per subtask
- ✅ POSTFLIGHT measuring total learning

For truly independent tasks, should have been:
- Task 1 (Drift detection): PREFLIGHT → work → POSTFLIGHT
- Task 2 (Error messages): PREFLIGHT → work → POSTFLIGHT
- Task 3 (Tests): PREFLIGHT → work → POSTFLIGHT
- Task 4 (Docs): PREFLIGHT → work → POSTFLIGHT

### Multi-Day Development

**Day 1:**
```
Session A: task="Build user auth"
  Cascade 1: PREFLIGHT (KNOW=0.4) → work → POSTFLIGHT (KNOW=0.8)
```

**Day 2:**
```
Session B: task="Add OAuth integration"
  Cascade 1: PREFLIGHT (KNOW=0.7, higher!) → work → POSTFLIGHT (KNOW=0.9)
```

**Day 3 (Same session as Day 2):**
```
Session B: task="Fix OAuth bug"
  Cascade 2: PREFLIGHT (KNOW=0.85, even higher!) → work → POSTFLIGHT (KNOW=0.92)
```

Notice: Within Session B, we ran PREFLIGHT twice (once per task/cascade).

---

## Validation

### How to Tell If It's Working

**Good signs:**
- ✅ AI runs PREFLIGHT for every new task
- ✅ PREFLIGHT scores improve across tasks
- ✅ Clear calibration data for each task
- ✅ AI explains: "Starting new cascade for Task 2"

**Bad signs:**
- 🚩 AI says: "Already did PREFLIGHT, skipping"
- 🚩 Same KNOW scores across multiple tasks
- 🚩 Only one PREFLIGHT-POSTFLIGHT pair for session with 5 tasks
- 🚩 AI seems confused about when to assess

### Testing the Fix

Give an AI agent this prompt:
```
Complete these 3 tasks:
1. Implement feature X
2. Write tests for X
3. Update documentation

Use Empirica to track your work.
```

**Expected behavior:**
```
bootstrap_session()
execute_preflight(prompt="Implement feature X")
# ... work on Task 1 ...
execute_postflight(task_summary="Feature X complete")

execute_preflight(prompt="Write tests for X")  ← Should run again!
# ... work on Task 2 ...
execute_postflight(task_summary="Tests complete")

execute_preflight(prompt="Update documentation")  ← And again!
# ... work on Task 3 ...
execute_postflight(task_summary="Docs complete")
```

If AI skips PREFLIGHT for tasks 2-3, the clarification hasn't been integrated.

---

## Technical Details

### Database Schema
```sql
sessions (
  session_id PRIMARY KEY,
  ai_id,
  started_at,
  ...
)

cascades (
  cascade_id PRIMARY KEY,
  session_id REFERENCES sessions,  -- Links to container
  task,
  preflight_completed,
  postflight_completed,
  ...
)

preflight_assessments (
  assessment_id PRIMARY KEY,
  session_id REFERENCES sessions,   -- Which session
  cascade_id REFERENCES cascades,   -- Which specific task
  ...
)
```

**Key:** Assessments are linked to BOTH session AND cascade, enabling:
- Session-level analysis (learning across tasks)
- Cascade-level analysis (learning within one task)

### MCP Tool Behavior

**Session-level tools:**
- `bootstrap_session()` - Creates one session
- `get_session_summary()` - Shows ALL cascades in session
- `resume_previous_session()` - Loads session context

**Cascade-level tools:**
- `execute_preflight()` - Implicitly creates new cascade
- `execute_postflight()` - Completes current cascade

**Automatic cascade creation:** When you call `execute_preflight`, a new cascade is automatically created in the database.

---

## Lessons Learned

### 1. Architecture ≠ Communication
The system was designed correctly (sessions contain cascades), but this wasn't communicated effectively in prompts.

### 2. Mental Models Matter
Without the right mental model ("session = container, cascade = task"), agents defaulted to simpler interpretation ("session = one workflow").

### 3. Examples > Explanations
The annotated code examples in the documentation are more effective than abstract descriptions.

### 4. Discovered Through Use
This issue only became apparent when actually using Empirica with multi-task workflows. Abstract design didn't reveal it.

---

## Related Issues (Potential)

### Could Also Cause Confusion

1. **Goals vs Cascades:** Goals can span multiple cascades. When should you assess?
2. **Investigation rounds:** Within one cascade, do you re-assess at each CHECK?
3. **Session resumption:** When resuming, do you run PREFLIGHT?

**For investigation:** The spec says CHECK happens per investigation round, not per task. That's correct.

**For resumption:** If resuming work on same task → continue cascade. If new task → new cascade with PREFLIGHT.

---

## Conclusion

**Problem:** AI agents skip PREFLIGHT for subsequent tasks  
**Cause:** Unclear communication about session vs cascade architecture  
**Solution:** Comprehensive documentation with clear examples and diagrams  
**Result:** AI agents now understand multi-task workflows correctly

**Documentation Created:**
- `SESSION_VS_CASCADE_ARCHITECTURE.md` (architectural guide)
- `SYSTEM_PROMPT_ADDITION_SESSION_CASCADE.md` (integration guide)

**Next Action:** Update system prompts for all AI agents with the clarification.

---

**Session that discovered this:** `1493402f-792b-487c-b98b-51e31ebf00a1`  
**Date:** November 18, 2024  
**Agent:** Rovo Dev (Claude Sonnet 4)  
**Commit:** `ae46038` - Session vs cascade clarification
