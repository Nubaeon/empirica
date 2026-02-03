"""
Workspace Database

Global registry of all projects with epistemic trajectory pointers.
Enables cross-project pattern matching and knowledge transfer.

Location: ~/.empirica/workspace/workspace.db
"""

import json
import logging
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from .schema.workspace_schema import SCHEMAS

logger = logging.getLogger(__name__)


class WorkspaceDatabase:
    """
    Global workspace database for cross-project epistemic tracking.

    This is the "portfolio view" that tracks:
    - All known projects and their trajectory paths
    - Cross-project patterns and learnings
    - Knowledge transfer links between projects
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialize workspace database.

        Args:
            db_path: Custom path. Defaults to ~/.empirica/workspace/workspace.db
        """
        if db_path is None:
            empirica_dir = Path.home() / '.empirica' / 'workspace'
            empirica_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(empirica_dir / 'workspace.db')

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

        self._create_tables()
        logger.info(f"📊 Workspace Database initialized: {db_path}")

    def _create_tables(self):
        """Create workspace tables from schema."""
        cursor = self.conn.cursor()
        for schema in SCHEMAS:
            try:
                cursor.execute(schema)
            except Exception as e:
                logger.warning(f"Schema creation warning: {e}")
        self.conn.commit()

    def close(self):
        """Close database connection."""
        self.conn.close()

    # ========================================================================
    # Project Registry
    # ========================================================================

    def register_project(
        self,
        name: str,
        trajectory_path: str,
        description: Optional[str] = None,
        git_remote_url: Optional[str] = None,
        project_type: str = 'product',
        project_tags: Optional[List[str]] = None,
    ) -> str:
        """Register a project in the global workspace.

        Args:
            name: Project display name
            trajectory_path: Path to project's .empirica directory
            description: Project description
            git_remote_url: Git remote URL for sync
            project_type: 'product', 'research', 'outreach'
            project_tags: Tags for categorization

        Returns:
            project_id: UUID string
        """
        project_id = str(uuid.uuid4())
        now = time.time()

        # Normalize trajectory path
        trajectory_path = str(Path(trajectory_path).expanduser().resolve())

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO global_projects (
                id, name, description, trajectory_path, git_remote_url,
                project_type, project_tags, status,
                created_timestamp, updated_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
        """, (
            project_id, name, description, trajectory_path, git_remote_url,
            project_type, json.dumps(project_tags) if project_tags else None,
            now, now
        ))
        self.conn.commit()

        logger.info(f"📁 Registered project: {name} -> {trajectory_path}")
        return project_id

    def get_project_by_path(self, trajectory_path: str) -> Optional[Dict]:
        """Get project by its trajectory path.

        Args:
            trajectory_path: Path to project's .empirica directory

        Returns:
            Project dict or None
        """
        trajectory_path = str(Path(trajectory_path).expanduser().resolve())

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM global_projects WHERE trajectory_path = ?",
            (trajectory_path,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_projects(
        self,
        status: Optional[str] = None,
        project_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """List all registered projects.

        Args:
            status: Filter by status ('active', 'dormant', 'archived')
            project_type: Filter by type
            limit: Max results

        Returns:
            List of project dicts
        """
        query = "SELECT * FROM global_projects WHERE 1=1"
        params: List = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if project_type:
            query += " AND project_type = ?"
            params.append(project_type)

        query += " ORDER BY last_transaction_timestamp DESC NULLS LAST LIMIT ?"
        params.append(limit)

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def update_project_stats(
        self,
        project_id: str,
        total_transactions: int,
        total_findings: int,
        total_unknowns: int,
        total_dead_ends: int,
        total_goals: int,
        last_transaction_id: Optional[str] = None,
        last_transaction_timestamp: Optional[float] = None,
    ):
        """Update cached statistics for a project.

        Call this after syncing from a project's local database.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE global_projects SET
                total_transactions = ?,
                total_findings = ?,
                total_unknowns = ?,
                total_dead_ends = ?,
                total_goals = ?,
                last_transaction_id = ?,
                last_transaction_timestamp = ?,
                last_sync_timestamp = ?,
                updated_timestamp = ?
            WHERE id = ?
        """, (
            total_transactions, total_findings, total_unknowns,
            total_dead_ends, total_goals,
            last_transaction_id, last_transaction_timestamp,
            time.time(), time.time(),
            project_id
        ))
        self.conn.commit()

    # ========================================================================
    # Cross-Trajectory Patterns
    # ========================================================================

    def log_pattern(
        self,
        pattern_type: str,
        pattern_description: str,
        source_project_ids: List[str],
        domain: Optional[str] = None,
        tech_stack: Optional[List[str]] = None,
        avg_impact: Optional[float] = None,
        confidence: float = 0.5,
        pattern_data: Optional[Dict] = None,
    ) -> str:
        """Log a cross-trajectory pattern.

        Args:
            pattern_type: 'learning', 'mistake', 'dead_end', 'success'
            pattern_description: Human-readable pattern description
            source_project_ids: Projects where this pattern was observed
            domain: Domain area (e.g., 'caching', 'auth')
            tech_stack: Technologies involved
            avg_impact: Average impact score
            confidence: How reliable is this pattern?
            pattern_data: Full pattern details

        Returns:
            pattern_id: UUID string
        """
        pattern_id = str(uuid.uuid4())
        now = time.time()

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO trajectory_patterns (
                id, pattern_type, pattern_description, source_project_ids,
                occurrence_count, avg_impact, confidence, domain, tech_stack,
                first_observed, last_observed, pattern_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pattern_id, pattern_type, pattern_description,
            json.dumps(source_project_ids), len(source_project_ids),
            avg_impact, confidence, domain,
            json.dumps(tech_stack) if tech_stack else None,
            now, now, json.dumps(pattern_data or {})
        ))
        self.conn.commit()

        logger.info(f"📊 Pattern logged: {pattern_type} - {pattern_description[:50]}...")
        return pattern_id

    def search_patterns(
        self,
        pattern_type: Optional[str] = None,
        domain: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: int = 20
    ) -> List[Dict]:
        """Search for cross-trajectory patterns.

        Args:
            pattern_type: Filter by type
            domain: Filter by domain
            min_confidence: Minimum confidence threshold
            limit: Max results

        Returns:
            List of pattern dicts
        """
        query = "SELECT * FROM trajectory_patterns WHERE confidence >= ?"
        params: List = [min_confidence]

        if pattern_type:
            query += " AND pattern_type = ?"
            params.append(pattern_type)

        if domain:
            query += " AND domain = ?"
            params.append(domain)

        query += " ORDER BY occurrence_count DESC, confidence DESC LIMIT ?"
        params.append(limit)

        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    # ========================================================================
    # Knowledge Transfer Links
    # ========================================================================

    def create_link(
        self,
        source_project_id: str,
        target_project_id: str,
        link_type: str,
        artifact_type: Optional[str] = None,
        artifact_id: Optional[str] = None,
        relevance: float = 1.0,
        notes: Optional[str] = None,
        created_by_ai_id: Optional[str] = None,
    ) -> str:
        """Create a knowledge transfer link between projects.

        Args:
            source_project_id: Source project UUID
            target_project_id: Target project UUID
            link_type: 'shared_learning', 'dependency', 'related', 'derived'
            artifact_type: Type of artifact being linked
            artifact_id: ID of specific artifact
            relevance: Relevance score
            notes: Link description
            created_by_ai_id: AI that created the link

        Returns:
            link_id: UUID string
        """
        link_id = str(uuid.uuid4())

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO trajectory_links (
                id, source_project_id, target_project_id, link_type,
                artifact_type, artifact_id, relevance, notes,
                created_timestamp, created_by_ai_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            link_id, source_project_id, target_project_id, link_type,
            artifact_type, artifact_id, relevance, notes,
            time.time(), created_by_ai_id
        ))
        self.conn.commit()

        logger.info(f"🔗 Link created: {source_project_id[:8]}... -> {target_project_id[:8]}...")
        return link_id

    def get_related_projects(self, project_id: str) -> List[Dict]:
        """Get all projects linked to this one.

        Returns projects that are sources or targets of links
        involving the given project.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT gp.*, tl.link_type, tl.relevance
            FROM global_projects gp
            JOIN trajectory_links tl ON (
                gp.id = tl.target_project_id AND tl.source_project_id = ?
            ) OR (
                gp.id = tl.source_project_id AND tl.target_project_id = ?
            )
            WHERE gp.id != ?
            ORDER BY tl.relevance DESC
        """, (project_id, project_id, project_id))

        return [dict(row) for row in cursor.fetchall()]

    # ========================================================================
    # Discovery / Sync
    # ========================================================================

    def discover_projects(self, workspace_root: str) -> List[Dict]:
        """Discover projects under a workspace root.

        Scans for directories with .empirica subdirectories
        and registers them if not already known.

        Args:
            workspace_root: Root directory to scan

        Returns:
            List of newly discovered projects
        """
        root = Path(workspace_root).expanduser().resolve()
        discovered = []

        for item in root.iterdir():
            if not item.is_dir():
                continue

            empirica_dir = item / '.empirica'
            if not empirica_dir.exists():
                continue

            trajectory_path = str(empirica_dir)

            # Check if already registered
            existing = self.get_project_by_path(trajectory_path)
            if existing:
                continue

            # Infer name from directory
            name = item.name

            # Try to get description from README
            description = None
            for readme in ['README.md', 'README.rst', 'README.txt']:
                readme_path = item / readme
                if readme_path.exists():
                    try:
                        with open(readme_path) as f:
                            lines = f.readlines()
                            for line in lines:
                                line = line.strip()
                                if line and not line.startswith('#') and len(line) > 10:
                                    description = line[:200]
                                    break
                    except Exception:
                        pass
                    break

            # Try to get git remote
            git_remote = None
            git_config = item / '.git' / 'config'
            if git_config.exists():
                try:
                    import configparser
                    config = configparser.ConfigParser()
                    config.read(git_config)
                    if 'remote "origin"' in config:
                        git_remote = config['remote "origin"'].get('url')
                except Exception:
                    pass

            project_id = self.register_project(
                name=name,
                trajectory_path=trajectory_path,
                description=description,
                git_remote_url=git_remote,
            )

            discovered.append({
                'id': project_id,
                'name': name,
                'trajectory_path': trajectory_path,
            })

        return discovered

    def sync_project_stats(self, project_id: str) -> bool:
        """Sync statistics from a project's local database.

        Reads the project's .empirica/sessions/sessions.db and
        updates cached stats in the workspace database.

        Args:
            project_id: Project UUID

        Returns:
            True if sync succeeded
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT trajectory_path FROM global_projects WHERE id = ?",
            (project_id,)
        )
        row = cursor.fetchone()
        if not row:
            logger.warning(f"Project not found: {project_id}")
            return False

        trajectory_path = row[0]
        sessions_db = Path(trajectory_path) / 'sessions' / 'sessions.db'

        if not sessions_db.exists():
            logger.warning(f"No sessions.db found at {sessions_db}")
            return False

        try:
            project_conn = sqlite3.connect(str(sessions_db))
            project_cursor = project_conn.cursor()

            # Get transaction count from reflexes (handle missing column)
            try:
                project_cursor.execute(
                    "SELECT COUNT(DISTINCT transaction_id) FROM reflexes WHERE transaction_id IS NOT NULL"
                )
                total_transactions = project_cursor.fetchone()[0] or 0
            except sqlite3.OperationalError:
                # Column doesn't exist in older databases
                total_transactions = 0

            # Get artifact counts (handle missing tables)
            def safe_count(table: str) -> int:
                try:
                    project_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    return project_cursor.fetchone()[0] or 0
                except sqlite3.OperationalError:
                    return 0

            total_findings = safe_count("project_findings")
            total_unknowns = safe_count("project_unknowns")
            total_dead_ends = safe_count("project_dead_ends")
            total_goals = safe_count("goals")

            # Get last transaction (handle missing column)
            try:
                project_cursor.execute("""
                    SELECT transaction_id, timestamp FROM reflexes
                    WHERE transaction_id IS NOT NULL
                    ORDER BY timestamp DESC LIMIT 1
                """)
                last_tx = project_cursor.fetchone()
                last_tx_id = last_tx[0] if last_tx else None
                last_tx_ts = last_tx[1] if last_tx else None
            except sqlite3.OperationalError:
                last_tx_id = None
                last_tx_ts = None

            project_conn.close()

            # Update workspace database
            self.update_project_stats(
                project_id=project_id,
                total_transactions=total_transactions,
                total_findings=total_findings,
                total_unknowns=total_unknowns,
                total_dead_ends=total_dead_ends,
                total_goals=total_goals,
                last_transaction_id=last_tx_id,
                last_transaction_timestamp=last_tx_ts,
            )

            logger.info(f"📊 Synced stats for project {project_id[:8]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to sync project stats: {e}")
            return False
