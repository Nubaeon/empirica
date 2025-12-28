"""
Sessions Schema

Database table schemas for sessions-related tables.
Extracted from SessionDatabase._create_tables()
"""

SCHEMAS = [
    # Schema 1
    """
    CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    ai_id TEXT NOT NULL,
                    user_id TEXT,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    components_loaded INTEGER NOT NULL,
                    total_turns INTEGER DEFAULT 0,
                    total_cascades INTEGER DEFAULT 0,
                    avg_confidence REAL,
                    drift_detected BOOLEAN DEFAULT 0,
                    session_notes TEXT,
                    bootstrap_level INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
    """,

    # Schema 2
    """
    CREATE TABLE IF NOT EXISTS cascades (
                    cascade_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    task TEXT NOT NULL,
                    context_json TEXT,
                    goal_id TEXT,
                    goal_json TEXT,
                    
                    preflight_completed BOOLEAN DEFAULT 0,
                    think_completed BOOLEAN DEFAULT 0,
                    plan_completed BOOLEAN DEFAULT 0,
                    investigate_completed BOOLEAN DEFAULT 0,
                    check_completed BOOLEAN DEFAULT 0,
                    act_completed BOOLEAN DEFAULT 0,
                    postflight_completed BOOLEAN DEFAULT 0,
                    
                    final_action TEXT,
                    final_confidence REAL,
                    investigation_rounds INTEGER DEFAULT 0,
                    
                    duration_ms INTEGER,
                    started_at TIMESTAMP NOT NULL,
                    completed_at TIMESTAMP,
                    
                    engagement_gate_passed BOOLEAN,
                    bayesian_active BOOLEAN DEFAULT 0,
                    drift_monitored BOOLEAN DEFAULT 0,
                    
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
    """,

]
