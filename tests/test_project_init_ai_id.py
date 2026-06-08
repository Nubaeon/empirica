"""Tests for the ai_id derivation in project_init.

Strict-canonical convention: the AI's identity is the **exact**
directory basename — prefix KEPT. `empirica-cortex` stays
`empirica-cortex`, not `cortex`. Short aliases (`cortex`,
`mesh-support`) live only in human-conversational layers (skills +
system prompt); code paths use the full basename so cortex routing +
ntfy event filtering stay aligned. `setup-claude-code` writes this
canonical value into project.yaml at project init.

Regression context: cortex's prop_5egdlfyq4r — pre-strict-canonical
the resolver stripped the prefix to `cortex`, then the SessionStart
hook armed Monitor with a grep filter on `cortex` while ntfy events
emitted with `empirica-cortex` → silent mesh wake drop for hours.
"""

from __future__ import annotations

from pathlib import Path

from empirica.cli.command_handlers.project_init import _derive_ai_id


def test_derive_ai_id_keeps_empirica_prefix():
    """`empirica-cortex` stays `empirica-cortex` — strict-canonical."""
    assert _derive_ai_id(Path("/home/user/empirical-ai/empirica-cortex")) == "empirica-cortex"
    assert _derive_ai_id(Path("/home/user/empirical-ai/empirica-outreach")) == "empirica-outreach"
    assert _derive_ai_id(Path("/home/user/empirical-ai/empirica-extension")) == "empirica-extension"


def test_derive_ai_id_keeps_empirica_root_as_is():
    """The empirica core repo itself stays `empirica`."""
    assert _derive_ai_id(Path("/home/user/empirical-ai/empirica")) == "empirica"


def test_derive_ai_id_handles_non_empirica_projects():
    """The convention generalizes — any project's basename becomes its ai_id."""
    assert _derive_ai_id(Path("/home/user/code/myproject")) == "myproject"
    assert _derive_ai_id(Path("/tmp/some-app")) == "some-app"


def test_derive_ai_id_accepts_string_paths():
    """Should accept both Path and str inputs (Path(...) coerces either way)."""
    assert _derive_ai_id("/home/user/empirical-ai/empirica-cortex") == "empirica-cortex"


def test_derive_ai_id_defensive_against_bare_prefix():
    """Edge case: basename is literally `empirica-` (no suffix). Result
    must not be empty — strict-canonical returns the basename as-is."""
    result = _derive_ai_id(Path("/home/user/empirica-"))
    assert result == "empirica-"


def test_derive_ai_id_non_dash_empirica_kept():
    """`empirica2` (no dash) is its own slug, not the empirica root.
    Strict-canonical: basename returned as-is."""
    assert _derive_ai_id(Path("/home/user/empirica2")) == "empirica2"
