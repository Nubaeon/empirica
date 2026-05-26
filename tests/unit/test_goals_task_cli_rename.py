"""
CLI surface regression test for the subtask→task rename (clean break).

Pins:
1. New verbs (goals-add-task, goals-complete-task, goals-get-tasks) are
   registered in the parser.
2. Old verbs (goals-add-subtask, goals-complete-subtask, goals-get-subtasks)
   are GONE — invoking them prints argparse's "invalid choice" error.
3. --task-id is the canonical flag; --subtask-id no longer exists on
   goals-complete-task.
4. New aliases (goal-add-task, goal-complete-task) work.

The clean-break decision means no backward-compat shim — old verbs are not
deprecated, they're removed.
"""

import subprocess


def _run(args: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(
        ["empirica", *args],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return p.returncode, p.stdout, p.stderr


class TestNewVerbsRegistered:
    def test_goals_add_task_help_works(self):
        rc, out, _err = _run(["goals-add-task", "--help"])
        assert rc == 0
        assert "goals-add-task" in out
        assert "--goal-id" in out
        assert "--description" in out

    def test_goals_complete_task_help_works(self):
        rc, out, _err = _run(["goals-complete-task", "--help"])
        assert rc == 0
        assert "goals-complete-task" in out
        assert "--task-id" in out
        assert "--evidence" in out

    def test_goals_get_tasks_help_works(self):
        rc, out, _err = _run(["goals-get-tasks", "--help"])
        assert rc == 0
        assert "goals-get-tasks" in out
        assert "--goal-id" in out


class TestOldVerbsRemoved:
    def test_goals_add_subtask_is_gone(self):
        rc, _out, err = _run(["goals-add-subtask", "--help"])
        assert rc != 0
        assert "invalid choice: 'goals-add-subtask'" in err

    def test_goals_complete_subtask_is_gone(self):
        rc, _out, err = _run(["goals-complete-subtask", "--help"])
        assert rc != 0
        assert "invalid choice: 'goals-complete-subtask'" in err

    def test_goals_get_subtasks_is_gone(self):
        rc, _out, err = _run(["goals-get-subtasks", "--help"])
        assert rc != 0
        assert "invalid choice: 'goals-get-subtasks'" in err


class TestSubtaskIdFlagRemoved:
    def test_complete_task_rejects_subtask_id_flag(self):
        rc, _out, err = _run([
            "goals-complete-task",
            "--subtask-id", "deadbeef",
            "--evidence", "should not work",
        ])
        assert rc != 0
        # argparse reports the missing-required first, but the --subtask-id flag
        # must NOT have been silently accepted as --task-id (clean break, no alias).
        assert "required" in err and "--task-id" in err

    def test_complete_task_requires_task_id(self):
        rc, _out, err = _run(["goals-complete-task"])
        assert rc != 0
        assert "--task-id" in err


class TestNewAliases:
    def test_goal_add_task_singular_alias(self):
        rc, out, _err = _run(["goal-add-task", "--help"])
        assert rc == 0
        assert "--goal-id" in out

    def test_goal_complete_task_singular_alias(self):
        rc, out, _err = _run(["goal-complete-task", "--help"])
        assert rc == 0
        assert "--task-id" in out


class TestCompleteTaskRejectsBadUUID:
    """The fix from yesterday's transaction must still hold after the rename.

    Note: only asserts rc != 0 (not rc == 1) because the exact exit code
    depends on whether a project DB exists in CWD. CI runs in a fresh
    checkout without a sessions.db, so the handler may exit via a
    different path. What matters is the silent-success regression
    can't recur — exit MUST be non-zero.
    """

    def test_phantom_uuid_returns_nonzero(self):
        rc, _out, _err = _run([
            "goals-complete-task",
            "--task-id", "deadbeef-cafe-1234-5678-aaaabbbbcccc",
            "--evidence", "should fail",
        ])
        assert rc != 0
