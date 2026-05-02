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

from empirica.core.chat.session import ChatSession, Turn, TurnKind, load_turns
from empirica.core.chat.translator_client import (
    TranslatorError,
    build_request_body,
    stream_responses,
)

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
        turn = Turn.new(TurnKind.USER, event.text)
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
        widget.update(f"[b]agent:[/b] {text}")

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
