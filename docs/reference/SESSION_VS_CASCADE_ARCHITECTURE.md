# Session vs Cascade Architecture - Multi-Task Workflow Guide

**Issue:** System prompts tell you to run PREFLIGHT once per session, but what about multiple tasks in the same session?

**Answer:** One session contains **multiple cascades**. Each task gets its own PREFLIGHT-POSTFLIGHT cycle.

---

## Core Concepts

### Session
- **Scope:** Long-lived container (hours/days/weeks)
- **Contains:** Multiple cascades (tasks)
- **Purpose:** Track overall learning and epistemic evolution
- **Lifecycle:** Bootstrap → Multiple tasks → Eventually ends
- **Analogy:** A work shift or project engagement

### Cascade
- **Scope:** Single task execution
- **Contains:** Complete workflow (PREFLIGHT → INVESTIGATE → CHECK → ACT → POSTFLIGHT)
- **Purpose:** Track epistemic state for ONE specific task
- **Lifecycle:** User gives task → Complete workflow → Task done
- **Analogy:** One ticket, one story, one feature

---

## The Confusion

### ❌ Wrong Mental Model
```
Session = One PREFLIGHT → Do all work → One POSTFLIGHT
```

This makes you think: "I already did PREFLIGHT, I can't do it again!"

### ✅ Correct Mental Model
```
Session {
  Cascade 1: PREFLIGHT → Task A → POSTFLIGHT
  Cascade 2: PREFLIGHT → Task B → POSTFLIGHT  
  Cascade 3: PREFLIGHT → Task C → POSTFLIGHT
  ...
}
```

**Each task gets its own complete epistemic cycle.**

---

## CASCADE Granularity Guidelines

### When to Use Full PREFLIGHT → POSTFLIGHT Cycle

**Use full CASCADE for:**
- ✅ **Significant tasks**: Features, bug fixes, refactoring, investigations
- ✅ **High uncertainty**: Initial uncertainty >0.5
- ✅ **Learning expected**: Exploring new domains, APIs, patterns
- ✅ **Long tasks**: Expected duration >30 minutes
- ✅ **Multiple goals/subtasks**: One CASCADE can contain many goals

### When to Skip Formal CASCADE

**Skip for:**
- ⚠️ **Quick clarifications**: "What does X mean?"
- ⚠️ **Trivial edits**: "Fix typo on line 42"
- ⚠️ **Simple queries**: "Show me the logs"
- ⚠️ **Follow-up questions**: Within active CASCADE
- ⚠️ **Low uncertainty**: Already know how to proceed (<0.3)

### Examples

**✅ Good CASCADE Usage:**
```
Session {
  CASCADE 1: "Implement OAuth authentication"
    PREFLIGHT (uncertainty: 0.7)
    INVESTIGATE: Research OAuth flows, create 3 goals, add 8 subtasks
    CHECK: Ready to implement? (confidence: 0.8)
    ACT: Implement, test, document
    POSTFLIGHT (uncertainty: 0.2) → learned significantly
    
  Lightweight interactions (no formal CASCADE):
    "What's the token expiry?" → just answer
    "Show me the flow diagram" → just show
    "Fix this lint error" → just fix
    
  CASCADE 2: "Add rate limiting"
    PREFLIGHT (can reuse OAuth knowledge!)
    ... continue pattern
}
```

**❌ Bad CASCADE Usage (over-formalization):**
```
Session {
  CASCADE 1: "What does this function do?" ← Too trivial for full cycle
  CASCADE 2: "Fix typo" ← Too simple
  CASCADE 3: "Show logs" ← Just a query
}
```

### Key Principles

1. **CASCADE = Significant Task**: Not per-interaction, per-significant-task
2. **Multiple Goals per CASCADE**: One task can have many goals/subtasks
3. **Epistemic Snapshots**: Each CASCADE generates one handoff report (~800 tokens)
4. **Natural Flow**: Work uninterrupted within CASCADE, assess at boundaries

---

## Architecture Details

### Database Schema
```sql
sessions (
  session_id,
  ai_id,
  started_at,
  ...
)

cascades (
  cascade_id,
  session_id,  -- Links cascade to session
  task,
  preflight_completed,
  postflight_completed,
  ...
)

preflight_assessments (
  assessment_id,
  session_id,   -- Which session
  cascade_id,   -- Which specific task
  ...
)
```

**Key Insight:** Assessments are linked to BOTH session AND cascade.

### Why This Design?

1. **Session-level learning:** Track how you improve across tasks
2. **Task-level accuracy:** Measure each task independently
3. **Calibration data:** Compare PREFLIGHT vs POSTFLIGHT per task
4. **Long-term memory:** Resume sessions, carry forward learnings

---

## Practical Workflow

### Scenario: You have 3 tasks to complete

#### Step 1: Bootstrap Session (Once)
```python
bootstrap_session(
    ai_id="rovodev",
    session_type="development",
    bootstrap_level=2
)
# Returns: session_id = "abc123..."
```

