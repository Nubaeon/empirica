"""
Goal Discovery Commands - Cross-AI Coordination

Handles CLI commands for discovering and resuming goals from other AIs via git notes.

Commands:
- goals-discover: Find goals created by other AIs
- goals-resume: Resume another AI's goal with epistemic handoff
"""

import json
import logging
from ..cli_utils import handle_cli_error

logger = logging.getLogger(__name__)


def handle_goals_discover_command(args):
    """Discover goals from other AIs via git notes"""
    try:
        from empirica.core.canonical.empirica_git import GitGoalStore
        
        goal_store = GitGoalStore()
        
        from_ai_id = getattr(args, 'from_ai_id', None)
        session_id = getattr(args, 'session_id', None)
        
        # Discover goals
        goals = goal_store.discover_goals(
            from_ai_id=from_ai_id,
            session_id=session_id
        )
        
        result = {
            "ok": True,
            "count": len(goals),
            "goals": goals,
            "filter": {
                "from_ai_id": from_ai_id,
                "session_id": session_id
            }
        }
        
        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            if not goals:
                print("🔍 No goals found")
                if from_ai_id:
                    print(f"   Searched for goals from: {from_ai_id}")
                if session_id:
                    print(f"   Searched in session: {session_id}")
                print("\n💡 Tip: Goals are stored in git notes when created")
                print("   Make sure you've run 'git fetch' to get latest goals")
            else:
                print(f"🔍 Discovered {len(goals)} goal(s):\n")
                for i, goal_data in enumerate(goals, 1):
                    print(f"{i}. Goal ID: {goal_data['goal_id'][:8]}...")
                    print(f"   Created by: {goal_data['ai_id']}")
                    print(f"   Session: {goal_data['session_id'][:8]}...")
                    print(f"   Objective: {goal_data['goal_data']['objective'][:80]}")
                    print(f"   Scope: {goal_data['goal_data']['scope']}")
                    
                    # Show lineage
                    if 'lineage' in goal_data and len(goal_data['lineage']) > 1:
                        print(f"   Lineage: {len(goal_data['lineage'])} action(s)")
                        for entry in goal_data['lineage']:
                            print(f"     • {entry['ai_id']} - {entry['action']} at {entry['timestamp'][:10]}")
                    
                    print()
                
                print("💡 To resume a goal, use:")
                print("   empirica goals-resume <goal-id> --ai-id <your-ai-id>")
        
        return result
        
    except Exception as e:
        handle_cli_error(e, "Goal discovery", getattr(args, 'verbose', False))
        # Error handler already manages output, return None to avoid duplicate output
        return None


def handle_goals_resume_command(args):
    """Resume another AI's goal with epistemic handoff"""
    try:
        from empirica.core.canonical.empirica_git import GitGoalStore
        from empirica.core.goals.repository import GoalRepository
        
        goal_id = args.goal_id
        ai_id = getattr(args, 'ai_id', 'empirica_cli')
        
        goal_store = GitGoalStore()
        
        # Load goal from git
        goal_data = goal_store.load_goal(goal_id)
        
        if not goal_data:
            result = {
                "ok": False,
                "error": f"Goal {goal_id} not found in git notes"
            }
            
            if hasattr(args, 'output') and args.output == 'json':
                print(json.dumps(result, indent=2))
            else:
                print(f"❌ Goal {goal_id[:8]}... not found")
                print("\n💡 Try:")
                print("   1. empirica goals-discover --from-ai-id <other-ai>")
                print("   2. git fetch  # Pull latest goals from remote")
            
            return result
        
        # Add lineage entry
        goal_store.add_lineage(goal_id, ai_id, "resumed")
        
        # Load into local database
        goal_repo = GoalRepository()
        # TODO: Import goal into local database
        
        result = {
            "ok": True,
            "goal_id": goal_id,
            "ai_id": ai_id,
            "original_ai": goal_data['ai_id'],
            "message": "Goal resumed successfully",
            "objective": goal_data['goal_data']['objective'],
            "epistemic_state": goal_data.get('epistemic_state', {})
        }
        
        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Goal resumed successfully")
            print(f"   Goal ID: {goal_id[:8]}...")
            print(f"   Original AI: {goal_data['ai_id']}")
            print(f"   Resuming as: {ai_id}")
            print(f"   Objective: {goal_data['goal_data']['objective'][:80]}")
            
            # Show epistemic handoff
            epistemic_state = goal_data.get('epistemic_state', {})
            if epistemic_state:
                print(f"\n📊 Epistemic State from {goal_data['ai_id']}:")
                for key, value in epistemic_state.items():
                    if isinstance(value, (int, float)):
                        print(f"   • {key.upper()}: {value:.2f}")
            
            print(f"\n💡 Next steps:")
            print(f"   1. Review original AI's epistemic state")
            print(f"   2. Run your own preflight: empirica preflight \"<task>\" --ai-id {ai_id}")
            print(f"   3. Compare your vectors with original AI's")
        
        goal_repo.close()
        return result
        
    except Exception as e:
        handle_cli_error(e, "Goal resume", getattr(args, 'verbose', False))
        # Error handler already manages output, return None to avoid duplicate output
        return None
