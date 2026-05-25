"""Tests for migration 046 (refdocs → sources) + the dual reader/writer.

Phase 1 of goal 3d6aeb08 (deprecate refdocs, full migration to sources
with source_type='pointer'):

  - Writer (`add_reference_doc`) now inserts into `epistemic_sources`
    with `source_type='pointer'` instead of `project_reference_docs`.
  - Reader (`get_project_reference_docs`) queries the same source-type
    and projects the row back into the legacy refdoc shape so existing
    consumers (bootstrap formatter, extension renderer) see no behavior
    change.
  - Migration 046 backfills any rows that exist in the legacy table.

These tests exercise: writer routes to sources, reader returns the
right shape, migration is idempotent, mixed (new + migrated) reads
work, and consumer-facing fields (doc_path, doc_type, doc_data) are
preserved across the unification.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

import pytest

from empirica.data.migrations.migrations import migration_046_refdocs_to_sources
from empirica.data.session_database import SessionDatabase


@pytest.fixture
def db(tmp_path: Path):
    """Fresh DB with one project."""
    db_path = str(tmp_path / "test.db")
    sdb = SessionDatabase(db_path)
    project_id = str(uuid.uuid4())
    sdb.conn.execute(
        "INSERT INTO projects (id, name, created_timestamp, project_data) "
        "VALUES (?, ?, ?, ?)",
        (project_id, "test-project", time.time(), "{}"),
    )
    sdb.conn.commit()
    sdb._test_project_id = project_id  # type: ignore[attr-defined]
    yield sdb
    sdb.close()


# ── Writer: add_reference_doc routes to epistemic_sources ─────────────


def test_add_reference_doc_writes_to_sources_not_legacy_table(db):
    """New writes land in epistemic_sources with source_type='pointer'."""
    project_id = db._test_project_id
    doc_id = db.add_reference_doc(
        project_id=project_id,
        doc_path="docs/architecture.md",
        doc_type="architecture",
        description="System architecture overview",
    )
    cursor = db.conn.cursor()

    # In sources, not in legacy table
    src = cursor.execute(
        "SELECT id, source_type, source_url, title, description, "
        "epistemic_layer, confidence FROM epistemic_sources WHERE id = ?",
        (doc_id,),
    ).fetchone()
    assert src is not None
    assert src["source_type"] == "pointer"
    assert src["source_url"] == "docs/architecture.md"
    assert src["title"] == "architecture.md"  # basename
    assert src["description"] == "System architecture overview"
    assert src["epistemic_layer"] == "noetic"
    assert src["confidence"] == 0.7

    legacy = cursor.execute(
        "SELECT COUNT(*) FROM project_reference_docs WHERE id = ?",
        (doc_id,),
    ).fetchone()[0]
    assert legacy == 0, "writer should not touch the legacy table"


def test_add_reference_doc_preserves_doc_type_in_metadata(db):
    """`doc_type` survives the trip through source_metadata."""
    project_id = db._test_project_id
    doc_id = db.add_reference_doc(
        project_id=project_id,
        doc_path="docs/api.md",
        doc_type="api",
        description="API ref",
    )
    cursor = db.conn.cursor()
    metadata_raw = cursor.execute(
        "SELECT source_metadata FROM epistemic_sources WHERE id = ?",
        (doc_id,),
    ).fetchone()[0]
    metadata = json.loads(metadata_raw)
    assert metadata["doc_type"] == "api"


# ── Reader: get_project_reference_docs projects sources to legacy shape


def test_reader_returns_legacy_refdoc_shape(db):
    """Reader returns dicts with doc_path / doc_type / description /
    created_timestamp / doc_data, matching what consumers expect."""
    project_id = db._test_project_id
    db.add_reference_doc(
        project_id=project_id,
        doc_path="docs/guide.md",
        doc_type="guide",
        description="User guide",
    )
    docs = db.get_project_reference_docs(project_id)
    assert len(docs) == 1
    d = docs[0]
    assert d["doc_path"] == "docs/guide.md"
    assert d["doc_type"] == "guide"
    assert d["description"] == "User guide"
    assert isinstance(d["created_timestamp"], float)
    assert d["created_timestamp"] > 0
    # doc_data reconstructed for backward compat
    assert "doc_data" in d


def test_reader_filters_by_source_type_pointer(db):
    """Reader returns only sources with source_type='pointer', not
    other source_types co-existing in the same project."""
    project_id = db._test_project_id
    # Add a refdoc (becomes pointer)
    db.add_reference_doc(project_id=project_id, doc_path="docs/x.md")
    # Add a non-pointer source — should NOT appear in refdoc reader
    db.add_epistemic_source(
        project_id=project_id,
        source_type="document",
        title="Some other source",
    )
    docs = db.get_project_reference_docs(project_id)
    assert len(docs) == 1
    assert docs[0]["doc_path"] == "docs/x.md"


def test_reader_excludes_archived_sources(db):
    """Archived sources don't show up in the refdoc reader."""
    project_id = db._test_project_id
    doc_id = db.add_reference_doc(project_id=project_id, doc_path="docs/y.md")

    # Manually flip archived
    db.conn.execute(
        "UPDATE epistemic_sources SET archived = 1 WHERE id = ?",
        (doc_id,),
    )
    db.conn.commit()

    docs = db.get_project_reference_docs(project_id)
    assert len(docs) == 0