#### Step 2: Task 1 - Complete Cascade
```python
# PREFLIGHT for Task 1
execute_preflight(
    session_id="abc123",
    prompt="Implement drift detection in CHECK phase"
)
submit_preflight_assessment(session_id="abc123", vectors={...})

# ... do the work (INVESTIGATE, CHECK, ACT) ...

# POSTFLIGHT for Task 1
execute_postflight(
    session_id="abc123",
    task_summary="Implemented drift detection with 3-tier severity"
)
submit_postflight_assessment(session_id="abc123", vectors={...})
```

#### Step 3: Task 2 - NEW Cascade (Same Session!)
```python
# PREFLIGHT for Task 2 (YES, do it again!)
execute_preflight(
    session_id="abc123",  # SAME SESSION
    prompt="Add error response helper function"
)
submit_preflight_assessment(session_id="abc123", vectors={...})

# ... do the work ...

# POSTFLIGHT for Task 2
execute_postflight(
    session_id="abc123",
    task_summary="Created error helper with 5 error types"
)
submit_postflight_assessment(session_id="abc123", vectors={...})
```

#### Step 4: Task 3 - ANOTHER Cascade
```python
# Repeat the same pattern for Task 3
execute_preflight(session_id="abc123", prompt="Task 3...")
# ... work ...
execute_postflight(session_id="abc123", task_summary="Task 3 done")
```

---

## How Cascades Are Created

### Automatic Creation
When you call `execute_preflight`, the system automatically creates a cascade:

```python
# In session_database.py
cascade_id = db.create_cascade(
    session_id=session_id,
    task=prompt,  # From execute_preflight
    context={"phase": "preflight"}
)
```

### Manual Creation (Advanced)
You can also create cascades explicitly:

```python
cascade_id = db.create_cascade(
    session_id="abc123",
    task="Fix bug #42",
    context={"bug_id": 42, "priority": "high"}
)
```

---

## Common Questions

### Q: When should I start a new session vs new cascade?

**New Cascade (Same Session):**
- ✅ Working on different tasks in the same sitting
- ✅ Related tasks in the same project
- ✅ Want to track learning across tasks
- ✅ Same day, same context

**New Session:**
- ✅ Different day (after sleep/break)
- ✅ Different project or context
- ✅ Want fresh epistemic baseline
- ✅ Previous session ended cleanly

### Q: How do I know which cascade I'm in?

Check your most recent PREFLIGHT:
```python
get_session_summary(session_id="abc123")
# Shows all cascades and their completion status
```

### Q: Can I have multiple incomplete cascades?

Yes! The architecture supports concurrent cascades. This is useful for:
- Multi-tasking
- Interrupted work (return to unfinished cascade)
- Delegating subtasks

### Q: What if I forget to do POSTFLIGHT?

The cascade remains incomplete in the database. You can:
1. Complete it later with `execute_postflight`
2. Start a new cascade (old one stays incomplete)
3. Query incomplete cascades: `db.get_session_cascades(session_id)`

### Q: Does PREFLIGHT change across cascades in the same session?

**It should!** That's the point of calibration:

**Cascade 1:**
- PREFLIGHT: KNOW=0.5, UNCERTAINTY=0.7
- POSTFLIGHT: KNOW=0.8, UNCERTAINTY=0.3
- Learning: You learned a lot!

**Cascade 2 (same session):**
- PREFLIGHT: KNOW=0.75, UNCERTAINTY=0.4  
  *(Higher because you learned from Cascade 1!)*
- POSTFLIGHT: KNOW=0.85, UNCERTAINTY=0.25
- Learning: Incremental improvement

This demonstrates **genuine learning across tasks**.

---

## System Prompt Guidance

### For AI Agents

**❌ Don't Think:**
"I already did PREFLIGHT for this session, I'm done with that."

**✅ Do Think:**
"Each new task needs its own PREFLIGHT-POSTFLIGHT cycle. The session is just the container."

### Key Rules

1. **One session, many cascades**
2. **Each task = new cascade = new PREFLIGHT-POSTFLIGHT**
3. **PREFLIGHT should improve across cascades** (shows learning)
4. **Session ends when you're done for the day/project**

---

## MCP Tools Pattern

### Session Tools (Once per session)
- `bootstrap_session()` - Start session
- `get_session_summary()` - Review all cascades
- `resume_previous_session()` - Continue from before

### Cascade Tools (Once per task)
- `execute_preflight()` - Start new cascade
- `submit_preflight_assessment()`
- `execute_check()` - During cascade
- `submit_check_assessment()`
- `execute_postflight()` - End cascade
- `submit_postflight_assessment()`

### Pattern Recognition
If a tool mentions "session" → use once  
If a tool mentions "assessment" → use per cascade/task

---

## Database Queries

### See All Cascades in Session
```python
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()
cascades = db.get_session_cascades("abc123")

for c in cascades:
    print(f"Task: {c['task']}")
    print(f"  PREFLIGHT: {c['preflight_completed']}")
    print(f"  POSTFLIGHT: {c['postflight_completed']}")
    print(f"  Duration: {c['duration_ms']}ms")
```

