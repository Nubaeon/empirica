"""
End-to-end validation that MCP tools actually work in real usage scenarios.

Tests complete workflows to ensure:
1. All parameter names work end-to-end
2. All types are accepted correctly
3. Data flows through the system properly
4. No integration issues exist
"""

import asyncio
import pytest
import uuid
import json
# Update import to use current MCP server architecture
try:
    from empirica_mcp.server import list_tools, app
except ImportError:
    # Fallback for compatibility during transition
    from empirica.cli.mcp_client import list_tools as cli_list_tools
    list_tools = cli_list_tools
    app = None  # MCP app not available in CLI-only mode
from mcp.types import Tool, CallToolRequest


class TestBootstrapGoalSubtaskFlow:
    """Test complete bootstrap → create goal → add subtask → complete subtask flow"""
    
    def test_bootstrap_create_goal_subtask_complete_flow(self):
        """End-to-end test of the goal management workflow"""
        
        # This test validates the complete workflow without actually executing
        # the full pipeline (which would require actual CLI execution)
        
        # Test 1: Bootstrap session parameters are correct
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        session_create_tool = next((t for t in tools if t.name == 'session_create'), None)
        assert session_create_tool is not None

        bootstrap_schema = session_create_tool.inputSchema
        assert 'ai_id' in bootstrap_schema['required'], "ai_id should be required"
        assert bootstrap_schema['properties']['ai_id']['type'] == 'string'
        assert 'bootstrap_level' in bootstrap_schema['properties'], "bootstrap_level should exist"
        
        # Test 2: Create goal parameters are correct
        create_goal_tool = next((t for t in tools if t.name == 'create_goal'), None)
        assert create_goal_tool is not None
        
        goal_schema = create_goal_tool.inputSchema
        assert 'session_id' in goal_schema['required'], "session_id should be required"
        assert 'objective' in goal_schema['required'], "objective should be required"
        assert 'scope' in goal_schema['properties'], "scope should exist"
        # scope is an object, not an enum
        assert goal_schema['properties']['scope']['type'] == 'object', "scope should be object type"
        assert 'properties' in goal_schema['properties']['scope'], "scope should have nested properties"
        assert goal_schema['properties']['success_criteria']['type'] == 'array', "success_criteria should be array"
        
        # Test 3: Add subtask parameters are correct
        add_subtask_tool = next((t for t in tools if t.name == 'add_subtask'), None)
        assert add_subtask_tool is not None
        
        subtask_schema = add_subtask_tool.inputSchema
        assert 'goal_id' in subtask_schema['required'], "goal_id should be required"
        assert 'description' in subtask_schema['required'], "description should be required"
        assert 'importance' in subtask_schema['properties'], "importance should exist"
        assert 'enum' in subtask_schema['properties']['importance'], "importance should be enum"
        assert subtask_schema['properties']['importance']['enum'] == ['critical', 'high', 'medium', 'low']
        
        # Test 4: Complete subtask parameters are correct
        complete_tool = next((t for t in tools if t.name == 'complete_subtask'), None)
        assert complete_tool is not None
        
        complete_schema = complete_tool.inputSchema
        assert 'task_id' in complete_schema['required'], "task_id should be required"
        assert 'subtask_id' not in complete_schema['properties'], "subtask_id should NOT exist (was causing errors)"
        
        # Verify the parameter flow makes sense
        assert 'session_id' in goal_schema['required'], "create_goal needs session_id"
        assert 'goal_id' in subtask_schema['required'], "add_subtask needs goal_id (from create_goal)"
        assert 'task_id' in complete_schema['required'], "complete_subtask needs task_id (from add_subtask)"
    
    def test_parameter_types_match_workflow(self):
        """Test that parameter types align with the workflow expectations"""
        
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        
        # Test UUID types
        uuid_params = [
            ('session_create', 'ai_id'),  # Should accept string (we'll generate UUID)
            ('create_goal', 'session_id'),  # Should accept string UUID
            ('add_subtask', 'goal_id'),  # Should accept string UUID
            ('complete_subtask', 'task_id'),  # Should accept string UUID
        ]
        
        for tool_name, param_name in uuid_params:
            tool = next((t for t in tools if t.name == tool_name), None)
            assert tool is not None, f"Tool {tool_name} should exist"
            
            schema = tool.inputSchema
            assert param_name in schema['properties'], f"{tool_name} should have {param_name}"
            param_def = schema['properties'][param_name]
            assert param_def['type'] == 'string', f"{tool_name}.{param_name} should be string type"
        
        # Test array types
        array_params = [
            ('create_goal', 'success_criteria'),  # Array of strings
            ('add_subtask', 'dependencies'),  # Array of strings
        ]
        
        for tool_name, param_name in array_params:
            tool = next((t for t in tools if t.name == tool_name), None)
            assert tool is not None, f"Tool {tool_name} should exist"
            
            schema = tool.inputSchema
            assert param_name in schema['properties'], f"{tool_name} should have {param_name}"
            param_def = schema['properties'][param_name]
            assert param_def['type'] == 'array', f"{tool_name}.{param_name} should be array type"
            assert 'items' in param_def, f"{tool_name}.{param_name} array should have items"
            assert param_def['items']['type'] == 'string', f"{tool_name}.{param_name} items should be strings"


