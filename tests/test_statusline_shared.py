"""Tests for empirica.core.statusline — Phase 6b shared module."""

from __future__ import annotations

import pytest

from empirica.core.statusline import (
    AnsiBackend,
    RichBackend,
    calculate_confidence,
    calculate_phase_composite,
    determine_work_phase,
    format_confidence,
    format_deltas,
    format_open_counts,
    format_phase_state,
    format_progress_bar,
    format_source_badge,
    format_vector_colored,
    format_work_phase_badge,
)
from empirica.core.statusline.renderers import render_default_line

# ─── Calculators ────────────────────────────────────────────────────


class TestCalculateConfidence:
    def test_empty_vectors_returns_zero(self):
        assert calculate_confidence({}) == 0.0
        assert calculate_confidence(None) == 0.0

    def test_high_confidence_inputs_yield_high_score(self):
        v = {"know": 1.0, "uncertainty": 0.0, "context": 1.0, "completion": 1.0}
        assert calculate_confidence(v) == pytest.approx(1.0)

    def test_low_confidence_inputs_yield_low_score(self):
        v = {"know": 0.0, "uncertainty": 1.0, "context": 0.0, "completion": 0.0}
        assert calculate_confidence(v) == pytest.approx(0.0)

    def test_default_uncertainty_05_subtracts_correctly(self):
        v = {"know": 0.5, "uncertainty": 0.5, "context": 0.5, "completion": 0.5}
        # 0.4*0.5 + 0.3*0.5 + 0.2*0.5 + 0.1*0.5 = 0.5
        assert calculate_confidence(v) == pytest.approx(0.5)

    def test_clamps_to_unit_interval(self):
        v = {"know": 2.0, "uncertainty": -1.0, "context": 2.0, "completion": 2.0}
        assert 0.0 <= calculate_confidence(v) <= 1.0


class TestCalculatePhaseComposite:
    def test_check_uses_check_keys(self):
        v = {"know": 0.8, "context": 0.8, "clarity": 0.8,
             "coherence": 0.8, "signal": 0.8, "density": 0.8}
        assert calculate_phase_composite(v, "check") == pytest.approx(0.8)

    def test_noetic_uses_noetic_keys(self):
        v = {"clarity": 0.5, "coherence": 0.5, "signal": 0.5, "density": 0.5}
        assert calculate_phase_composite(v, "noetic") == pytest.approx(0.5)

    def test_praxic_default_uses_execution_keys(self):
        v = {"state": 0.7, "change": 0.7, "completion": 0.7, "impact": 0.7}
        assert calculate_phase_composite(v, "praxic") == pytest.approx(0.7)

    def test_empty_vectors_returns_zero(self):
        assert calculate_phase_composite({}, "noetic") == 0.0
        assert calculate_phase_composite(None, "praxic") == 0.0

    def test_skips_missing_keys(self):
        # Only one key present — average is just that value
        v = {"clarity": 0.6}
        assert calculate_phase_composite(v, "noetic") == pytest.approx(0.6)


class TestDetermineWorkPhase:
    @pytest.mark.parametrize("phase,gate,expected", [
        (None, None, "noetic"),
        ("PREFLIGHT", None, "noetic"),
        ("CHECK", "proceed", "praxic"),
        ("CHECK", "investigate", "noetic"),
        ("CHECK", None, "noetic"),
        ("POSTFLIGHT", None, "praxic"),
        ("UNKNOWN", None, "noetic"),
    ])
    def test_table(self, phase, gate, expected):
        assert determine_work_phase(phase, gate) == expected


# ─── Backends ───────────────────────────────────────────────────────


class TestAnsiBackend:
    def test_wraps_with_ansi_codes(self):
        b = AnsiBackend()
        result = b.wrap("hi", "red")
        assert "\033[31m" in result
        assert "\033[0m" in result
        assert "hi" in result

    def test_unknown_color_returns_text_unchanged(self):
        assert AnsiBackend().wrap("hi", "purple") == "hi"


class TestRichBackend:
    def test_wraps_with_markup(self):
        assert RichBackend().wrap("hi", "red") == "[red]hi[/red]"

    def test_gray_maps_to_bright_black(self):
        assert RichBackend().wrap("dim", "gray") == "[bright_black]dim[/bright_black]"

    def test_unknown_color_returns_text_unchanged(self):
        assert RichBackend().wrap("hi", "purple") == "hi"


# ─── Formatters (parametrized over both backends) ───────────────────


@pytest.fixture(params=[AnsiBackend(), RichBackend()], ids=["ansi", "rich"])
def backend(request):
    return request.param