### Get Current Cascade
```python
cascades = db.get_session_cascades("abc123")
incomplete = [c for c in cascades if not c['postflight_completed']]

if incomplete:
    current = incomplete[0]
    print(f"Currently working on: {current['task']}")
```

---

## Example: Real Session with 3 Tasks

```python
# Day 1, Morning: Start session
session_id = bootstrap_session(ai_id="rovodev", ...)["session_id"]

# Task 1: Drift detection (Cascade 1)
execute_preflight(session_id, prompt="Add drift detection")
# KNOW=0.6, UNCERTAINTY=0.7 (baseline)
# ... work ...
execute_postflight(session_id, task_summary="Drift detection done")
# KNOW=0.85, UNCERTAINTY=0.3 (learned a lot!)

# Task 2: Error helper (Cascade 2)
execute_preflight(session_id, prompt="Add error response helper")
# KNOW=0.75, UNCERTAINTY=0.5 (already know more from Task 1!)
# ... work ...
execute_postflight(session_id, task_summary="Error helper done")
# KNOW=0.88, UNCERTAINTY=0.25 (incremental learning)

# Task 3: Fix tests (Cascade 3)
execute_preflight(session_id, prompt="Fix test mock imports")
# KNOW=0.8, UNCERTAINTY=0.4 (confidence building!)
# ... work ...
execute_postflight(session_id, task_summary="All tests passing")
# KNOW=0.9, UNCERTAINTY=0.2 (mastery achieved)

# Session summary shows learning trajectory across all 3 cascades
get_session_summary(session_id)
```

**Result:** Clear evidence of learning across tasks within the session!

---

## Implementation in System Prompts

### Add This Section

```markdown
## Session vs Cascade

**Critical Understanding:**
- **Session:** Container for multiple tasks (lasts hours/days)
- **Cascade:** Single task execution (PREFLIGHT → work → POSTFLIGHT)

**Each task needs its own PREFLIGHT-POSTFLIGHT cycle.**

**Workflow:**
1. Bootstrap session (once)
2. For each new task:
   - Execute PREFLIGHT (assess what you know about THIS task)
   - Do the work (INVESTIGATE, CHECK, ACT)
   - Execute POSTFLIGHT (measure learning for THIS task)
3. Repeat step 2 for all tasks
4. End session when done for the day

**Your PREFLIGHT should improve across tasks** - this proves genuine learning!

**Example:**
- Task 1 PREFLIGHT: KNOW=0.5 (baseline)
- Task 1 POSTFLIGHT: KNOW=0.8 (learned!)
- Task 2 PREFLIGHT: KNOW=0.75 (carried forward!)
- Task 2 POSTFLIGHT: KNOW=0.85 (incremental)

Don't skip PREFLIGHT thinking "I already did it" - each task needs assessment!
```

---

## Troubleshooting

### "I did PREFLIGHT once, now what?"

You're thinking of session-level PREFLIGHT. You need **task-level** PREFLIGHT.

**Fix:** For each new task, call `execute_preflight` again.

### "My PREFLIGHT scores don't change across tasks"

This suggests:
- Not learning from previous tasks
- Copy-pasting assessments
- Not genuinely assessing for each task

**Fix:** Honestly assess what you NOW know (after previous tasks).

### "I have 5 incomplete cascades"

You started tasks but didn't finish them.

**Fix:**
1. Query: `db.get_session_cascades(session_id)`
2. Complete or abandon each cascade
3. Start fresh cascade for new work

---

## Visual Summary

```
SESSION (Long-lived container)
├── CASCADE 1 (Task A)
│   ├── PREFLIGHT: baseline=0.5
│   ├── INVESTIGATE
│   ├── CHECK
│   ├── ACT
│   └── POSTFLIGHT: learned=0.8
│
├── CASCADE 2 (Task B) 
│   ├── PREFLIGHT: improved=0.75 (learned from Task A!)
│   ├── INVESTIGATE
│   ├── CHECK
│   ├── ACT
│   └── POSTFLIGHT: mastery=0.85
│
└── CASCADE 3 (Task C)
    ├── PREFLIGHT: confident=0.8
    ├── INVESTIGATE
    ├── CHECK
    ├── ACT
    └── POSTFLIGHT: expert=0.9

Result: Clear learning trajectory from 0.5 → 0.9!
```

---

## Conclusion

**The Big Picture:**
- Sessions are containers
- Cascades are tasks
- Each task gets full epistemic cycle
- Learning compounds across cascades
- This architecture enables **genuine AI learning measurement**

**Remember:**
Don't skip PREFLIGHT thinking you "already did it" for the session. Each task deserves its own honest epistemic assessment!

---

**Related Documentation:**
- `EMPIRICA_CASCADE_WORKFLOW_SPECIFICATION.md` - Cascade phases
- `SESSION_TRACKING.md` - Session management
- `COMPLETE_MCP_TOOL_REFERENCE.md` - Tool usage patterns
