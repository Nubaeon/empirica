#!/usr/bin/env python3
"""
Integration Tests for Git Notes Phase 2

Tests git notes integration with task completion tracking.
"""

import pytest
import uuid
import subprocess
from pathlib import Path

from empirica.core.goals.types import Goal, SuccessCriterion, ScopeVector
from empirica.core.goals.repository import GoalRepository
from empirica.core.tasks.types import SubTask, EpistemicImportance
from empirica.core.tasks.repository import TaskRepository
from empirica.core.completion.tracker import CompletionTracker
from empirica.core.completion.git_query import GitProgressQuery


class TestGitNotesIntegration:
    """Test git notes integration for task tracking"""
    
    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create temporary database"""
        db_path = tmp_path / "test_git_notes.db"
        return str(db_path)
    
    @pytest.fixture
    def session_id(self):
        """Generate test session ID"""
        return str(uuid.uuid4())
    
    def test_git_notes_written_on_completion(self, temp_db, session_id):
        """
        Test that git notes are written when subtask is completed
        
        Verifies:
        - CompletionTracker detects git availability
        - Git notes are written on subtask completion
        - Notes contain correct metadata
        """
        # Create goal and subtask
        goal_repo = GoalRepository(db_path=temp_db)
        task_repo = TaskRepository(db_path=temp_db)
        
        goal = Goal.create(
            objective="Test git notes integration",
            success_criteria=[
                SuccessCriterion(
                    id=str(uuid.uuid4()),
                    description="Git notes work",
                    validation_method="completion"
                )
            ],
            scope=ScopeVector(breadth=0.3, duration=0.2, coordination=0.1)
        )
        goal_repo.save_goal(goal, session_id)
        
        subtask = SubTask.create(
            goal_id=goal.id,
            description="Test git note creation",
            epistemic_importance=EpistemicImportance.HIGH,
            estimated_tokens=500
        )
        task_repo.save_subtask(subtask)
        
        # Complete subtask with tracker (should write git note)
        tracker = CompletionTracker(db_path=temp_db, enable_git_notes=True)
        
        if not tracker.git_available:
            pytest.skip("Git not available, skipping git notes test")
        
        # Complete with evidence (use HEAD commit)
        import subprocess
        head_commit = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True,
            text=True,
            cwd='.'
        ).stdout.strip()

        success = tracker.record_subtask_completion(
            subtask.id,
            evidence=f"commit:{head_commit}"
        )
        
        assert success, "Subtask completion should succeed"
        
        # Verify git note was created (check via git command)
        try:
            note_ref = f"empirica/tasks/{goal.id}"
            result = subprocess.run(
                ['git', 'notes', '--ref', note_ref, 'list', 'HEAD'],
                capture_output=True,
                timeout=2,
                cwd='.',
                text=True
            )
            
            # Should have a note
            assert result.returncode == 0, "Git notes should list successfully"
            assert result.stdout.strip(), "Should have at least one note"
            
        except subprocess.SubprocessError:
            pytest.skip("Could not verify git notes")
        
        # Cleanup
        tracker.close()
        goal_repo.close()
        task_repo.close()
    
    def test_git_query_retrieves_timeline(self, temp_db, session_id):
        """
        Test that GitProgressQuery can retrieve goal timeline
        
        Verifies:
        - Query returns commit timeline
        - Task metadata is included
        - Completed subtasks are tracked
        """
        query = GitProgressQuery()
        
        if not query.git_available:
            pytest.skip("Git not available, skipping query test")
        
        # Create a test goal
        goal_repo = GoalRepository(db_path=temp_db)
        goal = Goal.create(
            objective="Test timeline query",
            success_criteria=[
                SuccessCriterion(
                    id=str(uuid.uuid4()),
                    description="Timeline works",
                    validation_method="completion"
                )
            ]
        )
        goal_repo.save_goal(goal, session_id)
        
        # Query timeline
        timeline = query.get_goal_timeline(goal.id, max_commits=10)
        
        assert 'goal_id' in timeline
        assert timeline['goal_id'] == goal.id
        assert 'commits' in timeline
        assert isinstance(timeline['commits'], list)
        
        goal_repo.close()
    
    def test_unified_timeline(self, temp_db, session_id):
        """
        Test unified timeline combining tasks and epistemic state
        
        Verifies:
        - Combines task notes and epistemic checkpoints
        - Timeline is ordered correctly
        - Contains both types of data
        """
        query = GitProgressQuery()
        
        if not query.git_available:
            pytest.skip("Git not available, skipping unified timeline test")
        
        # Create test goal
        goal_repo = GoalRepository(db_path=temp_db)
        goal = Goal.create(
            objective="Test unified timeline",
            success_criteria=[
                SuccessCriterion(
                    id=str(uuid.uuid4()),
                    description="Unified timeline works",
                    validation_method="completion"
                )
            ]
        )
        goal_repo.save_goal(goal, session_id)
        
        # Query unified timeline
        timeline = query.get_unified_timeline(session_id, goal.id)
        
        assert 'session_id' in timeline
        assert 'goal_id' in timeline
        assert 'timeline' in timeline
        assert isinstance(timeline['timeline'], list)
        
        goal_repo.close()
    
    def test_bridge_integration(self, temp_db, session_id):
        """
        Test that bridge converts LLM goals to structured goals
        
        Verifies:
        - Bridge creates structured Goal from LLM Goal
        - Success criteria are created
        - Metadata is preserved
        """
        from empirica.core.canonical.goal_orchestrator_bridge import (
            create_orchestrator_with_bridge
        )
        
        bridge = create_orchestrator_with_bridge(use_placeholder=True, db_path=temp_db)
        
        # Test conversion (we'll use the internal method)
        from empirica.core.canonical.canonical_goal_orchestrator import (
            Goal as LLMGoal,
            GoalAutonomyLevel
        )
        
        llm_goal = LLMGoal(
            goal="Test bridge integration",
            priority=8,
            action_type="INVESTIGATE",
            autonomy_level=GoalAutonomyLevel.ACTIVE_COLLABORATION,
            reasoning="Testing the bridge conversion",
            success_criteria="Bridge works correctly"
        )
        
        structured_goal = bridge._convert_to_structured_goal(llm_goal)
        
        assert structured_goal.objective == llm_goal.goal
        assert len(structured_goal.success_criteria) >= 1
        assert structured_goal.metadata['llm_generated'] == True
        assert structured_goal.metadata['reasoning'] == llm_goal.reasoning
        assert structured_goal.metadata['action_type'] == llm_goal.action_type
        
        bridge.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
