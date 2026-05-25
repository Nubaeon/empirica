"""Statusline renderers with pluggable backend (ANSI vs Rich markup).

Same numbers, two surfaces:
  - `AnsiBackend` — emits raw `\\033[...m` escape sequences. The CC
    plugin shell statusline uses this so terminal renders work without
    a markup interpreter.
  - `RichBackend` — emits Textual/Rich markup like `[red]…[/red]`.
    Textual widgets (chat StatuslinePanel) use this; Static.update()
    parses the markup and renders proper styling.

Adding a new surface (e.g. HTML, Markdown): subclass `Backend`, fill
in the color tag methods, pass an instance to the formatters.
"""

from __future__ import annotations

from typing import ClassVar

from empirica.core.statusline.calculators import (
    calculate_phase_composite,
    determine_work_phase,
)

# Color palette: reset, bold, green, yellow, red, blue, cyan, gray,
# white, bright_green, bright_cyan. Subclasses map these to their
# concrete output (ANSI codes, Rich tags, HTML spans, …).


class Backend:
    """Abstract color-emission backend.

    Subclasses implement `wrap(text, color)` to produce a styled
    fragment. Backends are stateless — instances are cheap to make.
    """

    def wrap(self, text: str, color: str) -> str:
        raise NotImplementedError


class AnsiBackend(Backend):
    """Emit raw ANSI escape sequences for terminal output."""

    _ANSI: ClassVar[dict[str, str]] = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "red": "\033[31m",
        "blue": "\033[34m",
        "cyan": "\033[36m",
        "gray": "\033[90m",
        "white": "\033[37m",
        "bright_green": "\033[92m",
        "bright_cyan": "\033[96m",
    }

    def wrap(self, text: str, color: str) -> str:
        code = self._ANSI.get(color, "")
        if not code:
            return text
        return f"{code}{text}{self._ANSI['reset']}"


class RichBackend(Backend):
    """Emit Rich/Textual markup like `[red]text[/red]`.

    Rich uses `bright_green` / `bright_cyan` natively; gray maps to
    Rich's `bright_black` for terminal parity.
    """

    _RICH: ClassVar[dict[str, str]] = {
        "green": "green",
        "yellow": "yellow",
        "red": "red",
        "blue": "blue",
        "cyan": "cyan",
        "gray": "bright_black",
        "white": "white",
        "bright_green": "bright_green",
        "bright_cyan": "bright_cyan",
        "bold": "bold",
    }

    def wrap(self, text: str, color: str) -> str:
        tag = self._RICH.get(color)
        if not tag:
            return text
        return f"[{tag}]{text}[/{tag}]"


# ─── Color tier helpers ───────────────────────────────────────────────


def _color_by_value(value: float) -> str:
    """Tier a 0-1 value: bright_green ≥ 0.75, yellow ≥ 0.50, red <."""
    if value >= 0.75:
        return "bright_green"
    if value >= 0.50:
        return "yellow"
    return "red"


# ─── Formatters ───────────────────────────────────────────────────────


def format_progress_bar(completion: float, width: int = 8, *, backend: Backend) -> str:
    """`████░░░░ 45%` — block bar + percentage.

    Color tiers: bright_green ≥ 0.75, green ≥ 0.50, yellow ≥ 0.25, gray <.
    """
    completion = max(0.0, min(1.0, completion))
    filled = int(completion * width)
    empty = width - filled
    bar = "█" * filled + "░" * empty
    pct = int(completion * 100)
    if completion >= 0.75:
        color = "bright_green"
    elif completion >= 0.5:
        color = "green"
    elif completion >= 0.25:
        color = "yellow"
    else:
        color = "gray"
    return f"{backend.wrap(bar, color)} {pct}%"


