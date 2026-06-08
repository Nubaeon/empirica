"""Tests for the cortex-side participation checks (`empirica mesh diagnose --cortex`).

Closes cortex's prop_dd3epjwqyb ask. Read-only probes in v1:
identity, channels, listener subscription URL match, ntfy ACL, mesh
agreement (--peer only). Live wake test + inbox consistency deferred
to v2.
"""

from __future__ import annotations

import json
import urllib.error
from pathlib import Path
from unittest.mock import patch

from empirica.cli.command_handlers._mesh_diagnose_cortex import (
    aggregate_exit_code,
    check_channels_endpoint,
    check_identity,
    check_listener_subscription_matches,
    check_mesh_agreement,
    check_ntfy_acl,
    render_results_human,
    run_cortex_checks,
)

CORTEX_URL = "https://cortex.test"
API_KEY = "ctx_test_key"


# ── identity.roster_lookup ─────────────────────────────────────────────


def test_identity_passes_when_roster_has_ai_id():
    body = {
        "self": {"tenant_slug": "david"},
        "org": {"tenants": [{
            "tenant_slug": "david",
            "projects": [{
                "ai_id_short": "empirica-cortex",
                "ai_id_mesh": "empirica.david.empirica-cortex",
            }],
        }]},
    }
    with patch(
        "empirica.cli.command_handlers._mesh_diagnose_cortex._http_get_json",
        return_value=body,
    ):
        r = check_identity("empirica-cortex", CORTEX_URL, API_KEY)
    assert r.status == "pass"
    assert "empirica.david.empirica-cortex" in r.message
    assert r.details["canonical"] == "empirica.david.empirica-cortex"


def test_identity_fails_when_ai_id_not_in_roster():
    body = {
        "self": {"tenant_slug": "david"},
        "org": {"tenants": [{"tenant_slug": "david", "projects": []}]},
    }
    with patch(
        "empirica.cli.command_handlers._mesh_diagnose_cortex._http_get_json",
        return_value=body,
    ):
        r = check_identity("ghost-instance", CORTEX_URL, API_KEY)
    assert r.status == "fail"
    assert "ghost-instance" in r.message
    assert r.fix is not None


def test_identity_fails_on_http_error():
    err = urllib.error.HTTPError(CORTEX_URL, 401, "Unauthorized", {}, None)
    with patch(
        "empirica.cli.command_handlers._mesh_diagnose_cortex._http_get_json",
        side_effect=err,
    ):
        r = check_identity("empirica-cortex", CORTEX_URL, API_KEY)
    assert r.status == "fail"
    assert "roster fetch failed" in r.message


# ── channels.orchestration_events ─────────────────────────────────────


def test_channels_passes_per_tenant_topic():
    body = {
        "channels": [
            {"category": "orchestration_events",
             "topic": "empirica-orchestration-events-david"},
        ],
    }
    with patch(
        "empirica.cli.command_handlers._mesh_diagnose_cortex._http_get_json",
        return_value=body,
    ):
        r, topic = check_channels_endpoint(CORTEX_URL, API_KEY)
    assert r.status == "pass"
    assert topic == "empirica-orchestration-events-david"
    assert "per-tenant" in r.message


def test_channels_warns_on_bare_topic():
    body = {"channels": [{"category": "orchestration_events",
                          "topic": "orchestration-events"}]}
    with patch(
        "empirica.cli.command_handlers._mesh_diagnose_cortex._http_get_json",
        return_value=body,
    ):
        r, _ = check_channels_endpoint(CORTEX_URL, API_KEY)
    assert r.status == "warn"
    assert "BARE" in r.message


def test_channels_warns_on_per_org_topic():
    """Pre-T16/T17 per-org form (no -<tenant> suffix)."""
    body = {"channels": [{"category": "orchestration_events",
                          "topic": "empirica-orchestration-events"}]}
    with patch(
        "empirica.cli.command_handlers._mesh_diagnose_cortex._http_get_json",
        return_value=body,
    ):
        r, _ = check_channels_endpoint(CORTEX_URL, API_KEY)
    assert r.status == "warn"
    assert "PER-ORG" in r.message


