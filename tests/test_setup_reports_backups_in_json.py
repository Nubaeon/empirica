"""A backup nobody is told about recovers nothing — in EVERY output mode.

`_backup_locally_modified_plugin_files` copies each installed plugin file that
differs from what the sync is about to write, and the human branch names them.
The `--output json` branch printed nothing and the caller discarded the returned
list into `_preserved`, so under JSON the files were backed up and NOTHING said
so — in the mode scripts, CI and other tools consume, and where no human is
watching stdout.

Reported by a peer practice on 2026-09-06, in the reporting layer of the very
mechanism I had just cited to them as adequate.
"""

from __future__ import annotations

from pathlib import Path

from empirica.cli.command_handlers.setup_claude_code import _install_plugin_files


def _tree(root: Path, files: dict[str, str]) -> Path:
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return root


def test_json_mode_reports_which_files_were_overwritten(tmp_path, capsys):
    source = _tree(tmp_path / "src", {"skills/gardening/SKILL.md": "UPSTREAM TEXT\n"})
    plugin = _tree(tmp_path / "plugin", {"skills/gardening/SKILL.md": "LOCALLY PATCHED\n"})

    report = _install_plugin_files(source, plugin, "json")

    assert report is not None, "json mode must get the backup list, not None"
    assert "skills/gardening/SKILL.md" in report["backed_up"]
    assert report["backup_dir"].endswith(".bak")
    assert Path(report["backup_dir"], "skills/gardening/SKILL.md").read_text() == "LOCALLY PATCHED\n"
    assert capsys.readouterr().out == "", "json mode must not print — it must REPORT"


def test_an_unmodified_tree_reports_an_EMPTY_list_not_a_missing_key(tmp_path):
    """`backed_up: []` states that nothing was overwritten. An absent key states nothing."""
    same = {"skills/gardening/SKILL.md": "UPSTREAM TEXT\n"}
    source = _tree(tmp_path / "src", same)
    plugin = _tree(tmp_path / "plugin", dict(same))

    report = _install_plugin_files(source, plugin, "json")

    assert "backed_up" in report, "the key must be present so a consumer can check it"
    assert report["backed_up"] == []


def test_human_mode_still_prints(tmp_path, capsys):
    """Positive control: the two tests above assert JSON behaviour and would both
    pass against a build that had lost the human warning entirely."""
    source = _tree(tmp_path / "src", {"hooks/x.py": "new\n"})
    plugin = _tree(tmp_path / "plugin", {"hooks/x.py": "local\n"})

    _install_plugin_files(source, plugin, "human")

    out = capsys.readouterr().out
    assert "hooks/x.py" in out
    assert "backed up" in out
