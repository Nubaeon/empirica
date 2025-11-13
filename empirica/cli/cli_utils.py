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
    """Safely parse JSON string with fallback"""
    if not json_string:
        return default or {}
    
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parsing error: {e}")
        return default or {}


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