class TestFormatProgressBar:
    def test_zero_returns_empty_bar(self, backend):
        s = format_progress_bar(0.0, width=8, backend=backend)
        assert "0%" in s
        assert "░" in s and "█" not in s

    def test_full_returns_full_bar(self, backend):
        s = format_progress_bar(1.0, width=8, backend=backend)
        assert "100%" in s
        assert "█" in s and "░" not in s

    def test_clamps_above_one(self, backend):
        s = format_progress_bar(1.5, width=4, backend=backend)
        assert "100%" in s

    def test_clamps_below_zero(self, backend):
        s = format_progress_bar(-0.2, width=4, backend=backend)
        assert "0%" in s


class TestFormatOpenCounts:
    def test_empty_returns_dash(self, backend):
        s = format_open_counts(None, backend=backend)
        assert "--" in s
        s = format_open_counts({}, backend=backend)
        assert "--" in s

    def test_zero_goals_zero_unknowns(self, backend):
        s = format_open_counts(
            {"open_goals": 0, "open_unknowns": 0, "goal_linked_unknowns": 0},
            backend=backend,
        )
        assert "🎯0" in s
        assert "❓0" in s

    def test_blockers_appear_with_slash(self, backend):
        s = format_open_counts(
            {"open_goals": 3, "open_unknowns": 6, "goal_linked_unknowns": 4},
            backend=backend,
        )
        assert "🎯3" in s
        assert "❓6/4" in s

    def test_no_blockers_omits_slash(self, backend):
        s = format_open_counts(
            {"open_goals": 1, "open_unknowns": 2, "goal_linked_unknowns": 0},
            backend=backend,
        )
        assert "❓2" in s
        assert "❓2/" not in s


class TestFormatConfidence:
    @pytest.mark.parametrize("conf,emoji", [
        (0.85, "⚡"),
        (0.55, "💡"),
        (0.40, "💫"),
        (0.10, "🌑"),
    ])
    def test_tier_emoji(self, conf, emoji, backend):
        s = format_confidence(conf, backend=backend)
        assert emoji in s
        assert f"{int(conf * 100)}%" in s


class TestFormatPhaseState:
    def test_preflight_noetic_shows_pre_and_lens(self, backend):
        s = format_phase_state("PREFLIGHT", "noetic", 0.6, backend=backend)
        assert "PRE" in s
        assert "🔍" in s
        assert "60%" in s

    def test_check_proceed_appends_arrow(self, backend):
        s = format_phase_state("CHECK", "praxic", 0.8, "proceed", backend=backend)
        assert "CHK" in s
        assert "→" in s

    def test_check_investigate_appends_ellipsis(self, backend):
        s = format_phase_state("CHECK", "noetic", 0.5, "investigate", backend=backend)
        assert "CHK" in s
        assert "…" in s

    def test_postflight_praxic_uses_hammer(self, backend):
        # 🔨 (U+1F528) replaced ⚙ (U+2699) — the gear had ambiguous east-
        # asian-width and rendered narrow on some terminals, clipping the
        # percentage digits. Hammer is wide-default and matches docs.
        s = format_phase_state("POSTFLIGHT", "praxic", 0.95, backend=backend)
        assert "POST" in s
        assert "🔨" in s
        assert "⚙" not in s


class TestFormatVectorColored:
    def test_label_value_format(self, backend):
        s = format_vector_colored("K", 0.82, backend=backend)
        assert "K:82%" in s

    def test_high_value_gets_bright_green(self):
        s = format_vector_colored("K", 0.85, backend=AnsiBackend())
        assert "\033[92m" in s  # bright_green ANSI code

    def test_low_value_gets_red(self):
        s = format_vector_colored("K", 0.10, backend=AnsiBackend())
        assert "\033[31m" in s  # red ANSI code


class TestFormatDeltas:
    def test_empty_returns_empty_string(self, backend):
        assert format_deltas(None, backend=backend) == ""
        assert format_deltas({}, backend=backend) == ""

    def test_net_positive_returns_check(self, backend):
        s = format_deltas({"know": 0.2, "context": 0.1}, backend=backend)
        assert "✓" in s

    def test_net_negative_returns_warning(self, backend):
        s = format_deltas({"know": -0.2, "completion": -0.1}, backend=backend)
        assert "⚠" in s

    def test_uncertainty_inverted(self, backend):
        # Lower uncertainty (negative delta) is a positive signal
        s = format_deltas({"uncertainty": -0.2}, backend=backend)
        assert "✓" in s

    def test_neutral_returns_triangle(self, backend):
        s = format_deltas({"know": 0.01}, backend=backend)
        assert "△" in s


# ─── Composite line builder ─────────────────────────────────────────


