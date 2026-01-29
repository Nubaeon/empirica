#!/usr/bin/env python3
"""
Empirica Statusline v2 - Unified Signaling with Moon Phases

Uses the shared signaling module for consistent emoji display.
Reads vectors from DB (real-time) and drift from cache (hook-updated).

Display modes:
  - basic: Just drift status
  - default: Phase + key vectors + drift
  - learning: Focus on vector changes
  - full: Everything with values

Environment:
  EMPIRICA_STATUS_MODE: basic|default|learning|full (default: default)
  EMPIRICA_AI_ID: AI identifier (default: claude-code)
  EMPIRICA_SIGNALING_LEVEL: basic|default|full (default: default)

Author: Claude Code
Date: 2025-12-30
Version: 2.1.0 (Unified Signaling)
"""

import os
import sys
from pathlib import Path

# Add empirica to path
EMPIRICA_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(EMPIRICA_ROOT))

from empirica.config.path_resolver import get_empirica_root
from empirica.data.session_database import SessionDatabase
from empirica.core.signaling import (
    SignalingState,
    format_vectors_compact,
    format_drift_status,
    read_drift_cache,
)


# ANSI color codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    BLUE = '\033[34m'
    CYAN = '\033[36m'
    GRAY = '\033[90m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_CYAN = '\033[96m'


def get_ai_id() -> str:
    """Get AI identifier from environment."""
    return os.getenv('EMPIRICA_AI_ID', 'claude-code').strip()


def get_open_counts(db: SessionDatabase, session_id: str) -> dict:
    """
    Get counts of open goals and unknowns (project-wide).

    Goals and unknowns are project-wide because work spans sessions.
    Goal-linked unknowns indicate blockers that need resolution.

    Returns:
        {
            'open_goals': int,           # Goals not yet completed (project-wide)
            'open_unknowns': int,        # Unknowns not yet resolved (project-wide)
            'goal_linked_unknowns': int, # Unresolved unknowns linked to goals (blockers)
            'completion': float,         # Latest completion vector (0.0-1.0)
        }
    """
    cursor = db.conn.cursor()

    # Count open goals PROJECT-WIDE (goals span sessions)
    cursor.execute("""
        SELECT COUNT(*)
        FROM goals
        WHERE status != 'completed'
    """)
    open_goals = cursor.fetchone()[0] or 0

    # Count unresolved unknowns PROJECT-WIDE (not session-specific)
    cursor.execute("""
        SELECT COUNT(*)
        FROM session_unknowns
        WHERE is_resolved = FALSE
    """)
    open_unknowns = cursor.fetchone()[0] or 0

    # Count goal-linked unresolved unknowns (blockers)
    cursor.execute("""
        SELECT COUNT(*)
        FROM session_unknowns
        WHERE is_resolved = FALSE AND goal_id IS NOT NULL
    """)
    goal_linked_unknowns = cursor.fetchone()[0] or 0

    # Get completion from latest vector state
    cursor.execute("""
        SELECT completion
        FROM reflexes
        WHERE session_id = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (session_id,))
    reflex_row = cursor.fetchone()
    completion = reflex_row[0] if reflex_row and reflex_row[0] is not None else 0.0

    return {
        'open_goals': open_goals,
        'open_unknowns': open_unknowns,
        'goal_linked_unknowns': goal_linked_unknowns,
        'completion': completion,
    }


def get_active_goal(db: SessionDatabase, session_id: str) -> dict:
    """
    Get the active goal for a session (legacy, kept for 'full' mode).

    Returns:
        {
            'goal_id': str,
            'objective': str,
            'completion': float (0.0-1.0) - from vector state, not subtasks
            'subtask_progress': (completed, total) - for reference only
        }
        or None if no active goal
    """
    cursor = db.conn.cursor()

    # Get active (non-completed) goal for this session
    cursor.execute("""
        SELECT id, objective, status
        FROM goals
        WHERE session_id = ? AND status != 'completed'
        ORDER BY created_timestamp DESC
        LIMIT 1
    """, (session_id,))
    row = cursor.fetchone()

    if not row:
        return None

    goal_id, objective, _ = row  # _ for unused status

    # Get completion from latest vector state (epistemic measure)
    # This is the AI's self-assessed completion, not mechanical subtask checkboxes
    cursor.execute("""
        SELECT completion
        FROM reflexes
        WHERE session_id = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (session_id,))
    reflex_row = cursor.fetchone()
    completion = reflex_row[0] if reflex_row and reflex_row[0] is not None else 0.0

    # Get subtask progress (for reference, not primary measure)
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
        FROM subtasks
        WHERE goal_id = ?
    """, (goal_id,))
    subtask_row = cursor.fetchone()

    total_subtasks = subtask_row[0] if subtask_row else 0
    completed_subtasks = subtask_row[1] if subtask_row else 0

    return {
        'goal_id': goal_id,
        'objective': objective,
        'completion': completion,
        'subtask_progress': (completed_subtasks, total_subtasks)
    }


def format_progress_bar(completion: float, width: int = 8) -> str:
    """
    Format completion as ASCII progress bar.

    Args:
        completion: 0.0 to 1.0
        width: number of characters for the bar

    Returns:
        String like "████░░░░ 45%"
    """
    filled = int(completion * width)
    empty = width - filled

    bar = "█" * filled + "░" * empty
    pct = int(completion * 100)

    # Color based on progress
    if completion >= 0.75:
        color = Colors.BRIGHT_GREEN
    elif completion >= 0.5:
        color = Colors.GREEN
    elif completion >= 0.25:
        color = Colors.YELLOW
    else:
        color = Colors.GRAY

    return f"{color}{bar}{Colors.RESET} {pct}%"


def format_open_counts(open_counts: dict) -> str:
    """
    Format open goals and unknowns as actionable counts.

    Shows what needs to be closed - useful for peeking into AI reality.

    Returns:
        String like "🎯3 ❓6/4" (3 goals, 6 unknowns total, 4 goal-linked blockers)
    """
    if not open_counts:
        return f"{Colors.GRAY}--{Colors.RESET}"

    goals = open_counts.get('open_goals', 0)
    unknowns = open_counts.get('open_unknowns', 0)
    goal_linked = open_counts.get('goal_linked_unknowns', 0)

    # Color code based on counts
    if goals == 0:
        goal_color = Colors.GREEN
    elif goals <= 2:
        goal_color = Colors.YELLOW
    else:
        goal_color = Colors.CYAN

    # Color unknowns based on goal-linked (blockers) count
    if goal_linked == 0:
        unknown_color = Colors.GREEN
    elif goal_linked <= 5:
        unknown_color = Colors.YELLOW
    else:
        unknown_color = Colors.CYAN

    # Format: ❓total/blockers (e.g., ❓119/70 means 119 unresolved, 70 blocking goals)
    if goal_linked > 0 and goal_linked != unknowns:
        unknown_str = f"❓{unknowns}/{goal_linked}"
    else:
        unknown_str = f"❓{unknowns}"

    return f"{goal_color}🎯{goals}{Colors.RESET} {unknown_color}{unknown_str}{Colors.RESET}"


def format_goal_progress(goal: dict, max_name_len: int = 12) -> str:
    """
    Format goal progress for statusline (legacy, used in 'full' mode).

    Returns:
        String like "auth-fix ████░░░░ 45%" or "████░░░░ 45%" if no goal name
    """
    if not goal:
        return f"{Colors.GRAY}no goal{Colors.RESET}"

    objective = goal.get('objective', '')
    completion = goal.get('completion', 0.0)

    # Truncate objective for display
    if len(objective) > max_name_len:
        name = objective[:max_name_len-2] + ".."
    else:
        name = objective

    # Simplify name: lowercase, replace spaces with dashes
    name = name.lower().replace(' ', '-')[:max_name_len]

    bar = format_progress_bar(completion, width=6)

    if name:
        return f"{name} {bar}"
    else:
        return bar


def calculate_confidence(vectors: dict) -> float:
    """
    Calculate overall confidence score from vectors.

    Formula: weighted average of key epistemic indicators
    - know (40%): How much we understand
    - 1-uncertainty (30%): Inverse of doubt
    - context (20%): How well we understand the situation
    - completion (10%): How much is done

    Returns: 0.0 to 1.0 (displayed as 0-100%)
    """
    if not vectors:
        return 0.0

    know = vectors.get('know', 0.5)
    uncertainty = vectors.get('uncertainty', 0.5)
    context = vectors.get('context', 0.5)
    completion = vectors.get('completion', 0.0)

    confidence = (
        0.40 * know +
        0.30 * (1.0 - uncertainty) +
        0.20 * context +
        0.10 * completion
    )

    return max(0.0, min(1.0, confidence))


def format_confidence(confidence: float) -> str:
    """Format confidence as colored percentage with tiered emoji."""
    pct = int(confidence * 100)

    if confidence >= 0.75:
        color = Colors.BRIGHT_GREEN
        emoji = "⚡"  # High energy/power
    elif confidence >= 0.50:
        color = Colors.GREEN
        emoji = "💡"  # Good understanding
    elif confidence >= 0.35:
        color = Colors.YELLOW
        emoji = "💫"  # Some uncertainty
    else:
        color = Colors.RED
        emoji = "🌑"  # Low confidence/dark

    return f"{emoji}{color}{pct}%{Colors.RESET}"


def get_active_session(db: SessionDatabase, ai_id: str) -> dict:
    """
    Get the active session, with smart fallback logic.

    Priority:
    1. Check ~/.empirica/active_session file for explicit session
    2. Match exact ai_id (filtered by instance_id for multi-instance isolation)
    3. Match ai_id prefix (e.g., 'claude-code' matches 'claude-code-multimachine')
    """
    cursor = db.conn.cursor()

    # Get current instance_id for multi-instance isolation
    try:
        from empirica.utils.session_resolver import get_instance_id
        current_instance_id = get_instance_id()
    except ImportError:
        current_instance_id = None

    # Priority 1: Check instance-specific active_session file
    # Uses instance_id (e.g., tmux:%0) to prevent cross-pane bleeding
    # Search UPWARD from CWD like git does for .git/

    # Get instance_id for per-pane isolation
    instance_suffix = ""
    if current_instance_id:
        # Sanitize instance_id for filename (replace special chars)
        safe_instance = current_instance_id.replace(":", "_").replace("%", "")
        instance_suffix = f"_{safe_instance}"

    local_active_session = None
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        # Try instance-specific file first, then generic
        for filename in [f'active_session{instance_suffix}', 'active_session']:
            candidate = parent / '.empirica' / filename
            if candidate.exists():
                local_active_session = candidate
                break
        if local_active_session:
            break
        if parent == Path.home() or parent == parent.parent:
            break  # Stop at home or filesystem root

    global_active_session = Path.home() / '.empirica' / f'active_session{instance_suffix}'
    global_active_session_fallback = Path.home() / '.empirica' / 'active_session'

    # Build list of files to check (instance-specific first)
    files_to_check = []
    if local_active_session:
        files_to_check.append(local_active_session)
    files_to_check.append(global_active_session)
    if global_active_session != global_active_session_fallback:
        files_to_check.append(global_active_session_fallback)

    for active_session_file in files_to_check:
        if active_session_file.exists():
            try:
                session_id = active_session_file.read_text().strip()
                if session_id:
                    # Filter by ai_id to prevent sub-agent sessions from hijacking statusline
                    # (e.g., test-goal-agent overwrites active_session file in same pane)
                    cursor.execute("""
                        SELECT session_id, ai_id, start_time
                        FROM sessions
                        WHERE session_id = ? AND end_time IS NULL AND ai_id = ?
                    """, (session_id, ai_id))
                    row = cursor.fetchone()
                    if row:
                        return dict(row)
            except Exception:
                pass  # Try next file

    # Priority 2: Exact ai_id match (with instance isolation)
    if current_instance_id:
        # Filter by instance_id OR legacy sessions (NULL instance_id)
        cursor.execute("""
            SELECT session_id, ai_id, start_time
            FROM sessions
            WHERE end_time IS NULL AND ai_id = ?
              AND (instance_id = ? OR instance_id IS NULL)
            ORDER BY start_time DESC
            LIMIT 1
        """, (ai_id, current_instance_id))
    else:
        cursor.execute("""
            SELECT session_id, ai_id, start_time
            FROM sessions
            WHERE end_time IS NULL AND ai_id = ?
            ORDER BY start_time DESC
            LIMIT 1
        """, (ai_id,))
    row = cursor.fetchone()
    if row:
        return dict(row)

    # Priority 3: Prefix match (e.g., 'claude-code' matches 'claude-code-xyz')
    if current_instance_id:
        cursor.execute("""
            SELECT session_id, ai_id, start_time
            FROM sessions
            WHERE end_time IS NULL AND ai_id LIKE ?
              AND (instance_id = ? OR instance_id IS NULL)
            ORDER BY start_time DESC
            LIMIT 1
        """, (f"{ai_id}%", current_instance_id))
    else:
        cursor.execute("""
            SELECT session_id, ai_id, start_time
            FROM sessions
            WHERE end_time IS NULL AND ai_id LIKE ?
            ORDER BY start_time DESC
            LIMIT 1
        """, (f"{ai_id}%",))
    row = cursor.fetchone()
    return dict(row) if row else None


def get_latest_vectors(db: SessionDatabase, session_id: str) -> tuple:
    """Get latest vectors, phase, and gate decision from reflexes table."""
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT phase, engagement, know, do, context,
               clarity, coherence, signal, density,
               state, change, completion, impact, uncertainty,
               reflex_data
        FROM reflexes
        WHERE session_id = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (session_id,))
    row = cursor.fetchone()

    if not row:
        return None, {}, None

    phase = row[0]
    vectors = {
        'engagement': row[1],
        'know': row[2],
        'do': row[3],
        'context': row[4],
        'clarity': row[5],
        'coherence': row[6],
        'signal': row[7],
        'density': row[8],
        'state': row[9],
        'change': row[10],
        'completion': row[11],
        'impact': row[12],
        'uncertainty': row[13],
    }

    # Filter out None values
    vectors = {k: v for k, v in vectors.items() if v is not None}

    # Extract gate decision from reflex_data (CHECK phase)
    gate_decision = None
    if row[14]:  # reflex_data column
        try:
            import json
            reflex_data = json.loads(row[14])
            gate_decision = reflex_data.get('decision')
        except:
            pass

    return phase, vectors, gate_decision


def get_vector_deltas(db: SessionDatabase, session_id: str) -> dict:
    """
    Get learning deltas: PREFLIGHT → POSTFLIGHT only.

    This measures actual learning across the session, ignoring CHECK
    phases which are for gating, not learning measurement.
    """
    cursor = db.conn.cursor()

    # Get PREFLIGHT baseline (first PREFLIGHT in session)
    cursor.execute("""
        SELECT know, uncertainty, context, completion, engagement
        FROM reflexes
        WHERE session_id = ? AND phase = 'PREFLIGHT'
        ORDER BY timestamp ASC
        LIMIT 1
    """, (session_id,))
    preflight = cursor.fetchone()

    # Get latest POSTFLIGHT (final state)
    cursor.execute("""
        SELECT know, uncertainty, context, completion, engagement
        FROM reflexes
        WHERE session_id = ? AND phase = 'POSTFLIGHT'
        ORDER BY timestamp DESC
        LIMIT 1
    """, (session_id,))
    postflight = cursor.fetchone()

    if not preflight or not postflight:
        # Fallback: if no complete cycle, show sequential delta
        cursor.execute("""
            SELECT know, uncertainty, context, completion, engagement
            FROM reflexes
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT 2
        """, (session_id,))
        rows = cursor.fetchall()
        if len(rows) < 2:
            return {}
        postflight = rows[0]
        preflight = rows[1]

    deltas = {}
    keys = ['know', 'uncertainty', 'context', 'completion', 'engagement']

    for i, key in enumerate(keys):
        post_val = postflight[i]
        pre_val = preflight[i]

        if post_val is not None and pre_val is not None:
            delta = post_val - pre_val
            if abs(delta) >= 0.05:  # Only show meaningful changes
                deltas[key] = delta

    return deltas


def format_deltas(deltas: dict) -> str:
    """Format deltas for display (e.g., 'know:+0.15 unc:-0.10')."""
    if not deltas:
        return ""

    parts = []
    # Priority order for display
    priority_keys = ['know', 'uncertainty', 'completion', 'context', 'engagement']

    for key in priority_keys:
        if key in deltas:
            delta = deltas[key]
            # Abbreviate keys
            abbrev = {'know': 'K', 'uncertainty': 'U', 'context': 'C',
                      'completion': '✓', 'engagement': 'E'}
            sign = '+' if delta > 0 else ''

            # Color code: green for improvements, red for regressions
            # For uncertainty, lower is better (negative is green)
            if key == 'uncertainty':
                color = Colors.GREEN if delta < 0 else Colors.RED
            else:
                color = Colors.GREEN if delta > 0 else Colors.RED

            parts.append(f"{color}{abbrev.get(key, key[:1])}:{sign}{delta:.2f}{Colors.RESET}")

    return ' '.join(parts[:3])  # Max 3 deltas to keep it compact


def get_drift_from_db(db: SessionDatabase, session_id: str) -> tuple:
    """Check drift status from recent reflexes."""
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT know, uncertainty, context, completion
        FROM reflexes
        WHERE session_id = ?
        ORDER BY timestamp DESC
        LIMIT 6
    """, (session_id,))
    rows = cursor.fetchall()

    if len(rows) < 2:
        return False, None

    # Compare latest to average of previous
    latest = rows[0]
    previous = rows[1:]

    # Calculate average of previous
    avg_know = sum(r[0] or 0.5 for r in previous) / len(previous)
    avg_unc = sum(r[1] or 0.5 for r in previous) / len(previous)

    # Check for significant drops
    know_drop = avg_know - (latest[0] or 0.5)
    unc_increase = (latest[1] or 0.5) - avg_unc

    # Drift detection thresholds
    if know_drop > 0.3 or unc_increase > 0.3:
        return True, 'high'
    elif know_drop > 0.2 or unc_increase > 0.2:
        return True, 'medium'
    elif know_drop > 0.1 or unc_increase > 0.1:
        return True, 'low'

    return False, None


