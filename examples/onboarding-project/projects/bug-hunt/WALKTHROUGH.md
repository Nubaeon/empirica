# Bug Hunt Walkthrough

Find the bug while learning Empirica's epistemic workflow.

---

## Step 1: Create Session & PREFLIGHT

```bash
# Create session
empirica session-create --ai-id claude-code --output json
# Save the session_id!

# PREFLIGHT: Assess your starting point honestly
empirica preflight-submit - << 'EOF'
{
  "session_id": "<YOUR-SESSION-ID>",
  "task_context": "Find bug causing tasks to disappear after completion",
  "vectors": {
    "know": 0.3,
    "uncertainty": 0.7,
    "context": 0.4,
    "clarity": 0.6
  },
  "reasoning": "I haven't seen this codebase. I know Python and debugging, but don't know where the bug is. High uncertainty is honest here."
}
EOF
```

**Why these vectors?**
- `know: 0.3` - You haven't read the code yet
- `uncertainty: 0.7` - Many possible causes
- `context: 0.4` - Limited info about the system
- `clarity: 0.6` - The bug report is clear, the cause isn't

---

## Step 2: Create Investigation Goal

```bash
empirica goals-create --session-id <YOUR-SESSION-ID> \
  --objective "Find and fix the disappearing tasks bug" \
  --scope-breadth 0.4 \
  --scope-duration 0.3 \
  --output json
```

---

## Step 3: Reproduce the Bug (NOETIC Phase)

First, let's confirm the bug exists.

```bash
# Run the tests
python -m pytest test_tasks.py -v
```

You should see failures like:
- `test_completed_task_still_retrievable` - FAILED
- `test_list_includes_completed_when_requested` - FAILED

**Log what you observe:**

```bash
empirica finding-log --session-id <YOUR-SESSION-ID> \
  --finding "Bug confirmed: 4 tests fail. All failures involve accessing tasks AFTER completion. Pattern: task exists, complete it, task is gone." \
  --impact 0.6
```

---

## Step 4: Form Hypotheses

What could cause tasks to disappear after completion? Some possibilities:

1. **File not saved** - Maybe _save() has a bug?
2. **Task deleted instead of updated** - Something removes it?
3. **Wrong task ID** - ID changes after completion?
4. **Concurrency issue** - Race condition?

**Log your hypotheses as unknowns:**

```bash
empirica unknown-log --session-id <YOUR-SESSION-ID> \
  --unknown "Is the task being deleted somewhere? Need to trace complete_task flow"

empirica unknown-log --session-id <YOUR-SESSION-ID> \
  --unknown "Does _save() work correctly? Maybe data isn't persisted"
```

---

## Step 5: Investigate (NOETIC Phase continues)

Read `task_manager.py` and trace `complete_task()`:

```python
def complete_task(self, task_id: str) -> bool:
    if task_id not in self.tasks:
        return False

    self.tasks[task_id]["completed"] = True
    self.tasks[task_id]["completed_at"] = datetime.now().isoformat()

    # What does this do?
    self._archive_completed()
    self._save()
    return True
```

**Aha moment!** What's `_archive_completed()`?

```python
def _archive_completed(self):
    """Move completed tasks to archive."""
    completed = [tid for tid, t in self.tasks.items() if t["completed"]]
    for task_id in completed:
        del self.tasks[task_id]  # <-- THIS IS THE BUG!
```

**Log the finding:**

```bash
empirica finding-log --session-id <YOUR-SESSION-ID> \
  --finding "ROOT CAUSE FOUND: _archive_completed() deletes completed tasks instead of archiving them. Line 54: 'del self.tasks[task_id]' removes the task entirely." \
  --impact 0.9
```

**Resolve your unknowns:**

```bash
# Find the unknown ID
empirica query unknowns --session-id <YOUR-SESSION-ID>

# Resolve it
empirica unknown-resolve --unknown-id <UNKNOWN-ID> \
  --resolved-by "Found: _archive_completed() deletes tasks. Bug is on line 54."
```

---

## Step 6: CHECK Gate - Ready to Fix?

Before modifying code, validate your confidence:

```bash
empirica check-submit - << 'EOF'
{
  "session_id": "<YOUR-SESSION-ID>",
  "action_description": "Fix _archive_completed to preserve tasks instead of deleting",
  "vectors": {
    "know": 0.85,
    "uncertainty": 0.15,
    "context": 0.90,
    "scope": 0.3
  },
  "reasoning": "Found the exact line causing the bug. Fix is clear: don't delete tasks, either mark as archived or remove the archive call entirely."
}
EOF
```

If CHECK returns `proceed`, continue. If `investigate`, gather more info.

---

## Step 7: Fix the Bug (PRAXIC Phase)

**Option A:** Remove archiving entirely (simple fix)

```python
def complete_task(self, task_id: str) -> bool:
    if task_id not in self.tasks:
        return False

    self.tasks[task_id]["completed"] = True
    self.tasks[task_id]["completed_at"] = datetime.now().isoformat()

    # REMOVED: self._archive_completed()  <-- Don't auto-delete!
    self._save()
    return True
```

**Option B:** Fix archiving to actually archive

```python
def _archive_completed(self):
    """Mark completed tasks as archived (don't delete)."""
    for task_id, task in self.tasks.items():
        if task["completed"] and not task.get("archived"):
            task["archived"] = True
```

---

## Step 8: Verify the Fix

```bash
python -m pytest test_tasks.py -v
```

All tests should pass now!

**Log completion:**

```bash
empirica finding-log --session-id <YOUR-SESSION-ID> \
  --finding "Bug fixed: Removed _archive_completed() call from complete_task(). All 11 tests now pass." \
  --impact 0.7
```

---

## Step 9: Complete Goal

```bash
empirica goals-complete --goal-id <YOUR-GOAL-ID> \
  --reason "Found and fixed disappearing tasks bug. Root cause: _archive_completed deleted instead of archiving."
```

---

## Step 10: POSTFLIGHT - Measure Learning

```bash
empirica postflight-submit - << 'EOF'
{
  "session_id": "<YOUR-SESSION-ID>",
  "task_context": "Completed bug hunt - found and fixed disappearing tasks",
  "vectors": {
    "know": 0.90,
    "uncertainty": 0.10,
    "context": 0.95,
    "clarity": 0.95
  },
  "reasoning": "Started with no knowledge of codebase, ended with full understanding of the bug. Key learning: always trace method calls, especially ones with misleading names like 'archive'."
}
EOF
```

---

## Your Learning Delta

Compare PREFLIGHT to POSTFLIGHT:

| Vector | Before | After | Delta |
|--------|--------|-------|-------|
| know | 0.30 | 0.90 | **+0.60** |
| uncertainty | 0.70 | 0.10 | **-0.60** |
| context | 0.40 | 0.95 | **+0.55** |

That's a significant learning journey captured in your epistemic record!

---

## What You Learned

1. **PREFLIGHT with honest uncertainty** - Starting low is fine
2. **Log findings as you discover** - Builds searchable history
3. **Track unknowns** - Explicit questions focus investigation
4. **CHECK before action** - Validate confidence before coding
5. **POSTFLIGHT captures learning** - Delta shows real progress

Your debugging session is now preserved. Future you (or future AI) can search these findings.

```bash
empirica project-search --task "disappearing tasks bug"
```
