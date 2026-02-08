"""Session repository for session CRUD operations"""
import sqlite3
import uuid
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
from .base import BaseRepository

logger = logging.getLogger(__name__)


def _register_session_globally(
    session_id: str,
    ai_id: str,
    project_id: Optional[str],
    instance_id: Optional[str],
    parent_session_id: Optional[str] = None
) -> bool:
    """
    Register session in global_sessions table (workspace.db).

    This enables cross-project session tracking. Sessions are now global
    (one per Claude conversation), not per-project.

    Returns True if registered, False on error (non-fatal).
    """
    try:
        workspace_db = Path.home() / '.empirica' / 'workspace' / 'workspace.db'
        if not workspace_db.exists():
            logger.debug("No workspace.db - skipping global session registration")
            return False

        conn = sqlite3.connect(str(workspace_db))
        cursor = conn.cursor()

        # Check if table exists (graceful degradation for older workspaces)
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='global_sessions'
        """)
        if not cursor.fetchone():
            logger.debug("global_sessions table not found - skipping registration")
            conn.close()
            return False

        # Insert or update (in case of re-registration)
        cursor.execute("""
            INSERT INTO global_sessions
            (session_id, ai_id, origin_project_id, current_project_id,
             instance_id, status, created_at, parent_session_id)
            VALUES (?, ?, ?, ?, ?, 'active', ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                current_project_id = excluded.current_project_id,
                last_activity = excluded.created_at
        """, (
            session_id, ai_id, project_id, project_id,
            instance_id, time.time(), parent_session_id
        ))

        conn.commit()
        conn.close()
        logger.debug(f"Registered session {session_id[:8]}... in global registry")
        return True

    except Exception as e:
        logger.warning(f"Failed to register session globally: {e}")
        return False


def update_session_project(session_id: str, project_id: str) -> bool:
    """
    Update current_project_id for a session in global registry.

    Called by project-switch to track which project a session is currently working on.

    Returns True if updated, False on error.
    """
    try:
        workspace_db = Path.home() / '.empirica' / 'workspace' / 'workspace.db'
        if not workspace_db.exists():
            return False

        conn = sqlite3.connect(str(workspace_db))
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE global_sessions
            SET current_project_id = ?, last_activity = ?
            WHERE session_id = ?
        """, (project_id, time.time(), session_id))

        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()

        if updated:
            logger.debug(f"Updated session {session_id[:8]}... to project {project_id[:8]}...")
        return updated

    except Exception as e:
        logger.warning(f"Failed to update session project: {e}")
        return False


