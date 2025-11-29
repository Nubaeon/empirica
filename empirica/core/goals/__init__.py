#!/usr/bin/env python3
"""
Goal Management Module

Provides structured goal tracking with success criteria, dependencies, and constraints.
MVP implementation focuses on explicit goal creation (AI creates goals directly via MCP).
"""

from .types import (
    Goal,
    SuccessCriterion,
    Dependency,
    ScopeVector,
    DependencyType
)
from .repository import GoalRepository

__all__ = [
    'Goal',
    'SuccessCriterion',
    'Dependency',
    'ScopeVector',
    'DependencyType',
    'GoalRepository'
]
