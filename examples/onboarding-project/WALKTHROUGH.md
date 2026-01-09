# Empirica Walkthrough

This guide walks you through the complete Empirica workflow using a simple task.

---

## Step 1: Create a Session

Every Empirica workflow starts with a session.

```bash
cd examples/onboarding-project

# Create session (use your AI's name as ai-id)
empirica session-create --ai-id claude-code --output json
```

**Save the `session_id`** - you'll use it throughout this walkthrough.

```bash
# Example output:
{
  "session_id": "abc123-def456-...",
  "ai_id": "claude-code",
  "project_id": "xyz789-..."
}
```

**Pro tip:** Set an environment variable:
```bash
export SESSION_ID="your-session-id-here"
```

---

## Step 2: Load Project Context

Bootstrap loads existing project state (goals, findings, unknowns).

```bash
empirica project-bootstrap --session-id $SESSION_ID --output json
```

For a new project like this, it will show empty state. That's expected!

---

## Step 3: PREFLIGHT - Assess Before Starting

Before doing any work, honestly assess what you know.

```bash
# Replace <YOUR-SESSION-ID> with your actual session_id from Step 1
empirica preflight-submit - << 'EOF'
{
  "session_id": "<YOUR-SESSION-ID>",
  "task_context": "Implement a calculator module with add, subtract, multiply, divide functions",
  "vectors": {
    "know": 0.7,
    "uncertainty": 0.3,
    "context": 0.8,
    "clarity": 0.9
  },
  "reasoning": "Calculator functions are straightforward. I know Python well. The requirements are clear from the test file."
}
EOF
```

**Vector meanings:**
- `know` (0.7): I understand calculators and Python pretty well
- `uncertainty` (0.3): Low uncertainty, this is standard stuff
- `context` (0.8): I have the tests to guide me
- `clarity` (0.9): The requirements are very clear

**Bias correction:** AIs tend to be overconfident. Add +0.10 to uncertainty, subtract -0.05 from know.

---

## Step 4: Create a Goal

Break the work into a trackable goal.

```bash
empirica goals-create --session-id $SESSION_ID \
  --objective "Implement calculator module with all tests passing" \
  --scope-breadth 0.3 \
  --scope-duration 0.2 \
  --output json
```

**Save the `goal_id`** for later.

**Scope meanings:**
- `breadth` (0.3): Small scope, just one file
- `duration` (0.2): Quick task, ~15 minutes

---

## Step 5: Add Subtasks

Break the goal into concrete steps.

```bash
GOAL_ID="your-goal-id-here"

empirica goals-add-subtask --goal-id $GOAL_ID --description "Implement add function"
empirica goals-add-subtask --goal-id $GOAL_ID --description "Implement subtract function"
empirica goals-add-subtask --goal-id $GOAL_ID --description "Implement multiply function"
empirica goals-add-subtask --goal-id $GOAL_ID --description "Implement divide function with zero handling"
empirica goals-add-subtask --goal-id $GOAL_ID --description "Run tests and verify all pass"
```

Check your progress:
```bash
empirica goals-progress --goal-id $GOAL_ID
```

---

## Step 6: Do the Work (with Breadcrumbs)

Now implement the calculator. Open `calculator.py` and complete the functions.

**As you work, log what you learn:**

```bash
# When you discover something
empirica finding-log --session-id $SESSION_ID \
  --finding "Python division returns float by default, need to handle int division separately if needed" \
  --impact 0.4

# When you have a question
empirica unknown-log --session-id $SESSION_ID \
  --unknown "Should divide return int or float for whole number results?"

# If something doesn't work
empirica deadend-log --session-id $SESSION_ID \
  --approach "Tried using // for all division" \
  --why-failed "Loses precision for non-whole numbers"
```

**Impact scale:**
- 0.1-0.3: Trivial (minor syntax, style)
- 0.4-0.6: Important (design decisions, gotchas)
- 0.7-0.9: Critical (architecture, security)

---

## Step 7: Complete Subtasks

As you finish each function, mark it complete:

```bash
# Get subtask IDs
empirica goals-list-all --session-id $SESSION_ID --output json

# Complete each subtask with evidence
empirica goals-complete-subtask --subtask-id <SUBTASK_ID> \
  --evidence "Implemented add(a, b) -> return a + b"
```

---

## Step 8: Run Tests

```bash
python -m pytest test_calculator.py -v
```

When all tests pass, log it:

```bash
empirica finding-log --session-id $SESSION_ID \
  --finding "All 5 calculator tests passing" \
  --impact 0.5
```

---

## Step 9: Complete the Goal

```bash
empirica goals-complete --goal-id $GOAL_ID \
  --reason "All calculator functions implemented and tested"
```

---

## Step 10: POSTFLIGHT - Measure Learning

After completing the work, assess what changed.

```bash
# Replace <YOUR-SESSION-ID> with your actual session_id
empirica postflight-submit - << 'EOF'
{
  "session_id": "<YOUR-SESSION-ID>",
  "task_context": "Completed calculator module implementation",
  "vectors": {
    "know": 0.85,
    "uncertainty": 0.15,
    "context": 0.95,
    "clarity": 0.95
  },
  "reasoning": "Confirmed Python division behavior. Learned about ZeroDivisionError handling. All tests pass."
}
EOF
```

**Compare to PREFLIGHT:**
- `know`: 0.7 -> 0.85 (+0.15) - Learned about division edge cases
- `uncertainty`: 0.3 -> 0.15 (-0.15) - Much more confident now
- This is your **learning delta**!

---

## Step 11: View Your Session

```bash
# Full session summary
empirica sessions-show --session-id $SESSION_ID --output json

# Query your breadcrumbs
empirica query findings --session-id $SESSION_ID
empirica query unknowns --session-id $SESSION_ID
```

---

## Congratulations!

You've completed the full Empirica workflow:

1. **Session** - Created tracking context
2. **PREFLIGHT** - Baseline assessment
3. **Goal + Subtasks** - Structured work breakdown
4. **Breadcrumbs** - Logged findings, unknowns, dead-ends
5. **POSTFLIGHT** - Measured learning delta

**Key insight:** The value isn't in the numbers - it's in the honest self-assessment and the learning record you create.

---

## Next Steps

- Try a real task in your own project
- Explore `empirica project-search` for semantic memory
- Set up the Claude Code plugin for automatic hooks
- Read the full docs: `empirica docs-explain --topic CASCADE`

---

## Quick Reference

```bash
# Session
empirica session-create --ai-id claude-code --output json
empirica project-bootstrap --session-id <ID> --output json

# CASCADE
empirica preflight-submit -
empirica check-submit -
empirica postflight-submit -

# Breadcrumbs
empirica finding-log --finding "..." --impact 0.7
empirica unknown-log --unknown "..."
empirica deadend-log --approach "..." --why-failed "..."

# Goals
empirica goals-create --objective "..." --output json
empirica goals-add-subtask --goal-id <ID> --description "..."
empirica goals-complete-subtask --subtask-id <ID> --evidence "..."
empirica goals-complete --goal-id <ID> --reason "..."
```
