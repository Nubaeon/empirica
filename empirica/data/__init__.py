"""
Empirica Data Module
Provides session database, JSON handling, and epistemic snapshots for tracking
"""

from .session_database import SessionDatabase
from .epistemic_snapshot import EpistemicStateSnapshot, ContextSummary, create_snapshot
from .snapshot_provider import EpistemicSnapshotProvider

__all__ = [
    'SessionDatabase',
    'EpistemicStateSnapshot',
    'ContextSummary',
    'create_snapshot',
    'EpistemicSnapshotProvider'
]
