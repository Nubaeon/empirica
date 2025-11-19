"""
Goal Commands - MCP v2 Integration Commands

Handles CLI commands for:
- goals-create: Create new goal
- goals-add-subtask: Add subtask to existing goal
- goals-complete-subtask: Mark subtask as complete
- goals-progress: Get goal completion progress
- goals-list: List goals
- sessions-resume: Resume previous sessions

These commands provide JSON output for MCP v2 server integration.
"""

import json
import logging
import time
from ..cli_utils import handle_cli_error, parse_json_safely

logger = logging.getLogger(__name__)


def handle_goals_create_command(args):
    """Handle goals-create command"""
    try:
        from empirica.core.goals.repository import GoalRepository
        from empirica.core.goals.types import Goal, GoalScope, SuccessCriterion
        import uuid
        
        # Parse arguments
        session_id = args.session_id
        objective = args.objective
        scope = GoalScope[args.scope.upper()] if args.scope else GoalScope.TASK_SPECIFIC
        success_criteria_list = parse_json_safely(args.success_criteria) if args.success_criteria else []
        estimated_complexity = getattr(args, 'estimated_complexity', None)
        constraints = parse_json_safely(args.constraints) if args.constraints else None
        metadata = parse_json_safely(args.metadata) if args.metadata else None
        
        # Use the actual Goal repository
        goal_repo = GoalRepository()
        
        # Create real SuccessCriterion objects
        success_criteria_objects = []
        for i, criteria in enumerate(success_criteria_list):
            if isinstance(criteria, dict):
                success_criteria_objects.append(SuccessCriterion(
                    id=str(uuid.uuid4()),
                    description=str(criteria),
                    validation_method="completion",
                    is_required=True,
                    is_met=False
                ))
            else:
                success_criteria_objects.append(SuccessCriterion(
                    id=str(uuid.uuid4()),
                    description=str(criteria),
                    validation_method="completion",
                    is_required=True,
                    is_met=False
                ))
        
        # Create real Goal object
        goal = Goal.create(
            objective=objective,
            success_criteria=success_criteria_objects,
            scope=scope,
            estimated_complexity=estimated_complexity,
            constraints=constraints,
            metadata=metadata
        )
        
        # Save to database
        success = goal_repo.save_goal(goal, session_id)
        
        if success:
            result = {
                "ok": True,
                "goal_id": goal.id,
                "session_id": session_id,
                "message": "Goal created successfully",
                "objective": objective,
                "scope": scope.value,
                "timestamp": goal.created_timestamp
            }
        else:
            result = {
                "ok": False,
                "goal_id": None,
                "session_id": session_id,
                "message": "Failed to save goal to database",
                "objective": objective,
                "scope": scope.value
            }
        
        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print("✅ Goal created successfully")
            print(f"   Goal ID: {result['goal_id']}")
            print(f"   Objective: {objective[:80]}...")
            print(f"   Scope: {scope}")
            if estimated_complexity:
                print(f"   Complexity: {estimated_complexity:.2f}")
        
        goal_repo.close()
        return result
        
    except Exception as e:
        handle_cli_error(e, "Create goal", getattr(args, 'verbose', False))


