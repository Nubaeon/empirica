#!/usr/bin/env python3
"""
Empirica PostCompact Hook - Phase-Aware Recovery

After memory compaction, the AI has only a summary - not real knowledge.
This hook detects the CASCADE phase state and routes appropriately:

1. If old session is COMPLETE (has POSTFLIGHT) → New session + PREFLIGHT
2. If old session is INCOMPLETE (mid-work) → CHECK gate on old session

Key insight: Compact can happen at ANY point in the CASCADE cycle.
The recovery action depends on WHERE in the cycle compact occurred.
"""

import json
import sys
import subprocess
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# Import epistemic summarizer for confidence-weighted context
try:
    from epistemic_summarizer import format_epistemic_focus
    EPISTEMIC_SUMMARIZER_AVAILABLE = True
except ImportError:
    EPISTEMIC_SUMMARIZER_AVAILABLE = False


def _get_instance_id() -> Optional[str]:
    """Derive instance ID from environment. TMUX_PANE → TTY → 'default'."""
    tmux_pane = os.environ.get('TMUX_PANE')
    if tmux_pane:
        return f"tmux_{tmux_pane.lstrip('%')}"
    try:
        tty_path = os.ttyname(sys.stdin.fileno())
        safe = tty_path.replace('/', '_').lstrip('_').replace('dev_', '')
        return f"term_{safe}"
    except Exception:
        pass
    return "default"


def find_project_root(claude_session_id: str = None) -> Optional[Path]:
    """
    Find the Empirica project root using priority chain.

    Priority order:
    -2. Compact handoff file (written by pre-compact, highest priority for post-compact)
    -1. Open transaction file (AUTHORITATIVE - survives compaction, written at PREFLIGHT)
     0. Active work file by Claude session_id (most reliable - works for ALL users)
     1. Instance projects file by instance_id (works in hook context without TTY)
     2. EMPIRICA_WORKSPACE_ROOT environment variable
    NO CWD FALLBACK - fails explicitly to prevent wrong context pollution
    """
    def has_valid_db(path: Path) -> bool:
        """Check if path has valid Empirica database"""
        db_path = path / '.empirica' / 'sessions' / 'sessions.db'
        return db_path.exists() and db_path.stat().st_size > 0

    instance_id = _get_instance_id()

    # Priority -2: Compact handoff file (written by pre-compact in same compaction cycle)
    # This is the most reliable source because pre-compact runs while the conversation
    # is still live and has correct project context.
    if instance_id:
        try:
            handoff_file = Path.home() / '.empirica' / f'compact_handoff_{instance_id}.json'
            if handoff_file.exists():
                with open(handoff_file, 'r') as f:
                    handoff_data = json.load(f)
                project_path = handoff_data.get('project_path')
                if project_path and has_valid_db(Path(project_path)):
                    return Path(project_path)
        except Exception:
            pass

    # Collect ALL candidate paths (don't return early for Priorities 0-1)
    candidates = []

    # Priority 0 candidate: active_work file by Claude session_id
    if claude_session_id:
        try:
            active_work_file = Path.home() / '.empirica' / f'active_work_{claude_session_id}.json'
            if active_work_file.exists():
                with open(active_work_file, 'r') as f:
                    work_data = json.load(f)
                project_path = work_data.get('project_path')
                if project_path and has_valid_db(Path(project_path)):
                    candidates.append(project_path)
        except Exception:
            pass

    # Priority 1 candidate: instance_projects by instance_id
    if instance_id:
        try:
            instance_file = Path.home() / '.empirica' / 'instance_projects' / f'{instance_id}.json'
            if instance_file.exists():
                with open(instance_file, 'r') as f:
                    instance_data = json.load(f)
                project_path = instance_data.get('project_path')
                if project_path and has_valid_db(Path(project_path)):
                    candidates.append(project_path)
        except Exception:
            pass

    # Priority -1: Check candidates for open transaction (AUTHORITATIVE)
    # The transaction file is written at PREFLIGHT with explicit project_path.
    # If a candidate has an open transaction, that's definitively the right project.
    if instance_id and candidates:
        for path in candidates:
            try:
                tx_file = Path(path) / '.empirica' / f'active_transaction_{instance_id}.json'
                if tx_file.exists():
                    with open(tx_file, 'r') as f:
                        tx_data = json.load(f)
                    if tx_data.get('status') == 'open':
                        tx_project = tx_data.get('project_path')
                        if tx_project and has_valid_db(Path(tx_project)):
                            return Path(tx_project)
                        return Path(path)
            except Exception:
                continue

    # Priority -0.5: Workspace scan — if candidates didn't have open transactions,
    # scan ALL registered projects for open transactions with this instance_id.
    # Handles case where active_work/instance_projects are stale/wrong.
    # Picks the most recently modified transaction file if multiple are open.
    if instance_id:
        try:
            import sqlite3
            ws_db = Path.home() / '.empirica' / 'workspace' / 'workspace.db'
            if ws_db.exists():
                conn = sqlite3.connect(str(ws_db))
                cursor = conn.cursor()
                cursor.execute("SELECT trajectory_path FROM global_projects WHERE trajectory_path IS NOT NULL")
                all_projects = [row[0] for row in cursor.fetchall()]
                conn.close()

                # Check each project for open transaction, track by mtime
                best_match = None
                best_mtime = 0
                candidate_set = set(candidates)  # Skip already-checked candidates
                for proj_path in all_projects:
                    if proj_path in candidate_set:
                        continue
                    tx_file = Path(proj_path) / '.empirica' / f'active_transaction_{instance_id}.json'
                    try:
                        if tx_file.exists():
                            with open(tx_file, 'r') as f:
                                tx_data = json.load(f)
                            if tx_data.get('status') == 'open':
                                mtime = tx_file.stat().st_mtime
                                if mtime > best_mtime:
                                    tx_project = tx_data.get('project_path', proj_path)
                                    if has_valid_db(Path(tx_project)):
                                        best_match = Path(tx_project)
                                        best_mtime = mtime
                    except Exception:
                        continue

                if best_match:
                    return best_match
        except Exception:
            pass

    # No open transaction found - return first valid candidate
    if candidates:
        return Path(candidates[0])

    # Priority 2: Check environment variable
    if workspace_root := os.getenv('EMPIRICA_WORKSPACE_ROOT'):
        workspace_path = Path(workspace_root).expanduser().resolve()
        if has_valid_db(workspace_path):
            return workspace_path

    # NO CWD FALLBACK - fail explicitly to prevent wrong context pollution
    return None


