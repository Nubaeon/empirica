"""
Repository pattern implementation for session database domains.

Each repository encapsulates database operations for a specific domain,
sharing a single SQLite connection for transactional consistency.
"""

from .base import BaseRepository
from .sessions import SessionRepository
from .cascades import CascadeRepository
from .goals import GoalRepository
from .branches import BranchRepository
from .breadcrumbs import BreadcrumbRepository
from .projects import ProjectRepository
from .utilities import TokenRepository, CommandRepository, WorkspaceRepository
from .vectors import VectorRepository

__all__ = [
    'BaseRepository',
    'SessionRepository',
    'CascadeRepository',
    'GoalRepository',
    'BranchRepository',
    'BreadcrumbRepository',
    'ProjectRepository',
    'TokenRepository',
    'CommandRepository',
    'WorkspaceRepository',
    'VectorRepository',
]
