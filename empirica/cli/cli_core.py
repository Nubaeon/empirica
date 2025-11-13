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
    
    # MCP commands
    _add_mcp_parsers(subparsers)
    
    # Session commands
    _add_session_parsers(subparsers)
    
    # User interface commands (for human users)
    _add_user_interface_parsers(subparsers)
    
    return parser


def _add_bootstrap_parsers(subparsers):
    """Add bootstrap command parsers"""
    # Main bootstrap command
    bootstrap_parser = subparsers.add_parser('bootstrap', help='Bootstrap the Empirica framework')
    bootstrap_parser.add_argument('--level', 
                                choices=['0', '1', '2', '3', '4', 'minimal', 'standard', 'extended', 'complete'], 
                                default='standard', 
                                help='Bootstrap level (0-4 or minimal/standard/extended/complete)')
    bootstrap_parser.add_argument('--test', action='store_true', help='Run tests after bootstrap')
    bootstrap_parser.add_argument('--verbose', action='store_true', help='Show detailed bootstrap info')
    # Profile-related arguments
    bootstrap_parser.add_argument('--profile', help='Optional profile for session configuration')
    bootstrap_parser.add_argument('--ai-model', help='Optional AI model specification')
    bootstrap_parser.add_argument('--domain', help='Optional domain context')
    
    # System bootstrap command
    system_parser = subparsers.add_parser('bootstrap-system', help='Advanced system bootstrap')
    system_parser.add_argument('--level',
                              choices=['0', '1', '2', '3', '4', 'minimal', 'standard', 'extended', 'complete'],
                              default='2',
                              help='Extended bootstrap level (0-4 or minimal/standard/extended/complete)')
    system_parser.add_argument('--test', action='store_true', help='Run system tests')
    system_parser.add_argument('--verbose', action='store_true', help='Show detailed system info')
    system_parser.add_argument('--profile', help='Optional profile for session configuration')
    system_parser.add_argument('--ai-model', help='Optional AI model specification')
    system_parser.add_argument('--domain', help='Optional domain context')
    
    # Onboarding wizard command
    onboard_parser = subparsers.add_parser('onboard', help='Interactive onboarding wizard for learning Empirica')
    onboard_parser.add_argument('--ai-id', default='cli_user', help='AI identifier for session tracking')
    onboard_parser.add_argument('--verbose', action='store_true', help='Show detailed wizard steps')


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
    preflight_parser.add_argument('--assessment-json', help='Genuine AI self-assessment JSON (required for genuine assessment)')
    preflight_parser.add_argument('--json', action='store_true', help='Output as JSON')
    preflight_parser.add_argument('--compact', action='store_true', help='Output as single-line key=value')
    preflight_parser.add_argument('--kv', action='store_true', help='Output as multi-line key=value')
    preflight_parser.add_argument('--verbose', action='store_true', help='Show detailed assessment')
    
    # Postflight command
    postflight_parser = subparsers.add_parser('postflight', help='Execute postflight epistemic reassessment')
    postflight_parser.add_argument('session_id', help='Session ID from preflight')
    postflight_parser.add_argument('--summary', help='Task completion summary')
    postflight_parser.add_argument('--assessment-json', help='Genuine AI self-assessment JSON (required for genuine assessment)')
    postflight_parser.add_argument('--json', action='store_true', help='Output as JSON')
    postflight_parser.add_argument('--compact', action='store_true', help='Output as single-line key=value')
    postflight_parser.add_argument('--kv', action='store_true', help='Output as multi-line key=value')
    postflight_parser.add_argument('--verbose', action='store_true', help='Show detailed delta analysis')
    
    # Workflow command
    workflow_parser = subparsers.add_parser('workflow', help='Execute full preflight→work→postflight workflow')
    workflow_parser.add_argument('prompt', help='Task description')
    workflow_parser.add_argument('--auto', action='store_true', help='Skip manual pause between steps')
    workflow_parser.add_argument('--verbose', action='store_true', help='Show detailed workflow steps')


def _add_investigation_parsers(subparsers):
    """Add investigation command parsers"""
    # Main investigate command
    investigate_parser = subparsers.add_parser('investigate', help='Investigate file/directory/concept')
    investigate_parser.add_argument('target', help='Target to investigate')
    investigate_parser.add_argument('--context', help='JSON context data')
    investigate_parser.add_argument('--verbose', action='store_true', help='Show detailed investigation')
    
    # General analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze subject comprehensively')
    analyze_parser.add_argument('subject', help='Subject to analyze')
    analyze_parser.add_argument('--type', default='general', help='Analysis type')
    analyze_parser.add_argument('--context', help='JSON context data')
    analyze_parser.add_argument('--detailed', action='store_true', help='Show detailed breakdown')


