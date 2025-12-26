"""Utility repositories for token savings, command usage, and workspace stats"""
import sqlite3
import uuid
import json
from typing import Dict, List, Optional
from datetime import datetime
from .base import BaseRepository


class TokenRepository(BaseRepository):
    """Handles token savings tracking"""

    def log_token_saving(
        self,
        session_id: str,
        saving_type: str,
        tokens_saved: int,
        description: str
    ) -> str:
        """
        Log a token saving event

        Args:
            session_id: Session UUID
            saving_type: Type of saving (e.g., 'compression', 'caching', 'reuse')
            tokens_saved: Number of tokens saved
            description: Description of the saving

        Returns:
            saving_id: UUID string
        """
        saving_id = str(uuid.uuid4())
        self._execute("""
            INSERT INTO token_savings (
                id, session_id, saving_type, tokens_saved, description, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (saving_id, session_id, saving_type, tokens_saved, description, datetime.utcnow().isoformat()))
        return saving_id

    def get_session_token_savings(self, session_id: str) -> Dict:
        """
        Get total token savings for a session

        Args:
            session_id: Session UUID

        Returns:
            Dict with total_saved and breakdown by type
        """
        cursor = self._execute("""
            SELECT saving_type, SUM(tokens_saved) as total
            FROM token_savings
            WHERE session_id = ?
            GROUP BY saving_type
        """, (session_id,))

        breakdown = {row['saving_type']: row['total'] for row in cursor.fetchall()}
        total_saved = sum(breakdown.values())

        return {
            'total_saved': total_saved,
            'breakdown': breakdown
        }


class CommandRepository(BaseRepository):
    """Handles command usage tracking"""

    def log_command_usage(
        self,
        session_id: str,
        command: str,
        args: Optional[Dict] = None,
        success: bool = True,
        error_msg: Optional[str] = None
    ) -> str:
        """
        Log command usage

        Args:
            session_id: Session UUID
            command: Command name
            args: Command arguments
            success: Whether command succeeded
            error_msg: Error message if failed

        Returns:
            usage_id: UUID string
        """
        usage_id = str(uuid.uuid4())
        self._execute("""
            INSERT INTO command_usage (
                id, session_id, command, args, success, error_msg, executed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            usage_id, session_id, command,
            json.dumps(args) if args else None,
            success, error_msg, datetime.utcnow().isoformat()
        ))
        return usage_id

    def get_command_usage_stats(self, session_id: Optional[str] = None) -> List[Dict]:
        """
        Get command usage statistics

        Args:
            session_id: Optional session filter

        Returns:
            List of command stats
        """
        if session_id:
            cursor = self._execute("""
                SELECT command, COUNT(*) as count,
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                       SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failures
                FROM command_usage
                WHERE session_id = ?
                GROUP BY command
                ORDER BY count DESC
            """, (session_id,))
        else:
            cursor = self._execute("""
                SELECT command, COUNT(*) as count,
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                       SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failures
                FROM command_usage
                GROUP BY command
                ORDER BY count DESC
            """)

        return [dict(row) for row in cursor.fetchall()]


class WorkspaceRepository(BaseRepository):
    """Handles workspace-level operations"""

    def get_workspace_stats(self, project_ids: List[str]) -> Dict:
        """
        Get aggregated workspace statistics

        Args:
            project_ids: List of project UUIDs

        Returns:
            Dict with workspace stats
        """
        if not project_ids:
            return {
                'total_sessions': 0,
                'total_findings': 0,
                'total_unknowns': 0,
                'projects': []
            }

        placeholders = ','.join('?' * len(project_ids))

        # Get session count
        cursor = self._execute(f"""
            SELECT COUNT(*) as count
            FROM sessions
            WHERE project_id IN ({placeholders})
        """, tuple(project_ids))
        total_sessions = cursor.fetchone()['count']

        # Get findings count
        cursor = self._execute(f"""
            SELECT COUNT(*) as count
            FROM project_findings
            WHERE project_id IN ({placeholders})
        """, tuple(project_ids))
        total_findings = cursor.fetchone()['count']

        # Get unknowns count
        cursor = self._execute(f"""
            SELECT COUNT(*) as count
            FROM project_unknowns
            WHERE project_id IN ({placeholders})
            AND is_resolved = 0
        """, tuple(project_ids))
        total_unknowns = cursor.fetchone()['count']

        return {
            'total_sessions': total_sessions,
            'total_findings': total_findings,
            'total_unknowns': total_unknowns,
            'total_projects': len(project_ids)
        }
