"""Scanner — local-first inventory of running AI-touching services.

Phase 1 (deterministic data collection only). Per
docs/architecture/PROPOSAL_AI_SERVICE_SCANNER.md.

Public API:
    collect_snapshot(read_surface=None) -> Snapshot
    Snapshot                       — canonical output dataclass
    load_read_surface(path=None)   — parse cockpit.scanner.read_surface
    DEFAULT_READ_SURFACE           — fallback when no project.yaml entry
"""

from .read_surface import DEFAULT_READ_SURFACE, ReadSurface, load_read_surface
from .snapshot import Snapshot, collect_snapshot

__all__ = [
    'DEFAULT_READ_SURFACE',
    'ReadSurface',
    'Snapshot',
    'collect_snapshot',
    'load_read_surface',
]
