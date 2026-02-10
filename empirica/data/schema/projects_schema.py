"""
Projects Schema (v0.6.0)

Database table schemas for projects-related tables.
Extracted from SessionDatabase._create_tables()

v0.6.0 Changes:
- Added entity_type/entity_id to artifact tables (entity-agnostic pattern)
- Added assumptions and decisions tables
- entity_type defaults to 'project' for backwards compatibility
"""

SCHEMAS = [
    # Schema 1
    """
    CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    repos TEXT,
                    created_timestamp REAL NOT NULL,
                    last_activity_timestamp REAL,
                    status TEXT DEFAULT 'active',
                    metadata TEXT,
                    
                    total_sessions INTEGER DEFAULT 0,
                    total_goals INTEGER DEFAULT 0,
                    total_epistemic_deltas TEXT,

                    project_data TEXT NOT NULL,
                    project_type TEXT DEFAULT 'product',
                    project_tags TEXT,
                    parent_project_id TEXT
                )
    """,

    # Schema 2
    """
    CREATE TABLE IF NOT EXISTS project_handoffs (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    created_timestamp REAL NOT NULL,
                    project_summary TEXT NOT NULL,
                    sessions_included TEXT NOT NULL,
                    total_learning_deltas TEXT,
                    key_decisions TEXT,
                    patterns_discovered TEXT,
                    mistakes_summary TEXT,
                    remaining_work TEXT,
                    repos_touched TEXT,
                    next_session_bootstrap TEXT,
                    handoff_data TEXT NOT NULL,
                    
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
    """,

    # Schema 3
    """
    CREATE TABLE IF NOT EXISTS handoff_reports (
                    session_id TEXT PRIMARY KEY,
                    ai_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    task_summary TEXT,
                    duration_seconds REAL,
                    epistemic_deltas TEXT,
                    key_findings TEXT,
                    knowledge_gaps_filled TEXT,
                    remaining_unknowns TEXT,
                    noetic_tools TEXT,
                    next_session_context TEXT,
                    recommended_next_steps TEXT,
                    artifacts_created TEXT,
                    calibration_status TEXT,
                    overall_confidence_delta REAL,
                    compressed_json TEXT,
                    markdown_report TEXT,
                    created_at REAL NOT NULL,
                    
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
    """,

    # Schema 4
    """
    CREATE TABLE IF NOT EXISTS project_findings (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    goal_id TEXT,
                    subtask_id TEXT,
                    finding TEXT NOT NULL,
                    created_timestamp REAL NOT NULL,
                    finding_data TEXT NOT NULL,
                    subject TEXT,
                    impact REAL DEFAULT 0.5,
                    transaction_id TEXT,

                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                    FOREIGN KEY (goal_id) REFERENCES goals(id),
                    FOREIGN KEY (subtask_id) REFERENCES subtasks(id)
                )
    """,

    # Schema 5
    """
    CREATE TABLE IF NOT EXISTS project_unknowns (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
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
                    transaction_id TEXT,

                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                    FOREIGN KEY (goal_id) REFERENCES goals(id),
                    FOREIGN KEY (subtask_id) REFERENCES subtasks(id)
                )
    """,

    # Schema 6
    """
    CREATE TABLE IF NOT EXISTS project_dead_ends (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    goal_id TEXT,
                    subtask_id TEXT,
                    approach TEXT NOT NULL,
                    why_failed TEXT NOT NULL,
                    created_timestamp REAL NOT NULL,
                    dead_end_data TEXT NOT NULL,
                    subject TEXT,
                    impact REAL DEFAULT 0.5,
                    transaction_id TEXT,

                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                    FOREIGN KEY (goal_id) REFERENCES goals(id),
                    FOREIGN KEY (subtask_id) REFERENCES subtasks(id)
                )
    """,

    # Schema 7
    """
    CREATE TABLE IF NOT EXISTS project_reference_docs (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    doc_path TEXT NOT NULL,
                    doc_type TEXT,
                    description TEXT,
                    created_timestamp REAL NOT NULL,
                    doc_data TEXT NOT NULL,
    
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
    """,

    # Schema 8
    """
    CREATE TABLE IF NOT EXISTS epistemic_sources (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    session_id TEXT,

                    source_type TEXT NOT NULL,
                    source_url TEXT,
                    title TEXT NOT NULL,
                    description TEXT,

                    confidence REAL DEFAULT 0.5,
                    epistemic_layer TEXT,

                    supports_vectors TEXT,
                    related_findings TEXT,

                    discovered_by_ai TEXT,
                    discovered_at TIMESTAMP NOT NULL,

                    source_metadata TEXT,

                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
    """,

    # =========================================================================
    # Epistemic Intent Layer (v0.6.0)
    # Entity-agnostic columns + new artifact tables
    # =========================================================================

    # Assumptions: unverified beliefs (noetic) — per-project mirror of workspace table
    """
    CREATE TABLE IF NOT EXISTS assumptions (
        id TEXT PRIMARY KEY,
        assumption TEXT NOT NULL,
        confidence REAL DEFAULT 0.5 CHECK(confidence BETWEEN 0.0 AND 1.0),
        status TEXT NOT NULL DEFAULT 'unverified' CHECK(status IN (
            'unverified', 'verified', 'falsified'
        )),
        resolution_finding_id TEXT,
        entity_type TEXT NOT NULL DEFAULT 'project',
        entity_id TEXT,
        project_id TEXT,
        session_id TEXT,
        transaction_id TEXT,
        goal_id TEXT,
        created_by_ai TEXT,
        created_timestamp REAL NOT NULL,
        resolved_timestamp REAL,

        FOREIGN KEY (project_id) REFERENCES projects(id),
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
    """,

    # Decisions: recorded choice points (praxic) — per-project
    """
    CREATE TABLE IF NOT EXISTS decisions (
        id TEXT PRIMARY KEY,
        choice TEXT NOT NULL,
        alternatives TEXT,
        rationale TEXT NOT NULL,
        confidence_at_decision REAL CHECK(confidence_at_decision BETWEEN 0.0 AND 1.0),
        reversibility TEXT DEFAULT 'committal' CHECK(reversibility IN (
            'exploratory', 'committal', 'forced'
        )),
        entity_type TEXT NOT NULL DEFAULT 'project',
        entity_id TEXT,
        project_id TEXT,
        session_id TEXT,
        transaction_id TEXT,
        goal_id TEXT,
        outcome TEXT,
        outcome_assessed_at REAL,
        regret_score REAL,
        created_by_ai TEXT,
        created_timestamp REAL NOT NULL,

        FOREIGN KEY (project_id) REFERENCES projects(id),
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
    """,

    # Indexes for new tables
    "CREATE INDEX IF NOT EXISTS idx_assumptions_entity ON assumptions(entity_type, entity_id)",
    "CREATE INDEX IF NOT EXISTS idx_assumptions_status ON assumptions(status)",
    "CREATE INDEX IF NOT EXISTS idx_assumptions_transaction ON assumptions(transaction_id)",
    "CREATE INDEX IF NOT EXISTS idx_decisions_entity ON decisions(entity_type, entity_id)",
    "CREATE INDEX IF NOT EXISTS idx_decisions_transaction ON decisions(transaction_id)",

    # Indexes for existing tables
    "CREATE INDEX IF NOT EXISTS idx_project_findings_project ON project_findings(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_project_findings_session ON project_findings(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_findings_transaction ON project_findings(transaction_id)",
    "CREATE INDEX IF NOT EXISTS idx_project_unknowns_project ON project_unknowns(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_project_unknowns_resolved ON project_unknowns(is_resolved)",
    "CREATE INDEX IF NOT EXISTS idx_unknowns_transaction ON project_unknowns(transaction_id)",
    "CREATE INDEX IF NOT EXISTS idx_project_dead_ends_project ON project_dead_ends(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_dead_ends_transaction ON project_dead_ends(transaction_id)",
    "CREATE INDEX IF NOT EXISTS idx_epistemic_sources_project ON epistemic_sources(project_id)",
    "CREATE INDEX IF NOT EXISTS idx_epistemic_sources_session ON epistemic_sources(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_epistemic_sources_type ON epistemic_sources(source_type)",
    "CREATE INDEX IF NOT EXISTS idx_epistemic_sources_confidence ON epistemic_sources(confidence)",
]

