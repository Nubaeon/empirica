"""
Tracking Schema

Database table schemas for tracking-related tables.
Extracted from SessionDatabase._create_tables()
"""

SCHEMAS = [
    # Schema 1
    """
    CREATE TABLE IF NOT EXISTS divergence_tracking (
                    divergence_id TEXT PRIMARY KEY,
                    cascade_id TEXT NOT NULL,
                    turn_number INTEGER NOT NULL,
                    
                    delegate_perspective TEXT,
                    trustee_perspective TEXT,
                    
                    divergence_score REAL NOT NULL,
                    divergence_reason TEXT,
                    synthesis_needed BOOLEAN NOT NULL,
                    
                    delegate_weight REAL,
                    trustee_weight REAL,
                    tension_acknowledged BOOLEAN,
                    final_response TEXT,
                    synthesis_strategy TEXT,
                    
                    user_alerted BOOLEAN DEFAULT 0,
                    sycophancy_reset BOOLEAN DEFAULT 0,
                    
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (cascade_id) REFERENCES cascades(cascade_id)
                )
    """,

    # Schema 2
    """
    CREATE TABLE IF NOT EXISTS drift_monitoring (
                    drift_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    analysis_window_start TIMESTAMP,
                    analysis_window_end TIMESTAMP,
                    
                    sycophancy_detected BOOLEAN DEFAULT 0,
                    delegate_weight_early REAL,
                    delegate_weight_recent REAL,
                    delegate_weight_drift REAL,
                    
                    tension_avoidance_detected BOOLEAN DEFAULT 0,
                    tension_rate_early REAL,
                    tension_rate_recent REAL,
                    tension_rate_drift REAL,
                    
                    recommendation TEXT,
                    severity TEXT,
                    
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
    """,

    # Schema 3
    """
    CREATE TABLE IF NOT EXISTS investigation_tools (
                    tool_execution_id TEXT PRIMARY KEY,
                    cascade_id TEXT NOT NULL,
                    round_number INTEGER NOT NULL,
                    
                    tool_name TEXT NOT NULL,
                    tool_purpose TEXT,
                    target_vector TEXT,
                    
                    success BOOLEAN NOT NULL,
                    confidence_gain REAL,
                    information_gained TEXT,
                    
                    duration_ms INTEGER,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (cascade_id) REFERENCES cascades(cascade_id)
                )
    """,

    # Schema 4
    """
    CREATE TABLE IF NOT EXISTS investigation_logs (
                    log_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    cascade_id TEXT,
                    round_number INTEGER NOT NULL,
                    tools_mentioned TEXT,
                    findings TEXT,
                    confidence_before REAL,
                    confidence_after REAL,
                    summary TEXT,
                    assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                    FOREIGN KEY (cascade_id) REFERENCES cascades(cascade_id)
                )
    """,

    # Schema 5
    """
    CREATE TABLE IF NOT EXISTS act_logs (
                    act_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    cascade_id TEXT,
                    action_type TEXT NOT NULL,
                    action_rationale TEXT,
                    final_confidence REAL,
                    goal_id TEXT,
                    assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                    FOREIGN KEY (cascade_id) REFERENCES cascades(cascade_id)
                )
    """,

    # Schema 6
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

    # Schema 7
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

    # Schema 8
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

    # Schema 9
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
