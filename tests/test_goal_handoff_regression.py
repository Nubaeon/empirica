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
        
        # Add lineage entry
        success = store.add_lineage(goal_id, 'test-ai-regression', 'resumed')
        assert success, "add_lineage should succeed"
        
        # Reload goal and verify lineage grew
        updated_goal = store.load_goal(goal_id)
        assert updated_goal is not None
        assert len(updated_goal['lineage']) == original_lineage_count + 1
        
        # Last entry should be our addition
        last_entry = updated_goal['lineage'][-1]
        assert last_entry['ai_id'] == 'test-ai-regression'
        assert last_entry['action'] == 'resumed'
        
        # Original lineage should still be there
        for i in range(original_lineage_count):
            assert updated_goal['lineage'][i] == goal['lineage'][i]
    


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
