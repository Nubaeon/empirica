"""The finding-log immune-system decay helpers are DISABLED (2026-05-28).

Both previously fired on relatedness (keyword overlap / cosine similarity),
not actual contradiction, so a confirmatory finding decayed the fact/lesson it
confirmed (autoimmune). Until a real opposition predicate exists (goal 98055360
P2, converged w/ cortex on decay thread prop_j7y7f4), finding-log must NOT
auto-decay. These tests guard against accidental re-enable without the predicate.

The helpers early-return before any Qdrant / cold-storage I/O, so inputs that
would previously have triggered decay must now produce no-ops regardless.
"""

from __future__ import annotations

from empirica.cli.command_handlers.artifact_log_commands import (
    _decay_eidetic_by_finding,
    _decay_related_lessons,
)


def test_decay_related_lessons_is_disabled_noop():
    # Keyword-rich finding in a real domain — would previously decay lessons
    # sharing >=2 keywords. Must now be a no-op.
    assert _decay_related_lessons(
        "the sentinel gate blocks praxic tools before check", "sentinel", "proj"
    ) == []


def test_decay_eidetic_by_finding_is_disabled_noop():
    # Would previously decay eidetic facts with cosine >= 0.85. Must now be a no-op.
    assert _decay_eidetic_by_finding(
        "proj", "the sentinel gate blocks praxic tools before check", "sentinel"
    ) == 0
