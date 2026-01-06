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
import json
import sys
import time
from .cli_utils import handle_cli_error, print_header
from .command_handlers import *
from .command_handlers.utility_commands import handle_log_token_saving, handle_efficiency_report
from .command_handlers.edit_verification_command import handle_edit_with_confidence_command
from .command_handlers.issue_capture_commands import (
    handle_issue_list_command,
    handle_issue_show_command,
    handle_issue_handoff_command,
    handle_issue_resolve_command,
    handle_issue_export_command,
    handle_issue_stats_command,
)


class GroupedHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom formatter that groups subcommands by category"""
    
    def _format_action(self, action):
        try:
            if isinstance(action, argparse._SubParsersAction):
                categories = {
                    'Session Management': ['session-create', 'sessions-list', 'sessions-show', 'sessions-export', 'sessions-resume', 'session-snapshot', 'memory-compact'],
                    'CASCADE Workflow': ['preflight-submit', 'check', 'check-submit', 'postflight-submit'],
                    'Goals & Tasks': ['goals-create', 'goals-list', 'goals-complete', 'goals-claim', 'goals-add-subtask', 'goals-add-dependency', 'goals-complete-subtask', 'goals-get-subtasks', 'goals-progress', 'goals-discover', 'goals-ready', 'goals-resume'],
                    'Project Management': ['project-init', 'project-create', 'project-list', 'project-switch', 'project-bootstrap', 'project-handoff', 'project-search', 'project-embed', 'doc-check'],
                    'Workspace': ['workspace-init', 'workspace-map', 'workspace-overview'],
                    'Checkpoints': ['checkpoint-create', 'checkpoint-load', 'checkpoint-list', 'checkpoint-diff', 'checkpoint-sign', 'checkpoint-verify', 'checkpoint-signatures'],
                    'Identity': ['identity-create', 'identity-export', 'identity-list', 'identity-verify'],
                    'Handoffs': ['handoff-create', 'handoff-query'],
                    'Logging': ['finding-log', 'unknown-log', 'unknown-resolve', 'deadend-log', 'refdoc-add', 'mistake-log', 'mistake-query', 'act-log', 'investigate-log'],
                    'Issue Capture': ['issue-list', 'issue-show', 'issue-handoff', 'issue-resolve', 'issue-export', 'issue-stats'],
                    'Investigation': ['investigate', 'investigate-create-branch', 'investigate-checkpoint-branch', 'investigate-merge-branches', 'investigate-multi'],
                    'Monitoring': ['monitor', 'check-drift', 'assess-state', 'trajectory-project', 'efficiency-report'],
                    'Skills': ['skill-suggest', 'skill-fetch', 'skill-extract'],
                    'Utilities': ['log-token-saving', 'config', 'performance'],
                    'Vision': ['vision'],
                    'Epistemics': ['epistemics-list', 'epistemics-show'],
                    'User Interface': ['chat'],
                    'Architecture': ['assess-component', 'assess-compare', 'assess-directory'],
                    'Agents': ['agent-spawn', 'agent-report', 'agent-aggregate', 'agent-export', 'agent-import', 'agent-discover'],
                    'Sentinel': ['sentinel-orchestrate', 'sentinel-load-profile', 'sentinel-status', 'sentinel-check'],
                    'Personas': ['persona-list', 'persona-show', 'persona-promote', 'persona-find'],
                    'Lessons': ['lesson-create', 'lesson-load', 'lesson-list', 'lesson-search', 'lesson-recommend', 'lesson-path', 'lesson-replay-start', 'lesson-replay-end', 'lesson-stats']
                }
                
                parts = ['\nAvailable Commands (grouped by category):\n', '=' * 70 + '\n']
                for category, commands in categories.items():
                    parts.append(f'\n{category} ({len(commands)} commands):\n')
                    parts.append('-' * 70 + '\n')
                    for cmd in commands:
                        if cmd in action.choices:
                            parts.append(f'  {cmd:30s}\n')
                parts.append('\n' + '=' * 70 + '\n')
                parts.append('\nUse "empirica <command> --help" for detailed help on a specific command.\n')
                return ''.join(parts)
        except Exception:
            pass
        
        return super()._format_action(action)

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
    add_edit_verification_parsers,
    add_issue_capture_parsers,
    add_architecture_parsers,
    add_query_parsers,
    add_agent_parsers,
    add_sentinel_parsers,
    add_persona_parsers,
    add_release_parsers,
    add_lesson_parsers,
)
from .command_handlers.architecture_commands import (
    handle_assess_component_command,
    handle_assess_compare_command,
    handle_assess_directory_command,
)
from .command_handlers.query_commands import handle_query_command
from .command_handlers.agent_commands import (
    handle_agent_spawn_command,
    handle_agent_report_command,
    handle_agent_aggregate_command,
    handle_agent_export_command,
    handle_agent_import_command,
    handle_agent_discover_command,
)
from .command_handlers.sentinel_commands import (
    handle_sentinel_orchestrate_command,
    handle_sentinel_load_profile_command,
    handle_sentinel_status_command,
    handle_sentinel_check_command,
)
from .command_handlers.persona_commands import (
    handle_persona_list_command,
    handle_persona_show_command,
    handle_persona_promote_command,
    handle_persona_find_command,
)
from .command_handlers.release_commands import handle_release_ready_command
from .command_handlers.docs_commands import handle_docs_assess, handle_docs_explain


def _get_version():
    """Get Empirica version with additional info"""
    try:
        import empirica
        version = empirica.__version__
        
        # Add Python version and install location
        import sys
        python_version = f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        install_path = empirica.__file__.rsplit('/', 2)[0] if '/' in empirica.__file__ else empirica.__file__
        
        return f"{version}\n{python_version}\nInstall: {install_path}"
    except:
        return "1.0.5 (version info unavailable)"


def create_argument_parser():
    """Create and configure the main argument parser"""
    parser = argparse.ArgumentParser(
        prog='empirica',
        description='🧠 Empirica - Epistemic Vector-Based Functional Self-Awareness Framework',
        formatter_class=GroupedHelpFormatter,
        epilog="Global Flags (must come BEFORE command name):\n  empirica [--version] [--verbose] <command> [args]\n\nExamples:\n  empirica session-create --ai-id myai      # Create session\n  empirica --verbose sessions-list          # Show debug info\n  empirica preflight-submit --session-id xyz # PREFLIGHT\n  empirica --verbose check --session-id xyz # CHECK with debugging"
    )
    
    # Global options (must come before subcommand)
    parser.add_argument('--version', action='version', version=f'%(prog)s {_get_version()}')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output (shows DB path, execution time, etc.). Must come before command name.')
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
    add_edit_verification_parsers(subparsers)
    add_issue_capture_parsers(subparsers)
    add_architecture_parsers(subparsers)
    add_query_parsers(subparsers)
    add_agent_parsers(subparsers)
    add_sentinel_parsers(subparsers)
    add_persona_parsers(subparsers)
    add_release_parsers(subparsers)
    add_lesson_parsers(subparsers)

    return parser


def main(args=None):
    """Main CLI entry point"""
    start_time = time.time()
    
    parser = create_argument_parser()
    parsed_args = parser.parse_args(args)
    
    if not parsed_args.command:
        parser.print_help()
        sys.exit(1)
    
    # Enable verbose output if requested
    verbose = getattr(parsed_args, 'verbose', False)
    if verbose:
        print(f"[VERBOSE] Empirica v{_get_version().split()[0]}", file=sys.stderr)
        print(f"[VERBOSE] Command: {parsed_args.command}", file=sys.stderr)
        try:
            from empirica.data.session_database import SessionDatabase
            db = SessionDatabase()
            print(f"[VERBOSE] Database: {db.db_path}", file=sys.stderr)
            db.close()
        except Exception as e:
            print(f"[VERBOSE] Database: (unavailable: {e})", file=sys.stderr)
    
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
            'memory-compact': handle_memory_compact_command,
            
            # CASCADE commands (working -submit variants only)
            'preflight-submit': handle_preflight_submit_command,
            'check': handle_check_command,
            'check-submit': handle_check_submit_command,
            'postflight-submit': handle_postflight_submit_command,
            
            # Investigation commands
            'investigate': handle_investigate_command,
            'investigate-log': handle_investigate_log_command,
            'investigate-create-branch': handle_investigate_create_branch_command,
            'investigate-checkpoint-branch': handle_investigate_checkpoint_branch_command,
            'investigate-merge-branches': handle_investigate_merge_branches_command,
            'investigate-multi': handle_investigate_multi_command,
            
            # Action commands
            'act-log': handle_act_log_command,
            
            # Performance commands
            'performance': handle_performance_command,
            
            # Skill commands
            'skill-suggest': handle_skill_suggest_command,
            'skill-fetch': handle_skill_fetch_command,
            'skill-extract': handle_skill_extract_command,
            
            # Utility commands
            'log-token-saving': handle_log_token_saving,
            'efficiency-report': handle_efficiency_report,
            
            # Config commands
            'config': handle_config_command,
            
            # Monitor commands
            'monitor': handle_monitor_command,
            'check-drift': handle_check_drift_command,
            'assess-state': handle_assess_state_command,
            'mco-load': handle_mco_load_command,
            'trajectory-project': handle_trajectory_project_command,

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
            'project-switch': handle_project_switch_command,
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
            'unknown-resolve': handle_unknown_resolve_command,
            'deadend-log': handle_deadend_log_command,
            'refdoc-add': handle_refdoc_add_command,
            
            # Goals commands
            'goals-create': handle_goals_create_command,
            'goals-list': handle_goals_list_command,
            'goals-list-all': handle_goals_list_all_command,
            'goals-complete': handle_goals_complete_command,
            'goals-claim': handle_goals_claim_command,
            'goals-add-subtask': handle_goals_add_subtask_command,
            'goals-add-dependency': handle_goals_add_dependency_command,
            'goals-complete-subtask': handle_goals_complete_subtask_command,
            'goals-get-subtasks': handle_goals_get_subtasks_command,
            'goals-progress': handle_goals_progress_command,
            'goals-discover': handle_goals_discover_command,
            'goals-ready': handle_goals_ready_command,
            'goals-resume': handle_goals_resume_command,
            
            # User interface commands
            'chat': handle_chat_command,
            'dashboard': handle_dashboard_command,

            # Vision commands
            'vision': handle_vision_analyze,
            
            # Epistemics commands
            'epistemics-list': handle_epistemics_list_command,
            'epistemics-show': handle_epistemics_stats_command,

            # Edit verification commands
            'edit-with-confidence': handle_edit_with_confidence_command,
            
            # Issue capture commands
            'issue-list': handle_issue_list_command,
            'issue-show': handle_issue_show_command,
            'issue-handoff': handle_issue_handoff_command,
            'issue-resolve': handle_issue_resolve_command,
            'issue-export': handle_issue_export_command,
            'issue-stats': handle_issue_stats_command,

            # Architecture assessment commands
            'assess-component': handle_assess_component_command,
            'assess-compare': handle_assess_compare_command,
            'assess-directory': handle_assess_directory_command,

            # Unified query command
            'query': handle_query_command,

            # Agent commands
            'agent-spawn': handle_agent_spawn_command,
            'agent-report': handle_agent_report_command,
            'agent-aggregate': handle_agent_aggregate_command,
            'agent-export': handle_agent_export_command,
            'agent-import': handle_agent_import_command,
            'agent-discover': handle_agent_discover_command,

            # Sentinel orchestration commands
            'sentinel-orchestrate': handle_sentinel_orchestrate_command,
            'sentinel-load-profile': handle_sentinel_load_profile_command,
            'sentinel-status': handle_sentinel_status_command,
            'sentinel-check': handle_sentinel_check_command,

            # Persona commands
            'persona-list': handle_persona_list_command,
            'persona-show': handle_persona_show_command,
            'persona-promote': handle_persona_promote_command,
            'persona-find': handle_persona_find_command,

            # Release commands
            'release-ready': handle_release_ready_command,
            'docs-assess': handle_docs_assess,
            'docs-explain': handle_docs_explain,

            # Lesson commands (Epistemic Procedural Knowledge)
            'lesson-create': handle_lesson_create_command,
            'lesson-load': handle_lesson_load_command,
            'lesson-list': handle_lesson_list_command,
            'lesson-search': handle_lesson_search_command,
            'lesson-recommend': handle_lesson_recommend_command,
            'lesson-path': handle_lesson_path_command,
            'lesson-replay-start': handle_lesson_replay_start_command,
            'lesson-replay-end': handle_lesson_replay_end_command,
            'lesson-stats': handle_lesson_stats_command,
            'lesson-embed': handle_lesson_embed_command,
        }
        
        if parsed_args.command in command_handlers:
            handler = command_handlers[parsed_args.command]
            result = handler(parsed_args)

            # Handle result output and exit code
            exit_code = 0
            if isinstance(result, dict):
                # Dict results: print as JSON, exit based on 'ok' field
                output_format = getattr(parsed_args, 'output', 'json')
                if output_format == 'json':
                    print(json.dumps(result, indent=2, default=str))
                else:
                    # Human-readable format
                    if result.get('ok', True):
                        for key, value in result.items():
                            if key != 'ok':
                                print(f"{key}: {value}")
                    else:
                        print(f"❌ {result.get('error', 'Unknown error')}")
                exit_code = 0 if result.get('ok', True) else 1
            elif result is not None and result != 0:
                # Non-dict non-zero result is an exit code
                exit_code = result

            # Log successful execution
            elapsed_ms = int((time.time() - start_time) * 1000)
            if verbose:
                print(f"[VERBOSE] Execution time: {elapsed_ms}ms", file=sys.stderr)

            try:
                db = SessionDatabase()
                db.log_command_usage(
                    command_name=parsed_args.command,
                    execution_time_ms=elapsed_ms,
                    success=(exit_code == 0),
                    error_message=None if exit_code == 0 else "Command returned error"
                )
                db.close()
            except Exception:
                pass

            sys.exit(exit_code)
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
