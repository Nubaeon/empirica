"""Cockpit launcher config — ``~/.empirica/cockpit/config.yaml``.

User-editable file declaring the canonical layout: tmux session name,
attach behaviour, project list (one tmux window per project), optional
status windows, and on-abnormal-exit policy.

Sensible defaults: most users don't need to touch this file. First
``empirica cockpit launch`` run with no config writes a minimal one
based on detected projects (any directory under ``~/empirical-ai/`` with
a ``.empirica/`` folder).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path.home() / '.empirica' / 'cockpit' / 'config.yaml'
DEFAULT_PROJECTS_ROOT = Path.home() / 'empirical-ai'


@dataclass
class ProjectSpec:
    """One tmux window in the cockpit — typically one project."""
    name: str
    path: str
    launch: str = 'claude'   # command to run in this window
    kind: str = 'code'       # placeholder for future split / pane semantics


@dataclass
class StatusWindow:
    """An always-on observability window (monitor, log tail, etc.)."""
    name: str
    command: str


@dataclass
class LauncherConfig:
    """Loaded cockpit config."""
    session_name: str = 'cockpit'
    attach_on_launch: bool = True
    projects: list[ProjectSpec] = field(default_factory=list)
    status_windows: list[StatusWindow] = field(default_factory=list)
    warn_on_abnormal_exit: bool = True
    auto_prune_dead: bool = False
    notify_on_abnormal_exit: bool = True

    def project_names(self) -> list[str]:
        return [p.name for p in self.projects]


def _builtin_default(projects: list[ProjectSpec] | None = None) -> LauncherConfig:
    """Sensible defaults for first-run config."""
    return LauncherConfig(
        session_name='cockpit',
        attach_on_launch=True,
        projects=projects or [],
        status_windows=[
            StatusWindow(
                name='monitor',
                command='watch -n 2 empirica status --all --pretty',
            ),
        ],
        warn_on_abnormal_exit=True,
        auto_prune_dead=False,
        notify_on_abnormal_exit=True,
    )


def detect_projects(projects_root: Path | None = None) -> list[ProjectSpec]:
    """Discover candidate projects under ``~/empirical-ai/``.

    A directory qualifies if it has a ``.empirica/`` subdirectory.
    The launch command defaults to ``claude``.
    """
    root = projects_root or DEFAULT_PROJECTS_ROOT
    if not root.exists() or not root.is_dir():
        return []
    discovered: list[ProjectSpec] = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        if (entry / '.empirica').is_dir():
            discovered.append(ProjectSpec(
                name=entry.name,
                path=str(entry.resolve()),
                launch='claude',
                kind='code',
            ))
    return discovered


def load_config(path: Path | None = None) -> LauncherConfig:
    """Load cockpit config from disk. Returns built-in defaults when
    the file doesn't exist (caller decides whether to write the default).
    """
    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.exists():
        return _builtin_default()
    try:
        import yaml
        with config_path.open(encoding='utf-8') as fh:
            raw = yaml.safe_load(fh) or {}
    except Exception:
        return _builtin_default()

    if not isinstance(raw, dict):
        return _builtin_default()

    projects = []
    for entry in raw.get('projects') or []:
        if not isinstance(entry, dict):
            continue
        name = entry.get('name')
        path = entry.get('path')
        if not name or not path:
            continue
        projects.append(ProjectSpec(
            name=str(name),
            path=str(path),
            launch=str(entry.get('launch') or 'claude'),
            kind=str(entry.get('kind') or 'code'),
        ))

    status_windows = []
    for entry in raw.get('status_windows') or []:
        if not isinstance(entry, dict):
            continue
        name = entry.get('name')
        command = entry.get('command')
        if not name or not command:
            continue
        status_windows.append(StatusWindow(name=str(name), command=str(command)))

    abnormal = raw.get('on_abnormal_exit') or {}
    return LauncherConfig(
        session_name=str(raw.get('session_name') or 'cockpit'),
        attach_on_launch=bool(raw.get('attach_on_launch', True)),
        projects=projects,
        status_windows=status_windows,
        warn_on_abnormal_exit=bool(abnormal.get('warn', True)),
        auto_prune_dead=bool(abnormal.get('auto_prune_dead', False)),
        notify_on_abnormal_exit=bool(abnormal.get('notify', True)),
    )


def _serialize(config: LauncherConfig) -> dict[str, Any]:
    return {
        'session_name': config.session_name,
        'attach_on_launch': config.attach_on_launch,
        'projects': [
            {'name': p.name, 'path': p.path, 'launch': p.launch, 'kind': p.kind}
            for p in config.projects
        ],
        'status_windows': [
            {'name': w.name, 'command': w.command}
            for w in config.status_windows
        ],
        'on_abnormal_exit': {
            'warn': config.warn_on_abnormal_exit,
            'auto_prune_dead': config.auto_prune_dead,
            'notify': config.notify_on_abnormal_exit,
        },
    }


def write_default_config(
    path: Path | None = None,
    projects_root: Path | None = None,
) -> Path:
    """Write a default cockpit config.yaml based on detected projects.

    Returns the path written. Creates parent dirs if needed. Caller
    is responsible for confirming with the user before overwriting an
    existing file (this function does NOT check).
    """
    config_path = path or DEFAULT_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)

    projects = detect_projects(projects_root=projects_root)
    config = _builtin_default(projects=projects)

    import yaml
    with config_path.open('w', encoding='utf-8') as fh:
        yaml.safe_dump(_serialize(config), fh, default_flow_style=False, sort_keys=False)
    return config_path
