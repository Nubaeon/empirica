"""
Empirica Statusline Cache - Persistent multi-instance cache for statusline state

Provides a central cache at ~/.empirica/statusline_cache/ that:
1. Survives system reboots (not in /tmp)
2. Supports multi-instance isolation (per tmux pane)
3. Supports multi-project isolation (per project)
4. Uses file locking for concurrent access safety

Used by:
- statusline_empirica.py (reads)
- CASCADE phase handlers (writes)
- empirica_action_hooks.py (writes)

Author: Claude Code
Date: 2026-02-04
"""

import fcntl
import hashlib
import json
import os
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Optional, Any


# Cache directory - persistent location
CACHE_DIR = Path.home() / '.empirica' / 'statusline_cache'


@dataclass
class StatuslineCacheEntry:
    """Single cache entry for a pane+project combination."""

    # Identification
    session_id: str
    ai_id: str
    instance_id: str  # tmux pane or process identifier
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    project_path: Optional[str] = None

    # Epistemic state
    phase: Optional[str] = None  # PREFLIGHT, CHECK, POSTFLIGHT
    vectors: Optional[Dict[str, float]] = None
    gate_decision: Optional[str] = None  # proceed, investigate

    # Counts
    open_goals: int = 0
    open_unknowns: int = 0
    goal_linked_unknowns: int = 0

    # Computed metrics
    confidence: Optional[float] = None

    # Timestamps
    updated_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StatuslineCacheEntry':
        """Create from dictionary."""
        # Handle missing fields gracefully
        return cls(
            session_id=data.get('session_id', ''),
            ai_id=data.get('ai_id', 'claude-code'),
            instance_id=data.get('instance_id', ''),
            project_id=data.get('project_id'),
            project_name=data.get('project_name'),
            project_path=data.get('project_path'),
            phase=data.get('phase'),
            vectors=data.get('vectors'),
            gate_decision=data.get('gate_decision'),
            open_goals=data.get('open_goals', 0),
            open_unknowns=data.get('open_unknowns', 0),
            goal_linked_unknowns=data.get('goal_linked_unknowns', 0),
            confidence=data.get('confidence'),
            updated_at=data.get('updated_at', 0.0),
        )


def get_instance_id() -> str:
    """
    Get a unique identifier for the current instance/pane.

    Priority:
    1. TMUX_PANE environment variable
    2. CLAUDE_INSTANCE_ID environment variable
    3. PID-based fallback
    """
    # tmux pane (e.g., %0, %1)
    tmux_pane = os.environ.get('TMUX_PANE')
    if tmux_pane:
        return f"tmux_{tmux_pane.replace('%', '')}"

    # Explicit instance ID
    instance_id = os.environ.get('CLAUDE_INSTANCE_ID')
    if instance_id:
        return instance_id

    # Fallback: process ID
    return f"pid_{os.getpid()}"


def get_project_hash(project_path: str) -> str:
    """Get a short hash for a project path."""
    if not project_path:
        return "global"
    return hashlib.sha256(project_path.encode()).hexdigest()[:8]


def get_cache_path(instance_id: str, project_path: Optional[str] = None) -> Path:
    """Get the cache file path for an instance+project combination."""
    project_hash = get_project_hash(project_path or "")
    return CACHE_DIR / f"{instance_id}_{project_hash}.json"


