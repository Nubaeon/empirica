"""User interface command parsers."""


def add_user_interface_parsers(subparsers):
    """Add user interface command parsers (for human users)"""
    # Chat command - interactive conversation mode
    chat_parser = subparsers.add_parser('chat', help='Interactive chat with AI routing')
    chat_parser.add_argument('--adapter', help='Force specific adapter')
    chat_parser.add_argument('--model', help='Force specific model')
    chat_parser.add_argument('--strategy', default='epistemic', help='Routing strategy (default: epistemic)')
    chat_parser.add_argument('--session', help='Session ID (creates new if doesn\'t exist)')
    chat_parser.add_argument('--resume', help='Resume existing session by ID')
    chat_parser.add_argument('--no-save', action='store_true', help='Don\'t save conversation')
    chat_parser.add_argument('--verbose', action='store_true', help='Show routing details')

    # Dashboard command - TUI monitoring
    dashboard_parser = subparsers.add_parser('dashboard', help='Launch TUI dashboard for project monitoring')
    dashboard_parser.add_argument('--refresh-rate', type=float, default=1.0, help='Refresh rate in seconds (default: 1.0)')
