"""Read-time recency re-ranking of PREFLIGHT findings (decay P1/a, 2026-05-28).

retrieve_task_patterns previously ranked findings by raw cosine score, so a
finding about code removed months ago ranked identically to one written today.
_apply_findings_recency folds FindingsDeprecationEngine's 30-day-half-life
time-decay into the ranking at read time (no stored mutation). These tests pin
the ranking behaviour + the ISO-timestamp normalisation (the payload stores ISO
strings, which calculate_time_decay alone would silently score 0.5).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from empirica.core.qdrant.pattern_retrieval import _apply_findings_recency


def test_fresh_finding_outranks_stale_with_higher_cosine():
    now = datetime.now()
    items = [
        # Stale but higher cosine similarity
        {"text": "stale", "score": 0.90, "timestamp": (now - timedelta(days=120)).isoformat()},
        # Fresh, slightly lower cosine
        {"text": "fresh", "score": 0.85, "timestamp": now.isoformat()},
    ]
    ranked = _apply_findings_recency(items, limit=2)
    # 120d decay = e^-4 ~= 0.018 -> stale effective ~0.016; fresh ~0.85
    assert ranked[0]["text"] == "fresh"
    assert ranked[0]["recency_weight"] > ranked[1]["recency_weight"]
    assert ranked[0]["effective_score"] > ranked[1]["effective_score"]


def test_missing_timestamp_is_neutral_weight():
    ranked = _apply_findings_recency(
        [{"text": "x", "score": 0.7, "timestamp": None}], limit=1
    )
    assert ranked[0]["recency_weight"] == 1.0
    assert ranked[0]["effective_score"] == 0.7


def test_unparseable_timestamp_is_neutral_weight():
    ranked = _apply_findings_recency(
        [{"text": "x", "score": 0.6, "timestamp": "not-a-date"}], limit=1
    )
    assert ranked[0]["recency_weight"] == 1.0


def test_limit_truncates_after_rerank():
    now = datetime.now().isoformat()
    items = [{"text": str(i), "score": 0.5, "timestamp": now} for i in range(5)]
    assert len(_apply_findings_recency(items, limit=3)) == 3


def test_empty_input_returns_empty():
    assert _apply_findings_recency([], limit=3) == []
