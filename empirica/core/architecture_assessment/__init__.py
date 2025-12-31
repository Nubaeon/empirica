"""
Epistemic Architecture Assessment

Applies Empirica's epistemic framework to code architecture decisions.
Meta-analysis: using Empirica to assess Empirica.

Core insight: The same vectors that track AI epistemic state can track
code component health. High uncertainty about a component = high risk.

Components:
- ComponentAssessor: Main orchestrator combining all analyzers
- CouplingAnalyzer: Dependency graph, API surface, boundary clarity
- StabilityEstimator: Git history, change velocity, ownership patterns

Output: ComponentAssessment with vectors mapped to architecture concerns.

Usage:
    from empirica.core.architecture_assessment import ComponentAssessor

    assessor = ComponentAssessor("/path/to/project")
    assessment = assessor.assess("src/module.py")
    print(assessment.summary())
"""

from .schema import (
    ComponentAssessment,
    ArchitectureVectors,
    CouplingMetrics,
    StabilityMetrics,
)
from .coupling_analyzer import CouplingAnalyzer
from .stability_estimator import StabilityEstimator
from .assessor import ComponentAssessor

__all__ = [
    "ComponentAssessor",
    "ComponentAssessment",
    "ArchitectureVectors",
    "CouplingMetrics",
    "StabilityMetrics",
    "CouplingAnalyzer",
    "StabilityEstimator",
]
