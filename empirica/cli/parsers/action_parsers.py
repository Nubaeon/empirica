"""Action logging command parsers for INVESTIGATE and ACT phases."""


def add_action_parsers(subparsers):
    """Add action logging command parsers for INVESTIGATE and ACT phases"""
    # investigate-log command
    investigate_log_parser = subparsers.add_parser('investigate-log', 
        help='Log investigation findings during INVESTIGATE phase')
    investigate_log_parser.add_argument('--session-id', required=True, help='Session ID')
    investigate_log_parser.add_argument('--findings', required=True, 
        help='JSON array of findings discovered')
    investigate_log_parser.add_argument('--evidence', 
        help='JSON object with evidence (file paths, line numbers, etc.)')
    investigate_log_parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    # act-log command
    act_log_parser = subparsers.add_parser('act-log', 
        help='Log actions taken during ACT phase')
    act_log_parser.add_argument('--session-id', required=True, help='Session ID')
    act_log_parser.add_argument('--actions', required=True, 
        help='JSON array of actions taken')
    act_log_parser.add_argument('--artifacts', 
        help='JSON array of files modified/created')
    act_log_parser.add_argument('--goal-id', 
        help='Goal UUID being worked on')
    act_log_parser.add_argument('--verbose', action='store_true', help='Verbose output')
