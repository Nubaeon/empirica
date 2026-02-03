"""
Extended Schema

Database table schemas for tables originally created via migrations.
These are included in base schema so PostgreSQL gets them without
needing to run SQLite-specific migrations.

Tables:
- Session-scoped breadcrumbs (migration 013)
- Lessons and knowledge graph (migration 014)
- Auto-captured issues (migration 016)
- Project relationships (migration 018)
- Cross-project finding links (migration 019)
- Client projects (migration 020)
- Attention budgets and rollup logs (migration 024)
"""

SCHEMAS = [
    # ── Session-scoped breadcrumbs REMOVED (migration 027) ──
    # session_findings, session_unknowns, session_dead_ends, session_mistakes
    # were deprecated in favor of project_* tables with transaction_id.
    # Sessions delineate compact windows only; transactions are the atomic unit.
    # See: migration_027_drop_session_noetic_tables

    # ── Lessons and knowledge graph (migration 014) ──

    """
    CREATE TABLE IF NOT EXISTS lessons (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    description TEXT,
                    domain TEXT,
                    tags TEXT,

                    source_confidence REAL NOT NULL,
                    teaching_quality REAL NOT NULL,
                    reproducibility REAL NOT NULL,

                    step_count INTEGER DEFAULT 0,
                    prereq_count INTEGER DEFAULT 0,
                    replay_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0.0,

                    suggested_tier TEXT DEFAULT 'free',
                    suggested_price REAL DEFAULT 0.0,

                    created_by TEXT,
                    created_timestamp REAL NOT NULL,
                    updated_timestamp REAL NOT NULL,

                    lesson_data TEXT NOT NULL,

                    UNIQUE(name, version)
                )
    """,

    """
    CREATE TABLE IF NOT EXISTS lesson_steps (
                    id TEXT PRIMARY KEY,
                    lesson_id TEXT NOT NULL,
                    step_order INTEGER NOT NULL,
                    phase TEXT NOT NULL,
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
    """,

    """
    CREATE TABLE IF NOT EXISTS lesson_epistemic_deltas (
                    id TEXT PRIMARY KEY,
                    lesson_id TEXT NOT NULL,
                    vector_name TEXT NOT NULL,
                    delta_value REAL NOT NULL,

                    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE,
                    UNIQUE(lesson_id, vector_name)
                )
    """,

    """
    CREATE TABLE IF NOT EXISTS lesson_prerequisites (
                    id TEXT PRIMARY KEY,
                    lesson_id TEXT NOT NULL,
                    prereq_type TEXT NOT NULL,
                    prereq_id TEXT NOT NULL,
                    prereq_name TEXT NOT NULL,
                    required_level REAL DEFAULT 0.5,

                    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
                )
    """,

    """
    CREATE TABLE IF NOT EXISTS lesson_corrections (
                    id TEXT PRIMARY KEY,
                    lesson_id TEXT NOT NULL,
                    step_order INTEGER NOT NULL,
                    original_action TEXT NOT NULL,
                    corrected_action TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    corrector_type TEXT NOT NULL,
                    corrector_id TEXT,
                    created_timestamp REAL NOT NULL,

                    FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
                )
    """,

    """
    CREATE TABLE IF NOT EXISTS knowledge_graph (
                    id TEXT PRIMARY KEY,
                    source_type TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    created_timestamp REAL NOT NULL,
                    metadata TEXT,

                    UNIQUE(source_type, source_id, relation_type, target_type, target_id)
                )
    """,

    """
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
                    epistemic_before TEXT,
                    epistemic_after TEXT,
                    replay_data TEXT,

                    FOREIGN KEY (lesson_id) REFERENCES lessons(id),
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
    """,

    # ── Auto-captured issues (migration 016) ──

    """
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
    """,

    # ── Project relationships (migration 018) ──

    """
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
    """,

    # ── Cross-project finding links (migration 019) ──

    """
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
    """,

    # ── Client projects (migration 020) ──

    """
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

                    FOREIGN KEY (project_id) REFERENCES projects(id),
                    UNIQUE(client_id, project_id, relationship_type)
                )
    """,

    # ── Attention budgets and rollup logs (migration 024) ──

    """
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
    """,

    """
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
    """,
]
