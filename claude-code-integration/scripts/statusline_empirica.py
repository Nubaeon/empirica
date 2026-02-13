#!/usr/bin/env python3
"""
Empirica Statusline v2 - Unified Signaling with Moon Phases

Uses the shared signaling module for consistent emoji display.
Reads vectors from DB (real-time).

Display modes:
  - basic: Just confidence
  - default: Phase + key vectors + open counts
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
from empirica.core.signaling import format_vectors_compact
from empirica.core.statusline_cache import get_instance_id


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


def detect_extensions() -> dict:
    """
    Detect active Empirica extensions (CRM, WORKSPACE).

    Detection is based on database existence, not Python module imports.
    This allows extensions to work even if not installed as packages.

    Returns:
        {
            'crm': {'active': bool, 'db_path': str, 'active_client': str|None},
            'workspace': {'active': bool, 'db_path': str, 'project_count': int},
        }
    """
    import sqlite3

    result = {
        'crm': {'active': False, 'db_path': None, 'active_client': None},
        'workspace': {'active': False, 'db_path': None, 'project_count': 0},
    }

    # Check CRM
    crm_db = Path.home() / '.empirica' / 'crm' / 'crm.db'
    if crm_db.exists():
        result['crm']['active'] = True
        result['crm']['db_path'] = str(crm_db)
        try:
            conn = sqlite3.connect(str(crm_db))
            cursor = conn.cursor()
            # Try to get active client from recent engagement
            cursor.execute("""
                SELECT c.name FROM clients c
                JOIN engagements e ON e.client_id = c.client_id
                WHERE e.status = 'active'
                ORDER BY e.started_at DESC LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                result['crm']['active_client'] = row[0]
            conn.close()
        except Exception:
            pass

    # Check WORKSPACE
    workspace_db = Path.home() / '.empirica' / 'workspace' / 'workspace.db'
    if workspace_db.exists():
        result['workspace']['active'] = True
        result['workspace']['db_path'] = str(workspace_db)
        try:
            conn = sqlite3.connect(str(workspace_db))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM global_projects WHERE status = 'active'")
            row = cursor.fetchone()
            result['workspace']['project_count'] = row[0] if row else 0
            conn.close()
        except Exception:
            pass

    return result


def format_extension_indicators(extensions: dict) -> str:
    """
    Format extension indicators for statusline.

    Returns:
        String like "CRM:Acme WS:27" or "" if no extensions active
    """
    parts = []

    if extensions.get('crm', {}).get('active'):
        client = extensions['crm'].get('active_client')
        if client:
            # Truncate client name
            if len(client) > 8:
                client = client[:7] + '…'
            parts.append(f"{Colors.CYAN}CRM:{client}{Colors.RESET}")
        else:
            parts.append(f"{Colors.GRAY}CRM{Colors.RESET}")

    if extensions.get('workspace', {}).get('active'):
        count = extensions['workspace'].get('project_count', 0)
        if count > 0:
            parts.append(f"{Colors.CYAN}WS:{count}{Colors.RESET}")
        else:
            parts.append(f"{Colors.GRAY}WS{Colors.RESET}")

    return ' '.join(parts)


