#!/usr/bin/env python3
"""
Empirica Session End Hook - Auto-captures POSTFLIGHT

This hook runs when a session ends and automatically captures a POSTFLIGHT
assessment based on the session's final state. Since the AI can't respond
after session end, this uses the last known vectors to complete the
PREFLIGHT→POSTFLIGHT cycle.

This ensures the learning delta is always captured, even if the AI didn't
explicitly run POSTFLIGHT.
"""

import json
import sys
import subprocess
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path.home() / 'empirical-ai' / 'empirica'))


def find_project_root() -> Path:
    """Find Empirica project root."""
    def has_valid_db(path: Path) -> bool:
        db_path = path / '.empirica' / 'sessions' / 'sessions.db'
        return db_path.exists() and db_path.stat().st_size > 0

    if workspace_root := os.getenv('EMPIRICA_WORKSPACE_ROOT'):
        workspace_path = Path(workspace_root).expanduser().resolve()
        if has_valid_db(workspace_path):
            return workspace_path

    known_paths = [
        Path.home() / 'empirical-ai' / 'empirica',
        Path.home() / 'empirica',
    ]
    for path in known_paths:
        if has_valid_db(path):
            return path

    return Path.cwd()


def get_session_state(session_id: str) -> dict:
    """
    Get session's epistemic state for POSTFLIGHT.

    Returns:
        {
            "has_preflight": bool,
            "has_postflight": bool,
            "last_vectors": dict or None,
            "last_phase": str,
            "needs_postflight": bool
        }
    """
    try:
        from empirica.data.session_database import SessionDatabase
        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Get all reflexes for session
        cursor.execute("""
            SELECT phase, engagement, know, do, context,
                   clarity, coherence, signal, density,
                   state, change, completion, impact, uncertainty,
                   timestamp
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
                "last_vectors": None,
                "last_phase": None,
                "needs_postflight": False
            }

        phases = [r[0] for r in rows]
        has_preflight = 'PREFLIGHT' in phases
        has_postflight = 'POSTFLIGHT' in phases
        last_phase = phases[0] if phases else None

        # Get vectors from most recent entry
        latest = rows[0]
        last_vectors = {
            'engagement': latest[1],
            'know': latest[2],
            'do': latest[3],
            'context': latest[4],
            'clarity': latest[5],
            'coherence': latest[6],
            'signal': latest[7],
            'density': latest[8],
            'state': latest[9],
            'change': latest[10],
            'completion': latest[11],
            'impact': latest[12],
            'uncertainty': latest[13]
        }
        # Filter None values
        last_vectors = {k: v for k, v in last_vectors.items() if v is not None}

        # Needs POSTFLIGHT if has PREFLIGHT but no POSTFLIGHT
        needs_postflight = has_preflight and not has_postflight

        return {
            "has_preflight": has_preflight,
            "has_postflight": has_postflight,
            "last_vectors": last_vectors,
            "last_phase": last_phase,
            "needs_postflight": needs_postflight
        }

    except Exception as e:
        return {
            "has_preflight": False,
            "has_postflight": False,
            "last_vectors": None,
            "last_phase": None,
            "needs_postflight": False,
            "error": str(e)
        }


def auto_postflight(session_id: str, vectors: dict) -> dict:
    """
    Automatically submit POSTFLIGHT with final vectors.

    This completes the PREFLIGHT→POSTFLIGHT cycle so learning delta
    is captured even if AI didn't explicitly call postflight-submit.
    """
    try:
        # Build POSTFLIGHT payload
        payload = {
            "session_id": session_id,
            "vectors": vectors,
            "learnings": ["Session ended - auto-captured POSTFLIGHT"],
            "delta_summary": "Auto-captured at session end"
        }

        # Submit via CLI
        cmd = subprocess.run(
            ['empirica', 'postflight-submit', '-'],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            timeout=15
        )

        if cmd.returncode == 0:
            try:
                return {"ok": True, "output": json.loads(cmd.stdout)}
            except json.JSONDecodeError:
                return {"ok": True, "output": cmd.stdout[:500]}
        else:
            return {"ok": False, "error": cmd.stderr}

    except Exception as e:
        return {"ok": False, "error": str(e)}


def get_active_session() -> str:
    """Get active session ID."""
    try:
        from empirica.utils.session_resolver import get_latest_session_id
        return get_latest_session_id(ai_id='claude-code', active_only=True)
    except:
        return None


def main():
    """Main session end logic."""
    hook_input = {}
    try:
        hook_input = json.loads(sys.stdin.read())
    except:
        pass

    project_root = find_project_root()
    os.chdir(project_root)

    session_id = get_active_session()

    if not session_id:
        output = {
            "ok": True,
            "skipped": True,
            "reason": "No active Empirica session"
        }
        print(json.dumps(output))
        sys.exit(0)

    # Check session state
    state = get_session_state(session_id)

    if not state.get("needs_postflight"):
        reason = "POSTFLIGHT already exists" if state.get("has_postflight") else "No PREFLIGHT found"
        output = {
            "ok": True,
            "skipped": True,
            "reason": reason,
            "session_id": session_id,
            "state": state
        }
        print(json.dumps(output))
        sys.exit(0)

    # Auto-submit POSTFLIGHT
    vectors = state.get("last_vectors", {})

    if not vectors:
        output = {
            "ok": True,
            "skipped": True,
            "reason": "No vectors available for auto-POSTFLIGHT",
            "session_id": session_id
        }
        print(json.dumps(output))
        sys.exit(0)

    # Boost completion since session is ending
    vectors['completion'] = max(vectors.get('completion', 0.5), 0.7)

    result = auto_postflight(session_id, vectors)

    if result.get("ok"):
        print(f"""
📊 Empirica: Auto-POSTFLIGHT captured

Session: {session_id}
Vectors: know={vectors.get('know', 'N/A')}, uncertainty={vectors.get('uncertainty', 'N/A')}
Learning delta will be calculated from PREFLIGHT baseline.
""", file=sys.stderr)

    output = {
        "ok": result.get("ok", False),
        "session_id": session_id,
        "auto_postflight": True,
        "vectors_used": vectors,
        "result": result
    }

    print(json.dumps(output))
    sys.exit(0)


if __name__ == '__main__':
    main()
