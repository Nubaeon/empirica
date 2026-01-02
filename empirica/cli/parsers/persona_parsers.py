"""
Persona Parsers - CLI argument parsers for emerged persona commands

Commands:
- persona-list: List all emerged personas
- persona-show: Show details of a specific persona
- persona-promote: Promote emerged persona to MCO
- persona-find: Find personas similar to a task
"""


def add_persona_parsers(subparsers):
    """Add persona-related command parsers"""

    # persona-list
    list_parser = subparsers.add_parser(
        'persona-list',
        help='List all emerged personas'
    )
    list_parser.add_argument(
        '--domain',
        help='Filter by domain (e.g., security, performance)'
    )
    list_parser.add_argument(
        '--output', choices=['human', 'json'], default='human',
        help='Output format'
    )

    # persona-show
    show_parser = subparsers.add_parser(
        'persona-show',
        help='Show details of a specific emerged persona'
    )
    show_parser.add_argument(
        '--persona-id', required=True,
        help='Persona ID to show'
    )
    show_parser.add_argument(
        '--output', choices=['human', 'json'], default='human',
        help='Output format'
    )

    # persona-promote
    promote_parser = subparsers.add_parser(
        'persona-promote',
        help='Promote emerged persona to MCO personas.yaml for global reuse'
    )
    promote_parser.add_argument(
        '--persona-id', required=True,
        help='Persona ID to promote'
    )
    promote_parser.add_argument(
        '--output', choices=['human', 'json'], default='human',
        help='Output format'
    )

    # persona-find
    find_parser = subparsers.add_parser(
        'persona-find',
        help='Find emerged personas similar to a task description'
    )
    find_parser.add_argument(
        '--task', required=True,
        help='Task description to match against'
    )
    find_parser.add_argument(
        '--limit', type=int, default=5,
        help='Maximum results (default: 5)'
    )
    find_parser.add_argument(
        '--output', choices=['human', 'json'], default='human',
        help='Output format'
    )
