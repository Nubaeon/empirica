"""Tests for empirica.core.loop_scheduler.content_poll.

Content-aware tick body (T6, goal f718156c): replaces heartbeat ticks with
poll-Cortex-and-diff-against-last-seen so the AI only wakes on real
ECO-decided content. The fetch is injected via `fetch_fn` so tests can
exercise the diff + state-update logic without hitting a real Cortex.

Security property tested implicitly: only statuses in EMISSION_STATUSES
(accepted, changed, declined) produce events. eco_review proposals are
silently dropped — the AI must not act on ECO-undecided content.
"""

from __future__ import annotations

import json

from empirica.core.loop_scheduler.content_poll import (
    EMISSION_STATUSES,
    ProposalEvent,
    build_event,
    diff_proposals,
    load_state,
    poll_and_diff,
    save_state,
)

# ── EMISSION_STATUSES — the security/auth boundary ───────────────────────


def test_emission_statuses_excludes_eco_review():
    """ECO-undecided proposals must NOT wake the AI. The ECO-gated autonomy
    property requires that only ECO-reviewed states cross the wake boundary."""
    assert "eco_review" not in EMISSION_STATUSES
    assert "accepted" in EMISSION_STATUSES
    assert "changed" in EMISSION_STATUSES
    assert "declined" in EMISSION_STATUSES


# ── diff_proposals ───────────────────────────────────────────────────────


def test_diff_returns_all_new_when_state_empty():
    current = [
        {"id": "p1", "status": "accepted"},
        {"id": "p2", "status": "changed"},
    ]
    diffs = diff_proposals(current, {})
    assert len(diffs) == 2
    assert all(kind == "new" for _, kind in diffs)


def test_diff_skips_unchanged_proposals():
    current = [
        {"id": "p1", "status": "accepted"},
        {"id": "p2", "status": "changed"},
    ]
    last_seen = {"p1": "accepted", "p2": "changed"}
    assert diff_proposals(current, last_seen) == []


def test_diff_emits_only_status_change():
    current = [
        {"id": "p1", "status": "changed"},  # was accepted
        {"id": "p2", "status": "accepted"},  # unchanged
    ]
    last_seen = {"p1": "accepted", "p2": "accepted"}
    diffs = diff_proposals(current, last_seen)
    assert len(diffs) == 1
    assert diffs[0][0]["id"] == "p1"
    assert diffs[0][1] == "status_changed"


def test_diff_filters_out_eco_review_status():
    """Proposals still awaiting ECO decision must NOT emit — even if new."""
    current = [
        {"id": "p1", "status": "eco_review"},
        {"id": "p2", "status": "accepted"},
    ]
    diffs = diff_proposals(current, {})
    assert len(diffs) == 1
    assert diffs[0][0]["id"] == "p2"


def test_diff_handles_proposal_with_missing_id():
    """Malformed proposals (no id) are skipped, not crashed."""
    current = [
        {"id": "", "status": "accepted"},
        {"status": "accepted"},  # no id key at all
        {"id": "p_valid", "status": "accepted"},
    ]
    diffs = diff_proposals(current, {})
    assert len(diffs) == 1
    assert diffs[0][0]["id"] == "p_valid"


# ── State file IO ────────────────────────────────────────────────────────


def test_save_and_load_state_roundtrip(tmp_path):
    state_path = tmp_path / "state.json"
    state = {
        "last_poll_ts": "2026-05-15T20:00:00+00:00",
        "proposals": {"p1": {"status": "accepted", "seen_at": "2026-05-15T19:00:00Z"}},
    }
    save_state(state_path, state)
    loaded = load_state(state_path)
    assert loaded == state


def test_load_state_returns_empty_when_file_missing(tmp_path):
    assert load_state(tmp_path / "nonexistent.json") == {}


def test_load_state_returns_empty_on_malformed_file(tmp_path):
    state_path = tmp_path / "bad.json"
    state_path.write_text("not valid json {{{")
    assert load_state(state_path) == {}


def test_save_state_atomic_write(tmp_path):
    """save_state uses temp + rename so a crash mid-write doesn't poison
    the state file — there should be NO .tmp leftover after success."""
    state_path = tmp_path / "state.json"
    save_state(state_path, {"x": 1})
    assert state_path.exists()
    assert not (tmp_path / "state.json.tmp").exists()


# ── build_event ──────────────────────────────────────────────────────────


def test_build_event_extracts_eco_actor():
    proposal = {
        "id": "prop_abc",
        "title": "Test proposal",
        "status": "accepted",
        "action_category": "TACTICAL",
        "eco_decision": {"actor": "eco-phone", "decision": "accept"},
    }
    ev = build_event(proposal, "new", "cortex", "cortex-mailbox-poll")
    assert ev.proposal_id == "prop_abc"
    assert ev.proposal_title == "Test proposal"
    assert ev.status == "accepted"
    assert ev.eco_actor == "eco-phone"
    assert ev.action_category == "TACTICAL"
    assert ev.new_or_changed == "new"


