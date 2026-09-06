"""A rebuild may only DROP a collection it can put back.

`recreate_project_collections` dropped ten collections; `_embed_project_from_db`
refills three. `rebuild.py` contains zero references to decisions or assumptions.
So `empirica rebuild --qdrant-only` — the verb the gardening guidance names as
the way to refresh embedded payloads — permanently emptied seven collections and
reported success.

Measured 2026-09-06 on one box before the fix: 4,781 points across up to 24
practices (calibration 1,960 · episodic 1,688 · goals 1,036 · decisions 92 ·
assumptions 5). Nothing re-embeds them, so the loss was silent AND permanent.

The root cause is two hand-maintained lists that drifted. These tests assert the
INVARIANT — every dropped collection has a refiller — rather than the current
contents of either list, so they keep holding when a type is added.
"""

from __future__ import annotations

import ast
from pathlib import Path

from empirica.core.qdrant.collections import REBUILDABLE_COLLECTIONS, recreate_project_collections

SRC = Path(__file__).resolve().parents[1] / "empirica"


def _refill_calls() -> set[str]:
    """Embed/upsert functions the rebuild path actually invokes, read from its AST."""
    tree = ast.parse((SRC / "core" / "qdrant" / "rebuild.py").read_text())
    return {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id.startswith(("embed_", "upsert_"))
    }


def test_every_dropped_collection_has_a_refiller():
    """The invariant. Adding a collection to the drop list without a refiller fails here."""
    refillers = _refill_calls()
    assert refillers, "positive control: the rebuild path must call SOME embed function"

    # docs / memory / eidetic are covered by upsert_memory, embed_eidetic and
    # embed_project_code. Assert the mapping rather than trusting the names.
    coverage = {
        "_docs_collection": {"upsert_memory", "embed_result"},
        "_memory_collection": {"upsert_memory"},
        "_eidetic_collection": {"embed_eidetic", "embed_project_code"},
        "_decisions_collection": {"embed_decision"},
        "_assumptions_collection": {"embed_assumption"},
    }
    for fn in REBUILDABLE_COLLECTIONS:
        expected = coverage.get(fn.__name__)
        assert expected, f"{fn.__name__} is droppable but this test does not know its refiller"
        assert expected & refillers, f"{fn.__name__} is dropped but nothing in rebuild.py refills it"


def test_decisions_and_assumptions_ARE_now_refilled():
    """These two had no rebuild path at all until 2026-09-06.

    This test previously asserted the OPPOSITE — that they must stay out of the
    droppable set — and carried a note saying it was the reminder, not a
    prohibition. It fired when the refillers landed, which is the whole point:
    a collection becomes droppable by ACQUIRING a refiller, never by someone
    deciding it is safe to lose.
    """
    names = {fn.__name__ for fn in REBUILDABLE_COLLECTIONS}
    assert "_decisions_collection" in names
    assert "_assumptions_collection" in names
    assert _refill_calls() >= {"embed_decision", "embed_assumption"}


def test_the_refill_reads_the_tables_that_actually_hold_them():
    """`project_decisions` does not exist; the tables are `decisions` / `assumptions`.

    A refiller querying the wrong table returns zero rows forever and reports a
    successful rebuild — the zero-success-verb shape, indistinguishable from
    "this project has no decisions".
    """
    source = (SRC / "core" / "qdrant" / "rebuild.py").read_text()
    assert "FROM decisions" in source
    assert "FROM assumptions" in source
    assert "FROM project_decisions" not in source, "project_decisions is not a table in sessions.db"


def test_recreate_REPORTS_what_it_preserved_rather_than_silently_skipping(monkeypatch):
    """A skip that is not reported is indistinguishable from a collection that was handled."""
    monkeypatch.setattr("empirica.core.qdrant.collections.recreate_collection", lambda name: True)
    monkeypatch.setattr("empirica.core.qdrant.collections._get_qdrant_client", lambda *a, **k: None)

    result = recreate_project_collections("p1")

    assert "preserved" in result, "the untouched collections must be named in the receipt"
    assert "no rebuild path exists" in result["preserved"]["reason"]
    recreated = [k for k in result if k != "preserved"]
    assert len(recreated) == len(REBUILDABLE_COLLECTIONS)
    assert all(result[k] for k in recreated), "positive control: the recreatable ones still get recreated"
