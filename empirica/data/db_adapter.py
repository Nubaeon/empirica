#!/usr/bin/env python3
"""
Database Adapter Layer - Abstract interface for multiple database backends

Supports:
- SQLite (default, embedded, zero-ops)
- PostgreSQL (production, multi-agent, enterprise)

Design:
- Clean adapter pattern
- Minimal interface (execute, fetchone, fetchall, commit, close)
- Transparent connection management
- Feature flag support via config.yaml

Usage:
    adapter = DatabaseAdapter.create(db_type="sqlite", db_path="sessions.db")
    adapter.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = adapter.fetchone()
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters"""

    @staticmethod
    def create(db_type: str = "sqlite", **kwargs) -> "DatabaseAdapter":
        """
        Factory method to create appropriate database adapter

        Args:
            db_type: "sqlite" or "postgresql"
            **kwargs: Database-specific configuration

        Returns:
            DatabaseAdapter instance

        Example:
            # SQLite
            adapter = DatabaseAdapter.create(
                db_type="sqlite",
                db_path="./.empirica/sessions/sessions.db"
            )

            # PostgreSQL
            adapter = DatabaseAdapter.create(
                db_type="postgresql",
                host="localhost",
                port=5432,
                database="empirica",
                user="empirica",
                password="secret"
            )
        """
        if db_type == "sqlite":
            return SQLiteAdapter(**kwargs)
        elif db_type == "postgresql":
            return PostgreSQLAdapter(**kwargs)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    @abstractmethod
    def execute(self, query: str, params: Optional[Tuple] = None) -> "DatabaseAdapter":
        """Execute a query with optional parameters"""
        pass

    @abstractmethod
    def fetchone(self) -> Optional[Dict[str, Any]]:
        """Fetch one row as dictionary"""
        pass

    @abstractmethod
    def fetchall(self) -> List[Dict[str, Any]]:
        """Fetch all rows as list of dictionaries"""
        pass

    @abstractmethod
    def commit(self):
        """Commit current transaction"""
        pass

    @abstractmethod
    def rollback(self):
        """Rollback current transaction"""
        pass

    @abstractmethod
    def close(self):
        """Close database connection"""
        pass

    @property
    @abstractmethod
    def conn(self):
        """Return raw connection object (for repositories)"""
        pass


class SQLiteAdapter(DatabaseAdapter):
    """SQLite implementation of database adapter"""

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize SQLite adapter

        Args:
            db_path: Path to SQLite database file
        """
        import sqlite3

        if db_path is None:
            from empirica.config.path_resolver import get_session_db_path
            db_path = str(get_session_db_path())

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Enable timeout for database lock waits (30 seconds)
        self._conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        self._conn.row_factory = sqlite3.Row  # Return rows as dicts

        # Enable WAL mode for better concurrency
        # WAL allows readers and writers to work simultaneously
        self._conn.execute("PRAGMA journal_mode=WAL")

        # Set busy timeout (additional layer of protection)
        self._conn.execute("PRAGMA busy_timeout=30000")  # 30 seconds in milliseconds

        self._cursor = None

        logger.info(f"📊 SQLite adapter initialized: {self.db_path} (WAL mode enabled)")

    @property
    def conn(self):
        """Return raw SQLite connection"""
        return self._conn

    def execute(self, query: str, params: Optional[Tuple] = None) -> "SQLiteAdapter":
        """Execute a query with optional parameters"""
        self._cursor = self._conn.cursor()
        if params:
            self._cursor.execute(query, params)
        else:
            self._cursor.execute(query)
        return self

    def fetchone(self) -> Optional[Dict[str, Any]]:
        """Fetch one row as dictionary"""
        if self._cursor is None:
            return None
        row = self._cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def fetchall(self) -> List[Dict[str, Any]]:
        """Fetch all rows as list of dictionaries"""
        if self._cursor is None:
            return []
        rows = self._cursor.fetchall()
        return [dict(row) for row in rows]

    def commit(self):
        """Commit current transaction"""
        self._conn.commit()

    def rollback(self):
        """Rollback current transaction"""
        self._conn.rollback()

    def close(self):
        """Close database connection"""
        if self._cursor:
            self._cursor.close()
        self._conn.close()
        logger.info(f"📊 SQLite adapter closed: {self.db_path}")


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL implementation of database adapter"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "empirica",
        user: str = "empirica",
        password: str = "",
        **kwargs
    ):
        """
        Initialize PostgreSQL adapter

        Args:
            host: PostgreSQL server host
            port: PostgreSQL server port
            database: Database name
            user: Database user
            password: Database password
            **kwargs: Additional psycopg2 connection parameters
        """
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError:
            raise ImportError(
                "PostgreSQL support requires psycopg2. Install with: pip install psycopg2-binary"
            )

        self._conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            **kwargs
        )
        self._cursor = None

        logger.info(f"📊 PostgreSQL adapter initialized: {host}:{port}/{database}")

    @property
    def conn(self):
        """Return raw psycopg2 connection"""
        return self._conn

    def execute(self, query: str, params: Optional[Tuple] = None) -> "PostgreSQLAdapter":
        """
        Execute a query with optional parameters

        Note: Converts SQLite-style ? placeholders to PostgreSQL %s
        """
        import psycopg2.extras

        # Convert SQLite ? to PostgreSQL %s
        pg_query = query.replace("?", "%s")

        self._cursor = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if params:
            self._cursor.execute(pg_query, params)
        else:
            self._cursor.execute(pg_query)
        return self

    def fetchone(self) -> Optional[Dict[str, Any]]:
        """Fetch one row as dictionary"""
        if self._cursor is None:
            return None
        row = self._cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def fetchall(self) -> List[Dict[str, Any]]:
        """Fetch all rows as list of dictionaries"""
        if self._cursor is None:
            return []
        rows = self._cursor.fetchall()
        return [dict(row) for row in rows]

    def commit(self):
        """Commit current transaction"""
        self._conn.commit()

    def rollback(self):
        """Rollback current transaction"""
        self._conn.rollback()

    def close(self):
        """Close database connection"""
        if self._cursor:
            self._cursor.close()
        self._conn.close()
        logger.info("📊 PostgreSQL adapter closed")
