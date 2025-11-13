"""
Empirica Bootstrap Module

Provides bootstrap classes for initializing the Empirica framework
with different levels of metacognitive capability.
"""

from empirica.bootstraps.extended_metacognitive_bootstrap import ExtendedMetacognitiveBootstrap
from empirica.bootstraps.optimal_metacognitive_bootstrap import OptimalMetacognitiveBootstrap
from empirica.bootstraps.onboarding_wizard import EmpericaOnboardingWizard

__all__ = [
    'ExtendedMetacognitiveBootstrap',
    'OptimalMetacognitiveBootstrap',
    'EmpericaOnboardingWizard',
]