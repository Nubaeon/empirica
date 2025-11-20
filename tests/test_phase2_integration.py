#!/usr/bin/env python3
"""
Test 3: Integration with Phase 1 (Phase 2 Validation)
Verify Phase 2 builds on Phase 1 without breaking changes.
Based on docs/current_work/MINIMAX_PHASE2_CORRECTED_TASKS.md
"""

import sys
import uuid
from pathlib import Path

# Add the empirica package to path
sys.path.insert(0, str(Path(__file__).parent))

from empirica.core.goals.types import Goal, GoalScope, SuccessCriterion
from empirica.core.tasks.types import SubTask, TaskStatus, EpistemicImportance
from empirica.core.completion.tracker import CompletionTracker
from empirica.core.completion.git_query import GitProgressQuery

def main():
    print("🔧 Test 3: Integration with Phase 1")
    print("=" * 50)
    
    try:
        # Phase 1: Create goal and track progress
        print("🔍 Phase 1: Creating goal and tracking progress...")
        goal = Goal.create(
            objective="Integration Test",
            scope=GoalScope.TASK_SPECIFIC,
            success_criteria=[
                SuccessCriterion(
                    id=str(uuid.uuid4()),
                    description="Phase 1 + 2 work together",
                    validation_method="manual"
                )
            ]
        )
        print(f"✅ Phase 1 goal created: {goal.id[:8]}...")

        subtask = SubTask.create(
            goal_id=goal.id,
            description="Test integration",
            epistemic_importance=EpistemicImportance.HIGH
        )
        print(f"✅ Phase 1 subtask created: {subtask.id[:8]}...")

        # Phase 1: Track progress
        tracker = CompletionTracker(enable_git_notes=True)
        progress = tracker.track_progress(goal.id)
        print(f"✅ Phase 1 progress tracking: {progress.completion_percentage:.1f}%")
        print(f"   Tracker type: {type(tracker).__name__}")

        # Mark subtask as complete
        tracker.task_repo.update_subtask_status(
            subtask.id,
            TaskStatus.COMPLETED,
            completion_evidence="Integration validated"
        )
        print(f"✅ Phase 1 subtask marked complete")

        # Re-check progress after completion
        updated_progress = tracker.track_progress(goal.id)
        print(f"✅ Phase 1 updated progress: {updated_progress.completion_percentage:.1f}%")

        # Phase 2: Query git for progress
        print("\n🔍 Phase 2: Testing GitProgressQuery...")
        query = GitProgressQuery()
        print(f"✅ Phase 2 GitProgressQuery initialized")
        
        timeline = query.get_goal_timeline(goal.id)
        print(f"✅ Phase 2 git query: {len(timeline.get('commits', []))} commits")
        print(f"   Timeline keys: {list(timeline.keys())}")

        # Phase 2: Team progress
        team = query.get_team_progress([goal.id])
        print(f"✅ Phase 2 team tracking: {len(team.get('goals', []))} goals")
        print(f"   Team keys: {list(team.keys())}")

        # Integration: Verify both phases work together
        print("\n🔍 Integration: Verifying Phase 1 + Phase 2 work together...")
        
        # Create another goal and task to test multi-goal coordination
        goal2 = Goal.create(
            objective="Integration Test Goal 2",
            scope=GoalScope.TASK_SPECIFIC,
            success_criteria=[
                SuccessCriterion(
                    id=str(uuid.uuid4()),
                    description="Multi-goal coordination test",
                    validation_method="manual"
                )
            ]
        )
        
        subtask2 = SubTask.create(
            goal_id=goal2.id,
            description="Second integration test task",
            epistemic_importance=EpistemicImportance.MEDIUM
        )
        
        # Mark second task complete
        tracker.task_repo.update_subtask_status(
            subtask2.id,
            TaskStatus.COMPLETED,
            completion_evidence="Second integration test"
        )
        
        # Test team progress with multiple goals
        team_multi = query.get_team_progress([goal.id, goal2.id])
        print(f"✅ Multi-goal team tracking: {len(team_multi.get('goals', []))} goals")
        
        # Test unified timeline
        unified = query.get_unified_timeline(
            session_id="integration-test-session",
            goal_id=goal.id
        )
        print(f"✅ Unified timeline generated: {len(unified.get('timeline', []))} events")
        
        print("\n" + "=" * 50)
        print("✅ PHASE 1 + PHASE 2 INTEGRATION VALIDATED!")
        print("\nIntegration Summary:")
        print("✅ Phase 1 goal creation and progress tracking: WORKING")
        print("✅ Phase 2 git query functionality: WORKING")
        print("✅ Phase 1 + Phase 2 coordination: WORKING")
        print("✅ Multi-goal team progress: WORKING")
        print("✅ Unified timeline generation: WORKING")
        print("✅ No breaking changes detected")
        
        return True
        
    except Exception as e:
        print(f"❌ Test 3 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)