"""
Parsers for auto issue capture CLI commands
"""

def add_issue_capture_parsers(subparsers):
    """Add issue capture command parsers"""
    add_issue_list_parser(subparsers)
    add_issue_show_parser(subparsers)
    add_issue_handoff_parser(subparsers)
    add_issue_resolve_parser(subparsers)
    add_issue_export_parser(subparsers)
    add_issue_stats_parser(subparsers)


def add_issue_list_parser(subparsers):
    """Parser for: empirica issue-list"""
    parser = subparsers.add_parser(
        'issue-list',
        help='List captured issues',
        description='List all auto-captured issues with optional filtering'
    )
    
    parser.add_argument(
        '--session-id',
        required=True,
        help='Session ID to list issues for'
    )
    
    parser.add_argument(
        '--status',
        choices=['new', 'investigating', 'handoff', 'resolved', 'wontfix'],
        help='Filter by issue status'
    )
    
    parser.add_argument(
        '--category',
        choices=['bug', 'error', 'warning', 'deprecation', 'todo', 'performance', 'compatibility', 'design', 'other'],
        help='Filter by issue category'
    )
    
    parser.add_argument(
        '--severity',
        choices=['blocker', 'high', 'medium', 'low'],
        help='Filter by severity level'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Maximum number of issues to return (default: 100)'
    )
    
    parser.add_argument(
        '--output',
        choices=['json', 'human'],
        default='json',
        help='Output format (default: json)'
    )
    
    parser.set_defaults(handler='issue_list')


def add_issue_show_parser(subparsers):
    """Parser for: empirica issue-show"""
    parser = subparsers.add_parser(
        'issue-show',
        help='Show detailed issue information',
        description='Display full details of a specific captured issue'
    )
    
    parser.add_argument(
        '--session-id',
        required=True,
        help='Session ID'
    )
    
    parser.add_argument(
        '--issue-id',
        required=True,
        help='Issue ID to show'
    )
    
    parser.add_argument(
        '--output',
        choices=['json', 'human'],
        default='json',
        help='Output format (default: json)'
    )
    
    parser.set_defaults(handler='issue_show')


def add_issue_handoff_parser(subparsers):
    """Parser for: empirica issue-handoff"""
    parser = subparsers.add_parser(
        'issue-handoff',
        help='Mark issue for handoff to another AI',
        description='Mark an issue as ready for another AI to work on'
    )
    
    parser.add_argument(
        '--session-id',
        required=True,
        help='Session ID'
    )
    
    parser.add_argument(
        '--issue-id',
        required=True,
        help='Issue ID to hand off'
    )
    
    parser.add_argument(
        '--assigned-to',
        required=True,
        help='AI ID or name to assign this issue to'
    )
    
    parser.add_argument(
        '--output',
        choices=['json', 'human'],
        default='json',
        help='Output format (default: json)'
    )
    
    parser.set_defaults(handler='issue_handoff')


def add_issue_resolve_parser(subparsers):
    """Parser for: empirica issue-resolve"""
    parser = subparsers.add_parser(
        'issue-resolve',
        help='Mark issue as resolved',
        description='Mark an issue as resolved with an explanation'
    )
    
    parser.add_argument(
        '--session-id',
        required=True,
        help='Session ID'
    )
    
    parser.add_argument(
        '--issue-id',
        required=True,
        help='Issue ID that was resolved'
    )
    
    parser.add_argument(
        '--resolution',
        required=True,
        help='How was this issue resolved?'
    )
    
    parser.add_argument(
        '--output',
        choices=['json', 'human'],
        default='json',
        help='Output format (default: json)'
    )
    
    parser.set_defaults(handler='issue_resolve')


def add_issue_export_parser(subparsers):
    """Parser for: empirica issue-export"""
    parser = subparsers.add_parser(
        'issue-export',
        help='Export issues for handoff',
        description='Export all issues assigned to another AI in portable JSON format'
    )
    
    parser.add_argument(
        '--session-id',
        required=True,
        help='Session ID'
    )
    
    parser.add_argument(
        '--assigned-to',
        required=True,
        help='AI ID to export issues for'
    )
    
    parser.add_argument(
        '--output',
        choices=['json', 'human'],
        default='json',
        help='Output format (default: json)'
    )
    
    parser.set_defaults(handler='issue_export')


def add_issue_stats_parser(subparsers):
    """Parser for: empirica issue-stats"""
    parser = subparsers.add_parser(
        'issue-stats',
        help='Show issue capture statistics',
        description='Display statistics about captured issues'
    )
    
    parser.add_argument(
        '--session-id',
        required=True,
        help='Session ID'
    )
    
    parser.add_argument(
        '--output',
        choices=['json', 'human'],
        default='json',
        help='Output format (default: json)'
    )
    
    parser.set_defaults(handler='issue_stats')
