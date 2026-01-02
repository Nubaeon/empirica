"""Investigation command parsers."""


def add_investigation_parsers(subparsers):
    """Add investigation command parsers"""
    # Main investigate command (consolidates investigate + analyze)
    investigate_parser = subparsers.add_parser('investigate', help='Investigate file/directory/concept')
    investigate_parser.add_argument('target', help='Target to investigate')
    investigate_parser.add_argument('--session-id', help='Session ID (for noetic recalibration - loads context anchor via project-bootstrap)')
    investigate_parser.add_argument('--type', default='auto',
                                   choices=['auto', 'file', 'directory', 'concept', 'comprehensive'],
                                   help='Investigation type. Use "comprehensive" for deep analysis (replaces analyze command)')
    investigate_parser.add_argument('--context', help='JSON context data')
    investigate_parser.add_argument('--detailed', action='store_true', help='Show detailed investigation')
    investigate_parser.add_argument('--verbose', action='store_true', help='Show detailed investigation')

    # REMOVED: analyze command - use investigate --type=comprehensive instead

    # ========== Epistemic Branching Commands (CASCADE 2.0) ==========

    # investigate-create-branch command
    create_branch_parser = subparsers.add_parser(
        'investigate-create-branch',
        help='Create parallel investigation branch (epistemic auto-merge)'
    )
    create_branch_parser.add_argument('--session-id', required=True, help='Session ID')
    create_branch_parser.add_argument('--investigation-path', required=True, help='What is being investigated (e.g., oauth2)')
    create_branch_parser.add_argument('--description', help='Description of investigation')
    create_branch_parser.add_argument('--preflight-vectors', help='Epistemic vectors at branch start (JSON)')
    create_branch_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    create_branch_parser.add_argument('--verbose', action='store_true', help='Verbose output')

    # investigate-checkpoint-branch command
    checkpoint_branch_parser = subparsers.add_parser(
        'investigate-checkpoint-branch',
        help='Checkpoint branch after investigation'
    )
    checkpoint_branch_parser.add_argument('--branch-id', required=True, help='Branch ID')
    checkpoint_branch_parser.add_argument('--postflight-vectors', required=True, help='Epistemic vectors after investigation (JSON)')
    checkpoint_branch_parser.add_argument('--tokens-spent', help='Tokens spent in investigation')
    checkpoint_branch_parser.add_argument('--time-spent', help='Time spent in investigation (minutes)')
    checkpoint_branch_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    checkpoint_branch_parser.add_argument('--verbose', action='store_true', help='Verbose output')

    # investigate-merge-branches command
    merge_branches_parser = subparsers.add_parser(
        'investigate-merge-branches',
        help='Auto-merge best branch based on epistemic scores'
    )
    merge_branches_parser.add_argument('--session-id', required=True, help='Session ID')
    merge_branches_parser.add_argument('--round', help='Investigation round number')
    merge_branches_parser.add_argument('--tag-losers', action='store_true',
        help='Auto-tag losing branches as dead ends with divergence reason')
    merge_branches_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    merge_branches_parser.add_argument('--verbose', action='store_true', help='Verbose output')

    # ========== Multi-Persona Orchestration (CASCADE 2.1) ==========

    # investigate-multi command - parallel epistemic agents with different personas
    multi_parser = subparsers.add_parser(
        'investigate-multi',
        help='Multi-persona parallel investigation with epistemic auto-merge'
    )
    multi_parser.add_argument('--task', required=True, help='Task for all personas to investigate')
    multi_parser.add_argument('--personas', required=True,
        help='Comma-separated persona IDs (e.g., security,ux,performance)')
    multi_parser.add_argument('--session-id', required=True, help='Session ID')
    multi_parser.add_argument('--context', help='Additional context from parent investigation')
    multi_parser.add_argument('--aggregate-strategy',
        choices=['epistemic-score', 'consensus', 'all'],
        default='epistemic-score',
        help='How to merge results (default: epistemic-score)')
    multi_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
