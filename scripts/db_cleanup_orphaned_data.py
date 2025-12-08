#!/usr/bin/env python3
"""
Empirica Database Cleanup - Orphaned Data Removal

Removes orphaned records that violate referential integrity:
- Goals without parent sessions
- Subtasks without parent goals
- Reflexes without parent sessions

Usage:
    python scripts/db_cleanup_orphaned_data.py --dry-run  # Preview only
    python scripts/db_cleanup_orphaned_data.py --execute  # Actually delete
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from empirica.data.session_database import SessionDatabase


def check_orphaned_data(db):
    """Check for orphaned data and return counts"""
    cursor = db.conn.cursor()
    
    # Orphaned goals
    cursor.execute("""
        SELECT COUNT(*) FROM goals g
        WHERE NOT EXISTS (SELECT 1 FROM sessions s WHERE s.session_id = g.session_id);
    """)
    orphaned_goals = cursor.fetchone()[0]
    
    # Orphaned subtasks
    cursor.execute("""
        SELECT COUNT(*) FROM subtasks st
        WHERE NOT EXISTS (SELECT 1 FROM goals g WHERE g.id = st.goal_id);
    """)
    orphaned_subtasks = cursor.fetchone()[0]
    
    # Orphaned reflexes
    cursor.execute("""
        SELECT COUNT(*) FROM reflexes r
        WHERE NOT EXISTS (SELECT 1 FROM sessions s WHERE s.session_id = r.session_id);
    """)
    orphaned_reflexes = cursor.fetchone()[0]
    
    return {
        'goals': orphaned_goals,
        'subtasks': orphaned_subtasks,
        'reflexes': orphaned_reflexes,
        'total': orphaned_goals + orphaned_subtasks + orphaned_reflexes
    }


def get_orphaned_details(db):
    """Get details of orphaned records for logging"""
    cursor = db.conn.cursor()
    
    print("\n📋 Orphaned Data Details:\n")
    
    # Orphaned goals
    print("🎯 Orphaned Goals:")
    cursor.execute("""
        SELECT g.id, g.objective, g.session_id
        FROM goals g
        WHERE NOT EXISTS (SELECT 1 FROM sessions s WHERE s.session_id = g.session_id)
        LIMIT 10;
    """)
    for row in cursor.fetchall():
        goal_id, objective, session_id = row
        session_display = session_id[:8] + "..." if session_id else "NULL"
        print(f"   - {objective[:50]:50} | session: {session_display:12} | id: {goal_id[:8]}...")
    
    # Orphaned subtasks
    print("\n📋 Orphaned Subtasks:")
    cursor.execute("""
        SELECT st.id, st.description, st.goal_id
        FROM subtasks st
        WHERE NOT EXISTS (SELECT 1 FROM goals g WHERE g.id = st.goal_id)
        LIMIT 10;
    """)
    for row in cursor.fetchall():
        subtask_id, description, goal_id = row
        goal_display = goal_id[:8] + "..." if goal_id else "NULL"
        print(f"   - {description[:50]:50} | goal: {goal_display:12} | id: {subtask_id[:8]}...")
    
    # Orphaned reflexes
    print("\n🔄 Orphaned Reflexes:")
    cursor.execute("""
        SELECT r.id, r.session_id, r.phase, r.round, r.timestamp
        FROM reflexes r
        WHERE NOT EXISTS (SELECT 1 FROM sessions s WHERE s.session_id = r.session_id)
        LIMIT 10;
    """)
    for row in cursor.fetchall():
        reflex_id, session_id, phase, round_num, timestamp = row
        print(f"   - {phase:12} round {round_num} | session: {session_id[:8]}... | id: {reflex_id}")


def cleanup_orphaned_data(db, dry_run=True):
    """Clean up orphaned data"""
    
    print("\n" + "="*70)
    print("EMPIRICA DATABASE CLEANUP - Orphaned Data Removal")
    print("="*70)
    
    # Check current state
    before = check_orphaned_data(db)
    
    print(f"\n📊 Current State:")
    print(f"   Orphaned goals:    {before['goals']}")
    print(f"   Orphaned subtasks: {before['subtasks']}")
    print(f"   Orphaned reflexes: {before['reflexes']}")
    print(f"   Total orphaned:    {before['total']}")
    
    if before['total'] == 0:
        print("\n✅ No orphaned data found. Database is clean!")
        return
    
    # Show details
    get_orphaned_details(db)
    
    if dry_run:
        print("\n" + "="*70)
        print("🔍 DRY RUN MODE - No changes will be made")
        print("="*70)
        print("\nTo actually delete orphaned data, run:")
        print("  python scripts/db_cleanup_orphaned_data.py --execute")
        return
    
    # Execute cleanup
    print("\n" + "="*70)
    print("🚨 EXECUTING CLEANUP - Deleting orphaned data")
    print("="*70)
    
    cursor = db.conn.cursor()
    
    # Delete orphaned reflexes first (no dependencies)
    print("\n1️⃣  Deleting orphaned reflexes...")
    cursor.execute("""
        DELETE FROM reflexes 
        WHERE NOT EXISTS (SELECT 1 FROM sessions s WHERE s.session_id = reflexes.session_id);
    """)
    reflexes_deleted = cursor.rowcount
    print(f"   ✅ Deleted {reflexes_deleted} orphaned reflexes")
    
    # Delete orphaned subtasks (depend on goals)
    print("\n2️⃣  Deleting orphaned subtasks...")
    cursor.execute("""
        DELETE FROM subtasks 
        WHERE NOT EXISTS (SELECT 1 FROM goals g WHERE g.id = subtasks.goal_id);
    """)
    subtasks_deleted = cursor.rowcount
    print(f"   ✅ Deleted {subtasks_deleted} orphaned subtasks")
    
    # Delete orphaned goals (depend on sessions)
    print("\n3️⃣  Deleting orphaned goals...")
    cursor.execute("""
        DELETE FROM goals 
        WHERE NOT EXISTS (SELECT 1 FROM sessions s WHERE s.session_id = goals.session_id);
    """)
    goals_deleted = cursor.rowcount
    print(f"   ✅ Deleted {goals_deleted} orphaned goals")
    
    # Commit changes
    db.conn.commit()
    print("\n✅ Cleanup committed to database")
    
    # Check final state
    after = check_orphaned_data(db)
    
    print("\n" + "="*70)
    print("📊 Final State:")
    print("="*70)
    print(f"   Orphaned goals:    {after['goals']} (was {before['goals']})")
    print(f"   Orphaned subtasks: {after['subtasks']} (was {before['subtasks']})")
    print(f"   Orphaned reflexes: {after['reflexes']} (was {before['reflexes']})")
    print(f"   Total orphaned:    {after['total']} (was {before['total']})")
    
    print(f"\n✅ Deleted {before['total']} orphaned records")
    print(f"   - {goals_deleted} goals")
    print(f"   - {subtasks_deleted} subtasks")
    print(f"   - {reflexes_deleted} reflexes")
    
    if after['total'] == 0:
        print("\n🎉 Database integrity restored!")
    else:
        print(f"\n⚠️  Warning: {after['total']} orphaned records remain")


def main():
    parser = argparse.ArgumentParser(
        description='Clean up orphaned data from Empirica database'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without executing (default)'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually execute the cleanup'
    )
    
    args = parser.parse_args()
    
    # Default to dry-run if neither specified
    dry_run = not args.execute
    
    db = SessionDatabase()
    try:
        cleanup_orphaned_data(db, dry_run=dry_run)
    finally:
        db.close()


if __name__ == '__main__':
    main()
