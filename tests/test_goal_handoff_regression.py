"""
Regression test for goal handoff bug fix

Tests that discover_goals() and add_lineage() work correctly
after the git notes enumeration fix.

Bug: Goals stored in refs/notes/empirica/goals/<uuid> were not discoverable
Fix: Use 'git for-each-ref' instead of 'git notes list'
"""
import pytest
from empirica.core.canonical.empirica_git import GitGoalStore


class TestGoalHandoffRegression:
    """Regression tests for goal discovery and lineage tracking"""
    
    def test_discover_goals_returns_results(self):
        """
        Test that discover_goals() actually finds stored goals
        
        Regression: Previously returned empty list due to wrong git command
        """
        store = GitGoalStore()
        goals = store.discover_goals()
        
        # Should find at least some goals (4 documentation goals exist)
        assert len(goals) > 0, "discover_goals() should find stored goals"
        
        # Each goal should have required fields
        for goal in goals:
            assert 'goal_id' in goal
            assert 'ai_id' in goal
            assert 'goal_data' in goal
            assert 'lineage' in goal
    
    def test_discover_goals_filters_by_ai(self):
        """
        Test that filtering by ai_id works correctly
        
        Ensures the for-each-ref parsing correctly loads goal data
        """
        store = GitGoalStore()
        
        # Get all goals first
        all_goals = store.discover_goals()
        if len(all_goals) == 0:
            pytest.skip("No goals in repository")
        
        # Pick an AI that has goals
        ai_id = all_goals[0]['ai_id']
        
        # Filter by that AI
        filtered_goals = store.discover_goals(from_ai_id=ai_id)
        
        assert len(filtered_goals) > 0, f"Should find goals from {ai_id}"
        
        # All returned goals should be from that AI
        for goal in filtered_goals:
            assert goal['ai_id'] == ai_id
    
    def test_lineage_preserved_on_resume(self):
        """
        Test that lineage is preserved when updating goals
        
        Regression: Previously lineage was overwritten with fresh array
        """
        store = GitGoalStore()
        
        # Get a goal to test with
        goals = store.discover_goals()
        if len(goals) == 0:
            pytest.skip("No goals in repository")
        
        goal = goals[0]
        goal_id = goal['goal_id']
        original_lineage_count = len(goal['lineage'])
        
        # Use unique ai_id per run to avoid idempotency issues
        import uuid
        test_ai_id = f'test-ai-regression-{uuid.uuid4().hex[:8]}'

        # Add lineage entry
        success = store.add_lineage(goal_id, test_ai_id, 'resumed')
        assert success, "add_lineage should succeed"

        # NOTE: load_goal reads from the original commit's note (git notes list
        # returns the first annotated commit). add_lineage writes to HEAD.
        # When HEAD != original commit, the updated lineage is on a different
        # commit than what load_goal reads. This is a known limitation of
        # git-notes-based storage (see goal_store.py store_goal/load_goal).
        # Verify the note was written to HEAD directly.
        import subprocess
        note_ref = f'empirica/goals/{goal_id}'
        result = subprocess.run(
            ['git', 'notes', f'--ref={note_ref}', 'show', 'HEAD'],
            capture_output=True, text=True
        )
        assert result.returncode == 0, "Note should exist on HEAD"
        import json
        head_goal = json.loads(result.stdout)
        assert len(head_goal['lineage']) == original_lineage_count + 1

        # Last entry should be our addition
        last_entry = head_goal['lineage'][-1]
        assert last_entry['ai_id'] == test_ai_id
        assert last_entry['action'] == 'resumed'
        
        # Original lineage should still be there
        for i in range(original_lineage_count):
            assert head_goal['lineage'][i] == goal['lineage'][i]
    


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
