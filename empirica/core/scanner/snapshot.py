"""Snapshot — canonical scanner output dataclass + the ``collect_snapshot`` orchestrator.

A snapshot is the deterministic Phase-1 emission: a JSON-serializable
dataclass containing each collector's filtered output plus a small header.
No interpretation, no judgement, no classification. Phase 2 will read
``Snapshot.to_dict()`` and add the agent-judgment layer.
"""

from __future__ import annotations

import json
import os
import platform
import socket
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from .env_names import collect_env_var_names
from .manifests import collect_manifests
from .network import collect_network
from .processes import collect_processes
from .read_surface import DEFAULT_READ_SURFACE, ReadSurface, load_read_surface
from .scheduled import collect_scheduled


@dataclass
class Snapshot:
    """Single ``empirica scan`` snapshot — the deterministic ground truth."""

    scan_id: str
    started_at: float            # epoch seconds
    finished_at: float | None
    host: str
    platform: str
    scanner_pid: int
    snapshot: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=False, default=str)

    # ── Convenience accessors ────────────────────────────────────────────
    @property
    def processes(self) -> list[dict[str, Any]]:
        return self.snapshot.get('processes', [])

    @property
    def listening_ports(self) -> list[int]:
        net = self.snapshot.get('network') or {}
        return list(net.get('listening_ports', []))

    @property
    def env_var_names(self) -> list[str]:
        env = self.snapshot.get('process_env') or {}
        return list(env.get('var_names_only', []))


def collect_snapshot(read_surface: ReadSurface | None = None,
                     project_yaml: str | None = None) -> Snapshot:
    """Run every collector and assemble a :class:`Snapshot`.

    ``read_surface`` overrides automatic resolution; pass ``None`` to read
    from ``project.yaml`` (default).
    """
    surface = read_surface or load_read_surface(project_yaml)

    snap = Snapshot(
        scan_id=str(uuid.uuid4()),
        started_at=time.time(),
        finished_at=None,
        host=socket.gethostname(),
        platform=f"{platform.system()} {platform.release()}",
        scanner_pid=os.getpid(),
    )

    def _safe(name: str, fn):
        try:
            return fn()
        except Exception as exc:
            snap.errors.append(f"{name}: {type(exc).__name__}: {exc}")
            return None

    snap.snapshot['processes'] = _safe('processes', lambda: collect_processes(surface)) or []
    snap.snapshot['network'] = _safe('network', lambda: collect_network(surface)) or {}
    snap.snapshot['scheduled'] = _safe('scheduled', lambda: collect_scheduled(surface)) or {}
    snap.snapshot['process_env'] = _safe('process_env',
                                         lambda: collect_env_var_names(surface)) or {}
    snap.snapshot['filesystem'] = _safe('filesystem', lambda: collect_manifests(surface)) or {}
    snap.snapshot['read_surface_summary'] = {
        'process_fields': sorted(surface.process),
        'network_fields': sorted(surface.network),
        'filesystem_fields': sorted(surface.filesystem),
        'process_env_fields': sorted(surface.process_env),
        'scheduled_fields': sorted(surface.scheduled),
        'mcp_fields': sorted(surface.mcp),
    }

    snap.finished_at = time.time()
    return snap


__all__ = [
    'DEFAULT_READ_SURFACE',
    'Snapshot',
    'collect_snapshot',
]
