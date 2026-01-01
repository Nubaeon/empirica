"""
Agent Commands - CLI handlers for epistemic sub-agents

Commands:
- agent-spawn: Create epistemic agent prompt with branch tracking
- agent-report: Report agent postflight results
- agent-aggregate: Aggregate multiple agent results
"""

import json
import sys
from typing import Optional

from empirica.core.agents import (
    EpistemicAgentConfig,
    spawn_epistemic_agent,
    aggregate_agent_results,
    parse_postflight,
)
from empirica.data.session_database import SessionDatabase


def handle_agent_spawn_command(args) -> dict:
    """
    Spawn an epistemic agent (returns prompt for external execution).

    Usage:
        empirica agent-spawn --session-id <ID> --task "Review code" --persona security_expert

    Returns prompt with branch_id for tracking.
    """

    session_id = getattr(args, 'session_id', None)
    task = getattr(args, 'task', None)
    persona_id = getattr(args, 'persona', 'general')
    parent_context = getattr(args, 'context', None)
    output_format = getattr(args, 'output', 'text')

    if not session_id:
        return {"ok": False, "error": "session_id required"}

    if not task:
        return {"ok": False, "error": "task required"}

    config = EpistemicAgentConfig(
        session_id=session_id,
        task=task,
        persona_id=persona_id,
        parent_context=parent_context
    )

    result = spawn_epistemic_agent(config, execute_fn=None)

    response = {
        "ok": True,
        "branch_id": result.branch_id,
        "persona_id": result.persona_id,
        "preflight_vectors": result.preflight_vectors,
        "prompt": result.output,
        "usage": f"Execute prompt with your agent, then: empirica agent-report --branch-id {result.branch_id} -"
    }

    if output_format == 'json':
        print(json.dumps(response, indent=2))
    else:
        print(f"Branch ID: {result.branch_id}")
        print(f"Persona: {result.persona_id}")
        print(f"\n--- AGENT PROMPT ---\n")
        print(result.output)
        print(f"\n--- END PROMPT ---\n")
        print(f"After agent completes, report with:")
        print(f"  empirica agent-report --branch-id {result.branch_id} --postflight '<json>'")


def handle_agent_report_command(args) -> dict:
    """
    Report agent postflight results.

    Usage:
        empirica agent-report --branch-id <ID> --postflight '{"vectors": {...}, "findings": [...]}'

    Or pipe agent output:
        echo "<agent output>" | empirica agent-report --branch-id <ID> -
    """

    branch_id = getattr(args, 'branch_id', None)
    postflight_json = getattr(args, 'postflight', None)
    output_format = getattr(args, 'output', 'text')

    if not branch_id:
        return {"ok": False, "error": "branch_id required"}

    # Read from stdin if '-' provided
    if postflight_json == '-':
        postflight_json = sys.stdin.read()

    if not postflight_json:
        return {"ok": False, "error": "postflight data required (JSON or agent output with postflight block)"}

    # Try to parse as JSON directly
    try:
        data = json.loads(postflight_json)
        if 'vectors' in data:
            postflight_data = data
        else:
            postflight_data = None
    except json.JSONDecodeError:
        # Try to extract postflight block from agent output
        from empirica.core.agents.epistemic_agent import parse_postflight
        postflight_data = parse_postflight(postflight_json, branch_id)

    if not postflight_data:
        return {"ok": False, "error": "Could not parse postflight data. Expected JSON with 'vectors' key or agent output with ```postflight block."}

    # Update branch
    db = SessionDatabase()
    try:
        merge_score = db.branches.checkpoint_branch(
            branch_id=branch_id,
            postflight_vectors=postflight_data['vectors'],
            tokens_spent=postflight_data.get('tokens_spent', 0),
            time_spent_minutes=postflight_data.get('time_spent_minutes', 0)
        )

        # Log findings if any
        findings = postflight_data.get('findings', [])
        unknowns = postflight_data.get('unknowns', [])

        response = {
            "ok": True,
            "branch_id": branch_id,
            "postflight_vectors": postflight_data['vectors'],
            "merge_score": merge_score,
            "findings_count": len(findings),
            "unknowns_count": len(unknowns),
            "findings": findings,
            "unknowns": unknowns
        }

        if output_format == 'json':
            print(json.dumps(response, indent=2))
        else:
            print(f"Branch {branch_id[:8]}... updated")
            print(f"Merge Score: {merge_score:.4f}" if merge_score else "Merge Score: pending")
            print(f"Findings: {len(findings)}, Unknowns: {len(unknowns)}")
            if findings:
                print("\nFindings:")
                for f in findings[:5]:
                    print(f"  - {f}")

        return response

    finally:
        db.close()


