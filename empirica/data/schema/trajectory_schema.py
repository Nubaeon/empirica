"""
Trajectory Schema

Database table schemas for epistemic trajectory tracking.
Part of the experimental epistemic prediction system.
"""

SCHEMAS = [
    # Vector Trajectories - stores session-level trajectory metadata
    """
    CREATE TABLE IF NOT EXISTS vector_trajectories (
        trajectory_id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL,
        ai_id TEXT,
        project_id TEXT,

        -- Trajectory metadata
        snapshot_count INTEGER DEFAULT 0,
        first_timestamp REAL,
        last_timestamp REAL,
        duration_seconds REAL,

        -- Pattern detection results
        pattern TEXT,  -- 'breakthrough', 'dead_end', 'stable', 'oscillating', 'unknown'
        pattern_confidence REAL DEFAULT 0.0,
        phase_detected TEXT,  -- e.g., 'pre_breakthrough'

        -- Vector summaries (JSON)
        start_vectors TEXT,  -- JSON: initial vector state
        end_vectors TEXT,    -- JSON: final vector state
        vector_deltas TEXT,  -- JSON: cumulative deltas

        -- Analysis metadata
        analyzed_at TIMESTAMP,
        analysis_version TEXT DEFAULT '1.0',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
    """,

    # Trajectory Snapshots - individual vector measurements
    """
    CREATE TABLE IF NOT EXISTS trajectory_snapshots (
        snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
        trajectory_id TEXT NOT NULL,
        session_id TEXT NOT NULL,

        -- Snapshot data
        phase TEXT NOT NULL,  -- PREFLIGHT, CHECK, POSTFLIGHT
        round_num INTEGER DEFAULT 1,
        timestamp REAL NOT NULL,

        -- 13 epistemic vectors (denormalized for query performance)
        engagement REAL,
        know REAL,
        do_vector REAL,  -- 'do' is reserved word
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

        -- Additional data (JSON)
        vectors_json TEXT,  -- Full vector dict if more than 13
        concept_tags TEXT,  -- JSON array of tags
        reasoning TEXT,
        meta_json TEXT,     -- decision, gaps, etc.

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (trajectory_id) REFERENCES vector_trajectories(trajectory_id),
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
    """,

    # Trajectory Patterns - learned pattern templates
    """
    CREATE TABLE IF NOT EXISTS trajectory_patterns (
        pattern_id TEXT PRIMARY KEY,
        pattern_name TEXT NOT NULL UNIQUE,

        -- Pattern definition
        description TEXT,
        signature_json TEXT,  -- JSON: sequence of vector conditions
        typical_duration TEXT,

        -- Statistics
        occurrence_count INTEGER DEFAULT 0,
        success_rate REAL DEFAULT 0.0,
        avg_duration_seconds REAL,

        -- Learning metadata
        learned_from_count INTEGER DEFAULT 0,
        last_matched_at TIMESTAMP,
        confidence_threshold REAL DEFAULT 0.7,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP
    )
    """,

    # Indexes for performance
    """
    CREATE INDEX IF NOT EXISTS idx_trajectories_session
        ON vector_trajectories(session_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_trajectories_pattern
        ON vector_trajectories(pattern)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_snapshots_trajectory
        ON trajectory_snapshots(trajectory_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_snapshots_phase
        ON trajectory_snapshots(phase)
    """,
]
