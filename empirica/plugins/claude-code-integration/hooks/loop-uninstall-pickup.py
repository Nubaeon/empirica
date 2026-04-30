#!/usr/bin/env python3
"""UserPromptSubmit hook: surface pending loop uninstall requests.

Symmetric inverse of loop-install-pickup.py. When `empirica loop pause`
runs, it can clear `next_scheduled_job_id` from the registry but it
can't call CronDelete itself (that's a Claude Code tool, not a shell
command). The pause handler writes a pending uninstall file at
`~/.empirica/loop_uninstall_pending_{instance_id}_{name}.json`.

This hook reads pending requests for the currently-running instance,
injects them as `additionalContext` in the next prompt (so the running
Claude sees a `<system-reminder>` telling it to call CronDelete with
the recorded job_id), and removes the file so the request fires once.

If Claude doesn't call CronDelete in time, the body's pause check at
the next fire is the backstop — it sees the pause flag and exits
without scheduling the next fire, so the loop dies cleanly after at
most one more silent fire.

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
    from empirica.core.cockpit.loop_uninstall_request import consume_pending
    from empirica.utils.session_resolver import InstanceResolver
except Exception:
    print(json.dumps({}))
    sys.exit(0)


def _format_request(request) -> str:
    requested_by = request.requested_by or 'cockpit'
    return f"""\
## ⚙ Loop uninstall request from {requested_by}

A loop pause was issued and the cron one-shot needs to be cancelled in
this instance:
- **name:** `{request.name}`
- **job_id:** `{request.job_id}`
- **scheduler:** {request.scheduler_kind}
- **reason:** {request.reason}

Please run `CronDelete(\"{request.job_id}\")` to actually stop the cron
from firing. The empirica registry already has the loop marked paused
and `next_scheduled_job_id` cleared — what's left is cancelling the
already-installed scheduler job.

If you don't run CronDelete, the body's pause check at the next fire
is the backstop: the body will see the pause flag and exit without
scheduling the next fire, so the loop dies cleanly after at most one
more silent fire. CronDelete makes that one extra fire go away too.
"""


def main() -> int:
    try:
        instance_id = InstanceResolver.instance_id()
    except Exception:  # noqa: BLE001
        instance_id = None
    if not instance_id:
        print(json.dumps({}))
        return 0

    try:
        requests = consume_pending(instance_id)
    except Exception:  # noqa: BLE001
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