def handle_agent_aggregate_command(args) -> dict:
    """
    Aggregate results from multiple epistemic agents.

    Usage:
        empirica agent-aggregate --session-id <ID> --round 1

    Runs auto-merge scoring on all active branches in session.
    """

    session_id = getattr(args, 'session_id', None)
    investigation_round = getattr(args, 'round', 1)
    output_format = getattr(args, 'output', 'text')

    if not session_id:
        return {"ok": False, "error": "session_id required"}

    db = SessionDatabase()
    try:
        # Get all active branches for session
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT id, branch_name, investigation_path,
                   preflight_vectors, postflight_vectors,
                   merge_score, status
            FROM investigation_branches
            WHERE session_id = ? AND status = 'active'
            ORDER BY created_timestamp DESC
        """, (session_id,))

        branches = cursor.fetchall()

        if not branches:
            return {"ok": False, "error": "No active branches found for session"}

        # Run merge
        merge_result = db.branches.merge_branches(
            session_id=session_id,
            round_number=investigation_round
        )

        response = {
            "ok": True,
            "session_id": session_id,
            "investigation_round": investigation_round,
            "branches_evaluated": len(branches),
            "winner": merge_result.get('winning_branch_name'),
            "winning_score": merge_result.get('winning_score'),
            "decision_rationale": merge_result.get('decision_rationale'),
            "merge_decision_id": merge_result.get('decision_id')
        }

        if output_format == 'json':
            print(json.dumps(response, indent=2))
        else:
            print(f"Session: {session_id[:8]}...")
            print(f"Round: {investigation_round}")
            print(f"Branches Evaluated: {len(branches)}")
            print(f"\nWinner: {merge_result.get('winning_branch_name')}")
            print(f"Score: {merge_result.get('winning_score', 0):.4f}")
            print(f"\nRationale: {merge_result.get('decision_rationale')}")

        return response

    finally:
        db.close()


def register_agent_parsers(subparsers):
    """Register agent command parsers."""

    # agent-spawn
    spawn_parser = subparsers.add_parser(
        'agent-spawn',
        help='Spawn epistemic agent (returns prompt with branch tracking)'
    )
    spawn_parser.add_argument('--session-id', required=True, help='Parent session ID')
    spawn_parser.add_argument('--task', required=True, help='Task for the agent')
    spawn_parser.add_argument('--persona', default='general', help='Persona ID to use')
    spawn_parser.add_argument('--context', help='Additional context from parent')
    spawn_parser.add_argument('--output', choices=['text', 'json'], default='text')
    spawn_parser.set_defaults(func=handle_agent_spawn_command)

    # agent-report
    report_parser = subparsers.add_parser(
        'agent-report',
        help='Report agent postflight results'
    )
    report_parser.add_argument('--branch-id', required=True, help='Branch ID from agent-spawn')
    report_parser.add_argument('--postflight', help='Postflight JSON or "-" for stdin')
    report_parser.add_argument('--output', choices=['text', 'json'], default='text')
    report_parser.set_defaults(func=handle_agent_report_command)

    # agent-aggregate
    aggregate_parser = subparsers.add_parser(
        'agent-aggregate',
        help='Aggregate results from multiple agents'
    )
    aggregate_parser.add_argument('--session-id', required=True, help='Session ID')
    aggregate_parser.add_argument('--round', type=int, default=1, help='Investigation round')
    aggregate_parser.add_argument('--output', choices=['text', 'json'], default='text')
    aggregate_parser.set_defaults(func=handle_agent_aggregate_command)
