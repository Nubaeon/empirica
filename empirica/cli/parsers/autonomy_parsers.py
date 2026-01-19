"""
Parsers for earned autonomy CLI commands

Commands for the graduated autonomy system:
- suggestion-log: Log AI suggestions with domain and confidence
- suggestion-list: List suggestions by status
- suggestion-review: Review and accept/reject suggestions
- trust-status: Show domain-specific trust levels
- autonomy-status: Show graduated Sentinel mode and escalation path
- evaluate-action: Check if an action would be allowed
"""


def add_autonomy_parsers(subparsers):
    """Add all autonomy command parsers"""
    add_suggestion_log_parser(subparsers)
    add_suggestion_list_parser(subparsers)
    add_suggestion_review_parser(subparsers)
    add_trust_status_parser(subparsers)
    add_autonomy_status_parser(subparsers)
    add_evaluate_action_parser(subparsers)


def add_suggestion_log_parser(subparsers):
    """Parser for: empirica suggestion-log"""
    parser = subparsers.add_parser(
        'suggestion-log',
        aliases=['sug'],
        help='Log an AI suggestion for review',
        description='Log a suggestion with domain, confidence, and rationale. '
                    'Suggestions are reviewed by humans and affect domain-specific trust.'
    )

    parser.add_argument(
        '--session-id',
        required=True,
        help='Session ID'
    )

    parser.add_argument(
        '--suggestion',
        required=True,
        help='The suggestion text (what you recommend)'
    )

    parser.add_argument(
        '--domain',
        required=False,
        help='Domain of the suggestion (e.g., architecture, testing, performance, security)'
    )

    parser.add_argument(
        '--confidence',
        type=float,
        default=0.7,
        help='Confidence in this suggestion (0.0-1.0, default: 0.7)'
    )

    parser.add_argument(
        '--rationale',
        required=False,
        help='Rationale for the suggestion (why you recommend this)'
    )

    parser.add_argument(
        '--output',
        choices=['json', 'text'],
        default='text',
        help='Output format (default: text)'
    )

    parser.set_defaults(handler='suggestion_log')


def add_suggestion_list_parser(subparsers):
    """Parser for: empirica suggestion-list"""
    parser = subparsers.add_parser(
        'suggestion-list',
        help='List suggestions',
        description='List suggestions with optional filtering by status, domain, or session.'
    )

    parser.add_argument(
        '--session-id',
        required=False,
        help='Filter by session ID'
    )

    parser.add_argument(
        '--project-id',
        required=False,
        help='Filter by project ID'
    )

    parser.add_argument(
        '--status',
        choices=['pending', 'reviewed', 'accepted', 'rejected', 'modified'],
        required=False,
        help='Filter by status'
    )

    parser.add_argument(
        '--domain',
        required=False,
        help='Filter by domain (e.g., architecture, testing)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help='Maximum number of suggestions to return (default: 20)'
    )

    parser.add_argument(
        '--output',
        choices=['json', 'text'],
        default='text',
        help='Output format (default: text)'
    )

    parser.set_defaults(handler='suggestion_list')


def add_suggestion_review_parser(subparsers):
    """Parser for: empirica suggestion-review"""
    parser = subparsers.add_parser(
        'suggestion-review',
        help='Review a suggestion (accept/reject/modify)',
        description='Review a pending suggestion and mark it as accepted, rejected, or modified. '
                    'This affects domain-specific trust calculation.'
    )

    parser.add_argument(
        '--suggestion-id',
        required=True,
        help='ID of the suggestion to review'
    )

    parser.add_argument(
        '--outcome',
        choices=['accepted', 'rejected', 'modified'],
        required=True,
        help='Review outcome'
    )

    parser.add_argument(
        '--notes',
        required=False,
        help='Review notes (especially important for rejected suggestions)'
    )

    parser.add_argument(
        '--reviewed-by',
        default='human',
        help='Who reviewed this (default: human)'
    )

    parser.add_argument(
        '--output',
        choices=['json', 'text'],
        default='text',
        help='Output format (default: text)'
    )

    parser.set_defaults(handler='suggestion_review')


def add_trust_status_parser(subparsers):
    """Parser for: empirica trust-status"""
    parser = subparsers.add_parser(
        'trust-status',
        help='Show domain-specific trust levels',
        description='Display earned trust levels per domain based on calibration accuracy, '
                    'suggestion outcomes, and recent mistakes.'
    )

    parser.add_argument(
        '--domain',
        required=False,
        help='Specific domain to check (e.g., architecture, testing, security)'
    )

    parser.add_argument(
        '--project-id',
        required=False,
        help='Project ID to scope trust calculation'
    )

    parser.add_argument(
        '--output',
        choices=['json', 'text'],
        default='text',
        help='Output format (default: text)'
    )

    parser.set_defaults(handler='trust_status')


def add_autonomy_status_parser(subparsers):
    """Parser for: empirica autonomy-status"""
    parser = subparsers.add_parser(
        'autonomy-status',
        help='Show graduated Sentinel mode and escalation path',
        description='Display current Sentinel mode based on earned trust, '
                    'along with requirements and escalation path to higher autonomy.'
    )

    parser.add_argument(
        '--session-id',
        required=False,
        help='Session ID (optional)'
    )

    parser.add_argument(
        '--domain',
        required=False,
        help='Domain to check (e.g., architecture, testing, security)'
    )

    parser.add_argument(
        '--project-id',
        required=False,
        help='Project ID to scope trust calculation'
    )

    parser.add_argument(
        '--output',
        choices=['json', 'text'],
        default='text',
        help='Output format (default: text)'
    )

    parser.set_defaults(handler='autonomy_status')


def add_evaluate_action_parser(subparsers):
    """Parser for: empirica evaluate-action"""
    parser = subparsers.add_parser(
        'evaluate-action',
        help='Check if an action would be allowed under current trust',
        description='Evaluate whether an action would be allowed, blocked, or auto-applied '
                    'based on current trust level and Sentinel mode.'
    )

    parser.add_argument(
        '--action',
        required=True,
        help='Action to evaluate (e.g., "refactor authentication", "fix typo")'
    )

    parser.add_argument(
        '--domain',
        required=False,
        help='Domain for trust calculation (e.g., architecture, security)'
    )

    parser.add_argument(
        '--target',
        required=False,
        help='Target of the action (e.g., file path, module name)'
    )

    parser.add_argument(
        '--confidence',
        type=float,
        default=0.7,
        help='AI confidence in this action (0.0-1.0, default: 0.7)'
    )

    parser.add_argument(
        '--project-id',
        required=False,
        help='Project ID to scope trust calculation'
    )

    parser.add_argument(
        '--output',
        choices=['json', 'text'],
        default='text',
        help='Output format (default: text)'
    )

    parser.set_defaults(handler='evaluate_action')
