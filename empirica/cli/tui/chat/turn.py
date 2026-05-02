"""Per-kind turn widgets — one Static subclass per Turn kind.

Phase 1 covers user / agent_text / system. Future phases add
agent_reasoning (collapsed thinking block), tool_call (collapsed strip),
epistemic_action (rich artifact card).

Phase 14: AgentTurn header includes a per-turn source badge
(💡 intuition / 🔎 search) when turn.metadata['source'] is set.
"""

from __future__ import annotations

from textual.widgets import Static

from empirica.core.chat.session import Turn, TurnKind
from empirica.core.statusline import RichBackend, format_source_badge

_BADGE_BACKEND = RichBackend()


def render_turn(turn: Turn):
    """Factory: pick the right widget class for a turn kind."""
    if turn.kind == TurnKind.USER:
        return UserTurn(turn)
    if turn.kind == TurnKind.AGENT_TEXT:
        return AgentTurn(turn)
    if turn.kind == TurnKind.SYSTEM:
        return SystemTurn(turn)
    if turn.kind == TurnKind.EPISTEMIC_ACTION:
        # Lazy import to avoid Textual-circular issues at module load
        from .artifact_card import ArtifactCard
        return ArtifactCard(turn)
    # Phase 2+ kinds (tool_call, agent_reasoning, tool_result) — render
    # as plain labeled text until their dedicated widgets land.
    return UnknownTurn(turn)


class _BaseTurn(Static):
    """Common base — every turn carries its turn_id for later message routing."""

    DEFAULT_CSS = """
    _BaseTurn {
        margin: 0 1 1 1;
        padding: 0 1;
        height: auto;
    }
    """

    def __init__(self, turn: Turn) -> None:
        self.turn = turn
        super().__init__(self._format_body(), id=f"turn-{turn.turn_id[:8]}")

    def _format_body(self) -> str:
        return self.turn.text


class UserTurn(_BaseTurn):
    """User input — right-aligned style."""

    DEFAULT_CSS = """
    UserTurn {
        background: $primary 20%;
        border-left: thick $primary;
    }
    """

    def _format_body(self) -> str:
        return f"[b]you:[/b] {self.turn.text}"


class AgentTurn(_BaseTurn):
    """Agent text response — left-aligned style.

    Header includes Phase 14 per-turn source badge when set:
      💡 intuition (yellow) — model training data
      🔎 search (cyan)      — external retrieval (tool calls, file reads, etc.)
    """

    DEFAULT_CSS = """
    AgentTurn {
        background: $surface;
        border-left: thick $accent;
    }
    """

    def _format_body(self) -> str:
        source = self.turn.metadata.get("source") if self.turn.metadata else None
        badge = format_source_badge(source, backend=_BADGE_BACKEND)
        prefix = f"[b]agent:[/b] {badge} " if badge else "[b]agent:[/b] "
        return f"{prefix}{self.turn.text}"


class SystemTurn(_BaseTurn):
    """System message — italic muted (compaction markers, mode transitions)."""

    DEFAULT_CSS = """
    SystemTurn {
        color: $text-muted;
        text-style: italic;
    }
    """

    def _format_body(self) -> str:
        return f"— {self.turn.text} —"


class UnknownTurn(_BaseTurn):
    """Fallback for Phase 2+ kinds while we incrementally build them."""

    DEFAULT_CSS = """
    UnknownTurn {
        background: $warning 20%;
        border-left: thick $warning;
    }
    """

    def _format_body(self) -> str:
        return f"[dim]({self.turn.kind.value})[/dim] {self.turn.text}"
