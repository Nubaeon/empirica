"""
Goal and Subtask Repository

Manages goal trees and subtask investigation tracking for sessions.
Encapsulates all database operations for goals/subtasks domain.
"""

import json
import time
import uuid
from typing import Dict, List

from .base import BaseRepository


class GoalRepository(BaseRepository):
    """Repository for goal and subtask management"""

    def create_goal(self, session_id: str, objective: str, scope_breadth: float = None,
                   scope_duration: float = None, scope_coordination: float = None,
                   beads_issue_id: str = None) -> str:
        """Create a new goal for this session

        Args:
            session_id: Session UUID
            objective: What are you trying to accomplish?
            scope_breadth: 0.0-1.0 (0=single file, 1=entire codebase)
            scope_duration: 0.0-1.0 (0=minutes, 1=months)
            scope_coordination: 0.0-1.0 (0=solo, 1=heavy multi-agent)
            beads_issue_id: Optional BEADS issue ID (e.g., "bd-a1b2")

        Returns:
            goal_id (UUID string)
        """
        goal_id = str(uuid.uuid4())

        # Build scope JSON from individual vectors
        scope_data = {
            'breadth': scope_breadth,
            'duration': scope_duration,
            'coordination': scope_coordination
        }

        self._execute("""
            INSERT INTO goals (id, session_id, objective, scope, status, created_timestamp, is_completed, goal_data, beads_issue_id)
            VALUES (?, ?, ?, ?, 'in_progress', ?, 0, ?, ?)
        """, (goal_id, session_id, objective, json.dumps(scope_data), time.time(), json.dumps({}), beads_issue_id))

        self.commit()
        return goal_id

    def create_subtask(self, goal_id: str, description: str, importance: str = 'medium') -> str:
        """Create a subtask within a goal

        Args:
            goal_id: Parent goal UUID
            description: What are you investigating/implementing?
            importance: 'critical' | 'high' | 'medium' | 'low'

        Returns:
            subtask_id (UUID string)
        """
        subtask_id = str(uuid.uuid4())

        # Build subtask_data JSON with investigation tracking
        subtask_data = {
            'findings': [],
            'unknowns': [],
            'dead_ends': []
        }

        self._execute("""
            INSERT INTO subtasks (id, goal_id, description, epistemic_importance, status, created_timestamp, subtask_data)
            VALUES (?, ?, ?, ?, 'pending', ?, ?)
        """, (subtask_id, goal_id, description, importance, time.time(), json.dumps(subtask_data)))

        self.commit()
        return subtask_id

    def update_subtask_findings(self, subtask_id: str, findings: List[str]):
        """Update findings for a subtask

        Args:
            subtask_id: Subtask UUID
            findings: List of finding strings
        """
        # Get current subtask_data
        cursor = self._execute("SELECT subtask_data FROM subtasks WHERE id = ?", (subtask_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Subtask {subtask_id} not found")

        subtask_data = json.loads(row[0])
        subtask_data['findings'] = findings

        self._execute("""
            UPDATE subtasks SET subtask_data = ? WHERE id = ?
        """, (json.dumps(subtask_data), subtask_id))

        self.commit()

    def update_subtask_unknowns(self, subtask_id: str, unknowns: List[str]):
        """Update unknowns for a subtask

        Args:
            subtask_id: Subtask UUID
            unknowns: List of unknown strings
        """
        # Get current subtask_data
        cursor = self._execute("SELECT subtask_data FROM subtasks WHERE id = ?", (subtask_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Subtask {subtask_id} not found")

        subtask_data = json.loads(row[0])
        subtask_data['unknowns'] = unknowns

        self._execute("""
            UPDATE subtasks SET subtask_data = ? WHERE id = ?
        """, (json.dumps(subtask_data), subtask_id))

        self.commit()

    def update_subtask_dead_ends(self, subtask_id: str, dead_ends: List[str]):
        """Update dead ends for a subtask

        Args:
            subtask_id: Subtask UUID
            dead_ends: List of dead end strings (e.g., "Attempted X - blocked by Y")
        """
        # Get current subtask_data
        cursor = self._execute("SELECT subtask_data FROM subtasks WHERE id = ?", (subtask_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Subtask {subtask_id} not found")

        subtask_data = json.loads(row[0])
        subtask_data['dead_ends'] = dead_ends

        self._execute("""
            UPDATE subtasks SET subtask_data = ? WHERE id = ?
        """, (json.dumps(subtask_data), subtask_id))

        self.commit()

    def complete_subtask(self, subtask_id: str, evidence: str):
        """Mark subtask as completed with evidence

        Args:
            subtask_id: Subtask UUID
            evidence: Evidence of completion (e.g., "Documented in design doc", "PR merged")
        """
        self._execute("""
            UPDATE subtasks
            SET status = 'completed',
                completion_evidence = ?,
                completed_timestamp = ?
            WHERE id = ?
        """, (evidence, time.time(), subtask_id))

        self.commit()

    def get_goal_tree(self, session_id: str) -> List[Dict]:
        """Get complete goal tree for a session

        Returns list of goals with nested subtasks

        Args:
            session_id: Session UUID

        Returns:
            List of goal dicts, each with 'subtasks' list
        """
        cursor = self._execute("""
            SELECT id, objective, status, scope, estimated_complexity
            FROM goals WHERE session_id = ? ORDER BY created_timestamp
        """, (session_id,))

        goals = []
        for row in cursor.fetchall():
            goal_id = row[0]
            # Handle legacy scope formats: could be JSON dict, float, or string like "project_wide"
            scope_data = {}
            if row[3]:
                try:
                    parsed = json.loads(row[3])
                    if isinstance(parsed, dict):
                        scope_data = parsed
                    # If it's a float/int (legacy), ignore - scope_data stays {}
                except (json.JSONDecodeError, TypeError):
                    # Legacy string value like "project_wide" - ignore
                    pass

            # Get subtasks for this goal
            subtask_cursor = self._execute("""
                SELECT id, description, epistemic_importance, status, subtask_data
                FROM subtasks WHERE goal_id = ? ORDER BY created_timestamp
            """, (goal_id,))

            subtasks = []
            for sub_row in subtask_cursor.fetchall():
                subtask_data = json.loads(sub_row[4]) if sub_row[4] else {}
                subtasks.append({
                    'subtask_id': sub_row[0],
                    'description': sub_row[1],
                    'importance': sub_row[2],
                    'status': sub_row[3],
                    'findings': subtask_data.get('findings', []),
                    'unknowns': subtask_data.get('unknowns', []),
                    'dead_ends': subtask_data.get('dead_ends', [])
                })

            # Ensure scope_data is a dict before calling .get() (defensive check for legacy data)
            if not isinstance(scope_data, dict):
                scope_data = {}

            goals.append({
                'goal_id': goal_id,
                'objective': row[1],
                'status': row[2],
                'scope_breadth': scope_data.get('breadth'),
                'scope_duration': scope_data.get('duration'),
                'scope_coordination': scope_data.get('coordination'),
                'estimated_complexity': row[4],
                'subtasks': subtasks
            })

        return goals

    def query_unknowns_summary(self, session_id: str) -> Dict:
        """Get summary of all unknowns in a session (for CHECK decisions)

        Args:
            session_id: Session UUID

        Returns:
            Dict with total_unknowns count and breakdown by goal
        """
        cursor = self._execute("""
            SELECT g.id, g.objective, s.id, s.subtask_data
            FROM goals g
            LEFT JOIN subtasks s ON g.id = s.goal_id
            WHERE g.session_id = ? AND g.status = 'in_progress'
        """, (session_id,))

        total_unknowns = 0
        unknowns_by_goal = {}

        for row in cursor.fetchall():
            goal_id, objective, subtask_id, subtask_data_json = row

            if goal_id not in unknowns_by_goal:
                unknowns_by_goal[goal_id] = {
                    'goal_id': goal_id,
                    'objective': objective,
                    'unknown_count': 0
                }

            if subtask_data_json:
                subtask_data = json.loads(subtask_data_json)
                unknowns = subtask_data.get('unknowns', [])
                unknowns_count = len([u for u in unknowns if u])  # Count non-empty unknowns
                unknowns_by_goal[goal_id]['unknown_count'] += unknowns_count
                total_unknowns += unknowns_count

        return {
            'total_unknowns': total_unknowns,
            'unknowns_by_goal': list(unknowns_by_goal.values())
        }

    def get_project_goals(self, project_id: str) -> Dict:
        """Get incomplete and active goals for a project"""
        # Get incomplete goals
        cursor = self._execute("""
            SELECT id, objective, scope, status, created_timestamp
            FROM goals
            WHERE session_id IN (SELECT session_id FROM sessions WHERE project_id = ?)
            AND is_completed = 0
            ORDER BY created_timestamp DESC
        """, (project_id,))
        incomplete_goals = [dict(row) for row in cursor.fetchall()]

        # Get active goals with subtask counts
        cursor = self._execute("""
            SELECT g.id, g.objective, g.scope, g.status, g.goal_data,
                   COUNT(DISTINCT s.id) as subtask_count,
                   SUM(CASE WHEN s.status = 'completed' THEN 1 ELSE 0 END) as completed_subtasks
            FROM goals g
            LEFT JOIN subtasks s ON g.id = s.goal_id
            WHERE g.session_id IN (SELECT session_id FROM sessions WHERE project_id = ?)
            AND g.is_completed = 0
            GROUP BY g.id
            ORDER BY g.created_timestamp DESC
        """, (project_id,))
        active_goals = [dict(row) for row in cursor.fetchall()]

        return {
            'incomplete_work': incomplete_goals,
            'goals': active_goals
        }
