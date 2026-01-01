"""
Empirica Git Integration

Modular git-based coordination layer for multi-AI collaboration.

Modules:
- checkpoint_manager: Automatic checkpoint creation and loading
- goal_store: Goal/task storage in git notes for cross-AI discovery
- session_sync: Session state synchronization via git
- sentinel_hooks: Integration points for cognitive_vault Sentinel

Design Principles:
- Small, focused modules (keep files viewable)
- Each module <300 lines
- Clear separation of concerns
- Safe degradation (works without git repo)
"""

from .checkpoint_manager import CheckpointManager, auto_checkpoint
from .goal_store import GitGoalStore
from .session_sync import SessionSync
from .sentinel_hooks import SentinelHooks, SentinelDecision, SentinelState, TurtleStatus

__all__ = [
    'CheckpointManager',
    'auto_checkpoint',
    'GitGoalStore',
    'SessionSync',
    'SentinelHooks',
    'SentinelDecision',
    'SentinelState',
    'TurtleStatus'
]
