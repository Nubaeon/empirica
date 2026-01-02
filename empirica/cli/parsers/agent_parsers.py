"""
Agent Parsers - CLI argument parsers for epistemic agent commands.
"""

from empirica.cli.command_handlers.agent_commands import (
    handle_agent_spawn_command,
    handle_agent_report_command,
    handle_agent_aggregate_command,
    handle_agent_export_command,
    handle_agent_import_command,
    handle_agent_discover_command,
)


def add_agent_parsers(subparsers):
    """Register agent command parsers."""

    # agent-spawn
    spawn_parser = subparsers.add_parser(
        'agent-spawn',
        help='Spawn epistemic agent (returns prompt with branch tracking)'
    )
    spawn_parser.add_argument('--session-id', required=True, help='Parent session ID')
    spawn_parser.add_argument('--task', required=True, help='Task for the agent')
    spawn_parser.add_argument('--persona', default='general', help='Persona ID to use')
    spawn_parser.add_argument('--turtle', action='store_true',
        help='Auto-select best emerged persona for task (overrides --persona)')
    spawn_parser.add_argument('--context', help='Additional context from parent')
    spawn_parser.add_argument('--output', choices=['text', 'json'], default='text')
    spawn_parser.set_defaults(func=handle_agent_spawn_command)

    # agent-report
    report_parser = subparsers.add_parser(
        'agent-report',
        help='Report agent postflight results'
    )
    report_parser.add_argument('--branch-id', required=True, help='Branch ID from agent-spawn')
    report_parser.add_argument('--postflight', help='Postflight JSON or "-" for stdin')
    report_parser.add_argument('--output', choices=['text', 'json'], default='text')
    report_parser.set_defaults(func=handle_agent_report_command)

    # agent-aggregate
    aggregate_parser = subparsers.add_parser(
        'agent-aggregate',
        help='Aggregate results from multiple agents'
    )
    aggregate_parser.add_argument('--session-id', required=True, help='Session ID')
    aggregate_parser.add_argument('--round', type=int, default=1, help='Investigation round')
    aggregate_parser.add_argument('--output', choices=['text', 'json'], default='text')
    aggregate_parser.set_defaults(func=handle_agent_aggregate_command)

    # agent-export (for sharing network)
    export_parser = subparsers.add_parser(
        'agent-export',
        help='Export epistemic agent as shareable JSON package'
    )
    export_parser.add_argument('--branch-id', required=True, help='Branch ID to export')
    export_parser.add_argument('--output-file', help='Output file path (prints to stdout if not specified)')
    export_parser.add_argument('--register', action='store_true', help='Register to sharing network (Qdrant)')
    export_parser.add_argument('--output', choices=['text', 'json'], default='json')
    export_parser.set_defaults(func=handle_agent_export_command)

    # agent-import (for sharing network)
    import_parser = subparsers.add_parser(
        'agent-import',
        help='Import epistemic agent from JSON package'
    )
    import_parser.add_argument('--session-id', required=True, help='Session to import into')
    import_parser.add_argument('--input-file', required=True, help='Agent JSON file to import')
    import_parser.add_argument('--output', choices=['text', 'json'], default='text')
    import_parser.set_defaults(func=handle_agent_import_command)

    # agent-discover (search sharing network)
    discover_parser = subparsers.add_parser(
        'agent-discover',
        help='Discover epistemic agents in sharing network'
    )
    discover_parser.add_argument('--domain', help='Search by domain expertise (e.g., security, multi-persona)')
    discover_parser.add_argument('--min-reputation', type=float, help='Minimum reputation score (0.0-1.0)')
    discover_parser.add_argument('--limit', type=int, default=10, help='Maximum results')
    discover_parser.add_argument('--output', choices=['text', 'json'], default='text')
    discover_parser.set_defaults(func=handle_agent_discover_command)
