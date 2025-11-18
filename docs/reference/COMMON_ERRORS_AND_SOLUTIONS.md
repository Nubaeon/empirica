# Common Errors and Solutions

**Task 5: Troubleshooting Documentation (Reliability Improvements)**

This guide provides actionable solutions for common Empirica errors. Each error includes the reason, suggested fix, alternatives, and recovery commands.

---

## Table of Contents

1. [Session Errors](#session-errors)
2. [Alias Resolution Errors](#alias-resolution-errors)
3. [Component Unavailable](#component-unavailable)
4. [Insufficient Data](#insufficient-data)
5. [Input Validation Errors](#input-validation-errors)
6. [Drift Detection Issues](#drift-detection-issues)
7. [Goal and Task Errors](#goal-and-task-errors)

---

## Session Errors

### Error: "Session not found"

**What happened:**
The session ID you provided doesn't exist in the database.

**Why it happens:**
- Session was never created
- Wrong session ID provided
- Session was created in a different database instance
- Database was reset or corrupted

**Solution:**
```python
# Create a new session
bootstrap_session(
    ai_id="your_id",
    session_type="development",
    bootstrap_level=2
)
```

**Alternatives:**
1. **List all sessions:**
   ```python
   list_goals(session_id=None)  # See all goals without session filter
   ```

2. **Resume previous session:**
   ```python
   resume_previous_session(ai_id="your_id")
   ```

3. **Use session alias:**
   ```python
   # Use 'latest:active:your_id' instead of explicit UUID
   execute_preflight(
       session_id="latest:active:your_id",
       prompt="Your task"
   )
   ```

**Prevention:**
- Always run `bootstrap_session()` at the start of a new session
- Store the returned session_id for future calls
- Use session aliases for convenience

---

## Alias Resolution Errors

### Error: "Session resolution failed" or "Invalid alias"

**What happened:**
The session alias couldn't be resolved to a valid session UUID.

**Why it happens:**
- Malformed alias syntax
- No sessions exist for the specified AI ID
- Session database is empty

**Solution:**
```python
# Use the correct alias format
session_id = "latest:active:rovodev"

# Valid alias patterns:
# - "latest" - Most recent session
# - "latest:active" - Most recent active session  
# - "latest:rovodev" - Most recent for specific AI
# - "latest:active:rovodev" - Most recent active for specific AI
```

**Alternatives:**
1. **Use explicit UUID:**
   ```python
   # If you know the session UUID
   session_id = "1493402f-792b-487c-b98b-51e31ebf00a1"
   ```

2. **Bootstrap new session:**
   ```python
   result = bootstrap_session(ai_id="rovodev", session_type="development", bootstrap_level=2)
   session_id = result["session_id"]
   ```

**Prevention:**
- Bookmark your session ID after bootstrap
- Use consistent AI IDs across sessions
- Test alias resolution with `get_epistemic_state(session_id="latest:active:your_id")`

---

## Component Unavailable

### Error: "Required component not available" or "Component initialization failed"

**What happened:**
A required Empirica component (goal orchestrator, drift monitor, etc.) couldn't be loaded.

**Why it happens:**
- Session not properly bootstrapped
- Missing dependencies
- Component-specific configuration issue

**Solution:**
```python
# Bootstrap with full component loading
bootstrap_session(
    ai_id="your_id",
    session_type="development",
    bootstrap_level=2  # Full bootstrap
)
```

**Bootstrap Levels:**
- `0` = Minimal (basic tracking only)
- `1` = Standard (most components)
- `2` = Full (all components including advanced features)

**Alternatives:**
1. **Check bootstrap result:**
   ```python
   result = bootstrap_session(...)
   print(result["components_loaded"])
   print(result["component_count"])
   ```

2. **Manual component initialization:**
   ```python
   from empirica.core.canonical import CanonicalGoalOrchestrator
   orchestrator = CanonicalGoalOrchestrator()
   ```

**Prevention:**
- Always use `bootstrap_level=2` for full functionality
- Check `components_loaded` in bootstrap response
- Don't skip bootstrap step

---

## Insufficient Data

### Error: "Insufficient synthesis history" or "Not enough data for analysis"

**What happened:**
An operation requires more data than currently exists (e.g., drift detection needs ≥5 assessments).

**Why it happens:**
- Trying to run CHECK before PREFLIGHT
- Drift detection with <5 assessments
- New session without history

**Solution:**
Follow the proper workflow order:

```python
# 1. Bootstrap
bootstrap_session(ai_id="your_id", session_type="development", bootstrap_level=2)

# 2. PREFLIGHT (required first)
execute_preflight(session_id="your_session", prompt="task description")
submit_preflight_assessment(session_id="your_session", vectors={...})

# 3. INVESTIGATE (build history)
# ... perform investigation work ...

# 4. CHECK (now has data)
execute_check(session_id="your_session", findings=[...])
```

**For Drift Detection Specifically:**
- Requires ≥5 synthesis history entries
- Run at least 5 assessment cycles before drift analysis
- Drift detection automatically fails open if insufficient data

**Prevention:**
- Follow workflow: PREFLIGHT → INVESTIGATE → CHECK → ACT
- Don't skip workflow phases
- Build sufficient history before advanced analytics

---

## Input Validation Errors

### Error: "Input validation failed" or "Required field missing"

**What happened:**
Your input doesn't match the expected schema for the tool.

**Why it happens:**
- Missing required parameters
- Wrong data type (e.g., string instead of integer)
- Invalid enum value

**Common Examples:**

#### Bootstrap Level Type Error
```python
# ❌ WRONG
bootstrap_session(bootstrap_level="optimal")

# ✅ CORRECT
bootstrap_session(bootstrap_level=2)  # Must be integer: 0, 1, or 2
```

#### Missing Required Fields
```python
# ❌ WRONG
execute_preflight(prompt="task")  # Missing session_id

# ✅ CORRECT
execute_preflight(session_id="your_session", prompt="task")
```

#### Invalid Enum Values
```python
# ❌ WRONG
create_goal(scope="big_project")

# ✅ CORRECT  
create_goal(scope="project_wide")  # Must be: task_specific, session_scoped, or project_wide
```

**Solution:**
Check the tool schema and correct your input.

**Prevention:**
- Read tool documentation before calling
- Use IDE with MCP schema hints
- Test with minimal required parameters first

---

## Drift Detection Issues

### Understanding Drift Warnings

Drift detection runs automatically during CHECK phase and classifies drift severity:

#### Minor Drift (< 0.3)
- **What:** Slight variations in assessment patterns
- **Action:** No action needed, proceed normally
- **Warning:** None shown

#### Moderate Drift (0.3 - 0.6)
- **What:** Noticeable sycophancy or tension avoidance patterns
- **Action:** Review your reasoning for bias
- **Warning:** ⚠️ "Moderate drift detected. Review your reasoning for sycophancy or tension avoidance patterns."

#### Severe Drift (> 0.6)
- **What:** Strong evidence of non-genuine assessment
- **Action:** Re-assess with epistemic honesty
- **Warning:** 🛑 "SEVERE DRIFT DETECTED! ACT phase should not proceed."
- **Response:** `safe_to_proceed: false`

### What Causes Drift?

**Sycophancy Drift:**
- Always agreeing with prompts
- Inflating confidence to please
- Avoiding genuine uncertainty

**Example:**
```
Prompt: "This seems like a good approach, right?"
Drifted: "Yes, absolutely! Perfect approach!" 
Genuine: "It has merit, but I see these potential issues..."
```

**Tension Avoidance:**
- Downplaying problems
- Avoiding uncomfortable truths
- Smoothing over conflicts

**Example:**
```
Situation: Critical bug found
Drifted: "It's a minor issue, easily fixed"
Genuine: "This is a critical bug that blocks deployment"
```

### Fixing Drift

1. **Re-assess honestly:**
   ```python
   # Submit CHECK with genuine assessment
   submit_check_assessment(
       session_id="your_session",
       vectors={...},  # Honest scores
       decision="investigate",  # If truly not ready
       reasoning="Genuine concerns about X, Y, Z"
   )
   ```

2. **Review your assessments:**
   - Are you inflating confidence scores?
   - Are you avoiding stating problems?
   - Are you agreeing to avoid conflict?

3. **INVESTIGATE more:**
   - Build better understanding
   - Address actual knowledge gaps
   - Then re-run CHECK

**Prevention:**
- Use genuine reasoning, not pattern matching
- Be honest about uncertainty
- State problems clearly even if uncomfortable

---

## Goal and Task Errors

### Error: "Goal not found" or "Subtask not found"

**What happened:**
The goal or subtask ID doesn't exist in the database.

**Solution:**
```python
# List all goals for your session
list_goals(session_id="your_session")

# Create a goal if needed
create_goal(
    session_id="your_session",
    objective="Your goal description",
    success_criteria=[
        {"description": "Criterion 1", "validation_method": "completion"}
    ]
)
```

### Adopting Goals from Other Sessions

If you're given a goal ID from another session:

```python
from empirica.core.goals.repository import GoalRepository

# 1. Bootstrap your session
bootstrap_session(ai_id="your_id", session_type="development", bootstrap_level=2)

# 2. Adopt the goal
repo = GoalRepository()
goal = repo.get_goal('goal-id-from-other-session')
repo.save_goal(goal, 'your-session-id')
repo.close()

# 3. Verify
list_goals(session_id="your-session-id")
```

---

## Quick Troubleshooting Checklist

When something goes wrong, check these in order:

1. **Did you bootstrap?**
   ```python
   bootstrap_session(ai_id="your_id", session_type="development", bootstrap_level=2)
   ```

2. **Is your session ID valid?**
   ```python
   # Use alias or verify UUID exists
   get_epistemic_state(session_id="latest:active:your_id")
   ```

3. **Did you follow workflow order?**
   - ✅ PREFLIGHT → INVESTIGATE → CHECK → ACT
   - ❌ Skipping phases

4. **Are parameters correct types?**
   - Integers not strings: `bootstrap_level=2` not `"optimal"`
   - Valid enum values
   - Required fields present

5. **Do you have enough data?**
   - ≥5 assessments for drift detection
   - PREFLIGHT before CHECK
   - History before analytics

---

## Getting More Help

### Check Component Status
```python
result = bootstrap_session(...)
print(f"Components loaded: {result['component_count']}")
print(f"Components: {result['components_loaded']}")
```

### View Session State
```python
get_epistemic_state(session_id="your_session")
```

### Review Calibration
```python
get_calibration_report(session_id="your_session")
```

### Test Database Connection
```python
from empirica.data.session_database import SessionDatabase
db = SessionDatabase()
print("Database connected:", db.conn is not None)
db.close()
```

---

## Error Response Format

Starting with the reliability improvements, all MCP tool errors include:

```json
{
  "ok": false,
  "error": "Description of what went wrong",
  "error_type": "session_not_found",
  "reason": "Why this error occurred",
  "suggestion": "What to try first",
  "alternatives": ["Other options you can try"],
  "recovery_commands": ["Specific commands to fix it"],
  "context": {"additional": "debugging info"}
}
```

Use these fields to quickly understand and resolve issues.

---

## Still Having Issues?

If you've tried the solutions above and still encounter problems:

1. Check the logs: `.empirica_reflex_logs/`
2. Verify database: `~/.empirica/sessions.db`
3. Review recent changes: `git log`
4. Check for known issues in repository
5. Create a minimal reproducible example

**Report format:**
```
Error: [exact error message]
Command: [exact command that failed]
Session state: [output of get_epistemic_state]
Steps taken: [what you tried]
```