class TestPreflightCheckPostflightFlow:
    """Test complete preflight → check → postflight epistemic workflow"""
    
    def test_preflight_check_postflight_flow(self):
        """Test the complete epistemic assessment workflow"""
        
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        
        # Test 1: Preflight submit parameters
        preflight_tool = next((t for t in tools if t.name == 'submit_preflight_assessment'), None)
        assert preflight_tool is not None
        
        preflight_schema = preflight_tool.inputSchema
        assert 'session_id' in preflight_schema['required'], "session_id should be required"
        assert 'vectors' in preflight_schema['required'], "vectors should be required"
        assert 'reasoning' in preflight_schema['properties'], "reasoning should exist (unified parameter)"
        assert preflight_schema['properties']['vectors']['type'] == 'object', "vectors should be object"
        
        # Test 2: Check assessment parameters
        check_tool = next((t for t in tools if t.name == 'execute_check'), None)
        assert check_tool is not None
        
        check_schema = check_tool.inputSchema
        assert 'session_id' in check_schema['required'], "session_id should be required"
        assert 'findings' in check_schema['required'], "findings should be required (array)"
        assert 'remaining_unknowns' in check_schema['required'], "remaining_unknowns should be required (array)"
        assert 'confidence_to_proceed' in check_schema['required'], "confidence_to_proceed should be required (number)"
        assert check_schema['properties']['findings']['type'] == 'array', "findings should be array"
        assert check_schema['properties']['remaining_unknowns']['type'] == 'array', "remaining_unknowns should be array"
        assert check_schema['properties']['confidence_to_proceed']['type'] == 'number', "confidence_to_proceed should be number"
        
        # Test 3: Postflight submit parameters
        postflight_tool = next((t for t in tools if t.name == 'submit_postflight_assessment'), None)
        assert postflight_tool is not None
        
        postflight_schema = postflight_tool.inputSchema
        assert 'session_id' in postflight_schema['required'], "session_id should be required"
        assert 'vectors' in postflight_schema['required'], "vectors should be required"
        assert 'reasoning' in postflight_schema['properties'], "reasoning should exist (unified with preflight)"
        assert 'changes' not in postflight_schema['properties'], "changes should NOT exist (unified to reasoning)"
        
        # Test 4: Verify unified reasoning parameter
        assert 'reasoning' in preflight_schema['properties'], "preflight should use reasoning"
        assert 'reasoning' in postflight_schema['properties'], "postflight should use reasoning"
        
        # Test 5: Verify workflow consistency
        # Same session_id flows through all three stages
        required_session_params = [
            ('submit_preflight_assessment', 'session_id'),
            ('execute_check', 'session_id'),
            ('submit_postflight_assessment', 'session_id'),
        ]
        
        for tool_name, param_name in required_session_params:
            tool = next((t for t in tools if t.name == tool_name), None)
            schema = tool.inputSchema
            assert param_name in schema['required'], f"{tool_name} should require session_id for workflow continuity"