class StatuslineCache:
    """
    Central cache for statusline state with file locking.

    Usage:
        cache = StatuslineCache()

        # Write (from CASCADE handlers)
        cache.write(StatuslineCacheEntry(
            session_id="...",
            ai_id="claude-code",
            instance_id=get_instance_id(),
            phase="PREFLIGHT",
            vectors={...},
        ))

        # Read (from statusline)
        entry = cache.read()
        if entry:
            print(f"Phase: {entry.phase}, Know: {entry.vectors.get('know')}")
    """

    def __init__(self, instance_id: Optional[str] = None, project_path: Optional[str] = None):
        """
        Initialize cache for a specific instance and project.

        Args:
            instance_id: Pane/instance identifier. Auto-detected if None.
            project_path: Project root path. Auto-detected if None.
        """
        self.instance_id = instance_id or get_instance_id()
        self.project_path = project_path

        # Ensure cache directory exists
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def cache_file(self) -> Path:
        """Get the cache file path."""
        return get_cache_path(self.instance_id, self.project_path)

    def write(self, entry: StatuslineCacheEntry) -> bool:
        """
        Write cache entry with file locking.

        Args:
            entry: Cache entry to write

        Returns:
            True if write succeeded
        """
        try:
            # Update timestamp
            entry.updated_at = time.time()
            entry.instance_id = self.instance_id
            if self.project_path:
                entry.project_path = self.project_path

            # Write with exclusive lock
            with open(self.cache_file, 'w') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(entry.to_dict(), f, indent=2)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            return True
        except Exception:
            # Silent fail - statusline should never crash
            return False

    def read(self, max_age: float = 300.0) -> Optional[StatuslineCacheEntry]:
        """
        Read cache entry with file locking.

        Args:
            max_age: Maximum age in seconds. Returns None if older.

        Returns:
            Cache entry or None if not found/stale
        """
        if not self.cache_file.exists():
            return None

        try:
            with open(self.cache_file, 'r') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    data = json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            entry = StatuslineCacheEntry.from_dict(data)

            # Check staleness
            age = time.time() - entry.updated_at
            if age > max_age:
                return None

            return entry
        except Exception:
            return None

    def update(self, **kwargs) -> bool:
        """
        Update specific fields in the cache.

        Args:
            **kwargs: Fields to update

        Returns:
            True if update succeeded
        """
        entry = self.read(max_age=float('inf'))  # Don't check staleness for updates
        if entry is None:
            # Create new entry with provided fields
            entry = StatuslineCacheEntry(
                session_id=kwargs.get('session_id', ''),
                ai_id=kwargs.get('ai_id', 'claude-code'),
                instance_id=self.instance_id,
            )

        # Update provided fields
        for key, value in kwargs.items():
            if hasattr(entry, key):
                setattr(entry, key, value)

        return self.write(entry)

    def clear(self) -> bool:
        """Delete the cache file."""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
            return True
        except Exception:
            return False

    @classmethod
    def clear_all(cls, older_than: float = 86400.0) -> int:
        """
        Clear stale cache files.

        Args:
            older_than: Delete files older than this (seconds). Default 24h.

        Returns:
            Number of files deleted
        """
        count = 0
        try:
            for cache_file in CACHE_DIR.glob("*.json"):
                try:
                    if time.time() - cache_file.stat().st_mtime > older_than:
                        cache_file.unlink()
                        count += 1
                except Exception:
                    pass
        except Exception:
            pass
        return count

    @classmethod
    def list_active(cls, max_age: float = 300.0) -> list:
        """
        List all active cache entries.

        Args:
            max_age: Maximum age in seconds

        Returns:
            List of (instance_id, project_path, entry) tuples
        """
        active = []
        try:
            for cache_file in CACHE_DIR.glob("*.json"):
                try:
                    age = time.time() - cache_file.stat().st_mtime
                    if age <= max_age:
                        with open(cache_file, 'r') as f:
                            data = json.load(f)
                        entry = StatuslineCacheEntry.from_dict(data)
                        active.append((entry.instance_id, entry.project_path, entry))
                except Exception:
                    pass
        except Exception:
            pass
        return active


# Convenience functions for direct usage

def write_statusline_cache(
    session_id: str,
    ai_id: str,
    phase: Optional[str] = None,
    vectors: Optional[Dict[str, float]] = None,
    gate_decision: Optional[str] = None,
    project_path: Optional[str] = None,
    project_name: Optional[str] = None,
    open_goals: int = 0,
    open_unknowns: int = 0,
    confidence: Optional[float] = None,
) -> bool:
    """
    Write to statusline cache.

    Use this from CASCADE phase handlers and hooks.
    """
    cache = StatuslineCache(project_path=project_path)
    entry = StatuslineCacheEntry(
        session_id=session_id,
        ai_id=ai_id,
        instance_id=get_instance_id(),
        project_name=project_name,
        project_path=project_path,
        phase=phase,
        vectors=vectors,
        gate_decision=gate_decision,
        open_goals=open_goals,
        open_unknowns=open_unknowns,
        confidence=confidence,
    )
    return cache.write(entry)


def read_statusline_cache(
    project_path: Optional[str] = None,
    max_age: float = 300.0
) -> Optional[StatuslineCacheEntry]:
    """
    Read from statusline cache.

    Use this from statusline script for fast rendering.
    """
    cache = StatuslineCache(project_path=project_path)
    return cache.read(max_age=max_age)


def update_statusline_vectors(
    vectors: Dict[str, float],
    project_path: Optional[str] = None
) -> bool:
    """
    Update just the vectors in the cache.

    Use this for real-time vector updates.
    """
    cache = StatuslineCache(project_path=project_path)
    return cache.update(vectors=vectors)


def update_statusline_phase(
    phase: str,
    gate_decision: Optional[str] = None,
    project_path: Optional[str] = None
) -> bool:
    """
    Update the CASCADE phase in the cache.

    Use this after phase transitions.
    """
    cache = StatuslineCache(project_path=project_path)
    kwargs = {'phase': phase}
    if gate_decision:
        kwargs['gate_decision'] = gate_decision
    return cache.update(**kwargs)
