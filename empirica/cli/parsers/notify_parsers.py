"""Argparse parsers for `empirica notify` subcommand group.

Per PROPOSAL_NOTIFY_DISPATCHER.md.
"""

from __future__ import annotations

from empirica.core.notify.event import VALID_SEVERITY


def add_notify_parsers(subparsers):
    """Register the `notify` subcommand group with emit/config/backends/test."""
    notify_root = subparsers.add_parser(
        'notify',
        help='Notification dispatcher — emit events through configured backends',
        description="""
Single CLI verb every loop body and hook calls to send notifications.
The dispatcher decides where the event goes based on user config
(~/.empirica/notify.yaml). Loops never need to know about ntfy
specifically — switch backends without touching call sites.

Three sharp edges in the implementation:
  1. ntfy uses JSON publish format only (no header-stuffing — emoji bug)
  2. --actions mirrors ntfy's "Label|URL" format exactly
  3. Auth via env var (config names env var; never holds the secret)

Out of scope: hook auto-triggers, severity inference, action-callback
receivers — those belong to user-side automation, not core.
        """,
    )
    notify_subs = notify_root.add_subparsers(
        dest='notify_action', metavar='action'
    )

    # ─── emit ─────────────────────────────────────────────────────────────
    emit = notify_subs.add_parser(
        'emit',
        help='Emit a notification event',
        description='Single verb every caller uses. Reads ~/.empirica/notify.yaml '
                    'to decide where the event goes.',
    )
    emit.add_argument('--severity', required=True, choices=VALID_SEVERITY,
                       help='info | warning | critical (drives default routing)')
    emit.add_argument('--title', required=True, help='One-line title')
    emit.add_argument('--message', required=True, help='Body text')
    emit.add_argument('--rationale',
                       help='Why this event is being raised (surfaces in detail-capable backends)')
    emit.add_argument('--tags',
                       help='Comma-separated tag list, e.g. "clipboard,empirica"')
    emit.add_argument('--click-url',
                       help='Primary tap-through URL')
    emit.add_argument('--actions',
                       help='Action buttons in ntfy format: "Label1|URL1,Label2|URL2,..."')
    emit.add_argument('--source',
                       help='Opaque emitter identifier — convention: loop:<name>, hook:<event>, manual, script:<n>')
    emit.add_argument('--topic-override',
                       help='Explicit topic for backends that have topics (bypasses routing)')
    emit.add_argument('--backend-override',
                       help='Explicit backend (e.g. stdout, log, ntfy) — bypasses routing')
    emit.add_argument('--dry-run', action='store_true',
                       help='Print resolved event + backend choice; do not emit')
    emit.add_argument('--output', choices=['json', 'human'], default='json',
                       help='Output format (default: json)')

    # ─── config ───────────────────────────────────────────────────────────
    config = notify_subs.add_parser(
        'config',
        help='Print effective notify config (secrets redacted)',
    )
    config.add_argument('--output', choices=['json', 'human'], default='json',
                         help='Output format (default: json)')

    # ─── backends ─────────────────────────────────────────────────────────
    backends = notify_subs.add_parser(
        'backends',
        help='List registered backends and configured-status',
    )
    backends.add_argument('--output', choices=['json', 'human'], default='json',
                           help='Output format (default: json)')

    # ─── test ─────────────────────────────────────────────────────────────
    test = notify_subs.add_parser(
        'test',
        help='Send a test event end-to-end',
    )
    test.add_argument('--backend',
                       help='Force a specific backend for the test (default: routing rules)')
    test.add_argument('--output', choices=['json', 'human'], default='json',
                       help='Output format (default: json)')
