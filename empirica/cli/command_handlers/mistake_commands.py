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
        from empirica.cli.command_handlers.project_commands import infer_scope

        # Parse arguments
        project_id = getattr(args, 'project_id', None)
        session_id = args.session_id
        mistake = args.mistake
        why_wrong = args.why_wrong
        cost_estimate = getattr(args, 'cost_estimate', None)
        root_cause_vector = getattr(args, 'root_cause_vector', None)
        prevention = getattr(args, 'prevention', None)
        goal_id = getattr(args, 'goal_id', None)
        output_format = getattr(args, 'output', 'json')

        # Auto-resolve project_id if not provided
        db = SessionDatabase()
        if not project_id and session_id:
            cursor = db.conn.cursor()
            cursor.execute("SELECT project_id FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if row and row['project_id']:
                project_id = row['project_id']

        # DUAL-SCOPE LOGIC: Infer scope and log to appropriate table(s)
        explicit_scope = getattr(args, 'scope', None)
        scope = infer_scope(session_id, project_id, explicit_scope)
        
        mistake_ids = []
        
        if scope in ['session', 'both']:
            # Log to session_mistakes
            mistake_id_session = db.log_session_mistake(
                session_id=session_id,
                mistake=mistake,
                why_wrong=why_wrong,
                cost_estimate=cost_estimate,
                root_cause_vector=root_cause_vector,
                prevention=prevention,
                goal_id=goal_id
            )
            mistake_ids.append(('session', mistake_id_session))
        
        if scope in ['project', 'both']:
            # Log to mistakes_made (legacy table)
            mistake_id_project = db.log_mistake(
                session_id=session_id,
                mistake=mistake,
                why_wrong=why_wrong,
                cost_estimate=cost_estimate,
                root_cause_vector=root_cause_vector,
                prevention=prevention,
                goal_id=goal_id,
                project_id=project_id
            )
            mistake_ids.append(('project', mistake_id_project))
        
        db.close()

        # Format output
        result = {
            "ok": True,
            "scope": scope,
            "mistakes": [{"scope": s, "mistake_id": mid} for s, mid in mistake_ids],
            "session_id": session_id,
            "message": f"Mistake logged to {scope} scope{'s' if scope == 'both' else ''}"
        }
        
        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Mistake logged to {scope} scope{'s' if scope == 'both' else ''}")
            for s, mid in mistake_ids:
                print(f"   {s.capitalize()} mistake ID: {mid[:8]}...")
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
