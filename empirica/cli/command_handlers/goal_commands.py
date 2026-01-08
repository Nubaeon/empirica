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
import sys
from ..cli_utils import handle_cli_error, parse_json_safely

logger = logging.getLogger(__name__)


def handle_goals_create_command(args):
    """Handle goals-create command - AI-first with legacy flag support"""
    try:
        from empirica.core.goals.repository import GoalRepository
        from empirica.core.tasks.repository import TaskRepository
        from empirica.core.goals.types import Goal, ScopeVector, SuccessCriterion
        import uuid
        import os

        # AI-FIRST MODE: Check if config file provided as positional argument
        config_data = None
        if hasattr(args, 'config') and args.config:
            # Read config from file or stdin
            if args.config == '-':
                # Read from stdin (sys imported at module level)
                config_data = parse_json_safely(sys.stdin.read())
            else:
                # Read from file
                if not os.path.exists(args.config):
                    print(json.dumps({"ok": False, "error": f"Config file not found: {args.config}"}))
                    sys.exit(1)
                with open(args.config, 'r') as f:
                    config_data = parse_json_safely(f.read())

        # Extract parameters from config or fall back to legacy flags
        if config_data:
            # AI-FIRST MODE: Use config file
            session_id = config_data.get('session_id')
            objective = config_data.get('objective')

            # Validate required fields in config
            if not session_id or not objective:
                print(json.dumps({
                    "ok": False,
                    "error": "Config file must include 'session_id' and 'objective' fields",
                    "received": {"session_id": bool(session_id), "objective": bool(objective)}
                }))
                sys.exit(1)

            # Parse scope from config (nested or flat)
            scope_config = config_data.get('scope', {})
            if isinstance(scope_config, dict):
                scope_breadth = scope_config.get('breadth', 0.3)
                scope_duration = scope_config.get('duration', 0.2)
                scope_coordination = scope_config.get('coordination', 0.1)
            else:
                scope_breadth = 0.3
                scope_duration = 0.2
                scope_coordination = 0.1

            success_criteria_list = config_data.get('success_criteria', [])
            estimated_complexity = config_data.get('estimated_complexity')
            constraints = config_data.get('constraints')
            metadata = config_data.get('metadata')
            output_format = 'json'  # AI-first always uses JSON output

        else:
            # LEGACY MODE: Use CLI flags
            session_id = args.session_id
            objective = args.objective

            # Validate required fields for legacy mode
            if not session_id or not objective:
                print(json.dumps({
                    "ok": False,
                    "error": "Legacy mode requires --session-id and --objective flags",
                    "hint": "For AI-first mode, use: empirica goals-create config.json"
                }))
                sys.exit(1)
            scope_breadth = float(args.scope_breadth) if hasattr(args, 'scope_breadth') and args.scope_breadth else 0.3
            scope_duration = float(args.scope_duration) if hasattr(args, 'scope_duration') and args.scope_duration else 0.2
            scope_coordination = float(args.scope_coordination) if hasattr(args, 'scope_coordination') and args.scope_coordination else 0.1
            estimated_complexity = getattr(args, 'estimated_complexity', None)
            constraints = parse_json_safely(args.constraints) if args.constraints else None
            metadata = parse_json_safely(args.metadata) if args.metadata else None
            output_format = getattr(args, 'output', 'json')  # Default to JSON (AI-first)

            # LEGACY: Handle success_criteria from flags (file, stdin, or inline)
            success_criteria_list = []
            if hasattr(args, 'success_criteria_file') and args.success_criteria_file:
                if not os.path.exists(args.success_criteria_file):
                    print(f"❌ Error: File not found: {args.success_criteria_file}", file=sys.stderr)
                    sys.exit(1)
                with open(args.success_criteria_file, 'r') as f:
                    success_criteria_list = parse_json_safely(f.read())
            elif hasattr(args, 'success_criteria') and args.success_criteria:
                if args.success_criteria == '-':
                    # sys imported at module level
                    success_criteria_list = parse_json_safely(sys.stdin.read())
                elif args.success_criteria.strip().startswith('['):
                    success_criteria_list = parse_json_safely(args.success_criteria)
                else:
                    success_criteria_list = [args.success_criteria]

            # Safety check
            if isinstance(success_criteria_list, str):
                success_criteria_list = [success_criteria_list]

        # Build scope vector (works for both modes)
        scope = ScopeVector(
            breadth=scope_breadth,
            duration=scope_duration,
            coordination=scope_coordination
        )
        
        # Validate success criteria (make it optional now)
        if not success_criteria_list:
            # Make a default success criterion if none provided
            success_criteria_list = ["Goal completion achieved"]
        
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
            # BEADS Integration (Optional): Create linked issue tracker item
            beads_issue_id = None
            
            # Check if BEADS should be used (priority: flag > config file > project default)
            use_beads = getattr(args, 'use_beads', False) or (config_data and config_data.get('use_beads', False))
            
            # If not explicitly set, check project-level default
            if not use_beads and not hasattr(args, 'use_beads'):
                try:
                    from empirica.config.project_config_loader import load_project_config
                    project_config = load_project_config()
                    if project_config:
                        use_beads = project_config.default_use_beads
                        if use_beads:
                            logger.info("Using BEADS integration from project config default")
                except Exception as e:
                    logger.debug(f"Could not load project config for BEADS default: {e}")
            
            if use_beads:
                try:
                    from empirica.integrations.beads import BeadsAdapter
                    beads = BeadsAdapter()
                    
                    if beads.is_available():
                        # Map scope to BEADS priority (1=high, 2=medium, 3=low)
                        priority = 1 if scope_breadth > 0.7 else (2 if scope_breadth > 0.3 else 3)
                        
                        # Determine issue type based on scope
                        issue_type = "epic" if scope_breadth > 0.7 else "feature"
                        
                        # Create BEADS issue
                        beads_issue_id = beads.create_issue(
                            title=objective,
                            description=f"Empirica Goal {goal.id[:8]}\nScope: breadth={scope_breadth:.2f}, duration={scope_duration:.2f}",
                            priority=priority,
                            issue_type=issue_type,
                            labels=["empirica"]
                        )
                        
                        if beads_issue_id:
                            # Update goal with BEADS link
                            from empirica.data.session_database import SessionDatabase
                            temp_db = SessionDatabase()
                            temp_db.conn.execute(
                                "UPDATE goals SET beads_issue_id = ? WHERE id = ?",
                                (beads_issue_id, goal.id)
                            )
                            temp_db.conn.commit()
                            temp_db.close()
                            logger.info(f"Linked goal {goal.id[:8]} to BEADS issue {beads_issue_id}")
                    else:
                        # BEADS requested but not available - provide helpful error
                        import sys as _sys  # Local import to ensure availability
                        error_msg = (
                            "⚠️  BEADS integration requested but 'bd' CLI not found.\n\n"
                            "To use BEADS issue tracking:\n"
                            "  1. Install BEADS: pip install beads-project\n"
                            "  2. Initialize: bd init\n"
                            "  3. Try again: empirica goals-create --use-beads ...\n\n"
                            "Or omit --use-beads to create goal without issue tracking.\n"
                            "Learn more: https://github.com/cased/beads"
                        )
                        if output_format == 'json':
                            logger.warning("BEADS integration requested but bd CLI not available")
                            print(f"\n{error_msg}", file=_sys.stderr)
                        else:
                            print(f"\n{error_msg}", file=_sys.stderr)
                        # Continue without BEADS - goal already created successfully
                except Exception as e:
                    logger.warning(f"BEADS integration failed: {e}")
                    # Continue without BEADS - it's optional
            
            result = {
                "ok": True,
                "goal_id": goal.id,
                "session_id": session_id,
                "message": "Goal created successfully",
                "objective": objective,
                "scope": scope.to_dict(),
                "timestamp": goal.created_timestamp,
                "beads_issue_id": beads_issue_id  # Include BEADS link in response
            }
            
            # ===== SMART CHECK PROMPT: Scope-Based =====
            # Show CHECK recommendation for high-scope goals
            if scope_breadth >= 0.6 or scope_duration >= 0.5:
                check_prompt = {
                    "type": "check_recommendation",
                    "reason": "high_scope",
                    "message": "💡 High-scope goal: Consider running CHECK after initial investigation",
                    "scope_trigger": {
                        "breadth": scope_breadth if scope_breadth >= 0.6 else None,
                        "duration": scope_duration if scope_duration >= 0.5 else None
                    },
                    "suggested_timing": "after 1-2 subtasks or 30+ minutes",
                    "command": f"empirica check --session-id {session_id}"
                }
                result["check_recommendation"] = check_prompt
            
            # Store goal in git notes for cross-AI discovery (Phase 1: Git Automation)
            try:
                from empirica.core.canonical.empirica_git import GitGoalStore
                
                ai_id = getattr(args, 'ai_id', 'empirica_cli')
                goal_store = GitGoalStore()
                goal_data = {
                    'objective': objective,
                    'scope': scope.to_dict(),
                    'success_criteria': [sc.description for sc in success_criteria_objects],
                    'estimated_complexity': estimated_complexity,
                    'constraints': constraints,
                    'metadata': metadata
                }
                
                goal_store.store_goal(
                    goal_id=goal.id,
                    session_id=session_id,
                    ai_id=ai_id,
                    goal_data=goal_data
                )
                logger.debug(f"Goal {goal.id[:8]} stored in git notes for cross-AI discovery")
            except Exception as e:
                # Safe degradation - don't fail goal creation if git storage fails
                logger.debug(f"Git goal storage skipped: {e}")
        else:
            result = {
                "ok": False,
                "goal_id": None,
                "session_id": session_id,
                "message": "Failed to save goal to database",
                "objective": objective,
                "scope": scope.to_dict()
            }
        
        # Format output (AI-first = JSON by default)
        if output_format == 'json':
            print(json.dumps(result, indent=2))
            # Add helpful hint if BEADS not used (only in JSON mode for parsability)
            if result['ok'] and not beads_issue_id and not use_beads:
                import sys as _sys
                print(f"\n💡 Tip: Add --use-beads flag to track this goal in BEADS issue tracker", file=_sys.stderr)
        else:
            # Human-readable output (legacy)
            if result['ok']:
                print("✅ Goal created successfully")
                print(f"   Goal ID: {result['goal_id']}")
                print(f"   Objective: {objective[:80]}..." if len(objective) > 80 else f"   Objective: {objective}")
                print(f"   Scope: breadth={scope.breadth}, duration={scope.duration}, coordination={scope.coordination}")
                if estimated_complexity:
                    print(f"   Complexity: {estimated_complexity:.2f}")
                if beads_issue_id:
                    print(f"   BEADS Issue: {beads_issue_id}")
                elif not use_beads:
                    print(f"\n💡 Tip: Add --use-beads flag to track goals in BEADS issue tracker")
            else:
                print(f"❌ {result.get('message', 'Failed to create goal')}")
        
        goal_repo.close()
        # Return None to avoid exit code issues and duplicate output
        return None

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
            # BEADS Integration (Optional): Create child issue with dependency
            beads_subtask_id = None
            use_beads = getattr(args, 'use_beads', False)
            
            if use_beads:
                try:
                    from empirica.integrations.beads import BeadsAdapter
                    from empirica.data.session_database import SessionDatabase
                    
                    # Get parent goal's BEADS ID
                    db = SessionDatabase()
                    cursor = db.conn.execute(
                        "SELECT beads_issue_id FROM goals WHERE id = ?",
                        (goal_id,)
                    )
                    row = cursor.fetchone()
                    parent_beads_id = row[0] if row and row[0] else None
                    
                    if parent_beads_id:
                        beads = BeadsAdapter()
                        if beads.is_available():
                            # Map importance to BEADS priority
                            priority_map = {
                                EpistemicImportance.CRITICAL: 1,
                                EpistemicImportance.HIGH: 1,
                                EpistemicImportance.MEDIUM: 2,
                                EpistemicImportance.LOW: 3
                            }
                            priority = priority_map.get(importance, 2)
                            
                            # Create BEADS child issue (gets hierarchical ID like bd-a1b2.1)
                            beads_subtask_id = beads.create_issue(
                                title=description,
                                description=f"Empirica Subtask {subtask.id[:8]}\nParent Goal: {goal_id[:8]}",
                                priority=priority,
                                issue_type="task",
                                labels=["empirica", "subtask"]
                            )
                            
                            if beads_subtask_id:
                                # Add dependency: subtask blocks parent
                                beads.add_dependency(
                                    child_id=beads_subtask_id,
                                    parent_id=parent_beads_id,
                                    dep_type='blocks'
                                )
                                
                                # Store BEADS link in subtask_data
                                db.conn.execute("""
                                    UPDATE subtasks 
                                    SET subtask_data = json_set(subtask_data, '$.beads_issue_id', ?)
                                    WHERE id = ?
                                """, (beads_subtask_id, subtask.id))
                                db.conn.commit()
                                logger.info(f"Linked subtask {subtask.id[:8]} to BEADS issue {beads_subtask_id}")
                    else:
                        logger.warning("Parent goal has no BEADS issue - cannot create linked subtask")
                    
                    db.close()
                except Exception as e:
                    logger.warning(f"BEADS subtask integration failed: {e}")
                    # Continue without BEADS - it's optional
            
            result = {
                "ok": True,
                "task_id": subtask.id,
                "goal_id": goal_id,
                "message": "Subtask added successfully",
                "description": description,
                "importance": importance.value,
                "status": subtask.status.value,
                "timestamp": subtask.created_timestamp,
                "beads_issue_id": beads_subtask_id  # Include BEADS link
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
        # Return None to avoid exit code issues and duplicate output
        return None

    except Exception as e:
        handle_cli_error(e, "Add subtask", getattr(args, 'verbose', False))


def handle_goals_add_dependency_command(args):
    """Handle goals-add-dependency command - add goal-to-goal dependency"""
    try:
        from empirica.data.session_database import SessionDatabase
        import uuid

        # Parse arguments
        goal_id = args.goal_id
        depends_on_goal_id = args.depends_on
        dependency_type = getattr(args, 'type', 'blocks')
        description = getattr(args, 'description', None)
        output_format = getattr(args, 'output', 'human')

        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Verify both goals exist
        cursor.execute("SELECT id, objective FROM goals WHERE id = ?", (goal_id,))
        goal_row = cursor.fetchone()
        if not goal_row:
            result = {
                "ok": False,
                "error": f"Goal not found: {goal_id}",
                "hint": "Use 'empirica goals-list-all' to see available goals"
            }
            print(json.dumps(result, indent=2) if output_format == 'json' else f"Error: {result['error']}")
            db.close()
            return 1

        cursor.execute("SELECT id, objective FROM goals WHERE id = ?", (depends_on_goal_id,))
        depends_row = cursor.fetchone()
        if not depends_row:
            result = {
                "ok": False,
                "error": f"Dependency goal not found: {depends_on_goal_id}",
                "hint": "Use 'empirica goals-list-all' to see available goals"
            }
            print(json.dumps(result, indent=2) if output_format == 'json' else f"Error: {result['error']}")
            db.close()
            return 1

        # Check for circular dependency (simple check: A depends on B, B depends on A)
        cursor.execute("""
            SELECT id FROM goal_dependencies
            WHERE goal_id = ? AND depends_on_goal_id = ?
        """, (depends_on_goal_id, goal_id))
        if cursor.fetchone():
            result = {
                "ok": False,
                "error": "Circular dependency detected",
                "detail": f"Goal {depends_on_goal_id[:8]}... already depends on {goal_id[:8]}..."
            }
            print(json.dumps(result, indent=2) if output_format == 'json' else f"Error: {result['error']}")
            db.close()
            return 1

        # Check if dependency already exists
        cursor.execute("""
            SELECT id FROM goal_dependencies
            WHERE goal_id = ? AND depends_on_goal_id = ?
        """, (goal_id, depends_on_goal_id))
        if cursor.fetchone():
            result = {
                "ok": False,
                "error": "Dependency already exists",
                "goal_id": goal_id,
                "depends_on": depends_on_goal_id
            }
            print(json.dumps(result, indent=2) if output_format == 'json' else f"Error: {result['error']}")
            db.close()
            return 1

        # Insert dependency
        dep_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO goal_dependencies (id, goal_id, depends_on_goal_id, dependency_type, description)
            VALUES (?, ?, ?, ?, ?)
        """, (dep_id, goal_id, depends_on_goal_id, dependency_type, description))
        db.conn.commit()

        result = {
            "ok": True,
            "dependency_id": dep_id,
            "goal_id": goal_id,
            "goal_objective": goal_row[1][:50] + "..." if len(goal_row[1]) > 50 else goal_row[1],
            "depends_on": depends_on_goal_id,
            "depends_on_objective": depends_row[1][:50] + "..." if len(depends_row[1]) > 50 else depends_row[1],
            "type": dependency_type,
            "description": description,
            "message": f"Dependency added: {goal_id[:8]}... {dependency_type} {depends_on_goal_id[:8]}..."
        }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            type_labels = {
                'blocks': 'is blocked by',
                'informs': 'is informed by',
                'extends': 'extends'
            }
            print(f"Goal dependency added")
            print(f"  {result['goal_objective']}")
            print(f"    {type_labels.get(dependency_type, dependency_type)}")
            print(f"  {result['depends_on_objective']}")
            if description:
                print(f"  Reason: {description}")

        db.close()
        return None

    except Exception as e:
        handle_cli_error(e, "Add goal dependency", getattr(args, 'verbose', False))


def handle_goals_complete_subtask_command(args):
    """Handle goals-complete-subtask command"""
    try:
        from empirica.core.tasks.repository import TaskRepository
        from empirica.core.tasks.types import TaskStatus
        
        # Parse arguments with backward compatibility
        # Priority: subtask_id (new) > task_id (deprecated)
        if hasattr(args, 'subtask_id') and args.subtask_id:
            task_id = args.subtask_id
            if hasattr(args, 'task_id') and args.task_id and args.task_id != args.subtask_id:
                print("⚠️  Warning: Both --subtask-id and --task-id provided. Using --subtask-id.", file=sys.stderr)
        elif hasattr(args, 'task_id') and args.task_id:
            task_id = args.task_id
            print("ℹ️  Note: --task-id is deprecated. Please use --subtask-id instead.", file=sys.stderr)
        else:
            print(json.dumps({
                "ok": False,
                "error": "Either --subtask-id or --task-id is required",
                "hint": "Preferred: empirica goals-complete-subtask --subtask-id <ID>"
            }))
            sys.exit(1)
            
        evidence = args.evidence
        
        # Use the Task repository
        task_repo = TaskRepository()
        
        # Complete the subtask in database
        success = task_repo.update_subtask_status(task_id, TaskStatus.COMPLETED, evidence)
        
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
        # Return None to avoid exit code issues and duplicate output
        return None

    except Exception as e:
        handle_cli_error(e, "Complete subtask", getattr(args, 'verbose', False))


def handle_goals_progress_command(args):
    """Handle goals-progress command"""
    try:
        from empirica.core.goals.repository import GoalRepository
        from empirica.core.tasks.repository import TaskRepository
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
            if result.get('ok'):
                print("✅ Goal progress retrieved")
                print(f"   Goal: {goal_id[:8]}...")
                print(f"   Completion: {result['completion_percentage']:.1f}%")
                print(f"   Progress: {result['completed_subtasks']}/{result['total_subtasks']} subtasks")
                print(f"   Remaining: {result['remaining_subtasks']} subtasks")
            else:
                print(f"❌ {result.get('message', 'Error retrieving goal progress')}")
                print(f"   Goal ID: {goal_id}")
        
        goal_repo.close()
        # Return None to avoid exit code issues and duplicate output
        return None

    except Exception as e:
        handle_cli_error(e, "Get goal progress", getattr(args, 'verbose', False))


def handle_goals_list_command(args):
    """Handle goals-list command"""
    try:
        from empirica.core.goals.repository import GoalRepository
        from empirica.core.tasks.repository import TaskRepository
        
        # Parse arguments
        session_id = getattr(args, 'session_id', None)
        ai_id = getattr(args, 'ai_id', None)
        completed = getattr(args, 'completed', None)
        
        # Parse scope filtering parameters
        scope_filters = {
            'breadth_min': getattr(args, 'scope_breadth_min', None),
            'breadth_max': getattr(args, 'scope_breadth_max', None),
            'duration_min': getattr(args, 'scope_duration_min', None),
            'duration_max': getattr(args, 'scope_duration_max', None),
            'coordination_min': getattr(args, 'scope_coordination_min', None),
            'coordination_max': getattr(args, 'scope_coordination_max', None),
        }
        
        # Use the real repository to get goals
        goal_repo = GoalRepository()
        task_repo = TaskRepository()
        
        if session_id:
            goals = goal_repo.get_session_goals(session_id)
        elif ai_id:
            # Get goals for all sessions of a specific AI
            from empirica.data.session_database import SessionDatabase
            db = SessionDatabase()
            cursor = db.conn.cursor()

            # Get all session IDs for the specified AI
            cursor.execute("""
                SELECT session_id FROM sessions WHERE ai_id = ?
                ORDER BY start_time DESC
            """, (ai_id,))
            session_ids = [row[0] for row in cursor.fetchall()]

            # Get goals from all those sessions
            goals = []
            for sid in session_ids:
                session_goals = goal_repo.get_session_goals(sid)
                goals.extend(session_goals)

            db.close()
        else:
            # Show helpful reminder with preview of recent goals
            from empirica.data.session_database import SessionDatabase
            preview_db = SessionDatabase()
            cursor = preview_db.conn.cursor()

            # Get 5 most recent goals across all sessions
            cursor.execute("""
                SELECT g.id, g.objective, g.created_timestamp, g.session_id,
                       (SELECT COUNT(*) FROM subtasks WHERE goal_id = g.id) as total_subtasks,
                       (SELECT COUNT(*) FROM subtasks WHERE goal_id = g.id AND status = 'completed') as completed_subtasks
                FROM goals g
                ORDER BY g.created_timestamp DESC
                LIMIT 5
            """)

            preview_goals = []
            for row in cursor.fetchall():
                total = row[4] or 0
                completed = row[5] or 0
                completion_pct = (completed / total * 100) if total > 0 else 0.0

                preview_goals.append({
                    "goal_id": row[0],
                    "objective": row[1][:80] + "..." if len(row[1]) > 80 else row[1],
                    "created_at": row[2],
                    "session_id": row[3],
                    "completion_percentage": completion_pct,
                    "subtasks": f"{completed}/{total}"
                })

            preview_db.close()
            
            result = {
                "ok": False,
                "session_id": None,
                "message": "Session ID required for full goals list",
                "hint": "Create a session: empirica session-create --ai-id <YOUR_AI_ID>",
                "hint2": "Then query goals: empirica goals-list --session-id <SESSION_ID>",
                "recent_goals_preview": preview_goals,
                "preview_count": len(preview_goals),
                "preview_note": "Showing last 5 goals across all sessions as preview",
                "timestamp": time.time()
            }
            
            if hasattr(args, 'output') and args.output == 'json':
                print(json.dumps(result, indent=2))
            else:
                print("⚠️  Session ID required for full goals list")
                print()
                print("📋 Quick Start:")
                print("   1. Create session: empirica session-create --ai-id <YOUR_AI_ID>")
                print("   2. List goals: empirica goals-list --session-id <SESSION_ID>")
                print()
                if preview_goals:
                    print(f"🔍 Recent Goals Preview (last {len(preview_goals)}):")
                    for i, goal in enumerate(preview_goals, 1):
                        status_emoji = "✅" if goal['completion_percentage'] == 100.0 else "⏳"
                        print(f"   {status_emoji} {i}. {goal['objective']}")
                        print(f"      ID: {goal['goal_id'][:8]}... | Session: {goal['session_id'][:8]}... | Progress: {goal['subtasks']}")
                else:
                    print("   (No goals found in database)")
            
            goal_repo.close()
            return result
        
        # Convert goals to dictionary format with proper scope filtering
        goals_dict = []
        for goal in goals:
            # Filter by completion status
            if completed is not None:
                subtasks = task_repo.get_goal_subtasks(goal.id)
                total_subtasks = len(subtasks)
                completed_subtasks = sum(1 for task in subtasks if task.status.value == "completed")
                completion_percentage = (completed_subtasks / total_subtasks * 100) if total_subtasks > 0 else 0.0
                is_completed = completion_percentage == 100.0
                
                if is_completed != completed:
                    continue
            
            # Filter by scope parameters
            scope = goal.scope
            skip_goal = False
            
            # Check breadth range
            if scope_filters['breadth_min'] is not None and scope.breadth < scope_filters['breadth_min']:
                skip_goal = True
            if scope_filters['breadth_max'] is not None and scope.breadth > scope_filters['breadth_max']:
                skip_goal = True
            
            # Check duration range
            if scope_filters['duration_min'] is not None and scope.duration < scope_filters['duration_min']:
                skip_goal = True
            if scope_filters['duration_max'] is not None and scope.duration > scope_filters['duration_max']:
                skip_goal = True
            
            # Check coordination range
            if scope_filters['coordination_min'] is not None and scope.coordination < scope_filters['coordination_min']:
                skip_goal = True
            if scope_filters['coordination_max'] is not None and scope.coordination > scope_filters['coordination_max']:
                skip_goal = True
            
            if skip_goal:
                continue
                
            # Get subtasks for this goal to calculate real progress
            subtasks = task_repo.get_goal_subtasks(goal.id)
            total_subtasks = len(subtasks)
            completed_subtasks = sum(1 for task in subtasks if task.status.value == "completed")
            completion_percentage = (completed_subtasks / total_subtasks * 100) if total_subtasks > 0 else 0.0
            
            goals_dict.append({
                "goal_id": goal.id,
                "session_id": session_id,
                "objective": goal.objective,
                "scope": goal.scope.to_dict(),
                "status": "completed" if completion_percentage == 100.0 else "in_progress",
                "completion_percentage": completion_percentage,
                "total_subtasks": total_subtasks,
                "completed_subtasks": completed_subtasks,
                "created_at": goal.created_timestamp,
                "completed_at": goal.completed_timestamp
            })
        
        result = {
            "ok": True,
            "session_id": session_id,
            "ai_id": ai_id,
            "goals_count": len(goals_dict),
            "goals": goals_dict,
            "scope_filters_applied": {k: v for k, v in scope_filters.items() if v is not None},
            "timestamp": time.time()
        }
        
        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            if session_id:
                print(f"✅ Found {len(goals_dict)} goal(s) for session {session_id}:")
            elif ai_id:
                print(f"✅ Found {len(goals_dict)} goal(s) for AI {ai_id}:")
            else:
                print(f"✅ Found {len(goals_dict)} goal(s):")
            
            # Show applied filters if any
            active_filters = [f"{k.replace('_', ' ').title()}: {v}" for k, v in scope_filters.items() if v is not None]
            if active_filters:
                print(f"   Filters: {', '.join(active_filters)}")
            
            for i, goal in enumerate(goals_dict, 1):
                status_emoji = "✅" if goal['status'] == 'completed' else "⏳"
                print(f"\n{status_emoji} Goal {i}: {goal['goal_id']}")
                print(f"   Objective: {goal['objective'][:60]}...")
                print(f"   Scope: breadth={goal['scope']['breadth']:.2f}, duration={goal['scope']['duration']:.2f}, coordination={goal['scope']['coordination']:.2f}")
                print(f"   Progress: {float(goal['completion_percentage']):.1f}% ({goal['completed_subtasks']}/{goal['total_subtasks']} subtasks)")
                # Convert timestamp to date string
                from datetime import datetime
                created_date = datetime.fromtimestamp(goal['created_at']).strftime('%Y-%m-%d')
                print(f"   Created: {created_date}")
        
        goal_repo.close()
        task_repo.close()  # Close task repository too
        # Return None to avoid exit code issues and duplicate output
        return None

    except Exception as e:
        handle_cli_error(e, "List goals", getattr(args, 'verbose', False))


def handle_goals_get_subtasks_command(args):
    """Handle goals-get-subtasks command - get detailed subtask information"""
    try:
        from empirica.core.tasks.repository import TaskRepository
        
        # Parse arguments
        goal_id = args.goal_id
        
        # Use task repository to get subtasks
        task_repo = TaskRepository()
        subtasks = task_repo.get_goal_subtasks(goal_id)
        
        if not subtasks:
            result = {
                "ok": False,
                "goal_id": goal_id,
                "message": "No subtasks found for goal",
                "subtasks": [],
                "timestamp": time.time()
            }
        else:
            # Convert subtasks to dict format
            subtasks_dict = []
            for task in subtasks:
                subtasks_dict.append({
                    "task_id": task.id,
                    "description": task.description,
                    "status": task.status.value,
                    "importance": task.epistemic_importance.value,
                    "created_at": task.created_timestamp,
                    "completed_at": task.completed_timestamp if hasattr(task, 'completed_timestamp') else None,
                    "dependencies": task.dependencies if hasattr(task, 'dependencies') else [],
                    "estimated_tokens": task.estimated_tokens if hasattr(task, 'estimated_tokens') else None,
                    "actual_tokens": task.actual_tokens if hasattr(task, 'actual_tokens') else None,
                    "completion_evidence": task.completion_evidence if hasattr(task, 'completion_evidence') else None,
                    "notes": task.notes if hasattr(task, 'notes') else "",
                    "findings": task.findings if hasattr(task, 'findings') else [],
                    "unknowns": task.unknowns if hasattr(task, 'unknowns') else [],
                    "dead_ends": task.dead_ends if hasattr(task, 'dead_ends') else []
                })
            
            completed_count = sum(1 for t in subtasks if t.status.value == "completed")
            
            result = {
                "ok": True,
                "goal_id": goal_id,
                "message": "Subtasks retrieved successfully",
                "subtasks_count": len(subtasks),
                "completed_count": completed_count,
                "in_progress_count": len(subtasks) - completed_count,
                "subtasks": subtasks_dict,
                "timestamp": time.time()
            }
        
        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            if result.get('ok'):
                print(f"✅ Found {result['subtasks_count']} subtask(s) for goal {goal_id[:8]}...")
                print(f"   Progress: {result['completed_count']}/{result['subtasks_count']} completed")
                print()
                for i, task in enumerate(result['subtasks'], 1):
                    status_icon = "✅" if task['status'] == "completed" else "⏳"
                    print(f"{status_icon} {i}. {task['description']}")
                    print(f"   Status: {task['status']} | Importance: {task.get('importance', 'medium')}")
                    print(f"   Task ID: {task['task_id'][:8]}...")
                    if task.get('findings'):
                        print(f"   Findings: {len(task['findings'])} discovered")
                    if task.get('unknowns'):
                        print(f"   Unknowns: {len(task['unknowns'])} remaining")
                    if task.get('dead_ends'):
                        print(f"   Dead ends: {len(task['dead_ends'])} avoided")
            else:
                print(f"❌ {result.get('message', 'Error retrieving subtasks')}")
        
        task_repo.close()
        # Return None to avoid exit code issues and duplicate output
        return None

    except Exception as e:
        handle_cli_error(e, "Get subtasks", getattr(args, 'verbose', False))


def handle_sessions_resume_command(args):
    """Handle sessions-resume command"""
    try:
        from empirica.data.session_database import SessionDatabase
        
        # Parse arguments
        ai_id = getattr(args, 'ai_id', None)
        count = args.count
        detail_level = getattr(args, 'detail_level', 'summary')
        
        # Use real database queries
        db = SessionDatabase()
        
        # Query real sessions from database
        cursor = db.conn.cursor()
        
        if ai_id:
            # Get sessions for specific AI
            cursor.execute("""
                SELECT session_id, ai_id, start_time, end_time,
                       total_cascades, avg_confidence, session_notes
                FROM sessions
                WHERE ai_id = ?
                ORDER BY start_time DESC
                LIMIT ?
            """, (ai_id, count))
        else:
            # Get recent sessions for all AIs
            cursor.execute("""
                SELECT session_id, ai_id, start_time, end_time,
                       total_cascades, avg_confidence, session_notes
                FROM sessions
                ORDER BY start_time DESC
                LIMIT ?
            """, (count,))
        
        # Convert rows to real session data
        sessions = []
        for row in cursor.fetchall():
            session_data = dict(row)
            
            # Calculate current phase from cascades if available
            cascade_cursor = db.conn.cursor()
            cascade_cursor.execute("""
                SELECT preflight_completed, think_completed, plan_completed, 
                       investigate_completed, check_completed, act_completed, postflight_completed 
                FROM cascades 
                WHERE session_id = ? ORDER BY started_at DESC LIMIT 1
            """, (session_data['session_id'],))
            
            cascade_row = cascade_cursor.fetchone()
            if cascade_row:
                # Determine current phase based on completion status
                if cascade_row[6]:  # postflight_completed
                    current_phase = "POSTFLIGHT"
                elif cascade_row[5]:  # act_completed
                    current_phase = "ACT"
                elif cascade_row[4]:  # check_completed
                    current_phase = "CHECK"
                elif cascade_row[3]:  # investigate_completed
                    current_phase = "INVESTIGATE"
                elif cascade_row[2]:  # plan_completed
                    current_phase = "PLAN"
                elif cascade_row[1]:  # think_completed
                    current_phase = "THINK"
                else:
                    current_phase = "PREFLIGHT"
            else:
                current_phase = "PREFLIGHT"
            
            sessions.append({
                "session_id": session_data['session_id'],  # Real UUID!
                "ai_id": session_data['ai_id'],
                "start_time": session_data['start_time'],
                "end_time": session_data['end_time'],
                "status": "completed" if session_data['end_time'] else "active",
                "phase": current_phase,
                "total_cascades": session_data['total_cascades'],
                "avg_confidence": session_data['avg_confidence'],
                "last_activity": session_data['start_time'],  # Real timestamp!
            })
        
        result = {
            "ok": True,
            "ai_id": ai_id,
            "sessions_count": len(sessions),
            "detail_level": detail_level,
            "sessions": sessions,
            "timestamp": time.time()
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
                print(f"   Start time: {str(session['start_time'])[:16]}")
                if session['total_cascades'] > 0:
                    print(f"   Cascades: {session['total_cascades']}")
        
        db.close()
        # Return None to avoid exit code issues and duplicate output
        return None

    except Exception as e:
        handle_cli_error(e, "Resume sessions", getattr(args, 'verbose', False))


def handle_goals_list_all_command(args):
    """Handle goals-list-all command - show ALL goals with inline subtasks"""
    try:
        from empirica.data.session_database import SessionDatabase

        status_filter = getattr(args, 'status', 'active')
        limit = getattr(args, 'limit', 20)
        output = getattr(args, 'output', 'human')

        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Build query based on status filter
        # Schema: id, session_id, objective, scope, estimated_complexity, created_timestamp,
        #         completed_timestamp, is_completed, goal_data, status, beads_issue_id, project_id
        if status_filter == 'completed':
            # Goals where all subtasks are completed (or no subtasks)
            query = """
                SELECT g.id, g.objective, g.status,
                       g.created_timestamp, g.session_id, s.ai_id,
                       (SELECT COUNT(*) FROM subtasks WHERE goal_id = g.id) as total_subtasks,
                       (SELECT COUNT(*) FROM subtasks WHERE goal_id = g.id AND status = 'completed') as completed_subtasks
                FROM goals g
                LEFT JOIN sessions s ON g.session_id = s.session_id
                WHERE g.status = 'completed'
                   OR (SELECT COUNT(*) FROM subtasks WHERE goal_id = g.id) =
                      (SELECT COUNT(*) FROM subtasks WHERE goal_id = g.id AND status = 'completed')
                   AND (SELECT COUNT(*) FROM subtasks WHERE goal_id = g.id) > 0
                ORDER BY g.created_timestamp DESC
                LIMIT ?
            """
        elif status_filter == 'active':
            # Goals that are not completed
            query = """
                SELECT g.id, g.objective, g.status,
                       g.created_timestamp, g.session_id, s.ai_id,
                       (SELECT COUNT(*) FROM subtasks WHERE goal_id = g.id) as total_subtasks,
                       (SELECT COUNT(*) FROM subtasks WHERE goal_id = g.id AND status = 'completed') as completed_subtasks
                FROM goals g
                LEFT JOIN sessions s ON g.session_id = s.session_id
                WHERE g.status != 'completed'
                   AND NOT (
                       (SELECT COUNT(*) FROM subtasks WHERE goal_id = g.id) =
                       (SELECT COUNT(*) FROM subtasks WHERE goal_id = g.id AND status = 'completed')
                       AND (SELECT COUNT(*) FROM subtasks WHERE goal_id = g.id) > 0
                   )
                ORDER BY g.created_timestamp DESC
                LIMIT ?
            """
        else:  # 'all'
            query = """
                SELECT g.id, g.objective, g.status,
                       g.created_timestamp, g.session_id, s.ai_id,
                       (SELECT COUNT(*) FROM subtasks WHERE goal_id = g.id) as total_subtasks,
                       (SELECT COUNT(*) FROM subtasks WHERE goal_id = g.id AND status = 'completed') as completed_subtasks
                FROM goals g
                LEFT JOIN sessions s ON g.session_id = s.session_id
                ORDER BY g.created_timestamp DESC
                LIMIT ?
            """

        cursor.execute(query, (limit,))
        goals_rows = cursor.fetchall()

        # Build result with inline subtasks
        # Row indices: 0=id, 1=objective, 2=status, 3=created_timestamp, 4=session_id, 5=ai_id, 6=total, 7=completed
        goals = []
        for row in goals_rows:
            goal_id = row[0]
            total = row[6] or 0
            completed = row[7] or 0
            progress_pct = (completed / total * 100) if total > 0 else 0.0

            # Get subtasks for this goal
            cursor.execute("""
                SELECT id, description, status, epistemic_importance, created_timestamp
                FROM subtasks
                WHERE goal_id = ?
                ORDER BY
                    CASE epistemic_importance
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                        ELSE 5
                    END,
                    created_timestamp
            """, (goal_id,))
            subtasks_rows = cursor.fetchall()

            subtasks = []
            for st in subtasks_rows:
                subtasks.append({
                    'id': st[0],
                    'description': st[1],
                    'status': st[2],
                    'importance': st[3]  # Keep output key as 'importance' for simplicity
                })

            goals.append({
                'id': goal_id,
                'objective': row[1],
                'status': row[2],
                'created_at': row[3],
                'session_id': row[4],
                'ai_id': row[5],
                'progress': {
                    'total': total,
                    'completed': completed,
                    'percentage': round(progress_pct, 1)
                },
                'subtasks': subtasks
            })

        db.close()

        result = {
            'ok': True,
            'filter': status_filter,
            'count': len(goals),
            'goals': goals
        }

        if output == 'json':
            print(json.dumps(result, indent=2))
        else:
            # Human-readable format
            status_label = {'active': 'ACTIVE', 'completed': 'COMPLETED', 'all': 'ALL'}
            print(f"\n{'='*70}")
            print(f"🎯 GOALS ({status_label.get(status_filter, status_filter)}) - {len(goals)} found")
            print(f"{'='*70}\n")

            if not goals:
                print("  No goals found.")
                return None

            for i, goal in enumerate(goals, 1):
                progress = goal['progress']
                pct = progress['percentage']

                # Status indicator
                if pct == 100:
                    status_icon = "✅"
                elif pct > 0:
                    status_icon = "🔄"
                else:
                    status_icon = "⏳"

                print(f"{status_icon} {i}. {goal['objective']}")
                print(f"   ID: {goal['id'][:8]}... | Progress: {progress['completed']}/{progress['total']} ({pct}%)")
                if goal['ai_id']:
                    print(f"   AI: {goal['ai_id']} | Session: {goal['session_id'][:8]}...")

                # Inline subtasks
                if goal['subtasks']:
                    for st in goal['subtasks']:
                        st_icon = "✓" if st['status'] == 'completed' else "○"
                        imp_badge = f"[{st['importance'][:3]}]" if st['importance'] else ""
                        print(f"      {st_icon} {imp_badge} {st['description'][:60]}")
                print()

        return None

    except Exception as e:
        result = {'ok': False, 'error': str(e)}
        print(json.dumps(result))
        return 1
