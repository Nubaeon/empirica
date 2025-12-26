"""
Edit Verification Parsers - CLI Argument Parsers for Confidence-Based File Editing

Adds metacognitive edit verification to prevent 80% of AI edit failures.
"""

from . import format_help_text


def add_edit_verification_parsers(subparsers):
    """Add edit verification command parsers"""
    
    # edit-with-confidence command - metacognitive edit guard
    edit_confidence_parser = subparsers.add_parser(
        'edit-with-confidence',
        help='Edit file with metacognitive confidence assessment (prevents 80% of edit failures)'
    )
    edit_confidence_parser.add_argument(
        '--file-path',
        required=True,
        help=format_help_text('Path to file to edit', required=True)
    )
    edit_confidence_parser.add_argument(
        '--old-str',
        required=True,
        help=format_help_text('String to replace (exact match)', required=True)
    )
    edit_confidence_parser.add_argument(
        '--new-str',
        required=True,
        help=format_help_text('Replacement string', required=True)
    )
    edit_confidence_parser.add_argument(
        '--context-source',
        choices=['view_output', 'fresh_read', 'memory'],
        default='memory',
        help=format_help_text('Source of context (affects confidence assessment)', default='memory')
    )
    edit_confidence_parser.add_argument(
        '--output',
        choices=['human', 'json'],
        default='json',
        help=format_help_text('Output format', default='json')
    )
    edit_confidence_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed operation info'
    )