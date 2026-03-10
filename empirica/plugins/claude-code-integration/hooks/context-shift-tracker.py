#!/usr/bin/env python3
"""UserPromptSubmit hook: Track context shifts in epistemic transactions.

Classifies user prompts as:
- SOLICITED: AI asked a question (AskUserQuestion) → user responded
- UNSOLICITED: User initiated a new prompt without being asked

Uses a purely structural signal — no keyword matching:
- sentinel-gate.py sets pending_user_response=True when AskUserQuestion fires
- This hook checks that flag on each UserPromptSubmit event

Counts are stored in the active transaction file for POSTFLIGHT consumption.
Next-PREFLIGHT uses them to explain calibration divergence from context shifts.
"""

import json
import os
import sys
import tempfile
from pathlib import Path


def get_instance_id():
    """Get instance identifier from TMUX_PANE or fallback."""
    pane = os.environ.get('TMUX_PANE', '')
    if pane:
        return f"tmux{pane.replace('%', '')}"
    return None


def _find_transaction_file(claude_session_id: str = None) -> 'Path | None':
    """Find the active transaction file using the same priority as sentinel-gate."""
    instance_id = get_instance_id()
    suffix = f'_{instance_id}' if instance_id else ''

    # Try 1: active_work file for project_path
    if claude_session_id:
        aw_file = Path.home() / '.empirica' / f'active_work_{claude_session_id}.json'
        if aw_file.exists():
            try:
                with open(aw_file, 'r') as f:
                    pp = json.load(f).get('project_path')
                if pp:
                    candidate = Path(pp) / '.empirica' / f'active_transaction{suffix}.json'
                    if candidate.exists():
                        return candidate
            except Exception:
                pass

    # Try 2: instance_projects mapping
    if instance_id:
        ip_file = Path.home() / '.empirica' / 'instance_projects' / f'{instance_id}.json'
        if ip_file.exists():
            try:
                with open(ip_file, 'r') as f:
                    pp = json.load(f).get('project_path')
                if pp:
                    candidate = Path(pp) / '.empirica' / f'active_transaction{suffix}.json'
                    if candidate.exists():
                        return candidate
            except Exception:
                pass

    # Try 3: global fallback
    candidate = Path.home() / '.empirica' / f'active_transaction{suffix}.json'
    if candidate.exists():
        return candidate

    return None


def main():
    hook_input = json.loads(sys.stdin.read() or '{}')
    claude_session_id = hook_input.get('session_id')

    tx_path = _find_transaction_file(claude_session_id)
    if not tx_path:
        # No active transaction — nothing to track
        print(json.dumps({}))
        return

    try:
        with open(tx_path, 'r') as f:
            tx = json.load(f)

        if tx.get('status') != 'open':
            print(json.dumps({}))
            return

        # Check the structural signal
        was_solicited = tx.pop('pending_user_response', False)

        if was_solicited:
            tx['solicited_prompt_count'] = tx.get('solicited_prompt_count', 0) + 1
        else:
            tx['unsolicited_prompt_count'] = tx.get('unsolicited_prompt_count', 0) + 1

        # Atomic write-back
        fd, tmp = tempfile.mkstemp(dir=str(tx_path.parent))
        try:
            with os.fdopen(fd, 'w') as tf:
                json.dump(tx, tf, indent=2)
            os.rename(tmp, str(tx_path))
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass

    except Exception:
        pass

    print(json.dumps({}))


if __name__ == '__main__':
    main()
