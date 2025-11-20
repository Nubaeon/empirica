#!/usr/bin/env python3
"""
Manual Test Script for Goal Architecture
Testing the goal system directly without pytest
"""

import sys
import tempfile
import uuid
from pathlib import Path

# Add the empirica package to path
sys.path.insert(0, str(Path(__file__).parent))

def test_goal_creation():
    """Test basic goal creation"""
    print("🧪 Testing Goal Creation...")
    try:
        from empirica.core.goals.types import Goal, SuccessCriterion, GoalScope
        from empirica.core.goals.repository import GoalRepository
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Test goal creation
        goal_repo = GoalRepository(db_path=db_path)
        
        success_criteria = [
            SuccessCriterion(
                description="Test completes successfully",
                validation_method="completion"
            )
        ]
        
        goal = Goal(
            session_id="test-session",
            objective="Test Goal Architecture Implementation",
            success_criteria=success_criteria,
            scope=GoalScope.TASK_SPECIFIC,
            estimated_complexity=0.5,
            metadata={"test": True}
        )
        
        # Save goal
        goal_id = goal_repo.save_goal(goal)
        print(f"✅ Goal created successfully with ID: {goal_id}")
        
        # Retrieve goal
        retrieved_goal = goal_repo.get_goal(goal_id)
        assert retrieved_goal.objective == goal.objective
        print("✅ Goal retrieval successful")
        
        goal_repo.close()
        
        # Clean up
        Path(db_path).unlink(missing_ok=True)
        
        return True
        
    except Exception as e:
        print(f"❌ Goal creation test failed: {e}")
        return False

def test_subtask_management():
    """Test subtask creation and completion"""
    print("🧪 Testing Subtask Management...")
    try:
        from empirica.core.tasks.types import SubTask, EpistemicImportance, TaskStatus
        from empirica.core.tasks.repository import TaskRepository
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        task_repo = TaskRepository(db_path=db_path)
        
        # Create subtask
        subtask = SubTask(
            goal_id="test-goal-id",
            description="Test subtask",
            epistemic_importance=EpistemicImportance.HIGH,
            estimated_tokens=500
        )
        
        subtask_id = task_repo.save_subtask(subtask)
        print(f"✅ Subtask created successfully with ID: {subtask_id}")
        
        # Mark as complete
        task_repo.mark_subtask_complete(subtask_id, evidence="manual-test")
        print("✅ Subtask completion successful")
        
        # Verify status
        retrieved_task = task_repo.get_subtask(subtask_id)
        assert retrieved_task.status == TaskStatus.COMPLETED
        print("✅ Subtask status verification successful")
        
        task_repo.close()
        
        # Clean up
        Path(db_path).unlink(missing_ok=True)
        
        return True
        
    except Exception as e:
        print(f"❌ Subtask management test failed: {e}")
        return False

def test_input_validation():
    """Test input validation"""
    print("🧪 Testing Input Validation...")
    try:
        from empirica.core.goals.validation import validate_goal_input
        
        # Test empty objective (should fail)
        try:
            validate_goal_input({
                "objective": "",
                "success_criteria": [{"description": "Test", "validation_method": "completion"}]
            })
            print("❌ Validation should have failed for empty objective")
            return False
        except ValueError as e:
            if "empty" in str(e).lower():
                print("✅ Empty objective validation working")
            else:
                print(f"❌ Wrong validation error: {e}")
                return False
        
        # Test invalid scope (should fail)
        try:
            validate_goal_input({
                "objective": "Test",
                "success_criteria": [{"description": "Test", "validation_method": "completion"}],
                "scope": "invalid_scope"
            })
            print("❌ Validation should have failed for invalid scope")
            return False
        except ValueError as e:
            if "scope" in str(e).lower():
                print("✅ Invalid scope validation working")
            else:
                print(f"❌ Wrong validation error: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Input validation test failed: {e}")
        return False

def main():
    """Run all manual tests"""
    print("🚀 Starting Manual Goal Architecture Tests")
    print("=" * 50)
    
    tests = [
        test_goal_creation,
        test_subtask_management,
        test_input_validation
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        print(f"\n📋 Running {test_func.__name__}...")
        if test_func():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Goal Architecture is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)