"""
CLI Utilities - Shared helper functions for modular CLI components
"""

import json
import time
from typing import Dict, Any, List, Optional


def print_component_status(component_name: str, status: str, details: Optional[str] = None):
    """Print standardized component status information"""
    status_emoji = {
        'success': '✅',
        'warning': '⚠️', 
        'error': '❌',
        'info': 'ℹ️',
        'loading': '🔄'
    }.get(status.lower(), '•')
    
    print(f"{status_emoji} {component_name}: {status}")
    if details:
        print(f"   {details}")


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


def handle_cli_error(error: Exception, command: str, verbose: bool = False) -> None:
    """Standardized error handling for CLI commands"""
    print(f"❌ {command} error: {error}")
    
    if verbose:
        import traceback
        print("🔍 Detailed error information:")
        print(traceback.format_exc())


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
                print(f"⚠️ JSON parsing error: {e}")
                print(f"   Error details: Invalid \\escape in JSON string")
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
    print(f"\n{emoji} {title}")
    print("=" * (len(title) + 3))


def print_separator(char: str = "-", length: int = 50) -> None:
    """Print a separator line"""
    print(char * length)


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
        
        logger = logging.getLogger(__name__)
        
        # Import here to avoid circular dependency
        from empirica.config.path_resolver import get_git_root
        
        git_root = get_git_root()
        if not git_root:
            if not quiet:
                print("⚠️  Not in a git repository")
            return None
        
        project_yaml = git_root / '.empirica' / 'project.yaml'
        if not project_yaml.exists():
            if not quiet:
                print(f"⚠️  No .empirica/project.yaml - run 'empirica project-init'")
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
            print(f"📁 {project_info['name']} ({project_info['project_id'][:8]}...)")
        else:
            # Full banner for normal mode
            print(f"📁 Project: {project_info['name']}")
            print(f"🆔 ID: {project_info['project_id'][:8]}...")
            print(f"📍 Location: {project_info['git_root']}")
            
            if verbose and git_url:
                print(f"🔗 Repository: {git_url}")
        
        return project_info
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Could not load project context: {e}")
        if not quiet:
            print(f"⚠️  Error loading project context: {e}")
        return None