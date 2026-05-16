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
    # T8 (goal f718156c): switched from `tail -F loop_fires.log` to
    # `empirica loop listen` — the listener is the push-primary wake
    # mechanism. It holds an ntfy stream to cortex, emits one stdout
    # line per ECO-decided proposal event (catch-up content_poll on
    # every push arrival + on every reconnect). Each stdout line is
    # one Monitor wake event into the running Claude session.
    monitor_cmd = f"empirica loop listen --instance {instance_id}"
    return f"""\
## 📬 Empirica orchestration listener — arm at session start

This instance (`{instance_id}`) has canonical loops registered. The
push-primary wake mechanism is `empirica loop listen` — it holds an
authenticated ntfy stream to Cortex and emits one stdout line per
ECO-decided proposal event (real wake) or AI-to-AI completion ack.

{_build_reaction_table(loop_names)}

**Arm this Monitor at session start:**

```python
Monitor(
    description="Cortex orchestration push listener for {instance_id}",
    command="{monitor_cmd}",
    persistent=True,
)
```

The listener does the right thing on every failure mode: catches up via
content_poll on initial start, on each push arrival, AND on disconnect
+ reconnect. No periodic timer needed — push-primary, poll-on-reconnect-only
("epistemic email for the AI age" — David, 2026-05-15).

**Reaction protocol** — when an event arrives (one JSON line in the chat):

1. Read `direction` field:
   - `inbox` → ECO-decided proposal targeting you (act per status)
   - `outbox` → ack/refinement on a proposal you emitted (informational)
2. **If mid-transaction:** log a goal `"Process <direction>/<status>: <proposal_id>"`
   and pick up at next natural break (EWM pattern).
3. **If idle:** invoke `/cortex-mailbox-poll` skill — it has the per-direction
   per-status reaction protocol (act on accepted, refine on changed,
   acknowledge on completed, etc.).

**ECO-gated autonomy property:** every event you act on traces back to an
ECO actor decision (`eco_actor` field). The listener filters `eco_review`
proposals server-side — they never cross the wake boundary. Even if the
ntfy stream were compromised, your status re-verification against Cortex
by `proposal_id` is the auth boundary.

If you do not arm this Monitor, events will accumulate at Cortex but no
work will trigger in this session. Arming is idempotent (Monitor with
identical command is a no-op the second time).
"""


def main() -> int:
    # Use ai_id (project basename) for timer-name lookup, not the ephemeral
    # tmux pane id. Timers are named `empirica-loop-<ai_id>-<loop>.timer`
    # so they survive tmux restarts; the hook must query with the same
    # stable id the installer used. Falls back to instance_id only for
    # legacy/unconfigured environments. (David, 2026-05-16)
    try:
        instance_id = InstanceResolver.ai_id() or InstanceResolver.instance_id()
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
