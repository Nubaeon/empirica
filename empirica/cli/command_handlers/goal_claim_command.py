"""
Goals Claim Command - Start work on a goal by claiming it and creating a git branch

Handles:
- goals-claim: Claim goal, create git branch, optionally run PREFLIGHT
"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from ..cli_utils import handle_cli_error, parse_json_safely

logger = logging.getLogger(__name__)


def handle_goals_claim_command(args):
    """Handle goals-claim command - Claim goal and create git branch"""
    try:
        from empirica.core.goals.repository import GoalRepository
        from empirica.integrations.branch_mapping import get_branch_mapping
        from empirica.data.session_database import SessionDatabase
        
        goal_id = args.goal_id
        create_branch = getattr(args, 'create_branch', True)
        run_preflight = getattr(args, 'run_preflight', False)
        output_format = getattr(args, 'output', 'json')
        
        # Validate goal exists
        goal_repo = GoalRepository()
        goal = goal_repo.get_goal(goal_id)

        if not goal:
            result = {
                "ok": False,
                "error": f"Goal not found: {goal_id}"
            }
            print(json.dumps(result) if output_format == 'json' else f"❌ {result['error']}")
            sys.exit(1)

        # Get session_id from the database (not stored in the Goal object itself)
        db = SessionDatabase()
        cursor = db.conn.execute(
            "SELECT session_id FROM goals WHERE id = ?",
            (goal_id,)
        )
        row = cursor.fetchone()
        if not row:
            result = {
                "ok": False,
                "error": f"Goal session not found in database: {goal_id}"
            }
            print(json.dumps(result) if output_format == 'json' else f"❌ {result['error']}")
            db.close()
            sys.exit(1)
        session_id = row[0]

        # Get AI ID from session
        cursor = db.conn.execute(
            "SELECT ai_id FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        ai_id = row[0] if row else "unknown"
        
        # Get BEADS issue ID
        cursor = db.conn.execute(
            "SELECT beads_issue_id FROM goals WHERE id = ?",
            (goal_id,)
        )
        row = cursor.fetchone()
        beads_issue_id = row[0] if row and row[0] else None
        db.close()
        
        result = {
            "ok": True,
            "goal_id": goal_id,
            "session_id": session_id,
            "beads_issue_id": beads_issue_id
        }
        
        # Update BEADS status to in_progress
        if beads_issue_id:
            try:
                from empirica.integrations.beads import BeadsAdapter
                beads = BeadsAdapter()
                if beads.is_available():
                    beads.update_status(beads_issue_id, "in_progress")
                    result["beads_status_updated"] = True
            except Exception as e:
                logger.warning(f"Failed to update BEADS status: {e}")
                result["beads_status_updated"] = False
        
        # Create git branch
        if create_branch:
            try:
                # Generate branch name
                if beads_issue_id:
                    branch_name = f"epistemic/reasoning/issue-{beads_issue_id}"
                else:
                    branch_name = f"epistemic/reasoning/goal-{goal_id[:8]}"
                
                # Check if branch already exists
                check_result = subprocess.run(
                    ["git", "rev-parse", "--verify", branch_name],
                    capture_output=True,
                    text=True
                )
                
                if check_result.returncode == 0:
                    # Branch exists, just checkout
                    subprocess.run(
                        ["git", "checkout", branch_name],
                        check=True,
                        capture_output=True
                    )
                    result["branch_action"] = "checked_out_existing"
                else:
                    # Create new branch
                    subprocess.run(
                        ["git", "checkout", "-b", branch_name],
                        check=True,
                        capture_output=True
                    )
                    result["branch_action"] = "created_new"
                
                result["branch_name"] = branch_name
                result["branch_created"] = True
                
                # Add branch mapping
                try:
                    branch_mapping = get_branch_mapping()
                    branch_mapping.add_mapping(
                        branch_name=branch_name,
                        goal_id=goal_id,
                        beads_issue_id=beads_issue_id,
                        ai_id=ai_id,
                        session_id=session_id
                    )
                    result["branch_mapping_saved"] = True
                except Exception as e:
                    logger.warning(f"Failed to save branch mapping: {e}")
                    result["branch_mapping_saved"] = False
                
            except subprocess.CalledProcessError as e:
                result["branch_created"] = False
                result["branch_error"] = str(e)
        else:
            result["branch_created"] = False
            result["branch_skipped"] = True
        
        # Run PREFLIGHT if requested
        if run_preflight:
            try:
                # Import preflight command
                from .cascade_commands import handle_preflight_command
                
                # Create mock args for preflight
                class MockArgs:
                    def __init__(self, session_id, prompt):
                        self.session_id = session_id
                        self.prompt = prompt
                        self.prompt_only = False
                        self.output = 'json'
                
                preflight_args = MockArgs(
                    session_id=goal.session_id,
                    prompt=f"Starting work on goal: {goal.objective}"
                )
                
                # Run preflight (this will print its own output)
                handle_preflight_command(preflight_args)
                result["preflight_started"] = True
                
            except Exception as e:
                logger.warning(f"Failed to run PREFLIGHT: {e}")
                result["preflight_started"] = False
                result["preflight_error"] = str(e)
        else:
            result["preflight_started"] = False
        
        # Output result
        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Claimed goal: {goal_id[:8]}")
            if beads_issue_id and result.get("beads_status_updated"):
                print(f"✅ Updated BEADS status: in_progress")
            if result.get("branch_created"):
                print(f"✅ {'Created' if result['branch_action'] == 'created_new' else 'Checked out'} branch: {result['branch_name']}")
            if result.get("branch_mapping_saved"):
                print(f"✅ Branch mapping saved")
            if result.get("preflight_started"):
                print(f"🧠 Running PREFLIGHT...")
            print(f"✅ Ready to start work!")
        
    except Exception as e:
        handle_cli_error(e, "goals-claim", getattr(args, 'output', 'json'))