def test_event_to_log_line_is_valid_json_with_required_fields():
    ev = ProposalEvent(
        instance_id="cortex",
        loop_name="cortex-mailbox-poll",
        proposal_id="prop_x",
        proposal_title="A title",
        status="accepted",
        action_category="TACTICAL",
        eco_actor="David",
        new_or_changed="new",
    )
    line = ev.to_log_line()
    parsed = json.loads(line)
    # Fields the Monitor + reaction protocol depend on
    assert parsed["event_type"] == "proposal_event"
    assert parsed["instance_id"] == "cortex"
    assert parsed["proposal_id"] == "prop_x"
    assert parsed["status"] == "accepted"
    assert parsed["change_kind"] == "new"
    assert "ts" in parsed


def test_build_event_truncates_long_titles():
    long_title = "x" * 500
    ev = build_event({"id": "p", "status": "accepted", "title": long_title}, "new", "i", "l")
    assert len(ev.proposal_title) <= 200


# ── poll_and_diff end-to-end ─────────────────────────────────────────────


def _empty_fetch(url, key, ai_id):
    return []


def test_first_run_records_state_without_emitting(tmp_path):
    """Bootstrap behavior: when state file doesn't exist yet, record current
    proposals as seen but emit NOTHING — avoids flooding the chat with
    historical inbox content when David first enables a loop."""
    state_path = tmp_path / "state.json"

    def fake_inbox(url, key, ai_id):
        return [
            {"id": "prop_old1", "status": "accepted"},
            {"id": "prop_old2", "status": "changed"},
        ]

    events = poll_and_diff("cortex", "cortex-mailbox-poll",
                           "https://cortex.test", "ctx_test",
                           state_path=state_path,
                           inbox_fetch_fn=fake_inbox,
                           outbox_fetch_fn=_empty_fetch)
    assert events == [], "first run must not emit historical content"

    state = load_state(state_path)
    assert state.get("bootstrap_completed") is True
    assert "prop_old1" in state["proposals"]
    assert "prop_old2" in state["proposals"]


def test_subsequent_run_emits_only_new_proposals(tmp_path):
    state_path = tmp_path / "state.json"

    def fetch_first(url, key, ai_id):
        return [
            {"id": "prop_a", "status": "accepted"},
            {"id": "prop_b", "status": "accepted"},
        ]
    poll_and_diff("cortex", "mailbox", "https://c.test", "k",
                  state_path=state_path,
                  inbox_fetch_fn=fetch_first, outbox_fetch_fn=_empty_fetch)

    def fetch_second(url, key, ai_id):
        return [
            {"id": "prop_a", "status": "accepted", "title": "A"},
            {"id": "prop_b", "status": "changed", "title": "B"},
            {"id": "prop_c", "status": "accepted", "title": "C"},
        ]
    events = poll_and_diff("cortex", "mailbox", "https://c.test", "k",
                            state_path=state_path,
                            inbox_fetch_fn=fetch_second, outbox_fetch_fn=_empty_fetch)

    by_id = {e.proposal_id: e for e in events}
    assert "prop_a" not in by_id
    assert by_id["prop_b"].new_or_changed == "status_changed"
    assert by_id["prop_c"].new_or_changed == "new"


def test_poll_returns_empty_when_both_endpoints_fail(tmp_path):
    """Both inbox + outbox down → emit nothing, don't update state."""
    import urllib.error
    state_path = tmp_path / "state.json"

    def failing(url, key, ai_id):
        raise urllib.error.URLError("network down")

    events = poll_and_diff("cortex", "mailbox", "https://c.test", "k",
                            state_path=state_path,
                            inbox_fetch_fn=failing, outbox_fetch_fn=failing)
    assert events == []
    assert not state_path.exists()


def test_partial_failure_one_endpoint_down_other_succeeds(tmp_path):
    """If inbox fails but outbox works (or vice versa), still proceed with
    the successful side. Don't punish the user for a partial outage."""
    import urllib.error
    state_path = tmp_path / "state.json"

    # Bootstrap first
    poll_and_diff("cortex", "mailbox", "https://c.test", "k",
                  state_path=state_path,
                  inbox_fetch_fn=_empty_fetch, outbox_fetch_fn=_empty_fetch)

    def failing_inbox(url, key, ai_id):
        raise urllib.error.URLError("inbox endpoint timeout")

    def working_outbox(url, key, ai_id):
        return [{
            "id": "prop_done", "status": "completed",
            "title": "My emission completed",
            "audit_log": [{"action": "completed", "details": {"commit_sha": "abc123"}}],
        }]

    events = poll_and_diff("cortex", "mailbox", "https://c.test", "k",
                            state_path=state_path,
                            inbox_fetch_fn=failing_inbox,
                            outbox_fetch_fn=working_outbox)
    assert len(events) == 1
    assert events[0].direction == "outbox"
    assert events[0].status == "completed"
    assert events[0].commit_sha == "abc123"


