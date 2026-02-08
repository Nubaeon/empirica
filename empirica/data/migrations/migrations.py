"""Database schema migrations"""
import logging
import sqlite3
from typing import List, Tuple, Callable
from .migration_runner import add_column_if_missing

logger = logging.getLogger(__name__)


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


# Migration 14: Add lessons and knowledge graph tables
def migration_014_lessons_and_knowledge_graph(cursor: sqlite3.Cursor):
    """
    Add tables for Empirica Lessons - Epistemic Procedural Knowledge.

    4-layer architecture:
    - HOT: In-memory (not stored)
    - WARM: lessons, lesson_steps, lesson_epistemic_deltas (this migration)
    - SEARCH: Qdrant vectors (external)
    - COLD: YAML files (filesystem)
    """
    import logging
    logger = logging.getLogger(__name__)

    # lessons - Core lesson metadata (WARM layer)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            version TEXT NOT NULL,
            description TEXT,
            domain TEXT,
            tags TEXT,  -- Comma-separated

            -- Epistemic quality metrics
            source_confidence REAL NOT NULL,
            teaching_quality REAL NOT NULL,
            reproducibility REAL NOT NULL,

            -- Stats
            step_count INTEGER DEFAULT 0,
            prereq_count INTEGER DEFAULT 0,
            replay_count INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0.0,

            -- Marketplace
            suggested_tier TEXT DEFAULT 'free',  -- free, verified, pro, enterprise
            suggested_price REAL DEFAULT 0.0,

            -- Metadata
            created_by TEXT,
            created_timestamp REAL NOT NULL,
            updated_timestamp REAL NOT NULL,

            -- Full lesson data (JSON for cold storage reference)
            lesson_data TEXT NOT NULL,

            UNIQUE(name, version)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lessons_domain ON lessons(domain)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lessons_tier ON lessons(suggested_tier)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lessons_created ON lessons(created_timestamp)")
    logger.info("✓ Created lessons table")

    # lesson_steps - Procedural steps (for fast lookup without full YAML)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lesson_steps (
            id TEXT PRIMARY KEY,
            lesson_id TEXT NOT NULL,
            step_order INTEGER NOT NULL,
            phase TEXT NOT NULL,  -- 'noetic' or 'praxic'
            action TEXT NOT NULL,
            target TEXT,
            code TEXT,
            critical BOOLEAN DEFAULT 0,
            expected_outcome TEXT,
            error_recovery TEXT,
            timeout_ms INTEGER,

            FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE,
            UNIQUE(lesson_id, step_order)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lesson_steps_lesson ON lesson_steps(lesson_id)")
    logger.info("✓ Created lesson_steps table")

    # lesson_epistemic_deltas - What vectors each lesson improves
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lesson_epistemic_deltas (
            id TEXT PRIMARY KEY,
            lesson_id TEXT NOT NULL,
            vector_name TEXT NOT NULL,  -- 'know', 'do', 'context', etc.
            delta_value REAL NOT NULL,  -- Positive = improvement, negative = reduction

            FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE,
            UNIQUE(lesson_id, vector_name)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lesson_deltas_lesson ON lesson_epistemic_deltas(lesson_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lesson_deltas_vector ON lesson_epistemic_deltas(vector_name)")
    logger.info("✓ Created lesson_epistemic_deltas table")

    # lesson_prerequisites - What's required before executing a lesson
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lesson_prerequisites (
            id TEXT PRIMARY KEY,
            lesson_id TEXT NOT NULL,
            prereq_type TEXT NOT NULL,  -- 'lesson', 'skill', 'tool', 'context', 'epistemic'
            prereq_id TEXT NOT NULL,
            prereq_name TEXT NOT NULL,
            required_level REAL DEFAULT 0.5,

            FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lesson_prereqs_lesson ON lesson_prerequisites(lesson_id)")
    logger.info("✓ Created lesson_prerequisites table")

    # lesson_corrections - Human/AI corrections received during creation or replay
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lesson_corrections (
            id TEXT PRIMARY KEY,
            lesson_id TEXT NOT NULL,
            step_order INTEGER NOT NULL,
            original_action TEXT NOT NULL,
            corrected_action TEXT NOT NULL,
            reason TEXT NOT NULL,
            corrector_type TEXT NOT NULL,  -- 'human' or 'ai'
            corrector_id TEXT,
            created_timestamp REAL NOT NULL,

            FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lesson_corrections_lesson ON lesson_corrections(lesson_id)")
    logger.info("✓ Created lesson_corrections table")

    # knowledge_graph - Relationships between all entities
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_graph (
            id TEXT PRIMARY KEY,
            source_type TEXT NOT NULL,  -- 'lesson', 'skill', 'domain', 'goal', 'session'
            source_id TEXT NOT NULL,
            relation_type TEXT NOT NULL,  -- 'requires', 'enables', 'related_to', 'supersedes', 'derived_from', 'produced', 'discovered'
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            weight REAL DEFAULT 1.0,
            created_timestamp REAL NOT NULL,
            metadata TEXT,  -- JSON for additional context

            UNIQUE(source_type, source_id, relation_type, target_type, target_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kg_source ON knowledge_graph(source_type, source_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kg_target ON knowledge_graph(target_type, target_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_kg_relation ON knowledge_graph(relation_type)")
    logger.info("✓ Created knowledge_graph table")

    # lesson_replays - Track lesson execution history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lesson_replays (
            id TEXT PRIMARY KEY,
            lesson_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            ai_id TEXT,
            started_timestamp REAL NOT NULL,
            completed_timestamp REAL,
            success BOOLEAN,
            steps_completed INTEGER DEFAULT 0,
            total_steps INTEGER NOT NULL,
            error_message TEXT,
            epistemic_before TEXT,  -- JSON of vectors before
            epistemic_after TEXT,   -- JSON of vectors after
            replay_data TEXT,       -- JSON for additional context

            FOREIGN KEY (lesson_id) REFERENCES lessons(id),
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lesson_replays_lesson ON lesson_replays(lesson_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_lesson_replays_session ON lesson_replays(session_id)")
    logger.info("✓ Created lesson_replays table")

    logger.info("✅ Migration 014 complete: Lessons and knowledge graph tables created")


# Migration 15: Add instance_id to sessions for multi-instance isolation
def migration_015_sessions_instance_id(cursor: sqlite3.Cursor):
    """
    Add instance_id column to sessions table for multi-instance isolation.

    This allows multiple Claude instances to run simultaneously without
    session cross-talk. The instance_id is derived from:
    1. EMPIRICA_INSTANCE_ID env var (explicit override)
    2. TMUX_PANE (tmux terminal pane ID)
    3. TERM_SESSION_ID (macOS Terminal.app)
    4. WINDOWID (X11 window ID)
    5. None (fallback to legacy behavior)
    """
    import logging
    logger = logging.getLogger(__name__)

    add_column_if_missing(cursor, "sessions", "instance_id", "TEXT")

    # Add index for efficient instance-scoped queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_instance ON sessions(ai_id, instance_id)")
    logger.info("✓ Added instance_id column and index to sessions table")


# Migration 16: Add auto_captured_issues table
def migration_016_auto_captured_issues(cursor: sqlite3.Cursor):
    """
    Add auto_captured_issues table for automatic issue detection.

    This table was previously only created when IssueCapture service initialized,
    causing 'no such table' errors during project-bootstrap for users upgrading
    from older versions. Now created via migration for all users.

    Fixes: GitHub Issue #21 (Issue 1: Missing Database Migration)
    """
    import logging
    logger = logging.getLogger(__name__)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auto_captured_issues (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            severity TEXT NOT NULL,
            category TEXT NOT NULL,
            code_location TEXT,
            message TEXT NOT NULL,
            stack_trace TEXT,
            context TEXT,
            status TEXT DEFAULT 'new',
            assigned_to_ai TEXT,
            root_cause_id TEXT,
            resolution TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_issues_session_status
        ON auto_captured_issues(session_id, status)
    """)

    logger.info("✓ Created auto_captured_issues table and index")


# Migration 17: Add project_type and project_tags for multi-project workspace management
def migration_017_project_type_and_tags(cursor: sqlite3.Cursor):
    """
    Add project classification fields for workspace management.

    project_type: Categorizes project (product, application, research, documentation, infrastructure, operations)
    project_tags: JSON array of free-form tags for flexible categorization
    parent_project_id: Optional hierarchy (e.g., empirica-autonomy → empirica)
    """
    import logging
    logger = logging.getLogger(__name__)

    add_column_if_missing(cursor, "projects", "project_type", "TEXT", "'product'")
    add_column_if_missing(cursor, "projects", "project_tags", "TEXT")  # JSON array
    add_column_if_missing(cursor, "projects", "parent_project_id", "TEXT")

    # Add index for type-based queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_type ON projects(project_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_parent ON projects(parent_project_id)")

    logger.info("✓ Added project_type, project_tags, and parent_project_id to projects table")


# Migration 18: Add project_relationships table for cross-project links
def migration_018_project_relationships(cursor: sqlite3.Cursor):
    """
    Create project_relationships table for explicit cross-project links.

    This complements knowledge_graph by providing a simpler, project-focused view.
    Types: depends_on, blocks, shares_domain, cross_learns, parent_of
    """
    import logging
    logger = logging.getLogger(__name__)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_relationships (
            id TEXT PRIMARY KEY,
            source_project_id TEXT NOT NULL,
            target_project_id TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            weight REAL DEFAULT 1.0,
            notes TEXT,
            created_at REAL NOT NULL,
            created_by_ai_id TEXT,

            FOREIGN KEY (source_project_id) REFERENCES projects(id),
            FOREIGN KEY (target_project_id) REFERENCES projects(id),
            UNIQUE(source_project_id, target_project_id, relationship_type)
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_proj_rel_source ON project_relationships(source_project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_proj_rel_target ON project_relationships(target_project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_proj_rel_type ON project_relationships(relationship_type)")

    logger.info("✓ Created project_relationships table")


# Migration 19: Add cross_project_finding_links for shared learnings
def migration_019_cross_project_finding_links(cursor: sqlite3.Cursor):
    """
    Create table to link findings across projects.

    Allows a finding from project A to be marked as relevant to project B.
    Pattern borrowed from CRM's client_findings table.
    """
    import logging
    logger = logging.getLogger(__name__)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cross_project_finding_links (
            id TEXT PRIMARY KEY,
            finding_id TEXT NOT NULL,
            source_project_id TEXT NOT NULL,
            target_project_id TEXT NOT NULL,
            relevance REAL DEFAULT 1.0,
            notes TEXT,
            created_at REAL NOT NULL,
            created_by_ai_id TEXT,

            FOREIGN KEY (finding_id) REFERENCES project_findings(id),
            FOREIGN KEY (source_project_id) REFERENCES projects(id),
            FOREIGN KEY (target_project_id) REFERENCES projects(id),
            UNIQUE(finding_id, target_project_id)
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_xproj_finding_src ON cross_project_finding_links(source_project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_xproj_finding_tgt ON cross_project_finding_links(target_project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_xproj_finding_id ON cross_project_finding_links(finding_id)")

    logger.info("✓ Created cross_project_finding_links table")


# Migration 20: Add client_projects junction table for client-project relationships
def migration_020_client_projects(cursor: sqlite3.Cursor):
    """
    Create client_projects junction table for many-to-many client-project relationships.

    This fixes the schema design where engagements linked to goals instead of projects.
    Clients should link directly to projects, with engagements scoped to the relationship.

    Relationship types:
    - customer: Client is paying for work on this project
    - sponsor: Client is funding/sponsoring this project
    - partner: Collaborative relationship
    - stakeholder: Has interest but not direct ownership
    """
    import logging
    logger = logging.getLogger(__name__)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS client_projects (
            id TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            project_id TEXT NOT NULL,
            relationship_type TEXT DEFAULT 'customer',
            status TEXT DEFAULT 'active',
            started_at REAL NOT NULL,
            ended_at REAL,
            notes TEXT,
            created_at REAL NOT NULL,
            created_by_ai_id TEXT,

            FOREIGN KEY (client_id) REFERENCES clients(client_id),
            FOREIGN KEY (project_id) REFERENCES projects(id),
            UNIQUE(client_id, project_id, relationship_type)
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_projects_client ON client_projects(client_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_projects_project ON client_projects(project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_projects_status ON client_projects(status)")

    logger.info("✓ Created client_projects junction table")


# Migration 21: Add project_id to engagements table
def migration_021_engagements_project_id(cursor: sqlite3.Cursor):
    """
    Add project_id to engagements table for direct project scoping.

    This changes the relationship model:
    - Before: client → engagement → goal → project (inverted)
    - After: client → project (via client_projects), engagement has project_id

    The goal_id remains for optional fine-grained linking to specific goals.

    NOTE: The engagements table is part of empirica-crm, not core empirica.
    This migration gracefully skips if the table doesn't exist.
    """
    import logging
    logger = logging.getLogger(__name__)

    # Check if engagements table exists (it's part of empirica-crm)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='engagements'")
    if not cursor.fetchone():
        logger.info("⏭ Skipping migration 021: engagements table not present (empirica-crm not installed)")
        return

    add_column_if_missing(cursor, "engagements", "project_id", "TEXT")

    # Add index for project-based queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_engagements_project ON engagements(project_id)")

    logger.info("✓ Added project_id to engagements table")


# Migration 22: Add project_id to reflexes for project-aware PREFLIGHT tracking
def migration_022_reflexes_project_id(cursor: sqlite3.Cursor):
    """
    Add project_id to reflexes table for project-aware epistemic assessments.

    This enables the sentinel gate to detect when the AI switches between projects
    within the same session and require a new PREFLIGHT assessment for the new
    project context.

    Sessions are TEMPORAL (bounded by context windows/compactions).
    Goals are STRUCTURAL (persist across sessions).
    PREFLIGHT assessments are now PROJECT-SCOPED (valid for specific project context).
    """
    add_column_if_missing(cursor, "reflexes", "project_id", "TEXT")

    # Add index for project-based queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reflexes_project ON reflexes(project_id)")


# Migration 23: Add parent_session_id to sessions for sub-agent lineage tracking
def migration_023_sessions_parent_session_id(cursor: sqlite3.Cursor):
    """
    Add parent_session_id to sessions table for epistemic lineage tracking.

    When a sub-agent (e.g., test-goal-agent) creates its own session,
    parent_session_id links it back to the spawning session. This enables:
    - Epistemic lineage queries (who spawned whom)
    - Finding rollup from child sessions to parent
    - Preventing session file stomping (child sessions are explicitly linked)
    - Multi-agent coordination with clear provenance
    """
    import logging
    logger = logging.getLogger(__name__)

    add_column_if_missing(cursor, "sessions", "parent_session_id", "TEXT")

    # Index for parent-child queries (find all children of a session)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_parent ON sessions(parent_session_id)")

    logger.info("✓ Added parent_session_id to sessions table")


# Migration 24: Add attention_budgets and rollup_logs tables for epistemic attention budget
def migration_024_attention_budgets(cursor: sqlite3.Cursor):
    """
    Add tables for Epistemic Attention Budget system.

    attention_budgets: Track token/finding budgets allocated to parallel agent orchestration.
    rollup_logs: Record scored rollup decisions (accepted/rejected findings from sub-agents).
    """
    import logging
    logger = logging.getLogger(__name__)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attention_budgets (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            total_budget INTEGER NOT NULL,
            allocated INTEGER DEFAULT 0,
            remaining INTEGER NOT NULL,
            strategy TEXT DEFAULT 'information_gain',
            domain_allocations TEXT,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,

            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attention_budgets_session ON attention_budgets(session_id)")
    logger.info("✓ Created attention_budgets table")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rollup_logs (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            budget_id TEXT,
            agent_name TEXT NOT NULL,
            finding_hash TEXT NOT NULL,
            finding_text TEXT,
            score REAL NOT NULL,
            accepted BOOLEAN NOT NULL,
            reason TEXT,
            novelty REAL,
            domain_relevance REAL,
            timestamp REAL NOT NULL,

            FOREIGN KEY (session_id) REFERENCES sessions(session_id),
            FOREIGN KEY (budget_id) REFERENCES attention_budgets(id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rollup_logs_session ON rollup_logs(session_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rollup_logs_budget ON rollup_logs(budget_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rollup_logs_hash ON rollup_logs(finding_hash)")
    logger.info("✓ Created rollup_logs table")

    logger.info("✅ Migration 024 complete: Attention budget tables created")


def migration_025_transaction_id(cursor: sqlite3.Cursor):
    """
    Add transaction_id to epistemic artifact tables.

    Makes epistemic transactions first-class entities. A transaction_id (UUID)
    is generated at PREFLIGHT and links all artifacts (findings, unknowns,
    dead-ends, mistakes, assessments) created within that measurement window
    through to POSTFLIGHT.

    Enables:
    - Query all work within a transaction boundary
    - Explicit PREFLIGHT↔POSTFLIGHT linkage (replaces implicit timestamp ordering)
    - Cross-goal transaction boundaries for multi-goal sessions
    """
    # Core assessment table
    add_column_if_missing(cursor, "reflexes", "transaction_id", "TEXT")

    # Noetic artifact tables
    add_column_if_missing(cursor, "project_findings", "transaction_id", "TEXT")
    add_column_if_missing(cursor, "project_unknowns", "transaction_id", "TEXT")
    add_column_if_missing(cursor, "project_dead_ends", "transaction_id", "TEXT")
    add_column_if_missing(cursor, "mistakes_made", "transaction_id", "TEXT")

    # Praxic artifact table
    add_column_if_missing(cursor, "goals", "transaction_id", "TEXT")

    # Indexes for transaction queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reflexes_transaction ON reflexes(transaction_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_transaction ON project_findings(transaction_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_unknowns_transaction ON project_unknowns(transaction_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dead_ends_transaction ON project_dead_ends(transaction_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_mistakes_transaction ON mistakes_made(transaction_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_transaction ON goals(transaction_id)")

    logger.info("✓ Migration 025: Added transaction_id columns and indexes")


# Migration 26: Add post-test verification tables for grounded calibration
def migration_026_grounded_verification(cursor: sqlite3.Cursor):
    """
    Add tables for post-test verification system.

    Grounds epistemic calibration in objective evidence (test results,
    artifact counts, goal completion) rather than self-referential
    PREFLIGHT-to-POSTFLIGHT deltas.

    grounded_beliefs: Parallel Bayesian track using evidence as observations.
    verification_evidence: Raw evidence records per session.
    grounded_verifications: Per-session comparison of self-assessed vs grounded.
    calibration_trajectory: POSTFLIGHT-to-POSTFLIGHT evolution tracking.
    """
    import logging
    logger = logging.getLogger(__name__)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grounded_beliefs (
            belief_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            ai_id TEXT NOT NULL,
            vector_name TEXT NOT NULL,
            mean REAL NOT NULL,
            variance REAL NOT NULL,
            evidence_count INTEGER DEFAULT 0,
            last_observation REAL,
            last_observation_source TEXT,
            self_referential_mean REAL,
            divergence REAL,
            last_updated REAL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_grounded_beliefs_ai_vector
            ON grounded_beliefs(ai_id, vector_name)
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verification_evidence (
            evidence_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            source TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            raw_value TEXT,
            normalized_value REAL NOT NULL,
            quality TEXT NOT NULL,
            supports_vectors TEXT NOT NULL,
            collected_at REAL NOT NULL,
            metadata TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_verification_evidence_session
            ON verification_evidence(session_id)
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grounded_verifications (
            verification_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            ai_id TEXT NOT NULL,
            self_assessed_vectors TEXT NOT NULL,
            grounded_vectors TEXT,
            calibration_gaps TEXT,
            grounded_coverage REAL,
            overall_calibration_score REAL,
            evidence_count INTEGER DEFAULT 0,
            sources_available TEXT,
            sources_failed TEXT,
            domain TEXT,
            goal_id TEXT,
            created_at REAL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_grounded_verifications_session
            ON grounded_verifications(session_id)
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calibration_trajectory (
            point_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            ai_id TEXT NOT NULL,
            vector_name TEXT NOT NULL,
            self_assessed REAL NOT NULL,
            grounded REAL,
            gap REAL,
            domain TEXT,
            goal_id TEXT,
            timestamp REAL NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_calibration_trajectory_ai_vector
            ON calibration_trajectory(ai_id, vector_name, timestamp)
    """)

    logger.info("✅ Migration 026 complete: Post-test verification tables created")


# Migration 27: Drop deprecated session-scoped noetic tables
def migration_027_drop_session_noetic_tables(cursor: sqlite3.Cursor):
    """
    Drop deprecated session-scoped noetic artifact tables.

    These tables were created in migration 013 as part of a "dual-scope" approach
    that stored breadcrumbs in both session_* and project_* tables. This design
    was superseded:

    1. All noetic artifacts now go to project_* tables (with session_id + transaction_id)
    2. The session_* methods in BreadcrumbRepository are deprecated stubs
    3. Sessions delineate compact windows only — not epistemic boundaries
    4. Transactions are the atomic unit for epistemic measurement

    Tables dropped:
    - session_findings → use project_findings
    - session_unknowns → use project_unknowns
    - session_dead_ends → use project_dead_ends
    - session_mistakes → use mistakes_made

    This enables cleaner cross-trajectory pattern matching since all artifacts
    live in project-scoped tables with transaction_id linkage.
    """
    import logging
    logger = logging.getLogger(__name__)

    tables_to_drop = [
        'session_findings',
        'session_unknowns',
        'session_dead_ends',
        'session_mistakes',
    ]

    for table in tables_to_drop:
        try:
            # Check if table exists before dropping
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                # Check row count for logging
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                if count > 0:
                    logger.warning(f"⚠️  Dropping {table} with {count} rows (data migrated to project_* tables)")
                cursor.execute(f"DROP TABLE {table}")
                logger.info(f"✓ Dropped deprecated table: {table}")
            else:
                logger.debug(f"✓ Table {table} already dropped or never existed")
        except Exception as e:
            logger.warning(f"⚠️  Could not drop {table}: {e}")

    logger.info("✅ Migration 027 complete: Deprecated session noetic tables dropped")


def migration_028_investigation_branches_transaction_id(cursor: sqlite3.Cursor):
    """
    Add transaction_id to investigation_branches for epistemic continuity.

    Sub-agent branches should participate in the parent's epistemic transaction,
    allowing their learnings to contribute to the parent's POSTFLIGHT delta and
    grounded calibration.
    """
    import logging
    logger = logging.getLogger(__name__)

    add_column_if_missing(cursor, "investigation_branches", "transaction_id", "TEXT")
    logger.info("✅ Migration 028 complete: Added transaction_id to investigation_branches")


def migration_029_goals_transaction_index(cursor: sqlite3.Cursor):
    """
    Add index on goals.transaction_id for efficient transaction-scoped queries.

    Goals are structurally project-scoped but temporally transaction-scoped.
    Transactions (PREFLIGHT→POSTFLIGHT measurement windows) span compaction
    boundaries, making them the natural scope for epistemic measurement.

    This index enables:
    - get_transaction_goals(transaction_id)
    - query_goals_by_transaction()
    - Transaction-scoped goal completion tracking
    """
    import logging
    logger = logging.getLogger(__name__)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_goals_transaction_id
        ON goals(transaction_id)
    """)
    logger.info("✅ Migration 029 complete: Added index on goals.transaction_id")


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
    ("014_lessons_and_knowledge_graph", "Add lessons and knowledge graph tables for epistemic procedural knowledge", migration_014_lessons_and_knowledge_graph),
    ("015_sessions_instance_id", "Add instance_id to sessions for multi-instance isolation", migration_015_sessions_instance_id),
    ("016_auto_captured_issues", "Add auto_captured_issues table for issue tracking", migration_016_auto_captured_issues),
    ("017_project_type_and_tags", "Add project_type, project_tags, parent_project_id for workspace management", migration_017_project_type_and_tags),
    ("018_project_relationships", "Add project_relationships table for cross-project links", migration_018_project_relationships),
    ("019_cross_project_finding_links", "Add cross_project_finding_links for shared learnings", migration_019_cross_project_finding_links),
    ("020_client_projects", "Add client_projects junction table for client-project relationships", migration_020_client_projects),
    ("021_engagements_project_id", "Add project_id to engagements for direct project scoping", migration_021_engagements_project_id),
    ("022_reflexes_project_id", "Add project_id to reflexes for project-aware PREFLIGHT tracking", migration_022_reflexes_project_id),
    ("023_sessions_parent_session_id", "Add parent_session_id to sessions for sub-agent lineage tracking", migration_023_sessions_parent_session_id),
    ("024_attention_budgets", "Add attention_budgets and rollup_logs tables for epistemic attention budget", migration_024_attention_budgets),
    ("025_transaction_id", "Add transaction_id to epistemic artifact tables for first-class transaction tracking", migration_025_transaction_id),
    ("026_grounded_verification", "Add post-test verification tables for grounded calibration", migration_026_grounded_verification),
    ("027_drop_session_noetic_tables", "Drop deprecated session-scoped noetic tables (sessions delineate compact windows only)", migration_027_drop_session_noetic_tables),
    ("028_investigation_branches_transaction_id", "Add transaction_id to investigation_branches for sub-agent epistemic continuity", migration_028_investigation_branches_transaction_id),
    ("029_goals_transaction_index", "Add index on goals.transaction_id for transaction-scoped queries", migration_029_goals_transaction_index),
]