def format_open_counts(open_counts: dict | None, *, backend: Backend) -> str:
    """`🎯3 ❓6/4` — open goals + total/blocking unknowns.

    Goal color: green if 0, yellow if ≤2, cyan otherwise.
    Unknown color: green if 0 blockers, yellow if ≤5, cyan otherwise.
    Format `❓N/B` when blockers exist and differ from total; `❓N` else.
    Empty/None counts → muted `--`.
    """
    if not open_counts:
        return backend.wrap("--", "gray")
    goals = open_counts.get("open_goals", 0)
    unknowns = open_counts.get("open_unknowns", 0)
    goal_linked = open_counts.get("goal_linked_unknowns", 0)
    if goals == 0:
        goal_color = "green"
    elif goals <= 2:
        goal_color = "yellow"
    else:
        goal_color = "cyan"
    if goal_linked == 0:
        unk_color = "green"
    elif goal_linked <= 5:
        unk_color = "yellow"
    else:
        unk_color = "cyan"
    if goal_linked > 0 and goal_linked != unknowns:
        unk_str = f"❓{unknowns}/{goal_linked}"
    else:
        unk_str = f"❓{unknowns}"
    return f"{backend.wrap(f'🎯{goals}', goal_color)} {backend.wrap(unk_str, unk_color)}"


def format_confidence(confidence: float, *, backend: Backend) -> str:
    """`⚡82%` — tiered emoji + colored percentage.

    ⚡ ≥75% bright_green, 💡 ≥50% green, 💫 ≥35% yellow, 🌑 < red.
    """
    pct = int(confidence * 100)
    if confidence >= 0.75:
        color, emoji = "bright_green", "⚡"
    elif confidence >= 0.50:
        color, emoji = "green", "💡"
    elif confidence >= 0.35:
        color, emoji = "yellow", "💫"
    else:
        color, emoji = "red", "🌑"
    return f"{emoji}{backend.wrap(f'{pct}%', color)}"


def format_phase_state(
    phase: str | None,
    work_phase: str | None = None,
    composite: float | None = None,
    gate_decision: str | None = None,
    *,
    backend: Backend,
) -> str:
    """`PRE 🔍65%` / `CHK 🔍82%→` / `POST 🔨92%` — transaction phase + state.

    `phase` is the empirica transaction phase (PREFLIGHT / CHECK /
    POSTFLIGHT). `work_phase` is the noetic-vs-praxic tag derived
    from phase + gate decision (use determine_work_phase). `composite`
    is calculate_phase_composite(...) for the right phase bucket.

    On CHECK: appends `→` (proceed) or `…` (investigate).

    Praxic emoji is 🔨 (U+1F528, east-asian-width: W). Was ⚙ (U+2699,
    eaw: N/ambiguous) which terminal-rendered narrow on some surfaces
    and wide on others, causing digits to overlap or clip. 🔨 is
    wide-default and matches the plugin script + CLAUDE_CODE_SETUP.md docs.
    """
    abbrev_map = {"PREFLIGHT": "PRE", "CHECK": "CHK", "POSTFLIGHT": "POST"}
    abbrev = abbrev_map.get(phase or "", (phase or "---")[:3])
    emoji = "🔍" if work_phase == "noetic" else "🔨"
    pct = int((composite or 0.0) * 100)
    color = _color_by_value(composite or 0.0)
    head = f"{backend.wrap(abbrev, 'blue')} {emoji}{backend.wrap(f'{pct}%', color)}"
    if phase == "CHECK" and gate_decision:
        if gate_decision == "proceed":
            return head + backend.wrap("→", "green")
        return head + backend.wrap("…", "yellow")
    return head


def format_vector_colored(label: str, value: float, *, backend: Backend) -> str:
    """`K:82%` — labelled colored vector."""
    pct = int(value * 100)
    return backend.wrap(f"{label}:{pct}%", _color_by_value(value))


def format_work_phase_badge(work_phase: str | None, *, backend: Backend) -> str:
    """`🔍 INVESTIGATE` (noetic) or `▶ ACT` (praxic) — Phase 13 badge.

    The conversational-layer surface principle: users see WORK PHASE
    (am I learning vs am I shipping), not transaction lifecycle
    (PREFLIGHT/CHECK/POSTFLIGHT). The latter is substrate.

    Returns empty string when work_phase isn't one of the surfaceable
    values — caller can omit the section cleanly.
    """
    if work_phase == "noetic":
        return f"🔍 {backend.wrap('INVESTIGATE', 'cyan')}"
    if work_phase == "praxic":
        return f"▶ {backend.wrap('ACT', 'bright_green')}"
    return ""


