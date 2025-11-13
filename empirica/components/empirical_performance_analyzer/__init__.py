#!/usr/bin/env python3
"""
📊⚡ Empirical Performance Analyzer - Semantic Self-Aware Kit Component
Comprehensive benchmarking and metrics for obsessive AI performance measurement
"""

from .empirical_performance_analyzer import (
    PerformanceMetricType,
    BenchmarkCategory,
    BaselineType,
    SpeedMetrics,
    ReliabilityMetrics,
    QualityMetrics,
    PerformanceTestResult,
    FalsifiableHypothesis,
    EmpiricalPerformanceAnalyzer,
    SystemResourceMonitor
)

__all__ = [
    'EmpiricalPerformanceAnalyzer',
    'PerformanceTestResult',
    'SpeedMetrics',
    'ReliabilityMetrics', 
    'QualityMetrics',
    'FalsifiableHypothesis',
    'PerformanceMetricType',
    'BenchmarkCategory',
    'BaselineType',
    'SystemResourceMonitor'
]

__version__ = "1.0.0"
__component__ = "empirical_performance_analyzer"
__tier__ = "core"
__purpose__ = "Comprehensive benchmarking and metrics for obsessive AI performance measurement"

print(f"📊⚡ Empirical Performance Analyzer ready for obsessive measurement!")