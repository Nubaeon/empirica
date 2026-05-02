"""Golden-snapshot tests for empirica.core.chat.narration — Phase 15.

These tests pin down the exact verbiage used for each event kind. If
you change a one-liner string, intentionally update the golden
expected output. The test suite IS the spec for what users see.
"""

from __future__ import annotations

import pytest

from empirica.core.chat.narration import (
    narrate,
    narrate_empirica_event,
    narrate_translator_event,
)

# ─── Empirica events ──────────────────────────────────────────────


class TestEmpiricaEventGolden:
    @pytest.mark.parametrize("event,expected", [
        ({"kind": "preflight", "task_context": "Fix the auth bug in middleware.py"},
            "thinking through: Fix the auth bug in middleware.py"),
        ({"kind": "preflight"},
            "thinking through new transaction"),
        ({"kind": "check", "decision": "proceed"},
            "ready to act"),
        ({"kind": "check", "decision": "investigate"},
            "needs more investigation"),
        ({"kind": "postflight", "confidence": 0.92},
            "wrapped up (confidence 92%)"),
        ({"kind": "postflight"},
            "wrapped up transaction"),
        ({"kind": "finding_log", "finding": "Auth uses JWT in middleware chain"},
            "logged finding: Auth uses JWT in middleware chain"),
        ({"kind": "decision_log", "choice": "Use Redis for sessions"},
            "decided: Use Redis for sessions"),
        ({"kind": "unknown_log", "unknown": "How does role hierarchy resolve?"},
            "open question: How does role hierarchy resolve?"),
        ({"kind": "mistake_log", "mistake": "Edited wrong branch"},
            "caught a mistake: Edited wrong branch"),
        ({"kind": "deadend_log", "approach": "Tried passport.js"},
            "dead end: Tried passport.js"),
        ({"kind": "assumption_log", "assumption": "Migrations run automatically"},
            "assuming: Migrations run automatically"),
        ({"kind": "goal_create", "objective": "Implement auth middleware"},
            "new goal: Implement auth middleware"),
        ({"kind": "goal_complete", "objective": "Implement auth middleware"},
            "goal complete: Implement auth middleware"),
        ({"kind": "skill_invoke", "skill": "epistemic-transaction"},
            "invoking skill: epistemic-transaction"),
        ({"kind": "agent_launch", "agent": "code-reviewer", "description": "review the auth changes"},
            "launching code-reviewer — review the auth changes"),
        ({"kind": "agent_launch", "subagent_type": "Explore"},
            "launching Explore"),
        ({"kind": "plan_transition", "from": "noetic", "to": "praxic"},
            "plan: noetic → praxic"),
    ])
    def test_golden(self, event, expected):
        assert narrate_empirica_event(event) == expected

    def test_check_unknown_decision_returns_none(self):
        assert narrate_empirica_event({"kind": "check", "decision": "wat"}) is None

    def test_unrecognized_kind_returns_none(self):
        assert narrate_empirica_event({"kind": "imaginary_event"}) is None

    def test_missing_kind_returns_none(self):
        assert narrate_empirica_event({}) is None

    def test_long_text_is_ellipsized(self):
        long = "x" * 200
        out = narrate_empirica_event({"kind": "finding_log", "finding": long})
        assert out is not None
        assert len(out) < 100  # ellipsized to ~60 + "logged finding: " prefix
        assert out.endswith("…")


# ─── Translator events ────────────────────────────────────────────


class TestTranslatorEventGolden:
    @pytest.mark.parametrize("event,expected", [
        ({"kind": "request_started", "provider": "deepseek", "model": "deepseek-chat"},
            "calling deepseek:deepseek-chat"),
        ({"kind": "request_completed", "duration_ms": 1234, "text_chars": 567},
            "response complete (1234ms, 567 chars)"),
        ({"kind": "request_completed", "duration_ms": 89},
            "response complete (89ms)"),
        ({"kind": "request_completed"},
            "response complete"),
        ({"kind": "request_errored", "stage": "upstream", "error": "402 Insufficient Balance"},
            "request error at upstream: 402 Insufficient Balance"),
        ({"kind": "request_errored", "stage": "parsing"},
            "request error at parsing"),
    ])
    def test_golden(self, event, expected):
        assert narrate_translator_event(event) == expected

    def test_stream_event_returns_none(self):
        # High-frequency, no per-chunk surface
        assert narrate_translator_event({"kind": "stream_event", "delta": "Hi"}) is None

    def test_unrecognized_kind_returns_none(self):
        assert narrate_translator_event({"kind": "wat"}) is None

    def test_missing_kind_returns_none(self):
        assert narrate_translator_event({}) is None

    def test_accepts_type_field_alias(self):
        # Some emitters use 'type' instead of 'kind'
        assert narrate_translator_event({"type": "request_started"}) == "calling ?:?"


# ─── Dispatcher ───────────────────────────────────────────────────


class TestNarrateDispatcher:
    def test_translator_source_marker_routes_to_translator(self):
        e = {"source": "translator", "kind": "request_started", "provider": "p", "model": "m"}
        assert narrate(e) == "calling p:m"

    def test_translator_kind_alone_routes_to_translator(self):
        e = {"kind": "request_completed", "duration_ms": 100}
        assert narrate(e) == "response complete (100ms)"

    def test_empirica_kind_routes_to_empirica(self):
        e = {"kind": "preflight"}
        assert narrate(e) == "thinking through new transaction"

    def test_unrecognized_returns_none(self):
        assert narrate({"kind": "imaginary"}) is None
        assert narrate({}) is None
