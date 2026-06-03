"""Tests for _resolve_ai_id_for_session in session-init.py.

Surfaced by ecodex prop_vwmutw7nu: session-init.py:1246 hardcoded
ai_id = os.getenv('EMPIRICA_AI_ID', 'claude-code'), missing the
project.yaml ai_id field. Non-CC harnesses (codex/Kimi/ecodex-lab)
got silently stamped as 'claude-code' → wrong mesh identity →
silent delivery failure for cortex_propose(target=<practice>).

Fix wires the canonical resolution chain:
  1. EMPIRICA_AI_ID env (explicit override)
  2. project.yaml ai_id field (declared practitioner)
  3. basename(project_root) (canonical anchor, empirica- prefix kept)
  4. 'claude-code' + stderr warning (final fallback)
"""

from __future__ import annotations

import importlib.util
import io
import sys
from contextlib import redirect_stderr
from pathlib import Path

import yaml

HOOK_PATH = (
    Path(__file__).parent.parent
    / "empirica" / "plugins" / "claude-code-integration" / "hooks" / "session-init.py"
)
_spec = importlib.util.spec_from_file_location("session_init_resolve_ai_id", HOOK_PATH)
assert _spec is not None and _spec.loader is not None
session_init = importlib.util.module_from_spec(_spec)
sys.modules["session_init_resolve_ai_id"] = session_init
_spec.loader.exec_module(session_init)

_resolve = session_init._resolve_ai_id_for_session


def test_env_var_explicit_override_wins(tmp_path, monkeypatch):
    """EMPIRICA_AI_ID env always wins, even when project.yaml has a different value."""
    (tmp_path / ".empirica").mkdir()
    (tmp_path / ".empirica" / "project.yaml").write_text(
        yaml.dump({"ai_id": "from-yaml"})
    )
    monkeypatch.setenv("EMPIRICA_AI_ID", "from-env")
    assert _resolve(str(tmp_path)) == "from-env"


def test_project_yaml_ai_id_takes_precedence_over_basename(tmp_path, monkeypatch):
    """project.yaml ai_id beats basename derivation (declared practitioner wins)."""
    monkeypatch.delenv("EMPIRICA_AI_ID", raising=False)
    project = tmp_path / "some-random-folder-name"
    (project / ".empirica").mkdir(parents=True)
    (project / ".empirica" / "project.yaml").write_text(
        yaml.dump({"ai_id": "ecodex-lab"})
    )
    assert _resolve(str(project)) == "ecodex-lab"


def test_basename_fallback_when_no_yaml(tmp_path, monkeypatch):
    """No project.yaml → derive from basename (canonical, prefix kept)."""
    monkeypatch.delenv("EMPIRICA_AI_ID", raising=False)
    project = tmp_path / "empirica-mesh-support"
    project.mkdir()
    assert _resolve(str(project)) == "empirica-mesh-support"


def test_basename_keeps_empirica_prefix(tmp_path, monkeypatch):
    """1.11.x strict-canonical: empirica- prefix is preserved (NOT stripped)."""
    monkeypatch.delenv("EMPIRICA_AI_ID", raising=False)
    project = tmp_path / "empirica-cortex"
    project.mkdir()
    assert _resolve(str(project)) == "empirica-cortex"


def test_basename_non_empirica_project(tmp_path, monkeypatch):
    """Project without empirica- prefix → basename as-is."""
    monkeypatch.delenv("EMPIRICA_AI_ID", raising=False)
    project = tmp_path / "ecodex"
    project.mkdir()
    assert _resolve(str(project)) == "ecodex"


def test_empty_env_treated_as_unset(tmp_path, monkeypatch):
    """EMPIRICA_AI_ID='' is treated as unset (whitespace-only also)."""
    monkeypatch.setenv("EMPIRICA_AI_ID", "   ")
    project = tmp_path / "empirica-outreach"
    project.mkdir()
    assert _resolve(str(project)) == "empirica-outreach"


def test_yaml_without_ai_id_falls_through_to_basename(tmp_path, monkeypatch):
    """project.yaml exists but no ai_id field → fall through to basename."""
    monkeypatch.delenv("EMPIRICA_AI_ID", raising=False)
    project = tmp_path / "empirica-extension"
    (project / ".empirica").mkdir(parents=True)
    (project / ".empirica" / "project.yaml").write_text(
        yaml.dump({"name": "extension", "version": "2.0"})
    )
    assert _resolve(str(project)) == "empirica-extension"


def test_none_project_root_warns_and_returns_claude_code(monkeypatch):
    """No project_root + no env override → 'claude-code' with stderr warning."""
    monkeypatch.delenv("EMPIRICA_AI_ID", raising=False)
    buf = io.StringIO()
    with redirect_stderr(buf):
        result = _resolve(None)
    assert result == "claude-code"
    assert "misattribute" in buf.getvalue() or "claude-code" in buf.getvalue()


def test_malformed_yaml_warns_then_falls_through(tmp_path, monkeypatch):
    """Malformed project.yaml → warn, fall through to basename, no exception."""
    monkeypatch.delenv("EMPIRICA_AI_ID", raising=False)
    project = tmp_path / "empirica-autonomy"
    (project / ".empirica").mkdir(parents=True)
    (project / ".empirica" / "project.yaml").write_text("not: valid: yaml: [")
    buf = io.StringIO()
    with redirect_stderr(buf):
        result = _resolve(str(project))
    assert result == "empirica-autonomy"
    assert "yaml" in buf.getvalue().lower() or "fail" in buf.getvalue().lower()


def test_path_object_accepted(tmp_path, monkeypatch):
    """Accepts Path objects, not just strings."""
    monkeypatch.delenv("EMPIRICA_AI_ID", raising=False)
    project = tmp_path / "empirica-cortex"
    project.mkdir()
    assert _resolve(project) == "empirica-cortex"
