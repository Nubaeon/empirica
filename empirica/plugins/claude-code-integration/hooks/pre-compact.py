#!/usr/bin/env python3
"""
Empirica PreCompact Hook - Unified context capture before memory compacting

This hook runs automatically before Claude Code compacts the conversation.
It captures:
1. CANONICAL vectors via assess-state (fresh self-assessment)
2. Context anchor via project-bootstrap (findings, unknowns, goals)
3. Last human task from transcript (for continuity)
4. Git context (branch, modified files, recent commits)

Writes a UNIFIED breadcrumbs git note combining task context + epistemic state.
(Previously split across breadcrumbs bash scripts and empirica Python hooks.)
"""

import json
import sys
import subprocess
import os
from pathlib import Path
from datetime import datetime
# Import shared utilities from plugin lib
sys.path.insert(0, str(Path(__file__).parent.parent / 'lib'))
from project_resolver import get_instance_id, find_project_root  # noqa: E402


# Patterns that indicate a message is system-injected, not human input
_SKIP_PATTERNS = [
    '<command-name>',        # Skill tool injections
    '<system-reminder>',     # System reminders
    'Base directory for this skill:',  # Skill headers
    '[Request interrupted by user]',
    '[Request interrupted by user for tool use]',
]


def _extract_last_task(transcript_path: str, max_chars: int = 500) -> str:
    """Extract the last human task message from the JSONL transcript.

    Filters out:
    - Tool results (content is array, not string)
    - Skill injections (<command-name> tags)
    - System reminders
    - Very long messages (>2000 chars = likely injected content)
    """
    if not transcript_path or not Path(transcript_path).exists():
        return ""

    try:
        lines = Path(transcript_path).read_text().strip().split('\n')
        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            if entry.get('type') != 'user':
                continue

            message = entry.get('message', {})
            content = message.get('content', '')

            # Content must be a string (array = tool result)
            if not isinstance(content, str):
                continue

            content = content.strip()
            if not content:
                continue

            # Skip known non-human patterns
            skip = False
            for pattern in _SKIP_PATTERNS:
                if pattern in content[:300]:
                    skip = True
                    break
            if skip:
                continue

            # Skip very long messages (injected content, not human input)
            if len(content) > 2000:
                continue

            return content[:max_chars]
    except Exception:
        pass

    return ""


def _gather_git_context(num_commits: int = 5) -> dict:
    """Gather git context: branch, modified files, recent commits."""
    context = {'branch': '', 'modified_files': '', 'recent_commits': ''}

    try:
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True, text=True, timeout=5, cwd=os.getcwd()
        )
        context['branch'] = result.stdout.strip() or 'detached'
    except Exception:
        pass

    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True, text=True, timeout=5, cwd=os.getcwd()
        )
        files = result.stdout.strip()
        if files:
            lines = files.split('\n')[:20]
            context['modified_files'] = '\n'.join(f'  {l}' for l in lines)
    except Exception:
        pass

    try:
        result = subprocess.run(
            ['git', 'log', '--oneline', f'-{num_commits}'],
            capture_output=True, text=True, timeout=5, cwd=os.getcwd()
        )
        commits = result.stdout.strip()
        if commits:
            context['recent_commits'] = '\n'.join(f'  {l}' for l in commits.split('\n'))
    except Exception:
        pass

    return context


def _write_unified_breadcrumbs_note(
    session_id: str,
    timestamp: str,
    vectors: dict,
    snapshot_filename: str,
    breadcrumbs_summary: dict,
    last_task: str,
    git_context: dict
) -> bool:
    """Write unified breadcrumbs git note combining task context + epistemic state.

    Single note on 'breadcrumbs' ref replaces the old dual-system approach
    (separate bash breadcrumbs + empirica-precompact notes).
    """
    know = vectors.get('know', 'N/A')
    uncertainty = vectors.get('uncertainty', 'N/A')
    completion = vectors.get('completion', 'N/A')
    context_v = vectors.get('context', 'N/A')

    branch = git_context.get('branch', 'unknown')
    modified = git_context.get('modified_files', '') or '[Working tree clean]'
    commits = git_context.get('recent_commits', '') or '[No recent commits]'

    note = f"""🍞 BREADCRUMBS - {timestamp}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BRANCH: {branch}

LAST_TASK:
{last_task or '[Could not extract from transcript]'}

MODIFIED_FILES:
{modified}

RECENT_COMMITS:
{commits}

🧠 EPISTEMIC STATE
Session: {session_id}
Vectors: know={know}, uncertainty={uncertainty}, completion={completion}, context={context_v}
Snapshot: {snapshot_filename}

Artifacts: {breadcrumbs_summary.get('findings_count', 0)} findings, {breadcrumbs_summary.get('unknowns_count', 0)} unknowns, {breadcrumbs_summary.get('goals_count', 0)} goals, {breadcrumbs_summary.get('dead_ends_count', 0)} dead-ends

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RETRIEVAL:
  empirica project-bootstrap --session-id {session_id[:8]}...
  empirica project-search --task "<what you need>"
  cat .empirica/ref-docs/{snapshot_filename}
"""

    try:
        subprocess.run(
            ['git', 'notes', '--ref=breadcrumbs', 'add', '-f', '-m', note, 'HEAD'],
            capture_output=True, text=True, timeout=5, cwd=os.getcwd()
        )
        return True
    except Exception:
        return False


