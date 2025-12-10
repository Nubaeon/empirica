#!/usr/bin/env python3
"""
Session Database - SQLite storage for epistemic states and reasoning cascades

Stores:
- Sessions (AI sessions with metadata)
- Cascades (reasoning cascade executions)
- Epistemic Assessments (12D vector measurements)
- Divergence Tracking (delegate vs trustee, sycophancy detection)
- Drift Monitoring (long-term behavioral patterns)
- Bayesian Beliefs (evidence-based belief tracking)
- Investigation Tools (tool usage tracking)

Design:
- SQLite as source of truth (structured queries, relational integrity)
- JSON exports for AI-readable format (easy parsing)
- Temporal logging (prevents recursion)
- Session continuity (load previous session context)

Location (Canonical):
- Project-local: ./.empirica/sessions/sessions.db (relative to CWD)
- NOT home directory: ~/ (config/credentials are global, data is project-scoped)
- See: docs/reference/STORAGE_LOCATIONS.md for rationale

Storage Architecture:
- Global (~/.empirica/): config.yaml, credentials.yaml, calibration/
- Project-local (./.empirica/): sessions.db (this file)
"""

import sqlite3
import json
import uuid
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import asdict

logger = logging.getLogger(__name__)

# Import canonical structures
try:
    from canonical.reflex_frame import EpistemicAssessment, VectorState, Action
    CANONICAL_AVAILABLE = True
except ImportError:
    CANONICAL_AVAILABLE = False


