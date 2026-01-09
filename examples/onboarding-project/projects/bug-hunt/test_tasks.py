"""
Tests for Task Manager

Note: Some tests fail intermittently - that's the bug you need to find!
"""

import pytest
import tempfile
import os
from task_manager import TaskManager


@pytest.fixture
def task_manager():
    """Create a TaskManager with temporary storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = os.path.join(tmpdir, "test_tasks.json")
        yield TaskManager(storage)


class TestAddTask:
    def test_add_single_task(self, task_manager):
        task_id = task_manager.add_task("Test task")
        assert task_id is not None
        assert task_manager.get_task(task_id) is not None

    def test_add_multiple_tasks(self, task_manager):
        t1 = task_manager.add_task("Task 1")
        t2 = task_manager.add_task("Task 2")
        t3 = task_manager.add_task("Task 3")

        assert len(task_manager.list_tasks()) == 3

    def test_task_has_correct_fields(self, task_manager):
        task_id = task_manager.add_task("Test", priority=5)
        task = task_manager.get_task(task_id)

        assert task["title"] == "Test"
        assert task["priority"] == 5
        assert task["completed"] is False
        assert task["created_at"] is not None


class TestCompleteTask:
    def test_complete_existing_task(self, task_manager):
        task_id = task_manager.add_task("Complete me")
        result = task_manager.complete_task(task_id)
        assert result is True

    def test_complete_nonexistent_task(self, task_manager):
        result = task_manager.complete_task("fake_id")
        assert result is False

    def test_completed_task_still_retrievable(self, task_manager):
        """
        BUG MANIFESTATION: This test fails!
        After completing a task, we should still be able to get it.
        """
        task_id = task_manager.add_task("Important task")

        # Verify task exists
        assert task_manager.get_task(task_id) is not None

        # Complete it
        task_manager.complete_task(task_id)

        # Should still be able to retrieve it
        task = task_manager.get_task(task_id)
        assert task is not None, f"Task {task_id} disappeared after completion!"
        assert task["completed"] is True

    def test_completed_task_has_timestamp(self, task_manager):
        """Another test that exposes the bug."""
        task_id = task_manager.add_task("Timestamped task")
        task_manager.complete_task(task_id)

        task = task_manager.get_task(task_id)
        assert task is not None, "Task vanished!"
        assert task["completed_at"] is not None


class TestListTasks:
    def test_list_excludes_completed_by_default(self, task_manager):
        t1 = task_manager.add_task("Active")
        t2 = task_manager.add_task("Will complete")

        task_manager.complete_task(t2)

        active = task_manager.list_tasks(include_completed=False)
        # Should have 1 active task
        assert len(active) == 1

    def test_list_includes_completed_when_requested(self, task_manager):
        """This test reveals the bug - completed tasks are gone, not hidden."""
        t1 = task_manager.add_task("Active")
        t2 = task_manager.add_task("Completed")

        task_manager.complete_task(t2)

        all_tasks = task_manager.list_tasks(include_completed=True)
        # Should have 2 tasks total
        assert len(all_tasks) == 2, f"Expected 2 tasks, got {len(all_tasks)}. Completed task was deleted!"


class TestStats:
    def test_stats_count_all_tasks(self, task_manager):
        """Stats should reflect all tasks including completed."""
        task_manager.add_task("Task 1")
        task_manager.add_task("Task 2")
        t3 = task_manager.add_task("Task 3")

        task_manager.complete_task(t3)

        stats = task_manager.get_stats()
        # BUG: This will show wrong numbers because completed tasks are deleted
        assert stats["total"] == 3, f"Expected 3 total, got {stats['total']}"
        assert stats["completed"] == 1


class TestPersistence:
    def test_tasks_persist_across_instances(self):
        """Test that tasks survive reload."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = os.path.join(tmpdir, "persist_test.json")

            # Create and add
            tm1 = TaskManager(storage)
            task_id = tm1.add_task("Persistent task")

            # Reload
            tm2 = TaskManager(storage)
            task = tm2.get_task(task_id)

            assert task is not None
            assert task["title"] == "Persistent task"
