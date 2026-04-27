"""Tests for empirica.core.notify — event/config/dispatcher/backends.

Coverage focus:
  - parse_tags / parse_actions edge cases
  - NotifyConfig built-in defaults + YAML load
  - Routing rule matching (severity / source-glob / tag-glob)
  - Dispatcher fallback semantics (unknown backend, not-configured)
  - Backend interface contracts (stdout, log, ntfy JSON shape)
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from empirica.core.notify import (
    NotifyEvent,
    dispatch,
    load_config,
    parse_actions,
    parse_tags,
    redact_config,
)
from empirica.core.notify.backends import (
    LogBackend,
    NtfyBackend,
    StdoutBackend,
    get_backend,
    known_backends,
)
from empirica.core.notify.config import NotifyConfig, RoutingRule


# ─── parse_tags ─────────────────────────────────────────────────────────────


class TestParseTags:
    def test_empty_returns_empty(self):
        assert parse_tags(None) == []
        assert parse_tags('') == []

    def test_basic_split(self):
        assert parse_tags('a,b,c') == ['a', 'b', 'c']

    def test_strips_whitespace(self):
        assert parse_tags(' a , b , c ') == ['a', 'b', 'c']

    def test_drops_empty_segments(self):
        assert parse_tags('a,,b,') == ['a', 'b']


# ─── parse_actions ──────────────────────────────────────────────────────────


class TestParseActions:
    def test_empty_returns_empty(self):
        assert parse_actions(None) == []
        assert parse_actions('') == []

    def test_single_action(self):
        assert parse_actions('Accept|http://a') == [('Accept', 'http://a')]

    def test_multi_action_ntfy_format(self):
        assert parse_actions('Accept|http://a,Reject|http://b') == [
            ('Accept', 'http://a'),
            ('Reject', 'http://b'),
        ]

    def test_drops_malformed(self):
        # No pipe → drop. Empty label → drop. Empty url → drop.
        assert parse_actions('NoUrl,|orphan,Label|') == []

    def test_url_with_query_params_preserved(self):
        # First | only — URL can contain anything after.
        assert parse_actions('Open|http://x?a=1&b=2') == [
            ('Open', 'http://x?a=1&b=2'),
        ]


# ─── config ─────────────────────────────────────────────────────────────────


class TestConfigDefaults:
    def test_missing_file_returns_builtin(self):
        cfg = load_config(Path('/nonexistent/path/notify.yaml'))
        assert cfg.default_backend == 'stdout'
        assert 'stdout' in cfg.backends
        assert 'log' in cfg.backends

    def test_yaml_load_merges_with_defaults(self):
        with tempfile.NamedTemporaryFile('w', suffix='.yaml', delete=False) as f:
            f.write("""
default_backend: ntfy
backends:
  ntfy:
    server: https://ntfy.example.com
    auth_method: bearer
    auth_env: NTFY_TOKEN
    default_topic: empirica
routing:
  - match: {severity: critical}
    backend: ntfy
    topic: empirica-critical
defaults:
  click_url_base: https://example.com
