"""
Sentinel - Multi-persona orchestration for Empirica

Coordinates multiple PersonaHarness instances to perform multi-perspective
epistemic assessment with COMPOSE and ARBITRATE operations.

Components:
- SentinelOrchestrator: Main orchestrator class
- OrchestrationResult: Result data structure
- composition_strategies: COMPOSE algorithms (average, weighted, consensus)
- arbitration_strategies: ARBITRATE algorithms (majority, weighted, pessimistic)
"""

from .orchestration_result import OrchestrationResult, ArbitrationResult
from .sentinel_orchestrator import SentinelOrchestrator

__all__ = [
    'SentinelOrchestrator',
    'OrchestrationResult',
    'ArbitrationResult',
]
