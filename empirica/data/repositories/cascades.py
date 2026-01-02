"""Cascade repository for CASCADE workflow operations"""
import sqlite3
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from .base import BaseRepository


class CascadeRepository(BaseRepository):
    """Handles CASCADE workflow database operations"""

    def create_cascade(
        self,
        session_id: str,
        task: str,
        context: Dict[str, Any],
        goal_id: Optional[str] = None,
        goal: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create cascade record, return cascade_id

        Args:
            session_id: Session identifier
            task: Task description
            context: Context dictionary
            goal_id: Optional goal identifier
            goal: Optional full goal object

        Returns:
            cascade_id: UUID string
        """
        cascade_id = str(uuid.uuid4())
        goal_json = json.dumps(goal) if goal else None

        self._execute("""
            INSERT INTO cascades (
                cascade_id, session_id, task, context_json, goal_id, goal_json, started_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cascade_id, session_id, task, json.dumps(context), goal_id, goal_json, datetime.now(timezone.utc).isoformat()))

        # Increment session cascade count
        self._execute("""
            UPDATE sessions SET total_cascades = total_cascades + 1
            WHERE session_id = ?
        """, (session_id,))

        return cascade_id

    def update_cascade_phase(self, cascade_id: str, phase: str, completed: bool = True):
        """
        Mark cascade phase as completed

        Args:
            cascade_id: Cascade UUID
            phase: Phase name (preflight/think/plan/investigate/check/act/postflight)
            completed: Whether phase is completed
        """
        # SECURITY: Validate phase parameter to prevent SQL injection
        VALID_PHASES = {'preflight', 'think', 'plan', 'investigate', 'check', 'act', 'postflight'}
        if phase not in VALID_PHASES:
            raise ValueError(f"Invalid phase: {phase}. Must be one of {VALID_PHASES}")

        phase_column = f"{phase}_completed"
        self._execute(f"""
            UPDATE cascades SET {phase_column} = ? WHERE cascade_id = ?
        """, (completed, cascade_id))

    def complete_cascade(
        self,
        cascade_id: str,
        final_action: str,
        final_confidence: float,
        investigation_rounds: int,
        duration_ms: int,
        engagement_gate_passed: bool,
        bayesian_active: bool = False,
        drift_monitored: bool = False
    ):
        """
        Mark cascade as completed with final results

        Args:
            cascade_id: Cascade UUID
            final_action: Final action taken
            final_confidence: Final confidence score
            investigation_rounds: Number of investigation rounds
            duration_ms: Duration in milliseconds
            engagement_gate_passed: Whether engagement gate passed
            bayesian_active: Whether Bayesian reasoning was active
            drift_monitored: Whether drift was monitored
        """
        self._execute("""
            UPDATE cascades SET
                final_action = ?,
                final_confidence = ?,
                investigation_rounds = ?,
                duration_ms = ?,
                completed_at = ?,
                engagement_gate_passed = ?,
                bayesian_active = ?,
                drift_monitored = ?
            WHERE cascade_id = ?
        """, (
            final_action, final_confidence, investigation_rounds, duration_ms,
            datetime.now(timezone.utc).isoformat(), engagement_gate_passed, bayesian_active,
            drift_monitored, cascade_id
        ))

    def get_cascade(self, cascade_id: str) -> Optional[Dict]:
        """Get cascade by ID"""
        cursor = self._execute(
            "SELECT * FROM cascades WHERE cascade_id = ?",
            (cascade_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def store_epistemic_delta(self, cascade_id: str, delta: Dict[str, float]):
        """
        Store epistemic delta (PREFLIGHT vs POSTFLIGHT) for calibration tracking

        Args:
            cascade_id: Cascade UUID
            delta: Dictionary of epistemic changes (e.g., {'know': +0.15, 'uncertainty': -0.20})
        """
        self._execute("""
            UPDATE cascades SET epistemic_delta = ? WHERE cascade_id = ?
        """, (json.dumps(delta), cascade_id))
