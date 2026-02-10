#!/usr/bin/env python3
"""
Empirica Transaction Enforcer - Stop Hook for POSTFLIGHT Enforcement

Fires on every Claude Stop event. Checks if there's an open transaction
that has been running for enough turns without a POSTFLIGHT, and blocks
Claude from stopping until POSTFLIGHT is submitted.

Design principles:
- Claude decides WHAT to work on and HOW to split it
- The system enforces THAT work gets measured (POSTFLIGHT)
- Turn-based threshold: fuzzy but better than nothing
- Prevents infinite loops via stop_hook_active check

Turn counting:
- Increments a counter in the transaction state file on each Stop
- After SOFT_THRESHOLD turns: injects a reminder (additionalContext)
- After HARD_THRESHOLD turns: blocks stop with reason (forces POSTFLIGHT)
- Resets when POSTFLIGHT is submitted (transaction closes)

Author: Claude Code (Empirica co-pilot)
Date: 2026-02-10
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional


# Thresholds (can be tuned via env vars)
SOFT_THRESHOLD = int(os.environ.get('EMPIRICA_TX_SOFT_TURNS', '12'))
HARD_THRESHOLD = int(os.environ.get('EMPIRICA_TX_HARD_TURNS', '20'))


def _get_instance_id() -> Optional[str]:
    """Derive instance ID from environment."""
    tmux_pane = os.environ.get('TMUX_PANE')
    if tmux_pane:
        return f"tmux_{tmux_pane.lstrip('%')}"
    try:
        tty_path = os.ttyname(sys.stdin.fileno())
        safe = tty_path.replace('/', '_').lstrip('_').replace('dev_', '')
        return f"term_{safe}"
    except Exception:
        pass
    return "default"


def _find_transaction_file(instance_id: str) -> Optional[Path]:
    """
    Find the active transaction file for this instance.

    Checks instance_projects first to find the right project,
    then looks for the transaction file there.
    """
    # Check instance_projects for current project
    instance_file = Path.home() / '.empirica' / 'instance_projects' / f'{instance_id}.json'
    if instance_file.exists():
        try:
            with open(instance_file, 'r') as f:
                data = json.load(f)
            project_path = data.get('project_path')
            if project_path:
                tx_file = Path(project_path) / '.empirica' / f'active_transaction_{instance_id}.json'
                if tx_file.exists():
                    return tx_file
        except Exception:
            pass

    # Fallback: scan active_work files for project
    for aw_file in Path.home().glob('.empirica/active_work_*.json'):
        try:
            with open(aw_file, 'r') as f:
                data = json.load(f)
            project_path = data.get('project_path')
            if project_path:
                tx_file = Path(project_path) / '.empirica' / f'active_transaction_{instance_id}.json'
                if tx_file.exists():
                    return tx_file
        except Exception:
            continue

    return None


def _get_turn_counter_path(instance_id: str) -> Path:
    """Get path for the turn counter file."""
    return Path.home() / '.empirica' / f'tx_turns_{instance_id}.json'


def _read_turn_counter(instance_id: str) -> dict:
    """Read the turn counter state."""
    counter_path = _get_turn_counter_path(instance_id)
    if counter_path.exists():
        try:
            with open(counter_path, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {"turns": 0, "transaction_id": None, "soft_reminded": False}


def _write_turn_counter(instance_id: str, counter: dict):
    """Write the turn counter state."""
    counter_path = _get_turn_counter_path(instance_id)
    counter_path.parent.mkdir(parents=True, exist_ok=True)
    with open(counter_path, 'w') as f:
        json.dump(counter, f)


def _clear_turn_counter(instance_id: str):
    """Clear turn counter (transaction closed)."""
    counter_path = _get_turn_counter_path(instance_id)
    if counter_path.exists():
        counter_path.unlink()


def main():
    hook_input = json.loads(sys.stdin.read())

    # CRITICAL: Prevent infinite loops
    # If stop_hook_active is True, we already blocked once — let Claude stop
    if hook_input.get('stop_hook_active'):
        # Allow stop — don't re-block
        print(json.dumps({"ok": True, "skipped": True, "reason": "stop_hook_active — avoiding loop"}))
        sys.exit(0)

    instance_id = _get_instance_id()

    # Find open transaction
    tx_file = _find_transaction_file(instance_id)
    if not tx_file:
        # No transaction file found — nothing to enforce
        _clear_turn_counter(instance_id)
        print(json.dumps({"ok": True, "skipped": True, "reason": "no_open_transaction"}))
        sys.exit(0)

    # Read transaction state
    try:
        with open(tx_file, 'r') as f:
            tx_data = json.load(f)
    except Exception:
        print(json.dumps({"ok": True, "skipped": True, "reason": "tx_file_unreadable"}))
        sys.exit(0)

    if tx_data.get('status') != 'open':
        _clear_turn_counter(instance_id)
        print(json.dumps({"ok": True, "skipped": True, "reason": "transaction_not_open"}))
        sys.exit(0)

    # Transaction is open — increment turn counter
    counter = _read_turn_counter(instance_id)
    tx_id = tx_data.get('transaction_id', 'unknown')

    # Reset counter if transaction changed
    if counter.get('transaction_id') != tx_id:
        counter = {"turns": 0, "transaction_id": tx_id, "soft_reminded": False}

    counter['turns'] += 1
    counter['last_stop'] = datetime.now().isoformat()
    _write_turn_counter(instance_id, counter)

    turns = counter['turns']

    # Below soft threshold — allow stop silently
    if turns < SOFT_THRESHOLD:
        print(json.dumps({"ok": True, "turns": turns, "threshold": SOFT_THRESHOLD}))
        sys.exit(0)

    # Between soft and hard threshold — inject reminder but allow stop
    if turns < HARD_THRESHOLD:
        if not counter.get('soft_reminded'):
            counter['soft_reminded'] = True
            _write_turn_counter(instance_id, counter)

        session_id = tx_data.get('session_id', 'unknown')
        output = {
            "hookSpecificOutput": {
                "hookEventName": "Stop",
                "additionalContext": (
                    f"\n## Transaction Discipline Reminder\n\n"
                    f"You have an open transaction ({tx_id[:8]}...) that has been running "
                    f"for {turns} turns without POSTFLIGHT.\n\n"
                    f"**Consider:** Is this a natural commit point? If you've completed a "
                    f"coherent chunk of work, run POSTFLIGHT to close the transaction and "
                    f"capture your learning delta. Then open a new PREFLIGHT for the next chunk.\n\n"
                    f"```bash\n"
                    f"empirica postflight-submit - << 'EOF'\n"
                    f'{{"session_id": "{session_id}", '
                    f'"task_outcome": "<what was accomplished>", '
                    f'"vectors": {{"know": ..., "uncertainty": ..., "completion": ...}}, '
                    f'"reasoning": "<your assessment>"}}\n'
                    f"EOF\n```\n"
                )
            }
        }
        print(json.dumps(output))
        sys.exit(0)

    # At or above hard threshold — BLOCK stop, force POSTFLIGHT
    session_id = tx_data.get('session_id', 'unknown')
    output = {
        "decision": "block",
        "reason": (
            f"Open transaction ({tx_id[:8]}...) has been running for {turns} turns "
            f"without POSTFLIGHT. Submit POSTFLIGHT to close the transaction before stopping. "
            f"This captures your learning delta and enables calibration."
        ),
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": (
                f"\n## POSTFLIGHT Required (Transaction Enforcement)\n\n"
                f"Your transaction has been open for **{turns} turns** (threshold: {HARD_THRESHOLD}). "
                f"Submit POSTFLIGHT now to close the measurement cycle.\n\n"
                f"**Session:** {session_id}\n"
                f"**Transaction:** {tx_id[:8]}...\n\n"
                f"```bash\n"
                f"empirica postflight-submit - << 'EOF'\n"
                f'{{"session_id": "{session_id}", '
                f'"task_outcome": "<what was accomplished in this transaction>", '
                f'"vectors": {{"know": ..., "uncertainty": ..., "context": ..., '
                f'"completion": ..., "impact": ..., "do": ..., "change": ...}}, '
                f'"reasoning": "<honest assessment of this work chunk>"}}\n'
                f"EOF\n```\n\n"
                f"After POSTFLIGHT, start a new PREFLIGHT for the next chunk of work.\n"
            )
        }
    }
    print(json.dumps(output))
    sys.exit(0)


if __name__ == '__main__':
    main()