def format_statusline(
    session: dict,
    phase: str,
    vectors: dict,
    drift_state: SignalingState,
    deltas: dict = None,
    mode: str = 'default',
    drift_detected: bool = False,
    drift_severity: str = None,
    gate_decision: str = None,
    goal: dict = None,
    open_counts: dict = None
) -> str:
    """Format the statusline based on mode."""

    # Calculate confidence score
    confidence = calculate_confidence(vectors)
    conf_str = format_confidence(confidence)

    parts = [f"{Colors.GREEN}[empirica]{Colors.RESET} {conf_str}"]

    if mode == 'basic':
        # Just confidence + drift
        drift_str = format_drift_status(drift_detected, drift_severity)
        parts.append(drift_str)
        return ' '.join(parts)

    elif mode == 'default':
        # Open counts (goals/unknowns to close) + CASCADE gate + key vectors (%) + deltas + drift
        # Shows actionable items: what needs to be resolved
        counts_str = format_open_counts(open_counts)
        parts.append(counts_str)

        # CASCADE gate (compliance checkpoint) with metacog decision
        if phase:
            phase_str = f"{Colors.BLUE}{phase}{Colors.RESET}"
            # Show gate decision after CHECK phase
            if gate_decision and phase == 'CHECK':
                if gate_decision == 'proceed':
                    phase_str += f" {Colors.GREEN}→PROCEED{Colors.RESET}"
                elif gate_decision == 'investigate':
                    phase_str += f" {Colors.YELLOW}→INVESTIGATE{Colors.RESET}"
            parts.append(phase_str)

        if vectors:
            # Use percentage format for key vectors
            vec_str = format_vectors_compact(vectors, keys=['know', 'uncertainty', 'context'], use_percentage=True)
            parts.append(vec_str)

        # Add deltas if present
        if deltas:
            delta_str = format_deltas(deltas)
            if delta_str:
                parts.append(f"Δ {delta_str}")

        # Drift status
        drift_str = format_drift_status(drift_detected, drift_severity)
        parts.append(drift_str)

        return ' │ '.join(parts)

    elif mode == 'learning':
        # Focus on vectors with values and deltas (for developers)
        counts_str = format_open_counts(open_counts)
        parts.append(counts_str)

        if phase:
            parts.append(f"{phase}")

        if vectors:
            # Show more vectors with percentages
            all_keys = ['know', 'uncertainty', 'context', 'clarity', 'completion']
            vec_str = format_vectors_compact(vectors, keys=all_keys, use_percentage=True)
            parts.append(vec_str)

        # Always show deltas in learning mode
        if deltas:
            delta_str = format_deltas(deltas)
            if delta_str:
                parts.append(f"Δ {delta_str}")

        drift_str = format_drift_status(drift_detected, drift_severity)
        parts.append(drift_str)

        return ' │ '.join(parts)

    else:  # full
        # Everything (for developers/debugging)
        ai_id = session.get('ai_id', 'unknown')
        session_id = session.get('session_id', '????')[:4]
        parts = [f"{Colors.BRIGHT_CYAN}[empirica:{ai_id}@{session_id}]{Colors.RESET}"]

        # Goal progress with more detail
        if goal:
            completed, total = goal.get('subtask_progress', (0, 0))
            goal_str = format_goal_progress(goal)
            if total > 0:
                goal_str += f" ({completed}/{total})"
            parts.append(goal_str)
        else:
            parts.append(f"{Colors.GRAY}no goal{Colors.RESET}")

        if phase:
            parts.append(f"{Colors.BLUE}{phase}{Colors.RESET}")

        if vectors:
            all_keys = ['know', 'uncertainty', 'context', 'clarity', 'engagement', 'completion', 'impact']
            vec_str = format_vectors_compact(vectors, keys=all_keys, use_percentage=True)
            parts.append(vec_str)

        # Show deltas in full mode
        if deltas:
            delta_str = format_deltas(deltas)
            if delta_str:
                parts.append(f"Δ {delta_str}")

        drift_str = format_drift_status(drift_detected, drift_severity)
        parts.append(drift_str)

        return ' │ '.join(parts)


