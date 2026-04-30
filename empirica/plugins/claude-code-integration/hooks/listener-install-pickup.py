#!/usr/bin/env python3
"""UserPromptSubmit hook: surface pending listener install requests.

Symmetric to loop-install-pickup.py but for event listeners
(PROPOSAL_EVENT_LISTENER.md item 4). When `empirica listener
install-request` runs, it writes a pending file at
`~/.empirica/listener_install_pending_{instance_id}_{name}.json` with
an inbox-listener skill prompt template substituted with the
listener's name + topic + on-wake handler.

This hook reads pending requests for the running instance, injects
them as `additionalContext` in the next prompt (so the running Claude
sees a `<system-reminder>` telling it to invoke /inbox-listener with
the embedded prompt), and removes the file so the request fires once.

The Claude reading the system-reminder runs the inbox-listener skill
which arms the listener (background curl + Monitor) and writes the
listener_active_*.json runtime metadata.

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
    from empirica.core.cockpit.listener_install_request import consume_pending
    from empirica.utils.session_resolver import InstanceResolver
except Exception:
    print(json.dumps({}))
    sys.exit(0)


def _format_request(request) -> str:
    requested_by = request.requested_by or 'cockpit'
    return f"""\
## ⚙ Listener install request from {requested_by}

A listener is queued for installation in this instance:
- **name:** `{request.name}`
- **topic:** `{request.topic}`
- **description:** {request.description or '(none)'}

Please run `/inbox-listener` with the prompt below to arm the listener.
The empirica registry already has the listener registered (visible in
the cockpit), but the actual held connection (curl) and Monitor wake
need to be armed by you.

```
{request.prompt_template}
```
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
