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
    CognitivePhase,
    format_vectors_compact,
    format_drift_compact,
    format_drift_status,
    get_drift_level,
    detect_sentinel_action,
    read_drift_cache,
    infer_cognitive_phase,
    infer_cognitive_phase_from_vectors,
    format_cognitive_phase,
    DRIFT_CACHE_PATH,
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
    2. Match exact ai_id
    3. Match ai_id prefix (e.g., 'claude-code' matches 'claude-code-multimachine')
    """
    cursor = db.conn.cursor()

    # Priority 1: Check active_session file
    active_session_file = Path.home() / '.empirica' / 'active_session'
    if active_session_file.exists():
        try:
            session_id = active_session_file.read_text().strip()
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
            pass  # Fall through to other methods

    # Priority 2: Exact ai_id match
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
    """Get latest vectors and phase from reflexes table."""
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT phase, engagement, know, do, context,
               clarity, coherence, signal, density,
               state, change, completion, impact, uncertainty
        FROM reflexes
        WHERE session_id = ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (session_id,))
    row = cursor.fetchone()

    if not row:
        return None, {}

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

    return phase, vectors


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
    drift_severity: str = None
) -> str:
    """Format the statusline based on mode."""

    # Calculate confidence score
    confidence = calculate_confidence(vectors)
    conf_str = format_confidence(confidence)

    # Infer cognitive phase from VECTORS (emergent, not prescribed)
    # This is the Turtle Principle: phase is observed from epistemic state
    cognitive_phase = infer_cognitive_phase_from_vectors(vectors) if vectors else CognitivePhase.NOETIC

    parts = [f"{Colors.GREEN}[empirica]{Colors.RESET} {conf_str}"]

    if mode == 'basic':
        # Just confidence + drift
        drift_str = format_drift_status(drift_detected, drift_severity)
        parts.append(drift_str)
        return ' '.join(parts)

    elif mode == 'default':
        # Cognitive phase (emergent) + CASCADE gate + key vectors (%) + deltas + drift
        cog_str = format_cognitive_phase(cognitive_phase)
        parts.append(cog_str)

        # CASCADE gate (compliance checkpoint) - kept for oversight
        if phase:
            parts.append(f"{Colors.BLUE}{phase}{Colors.RESET}")

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
        # Focus on vectors with values and deltas
        cog_str = format_cognitive_phase(cognitive_phase, use_color=False)
        parts.append(cog_str)

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
        # Everything
        ai_id = session.get('ai_id', 'unknown')
        session_id = session.get('session_id', '????')[:4]
        parts = [f"{Colors.BRIGHT_CYAN}[empirica:{ai_id}@{session_id}]{Colors.RESET}"]

        if cognitive_phase:
            cog_str = format_cognitive_phase(cognitive_phase)
            parts.append(cog_str)

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

        db = SessionDatabase()
        session = get_active_session(db, ai_id)

        if not session:
            print(f"{Colors.GRAY}[empirica:{ai_id}:inactive]{Colors.RESET}")
            return

        session_id = session['session_id']

        # Get vectors from DB (real-time)
        phase, vectors = get_latest_vectors(db, session_id)

        # Get deltas (learning measurement)
        deltas = get_vector_deltas(db, session_id)

        # Check drift from DB (compare recent reflexes)
        drift_detected, drift_severity = get_drift_from_db(db, session_id)

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
            drift_detected=drift_detected, drift_severity=drift_severity
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
