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
  empirica bootstrap              # Bootstrap the framework
  empirica assess "my question"   # Run uncertainty assessment
  empirica cascade "should I?"    # Run metacognitive cascade
  empirica investigate ./code     # Investigate code/directory
  empirica benchmark              # Run performance benchmark
  empirica list --details        # List all components with details
        """
    )
    
    # Global options
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--config', help='Path to configuration file')
    
    # Create subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Bootstrap commands
    _add_bootstrap_parsers(subparsers)
    
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

    # Session commands
    _add_session_parsers(subparsers)
    
    # Checkpoint commands (Phase 2)
    _add_checkpoint_parsers(subparsers)
    
    # User interface commands (for human users)
    _add_user_interface_parsers(subparsers)
    
    return parser


def _add_bootstrap_parsers(subparsers):
    """Add bootstrap command parsers"""
    # Main bootstrap command (consolidates bootstrap, bootstrap-system, onboard)
    bootstrap_parser = subparsers.add_parser('bootstrap', help='Bootstrap the Empirica framework')
    bootstrap_parser.add_argument('--level',
                                choices=['0', '1', '2', '3', '4', 'minimal', 'standard', 'extended', 'complete'],
                                default='standard',
                                help='Bootstrap level (0-4 or minimal/standard/extended/complete). Use "extended" for advanced system bootstrap.')
    bootstrap_parser.add_argument('--onboard', action='store_true', help='Run interactive onboarding wizard (intro to Empirica for new users)')
    bootstrap_parser.add_argument('--test', action='store_true', help='Run tests after bootstrap')
    bootstrap_parser.add_argument('--verbose', action='store_true', help='Show detailed bootstrap info')
    # Profile-related arguments
    bootstrap_parser.add_argument('--profile', help='Optional profile for session configuration')
    bootstrap_parser.add_argument('--ai-model', help='Optional AI model specification')
    bootstrap_parser.add_argument('--domain', help='Optional domain context')
    bootstrap_parser.add_argument('--ai-id', default='empirica_cli', help='AI identifier for session tracking (used with --onboard)')

    # REMOVED: bootstrap-system and onboard commands - now consolidated into bootstrap
    # Use: bootstrap --level=extended (instead of bootstrap-system)
    # Use: bootstrap --onboard (instead of onboard)


def _add_assessment_parsers(subparsers):
    """Add assessment command parsers"""
    # Main assess command
    assess_parser = subparsers.add_parser('assess', help='Run uncertainty assessment')
    assess_parser.add_argument('query', help='Query or question to assess')
    assess_parser.add_argument('--context', help='JSON context data')
    assess_parser.add_argument('--detailed', action='store_true', help='Show detailed assessment')
    assess_parser.add_argument('--verbose', action='store_true', help='Show verbose output')
    
    # Self-awareness assessment
    self_aware_parser = subparsers.add_parser('self-awareness', help='Assess self-awareness')
    self_aware_parser.add_argument('--vectors', action='store_true', default=True, help='Include vector breakdown')
    self_aware_parser.add_argument('--detailed', action='store_true', help='Show detailed metrics')
    self_aware_parser.add_argument('--verbose', action='store_true', help='Show insights')
    
    # Metacognitive assessment
    metacog_parser = subparsers.add_parser('metacognitive', help='Run metacognitive evaluation')
    metacog_parser.add_argument('task', help='Task to evaluate metacognitively')
    metacog_parser.add_argument('--context', help='JSON context data')
    metacog_parser.add_argument('--reasoning', action='store_true', default=True, help='Include reasoning chain')
    metacog_parser.add_argument('--verbose', action='store_true', help='Show detailed reasoning')


def _add_cascade_parsers(subparsers):
    """Add cascade command parsers"""
    # Main cascade command with ModalitySwitcher
    cascade_parser = subparsers.add_parser('cascade', help='Epistemic cascade with ModalitySwitcher')
    cascade_parser.add_argument('question', help='Question for cascade analysis')
    
    # Epistemic state input options
    cascade_parser.add_argument('--epistemic-state', help='Path to JSON file with epistemic state')
    
    # Individual vector flags
    cascade_parser.add_argument('--know', type=float, help='KNOW vector (0.0-1.0)')
    cascade_parser.add_argument('--do', type=float, help='DO vector (0.0-1.0)')
    cascade_parser.add_argument('--context-vec', type=float, dest='context_vec', help='CONTEXT vector (0.0-1.0)')
    cascade_parser.add_argument('--uncertainty', type=float, help='UNCERTAINTY vector (0.0-1.0)')
    cascade_parser.add_argument('--clarity', type=float, help='CLARITY vector (0.0-1.0)')
    cascade_parser.add_argument('--coherence', type=float, help='COHERENCE vector (0.0-1.0)')
    cascade_parser.add_argument('--signal', type=float, help='SIGNAL vector (0.0-1.0)')
    cascade_parser.add_argument('--density', type=float, help='DENSITY vector (0.0-1.0)')
    cascade_parser.add_argument('--state', type=float, help='STATE vector (0.0-1.0)')
    cascade_parser.add_argument('--change', type=float, help='CHANGE vector (0.0-1.0)')
    cascade_parser.add_argument('--completion', type=float, help='COMPLETION vector (0.0-1.0)')
    cascade_parser.add_argument('--impact', type=float, help='IMPACT vector (0.0-1.0)')
    cascade_parser.add_argument('--engagement', type=float, help='ENGAGEMENT vector (0.0-1.0)')
    
    # Quiet mode
    cascade_parser.add_argument('--quiet', action='store_true', help='Quiet mode (minimal output)')
    
    # Routing options
    cascade_parser.add_argument('--strategy', choices=['epistemic', 'cost', 'latency', 'quality', 'balanced'],
                               default='epistemic', help='Routing strategy')
    cascade_parser.add_argument('--adapter', choices=['minimax', 'qwen', 'rovodev', 'gemini', 'qodo', 'openrouter', 'copilot', 'local'],
                               help='Force specific adapter')
    cascade_parser.add_argument('--model', type=str, help='Model to use (e.g., qwen-coder-turbo, gpt-5, claude-sonnet-4)')
    cascade_parser.add_argument('--list-models', action='store_true', help='List available models for selected adapter')
    cascade_parser.add_argument('--max-cost', type=float, default=1.0, help='Maximum cost in USD')
    cascade_parser.add_argument('--max-latency', type=float, default=30.0, help='Maximum latency in seconds')
    cascade_parser.add_argument('--min-quality', type=float, default=0.7, help='Minimum quality score')
    cascade_parser.add_argument('--no-fallback', action='store_true', help='Disable fallback adapters')
    
    # Output options  
    cascade_parser.add_argument('--verbose', action='store_true', help='Show detailed epistemic vectors')
    cascade_parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    
    # Enhanced decision analysis command with ModalitySwitcher
    decision_parser = subparsers.add_parser('decision', help='Epistemic decision-making with ModalitySwitcher')
    decision_parser.add_argument('decision', help='Decision query to analyze')
    
    # Epistemic state input options
    decision_parser.add_argument('--epistemic-state', help='Path to JSON file with epistemic state')
    
    # Individual vector flags
    decision_parser.add_argument('--know', type=float, help='KNOW vector (0.0-1.0)')
    decision_parser.add_argument('--do', type=float, help='DO vector (0.0-1.0)')
    decision_parser.add_argument('--context-vec', type=float, dest='context', help='CONTEXT vector (0.0-1.0)')
    decision_parser.add_argument('--uncertainty', type=float, help='UNCERTAINTY vector (0.0-1.0)')
    
    # Routing options
    decision_parser.add_argument('--strategy', choices=['epistemic', 'cost', 'latency', 'quality', 'balanced'],
                                default='epistemic', help='Routing strategy')
    decision_parser.add_argument('--adapter', choices=['minimax', 'qwen', 'rovodev', 'gemini', 'qodo', 'openrouter', 'copilot', 'local'],
                                help='Force specific adapter')
    decision_parser.add_argument('--model', type=str, help='Model to use (e.g., qwen-coder-turbo, gpt-5, claude-sonnet-4)')
    decision_parser.add_argument('--list-models', action='store_true', help='List available models for selected adapter')
    decision_parser.add_argument('--max-cost', type=float, default=1.0, help='Maximum cost in USD')
    decision_parser.add_argument('--max-latency', type=float, default=30.0, help='Maximum latency in seconds')
    decision_parser.add_argument('--min-quality', type=float, default=0.7, help='Minimum quality score')
    decision_parser.add_argument('--no-fallback', action='store_true', help='Disable fallback adapters')
    
    # Output options
    decision_parser.add_argument('--verbose', action='store_true', help='Show detailed epistemic vectors')
    decision_parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation prompt')
    
    # Batch processing
    decision_batch_parser = subparsers.add_parser('decision-batch', 
                                                   help='Batch decision processing from JSON file')
    decision_batch_parser.add_argument('batch_file', help='Path to JSON file with batch decisions')
    decision_batch_parser.add_argument('--output', help='Output file for results (default: input_results.json)')
    decision_batch_parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    
    # Preflight command
    preflight_parser = subparsers.add_parser('preflight', help='Execute preflight epistemic assessment')
    preflight_parser.add_argument('prompt', help='Task description to assess')
    preflight_parser.add_argument('--session-id', help='Optional session ID (auto-generated if not provided)')
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
    check_parser.add_argument('--unknowns', required=True, help='Remaining unknowns as JSON array')
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
    postflight_submit_parser.add_argument('--changes', help='Description of what changed from preflight')
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
    list_parser = subparsers.add_parser('list', help='List semantic components')
    list_parser.add_argument('--filter', help='Filter components by name')
    list_parser.add_argument('--tier', help='Filter by tier')
    list_parser.add_argument('--details', action='store_true', help='Show detailed component info')
    
    # Explain component command
    explain_parser = subparsers.add_parser('explain', help='Explain component functionality')
    explain_parser.add_argument('component', help='Component name to explain')
    explain_parser.add_argument('--verbose', action='store_true', help='Show API methods')
    
    # Demo component command
    demo_parser = subparsers.add_parser('demo', help='Run component demonstration')
    demo_parser.add_argument('component', nargs='?', default='random', help='Component to demo (or "random")')
    demo_parser.add_argument('--interactive', action='store_true', help='Run interactive demo')
    demo_parser.add_argument('--verbose', action='store_true', help='Show demo steps')


def _add_utility_parsers(subparsers):
    """Add utility command parsers"""
    # Feedback command
    feedback_parser = subparsers.add_parser('feedback', help='Provide decision feedback')
    feedback_parser.add_argument('decision_id', help='Decision ID for feedback')
    feedback_parser.add_argument('--success', action='store_true', help='Mark as successful')
    feedback_parser.add_argument('--notes', help='Additional feedback notes')
    
    # Goal analysis command
    goal_parser = subparsers.add_parser('goal-analysis', help='Analyze goal feasibility')
    goal_parser.add_argument('goal', help='Goal to analyze')
    goal_parser.add_argument('--context', help='JSON context data')
    goal_parser.add_argument('--verbose', action='store_true', help='Show detailed analysis')
    
    # Calibration command
    calibration_parser = subparsers.add_parser('calibration', help='Run calibration analysis')
    calibration_parser.add_argument('--data-file', help='Calibration data file')
    calibration_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    calibration_parser.add_argument('--verbose', action='store_true', help='Show detailed metrics')
    
    # UVL command
    uvl_parser = subparsers.add_parser('uvl', help='Run UVL (Uncertainty Vector Learning)')
    uvl_parser.add_argument('--task', help='Task for UVL analysis')
    uvl_parser.add_argument('--context', help='JSON context data')
    uvl_parser.add_argument('--verbose', action='store_true', help='Show uncertainty vectors')


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
    
    # Sessions show command
    sessions_show_parser = subparsers.add_parser('sessions-show', help='Show detailed session info')
    sessions_show_parser.add_argument('session_id', help='Session ID or alias (latest, latest:active, latest:<ai_id>, latest:active:<ai_id>)')
    sessions_show_parser.add_argument('--verbose', action='store_true', help='Show all vectors and cascades')

    # Sessions export command
    sessions_export_parser = subparsers.add_parser('sessions-export', help='Export session to JSON')
    sessions_export_parser.add_argument('session_id', help='Session ID or alias (latest, latest:active, latest:<ai_id>)')
    sessions_export_parser.add_argument('--output', '-o', help='Output file path (default: session_<id>.json)')


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

    # Handoff Reports Commands (Phase 1.6)
    
    # Handoff create command
    handoff_create_parser = subparsers.add_parser(
        'handoff-create',
        help='Create epistemic handoff report (98%% token reduction)'
    )
    handoff_create_parser.add_argument('--session-id', required=True, help='Session UUID')
    handoff_create_parser.add_argument('--task-summary', required=True, help='What was accomplished (2-3 sentences)')
    handoff_create_parser.add_argument('--key-findings', required=True, help='JSON array of findings')
    handoff_create_parser.add_argument('--remaining-unknowns', help='JSON array of unknowns (optional)')
    handoff_create_parser.add_argument('--next-session-context', required=True, help='Critical context for next session')
    handoff_create_parser.add_argument('--artifacts', help='JSON array of files created (optional)')
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
    goals_create_parser.add_argument('--objective', required=True, help='Goal objective text')
    goals_create_parser.add_argument('--scope', choices=['task_specific', 'session_scoped', 'project_wide'], default='task_specific', help='Goal scope')
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
    goals_list_parser.add_argument('--scope', choices=['task_specific', 'session_scoped', 'project_wide'], help='Filter by scope')
    goals_list_parser.add_argument('--completed', action='store_true', help='Filter by completion status')
    goals_list_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')
    
    # Sessions resume command
    sessions_resume_parser = subparsers.add_parser('sessions-resume', help='Resume previous sessions')
    sessions_resume_parser.add_argument('--ai-id', help='Filter by AI ID')
    sessions_resume_parser.add_argument('--count', type=int, default=1, help='Number of sessions to retrieve')
    sessions_resume_parser.add_argument('--detail-level', choices=['summary', 'detailed', 'full'], default='summary', help='Detail level')
    sessions_resume_parser.add_argument('--output', choices=['default', 'json'], default='default', help='Output format')


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
            'bootstrap': handle_bootstrap_command,  # Now handles --level=extended and --onboard

            # Assessment commands
            'assess': handle_assess_command,
            'self-awareness': handle_self_awareness_command,
            'metacognitive': handle_metacognitive_command,
            
            # Cascade commands
            'cascade': handle_cascade_command,
            'preflight': handle_preflight_command,
            'postflight': handle_postflight_command,
            'workflow': handle_workflow_command,
            
            # NEW: MCP v2 Workflow Commands (Critical Priority)
            'preflight-submit': handle_preflight_submit_command,
            'check': handle_check_command,
            'check-submit': handle_check_submit_command,
            'postflight-submit': handle_postflight_submit_command,
            
            # Decision commands
            'decision': handle_decision_command,
            'decision-batch': handle_decision_batch_command,
            
            # Investigation commands (consolidated: analyze removed)
            'investigate': handle_investigate_command,  # Now handles --type=comprehensive

            # Performance commands (consolidated: benchmark removed)
            'performance': handle_performance_command,  # Now handles --benchmark

            # Component commands
            'list': handle_list_command,
            'explain': handle_explain_command,
            'demo': handle_demo_command,
            
            # Utility commands
            'feedback': handle_feedback_command,
            'goal-analysis': handle_goal_analysis_command,
            'calibration': handle_calibration_command,
            'uvl': handle_uvl_command,
            
            # Config commands (consolidated: 5 commands → 1)
            'config': handle_config_command,  # Handles --init, --validate, KEY, KEY VALUE

            # Profile commands
            'profile-list': handle_profile_list_command,
            'profile-show': handle_profile_show_command,
            'profile-create': handle_profile_create_command,
            'profile-set-default': handle_profile_set_default_command,
            
            # Monitor commands (consolidated: 4 commands → 1)
            'monitor': handle_monitor_command,  # Handles --export, --reset, --cost

            # MCP commands - REMOVED (IDE/CLI manages MCP lifecycle)
            # mcp-start, mcp-stop, mcp-status, mcp-test, mcp-list-tools, mcp-call all removed

            # Session commands
            'sessions-list': handle_sessions_list_command,
            'sessions-show': handle_sessions_show_command,
            'sessions-export': handle_sessions_export_command,
            
            # NEW: Goal Management Commands (MCP v2 Integration)
            'goals-create': handle_goals_create_command,
            'goals-add-subtask': handle_goals_add_subtask_command,
            'goals-complete-subtask': handle_goals_complete_subtask_command,
            'goals-progress': handle_goals_progress_command,
            'goals-list': handle_goals_list_command,
            'sessions-resume': handle_sessions_resume_command,
            
            # Checkpoint commands (Phase 2)
            'checkpoint-create': handle_checkpoint_create_command,
            'checkpoint-load': handle_checkpoint_load_command,
            'checkpoint-list': handle_checkpoint_list_command,
            'checkpoint-diff': handle_checkpoint_diff_command,
            'efficiency-report': handle_efficiency_report_command,
            
            # Handoff Reports commands (Phase 1.6)
            'handoff-create': handle_handoff_create_command,
            'handoff-query': handle_handoff_query_command,
            
            # User interface commands (for human users)
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