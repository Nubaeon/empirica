"""
Command Handlers Module - Modular CLI Command Implementations

Organizes CLI command handlers by semantic function for maintainability.
"""

# Import all command handlers
from .onboard import handle_onboard_command
from .cascade_commands import (
    handle_preflight_command,
    handle_postflight_command,
    handle_workflow_command
)
from .modality_commands import (
    handle_modality_route_command,
    handle_decision_command as handle_modality_decision_command
)
from .action_commands import (
    handle_investigate_log_command,
    handle_act_log_command
)
from .workflow_commands import (
    handle_preflight_submit_command,
    handle_check_command,
    handle_check_submit_command,
    handle_postflight_submit_command
)
from .goal_commands import (
    handle_goals_create_command,
    handle_goals_add_subtask_command,
    handle_goals_complete_subtask_command,
    handle_goals_progress_command,
    handle_goals_get_subtasks_command,
    handle_goals_list_command,
    handle_sessions_resume_command
)
from .goals_ready_command import handle_goals_ready_command
from .goal_claim_command import handle_goals_claim_command
from .goal_complete_command import handle_goals_complete_command
from .goal_discovery_commands import (
    handle_goals_discover_command,
    handle_goals_resume_command
)
from .identity_commands import (
    handle_identity_create_command,
    handle_identity_list_command,
    handle_identity_export_command,
    handle_identity_verify_command
)
from .config_commands import (
    handle_config_command,
    handle_config_init_command, handle_config_show_command,
    handle_config_validate_command, handle_config_get_command, handle_config_set_command
)
from .mcp_commands import (
    handle_mcp_start_command, handle_mcp_stop_command, handle_mcp_status_command,
    handle_mcp_test_command, handle_mcp_list_tools_command, handle_mcp_call_command
)
from .session_commands import (
    handle_sessions_list_command, handle_sessions_show_command, handle_session_snapshot_command,
    handle_sessions_export_command, handle_memory_compact_command,
)
from .session_create import handle_session_create_command
from .checkpoint_commands import (
    handle_checkpoint_create_command, handle_checkpoint_load_command,
    handle_checkpoint_list_command, handle_checkpoint_diff_command,
    handle_efficiency_report_command
)
from .checkpoint_signing_commands import (
    handle_checkpoint_sign_command,
    handle_checkpoint_verify_command,
    handle_checkpoint_signatures_command
)
from .handoff_commands import (
    handle_handoff_create_command,
    handle_handoff_query_command
)
from .mistake_commands import (
    handle_mistake_log_command,
    handle_mistake_query_command
)
from .project_commands import (
    handle_project_create_command,
    handle_project_handoff_command,
    handle_project_list_command,
    handle_project_bootstrap_command,
    handle_workspace_overview_command,
    handle_workspace_map_command,
    handle_finding_log_command,
    handle_unknown_log_command,
    handle_unknown_resolve_command,
    handle_deadend_log_command,
    handle_refdoc_add_command
)
from .project_init import handle_project_init_command
from .workspace_init import handle_workspace_init_command
from .project_search import (
    handle_project_search_command,
)
from .project_embed import (
    handle_project_embed_command,
)
from .doc_commands import (
    handle_doc_check_command,
    handle_doc_plan_suggest_command,
)
from .skill_commands import (
    handle_skill_suggest_command,
    handle_skill_fetch_command,
)
from .monitor_commands import (
    handle_monitor_command, handle_monitor_export_command,
    handle_monitor_reset_command, handle_monitor_cost_command,
    handle_check_drift_command, handle_mco_load_command
)
from .investigation_commands import (
    handle_investigate_command,
    handle_analyze_command,
    handle_investigate_create_branch_command,
    handle_investigate_checkpoint_branch_command,
    handle_investigate_merge_branches_command
)
from .performance_commands import handle_benchmark_command, handle_performance_command
from .utility_commands import (
    handle_goal_analysis_command
)
from .ask_handler import handle_ask_command
from .chat_handler import handle_chat_command
from .dashboard import handle_dashboard_command
from .vision_commands import (
    handle_vision_analyze,
    handle_vision_log,
    add_vision_parsers as _add_vision_parsers
)
from .epistemics_commands import (
    handle_epistemics_search_command,
    handle_epistemics_stats_command,
    handle_epistemics_list_command
)


