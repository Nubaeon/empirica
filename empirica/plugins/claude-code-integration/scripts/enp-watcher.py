#!/usr/bin/env python3
"""
ENP Watcher v0 — Git folder change detector.

Polls configured repos, detects changes in watched paths,
writes pending notifications for Claude to surface.

Runs via cron. No dependencies beyond stdlib + git.
"""

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ENP_DIR = Path.home() / '.empirica' / 'enp'
CONFIG_PATH = ENP_DIR / 'config.json'
PENDING_PATH = ENP_DIR / 'pending.json'
STATE_PATH = ENP_DIR / 'state.json'
LOG_PATH = ENP_DIR / 'watcher.log'


def push_notify(config: dict, notifications: list):
    """Send push notification via the empirica notify dispatcher.

    Migrated 2026-04-28: was direct urllib request with ntfy header-
    stuffing, which crashes on emoji (latin-1 codec error). The empirica
    dispatcher uses ntfy's JSON publish format (UTF-8 native) and routes
    through ~/.empirica/notify.yaml so backend/auth changes don't
    require touching this script. Falls through silently when push is
    disabled in config.
    """
    push_cfg = config.get('push', {})
    if not push_cfg.get('enabled'):
        return

    # Topic precedence: explicit ntfy_topics list (config) overrides any
    # routing rules. Pass topic_override per emit so the dispatcher
    # respects what enp-config asked for.
    topics = push_cfg.get('ntfy_topics', [])
    if not topics:
        single = push_cfg.get('ntfy_topic')
        if single:
            topics = [single]

    for n in notifications:
        authors = ', '.join(n.get('authors', ['Unknown']))
        label = n.get('label', 'Update')
        files = n.get('files', [])
        messages = n.get('messages', [])

        title = f'{label}: {authors}'
        body_parts = []
        if messages:
            body_parts.append(messages[0])
        body_parts.append(f'{len(files)} file(s) changed')
        body = ' — '.join(body_parts)

        repo = n.get('repo', '')
        source = f'enp-watcher:{Path(repo).name}' if repo else 'enp-watcher'
        targets = topics or [None]
        for topic in targets:
            cmd = [
                'empirica', 'notify', 'emit',
                '--severity', 'info',
                '--title', title,
                '--message', body,
                '--source', source,
                '--tags', 'git,empirica,enp',
                '--output', 'json',
            ]
            if topic:
                cmd += ['--topic-override', topic]
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=15,
                )
                if result.returncode == 0:
                    label_ts = topic or '(routed)'
                    log(f'PUSH: dispatched {label_ts} — {title}')
                else:
                    detail = (result.stderr or result.stdout or '').strip()[:200]
                    log(f'PUSH: dispatcher rc={result.returncode} ({topic}) — {detail}')
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                log(f'PUSH: dispatcher failed ({topic}) — {e}')


def log(msg: str):
    """Append to log file."""
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    with open(LOG_PATH, 'a') as f:
        f.write(f'{ts} {msg}\n')