def format_source_badge(source: str | None, *, backend: Backend) -> str:
    """`💡 intuition` or `🔎 search` — Phase 14 per-turn signal source.

    Distinguishes how the agent's response was produced:
      - 'intuition' — from model training data (the default; what every
        chatbot does without retrieval)
      - 'search' — from external retrieval (web fetch, MCP tool call,
        file read, knowledge graph lookup) — i.e., the agent actually
        looked something up rather than confabulating from training

    Surfaces a signal users currently can't see in any LLM chat. The
    badge is per-turn, not per-session.

    Returns empty string for None or unknown values so callers can
    omit the prefix cleanly.
    """
    if source == "intuition":
        return f"💡 {backend.wrap('intuition', 'yellow')}"
    if source == "search":
        return f"🔎 {backend.wrap('search', 'cyan')}"
    return ""


def format_deltas(deltas: dict | None, *, backend: Backend) -> str:
    """Single-symbol summary of net vector deltas.

    `✓` net positive, `⚠` net negative, `△` neutral. For `uncertainty`
    the sign is inverted (lower uncertainty = positive). Empty/None
    deltas → empty string.
    """
    if not deltas:
        return ""
    net = 0.0
    for key, delta in deltas.items():
        if key == "uncertainty":
            net -= delta
        else:
            net += delta
    if net > 0.05:
        return backend.wrap("✓", "green")
    if net < -0.05:
        return backend.wrap("⚠", "red")
    return backend.wrap("△", "white")


# ─── Composite line builders (mode-aware) ─────────────────────────────


def render_default_line(
    *,
    vectors: dict | None,
    phase: str | None = None,
    gate_decision: str | None = None,
    open_counts: dict | None = None,
    deltas: dict | None = None,
    backend: Backend,
) -> str:
    """`default` mode: open counts │ phase + composite │ K/C or S/Δ │ Δ ..`.

    Each section is omitted when its inputs are empty.
    Used by chat StatuslinePanel's default render mode.

    The vector pair adjacent to the composite is **phase-aware** so it's
    drawn from the SAME vector set the composite represents — avoiding
    the "POST 🔨75% │ K:95% C:95%" mis-inference where the eye reads
    K/C as ingredients of the 75%, when in fact POSTFLIGHT's composite
    uses execution vectors (state/change/completion/impact) and K/C are
    noetic foundation vectors.
    """
    parts: list[str] = []
    parts.append(format_open_counts(open_counts, backend=backend))
    if phase:
        wp = determine_work_phase(phase, gate_decision)
        composite_phase = "check" if phase == "CHECK" else wp
        comp = calculate_phase_composite(vectors, composite_phase)
        parts.append(format_phase_state(phase, wp, comp, gate_decision, backend=backend))
    if vectors:
        # Vector pair matches the composite's vector set:
        #   composite_phase == 'check' or 'noetic' → readiness vectors (K/C)
        #   composite_phase == 'praxic' → execution vectors (S/Δ)
        # CHECK always uses 'check' formula regardless of gate_decision,
        # so the K/C pair stays through CHECK→proceed too. POSTFLIGHT
        # composite uses execution vectors, and the pair follows.
        use_execution_pair = (phase is not None) and (composite_phase == "praxic")
        if use_execution_pair:
            state = vectors.get("state", 0.0)
            change = vectors.get("change", 0.0)
            parts.append(
                f"{format_vector_colored('S', state, backend=backend)} "
                f"{format_vector_colored('Δ', change, backend=backend)}"
            )
        else:
            know = vectors.get("know", 0.0)
            ctx = vectors.get("context", 0.0)
            parts.append(
                f"{format_vector_colored('K', know, backend=backend)} "
                f"{format_vector_colored('C', ctx, backend=backend)}"
            )
    if phase == "POSTFLIGHT" and deltas:
        delta_str = format_deltas(deltas, backend=backend)
        if delta_str:
            parts.append(f"Δ {delta_str}")
    return " │ ".join(parts)
