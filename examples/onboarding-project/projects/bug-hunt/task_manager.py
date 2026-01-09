"""
Task Manager - A simple task tracking system

Users report: "Tasks sometimes disappear after marking complete"
Your mission: Find and fix the bug
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional


class TaskManager:
    """Simple task manager with file persistence."""

    def __init__(self, storage_path: str = "tasks.json"):
        self.storage_path = Path(storage_path)
        self.tasks: dict[str, dict] = {}
        self._load()

    def _load(self):
        """Load tasks from storage."""
        if self.storage_path.exists():
            with open(self.storage_path) as f:
                self.tasks = json.load(f)

    def _save(self):
        """Save tasks to storage."""
        with open(self.storage_path, "w") as f:
            json.dump(self.tasks, f, indent=2)

    def add_task(self, title: str, priority: int = 1) -> str:
        """Add a new task. Returns task ID."""
        task_id = f"task_{len(self.tasks) + 1}"
        self.tasks[task_id] = {
            "title": title,
            "priority": priority,
            "completed": False,
            "created_at": datetime.now().isoformat(),
            "completed_at": None
        }
        self._save()
        return task_id

    def complete_task(self, task_id: str) -> bool:
        """Mark a task as complete."""
        if task_id not in self.tasks:
            return False

        self.tasks[task_id]["completed"] = True
        self.tasks[task_id]["completed_at"] = datetime.now().isoformat()

        # Archive completed tasks to keep active list clean
        self._archive_completed()
        self._save()
        return True

    def _archive_completed(self):
        """Move completed tasks to archive."""
        completed = [tid for tid, t in self.tasks.items() if t["completed"]]
        for task_id in completed:
            del self.tasks[task_id]  # BUG: Deletes instead of archiving!

    def get_task(self, task_id: str) -> Optional[dict]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def list_tasks(self, include_completed: bool = False) -> list[dict]:
        """List all tasks."""
        tasks = []
        for task_id, task in self.tasks.items():
            if include_completed or not task["completed"]:
                tasks.append({"id": task_id, **task})
        return sorted(tasks, key=lambda t: t["priority"], reverse=True)

    def get_stats(self) -> dict:
        """Get task statistics."""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t["completed"])
        return {
            "total": total,
            "completed": completed,
            "pending": total - completed
        }

    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        if task_id not in self.tasks:
            return False
        del self.tasks[task_id]
        self._save()
        return True

    def update_priority(self, task_id: str, priority: int) -> bool:
        """Update task priority."""
        if task_id not in self.tasks:
            return False
        self.tasks[task_id]["priority"] = priority
        self._save()
        return True


# Quick test
if __name__ == "__main__":
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        storage = os.path.join(tmpdir, "test_tasks.json")
        tm = TaskManager(storage)

        # Add some tasks
        t1 = tm.add_task("Write documentation", priority=2)
        t2 = tm.add_task("Fix bug", priority=3)
        t3 = tm.add_task("Review PR", priority=1)

        print(f"Added tasks: {t1}, {t2}, {t3}")
        print(f"Stats: {tm.get_stats()}")

        # Complete one
        tm.complete_task(t2)
        print(f"After completing {t2}: {tm.get_stats()}")

        # Try to get the completed task
        task = tm.get_task(t2)
        if task:
            print(f"Task {t2}: {task}")
        else:
            print(f"WARNING: Task {t2} not found after completion!")
