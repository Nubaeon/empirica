"""Tests for empirica-mcp's command-building helpers.

Covers the three pure helpers extracted from `call_tool()` in v1.9.3:
- _build_cli_command — argv + stdin assembly per TOOL_REGISTRY entry shape
- _resolve_cwd — project_path arg → env var → session_resolver fallback chain
- _err_text — JSON-wrap-as-TextContent error helper
"""

from __future__ import annotations

import json
from unittest.mock import patch

import mcp.types as types
from empirica_mcp.server import (
    EMPIRICA_CLI,
    _build_cli_command,
    _err_text,
    _resolve_cwd,
)

# ─── _build_cli_command ────────────────────────────────────────────────


def test_stdin_json_entry_sends_full_payload():
    """stdin_json entries (CASCADE, lesson-create) pipe JSON via -."""
    entry = {"cli": "submit-cascade", "stdin_json": True, "params": {}, "required": []}
    args = {"session_id": "abc", "vectors": {"know": 0.7}}

    cmd, stdin = _build_cli_command(entry, args)

    assert cmd == [EMPIRICA_CLI, "submit-cascade", "--output", "json", "-"]
    assert stdin is not None
    assert json.loads(stdin) == args


def test_standard_entry_maps_params_to_flags():
    """Standard entries map argument keys to CLI --flags from entry['params']."""
    entry = {
        "cli": "finding-log",
        "params": {"finding": "--finding", "impact": "--impact"},
        "required": ["finding"],
    }
    args = {"finding": "test discovery", "impact": 0.7}

    cmd, stdin = _build_cli_command(entry, args)

    assert stdin is None
    assert "--finding" in cmd
    assert "test discovery" in cmd
    assert "--impact" in cmd
    assert "0.7" in cmd


def test_positional_argument_pops_from_args():
    """Entries with 'positional' consume the named arg as a bare CLI arg."""
    entry = {
        "cli": "investigate",
        "positional": "query",
        "params": {"limit": "--limit"},
        "required": ["query"],
    }
    args = {"query": "auth flow", "limit": 5}

    cmd, _ = _build_cli_command(entry, args)

    # Positional comes right after `--output json`
    output_idx = cmd.index("json")
    assert cmd[output_idx + 1] == "auth flow"
    # And it's NOT in arguments anymore (popped)
    assert "query" not in args
    # --limit pair is still there
    assert "--limit" in cmd and "5" in cmd


def test_list_params_repeat_the_flag():
    """list_params get the flag repeated per item: --source A --source B."""
    entry = {
        "cli": "log-graph",
        "params": {"source": "--source"},
        "list_params": ["source"],
        "required": [],
    }
    args = {"source": ["id-1", "id-2", "id-3"]}

    cmd, _ = _build_cli_command(entry, args)

    # Flag should appear 3 times, paired with each item
    flag_positions = [i for i, x in enumerate(cmd) if x == "--source"]
    assert len(flag_positions) == 3
    values = [cmd[i + 1] for i in flag_positions]
    assert values == ["id-1", "id-2", "id-3"]


def test_bool_true_emits_bare_flag():
    """Boolean params: True emits the flag alone, no value."""
    entry = {
        "cli": "scan",
        "params": {"grounded": "--grounded"},
        "required": [],
    }
    args = {"grounded": True}

    cmd, _ = _build_cli_command(entry, args)
    assert "--grounded" in cmd
    # The next element shouldn't be "True" (the bool value)
    grounded_idx = cmd.index("--grounded")
    assert grounded_idx == len(cmd) - 1 or cmd[grounded_idx + 1] != "True"


def test_bool_false_omits_flag():
    """Boolean params: False means the flag is NOT emitted at all."""
    entry = {
        "cli": "scan",
        "params": {"grounded": "--grounded"},
        "required": [],
    }
    args = {"grounded": False}

    cmd, _ = _build_cli_command(entry, args)
    assert "--grounded" not in cmd


def test_none_value_skipped():
    """Params with None values are skipped (not emitted as `--flag None`)."""
    entry = {
        "cli": "finding-log",
        "params": {"finding": "--finding", "impact": "--impact"},
        "required": ["finding"],
    }
    args = {"finding": "test", "impact": None}

    cmd, _ = _build_cli_command(entry, args)
    assert "--impact" not in cmd
    assert "--finding" in cmd


# ─── _resolve_cwd ──────────────────────────────────────────────────────


def test_explicit_project_path_wins(monkeypatch):
    """Explicit project_path arg beats env var and session_resolver."""
    monkeypatch.setenv("EMPIRICA_WORKSPACE_ROOT", "/from/env")
    assert _resolve_cwd({"project_path": "/explicit"}) == "/explicit"


def test_env_var_used_when_no_explicit(monkeypatch):
    """$EMPIRICA_WORKSPACE_ROOT is the second-tier fallback."""
    monkeypatch.setenv("EMPIRICA_WORKSPACE_ROOT", "/from/env")
    monkeypatch.delenv("PWD", raising=False)
    # Mock session_resolver so it can't interfere
    with patch("empirica.utils.session_resolver.get_active_project_path", return_value="/from/resolver"):
        assert _resolve_cwd({}) == "/from/env"


def test_session_resolver_fallback(monkeypatch):
    """Falls through to session_resolver.get_active_project_path() last."""
    monkeypatch.delenv("EMPIRICA_WORKSPACE_ROOT", raising=False)
    with patch("empirica.utils.session_resolver.get_active_project_path", return_value="/resolved"):
        assert _resolve_cwd({}) == "/resolved"


def test_returns_none_when_all_sources_empty(monkeypatch):
    """All sources empty → None (caller passes None to subprocess.run.cwd)."""
    monkeypatch.delenv("EMPIRICA_WORKSPACE_ROOT", raising=False)
    with patch(
        "empirica.utils.session_resolver.get_active_project_path",
        side_effect=Exception("boom"),
    ):
        assert _resolve_cwd({}) is None


# ─── _err_text ─────────────────────────────────────────────────────────


def test_err_text_returns_single_textcontent():
    """_err_text wraps a dict as exactly one TextContent element."""
    result = _err_text({"ok": False, "error": "oops"})

    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], types.TextContent)
    assert result[0].type == "text"

    payload = json.loads(result[0].text)
    assert payload == {"ok": False, "error": "oops"}


def test_err_text_handles_nested_payload():
    """Nested structures (lists, dicts) round-trip through JSON."""
    result = _err_text({
        "ok": False,
        "error": "Unknown tool",
        "available": ["a", "b", "c"],
        "meta": {"count": 3},
    })
    payload = json.loads(result[0].text)
    assert payload["available"] == ["a", "b", "c"]
    assert payload["meta"]["count"] == 3
