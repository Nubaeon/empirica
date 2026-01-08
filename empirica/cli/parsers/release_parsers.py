"""Release command parsers."""


def add_release_parsers(subparsers):
    """Add release command parsers"""
    # Release readiness check
    release_parser = subparsers.add_parser(
        'release-ready',
        help='Epistemic release assessment - verifies version sync, architecture health, security, and documentation'
    )
    release_parser.add_argument(
        '--project-root',
        help='Root directory of the project (default: current directory)'
    )
    release_parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick check (skip architecture assessment)'
    )
    release_parser.add_argument(
        '--output',
        choices=['human', 'json'],
        default='human',
        help='Output format'
    )

    # Docs assessment
    docs_parser = subparsers.add_parser(
        'docs-assess',
        help='Epistemic documentation assessment - measures docs coverage against actual features'
    )
    docs_parser.add_argument(
        '--project-root',
        help='Root directory of the project (default: current directory)'
    )
    docs_parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed undocumented items'
    )
    docs_parser.add_argument(
        '--summary-only',
        action='store_true',
        help='Lightweight summary (~50 tokens) for bootstrap context'
    )
    docs_parser.add_argument(
        '--output',
        choices=['human', 'json'],
        default='human',
        help='Output format'
    )

    # Docs explain - focused information retrieval
    explain_parser = subparsers.add_parser(
        'docs-explain',
        help='Get focused explanation of Empirica topics - inverts docs-assess'
    )
    explain_parser.add_argument(
        '--topic',
        help='Topic to explain (e.g., "vectors", "sessions", "goals")'
    )
    explain_parser.add_argument(
        '--question',
        help='Question to answer (e.g., "How do I start a session?")'
    )
    explain_parser.add_argument(
        '--audience',
        choices=['user', 'developer', 'ai', 'all'],
        default='all',
        help='Target audience for explanation'
    )
    explain_parser.add_argument(
        '--project-root',
        help='Root directory of the project (default: current directory)'
    )
    explain_parser.add_argument(
        '--project-id',
        help='Project ID for Qdrant semantic search (auto-detected if not specified)'
    )
    explain_parser.add_argument(
        '--output',
        choices=['human', 'json'],
        default='human',
        help='Output format'
    )
