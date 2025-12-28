"""Monitoring command parsers."""


def add_monitor_parsers(subparsers):
    """Add monitoring command parsers"""
    # Unified monitor command (consolidates monitor, monitor-export, monitor-reset, monitor-cost)
    monitor_parser = subparsers.add_parser('monitor', help='Monitoring dashboard and statistics')
    monitor_parser.add_argument('--export', metavar='FILE', help='Export data to file (replaces monitor-export)')
    monitor_parser.add_argument('--reset', action='store_true', help='Reset statistics (replaces monitor-reset)')
    monitor_parser.add_argument('--cost', action='store_true', help='Show cost analysis (replaces monitor-cost)')
    monitor_parser.add_argument('--history', action='store_true', help='Show recent request history')
    monitor_parser.add_argument('--health', action='store_true', help='Include adapter health checks')
    monitor_parser.add_argument('--project', action='store_true', help='Show cost projections (with --cost)')
    monitor_parser.add_argument('--output', choices=['json', 'csv'], default='json', help='Export format (with --export)')
    monitor_parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation (with --reset)')
    monitor_parser.add_argument('--verbose', action='store_true', help='Show detailed stats')

    # Check drift command - detect epistemic drift
    check_drift_parser = subparsers.add_parser('check-drift',
        help='Detect epistemic drift by comparing current state to historical baselines')
    check_drift_parser.add_argument('--session-id', required=True, help='Session UUID to check for drift')
    check_drift_parser.add_argument('--trigger',
        choices=['manual', 'pre_summary', 'post_summary'],
        default='manual',
        help='When check is triggered: manual (default) | pre_summary (save snapshot) | post_summary (compare with snapshot)')
    check_drift_parser.add_argument('--threshold', type=float, default=0.2, help='Drift threshold (default: 0.2)')
    check_drift_parser.add_argument('--lookback', type=int, default=5, help='Number of checkpoints to analyze (default: 5)')
    check_drift_parser.add_argument('--cycle', type=int, help='Investigation cycle number (optional filter)')
    check_drift_parser.add_argument('--round', type=int, help='CHECK round number (optional filter)')
    check_drift_parser.add_argument('--scope-depth', type=float, help='Investigation depth: 0.0=surface scan, 1.0=exhaustive (optional)')
    check_drift_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    check_drift_parser.add_argument('--verbose', action='store_true', help='Show detailed output')

    # MCO load command - load Meta-Agent Configuration Object
    mco_load_parser = subparsers.add_parser('mco-load',
        help='Load MCO (Meta-Agent Configuration Object) configuration')
    mco_load_parser.add_argument('--session-id', help='Session UUID (optional, for inference)')
    mco_load_parser.add_argument('--ai-id', help='AI identifier (optional, for model/persona inference)')
    mco_load_parser.add_argument('--snapshot', help='Path to pre_summary snapshot (for post-compact reload)')
    mco_load_parser.add_argument('--model', help='Explicit model override (claude_haiku, claude_sonnet, gpt4, etc.)')
    mco_load_parser.add_argument('--persona', help='Explicit persona override (researcher, implementer, reviewer, etc.)')
    mco_load_parser.add_argument('--output', choices=['human', 'json'], default='human', help='Output format')
    mco_load_parser.add_argument('--verbose', action='store_true', help='Show detailed output')

    # REMOVED: monitor-export, monitor-reset, monitor-cost
    # Use: monitor --export FILE, monitor --reset, monitor --cost
