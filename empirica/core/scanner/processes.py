"""Process collector — psutil-based process tree walk.

Phase 1 emission only. Each row carries the canonical fields listed in
``PROCESS_FIELDS``; the read-surface filter trims them down at the collector
boundary so callers receive exactly what the surface allows.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger(__name__)


def _shorten_cmdline(cmdline: list[str], max_chars: int = 512) -> str:
    """Join a process cmdline list and clip to ``max_chars`` for safety."""
    text = ' '.join(cmdline) if cmdline else ''
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + '…'


def _row_for_proc(proc, scanner_pid: int, now: float) -> dict[str, Any] | None:
    """Build a single process row. Returns None on access failure (skip)."""
    try:
        info = proc.as_dict(attrs=[
            'pid', 'ppid', 'cmdline', 'create_time', 'cwd',
            'num_fds', 'cpu_percent', 'memory_info', 'name', 'username',
        ])
    except Exception:  # psutil.NoSuchProcess / AccessDenied / ZombieProcess
        return None

    pid = info.get('pid')
    if pid is None:
        return None

    cmdline_list = info.get('cmdline') or []
    create_time = info.get('create_time')
    age_seconds = int(now - create_time) if create_time else None

    memory_info = info.get('memory_info')
    memory_mb = None
    if memory_info is not None:
        try:
            memory_mb = round(memory_info.rss / (1024 * 1024), 2)
        except Exception:
            memory_mb = None

    return {
        'pid': pid,
        'name': info.get('name'),
        'cmdline': _shorten_cmdline(cmdline_list),
        'parent_pid': info.get('ppid'),
        'age_seconds': age_seconds,
        'working_dir': info.get('cwd'),
        'num_open_files': info.get('num_fds'),
        'cpu_percent': info.get('cpu_percent'),
        'memory_mb': memory_mb,
        'username': info.get('username'),
        'is_scanner_self': pid == scanner_pid,
    }


def collect_processes(read_surface) -> list[dict[str, Any]]:
    """Iterate the live process table and emit filtered rows.

    Returns an empty list when ``psutil`` is unavailable or the iteration
    fails wholesale; partial failures (single processes inaccessible) are
    silently skipped per the safety contract — the snapshot is best-effort.
    """
    try:
        import psutil
    except ImportError:
        logger.warning("psutil not available; process collector returning []")
        return []

    scanner_pid = os.getpid()
    now = time.time()
    rows: list[dict[str, Any]] = []

    try:
        proc_iter = psutil.process_iter([])
    except Exception as exc:
        logger.warning(f"process_iter failed: {exc}")
        return []

    for proc in proc_iter:
        row = _row_for_proc(proc, scanner_pid, now)
        if row is None:
            continue
        rows.append(read_surface.filter_dict('process', row))

    return rows
