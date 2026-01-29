#!/usr/bin/env python3
"""
SubagentStart Hook: Create linked Empirica session when a sub-agent spawns.

Triggered by Claude Code SubagentStart event. Creates a child session
linked via parent_session_id, enabling epistemic lineage tracking.

Input (stdin JSON from Claude Code):
  - agent_name: str - The agent identifier (e.g., "empirica-integration:security")
  - agent_type: str - The agent type
  - session_id: str - Claude Code's internal session ID (not Empirica's)

Output (stdout JSON):
  - continue: true/false
  - message: str - Status message

Side effects:
  - Creates child Empirica session with parent_session_id
  - Writes child session to .empirica/subagent_sessions/<agent_name>.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def get_parent_session_id():
    """Get current Empirica session ID from active_session file or DB."""
    try:
        from empirica.utils.session_resolver import get_instance_id, get_latest_session_id
        session_id = get_latest_session_id(ai_id='claude-code', active_only=True)
        if session_id:
            return session_id
    except ImportError:
        pass

    # Fallback: read active_session file
    try:
        from empirica.utils.session_resolver import get_instance_id
        instance_id = get_instance_id()
        safe_instance = instance_id.replace(":", "_").replace("%", "") if instance_id else ""
        suffix = f"_{safe_instance}" if safe_instance else ""

        for base in [Path.cwd() / '.empirica', Path.home() / '.empirica']:
            active_file = base / f'active_session{suffix}'
            if active_file.exists():
                sid = active_file.read_text().strip()
                if sid:
                    return sid
    except Exception:
        pass

    return None


def create_child_session(parent_session_id: str, agent_name: str) -> dict:
    """Create a linked child session in Empirica."""
    try:
        from empirica.data.session_database import SessionDatabase

        db = SessionDatabase()
        child_session_id = db.create_session(
            ai_id=agent_name,
            components_loaded=0,
            parent_session_id=parent_session_id
        )
        db.close()

        return {
            "ok": True,
            "child_session_id": child_session_id,
            "parent_session_id": parent_session_id,
            "agent_name": agent_name
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


def get_budget_allocation(parent_session_id: str, agent_name: str) -> dict:
    """Get attention budget allocation for this agent, if one exists."""
    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Find active budget for parent session
        cursor.execute("""
            SELECT id, remaining, domain_allocations, strategy
            FROM attention_budgets
            WHERE session_id = ? ORDER BY created_at DESC LIMIT 1
        """, (parent_session_id,))
        row = cursor.fetchone()
        db.close()

        if not row:
            return {}

        budget_id, remaining, alloc_json, strategy = row
        allocations = json.loads(alloc_json) if alloc_json else []

        # Find domain allocation for this agent
        # Agent name format: "empirica-integration:security" -> domain "security"
        agent_domain = agent_name.split(":")[-1] if ":" in agent_name else "general"

        domain_alloc = None
        for alloc in allocations:
            if alloc.get("domain") == agent_domain:
                domain_alloc = alloc
                break

        return {
            "budget_id": budget_id,
            "budget_remaining": remaining,
            "strategy": strategy,
            "domain": agent_domain,
            "domain_budget": domain_alloc.get("budget", 5) if domain_alloc else 5,
            "expected_gain": domain_alloc.get("expected_gain", 0.5) if domain_alloc else 0.5,
            "priority": domain_alloc.get("priority", 0.5) if domain_alloc else 0.5,
        }
    except Exception:
        return {}


def store_subagent_session(agent_name: str, child_session_id: str, parent_session_id: str):
    """Store subagent session mapping for later rollup by SubagentStop."""
    subagent_dir = Path.cwd() / '.empirica' / 'subagent_sessions'
    subagent_dir.mkdir(parents=True, exist_ok=True)

    # Use timestamp to allow multiple invocations of same agent
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = agent_name.replace(":", "_").replace("/", "_")
    session_file = subagent_dir / f"{safe_name}_{timestamp}.json"

    # Get budget allocation for this agent
    budget_info = get_budget_allocation(parent_session_id, agent_name)

    session_data = {
        "agent_name": agent_name,
        "child_session_id": child_session_id,
        "parent_session_id": parent_session_id,
        "started_at": datetime.now().isoformat(),
        "status": "active",
        "budget": budget_info,
    }

    session_file.write_text(json.dumps(session_data, indent=2))
    return str(session_file)


def main():
    try:
        # Read hook input from stdin
        input_data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}
    except (json.JSONDecodeError, EOFError):
        input_data = {}

    agent_name = input_data.get("agent_name", input_data.get("agent_type", "unknown-agent"))

    # Get parent session
    parent_session_id = get_parent_session_id()

    if not parent_session_id:
        # No active session — allow agent to proceed without tracking
        result = {
            "continue": True,
            "message": f"SubagentStart: No active Empirica session. Agent '{agent_name}' proceeding without lineage tracking."
        }
        print(json.dumps(result))
        return

    # Create linked child session
    child_result = create_child_session(parent_session_id, agent_name)

    if child_result.get("ok"):
        child_session_id = child_result["child_session_id"]

        # Store mapping for SubagentStop rollup
        session_file = store_subagent_session(agent_name, child_session_id, parent_session_id)

        result = {
            "continue": True,
            "message": f"SubagentStart: Created child session {child_session_id[:8]} for '{agent_name}' (parent: {parent_session_id[:8]})"
        }
    else:
        # Creation failed — allow agent to proceed anyway (fail-open)
        result = {
            "continue": True,
            "message": f"SubagentStart: Failed to create child session for '{agent_name}': {child_result.get('error', 'unknown')}. Proceeding without tracking."
        }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
