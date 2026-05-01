"""Scheduled-task collector — crontab + systemd-user + launchd.

Each platform contributes whatever's present; the others come back empty.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _read_crontab() -> list[dict[str, Any]]:
    """Return rows for ``crontab -l`` if available."""
    if shutil.which('crontab') is None:
        return []
    try:
        result = subprocess.run(
            ['crontab', '-l'],
            check=False, capture_output=True, text=True, timeout=5,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        logger.info(f"crontab -l skipped: {exc}")
        return []

    if result.returncode != 0:
        # 'no crontab for $USER' is the normal no-content path
        return []

    rows: list[dict[str, Any]] = []
    for raw_line in (result.stdout or '').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        rows.append({'kind': 'crontab', 'line': line})
    return rows


def _scan_systemd_user_units() -> list[dict[str, Any]]:
    """Enumerate ``~/.config/systemd/user/*.{service,timer}`` filenames only."""
    base = Path(os.path.expanduser('~/.config/systemd/user'))
    if not base.exists() or not base.is_dir():
        return []

    rows: list[dict[str, Any]] = []
    try:
        for entry in sorted(base.iterdir()):
            if entry.is_file() and entry.suffix in ('.service', '.timer'):
                rows.append({
                    'kind': 'systemd-user',
                    'name': entry.name,
                    'path': str(entry),
                })
    except OSError as exc:
        logger.info(f"systemd-user unit scan skipped: {exc}")
    return rows


def _scan_launchd_agents() -> list[dict[str, Any]]:
    """Enumerate ``~/Library/LaunchAgents/*.plist`` (macOS only).

    Reads filenames; never parses plist contents.
    """
    base = Path(os.path.expanduser('~/Library/LaunchAgents'))
    if not base.exists() or not base.is_dir():
        return []

    rows: list[dict[str, Any]] = []
    try:
        for entry in sorted(base.iterdir()):
            if entry.is_file() and entry.suffix == '.plist':
                rows.append({
                    'kind': 'launchd',
                    'label': entry.stem,
                    'path': str(entry),
                })
    except OSError as exc:
        logger.info(f"launchd scan skipped: {exc}")
    return rows


def collect_scheduled(read_surface) -> dict[str, Any]:
    """Return scheduled-task rows for whichever surfaces the read-surface allows."""
    output: dict[str, Any] = {}
    if 'cron_entries' in read_surface.scheduled:
        output['cron_entries'] = _read_crontab()
    if 'systemd_user_units' in read_surface.scheduled:
        output['systemd_user_units'] = _scan_systemd_user_units()
    if 'launchd_agents' in read_surface.scheduled:
        output['launchd_agents'] = _scan_launchd_agents()
    return output
