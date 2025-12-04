"""Test individual MCP tools."""
import pytest
import json
from unittest.mock import MagicMock, patch
from mcp_local.empirica_mcp_server import call_tool
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
async def test_execute_preflight():
    """execute_preflight returns meta-prompt"""
    # This tool requires a session_id, so we'll call session_create first
    bootstrap_result = await call_tool("session_create", {"ai_id": "test_agent"})
    session_id = json.loads(bootstrap_result[0].text)["session_id"]

    result = await call_tool("execute_preflight", {"session_id": session_id, "prompt": "Test prompt"})
    assert isinstance(result, list)
    assert len(result) == 1
    content = result[0]
    assert isinstance(content, types.TextContent)

    data = json.loads(content.text)
    assert data["ok"] is True
    assert data["phase"] == "preflight"
    assert "self_assessment_prompt" in data

@pytest.mark.asyncio
async def test_submit_postflight_assessment():
    """submit_postflight_assessment calculates delta"""
    mock_db_instance = MagicMock()
    mock_db_instance.conn.cursor.return_value.fetchone.return_value = ["{\"know\": 0.5, \"do\": 0.5, \"context\": 0.5, \"uncertainty\": 0.5}"]
    mock_db_instance.conn.execute.return_value = None
    mock_db_instance.conn.commit.return_value = None
    mock_db_instance.close.return_value = None

    with patch('mcp_local.empirica_mcp_server.SessionDatabase', return_value=mock_db_instance):
        # Mock _calculate_delta_and_calibration to return dummy values
        with patch('mcp_local.empirica_mcp_server._calculate_delta_and_calibration', return_value=({'know': 0.1}, {'status': 'well_calibrated'})):
            session_id = "test_session_id"
            vectors = {"know": 0.6, "do": 0.6, "context": 0.6, "uncertainty": 0.4}
            changes_noticed = "Learned a lot"

            result = await call_tool("submit_postflight_assessment", {
                "session_id": session_id,
                "vectors": vectors,
                "changes_noticed": changes_noticed
            })

            assert isinstance(result, list)
            assert len(result) == 1
            content = result[0]
            assert isinstance(content, types.TextContent)

            data = json.loads(content.text)
            assert data["ok"] is True
            assert "epistemic_delta" in data
            assert "calibration" in data
            assert data["epistemic_delta"]["know"] == 0.1
            assert data["calibration"]["status"] == "well_calibrated"
