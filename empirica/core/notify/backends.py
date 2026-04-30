"""Backend implementations — stdout, log, ntfy.

Each backend implements the same interface (name attribute, is_configured(),
emit(event)) but they're not formal subclasses — duck-typed for clarity.

Three sharp edges enforced here:
  1. Ntfy uses JSON publish format ONLY (no header-stuffing — emoji bug)
  2. Actions are forwarded as ntfy's exact schema (no invented DSL)
  3. Auth is read from the env var named in config; never from YAML
"""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from empirica.core.notify.event import EmitResult, NotifyEvent

# ─── stdout ────────────────────────────────────────────────────────────────


class StdoutBackend:
    name = 'stdout'

    def __init__(self, _config: dict[str, Any] | None = None):
        self._config = _config or {}

    def is_configured(self) -> bool:
        return True  # always works

    def emit(self, event: NotifyEvent) -> EmitResult:
        lines = [f'[{event.severity.upper()}] Empirica notify · {event.source or "manual"}']
        lines.append(f'  {event.title}')
        if event.message:
            lines.append(f'  {event.message}')
        if event.rationale:
            lines.append(f'  Rationale: {event.rationale}')
        if event.tags:
            lines.append(f'  Tags: {", ".join(event.tags)}')
        if event.click_url:
            lines.append(f'  Click: {event.click_url}')
        if event.actions:
            actions_str = ', '.join(f'{label} → {url}' for label, url in event.actions)
            lines.append(f'  Actions: {actions_str}')
        if event.topic:
            lines.append(f'  Topic: {event.topic}')
        sys.stdout.write('\n'.join(lines) + '\n')
        sys.stdout.flush()
        return EmitResult(backend=self.name, ok=True, detail='printed to stdout')


# ─── log ───────────────────────────────────────────────────────────────────


class LogBackend:
    name = 'log'

    def __init__(self, config: dict[str, Any] | None = None):
        config = config or {}
        path_raw = config.get('path') or str(Path.home() / '.empirica' / 'notify.log')
        self.path = Path(path_raw).expanduser()
        self.max_size_mb = int(config.get('max_size_mb', 10) or 10)
        self.keep_files = int(config.get('keep_files', 5) or 5)

    def is_configured(self) -> bool:
        return True

    def _maybe_rotate(self) -> None:
        try:
            if not self.path.exists():
                return
            if self.path.stat().st_size <= self.max_size_mb * 1024 * 1024:
                return
            # Rotate: notify.log -> notify.log.1 -> .2 -> ...
            for i in range(self.keep_files - 1, 0, -1):
                src = self.path.with_suffix(self.path.suffix + f'.{i}')
                dst = self.path.with_suffix(self.path.suffix + f'.{i + 1}')
                if src.exists():
                    src.replace(dst)
            self.path.replace(self.path.with_suffix(self.path.suffix + '.1'))
        except OSError:
            # Rotation is best-effort; never block emit on it.
            pass

    def emit(self, event: NotifyEvent) -> EmitResult:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._maybe_rotate()
            entry = {
                'ts': datetime.now(tz=UTC).isoformat(),
                **event.to_dict(),
            }
            with open(self.path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry) + '\n')
            return EmitResult(backend=self.name, ok=True,
                              detail=f'appended to {self.path}')
        except OSError as e:
            return EmitResult(backend=self.name, ok=False, detail=f'write failed: {e}')


# ─── ntfy ──────────────────────────────────────────────────────────────────

_SEVERITY_TO_NTFY_PRIORITY = {
    'info': 3,        # default
    'warning': 4,     # high
    'critical': 5,    # max
}


