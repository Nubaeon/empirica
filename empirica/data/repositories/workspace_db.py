"""
Workspace Database Repository — centralized access to ~/.empirica/workspace/workspace.db

Tables managed:
- global_projects: Cross-project registry (trajectory_path is the stable key)
- instance_bindings: TMUX pane → project mapping for multi-instance support
- global_sessions: Cross-project session tracking
- entity_artifacts: CRM entity-artifact cross-references

Usage:
    with WorkspaceDBRepository.open() as repo:
        project = repo.get_project_by_path('/home/user/myrepo')
        repo.upsert_project(project_id, name, trajectory_path, ...)
"""

import sqlite3
import time
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from .base import BaseRepository

logger = logging.getLogger(__name__)


def _get_workspace_db_path() -> Path:
    """Get path to workspace database."""
    return Path.home() / '.empirica' / 'workspace' / 'workspace.db'


def _ensure_workspace_schema(conn: sqlite3.Connection) -> None:
    """Create workspace tables if they don't exist."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            trajectory_path TEXT NOT NULL UNIQUE,
            git_remote_url TEXT,
            git_branch TEXT DEFAULT 'main',
            total_transactions INTEGER DEFAULT 0,
            total_findings INTEGER DEFAULT 0,
            total_unknowns INTEGER DEFAULT 0,
            total_dead_ends INTEGER DEFAULT 0,
            total_goals INTEGER DEFAULT 0,
            last_transaction_id TEXT,
            last_transaction_timestamp REAL,
            last_sync_timestamp REAL,
            status TEXT DEFAULT 'active',
            project_type TEXT DEFAULT 'product',
            project_tags TEXT,
            created_timestamp REAL NOT NULL,
            updated_timestamp REAL NOT NULL,
            metadata TEXT
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_global_projects_status
        ON global_projects(status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_global_projects_type
        ON global_projects(project_type)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_global_projects_last_tx
        ON global_projects(last_transaction_timestamp)
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS instance_bindings (
            instance_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            project_path TEXT,
            bound_timestamp REAL NOT NULL,
            FOREIGN KEY (project_id) REFERENCES global_projects(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS global_sessions (
            session_id TEXT PRIMARY KEY,
            ai_id TEXT,
            origin_project_id TEXT,
            current_project_id TEXT,
            instance_id TEXT,
            status TEXT DEFAULT 'active',
            parent_session_id TEXT,
            created_at REAL,
            last_activity REAL,
            FOREIGN KEY (origin_project_id) REFERENCES global_projects(id),
            FOREIGN KEY (current_project_id) REFERENCES global_projects(id)
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_global_sessions_instance
        ON global_sessions(instance_id, status)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_global_sessions_project
        ON global_sessions(current_project_id)
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entity_artifacts (
            id TEXT PRIMARY KEY,
            artifact_type TEXT NOT NULL,
            artifact_id TEXT NOT NULL,
            artifact_source TEXT,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            relationship TEXT DEFAULT 'about',
            relevance REAL DEFAULT 1.0,
            discovered_via TEXT,
            engagement_id TEXT,
            transaction_id TEXT,
            created_at REAL,
            created_by_ai TEXT,
            UNIQUE(artifact_type, artifact_id, entity_type, entity_id)
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_entity_artifacts_entity
        ON entity_artifacts(entity_type, entity_id)
    """)
    conn.commit()


