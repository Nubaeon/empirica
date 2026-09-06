"""A filtered count must say what it filtered FROM, in the response itself.

Two daemon endpoints serve engagements and apply DIFFERENT default scopes on
DIFFERENT FIELDS — `/api/v1/engagements` on `engagements.lifecycle_state`,
`/api/v1/entities?type=engagement` on `entity_registry.status`. Measured
2026-09-06: 52 rows in the store, 44 from one endpoint, 41 from the other.

Both were correct. Neither said so. A peer practice comparing them could not
tell a designed filter from a dropped row, spent an investigation on it, and
blocked a deletion decision on possible data loss that had not occurred.

The fix is not to unify the filters — they answer different questions. It is to
make completeness checkable from the response, which is the only place the
consumer can check it.
"""

from __future__ import annotations

import pytest

from empirica.data.repositories.workspace_db import WorkspaceDBRepository


@pytest.fixture
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv("EMPIRICA_WORKSPACE_DB", str(tmp_path / "workspace.db"))
    monkeypatch.setenv("HOME", str(tmp_path))
    with WorkspaceDBRepository.open(ensure_schema=True) as r:
        yield r


def test_count_engagements_is_the_unfiltered_denominator(repo):
    assert repo.count_engagements() == 0, "positive control: an empty store counts zero, not -1"


def test_count_entities_scopes_by_type(repo):
    assert repo.count_entities(entity_type="engagement") == 0
    assert repo.count_entities() == 0


def test_an_unreadable_table_returns_MINUS_ONE_not_zero(repo, monkeypatch):
    """Unknown is not zero.

    A consumer comparing `count` against a total of 0 concludes everything was
    filtered out. Against -1 it concludes the total is unavailable — which is
    the truth, and a different statement.
    """

    def boom(*a, **k):
        raise RuntimeError("table gone")

    monkeypatch.setattr(type(repo), "_execute", boom)
    assert repo.count_engagements() == -1
    assert repo.count_entities(entity_type="engagement") == -1


def test_both_routes_declare_the_FIELD_they_scope_by():
    """The load-bearing detail: the two endpoints differ because they filter
    different COLUMNS, not because one is losing rows. A consumer told only
    'filtered' still cannot reconcile the two numbers."""
    import inspect

    from empirica.api.routes import engagements as eng_route
    from empirica.api.routes import entities as ent_route

    eng_src = inspect.getsource(eng_route.list_engagements)
    ent_src = inspect.getsource(ent_route.list_entities)

    assert '"engagements.lifecycle_state"' in eng_src
    assert '"entity_registry.status"' in ent_src
    for src in (eng_src, ent_src):
        assert "total_unfiltered" in src, "a scoped list must carry its own denominator"
        assert '"scope"' in src
