"""Plugin / MCP manifest discovery — paths and registered servers.

Reads filesystem paths and the JSON list of registered MCP servers. Never
inspects the inner traffic of any MCP server, just registration data.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_MCP_REGISTRY_CANDIDATES: tuple[Path, ...] = (
    Path(os.path.expanduser('~/.claude/mcp.json')),
    Path(os.path.expanduser('~/.claude/settings.json')),
)

_PLUGIN_MANIFEST_GLOBS: tuple[tuple[Path, str], ...] = (
    (Path(os.path.expanduser('~/.claude/plugins')), '**/plugin.json'),
)


def _read_mcp_servers() -> list[dict[str, Any]]:
    """Best-effort registered-MCP-server enumeration."""
    rows: list[dict[str, Any]] = []
    for path in _MCP_REGISTRY_CANDIDATES:
        if not path.exists():
            continue
        try:
            with path.open('r', encoding='utf-8') as fh:
                raw = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            logger.info(f"MCP registry parse skipped {path}: {exc}")
            continue

        servers_block = (raw or {}).get('mcpServers') if isinstance(raw, dict) else None
        if not isinstance(servers_block, dict):
            continue
        for name, cfg in servers_block.items():
            if not isinstance(cfg, dict):
                continue
            rows.append({
                'name': name,
                'source': str(path),
                'command': cfg.get('command'),
                'args_count': len(cfg.get('args') or []),
            })
    return rows


def _scan_plugin_manifests() -> list[str]:
    """Enumerate plugin.json paths under ``~/.claude/plugins``."""
    paths: list[str] = []
    for base, pattern in _PLUGIN_MANIFEST_GLOBS:
        if not base.exists():
            continue
        try:
            for match in base.glob(pattern):
                paths.append(str(match))
        except OSError as exc:
            logger.info(f"plugin manifest scan skipped {base}: {exc}")
    return sorted(paths)


def _detect_env_files(start: Path | None = None) -> list[str]:
    """Return ``.env*`` paths in the current project tree (no contents)."""
    cwd = (start or Path.cwd()).resolve()
    found: set[str] = set()
    for filename in ('.env', '.env.local', '.env.production', '.env.development'):
        candidate = cwd / filename
        if candidate.exists() and candidate.is_file():
            found.add(str(candidate))
    return sorted(found)


def collect_manifests(read_surface) -> dict[str, Any]:
    """Return filesystem-tier rows + MCP server registry."""
    output: dict[str, Any] = {}

    if 'plugin_manifest_paths' in read_surface.filesystem:
        output['plugin_manifest_paths'] = _scan_plugin_manifests()
    if 'env_files_present' in read_surface.filesystem:
        output['env_files_present'] = _detect_env_files()
    if 'recently_touched_model_weights' in read_surface.filesystem:
        # Phase 1: stub. Walking $HOME for >1GB files is expensive and easy
        # to get wrong; defer to Phase 2 with a per-project root + cache.
        output['recently_touched_model_weights'] = []

    if 'registered_servers' in read_surface.mcp:
        output['mcp_registered_servers'] = _read_mcp_servers()
    if 'active_connections' in read_surface.mcp:
        # Phase 1: stub — true active-connection introspection requires
        # MCP wire-protocol cooperation. Defer to Phase 2.
        output['mcp_active_connections'] = []

    return output
