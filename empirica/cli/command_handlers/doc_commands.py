"""
Doc Commands - compute documentation completeness and suggest update plan
"""
from __future__ import annotations
import json
from ..cli_utils import handle_cli_error


def handle_doc_check_command(args):
    """Handle doc-check command to compute documentation completeness."""
    try:
        from empirica.core.docs.doc_planner import compute_doc_plan
        project_id = args.project_id
        session_id = getattr(args, 'session_id', None)
        goal_id = getattr(args, 'goal_id', None)
        plan = compute_doc_plan(project_id, session_id=session_id, goal_id=goal_id)
        if getattr(args, 'output', 'default') == 'json':
            print(json.dumps({'ok': True, 'plan': plan}, indent=2))
        else:
            print(f"📄 Documentation completeness: {plan['doc_completeness_score']}")
            if plan['suggested_updates']:
                print("\n🛠️  Suggested updates:")
                for i, s in enumerate(plan['suggested_updates'], 1):
                    print(f"  {i}. {s['doc_path']} → {s['reason']}")
        return plan
    except Exception as e:
        handle_cli_error(e, "Doc check", getattr(args, 'verbose', False))
        return None


def handle_doc_plan_suggest_command(args):
    """Handle doc-plan-suggest command, alias to doc-check with JSON output."""
    try:
        from empirica.core.docs.doc_planner import compute_doc_plan
        plan = compute_doc_plan(args.project_id, session_id=getattr(args, 'session_id', None), goal_id=getattr(args, 'goal_id', None))
        print(json.dumps({'ok': True, 'plan': plan}, indent=2))
        return plan
    except Exception as e:
        handle_cli_error(e, "Doc plan suggest", getattr(args, 'verbose', False))
        return None