class TestFormatWorkPhaseBadge:
    def test_noetic_returns_investigate_badge(self, backend):
        s = format_work_phase_badge("noetic", backend=backend)
        assert "INVESTIGATE" in s
        assert "🔍" in s

    def test_praxic_returns_act_badge(self, backend):
        s = format_work_phase_badge("praxic", backend=backend)
        assert "ACT" in s
        assert "▶" in s

    @pytest.mark.parametrize("phase", [None, "", "closed", "no-transaction", "unknown"])
    def test_non_active_phases_return_empty(self, phase, backend):
        assert format_work_phase_badge(phase, backend=backend) == ""

    def test_noetic_uses_cyan_in_ansi(self):
        s = format_work_phase_badge("noetic", backend=AnsiBackend())
        assert "\033[36m" in s  # cyan ANSI code

    def test_praxic_uses_bright_green_in_ansi(self):
        s = format_work_phase_badge("praxic", backend=AnsiBackend())
        assert "\033[92m" in s  # bright_green ANSI code


class TestFormatSourceBadge:
    def test_intuition_returns_lightbulb_badge(self, backend):
        s = format_source_badge("intuition", backend=backend)
        assert "intuition" in s
        assert "💡" in s

    def test_search_returns_magnifier_badge(self, backend):
        s = format_source_badge("search", backend=backend)
        assert "search" in s
        assert "🔎" in s

    @pytest.mark.parametrize("src", [None, "", "unknown", "made-up"])
    def test_unknown_source_returns_empty(self, src, backend):
        assert format_source_badge(src, backend=backend) == ""

    def test_intuition_uses_yellow_in_ansi(self):
        s = format_source_badge("intuition", backend=AnsiBackend())
        assert "\033[33m" in s  # yellow

    def test_search_uses_cyan_in_ansi(self):
        s = format_source_badge("search", backend=AnsiBackend())
        assert "\033[36m" in s  # cyan


class TestRenderDefaultLine:
    def test_renders_all_sections_when_present(self, backend):
        s = render_default_line(
            vectors={"know": 0.8, "context": 0.7, "clarity": 0.6,
                     "coherence": 0.6, "signal": 0.6, "density": 0.6},
            phase="CHECK",
            gate_decision="proceed",
            open_counts={"open_goals": 2, "open_unknowns": 3, "goal_linked_unknowns": 1},
            backend=backend,
        )
        assert "🎯2" in s
        assert "CHK" in s
        assert "K:80%" in s
        assert "C:70%" in s
        assert "│" in s

    def test_postflight_appends_deltas(self, backend):
        s = render_default_line(
            vectors={"know": 0.9, "context": 0.85, "state": 0.9,
                     "change": 0.8, "completion": 1.0, "impact": 0.7},
            phase="POSTFLIGHT",
            deltas={"know": 0.2, "context": 0.15},
            open_counts={"open_goals": 0, "open_unknowns": 0, "goal_linked_unknowns": 0},
            backend=backend,
        )
        assert "Δ" in s
        assert "✓" in s

    def test_no_phase_omits_phase_section(self, backend):
        s = render_default_line(
            vectors={"know": 0.5, "context": 0.5},
            backend=backend,
        )
        assert "CHK" not in s
        assert "PRE" not in s
        assert "POST" not in s

    def test_postflight_shows_execution_pair_not_kc(self, backend):
        """POSTFLIGHT composite uses execution vectors (state/change/completion/
        impact) — the adjacent pair must do the same so the eye doesn't read
        K/C as ingredients of the praxic composite. Pre-fix: POST 🔨X% │ K:Y% C:Z%
        invited the wrong inference. Post-fix: POST 🔨X% │ S:Y% Δ:Z%."""
        s = render_default_line(
            vectors={
                "know": 0.95, "context": 0.95,  # Should NOT appear in POST
                "state": 0.6, "change": 0.4,     # SHOULD appear
                "completion": 1.0, "impact": 0.5,
            },
            phase="POSTFLIGHT",
            backend=backend,
        )
        assert "POST" in s
        assert "S:60%" in s  # state
        assert "Δ:40%" in s  # change
        assert "K:" not in s  # K/C deliberately suppressed during praxic
        assert "C:" not in s

    def test_check_proceed_keeps_kc_pair(self, backend):
        """CHECK composite uses 'check' formula regardless of gate_decision.
        K/C pair must stay through CHECK→proceed so the visible pair matches
        the composite's vector set (composite_phase stays 'check' even when
        work_phase becomes 'praxic')."""
        s = render_default_line(
            vectors={
                "know": 0.8, "context": 0.7, "clarity": 0.6,
                "coherence": 0.6, "signal": 0.6, "density": 0.6,
                "state": 0.0, "change": 0.0,  # Pre-execution — should NOT show
            },
            phase="CHECK",
            gate_decision="proceed",
            backend=backend,
        )
        assert "CHK" in s
        assert "K:80%" in s
        assert "C:70%" in s
        assert "S:" not in s  # Execution pair only at POSTFLIGHT
        assert "Δ:" not in s