class SessionRepository(BaseRepository):
    """Handles session-related database operations"""

    def create_session(
        self,
        ai_id: str,
        components_loaded: int = 0,
        user_id: Optional[str] = None,
        subject: Optional[str] = None,
        bootstrap_level: int = 1,
        instance_id: Optional[str] = None,
        parent_session_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> str:
        """
        Create a new session

        Args:
            ai_id: AI identifier (e.g., "claude-sonnet-3.5")
            components_loaded: Number of pre-loaded components
            user_id: Optional user identifier
            subject: Optional subject/topic for filtering
            bootstrap_level: Bootstrap configuration level (1-3, default 1)
            instance_id: Optional instance identifier for multi-instance isolation.
                         If None, auto-detected from environment (TMUX_PANE, etc.)
            parent_session_id: Optional parent session UUID for sub-agent lineage.
                               Links child sessions back to the spawning session.
            project_id: Optional project UUID for global registry

        Returns:
            session_id: UUID string
        """
        # Auto-detect instance_id if not provided
        if instance_id is None:
            from empirica.utils.session_resolver import get_instance_id
            instance_id = get_instance_id()

        session_id = str(uuid.uuid4())
        cursor = self._execute("""
            INSERT INTO sessions (
                session_id, ai_id, user_id, start_time, components_loaded,
                subject, bootstrap_level, instance_id, parent_session_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, ai_id, user_id, datetime.now(timezone.utc).isoformat(),
            components_loaded, subject, bootstrap_level, instance_id, parent_session_id
        ))

        # Register in global sessions registry (workspace.db)
        # This enables cross-project session tracking
        _register_session_globally(
            session_id=session_id,
            ai_id=ai_id,
            project_id=project_id,
            instance_id=instance_id,
            parent_session_id=parent_session_id
        )

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data by ID"""
        cursor = self._execute(
            "SELECT * FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_sessions(
        self,
        ai_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        List all sessions, optionally filtered by ai_id

        Args:
            ai_id: Optional AI identifier to filter by
            limit: Maximum number of sessions to return

        Returns:
            List of session dictionaries
        """
        if ai_id:
            cursor = self._execute("""
                SELECT * FROM sessions
                WHERE ai_id = ?
                ORDER BY start_time DESC
                LIMIT ?
            """, (ai_id, limit))
        else:
            cursor = self._execute("""
                SELECT * FROM sessions
                ORDER BY start_time DESC
                LIMIT ?
            """, (limit,))

        return [dict(row) for row in cursor.fetchall()]

    def get_session_cascades(self, session_id: str) -> List[Dict]:
        """Get all cascades for a session"""
        cursor = self._execute("""
            SELECT * FROM cascades
            WHERE session_id = ?
            ORDER BY started_at
        """, (session_id,))
        return [dict(row) for row in cursor.fetchall()]

    def end_session(
        self,
        session_id: str,
        avg_confidence: Optional[float] = None,
        drift_detected: bool = False,
        notes: Optional[str] = None
    ):
        """
        End a session and record summary stats

        Args:
            session_id: Session UUID
            avg_confidence: Average confidence across all cascades
            drift_detected: Whether drift was detected during session
            notes: Session notes
        """
        self._execute("""
            UPDATE sessions
            SET end_time = ?,
                avg_confidence = ?,
                drift_detected = ?,
                session_notes = ?
            WHERE session_id = ?
        """, (
            datetime.utcnow().isoformat(),
            avg_confidence,
            drift_detected,
            notes,
            session_id
        ))

    def get_latest_session(
        self,
        ai_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get the most recent session, optionally filtered by AI or project

        Args:
            ai_id: Optional AI identifier
            project_id: Optional project UUID

        Returns:
            Session dict or None
        """
        conditions = []
        params = []

        if ai_id:
            conditions.append("ai_id = ?")
            params.append(ai_id)

        if project_id:
            conditions.append("project_id = ?")
            params.append(project_id)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        cursor = self._execute(f"""
            SELECT * FROM sessions
            WHERE {where_clause}
            ORDER BY start_time DESC
            LIMIT 1
        """, tuple(params))

        row = cursor.fetchone()
        return dict(row) if row else None

    def get_child_sessions(self, parent_session_id: str) -> List[Dict]:
        """
        Get all child sessions spawned by a parent session.

        Args:
            parent_session_id: Parent session UUID

        Returns:
            List of child session dictionaries, ordered by start_time
        """
        cursor = self._execute("""
            SELECT * FROM sessions
            WHERE parent_session_id = ?
            ORDER BY start_time ASC
        """, (parent_session_id,))
        return [dict(row) for row in cursor.fetchall()]

    def get_session_summary(self, session_id: str, detail_level: str = "summary") -> Optional[Dict]:
        """
        Generate comprehensive session summary for resume/handoff

        Args:
            session_id: Session to summarize
            detail_level: 'summary', 'detailed', or 'full'

        Returns:
            Dictionary with session metadata, epistemic delta, accomplishments, etc.
        """
        # Get session metadata
        session = self.get_session(session_id)
        if not session:
            return None

        # Get cascades
        cascades = self.get_session_cascades(session_id)

        # Get PREFLIGHT/POSTFLIGHT from unified reflexes table instead of legacy cascade_metadata
        cursor = self._execute("""
            SELECT phase, json_extract(reflex_data, '$.vectors'), cascade_id, timestamp
            FROM reflexes
            WHERE session_id = ?
            AND phase IN ('PREFLIGHT', 'POSTFLIGHT')
            ORDER BY timestamp
        """, (session_id,))

        assessments = {}
        cascade_tasks = {}
        for row in cursor.fetchall():
            phase, vectors_json, cascade_id, timestamp = row
            if vectors_json:
                # Convert phase to the expected key format
                key = f"{phase.lower()}_vectors"
                assessments[key] = json.loads(vectors_json)
                # We don't have the task from reflexes, so we'll get it from cascades
                cascade_cursor = self._execute("SELECT task FROM cascades WHERE cascade_id = ?", (cascade_id,))
                cascade_row = cascade_cursor.fetchone()
                if cascade_row:
                    cascade_tasks[cascade_id] = cascade_row[0]

        # Get investigation tools used (if detailed)
        # Note: noetic_tools table was designed but never wired up
        tools_used = []
        if detail_level in ['detailed', 'full']:
            try:
                cursor = self._execute("""
                    SELECT tool_name, COUNT(*) as count
                    FROM noetic_tools
                    WHERE cascade_id IN (
                        SELECT cascade_id FROM cascades WHERE session_id = ?
                    )
                    GROUP BY tool_name
                    ORDER BY count DESC
                    LIMIT 10
                """, (session_id,))
                tools_used = [{"tool": row[0], "count": row[1]} for row in cursor.fetchall()]
            except Exception:
                # Table doesn't exist yet - feature not implemented
                tools_used = []

        # Calculate epistemic delta
        delta = None
        if 'preflight_vectors' in assessments and 'postflight_vectors' in assessments:
            pre = assessments['preflight_vectors']
            post = assessments['postflight_vectors']
            delta = {key: post.get(key, 0.5) - pre.get(key, 0.5) for key in post}

        return {
            'session_id': session_id,
            'ai_id': session['ai_id'],
            'start_time': session['start_time'],
            'end_time': session.get('end_time'),
            'total_cascades': len(cascades),
            'cascades': cascades if detail_level == 'full' else [c['task'] for c in cascades],
            'preflight': assessments.get('preflight_vectors'),
            'postflight': assessments.get('postflight_vectors'),
            'epistemic_delta': delta,
            'tools_used': tools_used,
            'avg_confidence': session.get('avg_confidence')
        }
