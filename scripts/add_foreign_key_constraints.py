#!/usr/bin/env python3
"""
Add Foreign Key Constraints to Empirica Database

Adds proper foreign key constraints with CASCADE DELETE to prevent orphaned data.

SQLite doesn't support ALTER TABLE ADD CONSTRAINT for foreign keys,
so we need to recreate tables with constraints.

Usage:
    python scripts/add_foreign_key_constraints.py --dry-run   # Preview
    python scripts/add_foreign_key_constraints.py --execute   # Apply changes
"""

import argparse
import sys
import sqlite3
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from empirica.data.session_database import SessionDatabase


def backup_database(db_path):
    """Create backup of database before making changes"""
    backup_path = f"{db_path}.backup.{int(time.time())}"
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✅ Database backed up to: {backup_path}")
    return backup_path


def check_current_constraints(db):
    """Check if foreign key constraints already exist"""
    cursor = db.conn.cursor()
    
    # Check goals table
    cursor.execute("PRAGMA foreign_key_list(goals);")
    goals_fks = cursor.fetchall()
    
    # Check subtasks table
    cursor.execute("PRAGMA foreign_key_list(subtasks);")
    subtasks_fks = cursor.fetchall()
    
    # Check reflexes table
    cursor.execute("PRAGMA foreign_key_list(reflexes);")
    reflexes_fks = cursor.fetchall()
    
    print("\n📊 Current Foreign Key Constraints:\n")
    print(f"   Goals table:    {len(goals_fks)} constraint(s)")
    print(f"   Subtasks table: {len(subtasks_fks)} constraint(s)")
    print(f"   Reflexes table: {len(reflexes_fks)} constraint(s)")
    
    return {
        'goals': goals_fks,
        'subtasks': subtasks_fks,
        'reflexes': reflexes_fks
    }


