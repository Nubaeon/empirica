"""CLI handlers for `empirica voice` subcommand group.

Verbs:
  list   List available voice profiles (project-local + global)
  show   Print full profile yaml + computed summary
  apply  Print structured AI guidance for adopting a voice in a register

Profile resolution order:
  1. {cwd}/.empirica/voice/{name}.yaml   (project-local override)
  2. ~/.empirica/voice/{name}.yaml       (user-global)

Profile schema (see ~/.empirica/voice/david.yaml for canonical):
  creator_id, name, archetype, natural_register, domains[],
  tendencies[], anti_patterns[], platforms{<name>: {register, depth, framing}},
  handles{<platform>: <handle>}, voice_stats, meta
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml

# ─── profile resolution ─────────────────────────────────────────────────────


def _voice_dirs() -> list[Path]:
    """Return profile lookup dirs in priority order (project, then global)."""
    project_local = Path.cwd() / '.empirica' / 'voice'
    user_global = Path.home() / '.empirica' / 'voice'
    return [project_local, user_global]


def _resolve_profile_path(name: str) -> Path | None:
    """Find a profile by name. Project-local wins over global."""
    if name.endswith('.yaml'):
        name = name[:-5]
    for d in _voice_dirs():
        candidate = d / f'{name}.yaml'
        if candidate.exists():
            return candidate
    return None


def _list_profiles() -> list[dict]:
    """Enumerate all profiles across lookup dirs.

    Returns one dict per unique profile name. Project-local takes
    precedence — a project-local profile shadows a same-named global
    one (only the project-local entry appears in output).
    """
    seen: dict[str, dict] = {}
    for d in _voice_dirs():
        if not d.exists():
            continue
        for f in sorted(d.glob('*.yaml')):
            stem = f.stem
            if stem in seen:
                continue  # project-local already won
            try:
                data = yaml.safe_load(f.read_text()) or {}
            except Exception as e:
                seen[stem] = {
                    'name': stem,
                    'path': str(f),
                    'scope': 'project' if d == _voice_dirs()[0] else 'global',
                    'error': f'parse error: {e}',
                }
                continue
            seen[stem] = {
                'name': stem,
                'path': str(f),
                'scope': 'project' if d == _voice_dirs()[0] else 'global',
                'archetype': data.get('archetype'),
                'natural_register': data.get('natural_register'),
                'samples': (data.get('voice_stats') or {}).get('total_samples', 0),
            }
    return list(seen.values())


# ─── output ─────────────────────────────────────────────────────────────────


def _emit(args, payload: Any, *, default_human=None) -> int:
    """JSON or human output, mirroring notify_commands._emit_output."""
    fmt = getattr(args, 'output', 'human')
    if fmt == 'json':
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + '\n')
    else:
        if default_human is not None:
            sys.stdout.write(default_human + '\n')
        else:
            sys.stdout.write(json.dumps(payload, indent=2, default=str) + '\n')
    return 0


# ─── handlers ───────────────────────────────────────────────────────────────


def handle_voice_list_command(args) -> int:
    profiles = _list_profiles()
    if getattr(args, 'output', 'human') == 'json':
        return _emit(args, {'profiles': profiles})

    if not profiles:
        sys.stdout.write('No voice profiles found.\n')
        sys.stdout.write('Looked in:\n')
        for d in _voice_dirs():
            sys.stdout.write(f'  {d}\n')
        sys.stdout.write(
            "\nTo populate: run mcp__cortex__populate_voice "
            "(scrapes reddit/devto/text into Qdrant + writes the yaml).\n"
        )
        return 0

    rows = ['NAME         SCOPE     REGISTER             SAMPLES  ARCHETYPE']
    rows.append('-' * 70)
    for p in profiles:
        rows.append(
            f"{p['name']:<12} "
            f"{p['scope']:<8} "
            f"{(p.get('natural_register') or '-'):<20} "
            f"{p.get('samples', 0):>7}  "
            f"{p.get('archetype') or '-'}"
        )
        if p.get('error'):
            rows.append(f"  ⚠ {p['error']}")
    sys.stdout.write('\n'.join(rows) + '\n')
    return 0


def handle_voice_show_command(args) -> int:
    name = getattr(args, 'name', None)
    if not name:
        sys.stderr.write('error: voice show requires a profile name\n')
        return 2

    path = _resolve_profile_path(name)
    if path is None:
        sys.stderr.write(
            f"error: profile {name!r} not found in any of:\n"
        )
        for d in _voice_dirs():
            sys.stderr.write(f'  {d}\n')
        return 1

    try:
        data = yaml.safe_load(path.read_text()) or {}
    except Exception as e:
        sys.stderr.write(f'error: parse failed for {path}: {e}\n')
        return 1

    if getattr(args, 'output', 'human') == 'json':
        return _emit(args, {'name': name, 'path': str(path), 'profile': data})

    # Human-friendly summary
    out = []
    out.append(f"Profile: {data.get('name', name)}")
    out.append(f"Path:    {path}")
    out.append(f"Type:    {data.get('profile_type', '-')} | "
               f"Archetype: {data.get('archetype', '-')}")
    out.append(f"Natural register: {data.get('natural_register', '-')}")
    if data.get('domains'):
        out.append(f"Domains: {', '.join(data['domains'])}")
    if data.get('tendencies'):
        out.append("\nTendencies (foreground when drafting):")
        for t in data['tendencies']:
            out.append(f"  + {t}")
    if data.get('anti_patterns'):
        out.append("\nAnti-patterns (suppress):")
        for a in data['anti_patterns']:
            out.append(f"  - {a}")
    if data.get('platforms'):
        out.append("\nPlatform registers:")
        for plat, conf in data['platforms'].items():
            reg = (conf or {}).get('register', '-')
            depth = (conf or {}).get('depth', '-')
            framing = (conf or {}).get('framing', '-')
            out.append(f"  {plat:<10} register={reg}, depth={depth}, framing={framing}")
    if data.get('voice_stats'):
        stats = data['voice_stats']
        total = stats.get('total_samples', 0)
        sources = stats.get('sources') or {}
        src_summary = ', '.join(
            f"{name}={(s or {}).get('samples', 0)}"
            for name, s in sources.items()
        )
        out.append(f"\nSamples: {total} total ({src_summary})")
    sys.stdout.write('\n'.join(out) + '\n')
    return 0


def handle_voice_apply_command(args) -> int:
    """Print structured guidance designed for the calling AI to internalize.

    Output is deliberately structured (numbered tendencies, explicit
    register, anti-pattern checklist) so the AI consuming this can
    treat it as a checklist while drafting. Caller scopes by --register
    when drafting for a specific platform.
    """
    name = getattr(args, 'name', None)
    register = getattr(args, 'register', None)
    if not name:
        sys.stderr.write('error: voice apply requires a profile name\n')
        return 2

    path = _resolve_profile_path(name)
    if path is None:
        sys.stderr.write(f"error: profile {name!r} not found\n")
        return 1

    try:
        data = yaml.safe_load(path.read_text()) or {}
    except Exception as e:
        sys.stderr.write(f'error: parse failed for {path}: {e}\n')
        return 1

    # Resolve register: explicit --register > platforms[register] > natural_register
    natural = data.get('natural_register', 'unspecified')
    platform_conf = (data.get('platforms') or {}).get(register or '') or {}
    effective_register = (
        platform_conf.get('register')
        if platform_conf.get('register')
        else natural
    )
    depth = platform_conf.get('depth', 'medium')
    framing = platform_conf.get('framing', 'unspecified')

    payload = {
        'profile': data.get('name', name),
        'register_requested': register,
        'register_effective': effective_register,
        'depth': depth,
        'framing': framing,
        'tendencies_foreground': data.get('tendencies') or [],
        'anti_patterns_suppress': data.get('anti_patterns') or [],
        'natural_register_fallback': natural,
        'profile_path': str(path),
        'hint': (
            'Apply these tendencies and avoid the anti-patterns when drafting '
            'in this register. The guidance is descriptive of the source '
            'voice, not aspirational — match what the person actually does.'
        ),
    }

    if getattr(args, 'output', 'human') == 'json':
        return _emit(args, payload)

    out = []
    out.append(f"=== Voice profile: {payload['profile']} ===")
    out.append(f"Register: {effective_register}"
               + (f" (requested: {register})" if register else ""))
    out.append(f"Depth: {depth} | Framing: {framing}")
    out.append("")
    out.append("Foreground these tendencies:")
    for i, t in enumerate(payload['tendencies_foreground'], 1):
        out.append(f"  {i}. {t}")
    out.append("")
    out.append("Suppress these anti-patterns:")
    for a in payload['anti_patterns_suppress']:
        out.append(f"  ✗ {a}")
    out.append("")
    out.append(payload['hint'])
    sys.stdout.write('\n'.join(out) + '\n')
    return 0


# ─── group dispatcher ───────────────────────────────────────────────────────


_VOICE_DISPATCH = {
    'list': handle_voice_list_command,
    'show': handle_voice_show_command,
    'apply': handle_voice_apply_command,
}


def handle_voice_group_command(args) -> int:
    """Dispatcher for `empirica voice <action>`."""
    action = getattr(args, 'voice_action', None)
    if not action:
        sys.stderr.write('usage: empirica voice <list|show|apply> [args...]\n')
        return 2
    handler = _VOICE_DISPATCH.get(action)
    if handler is None:
        sys.stderr.write(f'error: unknown voice action: {action}\n')
        return 2
    return handler(args) or 0


__all__ = [
    'handle_voice_apply_command',
    'handle_voice_group_command',
    'handle_voice_list_command',
    'handle_voice_show_command',
]
