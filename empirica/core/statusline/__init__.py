"""empirica.core.statusline — shared statusline rendering primitives.

Lifts the renderer core out of the Claude Code plugin's
statusline_empirica.py (1455 LOC) into a reusable package, so empirica
chat (Textual TUI) and the CC plugin (terminal ANSI) can share the
same calibration emojis, color tiers, and phase indicators.

The split:
  - `calculators` — pure math, no I/O, no color (confidence,
    phase_composite, work_phase derivation)
  - `renderers` — formatters with a Backend abstraction (ANSI for
    terminal, Rich-markup for Textual)

Phase 6b deliverable. Per the chat plan, the context-window field is
deliberately NOT extracted (Phase 9 owns per-model context tracking).
The CC plugin's session/db/extension scaffolding is also out of scope —
it stays in the plugin where it belongs.
"""

from empirica.core.statusline.calculators import (
    calculate_confidence,
    calculate_phase_composite,
    determine_work_phase,
)
from empirica.core.statusline.renderers import (
    AnsiBackend,
    Backend,
    RichBackend,
    format_confidence,
    format_deltas,
    format_open_counts,
    format_phase_state,
    format_progress_bar,
    format_source_badge,
    format_vector_colored,
    format_work_phase_badge,
)

__all__ = [
    "AnsiBackend",
    "Backend",
    "RichBackend",
    "calculate_confidence",
    "calculate_phase_composite",
    "determine_work_phase",
    "format_confidence",
    "format_deltas",
    "format_open_counts",
    "format_phase_state",
    "format_progress_bar",
    "format_source_badge",
    "format_vector_colored",
    "format_work_phase_badge",
]
