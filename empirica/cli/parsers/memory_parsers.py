"""
Memory Management CLI Parsers

Exposes the memory budget infrastructure (attention, context, rollup, information gain)
as first-class CLI commands for epistemic memory management.
"""


def add_memory_parsers(subparsers):
    """Add memory management command parsers."""

    # memory-prime: Allocate attention budget across domains
    prime_parser = subparsers.add_parser(
        'memory-prime',
        help='Allocate attention budget across investigation domains using Shannon info-gain'
    )
    prime_parser.add_argument(
        '--session-id', required=True,
        help='Session ID for budget tracking'
    )
    prime_parser.add_argument(
        '--domains', required=True,
        help='JSON array of domain names, e.g. \'["security", "architecture"]\''
    )
    prime_parser.add_argument(
        '--budget', type=int, default=20,
        help='Total findings budget to allocate (default: 20)'
    )
    prime_parser.add_argument(
        '--know', type=float, default=0.5,
        help='Current know vector (0.0-1.0, default: 0.5)'
    )
    prime_parser.add_argument(
        '--uncertainty', type=float, default=0.5,
        help='Current uncertainty vector (0.0-1.0, default: 0.5)'
    )
    prime_parser.add_argument(
        '--prior-findings', default='{}',
        help='JSON object of prior findings per domain, e.g. \'{"security": 3}\''
    )
    prime_parser.add_argument(
        '--dead-ends', default='{}',
        help='JSON object of dead ends per domain, e.g. \'{"architecture": 1}\''
    )
    prime_parser.add_argument(
        '--persist', action='store_true',
        help='Persist budget to database for later retrieval'
    )
    prime_parser.add_argument(
        '--output', choices=['human', 'json'], default='human',
        help='Output format (default: human)'
    )

    # memory-scope: Scope-based retrieval using context zones
    scope_parser = subparsers.add_parser(
        'memory-scope',
        help='Retrieve memories by scope vectors using zone-tiered access'
    )
    scope_parser.add_argument(
        '--session-id', required=True,
        help='Session ID for context management'
    )
    scope_parser.add_argument(
        '--scope-breadth', type=float, default=0.5,
        help='Scope breadth (0.0=narrow, 1.0=wide). Affects zone selection.'
    )
    scope_parser.add_argument(
        '--scope-duration', type=float, default=0.5,
        help='Scope duration (0.0=ephemeral, 1.0=long-term). Affects priority.'
    )
    scope_parser.add_argument(
        '--zone', choices=['anchor', 'working', 'cache', 'all'], default='all',
        help='Specific zone to query (default: all)'
    )
    scope_parser.add_argument(
        '--content-type',
        help='Filter by content type (finding, unknown, goal, etc.)'
    )
    scope_parser.add_argument(
        '--min-priority', type=float,
        help='Minimum priority score to include'
    )
    scope_parser.add_argument(
        '--output', choices=['human', 'json'], default='human',
        help='Output format (default: human)'
    )

    # memory-value: Prioritize retrieval by information gain
    value_parser = subparsers.add_parser(
        'memory-value',
        help='Retrieve memories ranked by information gain / token cost'
    )
    value_parser.add_argument(
        '--session-id', required=True,
        help='Session ID'
    )
    value_parser.add_argument(
        '--query', required=True,
        help='Query text to match against memories'
    )
    value_parser.add_argument(
        '--budget', type=int, default=5000,
        help='Token budget for retrieval (default: 5000)'
    )
    value_parser.add_argument(
        '--project-id',
        help='Project ID (auto-detected if not provided)'
    )
    value_parser.add_argument(
        '--min-gain', type=float, default=0.1,
        help='Minimum information gain to include (default: 0.1)'
    )
    value_parser.add_argument(
        '--include-eidetic', action='store_true',
        help='Include eidetic (fact) memory'
    )
    value_parser.add_argument(
        '--include-episodic', action='store_true',
        help='Include episodic (narrative) memory'
    )
    value_parser.add_argument(
        '--output', choices=['human', 'json'], default='human',
        help='Output format (default: human)'
    )

    # pattern-check: Real-time pattern sentinel
    pattern_parser = subparsers.add_parser(
        'pattern-check',
        help='Check current approach against dead-ends and mistake patterns (real-time sentinel)'
    )
    pattern_parser.add_argument(
        '--session-id', required=True,
        help='Session ID'
    )
    pattern_parser.add_argument(
        '--approach', required=True,
        help='Description of current approach to validate'
    )
    pattern_parser.add_argument(
        '--project-id',
        help='Project ID (auto-detected if not provided)'
    )
    pattern_parser.add_argument(
        '--know', type=float, default=0.5,
        help='Current know vector (for mistake risk calculation)'
    )
    pattern_parser.add_argument(
        '--uncertainty', type=float, default=0.5,
        help='Current uncertainty vector (for mistake risk calculation)'
    )
    pattern_parser.add_argument(
        '--threshold', type=float, default=0.7,
        help='Similarity threshold for pattern matching (default: 0.7)'
    )
    pattern_parser.add_argument(
        '--output', choices=['human', 'json'], default='human',
        help='Output format (default: human)'
    )

    # session-rollup: Aggregate epistemic state across parallel agents
    rollup_parser = subparsers.add_parser(
        'session-rollup',
        help='Aggregate findings and epistemic state from parallel sub-agents'
    )
    rollup_parser.add_argument(
        '--parent-session-id', required=True,
        help='Parent session ID to aggregate children for'
    )
    rollup_parser.add_argument(
        '--budget', type=int, default=20,
        help='Max findings to accept (default: 20)'
    )
    rollup_parser.add_argument(
        '--min-score', type=float, default=0.3,
        help='Minimum quality score to accept finding (default: 0.3)'
    )
    rollup_parser.add_argument(
        '--jaccard-threshold', type=float, default=0.7,
        help='Jaccard similarity for dedup (default: 0.7)'
    )
    rollup_parser.add_argument(
        '--semantic-dedup', action='store_true',
        help='Use Qdrant semantic dedup in addition to Jaccard'
    )
    rollup_parser.add_argument(
        '--project-id',
        help='Project ID for semantic dedup (auto-detected if not provided)'
    )
    rollup_parser.add_argument(
        '--log-decisions', action='store_true',
        help='Log accept/reject decisions to database'
    )
    rollup_parser.add_argument(
        '--output', choices=['human', 'json'], default='human',
        help='Output format (default: human)'
    )

    # memory-report: Get budget report (like /proc/meminfo)
    report_parser = subparsers.add_parser(
        'memory-report',
        help='Get context budget report (token usage by zone)'
    )
    report_parser.add_argument(
        '--session-id', required=True,
        help='Session ID'
    )
    report_parser.add_argument(
        '--output', choices=['human', 'json'], default='human',
        help='Output format (default: human)'
    )
