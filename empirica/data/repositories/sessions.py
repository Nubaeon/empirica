"""Session repository for session CRUD operations"""
import sqlite3
import uuid
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
        subject: Optional[str] = None
    ) -> str:
        """
        Create a new session

        Args:
            ai_id: AI identifier (e.g., "claude-sonnet-3.5")
            components_loaded: Number of pre-loaded components
            user_id: Optional user identifier
            subject: Optional subject/topic for filtering

        Returns:
            session_id: UUID string
        """
        session_id = str(uuid.uuid4())
        cursor = self._execute("""
            INSERT INTO sessions (
                session_id, ai_id, user_id, start_time, components_loaded, subject
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session_id, ai_id, user_id, datetime.utcnow().isoformat(),
            components_loaded, subject
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
