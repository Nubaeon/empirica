"""Empirica Cockpit — multi-instance state visibility and per-instance controls.

This module is the core for the `empirica sentinel`, `empirica loop`, and
`empirica status` CLI subcommands. It is intentionally narrow:

- sentinel_pause: wraps the existing ~/.empirica/sentinel_paused_{instance_id}
  pause file. Does NOT reinvent — defers to the same path the Sentinel hook
  already reads.
- loop_registry: per-instance ~/.empirica/loops_{instance_id}.json registry.
  Provides register/pause/resume/heartbeat/list/status/unregister.
- instance_state: state-file scan to discover instances and aggregate
  transaction/sentinel/loop state into one dict per instance.
- render: pretty (ANSI) and machine-readable JSON renderers for `status`.

State-file discovery, no process scanning, no tmux dependency.
"""

from empirica.core.cockpit.instance_actions import (
    ForgetResult,
    KillResult,
    forget_instance,
    get_label,
    kill_instance,
    set_label,
)
from empirica.core.cockpit.instance_state import (
    aggregate_all,
    aggregate_instance_state,
    discover_instances,
)
from empirica.core.cockpit.loop_registry import (
    LoopRegistry,
    is_loop_paused,
    set_loop_paused,
)
from empirica.core.cockpit.render import render_json, render_pretty
from empirica.core.cockpit.sentinel_pause import (
    SentinelPauseStatus,
    pause_sentinel,
    resume_sentinel,
    sentinel_status,
)

__all__ = [
    'ForgetResult',
    'KillResult',
    'LoopRegistry',
    'SentinelPauseStatus',
    'aggregate_all',
    'aggregate_instance_state',
    'discover_instances',
    'forget_instance',
    'get_label',
    'is_loop_paused',
    'kill_instance',
    'pause_sentinel',
    'render_json',
    'render_pretty',
    'resume_sentinel',
    'sentinel_status',
    'set_label',
    'set_loop_paused',
]