def main():
    # Read hook input from stdin (provided by Claude Code)
    hook_input = json.loads(sys.stdin.read())

    trigger = hook_input.get('trigger', 'auto')  # 'auto' or 'manual'

    # Get Claude session_id from hook input (available for ALL users)
    claude_session_id = hook_input.get('session_id')

    # CRITICAL: Find and change to project root BEFORE importing empirica
    # Uses priority chain: claude_session_id → instance_projects → env var
    # NO CWD FALLBACK - fails explicitly to prevent wrong context pollution
    project_root = find_project_root(claude_session_id=claude_session_id)
    if project_root is None:
        print(json.dumps({
            "error": "Could not resolve project root. No active_work file, instance_projects, or EMPIRICA_WORKSPACE_ROOT found.",
            "claude_session_id": claude_session_id,
            "tmux_pane": os.environ.get('TMUX_PANE')
        }))
        sys.exit(1)
    os.chdir(project_root)

    # =========================================================================
    # STEP 0: Extract task context + git state (absorbed from breadcrumbs bash)
    # =========================================================================
    transcript_path = hook_input.get('transcript_path', '')
    last_task = _extract_last_task(transcript_path)
    git_context = _gather_git_context()

    # Write compact handoff file for post-compact to read (belt and suspenders)
    # This ensures post-compact resolves to the same project even if
    # active_work/instance_projects get stale between pre and post compact.
    try:
        instance_id = get_instance_id()
        handoff_file = Path.home() / '.empirica' / f'compact_handoff_{instance_id}.json'
        handoff_data = {
            'project_path': str(project_root),
            'claude_session_id': claude_session_id,
            'instance_id': instance_id,
            'timestamp': datetime.now().isoformat()
        }
        with open(handoff_file, 'w') as f:
            json.dump(handoff_data, f, indent=2)
    except Exception:
        pass  # Handoff write failure is non-fatal

    # Auto-detect latest Empirica session (no env var needed)
    empirica_session = None
    try:
        # Import after cwd change to use correct database
        sys.path.insert(0, str(Path.home() / 'empirical-ai' / 'empirica'))
        from empirica.utils.session_resolver import get_latest_session_id

        # Get latest active claude-code* session
        # Try claude-code-* variants first, fallback to any active session
        for ai_pattern in ['claude-code', None]:
            try:
                empirica_session = get_latest_session_id(ai_id=ai_pattern, active_only=True)
                break
            except ValueError:
                continue
    except Exception:
        pass  # Session detection failure is non-fatal

    if not empirica_session:
        # Exit silently if no Empirica session active
        print(json.dumps({
            "ok": True,
            "skipped": True,
            "reason": "No active Empirica session detected"
        }))
        sys.exit(0)

    # Stash uncommitted work before snapshot (preserves WIP without polluting branch history)
    # Git notes handle the epistemic breadcrumb trail; stash handles uncommitted code.
    stash_created = False
    try:
        # Check if there are changes to stash
        status_result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            timeout=5
        )

        if status_result.stdout.strip():
            stash_msg = f"empirica: pre-compact {empirica_session[:8]} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            result = subprocess.run(
                ['git', 'stash', 'push', '-m', stash_msg, '--include-untracked'],
                cwd=os.getcwd(),
                capture_output=True,
                text=True,
                timeout=10
            )
            stash_created = result.returncode == 0
    except Exception:
        # Stash failure is not fatal
        pass

    # =========================================================================
    # STEP 0.5: Mark active goals as stale (context will be lost on compact)
    # =========================================================================
    # Goals created in this session should be marked stale since the AI's
    # full context about them will be compressed in the summary.
    stale_goals_count = 0
    try:
        stale_result = subprocess.run(
            ['empirica', 'goals-mark-stale', '--session-id', empirica_session, '--reason', 'memory_compact', '--output', 'json'],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=os.getcwd()
        )
        if stale_result.returncode == 0:
            stale_data = json.loads(stale_result.stdout)
            stale_goals_count = stale_data.get('goals_marked_stale', 0)
    except Exception:
        # Non-fatal - continue with compaction
        pass

    # =========================================================================
    # STEP 0.7: Context Budget triage (evict low-priority before compaction)
    # =========================================================================
    budget_report = None
    try:
        sys.path.insert(0, str(Path.home() / 'empirical-ai' / 'empirica'))
        from empirica.core.context_budget import (
            ContextBudgetManager, load_thresholds_from_config,
        )

        thresholds = load_thresholds_from_config()
        manager = ContextBudgetManager(
            session_id=empirica_session,
            thresholds=thresholds,
            auto_subscribe=False,
        )

        # Decay all items and evict stale ones before compaction
        manager._decay_all_items()

        # Get budget report for snapshot metadata
        budget_report = manager.get_inventory_summary()

        # Persist final state
        manager.persist_state()
    except Exception:
        pass  # Budget triage failure is non-fatal

    # =========================================================================
    # STEP 0.8: Capture active transaction state (for continuity across compact)
    # =========================================================================
    # Transaction files are instance-aware: active_transaction_{instance_id}.json
    # Instance ID comes from TMUX_PANE (e.g., "%4" → "tmux_4")
    active_transaction = None
    try:
        # Get instance_id from TMUX_PANE
        tmux_pane = os.environ.get('TMUX_PANE', '')
        if tmux_pane:
            instance_id = f"tmux_{tmux_pane.lstrip('%')}"
        else:
            # Fallback: try to find any transaction file in the project
            instance_id = None

        if instance_id:
            tx_path = project_root / '.empirica' / f'active_transaction_{instance_id}.json'
            if tx_path.exists():
                with open(tx_path, 'r') as f:
                    active_transaction = json.load(f)
        else:
            # Fallback: scan for any active transaction file
            tx_files = list((project_root / '.empirica').glob('active_transaction_*.json'))
            if tx_files:
                # Use most recently modified
                tx_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                with open(tx_files[0], 'r') as f:
                    active_transaction = json.load(f)
    except Exception:
        pass  # Transaction capture is non-fatal

    # =========================================================================
    # STEP 1: Capture FRESH epistemic vectors (canonical via assess-state)
    # =========================================================================
    # This is the AI's self-assessed state BEFORE compaction.
    # assess-state queries the latest reflexes/calibration data for the session.
    fresh_vectors = {}
    assess_error = None

    try:
        assess_result = subprocess.run(
            ['empirica', 'assess-state', '--session-id', empirica_session, '--output', 'json'],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=os.getcwd()
        )

        if assess_result.returncode == 0:
            assess_data = json.loads(assess_result.stdout)
            fresh_vectors = assess_data.get('state', {}).get('vectors', {})
        else:
            assess_error = assess_result.stderr
    except subprocess.TimeoutExpired:
        assess_error = "assess-state timed out (>10s)"
    except Exception as e:
        assess_error = str(e)

    # =========================================================================
    # STEP 2: Run project-bootstrap for context anchor (findings, unknowns, goals)
    # =========================================================================
    # This provides the breadcrumbs context - what was learned, what's unclear, active goals.
    ai_id = os.getenv('EMPIRICA_AI_ID', 'claude-code')

    try:
        result = subprocess.run(
            [
                'empirica', 'project-bootstrap',
                '--ai-id', ai_id,
                '--include-live-state',
                '--trigger', 'pre_compact',
                '--output', 'json'
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd()
        )

        if result.returncode == 0:
            # Success - save snapshot
            bootstrap = json.loads(result.stdout) if result.stdout else {}

            # Extract breadcrumbs (CLI wraps in {"ok", "project_id", "breadcrumbs"})
            breadcrumbs = bootstrap.get('breadcrumbs', bootstrap)

            # Save snapshot to .empirica/ref-docs
            ref_docs_dir = Path.cwd() / ".empirica" / "ref-docs"
            ref_docs_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            snapshot_path = ref_docs_dir / f"pre_summary_{timestamp}.json"

            # Build snapshot with CANONICAL vectors from assess-state
            # Fallback to live_state vectors if assess-state failed
            live_state = breadcrumbs.get('live_state', {})
            fallback_vectors = live_state.get('vectors', {}) if live_state else {}

            snapshot = {
                "type": "pre_summary_snapshot",
                "timestamp": timestamp,
                "session_id": breadcrumbs.get('session_id'),
                "trigger": trigger,
                "vectors_canonical": fresh_vectors,  # From assess-state (canonical)
                "vectors_source": "assess-state" if fresh_vectors else "live_state_fallback",
                "checkpoint": fresh_vectors or fallback_vectors,  # Best available vectors
                "live_state": live_state,
                "assess_error": assess_error,  # Track if assess-state failed
                "breadcrumbs_summary": {
                    "findings_count": len(breadcrumbs.get('findings', [])),
                    "unknowns_count": len(breadcrumbs.get('unknowns', [])),
                    "goals_count": len(breadcrumbs.get('goals', [])),
                    "dead_ends_count": len(breadcrumbs.get('dead_ends', []))
                },
                "context_budget": budget_report,  # Token budget state at compaction
                "active_transaction": active_transaction,  # Transaction state for continuity
                "last_task": last_task,  # Extracted human task from transcript
                "git_context": git_context,  # Branch, modified files, recent commits
            }

            with open(snapshot_path, 'w') as f:
                json.dump(snapshot, f, indent=2)

            # Write unified breadcrumbs git note (task context + epistemic state)
            session_id_for_notes = breadcrumbs.get('session_id') or empirica_session
            git_notes_written = _write_unified_breadcrumbs_note(
                session_id=session_id_for_notes,
                timestamp=timestamp,
                vectors=fresh_vectors or fallback_vectors,
                snapshot_filename=snapshot_path.name,
                breadcrumbs_summary=snapshot['breadcrumbs_summary'],
                last_task=last_task,
                git_context=git_context
            )

            # Restore stashed work (working directory back to pre-snapshot state)
            stash_restored = False
            if stash_created:
                try:
                    pop_result = subprocess.run(
                        ['git', 'stash', 'pop'],
                        cwd=os.getcwd(),
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    stash_restored = pop_result.returncode == 0
                except Exception:
                    pass  # Stash pop failure is non-fatal; user can manually pop

            # Determine which vectors to display
            display_vectors = fresh_vectors or fallback_vectors
            vector_source = "canonical" if fresh_vectors else "fallback"

            print(json.dumps({
                "ok": True,
                "trigger": trigger,
                "empirica_session_id": breadcrumbs.get('session_id'),
                "snapshot_saved": True,
                "snapshot_path": str(snapshot_path),
                "git_notes_written": git_notes_written,
                "stash_created": stash_created,
                "stash_restored": stash_restored,
                "vectors_source": vector_source,
                "vectors_captured": len(display_vectors),
                "goals_marked_stale": stale_goals_count,
                "message": f"Pre-compact snapshot saved ({trigger} compact, {vector_source} vectors, git_notes={'yes' if git_notes_written else 'no'})"
            }), file=sys.stdout)

            # Also print user-visible message to stderr
            session_id_str = breadcrumbs.get('session_id', 'Unknown')
            session_display = session_id_str[:8] if session_id_str else 'Unknown'

            stale_msg = f", {stale_goals_count} goals marked stale" if stale_goals_count > 0 else ""
            notes_msg = "✓" if git_notes_written else "✗"
            stash_msg = " (stash: saved+restored)" if stash_created else ""
            print(f"""
📸 Empirica: Pre-compact snapshot saved
   Session: {session_display}...
   Trigger: {trigger}
   Vectors: {vector_source} ({len(display_vectors)} captured){stale_msg}
   know={display_vectors.get('know', 'N/A')}, unc={display_vectors.get('uncertainty', 'N/A')}
   Snapshot: {snapshot_path.name}
   Git notes: {notes_msg}{stash_msg}
""", file=sys.stderr)

            sys.exit(0)
        else:
            # Error running project-bootstrap
            print(json.dumps({
                "ok": False,
                "error": result.stderr,
                "empirica_session_id": empirica_session
            }))
            sys.exit(2)  # Blocking error (show to user)

    except subprocess.TimeoutExpired:
        print(json.dumps({
            "ok": False,
            "error": "project-bootstrap timed out (>30s)"
        }))
        sys.exit(2)
    except Exception as e:
        print(json.dumps({
            "ok": False,
            "error": str(e)
        }))
        sys.exit(2)

if __name__ == '__main__':
    main()