def _add_performance_parsers(subparsers):
    """Add performance command parsers"""
    # Benchmark command
    benchmark_parser = subparsers.add_parser('benchmark', help='Run performance benchmark')
    benchmark_parser.add_argument('--type', default='comprehensive', help='Benchmark type')
    benchmark_parser.add_argument('--iterations', type=int, default=10, help='Number of iterations')
    benchmark_parser.add_argument('--memory', action='store_true', default=True, help='Include memory analysis')
    benchmark_parser.add_argument('--verbose', action='store_true', help='Show detailed results')
    
    # Performance analysis command
    performance_parser = subparsers.add_parser('performance', help='Analyze performance')
    performance_parser.add_argument('--target', default='system', help='Performance analysis target')
    performance_parser.add_argument('--context', help='JSON context data')
    performance_parser.add_argument('--detailed', action='store_true', help='Show detailed metrics')


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
    calibration_parser.add_argument('--verbose', action='store_true', help='Show detailed metrics')
    
    # UVL command
    uvl_parser = subparsers.add_parser('uvl', help='Run UVL (Uncertainty Vector Learning)')
    uvl_parser.add_argument('--task', help='Task for UVL analysis')
    uvl_parser.add_argument('--context', help='JSON context data')
    uvl_parser.add_argument('--verbose', action='store_true', help='Show uncertainty vectors')


def _add_config_parsers(subparsers):
    """Add configuration command parsers"""
    # Config init command
    config_init_parser = subparsers.add_parser('config-init', help='Initialize Empirica configuration')
    config_init_parser.add_argument('--force', action='store_true', help='Overwrite existing config')
    
    # Config show command
    config_show_parser = subparsers.add_parser('config-show', help='Show current configuration')
    config_show_parser.add_argument('--section', help='Show specific section (e.g., routing, adapters)')
    config_show_parser.add_argument('--format', choices=['yaml', 'json'], default='yaml', help='Output format')
    
    # Config validate command
    config_validate_parser = subparsers.add_parser('config-validate', help='Validate configuration')
    config_validate_parser.add_argument('--verbose', action='store_true', help='Show detailed validation')
    
    # Config get command
    config_get_parser = subparsers.add_parser('config-get', help='Get configuration value')
    config_get_parser.add_argument('key', help='Configuration key (dot notation, e.g., routing.default_strategy)')
    
    # Config set command
    config_set_parser = subparsers.add_parser('config-set', help='Set configuration value')
    config_set_parser.add_argument('key', help='Configuration key (dot notation)')
    config_set_parser.add_argument('value', help='Value to set')


def _add_monitor_parsers(subparsers):
    """Add monitoring command parsers"""
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Display usage monitoring dashboard')
    monitor_parser.add_argument('--history', action='store_true', help='Show recent request history')
    monitor_parser.add_argument('--health', action='store_true', help='Include adapter health checks')
    monitor_parser.add_argument('--verbose', action='store_true', help='Show detailed stats')
    
    # Monitor export command
    monitor_export_parser = subparsers.add_parser('monitor-export', help='Export monitoring data')
    monitor_export_parser.add_argument('output', help='Output file path')
    monitor_export_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    
    # Monitor reset command
    monitor_reset_parser = subparsers.add_parser('monitor-reset', help='Reset monitoring statistics')
    monitor_reset_parser.add_argument('--yes', '-y', action='store_true', help='Skip confirmation')
    
    # Monitor cost command
    monitor_cost_parser = subparsers.add_parser('monitor-cost', help='Display cost analysis')
    monitor_cost_parser.add_argument('--project', action='store_true', help='Show cost projections')


