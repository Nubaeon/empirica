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
    format_drift_compact,
    get_drift_level,
    detect_sentinel_action,
    read_drift_cache,
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


def get_active_session(db: SessionDatabase, ai_id: str) -> dict:
    """Get the active session for this AI."""
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT session_id, ai_id, start_time
        FROM sessions
        WHERE end_time IS NULL AND ai_id = ?
        ORDER BY start_time DESC
        LIMIT 1
    """, (ai_id,))
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


def format_statusline(
    session: dict,
    phase: str,
    vectors: dict,
    drift_state: SignalingState,
    mode: str = 'default'
) -> str:
    """Format the statusline based on mode."""

    parts = [f"{Colors.GREEN}[empirica]{Colors.RESET}"]

    if mode == 'basic':
        # Just drift
        if drift_state and drift_state.drift_score is not None:
            parts.append(drift_state.format_basic())
        else:
            parts.append("🌑 No drift data")
        return ' '.join(parts)

    elif mode == 'default':
        # Phase + key vectors + drift
        if phase:
            parts.append(f"{Colors.BLUE}{phase}{Colors.RESET}")

        if vectors:
            vec_str = format_vectors_compact(vectors, show_values=False)
            parts.append(vec_str)

        if drift_state and drift_state.drift_score is not None:
            drift_str = format_drift_compact(
                drift_state.drift_score,
                drift_state.sentinel_action
            )
            parts.append(drift_str)

        return ' │ '.join(parts)

    elif mode == 'learning':
        # Focus on vectors with values
        if phase:
            parts.append(f"{phase}")

        if vectors:
            # Show more vectors with values
            all_keys = ['know', 'uncertainty', 'context', 'clarity', 'completion']
            vec_str = format_vectors_compact(vectors, keys=all_keys, show_values=True)
            parts.append(vec_str)

        if drift_state and drift_state.drift_score is not None:
            parts.append(drift_state.format_basic())

        return ' │ '.join(parts)

    else:  # full
        # Everything
        ai_id = session.get('ai_id', 'unknown')
        session_id = session.get('session_id', '????')[:4]
        parts = [f"{Colors.BRIGHT_CYAN}[empirica:{ai_id}@{session_id}]{Colors.RESET}"]

        if phase:
            parts.append(f"{Colors.BLUE}{phase}{Colors.RESET}")

        if vectors:
            all_keys = ['know', 'uncertainty', 'context', 'clarity', 'engagement', 'completion', 'impact']
            vec_str = format_vectors_compact(vectors, keys=all_keys, show_values=True)
            parts.append(vec_str)

        if drift_state:
            parts.append(drift_state.format_basic())

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

        # Get drift from cache (updated by hooks)
        drift_state = read_drift_cache(str(Path.cwd()))

        # If no cached drift, create minimal state from vectors
        if not drift_state and vectors:
            drift_state = SignalingState(
                phase=phase,
                vectors=vectors,
                session_id=session_id,
                ai_id=ai_id
            )

        # Format and output
        output = format_statusline(session, phase, vectors, drift_state, mode)
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
