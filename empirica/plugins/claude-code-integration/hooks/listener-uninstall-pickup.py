#!/usr/bin/env python3
"""UserPromptSubmit hook: surface pending listener uninstall requests.

Symmetric inverse of listener-install-pickup.py. When
`empirica listener pause` runs against an armed listener (active
runtime file present), the pause handler writes a pending file at
`~/.empirica/listener_uninstall_pending_{instance_id}_{name}.json`
containing the Monitor task id + curl PID.

This hook reads pending requests for the running instance, injects
them as `additionalContext` asking the running Claude to TaskStop the
Monitor, kill the curl PID, and delete the listener_active_*.json
runtime file.

If Claude doesn't run TaskStop/kill in time, the listener body's pause
check at next wake is the backstop — the body will see the pause flag
and exit without re-arming the wake handler. The connection eventually
drops; the loop dies cleanly.

Hook output: hookSpecificOutput.additionalContext (string) or empty
when no pending requests. Non-blocking — failures swallowed so a bad
pending file never breaks the user's prompt.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Plugin script — empirica package is on sys.path via session-init bootstrap.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

try:
    from empirica.core.cockpit.listener_uninstall_request import consume_pending
    from empirica.utils.session_resolver import InstanceResolver
except Exception:
    print(json.dumps({}))
    sys.exit(0)


def _format_request(request) -> str:
    requested_by = request.requested_by or 'cockpit'
    pid_line = (
        f"- **curl_pid:** `{request.curl_pid}`\n"
        if request.curl_pid is not None else ''
    )
    pid_kill = (
        f"     and `kill {request.curl_pid}` to drop the held connection.\n"
        if request.curl_pid is not None else ''
    )
    return f"""\
## ⚙ Listener uninstall request from {requested_by}

A listener pause was issued and the held connection + Monitor need to
be cancelled in this instance:
- **name:** `{request.name}`
- **monitor_task_id:** `{request.monitor_task_id}`
{pid_line}- **reason:** {request.reason}

Please run:
  1. `TaskStop("{request.monitor_task_id}")` to disarm the Monitor,
{pid_kill}  2. Delete `~/.empirica/listener_active_{{INSTANCE}}_{request.name}.json`
     to clear the runtime metadata.

The empirica registry already has the listener marked paused — what's
left is killing the held connection so events stop being delivered.

If you don't run TaskStop/kill, the listener body's pause check at the
next wake is the backstop: the body will see the pause flag and exit
without re-arming. TaskStop makes that immediate.
"""


def main() -> int:
    try:
        instance_id = InstanceResolver.instance_id()
    except Exception:
        instance_id = None
    if not instance_id:
        print(json.dumps({}))
        return 0

    try:
        requests = consume_pending(instance_id)
    except Exception:
        requests = []

    if not requests:
        print(json.dumps({}))
        return 0

    blocks = [_format_request(r) for r in requests]
    additional = '\n\n'.join(blocks)
    print(json.dumps({
        'hookSpecificOutput': {
            'hookEventName': 'UserPromptSubmit',
            'additionalContext': additional,
        },
    }))
    return 0


if __name__ == '__main__':
    sys.exit(main())
