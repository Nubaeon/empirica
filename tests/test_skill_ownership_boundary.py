"""Empirica owns, versions and installs the skills it CARRIES. Nothing else.

The boundary (David, 2026-09-06): core's setup script owns, versions and installs
core's own skills. Practice packages, system prompts and every other skill belong
to `empirica-mesh-support`'s ecosystem-update lane and must be left untouched.

Before this, ownership was INFERRED from absence in the source dir. Two failures
follow from inferring rather than declaring, and both are asserted below:

1. A skill core stops shipping instantly reads as "somebody else's" and is
   preserved forever — a retired skill of ours kept alive as a zombie.
2. A local edit to a skill we DO ship is not attributable. An unattributed patch
   appeared in the shared skills dir on 2026-09-06 and no practice claimed it.
"""

from __future__ import annotations

import json

from empirica.cli.command_handlers.setup_claude_code import (
    SKILL_OWNERSHIP_MANIFEST,
    _install_plugin_files,
    _locally_modified_owned_skills,
)


def _tree(root, files):
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return root


def test_install_DECLARES_what_empirica_owns(tmp_path):
    source = _tree(tmp_path / "src", {"skills/gardening/SKILL.md": "a\n", "skills/transaction/SKILL.md": "b\n"})
    plugin = tmp_path / "plugin"

    report = _install_plugin_files(source, plugin, "json")

    assert report["owned_skills"] == ["gardening", "transaction"]
    assert report["owned_version"], "an ownership claim without a version is not a version claim"

    manifest = json.loads((plugin / "skills" / SKILL_OWNERSHIP_MANIFEST).read_text())
    assert manifest["owner"] == "empirica"
    assert set(manifest["skills"]) == {"gardening", "transaction"}
    assert "mesh-support" in manifest["note"], "the manifest must name who owns everything else"


def test_a_foreign_skill_is_PRESERVED_and_stays_unowned(tmp_path):
    """mesh-support's lane. Core installs over its own and leaves the rest alone."""
    source = _tree(tmp_path / "src", {"skills/gardening/SKILL.md": "a\n"})
    plugin = _tree(tmp_path / "plugin", {"skills/practice-pack/SKILL.md": "theirs\n"})

    report = _install_plugin_files(source, plugin, "json")

    assert (plugin / "skills" / "practice-pack" / "SKILL.md").read_text() == "theirs\n", "peer skill destroyed"
    assert "practice-pack" not in report["owned_skills"], "core must not claim a skill it does not ship"


def test_a_RETIRED_skill_is_not_mistaken_for_a_peers(tmp_path):
    """The zombie. Source-absence alone cannot tell 'we dropped it' from 'theirs'."""
    source_v1 = _tree(tmp_path / "src1", {"skills/old/SKILL.md": "a\n", "skills/keep/SKILL.md": "b\n"})
    plugin = tmp_path / "plugin"
    _install_plugin_files(source_v1, plugin, "json")
    assert (plugin / "skills" / "old").is_dir()

    # v2 drops `old`. It was ours; it must not survive as a foreign skill.
    source_v2 = _tree(tmp_path / "src2", {"skills/keep/SKILL.md": "b\n"})
    report = _install_plugin_files(source_v2, plugin, "json")

    assert not (plugin / "skills" / "old").exists(), "a retired core skill was preserved as a zombie"
    assert report["owned_skills"] == ["keep"]


def test_a_local_edit_to_an_OWNED_skill_is_attributable(tmp_path):
    """What the unattributed patch could not answer: whose file was edited."""
    source = _tree(tmp_path / "src", {"skills/gardening/SKILL.md": "upstream\n"})
    plugin = tmp_path / "plugin"
    _install_plugin_files(source, plugin, "json")

    assert _locally_modified_owned_skills(plugin) == [], "positive control: a fresh install is unmodified"

    (plugin / "skills" / "gardening" / "SKILL.md").write_text("locally patched\n")
    assert _locally_modified_owned_skills(plugin) == ["gardening"]

    report = _install_plugin_files(source, plugin, "json")
    assert report["locally_modified_owned_skills"] == ["gardening"]


def test_the_manifest_is_not_reported_as_a_local_edit(tmp_path):
    """setup writes it every run; treating its own stamp as a customization would
    bury the files that genuinely are one."""
    source = _tree(tmp_path / "src", {"skills/gardening/SKILL.md": "a\n"})
    plugin = tmp_path / "plugin"
    _install_plugin_files(source, plugin, "json")

    report = _install_plugin_files(source, plugin, "json")

    assert not any(SKILL_OWNERSHIP_MANIFEST in b for b in report["backed_up"])
