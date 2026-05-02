"""empirica chat — Textual TUI app entry (Phase 1).

Standalone-usable skeleton. Phase 1 capabilities:
  - Header with mode badge + model + clock (placeholders for Phase 6)
  - Conversation scroll with rendered turns (user / agent_text / system)
  - Multi-line input (Enter submits, Shift+Enter newline)
  - Footer with key bindings
  - --feed sample.jsonl loads pre-baked conversation (no app-server dep)
  - --session-id RESUME loads an existing session from disk
  - All turns auto-persist to ~/.empirica/chat_sessions/{session_id}.jsonl

Phase 2 wires app-server WebSocket. Phase 3 wires translator event tap.
Phase 4 adds artifact cards. See CHAT.md for the full roadmap.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Footer, Header

from empirica.core.chat.actions import (
    ActionError,
    extract_artifact_id,
    log_decision,
    log_finding,
    log_unknown,
)
from empirica.core.chat.session import ChatSession, Turn, TurnKind, load_turns
from empirica.core.chat.translator_client import (
    TranslatorError,
    build_request_body,
    stream_responses,
)

from .chat.artifact_card import ArtifactCard
from .chat.conversation import ConversationScroll
from .chat.input import ChatInput

REFRESH_SECONDS = 2.0


class ChatApp(App):
    """empirica chat — single-instance collaborative epistemic workspace."""

    CSS = """
    Screen { layout: vertical; }
    #chat-conversation { height: 1fr; }
    #chat-input { dock: bottom; }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+l", "clear_input", "Clear input"),
    ]

    TITLE = "empirica chat"
    SUB_TITLE = "🤖 conversational"  # Phase 6: dynamic from autonomy mode

    def __init__(
        self,
        feed_path: Path | None = None,
        session_id: str | None = None,
        feed_delay: float = 0.0,
        translator_url: str | None = None,
        model: str = "deepseek-chat",
        instructions: str | None = None,
    ) -> None:
        super().__init__()
        self.feed_path = feed_path
        self.session_id_to_resume = session_id
        self.feed_delay = feed_delay
        self.translator_url = translator_url
        self.model = model
        self.instructions = instructions
        self._session: ChatSession | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            yield ConversationScroll(id="chat-conversation")
            yield ChatInput(id="chat-input")
        yield Footer()

    def on_mount(self) -> None:
        # Establish the chat session — resume if requested, else create new.
        if self.session_id_to_resume:
            self._session = ChatSession.load(self.session_id_to_resume)
            self._convo().render_existing(self._session.turns)
        else:
            self._session = ChatSession.create()

        # Optional: replay a sample feed (no app-server dep — useful for
        # reviewing the rendering UX before wiring upstream).
        if self.feed_path:
            self.run_worker(self._replay_feed(), thread=False)

        # Focus the input so the user can start typing immediately.
        self.query_one(ChatInput).focus()

    def _convo(self) -> ConversationScroll:
        return self.query_one("#chat-conversation", ConversationScroll)

    async def _replay_feed(self) -> None:
        """Stream turns from a feed file into the conversation."""
        assert self.feed_path is not None  # noqa: S101 — type narrowing
        assert self._session is not None  # noqa: S101 — type narrowing
        for turn in load_turns(self.feed_path):
            self._session.append(turn)
            self._convo().append_turn(turn)
            if self.feed_delay > 0:
                await asyncio.sleep(self.feed_delay)

    def on_chat_input_submitted(self, event: ChatInput.Submitted) -> None:
        """User pressed Enter on a non-empty input."""
        assert self._session is not None  # noqa: S101 — type narrowing
        text = event.text

        # Phase 4: slash commands route to artifact creation rather than
        # the LLM. /finding, /decision, /unknown, /help — see _handle_slash.
        if text.startswith("/"):
            self._handle_slash(text)
            return

        turn = Turn.new(TurnKind.USER, text)
        self._session.append(turn)
        self._convo().append_turn(turn)

        if not self.translator_url:
            # Phase 1 fallback — no upstream wired
            echo = Turn.new(
                TurnKind.SYSTEM,
                "(no --translator-url set — pass one to enable agent flow)",
            )
            self._session.append(echo)
            self._convo().append_turn(echo)
            return

        # Phase 2a: dispatch to translator, stream agent response as a
        # single growing AgentTurn. Run in a thread worker so the UI
        # stays responsive during the streaming HTTP call.
        user_text = event.text
        self.run_worker(
            lambda: self._stream_agent_response(user_text),
            thread=True,
            exclusive=True,
            group="agent-stream",
        )

    def _stream_agent_response(self, user_text: str) -> None:
        """Worker thread: hit translator, stream deltas into a new agent turn."""
        assert self._session is not None  # noqa: S101 — type narrowing
        assert self.translator_url is not None  # noqa: S101 — gated by caller

        # Build request from prior history (excluding the just-appended user
        # turn — translator will see it explicitly via `user_text`).
        history = [
            {"role": _to_translator_role(t.kind), "text": t.text}
            for t in self._session.turns[:-1]  # exclude the new user turn
            if t.kind in (TurnKind.USER, TurnKind.AGENT_TEXT)
        ]
        body = build_request_body(
            user_text=user_text,
            model=self.model,
            instructions=self.instructions,
            history=history,
        )

        # Allocate a single AgentTurn we mutate as deltas arrive.
        agent_turn = Turn.new(TurnKind.AGENT_TEXT, "")
        # Schedule mount on the main thread.
        self.call_from_thread(self._convo().append_turn, agent_turn)

        accumulated: list[str] = []
        try:
            for event in stream_responses(self.translator_url, body):
                t = event.get("type", "")
                if t == "response.output_text.delta":
                    delta = event.get("delta", "")
                    if delta:
                        accumulated.append(delta)
                        self.call_from_thread(
                            self._update_agent_turn,
                            agent_turn.turn_id,
                            "".join(accumulated),
                        )
                elif t == "response.completed":
                    # Final assembled text is in response.output[0].content[0].text;
                    # we already accumulated identical text from deltas. Persist.
                    final_text = "".join(accumulated)
                    agent_turn.text = final_text
                    self._session.append(agent_turn)
        except TranslatorError as e:
            err = Turn.new(TurnKind.SYSTEM, f"translator error: {e}")
            self._session.append(err)
            self.call_from_thread(self._convo().append_turn, err)
        except Exception as e:  # noqa: BLE001 — surface any failure to chat
            err = Turn.new(TurnKind.SYSTEM, f"agent stream error: {type(e).__name__}: {e}")
            self._session.append(err)
            self.call_from_thread(self._convo().append_turn, err)

    def _update_agent_turn(self, turn_id: str, text: str) -> None:
        """Main-thread: update an existing agent turn widget's body in place."""
        try:
            widget = self.query_one(f"#turn-{turn_id[:8]}")
        except Exception:  # noqa: BLE001 — widget may have been removed
            return
        # Re-render via Static.update with the agent-style label
        widget.update(f"[b]agent:[/b] {text}")  # type: ignore[attr-defined]

    # ─── Phase 4: slash commands → artifact cards ─────────────────────

    def _handle_slash(self, text: str) -> None:
        """Parse and execute /finding, /decision, /unknown, /help."""
        assert self._session is not None  # noqa: S101 — type narrowing
        cmd, _, rest = text[1:].partition(" ")
        cmd = cmd.strip().lower()
        rest = rest.strip()

        if cmd in ("help", "?"):
            self._emit_system(
                "slash commands:\n"
                "  /finding TEXT       create a finding (renders as inline card)\n"
                "  /decision TEXT      create a decision\n"
                "  /unknown TEXT       create an unknown question\n"
                "  /help               this list\n"
                "Anything else goes to the agent (when --translator-url is set)."
            )
            return

        if not rest:
            self._emit_system(f"/{cmd}: missing text — usage: /{cmd} <description>")
            return

        if cmd == "finding":
            self.run_worker(
                lambda: self._create_artifact("finding", rest),
                thread=True, exclusive=False, group="artifact-create",
            )
            return
        if cmd == "decision":
            self.run_worker(
                lambda: self._create_artifact("decision", rest),
                thread=True, exclusive=False, group="artifact-create",
            )
            return
        if cmd == "unknown":
            self.run_worker(
                lambda: self._create_artifact("unknown", rest),
                thread=True, exclusive=False, group="artifact-create",
            )
            return

        self._emit_system(f"unknown slash command: /{cmd} — try /help")

    def _create_artifact(self, artifact_type: str, text: str) -> None:
        """Worker thread: invoke empirica CLI, render the artifact card."""
        assert self._session is not None  # noqa: S101 — type narrowing
        try:
            if artifact_type == "finding":
                resp = log_finding(text)
            elif artifact_type == "decision":
                resp = log_decision(text)
            elif artifact_type == "unknown":
                resp = log_unknown(text)
            else:
                self.call_from_thread(
                    self._emit_system, f"artifact type not yet supported: {artifact_type}"
                )
                return
        except ActionError as e:
            self.call_from_thread(self._emit_system, f"artifact creation failed: {e}")
            return

        artifact_id = extract_artifact_id(resp)
        meta: dict[str, object] = {
            "artifact_type": artifact_type,
            "artifact_id": artifact_id,
        }
        if artifact_type in ("finding", "unknown"):
            meta["impact"] = 0.5  # default; finer impact via slash flags is Phase 4b
        if artifact_type == "decision":
            meta["reversibility"] = "exploratory"

        turn = Turn.new(TurnKind.EPISTEMIC_ACTION, text, metadata=meta)
        self._session.append(turn)
        self.call_from_thread(self._convo().append_turn, turn)

    def _emit_system(self, text: str) -> None:
        """Append a SystemTurn from any thread (uses call_from_thread if needed)."""
        assert self._session is not None  # noqa: S101 — type narrowing
        turn = Turn.new(TurnKind.SYSTEM, text)
        self._session.append(turn)
        # If we're already on the main thread, append directly; otherwise
        # call_from_thread. Textual's threading model makes both safe enough.
        try:
            self._convo().append_turn(turn)
        except Exception:  # noqa: BLE001 — thread context unclear
            self.call_from_thread(self._convo().append_turn, turn)

    def on_artifact_card_action_invoked(self, event: ArtifactCard.ActionInvoked) -> None:
        """Bubble from per-card buttons. Phase 4 v1: emit a system note as ack.

        Phase 5+ wires this to real action invocations:
          - finding.confirm → empirica finding-log (with link to original)
          - unknown.resolve → empirica unknown-resolve
          - *.discuss → inject into next agent turn as system message
          - *.pin → write to chat_pinned_{session_id}.json
        """
        msg = (
            f"action: {event.artifact_type}.{event.action} "
            f"on artifact {(event.artifact_id or 'unknown')[:8]} "
            f"(turn {event.turn_id[:8]}) — wiring is Phase 5+"
        )
        self._emit_system(msg)

    def action_clear_input(self) -> None:
        try:
            self.query_one(ChatInput).load_text("")
        except Exception:  # noqa: S110 — clear is best-effort UI op
            pass


def _to_translator_role(kind: TurnKind) -> str:
    """Map a CIF turn kind to the role string the translator expects."""
    if kind == TurnKind.USER:
        return "user"
    if kind == TurnKind.AGENT_TEXT:
        return "assistant"
    return "user"  # safe fallback


def run_chat(
    feed_path: Path | None = None,
    session_id: str | None = None,
    feed_delay: float = 0.0,
    translator_url: str | None = None,
    model: str = "deepseek-chat",
    instructions: str | None = None,
) -> int:
    app = ChatApp(
        feed_path=feed_path,
        session_id=session_id,
        feed_delay=feed_delay,
        translator_url=translator_url,
        model=model,
        instructions=instructions,
    )
    app.run()
    return 0
