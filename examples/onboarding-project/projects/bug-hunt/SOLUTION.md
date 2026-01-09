# Solution - Bug Hunt

**SPOILERS BELOW - Try to find it yourself first!**

---

## The Bug

**Location:** `task_manager.py`, line 54, in `_archive_completed()`

**Code:**
```python
def _archive_completed(self):
    """Move completed tasks to archive."""
    completed = [tid for tid, t in self.tasks.items() if t["completed"]]
    for task_id in completed:
        del self.tasks[task_id]  # <-- BUG: Deletes instead of archiving!
```

**Problem:** The method name says "archive" but it actually DELETES completed tasks. When `complete_task()` is called, it marks the task complete then immediately calls `_archive_completed()` which removes it.

---

## The Fix

**Option 1: Remove the auto-archive call (simplest)**

```python
def complete_task(self, task_id: str) -> bool:
    if task_id not in self.tasks:
        return False

    self.tasks[task_id]["completed"] = True
    self.tasks[task_id]["completed_at"] = datetime.now().isoformat()
    # REMOVED: self._archive_completed()
    self._save()
    return True
```

**Option 2: Actually implement archiving**

```python
def _archive_completed(self):
    """Mark completed tasks as archived."""
    for task in self.tasks.values():
        if task["completed"] and not task.get("archived"):
            task["archived"] = True
```

---

## Why This Bug Is Realistic

1. **Misleading name** - "archive" sounds safe, but it deletes
2. **No tests for retention** - Only tested completion, not retrieval
3. **Intermittent appearance** - Only shows when you try to access completed tasks
4. **Plausible intention** - Developer might have meant to add archive storage later

---

## Key Debugging Lessons

1. **Trace method calls** - Don't trust names, read the code
2. **Test post-conditions** - Check state AFTER operations
3. **Question "helper" methods** - Private methods hide complexity
