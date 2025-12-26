"""Database schema migrations"""
import sqlite3
from typing import List, Tuple, Callable
from .migration_runner import add_column_if_missing


# Migration 1: Add CASCADE workflow columns to cascades table
def migration_001_cascade_workflow_columns(cursor: sqlite3.Cursor):
    """Add preflight/plan/postflight tracking columns to cascades"""
    add_column_if_missing(cursor, "cascades", "preflight_completed", "BOOLEAN", "0")
    add_column_if_missing(cursor, "cascades", "plan_completed", "BOOLEAN", "0")
    add_column_if_missing(cursor, "cascades", "postflight_completed", "BOOLEAN", "0")


# Migration 2: Add epistemic delta tracking to cascades
def migration_002_epistemic_delta(cursor: sqlite3.Cursor):
    """Add epistemic_delta JSON column to cascades"""
    add_column_if_missing(cursor, "cascades", "epistemic_delta", "TEXT")


# Migration 3: Add goal tracking to cascades
def migration_003_cascade_goal_tracking(cursor: sqlite3.Cursor):
    """Add goal_id and goal_json to cascades"""
    add_column_if_missing(cursor, "cascades", "goal_id", "TEXT")
    add_column_if_missing(cursor, "cascades", "goal_json", "TEXT")


# Migration 4: Add status column to goals
def migration_004_goals_status(cursor: sqlite3.Cursor):
    """Add status tracking to goals table"""
    add_column_if_missing(cursor, "goals", "status", "TEXT", "'in_progress'")


# Migration 5: Add project_id to sessions
def migration_005_sessions_project_id(cursor: sqlite3.Cursor):
    """Add project_id foreign key to sessions"""
    add_column_if_missing(cursor, "sessions", "project_id", "TEXT")


# Migration 6: Add subject filtering to sessions
def migration_006_sessions_subject(cursor: sqlite3.Cursor):
    """Add subject column to sessions for filtering"""
    add_column_if_missing(cursor, "sessions", "subject", "TEXT")


# Migration 7: Add impact scoring to project_findings
def migration_007_findings_impact(cursor: sqlite3.Cursor):
    """Add impact column to project_findings for importance weighting"""
    add_column_if_missing(cursor, "project_findings", "impact", "REAL")


# All migrations in execution order
ALL_MIGRATIONS: List[Tuple[str, str, Callable]] = [
    ("001_cascade_workflow_columns", "Add CASCADE workflow tracking to cascades", migration_001_cascade_workflow_columns),
    ("002_epistemic_delta", "Add epistemic delta JSON to cascades", migration_002_epistemic_delta),
    ("003_cascade_goal_tracking", "Add goal tracking to cascades", migration_003_cascade_goal_tracking),
    ("004_goals_status", "Add status column to goals", migration_004_goals_status),
    ("005_sessions_project_id", "Add project_id to sessions", migration_005_sessions_project_id),
    ("006_sessions_subject", "Add subject filtering to sessions", migration_006_sessions_subject),
    ("007_findings_impact", "Add impact scoring to project_findings", migration_007_findings_impact),
]