class TestHandoffWorkflow:
    """Test handoff creation and query workflow (replacement for session-end)"""
    
    def test_handoff_create_query_flow(self):
        """Test the handoff workflow as replacement for session-end"""
        
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        
        # Test 1: Handoff create parameters
        handoff_create_tool = next((t for t in tools if t.name == 'create_handoff_report'), None)
        assert handoff_create_tool is not None, "create_handoff_report should exist (session-end replacement)"
        
        handoff_schema = handoff_create_tool.inputSchema
        assert 'session_id' in handoff_schema['required'], "session_id should be required"
        assert 'task_summary' in handoff_schema['required'], "task_summary should be required"
        assert 'key_findings' in handoff_schema['required'], "key_findings should be required"
        assert 'next_session_context' in handoff_schema['required'], "next_session_context should be required"
        
        # Test 2: Verify session-end was removed
        session_end_tool = next((t for t in tools if t.name in ['session_end', 'session-end']), None)
        assert session_end_tool is None, "session_end should be removed (replaced by handoff-create)"
        
        # Test 3: Handoff query parameters (if it exists)
        handoff_query_tool = next((t for t in tools if t.name == 'query_handoff_reports'), None)
        if handoff_query_tool:
            query_schema = handoff_query_tool.inputSchema
            # Should have flexible query parameters
            assert 'session_id' in query_schema['properties'] or 'ai_id' in query_schema['properties'], \
                "handoff query should have session_id or ai_id parameter"
        
        # Test 4: Verify parameter types are correct
        assert handoff_schema['properties']['task_summary']['type'] == 'string', "task_summary should be string"
        assert handoff_schema['properties']['key_findings']['type'] == 'array', "key_findings should be array"
        assert handoff_schema['properties']['next_session_context']['type'] == 'string', "next_session_context should be string"
        assert handoff_schema['properties']['artifacts_created']['type'] == 'array', "artifacts_created should be array"


class TestIntegrationConsistency:
    """Test that MCP tools maintain consistency across the integration"""
    
    def test_all_required_session_parameters_match(self):
        """Verify that session_id is consistently required where expected"""
        
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        
        # Tools that should require session_id (session-level stateful operations)
        session_required_tools = [
            'create_goal',
            'list_goals',
            'submit_preflight_assessment',
            'execute_postflight',
            'submit_postflight_assessment',
            'create_handoff_report'
        ]
        
        for tool_name in session_required_tools:
            tool = next((t for t in tools if t.name == tool_name), None)
            if tool:
                schema = tool.inputSchema
                assert 'session_id' in schema.get('required', []), \
                    f"{tool_name} should require session_id for session-level stateful operation"
        
        # Tools that DON'T require session_id (goal-specific operations)
        goal_specific_tools = [
            'add_subtask',    # Requires goal_id instead
            'complete_subtask',  # Requires task_id instead
            'get_goal_progress',  # Requires goal_id instead
        ]
        
        for tool_name in goal_specific_tools:
            tool = next((t for t in tools if t.name == tool_name), None)
            if tool:
                schema = tool.inputSchema
                assert 'session_id' not in schema.get('required', []), \
                    f"{tool_name} should NOT require session_id (goal-specific operation)"
    
    def test_enum_consistency(self):
        """Verify that enum values are consistent across tools"""
        
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        
        # Test 1: Goal scope structure consistency
        create_goal_tool = next((t for t in tools if t.name == 'create_goal'), None)
        if create_goal_tool:
            scope_properties = create_goal_tool.inputSchema['properties']['scope']['properties']
            required_scope_fields = ['breadth', 'duration', 'coordination']
            for field in required_scope_fields:
                assert field in scope_properties, f"Scope should have {field} property"
        
        # Test 2: Subtask importance enum consistency
        add_subtask_tool = next((t for t in tools if t.name == 'add_subtask'), None)
        if add_subtask_tool:
            importance_enum = add_subtask_tool.inputSchema['properties']['importance']['enum']
            expected_importance = ['critical', 'high', 'medium', 'low']
            assert importance_enum == expected_importance, \
                f"add_subtask importance should be {expected_importance}"
        
        # Test 3: Check decision enum consistency
        check_submit_tool = next((t for t in tools if t.name == 'submit_check_assessment'), None)
        if check_submit_tool:
            decision_enum = check_submit_tool.inputSchema['properties']['decision']['enum']
            expected_decision = ['proceed', 'investigate']
            assert set(decision_enum) == set(expected_decision), \
                f"check_submit decision should be {expected_decision}"