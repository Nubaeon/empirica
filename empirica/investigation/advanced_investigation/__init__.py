#!/usr/bin/env python3
"""
🔬 Advanced Investigation Engine - Enterprise Component
Multi-source investigation and deep behavioral analysis capabilities
"""

from .advanced_investigation import (
    InvestigationStatus,
    EvidenceType,
    Evidence,
    InvestigationProtocol,
    AdvancedInvestigationEngine,
    CorrelationEngine,
    AnalysisEngine,
    SourceType,
    MultiSourceAnalyzer,
    SourceCorrelator
)

# Create default instances for immediate use
default_investigation_engine = AdvancedInvestigationEngine()
default_multi_source_analyzer = MultiSourceAnalyzer()
default_source_correlator = SourceCorrelator()

# Register default sources
try:
    default_multi_source_analyzer.register_source("behavioral_monitor", SourceType.BEHAVIORAL_MONITOR)
    default_multi_source_analyzer.register_source("performance_tracker", SourceType.PERFORMANCE_TRACKER)
    default_multi_source_analyzer.register_source("communication_log", SourceType.COMMUNICATION_LOG)
    
    print("🔬 Advanced Investigation: Default sources registered")
except Exception as e:
    print(f"⚠️ Source registration failed: {e}")

# Export main classes and instances
__all__ = [
    'AdvancedInvestigationEngine',
    'InvestigationProtocol',
    'Evidence',
    'EvidenceType',
    'InvestigationStatus',
    'MultiSourceAnalyzer',
    'SourceCorrelator',
    'SourceType',
    'CorrelationEngine',
    'AnalysisEngine',
    'default_investigation_engine',
    'default_multi_source_analyzer',
    'default_source_correlator'
]

__version__ = "1.0.0"
__component__ = "advanced_investigation"
__tier__ = "enterprise"
__purpose__ = "Multi-source investigation and deep behavioral analysis"

print(f"🔬 Advanced Investigation Engine ready for enterprise AI analysis!")