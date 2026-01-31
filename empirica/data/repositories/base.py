"""
Base repository class for shared database connection handling.

Design Pattern: Repository Pattern
- Each repository is stateless (just wraps SQL queries)
- All repositories share a single database connection (passed in constructor)
- Transactions are managed by the coordinator (SessionDatabase)
- Supports both SQLite and PostgreSQL connections
"""

import sqlite3
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base class for all domain repositories"""

    def __init__(self, conn):
        """
        Initialize repository with shared database connection.

        Args:
            conn: Database connection (SQLite or PostgreSQL, shared across all repositories)
        """
        self.conn = conn
        # Only set row_factory for SQLite connections
        # PostgreSQL adapter handles dict results via RealDictCursor
        if isinstance(conn, sqlite3.Connection):
            self.conn.row_factory = sqlite3.Row

    def _execute(self, query: str, params: Optional[tuple] = None):
        """
        Execute a SQL query with optional parameters.

        Handles dialect differences: converts SQLite ? placeholders to PostgreSQL %s
        when running on a psycopg2 connection.

        Args:
            query: SQL query string (uses ? placeholders)
            params: Optional tuple of query parameters

        Returns:
            Cursor object with results
        """
        # Convert placeholders for PostgreSQL
        if not isinstance(self.conn, sqlite3.Connection):
            query = query.replace("?", "%s")

        cursor = self.conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor

    def _execute_many(self, query: str, params_list: list) -> sqlite3.Cursor:
        """
        Execute a SQL query multiple times with different parameters.

        Args:
            query: SQL query string
            params_list: List of parameter tuples

        Returns:
            Cursor object
        """
        cursor = self.conn.cursor()
        cursor.executemany(query, params_list)
        return cursor

    def commit(self):
        """Commit the current transaction"""
        self.conn.commit()

    def rollback(self):
        """Rollback the current transaction"""
        self.conn.rollback()