def add_foreign_key_constraints(db, dry_run=True):
    """Add foreign key constraints to tables"""
    
    print("\n" + "="*70)
    print("EMPIRICA DATABASE - Add Foreign Key Constraints")
    print("="*70)
    
    # Check current state
    current_fks = check_current_constraints(db)
    
    # Check if constraints already exist
    has_goals_fk = len(current_fks['goals']) > 0
    has_subtasks_fk = len(current_fks['subtasks']) > 0
    has_reflexes_fk = len(current_fks['reflexes']) > 0
    
    if has_goals_fk and has_subtasks_fk and has_reflexes_fk:
        print("\n✅ Foreign key constraints already exist on all tables!")
        print("   No changes needed.")
        return
    
    if dry_run:
        print("\n" + "="*70)
        print("🔍 DRY RUN MODE - No changes will be made")
        print("="*70)
        
        print("\n📝 Planned Changes:\n")
        
        if not has_goals_fk:
            print("   ✏️  Add FK to goals table:")
            print("      - session_id → sessions(session_id) ON DELETE CASCADE")
        
        if not has_subtasks_fk:
            print("   ✏️  Add FK to subtasks table:")
            print("      - goal_id → goals(id) ON DELETE CASCADE")
        
        if not has_reflexes_fk:
            print("   ✏️  Add FK to reflexes table:")
            print("      - session_id → sessions(session_id) ON DELETE CASCADE")
        
        print("\n⚠️  Note: SQLite requires table recreation to add foreign keys")
        print("   This is a safe operation - all data will be preserved.")
        
        print("\nTo apply changes, run:")
        print("  python scripts/add_foreign_key_constraints.py --execute")
        return
    
    print("\n" + "="*70)
    print("🚨 APPLYING FOREIGN KEY CONSTRAINTS")
    print("="*70)
    
    cursor = db.conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # Backup current data counts
    cursor.execute("SELECT COUNT(*) FROM goals;")
    goals_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM subtasks;")
    subtasks_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM reflexes;")
    reflexes_count = cursor.fetchone()[0]
    
    print(f"\n📊 Current data:")
    print(f"   Goals:    {goals_count}")
    print(f"   Subtasks: {subtasks_count}")
    print(f"   Reflexes: {reflexes_count}")
    
    # 1. Add FK to reflexes table (if needed)
    if not has_reflexes_fk:
        print("\n1️⃣  Adding FK to reflexes table...")
        
        # Get table schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='reflexes';")
        original_schema = cursor.fetchone()[0]
        
        # Create new table with FK
        cursor.execute("""
            CREATE TABLE reflexes_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                cascade_id TEXT,
                phase TEXT NOT NULL,
                round INTEGER DEFAULT 1,
                timestamp REAL NOT NULL,
                engagement REAL,
                know REAL,
                do REAL,
                context REAL,
                clarity REAL,
                coherence REAL,
                signal REAL,
                density REAL,
                state REAL,
                change REAL,
                completion REAL,
                impact REAL,
                uncertainty REAL,
                reflex_data TEXT,
                reasoning TEXT,
                evidence TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            );
        """)
        
        # Copy data
        cursor.execute("""
            INSERT INTO reflexes_new 
            SELECT * FROM reflexes;
        """)
        
        # Verify data copied
        cursor.execute("SELECT COUNT(*) FROM reflexes_new;")
        new_count = cursor.fetchone()[0]
        
        if new_count != reflexes_count:
            raise Exception(f"Data copy failed! Expected {reflexes_count}, got {new_count}")
        
        # Drop old table and rename
        cursor.execute("DROP TABLE reflexes;")
        cursor.execute("ALTER TABLE reflexes_new RENAME TO reflexes;")
        
        # Recreate indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reflexes_session ON reflexes(session_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reflexes_phase ON reflexes(phase);")
        
        print("   ✅ FK added to reflexes table")
    
    # 2. Add FK to subtasks table (if needed)
    if not has_subtasks_fk:
        print("\n2️⃣  Adding FK to subtasks table...")
        
        cursor.execute("""
            CREATE TABLE subtasks_new (
                id TEXT PRIMARY KEY,
                goal_id TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                epistemic_importance TEXT,
                estimated_tokens INTEGER,
                actual_tokens INTEGER,
                completion_evidence TEXT,
                notes TEXT,
                created_timestamp REAL,
                completed_timestamp REAL,
                subtask_data TEXT,
                FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE
            );
        """)
        
        cursor.execute("INSERT INTO subtasks_new SELECT * FROM subtasks;")
        
        cursor.execute("SELECT COUNT(*) FROM subtasks_new;")
        new_count = cursor.fetchone()[0]
        
        if new_count != subtasks_count:
            raise Exception(f"Data copy failed! Expected {subtasks_count}, got {new_count}")
        
        cursor.execute("DROP TABLE subtasks;")
        cursor.execute("ALTER TABLE subtasks_new RENAME TO subtasks;")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_subtasks_goal ON subtasks(goal_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_subtasks_status ON subtasks(status);")
        
        print("   ✅ FK added to subtasks table")
    
    # 3. Add FK to goals table (if needed)
    if not has_goals_fk:
        print("\n3️⃣  Adding FK to goals table...")
        
        cursor.execute("""
            CREATE TABLE goals_new (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                objective TEXT NOT NULL,
                scope TEXT,
                estimated_complexity REAL,
                created_timestamp REAL,
                completed_timestamp REAL,
                is_completed BOOLEAN DEFAULT 0,
                goal_data TEXT,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            );
        """)
        
        cursor.execute("INSERT INTO goals_new SELECT * FROM goals;")
        
        cursor.execute("SELECT COUNT(*) FROM goals_new;")
        new_count = cursor.fetchone()[0]
        
        if new_count != goals_count:
            raise Exception(f"Data copy failed! Expected {goals_count}, got {new_count}")
        
        cursor.execute("DROP TABLE goals;")
        cursor.execute("ALTER TABLE goals_new RENAME TO goals;")
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_session ON goals(session_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);")
        
        print("   ✅ FK added to goals table")
    
    # Commit changes
    db.conn.commit()
    
    print("\n✅ All foreign key constraints applied successfully!")
    
    # Verify final state
    print("\n" + "="*70)
    print("📊 Verification:")
    print("="*70)
    
    final_fks = check_current_constraints(db)
    
    cursor.execute("SELECT COUNT(*) FROM goals;")
    final_goals = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM subtasks;")
    final_subtasks = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM reflexes;")
    final_reflexes = cursor.fetchone()[0]
    
    print(f"\n📊 Final data counts:")
    print(f"   Goals:    {final_goals} (was {goals_count}) {'✅' if final_goals == goals_count else '❌'}")
    print(f"   Subtasks: {final_subtasks} (was {subtasks_count}) {'✅' if final_subtasks == subtasks_count else '❌'}")
    print(f"   Reflexes: {final_reflexes} (was {reflexes_count}) {'✅' if final_reflexes == reflexes_count else '❌'}")
    
    if final_goals == goals_count and final_subtasks == subtasks_count and final_reflexes == reflexes_count:
        print("\n🎉 All data preserved! Foreign key constraints active.")
    else:
        print("\n⚠️  Warning: Data counts changed!")


def main():
    parser = argparse.ArgumentParser(
        description='Add foreign key constraints to Empirica database'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without executing (default)'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually execute the changes'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        default=True,
        help='Create backup before changes (default: True)'
    )
    
    args = parser.parse_args()
    
    # Default to dry-run if neither specified
    dry_run = not args.execute
    
    db = SessionDatabase()
    
    try:
        # Create backup before making changes
        if args.execute and args.backup:
            backup_database(db.db_path)
        
        add_foreign_key_constraints(db, dry_run=dry_run)
        
    finally:
        db.close()


if __name__ == '__main__':
    main()
