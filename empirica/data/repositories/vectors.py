"""Vector repository for epistemic vector storage and retrieval"""
import json
import time
from typing import Dict, List, Optional
from .base import BaseRepository


class VectorRepository(BaseRepository):
    """Handles epistemic vector operations"""

    def store_vectors(
        self,
        session_id: str,
        phase: str,
        vectors: Dict[str, float],
        cascade_id: Optional[str] = None,
        round_num: int = 1,
        metadata: Optional[Dict] = None,
        reasoning: Optional[str] = None
    ) -> int:
        """
        Store epistemic vectors in the reflexes table

        Args:
            session_id: Session identifier
            phase: Current phase (PREFLIGHT, CHECK, ACT, POSTFLIGHT)
            vectors: Dictionary of 13 epistemic vectors
            cascade_id: Optional cascade identifier
            round_num: Current round number
            metadata: Optional additional metadata
            reasoning: Optional reasoning text

        Returns:
            Row ID of the inserted record
        """
        # Extract the 13 vectors, providing default values if not present
        vector_names = [
            'engagement', 'know', 'do', 'context',
            'clarity', 'coherence', 'signal', 'density',
            'state', 'change', 'completion', 'impact', 'uncertainty'
        ]

        vector_values = []
        for name in vector_names:
            value = vectors.get(name, 0.5)  # Default to 0.5 if not provided
            vector_values.append(value if isinstance(value, (int, float)) else 0.5)

        # Create a reflex data entry with optional metadata
        reflex_data = {
            'session_id': session_id,
            'phase': phase,
            'round': round_num,
            'vectors': vectors,
            'timestamp': time.time()
        }

        # Merge in any additional metadata if provided
        if metadata:
            reflex_data.update(metadata)

        cursor = self._execute("""
            INSERT INTO reflexes (
                session_id, cascade_id, phase, round, timestamp,
                engagement, know, do, context,
                clarity, coherence, signal, density,
                state, change, completion, impact, uncertainty,
                reflex_data, reasoning
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, cascade_id, phase, round_num, time.time(),
            *vector_values,  # Unpack the 13 vector values
            json.dumps(reflex_data),
            reasoning
        ))

        self.commit()
        return cursor.lastrowid

    def get_latest_vectors(
        self,
        session_id: str,
        phase: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get the latest epistemic vectors for a session from the reflexes table

        Args:
            session_id: Session identifier
            phase: Optional phase filter

        Returns:
            Dictionary with vectors, metadata, timestamp, etc. or None if not found
        """
        query = """
            SELECT * FROM reflexes
            WHERE session_id = ?
        """
        params = [session_id]

        if phase:
            query += " AND phase = ?"
            params.append(phase)

        query += " ORDER BY timestamp DESC LIMIT 1"

        cursor = self._execute(query, params)
        result = cursor.fetchone()

        if result:
            row_dict = dict(result)

            # Extract the 13 vector values from the result
            vectors = {}
            for vector_name in ['engagement', 'know', 'do', 'context',
                               'clarity', 'coherence', 'signal', 'density',
                               'state', 'change', 'completion', 'impact', 'uncertainty']:
                if vector_name in row_dict:
                    value = row_dict[vector_name]
                    if value is not None:
                        vectors[vector_name] = float(value)

            # Return full data structure
            return {
                'session_id': row_dict['session_id'],
                'cascade_id': row_dict.get('cascade_id'),
                'phase': row_dict['phase'],
                'round': row_dict.get('round', 1),
                'timestamp': row_dict['timestamp'],
                'vectors': vectors,
                'metadata': json.loads(row_dict['reflex_data']) if row_dict.get('reflex_data') else {},
                'reasoning': row_dict.get('reasoning'),
                'evidence': row_dict.get('evidence')
            }

        return None

    def get_preflight_vectors(self, session_id: str) -> Optional[Dict]:
        """Get latest PREFLIGHT vectors for session (convenience method)"""
        return self.get_latest_vectors(session_id, phase="PREFLIGHT")

    def get_check_vectors(self, session_id: str, cycle: Optional[int] = None) -> List[Dict]:
        """Get CHECK phase vectors, optionally filtered by cycle"""
        vectors = self.get_vectors_by_phase(session_id, phase="CHECK")
        if cycle is not None:
            return [v for v in vectors if v.get('round') == cycle]
        return vectors

    def get_postflight_vectors(self, session_id: str) -> Optional[Dict]:
        """Get latest POSTFLIGHT vectors for session (convenience method)"""
        return self.get_latest_vectors(session_id, phase="POSTFLIGHT")

    def get_vectors_by_phase(self, session_id: str, phase: str) -> List[Dict]:
        """Get all vectors for a specific phase"""
        cursor = self._execute("""
            SELECT * FROM reflexes
            WHERE session_id = ? AND phase = ?
            ORDER BY timestamp ASC
        """, (session_id, phase))

        results = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            # Build vectors dict from columns
            vectors = {
                'engagement': row_dict.get('engagement'),
                'know': row_dict.get('know'),
                'do': row_dict.get('do'),
                'context': row_dict.get('context'),
                'clarity': row_dict.get('clarity'),
                'coherence': row_dict.get('coherence'),
                'signal': row_dict.get('signal'),
                'density': row_dict.get('density'),
                'state': row_dict.get('state'),
                'change': row_dict.get('change'),
                'completion': row_dict.get('completion'),
                'impact': row_dict.get('impact'),
                'uncertainty': row_dict.get('uncertainty')
            }
            # Remove None values
            vectors = {k: v for k, v in vectors.items() if v is not None}

            results.append({
                'session_id': row_dict['session_id'],
                'cascade_id': row_dict.get('cascade_id'),
                'phase': row_dict['phase'],
                'round': row_dict.get('round', 1),
                'timestamp': row_dict['timestamp'],
                'vectors': vectors,
                'metadata': json.loads(row_dict['reflex_data']) if row_dict.get('reflex_data') else {},
                'reasoning': row_dict.get('reasoning'),
                'evidence': row_dict.get('evidence')
            })

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
            ORDER BY timestamp ASC
        """, (session_id,))

        results = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            # Build vectors dict from columns
            vectors = {
                'engagement': row_dict.get('engagement'),
                'know': row_dict.get('know'),
                'do': row_dict.get('do'),
                'context': row_dict.get('context'),
                'clarity': row_dict.get('clarity'),
                'coherence': row_dict.get('coherence'),
                'signal': row_dict.get('signal'),
                'density': row_dict.get('density'),
                'state': row_dict.get('state'),
                'change': row_dict.get('change'),
                'completion': row_dict.get('completion'),
                'impact': row_dict.get('impact'),
                'uncertainty': row_dict.get('uncertainty')
            }
            # Remove None values
            vectors = {k: v for k, v in vectors.items() if v is not None}

            results.append({
                'session_id': row_dict['session_id'],
                'cascade_id': row_dict.get('cascade_id'),
                'phase': row_dict['phase'],
                'round': row_dict.get('round', 1),
                'timestamp': row_dict['timestamp'],
                'vectors': vectors,
                'metadata': json.loads(row_dict['reflex_data']) if row_dict.get('reflex_data') else {},
                'reasoning': row_dict.get('reasoning'),
                'evidence': row_dict.get('evidence')
            })

        return results
