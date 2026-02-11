"""
CLI Utilities - Shared helper functions for modular CLI components
"""

import json
import time
import sys
from typing import Dict, Any, List, Optional


def safe_print(*args, **kwargs):
    """
    Print function that handles Windows console encoding errors.
    Falls back to ASCII-safe output if Unicode fails.
    """
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Replace Unicode chars with ASCII equivalents
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                # Replace common Unicode chars with ASCII
                arg = arg.replace('━', '=').replace('─', '-')
                arg = arg.replace('✅', '[OK]').replace('❌', '[ERR]')
                arg = arg.replace('⚠️', '[WARN]').replace('ℹ️', '[INFO]')
                arg = arg.replace('🔍', '[DEBUG]').replace('🎯', '[TARGET]')
                arg = arg.replace('📁', '[FOLDER]').replace('🆔', '[ID]')
                arg = arg.replace('🗄️', '[DB]').replace('🏗️', '[BUILD]')
                arg = arg.replace('🛠️', '[TOOLS]').replace('🔄', '[LOAD]')
                # Encode to ASCII, ignoring errors
                arg = arg.encode('ascii', errors='replace').decode('ascii')
            safe_args.append(arg)
        print(*safe_args, **kwargs)


def print_component_status(component_name: str, status: str, details: Optional[str] = None):
    """Print standardized component status information"""
    status_emoji = {
        'success': '✅',
        'warning': '⚠️', 
        'error': '❌',
        'info': 'ℹ️',
        'loading': '🔄'
    }.get(status.lower(), '•')
    
    safe_print(f"{status_emoji} {component_name}: {status}")
    if details:
        safe_print(f"   {details}")


