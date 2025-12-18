"""
BEADS Integration Package

Provides optional integration with BEADS (git-native issue tracker) for
dependency tracking and multi-AI coordination.

BEADS handles:
- Task dependency graph (blocks, related, parent-child, discovered-from)
- Collision-free hash IDs (bd-a1b2, bd-f14c)
- Ready work detection
- Multi-AI coordination (optional Agent Mail)

Empirica handles:
- Epistemic tracking (confidence, learning deltas)
- CASCADE workflow integration
- Findings/unknowns/dead_ends

Integration pattern: Subprocess calls to bd CLI with --json flags.
"""

from .adapter import BeadsAdapter
from .config import BeadsConfig

__all__ = ['BeadsAdapter', 'BeadsConfig']
