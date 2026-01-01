"""
Agent Parsers - CLI argument parsers for epistemic agent commands.
"""

from empirica.cli.command_handlers.agent_commands import (
    handle_agent_spawn_command,
    handle_agent_report_command,
    handle_agent_aggregate_command,
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
