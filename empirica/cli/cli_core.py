"""
CLI Core - Main entry point and argument parsing for modular Empirica CLI

This module provides the main() function and argument parser setup for the
modularized Empirica CLI, replacing the monolithic cli.py structure.
"""

import argparse
import sys
import time
from .cli_utils import handle_cli_error, print_header
from .command_handlers import *


def create_argument_parser():
    """Create and configure the main argument parser"""
    parser = argparse.ArgumentParser(
        prog='empirica',
        description='🧠 Empirica - Semantic Self-Aware AI Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  empirica session-create --ai-id myai          # Create session
  empirica preflight --session-id xyz           # Execute PREFLIGHT
  empirica check --session-id xyz               # Execute CHECK gate
  empirica postflight --session-id xyz          # Execute POSTFLIGHT
  empirica goals-create --session-id xyz        # Create goal
        """
    )
    
    # Global options
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--config', help='Path to configuration file')
    
    # Create subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Session commands (use session-create for session initialization)
    _add_session_parsers(subparsers)

    # Assessment commands
    _add_assessment_parsers(subparsers)
    
    # Cascade commands
    _add_cascade_parsers(subparsers)
    
    # Investigation commands
    _add_investigation_parsers(subparsers)
    
    # Performance commands
    _add_performance_parsers(subparsers)
    
    # Component commands
    _add_component_parsers(subparsers)
    
    # Utility commands
    _add_utility_parsers(subparsers)
    
    # Config commands
    _add_config_parsers(subparsers)
    
    # Profile commands
    _add_profile_parsers(subparsers)
    
    # Monitor commands
    _add_monitor_parsers(subparsers)

    # MCP commands - REMOVED (no longer needed)
    # _add_mcp_parsers(subparsers)

    # Action commands (INVESTIGATE and ACT tracking)
    _add_action_parsers(subparsers)
    
    # Checkpoint commands (Phase 2)
    _add_checkpoint_parsers(subparsers)
    
    # User interface commands (for human users)
    _add_user_interface_parsers(subparsers)
    
    return parser


def _add_assessment_parsers(subparsers):
    """Add assessment command parsers"""
    # Main assess command
    
    # Metacognitive assessment

def _add_cascade_parsers(subparsers):
    """Add cascade command parsers (DEPRECATED - use MCP tools instead)
    
    The 'cascade' command was part of ModalitySwitcher plugin.
    For CASCADE workflow, use MCP tools:
    - empirica execute-preflight
    - empirica execute-check  
    - empirica execute-postflight
    
    This function is kept for backward compatibility but does nothing.
    """
    # Deprecated - CASCADE workflow now uses MCP tools
    pass
    
    # Enhanced decision analysis command with ModalitySwitcher
    # Preflight command
    preflight_parser = subparsers.add_parser('preflight', help='Execute preflight epistemic assessment')
    preflight_parser.add_argument('prompt', help='Task description to assess')
    preflight_parser.add_argument('--session-id', help='Optional session ID (auto-generated if not provided)')
    preflight_parser.add_argument('--ai-id', default='empirica_cli', help='AI identifier for session tracking')
    preflight_parser.add_argument('--no-git', action='store_true', help='Disable automatic git checkpoint creation')
    preflight_parser.add_argument('--sign', action='store_true', help='Sign assessment with AI keypair (Phase 2: EEP-1)')
    preflight_parser.add_argument('--prompt-only', action='store_true', help='Return ONLY the self-assessment prompt as JSON (no waiting, for genuine AI assessment)')
    preflight_parser.add_argument('--assessment-json', help='Genuine AI self-assessment JSON (required for genuine assessment)')
    preflight_parser.add_argument('--sentinel-assess', action='store_true', help='Route to Sentinel assessment system (future feature)')
    preflight_parser.add_argument('--json', action='store_const', const='json', dest='output_format', help='Output as JSON (deprecated, use --output json)')
    preflight_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    preflight_parser.add_argument('--compact', action='store_true', help='Output as single-line key=value')
    preflight_parser.add_argument('--kv', action='store_true', help='Output as multi-line key=value')
    preflight_parser.add_argument('--verbose', action='store_true', help='Show detailed assessment')
    preflight_parser.add_argument('--quiet', action='store_true', help='Quiet mode (requires --assessment-json)')
    
    # Postflight command
    postflight_parser = subparsers.add_parser('postflight', help='Execute postflight epistemic reassessment')
    postflight_parser.add_argument('session_id', help='Session ID from preflight')
    postflight_parser.add_argument('--summary', help='Task completion summary')
    postflight_parser.add_argument('--ai-id', help='AI identifier for session tracking (should match preflight)')
    postflight_parser.add_argument('--no-git', action='store_true', help='Disable automatic git checkpoint creation')
    postflight_parser.add_argument('--sign', action='store_true', help='Sign assessment with AI keypair (Phase 2: EEP-1)')
    postflight_parser.add_argument('--prompt-only', action='store_true', help='Return ONLY the self-assessment prompt as JSON (no waiting, for genuine AI assessment)')
    postflight_parser.add_argument('--assessment-json', help='Genuine AI self-assessment JSON (required for genuine assessment)')
    postflight_parser.add_argument('--sentinel-assess', action='store_true', help='Route to Sentinel assessment system (future feature)')
    postflight_parser.add_argument('--json', action='store_const', const='json', dest='output_format', help='Output as JSON (deprecated, use --output json)')
    postflight_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    postflight_parser.add_argument('--compact', action='store_true', help='Output as single-line key=value')
    postflight_parser.add_argument('--kv', action='store_true', help='Output as multi-line key=value')
    postflight_parser.add_argument('--verbose', action='store_true', help='Show detailed delta analysis')
    postflight_parser.add_argument('--quiet', action='store_true', help='Quiet mode (requires --assessment-json)')
    
    # Workflow command
    workflow_parser = subparsers.add_parser('workflow', help='Execute full preflight→work→postflight workflow')
    workflow_parser.add_argument('prompt', help='Task description')
    workflow_parser.add_argument('--auto', action='store_true', help='Skip manual pause between steps')
    workflow_parser.add_argument('--verbose', action='store_true', help='Show detailed workflow steps')

    # NEW: MCP v2 Workflow Commands (Critical Priority)
    
    # Preflight submit command
    preflight_submit_parser = subparsers.add_parser('preflight-submit', help='Submit preflight assessment results')
    preflight_submit_parser.add_argument('--session-id', required=True, help='Session ID')
    preflight_submit_parser.add_argument('--vectors', required=True, help='Epistemic vectors as JSON string or dict')
    preflight_submit_parser.add_argument('--reasoning', help='Reasoning for assessment scores')
    preflight_submit_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Execute epistemic check assessment')
    check_parser.add_argument('--session-id', required=True, help='Session ID')
    check_parser.add_argument('--findings', required=True, help='Investigation findings as JSON array')
    # Create mutually exclusive group for unknowns (accept either name)
    unknowns_group = check_parser.add_mutually_exclusive_group(required=True)
    unknowns_group.add_argument('--unknowns', dest='unknowns', help='Remaining unknowns as JSON array')
    unknowns_group.add_argument('--remaining-unknowns', dest='unknowns', help='Alias for --unknowns')
    check_parser.add_argument('--confidence', type=float, required=True, help='Confidence score (0.0-1.0)')
    check_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    check_parser.add_argument('--verbose', action='store_true', help='Show detailed analysis')
    
    # Check submit command
    check_submit_parser = subparsers.add_parser('check-submit', help='Submit check assessment results')
    check_submit_parser.add_argument('--session-id', required=True, help='Session ID')
    check_submit_parser.add_argument('--vectors', required=True, help='Epistemic vectors as JSON string or dict')
    check_submit_parser.add_argument('--decision', required=True, choices=['proceed', 'investigate', 'proceed_with_caution'], help='Decision made')
    check_submit_parser.add_argument('--reasoning', help='Reasoning for decision')
    check_submit_parser.add_argument('--cycle', type=int, help='Investigation cycle number')
    check_submit_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    
    # Postflight submit command
    postflight_submit_parser = subparsers.add_parser('postflight-submit', help='Submit postflight assessment results')
    postflight_submit_parser.add_argument('--session-id', required=True, help='Session ID')
    postflight_submit_parser.add_argument('--vectors', required=True, help='Epistemic vectors as JSON string or dict')
    postflight_submit_parser.add_argument('--reasoning', help='Description of what changed from preflight (was --changes, now unified with preflight-submit)')
    postflight_submit_parser.add_argument('--changes', help='Alias for --reasoning (deprecated, use --reasoning)', dest='reasoning')
    postflight_submit_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')


def _add_investigation_parsers(subparsers):
    """Add investigation command parsers"""
    # Main investigate command (consolidates investigate + analyze)
    investigate_parser = subparsers.add_parser('investigate', help='Investigate file/directory/concept')
    investigate_parser.add_argument('target', help='Target to investigate')
    investigate_parser.add_argument('--type', default='auto',
                                   choices=['auto', 'file', 'directory', 'concept', 'comprehensive'],
                                   help='Investigation type. Use "comprehensive" for deep analysis (replaces analyze command)')
    investigate_parser.add_argument('--context', help='JSON context data')
    investigate_parser.add_argument('--detailed', action='store_true', help='Show detailed investigation')
    investigate_parser.add_argument('--verbose', action='store_true', help='Show detailed investigation')

    # REMOVED: analyze command - use investigate --type=comprehensive instead


def _add_performance_parsers(subparsers):
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


def _add_component_parsers(subparsers):
    """Add component command parsers"""
    # List components command
    # Explain component command
    # Demo component command
def _add_utility_parsers(subparsers):
    """Add utility command parsers"""
    # Feedback command
    # Goal analysis command
    goal_parser = subparsers.add_parser('goal-analysis', help='Analyze goal feasibility')
    goal_parser.add_argument('goal', help='Goal to analyze')
    goal_parser.add_argument('--context', help='JSON context data')
    goal_parser.add_argument('--verbose', action='store_true', help='Show detailed analysis')
    
    # Calibration command
    # UVL command
def _add_config_parsers(subparsers):
    """Add configuration command parsers"""
    # Unified config command (consolidates config-init, config-show, config-validate, config-get, config-set)
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_parser.add_argument('key', nargs='?', help='Configuration key (dot notation, e.g., routing.default_strategy)')
    config_parser.add_argument('value', nargs='?', help='Value to set (if key provided)')
    config_parser.add_argument('--init', action='store_true', help='Initialize configuration (replaces config-init)')
    config_parser.add_argument('--validate', action='store_true', help='Validate configuration (replaces config-validate)')
    config_parser.add_argument('--section', help='Show specific section (e.g., routing, adapters)')
    config_parser.add_argument('--format', choices=['yaml', 'json'], default='yaml', help='Output format')
    config_parser.add_argument('--force', action='store_true', help='Overwrite existing config (with --init)')
    config_parser.add_argument('--verbose', action='store_true', help='Show detailed output')

    # REMOVED: config-init, config-show, config-validate, config-get, config-set
    # Use: config --init, config (no args), config --validate, config KEY, config KEY VALUE


def _add_monitor_parsers(subparsers):
    """Add monitoring command parsers"""
    # Unified monitor command (consolidates monitor, monitor-export, monitor-reset, monitor-cost)
    monitor_parser = subparsers.add_parser('monitor', help='Monitoring dashboard and statistics')
    monitor_parser.add_argument('--export', metavar='FILE', help='Export data to file (replaces monitor-export)')
    monitor_parser.add_argument('--reset', action='store_true', help='Reset statistics (replaces monitor-reset)')
    monitor_parser.add_argument('--cost', action='store_true', help='Show cost analysis (replaces monitor-cost)')
    monitor_parser.add_argument('--history', action='store_true', help='Show recent request history')
    monitor_parser.add_argument('--health', action='store_true', help='Include adapter health checks')
    monitor_parser.add_argument('--project', action='store_true', help='Show cost projections (with --cost)')
    monitor_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format (with --export)')
    monitor_parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation (with --reset)')
    monitor_parser.add_argument('--verbose', action='store_true', help='Show detailed stats')

    # REMOVED: monitor-export, monitor-reset, monitor-cost
    # Use: monitor --export FILE, monitor --reset, monitor --cost


def _add_mcp_parsers(subparsers):
    """Add MCP server command parsers - REMOVED: MCP server lifecycle managed by IDE/CLI"""
    # All MCP server commands (mcp-start, mcp-stop, mcp-status, mcp-test, mcp-list-tools, mcp-call)
    # removed as they are redundant - IDE/CLI manages MCP server lifecycle
    pass


def _add_session_parsers(subparsers):
    """Add session management command parsers"""
    # Sessions list command
    sessions_list_parser = subparsers.add_parser('sessions-list', help='List all sessions')
    sessions_list_parser.add_argument('--limit', type=int, default=50, help='Maximum sessions to show')
    sessions_list_parser.add_argument('--verbose', action='store_true', help='Show detailed info')
    sessions_list_parser.add_argument('--output', choices=['text', 'json'], default='text', help='Output format')
    
    # Sessions show command
    sessions_show_parser = subparsers.add_parser('sessions-show', help='Show detailed session info')
    sessions_show_parser.add_argument('session_id', nargs='?', help='Session ID or alias (latest, latest:active, latest:<ai_id>, latest:active:<ai_id>)')
    sessions_show_parser.add_argument('--session-id', dest='session_id_named', help='Session ID (alternative to positional argument)')
    sessions_show_parser.add_argument('--verbose', action='store_true', help='Show all vectors and cascades')
    sessions_show_parser.add_argument('--output', choices=['text', 'json'], default='text', help='Output format')

    # Sessions export command
    sessions_export_parser = subparsers.add_parser('sessions-export', help='Export session to JSON')
    sessions_export_parser.add_argument('session_id', nargs='?', help='Session ID or alias (latest, latest:active, latest:<ai_id>)')
    sessions_export_parser.add_argument('--session-id', dest='session_id_named', help='Session ID (alternative to positional argument)')
    sessions_export_parser.add_argument('--output', '-o', help='Output file path (default: session_<id>.json)')
    
    # Session end command
    # session-end removed - use handoff-create instead (better parameter names, already in MCP)


def _add_action_parsers(subparsers):
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


def _add_checkpoint_parsers(subparsers):
    """Add git checkpoint management command parsers (Phase 2)"""
    # Checkpoint create command
    checkpoint_create_parser = subparsers.add_parser(
        'checkpoint-create',
        help='Create git checkpoint for session (Phase 1.5/2.0)'
    )
    checkpoint_create_parser.add_argument('--session-id', required=True, help='Session ID')
    checkpoint_create_parser.add_argument(
        '--phase',
        choices=['PREFLIGHT', 'CHECK', 'ACT', 'POSTFLIGHT'],
        required=True,
        help='Workflow phase'
    )
    checkpoint_create_parser.add_argument('--round', type=int, required=True, help='Round number')
    checkpoint_create_parser.add_argument('--metadata', help='JSON metadata (optional)')
    
    # Checkpoint load command
    checkpoint_load_parser = subparsers.add_parser(
        'checkpoint-load',
        help='Load latest checkpoint for session'
    )
    checkpoint_load_parser.add_argument('--session-id', required=True, help='Session ID')
    checkpoint_load_parser.add_argument('--max-age', type=int, default=24, help='Max age in hours (default: 24)')
    checkpoint_load_parser.add_argument('--phase', help='Filter by specific phase (optional)')
    checkpoint_load_parser.add_argument(
        '--output',
        choices=['table', 'json'],
        default='table',
        help='Output format (also accepts --output json)'
    )
    # Add backward compatibility with --format
    checkpoint_load_parser.add_argument(
        '--format',
        dest='output',
        choices=['json', 'table'],
        help='Output format (deprecated, use --output)'
    )
    
    # Checkpoint list command
    checkpoint_list_parser = subparsers.add_parser(
        'checkpoint-list',
        help='List checkpoints for session'
    )
    checkpoint_list_parser.add_argument('--session-id', help='Session ID (optional, lists all if omitted)')
    checkpoint_list_parser.add_argument('--limit', type=int, default=10, help='Maximum checkpoints to show')
    checkpoint_list_parser.add_argument('--phase', help='Filter by phase (optional)')
    
    # Checkpoint diff command
    checkpoint_diff_parser = subparsers.add_parser(
        'checkpoint-diff',
        help='Show vector differences from last checkpoint'
    )
    checkpoint_diff_parser.add_argument('--session-id', required=True, help='Session ID')
    checkpoint_diff_parser.add_argument('--threshold', type=float, default=0.15, help='Significance threshold')
    checkpoint_diff_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    
    # Efficiency report command
    efficiency_report_parser = subparsers.add_parser(
        'efficiency-report',
        help='Generate token efficiency report (Phase 1.5/2.0)'
    )
    efficiency_report_parser.add_argument('--session-id', required=True, help='Session ID')
    efficiency_report_parser.add_argument(
        '--format',
        choices=['json', 'markdown', 'csv'],
        default='markdown',
        help='Report format'
    )
    efficiency_report_parser.add_argument('--output', '-o', help='Save to file (optional)')

    # Checkpoint Signing Commands (Phase 2 - Crypto)
    
    # Checkpoint sign command
    checkpoint_sign_parser = subparsers.add_parser(
        'checkpoint-sign',
        help='Sign checkpoint with AI identity (Phase 2 - Crypto)'
    )
    checkpoint_sign_parser.add_argument('--session-id', required=True, help='Session ID')
    checkpoint_sign_parser.add_argument(
        '--phase',
        choices=['PREFLIGHT', 'CHECK', 'ACT', 'POSTFLIGHT'],
        required=True,
        help='Workflow phase'
    )
    checkpoint_sign_parser.add_argument('--round', type=int, required=True, help='Round number')
    checkpoint_sign_parser.add_argument('--ai-id', required=True, help='AI identity to sign with')
    checkpoint_sign_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    
    # Checkpoint verify command
    checkpoint_verify_parser = subparsers.add_parser(
        'checkpoint-verify',
        help='Verify signed checkpoint (Phase 2 - Crypto)'
    )
    checkpoint_verify_parser.add_argument('--session-id', required=True, help='Session ID')
    checkpoint_verify_parser.add_argument(
        '--phase',
        choices=['PREFLIGHT', 'CHECK', 'ACT', 'POSTFLIGHT'],
        required=True,
        help='Workflow phase'
    )
    checkpoint_verify_parser.add_argument('--round', type=int, required=True, help='Round number')
    checkpoint_verify_parser.add_argument('--ai-id', help='AI identity (uses embedded public key if omitted)')
    checkpoint_verify_parser.add_argument('--public-key', help='Public key hex (overrides AI ID)')
    checkpoint_verify_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    
    # Checkpoint signatures command
    checkpoint_signatures_parser = subparsers.add_parser(
        'checkpoint-signatures',
        help='List all signed checkpoints (Phase 2 - Crypto)'
    )
    checkpoint_signatures_parser.add_argument('--session-id', help='Filter by session ID (optional)')
    checkpoint_signatures_parser.add_argument('--ai-id', help='AI identity (only needed if no local identities exist)')
    checkpoint_signatures_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')

    # Handoff Reports Commands (Phase 1.6)
    
    # Handoff create command
    handoff_create_parser = subparsers.add_parser(
        'handoff-create',
        help='Create handoff report: epistemic (with CASCADE deltas) or planning (documentation-only)'
    )
    handoff_create_parser.add_argument('--session-id', required=True, help='Session UUID')
    handoff_create_parser.add_argument('--task-summary', required=True, help='What was accomplished (2-3 sentences)')
    handoff_create_parser.add_argument('--summary', dest='task_summary', help='Alias for --task-summary')
    handoff_create_parser.add_argument('--key-findings', required=True, help='JSON array of findings')
    handoff_create_parser.add_argument('--findings', dest='key_findings', help='Alias for --key-findings')
    handoff_create_parser.add_argument('--remaining-unknowns', help='JSON array of unknowns (optional)')
    handoff_create_parser.add_argument('--unknowns', dest='remaining_unknowns', help='Alias for --remaining-unknowns')
    handoff_create_parser.add_argument('--next-session-context', required=True, help='Critical context for next session')
    handoff_create_parser.add_argument('--artifacts', help='JSON array of files created (optional)')
    handoff_create_parser.add_argument('--planning-only', action='store_true', help='Create planning handoff (no CASCADE workflow required) instead of epistemic handoff')
    handoff_create_parser.add_argument('--output', choices=['text', 'json'], default='text', help='Output format')
    
    # Handoff query command
    handoff_query_parser = subparsers.add_parser(
        'handoff-query',
        help='Query handoff reports'
    )
    handoff_query_parser.add_argument('--session-id', help='Specific session UUID')
    handoff_query_parser.add_argument('--ai-id', help='Filter by AI ID')
    handoff_query_parser.add_argument('--limit', type=int, default=5, help='Number of results (default: 5)')
    handoff_query_parser.add_argument('--output', choices=['text', 'json'], default='text', help='Output format')

    # NEW: Goal Management Commands (MCP v2 Integration)
    
    # Goals create command
    goals_create_parser = subparsers.add_parser('goals-create', help='Create new goal')
    goals_create_parser.add_argument('--session-id', required=True, help='Session ID')
    goals_create_parser.add_argument('--ai-id', default='empirica_cli', help='AI identifier')
    goals_create_parser.add_argument('--objective', required=True, help='Goal objective text')
    goals_create_parser.add_argument('--scope-breadth', type=float, default=0.3, help='Goal breadth (0.0-1.0, how wide the goal spans)')
    goals_create_parser.add_argument('--scope-duration', type=float, default=0.2, help='Goal duration (0.0-1.0, expected lifetime)')
    goals_create_parser.add_argument('--scope-coordination', type=float, default=0.1, help='Goal coordination (0.0-1.0, multi-agent coordination needed)')
    goals_create_parser.add_argument('--success-criteria', help='Success criteria as JSON array')
    goals_create_parser.add_argument('--estimated-complexity', type=float, help='Complexity estimate (0.0-1.0)')
    goals_create_parser.add_argument('--constraints', help='Constraints as JSON object')
    goals_create_parser.add_argument('--metadata', help='Metadata as JSON object')
    goals_create_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    
    # Goals add-subtask command
    goals_add_subtask_parser = subparsers.add_parser('goals-add-subtask', help='Add subtask to existing goal')
    goals_add_subtask_parser.add_argument('--goal-id', required=True, help='Goal UUID')
    goals_add_subtask_parser.add_argument('--description', required=True, help='Subtask description')
    goals_add_subtask_parser.add_argument('--importance', choices=['critical', 'high', 'medium', 'low'], default='medium', help='Epistemic importance')
    goals_add_subtask_parser.add_argument('--dependencies', help='Dependencies as JSON array')
    goals_add_subtask_parser.add_argument('--estimated-tokens', type=int, help='Estimated token usage')
    goals_add_subtask_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    
    # Goals complete-subtask command
    goals_complete_subtask_parser = subparsers.add_parser('goals-complete-subtask', help='Mark subtask as complete')
    goals_complete_subtask_parser.add_argument('--task-id', required=True, help='Subtask UUID')
    goals_complete_subtask_parser.add_argument('--evidence', help='Completion evidence (commit hash, file path, etc.)')
    goals_complete_subtask_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    
    # Goals progress command
    goals_progress_parser = subparsers.add_parser('goals-progress', help='Get goal completion progress')
    goals_progress_parser.add_argument('--goal-id', required=True, help='Goal UUID')
    goals_progress_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    
    # Goals list command
    goals_list_parser = subparsers.add_parser('goals-list', help='List goals')
    goals_list_parser.add_argument('--session-id', help='Filter by session ID')
    goals_list_parser.add_argument('--scope-breadth-min', type=float, help='Filter by minimum breadth (0.0-1.0)')
    goals_list_parser.add_argument('--scope-breadth-max', type=float, help='Filter by maximum breadth (0.0-1.0)')
    goals_list_parser.add_argument('--scope-duration-min', type=float, help='Filter by minimum duration (0.0-1.0)')
    goals_list_parser.add_argument('--scope-duration-max', type=float, help='Filter by maximum duration (0.0-1.0)')
    goals_list_parser.add_argument('--scope-coordination-min', type=float, help='Filter by minimum coordination (0.0-1.0)')
    goals_list_parser.add_argument('--scope-coordination-max', type=float, help='Filter by maximum coordination (0.0-1.0)')
    goals_list_parser.add_argument('--completed', action='store_true', help='Filter by completion status')
    goals_list_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    
    # Goals-discover command (NEW: Phase 1 - Cross-AI Goal Discovery)
    goals_discover_parser = subparsers.add_parser('goals-discover', help='Discover goals from other AIs via git')
    goals_discover_parser.add_argument('--from-ai-id', help='Filter by AI creator')
    goals_discover_parser.add_argument('--session-id', help='Filter by session')
    goals_discover_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    
    # Goals-resume command (NEW: Phase 1 - Cross-AI Goal Handoff)
    goals_resume_parser = subparsers.add_parser('goals-resume', help='Resume another AI\'s goal')
    goals_resume_parser.add_argument('goal_id', help='Goal ID to resume')
    goals_resume_parser.add_argument('--ai-id', default='empirica_cli', help='Your AI identifier')
    goals_resume_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    
    # Identity commands (NEW: Phase 2 - Cryptographic Trust / EEP-1)
    identity_create_parser = subparsers.add_parser('identity-create', help='Create new AI identity with Ed25519 keypair')
    identity_create_parser.add_argument('--ai-id', required=True, help='AI identifier')
    identity_create_parser.add_argument('--overwrite', action='store_true', help='Overwrite existing identity')
    identity_create_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    
    identity_list_parser = subparsers.add_parser('identity-list', help='List all AI identities')
    identity_list_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    
    identity_export_parser = subparsers.add_parser('identity-export', help='Export public key for sharing')
    identity_export_parser.add_argument('--ai-id', required=True, help='AI identifier')
    identity_export_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    
    identity_verify_parser = subparsers.add_parser('identity-verify', help='Verify signed session')
    identity_verify_parser.add_argument('session_id', help='Session ID to verify')
    identity_verify_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    
    # Sessions resume command
    sessions_resume_parser = subparsers.add_parser('sessions-resume', help='Resume previous sessions')
    sessions_resume_parser.add_argument('--ai-id', help='Filter by AI ID')
    sessions_resume_parser.add_argument('--count', type=int, default=1, help='Number of sessions to retrieve')
    sessions_resume_parser.add_argument('--detail-level', choices=['summary', 'detailed', 'full'], default='summary', help='Detail level')
    sessions_resume_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')

    # Session create command (replaces bootstrap)
    session_create_parser = subparsers.add_parser('session-create', help='Create new session')
    session_create_parser.add_argument('--ai-id', required=True, help='AI agent identifier')
    session_create_parser.add_argument('--user-id', help='User identifier')
    session_create_parser.add_argument('--bootstrap-level', type=int, default=1, help='Bootstrap level (0-4)')
    session_create_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')


def _add_profile_parsers(subparsers):
    """Add profile management command parsers"""
    # Profile list command
    profile_list_parser = subparsers.add_parser('profile-list', help='List available profiles')
    profile_list_parser.add_argument('--verbose', action='store_true', help='Show detailed profile information')
    
    # Profile show command
    profile_show_parser = subparsers.add_parser('profile-show', help='Show profile details')
    profile_show_parser.add_argument('profile_name', help='Profile name to show details for')
    profile_show_parser.add_argument('--verbose', action='store_true', help='Show all configuration details')
    
    # Profile create command
    profile_create_parser = subparsers.add_parser('profile-create', help='Create new profile')
    profile_create_parser.add_argument('profile_name', help='Name of the new profile')
    profile_create_parser.add_argument('--ai-model', help='Default AI model for this profile')
    profile_create_parser.add_argument('--domain', help='Default domain context')
    profile_create_parser.add_argument('--description', help='Profile description')
    profile_create_parser.add_argument('--verbose', action='store_true', help='Show creation details')
    
    # Profile set-default command
    profile_default_parser = subparsers.add_parser('profile-set-default', help='Set default profile')
    profile_default_parser.add_argument('profile_name', help='Profile name to set as default')
    profile_default_parser.add_argument('--verbose', action='store_true', help='Show update details')


def _add_user_interface_parsers(subparsers):
    """Add user interface commands for human terminal users"""
    
    # Onboard command - interactive intro to Empirica
    onboard_parser = subparsers.add_parser('onboard', help='Interactive introduction to Empirica')
    
    # Ask command - simple question answering
    ask_parser = subparsers.add_parser('ask', help='Ask a question (simple query interface for human users)')
    ask_parser.add_argument('query', help='Question to ask')
    ask_parser.add_argument('--adapter', help='Force specific adapter (qwen, minimax, gemini, etc.)')
    ask_parser.add_argument('--model', help='Force specific model (e.g., qwen-coder-turbo)')
    ask_parser.add_argument('--strategy', choices=['epistemic', 'cost', 'latency', 'quality', 'balanced'],
                           default='epistemic', help='Routing strategy (default: epistemic)')
    ask_parser.add_argument('--session', help='Session ID for conversation tracking (auto-generated if not provided)')
    ask_parser.add_argument('--temperature', type=float, default=0.7, help='Sampling temperature (0.0-1.0)')
    ask_parser.add_argument('--max-tokens', type=int, default=2000, help='Maximum response tokens')
    ask_parser.add_argument('--no-save', dest='save', action='store_false', help='Don\'t save to session database')
    ask_parser.add_argument('--verbose', action='store_true', help='Show routing details')
    
    # Chat command - interactive multi-turn conversation
    chat_parser = subparsers.add_parser('chat', help='Interactive chat session (REPL for human users)')
    chat_parser.add_argument('--adapter', help='Force specific adapter')
    chat_parser.add_argument('--model', help='Force specific model')
    chat_parser.add_argument('--strategy', choices=['epistemic', 'cost', 'latency', 'quality', 'balanced'],
                            default='epistemic', help='Routing strategy')
    chat_parser.add_argument('--session', help='Session ID (creates new if doesn\'t exist)')
    chat_parser.add_argument('--resume', help='Resume existing session by ID')
    chat_parser.add_argument('--no-save', dest='save', action='store_false', help='Don\'t save conversation')
    chat_parser.add_argument('--no-uvl', dest='show_uvl', action='store_false', help='Disable UVL visual indicators')
    chat_parser.add_argument('--uvl-verbose', action='store_true', help='Show detailed routing decisions')
    chat_parser.add_argument('--uvl-stream', action='store_true', help='Emit UVL JSON stream for visualization')
    chat_parser.add_argument('--verbose', action='store_true', help='Show routing details')



def main(args=None):
    """Main CLI entry point"""
    if args is None:
        args = sys.argv[1:]
    
    parser = create_argument_parser()
    parsed_args = parser.parse_args(args)
    
    # Handle no command case
    if not parsed_args.command:
        parser.print_help()
        return 0
    
    # Set quiet mode if specified
    if getattr(parsed_args, 'quiet', False):
        import os
        os.environ['EMPIRICA_QUIET'] = '1'
    
    start_time = time.time()
    
    try:
        # Route to appropriate command handler
        command_map = {
            # Bootstrap commands (consolidated: bootstrap-system and onboard removed)

            # Assessment commands
            
            # Cascade commands (core workflow via MCP)
            # 'cascade': removed - use MCP tools: execute_preflight, execute_check, execute_postflight
            'preflight': handle_preflight_command,
            'postflight': handle_postflight_command,
            'workflow': handle_workflow_command,
            
            # NEW: MCP v2 Workflow Commands (Critical Priority)
            'preflight-submit': handle_preflight_submit_command,
            'check': handle_check_command,
            'check-submit': handle_check_submit_command,
            'postflight-submit': handle_postflight_submit_command,
            
            # Decision commands (from decision_commands.py)
            'decision': handle_decision_command,
            'decision-batch': handle_decision_batch_command,
            
            # Modality commands (EXPERIMENTAL)
            'modality-route': handle_modality_route_command,
            
            # Investigation commands (consolidated: analyze removed)
            'investigate': handle_investigate_command,  # Now handles --type=comprehensive

            # Performance commands (consolidated: benchmark removed)
            'performance': handle_performance_command,  # Now handles --benchmark

            # Component commands
            'list': handle_list_command,
            'explain': handle_explain_command,
            'demo': handle_demo_command,
            
            # Utility commands
            'goal-analysis': handle_goal_analysis_command,
            
            # Config commands (consolidated: 5 commands → 1)
            'config': handle_config_command,  # Handles --init, --validate, KEY, KEY VALUE
            
            # Monitor commands (consolidated: 4 commands → 1)
            'monitor': handle_monitor_command,  # Handles --export, --reset, --cost

            # MCP commands - REMOVED (IDE/CLI manages MCP lifecycle)
            # mcp-start, mcp-stop, mcp-status, mcp-test, mcp-list-tools, mcp-call all removed

            # Session commands
            'sessions-list': handle_sessions_list_command,
            'sessions-show': handle_sessions_show_command,
            'sessions-export': handle_sessions_export_command,
            # 'session-end' removed - use 'handoff-create' instead
            
            # Action commands (INVESTIGATE and ACT phase tracking)
            'investigate-log': handle_investigate_log_command,
            'act-log': handle_act_log_command,
            
            # NEW: Goal Management Commands (MCP v2 Integration)
            'goals-create': handle_goals_create_command,
            'goals-add-subtask': handle_goals_add_subtask_command,
            'goals-complete-subtask': handle_goals_complete_subtask_command,
            'goals-progress': handle_goals_progress_command,
            'goals-list': handle_goals_list_command,
            'goals-discover': handle_goals_discover_command,
            'goals-resume': handle_goals_resume_command,
            'identity-create': handle_identity_create_command,
            'identity-list': handle_identity_list_command,
            'identity-export': handle_identity_export_command,
            'identity-verify': handle_identity_verify_command,
            'sessions-resume': handle_sessions_resume_command,
            'session-create': handle_session_create_command,
            
            # Checkpoint commands (Phase 2)
            'checkpoint-create': handle_checkpoint_create_command,
            'checkpoint-load': handle_checkpoint_load_command,
            'checkpoint-list': handle_checkpoint_list_command,
            'checkpoint-diff': handle_checkpoint_diff_command,
            'efficiency-report': handle_efficiency_report_command,
            
            # Checkpoint signing commands (Phase 2 - Crypto)
            'checkpoint-sign': handle_checkpoint_sign_command,
            'checkpoint-verify': handle_checkpoint_verify_command,
            'checkpoint-signatures': handle_checkpoint_signatures_command,
            
            # Handoff Reports commands (Phase 1.6)
            'handoff-create': handle_handoff_create_command,
            'handoff-query': handle_handoff_query_command,
            
            # User interface commands (for human users)
            'onboard': handle_onboard_command,
            'ask': handle_ask_command,
            'chat': handle_chat_command,
        }
        
        handler = command_map.get(parsed_args.command)
        if handler:
            handler(parsed_args)
        else:
            print(f"❌ Unknown command: {parsed_args.command}")
            parser.print_help()
            return 1
        
        # Show execution time if verbose
        if getattr(parsed_args, 'verbose', False):
            end_time = time.time()
            print(f"\n⏱️ Execution time: {end_time - start_time:.3f}s")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Operation interrupted by user")
        return 130
    except Exception as e:
        handle_cli_error(e, f"Command '{parsed_args.command}'", getattr(parsed_args, 'verbose', False))
        return 1


if __name__ == "__main__":
    sys.exit(main())