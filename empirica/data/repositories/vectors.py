"""Vector repository for epistemic vector storage and retrieval"""
import sqlite3
import json
from typing import Dict, List, Optional
from datetime import datetime
from .base import BaseRepository


class VectorRepository(BaseRepository):
    """Handles epistemic vector operations"""

    def store_vectors(
        self,
        session_id: str,
        phase: str,
        vectors: Dict[str, float],
        reasoning: Optional[str] = None,
        cascade_id: Optional[str] = None
    ) -> str:
        """
        Store epistemic vectors in reflexes table

        Args:
            session_id: Session UUID
            phase: CASCADE phase
            vectors: Epistemic vector dict
            reasoning: Optional reasoning text
            cascade_id: Optional cascade UUID

        Returns:
            reflex_id: UUID string
        """
        import uuid
        reflex_id = str(uuid.uuid4())

        self._execute("""
            INSERT INTO reflexes (
                id, session_id, cascade_id, phase, vectors, reasoning, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            reflex_id, session_id, cascade_id, phase.upper(),
            json.dumps(vectors), reasoning, datetime.utcnow().isoformat()
        ))

        return reflex_id

    def get_latest_vectors(
        self,
        session_id: str,
        phase: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get latest epistemic vectors for a session

        Args:
            session_id: Session UUID
            phase: Optional phase filter (PREFLIGHT, CHECK, POSTFLIGHT)

        Returns:
            Dict with vectors and metadata, or None
        """
        if phase:
            cursor = self._execute("""
                SELECT * FROM reflexes
                WHERE session_id = ? AND phase = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (session_id, phase.upper()))
        else:
            cursor = self._execute("""
                SELECT * FROM reflexes
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (session_id,))

        row = cursor.fetchone()
        if not row:
            return None

        result = dict(row)
        # Parse JSON vectors
        if result.get('vectors'):
            result['vectors'] = json.loads(result['vectors'])
        return result

    def get_preflight_vectors(self, session_id: str) -> Optional[Dict[str, float]]:
        """Get PREFLIGHT vectors for session"""
        result = self.get_latest_vectors(session_id, 'PREFLIGHT')
        return result.get('vectors') if result else None

    def get_check_vectors(self, session_id: str) -> Optional[Dict[str, float]]:
        """Get CHECK vectors for session"""
        result = self.get_latest_vectors(session_id, 'CHECK')
        return result.get('vectors') if result else None

    def get_postflight_vectors(self, session_id: str) -> Optional[Dict[str, float]]:
        """Get POSTFLIGHT vectors for session"""
        result = self.get_latest_vectors(session_id, 'POSTFLIGHT')
        return result.get('vectors') if result else None

    def get_vectors_by_phase(
        self,
        session_id: str,
        phase: str
    ) -> List[Dict]:
        """
        Get all vectors for a specific phase

        Args:
            session_id: Session UUID
            phase: CASCADE phase

        Returns:
            List of vector records
        """
        cursor = self._execute("""
            SELECT * FROM reflexes
            WHERE session_id = ? AND phase = ?
            ORDER BY created_at
        """, (session_id, phase.upper()))

        results = []
        for row in cursor.fetchall():
            result = dict(row)
            if result.get('vectors'):
                result['vectors'] = json.loads(result['vectors'])
            results.append(result)
        return results

    def get_session_vector_history(self, session_id: str) -> List[Dict]:
        """
        Get complete vector history for a session

        Args:
            session_id: Session UUID

        Returns:
            List of all vector records
        """
        cursor = self._execute("""
            SELECT * FROM reflexes
            WHERE session_id = ?
            ORDER BY created_at
        """, (session_id,))

        results = []
        for row in cursor.fetchall():
            result = dict(row)
            if result.get('vectors'):
                result['vectors'] = json.loads(result['vectors'])
            results.append(result)
        return results