def main():
    """Main statusline generation."""
    try:
        mode = os.getenv('EMPIRICA_STATUS_MODE', 'default').lower()
        ai_id = get_ai_id()

        # Auto-detect project from current directory (like git does with .git/)
        # Priority: 1) EMPIRICA_PROJECT_PATH env var, 2) .empirica/ in cwd or parents, 3) global
        project_path = os.getenv('EMPIRICA_PROJECT_PATH')

        if not project_path:
            # Search UPWARD for .empirica/ like git does for .git/
            current = Path.cwd()
            for parent in [current] + list(current.parents):
                candidate_db = parent / '.empirica' / 'sessions' / 'sessions.db'
                if candidate_db.exists():
                    project_path = str(parent)
                    break
                if parent == Path.home() or parent == parent.parent:
                    break

        if project_path:
            db_path = Path(project_path) / '.empirica' / 'sessions' / 'sessions.db'
            db = SessionDatabase(db_path=str(db_path))
        else:
            # Fallback to global hub at ~/.empirica/ instead of creating in CWD
            global_db = Path.home() / '.empirica' / 'sessions' / 'sessions.db'
            if global_db.exists():
                db = SessionDatabase(db_path=str(global_db))
            else:
                db = SessionDatabase()
        session = get_active_session(db, ai_id)

        # Always get project-level counts (goals are project-wide)
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM goals WHERE status != 'completed'")
        open_goals = cursor.fetchone()[0] or 0

        if not session:
            # No active session, but still show project-level data
            if open_goals > 0:
                print(f"{Colors.GRAY}[empirica]{Colors.RESET} {Colors.CYAN}🎯{open_goals}{Colors.RESET} │ {Colors.GRAY}no session{Colors.RESET}")
            else:
                print(f"{Colors.GRAY}[empirica:{ai_id}:inactive]{Colors.RESET}")
            db.close()
            return

        session_id = session['session_id']

        # Get vectors from DB (real-time)
        phase, vectors, gate_decision = get_latest_vectors(db, session_id)

        # Get deltas (learning measurement)
        deltas = get_vector_deltas(db, session_id)

        # Check drift from DB (compare recent reflexes)
        drift_detected, drift_severity = get_drift_from_db(db, session_id)

        # Get active goal for this session (used in 'full' mode)
        goal = get_active_goal(db, session_id)

        # Get open counts (goals/unknowns to close) - used in default/learning modes
        open_counts = get_open_counts(db, session_id)

        # Get drift from cache (updated by hooks) - fallback
        drift_state = read_drift_cache(str(Path.cwd()))

        # If no cached drift, create minimal state from vectors
        if not drift_state and vectors:
            drift_state = SignalingState(
                phase=phase,
                vectors=vectors,
                session_id=session_id,
                ai_id=ai_id
            )

        db.close()

        # Format and output
        output = format_statusline(
            session, phase, vectors, drift_state, deltas, mode,
            drift_detected=drift_detected, drift_severity=drift_severity,
            gate_decision=gate_decision, goal=goal, open_counts=open_counts
        )
        print(output)

    except Exception as e:
        print(f"{Colors.GRAY}[empirica:error]{Colors.RESET}")
        # Log error
        try:
            with open(get_empirica_root() / 'statusline.log', 'a') as f:
                f.write(f"ERROR: {e}\n")
        except:
            pass


if __name__ == '__main__':
    main()
