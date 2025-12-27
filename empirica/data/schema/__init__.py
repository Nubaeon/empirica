"""
Database Schema Modules

Organizes all Empirica database table schemas into logical groups.
Each module contains CREATE TABLE statements for related tables.
"""

from .sessions_schema import SCHEMAS as SESSIONS_SCHEMAS
from .epistemic_schema import SCHEMAS as EPISTEMIC_SCHEMAS
from .goals_schema import SCHEMAS as GOALS_SCHEMAS
from .projects_schema import SCHEMAS as PROJECTS_SCHEMAS
from .tracking_schema import SCHEMAS as TRACKING_SCHEMAS

# All schemas in execution order
ALL_SCHEMAS = (
    SESSIONS_SCHEMAS +
    EPISTEMIC_SCHEMAS +
    GOALS_SCHEMAS +
    PROJECTS_SCHEMAS +
    TRACKING_SCHEMAS
)

__all__ = [
    'ALL_SCHEMAS',
    'SESSIONS_SCHEMAS',
    'EPISTEMIC_SCHEMAS',
    'GOALS_SCHEMAS',
    'PROJECTS_SCHEMAS',
    'TRACKING_SCHEMAS',
]
