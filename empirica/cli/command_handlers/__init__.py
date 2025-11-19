"""
Command Handlers Module - Modular CLI Command Implementations

Organizes CLI command handlers by semantic function for maintainability.
"""

# Import all command handlers
from .bootstrap_commands import (
    handle_bootstrap_command, handle_bootstrap_system_command, handle_onboard_command,
    handle_profile_list_command, handle_profile_show_command, 
    handle_profile_create_command, handle_profile_set_default_command
)
from .assessment_commands import handle_assess_command, handle_self_awareness_command, handle_metacognitive_command
from .cascade_commands import (
    handle_cascade_command,
    handle_preflight_command,
    handle_postflight_command,
    handle_workflow_command
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
    handle_goals_list_command,
    handle_sessions_resume_command
)
from .decision_commands import handle_decision_command, handle_decision_batch_command
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
    handle_sessions_list_command, handle_sessions_show_command, handle_sessions_export_command
)
from .checkpoint_commands import (
    handle_checkpoint_create_command, handle_checkpoint_load_command,
    handle_checkpoint_list_command, handle_checkpoint_diff_command,
    handle_efficiency_report_command
)
from .handoff_commands import (
    handle_handoff_create_command,
    handle_handoff_query_command
)
from .monitor_commands import (
    handle_monitor_command, handle_monitor_export_command,
    handle_monitor_reset_command, handle_monitor_cost_command
)
from .investigation_commands import handle_investigate_command, handle_analyze_command
from .performance_commands import handle_benchmark_command, handle_performance_command
from .component_commands import handle_list_command, handle_explain_command, handle_demo_command
from .utility_commands import (
    handle_feedback_command, handle_goal_analysis_command, handle_calibration_command, handle_uvl_command
)
from .ask_handler import handle_ask_command
from .chat_handler import handle_chat_command

# Export all handlers
__all__ = [
    # Bootstrap commands
    'handle_bootstrap_command',
    'handle_bootstrap_system_command',
    'handle_onboard_command',
    'handle_profile_list_command',
    'handle_profile_show_command',
    'handle_profile_create_command',
    'handle_profile_set_default_command',
    
    # Assessment commands  
    'handle_assess_command',
    'handle_self_awareness_command',
    'handle_metacognitive_command',
    
    # Cascade commands
    'handle_cascade_command',
    'handle_preflight_command',
    'handle_postflight_command',
    'handle_workflow_command',
    
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
    'handle_goals_list_command',
    'handle_sessions_resume_command',
    
    # Decision commands
    'handle_decision_command',
    'handle_decision_batch_command',
    
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
    'handle_sessions_export_command',
    
    # Checkpoint commands (Phase 2)
    'handle_checkpoint_create_command',
    'handle_checkpoint_load_command',
    'handle_checkpoint_list_command',
    'handle_checkpoint_diff_command',
    'handle_efficiency_report_command',
    
    # Handoff Reports commands (Phase 1.6)
    'handle_handoff_create_command',
    'handle_handoff_query_command',
    
    # Monitor commands
    'handle_monitor_command',
    'handle_monitor_export_command',
    'handle_monitor_reset_command',
    'handle_monitor_cost_command',
    
    # Investigation commands
    'handle_investigate_command',
    'handle_analyze_command',
    
    # Performance commands
    'handle_benchmark_command',
    'handle_performance_command',
    
    # Component commands
    'handle_list_command',
    'handle_explain_command', 
    'handle_demo_command',
    
    # Utility commands
    'handle_feedback_command',
    'handle_goal_analysis_command',
    'handle_calibration_command',
    'handle_uvl_command',
    
    # Session commands
    'handle_sessions_list_command',
    'handle_sessions_show_command',
    'handle_sessions_export_command',
    
    # User interface commands (for human users)
    'handle_ask_command',
    'handle_chat_command',
]