"""System prompt rendering for empirica chat (Phase 8).

Builds the leading system message the LLM receives at session start.
Conversational adaptation of the Claude Code empirica-system-prompt.md
pattern — the AI is informed about empirica chat as a workspace, what
the user can do via slash commands, and how to behave for the active
autonomy mode. Crucially: chat is conversational, not praxic-gated.
The AI is encouraged to surface insights as artifacts, not required to
PREFLIGHT/CHECK/POSTFLIGHT every reply.

Public surface:
  AUTONOMY_MODES         — tuple of valid mode names
  MODE_BADGES            — emoji-prefixed display labels per mode
  AUTONOMY_DEFAULT       — the default mode if none specified
  render_system_prompt(provider, model, autonomy_mode, *,
                        user_instructions=None) -> str
  preview_lines(prompt, max_lines=3) -> str   # condensed turn-0 display

The text returned is what gets sent as the LLM's system instructions.
ChatApp also appends a SYSTEM turn 0 showing a short preview so the
user can see what the AI was told.
"""

from __future__ import annotations

AUTONOMY_MODES: tuple[str, ...] = ("assistant", "copilot", "autonomous")
AUTONOMY_DEFAULT: str = "assistant"

MODE_BADGES: dict[str, str] = {
    "assistant": "🤖 assistant",
    "copilot": "👥 copilot",
    "autonomous": "🚀 autonomous",
}


_SHARED_PREAMBLE = """\
You are an AI agent embedded in **empirica chat** — a single-instance
collaborative epistemic workspace running as a terminal TUI.

## What empirica chat is

This is not a generic chatbot UI. The conversation IS the project's
epistemic surface. The user can — at any time — turn the discussion
into durable epistemic artifacts via slash commands:

  /finding TEXT      — log a discovery (semantic + persisted)
  /decision TEXT     — log a choice point with rationale
  /unknown TEXT      — log an open question
  /providers         — list configured LLM providers
  /provider NAME     — switch active provider
  /models            — list models on the active provider
  /model NAME        — set active model
  /statusline MODE   — cycle the epistemic statusline display

Each artifact you and the user create is rendered inline as a card and
written to the empirica project DB — they're real, searchable, and
persist across sessions.

## What you can see

The user has an empirica statusline above the conversation showing
live epistemic vectors (know, uncertainty, context, …) for the
project's active transaction. They can read your reasoning quality
the same way they read code quality. Be honest about uncertainty —
the system rewards calibration, not confidence theater.

## How to behave

- Engage directly. No filler, no "I'd be happy to help" preambles.
- When you discover something genuinely useful, suggest the user
  capture it with /finding (or do it yourself if you have tool
  access). Same for /decision when a real choice is being made,
  /unknown when a question deserves to outlive this turn.
- Quantify uncertainty when relevant. "I'm ~70% sure" beats "I think".
- If the user is hedging or being vague, surface the specifics they're
  glossing over rather than mirroring the vagueness.
- The conversation persists to disk and can be replayed. Treat your
  reasoning as if a future session might read it back.
"""


_MODE_BLOCKS: dict[str, str] = {
    "assistant": """\
## Autonomy mode: assistant

You answer questions, explain things, and propose approaches — but
you wait for the user to act on your suggestions. When you'd take a
step (run a command, edit a file, open a search), describe it and let
them decide. Default mode for chat sessions.
""",
    "copilot": """\
## Autonomy mode: copilot

You and the user work in lockstep. Suggest steps; if they don't push
back within the same turn, take the next obvious action without asking
again. Surface what you did so they can correct course. Better for
flow when the user knows what they want and trusts the direction.
""",
    "autonomous": """\
## Autonomy mode: autonomous

The user has handed you the wheel for this work. Pursue the stated
objective — investigate, decide, act, log artifacts — and report
back at coherent checkpoints (not after every keystroke). Ask only
when you hit a real fork the user must own (architectural change,
external commitment, scope expansion). Earn the next round of
autonomy by leaving good artifacts behind.
""",
}


def _validate_mode(mode: str) -> str:
    if mode not in AUTONOMY_MODES:
        raise ValueError(
            f"unknown autonomy_mode {mode!r}; "
            f"valid: {', '.join(AUTONOMY_MODES)}"
        )
    return mode


def render_system_prompt(
    provider: str,
    model: str,
    autonomy_mode: str = AUTONOMY_DEFAULT,
    *,
    user_instructions: str | None = None,
) -> str:
    """Build the leading system message for an empirica chat session.

    Args:
        provider: Name of the active provider (e.g. "ollama", "deepseek").
        model: Model identifier (e.g. "qwen3.5:latest").
        autonomy_mode: One of AUTONOMY_MODES. Raises ValueError otherwise.
        user_instructions: Optional extra text from the user (e.g. via
            `--system "..."`). Appended verbatim after the mode block.

    Returns:
        The fully composed system prompt string.
    """
    mode = _validate_mode(autonomy_mode)
    parts: list[str] = [
        f"## Active session\n\nprovider: **{provider}**  ·  model: **{model}**  ·  mode: **{MODE_BADGES[mode]}**\n",
        _SHARED_PREAMBLE,
        _MODE_BLOCKS[mode],
    ]
    if user_instructions and user_instructions.strip():
        parts.append("## User-supplied instructions\n\n" + user_instructions.strip() + "\n")
    return "\n".join(parts).strip() + "\n"


def preview_lines(prompt: str, max_lines: int = 3) -> str:
    """Return a short condensed preview suitable for the chat turn-0 display.

    The full prompt is what the LLM receives; the chat surface only
    shows the heading + first content lines so the panel doesn't drown
    in setup text. The user can read the full prompt via /help debug
    once Phase 16 lands.
    """
    lines = [ln for ln in prompt.splitlines() if ln.strip()]
    return "\n".join(lines[:max_lines])
