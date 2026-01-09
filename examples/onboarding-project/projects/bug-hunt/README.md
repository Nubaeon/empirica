# Bug Hunt

**Difficulty:** ⭐⭐ | **Time:** 20 minutes

A user reports that the task manager "sometimes loses tasks." Your job: find the bug.

## The Scenario

You've inherited a simple task manager. Users report intermittent data loss - tasks occasionally disappear. The bug is subtle and requires investigation.

## Why This Is Epistemic

- You start with **low confidence** - you don't know the codebase
- Multiple hypotheses are possible - you must **investigate**
- Some leads will be **dead-ends**
- Your confidence should **increase** as you narrow down the cause

## Files

```
bug-hunt/
├── README.md           # This file
├── WALKTHROUGH.md      # Step-by-step guide
├── task_manager.py     # The buggy code (~80 lines)
├── test_tasks.py       # Tests (some fail intermittently)
└── SOLUTION.md         # Spoilers - read after solving
```

## Your Mission

1. Reproduce the bug
2. Form hypotheses
3. Investigate systematically (log findings!)
4. Find and fix the bug
5. Verify the fix

## Start Here

Follow [WALKTHROUGH.md](WALKTHROUGH.md) for the guided experience with Empirica.
