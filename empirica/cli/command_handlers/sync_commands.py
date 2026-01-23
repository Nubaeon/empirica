"""
Sync Commands - Git notes synchronization for multi-device/multi-AI coordination

Commands:
- sync push: Push all epistemic notes to remote
- sync pull: Pull all epistemic notes from remote
- sync status: Show sync status (local vs remote)
- rebuild: Reconstruct SQLite from git notes
"""

import json
import logging
import subprocess
from typing import Optional, Dict, Any, List
from ..cli_utils import handle_cli_error

logger = logging.getLogger(__name__)


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


def handle_sync_push_command(args):
    """Handle sync push command - push all epistemic notes to remote"""
    try:
        remote = getattr(args, 'remote', 'origin') or 'origin'
        output_format = getattr(args, 'output', 'json')
        dry_run = getattr(args, 'dry_run', False)
        verbose = getattr(args, 'verbose', False)

        # Check remote exists
        if not _check_remote(remote):
            result = {
                "ok": False,
                "error": f"Remote '{remote}' not found",
                "hint": "Run 'git remote add origin <url>' to add a remote"
            }
            print(json.dumps(result, indent=2))
            return 1

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
        remote = getattr(args, 'remote', 'origin') or 'origin'
        output_format = getattr(args, 'output', 'json')
        rebuild = getattr(args, 'rebuild', False)
        verbose = getattr(args, 'verbose', False)

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
    Rebuild SQLite from git notes.

    This reconstructs the derived SQLite tables from canonical git notes.
    """
    rebuilt = {
        'findings': 0,
        'unknowns': 0,
        'dead_ends': 0,
        'mistakes': 0,
        'goals': 0
    }

    try:
        from empirica.data.session_database import SessionDatabase
        from empirica.core.canonical.empirica_git.finding_store import GitFindingStore
        from empirica.core.canonical.empirica_git.unknown_store import GitUnknownStore
        from empirica.core.canonical.empirica_git.dead_end_store import GitDeadEndStore
        from empirica.core.canonical.empirica_git.mistake_store import GitMistakeStore
        from empirica.core.canonical.empirica_git.goal_store import GitGoalStore

        db = SessionDatabase()

        # Rebuild findings
        finding_store = GitFindingStore()
        findings = finding_store.discover_findings()
        for f in findings:
            try:
                db.log_finding(
                    project_id=f.get('project_id'),
                    session_id=f.get('session_id'),
                    finding=f.get('finding'),
                    goal_id=f.get('goal_id'),
                    subtask_id=f.get('subtask_id'),
                    subject=f.get('subject'),
                    impact=f.get('impact')
                )
                rebuilt['findings'] += 1
            except:
                pass

        # Rebuild unknowns
        unknown_store = GitUnknownStore()
        unknowns = unknown_store.discover_unknowns(include_resolved=True)
        for u in unknowns:
            try:
                db.log_unknown(
                    project_id=u.get('project_id'),
                    session_id=u.get('session_id'),
                    unknown=u.get('unknown'),
                    goal_id=u.get('goal_id'),
                    subtask_id=u.get('subtask_id')
                )
                rebuilt['unknowns'] += 1
            except:
                pass

        # Rebuild dead ends
        dead_end_store = GitDeadEndStore()
        dead_ends = dead_end_store.discover_dead_ends()
        for d in dead_ends:
            try:
                db.log_dead_end(
                    project_id=d.get('project_id'),
                    session_id=d.get('session_id'),
                    approach=d.get('approach'),
                    why_failed=d.get('why_failed'),
                    goal_id=d.get('goal_id'),
                    subtask_id=d.get('subtask_id')
                )
                rebuilt['dead_ends'] += 1
            except:
                pass

        # Rebuild mistakes
        mistake_store = GitMistakeStore()
        mistakes = mistake_store.discover_mistakes()
        for m in mistakes:
            try:
                db.log_mistake(
                    session_id=m.get('session_id'),
                    mistake=m.get('mistake'),
                    why_wrong=m.get('why_wrong'),
                    prevention=m.get('prevention'),
                    cost_estimate=m.get('cost_estimate'),
                    root_cause_vector=m.get('root_cause_vector'),
                    goal_id=m.get('goal_id'),
                    project_id=m.get('project_id')
                )
                rebuilt['mistakes'] += 1
            except:
                pass

        # Goals already have their own store and are handled by goal commands
        # Just count them for reporting
        goal_store = GitGoalStore()
        goals = goal_store.discover_goals()
        rebuilt['goals'] = len(goals)

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
