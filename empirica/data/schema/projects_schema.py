"""
Projects Schema

Database table schemas for projects-related tables.
Extracted from SessionDatabase._create_tables()
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
                    
                    project_data TEXT NOT NULL
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
                    investigation_tools TEXT,
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

]
