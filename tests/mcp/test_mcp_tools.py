"""Test individual MCP tools."""
import pytest
import json
from unittest.mock import MagicMock, patch
# Update import to use current MCP server architecture
try:
    from empirica_mcp.server import call_tool
except ImportError:
    # Fallback for compatibility during transition
    from empirica.cli.mcp_client import call_tool as cli_call_tool
    call_tool = cli_call_tool
from mcp import types

@pytest.mark.asyncio
async def test_session_create():
    """session_create tool works"""
    result = await call_tool("session_create", {"ai_id": "test_agent"})
    assert isinstance(result, list)
    assert len(result) == 1
    content = result[0]
    assert isinstance(content, types.TextContent)
    
    data = json.loads(content.text)
    assert data["ok"] is True
    assert "session_id" in data
    assert data["ai_id"] == "test_agent"

@pytest.mark.asyncio
async def test_submit_postflight_assessment():
    """submit_postflight_assessment calls CLI command"""
    # Since this tool routes to CLI, test that it can be called
    # First, create a session
    session_result = await call_tool("session_create", {"ai_id": "test_agent"})
    session_id = json.loads(session_result[0].text)["session_id"]

    # Also need preflight data to establish baseline for deltas
    vectors = {"engagement": 0.8, "know": 0.6, "do": 0.7, "context": 0.7, "clarity": 0.75, "coherence": 0.7, "signal": 0.65, "density": 0.5, "state": 0.6, "change": 0.55, "completion": 0.6, "impact": 0.65, "uncertainty": 0.4}

    result = await call_tool("submit_postflight_assessment", {
        "session_id": session_id,
        "vectors": vectors,
        "reasoning": "Test postflight assessment"
    })

    assert isinstance(result, list)
    assert len(result) == 1
    content = result[0]
    assert isinstance(content, types.TextContent)

    # Since this routes to CLI, check that it returns a valid response
    data = json.loads(content.text)
    # This should return the CLI response, which should have "ok": true
    if "ok" in data:
        assert data["ok"] is True
    else:
        # If CLI command succeeds, it may return different format
        # but should not return an error
        assert "error" not in data
