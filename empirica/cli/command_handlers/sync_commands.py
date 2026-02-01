"""
Sync Commands - Git notes synchronization for multi-device/multi-AI coordination

Commands:
- sync push: Push all epistemic notes to remote
- sync pull: Pull all epistemic notes from remote
- sync status: Show sync status (local vs remote)
- sync config: Configure sync settings
- rebuild: Reconstruct SQLite from git notes
"""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
from ..cli_utils import handle_cli_error

logger = logging.getLogger(__name__)


# Default sync configuration
DEFAULT_SYNC_CONFIG = {
    'enabled': True,
    'remote': 'origin',
    'visibility': 'private',  # 'private' or 'public' - determines warnings
    'provider': 'auto',  # 'github', 'gitlab', 'forgejo', 'bitbucket', 'auto'
    'auto_push_on': [],  # ['postflight', 'session_end'] - future auto-push triggers
}


def _get_config_path() -> Path:
    """Get path to .empirica/config.yaml"""
    workspace_root = _get_workspace_root()
    return Path(workspace_root) / '.empirica' / 'config.yaml'


def _load_sync_config() -> Dict[str, Any]:
    """Load sync configuration from .empirica/config.yaml"""
    config_path = _get_config_path()

    if not config_path.exists():
        return DEFAULT_SYNC_CONFIG.copy()

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

        sync_config = config.get('sync', {})

        # Merge with defaults
        result = DEFAULT_SYNC_CONFIG.copy()
        result.update(sync_config)
        return result
    except Exception as e:
        logger.warning(f"Failed to load sync config: {e}")
        return DEFAULT_SYNC_CONFIG.copy()


def _save_sync_config(sync_config: Dict[str, Any]) -> bool:
    """Save sync configuration to .empirica/config.yaml"""
    config_path = _get_config_path()

    try:
        # Load existing config
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {'version': '2.0'}

        # Update sync section
        config['sync'] = sync_config

        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write back
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        return True
    except Exception as e:
        logger.error(f"Failed to save sync config: {e}")
        return False


def _detect_provider(remote_url: str) -> str:
    """Detect git provider from remote URL"""
    remote_lower = remote_url.lower()
    if 'github.com' in remote_lower:
        return 'github'
    elif 'gitlab.com' in remote_lower or 'gitlab' in remote_lower:
        return 'gitlab'
    elif 'forgejo' in remote_lower or 'codeberg.org' in remote_lower:
        return 'forgejo'
    elif 'bitbucket.org' in remote_lower:
        return 'bitbucket'
    elif 'gitea' in remote_lower:
        return 'gitea'
    else:
        return 'unknown'