# =========================================================================
# Entity-agnostic migration for existing artifact tables
# Run once to add entity_type/entity_id columns and backfill from project_id
# =========================================================================

ENTITY_MIGRATION_STATEMENTS = [
    "ALTER TABLE project_findings ADD COLUMN entity_type TEXT DEFAULT 'project'",
    "ALTER TABLE project_findings ADD COLUMN entity_id TEXT",
    "UPDATE project_findings SET entity_id = project_id WHERE entity_id IS NULL",

    "ALTER TABLE project_unknowns ADD COLUMN entity_type TEXT DEFAULT 'project'",
    "ALTER TABLE project_unknowns ADD COLUMN entity_id TEXT",
    "UPDATE project_unknowns SET entity_id = project_id WHERE entity_id IS NULL",

    "ALTER TABLE project_dead_ends ADD COLUMN entity_type TEXT DEFAULT 'project'",
    "ALTER TABLE project_dead_ends ADD COLUMN entity_id TEXT",
    "UPDATE project_dead_ends SET entity_id = project_id WHERE entity_id IS NULL",

    "ALTER TABLE mistakes_made ADD COLUMN entity_type TEXT DEFAULT 'project'",
    "ALTER TABLE mistakes_made ADD COLUMN entity_id TEXT",
    "UPDATE mistakes_made SET entity_id = project_id WHERE entity_id IS NULL",

    "ALTER TABLE epistemic_sources ADD COLUMN entity_type TEXT DEFAULT 'project'",
    "ALTER TABLE epistemic_sources ADD COLUMN entity_id TEXT",
    "UPDATE epistemic_sources SET entity_id = project_id WHERE entity_id IS NULL",

    "ALTER TABLE goals ADD COLUMN entity_type TEXT DEFAULT 'project'",
    "ALTER TABLE goals ADD COLUMN entity_id TEXT",
    "UPDATE goals SET entity_id = project_id WHERE entity_id IS NULL",
]
