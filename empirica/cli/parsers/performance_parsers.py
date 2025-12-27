"""Performance command parsers."""


def add_performance_parsers(subparsers):
    """Add performance command parsers"""
    # Performance command (consolidates performance + benchmark)
    performance_parser = subparsers.add_parser('performance', help='Analyze performance or run benchmarks')
    performance_parser.add_argument('--benchmark', action='store_true', help='Run performance benchmarks (replaces benchmark command)')
    performance_parser.add_argument('--target', default='system', help='Performance analysis target')
    performance_parser.add_argument('--type', default='comprehensive', help='Benchmark/analysis type')
    performance_parser.add_argument('--iterations', type=int, default=10, help='Number of iterations (for benchmarks)')
    performance_parser.add_argument('--memory', action='store_true', default=True, help='Include memory analysis')
    performance_parser.add_argument('--context', help='JSON context data')
    performance_parser.add_argument('--detailed', action='store_true', help='Show detailed metrics')
    performance_parser.add_argument('--verbose', action='store_true', help='Show detailed results')

    # REMOVED: benchmark command - use performance --benchmark instead
