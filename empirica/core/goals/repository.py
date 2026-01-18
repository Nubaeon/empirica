#!/usr/bin/env python3
"""
Goal Repository - Database operations for Goal persistence

Provides CRUD operations for structured goals with full serialization.
MVP implementation: Simple database operations, no complex queries yet.
"""

import json
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from empirica.data.session_database import SessionDatabase
from .types import Goal, ScopeVector

logger = logging.getLogger(__name__)


class GoalRepository:
    """Database operations for Goal persistence"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize repository
        
        Args:
            db_path: Optional custom database path
        """
        self.db = SessionDatabase(db_path=db_path)
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create goal-related tables if they don't exist"""
        try:
            # Goals table
            self.db.conn.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    objective TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    estimated_complexity REAL,
                    created_timestamp REAL NOT NULL,
                    completed_timestamp REAL,
                    is_completed BOOLEAN DEFAULT 0,
                    goal_data TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)
            
            # Success criteria table (normalized)
            self.db.conn.execute("""
                CREATE TABLE IF NOT EXISTS success_criteria (
                    id TEXT PRIMARY KEY,
                    goal_id TEXT NOT NULL,
                    description TEXT NOT NULL,
                    validation_method TEXT NOT NULL,
                    threshold REAL,
                    is_required BOOLEAN DEFAULT 1,
                    is_met BOOLEAN DEFAULT 0,
                    FOREIGN KEY (goal_id) REFERENCES goals(id)
                )
            """)
            
            # Dependencies table (normalized)
            self.db.conn.execute("""
                CREATE TABLE IF NOT EXISTS goal_dependencies (
                    id TEXT PRIMARY KEY,
                    goal_id TEXT NOT NULL,
                    depends_on_goal_id TEXT NOT NULL,
                    dependency_type TEXT NOT NULL,
                    description TEXT,
                    FOREIGN KEY (goal_id) REFERENCES goals(id),
                    FOREIGN KEY (depends_on_goal_id) REFERENCES goals(id)
                )
            """)
            
            self.db.conn.commit()
            logger.info("Goal tables ensured in database")
            
        except Exception as e:
            logger.error(f"Error creating goal tables: {e}")
            raise
    
    def save_goal(self, goal: Goal, session_id: Optional[str] = None) -> bool:
        """
        Save goal to database
        
        Args:
            goal: Goal object to save
            session_id: Optional session ID to associate with goal
            
        Returns:
            True if successful
        """
        try:
            # Serialize full goal as JSON for easy retrieval
            goal_data = json.dumps(goal.to_dict())
            
            # Insert main goal record
            self.db.conn.execute("""
                INSERT OR REPLACE INTO goals 
                (id, session_id, objective, scope, estimated_complexity, 
                 created_timestamp, completed_timestamp, is_completed, goal_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                goal.id,
                session_id,
                goal.objective,
                json.dumps(goal.scope.to_dict()),
                goal.estimated_complexity,
                goal.created_timestamp,
                goal.completed_timestamp,
                goal.is_completed,
                goal_data
            ))
            
            # Insert success criteria (delete old ones first)
            self.db.conn.execute("DELETE FROM success_criteria WHERE goal_id = ?", (goal.id,))
            for sc in goal.success_criteria:
                self.db.conn.execute("""
                    INSERT INTO success_criteria
                    (id, goal_id, description, validation_method, threshold, is_required, is_met)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    sc.id,
                    goal.id,
                    sc.description,
                    sc.validation_method,
                    sc.threshold,
                    sc.is_required,
                    sc.is_met
                ))
            
            # Insert dependencies (delete old ones first)
            self.db.conn.execute("DELETE FROM goal_dependencies WHERE goal_id = ?", (goal.id,))
            for dep in goal.dependencies:
                self.db.conn.execute("""
                    INSERT INTO goal_dependencies
                    (id, goal_id, depends_on_goal_id, dependency_type, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    dep.id,
                    goal.id,
                    dep.goal_id,
                    dep.dependency_type.value,
                    dep.description
                ))
            
            self.db.conn.commit()
            logger.info(f"Saved goal {goal.id}: {goal.objective[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Error saving goal {goal.id}: {e}")
            self.db.conn.rollback()
            return False
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """
        Retrieve goal by ID
        
        Args:
            goal_id: Goal identifier
            
        Returns:
            Goal object or None if not found
        """
        try:
            cursor = self.db.conn.execute(
                "SELECT goal_data FROM goals WHERE id = ?",
                (goal_id,)
            )
            row = cursor.fetchone()
            
            if row:
                goal_dict = json.loads(row[0])
                return Goal.from_dict(goal_dict)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving goal {goal_id}: {e}")
            return None
    
    def get_session_goals(self, session_id: str) -> List[Goal]:
        """
        Retrieve all goals for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of Goal objects
        """
        try:
            cursor = self.db.conn.execute(
                "SELECT goal_data FROM goals WHERE session_id = ? ORDER BY created_timestamp",
                (session_id,)
            )
            
            goals = []
            for row in cursor.fetchall():
                goal_dict = json.loads(row[0])
                goals.append(Goal.from_dict(goal_dict))
            
            return goals
            
        except Exception as e:
            logger.error(f"Error retrieving session goals: {e}")
            return []
    
    def update_goal_completion(self, goal_id: str, is_completed: bool = True) -> bool:
        """
        Update goal completion status
        
        Args:
            goal_id: Goal identifier
            is_completed: Completion status
            
        Returns:
            True if successful
        """
        try:
            import time
            timestamp = time.time() if is_completed else None
            
            self.db.conn.execute("""
                UPDATE goals 
                SET is_completed = ?, completed_timestamp = ?
                WHERE id = ?
            """, (is_completed, timestamp, goal_id))
            
            # Also update the goal_data JSON
            goal = self.get_goal(goal_id)
            if goal:
                goal.is_completed = is_completed
                goal.completed_timestamp = timestamp
                goal_data = json.dumps(goal.to_dict())
                
                self.db.conn.execute(
                    "UPDATE goals SET goal_data = ? WHERE id = ?",
                    (goal_data, goal_id)
                )
            
            self.db.conn.commit()
            logger.info(f"Updated goal {goal_id} completion: {is_completed}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating goal completion: {e}")
            self.db.conn.rollback()
            return False
    
    def query_goals(
        self,
        session_id: Optional[str] = None,
        is_completed: Optional[bool] = None,
        scope: Optional[ScopeVector] = None
    ) -> List[Goal]:
        """
        Query goals with filters
        
        Args:
            session_id: Filter by session
            is_completed: Filter by completion status
            scope: Filter by scope
            
        Returns:
            List of matching Goal objects
        """
        try:
            query = "SELECT goal_data FROM goals WHERE 1=1"
            params = []
            
            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)
            
            if is_completed is not None:
                query += " AND is_completed = ?"
                params.append(is_completed)
            
            if scope:
                query += " AND scope = ?"
                params.append(json.dumps(scope.to_dict()))
            
            query += " ORDER BY created_timestamp DESC"
            
            cursor = self.db.conn.execute(query, params)
            
            goals = []
            for row in cursor.fetchall():
                goal_dict = json.loads(row[0])
                goals.append(Goal.from_dict(goal_dict))
            
            return goals
            
        except Exception as e:
            logger.error(f"Error querying goals: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        self.db.close()

    def mark_goals_stale(self, session_id: str, stale_reason: str = "memory_compact") -> int:
        """Mark all in_progress goals for a session as stale

        Called during memory compaction to signal that the AI's full context
        about these goals has been lost. Post-compact AI should re-evaluate
        these goals before continuing work.

        Args:
            session_id: Session UUID
            stale_reason: Why goals are being marked stale (e.g., "memory_compact")

        Returns:
            Number of goals marked stale
        """
        import time
        try:
            # Find all in_progress goals for this session
            cursor = self.db.conn.execute("""
                SELECT id, goal_data FROM goals
                WHERE session_id = ? AND is_completed = 0
            """, (session_id,))

            count = 0
            for row in cursor.fetchall():
                goal_id = row[0]
                goal_data = json.loads(row[1]) if row[1] else {}

                # Add stale metadata to goal_data
                if 'metadata' not in goal_data:
                    goal_data['metadata'] = {}
                goal_data['metadata']['stale_since'] = time.time()
                goal_data['metadata']['stale_reason'] = stale_reason

                self.db.conn.execute("""
                    UPDATE goals
                    SET goal_data = ?
                    WHERE id = ?
                """, (json.dumps(goal_data), goal_id))
                count += 1

            self.db.conn.commit()
            logger.info(f"Marked {count} goals as stale for session {session_id[:8]}...")
            return count

        except Exception as e:
            logger.error(f"Error marking goals stale: {e}")
            self.db.conn.rollback()
            return 0

    def get_stale_goals(self, session_id: Optional[str] = None, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get stale goals for a session or project

        Args:
            session_id: Optional session UUID filter
            project_id: Optional project UUID filter (checks all sessions in project)

        Returns:
            List of stale goal dicts with stale_since metadata
        """
        try:
            if session_id:
                cursor = self.db.conn.execute("""
                    SELECT id, objective, scope, goal_data, created_timestamp
                    FROM goals
                    WHERE session_id = ? AND is_completed = 0
                    ORDER BY created_timestamp DESC
                """, (session_id,))
            elif project_id:
                cursor = self.db.conn.execute("""
                    SELECT g.id, g.objective, g.scope, g.goal_data, g.created_timestamp
                    FROM goals g
                    JOIN sessions s ON g.session_id = s.session_id
                    WHERE s.project_id = ? AND g.is_completed = 0
                    ORDER BY g.created_timestamp DESC
                """, (project_id,))
            else:
                return []

            stale_goals = []
            for row in cursor.fetchall():
                goal_data = json.loads(row[3]) if row[3] else {}
                metadata = goal_data.get('metadata', {})

                # Only include goals that have stale metadata
                if metadata.get('stale_since'):
                    stale_goals.append({
                        'goal_id': row[0],
                        'objective': row[1],
                        'scope': json.loads(row[2]) if row[2] else {},
                        'stale_since': metadata.get('stale_since'),
                        'stale_reason': metadata.get('stale_reason'),
                        'created_timestamp': row[4]
                    })

            return stale_goals

        except Exception as e:
            logger.error(f"Error getting stale goals: {e}")
            return []

    def refresh_goal(self, goal_id: str) -> bool:
        """Mark a stale goal as refreshed (AI has regained context)

        Args:
            goal_id: Goal UUID to refresh

        Returns:
            True if refreshed, False if goal not found or not stale
        """
        import time
        try:
            cursor = self.db.conn.execute("""
                SELECT goal_data FROM goals WHERE id = ? AND is_completed = 0
            """, (goal_id,))
            row = cursor.fetchone()

            if not row:
                return False

            goal_data = json.loads(row[0]) if row[0] else {}
            metadata = goal_data.get('metadata', {})

            # Check if goal was stale
            if not metadata.get('stale_since'):
                return False

            # Clear stale flag and add refresh timestamp
            metadata['refreshed_at'] = time.time()
            metadata.pop('stale_since', None)
            metadata.pop('stale_reason', None)
            goal_data['metadata'] = metadata

            self.db.conn.execute("""
                UPDATE goals SET goal_data = ? WHERE id = ?
            """, (json.dumps(goal_data), goal_id))

            self.db.conn.commit()
            logger.info(f"Refreshed goal {goal_id[:8]}...")
            return True

        except Exception as e:
            logger.error(f"Error refreshing goal: {e}")
            self.db.conn.rollback()
            return False
