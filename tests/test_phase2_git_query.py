#!/usr/bin/env python3
"""
Test 1: GitProgressQuery Functionality (Phase 2 Validation)
Based on corrected validation document at docs/current_work/MINIMAX_PHASE2_CORRECTED_TASKS.md
"""

import sys
import uuid
from pathlib import Path

# Add the empirica package to path
sys.path.insert(0, str(Path(__file__).parent))

from empirica.core.completion.git_query import GitProgressQuery
from empirica.core.goals.types import Goal, SuccessCriterion, GoalScope
from empirica.core.tasks.types import SubTask, EpistemicImportance

def main():
    print("🔧 Test 1: GitProgressQuery Functionality")
    print("=" * 50)
    
    try:
        # Create test goal
        goal = Goal.create(
            objective="Phase 2 Validation Test",
            scope=GoalScope.TASK_SPECIFIC,
            success_criteria=[
                SuccessCriterion(
                    id=str(uuid.uuid4()),
                    description="Git query tools work",
                    validation_method="manual"
                )
            ]
        )
        print(f"✅ Goal: {goal.id[:8]}...")
        
        # Create subtask
        subtask = SubTask.create(
            goal_id=goal.id,
            description="Validate git query functionality",
            epistemic_importance=EpistemicImportance.HIGH
        )
        print(f"✅ Subtask: {subtask.id[:8]}...")
        
        # Test GitProgressQuery
        query = GitProgressQuery()
        print(f"✅ GitProgressQuery instantiated")
        print(f"   Git available: {query.git_available}")
        
        # Test 1: Get goal timeline (MCP: query_git_progress)
        print("\n🔍 Testing query_git_progress...")
        timeline = query.get_goal_timeline(goal.id, max_commits=10)
        assert 'commits' in timeline, "Timeline must contain 'commits' key"
        assert isinstance(timeline['commits'], list), "Commits must be a list"
        print(f"✅ query_git_progress: {len(timeline['commits'])} commits")
        print(f"   Timeline structure: {list(timeline.keys())}")
        
        # Test 2: Get team progress (MCP: get_team_progress)
        print("\n🔍 Testing get_team_progress...")
        team_status = query.get_team_progress([goal.id])
        assert 'goals' in team_status, "Team status must contain 'goals' key"
        print(f"✅ get_team_progress: {len(team_status['goals'])} goals")
        print(f"   Team structure: {list(team_status.keys())}")
        
        # Test 3: Get unified timeline (MCP: get_unified_timeline)
        print("\n🔍 Testing get_unified_timeline...")
        unified = query.get_unified_timeline(
            session_id="test-session-123",
            goal_id=goal.id
        )
        print(f"✅ get_unified_timeline: executed successfully")
        print(f"   Unified structure: {list(unified.keys())}")
        
        print("\n✅ ALL GIT QUERY TOOLS VALIDATED!")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)