"""Tests for empirica.core.noetic_batch.executor."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from empirica.core.noetic_batch import run_batch
from empirica.core.noetic_batch.budgets import BatchBudgets


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A small fake project tree for batch operations."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "auth.py").write_text(
        "def login():\n    pass\n\ndef logout():\n    pass\n"
    )
    (tmp_path / "src" / "middleware.py").write_text(
        "from auth import login\n\n@decorator\ndef wrap():\n    pass\n"
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_auth.py").write_text(
        "def test_login():\n    assert True\n"
    )
    (tmp_path / "README.md").write_text("# Project\n")
    return tmp_path


# =============================================================================
# Read
# =============================================================================


def test_read_full_file(project):
    result = run_batch(
        {"intent": "read auth", "reads": [{"path": "src/auth.py"}]},
        project_root=project,
    )
    assert result.ok
    assert len(result.reads) == 1
    r = result.reads[0]
    assert "def login()" in r.content
    assert r.error is None
    assert r.truncated is False


def test_read_missing_file_per_op_error(project):
    result = run_batch(
        {"intent": "x", "reads": [{"path": "src/nonexistent.py"}]},
        project_root=project,
    )
    assert result.ok  # batch is ok; per-op has error
    assert "not found" in result.reads[0].error


def test_read_line_range(project):
    result = run_batch(
        {"intent": "x", "reads": [{"path": "src/auth.py", "lines": "1-2"}]},
        project_root=project,
    )
    r = result.reads[0]
    assert r.error is None
    assert "def login()" in r.content
    assert "logout" not in r.content


def test_read_byte_cap_truncates(project):
    big = project / "big.txt"
    big.write_text("x" * 1000)
    result = run_batch(
        {"intent": "x", "reads": [{"path": "big.txt"}]},
        project_root=project,
        budgets=BatchBudgets(max_file_bytes=100),
    )
    r = result.reads[0]
    assert r.truncated is True
    assert r.size_bytes <= 100


# =============================================================================
# Grep
# =============================================================================


def test_grep_finds_matches(project):
    result = run_batch(
        {"intent": "x", "greps": [{"pattern": "decorator", "glob": "src/**/*.py"}]},
        project_root=project,
    )
    g = result.greps[0]
    assert g.error is None
    assert g.total_matches >= 1
    assert any("middleware.py" in m.file for m in g.matches)


def test_grep_max_matches_cap(project):
    # 5 lines all matching
    (project / "many.py").write_text("\n".join(f"hit {i}" for i in range(20)))
    result = run_batch(
        {
            "intent": "x",
            "greps": [{"pattern": "hit", "glob": "many.py", "max_matches": 3}],
        },
        project_root=project,
    )
    g = result.greps[0]
    assert g.total_matches == 3
    assert g.truncated is True


def test_grep_invalid_regex_per_op_error(project):
    """Pure-Python path catches regex errors. ripgrep returns no matches for unparseable regex."""
    import shutil
    has_rg = shutil.which("rg") is not None

    result = run_batch(
        {"intent": "x", "greps": [{"pattern": "[unclosed"}]},
        project_root=project,
    )
    g = result.greps[0]
    if has_rg:
        # ripgrep silently returns no matches for invalid regex; that's still graceful
        assert g.total_matches == 0
    else:
        assert g.error is not None and "regex" in g.error.lower()


def test_grep_per_op_root_overrides_project(project, tmp_path):
    """A grep with `root` set scopes to that directory, not project_root.

    Regression: previously, greps were hardcoded to project_root with no
    per-op override, breaking cross-project investigation from a different CWD.
    """
    other = tmp_path / "other_project"
    other.mkdir()
    (other / "marker.py").write_text("def UNIQUE_GREP_MARKER(): pass\n")

    # Grep targets `other` even though project_root is `project`
    result = run_batch(
        {
            "intent": "x",
            "greps": [{
                "pattern": "UNIQUE_GREP_MARKER",
                "glob": "**/*.py",
                "root": str(other),
            }],
        },
        project_root=project,
    )
    g = result.greps[0]
    assert g.error is None
    assert g.total_matches == 1
    assert "marker.py" in g.matches[0].file


def test_grep_missing_root_per_op_error(project):
    """A grep pointing at a missing root reports a per-op error, not silent zero results."""
    result = run_batch(
        {"intent": "x", "greps": [{"pattern": "x", "root": "/nonexistent/grep/root"}]},
        project_root=project,
    )
    g = result.greps[0]
    assert g.error is not None and "does not exist" in g.error


# =============================================================================
# Glob
# =============================================================================


def test_glob_resolves(project):
    result = run_batch(
        {"intent": "x", "globs": ["src/**/*.py"]},
        project_root=project,
    )
    g = result.globs[0]
    assert g.error is None
    assert g.total_matches == 2  # auth.py + middleware.py


def test_glob_max_files_cap(project):
    for i in range(10):
        (project / f"f{i}.txt").write_text("x")
    result = run_batch(
        {"intent": "x", "globs": ["*.txt"]},
        project_root=project,
        budgets=BatchBudgets(max_glob_files=3),
    )
    g = result.globs[0]
    assert g.total_matches == 3
    assert g.truncated is True


def test_glob_dict_form_with_root(project, tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    (other / "a.py").write_text("")
    result = run_batch(
        {"intent": "x", "globs": [{"pattern": "*.py", "root": str(other)}]},
        project_root=project,
    )
    g = result.globs[0]
    assert g.total_matches == 1


def test_glob_missing_root_per_op_error(project):
    result = run_batch(
        {"intent": "x", "globs": [{"pattern": "*", "root": "/nonexistent/path"}]},
        project_root=project,
    )
    assert "does not exist" in result.globs[0].error


# =============================================================================
# Investigate (mocked CLI subprocess)
# =============================================================================


def test_investigate_calls_project_search(project):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = '[{"finding": "x", "score": 0.7}]'
        mock_run.return_value.stderr = ""
        result = run_batch(
            {"intent": "x", "investigate": [{"query": "auth flow", "limit": 3}]},
            project_root=project,
        )
    inv = result.investigate[0]
    assert inv.error is None
    assert inv.query == "auth flow"
    assert len(inv.results) == 1


def test_investigate_truncates_oversize_results(project):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = '[{"x": 1}, {"x": 2}, {"x": 3}, {"x": 4}, {"x": 5}]'
        mock_run.return_value.stderr = ""
        result = run_batch(
            {"intent": "x", "investigate": [{"query": "q", "limit": 2}]},
            project_root=project,
        )
    inv = result.investigate[0]
    assert len(inv.results) == 2
    assert inv.truncated is True


def test_investigate_cli_missing_per_op_error(project):
    with patch("subprocess.run", side_effect=FileNotFoundError("empirica")):
        result = run_batch(
            {"intent": "x", "investigate": [{"query": "q"}]},
            project_root=project,
        )
    assert "empirica CLI not found" in result.investigate[0].error


def test_investigate_invalid_json_per_op_error(project):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.stdout = "not json"
        mock_run.return_value.stderr = ""
        result = run_batch(
            {"intent": "x", "investigate": [{"query": "q"}]},
            project_root=project,
        )
    assert "non-JSON" in result.investigate[0].error


# =============================================================================
# Multi-op batch + summary
# =============================================================================


def test_multi_op_batch(project):
    result = run_batch(
        {
            "intent": "understand auth surface",
            "reads": [{"path": "src/auth.py"}],
            "greps": [{"pattern": "def ", "glob": "**/*.py"}],
            "globs": ["src/**/*.py", "tests/**/*.py"],
        },
        project_root=project,
    )
    assert result.ok
    assert len(result.reads) == 1
    assert len(result.greps) == 1
    assert len(result.globs) == 2
    s = result.summary
    assert s.total_files_read == 1
    # auth.py: login, logout (2); middleware.py: wrap (1); test_auth.py: test_login (1) = 4
    assert s.total_grep_matches >= 4
    assert s.total_globs_resolved == 3  # 2 src + 1 test


def test_summary_includes_duration(project):
    result = run_batch(
        {"intent": "x", "reads": [{"path": "README.md"}]},
        project_root=project,
    )
    assert result.summary.duration_ms >= 0


def test_summary_approx_tokens(project):
    result = run_batch(
        {"intent": "x", "reads": [{"path": "src/auth.py"}]},
        project_root=project,
    )
    assert result.summary.approx_tokens > 0


def test_intent_echoed(project):
    result = run_batch({"intent": "specific goal here"}, project_root=project)
    assert result.intent == "specific goal here"


def test_per_op_errors_dont_fail_batch(project):
    result = run_batch(
        {
            "intent": "x",
            "reads": [
                {"path": "src/auth.py"},      # exists
                {"path": "nonexistent.py"},   # error
            ],
        },
        project_root=project,
    )
    assert result.ok
    assert result.reads[0].error is None
    assert result.reads[1].error is not None


# Misuse signals — a single-op batch is the tell-tale "I'm using this as a
# Sentinel bypass" pattern. Surface a warning so the misuse is visible in
# tooling and logs.


def test_single_op_batch_emits_warning(project):
    result = run_batch(
        {"intent": "single-read", "reads": [{"path": "src/auth.py"}]},
        project_root=project,
    )
    assert result.ok
    assert result.warning is not None
    assert 'misuse' in result.warning.lower()


def test_zero_op_batch_emits_warning(project):
    # No ops at all — degenerate case but still worth flagging.
    result = run_batch({"intent": "empty"}, project_root=project)
    assert result.warning is not None


def test_multi_op_batch_no_warning(project):
    result = run_batch(
        {
            "intent": "real investigation",
            "reads": [{"path": "src/auth.py"}],
            "greps": [{"pattern": "decorator", "glob": "src/**/*.py"}],
        },
        project_root=project,
    )
    assert result.warning is None


def test_stderr_breadcrumb_emitted(project, capsys):
    """Visibility breadcrumb on stderr summarizes what came back so
    observers can see misuse patterns without parsing the JSON payload."""
    run_batch(
        {
            "intent": "breadcrumb-test",
            "reads": [{"path": "src/auth.py"}],
            "greps": [{"pattern": "decorator", "glob": "src/**/*.py"}],
        },
        project_root=project,
    )
    captured = capsys.readouterr()
    assert '[noetic-batch]' in captured.err


# =============================================================================
# Project-root resolution priority chain
# =============================================================================
#
# Regression: when no project_root was passed and the resolver couldn't find
# one, the executor silently defaulted to Path.cwd() — breaking cross-project
# investigation from a CWD that isn't the empirica project. Now the priority
# is: explicit > InstanceResolver.project_path() > cwd.


def test_project_root_uses_resolver_when_unset(project, monkeypatch):
    """When project_root is None, executor uses InstanceResolver.project_path()."""
    from empirica.utils.session_resolver import InstanceResolver

    monkeypatch.setattr(InstanceResolver, "project_path", staticmethod(lambda *a, **k: str(project)))
    # CWD is somewhere unrelated; resolver returns the test project
    monkeypatch.chdir("/tmp")

    result = run_batch(
        {"intent": "x", "globs": ["src/**/*.py"]},
        # project_root NOT passed → must come from resolver
    )
    assert result.globs[0].error is None
    assert result.globs[0].total_matches == 2


def test_project_root_falls_back_to_cwd_when_resolver_returns_none(project, monkeypatch):
    """Last-resort fallback: resolver returns None → use cwd."""
    from empirica.utils.session_resolver import InstanceResolver

    monkeypatch.setattr(InstanceResolver, "project_path", staticmethod(lambda *a, **k: None))
    monkeypatch.chdir(project)

    result = run_batch({"intent": "x", "globs": ["src/**/*.py"]})
    assert result.globs[0].error is None
    assert result.globs[0].total_matches == 2


def test_explicit_project_root_overrides_resolver(project, tmp_path, monkeypatch):
    """Explicit project_root arg wins over resolver."""
    from empirica.utils.session_resolver import InstanceResolver

    other = tmp_path / "wrong_project"
    other.mkdir()
    monkeypatch.setattr(InstanceResolver, "project_path", staticmethod(lambda *a, **k: str(other)))

    result = run_batch(
        {"intent": "x", "globs": ["src/**/*.py"]},
        project_root=project,  # explicit arg → resolver ignored
    )
    assert result.globs[0].total_matches == 2  # from `project`, not `other`
