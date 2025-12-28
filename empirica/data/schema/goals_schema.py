"""
Goals Schema

Database table schemas for goals-related tables.
Extracted from SessionDatabase._create_tables()
"""

SCHEMAS = [
    # Schema 1
    """
    CREATE TABLE IF NOT EXISTS goals (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    objective TEXT NOT NULL,
                    scope TEXT NOT NULL,  -- JSON: {breadth, duration, coordination}
                    estimated_complexity REAL,
                    created_timestamp REAL NOT NULL,
                    completed_timestamp REAL,
                    is_completed BOOLEAN DEFAULT 0,
                    goal_data TEXT NOT NULL,
                    status TEXT DEFAULT 'in_progress',  -- 'in_progress' | 'complete' | 'blocked'
                    beads_issue_id TEXT,  -- Optional: Link to BEADS issue tracker (e.g., bd-a1b2)
    
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
    """,

    # Schema 2
    """
    CREATE TABLE IF NOT EXISTS subtasks (
                    id TEXT PRIMARY KEY,
                    goal_id TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    epistemic_importance TEXT NOT NULL DEFAULT 'medium',
                    estimated_tokens INTEGER,
                    actual_tokens INTEGER,
                    completion_evidence TEXT,
                    notes TEXT,
                    created_timestamp REAL NOT NULL,
                    completed_timestamp REAL,
                    subtask_data TEXT NOT NULL,
    
                    FOREIGN KEY (goal_id) REFERENCES goals(id)
                )
    """,

]