class WorkspaceDBRepository(BaseRepository):
    """Repository for workspace.db — the global project registry."""

    def __init__(self, conn: sqlite3.Connection):
        super().__init__(conn)

    @classmethod
    def open(cls, ensure_schema: bool = True) -> 'WorkspaceDBRepository':
        """Open workspace.db and return a repository instance.

        Creates the database directory and schema if needed.
        The caller should close the connection when done (or use as context manager).

        Args:
            ensure_schema: If True, create tables if they don't exist.

        Returns:
            WorkspaceDBRepository instance

        Raises:
            FileNotFoundError: If workspace directory doesn't exist and can't be created.
        """
        db_path = _get_workspace_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        if ensure_schema:
            _ensure_workspace_schema(conn)
        return cls(conn)

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    # --- global_projects ---

    def get_project_by_path(self, trajectory_path: str) -> Optional[Dict[str, Any]]:
        """Look up a project by its filesystem path (the stable key)."""
        cursor = self._execute(
            "SELECT * FROM global_projects WHERE trajectory_path = ? AND status = 'active'",
            (str(trajectory_path),)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Look up a project by UUID."""
        cursor = self._execute(
            "SELECT * FROM global_projects WHERE id = ?",
            (project_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_project_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Look up a project by name (case-insensitive)."""
        cursor = self._execute(
            "SELECT * FROM global_projects WHERE LOWER(name) = LOWER(?) AND status = 'active'",
            (name,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_projects(self, status: str = 'active') -> List[Dict[str, Any]]:
        """List all projects with given status."""
        cursor = self._execute(
            "SELECT * FROM global_projects WHERE status = ? ORDER BY updated_timestamp DESC",
            (status,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def upsert_project(
        self,
        project_id: str,
        name: str,
        trajectory_path: str,
        description: str = '',
        git_remote_url: str = '',
        git_branch: str = 'main',
        status: str = 'active',
        project_type: str = 'product',
        metadata: Optional[str] = None,
    ) -> None:
        """Insert or update a project in the global registry."""
        now = time.time()
        self._execute(
            """INSERT INTO global_projects
               (id, name, description, trajectory_path, git_remote_url, git_branch,
                status, project_type, metadata, created_timestamp, updated_timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                   name = excluded.name,
                   description = excluded.description,
                   trajectory_path = excluded.trajectory_path,
                   git_remote_url = excluded.git_remote_url,
                   git_branch = excluded.git_branch,
                   status = excluded.status,
                   project_type = excluded.project_type,
                   metadata = excluded.metadata,
                   updated_timestamp = excluded.updated_timestamp
            """,
            (project_id, name, description, str(trajectory_path),
             git_remote_url, git_branch, status, project_type, metadata, now, now)
        )
        self.commit()

    def update_project_stats(
        self,
        project_id: str,
        total_transactions: Optional[int] = None,
        total_findings: Optional[int] = None,
        total_unknowns: Optional[int] = None,
        total_dead_ends: Optional[int] = None,
        total_goals: Optional[int] = None,
        last_transaction_id: Optional[str] = None,
        last_transaction_timestamp: Optional[float] = None,
    ) -> None:
        """Update project statistics (transaction counts, last activity)."""
        updates = []
        params = []
        if total_transactions is not None:
            updates.append("total_transactions = ?")
            params.append(total_transactions)
        if total_findings is not None:
            updates.append("total_findings = ?")
            params.append(total_findings)
        if total_unknowns is not None:
            updates.append("total_unknowns = ?")
            params.append(total_unknowns)
        if total_dead_ends is not None:
            updates.append("total_dead_ends = ?")
            params.append(total_dead_ends)
        if total_goals is not None:
            updates.append("total_goals = ?")
            params.append(total_goals)
        if last_transaction_id is not None:
            updates.append("last_transaction_id = ?")
            params.append(last_transaction_id)
        if last_transaction_timestamp is not None:
            updates.append("last_transaction_timestamp = ?")
            params.append(last_transaction_timestamp)

        if not updates:
            return

        updates.append("updated_timestamp = ?")
        params.append(time.time())
        params.append(project_id)

        self._execute(
            f"UPDATE global_projects SET {', '.join(updates)} WHERE id = ?",
            tuple(params)
        )
        self.commit()

    # --- instance_bindings ---

    def get_instance_binding(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get the project binding for a TMUX pane instance."""
        cursor = self._execute(
            "SELECT * FROM instance_bindings WHERE instance_id = ?",
            (instance_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def set_instance_binding(
        self, instance_id: str, project_id: str, project_path: str
    ) -> None:
        """Bind a TMUX pane instance to a project."""
        self._execute(
            """INSERT INTO instance_bindings (instance_id, project_id, project_path, bound_timestamp)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(instance_id) DO UPDATE SET
                   project_id = excluded.project_id,
                   project_path = excluded.project_path,
                   bound_timestamp = excluded.bound_timestamp
            """,
            (instance_id, project_id, str(project_path), time.time())
        )
        self.commit()

    # --- global_sessions ---

    def register_session(
        self,
        session_id: str,
        ai_id: str,
        project_id: str,
        instance_id: Optional[str] = None,
        parent_session_id: Optional[str] = None,
    ) -> None:
        """Register a session in the global session registry."""
        now = time.time()
        self._execute(
            """INSERT INTO global_sessions
               (session_id, ai_id, origin_project_id, current_project_id,
                instance_id, status, parent_session_id, created_at, last_activity)
               VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?)
               ON CONFLICT(session_id) DO UPDATE SET
                   last_activity = excluded.last_activity,
                   current_project_id = excluded.current_project_id,
                   instance_id = excluded.instance_id
            """,
            (session_id, ai_id, project_id, project_id,
             instance_id, parent_session_id, now, now)
        )
        self.commit()

    # --- entity_artifacts ---

    def add_entity_artifact(
        self,
        artifact_id: str,
        artifact_type: str,
        artifact_source: str,
        entity_type: str,
        entity_id: str,
        relationship: str = 'about',
        relevance: float = 1.0,
        discovered_via: Optional[str] = None,
        engagement_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        created_by_ai: Optional[str] = None,
    ) -> Optional[str]:
        """Link an artifact to a CRM entity. Returns the link ID or None on conflict."""
        import uuid
        link_id = str(uuid.uuid4())
        try:
            self._execute(
                """INSERT INTO entity_artifacts
                   (id, artifact_type, artifact_id, artifact_source, entity_type, entity_id,
                    relationship, relevance, discovered_via, engagement_id, transaction_id,
                    created_at, created_by_ai)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (link_id, artifact_type, artifact_id, artifact_source,
                 entity_type, entity_id, relationship, relevance,
                 discovered_via, engagement_id, transaction_id,
                 time.time(), created_by_ai)
            )
            self.commit()
            return link_id
        except sqlite3.IntegrityError:
            return None
