"""Database schema migrations"""
import sqlite3
from typing import List, Tuple, Callable
from .migration_runner import add_column_if_missing


# Migration 1: Add CASCADE workflow columns to cascades table
def migration_001_cascade_workflow_columns(cursor: sqlite3.Cursor):
    """Add preflight/plan/postflight tracking columns to cascades"""
    add_column_if_missing(cursor, "cascades", "preflight_completed", "BOOLEAN", "0")
    add_column_if_missing(cursor, "cascades", "plan_completed", "BOOLEAN", "0")
    add_column_if_missing(cursor, "cascades", "postflight_completed", "BOOLEAN", "0")


# Migration 2: Add epistemic delta tracking to cascades
def migration_002_epistemic_delta(cursor: sqlite3.Cursor):
    """Add epistemic_delta JSON column to cascades"""
    add_column_if_missing(cursor, "cascades", "epistemic_delta", "TEXT")


# Migration 3: Add goal tracking to cascades
def migration_003_cascade_goal_tracking(cursor: sqlite3.Cursor):
    """Add goal_id and goal_json to cascades"""
    add_column_if_missing(cursor, "cascades", "goal_id", "TEXT")
    add_column_if_missing(cursor, "cascades", "goal_json", "TEXT")


# Migration 4: Add status column to goals
def migration_004_goals_status(cursor: sqlite3.Cursor):
    """Add status tracking to goals table"""
    add_column_if_missing(cursor, "goals", "status", "TEXT", "'in_progress'")


# Migration 5: Add project_id to sessions
def migration_005_sessions_project_id(cursor: sqlite3.Cursor):
    """Add project_id foreign key to sessions"""
    add_column_if_missing(cursor, "sessions", "project_id", "TEXT")


# Migration 6: Add subject filtering to sessions
def migration_006_sessions_subject(cursor: sqlite3.Cursor):
    """Add subject column to sessions for filtering"""
    add_column_if_missing(cursor, "sessions", "subject", "TEXT")


# Migration 7: Add impact scoring to project_findings
def migration_007_findings_impact(cursor: sqlite3.Cursor):
    """Add impact column to project_findings for importance weighting"""
    add_column_if_missing(cursor, "project_findings", "impact", "REAL")


