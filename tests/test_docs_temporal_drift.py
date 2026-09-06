"""Docs age out silently. This makes ageing require a DECISION, not a fix.

A doc cannot be checked for correctness by a test — that needs reading and
judgment. What a test CAN do is refuse to let drift accumulate unnoticed: past a
threshold, every doc must be in one of three states, and all three are deliberate

    FRESH       edited recently — nothing to decide
    ARCHIVED    under an `_archive/` path — the decision was "this is history"
    ACKNOWLEDGED listed in the registry with a reason and who decided

The registry is the point. It is not an ignore-list: each entry records WHY a
stale doc is still current, so a reader can disagree with the judgment. An
ignore-list hides the decision; this one publishes it.

**Archiving is usually the right move.** A doc that no longer describes the
system is worse than no doc, because it is discoverable and confident. Reach for
the registry only when the content is genuinely still true and simply has not
needed editing.

**When a stale doc must be brought current, read-then-WRITE the whole file** —
an edit keeps the old structure and strands every reference to what it changed.
Atomic edits are for specific known changes (a renamed flag, a moved path), not
for reconciling a drifted document.

Scope note: only git-TRACKED markdown counts. An earlier pass over `**/*.md`
found 1,711 files and reported 1,520 as untracked — 1,288 of those were
generated `.empirica/` artifacts and `build/` output. Measuring documentation
drift over generated output would have inflated the surface eightfold.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs" / "acknowledged-stale.json"

#: Past this, a doc must be fresh, archived, or acknowledged. Deliberately
#: generous: the goal is to catch abandonment, not to churn stable references.
STALE_DAYS = 180
DAY = 86400


def _tracked_markdown() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    return [ROOT / p for p in out]


def _last_commit_epoch(rel: str) -> int:
    r = subprocess.run(["git", "log", "-1", "--format=%ct", "--", rel], cwd=ROOT, capture_output=True, text=True)
    return int(r.stdout.strip() or 0)


def _head_epoch() -> int:
    return int(
        subprocess.run(["git", "log", "-1", "--format=%ct"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    )


def _registry() -> dict:
    if not REGISTRY.exists():
        return {}
    return json.loads(REGISTRY.read_text()).get("acknowledged", {})


def _is_archived(rel: str) -> bool:
    return "_archive/" in rel or rel.startswith("_archive")


def test_every_stale_doc_is_archived_or_ACKNOWLEDGED():
    """The gate. A doc past the threshold with no recorded decision fails here.

    The remedy is never "touch the file to reset the clock" — it is to decide:
    archive it, bring it current (read-then-write), or record why it is still
    true. All three are cheap; none is silent.
    """
    head = _head_epoch()
    acknowledged = _registry()
    unhandled = []
    for path in _tracked_markdown():
        rel = str(path.relative_to(ROOT))
        if rel == "CHANGELOG.md" or _is_archived(rel):
            continue
        ts = _last_commit_epoch(rel)
        if not ts:
            continue
        age = (head - ts) / DAY
        if age > STALE_DAYS and rel not in acknowledged:
            unhandled.append(f"{rel} ({age:.0f}d)")
    assert not unhandled, (
        f"{len(unhandled)} doc(s) older than {STALE_DAYS} days with no recorded decision.\n  "
        + "\n  ".join(sorted(unhandled))
        + f"\n\nArchive them (usually right), bring them current (read-then-WRITE the whole "
        f"file, not an edit), or add an entry to {REGISTRY.relative_to(ROOT)} saying why the "
        f"content is still true. Touching the file to reset the clock is not one of the three."
    )


def test_the_registry_records_a_REASON_not_just_a_path():
    """An entry without a reason is an ignore-list line wearing a decision's clothes."""
    for rel, entry in _registry().items():
        assert isinstance(entry, dict), f"{rel}: entry must be an object with a reason"
        reason = (entry.get("reason") or "").strip()
        assert len(reason) > 30, (
            f"{rel}: reason is {len(reason)} chars. Say why the content is STILL TRUE despite "
            "its age — 'still accurate' is not a reason, it is the claim being made."
        )
        assert entry.get("decided_by"), f"{rel}: record who decided, so it can be questioned"
        assert entry.get("status") in ("verified_current", "pending_review"), (
            f"{rel}: status must be `verified_current` (someone READ it and it is true) or "
            "`pending_review` (its subject still exists but nobody has read it yet). Conflating "
            "the two is how an unread doc becomes an endorsed one."
        )


