"""
Test that MCP tool schemas match CLI command implementations.

This prevents issues like:
- Wrong parameter names (epistemic_importance vs importance)
- Wrong parameter types (subtask_id vs task_id)
- Missing enum values
- Type mismatches
"""

import pytest
import asyncio
import argparse
from mcp_local.empirica_mcp_server import list_tools
from empirica.cli.cli_core import create_argument_parser


def extract_cli_arguments(command_name):
    """Extract CLI arguments for a given command"""
    parser = create_argument_parser()
    subparsers = parser._subparsers._group_actions[0].choices
    subparser = subparsers.get(command_name)
    if not subparser:
        return None
    
    arguments = {}
    for action in subparser._actions:
        if action.dest != 'help':
            arguments[action.dest] = {
                'type': action.type,
                'required': action.required if hasattr(action, 'required') else False,
                'choices': action.choices if hasattr(action, 'choices') else None,
                'default': action.default
            }
    return arguments


def extract_mcp_tool_schema(tool_name):
    """Extract MCP tool schema (synchronous wrapper)"""
    async def _get_schema():
        tools = await list_tools()
        for tool in tools:
            if tool.name == tool_name:
                return tool.inputSchema
        return None
    
    return asyncio.run(_get_schema())


class TestCriticalTools:
    """Test the tools that had issues in previous sessions"""
    
    def test_create_goal_scope_is_enum(self):
        """Validate create_goal scope parameter is enum (was: free text causing errors)"""
        mcp_schema = extract_mcp_tool_schema('create_goal')
        assert mcp_schema is not None
        
        scope = mcp_schema['properties']['scope']
        assert 'enum' in scope, "scope must be enum to prevent free-text errors"
        assert set(scope['enum']) == {'task_specific', 'session_scoped', 'project_wide'}
    
    def test_create_goal_success_criteria_is_array(self):
        """Validate success_criteria is array type (was: accepting strings causing errors)"""
        mcp_schema = extract_mcp_tool_schema('create_goal')
        
        success_criteria = mcp_schema['properties']['success_criteria']
        assert success_criteria['type'] == 'array', "success_criteria must be array, not string"
        assert 'items' in success_criteria, "array must have items schema"
    
    def test_add_subtask_uses_importance_not_epistemic_importance(self):
        """Validate parameter is 'importance' not 'epistemic_importance' (was causing errors)"""
        mcp_schema = extract_mcp_tool_schema('add_subtask')
        cli_args = extract_cli_arguments('goals-add-subtask')
        
        # MCP schema check
        assert 'importance' in mcp_schema['properties'], "MCP: must use 'importance'"
        assert 'epistemic_importance' not in mcp_schema['properties'], "MCP: epistemic_importance should NOT exist"
        
        # CLI check
        assert 'importance' in cli_args, "CLI: must have 'importance' parameter"
        assert cli_args['importance']['choices'] == ['critical', 'high', 'medium', 'low']
    
    def test_complete_subtask_uses_task_id_not_subtask_id(self):
        """Validate parameter is 'task_id' not 'subtask_id' (was causing errors)"""
        mcp_schema = extract_mcp_tool_schema('complete_subtask')
        cli_args = extract_cli_arguments('goals-complete-subtask')
        
        # MCP schema check
        assert 'task_id' in mcp_schema['properties'], "MCP: must use 'task_id'"
        assert 'subtask_id' not in mcp_schema['properties'], "MCP: subtask_id should NOT exist"
        
        # CLI check
        assert 'task_id' in cli_args, "CLI: must have 'task_id' parameter"
    
    def test_postflight_submit_uses_reasoning_not_changes(self):
        """Validate postflight-submit uses 'reasoning' (unified with preflight-submit)"""
        mcp_schema = extract_mcp_tool_schema('submit_postflight_assessment')
        cli_args = extract_cli_arguments('postflight-submit')
        
        # MCP schema check
        assert 'reasoning' in mcp_schema['properties'], "MCP: must use 'reasoning' (unified)"
        
        # CLI check
        assert 'reasoning' in cli_args, "CLI: must have 'reasoning' parameter"
        # Note: CLI accepts --changes as deprecated alias


class TestAllMCPTools:
    """Validate all 23 MCP tools have proper schemas"""
    
    def test_all_tools_have_schemas(self):
        """Every MCP tool must have an inputSchema"""
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        assert len(tools) == 23, f"Expected 23 tools, found {len(tools)}"
        
        for tool in tools:
            assert hasattr(tool, 'inputSchema'), f"{tool.name} missing inputSchema"
            assert 'type' in tool.inputSchema, f"{tool.name} schema missing 'type'"
            assert 'properties' in tool.inputSchema, f"{tool.name} schema missing 'properties'"
    
    def test_required_parameters_are_specified(self):
        """All tools must specify required parameters"""
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        
        for tool in tools:
            schema = tool.inputSchema
            if 'required' in schema:
                for req_param in schema['required']:
                    assert req_param in schema['properties'], \
                        f"{tool.name}: required param '{req_param}' not in properties"


class TestHandoffTools:
    """Test handoff-related tools (session-end was removed)"""
    
    def test_session_end_removed_from_mcp(self):
        """Validate session-end is NOT in MCP tools (was removed, use handoff-create)"""
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        tool_names = [tool.name for tool in tools]
        
        assert 'session_end' not in tool_names, "session_end should be removed"
        assert 'session-end' not in tool_names, "session-end should be removed"
    
    def test_handoff_create_exists(self):
        """Validate handoff-create exists as replacement for session-end"""
        mcp_schema = extract_mcp_tool_schema('create_handoff_report')
        assert mcp_schema is not None, "create_handoff_report must exist"
        
        # Check required parameters
        required = mcp_schema.get('required', [])
        assert 'session_id' in required
        assert 'task_summary' in required
        assert 'key_findings' in required
        assert 'next_session_context' in required