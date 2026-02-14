"""
Lens CLI Parsers — Epistemic Lens commands.

Commands:
- lens-profile: Show human epistemic profile
- lens-ingest: Extract, chunk, embed source content
- lens-delta: Score content against human profile
- lens-status: Collection stats + profile summary
"""


def add_lens_parsers(subparsers):
    """Add lens command parsers."""

    # lens-profile
    profile_parser = subparsers.add_parser(
        'lens-profile',
        aliases=['lp'],
        help='Show human epistemic profile — domain strengths, gaps, stale assumptions, calibration biases'
    )
    profile_parser.add_argument('--project-id', help='Project ID (optional, auto-detected from CWD)')
    profile_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    profile_parser.add_argument('--for-ai', action='store_true', help='Generate compact AI-readable summary')

    # lens-ingest
    ingest_parser = subparsers.add_parser(
        'lens-ingest',
        aliases=['li'],
        help='Extract, chunk, and embed source content into docs collection'
    )
    ingest_parser.add_argument('source', help='URL, PDF path, file path, or "-" for stdin')
    ingest_parser.add_argument('--project-id', help='Project ID (optional, auto-detected)')
    ingest_parser.add_argument('--chunk-size', type=int, default=512, help='Tokens per chunk (default: 512)')
    ingest_parser.add_argument('--overlap', type=int, default=64, help='Overlap tokens (default: 64)')
    ingest_parser.add_argument('--dry-run', action='store_true', help='Extract and chunk only, do not embed')
    ingest_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')

    # lens-delta
    delta_parser = subparsers.add_parser(
        'lens-delta',
        aliases=['ld'],
        help='Score source content against human epistemic profile'
    )
    delta_parser.add_argument('source', help='URL, PDF path, file path, or "-" for stdin')
    delta_parser.add_argument('--project-id', help='Project ID (optional, auto-detected)')
    delta_parser.add_argument('--learn', action='store_true', help='Auto-log artifacts + store HESM beliefs')
    delta_parser.add_argument('--verbose', action='store_true', help='Show full 13-vector HESM per chunk')
    delta_parser.add_argument('--gaps-only', action='store_true', help='Show only chunks matching open unknowns/goals')
    delta_parser.add_argument('--chunk-size', type=int, default=512, help='Tokens per chunk (default: 512)')
    delta_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')

    # lens-status
    status_parser = subparsers.add_parser(
        'lens-status',
        aliases=['ls-status'],
        help='Show lens collection stats and profile summary'
    )
    status_parser.add_argument('--project-id', help='Project ID (optional, auto-detected)')
    status_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
