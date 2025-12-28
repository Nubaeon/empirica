"""
General schema structure validation for MCP tools.

Tests that all MCP tool schemas follow proper JSON schema patterns.
"""

import asyncio
import pytest
from typing import Dict, Any
# Update import to use current MCP server architecture
try:
    from empirica_mcp.server import list_tools
except ImportError:
    # Fallback for compatibility during transition
    from empirica.cli.mcp_client import list_tools as cli_list_tools
    list_tools = cli_list_tools


def test_all_tools_have_schemas():
    """Every MCP tool must have an inputSchema"""
    async def _get_tools():
        return await list_tools()
    
    tools = asyncio.run(_get_tools())
    assert len(tools) == 29, f"Expected 29 tools, found {len(tools)}"
    
    for tool in tools:
        assert hasattr(tool, 'inputSchema'), f"{tool.name} missing inputSchema"
        assert 'type' in tool.inputSchema, f"{tool.name} schema missing 'type'"
        assert 'properties' in tool.inputSchema, f"{tool.name} schema missing 'properties'"


def test_all_schemas_have_required_fields():
    """Every schema must have type, properties, and optionally required"""
    async def _get_tools():
        return await list_tools()
    
    tools = asyncio.run(_get_tools())
    
    for tool in tools:
        schema = tool.inputSchema
        
        # Type field validation
        assert 'type' in schema, f"{tool.name}: schema missing 'type' field"
        assert schema['type'] == 'object', f"{tool.name}: type should be 'object', got '{schema['type']}'"
        
        # Properties field validation
        assert 'properties' in schema, f"{tool.name}: schema missing 'properties' field"
        assert isinstance(schema['properties'], dict), f"{tool.name}: properties should be dict, got {type(schema['properties'])}"
        
        # Stateless tools can have empty properties
        stateless_tools = ['get_empirica_introduction', 'get_workflow_guidance', 'cli_help', 'list_identities']
        if tool.name not in stateless_tools:
            assert len(schema['properties']) > 0, f"{tool.name}: properties should not be empty (except stateless tools)"
        
        # If required exists, validate it's correct
        if 'required' in schema:
            assert isinstance(schema['required'], list), f"{tool.name}: required should be list"
            # Check all required fields exist in properties
            for req_field in schema['required']:
                assert req_field in schema['properties'], f"{tool.name}: required field '{req_field}' not in properties"


def test_parameter_types_are_valid():
    """All parameter types must be valid JSON schema types"""
    async def _get_tools():
        return await list_tools()
    
    tools = asyncio.run(_get_tools())
    valid_types = {'string', 'number', 'integer', 'boolean', 'array', 'object', 'null'}
    
    for tool in tools:
        schema = tool.inputSchema
        properties = schema['properties']

        for param_name, param_def in properties.items():
            assert 'type' in param_def, f"{tool.name}.{param_name}: missing type field"
            # Handle both single types and arrays of types
            param_type = param_def['type']
            if isinstance(param_type, list):
                # If it's a list of types, each type in the list must be valid
                for t in param_type:
                    assert t in valid_types, f"{tool.name}.{param_name}: invalid type '{t}' in list '{param_type}'"
            else:
                assert param_type in valid_types, f"{tool.name}.{param_name}: invalid type '{param_type}'"

                # If type is array, validate items exist
                if param_type == 'array':
                    assert 'items' in param_def, f"{tool.name}.{param_name}: array type must have 'items' field"
                    assert 'type' in param_def['items'], f"{tool.name}.{param_name}: array items must specify type"
                    assert param_def['items']['type'] in valid_types, f"{tool.name}.{param_name}: array item type invalid"


def test_enum_parameters_have_values():
    """All enum parameters must have at least one valid value"""
    async def _get_tools():
        return await list_tools()
    
    tools = asyncio.run(_get_tools())
    
    for tool in tools:
        schema = tool.inputSchema
        properties = schema['properties']
        
        for param_name, param_def in properties.items():
            # If it's an enum parameter, validate it has values
            if 'enum' in param_def:
                assert len(param_def['enum']) > 0, f"{tool.name}.{param_name}: enum must have at least one value"
                # All enum values should be of the specified type
                for enum_value in param_def['enum']:
                    expected_type = param_def.get('type', 'string')
                    if expected_type == 'string':
                        assert isinstance(enum_value, str), f"{tool.name}.{param_name}: enum value '{enum_value}' should be string"
                    elif expected_type == 'number':
                        assert isinstance(enum_value, (int, float)), f"{tool.name}.{param_name}: enum value '{enum_value}' should be number"


def test_descriptions_exist():
    """Most parameters should have descriptions for clarity (best practice)"""
    async def _get_tools():
        return await list_tools()
    
    tools = asyncio.run(_get_tools())
    missing_descriptions = []
    
    for tool in tools:
        schema = tool.inputSchema
        properties = schema['properties']
        
        for param_name, param_def in properties.items():
            # Check if description exists
            if 'description' not in param_def:
                missing_descriptions.append(f"{tool.name}.{param_name}")
            
            # If description exists, validate it's non-empty
            if 'description' in param_def:
                description = param_def['description']
                assert isinstance(description, str), f"{tool.name}.{param_name}: description should be string"
                assert len(description.strip()) > 0, f"{tool.name}.{param_name}: description should not be empty"
    
    # Report missing descriptions but don't fail the test (for improvement tracking)
    if missing_descriptions:
        print(f"Parameters missing descriptions: {missing_descriptions}")
    else:
        print("All parameters have descriptions! ✅")


class TestSchemaCompleteness:
    """Test that schemas are complete and well-structured"""
    
    def test_no_empty_schemas(self):
        """Ensure no tool has an empty or minimal schema"""
        async def _get_tools():
            return await list_tools()

        tools = asyncio.run(_get_tools())

        for tool in tools:
            schema = tool.inputSchema

            # Should have at least one property (except stateless tools)
            if len(schema['properties']) == 0:
                assert tool.name in [
                    'get_empirica_introduction',
                    'get_workflow_guidance',
                    'cli_help',
                    'list_identities'
                ], f"{tool.name}: stateless tools should have no properties"
    
    def test_consistent_naming(self):
        """Test that parameter names follow consistent naming conventions"""
        async def _get_tools():
            return await list_tools()
        
        tools = asyncio.run(_get_tools())
        
        for tool in tools:
            properties = tool.inputSchema['properties']
            
            for param_name in properties.keys():
                # Should use snake_case (underscores for multi-word params)
                assert '_' in param_name or param_name.islower(), \
                    f"{tool.name}.{param_name}: should use snake_case (e.g., 'session_id' not 'sessionId')"
                
                # Should not have leading/trailing underscores
                assert not param_name.startswith('_') and not param_name.endswith('_'), \
                    f"{tool.name}.{param_name}: should not have leading/trailing underscores"