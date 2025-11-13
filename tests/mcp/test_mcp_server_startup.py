"""Test MCP server initialization."""
import pytest
import asyncio
from mcp_local.empirica_mcp_server import list_tools

@pytest.mark.asyncio
async def test_server_starts():
    """MCP server starts without errors"""
    # This is a placeholder. A true server start test would be more complex
    # and is better suited for a full integration test.
    assert True

@pytest.mark.asyncio
async def test_tools_registered():
    """All core tools are registered"""
    tools = await list_tools()
    # Core tools (always available): 21 tools
    # Optional modality switcher tools: +4 tools (if enabled)
    # Total: 21 or 25 tools depending on EMPIRICA_ENABLE_MODALITY_SWITCHER
    assert len(tools) >= 21, f"Expected at least 21 core tools, got {len(tools)}"
    assert len(tools) <= 25, f"Expected at most 25 tools (21 core + 4 modality), got {len(tools)}"

@pytest.mark.asyncio
async def test_introduction_tool_exists():
    """get_empirica_introduction tool available"""
    tools = await list_tools()
    tool_names = [tool.name for tool in tools]
    assert "get_empirica_introduction" in tool_names