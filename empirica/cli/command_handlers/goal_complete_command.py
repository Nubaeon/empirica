"""
Goals Complete Command - Complete a goal by merging branch and closing BEADS issue

Handles:
- goals-complete: Run POSTFLIGHT, close BEADS issue, merge git branch, create handoff
"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from ..cli_utils import handle_cli_error, parse_json_safely

logger = logging.getLogger(__name__)


def handle_goals_complete_command(args):
    """Handle goals-complete command - Complete goal, merge branch, close BEADS"""
    try:
        from empirica.core.goals.repository import GoalRepository
        from empirica.integrations.branch_mapping import get_branch_mapping
        from empirica.data.session_database import SessionDatabase
        
        goal_id = args.goal_id
        run_postflight = getattr(args, 'run_postflight', False)
        merge_branch = getattr(args, 'merge_branch', False)
        close_reason = getattr(args, 'reason', 'completed')
        output_format = getattr(args, 'output', 'json')
        
        # Validate goal exists
        db = SessionDatabase()
        cursor = db.conn.cursor()
        cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
        goal = cursor.fetchone()
        
        if not goal:
            result = {
                "ok": False,
                "error": f"Goal not found: {goal_id}"
            }
            print(json.dumps(result) if output_format == 'json' else f"❌ {result['error']}")
            sys.exit(1)
        
        # Get BEADS issue ID and session info  
        cursor = db.conn.execute(
            "SELECT beads_issue_id FROM goals WHERE id = ?",
            (goal_id,)
        )
        row = cursor.fetchone()
        beads_issue_id = row[0] if row and row[0] else None
        db.close()
        
        # Update goal status to completed
        import time
        db2 = SessionDatabase()
        db2.conn.execute(
            "UPDATE goals SET status = 'completed', is_completed = 1, completed_timestamp = ? WHERE id = ?",
            (time.time(), goal_id)
        )
        db2.conn.commit()
        db2.close()

        result = {
            "ok": True,
            "goal_id": goal_id,
            "objective": goal['objective'],
            "session_id": goal['session_id'],
            "beads_issue_id": beads_issue_id,
            "status_updated": True
        }
        
        # Run POSTFLIGHT if requested
        if run_postflight:
            try:
                from .cascade_commands import handle_postflight_command
                
                # Create mock args for postflight
                class MockArgs:
                    def __init__(self, session_id, task_summary):
                        self.session_id = session_id
                        self.task_summary = task_summary
                        self.output = 'json'
                
                postflight_args = MockArgs(
                    session_id=goal['session_id'],
                    task_summary=f"Completed goal: {goal['objective']}"
                )
                
                # Run postflight (this will print its own output)
                handle_postflight_command(postflight_args)
                result["postflight_started"] = True
                
            except Exception as e:
                logger.warning(f"Failed to run POSTFLIGHT: {e}")
                result["postflight_started"] = False
                result["postflight_error"] = str(e)
        else:
            result["postflight_started"] = False
        
        # Close BEADS issue
        if beads_issue_id:
            try:
                from empirica.integrations.beads import BeadsAdapter
                beads = BeadsAdapter()
                if beads.is_available():
                    beads.close_issue(beads_issue_id, reason=close_reason)
                    result["beads_issue_closed"] = True
            except Exception as e:
                logger.warning(f"Failed to close BEADS issue: {e}")
                result["beads_issue_closed"] = False
                result["beads_error"] = str(e)
        else:
            result["beads_issue_closed"] = False
            result["beads_not_linked"] = True
        
        # Get branch mapping
        branch_mapping = get_branch_mapping()
        branch_name = branch_mapping.get_branch_for_goal(goal_id)
        
        if branch_name:
            result["branch_name"] = branch_name
            
            # Merge branch if requested
            if merge_branch:
                try:
                    # Get current branch
                    current_branch_result = subprocess.run(
                        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    current_branch = current_branch_result.stdout.strip()
                    
                    # If we're on the goal branch, switch to main first
                    if current_branch == branch_name:
                        subprocess.run(
                            ["git", "checkout", "main"],
                            check=True,
                            capture_output=True
                        )
                    
                    # Merge the branch
                    merge_result = subprocess.run(
                        ["git", "merge", "--no-ff", branch_name, "-m", f"Merge goal: {goal.objective}"],
                        capture_output=True,
                        text=True
                    )
                    
                    if merge_result.returncode == 0:
                        result["branch_merged"] = True
                        result["merge_commit"] = subprocess.run(
                            ["git", "rev-parse", "HEAD"],
                            capture_output=True,
                            text=True,
                            check=True
                        ).stdout.strip()
                        
                        # Optionally delete the branch
                        if getattr(args, 'delete_branch', False):
                            subprocess.run(
                                ["git", "branch", "-d", branch_name],
                                check=True,
                                capture_output=True
                            )
                            result["branch_deleted"] = True
                    else:
                        result["branch_merged"] = False
                        result["merge_error"] = merge_result.stderr
                        
                except subprocess.CalledProcessError as e:
                    result["branch_merged"] = False
                    result["merge_error"] = str(e)
            else:
                result["branch_merged"] = False
                result["merge_skipped"] = True
            
            # Remove branch mapping
            try:
                branch_mapping.remove_mapping(branch_name, archive=True)
                result["branch_mapping_removed"] = True
            except Exception as e:
                logger.warning(f"Failed to remove branch mapping: {e}")
                result["branch_mapping_removed"] = False
        else:
            result["branch_found"] = False
            result["branch_merged"] = False
        
        # Create handoff report if requested
        if getattr(args, 'create_handoff', False):
            try:
                from .handoff_commands import handle_handoff_create_command
                
                # Create mock args for handoff
                class MockArgs:
                    def __init__(self, session_id, task_summary):
                        self.session_id = session_id
                        self.task_summary = task_summary
                        self.key_findings = None
                        self.remaining_unknowns = None
                        self.next_session_context = None
                        self.artifacts_created = None
                        self.output = 'json'
                
                handoff_args = MockArgs(
                    session_id=goal.session_id,
                    task_summary=f"Completed goal: {goal.objective}"
                )
                
                # Run handoff creation (this will print its own output)
                handle_handoff_create_command(handoff_args)
                result["handoff_created"] = True
                
            except Exception as e:
                logger.warning(f"Failed to create handoff: {e}")
                result["handoff_created"] = False
                result["handoff_error"] = str(e)
        else:
            result["handoff_created"] = False
        
        # Output result
        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Completed goal: {goal_id[:8]}")
            if result.get("postflight_started"):
                print(f"🧠 POSTFLIGHT completed")
            if result.get("beads_issue_closed"):
                print(f"✅ Closed BEADS issue: {beads_issue_id}")
            if result.get("branch_merged"):
                print(f"✅ Merged branch: {branch_name}")
                if result.get("branch_deleted"):
                    print(f"✅ Deleted branch: {branch_name}")
            if result.get("branch_mapping_removed"):
                print(f"✅ Branch mapping archived")
            if result.get("handoff_created"):
                print(f"✅ Handoff report created")
            print(f"✅ Goal complete!")
        
    except Exception as e:
        handle_cli_error(e, "goals-complete", getattr(args, 'output', 'json'))
