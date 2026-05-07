"""Tests for per-project compliance.yaml config layer.

The config layer lets projects override compliance-report defaults via
.empirica/compliance.yaml — skip_checks, extra_checks, repo_hygiene
relaxations. Required so compliance-report works on non-empirica project
shapes (servers, libraries, services) without forcing the empirica-CLI
docs metric on every project.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from empirica.cli.command_handlers.compliance_report_commands import (
    _build_repo_hygiene_check,
    _load_compliance_config,
    _run_extra_check,
)

# ── _load_compliance_config ──────────────────────────────────────────────


def test_load_compliance_config_missing_returns_empty(tmp_path):
    assert _load_compliance_config(tmp_path) == {}


def test_load_compliance_config_reads_yaml(tmp_path):
    (tmp_path / ".empirica").mkdir()
    (tmp_path / ".empirica" / "compliance.yaml").write_text(yaml.safe_dump({
        "skip_checks": ["tech_docs"],
        "extra_checks": [{"id": "foo", "runner": "scripts/foo.py"}],
    }))
    cfg = _load_compliance_config(tmp_path)
    assert cfg["skip_checks"] == ["tech_docs"]
    assert cfg["extra_checks"][0]["id"] == "foo"


def test_load_compliance_config_malformed_returns_empty(tmp_path):
    (tmp_path / ".empirica").mkdir()
    (tmp_path / ".empirica" / "compliance.yaml").write_text("::: not valid yaml :::")
    assert _load_compliance_config(tmp_path) == {}


# ── _build_repo_hygiene_check overrides ─────────────────────────────────


def _bare_project(tmp_path: Path) -> Path:
    """Project with .gitignore + pyproject.toml only (license/changelog missing)."""
    (tmp_path / ".gitignore").write_text("*.pyc\n")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0.1.0"\n')
    return tmp_path


def test_repo_hygiene_default_fails_on_missing_license(tmp_path):
    proj = _bare_project(tmp_path)
    result = _build_repo_hygiene_check(proj)
    assert result["passed"] is False
    assert result["details"]["license"] == "MISSING"
    assert result["details"]["changelog"] == "MISSING"


def test_repo_hygiene_license_required_false_relaxes_check(tmp_path):
    proj = _bare_project(tmp_path)
    result = _build_repo_hygiene_check(proj, overrides={"license_required": False})
    assert result["details"]["license"] == "skipped"
    # license no longer counts toward total → checks_total drops by 1
    assert result["checks_total"] == 5


def test_repo_hygiene_all_optional_passes_with_minimal_project(tmp_path):
    proj = _bare_project(tmp_path)
    result = _build_repo_hygiene_check(proj, overrides={
        "license_required": False,
        "changelog_required": False,
        "release_scripts_required": False,
    })
    # Only gitignore + no_tracked_secrets + version_file remain — all present
    assert result["passed"] is True
    assert result["checks_total"] == 3


# ── _run_extra_check ────────────────────────────────────────────────────


def _make_runner(tmp_path: Path, body: str) -> Path:
    runner = tmp_path / "runner.py"
    runner.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        f"{body}\n"
    )
    runner.chmod(0o755)
    return runner


def test_run_extra_check_passes_through_runner_json(tmp_path):
    _make_runner(tmp_path, 'print(json.dumps({"passed": True, "score": 0.95, "extra": "metadata"}))')
    result = _run_extra_check(
        {"id": "my_check", "runner": str(tmp_path / "runner.py")},
        tmp_path,
    )
    assert result["check"] == "my_check"
    assert result["passed"] is True
    assert result["score"] == 0.95
    assert result["extra"] == "metadata"
    assert result["status"] == "pass"


def test_run_extra_check_fail_status(tmp_path):
    _make_runner(tmp_path, 'print(json.dumps({"passed": False}))')
    result = _run_extra_check(
        {"id": "my_check", "runner": str(tmp_path / "runner.py")},
        tmp_path,
    )
    assert result["passed"] is False
    assert result["status"] == "fail"


def test_run_extra_check_invalid_json_marks_fail(tmp_path):
    _make_runner(tmp_path, 'print("not json")')
    result = _run_extra_check(
        {"id": "my_check", "runner": str(tmp_path / "runner.py")},
        tmp_path,
    )
    assert result["passed"] is False
    assert "valid JSON" in result["error"]


def test_run_extra_check_missing_runner_returns_unavailable(tmp_path):
    result = _run_extra_check({"id": "my_check"}, tmp_path)
    assert result["status"] == "unavailable"


def test_run_extra_check_attaches_regulatory_mapping(tmp_path):
    _make_runner(tmp_path, 'print(json.dumps({"passed": True}))')
    result = _run_extra_check(
        {
            "id": "my_check",
            "runner": str(tmp_path / "runner.py"),
            "regulatory": {"eu_ai_act": {"article": "Art. 11", "requirement": "X"}},
        },
        tmp_path,
    )
    assert result["regulatory"]["eu_ai_act"]["article"] == "Art. 11"


def test_run_extra_check_attaches_description(tmp_path):
    _make_runner(tmp_path, 'print(json.dumps({"passed": True}))')
    result = _run_extra_check(
        {"id": "my_check", "runner": str(tmp_path / "runner.py"), "description": "Cortex prod /health"},
        tmp_path,
    )
    assert result["description"] == "Cortex prod /health"


# ── docpistemic integration ────────────────────────────────────────────


from unittest.mock import patch  # noqa: E402 — section-local import block

from empirica.cli.command_handlers.compliance_report_commands import (  # noqa: E402
    _docpistemic_available,
    _parse_docpistemic_result,
)


def _docpistemic_payload(coverage: float = 92.3, documented: int = 24, total: int = 26) -> str:
    import json as _json
    return _json.dumps({
        "project": "test",
        "epistemic": {
            "overall_coverage": coverage,
            "total_features": total,
            "documented_features": documented,
        },
        "categories": [
            {"name": "Core Modules", "total": 20, "documented": 20, "coverage": 100.0},
        ],
        "discovery": {},
    })


def test_parse_docpistemic_pass_above_70():
    raw = {
        "stdout": _docpistemic_payload(coverage=85.0, documented=17, total=20),
        "duration_seconds": 0.5,
        "passed": True,
    }
    out = _parse_docpistemic_result(raw)
    assert out["check"] == "tech_docs"
    assert out["tool"] == "docpistemic"
    assert out["passed"] is True
    assert out["coverage_percent"] == 85.0
    assert out["documented"] == 17
    assert out["total"] == 20
    assert out["status"] == "pass"


def test_parse_docpistemic_fail_below_70():
    raw = {"stdout": _docpistemic_payload(coverage=42.0), "duration_seconds": 0.3, "passed": True}
    out = _parse_docpistemic_result(raw)
    assert out["passed"] is False
    assert out["status"] == "fail"


def test_parse_docpistemic_invalid_json_returns_unavailable():
    raw = {"stdout": "not json", "duration_seconds": 0.1, "passed": True}
    out = _parse_docpistemic_result(raw)
    assert out["passed"] is None
    assert out["status"] == "unavailable"


def test_parse_docpistemic_propagates_runner_error():
    raw = {"error": "tool not installed"}
    out = _parse_docpistemic_result(raw)
    assert out["status"] == "unavailable"
    assert out["error"] == "tool not installed"


def test_docpistemic_available_returns_bool():
    # Don't depend on actual install — just verify the contract.
    with patch("shutil.which", return_value="/usr/local/bin/docpistemic"):
        assert _docpistemic_available() is True
    with patch("shutil.which", return_value=None):
        assert _docpistemic_available() is False


# ── _parse_docs_link_check_result ────────────────────────────────────────

from empirica.cli.command_handlers.compliance_report_commands import (  # noqa: E402
    _parse_docs_link_check_result,
)


def _link_check_payload(broken_total: int = 0, scanned: int = 100,
                         tier_1: int = 0, tier_2: int = 0, tier_3: int = 0) -> str:
    import json as _json
    return _json.dumps({
        "scanned_files": scanned,
        "broken_total": broken_total,
        "passed": broken_total == 0,
        "tiers": {
            "tier_1_top_readme": {"broken_total": tier_1, "files_with_breaks": 1 if tier_1 else 0, "files": []},
            "tier_2_folder_readmes": {"broken_total": tier_2, "files_with_breaks": 0, "files": []},
            "tier_3_other_md": {"broken_total": tier_3, "files_with_breaks": 0, "files": []},
        },
    })


def test_parse_docs_link_check_pass_when_zero_broken():
    raw = {"stdout": _link_check_payload(broken_total=0, scanned=226), "duration_seconds": 0.4, "passed": True}
    out = _parse_docs_link_check_result(raw)
    assert out["check"] == "tech_docs_links"
    assert out["tool"] == "empirica docs-link-check"
    assert out["passed"] is True
    assert out["status"] == "pass"
    assert out["scanned_files"] == 226
    assert out["broken_total"] == 0


def test_parse_docs_link_check_fail_when_any_broken():
    raw = {"stdout": _link_check_payload(broken_total=5, tier_2=2, tier_3=3),
           "duration_seconds": 0.5, "passed": False}
    out = _parse_docs_link_check_result(raw)
    assert out["passed"] is False
    assert out["status"] == "fail"
    assert out["broken_total"] == 5
    assert out["broken_in_top_readme"] == 0
    assert out["broken_in_folder_readmes"] == 2
    assert out["broken_in_other_md"] == 3


def test_parse_docs_link_check_surfaces_top_readme_breaks():
    """Tier 1 (top-level README) breaks should be counted distinctly —
    most user-visible failure mode worth flagging."""
    raw = {"stdout": _link_check_payload(broken_total=1, tier_1=1),
           "duration_seconds": 0.3, "passed": False}
    out = _parse_docs_link_check_result(raw)
    assert out["broken_in_top_readme"] == 1


def test_parse_docs_link_check_invalid_json_returns_unavailable():
    raw = {"stdout": "not json", "duration_seconds": 0.1, "passed": True}
    out = _parse_docs_link_check_result(raw)
    assert out["passed"] is None
    assert out["status"] == "unavailable"


def test_parse_docs_link_check_propagates_runner_error():
    raw = {"error": "empirica command not found"}
    out = _parse_docs_link_check_result(raw)
    assert out["status"] == "unavailable"
    assert out["error"] == "empirica command not found"


def test_tech_docs_links_in_regulatory_map():
    """The new check_id is registered in REGULATORY_MAP with EU AI Act + ISO 42001 mappings."""
    from empirica.cli.command_handlers.compliance_report_commands import REGULATORY_MAP
    assert "tech_docs_links" in REGULATORY_MAP
    assert "eu_ai_act" in REGULATORY_MAP["tech_docs_links"]["frameworks"]
    assert "iso_42001" in REGULATORY_MAP["tech_docs_links"]["frameworks"]
    # Different ISO clause from tech_docs (7.5.3 vs 7.5.1) — distinguishes
    # control-of-information from creation-and-updating.
    assert REGULATORY_MAP["tech_docs_links"]["frameworks"]["iso_42001"]["clause"] == "7.5.3"
