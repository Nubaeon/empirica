"""Each artifact type has exactly ONE Qdrant destination, whichever verb wrote it.

Decisions and assumptions used to land in `memory` when written by
`log-artifacts` and in their TYPED collections when written by `decision-log` /
`assumption-log`. So the destination depended on which verb a practitioner
happened to use — and the documented default is the batch verb, so the
recommended path disagreed with the alternative.

Measured 2026-09-06: retrieval searches BOTH (`_SEARCH_COLLECTIONS` covers memory
and the typed collections) and keys results by collection with NO cross-collection
dedup. So the split never lost retrievability — it produced two half-populated
buckets, and a duplicate for anything written both ways. 62 decisions were
double-listed.

Typed wins: choice / rationale / alternatives / reversibility / confidence against
a single concatenated `text`, plus the higher search boost (1.3 vs 1.2).
"""

from __future__ import annotations

import pytest

from empirica.cli.command_handlers.graph_commands import _auto_embed_node

CTX = {"project_id": "p1", "session_id": "s1"}


@pytest.fixture
def routed(monkeypatch):
    """Record which embedder each node type reaches."""
    seen: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "empirica.core.qdrant.memory.embed_single_memory_item",
        lambda **kw: seen.append(("memory", kw.get("item_type"))) or True,
    )
    monkeypatch.setattr(
        "empirica.core.qdrant.intent_layer.embed_decision",
        lambda **kw: seen.append(("decisions", "decision")) or True,
    )
    monkeypatch.setattr(
        "empirica.core.qdrant.intent_layer.embed_assumption",
        lambda **kw: seen.append(("assumptions", "assumption")) or True,
    )
    return seen


def test_a_batch_decision_goes_to_the_TYPED_collection(routed):
    _auto_embed_node({"type": "decision", "data": {"choice": "c", "rationale": "r"}}, "a1", CTX)
    assert routed == [("decisions", "decision")], "the batch verb must not send decisions to memory"


def test_a_batch_assumption_goes_to_the_TYPED_collection(routed):
    _auto_embed_node({"type": "assumption", "data": {"assumption": "a"}}, "a1", CTX)
    assert routed == [("assumptions", "assumption")]


@pytest.mark.parametrize(
    "ntype,data",
    [
        ("finding", {"finding": "f"}),
        ("unknown", {"unknown": "u"}),
        ("dead_end", {"approach": "a", "why_failed": "w"}),
        ("mistake", {"mistake": "m", "why_wrong": "w"}),
    ],
)
def test_the_memory_types_still_go_to_memory(routed, ntype, data):
    """Positive control. The two tests above would pass against a build that had
    stopped embedding to memory entirely."""
    _auto_embed_node({"type": ntype, "data": data}, "a1", CTX)
    assert routed == [("memory", ntype)]


def test_nothing_lands_in_TWO_collections(routed):
    """The regression this file exists to prevent: writing both destinations
    double-lists the artifact, because results are keyed by collection and
    nothing dedups across them."""
    for ntype, data in [
        ("decision", {"choice": "c", "rationale": "r"}),
        ("assumption", {"assumption": "a"}),
        ("finding", {"finding": "f"}),
    ]:
        _auto_embed_node({"type": ntype, "data": data}, "a1", CTX)
    assert len(routed) == 3, f"each artifact must reach exactly one embedder, got {routed}"
    assert len({c for c, _ in routed}) == 3


def test_the_rebuild_refill_does_not_also_write_memory():
    """The same rule on the re-embed side. bf0955f8 wrote both and would have
    duplicated all 595 decisions on the next run."""
    import inspect

    from empirica.core.qdrant import rebuild

    src = inspect.getsource(rebuild._embed_project_from_db)
    assert "_build_decision_items" not in src, "decisions must not be added to mem_items"
    assert "_build_assumption_items" not in src
    assert "_embed_typed_decisions" in src, "positive control: the typed refill must still run"
