"""Empirica notify dispatcher — pluggable notification primitive.

Per `OutreachShared/empirica-final-docs/PROPOSAL_NOTIFY_DISPATCHER.md`.

The dispatcher is a primitive, not a behavior:
  - Callers describe an event (severity / title / message / actions / ...)
  - Config decides where it goes (stdout / log / ntfy / future backends)
  - Empirica core does NOT decide WHEN events fire — that's user-side
    automation (Claude Code hooks, cron loops, manual scripts)

Three sharp edges:
  1. Ntfy uses JSON publish format ONLY (no header-stuffing — emoji bug)
  2. --actions mirrors ntfy's "Label|URL" format exactly (no DSL)
  3. Auth via env var, never YAML (config names the env var, not the secret)
"""

from empirica.core.notify.config import (
    NotifyConfig,
    load_config,
    redact_config,
)
from empirica.core.notify.dispatcher import (
    DispatchResult,
    dispatch,
)
from empirica.core.notify.event import (
    EmitResult,
    NotifyEvent,
    parse_actions,
    parse_tags,
)

__all__ = [
    'DispatchResult',
    'EmitResult',
    'NotifyConfig',
    'NotifyEvent',
    'dispatch',
    'load_config',
    'parse_actions',
    'parse_tags',
    'redact_config',
]
