"""MCP server management command parsers."""


def add_mcp_parsers(subparsers):
    """Add MCP server management command parsers"""

    # mcp start - Start MCP server
    mcp_start = subparsers.add_parser(
        'mcp-start',
        help='Start Empirica MCP server in background'
    )
    mcp_start.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')

    # mcp stop - Stop MCP server
    mcp_stop = subparsers.add_parser(
        'mcp-stop',
        help='Stop Empirica MCP server'
    )
    mcp_stop.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')

    # mcp status - Check MCP server status
    mcp_status = subparsers.add_parser(
        'mcp-status',
        help='Check Empirica MCP server status'
    )
    mcp_status.add_argument('--verbose', '-v', action='store_true', help='Show detailed process info')

    # mcp test - Test MCP server connection
    mcp_test = subparsers.add_parser(
        'mcp-test',
        help='Test Empirica MCP server connection'
    )
    mcp_test.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')

    # mcp list-tools - List available MCP tools
    mcp_list_tools = subparsers.add_parser(
        'mcp-list-tools',
        help='List available MCP tools'
    )
    mcp_list_tools.add_argument('--verbose', '-v', action='store_true', help='Show usage examples')
    mcp_list_tools.add_argument('--show-all', action='store_true', help='Include disabled/optional tools')

    # mcp call - Call MCP tool directly (for testing)
    mcp_call = subparsers.add_parser(
        'mcp-call',
        help='Call MCP tool directly (experimental)'
    )
    mcp_call.add_argument('tool_name', help='Name of the MCP tool to call')
    mcp_call.add_argument('arguments', nargs='?', default='{}', help='JSON arguments for the tool')
    mcp_call.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