""")
            path = Path(f.name)

        try:
            cfg = load_config(path)
            assert cfg.default_backend == 'ntfy'
            assert cfg.backends['ntfy']['server'] == 'https://ntfy.example.com'
            # builtin stdout/log still present (merge)
            assert 'stdout' in cfg.backends
            assert 'log' in cfg.backends
            assert len(cfg.routing) == 1
            assert cfg.routing[0].backend == 'ntfy'
            assert cfg.routing[0].topic == 'empirica-critical'
        finally:
            path.unlink()


class TestRedactConfig:
    def test_inline_secrets_redacted(self):
        cfg = NotifyConfig(
            default_backend='ntfy',
            backends={'ntfy': {'token': 'super-secret', 'auth': 'pw'}},
        )
        out = redact_config(cfg)
        assert out['backends']['ntfy']['token'] == '<redacted>'
        assert out['backends']['ntfy']['auth'] == '<redacted>'

    def test_auth_env_resolution_indicated(self):
        cfg = NotifyConfig(
            default_backend='ntfy',
            backends={'ntfy': {'auth_env': '__NEVER_SET_HOPEFULLY'}},
        )
        out = redact_config(cfg)
        assert out['backends']['ntfy']['_auth_env_resolved'] == '<unset>'


# ─── dispatcher routing ─────────────────────────────────────────────────────


class TestRouting:
    def test_empty_routing_uses_default_backend(self):
        cfg = NotifyConfig(default_backend='stdout')
        event = NotifyEvent(severity='info', title='t', message='m')
        result = dispatch(event, cfg, dry_run=True)
        assert result.resolved_backend == 'stdout'

    def test_severity_match_picks_rule(self):
        cfg = NotifyConfig(
            default_backend='stdout',
            routing=[
                RoutingRule(match={'severity': 'critical'}, backend='log'),
            ],
        )
        event = NotifyEvent(severity='critical', title='t', message='m')
        result = dispatch(event, cfg, dry_run=True)
        assert result.resolved_backend == 'log'

    def test_source_glob_match(self):
        cfg = NotifyConfig(
            default_backend='stdout',
            routing=[
                RoutingRule(match={'source': 'loop:*'}, backend='log'),
            ],
        )
        event = NotifyEvent(
            severity='info', title='t', message='m', source='loop:metrics',
        )
        result = dispatch(event, cfg, dry_run=True)
        assert result.resolved_backend == 'log'

    def test_tag_glob_match(self):
        cfg = NotifyConfig(
            default_backend='stdout',
            routing=[
                RoutingRule(match={'tag': 'urgent'}, backend='log'),
            ],
        )
        event = NotifyEvent(
            severity='info', title='t', message='m',
            tags=['urgent', 'oncall'],
        )
        result = dispatch(event, cfg, dry_run=True)
        assert result.resolved_backend == 'log'

    def test_first_match_wins(self):
        cfg = NotifyConfig(
            default_backend='stdout',
            routing=[
                RoutingRule(match={'severity': 'info'}, backend='log'),
                RoutingRule(match={}, backend='ntfy'),  # would match all
            ],
        )
        event = NotifyEvent(severity='info', title='t', message='m')
        result = dispatch(event, cfg, dry_run=True)
        assert result.resolved_backend == 'log'

    def test_backend_override_bypasses_routing(self):
        cfg = NotifyConfig(
            default_backend='stdout',
            routing=[RoutingRule(match={}, backend='log')],
        )
        event = NotifyEvent(severity='info', title='t', message='m')
        result = dispatch(event, cfg, backend_override='stdout', dry_run=True)
        assert result.resolved_backend == 'stdout'


# ─── dispatcher fallback ────────────────────────────────────────────────────


class TestFallback:
    def test_unknown_backend_falls_back_to_stdout(self, capsys):
        cfg = NotifyConfig(default_backend='stdout')
        event = NotifyEvent(severity='info', title='t', message='m')
        result = dispatch(event, cfg, backend_override='nonexistent')
        assert result.fell_back is True
        assert result.resolved_backend == 'nonexistent'
        assert result.emit_result.backend == 'stdout'
        assert 'unknown backend' in (result.fallback_reason or '')

    def test_not_configured_falls_back_to_stdout(self, capsys):
        # ntfy with no server URL is not configured.
        cfg = NotifyConfig(
            default_backend='ntfy',
            backends={'ntfy': {}},  # no server, no auth
        )
        event = NotifyEvent(severity='info', title='t', message='m')
        result = dispatch(event, cfg)
        assert result.fell_back is True
        assert result.resolved_backend == 'ntfy'
        assert result.emit_result.backend == 'stdout'
        assert 'not configured' in (result.fallback_reason or '')

    def test_dry_run_skips_emit(self):
        cfg = NotifyConfig(default_backend='stdout')
        event = NotifyEvent(severity='info', title='t', message='m')
        result = dispatch(event, cfg, dry_run=True)
        assert result.fell_back is False
        assert '[dry-run]' in result.emit_result.detail


# ─── backends ───────────────────────────────────────────────────────────────


class TestBackendRegistry:
    def test_known_backends(self):
        assert set(known_backends()) == {'stdout', 'log', 'ntfy'}

    def test_unknown_backend_returns_none(self):
        assert get_backend('made-up', {}) is None


class TestStdoutBackend:
    def test_always_configured(self):
        assert StdoutBackend({}).is_configured() is True

    def test_emit_succeeds(self, capsys):
        b = StdoutBackend({})
        event = NotifyEvent(
            severity='info', title='hi', message='m',
            tags=['x', 'y'], source='manual',
        )
        result = b.emit(event)
        assert result.ok is True
        captured = capsys.readouterr()
        assert 'hi' in captured.out
        assert 'INFO' in captured.out


class TestLogBackend:
    def test_emit_writes_jsonl(self, tmp_path):
        log_path = tmp_path / 'notify.log'
        b = LogBackend({'path': str(log_path)})
        event = NotifyEvent(severity='info', title='t', message='m')
        result = b.emit(event)
        assert result.ok is True
        line = log_path.read_text().strip()
        parsed = json.loads(line)
        assert parsed['title'] == 't'
        assert parsed['severity'] == 'info'
        assert 'ts' in parsed


class TestNtfyBackend:
    def test_not_configured_without_server(self):
        b = NtfyBackend({})
        assert b.is_configured() is False

    def test_not_configured_when_auth_env_missing(self):
        b = NtfyBackend({
            'server': 'https://ntfy.example.com',
            'auth_method': 'bearer',
            'auth_env': '__NTFY_TEST_NEVER_SET',
        })
        # Ensure env var is unset
        os.environ.pop('__NTFY_TEST_NEVER_SET', None)
        assert b.is_configured() is False

    def test_configured_with_server_and_no_auth(self):
        b = NtfyBackend({
            'server': 'https://ntfy.example.com',
            'auth_method': 'none',
        })
        assert b.is_configured() is True

    def test_payload_shape_matches_ntfy_json_spec(self):
        # Validates the sharp edge: JSON publish format only, never headers.
        b = NtfyBackend({
            'server': 'https://ntfy.example.com',
            'auth_method': 'none',
            'default_topic': 'empirica',
        })
        event = NotifyEvent(
            severity='warning', title='t', message='m',
            tags=['a', 'b'], click_url='http://c',
            actions=[('Accept', 'http://acc'), ('Reject', 'http://rej')],
        )
        payload = b._build_payload(event)
        assert payload['topic'] == 'empirica'
        assert payload['title'] == 't'
        assert payload['message'] == 'm'
        assert payload['priority'] == 4  # warning → 4
        assert payload['tags'] == ['a', 'b']
        assert payload['click'] == 'http://c'
        assert payload['actions'] == [
            {'action': 'view', 'label': 'Accept', 'url': 'http://acc'},
            {'action': 'view', 'label': 'Reject', 'url': 'http://rej'},
        ]

    def test_severity_to_priority_mapping(self):
        b = NtfyBackend({'server': 'http://x', 'default_topic': 't'})
        assert b._build_payload(
            NotifyEvent(severity='info', title='t', message='m'),
        )['priority'] == 3
        assert b._build_payload(
            NotifyEvent(severity='warning', title='t', message='m'),
        )['priority'] == 4
        assert b._build_payload(
            NotifyEvent(severity='critical', title='t', message='m'),
        )['priority'] == 5

    def test_emit_no_topic_returns_error(self):
        b = NtfyBackend({'server': 'https://ntfy.example.com'})
        event = NotifyEvent(severity='info', title='t', message='m')
        result = b.emit(event)
        assert result.ok is False
        assert 'topic' in result.detail.lower()

    def test_emoji_in_title_no_unicode_error(self):
        # The bug we paid for: emoji in headers → latin-1 codec error.
        # JSON body avoids this entirely. Just verify payload encodes cleanly.
        b = NtfyBackend({'server': 'http://x', 'default_topic': 't'})
        event = NotifyEvent(
            severity='info', title='🔔 Empirica notify', message='hello',
        )
        payload = b._build_payload(event)
        # Must encode to UTF-8 without error.
        body = json.dumps(payload).encode('utf-8')
        assert b'\\u' in body or 'Empirica notify' in body.decode('utf-8')


# ─── NotifyEvent serialization ──────────────────────────────────────────────


class TestNotifyEventToDict:
    def test_actions_serialized_as_label_url_dicts(self):
        event = NotifyEvent(
            severity='info', title='t', message='m',
            actions=[('A', 'http://a')],
        )
        d = event.to_dict()
        assert d['actions'] == [{'label': 'A', 'url': 'http://a'}]

    def test_full_round_trip(self):
        event = NotifyEvent(
            severity='critical', title='t', message='m',
            rationale='because', tags=['x'], click_url='http://c',
            source='loop:foo', topic='topic-x',
        )
        d = event.to_dict()
        assert d['severity'] == 'critical'
        assert d['rationale'] == 'because'
        assert d['source'] == 'loop:foo'
        assert d['topic'] == 'topic-x'