class NtfyBackend:
    """ntfy.sh backend — JSON publish format only.

    Spec: https://docs.ntfy.sh/publish/#publish-as-json

    Why JSON-only: header-stuffing breaks on emoji (latin-1 codec error).
    David and Cortex Claude have both hit this. The JSON body form is
    UTF-8 native and avoids the bug entirely.
    """
    name = 'ntfy'

    def __init__(self, config: dict[str, Any] | None = None):
        config = config or {}
        self.server = (config.get('server') or '').rstrip('/')
        self.auth_method = config.get('auth_method', 'none')  # basic | bearer | none
        self.auth_env = config.get('auth_env')
        self.default_topic = config.get('default_topic')
        self.default_priority = int(config.get('default_priority', 3) or 3)

    def is_configured(self) -> bool:
        if not self.server:
            return False
        if self.auth_method in ('basic', 'bearer'):
            if not self.auth_env:
                return False
            if not os.environ.get(self.auth_env):
                return False
        return True

    def _auth_header(self) -> dict[str, str]:
        if self.auth_method == 'none' or not self.auth_env:
            return {}
        secret = os.environ.get(self.auth_env, '')
        if not secret:
            return {}
        if self.auth_method == 'basic':
            # secret format: 'user:pass'
            encoded = base64.b64encode(secret.encode('utf-8')).decode('ascii')
            return {'Authorization': f'Basic {encoded}'}
        if self.auth_method == 'bearer':
            return {'Authorization': f'Bearer {secret}'}
        return {}

    def _build_payload(self, event: NotifyEvent) -> dict[str, Any]:
        priority = _SEVERITY_TO_NTFY_PRIORITY.get(event.severity, self.default_priority)
        topic = event.topic or self.default_topic
        payload: dict[str, Any] = {
            'topic': topic,
            'title': event.title,
            'message': event.message,
            'priority': priority,
        }
        if event.tags:
            payload['tags'] = list(event.tags)
        if event.click_url:
            payload['click'] = event.click_url
        if event.actions:
            # ntfy expects {action, label, url} — 'view' is the click action.
            payload['actions'] = [
                {'action': 'view', 'label': label, 'url': url}
                for label, url in event.actions
            ]
        return payload

    def emit(self, event: NotifyEvent) -> EmitResult:
        if not self.is_configured():
            return EmitResult(
                backend=self.name, ok=False,
                detail='not configured — server URL or auth env var missing',
            )

        payload = self._build_payload(event)
        if not payload.get('topic'):
            return EmitResult(
                backend=self.name, ok=False,
                detail='no topic — set default_topic in config or pass --topic-override',
            )

        body = json.dumps(payload).encode('utf-8')
        headers = {
            'Content-Type': 'application/json',
            **self._auth_header(),
        }
        req = urllib.request.Request(self.server + '/', data=body,
                                      headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                code = resp.getcode()
                return EmitResult(
                    backend=self.name, ok=200 <= code < 300,
                    detail=f'ntfy {code}',
                    response_code=code,
                )
        except urllib.error.HTTPError as e:
            return EmitResult(
                backend=self.name, ok=False,
                detail=f'ntfy {e.code} {e.reason}',
                response_code=e.code,
            )
        except urllib.error.URLError as e:
            return EmitResult(
                backend=self.name, ok=False,
                detail=f'network error: {e.reason}',
            )
        except Exception as e:
            return EmitResult(backend=self.name, ok=False, detail=f'unexpected: {e}')


# ─── registry ──────────────────────────────────────────────────────────────

_BACKEND_CLASSES = {
    'stdout': StdoutBackend,
    'log': LogBackend,
    'ntfy': NtfyBackend,
}


def get_backend(name: str, config: dict[str, Any] | None = None):
    """Instantiate a backend by name. Returns None for unknown names so
    the dispatcher can surface a clean error rather than crash."""
    cls = _BACKEND_CLASSES.get(name)
    if cls is None:
        return None
    return cls(config or {})


def known_backends() -> list[str]:
    return sorted(_BACKEND_CLASSES.keys())


def backends_status_snapshot(config) -> list[dict[str, Any]]:
    """Single source of truth for `is each backend configured right now?`.

    Used by both `empirica notify backends` and the cockpit dispatcher view
    so the two views can never disagree about whether a backend is
    configured. Includes ntfy auth_method/server/default_topic for the
    cockpit's display (no secret).

    Pass a NotifyConfig (typed) so callers don't replicate
    config.backend_config(name) lookups.
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
        if name == 'ntfy':
            item['auth_method'] = bcfg.get('auth_method', 'none')
            item['server'] = bcfg.get('server') or None
            item['default_topic'] = bcfg.get('default_topic') or None
        out.append(item)
    return out


__all__ = [
    'LogBackend',
    'NtfyBackend',
    'StdoutBackend',
    'backends_status_snapshot',
    'get_backend',
    'known_backends',
]