def test_eco_review_status_never_emits(tmp_path):
    """The ECO-gated autonomy property: ECO-undecided content must never
    appear in the fires log. Even though prop_pending is 'new', its
    eco_review status keeps it out of the emission."""
    state_path = tmp_path / "state.json"
    poll_and_diff("cortex", "mailbox", "https://c.test", "k",
                  state_path=state_path,
                  inbox_fetch_fn=_empty_fetch, outbox_fetch_fn=_empty_fetch)

    def fetch_pending_inbox(url, key, ai_id):
        return [
            {"id": "prop_pending", "status": "eco_review", "title": "Pending"},
            {"id": "prop_decided", "status": "accepted", "title": "Decided"},
        ]
    events = poll_and_diff("cortex", "mailbox", "https://c.test", "k",
                            state_path=state_path,
                            inbox_fetch_fn=fetch_pending_inbox,
                            outbox_fetch_fn=_empty_fetch)
    proposal_ids = [e.proposal_id for e in events]
    assert "prop_pending" not in proposal_ids
    assert "prop_decided" in proposal_ids


# ── Outbox / completion path (T7 — AI-to-AI ack wake signals) ────────────


def test_outbox_completed_event_carries_commit_sha(tmp_path):
    """David's completion primitive: the audit log's 'completed' entry has
    details.commit_sha. The event MUST surface it so the source AI knows
    which commit landed their work."""
    state_path = tmp_path / "state.json"
    # Bootstrap
    poll_and_diff("cortex", "mailbox", "https://c.test", "k",
                  state_path=state_path,
                  inbox_fetch_fn=_empty_fetch, outbox_fetch_fn=_empty_fetch)

    def outbox_with_completion(url, key, ai_id):
        return [{
            "id": "prop_ox66hmeipzesjjtbasjkqgbpsm",
            "status": "completed",
            "title": "Add completion primitive",
            "audit_log": [
                {"action": "created", "actor": "David"},
                {"action": "accepted", "actor": "eco-phone"},
                {"action": "completed", "actor": "extension",
                 "details": {"commit_sha": "66cda47"}},
            ],
        }]
    events = poll_and_diff("cortex", "mailbox", "https://c.test", "k",
                            state_path=state_path,
                            inbox_fetch_fn=_empty_fetch,
                            outbox_fetch_fn=outbox_with_completion)
    assert len(events) == 1
    ev = events[0]
    assert ev.direction == "outbox"
    assert ev.status == "completed"
    assert ev.commit_sha == "66cda47"
    # Log-line carries direction + commit_sha
    line = json.loads(ev.to_log_line())
    assert line["direction"] == "outbox"
    assert line["commit_sha"] == "66cda47"


def test_outbox_accepted_does_not_emit():
    """'accepted' on outbox = ECO approved YOUR emission. Target AI will act —
    no wake needed for the source AI. Must NOT cross emission boundary."""
    from empirica.core.loop_scheduler.content_poll import EMISSION_STATUSES_OUTBOX
    current = [{"id": "p1", "status": "accepted"}]
    outbox_diffs = diff_proposals(current, {}, valid_statuses=EMISSION_STATUSES_OUTBOX)
    assert outbox_diffs == [], "outbox 'accepted' is informational, must not emit"


def test_outbox_changed_emits_for_eco_refinement_request(tmp_path):
    """ECO sends a proposal back for refinement → outbox shows status=changed.
    The source AI must wake to emit a parent_id-linked refined proposal."""
    state_path = tmp_path / "state.json"
    poll_and_diff("cortex", "mailbox", "https://c.test", "k",
                  state_path=state_path,
                  inbox_fetch_fn=_empty_fetch, outbox_fetch_fn=_empty_fetch)

    def outbox_changed(url, key, ai_id):
        return [{"id": "prop_x", "status": "changed",
                 "title": "Needs refinement",
                 "eco_decision": {"actor": "David", "note": "tighten scope"}}]
    events = poll_and_diff("cortex", "mailbox", "https://c.test", "k",
                            state_path=state_path,
                            inbox_fetch_fn=_empty_fetch,
                            outbox_fetch_fn=outbox_changed)
    assert len(events) == 1
    assert events[0].status == "changed"
    assert events[0].direction == "outbox"
    assert events[0].eco_actor == "David"


def test_inbox_and_outbox_state_share_proposals_map(tmp_path):
    """UUIDs are globally unique, so a single proposals map covers both
    directions. Tracking includes the direction field so the AI can replay
    state from disk if needed."""
    state_path = tmp_path / "state.json"

    def inbox(url, key, ai_id):
        return [{"id": "in1", "status": "accepted"}]
    def outbox(url, key, ai_id):
        return [{"id": "out1", "status": "completed",
                 "audit_log": [{"action": "completed", "details": {"commit_sha": "deadbeef"}}]}]
    poll_and_diff("cortex", "mailbox", "https://c.test", "k",
                  state_path=state_path,
                  inbox_fetch_fn=inbox, outbox_fetch_fn=outbox)
    state = load_state(state_path)
    props = state["proposals"]
    assert "in1" in props and props["in1"]["direction"] == "inbox"
    assert "out1" in props and props["out1"]["direction"] == "outbox"