# Migration 8: Migrate legacy tables to reflexes
def migration_008_migrate_legacy_to_reflexes(cursor: sqlite3.Cursor):
    """
    Migrate data from deprecated tables to reflexes table, then drop old tables.

    This runs automatically on database initialization. It's idempotent - safe to run multiple times.

    Migration mapping:
    - preflight_assessments → reflexes (phase='PREFLIGHT')
    - postflight_assessments → reflexes (phase='POSTFLIGHT')
    - check_phase_assessments → reflexes (phase='CHECK')
    - epistemic_assessments → (unused, just drop)
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Check if old tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='preflight_assessments'")
        if not cursor.fetchone():
            logger.debug("✓ Legacy tables already migrated or don't exist")
            return  # Already migrated

        logger.info("🔄 Migrating legacy epistemic tables to reflexes...")

        # Migrate preflight_assessments → reflexes
        cursor.execute("""
            INSERT INTO reflexes (session_id, cascade_id, phase, round, timestamp,
                                engagement, know, do, context, clarity, coherence, signal, density,
                                state, change, completion, impact, uncertainty, reflex_data, reasoning)
            SELECT session_id, cascade_id, 'PREFLIGHT', 1,
                   CAST(strftime('%s', assessed_at) AS REAL),
                   engagement, know, do, context, clarity, coherence, signal, density,
                   state, change, completion, impact, uncertainty,
                   vectors_json, initial_uncertainty_notes
            FROM preflight_assessments
            WHERE NOT EXISTS (
                SELECT 1 FROM reflexes r
                WHERE r.session_id = preflight_assessments.session_id
                AND r.phase = 'PREFLIGHT'
                AND r.cascade_id IS preflight_assessments.cascade_id
            )
        """)
        preflight_count = cursor.rowcount
        logger.info(f"  ✓ Migrated {preflight_count} preflight assessments")

        # Migrate postflight_assessments → reflexes
        cursor.execute("""
            INSERT INTO reflexes (session_id, cascade_id, phase, round, timestamp,
                                engagement, know, do, context, clarity, coherence, signal, density,
                                state, change, completion, impact, uncertainty, reflex_data, reasoning)
            SELECT session_id, cascade_id, 'POSTFLIGHT', 1,
                   CAST(strftime('%s', assessed_at) AS REAL),
                   engagement, know, do, context, clarity, coherence, signal, density,
                   state, change, completion, impact, uncertainty,
                   json_object('calibration_accuracy', calibration_accuracy,
                               'postflight_confidence', postflight_actual_confidence),
                   learning_notes
            FROM postflight_assessments
            WHERE NOT EXISTS (
                SELECT 1 FROM reflexes r
                WHERE r.session_id = postflight_assessments.session_id
                AND r.phase = 'POSTFLIGHT'
                AND r.cascade_id IS postflight_assessments.cascade_id
            )
        """)
        postflight_count = cursor.rowcount
        logger.info(f"  ✓ Migrated {postflight_count} postflight assessments")

        # Migrate check_phase_assessments → reflexes (confidence → uncertainty conversion)
        cursor.execute("""
            INSERT INTO reflexes (session_id, cascade_id, phase, round, timestamp,
                                uncertainty, reflex_data, reasoning)
            SELECT session_id, cascade_id, 'CHECK', investigation_cycle,
                   CAST(strftime('%s', assessed_at) AS REAL),
                   (1.0 - confidence),
                   json_object('decision', decision,
                               'gaps_identified', gaps_identified,
                               'next_investigation_targets', next_investigation_targets,
                               'confidence', confidence),
                   self_assessment_notes
            FROM check_phase_assessments
            WHERE NOT EXISTS (
                SELECT 1 FROM reflexes r
                WHERE r.session_id = check_phase_assessments.session_id
                AND r.phase = 'CHECK'
                AND r.cascade_id IS check_phase_assessments.cascade_id
                AND r.round = check_phase_assessments.investigation_cycle
            )
        """)
        check_count = cursor.rowcount
        logger.info(f"  ✓ Migrated {check_count} check phase assessments")

        # Drop old tables (no longer needed)
        logger.info("  🗑️  Dropping deprecated tables...")
        cursor.execute("DROP TABLE IF EXISTS epistemic_assessments")
        cursor.execute("DROP TABLE IF EXISTS preflight_assessments")
        cursor.execute("DROP TABLE IF EXISTS postflight_assessments")
        cursor.execute("DROP TABLE IF EXISTS check_phase_assessments")

        logger.info("✅ Migration complete: All data moved to reflexes table")

    except sqlite3.OperationalError as e:
        # Table doesn't exist or already migrated - this is fine
        logger.debug(f"Migration check: {e} (this is expected if tables don't exist)")
    except Exception as e:
        logger.error(f"⚠️  Migration failed: {e}")
        # Don't raise - allow database to continue working
        # Old tables will remain if migration fails


# All migrations in execution order
# Migration 9: Add project_id to goals
def migration_009_goals_project_id(cursor: sqlite3.Cursor):
    """Add project_id to goals table and populate from sessions"""
    import logging
    logger = logging.getLogger(__name__)

    # Add column
    add_column_if_missing(cursor, "goals", "project_id", "TEXT")

    # Populate project_id from sessions
    cursor.execute("""
        UPDATE goals
        SET project_id = (
            SELECT project_id FROM sessions WHERE sessions.session_id = goals.session_id
        )
        WHERE project_id IS NULL
    """)
    rows_updated = cursor.rowcount
    logger.info(f"✓ Updated {rows_updated} goals with project_id from sessions")


# Migration 10: Add bootstrap_level to sessions
def migration_010_sessions_bootstrap_level(cursor: sqlite3.Cursor):
    """Add bootstrap_level column to sessions table"""
    add_column_if_missing(cursor, "sessions", "bootstrap_level", "INTEGER", "1")


# Migration 11: Add project_id to mistakes_made
def migration_011_mistakes_project_id(cursor: sqlite3.Cursor):
    """Add project_id column to mistakes_made table"""
    add_column_if_missing(cursor, "mistakes_made", "project_id", "TEXT")


# Migration 12: Add impact column to project_unknowns
def migration_012_unknowns_impact(cursor: sqlite3.Cursor):
    """Add impact scoring to project_unknowns for importance weighting"""
    add_column_if_missing(cursor, "project_unknowns", "impact", "REAL", "0.5")


# Migration 13: Add session-scoped breadcrumb tables (dual-scope architecture)
def migration_013_session_scoped_breadcrumbs(cursor: sqlite3.Cursor):
    """Create session_* tables for session-scoped learning (dual-scope Phase 1)"""
    
    # session_findings (mirrors project_findings)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_findings (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            goal_id TEXT,
            subtask_id TEXT,
            finding TEXT NOT NULL,
            created_timestamp REAL NOT NULL,
            finding_data TEXT NOT NULL,
            subject TEXT,
            impact REAL,
            
            FOREIGN KEY (session_id) REFERENCES sessions(session_id),
            FOREIGN KEY (goal_id) REFERENCES goals(id),
            FOREIGN KEY (subtask_id) REFERENCES subtasks(id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_findings_session ON session_findings(session_id)")
    
    # session_unknowns (mirrors project_unknowns)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_unknowns (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            goal_id TEXT,
            subtask_id TEXT,
            unknown TEXT NOT NULL,
            is_resolved BOOLEAN DEFAULT FALSE,
            resolved_by TEXT,
            created_timestamp REAL NOT NULL,
            resolved_timestamp REAL,
            unknown_data TEXT NOT NULL,
            subject TEXT,
            impact REAL DEFAULT 0.5,
            
            FOREIGN KEY (session_id) REFERENCES sessions(session_id),
            FOREIGN KEY (goal_id) REFERENCES goals(id),
            FOREIGN KEY (subtask_id) REFERENCES subtasks(id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_unknowns_session ON session_unknowns(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_unknowns_resolved ON session_unknowns(is_resolved)")
    
    # session_dead_ends (mirrors project_dead_ends)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_dead_ends (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            goal_id TEXT,
            subtask_id TEXT,
            approach TEXT NOT NULL,
            why_failed TEXT NOT NULL,
            created_timestamp REAL NOT NULL,
            dead_end_data TEXT NOT NULL,
            subject TEXT,
            
            FOREIGN KEY (session_id) REFERENCES sessions(session_id),
            FOREIGN KEY (goal_id) REFERENCES goals(id),
            FOREIGN KEY (subtask_id) REFERENCES subtasks(id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_dead_ends_session ON session_dead_ends(session_id)")
    
    # session_mistakes (mirrors mistakes_made structure)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_mistakes (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            goal_id TEXT,
            mistake TEXT NOT NULL,
            why_wrong TEXT NOT NULL,
            cost_estimate TEXT,
            root_cause_vector TEXT,
            prevention TEXT,
            created_timestamp REAL NOT NULL,
            mistake_data TEXT NOT NULL,
            
            FOREIGN KEY (session_id) REFERENCES sessions(session_id),
            FOREIGN KEY (goal_id) REFERENCES goals(id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_mistakes_session ON session_mistakes(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_mistakes_goal ON session_mistakes(goal_id)")


ALL_MIGRATIONS: List[Tuple[str, str, Callable]] = [
    ("001_cascade_workflow_columns", "Add CASCADE workflow tracking to cascades", migration_001_cascade_workflow_columns),
    ("002_epistemic_delta", "Add epistemic delta JSON to cascades", migration_002_epistemic_delta),
    ("003_cascade_goal_tracking", "Add goal tracking to cascades", migration_003_cascade_goal_tracking),
    ("004_goals_status", "Add status column to goals", migration_004_goals_status),
    ("005_sessions_project_id", "Add project_id to sessions", migration_005_sessions_project_id),
    ("006_sessions_subject", "Add subject filtering to sessions", migration_006_sessions_subject),
    ("007_findings_impact", "Add impact scoring to project_findings", migration_007_findings_impact),
    ("008_migrate_legacy_to_reflexes", "Migrate legacy epistemic tables to reflexes", migration_008_migrate_legacy_to_reflexes),
    ("009_goals_project_id", "Add project_id to goals table", migration_009_goals_project_id),
    ("010_sessions_bootstrap_level", "Add bootstrap_level to sessions", migration_010_sessions_bootstrap_level),
    ("011_mistakes_project_id", "Add project_id to mistakes_made", migration_011_mistakes_project_id),
    ("012_unknowns_impact", "Add impact scoring to project_unknowns", migration_012_unknowns_impact),
    ("013_session_scoped_breadcrumbs", "Add session-scoped breadcrumb tables (dual-scope Phase 1)", migration_013_session_scoped_breadcrumbs),
]
