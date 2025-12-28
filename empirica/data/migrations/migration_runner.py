"""Migration runner with tracking for database schema changes"""
import sqlite3
from typing import Callable, List, Tuple
from datetime import datetime


class MigrationRunner:
    """Manages database migrations with execution tracking"""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._ensure_migrations_table()

    def _ensure_migrations_table(self):
        """Create migrations tracking table if it doesn't exist"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                migration_id TEXT PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)
        self.conn.commit()

    def has_run(self, migration_id: str) -> bool:
        """Check if a migration has already been executed"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM schema_migrations WHERE migration_id = ?",
            (migration_id,)
        )
        return cursor.fetchone()[0] > 0

    def mark_as_run(self, migration_id: str, description: str = ""):
        """Mark a migration as executed"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO schema_migrations (migration_id, description) VALUES (?, ?)",
            (migration_id, description)
        )
        self.conn.commit()

    def run_migration(self, migration_id: str, description: str, migration_func: Callable):
        """
        Run a migration if it hasn't been executed yet

        Args:
            migration_id: Unique identifier (e.g., "20240101_add_status_column")
            description: Human-readable description
            migration_func: Function that executes the migration (takes cursor as arg)
        """
        if self.has_run(migration_id):
            return  # Already applied

        cursor = self.conn.cursor()
        try:
            migration_func(cursor)
            self.mark_as_run(migration_id, description)
        except Exception as e:
            # Re-raise with context
            raise RuntimeError(f"Migration {migration_id} failed: {e}") from e

    def run_all(self, migrations: List[Tuple[str, str, Callable]]):
        """
        Run all pending migrations

        Args:
            migrations: List of (migration_id, description, migration_func) tuples
        """
        for migration_id, description, migration_func in migrations:
            self.run_migration(migration_id, description, migration_func)


def column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    """Check if a column exists in a table"""
    cursor.execute(f"SELECT COUNT(*) FROM pragma_table_info('{table}') WHERE name='{column}'")
    return cursor.fetchone()[0] > 0


def add_column_if_missing(cursor: sqlite3.Cursor, table: str, column: str, column_type: str, default: str = ""):
    """Add a column to a table if it doesn't already exist"""
    if not column_exists(cursor, table, column):
        default_clause = f" DEFAULT {default}" if default else ""
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}{default_clause}")