def test_channels_fails_when_no_orchestration_channel():
    body = {"channels": [{"category": "system", "topic": "empirica-system"}]}
    with patch(
        "empirica.cli.command_handlers._mesh_diagnose_cortex._http_get_json",
        return_value=body,
    ):
        r, topic = check_channels_endpoint(CORTEX_URL, API_KEY)
    assert r.status == "fail"
    assert topic is None


# ── listener.subscription_match ───────────────────────────────────────


def test_subscription_match_passes_when_topics_align(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    (tmp_path / ".empirica").mkdir()
    (tmp_path / ".empirica" / "listener_active_x_x-inbox.json").write_text(json.dumps({
        "ai_id": "empirica-cortex",
        "topic": "ntfy:empirica-orchestration-events-david?tags=empirica.david.empirica-cortex",
    }))
    r = check_listener_subscription_matches(
        "empirica-cortex",
        "empirica-orchestration-events-david?tags=anything",
    )
    assert r.status == "pass"


def test_subscription_match_fails_on_topic_mismatch(tmp_path, monkeypatch):
    """Silent-strand: listener pinned to retired topic while cortex
    advertises a different one."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    (tmp_path / ".empirica").mkdir()
    (tmp_path / ".empirica" / "listener_active_x_x-inbox.json").write_text(json.dumps({
        "ai_id": "empirica-cortex",
        "topic": "ntfy:orchestration-events?tags=cortex",  # retired bare topic
    }))
    r = check_listener_subscription_matches(
        "empirica-cortex",
        "empirica-orchestration-events-david",
    )
    assert r.status == "fail"
    assert "silent-strand" in r.message
    assert r.details["mismatches"]


def test_subscription_match_warns_when_no_active_file(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    r = check_listener_subscription_matches(
        "empirica-cortex", "empirica-orchestration-events-david",
    )
    assert r.status == "warn"
    assert "not be armed" in r.message


def test_subscription_match_warns_when_no_expected_topic():
    r = check_listener_subscription_matches("empirica-cortex", None)
    assert r.status == "warn"


# ── ntfy.read_grant ───────────────────────────────────────────────────


def test_ntfy_acl_passes_on_200():
    with patch(
        "empirica.cli.command_handlers._mesh_diagnose_cortex._http_head",
        return_value=200,
    ):
        r = check_ntfy_acl(
            "empirica-orchestration-events-david",
            "https://ntfy.test", "tk_test",
        )
    assert r.status == "pass"


def test_ntfy_acl_fails_on_403():
    err = urllib.error.HTTPError(
        "https://ntfy.test/x", 403, "Forbidden", {}, None,
    )
    with patch(
        "empirica.cli.command_handlers._mesh_diagnose_cortex._http_head",
        side_effect=err,
    ):
        r = check_ntfy_acl(
            "empirica-orchestration-events-david",
            "https://ntfy.test", "tk_test",
        )
    assert r.status == "fail"
    assert "403" in r.message
    assert "READ grant" in r.message


def test_ntfy_acl_warns_on_other_http_error():
    err = urllib.error.HTTPError(
        "https://ntfy.test/x", 500, "Server Error", {}, None,
    )
    with patch(
        "empirica.cli.command_handlers._mesh_diagnose_cortex._http_head",
        side_effect=err,
    ):
        r = check_ntfy_acl("topic", "https://ntfy.test", "tk")
    assert r.status == "warn"


def test_ntfy_acl_warns_on_network_error():
    with patch(
        "empirica.cli.command_handlers._mesh_diagnose_cortex._http_head",
        side_effect=TimeoutError("timed out"),
    ):
        r = check_ntfy_acl("topic", "https://ntfy.test", "tk")
    assert r.status == "warn"


def test_ntfy_acl_warns_when_no_topic():
    r = check_ntfy_acl(None, "https://ntfy.test", "tk")
    assert r.status == "warn"


def test_ntfy_acl_warns_when_no_ntfy_url():
    r = check_ntfy_acl("topic", None, "tk")
    assert r.status == "warn"


# ── mesh.agreement ────────────────────────────────────────────────────


def test_mesh_agreement_passes_for_active_row():
    body = {"agreements": [{
        "source_practice": "empirica.david.empirica",
        "target_practice": "empirica.philipp.empirica-autonomy",
        "active": True,
    }]}
    with patch(
        "empirica.cli.command_handlers._mesh_diagnose_cortex._http_get_json",
        return_value=body,
    ):
        r = check_mesh_agreement(
            "empirica.philipp.empirica-autonomy", CORTEX_URL, API_KEY,
        )
    assert r.status == "pass"


def test_mesh_agreement_fails_when_no_active_row():
    body = {"agreements": []}
    with patch(
        "empirica.cli.command_handlers._mesh_diagnose_cortex._http_get_json",
        return_value=body,
    ):
        r = check_mesh_agreement("empirica.philipp.x", CORTEX_URL, API_KEY)
    assert r.status == "fail"
    assert "no active mesh_sharing_agreement" in r.message


# ── orchestration + render ────────────────────────────────────────────


def test_run_cortex_checks_executes_in_order(tmp_path, monkeypatch):
    """run_cortex_checks calls each probe; order matters because the
    channels probe yields the topic the others compare against."""
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    roster_body = {
        "self": {"tenant_slug": "david"},
        "org": {"tenants": [{
            "tenant_slug": "david",
            "projects": [{
                "ai_id_short": "empirica-cortex",
                "ai_id_mesh": "empirica.david.empirica-cortex",
            }],
        }]},
    }
    channels_body = {"channels": [{
        "category": "orchestration_events",
        "topic": "empirica-orchestration-events-david",
    }]}

    def _fake_get(url, **_kw):
        if "roster" in url:
            return roster_body
        if "notification-channels" in url:
            return channels_body
        return {}

    with patch(
        "empirica.cli.command_handlers._mesh_diagnose_cortex._http_get_json",
        side_effect=_fake_get,
    ), patch(
        "empirica.cli.command_handlers._mesh_diagnose_cortex._http_head",
        return_value=200,
    ):
        results = run_cortex_checks(
            "empirica-cortex", cortex_url=CORTEX_URL, api_key=API_KEY,
            ntfy_url="https://ntfy.test", ntfy_token="tk",  # noqa: S106
        )
    # 4 checks without --peer (no mesh.agreement)
    assert len(results) == 4
    assert [r.name for r in results] == [
        "identity.roster_lookup",
        "channels.orchestration_events",
        "listener.subscription_match",
        "ntfy.read_grant",
    ]


def test_aggregate_exit_code_fail_dominates():
    from empirica.cli.command_handlers._mesh_diagnose_cortex import CheckResult
    results = [
        CheckResult(name="a", status="pass", message="ok"),
        CheckResult(name="b", status="warn", message="meh"),
        CheckResult(name="c", status="fail", message="nope"),
    ]
    assert aggregate_exit_code(results) == 2


def test_aggregate_exit_code_warn_when_no_fail():
    from empirica.cli.command_handlers._mesh_diagnose_cortex import CheckResult
    results = [
        CheckResult(name="a", status="pass", message="ok"),
        CheckResult(name="b", status="warn", message="meh"),
    ]
    assert aggregate_exit_code(results) == 1


def test_aggregate_exit_code_zero_on_all_pass():
    from empirica.cli.command_handlers._mesh_diagnose_cortex import CheckResult
    results = [
        CheckResult(name="a", status="pass", message="ok"),
        CheckResult(name="b", status="pass", message="ok"),
    ]
    assert aggregate_exit_code(results) == 0


def test_render_human_shows_glyphs_and_fixes():
    from empirica.cli.command_handlers._mesh_diagnose_cortex import CheckResult
    results = [
        CheckResult(name="a.b", status="pass", message="ok"),
        CheckResult(name="x.y", status="fail", message="broken", fix="restart"),
    ]
    out = render_results_human(results)
    assert "✓" in out
    assert "✗" in out
    assert "a.b" in out
    assert "broken" in out
    assert "restart" in out