def _write_active_work_for_new_conversation(
    claude_session_id: str,
    project_path: str,
    empirica_session_id: str,
    instance_id: str = None
) -> bool:
    """
    Write active_work file for the NEW conversation after compaction.

    This is CRITICAL: without this file, all subsequent CLI commands in the
    new conversation (project-bootstrap, finding-log, goals-create, etc.)
    will fail to resolve the correct project and fall through to CWD-based
    resolution, which poisons context with the wrong project.

    The pre-compact hook writes compact_handoff for project resolution,
    but this function writes active_work for CLI command resolution.
    """
    if not claude_session_id:
        return False

    try:
        active_work_file = Path.home() / '.empirica' / f'active_work_{claude_session_id}.json'
        folder_name = Path(project_path).name if project_path else None

        work_data = {
            'project_path': project_path,
            'folder_name': folder_name,
            'claude_session_id': claude_session_id,
            'empirica_session_id': empirica_session_id,
            'source': 'post-compact',
            'timestamp': datetime.now().isoformat(),
            'timestamp_epoch': datetime.now().timestamp()
        }

        with open(active_work_file, 'w') as f:
            json.dump(work_data, f, indent=2)

        # Also update instance_projects for consistency
        if instance_id:
            instance_file = Path.home() / '.empirica' / 'instance_projects' / f'{instance_id}.json'
            instance_file.parent.mkdir(parents=True, exist_ok=True)
            instance_data = {
                'project_path': project_path,
                'claude_session_id': claude_session_id,
                'empirica_session_id': empirica_session_id,
                'timestamp': datetime.now().isoformat()
            }
            with open(instance_file, 'w') as f:
                json.dump(instance_data, f, indent=2)

        return True
    except Exception:
        return False