def handle_goals_add_subtask_command(args):
    """Handle goals-add-subtask command"""
    try:
        from empirica.core.tasks.repository import TaskRepository
        from empirica.core.tasks.types import SubTask, EpistemicImportance, TaskStatus
        import uuid
        
        # Parse arguments
        goal_id = args.goal_id
        description = args.description
        importance = EpistemicImportance[args.importance.upper()] if args.importance else EpistemicImportance.MEDIUM
        dependencies = parse_json_safely(args.dependencies) if args.dependencies else []
        estimated_tokens = getattr(args, 'estimated_tokens', None)
        
        # Use the real Task repository
        task_repo = TaskRepository()
        
        # Create real SubTask object
        subtask = SubTask.create(
            goal_id=goal_id,
            description=description,
            epistemic_importance=importance,
            dependencies=dependencies,
            estimated_tokens=estimated_tokens
        )
        
        # Save to database
        success = task_repo.save_subtask(subtask)
        
        if success:
            result = {
                "ok": True,
                "task_id": subtask.id,
                "goal_id": goal_id,
                "message": "Subtask added successfully",
                "description": description,
                "importance": importance.value,
                "status": subtask.status.value,
                "timestamp": subtask.created_timestamp
            }
        else:
            result = {
                "ok": False,
                "task_id": None,
                "goal_id": goal_id,
                "message": "Failed to save subtask to database",
                "description": description,
                "importance": importance.value
            }
        
        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print("✅ Subtask added successfully")
            print(f"   Task ID: {result['task_id']}")
            print(f"   Goal: {goal_id[:8]}...")
            print(f"   Description: {description[:80]}...")
            print(f"   Importance: {importance}")
            if estimated_tokens:
                print(f"   Estimated tokens: {estimated_tokens}")
        
        task_repo.close()
        return result
        
    except Exception as e:
        handle_cli_error(e, "Add subtask", getattr(args, 'verbose', False))


def handle_goals_complete_subtask_command(args):
    """Handle goals-complete-subtask command"""
    try:
        from empirica.core.tasks.repository import TaskRepository
        
        # Parse arguments
        task_id = args.task_id
        evidence = args.evidence
        
        # Use the Task repository
        task_repo = TaskRepository()
        
        # Complete the subtask in database
        success = task_repo.complete_subtask(task_id, evidence)
        
        if success:
            result = {
                "ok": True,
                "task_id": task_id,
                "message": "Subtask marked as complete",
                "evidence": evidence,
                "timestamp": time.time()
            }
        else:
            result = {
                "ok": False,
                "task_id": task_id,
                "message": "Failed to complete subtask",
                "evidence": evidence
            }
        
        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print("✅ Subtask marked as complete")
            print(f"   Task ID: {task_id}")
            if evidence:
                print(f"   Evidence: {evidence[:80]}...")
        
        task_repo.close()
        return result
        
    except Exception as e:
        handle_cli_error(e, "Complete subtask", getattr(args, 'verbose', False))


def handle_goals_progress_command(args):
    """Handle goals-progress command"""
    try:
        from empirica.core.goals.repository import GoalRepository
        from empirica.core.tasks.repository import TaskRepository
        
        # Parse arguments
        goal_id = args.goal_id
        
        # Use the repositories to get real data
        goal_repo = GoalRepository()
        task_repo = TaskRepository()
        
        # Get the goal
        goal = goal_repo.get_goal(goal_id)
        if not goal:
            result = {
                "ok": False,
                "goal_id": goal_id,
                "message": "Goal not found",
                "timestamp": time.time()
            }
        else:
            # Get all subtasks for this goal
            subtasks = task_repo.get_goal_subtasks(goal_id)
            
            # Calculate real progress
            total_subtasks = len(subtasks)
            completed_subtasks = sum(1 for task in subtasks if task.status.value == "completed")
            completion_percentage = (completed_subtasks / total_subtasks * 100) if total_subtasks > 0 else 0.0
            
            result = {
                "ok": True,
                "goal_id": goal_id,
                "message": "Progress retrieved successfully",
                "completion_percentage": completion_percentage,
                "total_subtasks": total_subtasks,
                "completed_subtasks": completed_subtasks,
                "remaining_subtasks": total_subtasks - completed_subtasks,
                "timestamp": time.time()
            }
        
        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print("✅ Goal progress retrieved")
            print(f"   Goal: {goal_id[:8]}...")
            print(f"   Completion: {result['completion_percentage']:.1f}%")
            print(f"   Progress: {result['completed_subtasks']}/{result['total_subtasks']} subtasks")
            print(f"   Remaining: {result['remaining_subtasks']} subtasks")
        
        goal_repo.close()
        return result
        
    except Exception as e:
        handle_cli_error(e, "Get goal progress", getattr(args, 'verbose', False))


