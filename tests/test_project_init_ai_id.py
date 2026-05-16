"""Tests for the ai_id derivation in project_init.

Convention (David, 2026-05-16): the AI's identity comes from its home
project's basename, with `empirica-` prefix stripped where present.
`setup-claude-code` writes the canonical value into project.yaml at
project init so peer AIs can address it consistently in cortex
orchestration routing.
"""

from __future__ import annotations

from pathlib import Path

from empirica.cli.command_handlers.project_init import _derive_ai_id


def test_derive_ai_id_strips_empirica_prefix():
    """`empirica-cortex` → `cortex`, the David-2026-05-16 convention."""
    assert _derive_ai_id(Path("/home/user/empirical-ai/empirica-cortex")) == "cortex"
    assert _derive_ai_id(Path("/home/user/empirical-ai/empirica-outreach")) == "outreach"
    assert _derive_ai_id(Path("/home/user/empirical-ai/empirica-extension")) == "extension"


def test_derive_ai_id_keeps_empirica_root_as_is():
    """The empirica core repo itself has no prefix to strip — stays `empirica`."""
    assert _derive_ai_id(Path("/home/user/empirical-ai/empirica")) == "empirica"


def test_derive_ai_id_handles_non_empirica_projects():
    """The convention generalizes — any project's basename becomes its ai_id."""
    assert _derive_ai_id(Path("/home/user/code/myproject")) == "myproject"
    assert _derive_ai_id(Path("/tmp/some-app")) == "some-app"


def test_derive_ai_id_accepts_string_paths():
    """Should accept both Path and str inputs (Path(...) coerces either way)."""
    assert _derive_ai_id("/home/user/empirical-ai/empirica-cortex") == "cortex"


def test_derive_ai_id_defensive_against_bare_prefix(tmp_path):
    """Edge case: basename is literally `empirica-` (no suffix). Result
    must not be empty — fall back to the basename itself (or claude-code
    as last resort) so we never write an empty ai_id."""
    # Can't create a real dir named "empirica-" reliably across filesystems,
    # so just exercise the function with the path string directly.
    result = _derive_ai_id(Path("/home/user/empirica-"))
    # removeprefix on 'empirica-' gives empty; defensive `or basename` keeps it usable
    assert result == "empirica-"


def test_derive_ai_id_doesnt_strip_non_dash_empirica():
    """`empirica2` (no dash) should not have the prefix stripped — removeprefix
    only matches the exact 'empirica-' literal."""
    assert _derive_ai_id(Path("/home/user/empirica2")) == "empirica2"
