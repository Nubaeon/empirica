"""Cockpit view onto the notify dispatcher.

Bundles audit-log telemetry + current backend status into one dict
the cockpit can render. Single source of truth so the TUI and the
JSON `--output json` view agree.

The audit log is global (one file at `~/.empirica/notify-dispatcher.jsonl`)
because notify config is global. Per-instance scoping is achieved by
filtering the `recent` list to events whose `source` matches loops
registered to that instance — the cockpit's instance_state does that
join.

Out of scope here: routing-rule preview, hypothetical-event matcher,
topic subscription introspection. Just makes the existing data
legible.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from empirica.core.notify.audit import (
    emit_count,
    fell_back_count,
    last_emit_by_source,
    last_failure,
    read_recent,
)
from empirica.core.notify.backends import get_backend, known_backends
from empirica.core.notify.config import NotifyConfig, load_config

# How long after a failure the cockpit header should banner it.
FAILURE_BANNER_WINDOW_SECONDS = 3600  # 1 hour


def _backends_block(config: NotifyConfig) -> list[dict[str, Any]]:
    """Snapshot of every registered backend with its current status.

    Includes the auth method for ntfy so the cockpit can render
    `bearer @ntfy.sh` style annotations without leaking the secret.
    """
    out: list[dict[str, Any]] = []
    for name in known_backends():
        bcfg = config.backend_config(name)
        backend = get_backend(name, bcfg)
        configured = bool(backend and backend.is_configured())
        item: dict[str, Any] = {
            'name': name,
            'configured': configured,
            'is_default': name == config.default_backend,
        }
        # ntfy-specific surface: auth method + server host (no secret).
        if name == 'ntfy':
            item['auth_method'] = bcfg.get('auth_method', 'none')
            item['server'] = bcfg.get('server') or None
            item['default_topic'] = bcfg.get('default_topic') or None
        out.append(item)
    return out


def _failure_within_window(
    failure_row: dict[str, Any] | None,
    now: datetime,
    window_seconds: int,
) -> dict[str, Any] | None:
    """Return failure row if it's within the alert window, else None."""
    if not failure_row:
        return None
    ts_raw = failure_row.get('ts')
    if not ts_raw:
        return None
    try:
        ts = datetime.fromisoformat(ts_raw)
    except ValueError:
        return None
    age = (now - ts).total_seconds()
    if age > window_seconds:
        return None
    out = dict(failure_row)
    out['age_seconds'] = int(age)
    return out


_EMPTY_BLOCK: dict[str, Any] = {
    'default_backend': None,
    'backends': [],
    'recent': [],
    'last_failure': None,
    'banner_failure': None,
    'fell_back_count_24h': 0,
    'emit_count_24h': 0,
}


def build_notify_dispatcher_block(
    config: NotifyConfig | None = None,
    recent_limit: int = 5,
) -> dict[str, Any]:
    """Return the cockpit-facing dispatcher dict.

    Shape:
      default_backend       str
      backends              list[{name, configured, is_default, ...}]
      recent                list[audit rows] (oldest of slice first)
      last_failure          audit row or None  (most recent ok==False ever)
      banner_failure        audit row or None  (last_failure within 1h)
      fell_back_count_24h   int
      emit_count_24h        int

    Telemetry must never break the cockpit — any read/parse failure
    yields an empty block, never an exception.
    """
    try:
        cfg = config if config is not None else load_config()
        now = datetime.now(tz=UTC)
        failure = last_failure()
        return {
            'default_backend': cfg.default_backend,
            'backends': _backends_block(cfg),
            'recent': read_recent(limit=recent_limit),
            'last_failure': failure,
            'banner_failure': _failure_within_window(
                failure, now, FAILURE_BANNER_WINDOW_SECONDS,
            ),
            'fell_back_count_24h': fell_back_count(window_hours=24.0),
            'emit_count_24h': emit_count(window_hours=24.0),
        }
    except Exception:  # noqa: BLE001 — never break cockpit on telemetry
        return dict(_EMPTY_BLOCK)


def annotate_loops_with_last_notify(
    loops_dict: dict[str, dict[str, Any]],
    instance_label: str | None = None,
    audit_path: Any = None,
) -> None:
    """Mutate `loops_dict` in place, adding a `last_notify` field per loop.

    Match key: source == "loop:{name}". Loops without a matching audit
    row get last_notify=None.

    `instance_label` is currently unused (audit log doesn't include
    instance scope) but reserved for future per-instance audit.

    `audit_path`: optional override for tests.
    """
    if not loops_dict:
        return
    sources = [f'loop:{name}' for name in loops_dict]
    by_source = last_emit_by_source(sources, path=audit_path)
    for name, loop in loops_dict.items():
        row = by_source.get(f'loop:{name}')
        loop['last_notify'] = (
            {
                'ts': row.get('ts'),
                'resolved_backend': row.get('resolved_backend'),
                'topic': row.get('topic'),
                'fell_back': bool(row.get('fell_back')),
                'ok': bool(row.get('ok')),
            }
            if row
            else None
        )


__all__ = [
    'FAILURE_BANNER_WINDOW_SECONDS',
    'annotate_loops_with_last_notify',
    'build_notify_dispatcher_block',
]