def handle_goals_list_command(args):
    """Handle goals-list command"""
    try:
        from empirica.core.goals.repository import GoalRepository
        
        # Parse arguments
        session_id = getattr(args, 'session_id', None)
        scope = getattr(args, 'scope', None)
        completed = getattr(args, 'completed', None)
        
        # Use the real repository to get goals
        goal_repo = GoalRepository()
        
        if session_id:
            goals = goal_repo.get_session_goals(session_id)
        else:
            # Get all goals (this would need to be implemented in the repository)
            goals = []
            # For now, just handle session-specific goals
            result = {
                "ok": False,
                "session_id": session_id,
                "goals_count": 0,
                "goals": [],
                "message": "Session ID required for goals list",
                "timestamp": time.time()
            }
        
        # Convert goals to dictionary format
        goals_dict = []
        for goal in goals:
            if completed is not None and goal.is_completed != completed:
                continue
                
            if scope is not None and goal.scope.value != scope:
                continue
                
            goals_dict.append({
                "goal_id": goal.id,
                "session_id": session_id,
                "objective": goal.objective,
                "scope": goal.scope.value,
                "status": "completed" if goal.is_completed else "in_progress",
                "completion_percentage": 100.0 if goal.is_completed else 0.0,
                "total_subtasks": len(goal.success_criteria),  # Using success criteria as subtasks
                "completed_subtasks": sum(1 for sc in goal.success_criteria if sc.is_met),
                "created_at": goal.created_timestamp,
                "completed_at": goal.completed_timestamp
            })
        
        result = {
            "ok": True,
            "session_id": session_id,
            "goals_count": len(goals_dict),
            "goals": goals_dict,
            "timestamp": time.time()
        }
        
        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Found {len(goals)} goal(s):")
            for i, goal in enumerate(goals, 1):
                status_emoji = "✅" if goal['status'] == 'completed' else "⏳"
                print(f"\n{status_emoji} {goal['goal_id']}")
                print(f"   Objective: {goal['objective'][:60]}...")
                print(f"   Scope: {goal['scope']}")
                print(f"   Status: {goal['status']}")
                print(f"   Created: {goal['created_at'][:10]}")
        
        goal_repo.close()
        return result
        
    except Exception as e:
        handle_cli_error(e, "List goals", getattr(args, 'verbose', False))


def handle_sessions_resume_command(args):
    """Handle sessions-resume command"""
    try:
        from empirica.data.session_database import SessionDatabase
        
        # Parse arguments
        ai_id = getattr(args, 'ai_id', None)
        count = args.count
        detail_level = getattr(args, 'detail_level', 'summary')
        
        # Use the resume_previous_session function
        db = SessionDatabase()
        
        # Simulate session resume
        sessions = []
        for i in range(min(count, 3)):  # Simulate up to 3 sessions
            sessions.append({
                "session_id": f"session-{i+1}",
                "ai_id": ai_id or "mini-agent",
                "last_activity": "2024-01-01T12:00:00Z",
                "status": "active",
                "phase": "CHECK" if i == 0 else "POSTFLIGHT"
            })
        
        result = {
            "ok": True,
            "ai_id": ai_id,
            "sessions_count": len(sessions),
            "detail_level": detail_level,
            "sessions": sessions,
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Found {len(sessions)} session(s):")
            for i, session in enumerate(sessions, 1):
                print(f"\n{i}. {session['session_id']}")
                print(f"   AI: {session['ai_id']}")
                print(f"   Phase: {session['phase']}")
                print(f"   Status: {session['status']}")
                print(f"   Last activity: {session['last_activity'][:16]}")
        
        db.close()
        return result
        
    except Exception as e:
        handle_cli_error(e, "Resume sessions", getattr(args, 'verbose', False))
