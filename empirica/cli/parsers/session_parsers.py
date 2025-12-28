"""Session management command parsers."""


def add_session_parsers(subparsers):
    """Add session management command parsers"""
    # Sessions list command
    sessions_list_parser = subparsers.add_parser('sessions-list', help='List all sessions')
    sessions_list_parser.add_argument('--ai-id', help='Filter by AI identifier')
    sessions_list_parser.add_argument('--limit', type=int, default=50, help='Maximum sessions to show')
    sessions_list_parser.add_argument('--verbose', action='store_true', help='Show detailed info')
    sessions_list_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    
    # Sessions show command
    sessions_show_parser = subparsers.add_parser('sessions-show', help='Show detailed session info')
    sessions_show_parser.add_argument('session_id', nargs='?', help='Session ID or alias (latest, latest:active, latest:<ai_id>, latest:active:<ai_id>)')
    sessions_show_parser.add_argument('--session-id', dest='session_id_named', help='Session ID (alternative to positional argument)')
    sessions_show_parser.add_argument('--verbose', action='store_true', help='Show all vectors and cascades')
    sessions_show_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')

    # session-snapshot command
    session_snapshot_parser = subparsers.add_parser('session-snapshot', help='Show session snapshot (where you left off)')
    session_snapshot_parser.add_argument('session_id', help='Session ID or alias')
    session_snapshot_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')

    # Sessions export command
    sessions_export_parser = subparsers.add_parser('sessions-export', help='Export session to JSON')
    sessions_export_parser.add_argument('session_id', nargs='?', help='Session ID or alias (latest, latest:active, latest:<ai_id>)')
    sessions_export_parser.add_argument('--session-id', dest='session_id_named', help='Session ID (alternative to positional argument)')
    sessions_export_parser.add_argument('--output', '-o', help='Output file path (default: session_<id>.json)')
    
    # Memory compact command (AI-first JSON stdin)
    memory_compact_parser = subparsers.add_parser('memory-compact',
        help='Create epistemic continuity across memory compaction boundaries')
    memory_compact_parser.add_argument('config', nargs='?',
        help='JSON config file path or "-" for stdin (AI-first mode, default: stdin)')
    memory_compact_parser.add_argument('--output', choices=['human', 'json'], default='json',
        help='Output format (default: json)')
    memory_compact_parser.add_argument('--verbose', action='store_true',
        help='Show detailed operation info')

    # Session end command
    # session-end removed - use handoff-create instead (better parameter names, already in MCP)
