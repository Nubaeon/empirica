#!/usr/bin/env python3
"""
Migrate handoff reports between git notes and database storage

Usage:
    python scripts/migrate_handoff_storage.py --direction git-to-db
    python scripts/migrate_handoff_storage.py --direction db-to-git
    python scripts/migrate_handoff_storage.py --direction sync  # both ways
"""

import argparse
import logging
from pathlib import Path
import sys

# Add empirica to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from empirica.core.handoff.storage import GitHandoffStorage, DatabaseHandoffStorage, HybridHandoffStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_git_to_db():
    """Migrate handoffs from git notes to database"""
    logger.info("📝→📊 Migrating git notes → database...")

    git_storage = GitHandoffStorage()
    db_storage = DatabaseHandoffStorage()

    # Get all session IDs from git notes
    session_ids = git_storage.list_handoffs()
    logger.info(f"Found {len(session_ids)} handoffs in git notes")

    migrated = 0
    skipped = 0
    errors = 0

    for session_id in session_ids:
        try:
            # Check if already in database
            existing = db_storage.load_handoff(session_id)
            if existing:
                logger.debug(f"⏭️  Skipping {session_id[:8]}... (already in database)")
                skipped += 1
                continue

            # Load from git notes
            handoff = git_storage.load_handoff(session_id)
            if not handoff:
                logger.warning(f"⚠️ Could not load {session_id[:8]}... from git notes")
                errors += 1
                continue

            # Store in database
            db_storage.store_handoff(session_id, handoff)
            logger.info(f"✅ Migrated {session_id[:8]}...")
            migrated += 1

        except Exception as e:
            logger.error(f"❌ Error migrating {session_id[:8]}...: {e}")
            errors += 1

    logger.info(f"\n📊 Migration complete!")
    logger.info(f"   Migrated: {migrated}")
    logger.info(f"   Skipped: {skipped}")
    logger.info(f"   Errors: {errors}")

    return migrated, skipped, errors


def migrate_db_to_git():
    """Migrate handoffs from database to git notes"""
    logger.info("📊→📝 Migrating database → git notes...")

    git_storage = GitHandoffStorage()
    db_storage = DatabaseHandoffStorage()

    # Get all session IDs from database
    session_ids = db_storage.list_handoffs()
    logger.info(f"Found {len(session_ids)} handoffs in database")

    migrated = 0
    skipped = 0
    errors = 0

    for session_id in session_ids:
        try:
            # Check if already in git notes
            existing = git_storage.load_handoff(session_id)
            if existing:
                logger.debug(f"⏭️  Skipping {session_id[:8]}... (already in git notes)")
                skipped += 1
                continue

            # Load from database
            handoff = db_storage.load_handoff(session_id)
            if not handoff:
                logger.warning(f"⚠️ Could not load {session_id[:8]}... from database")
                errors += 1
                continue

            # Store in git notes
            git_storage.store_handoff(session_id, handoff)
            logger.info(f"✅ Migrated {session_id[:8]}...")
            migrated += 1

        except Exception as e:
            logger.error(f"❌ Error migrating {session_id[:8]}...: {e}")
            errors += 1

    logger.info(f"\n📊 Migration complete!")
    logger.info(f"   Migrated: {migrated}")
    logger.info(f"   Skipped: {skipped}")
    logger.info(f"   Errors: {errors}")

    return migrated, skipped, errors


def sync_both_ways():
    """Sync handoffs in both directions"""
    logger.info("🔄 Syncing handoffs (both directions)...")

    # Git → Database
    git_to_db = migrate_git_to_db()

    print("\n" + "="*60 + "\n")

    # Database → Git
    db_to_git = migrate_db_to_git()

    logger.info(f"\n✅ Full sync complete!")
    logger.info(f"   Git→DB: {git_to_db[0]} migrated, {git_to_db[1]} skipped, {git_to_db[2]} errors")
    logger.info(f"   DB→Git: {db_to_git[0]} migrated, {db_to_git[1]} skipped, {db_to_git[2]} errors")


def check_sync_status():
    """Check sync status of all handoffs"""
    logger.info("🔍 Checking sync status...")

    hybrid = HybridHandoffStorage()

    git_storage = GitHandoffStorage()
    db_storage = DatabaseHandoffStorage()

    git_ids = set(git_storage.list_handoffs())
    db_ids = set(db_storage.list_handoffs())

    logger.info(f"\n📊 Storage Status:")
    logger.info(f"   Git notes: {len(git_ids)} handoffs")
    logger.info(f"   Database: {len(db_ids)} handoffs")

    only_git = git_ids - db_ids
    only_db = db_ids - git_ids
    in_both = git_ids & db_ids

    logger.info(f"\n🔄 Sync Status:")
    logger.info(f"   ✅ In both: {len(in_both)}")
    logger.info(f"   ⚠️ Only in git: {len(only_git)}")
    logger.info(f"   ⚠️ Only in database: {len(only_db)}")

    if only_git:
        logger.warning(f"\n📝 Only in git notes:")
        for sid in sorted(only_git)[:10]:
            logger.warning(f"   - {sid}")

    if only_db:
        logger.warning(f"\n📊 Only in database:")
        for sid in sorted(only_db)[:10]:
            logger.warning(f"   - {sid}")

    if len(in_both) == len(git_ids) == len(db_ids):
        logger.info(f"\n✅ All handoffs fully synced!")
        return True
    else:
        logger.warning(f"\n⚠️ Some handoffs not synced!")
        return False


def main():
    parser = argparse.ArgumentParser(description='Migrate handoff storage')
    parser.add_argument(
        '--direction',
        choices=['git-to-db', 'db-to-git', 'sync', 'status'],
        required=True,
        help='Migration direction'
    )

    args = parser.parse_args()

    if args.direction == 'git-to-db':
        migrate_git_to_db()
    elif args.direction == 'db-to-git':
        migrate_db_to_git()
    elif args.direction == 'sync':
        sync_both_ways()
    elif args.direction == 'status':
        check_sync_status()


if __name__ == '__main__':
    main()