# ── Migration 046: idempotent backfill of legacy rows ─────────────────


def test_migration_046_copies_legacy_rows_into_sources(db):
    """Migration backfills any rows that exist in the legacy table."""
    project_id = db._test_project_id
    legacy_id = str(uuid.uuid4())
    db.conn.execute(
        """INSERT INTO project_reference_docs
           (id, project_id, doc_path, doc_type, description,
            created_timestamp, doc_data)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (legacy_id, project_id, "docs/legacy.md", "arch", "Legacy",
         time.time(), '{"x": 1}'),
    )
    db.conn.commit()

    migration_046_refdocs_to_sources(db.conn.cursor())
    db.conn.commit()

    src = db.conn.execute(
        "SELECT source_type, source_url, description, source_metadata "
        "FROM epistemic_sources WHERE id = ?",
        (legacy_id,),
    ).fetchone()
    assert src is not None
    assert src["source_type"] == "pointer"
    assert src["source_url"] == "docs/legacy.md"
    assert src["description"] == "Legacy"
    metadata = json.loads(src["source_metadata"])
    assert metadata["doc_type"] == "arch"
    assert metadata["migrated_from"] == "project_reference_docs"


def test_migration_046_is_idempotent(db):
    """Re-running the migration doesn't duplicate rows."""
    project_id = db._test_project_id
    legacy_id = str(uuid.uuid4())
    db.conn.execute(
        """INSERT INTO project_reference_docs
           (id, project_id, doc_path, created_timestamp, doc_data)
           VALUES (?, ?, ?, ?, ?)""",
        (legacy_id, project_id, "docs/z.md", time.time(), "{}"),
    )
    db.conn.commit()

    migration_046_refdocs_to_sources(db.conn.cursor())
    db.conn.commit()
    migration_046_refdocs_to_sources(db.conn.cursor())  # re-run
    db.conn.commit()
    migration_046_refdocs_to_sources(db.conn.cursor())  # and again
    db.conn.commit()

    count = db.conn.execute(
        "SELECT COUNT(*) FROM epistemic_sources WHERE id = ?",
        (legacy_id,),
    ).fetchone()[0]
    assert count == 1


def test_migration_046_handles_empty_legacy_table(db):
    """No legacy rows → migration completes cleanly."""
    # Smoke: no exception
    migration_046_refdocs_to_sources(db.conn.cursor())
    db.conn.commit()


def test_refdoc_add_cli_command_is_removed():
    """Phase 2: the `empirica refdoc-add` CLI no longer exists.

    Phase 2 of goal 3d6aeb08. The Python API (add_reference_doc /
    get_project_reference_docs) is still in place for internal callers
    — only the user-facing CLI surface is dropped. Users should use
    `empirica source-add` instead (which routes to the same epistemic_sources
    table; source_type='pointer' if they want strict equivalence).
    """
    import subprocess
    proc = subprocess.run(
        ["empirica", "refdoc-add", "--help"],
        capture_output=True, text=True, check=False,
    )
    # Argparse exits 2 on unknown command + writes "invalid choice" to stderr
    assert proc.returncode != 0
    assert "invalid choice: 'refdoc-add'" in (proc.stderr or proc.stdout)


def test_source_add_does_not_double_write_to_refdocs(db):
    """Phase 2 fix: source-add used to dual-write (sources table + refdocs
    back-compat). Post-Phase-1, add_reference_doc routes to sources too,
    which made the dual-write a silent double-insert (one row with the
    user's source_type, one with source_type='pointer'). The back-compat
    write is removed in Phase 2; source-add now writes exactly one row.
    """
    project_id = db._test_project_id
    source_id = db.add_epistemic_source(
        project_id=project_id,
        source_type="document",
        title="My Doc",
        source_url="docs/my.md",
    )
    cursor = db.conn.cursor()
    # Exactly one row in epistemic_sources for this project
    count = cursor.execute(
        "SELECT COUNT(*) FROM epistemic_sources WHERE project_id = ?",
        (project_id,),
    ).fetchone()[0]
    assert count == 1
    assert source_id is not None
    # The single row has the user's source_type, NOT 'pointer'
    row_type = cursor.execute(
        "SELECT source_type FROM epistemic_sources WHERE id = ?",
        (source_id,),
    ).fetchone()[0]
    assert row_type == "document"


def test_reader_merges_new_writes_with_migrated_rows(db):
    """A mix of new writes (already in sources) + migrated legacy rows
    (after migration runs) all appear in one reader call."""
    project_id = db._test_project_id

    # New-style write
    db.add_reference_doc(project_id=project_id, doc_path="docs/new.md")

    # Legacy + migrate
    legacy_id = str(uuid.uuid4())
    db.conn.execute(
        """INSERT INTO project_reference_docs
           (id, project_id, doc_path, created_timestamp, doc_data)
           VALUES (?, ?, ?, ?, ?)""",
        (legacy_id, project_id, "docs/old.md", time.time(), "{}"),
    )
    db.conn.commit()
    migration_046_refdocs_to_sources(db.conn.cursor())
    db.conn.commit()

    docs = db.get_project_reference_docs(project_id)
    paths = {d["doc_path"] for d in docs}
    assert paths == {"docs/new.md", "docs/old.md"}
