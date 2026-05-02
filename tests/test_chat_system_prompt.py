"""Tests for empirica.core.chat.system_prompt — Phase 8."""

from __future__ import annotations

import pytest

from empirica.core.chat.system_prompt import (
    AUTONOMY_DEFAULT,
    AUTONOMY_MODES,
    MODE_BADGES,
    preview_lines,
    render_system_prompt,
)


class TestRenderSystemPrompt:
    def test_default_mode_renders(self):
        prompt = render_system_prompt("ollama", "qwen3.5:latest")
        assert "ollama" in prompt
        assert "qwen3.5:latest" in prompt
        assert MODE_BADGES[AUTONOMY_DEFAULT] in prompt
        assert "empirica chat" in prompt

    @pytest.mark.parametrize("mode", AUTONOMY_MODES)
    def test_each_mode_renders_unique_block(self, mode):
        prompt = render_system_prompt("p", "m", autonomy_mode=mode)
        assert MODE_BADGES[mode] in prompt
        assert f"Autonomy mode: {mode}" in prompt

    @pytest.mark.parametrize("mode", AUTONOMY_MODES)
    def test_each_mode_excludes_other_mode_blocks(self, mode):
        prompt = render_system_prompt("p", "m", autonomy_mode=mode)
        for other in AUTONOMY_MODES:
            if other == mode:
                continue
            assert f"Autonomy mode: {other}" not in prompt

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="unknown autonomy_mode"):
            render_system_prompt("p", "m", autonomy_mode="bogus")

    def test_user_instructions_appended(self):
        prompt = render_system_prompt(
            "p", "m", user_instructions="Reply only in haiku."
        )
        assert "User-supplied instructions" in prompt
        assert "Reply only in haiku." in prompt

    def test_user_instructions_omitted_when_blank(self):
        prompt = render_system_prompt("p", "m", user_instructions="   ")
        assert "User-supplied instructions" not in prompt

    def test_user_instructions_none_omitted(self):
        prompt = render_system_prompt("p", "m", user_instructions=None)
        assert "User-supplied instructions" not in prompt

    def test_provider_and_model_in_session_header(self):
        prompt = render_system_prompt("deepseek", "deepseek-chat")
        assert "provider: **deepseek**" in prompt
        assert "model: **deepseek-chat**" in prompt

    def test_slash_commands_documented(self):
        prompt = render_system_prompt("p", "m")
        for cmd in ("/finding", "/decision", "/unknown", "/provider", "/model"):
            assert cmd in prompt, f"slash command {cmd} missing from system prompt"

    def test_returned_prompt_is_nonempty_and_terminates_in_newline(self):
        prompt = render_system_prompt("p", "m")
        assert prompt.endswith("\n")
        assert len(prompt) > 500  # non-trivial content


class TestPreviewLines:
    def test_preview_returns_first_n_nonblank_lines(self):
        text = "line1\n\nline2\n\n\nline3\nline4"
        result = preview_lines(text, max_lines=2)
        lines = result.splitlines()
        assert lines == ["line1", "line2"]

    def test_preview_zero_max_returns_empty(self):
        result = preview_lines("a\nb\nc", max_lines=0)
        assert result == ""

    def test_preview_handles_short_input(self):
        result = preview_lines("only line", max_lines=10)
        assert result == "only line"


class TestModeMetadata:
    def test_badges_cover_all_modes(self):
        assert set(MODE_BADGES.keys()) == set(AUTONOMY_MODES)

    def test_default_mode_is_valid(self):
        assert AUTONOMY_DEFAULT in AUTONOMY_MODES
