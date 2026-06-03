"""Tests for _heal_project_yaml_ai_id_at_init — migrates stripped-prefix
legacy ai_id values to the canonical exact-basename form.

Post-strict-canonical (1.11.x): ai_id IS the exact project basename.
Legacy project.yamls had stripped form (e.g. `ai_id: extension` instead
of `ai_id: empirica-extension`). The heal runs idempotently at
session-init to migrate installed practices forward.

Goal e42e373e.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import yaml

# session-init.py isn't a package import; load it as a module
HOOK_PATH = (
    Path(__file__).parent.parent
    / "empirica" / "plugins" / "claude-code-integration" / "hooks" / "session-init.py"
)
_spec = importlib.util.spec_from_file_location("session_init_for_heal_test", HOOK_PATH)
assert _spec is not None and _spec.loader is not None
session_init = importlib.util.module_from_spec(_spec)
sys.modules["session_init_for_heal_test"] = session_init
_spec.loader.exec_module(session_init)

_heal = session_init._heal_project_yaml_ai_id_at_init


def _write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False))


def _read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {}


def test_heal_stripped_prefix_to_canonical(tmp_path):
    """ai_id='extension' in 'empirica-extension/' → heal to 'empirica-extension'."""
    project = tmp_path / "empirica-extension"
    yml = project / ".empirica" / "project.yaml"
    _write_yaml(yml, {"name": "extension", "ai_id": "extension"})

    _heal(str(project))

    assert _read_yaml(yml)["ai_id"] == "empirica-extension"


def test_already_canonical_is_noop(tmp_path):
    """ai_id == basename → no rewrite."""
    project = tmp_path / "empirica"
    yml = project / ".empirica" / "project.yaml"
    _write_yaml(yml, {"ai_id": "empirica", "name": "empirica"})
    mtime_before = yml.stat().st_mtime

    _heal(str(project))

    assert yml.stat().st_mtime == mtime_before
    assert _read_yaml(yml)["ai_id"] == "empirica"


def test_no_prefix_basename_noop(tmp_path):
    """Project without 'empirica-' prefix and ai_id matching basename → no-op."""
    project = tmp_path / "ecodex"
    yml = project / ".empirica" / "project.yaml"
    _write_yaml(yml, {"ai_id": "ecodex"})

    _heal(str(project))

    assert _read_yaml(yml)["ai_id"] == "ecodex"


def test_custom_provisioner_value_left_alone(tmp_path):
    """ai_id is neither basename nor stripped — assume custom, don't touch."""
    project = tmp_path / "empirica-mesh-support"
    yml = project / ".empirica" / "project.yaml"
    _write_yaml(yml, {"ai_id": "practitioner-uuid-abc-123"})

    _heal(str(project))

    # Untouched — heal must not second-guess custom provisioner values
    assert _read_yaml(yml)["ai_id"] == "practitioner-uuid-abc-123"


def test_absent_ai_id_left_alone(tmp_path):
    """ai_id field missing → no-op (project-init handles introduction)."""
    project = tmp_path / "empirica-cortex"
    yml = project / ".empirica" / "project.yaml"
    _write_yaml(yml, {"name": "cortex", "version": "2.0"})

    _heal(str(project))

    # ai_id stays absent — heal doesn't fabricate
    assert "ai_id" not in _read_yaml(yml)


def test_idempotent_double_run(tmp_path):
    """Run heal twice → second call is no-op (file unchanged after first heal)."""
    project = tmp_path / "empirica-outreach"
    yml = project / ".empirica" / "project.yaml"
    _write_yaml(yml, {"ai_id": "outreach"})

    _heal(str(project))
    mtime_after_first = yml.stat().st_mtime

    _heal(str(project))

    assert yml.stat().st_mtime == mtime_after_first
    assert _read_yaml(yml)["ai_id"] == "empirica-outreach"


def test_missing_project_yaml_no_error(tmp_path):
    """No project.yaml at the path → silent no-op, no exception."""
    project = tmp_path / "empirica-cortex"
    project.mkdir()

    _heal(str(project))  # should not raise


def test_none_project_root_no_error():
    """project_root=None → silent no-op."""
    _heal(None)  # should not raise


def test_malformed_yaml_no_error(tmp_path):
    """Malformed YAML → caught, logged, no exception escapes."""
    project = tmp_path / "empirica-broken"
    yml = project / ".empirica" / "project.yaml"
    yml.parent.mkdir(parents=True)
    yml.write_text("not: valid: yaml: [")

    _heal(str(project))  # should not raise


def test_preserves_other_yaml_keys(tmp_path):
    """Heal only touches ai_id — other keys preserved in order."""
    project = tmp_path / "empirica-extension"
    yml = project / ".empirica" / "project.yaml"
    _write_yaml(yml, {
        "version": "2.0",
        "name": "extension",
        "ai_id": "extension",
        "tags": ["mesh", "ui"],
        "domain": "ai/ui",
    })

    _heal(str(project))

    cfg = _read_yaml(yml)
    assert cfg["ai_id"] == "empirica-extension"
    assert cfg["version"] == "2.0"
    assert cfg["name"] == "extension"
    assert cfg["tags"] == ["mesh", "ui"]
    assert cfg["domain"] == "ai/ui"
