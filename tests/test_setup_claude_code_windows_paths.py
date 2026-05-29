"""Issue #111: setup-claude-code must emit forward-slash command paths.

On Windows, Claude Code runs `type: command` hooks + statusLine via Git Bash,
which eats backslashes (C:\\Users\\... -> C:Users... -> "command not found", so
every hook fails on every event). setup-claude-code must therefore write
forward-slash paths (valid on Windows too). These tests simulate Windows inputs
(PureWindowsPath plugin dir + a backslash python.exe path) and assert no
backslash survives into the generated commands. Runs on any host (PureWindowsPath
stringifies with backslashes regardless of OS).
"""

from __future__ import annotations

from pathlib import PureWindowsPath

from empirica.cli.command_handlers.setup_claude_code import (
    _configure_statusline,
    _register_all_hooks,
)

_WIN_PLUGIN = PureWindowsPath(r"C:\Users\graem\.claude\plugins\local\empirica")
_WIN_PY = r"C:\Users\graem\AppData\Roaming\uv\tools\empirica\Scripts\python.exe"


def _all_commands(settings: dict) -> list[str]:
    cmds: list[str] = []
    for event_entries in settings.get("hooks", {}).values():
        for entry in event_entries:
            for h in entry.get("hooks", []):
                cmds.append(h.get("command", ""))
    if "statusLine" in settings:
        cmds.append(settings["statusLine"].get("command", ""))
    return cmds


def test_register_all_hooks_emits_forward_slashes_on_windows():
    settings: dict = {}
    _register_all_hooks(settings, _WIN_PLUGIN, _WIN_PY, "json")
    cmds = _all_commands(settings)
    assert cmds, "expected hook commands to be registered"
    for c in cmds:
        assert "\\" not in c, f"backslash leaked into hook command (issue #111): {c}"
        assert "/hooks/" in c  # plugin path present + forward-slashed


def test_configure_statusline_emits_forward_slashes_on_windows():
    settings: dict = {}
    _configure_statusline(settings, _WIN_PLUGIN, _WIN_PY, "json")
    cmd = settings["statusLine"]["command"]
    assert "\\" not in cmd, f"backslash leaked into statusLine command (issue #111): {cmd}"
    assert "statusline_empirica.py" in cmd
