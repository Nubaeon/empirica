#!/usr/bin/env python3
"""SessionStart hook: arm a Monitor to bridge systemd loop fires into this session.

The Phase 1b wake-from-idle bridge for canonical loops scheduled by
systemd-user timers (goal f718156c). The systemd service ExecStart
(`empirica loop tick`) appends one JSON line per fire to
`~/.empirica/loop_fires.log`. This hook tells the running Claude to
arm a persistent Monitor that tails the log and reacts to each event.

Output: hookSpecificOutput.additionalContext (string) — markdown
instructions telling Claude exactly which Monitor to arm and how to
react to fire events. Empty output when no enabled loops exist (or
systemd isn't available, or the instance can't be resolved).

Non-blocking — any failure path emits empty output so a missing
systemd doesn't break SessionStart.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Plugin script — empirica package on sys.path via plugin bootstrap.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

try:
    from empirica.core.cockpit.canonical_loops import canonical_loop_by_name
    from empirica.core.loop_scheduler import list_active_loops_for_instance
    from empirica.utils.session_resolver import InstanceResolver
except Exception:
    # Empirica package broken / not installed → emit empty output, exit clean.
    print(json.dumps({}))
    sys.exit(0)


def _build_reaction_table(loop_names: list[str]) -> str:
    """Markdown table mapping each active loop → its body skill."""
    rows = []
    for name in loop_names:
        entry = canonical_loop_by_name(name) or {}
        body_skill = entry.get("body_skill") or name
        rows.append(f"| `{name}` | `/{body_skill}` |")
    if not rows:
        return ""
    return (
        "| Loop name | Body skill to invoke on fire |\n"
        "|---|---|\n"
        + "\n".join(rows)
    )


def _build_additional_context(instance_id: str, loop_names: list[str]) -> str:
    fires_log = "~/.empirica/loop_fires.log"
    # tail -F + grep --line-buffered: one match line per event, filtered to
    # this instance only (the log is shared across instances).
    monitor_cmd = (
        f'tail -F {fires_log} 2>/dev/null | '
        f'grep --line-buffered \'"instance_id": "{instance_id}"\''
    )
    return f"""\
## ⚙ Empirica systemd loops armed

The following canonical loops are active for instance `{instance_id}` via
systemd-user timers (they fire on the OS schedule regardless of this
session's state — true synchronous pause is `empirica loop disable <name>`):

{_build_reaction_table(loop_names)}

**Action required at session start:** arm a persistent Monitor that bridges
timer fires into this session. Each new line in `{fires_log}` is one fire
event. The Monitor tool streams matching lines as events into the active
conversation — that's the wake-from-idle mechanism replacing /loop's
in-session CronCreate.

```python
Monitor(
    description="systemd canonical-loop fires for instance {instance_id}",
    command="{monitor_cmd}",
    persistent=True,
)
```

**Reaction protocol** — when a fire event arrives (a JSON line in the chat):

1. Parse the line. The `loop` field tells you which skill to invoke.
2. **If you're mid-transaction:** log a goal `"Process pending fire: <loop>"`
   and continue current work. Pick it up at the next natural break (EWM pattern).
3. **If you're idle (between user prompts):** invoke the matching body skill
   directly via the Skill tool.
4. Body skills self-throttle on open transactions — re-firing is safe.

If you do not arm this Monitor, timer fires will accumulate in the log but
no work will trigger. Arming is idempotent — calling Monitor with the same
command twice is fine.
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
        loops = list_active_loops_for_instance(instance_id)
    except Exception:
        loops = []

    if not loops:
        print(json.dumps({}))
        return 0

    additional = _build_additional_context(instance_id, loops)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": additional,
        },
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
