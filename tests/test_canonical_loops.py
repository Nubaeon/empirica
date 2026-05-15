"""Tests for the system-level canonical loop catalog.

The catalog backs the TUI cockpit's auto-install fallback: when an
instance has no loops registered AND no project.yaml cockpit.loops
block, the cockpit falls back to CANONICAL_LOOPS to install a sane
default set.
"""

from __future__ import annotations

import pytest

from empirica.core.cockpit.canonical_loops import (
    CANONICAL_LOOPS,
    canonical_loop_by_name,
    canonical_loop_names,
)


def test_catalog_is_non_empty():
    """The catalog must ship at least one entry — empty defeats its
    purpose (the TUI would just fall through to the CLI hint)."""
    assert len(CANONICAL_LOOPS) > 0


def test_every_entry_has_required_fields():
    """Each entry must satisfy the loop-install-request schema:
    name + kind + (cron OR interval) + description."""
    for entry in CANONICAL_LOOPS:
        assert isinstance(entry, dict)
        assert entry.get('name'), f"missing name in {entry}"
        assert entry.get('kind') in {'interval', 'cron', 'monitor'}, \
            f"invalid kind in {entry}"
        # Must have either cron or interval (depending on kind)
        has_schedule = bool(entry.get('cron') or entry.get('interval'))
        assert has_schedule, f"no schedule (cron or interval) in {entry}"
        assert isinstance(entry.get('description'), str), \
            f"missing/non-string description in {entry}"


def test_adaptive_entries_have_backoff_floor_and_ceiling():
    """Interval entries that ship with backoff must declare both
    base_interval and max_interval so the decay is bounded both ways."""
    for entry in CANONICAL_LOOPS:
        has_base = bool(entry.get('base_interval'))
        has_max = bool(entry.get('max_interval'))
        # Either neither (no backoff) or both (bounded backoff) — not one
        # without the other.
        assert has_base == has_max, (
            f"{entry.get('name')} has half-specified backoff "
            f"(base={has_base}, max={has_max})"
        )


def test_names_are_unique():
    """Two entries with the same name would collide on install — the
    second would either overwrite the first silently or fail."""
    names = [e.get('name') for e in CANONICAL_LOOPS]
    assert len(names) == len(set(names)), \
        f"duplicate names in catalog: {names}"


def test_canonical_loop_names_returns_all_names():
    assert canonical_loop_names() == [e['name'] for e in CANONICAL_LOOPS]


def test_canonical_loop_by_name_hit():
    """Roundtrip: pull a known entry by its name."""
    name = CANONICAL_LOOPS[0]['name']
    entry = canonical_loop_by_name(name)
    assert entry is not None
    assert entry['name'] == name


def test_canonical_loop_by_name_miss():
    """Unknown name returns None — never raises."""
    assert canonical_loop_by_name('not-a-real-loop-zzz9') is None


def test_cortex_mailbox_poll_preset_present():
    """The orchestration spine ships in the catalog. If we remove it,
    that's a deliberate decision — failing this test forces the
    decision to be conscious."""
    entry = canonical_loop_by_name('cortex-mailbox-poll')
    assert entry is not None, (
        "cortex-mailbox-poll is the orchestration spine — if you "
        "removed it, log a decision-log explaining why"
    )
    # Adaptive cadence is the whole point — fast base, idle ceiling
    assert entry['base_interval']
    assert entry['max_interval']
    # 30s base is intentional — David's requirement: must be faster
    # than 15m for true interactive work
    assert entry['base_interval'] == '30s'


@pytest.fixture
def fake_project_no_yaml(tmp_path):
    """A project path with no .empirica/project.yaml — triggers the
    canonical catalog fallback when used with project_loops."""
    return tmp_path / 'fake_project'


def test_fallback_path_returns_canonical_when_project_has_none(fake_project_no_yaml):
    """The integration-shaped check: project_loops() returns [] for an
    empty project, which is the trigger condition for the canonical
    fallback in _install_loops_from_project."""
    from empirica.core.cockpit.project_cockpit_config import project_loops
    assert project_loops(fake_project_no_yaml) == []
    # CANONICAL_LOOPS is the fallback the TUI uses when this returns []
    assert len(CANONICAL_LOOPS) > 0


def test_cortex_mailbox_poll_uses_systemd_scheduler():
    """Phase 1c (goal f718156c): cortex-mailbox-poll is the pilot loop for
    the systemd scheduler path. The TUI's _install_loops_from_project +
    action_toggle_loops dispatch on this field. Removing it reverts the
    pilot to the legacy CronCreate path — log a decision if you do so."""
    entry = canonical_loop_by_name('cortex-mailbox-poll')
    assert entry is not None
    assert entry.get('scheduler_kind') == 'systemd', (
        "cortex-mailbox-poll must carry scheduler_kind='systemd' so the TUI "
        "routes through systemctl rather than CronCreate"
    )
