"""
Tracking Schema

Database table schemas for tracking-related tables.
Extracted from SessionDatabase._create_tables()

Note: Orphaned tables removed 2025-12-31:
- divergence_tracking (never wired up)
- drift_monitoring (replaced by MirrorDriftMonitor using Git)
- investigation_tools (never wired up)
- investigation_logs (never wired up)
- act_logs (never wired up)
"""

SCHEMAS = [
    # Schema 1: Mistakes tracking (26 rows as of cleanup)
    """
    CREATE TABLE IF NOT EXISTS mistakes_made (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    goal_id TEXT,
                    project_id TEXT,
                    mistake TEXT NOT NULL,
                    why_wrong TEXT NOT NULL,
                    cost_estimate TEXT,
                    root_cause_vector TEXT,
                    prevention TEXT,
                    created_timestamp REAL NOT NULL,
                    mistake_data TEXT NOT NULL,

                    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                    FOREIGN KEY (goal_id) REFERENCES goals(id),
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                )
    """,

    # Schema 2: Investigation branches for parallel exploration
    """
    CREATE TABLE IF NOT EXISTS investigation_branches (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    branch_name TEXT NOT NULL,
                    investigation_path TEXT NOT NULL,
                    git_branch_name TEXT NOT NULL,

                    -- Epistemic state for this branch
                    preflight_vectors TEXT NOT NULL,
                    postflight_vectors TEXT,

                    -- Cost tracking
                    tokens_spent INTEGER DEFAULT 0,
                    time_spent_minutes INTEGER DEFAULT 0,

                    -- Merge metadata
                    merge_score REAL,
                    epistemic_quality REAL,
                    is_winner BOOLEAN DEFAULT FALSE,

                    -- Timestamps and state
                    created_timestamp REAL NOT NULL,
                    checkpoint_timestamp REAL,
                    merged_timestamp REAL,
                    status TEXT DEFAULT 'active',

                    branch_metadata TEXT,

                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
    """,

    # Schema 3: Merge decisions when consolidating branches
    """
    CREATE TABLE IF NOT EXISTS merge_decisions (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    investigation_round INTEGER NOT NULL,

                    winning_branch_id TEXT NOT NULL,
                    winning_branch_name TEXT,
                    winning_score REAL NOT NULL,

                    other_branches TEXT,
                    decision_rationale TEXT NOT NULL,

                    auto_merged BOOLEAN DEFAULT TRUE,
                    created_timestamp REAL NOT NULL,

                    decision_metadata TEXT,

                    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                    FOREIGN KEY (winning_branch_id) REFERENCES investigation_branches(id)
                )
    """,

    # Schema 4: Token savings tracking
    """
    CREATE TABLE IF NOT EXISTS token_savings (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    saving_type TEXT NOT NULL,
                    tokens_saved INTEGER NOT NULL,
                    evidence TEXT,
                    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
    """,

]
