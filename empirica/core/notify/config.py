"""Notify config loader — ~/.empirica/notify.yaml.

Sane defaults so empirica works out of the box without external services
(stdout backend with no config). Loaded lazily on first emit.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CONFIG_PATH = Path.home() / '.empirica' / 'notify.yaml'


@dataclass
class RoutingRule:
    """A single first-match-wins rule. Empty match dict = always-match
    (use as a final catch-all)."""
    match: dict[str, Any]
    backend: str
    topic: str | None = None


@dataclass
class NotifyConfig:
    default_backend: str = 'stdout'
    backends: dict[str, dict[str, Any]] = field(default_factory=dict)
    routing: list[RoutingRule] = field(default_factory=list)
    defaults: dict[str, Any] = field(default_factory=dict)

    def backend_config(self, name: str) -> dict[str, Any]:
        return self.backends.get(name, {})


def _builtin_defaults() -> NotifyConfig:
    """Empirica works out of the box without notify.yaml — stdout default."""
    return NotifyConfig(
        default_backend='stdout',
        backends={
            'stdout': {},
            'log': {
                'path': str(Path.home() / '.empirica' / 'notify.log'),
                'max_size_mb': 10,
                'keep_files': 5,
            },
        },
        routing=[],
        defaults={'emoji_in_title': True, 'click_url_base': None},
    )


def load_config(path: Path | None = None) -> NotifyConfig:
    """Load notify config from YAML. Returns built-in defaults when missing.

    File errors are non-fatal — fall back to built-in defaults so the
    primitive always works. Yaml schema is forgiving: missing top-level
    keys fill from defaults.
    """
    p = path or CONFIG_PATH
    if not p.exists():
        return _builtin_defaults()

    try:
        import yaml
        with open(p, encoding='utf-8') as f:
            raw = yaml.safe_load(f) or {}
    except Exception:
        return _builtin_defaults()

    base = _builtin_defaults()
    cfg = NotifyConfig(
        default_backend=raw.get('default_backend', base.default_backend),
        backends={**base.backends, **(raw.get('backends') or {})},
        routing=[],
        defaults={**base.defaults, **(raw.get('defaults') or {})},
    )

    raw_routing = raw.get('routing') or []
    if isinstance(raw_routing, list):
        for entry in raw_routing:
            if not isinstance(entry, dict):
                continue
            cfg.routing.append(RoutingRule(
                match=entry.get('match') or {},
                backend=entry.get('backend') or base.default_backend,
                topic=entry.get('topic'),
            ))

    return cfg


def redact_config(cfg: NotifyConfig) -> dict:
    """Return a serializable dict with secrets redacted.

    Auth is always via env var (`auth_env`), never inline YAML. We still
    redact env-var values when printing — leaking the *reference* is OK,
    leaking the *secret* is not.
    """
    out: dict = {
        'default_backend': cfg.default_backend,
        'backends': {},
        'routing': [{'match': r.match, 'backend': r.backend, 'topic': r.topic}
                    for r in cfg.routing],
        'defaults': dict(cfg.defaults),
    }
    for name, bcfg in cfg.backends.items():
        redacted = dict(bcfg)
        # Show that an env var is configured, hide its current value.
        env_name = redacted.get('auth_env')
        if env_name:
            present = bool(os.environ.get(str(env_name)))
            redacted['_auth_env_resolved'] = '<set>' if present else '<unset>'
        # If anyone hard-codes secrets here against the spec, redact them.
        for key in ('auth', 'token', 'password', 'secret', 'api_key'):
            if key in redacted:
                redacted[key] = '<redacted>'
        out['backends'][name] = redacted
    return out
