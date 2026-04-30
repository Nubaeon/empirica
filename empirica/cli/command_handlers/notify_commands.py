"""CLI handlers for `empirica notify` subcommand group.

Verbs:
  emit      Emit a notify event through the configured backend
  config    Print effective config (with secrets redacted)
  backends  List registered backends + status
  test      Send a test event ('Empirica notify test: ...')
"""

from __future__ import annotations

import json
import sys

from empirica.core.notify import (
    NotifyEvent,
    dispatch,
    load_config,
    parse_actions,
    parse_tags,
    redact_config,
)
from empirica.core.notify.backends import backends_status_snapshot
from empirica.core.notify.event import VALID_SEVERITY


def _emit_output(args, payload: dict, exit_code: int) -> int:
    """JSON output unless --output human."""
    fmt = getattr(args, 'output', 'json')
    if fmt == 'human':
        # Skip extra output — backends already print to stdout where appropriate.
        if not payload.get('ok', True):
            sys.stderr.write(f'[empirica notify] {payload.get("detail", "failed")}\n')
    else:
        sys.stdout.write(json.dumps(payload, indent=2) + '\n')
    return exit_code


def handle_notify_emit_command(args) -> int:
    """`empirica notify emit` — single dispatch verb every caller uses."""
    severity = getattr(args, 'severity', None)
    if severity not in VALID_SEVERITY:
        return _emit_output(args, {
            'ok': False,
            'detail': f'invalid severity {severity!r} — must be one of {list(VALID_SEVERITY)}',
        }, 1)

    title = getattr(args, 'title', None) or ''
    message = getattr(args, 'message', None) or ''
    if not title:
        return _emit_output(args, {
            'ok': False,
            'detail': '--title is required',
        }, 1)

    event = NotifyEvent(
        severity=severity,
        title=title,
        message=message,
        rationale=getattr(args, 'rationale', None),
        tags=parse_tags(getattr(args, 'tags', None)),
        click_url=getattr(args, 'click_url', None),
        actions=parse_actions(getattr(args, 'actions', None)),
        source=getattr(args, 'source', None),
    )

    try:
        config = load_config()
    except Exception as e:
        return _emit_output(args, {
            'ok': False, 'detail': f'config load failed: {e}',
        }, 1)

    # Apply config-level defaults (e.g. click_url_base when click_url unset).
    if not event.click_url:
        base = config.defaults.get('click_url_base')
        if base:
            event.click_url = str(base)

    result = dispatch(
        event,
        config,
        backend_override=getattr(args, 'backend_override', None),
        topic_override=getattr(args, 'topic_override', None),
        dry_run=getattr(args, 'dry_run', False),
    )

    payload = {
        'ok': result.emit_result.ok,
        'backend': result.resolved_backend,
        'topic': result.resolved_topic,
        'fell_back': result.fell_back,
        'fallback_reason': result.fallback_reason,
        'detail': result.emit_result.detail,
        'response_code': result.emit_result.response_code,
        'dry_run': getattr(args, 'dry_run', False),
    }

    # Exit codes per spec:
    #   0 emitted (or dry-run completed)
    #   1 config error  (handled above before dispatch)
    #   2 backend rejected (4xx/5xx)
    #   3 backend unavailable (network/timeout)
    if result.emit_result.ok:
        exit_code = 0
    else:
        rc = result.emit_result.response_code
        detail = (result.emit_result.detail or '').lower()
        if rc and 400 <= rc < 600:
            exit_code = 2
        elif 'network' in detail or 'timeout' in detail or 'unavailable' in detail:
            exit_code = 3
        else:
            exit_code = 2  # default to "rejected"
    return _emit_output(args, payload, exit_code)


def handle_notify_config_command(args) -> int:
    """`empirica notify config` — print effective config with secrets redacted."""
    try:
        config = load_config()
    except Exception as e:
        return _emit_output(args, {
            'ok': False, 'detail': f'config load failed: {e}',
        }, 1)
    sys.stdout.write(json.dumps({
        'ok': True,
        'config': redact_config(config),
    }, indent=2) + '\n')
    return 0


def handle_notify_backends_command(args) -> int:
    """`empirica notify backends` — list registered backends + configured status."""
    try:
        config = load_config()
    except Exception as e:
        return _emit_output(args, {
            'ok': False, 'detail': f'config load failed: {e}',
        }, 1)

    sys.stdout.write(json.dumps({
        'ok': True,
        'default_backend': config.default_backend,
        'backends': backends_status_snapshot(config),
    }, indent=2) + '\n')
    return 0


def handle_notify_test_command(args) -> int:
    """`empirica notify test` — send a test event so the user can verify
    end-to-end delivery without crafting a full emit invocation."""
    backend = getattr(args, 'backend', None)
    event = NotifyEvent(
        severity='info',
        title='🔔 Empirica notify — test event',
        message=f'Test fire from `empirica notify test`{" via " + backend if backend else ""}',
        rationale='If you can read this, the dispatcher path works end-to-end.',
        tags=['empirica', 'notify-test'],
        source='manual:notify-test',
    )

    try:
        config = load_config()
    except Exception as e:
        return _emit_output(args, {
            'ok': False, 'detail': f'config load failed: {e}',
        }, 1)

    result = dispatch(event, config, backend_override=backend)
    sys.stdout.write(json.dumps({
        'ok': result.emit_result.ok,
        'backend': result.resolved_backend,
        'fell_back': result.fell_back,
        'detail': result.emit_result.detail,
    }, indent=2) + '\n')
    return 0 if result.emit_result.ok else 2


# ─── group dispatch ────────────────────────────────────────────────────────

_NOTIFY_DISPATCH = {
    'emit': handle_notify_emit_command,
    'config': handle_notify_config_command,
    'backends': handle_notify_backends_command,
    'test': handle_notify_test_command,
}


def handle_notify_group_command(args) -> int:
    """Dispatcher for `empirica notify <action>`."""
    action = getattr(args, 'notify_action', None)
    if not action:
        sys.stderr.write(
            'usage: empirica notify <emit|config|backends|test> [args...]\n'
        )
        return 2
    handler = _NOTIFY_DISPATCH.get(action)
    if handler is None:
        sys.stderr.write(f'error: unknown notify action: {action}\n')
        return 2
    return handler(args) or 0


__all__ = [
    'handle_notify_backends_command',
    'handle_notify_config_command',
    'handle_notify_emit_command',
    'handle_notify_group_command',
    'handle_notify_test_command',
]
