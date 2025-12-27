"""Utility command parsers."""


def add_utility_parsers(subparsers):
    """Add utility command parsers"""
    # Goal analysis command
    goal_parser = subparsers.add_parser('goal-analysis', help='Analyze goal feasibility')
    goal_parser.add_argument('goal', help='Goal to analyze')
    goal_parser.add_argument('--context', help='JSON context data')
    goal_parser.add_argument('--verbose', action='store_true', help='Show detailed analysis')
    
    # Token savings commands
    log_token_saving_parser = subparsers.add_parser('log-token-saving', help='Log a token saving event')
    log_token_saving_parser.add_argument('--session-id', required=True, help='Session ID')
    log_token_saving_parser.add_argument('--type', required=True,
        choices=['doc_awareness', 'finding_reuse', 'mistake_prevention', 'handoff_efficiency'],
        help='Type of token saving')
    log_token_saving_parser.add_argument('--tokens', type=int, required=True, help='Tokens saved')
    log_token_saving_parser.add_argument('--evidence', required=True, help='What was avoided/reused')
    log_token_saving_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    
    efficiency_report_parser = subparsers.add_parser('efficiency-report', help='Show token efficiency report')
    efficiency_report_parser.add_argument('--session-id', required=True, help='Session ID')
    efficiency_report_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