class SessionDatabase:
    """Central SQLite database for all session data"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Use path resolver for consistent database location
            from empirica.config.path_resolver import get_session_db_path
            db_path = get_session_db_path()

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Return rows as dicts

        self._create_tables()
        logger.info(f"📊 Session Database initialized: {self.db_path}")

    @staticmethod
    def _validate_session_id(session_id: str) -> None:
        """
        Validate session_id is a proper UUID format.

        This ensures:
        - Session IDs are globally unique
        - Git notes refs are valid paths
        - Session aliases work correctly
        - Multi-AI coordination is safe

        Args:
            session_id: Session ID to validate

        Raises:
            ValueError: If session_id is not a valid UUID
        """
        try:
            uuid.UUID(session_id)
        except (ValueError, AttributeError, TypeError):
            raise ValueError(
                f"Invalid session_id: '{session_id}'. "
                f"Session IDs must be valid UUIDs (e.g., '550e8400-e29b-41d4-a716-446655440000')"
            )
    
    def _create_tables(self):
        """Create all database tables"""
        cursor = self.conn.cursor()
        
        # Table 1: sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                ai_id TEXT NOT NULL,
                user_id TEXT,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                bootstrap_level INTEGER NOT NULL,
                components_loaded INTEGER NOT NULL,
                total_turns INTEGER DEFAULT 0,
                total_cascades INTEGER DEFAULT 0,
                avg_confidence REAL,
                drift_detected BOOLEAN DEFAULT 0,
                session_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table 2: cascades (Enhanced Cascade Workflow v1.2 - with goal tracking)
        cursor.execute("""
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
        """)
        
        # Migration: Add new columns if they don't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE cascades ADD COLUMN preflight_completed BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE cascades ADD COLUMN plan_completed BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE cascades ADD COLUMN postflight_completed BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE cascades ADD COLUMN epistemic_delta TEXT")  # JSON
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE cascades ADD COLUMN goal_id TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE cascades ADD COLUMN goal_json TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Migration for goals table: Add status column if missing
        try:
            cursor.execute("ALTER TABLE goals ADD COLUMN status TEXT DEFAULT 'in_progress'")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Migration for sessions table: Add project_id column if missing
        try:
            cursor.execute("ALTER TABLE sessions ADD COLUMN project_id TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Note: Deprecated tables (epistemic_assessments, preflight_assessments,
        # postflight_assessments, check_phase_assessments) have been removed.
        # All epistemic data is now stored in the unified reflexes table.
        # Migration happens automatically in _migrate_legacy_tables_to_reflexes()
        
        # Table 4: divergence_tracking
        cursor.execute("""
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
        """)
        
        # Table 5: drift_monitoring
        cursor.execute("""
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
        """)
        
        # Table 6: bayesian_beliefs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bayesian_beliefs (
                belief_id TEXT PRIMARY KEY,
                cascade_id TEXT NOT NULL,
                vector_name TEXT NOT NULL,
                
                mean REAL NOT NULL,
                variance REAL NOT NULL,
                evidence_count INTEGER DEFAULT 0,
                
                prior_mean REAL NOT NULL,
                prior_variance REAL NOT NULL,
                
                last_updated TIMESTAMP,
                
                FOREIGN KEY (cascade_id) REFERENCES cascades(cascade_id)
            )
        """)
        
        # Table 7: investigation_tools
        cursor.execute("""
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
        """)
        
        
        # Note: cascade_metadata table removed - all CASCADE data now in unified reflexes table
        
        # Table 12: investigation_logs (NEW - investigation phase tracking)
        cursor.execute("""
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
        """)
        
        # Table 13: act_logs (NEW - action phase tracking)
        cursor.execute("""
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
        """)

        # Table 14: epistemic_snapshots (Cross-AI Context Transfer)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS epistemic_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                ai_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,

                cascade_phase TEXT,
                cascade_id TEXT,

                vectors TEXT NOT NULL,
                delta TEXT,
                previous_snapshot_id TEXT,

                context_summary TEXT,
                evidence_refs TEXT,
                db_session_ref TEXT,

                domain_vectors TEXT,

                original_context_tokens INTEGER DEFAULT 0,
                snapshot_tokens INTEGER DEFAULT 0,
                compression_ratio REAL DEFAULT 0.0,

                information_loss_estimate REAL DEFAULT 0.0,
                fidelity_score REAL DEFAULT 1.0,

                transfer_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                FOREIGN KEY (cascade_id) REFERENCES cascades(cascade_id),
                FOREIGN KEY (previous_snapshot_id) REFERENCES epistemic_snapshots(snapshot_id)
            )
        """)

        # Table 15: reflexes (NEW - for checkpoint system)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reflexes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                cascade_id TEXT,
                phase TEXT NOT NULL,
                round INTEGER DEFAULT 1,
                timestamp REAL NOT NULL,

                -- 13 epistemic vectors
                engagement REAL,
                know REAL,
                do REAL,
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

                -- Metadata
                reflex_data TEXT,
                reasoning TEXT,
                evidence TEXT,

                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # Table 16: goals (Goal/Subtask Tracking for Decision Quality)
        cursor.execute("""
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

                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # Table 17: subtasks (Investigation and Work Items)
        cursor.execute("""
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
        """)

        # Table 18: mistakes_made (Learning from Failures)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mistakes_made (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                goal_id TEXT,
                mistake TEXT NOT NULL,
                why_wrong TEXT NOT NULL,
                cost_estimate TEXT,
                root_cause_vector TEXT,
                prevention TEXT,
                created_timestamp REAL NOT NULL,
                mistake_data TEXT NOT NULL,

                FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                FOREIGN KEY (goal_id) REFERENCES goals(id)
            )
        """)

        # Table 19: projects (Multi-Repo Long-Term Work Tracking)
        cursor.execute("""
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
        """)

        # Table 20: project_handoffs (Project-Level Epistemic Continuity)
        cursor.execute("""
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
        """)

        # Table 21: project_findings (What Was Learned/Discovered)
        cursor.execute("""
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
        """)

        # Table 22: project_unknowns (What's Still Unclear)
        cursor.execute("""
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
        """)

        # Table 23: project_dead_ends (What Didn't Work)
        cursor.execute("""
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
        """)

        # Table 24: project_reference_docs (Key Documentation)
        cursor.execute("""
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
        """)

        # Table 25: investigation_branches (Parallel investigation paths for epistemic auto-merge)
        cursor.execute("""
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
        """)

        # Table 26: merge_decisions (Auto-merge decision history and rationale)
        cursor.execute("""
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
        """)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_ai ON sessions(ai_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cascades_session ON cascades(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cascades_confidence ON cascades(final_confidence)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_divergence_cascade ON divergence_tracking(cascade_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_beliefs_cascade ON bayesian_beliefs(cascade_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tools_cascade ON investigation_tools(cascade_id)")
        # Index for reflexes table (replaces old cascade_metadata index)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_session ON epistemic_snapshots(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_ai ON epistemic_snapshots(ai_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_cascade ON epistemic_snapshots(cascade_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_created ON epistemic_snapshots(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reflexes_session ON reflexes(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reflexes_phase ON reflexes(phase)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_session ON goals(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_subtasks_goal ON subtasks(goal_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_subtasks_status ON subtasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mistakes_session ON mistakes_made(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mistakes_goal ON mistakes_made(goal_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_activity ON projects(last_activity_timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_handoffs_project ON project_handoffs(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_handoffs_timestamp ON project_handoffs(created_timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_findings_project ON project_findings(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_findings_session ON project_findings(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_unknowns_project ON project_unknowns(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_unknowns_resolved ON project_unknowns(is_resolved)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_dead_ends_project ON project_dead_ends(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_reference_docs_project ON project_reference_docs(project_id)")

        # Indexes for investigation_branches
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_investigation_branches_session ON investigation_branches(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_investigation_branches_status ON investigation_branches(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_investigation_branches_winner ON investigation_branches(is_winner)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_investigation_branches_merge_score ON investigation_branches(merge_score)")

        # Indexes for merge_decisions
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_merge_decisions_session ON merge_decisions(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_merge_decisions_round ON merge_decisions(investigation_round)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_merge_decisions_winning_branch ON merge_decisions(winning_branch_id)")

        self.conn.commit()
        
        # Migrate legacy tables to reflexes (automatic one-time migration)
        self._migrate_legacy_tables_to_reflexes()
    
    def _migrate_legacy_tables_to_reflexes(self):
        """
        Migrate data from deprecated tables to reflexes table, then drop old tables.
        
        This runs automatically on database initialization. It's idempotent - safe to run multiple times.
        
        Migration mapping:
        - preflight_assessments → reflexes (phase='PREFLIGHT')
        - postflight_assessments → reflexes (phase='POSTFLIGHT')
        - check_phase_assessments → reflexes (phase='CHECK')
        - epistemic_assessments → (unused, just drop)
        """
        cursor = self.conn.cursor()
        
        try:
            # Check if old tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='preflight_assessments'")
            if not cursor.fetchone():
                logger.debug("✓ Legacy tables already migrated or don't exist")
                return  # Already migrated
            
            logger.info("🔄 Migrating legacy epistemic tables to reflexes...")
            
            # Migrate preflight_assessments → reflexes
            cursor.execute("""
                INSERT INTO reflexes (session_id, cascade_id, phase, round, timestamp,
                                    engagement, know, do, context, clarity, coherence, signal, density,
                                    state, change, completion, impact, uncertainty, reflex_data, reasoning)
                SELECT session_id, cascade_id, 'PREFLIGHT', 1, 
                       CAST(strftime('%s', assessed_at) AS REAL),
                       engagement, know, do, context, clarity, coherence, signal, density,
                       state, change, completion, impact, uncertainty, 
                       vectors_json, initial_uncertainty_notes
                FROM preflight_assessments
                WHERE NOT EXISTS (
                    SELECT 1 FROM reflexes r
                    WHERE r.session_id = preflight_assessments.session_id
                    AND r.phase = 'PREFLIGHT'
                    AND r.cascade_id IS preflight_assessments.cascade_id
                )
            """)
            preflight_count = cursor.rowcount
            logger.info(f"  ✓ Migrated {preflight_count} preflight assessments")
            
            # Migrate postflight_assessments → reflexes
            cursor.execute("""
                INSERT INTO reflexes (session_id, cascade_id, phase, round, timestamp,
                                    engagement, know, do, context, clarity, coherence, signal, density,
                                    state, change, completion, impact, uncertainty, reflex_data, reasoning)
                SELECT session_id, cascade_id, 'POSTFLIGHT', 1,
                       CAST(strftime('%s', assessed_at) AS REAL),
                       engagement, know, do, context, clarity, coherence, signal, density,
                       state, change, completion, impact, uncertainty,
                       json_object('calibration_accuracy', calibration_accuracy, 
                                   'postflight_confidence', postflight_actual_confidence),
                       learning_notes
                FROM postflight_assessments
                WHERE NOT EXISTS (
                    SELECT 1 FROM reflexes r
                    WHERE r.session_id = postflight_assessments.session_id
                    AND r.phase = 'POSTFLIGHT'
                    AND r.cascade_id IS postflight_assessments.cascade_id
                )
            """)
            postflight_count = cursor.rowcount
            logger.info(f"  ✓ Migrated {postflight_count} postflight assessments")
            
            # Migrate check_phase_assessments → reflexes (confidence → uncertainty conversion)
            cursor.execute("""
                INSERT INTO reflexes (session_id, cascade_id, phase, round, timestamp,
                                    uncertainty, reflex_data, reasoning)
                SELECT session_id, cascade_id, 'CHECK', investigation_cycle,
                       CAST(strftime('%s', assessed_at) AS REAL),
                       (1.0 - confidence),
                       json_object('decision', decision, 
                                   'gaps_identified', gaps_identified,
                                   'next_investigation_targets', next_investigation_targets,
                                   'confidence', confidence),
                       self_assessment_notes
                FROM check_phase_assessments
                WHERE NOT EXISTS (
                    SELECT 1 FROM reflexes r
                    WHERE r.session_id = check_phase_assessments.session_id
                    AND r.phase = 'CHECK'
                    AND r.cascade_id IS check_phase_assessments.cascade_id
                    AND r.round = check_phase_assessments.investigation_cycle
                )
            """)
            check_count = cursor.rowcount
            logger.info(f"  ✓ Migrated {check_count} check phase assessments")
            
            self.conn.commit()
            
            # Drop old tables (no longer needed)
            logger.info("  🗑️  Dropping deprecated tables...")
            cursor.execute("DROP TABLE IF EXISTS epistemic_assessments")
            cursor.execute("DROP TABLE IF EXISTS preflight_assessments")
            cursor.execute("DROP TABLE IF EXISTS postflight_assessments")
            cursor.execute("DROP TABLE IF EXISTS check_phase_assessments")
            
            self.conn.commit()
            logger.info("✅ Migration complete: All data moved to reflexes table")
            
        except sqlite3.OperationalError as e:
            # Table doesn't exist or already migrated - this is fine
            logger.debug(f"Migration check: {e} (this is expected if tables don't exist)")
        except Exception as e:
            logger.error(f"⚠️  Migration failed: {e}")
            # Don't raise - allow database to continue working
            # Old tables will remain if migration fails
    
    def create_session(self, ai_id: str, bootstrap_level: int = 0, components_loaded: int = 0, 
                      user_id: Optional[str] = None) -> str:
        """
        Create new session, return session_id.
        
        Args:
            ai_id: AI identifier (required)
            bootstrap_level: Bootstrap level (0-4 or minimal/standard/complete) - default 0
            components_loaded: Number of components loaded - default 0 (components created on-demand)
            user_id: Optional user identifier
            
        Returns:
            session_id: UUID string
        """
        session_id = str(uuid.uuid4())
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO sessions (
                session_id, ai_id, user_id, start_time, bootstrap_level, components_loaded
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, ai_id, user_id, datetime.now(), bootstrap_level, components_loaded))
        
        self.conn.commit()
        return session_id
    
    def end_session(self, session_id: str, avg_confidence: Optional[float] = None,
                   drift_detected: bool = False, notes: Optional[str] = None):
        """Mark session as ended"""
        self._validate_session_id(session_id)

        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE sessions
            SET end_time = ?, avg_confidence = ?, drift_detected = ?, session_notes = ?
            WHERE session_id = ?
        """, (datetime.now(), avg_confidence, drift_detected, notes, session_id))

        self.conn.commit()
    
    def create_cascade(self, session_id: str, task: str, context: Dict[str, Any],
                      goal_id: Optional[str] = None, goal: Optional[Dict[str, Any]] = None) -> str:
        """
        Create cascade record, return cascade_id

        Args:
            session_id: Session identifier
            task: Task description
            context: Context dictionary
            goal_id: Optional goal identifier
            goal: Optional full goal object
        """
        self._validate_session_id(session_id)
        cascade_id = str(uuid.uuid4())
        goal_json = json.dumps(goal) if goal else None
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO cascades (
                cascade_id, session_id, task, context_json, goal_id, goal_json, started_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (cascade_id, session_id, task, json.dumps(context), goal_id, goal_json, datetime.now()))
        
        # Increment session cascade count
        cursor.execute("""
            UPDATE sessions SET total_cascades = total_cascades + 1
            WHERE session_id = ?
        """, (session_id,))
        
        self.conn.commit()
        return cascade_id
    
    def update_cascade_phase(self, cascade_id: str, phase: str, completed: bool = True):
        """Mark cascade phase as completed"""
        # SECURITY: Validate phase parameter to prevent SQL injection
        VALID_PHASES = {'preflight', 'think', 'plan', 'investigate', 'check', 'act', 'postflight'}
        if phase not in VALID_PHASES:
            raise ValueError(f"Invalid phase: {phase}. Must be one of {VALID_PHASES}")
        
        phase_column = f"{phase}_completed"
        cursor = self.conn.cursor()
        cursor.execute(f"""
            UPDATE cascades SET {phase_column} = ? WHERE cascade_id = ?
        """, (completed, cascade_id))
        self.conn.commit()
    
    def complete_cascade(self, cascade_id: str, final_action: str, final_confidence: float,
                        investigation_rounds: int, duration_ms: int,
                        engagement_gate_passed: bool, bayesian_active: bool = False,
                        drift_monitored: bool = False):
        """Mark cascade as completed with final results"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE cascades SET
                final_action = ?,
                final_confidence = ?,
                investigation_rounds = ?,
                duration_ms = ?,
                completed_at = ?,
                engagement_gate_passed = ?,
                bayesian_active = ?,
                drift_monitored = ?
            WHERE cascade_id = ?
        """, (final_action, final_confidence, investigation_rounds, duration_ms,
              datetime.now(), engagement_gate_passed, bayesian_active, drift_monitored,
              cascade_id))
        
        self.conn.commit()
    
    def log_epistemic_assessment(self, cascade_id: str, assessment: Any, 
                                phase: str):
        """
        DEPRECATED: Use store_vectors() instead.
        
        This method is kept for backward compatibility with canonical structures.
        """
        if not CANONICAL_AVAILABLE:
            logger.warning("[DB] Canonical structures not available, skipping epistemic assessment")
            return
        
        # Extract vectors from assessment object
        vectors = {
            'engagement': assessment.engagement.score,
            'know': assessment.know.score,
            'do': assessment.do.score,
            'context': assessment.context.score,
            'clarity': assessment.clarity.score,
            'coherence': assessment.coherence.score,
            'signal': assessment.signal.score,
            'density': assessment.density.score,
            'state': assessment.state.score,
            'change': assessment.change.score,
            'completion': assessment.completion.score,
            'impact': assessment.impact.score,
            'uncertainty': assessment.uncertainty.score
        }
        
        # Build metadata from rationales
        metadata = {
            'assessment_id': assessment.assessment_id,
            'engagement_gate_passed': assessment.engagement_gate_passed,
            'foundation_confidence': assessment.foundation_confidence,
            'comprehension_confidence': assessment.comprehension_confidence,
            'execution_confidence': assessment.execution_confidence,
            'overall_confidence': assessment.overall_confidence,
            'recommended_action': assessment.recommended_action.value
        }
        
        # Get session_id from cascade
        cursor = self.conn.cursor()
        cursor.execute("SELECT session_id FROM cascades WHERE cascade_id = ?", (cascade_id,))
        row = cursor.fetchone()
        if not row:
            logger.error(f"Cascade {cascade_id} not found")
            return
        
        session_id = row[0]
        
        # Store using reflexes table
        self.store_vectors(
            session_id=session_id,
            phase=phase.upper(),
            vectors=vectors,
            cascade_id=cascade_id,
            metadata=metadata
        )
    
    def log_divergence(self, cascade_id: str, turn_number: int, delegate: str, trustee: str,
                      divergence_score: float, divergence_reason: str,
                      synthesis_needed: bool, synthesis_data: Optional[Dict] = None):
        """Track delegate vs trustee divergence"""
        divergence_id = str(uuid.uuid4())
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO divergence_tracking (
                divergence_id, cascade_id, turn_number,
                delegate_perspective, trustee_perspective,
                divergence_score, divergence_reason, synthesis_needed,
                delegate_weight, trustee_weight, tension_acknowledged,
                final_response, synthesis_strategy
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            divergence_id, cascade_id, turn_number,
            json.dumps(delegate), json.dumps(trustee),
            divergence_score, divergence_reason, synthesis_needed,
            synthesis_data.get('delegate_weight') if synthesis_data else None,
            synthesis_data.get('trustee_weight') if synthesis_data else None,
            synthesis_data.get('tension_acknowledged') if synthesis_data else None,
            synthesis_data.get('final_response') if synthesis_data else None,
            synthesis_data.get('strategy') if synthesis_data else None
        ))
        
        self.conn.commit()
    
    def log_bayesian_belief(self, cascade_id: str, vector_name: str, mean: float,
                           variance: float, evidence_count: int,
                           prior_mean: float, prior_variance: float):
        """Track Bayesian belief updates"""
        belief_id = str(uuid.uuid4())
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO bayesian_beliefs (
                belief_id, cascade_id, vector_name,
                mean, variance, evidence_count,
                prior_mean, prior_variance, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            belief_id, cascade_id, vector_name,
            mean, variance, evidence_count,
            prior_mean, prior_variance, datetime.now()
        ))
        
        self.conn.commit()
    
    def log_tool_execution(self, cascade_id: str, round_number: int, tool_name: str,
                          tool_purpose: str, target_vector: str, success: bool,
                          confidence_gain: float, information: Dict,
                          duration_ms: int):
        """Track investigation tool usage"""
        tool_id = str(uuid.uuid4())
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO investigation_tools (
                tool_execution_id, cascade_id, round_number,
                tool_name, tool_purpose, target_vector,
                success, confidence_gain, information_gained, duration_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tool_id, cascade_id, round_number,
            tool_name, tool_purpose, target_vector,
            success, confidence_gain, json.dumps(information), duration_ms
        ))
        
        self.conn.commit()
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_session_cascades(self, session_id: str) -> List[Dict]:
        """Get all cascades for a session"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM cascades WHERE session_id = ? ORDER BY started_at
        """, (session_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_cascade_assessments(self, cascade_id: str) -> List[Dict]:
        """
        DEPRECATED: Use reflexes table queries instead.
        
        Get all assessments for a cascade from reflexes table.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM reflexes WHERE cascade_id = ? ORDER BY timestamp
        """, (cascade_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def log_preflight_assessment(self, session_id: str, cascade_id: Optional[str],
                                 prompt_summary: str, vectors: Dict[str, float],
                                 uncertainty_notes: str = "") -> str:
        """
        DEPRECATED: Use store_vectors() instead.
        
        This method redirects to store_vectors() for backward compatibility.
        """
        # Store metadata in reflex_data
        metadata = {
            "prompt_summary": prompt_summary,
            "uncertainty_notes": uncertainty_notes
        }
        
        return self.store_vectors(
            session_id=session_id,
            phase="PREFLIGHT",
            vectors=vectors,
            cascade_id=cascade_id,
            metadata=metadata,
            reasoning=uncertainty_notes
        )
    
    def log_check_phase_assessment(self, session_id: str, cascade_id: Optional[str],
                                   investigation_cycle: int, confidence: float,
                                   decision: str, gaps: List[str],
                                   next_targets: List[str],
                                   notes: str = "",
                                   vectors: Optional[Dict[str, float]] = None,
                                   findings: Optional[List[str]] = None,
                                   remaining_unknowns: Optional[List[str]] = None) -> str:
        """
        DEPRECATED: Use store_vectors() instead.
        
        This method redirects to store_vectors() for backward compatibility.
        """
        # Store CHECK-specific data in metadata
        metadata = {
            "decision": decision,
            "confidence": confidence,
            "gaps_identified": gaps,
            "next_investigation_targets": next_targets,
            "findings": findings,
            "remaining_unknowns": remaining_unknowns
        }
        
        # If vectors provided, use them; otherwise create minimal vector with uncertainty
        if not vectors:
            vectors = {"uncertainty": 1.0 - confidence}
        
        return self.store_vectors(
            session_id=session_id,
            phase="CHECK",
            vectors=vectors,
            cascade_id=cascade_id,
            round_num=investigation_cycle,
            metadata=metadata,
            reasoning=notes
        )
    
    def log_postflight_assessment(self, session_id: str, cascade_id: Optional[str],
                                  task_summary: str, vectors: Dict[str, float],
                                  postflight_confidence: float,
                                  calibration_accuracy: str,
                                  learning_notes: str = "") -> str:
        """
        DEPRECATED: Use store_vectors() instead.
        
        This method redirects to store_vectors() for backward compatibility.
        """
        # Store postflight-specific data in metadata
        metadata = {
            "task_summary": task_summary,
            "postflight_confidence": postflight_confidence,
            "calibration_accuracy": calibration_accuracy
        }
        
        return self.store_vectors(
            session_id=session_id,
            phase="POSTFLIGHT",
            vectors=vectors,
            cascade_id=cascade_id,
            metadata=metadata,
            reasoning=learning_notes
        )
    
    def log_investigation_round(
        self,
        session_id: str,
        cascade_id: Optional[str],
        round_number: int,
        tools_mentioned: Optional[str] = None,
        findings: Optional[str] = None,
        confidence_before: Optional[float] = None,
        confidence_after: Optional[float] = None,
        summary: Optional[str] = None
    ) -> str:
        """Log investigation round for transparency"""
        log_id = str(uuid.uuid4())
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO investigation_logs (
                log_id, session_id, cascade_id, round_number,
                tools_mentioned, findings, confidence_before, confidence_after, summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log_id, session_id, cascade_id, round_number,
            tools_mentioned, findings, confidence_before, confidence_after, summary
        ))
        
        self.conn.commit()
        
        # Export to reflex logs for dashboard
        try:
            self._export_to_reflex_logs(
                session_id=session_id,
                phase="investigate",
                assessment_data={
                    "log_id": log_id,
                    "cascade_id": cascade_id,
                    "round_number": round_number,
                    "tools_mentioned": tools_mentioned,
                    "findings": findings,
                    "confidence_before": confidence_before,
                    "confidence_after": confidence_after,
                    "summary": summary or f"Investigation round {round_number}"
                }
            )
        except Exception:
            pass  # Silent fail - reflex export is not critical
        
        return log_id
    
    def log_act_phase(
        self,
        session_id: str,
        cascade_id: Optional[str],
        action_type: str,
        action_rationale: Optional[str] = None,
        final_confidence: Optional[float] = None,
        goal_id: Optional[str] = None
    ) -> str:
        """Log ACT phase decision for transparency and audit trail"""
        act_id = str(uuid.uuid4())
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO act_logs (
                act_id, session_id, cascade_id, action_type,
                action_rationale, final_confidence, goal_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            act_id, session_id, cascade_id, action_type,
            action_rationale, final_confidence, goal_id
        ))
        
        self.conn.commit()
        
        # Export to reflex logs for dashboard
        try:
            self._export_to_reflex_logs(
                session_id=session_id,
                phase="act",
                assessment_data={
                    "act_id": act_id,
                    "cascade_id": cascade_id,
                    "action_type": action_type,
                    "action_rationale": action_rationale,
                    "final_confidence": final_confidence,
                    "goal_id": goal_id
                }
            )
        except Exception:
            pass  # Silent fail - reflex export is not critical
        
        return act_id
    
    def _export_to_reflex_logs(
        self,
        session_id: str,
        phase: str,
        assessment_data: Dict[str, Any],
        log_dir: str = ".empirica_reflex_logs"
    ) -> Optional[Path]:
        """Export assessment to reflex log format for dashboard visualization"""
        try:
            from datetime import datetime
            
            vectors = assessment_data.get("vectors", {})
            
            # Load configuration weights for confidence calculations
            try:
                import yaml
                from pathlib import Path

                # Load the confidence weights configuration
                config_path = Path(__file__).parent.parent / "config" / "mco" / "confidence_weights.yaml"
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config = yaml.safe_load(f)

                    foundation_weights = config.get("foundation_confidence_weights", {
                        'know': 0.4,
                        'do': 0.3,
                        'context': 0.3
                    })
                else:
                    # Default weights if config file not found
                    foundation_weights = {
                        'know': 0.4,
                        'do': 0.3,
                        'context': 0.3
                    }
            except Exception:
                # Fallback to original hardcoded values if config loading fails
                foundation_weights = {
                    'know': 0.4,
                    'do': 0.3,
                    'context': 0.3
                }

            # Calculate confidence scores using configurable weights
            foundation_confidence = (
                vectors.get('know', 0.5) * foundation_weights.get('know', 0.4) +
                vectors.get('do', 0.5) * foundation_weights.get('do', 0.3) +
                vectors.get('context', 0.5) * foundation_weights.get('context', 0.3)
            )

            # Load comprehension weights
            try:
                comprehension_weights = config.get("comprehension_confidence_weights", {
                    'clarity': 0.3,
                    'coherence': 0.3,
                    'signal': 0.2,
                    'density': 0.2
                }) if 'config' in locals() else {
                    'clarity': 0.3,
                    'coherence': 0.3,
                    'signal': 0.2,
                    'density': 0.2
                }
            except:
                comprehension_weights = {
                    'clarity': 0.3,
                    'coherence': 0.3,
                    'signal': 0.2,
                    'density': 0.2
                }

            comprehension_confidence = (
                vectors.get('clarity', 0.5) * comprehension_weights.get('clarity', 0.3) +
                vectors.get('coherence', 0.5) * comprehension_weights.get('coherence', 0.3) +
                vectors.get('signal', 0.5) * comprehension_weights.get('signal', 0.2) +
                (1.0 - vectors.get('density', 0.5)) * comprehension_weights.get('density', 0.2)
            )

            # Load execution weights
            try:
                execution_weights = config.get("execution_confidence_weights", {
                    'state': 0.25,
                    'change': 0.25,
                    'completion': 0.25,
                    'impact': 0.25
                }) if 'config' in locals() else {
                    'state': 0.25,
                    'change': 0.25,
                    'completion': 0.25,
                    'impact': 0.25
                }
            except:
                execution_weights = {
                    'state': 0.25,
                    'change': 0.25,
                    'completion': 0.25,
                    'impact': 0.25
                }

            execution_confidence = (
                vectors.get('state', 0.5) * execution_weights.get('state', 0.25) +
                vectors.get('change', 0.5) * execution_weights.get('change', 0.25) +
                vectors.get('completion', 0.5) * execution_weights.get('completion', 0.25) +
                vectors.get('impact', 0.5) * execution_weights.get('impact', 0.25)
            )

            # Load overall weights
            try:
                overall_weights = config.get("overall_confidence_weights", {
                    'foundation': 0.35,
                    'comprehension': 0.25,
                    'execution': 0.25,
                    'engagement': 0.15
                }) if 'config' in locals() else {
                    'foundation': 0.35,
                    'comprehension': 0.25,
                    'execution': 0.25,
                    'engagement': 0.15
                }
            except:
                overall_weights = {
                    'foundation': 0.35,
                    'comprehension': 0.25,
                    'execution': 0.25,
                    'engagement': 0.15
                }

            overall_confidence = (
                foundation_confidence * overall_weights.get('foundation', 0.35) +
                comprehension_confidence * overall_weights.get('comprehension', 0.25) +
                execution_confidence * overall_weights.get('execution', 0.25) +
                vectors.get('engagement', 0.5) * overall_weights.get('engagement', 0.15)
            )
            
            # Build metaStateVector (current phase = 1.0, others = 0.0)
            meta_state = {
                "preflight": 1.0 if phase == "preflight" else 0.0,
                "think": 0.0,
                "plan": 0.0,
                "investigate": 0.0,
                "check": 1.0 if phase == "check" else 0.0,
                "act": 0.0,
                "postflight": 1.0 if phase == "postflight" else 0.0
            }
            
            # Create ReflexFrame structure
            frame_data = {
                "frameId": f"{session_id}_{phase}_{assessment_data.get('assessment_id', 'unknown')}",
                "timestamp": datetime.utcnow().isoformat(),
                "selfAwareFlag": True,
                "epistemicVector": {
                    **vectors,
                    "foundation_confidence": foundation_confidence,
                    "comprehension_confidence": comprehension_confidence,
                    "execution_confidence": execution_confidence,
                    "overall_confidence": overall_confidence,
                    "engagement_gate_passed": vectors.get('engagement', 0) >= 0.6
                },
                "metaStateVector": meta_state,
                "recommendedAction": self._determine_action(vectors),
                "criticalFlags": {
                    "coherence_critical": vectors.get('coherence', 1.0) < 0.5,
                    "density_critical": vectors.get('density', 0.0) > 0.9,
                    "change_critical": vectors.get('change', 1.0) < 0.5
                },
                "task": assessment_data.get("task_summary", assessment_data.get("prompt_summary", "Unknown task")),
                "session_id": session_id,
                "cascade_id": assessment_data.get("cascade_id"),
                "phase": phase,
                "full_assessment": assessment_data
            }
            
            # Write JSON
            log_date = datetime.utcnow().date()
            agent_dir = Path(log_dir) / session_id / log_date.isoformat()
            agent_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
            filename = f"reflex_frame_{timestamp}_{phase}.json"
            log_path = agent_dir / filename
            
            with open(log_path, 'w') as f:
                json.dump(frame_data, f, indent=2)
            
            return log_path
            
        except Exception as e:
            return None
    
    def _determine_action(self, vectors: Dict[str, float]) -> str:
        """Determine recommended action based on vectors"""
        if vectors.get('coherence', 1.0) < 0.5 or vectors.get('density', 0.0) > 0.9:
            return "reset"
        if vectors.get('change', 1.0) < 0.5:
            return "stop"
        if vectors.get('engagement', 1.0) < 0.6:
            return "clarify"
        if vectors.get('uncertainty', 0.0) > 0.8:
            return "investigate"
        return "proceed"
    
    def get_preflight_assessment(self, session_id: str) -> Optional[Dict]:
        """
        DEPRECATED: Use get_latest_vectors(session_id, phase='PREFLIGHT') instead.
        
        This method redirects to reflexes table for backward compatibility.
        """
        return self.get_latest_vectors(session_id, phase="PREFLIGHT")
    
    def get_check_phase_assessments(self, session_id: str) -> List[Dict]:
        """
        DEPRECATED: Use get_vectors_by_phase(session_id, phase='CHECK') instead.
        
        This method redirects to reflexes table for backward compatibility.
        """
        return self.get_vectors_by_phase(session_id, phase="CHECK")
    
    def get_postflight_assessment(self, session_id: str) -> Optional[Dict]:
        """
        DEPRECATED: Use get_latest_vectors(session_id, phase='POSTFLIGHT') instead.
        
        This method redirects to reflexes table for backward compatibility.
        """
        return self.get_latest_vectors(session_id, phase="POSTFLIGHT")
    
    def get_preflight_vectors(self, session_id: str) -> Optional[Dict]:
        """Get latest PREFLIGHT vectors for session (convenience method)"""
        return self.get_latest_vectors(session_id, phase="PREFLIGHT")
    
    def get_check_vectors(self, session_id: str, cycle: Optional[int] = None) -> List[Dict]:
        """Get CHECK phase vectors, optionally filtered by cycle"""
        vectors = self.get_vectors_by_phase(session_id, phase="CHECK")
        if cycle is not None:
            return [v for v in vectors if v.get('round') == cycle]
        return vectors
    
    def get_postflight_vectors(self, session_id: str) -> Optional[Dict]:
        """Get latest POSTFLIGHT vectors for session (convenience method)"""
        return self.get_latest_vectors(session_id, phase="POSTFLIGHT")
    
    def get_vectors_by_phase(self, session_id: str, phase: str) -> List[Dict]:
        """Get all vectors for a specific phase"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM reflexes 
            WHERE session_id = ? AND phase = ? 
            ORDER BY timestamp ASC
        """, (session_id, phase))
        
        results = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            # Build vectors dict from columns
            vectors = {
                'engagement': row_dict.get('engagement'),
                'know': row_dict.get('know'),
                'do': row_dict.get('do'),
                'context': row_dict.get('context'),
                'clarity': row_dict.get('clarity'),
                'coherence': row_dict.get('coherence'),
                'signal': row_dict.get('signal'),
                'density': row_dict.get('density'),
                'state': row_dict.get('state'),
                'change': row_dict.get('change'),
                'completion': row_dict.get('completion'),
                'impact': row_dict.get('impact'),
                'uncertainty': row_dict.get('uncertainty')
            }
            # Remove None values
            vectors = {k: v for k, v in vectors.items() if v is not None}
            
            result = {
                'session_id': row_dict['session_id'],
                'cascade_id': row_dict.get('cascade_id'),
                'phase': row_dict['phase'],
                'round': row_dict.get('round', 1),
                'timestamp': row_dict['timestamp'],
                'vectors': vectors,
                'metadata': json.loads(row_dict['reflex_data']) if row_dict.get('reflex_data') else {},
                'reasoning': row_dict.get('reasoning'),
                'evidence': row_dict.get('evidence')
            }
            results.append(result)
        
        return results
    
    def store_epistemic_delta(self, cascade_id: str, delta: Dict[str, float]):
        """
        Store epistemic delta (PREFLIGHT vs POSTFLIGHT) for calibration tracking
        
        Args:
            cascade_id: Cascade identifier
            delta: Dictionary of epistemic changes (e.g., {'know': +0.15, 'uncertainty': -0.20})
        """
        cursor = self.conn.cursor()
        
        # Store as JSON in cascade metadata
        cursor.execute("""
            UPDATE cascades
            SET epistemic_delta = ?
            WHERE cascade_id = ?
        """, (json.dumps(delta), cascade_id))
        
        self.conn.commit()
    
    def get_last_session_by_ai(self, ai_id: str) -> Optional[Dict]:
        """Get most recent session for an AI agent"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM sessions 
            WHERE ai_id = ? 
            ORDER BY start_time DESC 
            LIMIT 1
        """, (ai_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_session_summary(self, session_id: str, detail_level: str = "summary") -> Optional[Dict]:
        """
        Generate comprehensive session summary for resume/handoff
        
        Args:
            session_id: Session to summarize
            detail_level: 'summary', 'detailed', or 'full'
        
        Returns:
            Dictionary with session metadata, epistemic delta, accomplishments, etc.
        """
        cursor = self.conn.cursor()
        
        # Get session metadata
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Get cascades
        cascades = self.get_session_cascades(session_id)
        
        # Get PREFLIGHT/POSTFLIGHT from unified reflexes table instead of legacy cascade_metadata
        cursor.execute("""
            SELECT phase, json_extract(reflex_data, '$.vectors'), cascade_id, timestamp
            FROM reflexes
            WHERE session_id = ?
            AND phase IN ('PREFLIGHT', 'POSTFLIGHT')
            ORDER BY timestamp
        """, (session_id,))

        assessments = {}
        cascade_tasks = {}
        for row in cursor.fetchall():
            phase, vectors_json, cascade_id, timestamp = row
            if vectors_json:
                # Convert phase to the expected key format
                key = f"{phase.lower()}_vectors"
                assessments[key] = json.loads(vectors_json)
                # We don't have the task from reflexes, so we'll get it from cascades
                cascade_cursor = self.conn.cursor()
                cascade_cursor.execute("SELECT task FROM cascades WHERE cascade_id = ?", (cascade_id,))
                cascade_row = cascade_cursor.fetchone()
                if cascade_row:
                    cascade_tasks[cascade_id] = cascade_row[0]
        
        # Get investigation tools used (if detailed)
        tools_used = []
        if detail_level in ['detailed', 'full']:
            cursor.execute("""
                SELECT tool_name, COUNT(*) as count
                FROM investigation_tools
                WHERE cascade_id IN (
                    SELECT cascade_id FROM cascades WHERE session_id = ?
                )
                GROUP BY tool_name
                ORDER BY count DESC
                LIMIT 10
            """, (session_id,))
            tools_used = [{"tool": row[0], "count": row[1]} for row in cursor.fetchall()]
        
        # Calculate epistemic delta
        delta = None
        if 'preflight_vectors' in assessments and 'postflight_vectors' in assessments:
            pre = assessments['preflight_vectors']
            post = assessments['postflight_vectors']
            delta = {key: post.get(key, 0.5) - pre.get(key, 0.5) for key in post}
        
        return {
            'session_id': session_id,
            'ai_id': session['ai_id'],
            'start_time': session['start_time'],
            'end_time': session.get('end_time'),
            'total_cascades': len(cascades),
            'cascades': cascades if detail_level == 'full' else [c['task'] for c in cascades],
            'preflight': assessments.get('preflight_vectors'),
            'postflight': assessments.get('postflight_vectors'),
            'epistemic_delta': delta,
            'tools_used': tools_used,
            'avg_confidence': session.get('avg_confidence')
        }
    
    def get_git_checkpoint(self, session_id: str, phase: Optional[str] = None) -> Optional[Dict]:
        """
        Retrieve checkpoint from git notes with SQLite fallback (Phase 2).
        
        Priority:
        1. Try git notes first (via GitEnhancedReflexLogger)
        2. Fall back to SQLite reflexes if git unavailable
        
        Args:
            session_id: Session identifier
            phase: Optional phase filter (PREFLIGHT, CHECK, POSTFLIGHT)
        
        Returns:
            Checkpoint dict or None if not found
        """
        try:
            from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
            
            git_logger = GitEnhancedReflexLogger(session_id=session_id, enable_git_notes=True)
            
            if git_logger.git_available:
                checkpoint = git_logger.get_last_checkpoint(phase=phase)
                if checkpoint:
                    logger.debug(f"✅ Loaded git checkpoint for session {session_id}")
                    return checkpoint
        except Exception as e:
            logger.debug(f"Git checkpoint retrieval failed, using SQLite fallback: {e}")
        
        # Fallback to SQLite reflexes
        return self._get_checkpoint_from_reflexes(session_id, phase)

    def list_git_checkpoints(self, session_id: str, limit: int = 10, phase: Optional[str] = None) -> List[Dict]:
        """
        List all checkpoints for session from git notes (Phase 2).
        
        Args:
            session_id: Session identifier
            limit: Maximum number of checkpoints to return
            phase: Optional phase filter
        
        Returns:
            List of checkpoint dicts
        """
        try:
            from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
            
            git_logger = GitEnhancedReflexLogger(session_id=session_id, enable_git_notes=True)
            
            if git_logger.git_available:
                checkpoints = git_logger.list_checkpoints(limit=limit, phase=phase)
                logger.debug(f"✅ Listed {len(checkpoints)} git checkpoints for session {session_id}")
                return checkpoints
        except Exception as e:
            logger.warning(f"Git checkpoint listing failed: {e}")
        
        # Fallback: return empty list (SQLite doesn't have checkpoint history in same format)
        return []

    def get_checkpoint_diff(self, session_id: str, threshold: float = 0.15) -> Dict:
        """
        Calculate vector differences between current state and last checkpoint (Phase 2).
        
        Args:
            session_id: Session identifier
            threshold: Significance threshold for reporting changes
        
        Returns:
            Dict with vector diffs and significant changes
        """
        from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
        
        git_logger = GitEnhancedReflexLogger(session_id=session_id, enable_git_notes=True)
        
        last_checkpoint = git_logger.get_last_checkpoint()
        if not last_checkpoint:
            return {"error": "No checkpoint found for comparison"}
        
        # Get current state from latest assessment
        current_vectors = self._get_latest_vectors(session_id)
        
        if not current_vectors:
            return {"error": "No current state found"}
        
        # Calculate diffs
        diffs = {}
        significant_changes = []
        
        checkpoint_vectors = last_checkpoint.get('vectors', {})
        
        for key in current_vectors.keys():
            old_val = checkpoint_vectors.get(key, 0.5)
            new_val = current_vectors[key]
            diff = new_val - old_val
            
            diffs[key] = {
                'old': old_val,
                'new': new_val,
                'diff': diff,
                'abs_diff': abs(diff)
            }
            
            if abs(diff) >= threshold:
                significant_changes.append({
                    'vector': key,
                    'change': diff,
                    'direction': 'increased' if diff > 0 else 'decreased'
                })
        
        return {
            'checkpoint_id': last_checkpoint.get('checkpoint_id'),
            'checkpoint_phase': last_checkpoint.get('phase'),
            'checkpoint_timestamp': last_checkpoint.get('timestamp'),
            'diffs': diffs,
            'significant_changes': significant_changes,
            'threshold': threshold
        }

    def _get_checkpoint_from_reflexes(self, session_id: str, phase: Optional[str] = None) -> Optional[Dict]:
        """SQLite fallback for checkpoint retrieval (Phase 2)"""
        cursor = self.conn.cursor()
        
        # Try preflight_assessments first (most common)
        query = """
            SELECT 
                assessment_id,
                'preflight' as phase,
                vectors_json,
                assessed_at as created_at
            FROM preflight_assessments
            WHERE session_id = ?
        """
        params = [session_id]
        
        if phase and phase.lower() == 'postflight':
            # Use postflight_assessments instead
            query = """
                SELECT 
                    assessment_id,
                    'postflight' as phase,
                    vectors_json,
                    assessed_at as created_at
                FROM postflight_assessments
                WHERE session_id = ?
            """
        
        query += " ORDER BY assessed_at DESC LIMIT 1"
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        if result:
            return {
                "checkpoint_id": result['assessment_id'],
                "vectors": json.loads(result['vectors_json']) if result['vectors_json'] else {},
                "phase": result['phase'],
                "timestamp": result['created_at'],
                "round": 0,  # SQLite doesn't track rounds
                "source": "sqlite_fallback",
                "token_count": None  # Not tracked in SQLite
            }
        
        return None

    def _get_latest_vectors(self, session_id: str) -> Optional[Dict[str, float]]:
        """Get latest epistemic vectors for session (Phase 2)"""
        cursor = self.conn.cursor()
        
        # Try preflight first, then postflight
        cursor.execute("""
            SELECT vectors_json, assessed_at
            FROM preflight_assessments
            WHERE session_id = ?
            ORDER BY assessed_at DESC
            LIMIT 1
        """, (session_id,))
        
        result = cursor.fetchone()
        
        if result and result['vectors_json']:
            return json.loads(result['vectors_json'])
        
        # Try postflight if preflight not found
        cursor.execute("""
            SELECT vectors_json, assessed_at
            FROM postflight_assessments
            WHERE session_id = ?
            ORDER BY assessed_at DESC
            LIMIT 1
        """, (session_id,))
        
        result = cursor.fetchone()
        
        if result and result['vectors_json']:
            return json.loads(result['vectors_json'])
        
        return None
    
    def store_vectors(self, session_id: str, phase: str, vectors: Dict[str, float], cascade_id: Optional[str] = None, round_num: int = 1, metadata: Optional[Dict] = None, reasoning: Optional[str] = None):
        """
        Store epistemic vectors in the reflexes table

        Args:
            session_id: Session identifier
            phase: Current phase (PREFLIGHT, CHECK, ACT, POSTFLIGHT)
            vectors: Dictionary of 13 epistemic vectors
            cascade_id: Optional cascade identifier
            round_num: Current round number
        """
        cursor = self.conn.cursor()

        # Extract the 13 vectors, providing default values if not present
        vector_names = [
            'engagement', 'know', 'do', 'context',
            'clarity', 'coherence', 'signal', 'density',
            'state', 'change', 'completion', 'impact', 'uncertainty'
        ]

        vector_values = []
        for name in vector_names:
            value = vectors.get(name, 0.5)  # Default to 0.5 if not provided
            vector_values.append(value if isinstance(value, (int, float)) else 0.5)

        # Create a reflex data entry with optional metadata
        reflex_data = {
            'session_id': session_id,
            'phase': phase,
            'round': round_num,
            'vectors': vectors,
            'timestamp': time.time()
        }
        
        # Merge in any additional metadata if provided
        if metadata:
            reflex_data.update(metadata)

        cursor.execute("""
            INSERT INTO reflexes (
                session_id, cascade_id, phase, round, timestamp,
                engagement, know, do, context,
                clarity, coherence, signal, density,
                state, change, completion, impact, uncertainty,
                reflex_data, reasoning
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, cascade_id, phase, round_num, time.time(),
            *vector_values,  # Unpack the 13 vector values
            json.dumps(reflex_data),
            reasoning
        ))

        self.conn.commit()

    def get_latest_vectors(self, session_id: str, phase: Optional[str] = None) -> Optional[Dict]:
        """
        Get the latest epistemic vectors for a session from the reflexes table

        Args:
            session_id: Session identifier
            phase: Optional phase filter

        Returns:
            Dictionary with vectors, metadata, timestamp, etc. or None if not found
        """
        cursor = self.conn.cursor()

        query = """
            SELECT * FROM reflexes
            WHERE session_id = ?
        """
        params = [session_id]

        if phase:
            query += " AND phase = ?"
            params.append(phase)

        query += " ORDER BY timestamp DESC LIMIT 1"

        cursor.execute(query, params)
        result = cursor.fetchone()

        if result:
            row_dict = dict(result)
            
            # Extract the 13 vector values from the result
            vectors = {}
            for vector_name in ['engagement', 'know', 'do', 'context',
                               'clarity', 'coherence', 'signal', 'density',
                               'state', 'change', 'completion', 'impact', 'uncertainty']:
                if vector_name in row_dict:
                    value = row_dict[vector_name]
                    if value is not None:
                        vectors[vector_name] = float(value)
            
            # Return full data structure
            return {
                'session_id': row_dict['session_id'],
                'cascade_id': row_dict.get('cascade_id'),
                'phase': row_dict['phase'],
                'round': row_dict.get('round', 1),
                'timestamp': row_dict['timestamp'],
                'vectors': vectors,
                'metadata': json.loads(row_dict['reflex_data']) if row_dict.get('reflex_data') else {},
                'reasoning': row_dict.get('reasoning'),
                'evidence': row_dict.get('evidence')
            }

        return None

    def get_findings_by_file(self, filename: str, session_id: Optional[str] = None) -> List[Dict]:
        """Get all findings mentioning a specific file"""
        import json
        
        cursor = self.conn.cursor()
        
        if session_id:
            query = "SELECT findings, session_id, check_id FROM check_phase_assessments WHERE session_id = ? AND findings IS NOT NULL"
            cursor.execute(query, (session_id,))
        else:
            query = "SELECT findings, session_id, check_id FROM check_phase_assessments WHERE findings IS NOT NULL"
            cursor.execute(query)
        
        results = []
        for row in cursor.fetchall():
            findings_json = row[0]
            if not findings_json:
                continue
                
            findings = json.loads(findings_json)
            for finding in findings:
                # Backward compatibility: handle both string and structured findings
                if isinstance(finding, str):
                    # Old format: plain string, check if filename appears in text
                    if filename in finding:
                        results.append({
                            "finding": {"text": finding, "refs": {"files": [], "docs": [], "urls": []}},
                            "session_id": row[1],
                            "check_id": row[2]
                        })
                else:
                    # New format: structured with refs
                    for ref in finding.get("refs", {}).get("files", []):
                        if filename in ref.get("file", ""):
                            results.append({
                                "finding": finding,
                                "session_id": row[1],
                                "check_id": row[2]
                            })
                            break
        
        return results
    
    def get_findings_by_commit(self, commit_sha: str) -> List[Dict]:
        """Get all findings from a specific git commit"""
        import json
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT findings, session_id, check_id FROM check_phase_assessments WHERE findings IS NOT NULL")
        
        results = []
        for row in cursor.fetchall():
            findings_json = row[0]
            if not findings_json:
                continue
                
            findings = json.loads(findings_json)
            for finding in findings:
                if finding.get("commit", "").startswith(commit_sha[:7]):  # Match short SHA
                    results.append({
                        "finding": finding,
                        "session_id": row[1],
                        "check_id": row[2]
                    })
        
        return results

    # =========================================================================
    # Goal and Subtask Management (for decision quality + continuity + audit)
    # =========================================================================

    def create_goal(self, session_id: str, objective: str, scope_breadth: float = None,
                   scope_duration: float = None, scope_coordination: float = None) -> str:
        """Create a new goal for this session

        Args:
            session_id: Session UUID
            objective: What are you trying to accomplish?
            scope_breadth: 0.0-1.0 (0=single file, 1=entire codebase)
            scope_duration: 0.0-1.0 (0=minutes, 1=months)
            scope_coordination: 0.0-1.0 (0=solo, 1=heavy multi-agent)

        Returns:
            goal_id (UUID string)
        """
        goal_id = str(uuid.uuid4())
        cursor = self.conn.cursor()

        # Build scope JSON from individual vectors
        scope_data = {
            'breadth': scope_breadth,
            'duration': scope_duration,
            'coordination': scope_coordination
        }

        cursor.execute("""
            INSERT INTO goals (id, session_id, objective, scope, status, created_timestamp, is_completed, goal_data)
            VALUES (?, ?, ?, ?, 'in_progress', ?, 0, ?)
        """, (goal_id, session_id, objective, json.dumps(scope_data), time.time(), json.dumps({})))

        self.conn.commit()
        return goal_id

    def create_subtask(self, goal_id: str, description: str, importance: str = 'medium') -> str:
        """Create a subtask within a goal

        Args:
            goal_id: Parent goal UUID
            description: What are you investigating/implementing?
            importance: 'critical' | 'high' | 'medium' | 'low'

        Returns:
            subtask_id (UUID string)
        """
        subtask_id = str(uuid.uuid4())
        cursor = self.conn.cursor()

        # Build subtask_data JSON with investigation tracking
        subtask_data = {
            'findings': [],
            'unknowns': [],
            'dead_ends': []
        }

        cursor.execute("""
            INSERT INTO subtasks (id, goal_id, description, epistemic_importance, status, created_timestamp, subtask_data)
            VALUES (?, ?, ?, ?, 'pending', ?, ?)
        """, (subtask_id, goal_id, description, importance, time.time(), json.dumps(subtask_data)))

        self.conn.commit()
        return subtask_id

    def update_subtask_findings(self, subtask_id: str, findings: List[str]):
        """Update findings for a subtask

        Args:
            subtask_id: Subtask UUID
            findings: List of finding strings
        """
        cursor = self.conn.cursor()
        
        # Get current subtask_data
        cursor.execute("SELECT subtask_data FROM subtasks WHERE id = ?", (subtask_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Subtask {subtask_id} not found")
        
        subtask_data = json.loads(row[0])
        subtask_data['findings'] = findings
        
        cursor.execute("""
            UPDATE subtasks SET subtask_data = ? WHERE id = ?
        """, (json.dumps(subtask_data), subtask_id))

        self.conn.commit()

    def update_subtask_unknowns(self, subtask_id: str, unknowns: List[str]):
        """Update unknowns for a subtask

        Args:
            subtask_id: Subtask UUID
            unknowns: List of unknown strings
        """
        cursor = self.conn.cursor()
        
        # Get current subtask_data
        cursor.execute("SELECT subtask_data FROM subtasks WHERE id = ?", (subtask_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Subtask {subtask_id} not found")
        
        subtask_data = json.loads(row[0])
        subtask_data['unknowns'] = unknowns
        
        cursor.execute("""
            UPDATE subtasks SET subtask_data = ? WHERE id = ?
        """, (json.dumps(subtask_data), subtask_id))

        self.conn.commit()

    def update_subtask_dead_ends(self, subtask_id: str, dead_ends: List[str]):
        """Update dead ends for a subtask

        Args:
            subtask_id: Subtask UUID
            dead_ends: List of dead end strings (e.g., "Attempted X - blocked by Y")
        """
        cursor = self.conn.cursor()
        
        # Get current subtask_data
        cursor.execute("SELECT subtask_data FROM subtasks WHERE id = ?", (subtask_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Subtask {subtask_id} not found")
        
        subtask_data = json.loads(row[0])
        subtask_data['dead_ends'] = dead_ends
        
        cursor.execute("""
            UPDATE subtasks SET subtask_data = ? WHERE id = ?
        """, (json.dumps(subtask_data), subtask_id))

        self.conn.commit()

    def complete_subtask(self, subtask_id: str, evidence: str):
        """Mark subtask as completed with evidence

        Args:
            subtask_id: Subtask UUID
            evidence: Evidence of completion (e.g., "Documented in design doc", "PR merged")
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            UPDATE subtasks 
            SET status = 'completed', 
                completion_evidence = ?,
                completed_timestamp = ?
            WHERE id = ?
        """, (evidence, time.time(), subtask_id))
        
        self.conn.commit()

    def get_all_sessions(self, ai_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """List all sessions, optionally filtered by ai_id

        Args:
            ai_id: Optional AI identifier to filter by
            limit: Maximum number of sessions to return (default 50)

        Returns:
            List of session dictionaries
        """
        cursor = self.conn.cursor()
        
        if ai_id:
            cursor.execute("""
                SELECT * FROM sessions 
                WHERE ai_id = ? 
                ORDER BY start_time DESC 
                LIMIT ?
            """, (ai_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM sessions 
                ORDER BY start_time DESC 
                LIMIT ?
            """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]

    def get_goal_tree(self, session_id: str) -> List[Dict]:
        """Get complete goal tree for a session

        Returns list of goals with nested subtasks

        Args:
            session_id: Session UUID

        Returns:
            List of goal dicts, each with 'subtasks' list
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT id, objective, status, scope, estimated_complexity
            FROM goals WHERE session_id = ? ORDER BY created_timestamp
        """, (session_id,))

        goals = []
        for row in cursor.fetchall():
            goal_id = row[0]
            scope_data = json.loads(row[3]) if row[3] else {}

            # Get subtasks for this goal
            cursor.execute("""
                SELECT id, description, epistemic_importance, status, subtask_data
                FROM subtasks WHERE goal_id = ? ORDER BY created_timestamp
            """, (goal_id,))

            subtasks = []
            for sub_row in cursor.fetchall():
                subtask_data = json.loads(sub_row[4]) if sub_row[4] else {}
                subtasks.append({
                    'subtask_id': sub_row[0],
                    'description': sub_row[1],
                    'importance': sub_row[2],
                    'status': sub_row[3],
                    'findings': subtask_data.get('findings', []),
                    'unknowns': subtask_data.get('unknowns', []),
                    'dead_ends': subtask_data.get('dead_ends', [])
                })

            goals.append({
                'goal_id': goal_id,
                'objective': row[1],
                'status': row[2],
                'scope_breadth': scope_data.get('breadth'),
                'scope_duration': scope_data.get('duration'),
                'scope_coordination': scope_data.get('coordination'),
                'estimated_complexity': row[4],
                'subtasks': subtasks
            })

        return goals

    def query_unknowns_summary(self, session_id: str) -> Dict:
        """Get summary of all unknowns in a session (for CHECK decisions)

        Args:
            session_id: Session UUID

        Returns:
            Dict with total_unknowns count and breakdown by goal
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT g.id, g.objective, s.id, s.subtask_data
            FROM goals g
            LEFT JOIN subtasks s ON g.id = s.goal_id
            WHERE g.session_id = ? AND g.status = 'in_progress'
        """, (session_id,))

        total_unknowns = 0
        unknowns_by_goal = {}

        for row in cursor.fetchall():
            goal_id, objective, subtask_id, subtask_data_json = row
            
            if goal_id not in unknowns_by_goal:
                unknowns_by_goal[goal_id] = {
                    'goal_id': goal_id,
                    'objective': objective,
                    'unknown_count': 0
                }
            
            if subtask_data_json:
                subtask_data = json.loads(subtask_data_json)
                unknowns = subtask_data.get('unknowns', [])
                unknowns_count = len([u for u in unknowns if u])  # Count non-empty unknowns
                unknowns_by_goal[goal_id]['unknown_count'] += unknowns_count
                total_unknowns += unknowns_count

        return {
            'total_unknowns': total_unknowns,
            'unknowns_by_goal': list(unknowns_by_goal.values())
        }

    # ========== Investigation Branches (Epistemic Auto-Merge) ==========

    def create_branch(self, session_id: str, branch_name: str, investigation_path: str,
                     git_branch_name: str, preflight_vectors: Dict) -> str:
        """Create a new investigation branch

        Args:
            session_id: Session UUID
            branch_name: Human-readable branch name
            investigation_path: What is being investigated (e.g., 'oauth2')
            git_branch_name: Git branch name
            preflight_vectors: Epistemic vectors at branch start

        Returns:
            Branch ID
        """
        import uuid
        import time
        branch_id = str(uuid.uuid4())
        now = time.time()

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO investigation_branches
            (id, session_id, branch_name, investigation_path, git_branch_name,
             preflight_vectors, created_timestamp, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
        """, (branch_id, session_id, branch_name, investigation_path, git_branch_name,
              json.dumps(preflight_vectors), now))

        self.conn.commit()
        return branch_id

    def checkpoint_branch(self, branch_id: str, postflight_vectors: Dict,
                         tokens_spent: int, time_spent_minutes: int) -> bool:
        """Checkpoint a branch after investigation

        Args:
            branch_id: Branch ID
            postflight_vectors: Epistemic vectors after investigation
            tokens_spent: Tokens used in investigation
            time_spent_minutes: Time spent in investigation

        Returns:
            Success boolean
        """
        import time
        now = time.time()

        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE investigation_branches
            SET postflight_vectors = ?, tokens_spent = ?, time_spent_minutes = ?,
                checkpoint_timestamp = ?
            WHERE id = ?
        """, (json.dumps(postflight_vectors), tokens_spent, time_spent_minutes, now, branch_id))

        self.conn.commit()
        return True

    def calculate_branch_merge_score(self, branch_id: str) -> Dict:
        """Calculate epistemic merge score for a branch

        Score = (learning_delta × quality × confidence) / cost_penalty
        Where: confidence = 1 - uncertainty (uncertainty is a DAMPENER)

        Returns:
            Dict with merge_score, quality, and rationale
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT preflight_vectors, postflight_vectors, tokens_spent
            FROM investigation_branches WHERE id = ?
        """, (branch_id,))

        row = cursor.fetchone()
        if not row or not row[1]:  # No postflight data yet
            return {"merge_score": 0, "quality": 0, "rationale": "No postflight data"}

        preflight = json.loads(row[0])
        postflight = json.loads(row[1])
        tokens_spent = row[2] or 0

        # 1. Calculate learning delta
        key_vectors = ['know', 'do', 'context', 'clarity', 'signal']
        learning_deltas = []
        for key in key_vectors:
            pre_val = preflight.get(key, 0.5)
            post_val = postflight.get(key, 0.5)
            learning_deltas.append(post_val - pre_val)
        learning_delta = sum(learning_deltas) / len(key_vectors)

        # 2. Calculate quality
        coherence = postflight.get('coherence', 0.5)
        clarity = postflight.get('clarity', 0.5)
        density = postflight.get('density', 0.5)
        quality = (coherence + clarity + (1 - density)) / 3

        # 3. Calculate confidence (1 - uncertainty, CRITICAL DAMPENER)
        uncertainty = postflight.get('uncertainty', 0.5)
        confidence = 1.0 - uncertainty

        # 4. Calculate cost penalty
        cost_penalty = max(1.0, tokens_spent / 2000.0)

        # 5. Calculate final merge score
        merge_score = (learning_delta * quality * confidence) / cost_penalty

        return {
            "merge_score": round(merge_score, 4),
            "quality": round(quality, 4),
            "learning_delta": round(learning_delta, 4),
            "confidence": round(confidence, 4),
            "uncertainty_dampener": round(uncertainty, 4)
        }

    def merge_branches(self, session_id: str, investigation_round: int = 1) -> Dict:
        """Auto-merge best branch based on epistemic scores

        Returns:
            Dict with winning_branch_id, merge_decision_id, rationale
        """
        import uuid
        import time

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, branch_name, investigation_path
            FROM investigation_branches
            WHERE session_id = ? AND status = 'active'
        """, (session_id,))

        branches = cursor.fetchall()
        if not branches:
            return {"error": "No active branches to merge"}

        # Calculate scores for all branches
        branch_scores = []
        for branch_id, branch_name, investigation_path in branches:
            score_data = self.calculate_branch_merge_score(branch_id)
            if score_data.get('merge_score', 0) > 0:
                branch_scores.append({
                    'branch_id': branch_id,
                    'branch_name': branch_name,
                    'investigation_path': investigation_path,
                    'score': score_data['merge_score'],
                    'quality': score_data['quality'],
                    'confidence': score_data['confidence'],
                    'uncertainty': score_data['uncertainty_dampener']
                })

        if not branch_scores:
            return {"error": "No branches with valid epistemic data"}

        # Select winner (highest score)
        winner = max(branch_scores, key=lambda x: x['score'])

        # Mark winner in database
        cursor.execute("""
            UPDATE investigation_branches
            SET is_winner = TRUE, status = 'merged', merged_timestamp = ?
            WHERE id = ?
        """, (time.time(), winner['branch_id']))

        # Record merge decision
        decision_id = str(uuid.uuid4())
        other_branches = [b['branch_name'] for b in branch_scores if b['branch_id'] != winner['branch_id']]
        rationale = (
            f"Selected {winner['investigation_path']}: "
            f"score={winner['score']:.4f}, "
            f"quality={winner['quality']:.4f}, "
            f"confidence={winner['confidence']:.4f} "
            f"({len(other_branches)} other paths evaluated)"
        )

        cursor.execute("""
            INSERT INTO merge_decisions
            (id, session_id, investigation_round, winning_branch_id, winning_branch_name,
             winning_score, other_branches, decision_rationale, auto_merged, created_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, TRUE, ?)
        """, (decision_id, session_id, investigation_round, winner['branch_id'],
              winner['branch_name'], winner['score'], json.dumps(other_branches),
              rationale, time.time()))

        self.conn.commit()

        return {
            "success": True,
            "winning_branch_id": winner['branch_id'],
            "winning_branch_name": winner['branch_name'],
            "winning_score": round(winner['score'], 4),
            "merge_decision_id": decision_id,
            "other_branches": other_branches,
            "rationale": rationale
        }

    def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        repos: Optional[List[str]] = None
    ) -> str:
        """
        Create a new project for multi-repo/multi-session tracking.
        
        Args:
            name: Project name (e.g., "Empirica Core")
            description: Project description
            repos: List of repository names (e.g., ["empirica", "empirica-dev"])
            
        Returns:
            project_id: UUID string
        """
        project_id = str(uuid.uuid4())
        
        project_data = {
            "name": name,
            "description": description,
            "repos": repos or []
        }
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO projects (
                id, name, description, repos, created_timestamp, 
                last_activity_timestamp, project_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            project_id, name, description, json.dumps(repos or []),
            time.time(), time.time(), json.dumps(project_data)
        ))
        
        self.conn.commit()
        logger.info(f"📁 Project created: {name} ({project_id[:8]}...)")
        
        return project_id
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project data"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def link_session_to_project(self, session_id: str, project_id: str):
        """Link a session to a project"""
        self._validate_session_id(session_id)
        
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE sessions SET project_id = ? WHERE session_id = ?
        """, (project_id, session_id))
        
        # Update project activity timestamp and session count
        cursor.execute("""
            UPDATE projects 
            SET last_activity_timestamp = ?,
                total_sessions = total_sessions + 1
            WHERE id = ?
        """, (time.time(), project_id))
        
        self.conn.commit()
        logger.info(f"🔗 Session {session_id[:8]}... linked to project {project_id[:8]}...")
    
    def get_project_sessions(self, project_id: str) -> List[Dict]:
        """Get all sessions for a project"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM sessions WHERE project_id = ? ORDER BY start_time DESC
        """, (project_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def aggregate_project_learning_deltas(self, project_id: str) -> Dict[str, float]:
        """
        Compute total epistemic learning across all project sessions.
        
        Queries PREFLIGHT and POSTFLIGHT reflexes for each session,
        computes deltas, and aggregates.
        """
        cursor = self.conn.cursor()
        
        # Get all sessions for project
        cursor.execute("""
            SELECT session_id FROM sessions WHERE project_id = ? ORDER BY start_time
        """, (project_id,))
        session_ids = [row[0] for row in cursor.fetchall()]
        
        if not session_ids:
            return {}
        
        # Aggregate deltas across all sessions
        total_deltas = {
            'engagement': 0.0, 'know': 0.0, 'do': 0.0, 'context': 0.0, 'clarity': 0.0,
            'coherence': 0.0, 'signal': 0.0, 'density': 0.0, 'state': 0.0,
            'change': 0.0, 'completion': 0.0, 'impact': 0.0, 'uncertainty': 0.0
        }
        
        for session_id in session_ids:
            # Get PREFLIGHT vectors
            cursor.execute("""
                SELECT engagement, know, do, context, clarity, coherence, signal, density,
                       state, change, completion, impact, uncertainty
                FROM reflexes
                WHERE session_id = ? AND phase = 'PREFLIGHT'
                ORDER BY timestamp
                LIMIT 1
            """, (session_id,))
            preflight = cursor.fetchone()
            
            # Get POSTFLIGHT vectors
            cursor.execute("""
                SELECT engagement, know, do, context, clarity, coherence, signal, density,
                       state, change, completion, impact, uncertainty
                FROM reflexes
                WHERE session_id = ? AND phase = 'POSTFLIGHT'
                ORDER BY timestamp DESC
                LIMIT 1
            """, (session_id,))
            postflight = cursor.fetchone()
            
            if preflight and postflight:
                # Compute deltas and add to totals
                for i, vector in enumerate(['engagement', 'know', 'do', 'context', 'clarity',
                                            'coherence', 'signal', 'density', 'state', 'change',
                                            'completion', 'impact', 'uncertainty']):
                    if preflight[i] is not None and postflight[i] is not None:
                        total_deltas[vector] += (postflight[i] - preflight[i])
        
        return total_deltas
    
    def create_project_handoff(
        self,
        project_id: str,
        project_summary: str,
        key_decisions: Optional[List[str]] = None,
        patterns_discovered: Optional[List[str]] = None,
        remaining_work: Optional[List[str]] = None
    ) -> str:
        """
        Create project-level handoff report by aggregating session handoffs.
        
        Args:
            project_id: Project identifier
            project_summary: High-level summary of project state
            key_decisions: List of major decisions made
            patterns_discovered: Reusable patterns found
            remaining_work: Outstanding tasks
            
        Returns:
            handoff_id: UUID string
        """
        handoff_id = str(uuid.uuid4())
        
        # Get all sessions for project
        sessions = self.get_project_sessions(project_id)
        
        # Aggregate session handoffs
        sessions_included = []
        for session in sessions:
            # Query session handoff from git notes or database
            # For now, just include session metadata
            sessions_included.append({
                "session_id": session['session_id'],
                "start_time": session['start_time'],
                "ai_id": session['ai_id']
            })
        
        # Compute total learning deltas
        total_deltas = self.aggregate_project_learning_deltas(project_id)
        
        # Get recent mistakes from project
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT mistake, cost_estimate, root_cause_vector, prevention
            FROM mistakes_made m
            JOIN sessions s ON m.session_id = s.session_id
            WHERE s.project_id = ?
            ORDER BY m.created_timestamp DESC
            LIMIT 10
        """, (project_id,))
        mistakes_summary = [dict(row) for row in cursor.fetchall()]
        
        # Get repos touched
        project = self.get_project(project_id)
        repos_touched = json.loads(project['repos']) if project and project['repos'] else []
        
        # Build handoff data
        handoff_data = {
            "project_summary": project_summary,
            "sessions_included": sessions_included,
            "total_learning_deltas": total_deltas,
            "key_decisions": key_decisions or [],
            "patterns_discovered": patterns_discovered or [],
            "mistakes_summary": mistakes_summary,
            "remaining_work": remaining_work or [],
            "repos_touched": repos_touched,
            "next_session_bootstrap": {
                "suggested_focus": remaining_work[0] if remaining_work else "Continue project work",
                "context_breadcrumbs": key_decisions[-5:] if key_decisions else []
            }
        }
        
        cursor.execute("""
            INSERT INTO project_handoffs (
                id, project_id, created_timestamp, project_summary,
                sessions_included, total_learning_deltas, key_decisions,
                patterns_discovered, mistakes_summary, remaining_work,
                repos_touched, next_session_bootstrap, handoff_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            handoff_id, project_id, time.time(), project_summary,
            json.dumps(sessions_included), json.dumps(total_deltas),
            json.dumps(key_decisions or []), json.dumps(patterns_discovered or []),
            json.dumps(mistakes_summary), json.dumps(remaining_work or []),
            json.dumps(repos_touched), json.dumps(handoff_data["next_session_bootstrap"]),
            json.dumps(handoff_data)
        ))
        
        self.conn.commit()
        logger.info(f"📋 Project handoff created: {handoff_id[:8]}...")
        
        return handoff_id
    
    def get_latest_project_handoff(self, project_id: str) -> Optional[Dict]:
        """Get the most recent project handoff"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM project_handoffs 
            WHERE project_id = ? 
            ORDER BY created_timestamp DESC 
            LIMIT 1
        """, (project_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def bootstrap_project_breadcrumbs(self, project_id: str, mode: str = "session_start", project_root: str = None) -> Dict:
        """
        Generate epistemic breadcrumbs for starting a new session on existing project.

        Args:
            project_id: Project identifier
            mode: "session_start" (fast, recent items) or "live" (complete, all items)
            project_root: Optional path to project root (defaults to cwd)

        Returns quick context: findings, unknowns, dead_ends, mistakes, decisions, incomplete work, suggested skills.
        """
        import os
        import yaml

        if project_root is None:
            project_root = os.getcwd()

        project = self.get_project(project_id)
        if not project:
            return {"error": "Project not found"}
        
        # Get latest handoff
        latest_handoff = self.get_latest_project_handoff(project_id)
        
        if mode == "session_start":
            # FAST: Recent items only for quick bootstrap
            findings = self.get_project_findings(project_id, limit=10)
            unknowns = self.get_project_unknowns(project_id, resolved=False)  # Only unresolved
            dead_ends = self.get_project_dead_ends(project_id, limit=5)
            
            # Get recent mistakes (top 5)
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT mistake, prevention, cost_estimate, root_cause_vector
                FROM mistakes_made m
                JOIN sessions s ON m.session_id = s.session_id
                WHERE s.project_id = ?
                ORDER BY m.created_timestamp DESC
                LIMIT 5
            """, (project_id,))
            recent_mistakes = [dict(row) for row in cursor.fetchall()]
            
            reference_docs = self.get_project_reference_docs(project_id)
            
        elif mode == "live":
            # COMPLETE: All items for full context
            findings = self.get_project_findings(project_id)
            unknowns = self.get_project_unknowns(project_id)  # All unknowns
            dead_ends = self.get_project_dead_ends(project_id)
            
            # Get ALL mistakes
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT mistake, prevention, cost_estimate, root_cause_vector
                FROM mistakes_made m
                JOIN sessions s ON m.session_id = s.session_id
                WHERE s.project_id = ?
                ORDER BY m.created_timestamp DESC
            """, (project_id,))
            recent_mistakes = [dict(row) for row in cursor.fetchall()]
            
            reference_docs = self.get_project_reference_docs(project_id)
        
        else:
            return {"error": f"Invalid mode: {mode}"}
        
        # Get incomplete goals
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT g.objective, g.id,
                   (SELECT COUNT(*) FROM subtasks WHERE goal_id = g.id) as total_subtasks,
                   (SELECT COUNT(*) FROM subtasks WHERE goal_id = g.id AND status = 'complete') as completed_subtasks
            FROM goals g
            JOIN sessions s ON g.session_id = s.session_id
            WHERE s.project_id = ? AND g.status != 'complete'
            ORDER BY g.created_timestamp DESC
        """, (project_id,))
        incomplete_goals = [dict(row) for row in cursor.fetchall()]

        # Load available skills from project_skills/*.yaml
        available_skills = []
        skills_dir = os.path.join(project_root, 'project_skills')
        if os.path.exists(skills_dir):
            try:
                for filename in os.listdir(skills_dir):
                    if filename.endswith(('.yaml', '.yml')):
                        skill_path = os.path.join(skills_dir, filename)
                        try:
                            with open(skill_path, 'r', encoding='utf-8') as f:
                                skill = yaml.safe_load(f)
                                if skill:
                                    available_skills.append({
                                        'id': skill.get('id', filename.replace('.yaml', '').replace('.yml', '')),
                                        'title': skill.get('title', filename),
                                        'tags': skill.get('tags', []),
                                        'source': 'local'
                                    })
                        except Exception:
                            pass
            except Exception:
                pass

        # Build breadcrumbs
        handoff_data = json.loads(latest_handoff['handoff_data']) if latest_handoff else {}
        
        breadcrumbs = {
            "project": {
                "name": project['name'],
                "description": project['description'],
                "repos": json.loads(project['repos']) if project['repos'] else [],
                "total_sessions": project['total_sessions'],
                "learning_deltas": json.loads(project['total_epistemic_deltas']) if project.get('total_epistemic_deltas') else {}
            },
            "last_activity": {
                "summary": latest_handoff['project_summary'] if latest_handoff else "No handoff yet",
                "timestamp": latest_handoff['created_timestamp'] if latest_handoff else None,
                "next_focus": handoff_data.get("next_session_bootstrap", {}).get("suggested_focus", "Continue project work")
            },
            "findings": [f['finding'] for f in findings],
            "unknowns": [
                {
                    "unknown": u['unknown'],
                    "is_resolved": bool(u['is_resolved'])
                }
                for u in unknowns
            ],
            "dead_ends": [
                {
                    "approach": d['approach'],
                    "why_failed": d['why_failed']
                }
                for d in dead_ends
            ],
            "mistakes_to_avoid": [
                {
                    "mistake": m['mistake'],
                    "prevention": m['prevention'],
                    "cost": m['cost_estimate'],
                    "root_cause": m['root_cause_vector']
                }
                for m in recent_mistakes
            ],
            "key_decisions": handoff_data.get("key_decisions", [])[-5:] if handoff_data else [],
            "reference_docs": [
                {
                    "path": d['doc_path'],
                    "type": d['doc_type'],
                    "description": d['description']
                }
                for d in reference_docs
            ],
            "incomplete_work": [
                {
                    "goal": g['objective'],
                    "progress": f"{g['completed_subtasks']}/{g['total_subtasks']}"
                }
                for g in incomplete_goals
            ],
            "available_skills": available_skills,
            "mode": mode
        }
        
        return breadcrumbs

    def log_finding(
        self,
        project_id: str,
        session_id: str,
        finding: str,
        goal_id: Optional[str] = None,
        subtask_id: Optional[str] = None
    ) -> str:
        """Log a project finding (what was learned/discovered)"""
        finding_id = str(uuid.uuid4())
        
        finding_data = {
            "finding": finding,
            "goal_id": goal_id,
            "subtask_id": subtask_id
        }
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO project_findings (
                id, project_id, session_id, goal_id, subtask_id,
                finding, created_timestamp, finding_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            finding_id, project_id, session_id, goal_id, subtask_id,
            finding, time.time(), json.dumps(finding_data)
        ))
        
        self.conn.commit()
        logger.info(f"📝 Finding logged: {finding[:50]}...")
        
        return finding_id
    
    def log_unknown(
        self,
        project_id: str,
        session_id: str,
        unknown: str,
        goal_id: Optional[str] = None,
        subtask_id: Optional[str] = None
    ) -> str:
        """Log a project unknown (what's still unclear)"""
        unknown_id = str(uuid.uuid4())
        
        unknown_data = {
            "unknown": unknown,
            "goal_id": goal_id,
            "subtask_id": subtask_id
        }
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO project_unknowns (
                id, project_id, session_id, goal_id, subtask_id,
                unknown, created_timestamp, unknown_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            unknown_id, project_id, session_id, goal_id, subtask_id,
            unknown, time.time(), json.dumps(unknown_data)
        ))
        
        self.conn.commit()
        logger.info(f"❓ Unknown logged: {unknown[:50]}...")
        
        return unknown_id
    
    def resolve_unknown(self, unknown_id: str, resolved_by: str):
        """Mark an unknown as resolved"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE project_unknowns 
            SET is_resolved = TRUE, resolved_by = ?, resolved_timestamp = ?
            WHERE id = ?
        """, (resolved_by, time.time(), unknown_id))
        
        self.conn.commit()
        logger.info(f"✅ Unknown resolved: {unknown_id[:8]}...")
    
    def log_dead_end(
        self,
        project_id: str,
        session_id: str,
        approach: str,
        why_failed: str,
        goal_id: Optional[str] = None,
        subtask_id: Optional[str] = None
    ) -> str:
        """Log a project dead end (what didn't work)"""
        dead_end_id = str(uuid.uuid4())
        
        dead_end_data = {
            "approach": approach,
            "why_failed": why_failed,
            "goal_id": goal_id,
            "subtask_id": subtask_id
        }
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO project_dead_ends (
                id, project_id, session_id, goal_id, subtask_id,
                approach, why_failed, created_timestamp, dead_end_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dead_end_id, project_id, session_id, goal_id, subtask_id,
            approach, why_failed, time.time(), json.dumps(dead_end_data)
        ))
        
        self.conn.commit()
        logger.info(f"💀 Dead end logged: {approach[:50]}...")
        
        return dead_end_id
    
    def add_reference_doc(
        self,
        project_id: str,
        doc_path: str,
        doc_type: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """Add a reference document to project"""
        doc_id = str(uuid.uuid4())
        
        doc_data = {
            "doc_path": doc_path,
            "doc_type": doc_type,
            "description": description
        }
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO project_reference_docs (
                id, project_id, doc_path, doc_type, description,
                created_timestamp, doc_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_id, project_id, doc_path, doc_type, description,
            time.time(), json.dumps(doc_data)
        ))
        
        self.conn.commit()
        logger.info(f"📄 Reference doc added: {doc_path}")
        
        return doc_id
    
    def get_project_findings(self, project_id: str, limit: Optional[int] = None) -> List[Dict]:
        """Get all findings for a project"""
        cursor = self.conn.cursor()
        query = "SELECT * FROM project_findings WHERE project_id = ? ORDER BY created_timestamp DESC"
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query, (project_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_project_unknowns(self, project_id: str, resolved: Optional[bool] = None) -> List[Dict]:
        """Get unknowns for a project (optionally filter by resolved status)"""
        cursor = self.conn.cursor()
        if resolved is None:
            cursor.execute("""
                SELECT * FROM project_unknowns 
                WHERE project_id = ? 
                ORDER BY created_timestamp DESC
            """, (project_id,))
        else:
            cursor.execute("""
                SELECT * FROM project_unknowns 
                WHERE project_id = ? AND is_resolved = ?
                ORDER BY created_timestamp DESC
            """, (project_id, resolved))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_project_dead_ends(self, project_id: str, limit: Optional[int] = None) -> List[Dict]:
        """Get all dead ends for a project"""
        cursor = self.conn.cursor()
        query = "SELECT * FROM project_dead_ends WHERE project_id = ? ORDER BY created_timestamp DESC"
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query, (project_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_project_reference_docs(self, project_id: str) -> List[Dict]:
        """Get all reference docs for a project"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM project_reference_docs 
            WHERE project_id = ? 
            ORDER BY created_timestamp DESC
        """, (project_id,))
        return [dict(row) for row in cursor.fetchall()]

    def log_mistake(
        self,
        session_id: str,
        mistake: str,
        why_wrong: str,
        cost_estimate: Optional[str] = None,
        root_cause_vector: Optional[str] = None,
        prevention: Optional[str] = None,
        goal_id: Optional[str] = None
    ) -> str:
        """
        Log a mistake for learning and future prevention.
        
        Args:
            session_id: Session identifier
            mistake: What was done wrong
            why_wrong: Explanation of why it was wrong
            cost_estimate: Estimated time/effort wasted (e.g., "2 hours")
            root_cause_vector: Epistemic vector that caused the mistake (e.g., "KNOW", "CONTEXT")
            prevention: How to prevent this mistake in the future
            goal_id: Optional goal identifier this mistake relates to
            
        Returns:
            mistake_id: UUID string
        """
        self._validate_session_id(session_id)
        mistake_id = str(uuid.uuid4())
        
        # Build mistake_data JSON
        mistake_data = {
            "mistake": mistake,
            "why_wrong": why_wrong,
            "cost_estimate": cost_estimate,
            "root_cause_vector": root_cause_vector,
            "prevention": prevention
        }
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO mistakes_made (
                id, session_id, goal_id, mistake, why_wrong,
                cost_estimate, root_cause_vector, prevention,
                created_timestamp, mistake_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            mistake_id, session_id, goal_id, mistake, why_wrong,
            cost_estimate, root_cause_vector, prevention,
            time.time(), json.dumps(mistake_data)
        ))
        
        self.conn.commit()
        logger.info(f"📝 Mistake logged: {mistake[:50]}...")
        
        return mistake_id
    
    def get_mistakes(
        self,
        session_id: Optional[str] = None,
        goal_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Retrieve logged mistakes.
        
        Args:
            session_id: Optional filter by session
            goal_id: Optional filter by goal
            limit: Maximum number of results
            
        Returns:
            List of mistake dictionaries
        """
        cursor = self.conn.cursor()
        
        if session_id and goal_id:
            cursor.execute("""
                SELECT * FROM mistakes_made
                WHERE session_id = ? AND goal_id = ?
                ORDER BY created_timestamp DESC
                LIMIT ?
            """, (session_id, goal_id, limit))
        elif session_id:
            cursor.execute("""
                SELECT * FROM mistakes_made
                WHERE session_id = ?
                ORDER BY created_timestamp DESC
                LIMIT ?
            """, (session_id, limit))
        elif goal_id:
            cursor.execute("""
                SELECT * FROM mistakes_made
                WHERE goal_id = ?
                ORDER BY created_timestamp DESC
                LIMIT ?
            """, (goal_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM mistakes_made
                ORDER BY created_timestamp DESC
                LIMIT ?
            """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Close database connection"""
        self.conn.close()



if __name__ == "__main__":
    # Test the database
    logger.info("🧪 Testing Session Database...")
    db = SessionDatabase()
    db.close()
    logger.info("✅ Session Database ready")
