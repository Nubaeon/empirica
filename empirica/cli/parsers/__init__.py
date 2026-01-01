"""
CLI Parser Modules - Modularized argument parsers for Empirica CLI

Each module contains parser definitions for a specific command group.
This modularization makes the CLI more maintainable by breaking down
the monolithic cli_core.py (1176 lines) into focused modules.

Help Text Guidelines:
- Required arguments: Include "(required)" in help text
- Optional arguments: Include "(optional)" or explain default behavior
- Example: '--session-id SESSION_ID (required)'
- Example: '--limit LIMIT (optional, default: 10)'
"""


def format_help_text(text, required=False, default=None):
    """
    Format help text with clear required/optional markers.

    Args:
        text: Base help text
        required: If True, add (required) marker
        default: If provided, add default value info

    Returns:
        Formatted help text

    Examples:
        format_help_text("Session ID", required=True)
        # Returns: "Session ID (required)"

        format_help_text("Maximum items", default=10)
        # Returns: "Maximum items (optional, default: 10)"
    """
    if required:
        return f"{text} (required)"
    elif default is not None:
        return f"{text} (optional, default: {default})"
    else:
        return f"{text} (optional)"

from .cascade_parsers import add_cascade_parsers
from .investigation_parsers import add_investigation_parsers
from .performance_parsers import add_performance_parsers
from .skill_parsers import add_skill_parsers
from .utility_parsers import add_utility_parsers
from .config_parsers import add_config_parsers
from .monitor_parsers import add_monitor_parsers
from .session_parsers import add_session_parsers
from .action_parsers import add_action_parsers
from .checkpoint_parsers import add_checkpoint_parsers
from .user_interface_parsers import add_user_interface_parsers
from .vision_parsers import add_vision_parsers
from .epistemics_parsers import add_epistemics_parsers
from .edit_verification_parsers import add_edit_verification_parsers
from .issue_capture_parsers import add_issue_capture_parsers
from .architecture_parsers import add_architecture_parsers
from .query_parsers import add_query_parsers

__all__ = [
    'format_help_text',
    'add_cascade_parsers',
    'add_investigation_parsers',
    'add_performance_parsers',
    'add_skill_parsers',
    'add_utility_parsers',
    'add_config_parsers',
    'add_monitor_parsers',
    'add_session_parsers',
    'add_action_parsers',
    'add_checkpoint_parsers',
    'add_user_interface_parsers',
    'add_vision_parsers',
    'add_epistemics_parsers',
    'add_edit_verification_parsers',
    'add_issue_capture_parsers',
    'add_architecture_parsers',
    'add_query_parsers',
]
