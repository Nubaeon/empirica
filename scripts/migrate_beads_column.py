#!/usr/bin/env python3
"""
Database migration: Add beads_issue_id column to goals table

This migration adds optional BEADS integration support to Empirica goals.
"""

import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_database(db_path: str):
    """Add beads_issue_id column to goals table"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(goals)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'beads_issue_id' in columns:
            logger.info("✅ Column 'beads_issue_id' already exists in goals table")
            return
        
        # Add column
        logger.info("Adding 'beads_issue_id' column to goals table...")
        cursor.execute("ALTER TABLE goals ADD COLUMN beads_issue_id TEXT")
        
        # Create index
        logger.info("Creating index on beads_issue_id...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_beads_issue_id ON goals(beads_issue_id)")
        
        conn.commit()
        logger.info("✅ Migration complete!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    # Find .empirica database
    empirica_dir = Path.cwd() / ".empirica"
    db_path = empirica_dir / "empirica_sessions.db"
    
    if not db_path.exists():
        logger.error(f"❌ Database not found: {db_path}")
        logger.info("Run this from a directory with .empirica/ initialized")
        exit(1)
    
    logger.info(f"📊 Migrating database: {db_path}")
    migrate_database(str(db_path))
