#!/usr/bin/env python3
"""
🧭 Workspace Awareness Module
Intelligent workspace navigation and persistent awareness for AI systems
"""

from .workspace_awareness import (
    DigitalMap,
    WorkspaceNavigator
)

def create_workspace_navigator(map_file_path: str = "digital_workspace_map.json") -> WorkspaceNavigator:
    """
    Create a Workspace Navigator instance
    
    Args:
        map_file_path (str): Path to the digital map file
        
    Returns:
        WorkspaceNavigator: Instance of the workspace navigator
    """
    return WorkspaceNavigator(map_file_path)

def activate_workspace_awareness(map_file_path: str = "digital_workspace_map.json") -> WorkspaceNavigator:
    """Activate workspace awareness capabilities"""
    print("🧭 ACTIVATING WORKSPACE AWARENESS")
    print("=" * 35)
    print("✅ Digital map initialization")
    print("✅ Persistent awareness tracking")
    print("✅ Task and project organization")
    print("✅ Intelligent navigation")
    
    return create_workspace_navigator(map_file_path)

__all__ = [
    'DigitalMap',
    'WorkspaceNavigator',
    'create_workspace_navigator',
    'activate_workspace_awareness'
]

__version__ = "1.0.0"
__component__ = "workspace_awareness"
__purpose__ = "Intelligent workspace navigation and persistent awareness for AI systems"

print(f"🧭 Workspace awareness ready for AI collaboration!")