def git(repo: str, *args) -> tuple[int, str]:
    """Run a git command in repo dir."""
    try:
        result = subprocess.run(
            ['git'] + list(args),
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return 1, str(e)


def load_state() -> dict:
    """Load watcher state (last known commit per repo)."""
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_state(state: dict):
    STATE_PATH.write_text(json.dumps(state, indent=2))


def load_pending() -> list:
    """Load pending notifications."""
    if PENDING_PATH.exists():
        try:
            data = json.loads(PENDING_PATH.read_text())
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return []


def save_pending(notifications: list):
    PENDING_PATH.write_text(json.dumps(notifications, indent=2))


def expire_old(notifications: list, max_age_hours: float) -> list:
    """Remove notifications older than max_age_hours."""
    now = time.time()
    cutoff = now - (max_age_hours * 3600)
    return [n for n in notifications if n.get('timestamp_epoch', 0) > cutoff]


def check_repo(watch_config: dict, state: dict) -> list:
    """Check a single repo for changes in watched paths."""
    repo = watch_config['repo']
    remote = watch_config.get('remote', 'origin')
    branch = watch_config.get('branch', 'main')
    paths = watch_config.get('paths', [])
    label = watch_config.get('label', repo)

    if not Path(repo).exists():
        log(f'SKIP {repo}: directory not found')
        return []

    # Fetch remote
    rc, _ = git(repo, 'fetch', remote, '--quiet')
    if rc != 0:
        log(f'SKIP {repo}: fetch failed')
        return []

    # Get local and remote HEADs
    rc, local_head = git(repo, 'rev-parse', 'HEAD')
    if rc != 0:
        return []

    rc, remote_head = git(repo, 'rev-parse', f'{remote}/{branch}')
    if rc != 0:
        return []

    # State key for this repo
    state_key = f'{repo}:{remote}/{branch}'
    last_known = state.get(state_key, local_head)

    if remote_head == last_known:
        return []  # No changes

    # Get changed files between last known and remote
    rc, diff_output = git(repo, 'diff', '--name-only', last_known, remote_head)
    if rc != 0:
        log(f'SKIP {repo}: diff failed')
        return []

    all_changed = [f for f in diff_output.split('\n') if f.strip()]

    # Filter to watched paths
    watched_changes = []
    for changed_file in all_changed:
        for watch_path in paths:
            if changed_file.startswith(watch_path):
                watched_changes.append(changed_file)
                break

    if not watched_changes:
        # Files changed but not in watched paths
        state[state_key] = remote_head
        return []

    # Get commit authors for the new commits
    rc, author_output = git(repo, 'log', '--format=%an', f'{last_known}..{remote_head}')
    authors = list({a.strip() for a in author_output.split('\n') if a.strip()})

    # Get commit messages
    rc, msg_output = git(repo, 'log', '--format=%s', f'{last_known}..{remote_head}')
    messages = [m.strip() for m in msg_output.split('\n') if m.strip()]

    # Get commit count
    rc, count_output = git(repo, 'rev-list', '--count', f'{last_known}..{remote_head}')
    commit_count = int(count_output) if rc == 0 and count_output.isdigit() else len(messages)

    # Update state
    state[state_key] = remote_head

    # Pull the changes
    git(repo, 'pull', remote, branch, '--quiet')

    now = datetime.now(timezone.utc)
    notification = {
        'type': 'folder_update',
        'label': label,
        'repo': repo,
        'authors': authors,
        'files': watched_changes,
        'commit_count': commit_count,
        'messages': messages[:5],  # Cap at 5 most recent
        'from_commit': last_known[:8],
        'to_commit': remote_head[:8],
        'timestamp': now.isoformat(),
        'timestamp_epoch': time.time(),
        'acknowledged': False
    }

    log(f'NOTIFY {label}: {len(watched_changes)} files from {", ".join(authors)} ({commit_count} commits)')
    return [notification]


def main():
    if not CONFIG_PATH.exists():
        print(f'No config at {CONFIG_PATH}', file=sys.stderr)
        sys.exit(1)

    config = json.loads(CONFIG_PATH.read_text())
    max_pending = config.get('max_pending', 20)
    expiry_hours = config.get('notification_expiry_hours', 48)

    state = load_state()
    pending = load_pending()

    # Expire old notifications
    pending = expire_old(pending, expiry_hours)

    # Check each watched repo
    new_notifications = []
    for watch in config.get('watch', []):
        new_notifications.extend(check_repo(watch, state))

    if new_notifications:
        pending.extend(new_notifications)
        # Cap total pending
        if len(pending) > max_pending:
            pending = pending[-max_pending:]
        # Write flag for active session hooks to pick up
        flag_path = ENP_DIR / 'new_notification_flag'
        flag_path.write_text(str(len(new_notifications)))
        # Push to phone
        push_notify(config, new_notifications)

    save_state(state)
    save_pending(pending)

    # Print summary for cron log
    unacked = [n for n in pending if not n.get('acknowledged')]
    if unacked:
        print(f'ENP: {len(unacked)} pending notification(s)')
    if new_notifications:
        for n in new_notifications:
            print(f'  NEW: {n["label"]} — {len(n["files"])} files from {", ".join(n["authors"])}')


if __name__ == '__main__':
    main()