# Export all handlers
__all__ = [
    # Onboarding commands
    'handle_onboard_command',

    # Cascade commands
    'handle_preflight_command',
    'handle_postflight_command',
    'handle_workflow_command',
    
    # Modality commands (EXPERIMENTAL)
    'handle_modality_route_command',
    'handle_modality_decision_command',
    
    # Action commands (INVESTIGATE and ACT phase tracking)
    'handle_investigate_log_command',
    'handle_act_log_command',
    
    # NEW: MCP v2 Workflow Commands (Critical Priority)
    'handle_preflight_submit_command',
    'handle_check_command',
    'handle_check_submit_command',
    'handle_postflight_submit_command',
    
    # NEW: Goal Management Commands (MCP v2 Integration)
    'handle_goals_create_command',
    'handle_goals_add_subtask_command',
    'handle_goals_complete_subtask_command',
    'handle_goals_progress_command',
    'handle_goals_get_subtasks_command',
    'handle_goals_list_command',
    'handle_goals_discover_command',
    'handle_goals_resume_command',
    'handle_goals_ready_command',  # BEADS integration
    'handle_goals_claim_command',  # Phase 3a - Git bridge
    'handle_goals_complete_command',  # Phase 3a - Git bridge
    'handle_sessions_resume_command',
    
    # NEW: Identity Management Commands (Phase 2 - EEP-1)
    'handle_identity_create_command',
    'handle_identity_list_command',
    'handle_identity_export_command',
    'handle_identity_verify_command',
    
    # Config commands
    'handle_config_command',
    'handle_config_init_command',
    'handle_config_show_command',
    'handle_config_validate_command',
    'handle_config_get_command',
    'handle_config_set_command',
    
    # MCP commands
    'handle_mcp_start_command',
    'handle_mcp_stop_command',
    'handle_mcp_status_command',
    'handle_mcp_test_command',
    'handle_mcp_list_tools_command',
    'handle_mcp_call_command',
    
    # Session commands
    'handle_sessions_list_command',
    'handle_sessions_show_command',
    'handle_session_snapshot_command',
    'handle_sessions_export_command',
    'handle_memory_compact_command',

    # Checkpoint commands (Phase 2)
    'handle_session_create_command',
    'handle_checkpoint_create_command',
    'handle_checkpoint_load_command',
    'handle_checkpoint_list_command',
    'handle_checkpoint_diff_command',
    'handle_efficiency_report_command',
    
    # Checkpoint signing commands (Phase 2 - Crypto)
    'handle_checkpoint_sign_command',
    'handle_checkpoint_verify_command',
    'handle_checkpoint_signatures_command',
    
    # Handoff Reports commands (Phase 1.6)
    'handle_handoff_create_command',
    'handle_handoff_query_command',
    
    # Mistake Logging commands (Learning from Failures)
    'handle_mistake_log_command',
    'handle_mistake_query_command',
    
    # Project Tracking commands (Multi-repo/multi-session)
    'handle_project_create_command',
    'handle_project_handoff_command',
    'handle_project_list_command',
    'handle_project_bootstrap_command',
    'handle_project_init_command',
    'handle_workspace_overview_command',
    'handle_workspace_map_command',
    'handle_workspace_init_command',
    'handle_finding_log_command',
    'handle_unknown_log_command',
    'handle_unknown_resolve_command',
    'handle_deadend_log_command',
    'handle_refdoc_add_command',
    'handle_project_search_command',
    'handle_project_embed_command',
    'handle_doc_check_command',
    'handle_doc_plan_suggest_command',
    'handle_skill_suggest_command',
    'handle_skill_fetch_command',
    
    # Monitor commands
    'handle_monitor_command',
    'handle_monitor_export_command',
    'handle_monitor_reset_command',
    'handle_monitor_cost_command',
    'handle_check_drift_command',
    'handle_mco_load_command',

    # Investigation commands
    'handle_investigate_command',
    'handle_analyze_command',
    'handle_investigate_create_branch_command',
    'handle_investigate_checkpoint_branch_command',
    'handle_investigate_merge_branches_command',

    # Performance commands
    'handle_benchmark_command',
    'handle_performance_command',
    
    # Utility commands
    'handle_goal_analysis_command',
    
    # Session commands
    'handle_sessions_list_command',
    'handle_sessions_show_command',
    'handle_sessions_export_command',
    
    # User interface commands (for human users)
    'handle_ask_command',
    'handle_chat_command',
    'handle_dashboard_command',

    # Vision commands
    'handle_vision_analyze',
    'handle_vision_log',
    '_add_vision_parsers',
    
    # Epistemic trajectory commands
    'handle_epistemics_search_command',
    'handle_epistemics_stats_command',
    'handle_epistemics_list_command',
    
    # Session-end command
    # 'handle_session_end_command',  # removed - use handoff-create
]