def test_a_pending_review_entry_carries_a_DEADLINE_and_it_has_not_passed():
    """`pending_review` is a deferral, and a deferral without a clock is a decision
    never to look.

    This is the state that keeps the registry honest when a triage cannot be
    finished: the entry says plainly that nobody has read the document, and the
    deadline turns silence into a failing test rather than permanent quiet.
    """
    import datetime as _dt

    today = _dt.date.today().isoformat()
    overdue = []
    for rel, entry in _registry().items():
        if entry.get("status") != "pending_review":
            continue
        by = entry.get("review_by")
        assert by, f"{rel}: pending_review must carry `review_by` (YYYY-MM-DD)"
        if by < today:
            overdue.append(f"{rel} (was due {by})")
    assert not overdue, (
        "pending_review deadlines have passed — READ these and either archive them, "
        "rewrite them whole, or flip to verified_current with what you checked:\n  " + "\n  ".join(sorted(overdue))
    )


def test_the_registry_has_no_entries_for_docs_that_are_FRESH_or_GONE():
    """A registry that outlives its subjects becomes noise nobody prunes.

    An entry for a file that is now fresh, archived, or deleted is a decision
    about a situation that no longer exists.
    """
    head = _head_epoch()
    stale_entries = []
    for rel in _registry():
        path = ROOT / rel
        if not path.exists():
            stale_entries.append(f"{rel} (file no longer exists)")
            continue
        ts = _last_commit_epoch(rel)
        if ts and (head - ts) / DAY <= STALE_DAYS:
            stale_entries.append(f"{rel} (now fresh — drop the entry)")
    assert not stale_entries, "registry entries that no longer describe anything:\n  " + "\n  ".join(stale_entries)


def test_the_threshold_actually_bites():
    """Positive control.

    The three tests above all pass trivially against an empty corpus, a broken
    `git ls-files`, or a threshold nothing can exceed. Assert the instrument is
    live: real tracked docs exist, and some are old enough that the gate is doing
    work rather than being vacuously satisfied.
    """
    docs = _tracked_markdown()
    assert len(docs) > 50, f"only {len(docs)} tracked markdown files — is git ls-files working?"

    head = _head_epoch()
    ages = sorted(((head - _last_commit_epoch(str(p.relative_to(ROOT)))) / DAY) for p in docs[:200])
    assert ages, "no ages computed — the clock is dead and every absence proves nothing"
    assert max(ages) > 30, "no doc is even 30 days old; the threshold cannot be exercised"


@pytest.mark.parametrize(
    "bad",
    [
        {"reason": "still accurate", "decided_by": "x", "status": "verified_current"},
        {"decided_by": "x", "status": "verified_current"},
        {"reason": "a" * 40, "decided_by": "x"},
        {"reason": "a" * 40, "decided_by": "x", "status": "probably_fine"},
    ],
)
def test_a_THIN_or_UNTYPED_entry_is_REJECTED(bad, monkeypatch):
    """Control for the reason check: it must REJECT as well as accept.

    Without this the reason gate would pass against a validator that checked
    nothing, and the registry would silently become an ignore-list.
    """
    import sys

    mod = sys.modules[__name__]
    monkeypatch.setattr(mod, "_registry", lambda: {"docs/x.md": bad})
    with pytest.raises(AssertionError):
        mod.test_the_registry_records_a_REASON_not_just_a_path()


def test_an_OVERDUE_pending_review_is_REJECTED(monkeypatch):
    """Control for the deadline: a passed date must fail, or the clock is decorative."""
    import sys

    mod = sys.modules[__name__]
    monkeypatch.setattr(
        mod,
        "_registry",
        lambda: {
            "docs/x.md": {
                "status": "pending_review",
                "reason": "x" * 40,
                "decided_by": "y",
                "review_by": "2020-01-01",
            }
        },
    )
    with pytest.raises(AssertionError):
        mod.test_a_pending_review_entry_carries_a_DEADLINE_and_it_has_not_passed()
