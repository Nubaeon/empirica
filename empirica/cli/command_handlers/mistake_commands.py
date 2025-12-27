"""
Mistake Commands - Log and query mistakes for learning from failures
"""

import json
import logging
from typing import Optional
from ..cli_utils import handle_cli_error

logger = logging.getLogger(__name__)


def handle_mistake_log_command(args):
    """Handle mistake-log command"""
    try:
        from empirica.data.session_database import SessionDatabase

        # Parse arguments
        project_id = getattr(args, 'project_id', None)
        session_id = args.session_id
        mistake = args.mistake
        why_wrong = args.why_wrong
        cost_estimate = getattr(args, 'cost_estimate', None)
        root_cause_vector = getattr(args, 'root_cause_vector', None)
        prevention = getattr(args, 'prevention', None)
        goal_id = getattr(args, 'goal_id', None)

        # Log the mistake
        db = SessionDatabase()
        mistake_id = db.log_mistake(
            session_id=session_id,
            mistake=mistake,
            why_wrong=why_wrong,
            cost_estimate=cost_estimate,
            root_cause_vector=root_cause_vector,
            prevention=prevention,
            goal_id=goal_id,
            project_id=project_id  # Add project_id parameter
        )
        db.close()

        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            result = {
                "ok": True,
                "mistake_id": mistake_id,
                "session_id": session_id,
                "message": "Mistake logged successfully"
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Mistake logged successfully")
            print(f"   Mistake ID: {mistake_id}")
            print(f"   Session: {session_id[:8]}...")
            if root_cause_vector:
                print(f"   Root cause: {root_cause_vector} vector")
            if cost_estimate:
                print(f"   Cost: {cost_estimate}")

        # Return None to avoid exit code issues and duplicate output
        return None

    except Exception as e:
        handle_cli_error(e, "Mistake log", getattr(args, 'verbose', False))
        return None


def handle_mistake_query_command(args):
    """Handle mistake-query command"""
    try:
        from empirica.data.session_database import SessionDatabase

        # Parse arguments
        session_id = getattr(args, 'session_id', None)
        goal_id = getattr(args, 'goal_id', None)
        limit = getattr(args, 'limit', 10)

        # Query mistakes
        db = SessionDatabase()
        mistakes = db.get_mistakes(
            session_id=session_id,
            goal_id=goal_id,
            limit=limit
        )
        db.close()

        # Format output
        if hasattr(args, 'output') and args.output == 'json':
            result = {
                "ok": True,
                "mistakes_count": len(mistakes),
                "mistakes": [
                    {
                        "mistake_id": m['id'],
                        "session_id": m['session_id'],
                        "goal_id": m['goal_id'],
                        "mistake": m['mistake'],
                        "why_wrong": m['why_wrong'],
                        "cost_estimate": m['cost_estimate'],
                        "root_cause_vector": m['root_cause_vector'],
                        "prevention": m['prevention'],
                        "timestamp": m['created_timestamp']
                    }
                    for m in mistakes
                ]
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"📋 Found {len(mistakes)} mistake(s):")
            for i, m in enumerate(mistakes, 1):
                print(f"\n{i}. {m['mistake'][:60]}...")
                print(f"   Why wrong: {m['why_wrong'][:60]}...")
                if m['cost_estimate']:
                    print(f"   Cost: {m['cost_estimate']}")
                if m['root_cause_vector']:
                    print(f"   Root cause: {m['root_cause_vector']}")
                if m['prevention']:
                    print(f"   Prevention: {m['prevention'][:60]}...")
                print(f"   Session: {m['session_id'][:8]}...")

        # Return None to avoid exit code issues and duplicate output
        return None

    except Exception as e:
        handle_cli_error(e, "Mistake query", getattr(args, 'verbose', False))
        return None
