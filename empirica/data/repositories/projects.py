"""
Project Repository

Manages project-level operations: project creation, session linking, handoffs,
learning aggregation, and context bootstrap for multi-session work.
"""

import json
import logging
import os
import time
import uuid
import yaml
from typing import Dict, List, Optional

from .base import BaseRepository

logger = logging.getLogger(__name__)


class ProjectRepository(BaseRepository):
    """Repository for project-level management and context"""

    def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        repos: Optional[List[str]] = None
    ) -> str:
        """
        Create a new project for multi-repo/multi-session tracking.

        Args:
            name: Project name (e.g., "Empirica Core")
            description: Project description
            repos: List of repository names (e.g., ["empirica", "empirica-dev"])

        Returns:
            project_id: UUID string
        """
        project_id = str(uuid.uuid4())

        project_data = {
            "name": name,
            "description": description,
            "repos": repos or []
        }

        self._execute("""
            INSERT INTO projects (
                id, name, description, repos, created_timestamp,
                last_activity_timestamp, project_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id, name, description, json.dumps(repos or []),
            time.time(), time.time(), json.dumps(project_data)
        ))

        self.commit()
        logger.info(f"📁 Project created: {name} ({project_id[:8]}...)")

        return project_id

    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project data"""
        cursor = self._execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_project_by_name(self, name: str) -> Optional[Dict]:
        """Get project data by name (case-insensitive)"""
        cursor = self._execute("SELECT * FROM projects WHERE LOWER(name) = LOWER(?)", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def resolve_project_id(self, project_id_or_name: str) -> Optional[str]:
        """
        Resolve project identifier to UUID.
        Accepts either UUID or project name.
        
        Args:
            project_id_or_name: UUID or project name
            
        Returns:
            Project UUID if found, None otherwise
        """
        # Try as UUID first
        project = self.get_project(project_id_or_name)
        if project:
            return project['id']
        
        # Try as name
        project = self.get_project_by_name(project_id_or_name)
        if project:
            return project['id']
        
        return None

    def link_session_to_project(self, session_id: str, project_id: str):
        """Link a session to a project"""
        self._execute("""
            UPDATE sessions SET project_id = ? WHERE session_id = ?
        """, (project_id, session_id))

        # Update project activity timestamp and session count
        self._execute("""
            UPDATE projects
            SET last_activity_timestamp = ?,
                total_sessions = total_sessions + 1
            WHERE id = ?
        """, (time.time(), project_id))

        self.commit()
        logger.info(f"🔗 Session {session_id[:8]}... linked to project {project_id[:8]}...")

    def get_project_sessions(self, project_id: str) -> List[Dict]:
        """Get all sessions for a project"""
        cursor = self._execute("""
            SELECT * FROM sessions WHERE project_id = ? ORDER BY start_time DESC
        """, (project_id,))
        return [dict(row) for row in cursor.fetchall()]

    def aggregate_project_learning_deltas(self, project_id: str) -> Dict[str, float]:
        """
        Compute total epistemic learning across all project sessions.

        Queries PREFLIGHT and POSTFLIGHT reflexes for each session,
        computes deltas, and aggregates.
        """
        # Get all sessions for project
        cursor = self._execute("""
            SELECT session_id FROM sessions WHERE project_id = ? ORDER BY start_time
        """, (project_id,))
        session_ids = [row[0] for row in cursor.fetchall()]

        if not session_ids:
            return {}

        # Aggregate deltas across all sessions
        total_deltas = {
            'engagement': 0.0, 'know': 0.0, 'do': 0.0, 'context': 0.0, 'clarity': 0.0,
            'coherence': 0.0, 'signal': 0.0, 'density': 0.0, 'state': 0.0,
            'change': 0.0, 'completion': 0.0, 'impact': 0.0, 'uncertainty': 0.0
        }

        for session_id in session_ids:
            # Get PREFLIGHT vectors
            cursor = self._execute("""
                SELECT engagement, know, do, context, clarity, coherence, signal, density,
                       state, change, completion, impact, uncertainty
                FROM reflexes
                WHERE session_id = ? AND phase = 'PREFLIGHT'
                ORDER BY timestamp
                LIMIT 1
            """, (session_id,))
            preflight = cursor.fetchone()

            # Get POSTFLIGHT vectors
            cursor = self._execute("""
                SELECT engagement, know, do, context, clarity, coherence, signal, density,
                       state, change, completion, impact, uncertainty
                FROM reflexes
                WHERE session_id = ? AND phase = 'POSTFLIGHT'
                ORDER BY timestamp DESC
                LIMIT 1
            """, (session_id,))
            postflight = cursor.fetchone()

            if preflight and postflight:
                # Compute deltas and add to totals
                for i, vector in enumerate(['engagement', 'know', 'do', 'context', 'clarity',
                                            'coherence', 'signal', 'density', 'state', 'change',
                                            'completion', 'impact', 'uncertainty']):
                    if preflight[i] is not None and postflight[i] is not None:
                        total_deltas[vector] += (postflight[i] - preflight[i])

        return total_deltas

    def create_project_handoff(
        self,
        project_id: str,
        project_summary: str,
        key_decisions: Optional[List[str]] = None,
        patterns_discovered: Optional[List[str]] = None,
        remaining_work: Optional[List[str]] = None
    ) -> str:
        """
        Create project-level handoff report by aggregating session handoffs.

        Args:
            project_id: Project identifier
            project_summary: High-level summary of project state
            key_decisions: List of major decisions made
            patterns_discovered: Reusable patterns found
            remaining_work: Outstanding tasks

        Returns:
            handoff_id: UUID string
        """
        handoff_id = str(uuid.uuid4())

        # Get all sessions for project
        sessions = self.get_project_sessions(project_id)

        # Aggregate session handoffs
        sessions_included = []
        for session in sessions:
            sessions_included.append({
                "session_id": session['session_id'],
                "start_time": session['start_time'],
                "ai_id": session['ai_id']
            })

        # Compute total learning deltas
        total_deltas = self.aggregate_project_learning_deltas(project_id)

        # Get recent mistakes from project
        cursor = self._execute("""
            SELECT mistake, cost_estimate, root_cause_vector, prevention
            FROM mistakes_made m
            JOIN sessions s ON m.session_id = s.session_id
            WHERE s.project_id = ?
            ORDER BY m.created_timestamp DESC
            LIMIT 10
        """, (project_id,))
        mistakes_summary = [dict(row) for row in cursor.fetchall()]

        # Get repos touched
        project = self.get_project(project_id)
        repos_touched = json.loads(project['repos']) if project and project['repos'] else []

        # Build handoff data
        handoff_data = {
            "project_summary": project_summary,
            "sessions_included": sessions_included,
            "total_learning_deltas": total_deltas,
            "key_decisions": key_decisions or [],
            "patterns_discovered": patterns_discovered or [],
            "mistakes_summary": mistakes_summary,
            "remaining_work": remaining_work or [],
            "repos_touched": repos_touched,
            "next_session_bootstrap": {
                "suggested_focus": remaining_work[0] if remaining_work else "Continue project work",
                "context_breadcrumbs": key_decisions[-5:] if key_decisions else []
            }
        }

        self._execute("""
            INSERT INTO project_handoffs (
                id, project_id, created_timestamp, project_summary,
                sessions_included, total_learning_deltas, key_decisions,
                patterns_discovered, mistakes_summary, remaining_work,
                repos_touched, next_session_bootstrap, handoff_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            handoff_id, project_id, time.time(), project_summary,
            json.dumps(sessions_included), json.dumps(total_deltas),
            json.dumps(key_decisions or []), json.dumps(patterns_discovered or []),
            json.dumps(mistakes_summary), json.dumps(remaining_work or []),
            json.dumps(repos_touched), json.dumps(handoff_data["next_session_bootstrap"]),
            json.dumps(handoff_data)
        ))

        self.commit()
        logger.info(f"📋 Project handoff created: {handoff_id[:8]}...")

        return handoff_id

    def get_latest_project_handoff(self, project_id: str) -> Optional[Dict]:
        """Get the most recent project handoff"""
        cursor = self._execute("""
            SELECT * FROM project_handoffs
            WHERE project_id = ?
            ORDER BY created_timestamp DESC
            LIMIT 1
        """, (project_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_ai_epistemic_handoff(self, project_id: str, ai_id: str) -> Optional[Dict]:
        """Get latest epistemic handoff (POSTFLIGHT checkpoint) for a specific AI in this project.
        
        This loads the most recent session's POSTFLIGHT checkpoint for the given AI ID,
        enabling epistemic continuity across session boundaries.
        
        Includes delta calculation: Shows what changed from PREFLIGHT → POSTFLIGHT.
        
        Args:
            project_id: Project UUID
            ai_id: AI identifier (e.g., 'claude-code')
            
        Returns:
            Dictionary with epistemic vectors, deltas, and reasoning, or None if no checkpoint exists
        """
        cursor = self._execute("""
            SELECT r.* FROM reflexes r
            JOIN sessions s ON r.session_id = s.session_id
            WHERE s.project_id = ? AND s.ai_id = ? AND r.phase = 'POSTFLIGHT'
            ORDER BY r.timestamp DESC
            LIMIT 1
        """, (project_id, ai_id))
        
        postflight = cursor.fetchone()
        if not postflight:
            return None
        
        # Convert to dict
        postflight_dict = dict(postflight)
        session_id = postflight_dict.get('session_id')
        
        # Try to find corresponding PREFLIGHT to calculate deltas
        cursor = self._execute("""
            SELECT r.* FROM reflexes r
            WHERE r.session_id = ? AND r.phase = 'PREFLIGHT'
            ORDER BY r.timestamp ASC
            LIMIT 1
        """, (session_id,))
        
        preflight = cursor.fetchone()
        preflight_dict = dict(preflight) if preflight else None
        
        # Build epistemic vectors dict from POSTFLIGHT
        vectors = {
            'engagement': postflight_dict.get('engagement'),
            'foundation': {
                'know': postflight_dict.get('know'),
                'do': postflight_dict.get('do'),
                'context': postflight_dict.get('context')
            },
            'comprehension': {
                'clarity': postflight_dict.get('clarity'),
                'coherence': postflight_dict.get('coherence'),
                'signal': postflight_dict.get('signal'),
                'density': postflight_dict.get('density')
            },
            'execution': {
                'state': postflight_dict.get('state'),
                'change': postflight_dict.get('change'),
                'completion': postflight_dict.get('completion'),
                'impact': postflight_dict.get('impact')
            },
            'uncertainty': postflight_dict.get('uncertainty')
        }
        
        # Remove None values
        vectors = {k: v for k, v in vectors.items() if v is not None}
        
        # Calculate deltas if PREFLIGHT exists
        deltas = None
        if preflight_dict:
            deltas = {
                'engagement': self._calculate_delta(preflight_dict.get('engagement'), postflight_dict.get('engagement')),
                'foundation': {
                    'know': self._calculate_delta(preflight_dict.get('know'), postflight_dict.get('know')),
                    'do': self._calculate_delta(preflight_dict.get('do'), postflight_dict.get('do')),
                    'context': self._calculate_delta(preflight_dict.get('context'), postflight_dict.get('context'))
                },
                'comprehension': {
                    'clarity': self._calculate_delta(preflight_dict.get('clarity'), postflight_dict.get('clarity')),
                    'coherence': self._calculate_delta(preflight_dict.get('coherence'), postflight_dict.get('coherence')),
                    'signal': self._calculate_delta(preflight_dict.get('signal'), postflight_dict.get('signal')),
                    'density': self._calculate_delta(preflight_dict.get('density'), postflight_dict.get('density'))
                },
                'execution': {
                    'state': self._calculate_delta(preflight_dict.get('state'), postflight_dict.get('state')),
                    'change': self._calculate_delta(preflight_dict.get('change'), postflight_dict.get('change')),
                    'completion': self._calculate_delta(preflight_dict.get('completion'), postflight_dict.get('completion')),
                    'impact': self._calculate_delta(preflight_dict.get('impact'), postflight_dict.get('impact'))
                },
                'uncertainty': self._calculate_delta(preflight_dict.get('uncertainty'), postflight_dict.get('uncertainty'))
            }
            # Remove None deltas
            deltas = {k: v for k, v in deltas.items() if v is not None}
        
        result = {
            'checkpoint_id': postflight_dict.get('id'),
            'session_id': session_id,
            'ai_id': ai_id,
            'phase': 'POSTFLIGHT',
            'vectors': vectors,
            'reasoning': postflight_dict.get('reasoning'),
            'evidence': postflight_dict.get('evidence'),
            'timestamp': postflight_dict.get('timestamp')
        }
        
        if deltas:
            result['deltas'] = deltas
        
        return result
    
    def _calculate_delta(self, before: Optional[float], after: Optional[float]) -> Optional[float]:
        """Calculate change from before to after, returning None if either is None"""
        if before is None or after is None:
            return None
        return round(after - before, 3)

    # Note: bootstrap_project_breadcrumbs is kept in SessionDatabase facade
    # due to complex cross-repository dependencies (breadcrumbs, goals, handoffs)
    # The facade handles the orchestration of multiple repository calls
