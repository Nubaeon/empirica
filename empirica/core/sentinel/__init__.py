"""
Sentinel Orchestration Layer

Domain-aware epistemic governance with:
- Persona selection via Qdrant similarity
- Auto-spawning of parallel epistemic agents
- Domain profile compliance gates
- CHECK phase enhancement

Usage:
    from empirica.core.sentinel import Sentinel, DecisionLogic

    sentinel = Sentinel(session_id=session_id)
    sentinel.load_domain_profile("healthcare")

    # Auto-orchestrate a task
    result = sentinel.orchestrate(
        task="Analyze authentication vulnerabilities",
        max_agents=3
    )
"""

from .decision_logic import DecisionLogic, PersonaMatch
from .orchestrator import (
    Sentinel,
    OrchestrationResult,
    EpistemicLoopTracker,
    LoopRecord,
    LoopMode,
    DomainProfile,
    ComplianceGate,
    GateAction,
    MergeStrategy,
)

__all__ = [
    'DecisionLogic',
    'PersonaMatch',
    'Sentinel',
    'OrchestrationResult',
    'EpistemicLoopTracker',
    'LoopRecord',
    'LoopMode',
    'DomainProfile',
    'ComplianceGate',
    'GateAction',
    'MergeStrategy',
]
