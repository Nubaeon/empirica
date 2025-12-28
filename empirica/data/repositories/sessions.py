"""Session repository for session CRUD operations"""
import sqlite3
import uuid
import json
from typing import Dict, List, Optional
from datetime import datetime
from .base import BaseRepository


class SessionRepository(BaseRepository):
    """Handles session-related database operations"""

    def create_session(
        self,
        ai_id: str,
        components_loaded: int = 0,
        user_id: Optional[str] = None,
        subject: Optional[str] = None,
        bootstrap_level: int = 1
    ) -> str:
        """
        Create a new session

        Args:
            ai_id: AI identifier (e.g., "claude-sonnet-3.5")
            components_loaded: Number of pre-loaded components
            user_id: Optional user identifier
            subject: Optional subject/topic for filtering
            bootstrap_level: Bootstrap configuration level (1-3, default 1)

        Returns:
            session_id: UUID string
        """
        session_id = str(uuid.uuid4())
        cursor = self._execute("""
            INSERT INTO sessions (
                session_id, ai_id, user_id, start_time, components_loaded, subject, bootstrap_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, ai_id, user_id, datetime.utcnow().isoformat(),
            components_loaded, subject, bootstrap_level
        ))
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
        tools_used = []
        if detail_level in ['detailed', 'full']:
            cursor = self._execute("""
                SELECT tool_name, COUNT(*) as count
                FROM investigation_tools
                WHERE cascade_id IN (
                    SELECT cascade_id FROM cascades WHERE session_id = ?
                )
                GROUP BY tool_name
                ORDER BY count DESC
                LIMIT 10
            """, (session_id,))
            tools_used = [{"tool": row[0], "count": row[1]} for row in cursor.fetchall()]

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
