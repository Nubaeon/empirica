"""
Action Commands - Log implicit INVESTIGATE and ACT phases

These commands track decisions made during work phases for better handoff generation.
Storage: SQLite (cascade context_json) + Git notes (optional)
"""

import json
import logging
import subprocess
import uuid
from datetime import datetime
from ..cli_utils import handle_cli_error, parse_json_safely

logger = logging.getLogger(__name__)


def handle_investigate_log_command(args):
    """
    Log investigation findings during INVESTIGATE phase
    
    Storage: SQLite (cascade context_json) + Git notes (optional)
    """
    try:
        from empirica.data.session_database import SessionDatabase
        
        session_id = args.session_id
        findings = parse_json_safely(args.findings) if isinstance(args.findings, str) else args.findings
        evidence = parse_json_safely(args.evidence) if hasattr(args, 'evidence') and args.evidence else {}
        output_format = getattr(args, 'output', 'text')

        if not isinstance(findings, list):
            raise ValueError("Findings must be a JSON array")

        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Get active cascade
        cursor.execute("""
            SELECT cascade_id, context_json FROM cascades
            WHERE session_id = ? AND completed_at IS NULL
            ORDER BY started_at DESC LIMIT 1
        """, (session_id,))

        result = cursor.fetchone()
        if not result:
            if output_format == 'json':
                print(json.dumps({"ok": False, "error": "No active cascade found"}))
            else:
                print("❌ No active cascade found. Run preflight first.")
            db.close()
            return

        # Extract cascade data
        cascade_id, context_json_str = result
        context = json.loads(context_json_str) if context_json_str else {}

        # Append to investigation log
        context.setdefault("investigation_log", []).append({
            "timestamp": datetime.utcnow().isoformat(),
            "findings": findings,
            "evidence": evidence
        })

        # Save to SQLite
        cursor.execute("""
            UPDATE cascades
            SET context_json = ?, investigate_completed = 1
            WHERE cascade_id = ?
        """, (json.dumps(context), cascade_id))

        db.conn.commit()
        db.close()

        # Optional: Save to git notes
        try:
            note_ref = f"refs/notes/empirica/cascades/{args.session_id}/{cascade_id}"
            note_data = {
                "type": "investigate",
                "findings": findings,
                "evidence": evidence,
                "timestamp": datetime.utcnow().isoformat()
            }
            subprocess.run(
                ['git', 'notes', '--ref', note_ref, 'append', '-m',
                 f"INVESTIGATE: {json.dumps(note_data)}", 'HEAD'],
                capture_output=True,
                timeout=5
            )
        except Exception as e:
            logger.debug(f"Git notes optional: {e}")

        if output_format == 'json':
            print(json.dumps({
                "ok": True,
                "session_id": session_id,
                "cascade_id": cascade_id,
                "findings_count": len(findings),
                "evidence_keys": list(evidence.keys()) if evidence else []
            }))
        else:
            print("✅ Investigation findings logged")
            print(f"   Session: {session_id[:8]}...")
            print(f"   Cascade: {cascade_id[:8]}...")
            print(f"   Findings: {len(findings)}")
            if evidence:
                print(f"   Evidence: {list(evidence.keys())}")

    except Exception as e:
        handle_cli_error(e, "Investigation log", getattr(args, 'verbose', False))


def handle_act_log_command(args):
    """
    Log actions taken during ACT phase
    
    Storage: SQLite (cascade context_json + final_action) + Git notes (optional)
    """
    try:
        from empirica.data.session_database import SessionDatabase
        
        session_id = args.session_id
        actions = parse_json_safely(args.actions) if isinstance(args.actions, str) else args.actions
        artifacts = parse_json_safely(args.artifacts) if hasattr(args, 'artifacts') and args.artifacts else []
        goal_id = getattr(args, 'goal_id', None)
        output_format = getattr(args, 'output', 'text')

        if not isinstance(actions, list):
            raise ValueError("Actions must be a JSON array")

        db = SessionDatabase()
        cursor = db.conn.cursor()

        # Get active cascade
        cursor.execute("""
            SELECT cascade_id, context_json FROM cascades
            WHERE session_id = ? AND completed_at IS NULL
            ORDER BY started_at DESC LIMIT 1
        """, (session_id,))

        result = cursor.fetchone()
        if not result:
            if output_format == 'json':
                print(json.dumps({"ok": False, "error": "No active cascade found"}))
            else:
                print("❌ No active cascade found")
            db.close()
            return
        
        cascade_id, context_json_str = result
        context = json.loads(context_json_str) if context_json_str else {}
        
        # Append to act log
        context.setdefault("act_log", []).append({
            "timestamp": datetime.utcnow().isoformat(),
            "actions": actions,
            "artifacts": artifacts,
            "goal_id": goal_id
        })
        
        # Set final_action
        final_action = "; ".join(actions) if isinstance(actions, list) else actions
        
        # Save to SQLite
        cursor.execute("""
            UPDATE cascades 
            SET context_json = ?, 
                act_completed = 1,
                final_action = ?
            WHERE cascade_id = ?
        """, (json.dumps(context), final_action, cascade_id))
        
        db.conn.commit()
        db.close()
        
        # Optional: Save to git notes
        try:
            note_ref = f"refs/notes/empirica/cascades/{session_id}/{cascade_id}"
            note_data = {
                "type": "act",
                "actions": actions,
                "artifacts": artifacts,
                "goal_id": goal_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            subprocess.run(
                ['git', 'notes', '--ref', note_ref, 'append', '-m',
                 f"ACT: {json.dumps(note_data)}", 'HEAD'],
                capture_output=True,
                timeout=5
            )
        except Exception as e:
            logger.debug(f"Git notes optional: {e}")

        if output_format == 'json':
            print(json.dumps({
                "ok": True,
                "session_id": session_id,
                "cascade_id": cascade_id,
                "actions_count": len(actions) if isinstance(actions, list) else 1,
                "artifacts_count": len(artifacts) if artifacts else 0,
                "goal_id": goal_id
            }))
        else:
            print("✅ Actions logged")
            print(f"   Session: {session_id[:8]}...")
            print(f"   Cascade: {cascade_id[:8]}...")
            print(f"   Actions: {len(actions) if isinstance(actions, list) else 1}")
            if artifacts:
                print(f"   Artifacts: {len(artifacts)}")

    except Exception as e:
        handle_cli_error(e, "Action log", getattr(args, 'verbose', False))
