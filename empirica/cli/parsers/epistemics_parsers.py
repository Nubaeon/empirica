"""Epistemic trajectory command parsers."""


def add_epistemics_parsers(subparsers):
    """Add epistemic trajectory command parsers"""
    # Epistemic trajectory list command
    epistemics_list_parser = subparsers.add_parser('epistemics-list', help='List epistemic trajectory')
    epistemics_list_parser.add_argument('--session-id', required=True, help='Session ID')
    epistemics_list_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    
    # Epistemic trajectory show command
    epistemics_show_parser = subparsers.add_parser('epistemics-show', help='Show epistemic trajectory details')
    epistemics_show_parser.add_argument('--session-id', required=True, help='Session ID')
    epistemics_show_parser.add_argument('--phase', help='Filter by phase (optional)')
    epistemics_show_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
