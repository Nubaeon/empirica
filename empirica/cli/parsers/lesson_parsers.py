"""Lesson management command parsers for Epistemic Procedural Knowledge."""


def add_lesson_parsers(subparsers):
    """Add lesson management command parsers"""

    # lesson-create: Create a new lesson
    lesson_create = subparsers.add_parser(
        'lesson-create',
        help='Create a new lesson from JSON input'
    )
    lesson_create.add_argument('--name', help='Lesson name')
    lesson_create.add_argument('--input', '-i', help='Input JSON file (use "-" for stdin)')
    lesson_create.add_argument('--json', help='Inline JSON data')
    lesson_create.add_argument('--output', choices=['human', 'json'], default='json', help='Output format')

    # lesson-load: Load and display a lesson
    lesson_load = subparsers.add_parser(
        'lesson-load',
        help='Load and display a lesson'
    )
    lesson_load.add_argument('--id', '--lesson-id', dest='lesson_id', required=True, help='Lesson ID (required)')
    lesson_load.add_argument('--steps-only', action='store_true', help='Only show steps')
    lesson_load.add_argument('--output', choices=['human', 'json'], default='json', help='Output format')

    # lesson-list: List all lessons
    lesson_list = subparsers.add_parser(
        'lesson-list',
        help='List all lessons'
    )
    lesson_list.add_argument('--domain', help='Filter by domain')
    lesson_list.add_argument('--limit', type=int, default=20, help='Maximum results (default: 20)')
    lesson_list.add_argument('--output', choices=['human', 'json'], default='json', help='Output format')

    # lesson-search: Search for lessons
    lesson_search = subparsers.add_parser(
        'lesson-search',
        help='Search for lessons by query, vector, or domain'
    )
    lesson_search.add_argument('--query', '-q', help='Semantic search query')
    lesson_search.add_argument('--improves', help='Find lessons that improve this vector (know, do, context, etc.)')
    lesson_search.add_argument('--domain', help='Filter by domain')
    lesson_search.add_argument('--limit', type=int, default=10, help='Maximum results (default: 10)')
    lesson_search.add_argument('--output', choices=['human', 'json'], default='json', help='Output format')

    # lesson-recommend: Get lesson recommendations based on epistemic state
    lesson_recommend = subparsers.add_parser(
        'lesson-recommend',
        help='Get lesson recommendations based on epistemic state'
    )
    lesson_recommend.add_argument('--session-id', help='Session ID to load epistemic state from')
    lesson_recommend.add_argument('--know', type=float, help='Current know vector (0-1)')
    lesson_recommend.add_argument('--do', type=float, help='Current do vector (0-1)')
    lesson_recommend.add_argument('--context', type=float, help='Current context vector (0-1)')
    lesson_recommend.add_argument('--uncertainty', type=float, help='Current uncertainty vector (0-1)')
    lesson_recommend.add_argument('--threshold', type=float, default=0.6, help='Threshold for "acceptable" (default: 0.6)')
    lesson_recommend.add_argument('--output', choices=['human', 'json'], default='json', help='Output format')

    # lesson-path: Get learning path to reach a target lesson
    lesson_path = subparsers.add_parser(
        'lesson-path',
        help='Get learning path to reach a target lesson'
    )
    lesson_path.add_argument('--target', required=True, help='Target lesson ID (required)')
    lesson_path.add_argument('--completed', help='Comma-separated list of already completed lesson IDs')
    lesson_path.add_argument('--output', choices=['human', 'json'], default='json', help='Output format')

    # lesson-replay-start: Start tracking a lesson replay
    lesson_replay_start = subparsers.add_parser(
        'lesson-replay-start',
        help='Start tracking a lesson replay'
    )
    lesson_replay_start.add_argument('--lesson-id', required=True, help='Lesson ID (required)')
    lesson_replay_start.add_argument('--session-id', required=True, help='Session ID (required)')
    lesson_replay_start.add_argument('--ai-id', help='AI agent ID')
    lesson_replay_start.add_argument('--output', choices=['human', 'json'], default='json', help='Output format')

    # lesson-replay-end: End a lesson replay
    lesson_replay_end = subparsers.add_parser(
        'lesson-replay-end',
        help='End a lesson replay and record results'
    )
    lesson_replay_end.add_argument('--replay-id', required=True, help='Replay ID (required)')
    lesson_replay_end.add_argument('--success', action='store_true', help='Mark replay as successful')
    lesson_replay_end.add_argument('--failed', action='store_true', help='Mark replay as failed')
    lesson_replay_end.add_argument('--steps-completed', type=int, default=0, help='Number of steps completed')
    lesson_replay_end.add_argument('--error', help='Error message if failed')
    lesson_replay_end.add_argument('--output', choices=['human', 'json'], default='json', help='Output format')

    # lesson-stats: Show lesson storage statistics
    lesson_stats = subparsers.add_parser(
        'lesson-stats',
        help='Show lesson storage statistics'
    )
    lesson_stats.add_argument('--output', choices=['human', 'json'], default='json', help='Output format')

    # lesson-embed: Embed lessons into Qdrant
    lesson_embed = subparsers.add_parser(
        'lesson-embed',
        help='Embed all lessons into Qdrant for semantic search'
    )
    lesson_embed.add_argument('--force', action='store_true', help='Force re-embed all')
    lesson_embed.add_argument('--output', choices=['human', 'json'], default='json', help='Output format')