def format_uncertainty_output(uncertainty_scores: Dict[str, float], verbose: bool = False) -> str:
    """Format uncertainty scores for display"""
    if not uncertainty_scores:
        return "No uncertainty data available"
    
    output = []
    if verbose:
        output.append("🔍 Detailed uncertainty assessment:")
        for vector, score in uncertainty_scores.items():
            output.append(f"   • {vector}: {score:.2f}")
    else:
        # Show top 3 uncertainty vectors
        sorted_scores = sorted(uncertainty_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        output.append("🎯 Key uncertainty vectors:")
        for vector, score in sorted_scores:
            output.append(f"   • {vector}: {score:.2f}")
    
    return "\n".join(output)


def handle_cli_error(error: Exception, command: str, verbose: bool = False, session_id: Optional[str] = None) -> None:
    """
    Standardized error handling for CLI commands with auto-capture integration.

    Args:
        error: The exception that occurred
        command: Name of the command that failed
        verbose: Whether to print detailed traceback
        session_id: Optional session ID for auto-capture (auto-detected if not provided)
    """
    # Broken pipe is a normal condition when output is piped to `head`/`tail` and the reader exits early.
    # Treat it as non-fatal and do NOT auto-capture as an issue.
    # Depending on where it's raised, it may appear as BrokenPipeError or as OSError(errno=32).
    if isinstance(error, BrokenPipeError):
        return
    if isinstance(error, OSError) and getattr(error, "errno", None) == 32:
        return
    if "Broken pipe" in str(error):
        return

    safe_print(f"❌ {command} error: {error}")

    if verbose:
        import traceback
        safe_print("🔍 Detailed error information:")
        safe_print(traceback.format_exc())

    # Auto-capture the error for handoff to other AIs
    try:
        from empirica.core.issue_capture import get_auto_capture, initialize_auto_capture, IssueSeverity, IssueCategory

        # Get or initialize auto-capture service
        service = get_auto_capture()
        if not service:
            # Try to auto-detect session_id if not provided
            if not session_id:
                try:
                    from empirica.data.session_database import SessionDatabase
                    db = SessionDatabase()
                    cursor = db.conn.cursor()
                    cursor.execute("""
                        SELECT session_id FROM sessions
                        WHERE end_time IS NULL
                        ORDER BY start_time DESC
                        LIMIT 1
                    """)
                    row = cursor.fetchone()
                    if row:
                        # Support both sqlite3.Row (dict-style) and tuple rows
                        try:
                            session_id = row['session_id']
                        except Exception:
                            session_id = row[0]
                    else:
                        session_id = None
                    db.close()
                except:
                    pass

            # Initialize service if we have a session_id
            if session_id:
                service = initialize_auto_capture(session_id, enable=True)

        # Capture the error if service is available
        if service:
            issue_id = service.capture_error(
                message=f"{command} command failed: {str(error)}",
                severity=IssueSeverity.HIGH,
                category=IssueCategory.ERROR,
                context={"command": command},
                exc_info=error
            )
            if verbose and issue_id:
                safe_print(f"📋 Auto-captured as issue {issue_id[:8]}... for handoff")
    except Exception as capture_error:
        # Don't fail the error handler if auto-capture fails
        if verbose:
            safe_print(f"⚠️  Auto-capture failed: {capture_error}")


def parse_json_safely(json_string: Optional[str], default: Dict = None) -> Dict[str, Any]:
    """Safely parse JSON string with fallback and escape sequence repair"""
    if not json_string:
        return default or {}

    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        # Try to fix common escape sequence issues
        try:
            # Common issue: unescaped backslashes in paths or strings
            # Replace single backslashes that aren't part of valid escape sequences
            import re
            # First, try to fix simple backslash issues
            fixed_json = json_string.replace('\\', '\\\\')
            # But be careful not to double-escape already escaped sequences
            # Restore common valid escape sequences
            fixed_json = fixed_json.replace('\\\\n', '\\n').replace('\\\\t', '\\t').replace('\\\\r', '\\r')
            fixed_json = fixed_json.replace('\\\\b', '\\b').replace('\\\\f', '\\f').replace('\\\\/', '/')
            fixed_json = fixed_json.replace('\\\\\\/', '\\/')  # Handle over-correction

            # Try to parse again with the fixed string
            parsed = json.loads(fixed_json)
            return parsed
        except json.JSONDecodeError:
            # If still failing, try a more sophisticated approach
            try:
                # Try to detect and fix common escape sequence patterns
                fixed_json = _fix_json_escapes(json_string)
                return json.loads(fixed_json)
            except json.JSONDecodeError:
                safe_print(f"⚠️ JSON parsing error: {e}")
                safe_print(f"   Error details: Invalid \\escape in JSON string")
                return default or {}


def _fix_json_escapes(json_str: str) -> str:
    """Attempt to fix common JSON escape sequence issues"""
    import re

    # Pattern to match problematic backslashes that are not part of valid escape sequences
    # Valid escape sequences: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
    # Any \ that is not followed by these is likely problematic

    # First, extract and preserve valid escape sequences temporarily
    valid_escapes = {}
    escape_placeholder = "__ESCAPE_PLACEHOLDER_{}__"

    # Find and temporarily replace valid escape sequences
    valid_escape_pattern = r'\\[\"\\/bfnrt]|\\u[0-9a-fA-F]{4}'
    matches = list(re.finditer(valid_escape_pattern, json_str))

    temp_str = json_str
    for i, match in enumerate(matches):
        placeholder = escape_placeholder.format(i)
        valid_escapes[placeholder] = match.group(0)
        temp_str = temp_str.replace(match.group(0), placeholder, 1)

    # Now fix remaining problematic backslashes
    # Replace single backslashes with double backslashes
    temp_str = re.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', temp_str)

    # Restore the valid escape sequences
    for placeholder, original in valid_escapes.items():
        temp_str = temp_str.replace(placeholder, original)

    return temp_str


def format_execution_time(start_time: float, end_time: Optional[float] = None) -> str:
    """Format execution time for display"""
    if end_time is None:
        end_time = time.time()
    
    duration = end_time - start_time
    
    if duration < 0.001:
        return f"{duration*1000000:.0f}μs"
    elif duration < 1:
        return f"{duration*1000:.1f}ms"
    else:
        return f"{duration:.3f}s"


def validate_confidence_threshold(threshold: float) -> bool:
    """Validate confidence threshold is in valid range"""
    return 0.0 <= threshold <= 1.0


def print_header(title: str, emoji: str = "🎯") -> None:
    """Print a formatted header for CLI sections"""
    safe_print(f"\n{emoji} {title}")
    safe_print("=" * (len(title) + 3))


def print_separator(char: str = "-", length: int = 50) -> None:
    """Print a separator line"""
    safe_print(char * length)


def format_component_list(components: List[Dict[str, Any]], show_details: bool = False) -> str:
    """Format component list for display"""
    if not components:
        return "No components available"
    
    output = []
    working_count = sum(1 for c in components if c.get('status') == 'working')
    total_count = len(components)
    
    output.append(f"📊 Component Status: {working_count}/{total_count} working")
    
    if show_details:
        output.append("\n📋 Component Details:")
        for component in components:
            status_emoji = "✅" if component.get('status') == 'working' else "❌"
            name = component.get('name', 'Unknown')
            output.append(f"   {status_emoji} {name}")
            
            if component.get('error') and component.get('status') != 'working':
                output.append(f"      Error: {component['error']}")
    
    return "\n".join(output)


def print_project_context(quiet: bool = False, verbose: bool = False) -> Optional[Dict[str, str]]:
    """
    Print current project context banner.
    
    Shows:
    - Project name
    - Project ID
    - Current location
    - Database path
    
    This helps AI agents understand which project they're working in,
    preventing accidental writes to wrong project databases.
    
    Args:
        quiet: If True, only print minimal info (single line)
        verbose: If True, show additional details (git remote, etc.)
    
    Returns:
        dict with project info (name, project_id, git_root, db_path),
        or None if not in a project
    """
    try:
        from pathlib import Path
        import logging
        import subprocess
        import json

        logger = logging.getLogger(__name__)

        # Priority 0: Use unified context resolver (respects instance_projects, active_work, etc.)
        # This ensures we show the correct project after project-switch even if CWD differs
        git_root = None
        try:
            from empirica.utils.session_resolver import get_active_context
            context = get_active_context()
            project_path = context.get('project_path')
            if project_path:
                git_root = Path(project_path)
        except Exception:
            pass

        # Fallback: CWD-based git root detection
        if not git_root:
            from empirica.config.path_resolver import get_git_root
            git_root = get_git_root()

        if not git_root:
            if not quiet:
                safe_print("⚠️  Not in a git repository")
            return None

        project_yaml = git_root / '.empirica' / 'project.yaml'
        if not project_yaml.exists():
            if not quiet:
                safe_print(f"⚠️  No .empirica/project.yaml - run 'empirica project-init'")
            return None
        
        # Load project config
        import yaml
        with open(project_yaml) as f:
            config = yaml.safe_load(f)
        
        project_info = {
            'name': config.get('name', 'Unknown'),
            'project_id': config.get('project_id', 'Unknown'),
            'git_root': str(git_root),
            'db_path': str(git_root / '.empirica' / 'sessions' / 'sessions.db')
        }
        
        # Get git remote URL if verbose
        git_url = None
        if verbose:
            try:
                result = subprocess.run(
                    ['git', 'remote', 'get-url', 'origin'],
                    capture_output=True,
                    text=True,
                    timeout=2,
                    cwd=str(git_root)
                )
                if result.returncode == 0:
                    git_url = result.stdout.strip()
            except Exception as e:
                logger.debug(f"Could not get git remote: {e}")
        
        # Print based on mode
        if quiet:
            # Single line for quiet mode
            safe_print(f"📁 {project_info['name']} ({project_info['project_id'][:8]}...)")
        else:
            # Full banner for normal mode
            safe_print(f"📁 Project: {project_info['name']}")
            safe_print(f"🆔 ID: {project_info['project_id'][:8]}...")
            safe_print(f"📍 Location: {project_info['git_root']}")
            
            if verbose and git_url:
                safe_print(f"🔗 Repository: {git_url}")
        
        return project_info
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Could not load project context: {e}")
        if not quiet:
            safe_print(f"⚠️  Error loading project context: {e}")
        return None