def get_open_counts(db: SessionDatabase, session_id: str, project_id: str = None) -> dict:
    """
    Get counts of open goals and unknowns for a specific project.

    Goals and unknowns are project-scoped to prevent cross-project data leakage.
    Goal-linked unknowns indicate blockers that need resolution.

    Args:
        db: Database connection
        session_id: Current session ID
        project_id: Project ID to filter by (required for accurate counts)

    Returns:
        {
            'open_goals': int,           # Goals not yet completed (project-scoped)
            'open_unknowns': int,        # Unknowns not yet resolved (project-scoped)
            'goal_linked_unknowns': int, # Unresolved unknowns linked to goals (blockers)
            'completion': float,         # Latest completion vector (0.0-1.0)
        }
    """
    cursor = db.conn.cursor()

    # Count open goals for THIS PROJECT (project-scoped, not session-scoped)
    # Use is_completed (source of truth) not status column (can be inconsistent)
    if project_id:
        cursor.execute("""
            SELECT COUNT(*)
            FROM goals
            WHERE is_completed = 0 AND project_id = ?
        """, (project_id,))
    else:
        cursor.execute("""
            SELECT COUNT(*)
            FROM goals
            WHERE is_completed = 0
        """)
    open_goals = cursor.fetchone()[0] or 0

    # Count unresolved unknowns for THIS PROJECT
    # Use project_unknowns directly (has project_id column) - no session JOIN needed
    if project_id:
        cursor.execute("""
            SELECT COUNT(*)
            FROM project_unknowns
            WHERE is_resolved = 0 AND project_id = ?
        """, (project_id,))
    else:
        cursor.execute("""
            SELECT COUNT(*)
            FROM project_unknowns
            WHERE is_resolved = 0
        """)
    open_unknowns = cursor.fetchone()[0] or 0

    # Count goal-linked unresolved unknowns (blockers) for THIS PROJECT
    if project_id:
        cursor.execute("""
            SELECT COUNT(*)
            FROM project_unknowns
            WHERE is_resolved = 0 AND goal_id IS NOT NULL AND project_id = ?
        """, (project_id,))
    else:
        cursor.execute("""
            SELECT COUNT(*)
            FROM project_unknowns
            WHERE is_resolved = 0 AND goal_id IS NOT NULL
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


def _resolve_claude_session_id(stdin_claude_session_id: str = None):
    """
    Resolve the Claude session ID from available sources.

    Priority:
    1. stdin JSON (passed by Claude Code to statusline commands)
    2. TTY session (requires TMUX_PANE)

    Returns claude_session_id or None.
    """
    if stdin_claude_session_id:
        return stdin_claude_session_id

    try:
        from empirica.utils.session_resolver import get_tty_session
        tty_session = get_tty_session(warn_if_stale=False)
        if tty_session:
            return tty_session.get('claude_session_id')
    except Exception:
        pass

    return None


def get_active_session(db: SessionDatabase, ai_id: str, stdin_claude_session_id: str = None) -> dict:
    """
    Get the active session with strict pane isolation.

    Priority:
    0. Claude session_id (from stdin or TTY) → active_work file → empirica_session_id
    1. Instance-specific active_session file (active_session_tmux_N)
    2. Exact ai_id + exact instance_id match in DB (NO NULL fallback)
    3. Generic active_session file (only if no instance_id available)

    IMPORTANT: Never fall back to instance_id IS NULL - that causes
    cross-pane bleeding where any pane picks up legacy sessions.
    """
    cursor = db.conn.cursor()

    # Priority 0: Claude session_id → active_work file → empirica_session_id
    # Sources: stdin JSON from Claude Code (works without tmux) OR TTY session (needs TMUX_PANE)
    try:
        import json as _json

        claude_session_id = _resolve_claude_session_id(stdin_claude_session_id)
        if claude_session_id:
            empirica_session_id = None

            # Priority 0a: active_work file (authoritative, updated by project-switch)
            active_work_path = Path.home() / '.empirica' / f'active_work_{claude_session_id}.json'
            if active_work_path.exists():
                with open(active_work_path, 'r') as f:
                    active_work = _json.load(f)
                    empirica_session_id = active_work.get('empirica_session_id')

            # Priority 0b: TTY session empirica_session_id (fallback)
            if not empirica_session_id:
                try:
                    from empirica.utils.session_resolver import get_tty_session
                    tty_session = get_tty_session(warn_if_stale=False)
                    if tty_session:
                        empirica_session_id = tty_session.get('empirica_session_id')
                except Exception:
                    pass

            if empirica_session_id:
                cursor.execute("""
                    SELECT session_id, ai_id, start_time
                    FROM sessions
                    WHERE session_id = ? AND end_time IS NULL
                """, (empirica_session_id,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
    except Exception:
        pass  # Fall through to legacy methods

    # Get current instance_id for multi-instance isolation (legacy)
    try:
        from empirica.utils.session_resolver import get_instance_id
        current_instance_id = get_instance_id()
    except ImportError:
        current_instance_id = None

    # Build instance-specific filename suffix
    instance_suffix = ""
    if current_instance_id:
        safe_instance = current_instance_id.replace(":", "_").replace("%", "")
        instance_suffix = f"_{safe_instance}"

    # Priority 1: Instance-specific active_session file ONLY
    # Do NOT fall through to generic 'active_session' when instance_id is known
    # That's the primary bleeding vector - generic file has no pane isolation
    if instance_suffix:
        # Search upward for instance-specific file only
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            candidate = parent / '.empirica' / f'active_session{instance_suffix}'
            if candidate.exists():
                try:
                    content = candidate.read_text().strip()
                    # Handle JSON format (new) or plain session_id (legacy)
                    if content.startswith('{'):
                        import json as _json
                        data = _json.loads(content)
                        session_id = data.get('session_id', '')
                    else:
                        session_id = content
                    if session_id:
                        cursor.execute("""
                            SELECT session_id, ai_id, start_time
                            FROM sessions
                            WHERE session_id = ? AND end_time IS NULL
                        """, (session_id,))
                        row = cursor.fetchone()
                        if row:
                            return dict(row)
                except Exception:
                    pass
                break  # Found file but session ended - don't keep searching
            if parent == Path.home() or parent == parent.parent:
                break

        # Also check global instance-specific file
        global_instance_file = Path.home() / '.empirica' / f'active_session{instance_suffix}'
        if global_instance_file.exists():
            try:
                content = global_instance_file.read_text().strip()
                # Handle JSON format (new) or plain session_id (legacy)
                if content.startswith('{'):
                    import json as _json
                    data = _json.loads(content)
                    session_id = data.get('session_id', '')
                else:
                    session_id = content
                if session_id:
                    cursor.execute("""
                        SELECT session_id, ai_id, start_time
                        FROM sessions
                        WHERE session_id = ? AND end_time IS NULL
                    """, (session_id,))
                    row = cursor.fetchone()
                    if row:
                        return dict(row)
            except Exception:
                pass
    else:
        # No instance_id - use generic file (legacy mode)
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            candidate = parent / '.empirica' / 'active_session'
            if candidate.exists():
                try:
                    content = candidate.read_text().strip()
                    # Handle JSON format (new) or plain session_id (legacy)
                    if content.startswith('{'):
                        import json as _json
                        data = _json.loads(content)
                        session_id = data.get('session_id', '')
                    else:
                        session_id = content
                    if session_id:
                        cursor.execute("""
                            SELECT session_id, ai_id, start_time
                            FROM sessions
                            WHERE session_id = ? AND end_time IS NULL
                        """, (session_id,))
                        row = cursor.fetchone()
                        if row:
                            return dict(row)
                except Exception:
                    pass
                break
            if parent == Path.home() or parent == parent.parent:
                break

    # Priority 2: Exact ai_id + STRICT instance_id match (no NULL fallback)
    if current_instance_id:
        cursor.execute("""
            SELECT session_id, ai_id, start_time
            FROM sessions
            WHERE end_time IS NULL AND ai_id = ?
              AND instance_id = ?
            ORDER BY start_time DESC
            LIMIT 1
        """, (ai_id, current_instance_id))
        row = cursor.fetchone()
        if row:
            return dict(row)
    else:
        # No instance isolation available - match any for this ai_id
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

    return None


def get_latest_vectors(db: SessionDatabase, session_id: str, transaction_session_id: str = None, transaction_id: str = None) -> tuple:
    """
    Get latest vectors, phase, and gate decision from reflexes table.

    Args:
        db: Database connection
        session_id: Current session ID (for cache compatibility)
        transaction_session_id: The session ID where PREFLIGHT was submitted (survives compaction)
                               If provided, queries this session for vectors instead
        transaction_id: The specific transaction ID to filter by (for multi-instance isolation)
                       CRITICAL: Without this, shared sessions show wrong phase across instances

    This enables cross-session vector lookup when transactions span compaction boundaries.
    """
    cursor = db.conn.cursor()
    # Use transaction's session_id if available (survives compaction)
    lookup_session_id = transaction_session_id or session_id

    # CRITICAL: Filter by transaction_id to prevent cross-instance bleed
    # Without this, two Claudes sharing a session see each other's phases
    if transaction_id:
        cursor.execute("""
            SELECT phase, engagement, know, do, context,
                   clarity, coherence, signal, density,
                   state, change, completion, impact, uncertainty,
                   reflex_data
            FROM reflexes
            WHERE session_id = ? AND transaction_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (lookup_session_id, transaction_id))
    else:
        cursor.execute("""
            SELECT phase, engagement, know, do, context,
                   clarity, coherence, signal, density,
                   state, change, completion, impact, uncertainty,
                   reflex_data
            FROM reflexes
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (lookup_session_id,))
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


def format_statusline(
    session: dict,
    phase: str,
    vectors: dict,
    deltas: dict = None,
    mode: str = 'default',
    gate_decision: str = None,
    goal: dict = None,
    open_counts: dict = None,
    project_name: str = None,
    extensions: dict = None
) -> str:
    """Format the statusline based on mode."""

    # Calculate confidence score
    confidence = calculate_confidence(vectors)
    conf_str = format_confidence(confidence)

    # Show project name instead of generic "empirica" branding
    # Truncate long names to keep statusline compact
    label = project_name or 'empirica'
    if len(label) > 20:
        label = label[:18] + '..'

    parts = [f"{Colors.GREEN}[{label}]{Colors.RESET} {conf_str}"]

    # Add extension indicators (CRM, WORKSPACE) if present
    if extensions:
        ext_str = format_extension_indicators(extensions)
        if ext_str:
            parts.append(ext_str)

    if mode == 'basic':
        # Just confidence
        return ' '.join(parts)

    elif mode == 'default':
        # Open counts (goals/unknowns to close) + CASCADE gate + key vectors (%) + deltas
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

        # Add deltas only on POSTFLIGHT (deltas measure PREFLIGHT→POSTFLIGHT change)
        if phase == 'POSTFLIGHT' and deltas:
            delta_str = format_deltas(deltas)
            if delta_str:
                parts.append(f"Δ {delta_str}")

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

        # Show deltas only on POSTFLIGHT (deltas measure PREFLIGHT→POSTFLIGHT change)
        if phase == 'POSTFLIGHT' and deltas:
            delta_str = format_deltas(deltas)
            if delta_str:
                parts.append(f"Δ {delta_str}")

        return ' │ '.join(parts)

    else:  # full
        # Everything (for developers/debugging)
        ai_id = session.get('ai_id', 'unknown')
        session_id = session.get('session_id', '????')[:4]
        parts = [f"{Colors.BRIGHT_CYAN}[{label}:{ai_id}@{session_id}]{Colors.RESET}"]

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

        # Show deltas only on POSTFLIGHT (deltas measure PREFLIGHT→POSTFLIGHT change)
        if phase == 'POSTFLIGHT' and deltas:
            delta_str = format_deltas(deltas)
            if delta_str:
                parts.append(f"Δ {delta_str}")

        return ' │ '.join(parts)


def build_statusline_data(
    session: dict,
    phase: str,
    vectors: dict,
    deltas: dict = None,
    gate_decision: str = None,
    goal: dict = None,
    open_counts: dict = None,
    project_name: str = None,
    project_path: str = None,
    extensions: dict = None,
    ai_id: str = None,
) -> dict:
    """
    Build structured statusline data for JSON output.

    This enables TUI/GUI dashboards to consume statusline state.

    Returns:
        {
            'project': {'name': str, 'path': str},
            'session': {'id': str, 'ai_id': str},
            'epistemic': {'phase': str, 'vectors': dict, 'deltas': dict, 'confidence': float},
            'goals': {'open': int, 'completion': float},
            'unknowns': {'open': int, 'blockers': int},
            'gate': {'decision': str},
            'extensions': {'crm': {...}, 'workspace': {...}},
            'timestamp': float,
        }
    """
    import time

    confidence = calculate_confidence(vectors) if vectors else 0.0

    return {
        'project': {
            'name': project_name,
            'path': project_path,
        },
        'session': {
            'id': session.get('session_id') if session else None,
            'ai_id': ai_id or (session.get('ai_id') if session else None),
        },
        'epistemic': {
            'phase': phase,
            'vectors': vectors or {},
            'deltas': deltas or {},
            'confidence': confidence,
        },
        'goals': {
            'open': open_counts.get('open_goals', 0) if open_counts else 0,
            'active': goal.get('objective') if goal else None,
            'completion': open_counts.get('completion', 0.0) if open_counts else 0.0,
        },
        'unknowns': {
            'open': open_counts.get('open_unknowns', 0) if open_counts else 0,
            'blockers': open_counts.get('goal_linked_unknowns', 0) if open_counts else 0,
        },
        'gate': {
            'decision': gate_decision,
        },
        'extensions': extensions or {},
        'timestamp': time.time(),
    }


def format_tmux_statusline(confidence: float, phase: str) -> str:
    """
    Format a super-compact statusline for tmux status-right.

    Target: ~20 characters max for tmux status bar
    Format: "E:💡63% PRE"
    """
    pct = int(confidence * 100) if confidence else 0

    # Confidence emoji (no ANSI colors for tmux)
    if confidence >= 0.75:
        emoji = "⚡"
    elif confidence >= 0.50:
        emoji = "💡"
    elif confidence >= 0.35:
        emoji = "💫"
    else:
        emoji = "🌑"

    # Phase abbreviation
    phase_abbrev = {
        'PREFLIGHT': 'PRE',
        'CHECK': 'CHK',
        'POSTFLIGHT': 'POST',
        'INVESTIGATE': 'INV',
    }.get(phase, phase[:3] if phase else '---')

    return f"E:{emoji}{pct}% {phase_abbrev}"


def main():
    """Main statusline generation."""
    try:
        mode = os.getenv('EMPIRICA_STATUS_MODE', 'default').lower()
        output_json = '--json' in sys.argv or os.getenv('EMPIRICA_STATUS_JSON', '').lower() == 'true'
        output_tmux = '--tmux' in sys.argv or os.getenv('EMPIRICA_STATUS_TMUX', '').lower() == 'true'
        ai_id = get_ai_id()

        # OFF-RECORD CHECK: If Empirica is paused, show collapsed statusline
        pause_file = Path.home() / '.empirica' / 'sentinel_paused'
        if pause_file.exists():
            try:
                import json as _json
                import time as _time
                pause_data = _json.loads(pause_file.read_text())
                paused_at = pause_data.get('paused_at', 0)
                gap_minutes = int((_time.time() - paused_at) / 60) if paused_at else 0
                gap_str = f"{gap_minutes}m" if gap_minutes < 60 else f"{gap_minutes // 60}h{gap_minutes % 60}m"
                print(f"{Colors.GRAY}[empirica]{Colors.RESET} {Colors.YELLOW}OFF-RECORD{Colors.RESET} {Colors.GRAY}({gap_str}){Colors.RESET}")
            except Exception:
                print(f"{Colors.GRAY}[empirica]{Colors.RESET} {Colors.YELLOW}OFF-RECORD{Colors.RESET}")
            return

        # Read Claude Code stdin context (JSON with session_id, cwd, workspace, etc.)
        # This is the primary session resolution method in non-tmux environments
        stdin_context = {}
        stdin_claude_session_id = None
        try:
            import select
            import json as _json
            if not sys.stdin.isatty():
                ready, _, _ = select.select([sys.stdin], [], [], 0.1)
                if ready:
                    raw = sys.stdin.read()
                    if raw and raw.strip():
                        stdin_context = _json.loads(raw.strip())
                        stdin_claude_session_id = stdin_context.get('session_id')
        except Exception:
            pass

        # Auto-detect project from active context
        # Priority: 0) stdin Claude session → active_work file, 1) EMPIRICA_PROJECT_PATH env var,
        #           2) TTY session (needs TMUX_PANE), 3) path_resolver, 4) manual upward search
        # NOTE: We do NOT fall back to global ~/.empirica/ to prevent cross-project data leakage
        project_path = None
        is_local_project = False

        # Priority 0: Claude session_id from stdin → active_work file → project_path
        if stdin_claude_session_id:
            try:
                import json as _json
                active_work_path = Path.home() / '.empirica' / f'active_work_{stdin_claude_session_id}.json'
                if active_work_path.exists():
                    with open(active_work_path, 'r') as f:
                        active_work = _json.load(f)
                    aw_project_path = active_work.get('project_path')
                    if aw_project_path:
                        aw_db = Path(aw_project_path) / '.empirica' / 'sessions' / 'sessions.db'
                        if aw_db.exists():
                            project_path = aw_project_path
                            is_local_project = True
            except Exception:
                pass

        # Priority 1: EMPIRICA_PROJECT_PATH env var
        if not project_path:
            project_path = os.getenv('EMPIRICA_PROJECT_PATH')

        # Priority 2: Check TTY session for project-switch context
        # TTY session has project_path directly from session_create/project_switch
        if not project_path:
            try:
                from empirica.utils.session_resolver import get_tty_session

                tty_session = get_tty_session(warn_if_stale=False)
                if tty_session:
                    # Use project_path directly from TTY session (most reliable)
                    tty_project_path = tty_session.get('project_path')
                    if tty_project_path:
                        tty_db = Path(tty_project_path) / '.empirica' / 'sessions' / 'sessions.db'
                        if tty_db.exists():
                            project_path = tty_project_path
                            is_local_project = True
            except Exception:
                pass  # Fall through to other methods

        # Priority 3: Try canonical path_resolver (same logic as sentinel-gate.py)
        if not project_path:
            try:
                from empirica.config.path_resolver import get_empirica_root
                empirica_root = get_empirica_root()
                if empirica_root and empirica_root.exists():
                    db_candidate = empirica_root / 'sessions' / 'sessions.db'
                    if db_candidate.exists():
                        project_path = str(empirica_root.parent)
                        is_local_project = True
            except (ImportError, Exception):
                pass

        if not project_path:
            # Fallback: Search UPWARD for .empirica/ like git does for .git/
            current = Path.cwd()
            for parent in [current] + list(current.parents):
                candidate_db = parent / '.empirica' / 'sessions' / 'sessions.db'
                if candidate_db.exists():
                    project_path = str(parent)
                    is_local_project = True
                    break
                if parent == Path.home() or parent == parent.parent:
                    break

        if project_path:
            db_path = Path(project_path) / '.empirica' / 'sessions' / 'sessions.db'
            db = SessionDatabase(db_path=str(db_path))
            is_local_project = True
        else:
            # No local .empirica/ found - show "no project" instead of using global data
            # This prevents showing Empirica project data in unrelated projects
            print(f"{Colors.GRAY}[no project]{Colors.RESET}")
            return

        session = get_active_session(db, ai_id, stdin_claude_session_id=stdin_claude_session_id)

        # Get project_id and project_name from session for filtering and display
        project_id = None
        project_name = None
        if session:
            cursor = db.conn.cursor()
            cursor.execute("SELECT project_id FROM sessions WHERE session_id = ?", (session['session_id'],))
            row = cursor.fetchone()
            if row and row[0]:
                project_id = row[0]
                cursor.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
                prow = cursor.fetchone()
                if prow:
                    project_name = prow[0]

        # If no session yet, still try to get project name from the most recent session
        if not project_name:
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT p.name FROM projects p
                JOIN sessions s ON s.project_id = p.id
                ORDER BY s.start_time DESC LIMIT 1
            """)
            prow = cursor.fetchone()
            if prow:
                project_name = prow[0]

        if not session:
            # No active session - show project name so user knows which pane this is
            label = project_name or ai_id
            if len(label) > 20:
                label = label[:18] + '..'
            print(f"{Colors.GRAY}[{label}:inactive]{Colors.RESET}")
            db.close()
            return

        session_id = session['session_id']

        # TRANSACTION AWARENESS: Read instance-specific active_transaction file
        # IMPORTANT: Uses instance suffix for multi-instance isolation (tmux panes)
        # The file is named active_transaction_{instance_id}.json, not active_transaction.json
        transaction_session_id = None
        transaction_id = None
        try:
            from empirica.core.statusline_cache import get_instance_id as _get_instance_id
            instance_id = _get_instance_id()
            # Build instance-aware filename
            suffix = f"_{instance_id}" if instance_id else ""
            if project_path:
                tx_path = Path(project_path) / '.empirica' / f'active_transaction{suffix}.json'
            else:
                tx_path = Path.home() / '.empirica' / f'active_transaction{suffix}.json'
            if tx_path and tx_path.exists():
                import json as _json
                with open(tx_path, 'r') as f:
                    tx_data = _json.load(f)
                # Only use transaction data if status is "open" (active transaction)
                # If closed, fall back to current session_id
                if tx_data.get('status') == 'open':
                    transaction_session_id = tx_data.get('session_id')
                    transaction_id = tx_data.get('transaction_id')  # CRITICAL for instance isolation
        except Exception:
            pass  # Fall back to current session_id

        # Get vectors from DB (real-time) - use transaction's session_id and transaction_id
        # transaction_id is CRITICAL to prevent cross-instance phase bleed
        phase, vectors, gate_decision = get_latest_vectors(db, session_id, transaction_session_id, transaction_id)

        # Get deltas (learning measurement) - use transaction's session for continuity
        deltas = get_vector_deltas(db, transaction_session_id or session_id)

        # Get active goal for this session (used in 'full' mode)
        goal = get_active_goal(db, session_id)

        # Get open counts (goals/unknowns to close) - used in default/learning modes
        # Pass project_id to filter by THIS project only
        open_counts = get_open_counts(db, session_id, project_id=project_id)

        db.close()

        # Detect extensions (CRM, WORKSPACE)
        extensions = detect_extensions()

        # JSON output for dashboards
        if output_json:
            import json
            data = build_statusline_data(
                session, phase, vectors, deltas,
                gate_decision=gate_decision, goal=goal, open_counts=open_counts,
                project_name=project_name, project_path=project_path,
                extensions=extensions, ai_id=ai_id,
            )
            print(json.dumps(data, indent=2))
            return

        # Compact tmux output (for tmux status-right)
        if output_tmux:
            confidence = calculate_confidence(vectors) if vectors else 0.0
            print(format_tmux_statusline(confidence, phase))
            return

        # Format and output
        output = format_statusline(
            session, phase, vectors, deltas, mode,
            gate_decision=gate_decision, goal=goal, open_counts=open_counts,
            project_name=project_name, extensions=extensions
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