def main():
    hook_input = json.loads(sys.stdin.read())
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

    # Compute instance_id for active_work file writing
    instance_id = _get_instance_id()

    # Now safe to import empirica (after cwd is set correctly)
    sys.path.insert(0, str(Path.home() / 'empirical-ai' / 'empirica'))

    # Find active Empirica session (using active_work file first, then DB fallback)
    empirica_session = _get_empirica_session(claude_session_id=claude_session_id)
    if not empirica_session:
        print(json.dumps({"ok": True, "skipped": True, "reason": "No active Empirica session"}))
        sys.exit(0)

    ai_id = os.getenv('EMPIRICA_AI_ID', 'claude-code')

    # CRITICAL: Detect phase state to route recovery correctly
    phase_state = _get_session_phase_state(empirica_session)

    # Load pre-compact snapshot (what the AI thought it knew)
    pre_snapshot = _load_pre_snapshot()
    pre_vectors = {}
    pre_reasoning = None

    if pre_snapshot:
        pre_vectors = pre_snapshot.get('checkpoint', {}) or \
                      (pre_snapshot.get('live_state') or {}).get('vectors', {})
        pre_reasoning = (pre_snapshot.get('live_state') or {}).get('reasoning')

    # Extract active transaction from pre-compact snapshot (for continuity)
    active_transaction = None
    if pre_snapshot:
        active_transaction = pre_snapshot.get('active_transaction')

    # Load DYNAMIC context - only what's relevant for re-grounding
    dynamic_context = _load_dynamic_context(empirica_session, ai_id, pre_snapshot)

    # Inject transaction context into dynamic_context
    if active_transaction:
        dynamic_context['active_transaction'] = active_transaction

    # Route based on phase state and transaction state:
    # - OPEN TRANSACTION → Just continue (no new PREFLIGHT/CHECK needed)
    # - Session COMPLETE (has POSTFLIGHT) → Create new session + bootstrap + PREFLIGHT
    # - Session INCOMPLETE (mid-work, no open tx) → CHECK gate on old session
    session_bootstrap = None

    # TRANSACTION CONTINUITY: If there's an open transaction, just continue
    # The transaction file persists on disk - no action needed from AI
    if active_transaction and active_transaction.get('status') == 'open':
        recovery_prompt = _generate_transaction_continue_prompt(
            pre_vectors=pre_vectors,
            dynamic_context=dynamic_context,
            active_transaction=active_transaction
        )
        action_required = "CONTINUE_TRANSACTION"

        # CRITICAL: Write active_work file for NEW conversation even when continuing transaction.
        # The transaction file has the right session_id, but CLI commands need active_work
        # keyed by the NEW claude_session_id to resolve the correct project.
        _write_active_work_for_new_conversation(
            claude_session_id=claude_session_id,
            project_path=str(project_root),
            empirica_session_id=empirica_session,
            instance_id=instance_id
        )
    elif phase_state.get('is_complete'):
        # NEW: Actually create session and run bootstrap here
        # This enforces the correct sequence before AI does PREFLIGHT
        project_id = dynamic_context.get('session_context', {}).get('project_id')
        session_bootstrap = _create_session_and_bootstrap(ai_id, project_id)

        recovery_prompt = _generate_new_session_prompt(
            pre_vectors=pre_vectors,
            dynamic_context=dynamic_context,
            old_session_id=empirica_session,
            ai_id=ai_id,
            session_bootstrap=session_bootstrap
        )
        action_required = "NEW_SESSION_PREFLIGHT"

        # Update session_id if we created one
        if session_bootstrap.get('session_id'):
            empirica_session = session_bootstrap['session_id']

        # CRITICAL: Write active_work file for NEW conversation so all subsequent
        # CLI commands (project-bootstrap, finding-log, etc.) resolve correctly.
        # Without this, CLI falls through to CWD-based git remote lookup = wrong project.
        _write_active_work_for_new_conversation(
            claude_session_id=claude_session_id,
            project_path=str(project_root),
            empirica_session_id=empirica_session,
            instance_id=instance_id
        )
    else:
        recovery_prompt = _generate_check_prompt(
            pre_vectors=pre_vectors,
            pre_reasoning=pre_reasoning,
            dynamic_context=dynamic_context
        )
        action_required = "CHECK_GATE"

        # CRITICAL: Write active_work file for NEW conversation
        _write_active_work_for_new_conversation(
            claude_session_id=claude_session_id,
            project_path=str(project_root),
            empirica_session_id=empirica_session,
            instance_id=instance_id
        )

    # Calculate what drift WOULD be if vectors unchanged (to show the problem)
    potential_drift = _calculate_potential_drift(pre_vectors)

    # Build the injection payload using Claude Code's hook format
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": recovery_prompt
        },
        "empirica_session_id": empirica_session,
        "action_required": action_required,
        "phase_state": phase_state,
        "pre_compact_state": {
            "vectors": pre_vectors,
            "reasoning": pre_reasoning,
            "timestamp": pre_snapshot.get('timestamp') if pre_snapshot else None
        },
        "potential_drift_warning": potential_drift,
        "session_bootstrap": session_bootstrap  # NEW: Include bootstrap result
    }

    print(json.dumps(output), file=sys.stdout)

    # User-visible message to stderr
    _print_user_message(pre_vectors, dynamic_context, potential_drift, phase_state, ai_id, session_bootstrap)

    sys.exit(0)


def _get_empirica_session(claude_session_id: str = None):
    """
    Find the active Empirica session using priority chain.

    Priority:
    0. active_work file's empirica_session_id (set by project-switch, instance-aware)
    1. Database query for latest active session (fallback)
    """
    # Priority 0: Check active_work file (authoritative for this Claude instance)
    if claude_session_id:
        try:
            active_work_file = Path.home() / '.empirica' / f'active_work_{claude_session_id}.json'
            if active_work_file.exists():
                with open(active_work_file, 'r') as f:
                    work_data = json.load(f)
                empirica_session_id = work_data.get('empirica_session_id')
                if empirica_session_id:
                    return empirica_session_id
        except Exception:
            pass

    # Priority 1: Database query (fallback)
    try:
        from empirica.utils.session_resolver import get_latest_session_id
        for ai_pattern in ['claude-code', None]:
            try:
                return get_latest_session_id(ai_id=ai_pattern, active_only=True)
            except ValueError:
                continue
    except Exception:
        pass
    return None


def _get_session_phase_state(session_id: str) -> dict:
    """
    Detect the CASCADE phase state of a session.

    Returns:
        {
            "has_preflight": bool,
            "has_postflight": bool,
            "last_phase": str or None,
            "is_complete": bool  # True if session has POSTFLIGHT
        }
    """
    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Get all phases for this session
        cursor.execute("""
            SELECT phase, timestamp
            FROM reflexes
            WHERE session_id = ?
            ORDER BY timestamp DESC
        """, (session_id,))
        rows = cursor.fetchall()
        db.close()

        if not rows:
            return {
                "has_preflight": False,
                "has_postflight": False,
                "last_phase": None,
                "is_complete": False
            }

        phases = [r[0] for r in rows]
        last_phase = phases[0] if phases else None

        # Session is "complete" if the LAST phase was POSTFLIGHT
        # (not just if it ever had a POSTFLIGHT - could be in cycle 2+)
        is_complete = last_phase == "POSTFLIGHT"

        return {
            "has_preflight": "PREFLIGHT" in phases,
            "has_postflight": "POSTFLIGHT" in phases,
            "last_phase": last_phase,
            "is_complete": is_complete
        }
    except Exception as e:
        return {
            "has_preflight": False,
            "has_postflight": False,
            "last_phase": None,
            "is_complete": False,
            "error": str(e)
        }


