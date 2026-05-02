"""ArtifactCard widget — first-class chat element for epistemic artifacts.

Per CHAT.md spec, this is THE differentiator. When an agent (or user)
logs a finding/decision/unknown/etc., the conversation renders a
styled card with type-specific quick-action buttons inline — not a
buried tool-call expand.

Pattern lifted from empirica_workspace.dashboard.CandenceChatScreen
(prediction triage with Authorize/Queue/Deny actions). Generalized
here from one card type to all 8 Empirica artifact types + goals +
transactions.

Phase 4 ships: finding, decision, unknown rendering. Buttons emit
Textual messages bubble-up to the App for routing. Phase 5+ wires
the buttons to real action invocations (confirm-as-finding,
resolve-unknown, discuss-via-EPE, pin).
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Button, Static

from empirica.core.chat.session import Turn

# Type-specific badge prefixes — short visual signal per artifact kind
_BADGE = {
    "finding": "🔎 Finding",
    "decision": "⚖ Decision",
    "unknown": "❓ Unknown",
    "mistake": "⚠ Mistake",
    "dead_end": "🚫 Dead-End",
    "assumption": "🌫 Assumption",
    "goal": "🎯 Goal",
    "transaction": "📊 Transaction",
    "source": "🔗 Source",
}


class ArtifactCard(Vertical):
    """Inline card rendering an epistemic artifact with type-specific actions.

    Reads the artifact metadata from the Turn's `metadata` dict:
      {
        "artifact_type": "finding|decision|unknown|...",
        "artifact_id": "uuid-or-None",
        "impact": 0.85,        # finding/unknown
        "rationale": "...",    # decision
        "subject": "...",      # finding/unknown
        "reversibility": "...",# decision
      }
    """

    DEFAULT_CSS = """
    ArtifactCard {
        margin: 0 1 1 1;
        padding: 0 1;
        height: auto;
        border: round $secondary;
        background: $boost;
    }
    ArtifactCard #card-header {
        height: 1;
        color: $secondary;
        text-style: bold;
    }
    ArtifactCard #card-body {
        height: auto;
        padding: 0 0 1 0;
    }
    ArtifactCard #card-meta {
        height: 1;
        color: $text-muted;
    }
    ArtifactCard #card-actions {
        height: 3;
        align-horizontal: left;
    }
    ArtifactCard Button {
        margin: 0 1 0 0;
        min-width: 10;
        height: 1;
    }
    """

    class ActionInvoked(Message):
        """Bubble up when an action button is clicked."""

        def __init__(
            self,
            artifact_id: str | None,
            artifact_type: str,
            action: str,
            turn_id: str,
        ) -> None:
            self.artifact_id = artifact_id
            self.artifact_type = artifact_type
            self.action = action
            self.turn_id = turn_id
            super().__init__()

    def __init__(self, turn: Turn) -> None:
        self.turn = turn
        meta = turn.metadata or {}
        self.artifact_type = meta.get("artifact_type", "unknown")
        self.artifact_id = meta.get("artifact_id")
        super().__init__(id=f"turn-{turn.turn_id[:8]}")

    def compose(self) -> ComposeResult:
        meta = self.turn.metadata or {}

        # Header: badge + impact/confidence/reversibility hint
        badge = _BADGE.get(self.artifact_type, f"• {self.artifact_type}")
        header_extras = _format_header_extras(self.artifact_type, meta)
        yield Static(f"{badge}{header_extras}", id="card-header")

        # Body: the artifact's primary text
        yield Static(self.turn.text, id="card-body")

        # Meta footer: subject / id / source if present
        meta_line = _format_meta_line(self.artifact_type, meta, self.artifact_id)
        if meta_line:
            yield Static(meta_line, id="card-meta")

        # Per-type action row
        action_row = Horizontal(id="card-actions")
        with action_row:
            for action in _actions_for(self.artifact_type):
                # Button id encodes artifact + action for easy routing
                yield Button(
                    action["label"],
                    id=f"act-{self.artifact_type}-{action['key']}-{self.turn.turn_id[:8]}",
                    variant=action.get("variant", "default"),  # type: ignore[arg-type]
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # Button id pattern: act-{type}-{action_key}-{turn_short_id}
        bid = event.button.id or ""
        if not bid.startswith("act-"):
            return
        parts = bid.split("-", 3)  # ["act", type, action_key, ...]
        if len(parts) < 3:
            return
        action_key = parts[2]
        self.post_message(
            self.ActionInvoked(
                artifact_id=self.artifact_id,
                artifact_type=self.artifact_type,
                action=action_key,
                turn_id=self.turn.turn_id,
            )
        )


def _format_header_extras(artifact_type: str, meta: dict) -> str:
    """Inline strength/significance signal next to the badge."""
    if artifact_type == "finding" and "impact" in meta:
        return f"  ·  impact {meta['impact']:.2f}"
    if artifact_type == "decision" and "reversibility" in meta:
        return f"  ·  {meta['reversibility']}"
    if artifact_type == "unknown" and "impact" in meta:
        return f"  ·  impact {meta['impact']:.2f}"
    return ""


def _format_meta_line(artifact_type: str, meta: dict, artifact_id: str | None) -> str:
    """Footer line: subject + id + extras per type."""
    parts: list[str] = []
    subject = meta.get("subject")
    if subject:
        parts.append(f"subject: {subject}")
    if artifact_type == "decision" and meta.get("rationale"):
        # Truncate long rationales — they're rendered separately if needed
        rat = meta["rationale"]
        if len(rat) > 60:
            rat = rat[:57] + "…"
        parts.append(f"why: {rat}")
    if artifact_id:
        parts.append(f"id: {artifact_id[:8]}")
    return "  ·  ".join(parts) if parts else ""


def _actions_for(artifact_type: str) -> list[dict[str, str]]:
    """Per-type quick actions per CHAT.md spec."""
    if artifact_type == "finding":
        return [
            {"key": "confirm", "label": "👍 confirm", "variant": "success"},
            {"key": "challenge", "label": "👎 challenge", "variant": "warning"},
            {"key": "discuss", "label": "💬 discuss"},
            {"key": "pin", "label": "📌 pin"},
        ]
    if artifact_type == "decision":
        return [
            {"key": "ack", "label": "✓ acknowledge", "variant": "success"},
            {"key": "reverse", "label": "↶ reverse", "variant": "warning"},
            {"key": "discuss", "label": "💬 discuss"},
        ]
    if artifact_type == "unknown":
        return [
            {"key": "resolve", "label": "✓ resolve", "variant": "success"},
            {"key": "escalate", "label": "🚨 escalate", "variant": "warning"},
            {"key": "discuss", "label": "💬 discuss"},
        ]
    if artifact_type == "mistake":
        return [
            {"key": "ack", "label": "✓ acknowledge"},
            {"key": "discuss", "label": "💬 discuss"},
        ]
    # Default minimal action set for types not yet specialized
    return [{"key": "discuss", "label": "💬 discuss"}]
