"""Tests for goal-driven post-test criterion evaluators (G1).

Covers:
  - Public surface: CriterionContext, CriterionResult, register/dispatch
  - SubtaskCompletionEvaluator: passes when ratio ≥ threshold, fails otherwise,
    handles zero-subtask case via is_completed flag
  - Registry: skipped result for unmatched validation_method
  - Evaluator-raises-exception path returns skipped, not raise
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from empirica.core.goals.types import (
    Goal,
    ScopeVector,
    SuccessCriterion,
)
from empirica.core.post_test.collector import EvidenceBundle, EvidenceItem, EvidenceQuality
from empirica.core.post_test.criterion_evaluators import (
    CriterionContext,
    CriterionResult,
    dispatch,
    register,
)
from empirica.core.post_test.criterion_evaluators._types import CriterionEvaluator
from empirica.core.post_test.criterion_evaluators.builtin import (
    EvidenceMetricEvaluator,
    SubtaskCompletionEvaluator,
)
from empirica.core.post_test.criterion_evaluators.registry import (
    _EVALUATORS,
    reset_for_tests,
)


def _make_goal(*, total_subtasks: int, completed: int, is_completed: bool = False) -> Goal:
    """Build a Goal with a stubbed calculate_progress() return value."""
    import uuid
    goal = Goal(
        id=str(uuid.uuid4()),
        objective="test goal",
        success_criteria=[],
        scope=ScopeVector(0.3, 0.2, 0.1),
    )
    goal.is_completed = is_completed
    pct = (completed / total_subtasks * 100.0) if total_subtasks else 0.0
    goal.calculate_progress = lambda: {  # type: ignore[method-assign]
        "total_subtasks": total_subtasks,
        "completed": completed,
        "in_progress": 0,
        "pending": total_subtasks - completed,
        "blocked": 0,
        "skipped": 0,
        "completion_percentage": pct,
    }
    return goal


def _make_criterion(
    *, threshold: float | None = 1.0, method: str = "completion", required: bool = True
) -> SuccessCriterion:
    return SuccessCriterion(
        id="crit-test",
        description="test criterion",
        validation_method=method,
        threshold=threshold,
        is_required=required,
    )


def _make_ctx(goal: Goal, criterion: SuccessCriterion) -> CriterionContext:
    return CriterionContext(
        criterion=criterion,
        goal=goal,
        evidence=EvidenceBundle(session_id="test-session"),
        session_id="test-session",
    )


# ---------------------------------------------------------------------------
# SubtaskCompletionEvaluator
# ---------------------------------------------------------------------------


def test_subtask_completion_passes_when_ratio_meets_threshold():
    goal = _make_goal(total_subtasks=4, completed=4)
    crit = _make_criterion(threshold=1.0)
    result = SubtaskCompletionEvaluator().evaluate(_make_ctx(goal, crit))
    assert result.passed is True
    assert result.skipped is False
    assert result.value == 1.0
    assert result.threshold == 1.0
    assert result.iteration_needed is False


def test_subtask_completion_fails_when_ratio_below_threshold():
    goal = _make_goal(total_subtasks=4, completed=2)
    crit = _make_criterion(threshold=0.75)
    result = SubtaskCompletionEvaluator().evaluate(_make_ctx(goal, crit))
    assert result.passed is False
    assert result.value == 0.5
    assert result.iteration_needed is True
    assert result.next_transaction is not None


def test_subtask_completion_no_iteration_needed_when_not_required():
    goal = _make_goal(total_subtasks=4, completed=2)
    crit = _make_criterion(threshold=0.75, required=False)
    result = SubtaskCompletionEvaluator().evaluate(_make_ctx(goal, crit))
    assert result.passed is False
    assert result.iteration_needed is False


def test_subtask_completion_zero_subtasks_with_completed_flag_passes():
    goal = _make_goal(total_subtasks=0, completed=0, is_completed=True)
    crit = _make_criterion()
    result = SubtaskCompletionEvaluator().evaluate(_make_ctx(goal, crit))
    assert result.passed is True
    assert result.skipped is False
    assert result.value == 1.0


def test_subtask_completion_zero_subtasks_no_completion_skipped():
    goal = _make_goal(total_subtasks=0, completed=0, is_completed=False)
    crit = _make_criterion()
    result = SubtaskCompletionEvaluator().evaluate(_make_ctx(goal, crit))
    assert result.passed is False
    assert result.skipped is True


def test_subtask_completion_default_threshold_is_one():
    """When criterion.threshold is None, evaluator defaults to 1.0."""
    goal = _make_goal(total_subtasks=2, completed=2)
    crit = _make_criterion(threshold=None)
    result = SubtaskCompletionEvaluator().evaluate(_make_ctx(goal, crit))
    assert result.threshold == 1.0
    assert result.passed is True


# ---------------------------------------------------------------------------
# Registry / dispatch
# ---------------------------------------------------------------------------


@pytest.fixture
def isolated_registry():
    """Each test gets a fresh registry; built-ins re-registered after."""
    saved = {k: list(v) for k, v in _EVALUATORS.items()}
    reset_for_tests()
    yield
    reset_for_tests()
    for k, v in saved.items():
        _EVALUATORS[k] = list(v)


def test_dispatch_unmatched_method_returns_skipped(isolated_registry):
    goal = _make_goal(total_subtasks=1, completed=0)
    crit = _make_criterion(method="nonexistent_method")
    result = dispatch(_make_ctx(goal, crit))
    assert result.skipped is True
    assert "No evaluator registered" in result.summary


def test_dispatch_first_applicable_wins(isolated_registry):
    """Registry returns first evaluator whose applies() returns True."""
    calls: list[str] = []

    class FirstNo:
        validation_method = "x"

        def applies(self, _ctx: CriterionContext) -> bool:
            calls.append("first")
            return False

        def evaluate(self, ctx: CriterionContext) -> CriterionResult:
            return CriterionResult(
                criterion_id=ctx.criterion.id, goal_id=ctx.goal.id,
                validation_method="x", passed=True, summary="first",
            )

    class SecondYes:
        validation_method = "x"

        def applies(self, _ctx: CriterionContext) -> bool:
            calls.append("second")
            return True

        def evaluate(self, ctx: CriterionContext) -> CriterionResult:
            return CriterionResult(
                criterion_id=ctx.criterion.id, goal_id=ctx.goal.id,
                validation_method="x", passed=True, summary="second",
            )

    register(FirstNo())  # type: ignore[arg-type]
    register(SecondYes())  # type: ignore[arg-type]

    goal = _make_goal(total_subtasks=1, completed=0)
    crit = _make_criterion(method="x")
    result = dispatch(_make_ctx(goal, crit))
    assert result.summary == "second"
    assert calls == ["first", "second"]


def test_dispatch_evaluator_exception_returns_skipped(isolated_registry):
    """Evaluator raising mid-evaluate yields skipped result, not crash."""

    class Boom:
        validation_method = "x"

        def applies(self, _ctx: CriterionContext) -> bool:
            return True

        def evaluate(self, _ctx: CriterionContext) -> CriterionResult:
            raise RuntimeError("simulated")

    register(Boom())  # type: ignore[arg-type]

    goal = _make_goal(total_subtasks=1, completed=0)
    crit = _make_criterion(method="x")
    result = dispatch(_make_ctx(goal, crit))
    assert result.skipped is True
    assert "Boom" in result.summary
    assert "RuntimeError" in result.summary


def test_builtin_completion_evaluator_is_registered():
    """SubtaskCompletionEvaluator should be registered on package import."""
    completion_evaluators = _EVALUATORS.get("completion", [])
    assert any(
        type(e).__name__ == "SubtaskCompletionEvaluator" for e in completion_evaluators
    )


# ---------------------------------------------------------------------------
# Result serialization
# ---------------------------------------------------------------------------


def test_result_to_dict_has_expected_keys():
    r = CriterionResult(
        criterion_id="c1", goal_id="g1", validation_method="completion",
        passed=True, value=0.9, threshold=0.8,
    )
    d = r.to_dict()
    assert d["criterion_id"] == "c1"
    assert d["goal_id"] == "g1"
    assert d["passed"] is True
    assert d["value"] == 0.9
    assert d["threshold"] == 0.8
    assert d["skipped"] is False


# ---------------------------------------------------------------------------
# Protocol type contract (compile-time only; smoke check)
# ---------------------------------------------------------------------------


def test_subtask_evaluator_satisfies_protocol():
    """SubtaskCompletionEvaluator should satisfy CriterionEvaluator structurally."""
    inst: CriterionEvaluator = SubtaskCompletionEvaluator()
    assert inst.validation_method == "completion"
    assert callable(inst.applies)
    assert callable(inst.evaluate)


# ---------------------------------------------------------------------------
# evaluate_goal_criteria orchestrator (integration with repo)
# ---------------------------------------------------------------------------


def test_evaluate_goal_criteria_empty_when_no_active_goals():
    """No active criteria → evaluated=0, no errors."""
    from empirica.core.post_test.criterion_evaluators import evaluate_goal_criteria

    with patch(
        "empirica.core.goals.repository.GoalRepository"
    ) as MockRepo:
        MockRepo.return_value.list_active_criteria_for_session.return_value = []
        block = evaluate_goal_criteria(
            session_id="s1",
            evidence=EvidenceBundle(session_id="s1"),
        )
    assert block["evaluated"] == 0
    assert block["results"] == []


def test_evaluate_goal_criteria_persists_is_met():
    """Each non-skipped result triggers update_is_met on the criterion."""
    from empirica.core.post_test.criterion_evaluators import evaluate_goal_criteria

    goal = _make_goal(total_subtasks=2, completed=2)
    crit = _make_criterion(threshold=1.0)

    with patch(
        "empirica.core.goals.repository.GoalRepository"
    ) as MockRepo:
        MockRepo.return_value.list_active_criteria_for_session.return_value = [(goal, crit)]
        block = evaluate_goal_criteria(
            session_id="s1",
            evidence=EvidenceBundle(session_id="s1"),
        )
        MockRepo.return_value.update_is_met.assert_called_once_with(crit.id, True)
    assert block["evaluated"] == 1
    assert block["passed"] == 1
    assert block["failed"] == 0


# ---------------------------------------------------------------------------
# EvidenceMetricEvaluator (G2)
# ---------------------------------------------------------------------------


def _make_bundle_with_metric(
    metric_name: str, value: float, *, direction: str = "higher_is_better"
) -> EvidenceBundle:
    bundle = EvidenceBundle(session_id="test")
    bundle.items.append(EvidenceItem(
        source="test",
        metric_name=metric_name,
        value=value,
        raw_value=value,
        quality=EvidenceQuality.OBJECTIVE,
        supports_vectors=[],
        direction=direction,
    ))
    return bundle


def _make_quality_gate_ctx(
    bundle: EvidenceBundle, metric_name: str, threshold: float | None = 0.5,
    is_required: bool = True,
) -> CriterionContext:
    goal = _make_goal(total_subtasks=0, completed=0)
    crit = SuccessCriterion(
        id="qg-crit",
        description=metric_name,
        validation_method="quality_gate",
        threshold=threshold,
        is_required=is_required,
    )
    return CriterionContext(
        criterion=crit, goal=goal, evidence=bundle,
        session_id="test",
    )


def test_quality_gate_higher_is_better_passes_when_value_at_or_above_threshold():
    bundle = _make_bundle_with_metric("test_metric", value=0.8, direction="higher_is_better")
    ctx = _make_quality_gate_ctx(bundle, "test_metric", threshold=0.5)
    result = EvidenceMetricEvaluator().evaluate(ctx)
    assert result.passed is True
    assert result.value == 0.8
    assert "higher_is_better" in result.summary


def test_quality_gate_higher_is_better_fails_when_value_below_threshold():
    bundle = _make_bundle_with_metric("test_metric", value=0.3, direction="higher_is_better")
    ctx = _make_quality_gate_ctx(bundle, "test_metric", threshold=0.5)
    result = EvidenceMetricEvaluator().evaluate(ctx)
    assert result.passed is False
    assert result.iteration_needed is True


def test_quality_gate_lower_is_better_passes_when_value_at_or_below_threshold():
    bundle = _make_bundle_with_metric("violations_per_100", value=0.2, direction="lower_is_better")
    ctx = _make_quality_gate_ctx(bundle, "violations_per_100", threshold=0.25)
    result = EvidenceMetricEvaluator().evaluate(ctx)
    assert result.passed is True
    assert "lower_is_better" in result.summary


def test_quality_gate_lower_is_better_fails_when_value_above_threshold():
    bundle = _make_bundle_with_metric("violations_per_100", value=0.4, direction="lower_is_better")
    ctx = _make_quality_gate_ctx(bundle, "violations_per_100", threshold=0.25)
    result = EvidenceMetricEvaluator().evaluate(ctx)
    assert result.passed is False
    assert result.iteration_needed is True


def test_quality_gate_skips_when_metric_missing_from_bundle():
    bundle = EvidenceBundle(session_id="test")  # empty
    ctx = _make_quality_gate_ctx(bundle, "absent_metric", threshold=0.5)
    # applies() should return False since metric is missing
    assert EvidenceMetricEvaluator().applies(ctx) is False


def test_quality_gate_evaluate_returns_skipped_when_threshold_none():
    bundle = _make_bundle_with_metric("test_metric", value=0.5)
    ctx = _make_quality_gate_ctx(bundle, "test_metric", threshold=None)
    result = EvidenceMetricEvaluator().evaluate(ctx)
    assert result.skipped is True
    assert "without threshold" in result.summary


def test_quality_gate_iteration_skipped_for_non_required_failing():
    bundle = _make_bundle_with_metric("test_metric", value=0.1, direction="higher_is_better")
    ctx = _make_quality_gate_ctx(bundle, "test_metric", threshold=0.5, is_required=False)
    result = EvidenceMetricEvaluator().evaluate(ctx)
    assert result.passed is False
    assert result.iteration_needed is False


def test_quality_gate_evaluator_is_registered():
    """EvidenceMetricEvaluator should be registered on package import."""
    from empirica.core.post_test.criterion_evaluators.registry import _EVALUATORS
    quality_evaluators = _EVALUATORS.get("quality_gate", [])
    assert any(
        type(e).__name__ == "EvidenceMetricEvaluator" for e in quality_evaluators
    )


# ---------------------------------------------------------------------------
# EvidenceBundle helpers (has, get, direction)
# ---------------------------------------------------------------------------


def test_evidence_bundle_has_returns_false_for_missing_metric():
    bundle = EvidenceBundle(session_id="test")
    assert bundle.has("anything") is False


def test_evidence_bundle_has_returns_true_for_present_metric():
    bundle = _make_bundle_with_metric("foo", 0.5)
    assert bundle.has("foo") is True


def test_evidence_bundle_get_returns_raw_value_when_scalar():
    bundle = _make_bundle_with_metric("foo", 0.42)
    assert bundle.get("foo") == 0.42


def test_evidence_bundle_get_falls_back_to_normalized_when_raw_non_scalar():
    bundle = EvidenceBundle(session_id="test")
    bundle.items.append(EvidenceItem(
        source="test", metric_name="bar", value=0.7,
        raw_value={"complex": "dict"},  # not scalar
        quality=EvidenceQuality.OBJECTIVE, supports_vectors=[],
    ))
    assert bundle.get("bar") == 0.7


def test_evidence_bundle_get_returns_none_for_missing():
    bundle = EvidenceBundle(session_id="test")
    assert bundle.get("missing") is None


def test_evidence_bundle_direction_returns_declared_value():
    bundle = _make_bundle_with_metric("err_count", 5.0, direction="lower_is_better")
    assert bundle.direction("err_count") == "lower_is_better"


def test_evidence_bundle_direction_defaults_to_higher_is_better_for_missing():
    bundle = EvidenceBundle(session_id="test")
    assert bundle.direction("missing") == "higher_is_better"


def test_evidence_item_default_direction_is_higher_is_better():
    item = EvidenceItem(
        source="x", metric_name="y", value=0.5, raw_value=0.5,
        quality=EvidenceQuality.OBJECTIVE, supports_vectors=[],
    )
    assert item.direction == "higher_is_better"


def test_evaluate_goal_criteria_iteration_needed_propagates():
    """Failing required criterion → iteration_needed=True at the block level."""
    from empirica.core.post_test.criterion_evaluators import evaluate_goal_criteria

    goal = _make_goal(total_subtasks=4, completed=1)
    crit = _make_criterion(threshold=1.0, required=True)

    with patch(
        "empirica.core.goals.repository.GoalRepository"
    ) as MockRepo:
        MockRepo.return_value.list_active_criteria_for_session.return_value = [(goal, crit)]
        block = evaluate_goal_criteria(
            session_id="s1",
            evidence=EvidenceBundle(session_id="s1"),
        )
    assert block["iteration_needed"] is True
    assert block["failed"] == 1
