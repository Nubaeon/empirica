"""
Component package exports
"""

try:
    from .code_intelligence_analyzer.code_intelligence_analyzer import CodeIntelligenceAnalyzer
    from .context_validation.context_validation import ContextIntegrityValidator
    from .empirical_performance_analyzer.empirical_performance_analyzer import EmpiricalPerformanceAnalyzer
    from .environment_stabilization.environment_stabilization import EnvironmentStabilizer
    # Removed: canonical_goal_orchestrator - replaced by canonical architecture
    from .intelligent_navigation.intelligent_navigation import IntelligentWorkspaceNavigator
    from .procedural_analysis.procedural_analysis import ProceduralAnalysisEngine
    from .runtime_validation.runtime_validation import RuntimeCodeValidator
    from .security_monitoring.security_monitoring import SecurityMonitoringEngine
    from .tool_management.tool_management import AIEnhancedToolManager
    from .workspace_awareness.workspace_awareness import WorkspaceNavigator

    __all__ = [
        'CodeIntelligenceAnalyzer',
        'ContextIntegrityValidator',
        'EmpiricalPerformanceAnalyzer',
        'EnvironmentStabilizer',
        # Removed: 'CanonicalGoalOrchestrator',
        'IntelligentWorkspaceNavigator',
        'ProceduralAnalysisEngine',
        'RuntimeCodeValidator',
        'SecurityMonitoringEngine',
        'AIEnhancedToolManager',
        'WorkspaceNavigator',
    ]
except ImportError:
    __all__ = []