def _load_pre_snapshot():
    """Load the most recent pre-compact snapshot"""
    try:
        ref_docs_dir = Path.cwd() / ".empirica" / "ref-docs"
        snapshots = sorted(ref_docs_dir.glob("pre_summary_*.json"), reverse=True)
        if snapshots:
            with open(snapshots[0], 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return None


def _load_dynamic_context(session_id: str, ai_id: str, pre_snapshot: dict) -> dict:
    """
    Load DYNAMIC context - only what's relevant for re-grounding.

    NOT everything that ever was - just:
    1. Active goals (what was being worked on)
    2. Recent findings from THIS session (last learnings)
    3. Unresolved unknowns (open questions)
    4. Critical dead ends (mistakes to avoid)
    """
    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Get the session's project_id
        cursor.execute("SELECT project_id FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        project_id = row[0] if row else None

        context = {
            "active_goals": [],
            "recent_findings": [],
            "open_unknowns": [],
            "critical_dead_ends": [],
            "session_context": {}
        }

        if not project_id:
            db.close()
            return context

        # 1. Active goals (incomplete, high priority)
        cursor.execute("""
            SELECT id, objective, status, scope, created_timestamp
            FROM goals
            WHERE project_id = ? AND status IN ('active', 'in_progress', 'blocked')
            ORDER BY created_timestamp DESC LIMIT 3
        """, (project_id,))
        for row in cursor.fetchall():
            context["active_goals"].append({
                "id": row[0],
                "objective": row[1],
                "status": row[2],
                "scope": row[3],
                "created_timestamp": row[4]
            })

        # 1b. Load subtasks for each active goal (for continuity across sessions)
        context["pending_subtasks"] = []
        for goal in context["active_goals"]:
            cursor.execute("""
                SELECT id, description, status, importance, created_timestamp
                FROM subtasks
                WHERE goal_id = ? AND status != 'completed'
                ORDER BY
                    CASE importance
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        ELSE 4
                    END,
                    created_timestamp DESC
                LIMIT 5
            """, (goal["id"],))
            subtasks = []
            for st_row in cursor.fetchall():
                subtask = {
                    "id": st_row[0],
                    "description": st_row[1],
                    "status": st_row[2],
                    "importance": st_row[3],
                    "created_timestamp": st_row[4],
                    "goal_id": goal["id"],
                    "goal_objective": goal["objective"][:50]  # Truncate for context
                }
                subtasks.append(subtask)
                # Also add to flat list for epistemic ranking
                context["pending_subtasks"].append(subtask)
            goal["subtasks"] = subtasks

        # 2. Recent findings from THIS session (last session's learnings)
        cursor.execute("""
            SELECT finding, impact, created_timestamp
            FROM project_findings
            WHERE project_id = ? AND impact >= 0.6
            ORDER BY created_timestamp DESC LIMIT 5
        """, (project_id,))
        for row in cursor.fetchall():
            context["recent_findings"].append({
                "finding": row[0],
                "impact": row[1],
                "when": str(row[2])[:19] if row[2] else None
            })

        # 3. Unresolved unknowns (open questions you need to address)
        cursor.execute("""
            SELECT unknown, impact, created_timestamp
            FROM project_unknowns
            WHERE project_id = ? AND is_resolved = 0
            ORDER BY impact DESC, created_timestamp DESC LIMIT 5
        """, (project_id,))
        for row in cursor.fetchall():
            context["open_unknowns"].append({
                "unknown": row[0],
                "impact": row[1]
            })

        # 4. Critical dead ends (mistakes to avoid)
        cursor.execute("""
            SELECT approach, why_failed
            FROM project_dead_ends
            WHERE project_id = ?
            ORDER BY created_timestamp DESC LIMIT 3
        """, (project_id,))
        for row in cursor.fetchall():
            context["critical_dead_ends"].append({
                "approach": row[0],
                "why_failed": row[1]
            })

        # 5. Session context (what was happening)
        context["session_context"] = {
            "session_id": session_id,
            "ai_id": ai_id,
            "project_id": project_id
        }

        db.close()
        return context

    except Exception as e:
        return {
            "error": str(e),
            "active_goals": [],
            "recent_findings": [],
            "open_unknowns": [],
            "critical_dead_ends": []
        }


def _create_session_and_bootstrap(ai_id: str, project_id: str = None) -> dict:
    """
    Create a new session AND run project-bootstrap in one step.

    This enforces the correct sequence: session-create → project-bootstrap
    before the AI does PREFLIGHT. Previously, AI could skip bootstrap.

    Returns:
        {
            "session_id": str,
            "bootstrap_output": dict or None,
            "memory_context": dict or None,
            "error": str or None
        }
    """
    result = {
        "session_id": None,
        "bootstrap_output": None,
        "memory_context": None,
        "error": None
    }

    try:
        # Step 1: Create new session
        create_cmd = subprocess.run(
            ['empirica', 'session-create', '--ai-id', ai_id, '--output', 'json'],
            capture_output=True, text=True, timeout=15
        )
        if create_cmd.returncode != 0:
            result["error"] = f"session-create failed: {create_cmd.stderr}"
            return result

        create_output = json.loads(create_cmd.stdout)
        new_session_id = create_output.get('session_id')
        if not new_session_id:
            result["error"] = "session-create returned no session_id"
            return result

        result["session_id"] = new_session_id

        # Step 2: Run project-bootstrap to load context
        bootstrap_cmd = subprocess.run(
            ['empirica', 'project-bootstrap', '--session-id', new_session_id, '--output', 'json'],
            capture_output=True, text=True, timeout=30
        )
        if bootstrap_cmd.returncode == 0:
            try:
                result["bootstrap_output"] = json.loads(bootstrap_cmd.stdout)
            except json.JSONDecodeError:
                result["bootstrap_output"] = {"raw": bootstrap_cmd.stdout[:500]}

        # Step 3: Try to get memory context from Qdrant (optional)
        if project_id:
            try:
                search_cmd = subprocess.run(
                    ['empirica', 'project-search', '--project-id', project_id,
                     '--task', 'current context and recent work', '--output', 'json'],
                    capture_output=True, text=True, timeout=15
                )
                if search_cmd.returncode == 0:
                    result["memory_context"] = json.loads(search_cmd.stdout)
            except Exception:
                pass  # Memory search is optional

        # Step 4: Semantic search for related goals (optional)
        if project_id:
            try:
                goals_cmd = subprocess.run(
                    ['empirica', 'goals-search', 'current work in progress',
                     '--project-id', project_id, '--status', 'in_progress',
                     '--limit', '5', '--output', 'json'],
                    capture_output=True, text=True, timeout=15
                )
                if goals_cmd.returncode == 0:
                    goals_result = json.loads(goals_cmd.stdout)
                    if goals_result.get('results'):
                        result["related_goals"] = goals_result['results']
            except Exception:
                pass  # Goal search is optional - Qdrant may not have goals yet

        # Step 5: Get stale goals (marked during pre-compact)
        if project_id:
            try:
                stale_cmd = subprocess.run(
                    ['empirica', 'goals-get-stale', '--project-id', project_id, '--output', 'json'],
                    capture_output=True, text=True, timeout=10
                )
                if stale_cmd.returncode == 0:
                    stale_result = json.loads(stale_cmd.stdout)
                    if stale_result.get('stale_goals'):
                        result["stale_goals"] = stale_result['stale_goals']
            except Exception:
                pass  # Stale goal check is optional

    except subprocess.TimeoutExpired:
        result["error"] = "Command timed out"
    except Exception as e:
        result["error"] = str(e)

    return result


def _generate_new_session_prompt(pre_vectors: dict, dynamic_context: dict, old_session_id: str, ai_id: str,
                                  session_bootstrap: dict = None) -> str:
    """
    Generate prompt for NEW session + PREFLIGHT when old session was complete.

    This is the correct path when compact happens AFTER POSTFLIGHT - the old
    session is done, we need a fresh start with proper baseline.

    If session_bootstrap is provided, the session was already created and bootstrapped
    by the hook - AI just needs to do PREFLIGHT with the loaded context.
    """
    pre_know = pre_vectors.get('know', 'N/A')
    pre_unc = pre_vectors.get('uncertainty', 'N/A')

    # Determine session_id for retrieval guidance
    new_session_id = None
    if session_bootstrap and session_bootstrap.get('session_id'):
        new_session_id = session_bootstrap['session_id']

    # Use epistemic summarizer for confidence-weighted ranking (no chronological fallback)
    if EPISTEMIC_SUMMARIZER_AVAILABLE:
        epistemic_focus = format_epistemic_focus(
            findings=dynamic_context.get('recent_findings', []),
            unknowns=dynamic_context.get('open_unknowns', []),
            dead_ends=dynamic_context.get('critical_dead_ends', []),
            goals=dynamic_context.get('active_goals', []),
            subtasks=dynamic_context.get('pending_subtasks', []),
            max_items=15,
            session_id=new_session_id
        )
    else:
        # Fallback to legacy formatting if summarizer not available
        goals_text = _format_goals(dynamic_context)
        findings_text = _format_findings(dynamic_context)
        unknowns_text = _format_unknowns(dynamic_context)
        epistemic_focus = f"""**Active Goals:**
{goals_text}

**Recent Findings (high-impact learnings):**
{findings_text}

**Open Unknowns (unresolved questions):**
{unknowns_text}"""

    # If hook already created session and ran bootstrap, use that
    if new_session_id:
        memory_text = _format_memory_context(session_bootstrap.get('memory_context'))

        return f"""
## POST-COMPACT: SESSION CREATED, PREFLIGHT REQUIRED

Your context was just compacted. The previous session ({old_session_id[:8]}...) was **COMPLETE**
(had POSTFLIGHT).

**✅ Session created:** `{new_session_id}`
**✅ Project context loaded via bootstrap**

**Pre-compact vectors (NOW INVALID):** know={pre_know}, uncertainty={pre_unc}

{epistemic_focus}

### Memory Context (Auto-Retrieved):
{memory_text}

### REQUIRED: Run PREFLIGHT (Baseline)

The session is ready. Now assess your ACTUAL epistemic state after loading this context:

```bash
empirica preflight-submit - << 'EOF'
{{
  "session_id": "{new_session_id}",
  "task_context": "<what you're working on>",
  "vectors": {{
    "know": <0.0-1.0: What do you ACTUALLY know now after loading context?>,
    "uncertainty": <0.0-1.0: How uncertain are you?>,
    "context": <0.0-1.0: How well do you understand current state?>,
    "engagement": <0.0-1.0: How engaged are you with the task?>
  }},
  "reasoning": "Post-compact with loaded context: <explain current epistemic state>"
}}
EOF
```

**Key principle:** Your PREFLIGHT should reflect knowledge AFTER reading the bootstrap context above.
This makes the PREFLIGHT→POSTFLIGHT delta meaningful.
"""

    # Fallback: Hook couldn't create session, AI needs to do full sequence
    return f"""
## POST-COMPACT: NEW SESSION REQUIRED

Your context was just compacted. The previous session ({old_session_id[:8]}...) was **COMPLETE**
(had POSTFLIGHT), so you need a NEW session with fresh PREFLIGHT baseline.

**Pre-compact vectors (NOW INVALID):** know={pre_know}, uncertainty={pre_unc}

{epistemic_focus}

### Step 1: Create New Session

```bash
empirica session-create --ai-id {ai_id} --output json
```

### Step 2: Load Project Context (REQUIRED BEFORE PREFLIGHT)

```bash
empirica project-bootstrap --session-id <NEW_SESSION_ID> --output json
```

### Step 3: Run PREFLIGHT (Baseline)

**IMPORTANT:** Only run PREFLIGHT AFTER loading context in Step 2.
PREFLIGHT should measure your knowledge AFTER bootstrap, not before.

```bash
empirica preflight-submit - << 'EOF'
{{
  "session_id": "<NEW_SESSION_ID>",
  "task_context": "<what you're working on>",
  "vectors": {{
    "know": <0.0-1.0: What do you ACTUALLY know now?>,
    "uncertainty": <0.0-1.0: How uncertain are you?>,
    "context": <0.0-1.0: How well do you understand current state?>,
    "engagement": <0.0-1.0: How engaged are you with the task?>
  }},
  "reasoning": "Post-compact fresh session: <explain current epistemic state>"
}}
EOF
```

**Key principle:** Be HONEST about reduced knowledge. This is a FRESH START, not a continuation.
"""


def _format_memory_context(memory_context: dict) -> str:
    """Format memory context from Qdrant search for prompt."""
    if not memory_context:
        return "  (No memory context available - Qdrant may not be running)"

    results = memory_context.get('results', {})
    if not results:
        return "  (No relevant memories found)"

    lines = []

    # Handle both old format (list) and new format (dict with docs/memory keys)
    if isinstance(results, dict):
        # New format: {"docs": [...], "memory": [...]}
        all_results = []
        for key in ['memory', 'docs', 'eidetic', 'episodic']:
            if key in results and isinstance(results[key], list):
                all_results.extend(results[key])
        results = all_results

    if not results:
        return "  (No relevant memories found)"

    for r in results[:5]:  # Top 5 memories
        if not isinstance(r, dict):
            continue
        content = r.get('content', r.get('text', ''))[:150]
        score = r.get('score', 0)
        lines.append(f"  - [{score:.2f}] {content}...")

    return "\n".join(lines) if lines else "  (No memories)"


def _format_goals(dynamic_context: dict) -> str:
    """Format goals for prompt, including semantic search results and stale goals."""
    lines = []

    # Stale goals (marked during pre-compact) - show first as they need attention
    if dynamic_context.get("stale_goals"):
        lines.append("  **⚠️ STALE (context lost during compaction - re-evaluate before continuing):**")
        for g in dynamic_context["stale_goals"]:
            obj = g.get('objective', 'Unknown')
            reason = g.get('stale_reason', 'memory_compact')
            lines.append(f"  - ⚠️ {obj[:80]}... (stale: {reason})")
            lines.append(f"       Refresh with: empirica goals-refresh --goal-id {g['goal_id']}")
        lines.append("  ")  # separator

    # Active goals from project-bootstrap
    if dynamic_context.get("active_goals"):
        for g in dynamic_context["active_goals"]:
            lines.append(f"  - {g['objective']} ({g['status']})")

    # Related goals from semantic search (goals-search)
    if dynamic_context.get("related_goals"):
        if lines:
            lines.append("  ")  # separator
            lines.append("  **Semantically related (from Qdrant):**")
        for g in dynamic_context["related_goals"]:
            obj = g.get('objective') or g.get('description', 'Unknown')
            status = g.get('status', 'unknown')
            score = g.get('score', 0)
            goal_type = g.get('type', 'goal')
            lines.append(f"  - [{goal_type}] {obj[:80]} ({status}, score={score:.2f})")

    return "\n".join(lines) if lines else "  (No active goals)"


def _format_findings(dynamic_context: dict) -> str:
    """Format findings for prompt."""
    if dynamic_context.get("recent_findings"):
        return "\n".join([
            f"  - {f['finding'][:100]}..." if len(f['finding']) > 100 else f"  - {f['finding']}"
            for f in dynamic_context["recent_findings"]
        ])
    return "  (No recent findings)"


def _format_unknowns(dynamic_context: dict) -> str:
    """Format unknowns for prompt."""
    if dynamic_context.get("open_unknowns"):
        return "\n".join([
            f"  - {u['unknown'][:100]}..." if len(u['unknown']) > 100 else f"  - {u['unknown']}"
            for u in dynamic_context["open_unknowns"]
        ])
    return "  (No open unknowns)"


def _format_dead_ends(dynamic_context: dict) -> str:
    """Format dead ends for prompt."""
    if dynamic_context.get("critical_dead_ends"):
        return "\n".join([
            f"  - {d['approach']}: {d['why_failed']}"
            for d in dynamic_context["critical_dead_ends"]
        ])
    return "  (None recorded)"


def _generate_transaction_continue_prompt(pre_vectors: dict, dynamic_context: dict, active_transaction: dict) -> str:
    """
    Generate a simple continuation prompt when there's an open transaction.

    When a transaction is open, the AI should just continue - no new PREFLIGHT or CHECK needed.
    The transaction file on disk is the source of truth.
    """
    pre_know = pre_vectors.get('know', 'N/A')
    pre_unc = pre_vectors.get('uncertainty', 'N/A')
    session_id = dynamic_context.get('session_context', {}).get('session_id', 'unknown')

    tx_id = active_transaction.get('transaction_id', 'unknown')[:8]
    tx_session = active_transaction.get('session_id', 'unknown')[:8]
    tx_project = active_transaction.get('project_path', 'unknown')
    if isinstance(tx_project, str) and '/' in tx_project:
        tx_project = tx_project.split('/')[-1]

    # Use epistemic summarizer for focus section if available
    if EPISTEMIC_SUMMARIZER_AVAILABLE:
        epistemic_focus = format_epistemic_focus(
            findings=dynamic_context.get('recent_findings', []),
            unknowns=dynamic_context.get('open_unknowns', []),
            dead_ends=dynamic_context.get('critical_dead_ends', []),
            goals=dynamic_context.get('active_goals', []),
            subtasks=dynamic_context.get('pending_subtasks', []),
            max_items=10,
            session_id=session_id if session_id != 'unknown' else None
        )
    else:
        epistemic_focus = "*No breadcrumbs loaded.*"

    return f"""## TRANSACTION CONTINUES

Your context was compacted but your **transaction is still open**.
No new PREFLIGHT or CHECK needed - just continue where you left off.

**⚡ ACTIVE TRANSACTION:**
   Transaction: {tx_id}... | Session: {tx_session}... | Project: {tx_project}
   Pre-compact vectors: know={pre_know}, uncertainty={pre_unc}

## EPISTEMIC FOCUS

{epistemic_focus}

**Continue your work.** When done with the current task, close with POSTFLIGHT.
"""


def _generate_check_prompt(pre_vectors: dict, pre_reasoning: str, dynamic_context: dict) -> str:
    """
    Generate a CHECK gate prompt for post-compact validation.

    CHECK is correct when session is INCOMPLETE (no POSTFLIGHT yet) -
    we're continuing work and need to validate readiness.
    """
    pre_know = pre_vectors.get('know', 'N/A')
    pre_unc = pre_vectors.get('uncertainty', 'N/A')
    session_id = dynamic_context.get('session_context', {}).get('session_id', 'unknown')

    # Format active transaction context (if exists)
    tx_context = ""
    project_folder = "unknown"  # Default for bootstrap command
    active_tx = dynamic_context.get('active_transaction')
    if active_tx:
        tx_id = active_tx.get('transaction_id', 'unknown')[:8]
        tx_status = active_tx.get('status', 'unknown')
        tx_project = active_tx.get('project_path', 'unknown')
        if isinstance(tx_project, str) and '/' in tx_project:
            project_folder = tx_project.split('/')[-1]  # Just folder name for commands
            tx_project = project_folder
        tx_context = f"""
**⚡ ACTIVE TRANSACTION (preserved across compact):**
   Transaction: {tx_id}... | Status: {tx_status} | Project: {tx_project}
   → This transaction is still open. Continue work within it or close with POSTFLIGHT.
"""
    else:
        # Try to get project folder from session_context
        project_id = dynamic_context.get('session_context', {}).get('project_id', '')
        if project_id:
            project_folder = project_id  # May be UUID or folder name

    # Use epistemic summarizer for confidence-weighted ranking (no chronological fallback)
    if EPISTEMIC_SUMMARIZER_AVAILABLE:
        epistemic_focus = format_epistemic_focus(
            findings=dynamic_context.get('recent_findings', []),
            unknowns=dynamic_context.get('open_unknowns', []),
            dead_ends=dynamic_context.get('critical_dead_ends', []),
            goals=dynamic_context.get('active_goals', []),
            subtasks=dynamic_context.get('pending_subtasks', []),
            max_items=15,
            session_id=session_id if session_id != 'unknown' else None
        )
    else:
        # Fallback to legacy formatting if summarizer not available
        goals_text = _format_goals(dynamic_context)
        findings_text = _format_findings(dynamic_context)
        unknowns_text = _format_unknowns(dynamic_context)
        dead_ends_text = _format_dead_ends(dynamic_context)
        epistemic_focus = f"""**Active Goals:**
{goals_text}

**Recent Findings (high-impact learnings):**
{findings_text}

**Open Unknowns (unresolved questions):**
{unknowns_text}

**Dead Ends (approaches that failed):**
{dead_ends_text}"""

    prompt = f"""
## POST-COMPACT CHECK GATE

Your context was just compacted. Your previous vectors (know={pre_know}, uncertainty={pre_unc})
are NO LONGER VALID - they reflected knowledge you had in full context.

**You now have only a summary. Run CHECK to validate readiness before proceeding.**
{tx_context}
{epistemic_focus}

### Step 1: Load Context (Recommended)

Before CHECK, recover context via bootstrap and/or semantic search:

```bash
# Load project context (depth scales with uncertainty)
empirica project-bootstrap --session-id {session_id} --project-id {project_folder} --output json

# Semantic search for specific topics (if Qdrant running)
empirica project-search --project-id {project_folder} --task "<your current task>" --output json
```

### Step 2: Run CHECK Gate

After loading context, validate readiness to proceed:

```bash
empirica check-submit - << 'EOF'
{{
  "session_id": "{session_id}",
  "action_description": "<what you intend to do next>",
  "vectors": {{
    "know": <0.0-1.0: What do you ACTUALLY know now?>,
    "uncertainty": <0.0-1.0: How uncertain are you?>,
    "context": <0.0-1.0: How well do you understand current state?>,
    "scope": <0.0-1.0: How broad is the intended action?>
  }},
  "reasoning": "Post-compact assessment: <explain current epistemic state>"
}}
EOF
```

### Step 3: Follow CHECK Decision

CHECK returns one of:
- **"proceed"** → You have sufficient confidence. Continue with work.
- **"investigate"** → Confidence too low. Load more context, read files, then CHECK again.

**Key principle:** Be HONEST about reduced knowledge. Post-compact know should typically be
LOWER than pre-compact. Do NOT proceed until CHECK returns "proceed".
"""
    return prompt


def _calculate_potential_drift(pre_vectors: dict) -> dict:
    """
    Calculate what drift WOULD look like if we naively kept pre-compact vectors.
    This shows why re-assessment is necessary.
    """
    if not pre_vectors:
        return {"warning": "No pre-compact vectors to compare"}

    # Post-compact, honest assessment would typically show:
    # - Lower know (lost detailed context)
    # - Higher uncertainty (less confident)
    # - Similar or lower context (depends on evidence loaded)

    pre_know = pre_vectors.get('know', 0.5)
    pre_unc = pre_vectors.get('uncertainty', 0.5)

    return {
        "pre_compact": {
            "know": pre_know,
            "uncertainty": pre_unc
        },
        "expected_honest_post_compact": {
            "know": max(0.3, pre_know - 0.2),  # Typically drops
            "uncertainty": min(0.8, pre_unc + 0.2)  # Typically rises
        },
        "message": "If your post-compact know equals pre-compact, you may be overestimating"
    }


def _print_user_message(pre_vectors: dict, dynamic_context: dict, potential_drift: dict,
                        phase_state: dict = None, ai_id: str = 'claude-code',
                        session_bootstrap: dict = None):
    """Print user-visible summary to stderr"""
    pre_know = pre_vectors.get('know', 'N/A')
    pre_unc = pre_vectors.get('uncertainty', 'N/A')

    goals_count = len(dynamic_context.get('active_goals', []))
    findings_count = len(dynamic_context.get('recent_findings', []))
    unknowns_count = len(dynamic_context.get('open_unknowns', []))

    is_complete = phase_state.get('is_complete', False) if phase_state else False
    last_phase = phase_state.get('last_phase', 'unknown') if phase_state else 'unknown'

    if is_complete:
        # Session was complete - check if hook created new session
        if session_bootstrap and session_bootstrap.get('session_id'):
            new_session_id = session_bootstrap['session_id']
            print(f"""
🔄 Empirica: Post-Compact Recovery (Session Complete)

📊 Previous Session State:
   Last Phase: {last_phase} (COMPLETE)
   Pre-compact vectors (NOW INVALID): know={pre_know}, uncertainty={pre_unc}

✅ NEW SESSION CREATED: {new_session_id}
✅ Project context bootstrapped automatically

📚 Dynamic Context Loaded:
   Active Goals: {goals_count}
   Recent Findings: {findings_count}
   Open Unknowns: {unknowns_count}

🎯 ACTION REQUIRED:
   Run PREFLIGHT with your ACTUAL knowledge state (after reading loaded context):
   empirica preflight-submit --session-id {new_session_id}

💡 TIP: Your PREFLIGHT should reflect knowledge AFTER reading the bootstrap context.
   This makes the PREFLIGHT→POSTFLIGHT delta meaningful.
""", file=sys.stderr)
        else:
            # Fallback: Hook couldn't create session
            print(f"""
🔄 Empirica: Post-Compact Recovery (Session Complete)

📊 Previous Session State:
   Last Phase: {last_phase} (COMPLETE)
   Pre-compact vectors (NOW INVALID): know={pre_know}, uncertainty={pre_unc}

⚠️  Previous session had POSTFLIGHT - it's COMPLETE.
   You need a NEW session with fresh PREFLIGHT baseline.

📚 Dynamic Context Available:
   Active Goals: {goals_count}
   Recent Findings: {findings_count}
   Open Unknowns: {unknowns_count}

🎯 ACTION REQUIRED:
   1. Create new session: empirica session-create --ai-id {ai_id}
   2. Load context: empirica project-bootstrap --session-id <NEW_ID>
   3. Run PREFLIGHT: empirica preflight-submit (AFTER loading context!)
""", file=sys.stderr)
    else:
        # Session incomplete - need CHECK to continue
        print(f"""
🔄 Empirica: Post-Compact CHECK Gate (Session Incomplete)

📊 Pre-Compact State (NOW INVALID):
   Last Phase: {last_phase}
   know={pre_know}, uncertainty={pre_unc}

⚠️  These vectors reflected FULL context knowledge.
   You now have only a summary. Session is INCOMPLETE.

📚 Dynamic Context Loaded:
   Active Goals: {goals_count}
   Recent Findings: {findings_count}
   Open Unknowns: {unknowns_count}

🎯 ACTION REQUIRED:
   1. Load context: empirica project-bootstrap --session-id <ID>
   2. Run CHECK: empirica check-submit (with honest assessment)
   3. Follow decision: "proceed" or "investigate"
""", file=sys.stderr)


if __name__ == '__main__':
    main()
