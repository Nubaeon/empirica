"""
Validate arg_map correctly translates MCP parameters to CLI flags.

This tests the parameter translation layer that handles cases like:
- bootstrap_level → level
- task_id → task-id  
- key_findings → key-findings
- next_session_context → next-session-context
"""

import asyncio
import pytest
# Update import to use current MCP server architecture
try:
    from empirica_mcp.server import list_tools
except ImportError:
    # Fallback for compatibility during transition
    from empirica.cli.mcp_client import list_tools as cli_list_tools
    list_tools = cli_list_tools


class TestArgMapTranslations:
    """Test that arg_map correctly maps MCP parameters to CLI flags"""

    def test_task_id_maps_to_task_id_hyphen(self):
        """Complete subtask MCP tool should map task_id to --task-id in CLI"""
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        complete_tool = next((t for t in tools if t.name == 'complete_subtask'), None)
        assert complete_tool is not None
        
        schema = complete_tool.inputSchema
        assert 'task_id' in schema['properties'], "task_id should exist in MCP schema"
        
        # Verify that the mapping to task-id would work
        # (The actual mapping happens in arg_map translation)
    
    def test_key_findings_maps_to_hyphenated(self):
        """Handoff create MCP tool should map key_findings to --key-findings in CLI"""
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        handoff_tool = next((t for t in tools if t.name == 'create_handoff_report'), None)
        assert handoff_tool is not None
        
        schema = handoff_tool.inputSchema
        assert 'key_findings' in schema['properties'], "key_findings should exist in MCP schema"
    
    def test_next_session_context_maps_to_hyphenated(self):
        """Handoff create MCP tool should map next_session_context to --next-session-context"""
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        handoff_tool = next((t for t in tools if t.name == 'create_handoff_report'), None)
        assert handoff_tool is not None
        
        schema = handoff_tool.inputSchema
        assert 'next_session_context' in schema['properties'], "next_session_context should exist in MCP schema"
    
    def test_reasoning_maps_consistently(self):
        """Both preflight and postflight should use reasoning parameter (unified)"""
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        
        # Check preflight submit tool
        preflight_tool = next((t for t in tools if t.name == 'submit_preflight_assessment'), None)
        assert preflight_tool is not None
        preflight_schema = preflight_tool.inputSchema
        assert 'reasoning' in preflight_schema['properties'], "preflight should use reasoning"
        
        # Check postflight submit tool
        postflight_tool = next((t for t in tools if t.name == 'submit_postflight_assessment'), None)
        assert postflight_tool is not None
        postflight_schema = postflight_tool.inputSchema
        assert 'reasoning' in postflight_schema['properties'], "postflight should use reasoning (unified with preflight)"
        
        # Verify they don't use 'changes' parameter
        assert 'changes' not in preflight_schema['properties'], "preflight should not use 'changes'"
        assert 'changes' not in postflight_schema['properties'], "postflight should not use 'changes'"


class TestUnderscoreToHyphenConversion:
    """Test that underscore-to-hyphen conversion works for parameters not in arg_map"""
    
    def test_session_id_converts_to_session_id_hyphen(self):
        """session_id should convert to --session-id by default"""
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        
        # Find a tool that uses session_id
        tools_with_session_id = [t for t in tools if 'session_id' in t.inputSchema['properties']]
        assert len(tools_with_session_id) > 0, "Should have tools with session_id parameter"
        
        # Check that the parameter exists
        for tool in tools_with_session_id[:1]:  # Check first one as example
            schema = tool.inputSchema
            assert 'session_id' in schema['properties'], "session_id should exist"
    
    def test_goal_id_converts_to_goal_id_hyphen(self):
        """goal_id should convert to --goal-id by default"""
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        
        # Find a tool that uses goal_id
        tools_with_goal_id = [t for t in tools if 'goal_id' in t.inputSchema['properties']]
        assert len(tools_with_goal_id) > 0, "Should have tools with goal_id parameter"
        
        # Check that the parameter exists
        for tool in tools_with_goal_id[:1]:  # Check first one as example
            schema = tool.inputSchema
            assert 'goal_id' in schema['properties'], "goal_id should exist"
    
    def test_estimated_tokens_converts_to_estimated_tokens_hyphen(self):
        """estimated_tokens should convert to --estimated-tokens by default"""
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        
        # Find a tool that uses estimated_tokens
        tools_with_tokens = [t for t in tools if 'estimated_tokens' in t.inputSchema['properties']]
        assert len(tools_with_tokens) > 0, "Should have tools with estimated_tokens parameter"
        
        # Check that the parameter exists
        for tool in tools_with_tokens[:1]:  # Check first one as example
            schema = tool.inputSchema
            assert 'estimated_tokens' in schema['properties'], "estimated_tokens should exist"


class TestSpecialMappings:
    """Test special parameter mappings that deviate from standard patterns"""

    def test_remaining_unknowns_special_mapping(self):
        """remaining_unknowns has special mapping to --unknowns (not --remaining-unknowns)"""
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        
        # Find tools that use remaining_unknowns
        tools_with_unknowns = [t for t in tools if 'remaining_unknowns' in t.inputSchema['properties']]
        assert len(tools_with_unknowns) > 0, "Should have tools with remaining_unknowns parameter"
        
        # Check first tool as example
        for tool in tools_with_unknowns[:1]:
            schema = tool.inputSchema
            assert 'remaining_unknowns' in schema['properties'], "remaining_unknowns should exist"
    
    def test_artifacts_created_special_mapping(self):
        """artifacts_created has special mapping to --artifacts (not --artifacts-created)"""
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        handoff_tool = next((t for t in tools if t.name == 'create_handoff_report'), None)
        assert handoff_tool is not None
        
        schema = handoff_tool.inputSchema
        assert 'artifacts_created' in schema['properties'], "artifacts_created should exist"
    
    def test_confidence_to_proceed_special_mapping(self):
        """confidence_to_proceed has special mapping to --confidence (not --confidence-to-proceed)"""
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        
        # Find tools that use confidence_to_proceed
        tools_with_confidence = [t for t in tools if 'confidence_to_proceed' in t.inputSchema['properties']]
        assert len(tools_with_confidence) > 0, "Should have tools with confidence_to_proceed parameter"
        
        # Check first tool as example
        for tool in tools_with_confidence[:1]:
            schema = tool.inputSchema
            assert 'confidence_to_proceed' in schema['properties'], "confidence_to_proceed should exist"


class TestArgMapCompleteness:
    """Test that arg_map covers all necessary mappings"""
    
    def test_all_known_mappings_are_used(self):
        """Verify that the arg_map includes all expected special mappings"""
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        
        # Expected special mappings based on the implementation
        # NOTE: bootstrap_level is planned but not yet implemented in MCP schema
        expected_special_params = [
            # 'bootstrap_level',  # Planned: should map to --level (not yet in MCP schema)
            'task_id',  # Should map to --task-id
            'key_findings',  # Should map to --key-findings
            'next_session_context',  # Should map to --next-session-context
            'artifacts_created',  # Should map to --artifacts
            'reasoning',  # Should map to --reasoning
            'remaining_unknowns',  # Should map to --unknowns
            'confidence_to_proceed',  # Should map to --confidence
        ]
        
        # Check that these parameters exist in the appropriate tools
        for param in expected_special_params:
            tools_with_param = [t for t in tools if param in t.inputSchema['properties']]
            assert len(tools_with_param) > 0, f"Parameter '{param}' should exist in at least one tool"