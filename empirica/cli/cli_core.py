"""
CLI Core - Main entry point and argument parsing for Empirica CLI

This module provides the main() function and argument parser setup.
Parser definitions are modularized in the parsers/ subdirectory.
"""

# Apply asyncio fixes early (before any MCP connections)
try:
    from empirica.cli.asyncio_fix import patch_asyncio_for_mcp
    patch_asyncio_for_mcp()
except Exception:
    pass  # Don't fail if fix can't be applied

import argparse
import sys
import time
from .cli_utils import handle_cli_error, print_header
from .command_handlers import *
from .command_handlers.utility_commands import handle_log_token_saving, handle_efficiency_report

# Import all parser modules
from .parsers import (
    add_cascade_parsers,
    add_investigation_parsers,
    add_performance_parsers,
    add_skill_parsers,
    add_utility_parsers,
    add_config_parsers,
    add_monitor_parsers,
    add_session_parsers,
    add_action_parsers,
    add_checkpoint_parsers,
    add_user_interface_parsers,
    add_vision_parsers,
    add_epistemics_parsers,
)


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

    # Add all parser groups
    add_session_parsers(subparsers)
    add_cascade_parsers(subparsers)
    add_investigation_parsers(subparsers)
    add_performance_parsers(subparsers)
    add_skill_parsers(subparsers)
    add_utility_parsers(subparsers)
    add_config_parsers(subparsers)
    add_monitor_parsers(subparsers)
    add_action_parsers(subparsers)
    add_checkpoint_parsers(subparsers)
    add_user_interface_parsers(subparsers)
    add_vision_parsers(subparsers)
    add_epistemics_parsers(subparsers)
    
    return parser


def main(args=None):
    """Main CLI entry point"""
    start_time = time.time()
    
    parser = create_argument_parser()
    parsed_args = parser.parse_args(args)
    
    if not parsed_args.command:
        parser.print_help()
        sys.exit(1)
    
    # Log command usage for telemetry
    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()
        db.log_command_usage(
            command_name=parsed_args.command,
            execution_time_ms=0,  # Will update at end
            success=None,  # Will update based on execution
            error_message=None
        )
        db.close()
    except Exception:
        pass  # Don't fail if telemetry fails
    
    # Command handler mapping
    try:
        command_handlers = {
            # Session commands
            'session-create': handle_session_create_command,
            'sessions-list': handle_sessions_list_command,
            'sessions-show': handle_sessions_show_command,
            'sessions-export': handle_sessions_export_command,
            'sessions-resume': handle_sessions_resume_command,
            'session-snapshot': handle_session_snapshot_command,
            
            # CASCADE commands
            'preflight': handle_preflight_command,
            'preflight-submit': handle_preflight_submit_command,
            'check': handle_check_command,
            'check-submit': handle_check_submit_command,
            'postflight': handle_postflight_command,
            'postflight-submit': handle_postflight_submit_command,
            'workflow': handle_workflow_command,
            
            # Investigation commands
            'investigate': handle_investigate_command,
            'investigate-log': handle_investigate_log_command,
            'investigate-create-branch': handle_investigate_create_branch_command,
            'investigate-checkpoint-branch': handle_investigate_checkpoint_branch_command,
            'investigate-merge-branches': handle_investigate_merge_branches_command,
            
            # Action commands
            'act-log': handle_act_log_command,
            
            # Performance commands
            'performance': handle_performance_command,
            
            # Skill commands
            'skill-suggest': handle_skill_suggest_command,
            'skill-fetch': handle_skill_fetch_command,
            
            # Utility commands
            'goal-analysis': handle_goal_analysis_command,
            'log-token-saving': handle_log_token_saving,
            'efficiency-report': handle_efficiency_report,
            
            # Config commands
            'config': handle_config_command,
            
            # Monitor commands
            'monitor': handle_monitor_command,
            'check-drift': handle_check_drift_command,
            
            # Checkpoint commands
            'checkpoint-create': handle_checkpoint_create_command,
            'checkpoint-load': handle_checkpoint_load_command,
            'checkpoint-list': handle_checkpoint_list_command,
            'checkpoint-diff': handle_checkpoint_diff_command,
            'checkpoint-sign': handle_checkpoint_sign_command,
            'checkpoint-verify': handle_checkpoint_verify_command,
            'checkpoint-signatures': handle_checkpoint_signatures_command,
            
            # Identity commands
            'identity-create': handle_identity_create_command,
            'identity-export': handle_identity_export_command,
            'identity-list': handle_identity_list_command,
            'identity-verify': handle_identity_verify_command,
            
            # Handoff commands
            'handoff-create': handle_handoff_create_command,
            'handoff-query': handle_handoff_query_command,
            
            # Mistake logging
            'mistake-log': handle_mistake_log_command,
            'mistake-query': handle_mistake_query_command,
            
            # Project commands
            'project-init': handle_project_init_command,
            'project-create': handle_project_create_command,
            'project-handoff': handle_project_handoff_command,
            'project-list': handle_project_list_command,
            'project-bootstrap': handle_project_bootstrap_command,
            'workspace-overview': handle_workspace_overview_command,
            'workspace-map': handle_workspace_map_command,
            'workspace-init': handle_workspace_init_command,
            'project-search': handle_project_search_command,
            'project-embed': handle_project_embed_command,
            'doc-check': handle_doc_check_command,
            
            # Finding/unknown/deadend logging
            'finding-log': handle_finding_log_command,
            'unknown-log': handle_unknown_log_command,
            'deadend-log': handle_deadend_log_command,
            'refdoc-add': handle_refdoc_add_command,
            
            # Goals commands
            'goals-create': handle_goals_create_command,
            'goals-list': handle_goals_list_command,
            'goals-complete': handle_goals_complete_command,
            'goals-claim': handle_goals_claim_command,
            'goals-add-subtask': handle_goals_add_subtask_command,
            'goals-complete-subtask': handle_goals_complete_subtask_command,
            'goals-get-subtasks': handle_goals_get_subtasks_command,
            'goals-progress': handle_goals_progress_command,
            'goals-discover': handle_goals_discover_command,
            'goals-ready': handle_goals_ready_command,
            'goals-resume': handle_goals_resume_command,
            
            # User interface commands
            'chat': handle_chat_command,
            
            # Vision commands
            'vision': handle_vision_command,
            
            # Epistemics commands
            'epistemics-list': handle_epistemics_list_command,
            'epistemics-show': handle_epistemics_show_command,
        }
        
        if parsed_args.command in command_handlers:
            handler = command_handlers[parsed_args.command]
            result = handler(parsed_args)
            
            # Log successful execution
            elapsed_ms = int((time.time() - start_time) * 1000)
            try:
                db = SessionDatabase()
                db.log_command_usage(
                    command_name=parsed_args.command,
                    execution_time_ms=elapsed_ms,
                    success=True,
                    error_message=None
                )
                db.close()
            except Exception:
                pass
            
            sys.exit(0 if result is None or result == 0 else result)
        else:
            print(f"❌ Unknown command: {parsed_args.command}")
            sys.exit(1)
            
    except Exception as e:
        # Log failed execution
        elapsed_ms = int((time.time() - start_time) * 1000)
        try:
            db = SessionDatabase()
            db.log_command_usage(
                command_name=parsed_args.command,
                execution_time_ms=elapsed_ms,
                success=False,
                error_message=str(e)
            )
            db.close()
        except Exception:
            pass
        
        handle_cli_error(e, parsed_args.command)
        sys.exit(1)


if __name__ == '__main__':
    main()
