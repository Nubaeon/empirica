"""Read-surface — declares which fields each collector is allowed to emit.

The read-surface lives in ``project.yaml`` under ``cockpit.scanner.read_surface``.
It is *the agent's read permission boundary*, not classification logic. The
collectors filter their output to exactly the fields listed here.

Phase 1 honors a fixed allow-list per collector class. The default profile
matches the proposal verbatim — projects that need a narrower surface override
the relevant section in their ``project.yaml``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Allow-lists — the universe of fields each collector can ever emit. The
# read-surface yaml is intersected with these so a typo or stray entry can
# never silently widen the boundary.
PROCESS_FIELDS: frozenset[str] = frozenset({
    'pid', 'cmdline', 'parent_pid', 'age_seconds', 'working_dir',
    'num_open_files', 'cpu_percent', 'memory_mb', 'username', 'name',
    'is_scanner_self',
})
NETWORK_FIELDS: frozenset[str] = frozenset({
    'pid', 'family', 'type', 'local_address', 'local_port',
    'peer_host', 'peer_port', 'status',
    # Aliases the proposal uses that we accept as synonyms:
    'listening_ports',
})
FILESYSTEM_FIELDS: frozenset[str] = frozenset({
    'plugin_manifest_paths', 'recently_touched_model_weights',
    'env_files_present',
})
PROCESS_ENV_FIELDS: frozenset[str] = frozenset({
    'var_names_only',  # the only valid emission — values are never read
})
SCHEDULED_FIELDS: frozenset[str] = frozenset({
    'cron_entries', 'systemd_user_units', 'launchd_agents',
})
MCP_FIELDS: frozenset[str] = frozenset({
    'registered_servers', 'active_connections',
})


@dataclass(frozen=True)
class ReadSurface:
    """Effective per-collector field allow-list."""

    process: frozenset[str]
    network: frozenset[str]
    filesystem: frozenset[str]
    process_env: frozenset[str]
    scheduled: frozenset[str]
    mcp: frozenset[str]
    relevant_globs_for_coverage: dict[str, list[str]] = field(default_factory=dict)

    def filter_dict(self, collector: str, row: dict[str, Any]) -> dict[str, Any]:
        """Return ``row`` reduced to the fields permitted for ``collector``."""
        allow = getattr(self, collector, frozenset())
        return {k: v for k, v in row.items() if k in allow}


# Default surface — the proposal verbatim, intersected with allow-lists.
DEFAULT_READ_SURFACE = ReadSurface(
    process=frozenset({
        'pid', 'cmdline', 'parent_pid', 'age_seconds', 'working_dir',
        'num_open_files', 'cpu_percent', 'memory_mb', 'is_scanner_self',
    }),
    network=frozenset({
        'pid', 'peer_host', 'peer_port', 'listening_ports',
        'local_address', 'local_port', 'status',
    }),
    filesystem=frozenset({
        'plugin_manifest_paths', 'recently_touched_model_weights',
        'env_files_present',
    }),
    process_env=frozenset({'var_names_only'}),
    scheduled=frozenset({'cron_entries', 'systemd_user_units', 'launchd_agents'}),
    mcp=frozenset({'registered_servers', 'active_connections'}),
    relevant_globs_for_coverage={},
)


_COLLECTOR_FIELD_UNIVERSES: dict[str, frozenset[str]] = {
    'process': PROCESS_FIELDS,
    'network': NETWORK_FIELDS,
    'filesystem': FILESYSTEM_FIELDS,
    'process_env': PROCESS_ENV_FIELDS,
    'scheduled': SCHEDULED_FIELDS,
    'mcp': MCP_FIELDS,
}


def _coerce_collector_fields(name: str, raw: Any) -> frozenset[str]:
    """Intersect a user-provided field list with the universe for ``name``."""
    if raw is None:
        return getattr(DEFAULT_READ_SURFACE, name)
    if not isinstance(raw, list):
        return getattr(DEFAULT_READ_SURFACE, name)
    universe = _COLLECTOR_FIELD_UNIVERSES.get(name, frozenset())
    return frozenset(f for f in raw if isinstance(f, str) and f in universe)


def parse_read_surface(raw: dict[str, Any] | None) -> ReadSurface:
    """Build a :class:`ReadSurface` from the parsed YAML ``read_surface`` block.

    Missing fields fall back to the default, unknown fields are silently dropped.
    """
    if not raw or not isinstance(raw, dict):
        return DEFAULT_READ_SURFACE

    coverage = raw.get('relevant_globs_for_coverage', {})
    if not isinstance(coverage, dict):
        coverage = {}

    return ReadSurface(
        process=_coerce_collector_fields('process', raw.get('process')),
        network=_coerce_collector_fields('network', raw.get('network')),
        filesystem=_coerce_collector_fields('filesystem', raw.get('filesystem')),
        process_env=_coerce_collector_fields('process_env', raw.get('process_env')),
        scheduled=_coerce_collector_fields('scheduled', raw.get('scheduled')),
        mcp=_coerce_collector_fields('mcp', raw.get('mcp')),
        relevant_globs_for_coverage=coverage,
    )


def _find_project_yaml(start: Path | None = None) -> Path | None:
    """Walk upward from ``start`` looking for ``.empirica/project.yaml``."""
    cwd = (start or Path.cwd()).resolve()
    for candidate in (cwd, *cwd.parents):
        path = candidate / '.empirica' / 'project.yaml'
        if path.exists():
            return path
    return None


def load_read_surface(project_yaml: str | Path | None = None) -> ReadSurface:
    """Resolve the effective read-surface for the current project.

    If ``project_yaml`` is None, walk upward from the current directory looking
    for ``.empirica/project.yaml``. Falls back to :data:`DEFAULT_READ_SURFACE`
    when no file is found, the file fails to parse, or the ``cockpit.scanner``
    block is absent.
    """
    try:
        import yaml
    except ImportError:
        return DEFAULT_READ_SURFACE

    if project_yaml is None:
        path = _find_project_yaml()
    else:
        path = Path(project_yaml)
        if not path.exists():
            return DEFAULT_READ_SURFACE

    if path is None:
        return DEFAULT_READ_SURFACE

    try:
        with path.open('r', encoding='utf-8') as fh:
            data = yaml.safe_load(fh) or {}
    except (OSError, yaml.YAMLError):
        return DEFAULT_READ_SURFACE

    cockpit = data.get('cockpit') if isinstance(data, dict) else None
    scanner_cfg = (cockpit or {}).get('scanner') if isinstance(cockpit, dict) else None
    surface_cfg = (scanner_cfg or {}).get('read_surface') if isinstance(scanner_cfg, dict) else None
    surface = parse_read_surface(surface_cfg)

    coverage_cfg = (scanner_cfg or {}).get('relevant_globs_for_coverage') \
        if isinstance(scanner_cfg, dict) else None
    if isinstance(coverage_cfg, dict) and coverage_cfg:
        surface = ReadSurface(
            process=surface.process,
            network=surface.network,
            filesystem=surface.filesystem,
            process_env=surface.process_env,
            scheduled=surface.scheduled,
            mcp=surface.mcp,
            relevant_globs_for_coverage=coverage_cfg,
        )
    return surface
