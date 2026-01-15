"""Trajectory analysis command parsers (experimental)."""


def add_trajectory_parsers(subparsers):
    """Add trajectory analysis command parsers"""
    # Trajectory show command - display trajectory for a session
    trajectory_show_parser = subparsers.add_parser(
        'trajectory-show',
        help='Show vector trajectory for a session (experimental)'
    )
    trajectory_show_parser.add_argument(
        '--session-id',
        help='Session ID to show trajectory for'
    )
    trajectory_show_parser.add_argument(
        '--pattern',
        choices=['breakthrough', 'dead_end', 'stable', 'oscillating', 'unknown'],
        help='Filter by pattern type'
    )
    trajectory_show_parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Maximum trajectories to show (default: 10)'
    )
    trajectory_show_parser.add_argument(
        '--output',
        choices=['human', 'json'],
        default='human',
        help='Output format'
    )

    # Trajectory stats command - show pattern distribution
    trajectory_stats_parser = subparsers.add_parser(
        'trajectory-stats',
        help='Show trajectory pattern statistics (experimental)'
    )
    trajectory_stats_parser.add_argument(
        '--output',
        choices=['human', 'json'],
        default='human',
        help='Output format'
    )

    # Trajectory backfill command - populate from historical data
    trajectory_backfill_parser = subparsers.add_parser(
        'trajectory-backfill',
        help='Backfill trajectories from historical git notes (experimental)'
    )
    trajectory_backfill_parser.add_argument(
        '--min-phases',
        type=int,
        default=2,
        help='Minimum phases required (default: 2)'
    )
    trajectory_backfill_parser.add_argument(
        '--analyze',
        action='store_true',
        help='Run pattern analysis after backfill'
    )
    trajectory_backfill_parser.add_argument(
        '--output',
        choices=['human', 'json'],
        default='human',
        help='Output format'
    )
