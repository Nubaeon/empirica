"""
Verification Schema

Database table schemas for post-test verification system.
Provides objective grounding for epistemic calibration via
deterministic evidence (test results, artifact counts, goal completion).
"""

SCHEMAS = [
    # Grounded beliefs - parallel to bayesian_beliefs but evidence-based
    """
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
    """,

    # Evidence records - what objective evidence was collected per session
    """
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
    """,

    # Per-session grounded verification results
    """
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

        created_at REAL DEFAULT (strftime('%s', 'now')),

        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
    """,

    # POSTFLIGHT-to-POSTFLIGHT trajectory points
    """
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
    """,

    # Indexes
    """
    CREATE INDEX IF NOT EXISTS idx_grounded_beliefs_ai_vector
        ON grounded_beliefs(ai_id, vector_name)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_verification_evidence_session
        ON verification_evidence(session_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_grounded_verifications_session
        ON grounded_verifications(session_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_calibration_trajectory_ai_vector
        ON calibration_trajectory(ai_id, vector_name, timestamp)
    """,
]