def _get_remote_url(remote: str = 'origin') -> Optional[str]:
    """Get the URL for a remote"""
    try:
        result = subprocess.run(
            ['git', 'remote', 'get-url', remote],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return None


def _is_public_repo() -> Optional[bool]:
    """Try to detect if repo is public (best effort, may return None)"""
    # This is a heuristic - we can't truly know without API calls
    # For now, return None (unknown) and rely on user config
    return None


def _list_remotes() -> Dict[str, str]:
    """List all git remotes and their URLs"""
    try:
        result = subprocess.run(
            ['git', 'remote', '-v'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return {}

        remotes = {}
        for line in result.stdout.strip().split('\n'):
            if line and '(push)' in line:
                parts = line.split()
                if len(parts) >= 2:
                    remotes[parts[0]] = parts[1]
        return remotes
    except:
        return {}


# All empirica git notes refs
EMPIRICA_NOTES_REFS = [
    'empirica/goals',
    'empirica/cascades',
    'empirica/handoffs',
    'empirica/findings',
    'empirica/unknowns',
    'empirica/dead_ends',
    'empirica/mistakes',
    'empirica/sessions',
    'empirica/checkpoints',
    'empirica/messages',
    'empirica-precompact',
    'breadcrumbs',
]


def _get_workspace_root() -> str:
    """Get workspace root (git root or cwd)"""
    import os
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except:
        pass
    return os.getcwd()


def _check_remote(remote: str = 'origin') -> bool:
    """Check if remote exists"""
    try:
        result = subprocess.run(
            ['git', 'remote', 'get-url', remote],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except:
        return False


def _count_local_notes() -> Dict[str, int]:
    """Count notes in each ref locally"""
    counts = {}
    for ref in EMPIRICA_NOTES_REFS:
        try:
            result = subprocess.run(
                ['git', 'for-each-ref', f'refs/notes/{ref}/'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                counts[ref] = len(result.stdout.strip().split('\n'))
            else:
                counts[ref] = 0
        except:
            counts[ref] = 0
    return counts


def handle_sync_config_command(args):
    """Handle sync config command - show/set sync configuration"""
    try:
        output_format = getattr(args, 'output', 'json')
        key = getattr(args, 'key', None)
        value = getattr(args, 'value', None)

        # Load current config
        sync_config = _load_sync_config()

        # If setting a value
        if key and value is not None:
            valid_keys = ['enabled', 'remote', 'visibility', 'provider']
            if key not in valid_keys:
                result = {
                    "ok": False,
                    "error": f"Unknown config key: {key}",
                    "valid_keys": valid_keys
                }
                print(json.dumps(result, indent=2))
                return 1

            # Parse boolean values
            if key == 'enabled':
                value = value.lower() in ('true', '1', 'yes', 'on')

            # Validate visibility
            if key == 'visibility' and value not in ('public', 'private'):
                result = {
                    "ok": False,
                    "error": f"visibility must be 'public' or 'private', got '{value}'"
                }
                print(json.dumps(result, indent=2))
                return 1

            # Validate provider
            if key == 'provider' and value not in ('github', 'gitlab', 'forgejo', 'gitea', 'bitbucket', 'auto', 'other'):
                result = {
                    "ok": False,
                    "error": f"provider must be one of: github, gitlab, forgejo, gitea, bitbucket, auto, other"
                }
                print(json.dumps(result, indent=2))
                return 1

            # Update and save
            sync_config[key] = value
            if _save_sync_config(sync_config):
                result = {
                    "ok": True,
                    "message": f"Set sync.{key} = {value}",
                    "config": sync_config
                }
            else:
                result = {
                    "ok": False,
                    "error": "Failed to save config"
                }

            if output_format == 'json':
                print(json.dumps(result, indent=2))
            else:
                print(f"✅ Set sync.{key} = {value}")

            return 0 if result['ok'] else 1

        # Show config (with optional key filter)
        if key:
            if key in sync_config:
                result = {
                    "ok": True,
                    "key": key,
                    "value": sync_config[key]
                }
            else:
                result = {
                    "ok": False,
                    "error": f"Unknown config key: {key}"
                }
        else:
            # Get remote info for context
            current_remote = sync_config.get('remote', 'origin')
            remote_url = _get_remote_url(current_remote)
            detected_provider = _detect_provider(remote_url) if remote_url else 'unknown'
            all_remotes = _list_remotes()

            result = {
                "ok": True,
                "config": sync_config,
                "remote_url": remote_url,
                "detected_provider": detected_provider,
                "available_remotes": all_remotes,
                "config_path": str(_get_config_path())
            }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print("📋 Sync Configuration")
            print(f"   enabled: {sync_config.get('enabled', True)}")
            print(f"   remote: {sync_config.get('remote', 'origin')}")
            print(f"   visibility: {sync_config.get('visibility', 'private')}")
            print(f"   provider: {sync_config.get('provider', 'auto')}")
            if remote_url:
                print(f"\n   Remote URL: {remote_url}")
                print(f"   Detected provider: {detected_provider}")

            # Show available remotes
            if all_remotes and len(all_remotes) > 1:
                print(f"\n   Available remotes:")
                for name, url in all_remotes.items():
                    marker = "→" if name == current_remote else " "
                    print(f"   {marker} {name}: {url}")

            print(f"\n   Config file: {_get_config_path()}")

            # Show private sync hint if visibility is private but using public provider
            visibility = sync_config.get('visibility', 'private')
            if visibility == 'private' and detected_provider in ('github', 'gitlab', 'bitbucket'):
                print("\n   💡 Private Sync Tip:")
                print("      Your visibility is 'private' but using a public provider.")
                print("      To keep epistemic notes private:")
                print("      1. Create a private repo for notes")
                print("      2. git remote add notes-private <private-repo-url>")
                print("      3. empirica sync-config remote notes-private")

            print("\n   Set with: empirica sync-config <key> <value>")
            print("   Keys: enabled, remote, visibility, provider")

        return 0 if result['ok'] else 1

    except Exception as e:
        handle_cli_error(e, "Sync config", getattr(args, 'verbose', False))
        return 1


def handle_sync_push_command(args):
    """Handle sync push command - push all epistemic notes to remote"""
    try:
        # Load config
        sync_config = _load_sync_config()

        # Use CLI arg if provided, otherwise use config
        remote = getattr(args, 'remote', None) or sync_config.get('remote', 'origin')
        output_format = getattr(args, 'output', 'json')
        dry_run = getattr(args, 'dry_run', False)
        verbose = getattr(args, 'verbose', False)
        force = getattr(args, 'force', False)

        # Check if sync is enabled
        if not sync_config.get('enabled', True) and not force:
            result = {
                "ok": False,
                "error": "Sync is disabled in config",
                "hint": "Run 'empirica sync-config enabled true' to enable or use --force"
            }
            print(json.dumps(result, indent=2))
            return 1

        # Check remote exists
        if not _check_remote(remote):
            result = {
                "ok": False,
                "error": f"Remote '{remote}' not found",
                "hint": "Run 'git remote add origin <url>' to add a remote"
            }
            print(json.dumps(result, indent=2))
            return 1

        # Visibility warning for public repos
        visibility = sync_config.get('visibility', 'private')
        remote_url = _get_remote_url(remote)
        if visibility == 'public' and not force:
            # Show warning but continue
            if output_format != 'json':
                print("⚠️  Warning: visibility=public - epistemic notes will be visible in the repo")
                print("   Use 'empirica sync-config visibility private' if this repo should be private")
                print()

        # Count local notes
        local_counts = _count_local_notes()
        total_refs = sum(1 for c in local_counts.values() if c > 0)

        if dry_run:
            result = {
                "ok": True,
                "dry_run": True,
                "remote": remote,
                "refs_to_push": total_refs,
                "note_counts": local_counts,
                "command": f"git push {remote} 'refs/notes/empirica/*:refs/notes/empirica/*'"
            }
            if output_format == 'json':
                print(json.dumps(result, indent=2))
            else:
                print(f"🔍 Dry run - would push {total_refs} note refs to {remote}")
                for ref, count in local_counts.items():
                    if count > 0:
                        print(f"   refs/notes/{ref}: {count} notes")
            return 0

        # Execute push
        push_results = {}
        errors = []

        # Push all empirica notes at once
        try:
            result = subprocess.run(
                ['git', 'push', remote, 'refs/notes/empirica/*:refs/notes/empirica/*'],
                capture_output=True, text=True, timeout=60
            )
            push_results['empirica/*'] = result.returncode == 0
            if result.returncode != 0 and result.stderr:
                errors.append(f"empirica/*: {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            errors.append("Push timed out")
        except Exception as e:
            errors.append(str(e))

        # Push breadcrumbs separately (different namespace)
        try:
            result = subprocess.run(
                ['git', 'push', remote, 'refs/notes/breadcrumbs:refs/notes/breadcrumbs'],
                capture_output=True, text=True, timeout=30
            )
            push_results['breadcrumbs'] = result.returncode == 0
        except:
            push_results['breadcrumbs'] = False

        # Push empirica-precompact separately
        try:
            result = subprocess.run(
                ['git', 'push', remote, 'refs/notes/empirica-precompact:refs/notes/empirica-precompact'],
                capture_output=True, text=True, timeout=30
            )
            push_results['empirica-precompact'] = result.returncode == 0
        except:
            push_results['empirica-precompact'] = False

        success = push_results.get('empirica/*', False)

        result = {
            "ok": success,
            "remote": remote,
            "push_results": push_results,
            "errors": errors if errors else None,
            "message": f"Pushed epistemic notes to {remote}" if success else "Push failed"
        }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            if success:
                print(f"✅ Pushed epistemic notes to {remote}")
                for ref, ok in push_results.items():
                    status = "✓" if ok else "✗"
                    print(f"   {status} {ref}")
            else:
                print(f"❌ Push failed to {remote}")
                for err in errors:
                    print(f"   Error: {err}")

        return 0 if success else 1

    except Exception as e:
        handle_cli_error(e, "Sync push", getattr(args, 'verbose', False))
        return 1


def handle_sync_pull_command(args):
    """Handle sync pull command - pull all epistemic notes from remote"""
    try:
        # Load config
        sync_config = _load_sync_config()

        # Use CLI arg if provided, otherwise use config
        remote = getattr(args, 'remote', None) or sync_config.get('remote', 'origin')
        output_format = getattr(args, 'output', 'json')
        rebuild = getattr(args, 'rebuild', False)
        verbose = getattr(args, 'verbose', False)
        force = getattr(args, 'force', False)

        # Check if sync is enabled
        if not sync_config.get('enabled', True) and not force:
            result = {
                "ok": False,
                "error": "Sync is disabled in config",
                "hint": "Run 'empirica sync-config enabled true' to enable or use --force"
            }
            print(json.dumps(result, indent=2))
            return 1

        # Check remote exists
        if not _check_remote(remote):
            result = {
                "ok": False,
                "error": f"Remote '{remote}' not found"
            }
            print(json.dumps(result, indent=2))
            return 1

        # Count local notes before pull
        local_before = _count_local_notes()

        # Execute fetch
        fetch_results = {}
        errors = []

        # Fetch all empirica notes at once
        try:
            result = subprocess.run(
                ['git', 'fetch', remote, 'refs/notes/empirica/*:refs/notes/empirica/*'],
                capture_output=True, text=True, timeout=60
            )
            fetch_results['empirica/*'] = result.returncode == 0
            if result.returncode != 0 and result.stderr:
                # Check if it's just "no matching refs" (not an error)
                if 'no matching refs' not in result.stderr.lower():
                    errors.append(f"empirica/*: {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            errors.append("Fetch timed out")
        except Exception as e:
            errors.append(str(e))

        # Fetch breadcrumbs separately
        try:
            result = subprocess.run(
                ['git', 'fetch', remote, 'refs/notes/breadcrumbs:refs/notes/breadcrumbs'],
                capture_output=True, text=True, timeout=30
            )
            fetch_results['breadcrumbs'] = result.returncode == 0
        except:
            fetch_results['breadcrumbs'] = False

        # Fetch empirica-precompact separately
        try:
            result = subprocess.run(
                ['git', 'fetch', remote, 'refs/notes/empirica-precompact:refs/notes/empirica-precompact'],
                capture_output=True, text=True, timeout=30
            )
            fetch_results['empirica-precompact'] = result.returncode == 0
        except:
            fetch_results['empirica-precompact'] = False

        # Count local notes after pull
        local_after = _count_local_notes()

        # Calculate changes
        changes = {}
        for ref in EMPIRICA_NOTES_REFS:
            before = local_before.get(ref, 0)
            after = local_after.get(ref, 0)
            if after != before:
                changes[ref] = {'before': before, 'after': after, 'delta': after - before}

        success = fetch_results.get('empirica/*', False) or not errors

        result = {
            "ok": success,
            "remote": remote,
            "fetch_results": fetch_results,
            "changes": changes if changes else None,
            "errors": errors if errors else None,
            "message": f"Pulled epistemic notes from {remote}"
        }

        # Rebuild if requested
        if rebuild and success:
            rebuild_result = _rebuild_from_notes()
            result['rebuild'] = rebuild_result

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            if success:
                print(f"✅ Pulled epistemic notes from {remote}")
                if changes:
                    for ref, change in changes.items():
                        print(f"   {ref}: {change['before']} → {change['after']} ({change['delta']:+d})")
                else:
                    print("   No changes (already up to date)")
                if rebuild and 'rebuild' in result:
                    print(f"   🔄 Rebuilt SQLite from notes")
            else:
                print(f"❌ Pull failed from {remote}")
                for err in errors:
                    print(f"   Error: {err}")

        return 0 if success else 1

    except Exception as e:
        handle_cli_error(e, "Sync pull", getattr(args, 'verbose', False))
        return 1


def handle_sync_status_command(args):
    """Handle sync status command - show sync status"""
    try:
        remote = getattr(args, 'remote', 'origin') or 'origin'
        output_format = getattr(args, 'output', 'json')

        # Check remote exists
        remote_configured = _check_remote(remote)

        # Count local notes
        local_counts = _count_local_notes()
        total_notes = sum(local_counts.values())
        refs_with_data = sum(1 for c in local_counts.values() if c > 0)

        result = {
            "ok": True,
            "remote": remote,
            "remote_configured": remote_configured,
            "local_refs": refs_with_data,
            "total_notes": total_notes,
            "note_counts": {k: v for k, v in local_counts.items() if v > 0},
            "sync_available": remote_configured
        }

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            print(f"📊 Empirica Sync Status")
            print(f"   Remote: {remote} ({'configured' if remote_configured else 'NOT configured'})")
            print(f"   Local refs with data: {refs_with_data}")
            print(f"   Total notes: {total_notes}")
            if local_counts:
                print(f"\n   Note counts:")
                for ref, count in sorted(local_counts.items()):
                    if count > 0:
                        print(f"      refs/notes/{ref}: {count}")

            if not remote_configured:
                print(f"\n   ⚠️ No remote configured. Run 'git remote add origin <url>' to enable sync.")

        return 0

    except Exception as e:
        handle_cli_error(e, "Sync status", getattr(args, 'verbose', False))
        return 1


def _rebuild_from_notes() -> Dict[str, Any]:
    """
    Rebuild database from git notes.

    This reconstructs the derived database tables from canonical git notes.
    Handles FK dependencies by ensuring referenced projects and sessions exist
    before inserting breadcrumbs.
    """
    rebuilt = {
        'projects': 0,
        'sessions': 0,
        'findings': 0,
        'unknowns': 0,
        'dead_ends': 0,
        'mistakes': 0,
        'goals': 0
    }

    try:
        import json
        import time
        import uuid
        from empirica.data.session_database import SessionDatabase
        from empirica.core.canonical.empirica_git.finding_store import GitFindingStore
        from empirica.core.canonical.empirica_git.unknown_store import GitUnknownStore
        from empirica.core.canonical.empirica_git.dead_end_store import GitDeadEndStore
        from empirica.core.canonical.empirica_git.mistake_store import GitMistakeStore
        from empirica.core.canonical.empirica_git.goal_store import GitGoalStore

        db = SessionDatabase()

        # Phase 0: Collect all referenced project_ids and session_ids
        # then create stub records to satisfy FK constraints
        finding_store = GitFindingStore()
        unknown_store = GitUnknownStore()
        dead_end_store = GitDeadEndStore()
        mistake_store = GitMistakeStore()

        findings = finding_store.discover_findings()
        unknowns = unknown_store.discover_unknowns(include_resolved=True)
        dead_ends = dead_end_store.discover_dead_ends()
        mistakes = mistake_store.discover_mistakes()

        # Collect unique project_ids, session_ids, goal_ids from all breadcrumbs
        project_ids = set()
        session_ids = set()
        goal_ids_needed = set()
        for items in [findings, unknowns, dead_ends, mistakes]:
            for item in items:
                pid = item.get('project_id')
                sid = item.get('session_id')
                gid = item.get('goal_id')
                if pid:
                    project_ids.add(pid)
                if sid:
                    session_ids.add(sid)
                if gid:
                    goal_ids_needed.add(gid)

        # Ensure projects exist (stub records)
        now = time.time()
        for pid in project_ids:
            try:
                db.adapter.execute(
                    "INSERT INTO projects (id, name, description, created_timestamp, project_data) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (pid, f"project-{pid[:8]}", "Rebuilt from git notes", now, json.dumps({"rebuilt": True}))
                )
                db.adapter.commit()
                rebuilt['projects'] += 1
            except Exception:
                # Already exists or other constraint - OK for rebuild
                db.adapter.conn.rollback() if hasattr(db.adapter, 'conn') else None

        # Ensure sessions exist (stub records)
        for sid in session_ids:
            try:
                pid = None
                # Find which project this session belongs to
                for items in [findings, unknowns, dead_ends, mistakes]:
                    for item in items:
                        if item.get('session_id') == sid and item.get('project_id'):
                            pid = item.get('project_id')
                            break
                    if pid:
                        break

                from datetime import datetime
                now_ts = datetime.utcnow().isoformat()
                db.adapter.execute(
                    "INSERT INTO sessions (session_id, ai_id, start_time, "
                    "components_loaded, project_id) VALUES (?, ?, ?, ?, ?)",
                    (sid, "rebuilt", now_ts, 0, pid)
                )
                db.adapter.commit()
                rebuilt['sessions'] += 1
            except Exception:
                try:
                    db.adapter.conn.rollback()
                except Exception:
                    pass

        # Ensure goals exist (from git notes)
        goal_store = GitGoalStore()
        goals = goal_store.discover_goals()
        for g in goals:
            try:
                gid = g.get('goal_id')
                gsid = g.get('session_id', '')
                gdata = g.get('goal_data', {})
                db.adapter.execute(
                    "INSERT INTO goals (id, session_id, objective, scope, estimated_complexity, "
                    "created_timestamp, goal_data, status, project_id) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        gid, gsid,
                        gdata.get('objective', 'Rebuilt from notes'),
                        json.dumps(gdata.get('scope', {})),
                        gdata.get('estimated_complexity'),
                        now,
                        json.dumps(gdata),
                        gdata.get('status', 'in_progress'),
                        gdata.get('project_id')
                    )
                )
                db.adapter.commit()
                rebuilt['goals'] += 1
            except Exception:
                try:
                    db.adapter.conn.rollback()
                except Exception:
                    pass

        # Ensure any goal_ids referenced by breadcrumbs also exist as stubs
        inserted_goal_ids = {g.get('goal_id') for g in goals}
        orphan_goal_ids = goal_ids_needed - inserted_goal_ids
        for gid in orphan_goal_ids:
            try:
                # Pick a session_id from the breadcrumbs that reference this goal
                gsid = ''
                for items in [findings, unknowns, dead_ends, mistakes]:
                    for item in items:
                        if item.get('goal_id') == gid and item.get('session_id'):
                            gsid = item.get('session_id')
                            break
                    if gsid:
                        break
                db.adapter.execute(
                    "INSERT INTO goals (id, session_id, objective, scope, "
                    "created_timestamp, goal_data) VALUES (?, ?, ?, ?, ?, ?)",
                    (gid, gsid, "Rebuilt stub (orphaned ref)", "{}", now,
                     json.dumps({"rebuilt": True, "orphan": True}))
                )
                db.adapter.commit()
                rebuilt['goals'] += 1
            except Exception:
                try:
                    db.adapter.conn.rollback()
                except Exception:
                    pass

        logger.info(
            f"Rebuild Phase 0: {rebuilt['projects']} projects, "
            f"{rebuilt['sessions']} sessions, {rebuilt['goals']} goals"
        )

        # Phase 1: Insert breadcrumbs (already discovered in Phase 0)
        # Note: psycopg2 requires rollback after failed queries before next query
        # Goal IDs are set only if the goal was successfully inserted in Phase 0
        inserted_all_goal_ids = inserted_goal_ids | {gid for gid in orphan_goal_ids}

        for f in findings:
            try:
                gid = f.get('goal_id')
                db.log_finding(
                    project_id=f.get('project_id'),
                    session_id=f.get('session_id'),
                    finding=f.get('finding'),
                    goal_id=gid if gid in inserted_all_goal_ids else None,
                    subtask_id=None,  # Subtasks not rebuilt
                    subject=f.get('subject'),
                    impact=f.get('impact')
                )
                rebuilt['findings'] += 1
            except Exception as e:
                logger.debug(f"Finding rebuild skip: {e}")
                try:
                    db.adapter.conn.rollback()
                except Exception:
                    pass

        for u in unknowns:
            try:
                gid = u.get('goal_id')
                db.log_unknown(
                    project_id=u.get('project_id'),
                    session_id=u.get('session_id'),
                    unknown=u.get('unknown'),
                    goal_id=gid if gid in inserted_all_goal_ids else None,
                    subtask_id=None
                )
                rebuilt['unknowns'] += 1
            except Exception as e:
                logger.debug(f"Unknown rebuild skip: {e}")
                try:
                    db.adapter.conn.rollback()
                except Exception:
                    pass

        for d in dead_ends:
            try:
                gid = d.get('goal_id')
                db.log_dead_end(
                    project_id=d.get('project_id'),
                    session_id=d.get('session_id'),
                    approach=d.get('approach'),
                    why_failed=d.get('why_failed'),
                    goal_id=gid if gid in inserted_all_goal_ids else None,
                    subtask_id=None
                )
                rebuilt['dead_ends'] += 1
            except Exception as e:
                logger.debug(f"Dead end rebuild skip: {e}")
                try:
                    db.adapter.conn.rollback()
                except Exception:
                    pass

        for m in mistakes:
            try:
                db.log_mistake(
                    session_id=m.get('session_id'),
                    mistake=m.get('mistake'),
                    why_wrong=m.get('why_wrong'),
                    prevention=m.get('prevention'),
                    cost_estimate=m.get('cost_estimate'),
                    root_cause_vector=m.get('root_cause_vector'),
                    goal_id=m.get('goal_id') if m.get('goal_id') in inserted_all_goal_ids else None,
                    project_id=m.get('project_id')
                )
                rebuilt['mistakes'] += 1
            except Exception as e:
                logger.debug(f"Mistake rebuild skip: {e}")
                try:
                    db.adapter.conn.rollback()
                except Exception:
                    pass

        db.close()

    except Exception as e:
        logger.warning(f"Rebuild failed: {e}")
        rebuilt['error'] = str(e)

    return rebuilt


def handle_rebuild_command(args):
    """Handle rebuild command - reconstruct SQLite from git notes"""
    try:
        output_format = getattr(args, 'output', 'json')
        from_notes = getattr(args, 'from_notes', True)
        qdrant = getattr(args, 'qdrant', False)

        if not from_notes:
            result = {
                "ok": False,
                "error": "Only --from-notes rebuild is currently supported"
            }
            print(json.dumps(result, indent=2))
            return 1

        # Run rebuild
        rebuild_result = _rebuild_from_notes()

        total_rebuilt = sum(v for k, v in rebuild_result.items() if k != 'error' and isinstance(v, int))

        result = {
            "ok": 'error' not in rebuild_result,
            "rebuilt": rebuild_result,
            "total": total_rebuilt,
            "message": f"Rebuilt {total_rebuilt} records from git notes"
        }

        # Optionally rebuild Qdrant
        if qdrant:
            try:
                from empirica.core.qdrant.vector_store import rebuild_qdrant_from_db
                qdrant_result = rebuild_qdrant_from_db()
                result['qdrant'] = qdrant_result
            except Exception as e:
                result['qdrant_error'] = str(e)

        if output_format == 'json':
            print(json.dumps(result, indent=2))
        else:
            if result['ok']:
                print(f"✅ Rebuilt {total_rebuilt} records from git notes")
                for type_name, count in rebuild_result.items():
                    if type_name != 'error' and count > 0:
                        print(f"   {type_name}: {count}")
                if qdrant and 'qdrant' in result:
                    print(f"   🔍 Qdrant: rebuilt")
            else:
                print(f"❌ Rebuild failed: {rebuild_result.get('error', 'Unknown error')}")

        return 0 if result['ok'] else 1

    except Exception as e:
        handle_cli_error(e, "Rebuild", getattr(args, 'verbose', False))
        return 1
