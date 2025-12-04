"""
Simplified Bootstrap - Session creation only

Components (assessor, cascade, orchestrator) created on-demand by MCP/CLI tools.
"""

from .bootstrap import (
    bootstrap_session,
    bootstrap_metacognition,
    OptimalMetacognitiveBootstrap,
    ExtendedMetacognitiveBootstrap
)

__all__ = [
    'bootstrap_session',
    'bootstrap_metacognition',
    'OptimalMetacognitiveBootstrap',
    'ExtendedMetacognitiveBootstrap',
    'EmpericaOnboardingWizard',
]