"""
🧭 Intelligent Navigation Engine - Enterprise Component
Advanced workspace navigation and intelligent path optimization
"""

from .intelligent_navigation import (
    NavigationMode,
    PathType,
    NavigationMetrics,
    NavigationStrategy,
    IntelligentWorkspaceNavigator,
    WorkspaceOptimizer,
    PathIntelligence
)

__all__ = [
    'IntelligentWorkspaceNavigator',
    'NavigationStrategy',
    'WorkspaceOptimizer',
    'PathIntelligence',
    'NavigationMode',
    'PathType',
    'NavigationMetrics'
]

__version__ = "1.0.0"
__component__ = "intelligent_navigation"
__tier__ = "enterprise"
__purpose__ = "Advanced workspace navigation with intelligent optimization"