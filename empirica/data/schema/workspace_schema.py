"""
Workspace Schema

Global registry of all projects with epistemic trajectory pointers.

This is the "portfolio view" that tracks:
- All known projects across the workspace
- Path to each project's epistemic trajectory (.empirica directory)
- Summary statistics for cross-project queries
- Last sync timestamps for staleness detection

Lives at: ~/.empirica/workspace/workspace.db
"""

SCHEMAS = [
    # Global projects registry
    """
    CREATE TABLE IF NOT EXISTS global_projects (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,

        -- Trajectory pointer (path to project's .empirica directory)
        trajectory_path TEXT NOT NULL UNIQUE,

        -- Git info (for sync/discovery)
        git_remote_url TEXT,
        git_branch TEXT DEFAULT 'main',

        -- Summary stats (cached, refreshed on sync)
        total_transactions INTEGER DEFAULT 0,
        total_findings INTEGER DEFAULT 0,
        total_unknowns INTEGER DEFAULT 0,
        total_dead_ends INTEGER DEFAULT 0,
        total_goals INTEGER DEFAULT 0,

        -- Trajectory health
        last_transaction_id TEXT,
        last_transaction_timestamp REAL,
        last_sync_timestamp REAL,

        -- Status
        status TEXT DEFAULT 'active',  -- 'active', 'dormant', 'archived'
        project_type TEXT DEFAULT 'product',  -- 'product', 'research', 'outreach'
        project_tags TEXT,  -- JSON array

        -- Metadata
        created_timestamp REAL NOT NULL,
        updated_timestamp REAL NOT NULL,
        metadata TEXT  -- JSON for extensibility
    )
    """,

    # Cross-trajectory pattern cache
    # Stores discovered patterns across multiple projects for fast querying
    """
    CREATE TABLE IF NOT EXISTS trajectory_patterns (
        id TEXT PRIMARY KEY,
        pattern_type TEXT NOT NULL,  -- 'learning', 'mistake', 'dead_end', 'success'
        pattern_description TEXT NOT NULL,

        -- Source trajectories (projects where this pattern was observed)
        source_project_ids TEXT NOT NULL,  -- JSON array
        occurrence_count INTEGER DEFAULT 1,

        -- Pattern vectors (aggregated from source findings)
        avg_impact REAL,
        confidence REAL,  -- How reliable is this pattern?

        -- Context
        domain TEXT,  -- 'caching', 'auth', 'performance', etc.
        tech_stack TEXT,  -- JSON array: ['Python', 'Redis']

        -- Timestamps
        first_observed REAL NOT NULL,
        last_observed REAL NOT NULL,

        -- Searchable content
        pattern_data TEXT NOT NULL  -- JSON with full pattern details
    )
    """,

    # Trajectory links (for cross-project knowledge transfer)
    """
    CREATE TABLE IF NOT EXISTS trajectory_links (
        id TEXT PRIMARY KEY,
        source_project_id TEXT NOT NULL,
        target_project_id TEXT NOT NULL,
        link_type TEXT NOT NULL,  -- 'shared_learning', 'dependency', 'related', 'derived'

        -- What was transferred
        artifact_type TEXT,  -- 'finding', 'unknown', 'dead_end', 'pattern'
        artifact_id TEXT,

        -- Link metadata
        relevance REAL DEFAULT 1.0,
        notes TEXT,
        created_timestamp REAL NOT NULL,
        created_by_ai_id TEXT,

        FOREIGN KEY (source_project_id) REFERENCES global_projects(id),
        FOREIGN KEY (target_project_id) REFERENCES global_projects(id),
        UNIQUE(source_project_id, target_project_id, artifact_type, artifact_id)
    )
    """,

    # Indexes for efficient queries
    "CREATE INDEX IF NOT EXISTS idx_global_projects_status ON global_projects(status)",
    "CREATE INDEX IF NOT EXISTS idx_global_projects_type ON global_projects(project_type)",
    "CREATE INDEX IF NOT EXISTS idx_global_projects_last_tx ON global_projects(last_transaction_timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_trajectory_patterns_type ON trajectory_patterns(pattern_type)",
    "CREATE INDEX IF NOT EXISTS idx_trajectory_patterns_domain ON trajectory_patterns(domain)",
    "CREATE INDEX IF NOT EXISTS idx_trajectory_links_source ON trajectory_links(source_project_id)",
    "CREATE INDEX IF NOT EXISTS idx_trajectory_links_target ON trajectory_links(target_project_id)",
]