def _add_mcp_parsers(subparsers):
    """Add MCP server command parsers"""
    # MCP start command
    mcp_start_parser = subparsers.add_parser('mcp-start', help='Start MCP server')
    mcp_start_parser.add_argument('--verbose', action='store_true', help='Show detailed startup info')
    
    # MCP stop command
    mcp_stop_parser = subparsers.add_parser('mcp-stop', help='Stop MCP server')
    mcp_stop_parser.add_argument('--verbose', action='store_true', help='Show detailed shutdown info')
    
    # MCP status command
    mcp_status_parser = subparsers.add_parser('mcp-status', help='Check MCP server status')
    mcp_status_parser.add_argument('--verbose', action='store_true', help='Show detailed process info')
    
    # MCP test command
    mcp_test_parser = subparsers.add_parser('mcp-test', help='Test MCP server connection')
    mcp_test_parser.add_argument('--verbose', action='store_true', help='Show detailed test results')
    
    # MCP list-tools command
    mcp_list_tools_parser = subparsers.add_parser('mcp-list-tools', help='List available MCP tools')
    mcp_list_tools_parser.add_argument('--show-all', action='store_true', help='Show all tools including disabled ones')
    mcp_list_tools_parser.add_argument('--verbose', action='store_true', help='Show usage examples')
    
    # MCP call command
    mcp_call_parser = subparsers.add_parser('mcp-call', help='Call MCP tool directly (for testing)')
    mcp_call_parser.add_argument('tool_name', help='MCP tool name to call')
    mcp_call_parser.add_argument('--arguments', help='JSON arguments for the tool')
    mcp_call_parser.add_argument('--verbose', action='store_true', help='Show detailed output')


def _add_session_parsers(subparsers):
    """Add session management command parsers"""
    # Sessions list command
    sessions_list_parser = subparsers.add_parser('sessions-list', help='List all sessions')
    sessions_list_parser.add_argument('--limit', type=int, default=50, help='Maximum sessions to show')
    sessions_list_parser.add_argument('--verbose', action='store_true', help='Show detailed info')
    
    # Sessions show command
    sessions_show_parser = subparsers.add_parser('sessions-show', help='Show detailed session info')
    sessions_show_parser.add_argument('session_id', help='Session ID to show')
    sessions_show_parser.add_argument('--verbose', action='store_true', help='Show all vectors and cascades')
    
    # Sessions export command
    sessions_export_parser = subparsers.add_parser('sessions-export', help='Export session to JSON')
    sessions_export_parser.add_argument('session_id', help='Session ID to export')
    sessions_export_parser.add_argument('--output', '-o', help='Output file path (default: session_<id>.json)')


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
            # Bootstrap commands
            'bootstrap': handle_bootstrap_command,
            'bootstrap-system': handle_bootstrap_system_command,
            'onboard': handle_onboard_command,
            
            # Assessment commands
            'assess': handle_assess_command,
            'self-awareness': handle_self_awareness_command,
            'metacognitive': handle_metacognitive_command,
            
            # Cascade commands
            'cascade': handle_cascade_command,
            'preflight': handle_preflight_command,
            'postflight': handle_postflight_command,
            'workflow': handle_workflow_command,
            
            # Decision commands
            'decision': handle_decision_command,
            'decision-batch': handle_decision_batch_command,
            
            # Investigation commands
            'investigate': handle_investigate_command,
            'analyze': handle_analyze_command,
            
            # Performance commands
            'benchmark': handle_benchmark_command,
            'performance': handle_performance_command,
            
            # Component commands
            'list': handle_list_command,
            'explain': handle_explain_command,
            'demo': handle_demo_command,
            
            # Utility commands
            'feedback': handle_feedback_command,
            'goal-analysis': handle_goal_analysis_command,
            'calibration': handle_calibration_command,
            'uvl': handle_uvl_command,
            
            # Config commands
            'config-init': handle_config_init_command,
            'config-show': handle_config_show_command,
            'config-validate': handle_config_validate_command,
            'config-get': handle_config_get_command,
            'config-set': handle_config_set_command,
            
            # Profile commands
            'profile-list': handle_profile_list_command,
            'profile-show': handle_profile_show_command,
            'profile-create': handle_profile_create_command,
            'profile-set-default': handle_profile_set_default_command,
            
            # Monitor commands
            'monitor': handle_monitor_command,
            'monitor-export': handle_monitor_export_command,
            'monitor-reset': handle_monitor_reset_command,
            'monitor-cost': handle_monitor_cost_command,
            
            # MCP commands
            'mcp-start': handle_mcp_start_command,
            'mcp-stop': handle_mcp_stop_command,
            'mcp-status': handle_mcp_status_command,
            'mcp-test': handle_mcp_test_command,
            'mcp-list-tools': handle_mcp_list_tools_command,
            'mcp-call': handle_mcp_call_command,
            
            # Session commands
            'sessions-list': handle_sessions_list_command,
            'sessions-show': handle_sessions_show_command,
            'sessions-export': handle_sessions_export_command,
            
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