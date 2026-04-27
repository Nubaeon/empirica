"""NotifyEvent dataclass + parsers for actions/tags fields.

The event is the contract between callers (loops, hooks, scripts) and
backends (stdout, log, ntfy). Backends consume an Event and return an
EmitResult; the dispatcher orchestrates resolution + invocation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Severity = Literal['info', 'warning', 'critical']
VALID_SEVERITY: tuple[str, ...] = ('info', 'warning', 'critical')


@dataclass
class NotifyEvent:
    """The unit a caller emits. Backends receive this and decide how to
    render it for their channel."""
    severity: Severity
    title: str
    message: str
    rationale: str | None = None
    tags: list[str] = field(default_factory=list)
    click_url: str | None = None
    actions: list[tuple[str, str]] = field(default_factory=list)  # [(label, url), ...]
    source: str | None = None     # 'loop:<name>' | 'hook:<event>' | 'manual' | 'script:<n>'
    topic: str | None = None      # resolved by dispatcher; backends use as-is

    def to_dict(self) -> dict:
        return {
            'severity': self.severity,
            'title': self.title,
            'message': self.message,
            'rationale': self.rationale,
            'tags': list(self.tags),
            'click_url': self.click_url,
            'actions': [{'label': l, 'url': u} for l, u in self.actions],
            'source': self.source,
            'topic': self.topic,
        }


@dataclass
class EmitResult:
    """Backend returns this. Dispatcher aggregates."""
    backend: str
    ok: bool
    detail: str
    response_code: int | None = None  # HTTP code for ntfy etc.


def parse_tags(raw: str | None) -> list[str]:
    """'a,b,c' → ['a', 'b', 'c']. Empty/None → []."""
    if not raw:
        return []
    return [t.strip() for t in raw.split(',') if t.strip()]


def parse_actions(raw: str | None) -> list[tuple[str, str]]:
    """Mirrors ntfy's Label|URL format exactly.

    'Accept|http://a,Reclassify|http://b' → [('Accept','http://a'), ('Reclassify','http://b')]

    No DSL invented; if ntfy adds new action types we forward without
    renegotiating the contract. Validation is minimal: pair has exactly
    one '|' and the URL part is non-empty.
    """
    if not raw:
        return []
    out: list[tuple[str, str]] = []
    for entry in raw.split(','):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split('|', 1)
        if len(parts) != 2:
            continue
        label, url = parts[0].strip(), parts[1].strip()
        if not label or not url:
            continue
        out.append((label, url))
    return out
