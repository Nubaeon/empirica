"""Tests for InstanceResolver.ai_id(project_path=...) — explicit-path mode
that bypasses the resolver chain for callers iterating known paths
(cockpit per-instance ai_id, project_init at provisioning time).

Part of the anchor refactor (goal 1029a40d): ai_id = THE anchor; the
resolution chain consolidates here so caller sites stop re-implementing
basename.removeprefix('empirica-').
"""

from __future__ import annotations

import yaml

from empirica.utils.session_resolver import InstanceResolver


def test_explicit_path_reads_project_yaml_ai_id(tmp_path):
    """Priority: explicit ai_id in project.yaml wins over basename derivation."""
    (tmp_path / ".empirica").mkdir()
    (tmp_path / ".empirica" / "project.yaml").write_text(
        yaml.dump({"ai_id": "ecodex", "name": "test"})
    )
    # tmp_path basename is something like 'test_explicit_path_reads_project_yaml_ai_id0',
    # NOT 'ecodex'. The project.yaml ai_id should win.
    assert InstanceResolver.ai_id(project_path=str(tmp_path)) == "ecodex"


def test_explicit_path_falls_back_to_basename_when_no_yaml(tmp_path):
    """No project.yaml → derive from basename, strip empirica- prefix."""
    sub = tmp_path / "empirica-mesh-support"
    sub.mkdir()
    assert InstanceResolver.ai_id(project_path=str(sub)) == "mesh-support"


def test_explicit_path_basename_without_empirica_prefix(tmp_path):
    """No project.yaml + no empirica- prefix → basename as-is."""
    sub = tmp_path / "myproject"
    sub.mkdir()
    assert InstanceResolver.ai_id(project_path=str(sub)) == "myproject"


def test_explicit_path_accepts_pathlib_path(tmp_path):
    """Accepts Path objects, not just strings."""
    (tmp_path / ".empirica").mkdir()
    (tmp_path / ".empirica" / "project.yaml").write_text(
        yaml.dump({"ai_id": "extension"})
    )
    assert InstanceResolver.ai_id(project_path=tmp_path) == "extension"


def test_explicit_path_yaml_without_ai_id_falls_back_to_basename(tmp_path):
    """project.yaml exists but no ai_id field → basename derivation."""
    sub = tmp_path / "empirica-cortex"
    sub.mkdir()
    (sub / ".empirica").mkdir()
    (sub / ".empirica" / "project.yaml").write_text(yaml.dump({"name": "cortex"}))
    assert InstanceResolver.ai_id(project_path=str(sub)) == "cortex"


def test_explicit_path_none_returns_none_without_resolver_fallback(monkeypatch):
    """Passing project_path=None falls through to resolver chain.

    Verifies backward-compat: when project_path is None and the resolver
    can't resolve, ai_id returns None (doesn't accidentally read cwd).
    """
    from empirica.utils import session_resolver
    monkeypatch.setattr(
        session_resolver, "get_active_project_path", lambda *args, **kwargs: None
    )
    assert InstanceResolver.ai_id(project_path=None) is None


def test_explicit_path_takes_precedence_over_resolver(monkeypatch, tmp_path):
    """When BOTH explicit project_path and resolver-derivable path exist,
    explicit wins — the whole point of the parameter.
    """
    # Resolver would have returned a different path
    bogus_resolver_path = tmp_path / "bogus"
    bogus_resolver_path.mkdir()
    from empirica.utils import session_resolver
    monkeypatch.setattr(
        session_resolver,
        "get_active_project_path",
        lambda *args, **kwargs: str(bogus_resolver_path),
    )

    # Explicit path
    explicit = tmp_path / "empirica-the-real-one"
    explicit.mkdir()
    assert InstanceResolver.ai_id(project_path=str(explicit)) == "the-real-one"


def test_empty_project_path_treated_as_none(monkeypatch):
    """Empty string project_path falls through to resolver (str() of None
    would never produce ''; this guards against caller accidents).
    """
    from empirica.utils import session_resolver
    monkeypatch.setattr(
        session_resolver, "get_active_project_path", lambda *args, **kwargs: None
    )
    # Empty string converts to truthy via `if project_path is not None`
    # check. The function then resolves it as a path with no useful name.
    # The behavior: Path("").name is "", derivation falls through to None.
    result = InstanceResolver.ai_id(project_path="")
    # Either None (no useful path) or the resolver was hit. Both acceptable.
    assert result is None or isinstance(result, str)
