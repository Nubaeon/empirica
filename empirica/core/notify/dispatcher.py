"""Dispatcher — resolves backend + topic from config, calls emit, falls
back to stdout when the resolved backend isn't configured.

Resolution order per emit:
  1. --backend-override (if set)
  2. First matching routing rule (severity / source / topic / tags)
  3. default_backend

If the resolved backend has is_configured()==False (e.g. ntfy auth env
var unset), fall back to stdout AND emit a warning to stderr. NEVER
silently drop notifications.
"""

from __future__ import annotations

import fnmatch
import sys
from dataclasses import dataclass

from empirica.core.notify.audit import append_audit
from empirica.core.notify.backends import get_backend
from empirica.core.notify.config import NotifyConfig, RoutingRule
from empirica.core.notify.event import EmitResult, NotifyEvent


@dataclass
class DispatchResult:
    """What dispatch() returns — covers both successful and fallback paths."""
    resolved_backend: str
    resolved_topic: str | None
    fell_back: bool                # True when the resolved backend wasn't configured
    fallback_reason: str | None
    emit_result: EmitResult


def _rule_matches(rule: RoutingRule, event: NotifyEvent) -> bool:
    """Match rule criteria to an event. Empty match dict matches everything.

    Supported keys: severity, source (glob), topic (glob), tag (any-tag glob).
    All specified criteria must match (AND semantics within a rule).
    """
    match = rule.match or {}
    if not match:
        return True

    # severity is exact match
    if 'severity' in match and match['severity'] != event.severity:
        return False

    # source uses glob (e.g. "loop:*", "hook:postflight")
    if 'source' in match:
        pattern = str(match['source'])
        if not event.source or not fnmatch.fnmatch(event.source, pattern):
            return False

    # topic uses glob
    if 'topic' in match:
        pattern = str(match['topic'])
        if not event.topic or not fnmatch.fnmatch(event.topic, pattern):
            return False

    # tag matches if ANY event tag matches the glob
    if 'tag' in match:
        pattern = str(match['tag'])
        if not any(fnmatch.fnmatch(t, pattern) for t in event.tags):
            return False

    return True


def _resolve(
    event: NotifyEvent,
    config: NotifyConfig,
    backend_override: str | None,
    topic_override: str | None,
) -> tuple[str, str | None]:
    """Pick backend name + topic for this event.

    Returns (backend_name, topic). topic is None when the backend doesn't
    use topics (stdout, log).
    """
    if backend_override:
        return backend_override, topic_override

    for rule in config.routing:
        if _rule_matches(rule, event):
            return rule.backend, topic_override or rule.topic

    return config.default_backend, topic_override


def _audit(
    event: NotifyEvent,
    resolved_backend: str,
    resolved_topic: str | None,
    fell_back: bool,
    fallback_reason: str | None,
    emit_result: EmitResult,
    project_id: str | None,
) -> None:
    """Best-effort audit append. Telemetry never blocks emit."""
    append_audit(
        source=event.source,
        severity=event.severity,
        topic=resolved_topic,
        resolved_backend=resolved_backend,
        fell_back=fell_back,
        fallback_reason=fallback_reason,
        ok=emit_result.ok,
        response_code=emit_result.response_code,
        detail=emit_result.detail,
        project_id=project_id,
    )


def dispatch(
    event: NotifyEvent,
    config: NotifyConfig,
    backend_override: str | None = None,
    topic_override: str | None = None,
    dry_run: bool = False,
    project_id: str | None = None,
) -> DispatchResult:
    """Send `event` through the configured backend, falling back to stdout
    when the resolved backend isn't configured.

    `dry_run`: don't emit, just return the resolved decision (no audit row).
    `project_id`: optional caller-supplied identifier recorded in the audit
    log so cockpit views can render cross-project routing.
    """
    backend_name, topic = _resolve(event, config, backend_override, topic_override)

    # Stamp resolved topic onto the event for backends that use it.
    if topic and not event.topic:
        event.topic = topic

    if dry_run:
        return DispatchResult(
            resolved_backend=backend_name,
            resolved_topic=topic,
            fell_back=False,
            fallback_reason=None,
            emit_result=EmitResult(
                backend=backend_name, ok=True,
                detail=f'[dry-run] would emit via {backend_name}'
                       f'{" topic=" + topic if topic else ""}',
            ),
        )

    backend = get_backend(backend_name, config.backend_config(backend_name))
    if backend is None:
        # Unknown backend name — fall back to stdout with a clear warning.
        sys.stderr.write(
            f'[empirica notify] WARN: unknown backend "{backend_name}" — '
            f'falling back to stdout\n'
        )
        fb = get_backend('stdout', {})
        result = fb.emit(event) if fb is not None else EmitResult(
            backend='stdout', ok=False, detail='no backends available',
        )
        fallback_reason = f'unknown backend "{backend_name}"'
        _audit(event, backend_name, topic, True, fallback_reason, result, project_id)
        return DispatchResult(
            resolved_backend=backend_name,
            resolved_topic=topic,
            fell_back=True,
            fallback_reason=fallback_reason,
            emit_result=result,
        )

    if not backend.is_configured():
        # Configured but missing creds (ntfy auth env unset, etc.) — fall
        # back to stdout + warn. NEVER silently drop.
        sys.stderr.write(
            f'[empirica notify] WARN: backend "{backend_name}" not configured — '
            f'falling back to stdout (was missing credentials or required config)\n'
        )
        fb = get_backend('stdout', {})
        result = fb.emit(event) if fb is not None else EmitResult(
            backend='stdout', ok=False, detail='no backends available',
        )
        fallback_reason = f'{backend_name} not configured'
        _audit(event, backend_name, topic, True, fallback_reason, result, project_id)
        return DispatchResult(
            resolved_backend=backend_name,
            resolved_topic=topic,
            fell_back=True,
            fallback_reason=fallback_reason,
            emit_result=result,
        )

    emit_result = backend.emit(event)
    _audit(event, backend_name, topic, False, None, emit_result, project_id)
    return DispatchResult(
        resolved_backend=backend_name,
        resolved_topic=topic,
        fell_back=False,
        fallback_reason=None,
        emit_result=emit_result,
    )


__all__ = ['DispatchResult', 'dispatch']
