"""Phase 1 tests for the AI service scanner.

Covers:
- Read-surface defaults and parse-from-yaml
- Read-surface enforcement (collectors only emit fields the surface allows)
- Scanner self-detection (the running process appears with the self flag)
- Snapshot orchestration (errors are captured, not raised)

See docs/architecture/PROPOSAL_AI_SERVICE_SCANNER.md.
"""

from __future__ import annotations

import os

from empirica.core.scanner import (
    DEFAULT_READ_SURFACE,
    Snapshot,
    collect_snapshot,
    load_read_surface,
)
from empirica.core.scanner.env_names import collect_env_var_names
from empirica.core.scanner.processes import collect_processes
from empirica.core.scanner.read_surface import (
    PROCESS_FIELDS,
    ReadSurface,
    parse_read_surface,
)


# ── Read-surface defaults + parse ────────────────────────────────────────


class TestReadSurface:
    def test_default_surface_has_all_collector_fields(self):
        for name in ('process', 'network', 'filesystem',
                     'process_env', 'scheduled', 'mcp'):
            assert getattr(DEFAULT_READ_SURFACE, name)

    def test_default_process_surface_includes_self_flag(self):
        assert 'is_scanner_self' in DEFAULT_READ_SURFACE.process

    def test_parse_drops_unknown_fields(self):
        cfg = {'process': ['pid', 'cmdline', 'banana_count']}
        surface = parse_read_surface(cfg)
        assert 'pid' in surface.process
        assert 'cmdline' in surface.process
        assert 'banana_count' not in surface.process

    def test_parse_falls_back_to_default_when_missing(self):
        cfg = {'process': ['pid']}
        surface = parse_read_surface(cfg)
        # 'process' was overridden; 'network' falls back to default.
        assert surface.process == frozenset({'pid'})
        assert surface.network == DEFAULT_READ_SURFACE.network

    def test_load_read_surface_returns_default_when_no_yaml(self, tmp_path):
        # Path that doesn't exist → default
        result = load_read_surface(tmp_path / 'missing.yaml')
        assert result == DEFAULT_READ_SURFACE

    def test_load_read_surface_parses_yaml(self, tmp_path):
        import yaml

        yaml_path = tmp_path / 'project.yaml'
        yaml_path.write_text(yaml.safe_dump({
            'cockpit': {
                'scanner': {
                    'read_surface': {
                        'process': ['pid', 'cmdline'],
                        'network': ['pid', 'peer_host'],
                    },
                    'relevant_globs_for_coverage': {
                        'code': ['empirica/**/*.py'],
                    },
                }
            }
        }))

        surface = load_read_surface(yaml_path)
        assert surface.process == frozenset({'pid', 'cmdline'})
        assert surface.network == frozenset({'pid', 'peer_host'})
        assert surface.relevant_globs_for_coverage == {'code': ['empirica/**/*.py']}

    def test_filter_dict_drops_disallowed_keys(self):
        surface = ReadSurface(
            process=frozenset({'pid', 'cmdline'}),
            network=frozenset(),
            filesystem=frozenset(),
            process_env=frozenset(),
            scheduled=frozenset(),
            mcp=frozenset(),
        )
        row = {'pid': 1, 'cmdline': 'init', 'memory_mb': 99, 'username': 'root'}
        filtered = surface.filter_dict('process', row)
        assert filtered == {'pid': 1, 'cmdline': 'init'}


# ── Process collector + self-detection ────────────────────────────────────


class TestProcessCollector:
    def test_emits_only_surface_fields(self):
        surface = ReadSurface(
            process=frozenset({'pid', 'cmdline', 'is_scanner_self'}),
            network=frozenset(),
            filesystem=frozenset(),
            process_env=frozenset(),
            scheduled=frozenset(),
            mcp=frozenset(),
        )
        rows = collect_processes(surface)
        # If psutil is unavailable the collector returns []; either way the
        # invariant must hold for whatever rows do come back.
        for row in rows:
            assert set(row.keys()) <= surface.process

    def test_scanner_self_row_present(self):
        rows = collect_processes(DEFAULT_READ_SURFACE)
        if not rows:
            # psutil unavailable in this env — degrade gracefully
            return
        self_rows = [r for r in rows if r.get('is_scanner_self')]
        assert len(self_rows) == 1
        assert self_rows[0]['pid'] == os.getpid()

    def test_universe_includes_documented_fields(self):
        # The universe should permit every field the proposal lists
        for required in ('pid', 'cmdline', 'parent_pid', 'age_seconds',
                         'working_dir', 'is_scanner_self'):
            assert required in PROCESS_FIELDS


# ── Env-name collector — values never leak ────────────────────────────────


class TestEnvNameCollector:
    def test_only_returns_names(self):
        fake_env = {
            'OPENAI_API_KEY': 'sk-this-must-never-be-emitted',
            'PATH': '/usr/bin',
            'ANTHROPIC_API_KEY': 'sk-ant-secret',
            'HOME': '/home/test',
        }
        result = collect_env_var_names(DEFAULT_READ_SURFACE, env=fake_env)
        names = result['var_names_only']
        assert 'OPENAI_API_KEY' in names
        assert 'ANTHROPIC_API_KEY' in names
        assert 'PATH' not in names  # not interesting
        # The value must never appear anywhere in the result
        joined = repr(result)
        assert 'sk-this-must-never-be-emitted' not in joined
        assert 'sk-ant-secret' not in joined

    def test_empty_when_surface_disallows(self):
        surface = ReadSurface(
            process=frozenset(),
            network=frozenset(),
            filesystem=frozenset(),
            process_env=frozenset(),
            scheduled=frozenset(),
            mcp=frozenset(),
        )
        result = collect_env_var_names(surface, env={'OPENAI_API_KEY': 'x'})
        assert result == {'var_names_only': []}


# ── Snapshot orchestrator ─────────────────────────────────────────────────


class TestSnapshotOrchestrator:
    def test_produces_snapshot(self):
        snap = collect_snapshot(DEFAULT_READ_SURFACE)
        assert isinstance(snap, Snapshot)
        assert snap.scan_id
        assert snap.started_at > 0
        assert snap.finished_at and snap.finished_at >= snap.started_at
        assert snap.scanner_pid == os.getpid()

    def test_snapshot_serializes_to_json(self):
        snap = collect_snapshot(DEFAULT_READ_SURFACE)
        text = snap.to_json()
        assert text.startswith('{')
        # round-trip
        import json as _json
        data = _json.loads(text)
        assert data['scan_id'] == snap.scan_id

    def test_collector_errors_are_captured_not_raised(self, monkeypatch):
        # Force one collector to raise; the snapshot should still complete
        from empirica.core.scanner import snapshot as snapshot_module

        def boom(_surface):
            raise RuntimeError("synthetic")

        monkeypatch.setattr(snapshot_module, 'collect_processes', boom)
        snap = collect_snapshot(DEFAULT_READ_SURFACE)
        assert any('processes' in err for err in snap.errors)
        assert snap.snapshot['processes'] == []
