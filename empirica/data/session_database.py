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

# Import formatters
from .formatters import (
    generate_context_markdown,
    export_to_reflex_logs,
    determine_action
)


class SessionDatabase:
    """Central database for all session data (supports SQLite and PostgreSQL)"""

    def __init__(self, db_path: Optional[str] = None, db_type: Optional[str] = None):
        """
        Initialize session database with pluggable backend

        Args:
            db_path: Path to database (SQLite only, ignored for PostgreSQL)
            db_type: "sqlite" or "postgresql" (defaults to config or "sqlite")
        """
        # Import adapter layer
        from empirica.data.db_adapter import DatabaseAdapter
        from empirica.config.database_config import get_database_config

        # If db_type not specified, load from config
        if db_type is None:
            db_config = get_database_config()
            db_type = db_config.get("type", "sqlite")
        else:
            db_config = {"type": db_type}

        # Create appropriate adapter
        if db_type == "sqlite":
            # Use provided path or default
            if db_path is None:
                from empirica.config.path_resolver import get_session_db_path
                db_path = str(get_session_db_path())

            self.db_path = Path(db_path)
            self.adapter = DatabaseAdapter.create(db_type="sqlite", db_path=str(self.db_path))
            logger.info(f"📊 Session Database initialized (SQLite): {self.db_path}")

        elif db_type == "postgresql":
            pg_config = db_config.get("postgresql", {})
            self.adapter = DatabaseAdapter.create(db_type="postgresql", **pg_config)
            self.db_path = None  # N/A for PostgreSQL
            logger.info(f"📊 Session Database initialized (PostgreSQL)")

        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        # Expose raw connection for backward compatibility with repositories
        self.conn = self.adapter.conn

        self._create_tables()

        # Initialize domain repositories (sharing same connection)
        from empirica.data.repositories import (
            SessionRepository, CascadeRepository, GoalRepository,
            BranchRepository, BreadcrumbRepository, ProjectRepository,
            TokenRepository, CommandRepository, WorkspaceRepository,
            VectorRepository
        )
        self.sessions = SessionRepository(self.conn)
        self.cascades = CascadeRepository(self.conn)
        self.goals = GoalRepository(self.conn)
        self.branches = BranchRepository(self.conn)
        self.breadcrumbs = BreadcrumbRepository(self.conn)
        self.projects = ProjectRepository(self.conn)
        self.tokens = TokenRepository(self.conn)
        self.commands = CommandRepository(self.conn)
        self.workspace = WorkspaceRepository(self.conn)
        self.vectors = VectorRepository(self.conn)

        # Core repositories need special handling to avoid circular dependency
        # We'll initialize them lazily when first accessed
        self._tasks = None
        self._core_goals = None
        self._tasks_db_path = str(self.db_path) if self.db_path else None

    @property
    def tasks(self):
        """Lazy-load TaskRepository to avoid circular dependency"""
        if self._tasks is None:
            from empirica.core.tasks.repository import TaskRepository
            self._tasks = TaskRepository(db_path=self._tasks_db_path)
        return self._tasks

    @property
    def core_goals(self):
        """Lazy-load core GoalRepository for query methods"""
        if self._core_goals is None:
            from empirica.core.goals.repository import GoalRepository as CoreGoalRepository
            self._core_goals = CoreGoalRepository()
        return self._core_goals

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
        """Create all database tables from schema modules"""
        from empirica.data.schema import ALL_SCHEMAS
        from empirica.data.migrations import MigrationRunner, ALL_MIGRATIONS

        cursor = self.conn.cursor()

        # Execute all table schemas
        for schema_sql in ALL_SCHEMAS:
            cursor.execute(schema_sql)

        # Run tracked migrations (only executes once per migration)
        migration_runner = MigrationRunner(self.conn)
        migration_runner.run_all(ALL_MIGRATIONS)

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_ai ON sessions(ai_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cascades_session ON cascades(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cascades_confidence ON cascades(final_confidence)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_divergence_cascade ON divergence_tracking(cascade_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_beliefs_cascade ON bayesian_beliefs(cascade_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tools_cascade ON investigation_tools(cascade_id)")
        # BEADS integration index (check if column exists first)
        cursor.execute("SELECT COUNT(*) FROM pragma_table_info('goals') WHERE name='beads_issue_id'")
        if cursor.fetchone()[0] > 0:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_beads_issue_id ON goals(beads_issue_id)")
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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_epistemic_sources_project ON epistemic_sources(project_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_epistemic_sources_session ON epistemic_sources(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_epistemic_sources_type ON epistemic_sources(source_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_epistemic_sources_confidence ON epistemic_sources(confidence)")

        # Indexes for investigation_branches
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_investigation_branches_session ON investigation_branches(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_investigation_branches_status ON investigation_branches(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_investigation_branches_winner ON investigation_branches(is_winner)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_investigation_branches_merge_score ON investigation_branches(merge_score)")

        # Indexes for merge_decisions
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_merge_decisions_session ON merge_decisions(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_merge_decisions_round ON merge_decisions(investigation_round)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_merge_decisions_winning_branch ON merge_decisions(winning_branch_id)")

        # Indexes for token_savings
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_token_savings_session ON token_savings(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_token_savings_type ON token_savings(saving_type)")

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
    
    def create_session(self, ai_id: str, components_loaded: int = 0,
                      user_id: Optional[str] = None, subject: Optional[str] = None) -> str:
        """
        Create new session, return session_id (delegates to SessionRepository)

        Args:
            ai_id: AI identifier (required)
            components_loaded: Number of components loaded - default 0 (components created on-demand)
            user_id: Optional user identifier
            subject: Optional subject/workstream identifier for filtering

        Returns:
            session_id: UUID string
        """
        return self.sessions.create_session(ai_id, components_loaded, user_id, subject)
    
    def end_session(self, session_id: str, avg_confidence: Optional[float] = None,
                   drift_detected: bool = False, notes: Optional[str] = None):
        """Mark session as ended (delegates to SessionRepository)"""
        self._validate_session_id(session_id)
        return self.sessions.end_session(session_id, avg_confidence, drift_detected, notes)
    
    def create_cascade(self, session_id: str, task: str, context: Dict[str, Any],
                      goal_id: Optional[str] = None, goal: Optional[Dict[str, Any]] = None) -> str:
        """Create cascade record (delegates to CascadeRepository)"""
        self._validate_session_id(session_id)
        return self.cascades.create_cascade(session_id, task, context, goal_id, goal)
    
    def update_cascade_phase(self, cascade_id: str, phase: str, completed: bool = True):
        """Mark cascade phase as completed (delegates to CascadeRepository)"""
        return self.cascades.update_cascade_phase(cascade_id, phase, completed)
    
    def complete_cascade(self, cascade_id: str, final_action: str, final_confidence: float,
                        investigation_rounds: int, duration_ms: int,
                        engagement_gate_passed: bool, bayesian_active: bool = False,
                        drift_monitored: bool = False):
        """Mark cascade as completed with final results (delegates to CascadeRepository)"""
        return self.cascades.complete_cascade(
            cascade_id, final_action, final_confidence, investigation_rounds,
            duration_ms, engagement_gate_passed, bayesian_active, drift_monitored
        )
    
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
        """Get session data (delegates to SessionRepository)"""
        return self.sessions.get_session(session_id)
    
    def get_session_cascades(self, session_id: str) -> List[Dict]:
        """Get all cascades for a session (delegates to SessionRepository)"""
        return self.sessions.get_session_cascades(session_id)
    
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
            export_to_reflex_logs(
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
            export_to_reflex_logs(
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
        """Get latest PREFLIGHT vectors for session (delegates to VectorRepository)"""
        return self.vectors.get_preflight_vectors(session_id)

    def get_check_vectors(self, session_id: str, cycle: Optional[int] = None) -> List[Dict]:
        """Get CHECK phase vectors (delegates to VectorRepository)"""
        return self.vectors.get_check_vectors(session_id, cycle)

    def get_postflight_vectors(self, session_id: str) -> Optional[Dict]:
        """Get latest POSTFLIGHT vectors for session (delegates to VectorRepository)"""
        return self.vectors.get_postflight_vectors(session_id)
    
    def get_vectors_by_phase(self, session_id: str, phase: str) -> List[Dict]:
        """Get all vectors for a specific phase (delegates to VectorRepository)"""
        return self.vectors.get_vectors_by_phase(session_id, phase)
    
    def store_epistemic_delta(self, cascade_id: str, delta: Dict[str, float]):
        """Store epistemic delta for calibration tracking (delegates to CascadeRepository)"""
        return self.cascades.store_epistemic_delta(cascade_id, delta)
    
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
    
    def get_session_snapshot(self, session_id: str) -> Optional[Dict]:
        """
        Get git-native session snapshot showing where you left off
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with git state, epistemic trajectory, learning delta, goals, sources
        """
        import subprocess
        
        session = self.get_session(session_id)
        if not session:
            return None
        
        # Get git state
        git_state = {}
        try:
            # Current branch
            branch = subprocess.run(['git', 'branch', '--show-current'], 
                                   capture_output=True, text=True, check=True)
            git_state['branch'] = branch.stdout.strip()
            
            # Current commit
            commit = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'],
                                   capture_output=True, text=True, check=True)
            git_state['commit'] = commit.stdout.strip()
            
            # Last 5 commits
            log = subprocess.run(['git', 'log', '--oneline', '-5'],
                                capture_output=True, text=True, check=True)
            git_state['last_5_commits'] = log.stdout.strip().split('\n')
            
            # Diff stat (lightweight)
            diff_stat = subprocess.run(['git', 'diff', '--stat', 'HEAD'],
                                      capture_output=True, text=True, check=True)
            git_state['diff_stat'] = diff_stat.stdout.strip() if diff_stat.stdout.strip() else "No uncommitted changes"
            
        except subprocess.CalledProcessError as e:
            git_state['error'] = f"Git error: {e}"
        
        # Get epistemic trajectory (PREFLIGHT → CHECK → POSTFLIGHT)
        trajectory = {}
        
        # PREFLIGHT
        preflight = self.get_latest_vectors(session_id, phase='PREFLIGHT')
        if preflight:
            trajectory['preflight'] = preflight['vectors']
        
        # CHECK gates (all of them)
        check_gates = self.get_vectors_by_phase(session_id, phase='CHECK')
        if check_gates:
            trajectory['check_gates'] = [c['vectors'] for c in check_gates]
        
        # POSTFLIGHT
        postflight = self.get_latest_vectors(session_id, phase='POSTFLIGHT')
        if postflight:
            trajectory['postflight'] = postflight['vectors']
        
        # Calculate learning delta
        learning_delta = {}
        if preflight and postflight:
            pre_vectors = preflight['vectors']
            post_vectors = postflight['vectors']
            for key in post_vectors:
                if key in pre_vectors:
                    learning_delta[key] = round(post_vectors[key] - pre_vectors[key], 3)
        
        # Get active goals
        active_goals = []
        goal_tree = self.get_goal_tree(session_id)
        for goal in goal_tree:
            if goal.get('status') != 'completed':
                active_goals.append({
                    'id': goal['goal_id'],
                    'objective': goal['objective'],
                    'progress': f"{goal.get('completed_subtasks', 0)}/{goal.get('total_subtasks', 0)}"
                })
        
        # Get sources referenced in this session
        project_id = session.get('project_id')
        sources_referenced = []
        if project_id:
            sources = self.get_epistemic_sources(project_id, session_id=session_id, limit=10)
            sources_referenced = [{
                'title': s['title'],
                'type': s['source_type'],
                'confidence': s['confidence'],
                'url': s.get('source_url')
            } for s in sources]
        
        return {
            'session_id': session_id,
            'ai_id': session['ai_id'],
            'git_state': git_state,
            'epistemic_trajectory': trajectory,
            'learning_delta': learning_delta,
            'active_goals': active_goals,
            'sources_referenced': sources_referenced,
            'subject': session.get('subject')
        }

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
        current_state = self.get_latest_vectors(session_id)

        if not current_state:
            return {"error": "No current state found"}

        current_vectors = current_state.get('vectors', {})
        
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

    def store_vectors(self, session_id: str, phase: str, vectors: Dict[str, float], cascade_id: Optional[str] = None, round_num: int = 1, metadata: Optional[Dict] = None, reasoning: Optional[str] = None):
        """Store epistemic vectors (delegates to VectorRepository)"""
        return self.vectors.store_vectors(session_id, phase, vectors, cascade_id, round_num, metadata, reasoning)

    def get_latest_vectors(self, session_id: str, phase: Optional[str] = None) -> Optional[Dict]:
        """Get latest epistemic vectors for session (delegates to VectorRepository)"""
        return self.vectors.get_latest_vectors(session_id, phase)

    # =========================================================================
    # Goal and Subtask Management (for decision quality + continuity + audit)
    # =========================================================================

    def create_goal(self, session_id: str, objective: str, scope_breadth: float = None,
                   scope_duration: float = None, scope_coordination: float = None) -> str:
        """Create a new goal for this session (delegates to GoalRepository)

        Args:
            session_id: Session UUID
            objective: What are you trying to accomplish?
            scope_breadth: 0.0-1.0 (0=single file, 1=entire codebase)
            scope_duration: 0.0-1.0 (0=minutes, 1=months)
            scope_coordination: 0.0-1.0 (0=solo, 1=heavy multi-agent)

        Returns:
            goal_id (UUID string)
        """
        return self.goals.create_goal(session_id, objective, scope_breadth,
                                      scope_duration, scope_coordination)

    def create_subtask(self, goal_id: str, description: str, importance: str = 'medium') -> str:
        """Create a subtask within a goal (delegates to GoalRepository)

        Args:
            goal_id: Parent goal UUID
            description: What are you investigating/implementing?
            importance: 'critical' | 'high' | 'medium' | 'low'

        Returns:
            subtask_id (UUID string)
        """
        return self.goals.create_subtask(goal_id, description, importance)

    def update_subtask_findings(self, subtask_id: str, findings: List[str]):
        """Update findings for a subtask (delegates to GoalRepository)

        Args:
            subtask_id: Subtask UUID
            findings: List of finding strings
        """
        return self.goals.update_subtask_findings(subtask_id, findings)

    def update_subtask_unknowns(self, subtask_id: str, unknowns: List[str]):
        """Update unknowns for a subtask (delegates to GoalRepository)

        Args:
            subtask_id: Subtask UUID
            unknowns: List of unknown strings
        """
        return self.goals.update_subtask_unknowns(subtask_id, unknowns)

    def update_subtask_dead_ends(self, subtask_id: str, dead_ends: List[str]):
        """Update dead ends for a subtask (delegates to GoalRepository)

        Args:
            subtask_id: Subtask UUID
            dead_ends: List of dead end strings (e.g., "Attempted X - blocked by Y")
        """
        return self.goals.update_subtask_dead_ends(subtask_id, dead_ends)

    def complete_subtask(self, subtask_id: str, evidence: str):
        """Mark subtask as completed with evidence (delegates to GoalRepository)

        Args:
            subtask_id: Subtask UUID
            evidence: Evidence of completion (e.g., "Documented in design doc", "PR merged")
        """
        return self.goals.complete_subtask(subtask_id, evidence)

    def get_all_sessions(self, ai_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """List all sessions, optionally filtered by ai_id (delegates to SessionRepository)

        Args:
            ai_id: Optional AI identifier to filter by
            limit: Maximum number of sessions to return (default 50)

        Returns:
            List of session dictionaries
        """
        return self.sessions.get_all_sessions(ai_id, limit)

    def get_goal_tree(self, session_id: str) -> List[Dict]:
        """Get complete goal tree for a session (delegates to GoalRepository)

        Returns list of goals with nested subtasks

        Args:
            session_id: Session UUID

        Returns:
            List of goal dicts, each with 'subtasks' list
        """
        return self.goals.get_goal_tree(session_id)

    def query_unknowns_summary(self, session_id: str) -> Dict:
        """Get summary of all unknowns in a session (delegates to GoalRepository)

        Args:
            session_id: Session UUID

        Returns:
            Dict with total_unknowns count and breakdown by goal
        """
        return self.goals.query_unknowns_summary(session_id)

    def query_goals(self, session_id: Optional[str] = None, is_completed: Optional[bool] = None) -> List:
        """Query goals with optional filters (delegates to core GoalsRepository)

        Args:
            session_id: Optional session UUID to filter by
            is_completed: Optional completion status filter (True/False/None for all)

        Returns:
            List of Goal objects matching filters
        """
        return self.core_goals.query_goals(
            session_id=session_id,
            is_completed=is_completed
        )

    def query_subtasks(self, goal_id: Optional[str] = None, status: Optional[str] = None) -> List:
        """Query subtasks with optional filters (delegates to TaskRepository)

        Args:
            goal_id: Optional goal UUID to filter by
            status: Optional status filter (string like 'pending', 'completed')

        Returns:
            List of SubTask objects matching filters
        """
        # Convert status string to TaskStatus enum if provided
        task_status = None
        if status:
            from empirica.core.tasks.types import TaskStatus
            try:
                task_status = TaskStatus(status)
            except ValueError:
                pass  # Invalid status, ignore

        return self.tasks.query_subtasks(
            goal_id=goal_id,
            status=task_status
        )

    def get_goal_subtasks(self, goal_id: str) -> List:
        """Get all subtasks for a specific goal (delegates to TaskRepository)

        Args:
            goal_id: Goal UUID

        Returns:
            List of SubTask objects for this goal
        """
        return self.tasks.get_goal_subtasks(goal_id)

    def query_goal_progress(self, goal_id: str) -> Dict:
        """Get goal completion statistics

        Args:
            goal_id: Goal UUID

        Returns:
            Dict with total, completed, remaining counts and percentage
        """
        subtasks = self.tasks.get_goal_subtasks(goal_id)
        total = len(subtasks)
        completed = sum(1 for st in subtasks if st.status.value == "completed")

        return {
            "goal_id": goal_id,
            "total": total,
            "completed": completed,
            "remaining": total - completed,
            "percentage": round((completed / total * 100), 1) if total > 0 else 0.0
        }

    # ========== Investigation Branches (Epistemic Auto-Merge) ==========

    def create_branch(self, session_id: str, branch_name: str, investigation_path: str,
                     git_branch_name: str, preflight_vectors: Dict) -> str:
        """Create a new investigation branch (delegates to BranchRepository)

        Args:
            session_id: Session UUID
            branch_name: Human-readable branch name
            investigation_path: What is being investigated (e.g., 'oauth2')
            git_branch_name: Git branch name
            preflight_vectors: Epistemic vectors at branch start

        Returns:
            Branch ID
        """
        return self.branches.create_branch(session_id, branch_name, investigation_path,
                                           git_branch_name, preflight_vectors)

    def checkpoint_branch(self, branch_id: str, postflight_vectors: Dict,
                         tokens_spent: int, time_spent_minutes: int) -> bool:
        """Checkpoint a branch after investigation (delegates to BranchRepository)

        Args:
            branch_id: Branch ID
            postflight_vectors: Epistemic vectors after investigation
            tokens_spent: Tokens used in investigation
            time_spent_minutes: Time spent in investigation

        Returns:
            Success boolean
        """
        return self.branches.checkpoint_branch(branch_id, postflight_vectors,
                                               tokens_spent, time_spent_minutes)

    def calculate_branch_merge_score(self, branch_id: str) -> Dict:
        """Calculate epistemic merge score for a branch (delegates to BranchRepository)

        Score = (learning_delta × quality × confidence) / cost_penalty
        Where: confidence = 1 - uncertainty (uncertainty is a DAMPENER)

        Returns:
            Dict with merge_score, quality, and rationale
        """
        return self.branches.calculate_branch_merge_score(branch_id)

    def merge_branches(self, session_id: str, investigation_round: int = 1) -> Dict:
        """Auto-merge best branch based on epistemic scores (delegates to BranchRepository)

        Returns:
            Dict with winning_branch_id, merge_decision_id, rationale
        """
        return self.branches.merge_branches(session_id, investigation_round)

    def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        repos: Optional[List[str]] = None
    ) -> str:
        """Create a new project (delegates to ProjectRepository)

        Args:
            name: Project name (e.g., "Empirica Core")
            description: Project description
            repos: List of repository names (e.g., ["empirica", "empirica-dev"])

        Returns:
            project_id: UUID string
        """
        return self.projects.create_project(name, description, repos)
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project data (delegates to ProjectRepository)"""
        return self.projects.get_project(project_id)
    
    def resolve_project_id(self, project_id_or_name: str) -> Optional[str]:
        """Resolve project name or UUID to UUID (delegates to ProjectRepository)"""
        return self.projects.resolve_project_id(project_id_or_name)
    
    def link_session_to_project(self, session_id: str, project_id: str):
        """Link a session to a project (delegates to ProjectRepository)"""
        self._validate_session_id(session_id)
        return self.projects.link_session_to_project(session_id, project_id)
    
    def get_project_sessions(self, project_id: str) -> List[Dict]:
        """Get all sessions for a project (delegates to ProjectRepository)"""
        return self.projects.get_project_sessions(project_id)
    
    def aggregate_project_learning_deltas(self, project_id: str) -> Dict[str, float]:
        """Compute total epistemic learning across all project sessions (delegates to ProjectRepository)"""
        return self.projects.aggregate_project_learning_deltas(project_id)
    
    def create_project_handoff(
        self,
        project_id: str,
        project_summary: str,
        key_decisions: Optional[List[str]] = None,
        patterns_discovered: Optional[List[str]] = None,
        remaining_work: Optional[List[str]] = None
    ) -> str:
        """Create project-level handoff report (delegates to ProjectRepository)"""
        return self.projects.create_project_handoff(
            project_id, project_summary, key_decisions, patterns_discovered, remaining_work
        )
    
    def get_latest_project_handoff(self, project_id: str) -> Optional[Dict]:
        """Get the most recent project handoff (delegates to ProjectRepository)"""
        return self.projects.get_latest_project_handoff(project_id)
    
    def generate_file_tree(self, project_root: str, max_depth: int = 3, use_cache: bool = True) -> Optional[str]:
        """Generate file tree respecting .gitignore
        
        Args:
            project_root: Path to project root
            max_depth: Tree depth (default: 3)
            use_cache: Use cached tree if <60s old
            
        Returns:
            str: Tree output (plain text, no ANSI codes) or None if tree not available
        """
        import subprocess
        import time
        from pathlib import Path
        
        # Check if tree is installed
        try:
            subprocess.run(["tree", "--version"], capture_output=True, check=True, timeout=1)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            logger.debug("tree command not available, skipping file tree generation")
            return None
        
        cache_key = f"tree_{Path(project_root).name}_{max_depth}"
        cache_dir = Path(project_root) / ".empirica" / "cache"
        cache_file = cache_dir / f"{cache_key}.txt"
        
        # Check cache
        if use_cache and cache_file.exists():
            age = time.time() - cache_file.stat().st_mtime
            if age < 60:  # 60 second cache
                logger.debug(f"Using cached file tree (age: {age:.1f}s)")
                return cache_file.read_text()
        
        # Generate tree
        cmd = [
            "tree",
            "-L", str(max_depth),
            "--gitignore",
            "--dirsfirst",
            "-n",  # No color (plain text)
            project_root
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                tree_output = result.stdout
                # Cache it
                cache_dir.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(tree_output)
                logger.debug(f"Generated file tree (cached to {cache_file})")
                return tree_output
            else:
                logger.warning(f"tree command failed: {result.stderr}")
                return None
        except subprocess.TimeoutExpired:
            logger.warning("tree command timed out (>5s)")
            return None
        except Exception as e:
            logger.warning(f"Error generating file tree: {e}")
            return None
    

    def _resolve_and_validate_project(self, project_id: str) -> Optional[Dict]:
        """Resolve project name to UUID and validate it exists"""
        resolved_id = self.resolve_project_id(project_id)
        if not resolved_id:
            return None

        project = self.get_project(resolved_id)
        return project

    def _load_breadcrumbs_for_mode(self, project_id: str, mode: str, subject: Optional[str] = None) -> Dict:
        """Load all breadcrumbs (findings, unknowns, dead_ends, mistakes, reference_docs) based on mode"""
        if mode == "session_start":
            # FAST: Recent items only
            findings = self.breadcrumbs.get_project_findings(project_id, limit=10, subject=subject)
            unknowns = self.breadcrumbs.get_project_unknowns(project_id, resolved=False, subject=subject)
            dead_ends = self.breadcrumbs.get_project_dead_ends(project_id, limit=5, subject=subject)
            recent_mistakes = self.breadcrumbs.get_project_mistakes(project_id, limit=5)
        else:  # mode == "live"
            # COMPLETE: All items
            findings = self.breadcrumbs.get_project_findings(project_id, subject=subject)
            unknowns = self.breadcrumbs.get_project_unknowns(project_id, subject=subject)
            dead_ends = self.breadcrumbs.get_project_dead_ends(project_id, subject=subject)
            recent_mistakes = self.breadcrumbs.get_project_mistakes(project_id)

        reference_docs = self.breadcrumbs.get_project_reference_docs(project_id)

        return {
            'findings': findings,
            'unknowns': unknowns,
            'dead_ends': dead_ends,
            'mistakes_to_avoid': recent_mistakes,
            'reference_docs': reference_docs
        }

    def _load_goals_for_project(self, project_id: str) -> Dict:
        """Load incomplete and active goals for project"""
        # Get incomplete goals
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, objective, scope, status, created_timestamp
            FROM goals
            WHERE session_id IN (SELECT session_id FROM sessions WHERE project_id = ?)
            AND is_completed = 0
            ORDER BY created_timestamp DESC
        """, (project_id,))
        incomplete_goals = [dict(row) for row in cursor.fetchall()]

        # Get active goals (more detailed)
        cursor.execute("""
            SELECT g.id, g.objective, g.scope, g.status, g.goal_data,
                   COUNT(DISTINCT s.id) as subtask_count,
                   SUM(CASE WHEN s.status = 'completed' THEN 1 ELSE 0 END) as completed_subtasks
            FROM goals g
            LEFT JOIN subtasks s ON g.id = s.goal_id
            WHERE g.session_id IN (SELECT session_id FROM sessions WHERE project_id = ?)
            AND g.is_completed = 0
            GROUP BY g.id
            ORDER BY g.created_timestamp DESC
        """, (project_id,))
        active_goals = [dict(row) for row in cursor.fetchall()]

        return {
            'incomplete_work': incomplete_goals,
            'goals': active_goals
        }

    def _capture_live_state_if_requested(
        self,
        session_id: Optional[str],
        project_id: str,
        include_live_state: bool,
        fresh_assess: bool,
        trigger: Optional[str]
    ) -> Optional[Dict]:
        """Capture live epistemic state if requested"""
        if not include_live_state:
            return None

        # Auto-resolve session_id if not provided
        if not session_id:
            session_id = self._auto_resolve_session(project_id, trigger)

        if not session_id:
            return None

        # Capture or load live state
        if fresh_assess:
            return self._capture_fresh_state(session_id, project_id)
        else:
            return self._load_latest_checkpoint_state(session_id)


    def bootstrap_project_breadcrumbs(
        self,
        project_id: str,
        mode: str = "session_start",
        project_root: str = None,
        check_integrity: bool = False,
        task_description: str = None,
        epistemic_state: Dict[str, float] = None,
        context_to_inject: bool = False,
        subject: Optional[str] = None,
        session_id: Optional[str] = None,
        include_live_state: bool = False,
        fresh_assess: bool = False,
        trigger: Optional[str] = None,
        depth: str = "auto"
    ) -> Dict:
        """
        Generate epistemic breadcrumbs for starting a new session on existing project.

        Args:
            project_id: Project identifier (UUID or project name)
            mode: "session_start" (fast, recent items) or "live" (complete, all items)
            project_root: Optional path to project root (defaults to cwd)
            check_integrity: If True, analyze doc-code integrity (adds ~2s)
            task_description: Task description for context load balancing (optional)
            epistemic_state: Epistemic vectors for intelligent routing (optional)
            context_to_inject: If True, generate markdown context string (optional)
            subject: Filter breadcrumbs by subject (optional)
            session_id: Session ID for live state capture (optional, auto-resolved if needed)
            include_live_state: Include current epistemic state (optional)
            fresh_assess: Use fresh self-assessment vs loading checkpoint (optional)
            trigger: Trigger context for session resolution (pre_compact/post_compact/manual)
            depth: Context depth (minimal/moderate/full/auto)

        Returns quick context: findings, unknowns, dead_ends, mistakes, decisions, incomplete work.
        """
        import os

        if project_root is None:
            project_root = os.getcwd()

        # 1. Resolve and validate project
        project = self._resolve_and_validate_project(project_id)
        if not project:
            return {"error": f"Project not found: {project_id}"}

        resolved_id = project['id']

        # 2. Get latest handoff
        latest_handoff = self.get_latest_project_handoff(resolved_id)

        # 3. Load all breadcrumbs based on mode
        breadcrumbs = self._load_breadcrumbs_for_mode(resolved_id, mode, subject)

        # 4. Load goals
        goals_data = self._load_goals_for_project(resolved_id)
        breadcrumbs.update(goals_data)

        # 5. Generate file tree
        file_tree = self.generate_file_tree(project_root)
        breadcrumbs['file_tree'] = file_tree

        # 6. Capture live state if requested
        live_state = self._capture_live_state_if_requested(
            session_id, resolved_id, include_live_state, fresh_assess, trigger
        )
        if live_state:
            breadcrumbs['live_state'] = live_state
            breadcrumbs['session_id'] = session_id or live_state.get('session_id')

        # 7. Add project metadata
        breadcrumbs['project'] = {
            'id': project['id'],
            'name': project.get('name', 'Unknown'),
            'description': project.get('description', ''),
            'status': project.get('status', 'active')
        }

        if latest_handoff:
            breadcrumbs['latest_handoff'] = latest_handoff

        # 8. Generate context markdown if requested
        if context_to_inject:
            context_markdown = generate_context_markdown(breadcrumbs)
            breadcrumbs['context_markdown'] = context_markdown

        # 9. Apply adaptive depth filtering if needed
        if depth != "auto" or trigger == "post_compact":
            breadcrumbs = self._apply_depth_filter(breadcrumbs, depth, trigger)

        return breadcrumbs


    def _auto_resolve_session(self, project_id: str, trigger: Optional[str]) -> Optional[str]:
        """
        Auto-resolve session_id from project and trigger context.

        Resolution order:
        1. If trigger='post_compact': Load from latest pre-summary snapshot
        2. If trigger='pre_compact': Get latest session for project (even if ended)
        3. Otherwise: Get latest ACTIVE session for project
        """
        if trigger == 'post_compact':
            # Load session from pre-compact snapshot
            try:
                from pathlib import Path
                import json
                ref_docs_dir = Path.cwd() / ".empirica" / "ref-docs"
                snapshots = sorted(ref_docs_dir.glob("pre_summary_*.json"), reverse=True)
                if snapshots:
                    with open(snapshots[0], 'r') as f:
                        snapshot = json.load(f)
                        return snapshot.get('session_id')
            except:
                pass

        # Get latest session for project
        cursor = self.conn.cursor()
        if trigger == 'pre_compact':
            # Include ended sessions (POSTFLIGHT just ran)
            cursor.execute("""
                SELECT session_id FROM sessions
                WHERE project_id = ?
                ORDER BY start_time DESC
                LIMIT 1
            """, (project_id,))
        else:
            # Only active sessions (end_time IS NULL)
            cursor.execute("""
                SELECT session_id FROM sessions
                WHERE project_id = ? AND end_time IS NULL
                ORDER BY start_time DESC
                LIMIT 1
            """, (project_id,))

        row = cursor.fetchone()
        return row['session_id'] if row else None

    def _capture_fresh_state(self, session_id: str, project_id: str) -> Dict:
        """
        Capture fresh epistemic state via self-assessment.

        Returns current state (not from old checkpoint):
        - Vectors from latest available checkpoint OR minimal self-assess
        - Current git state
        - Reasoning
        - Investigation context
        """
        import subprocess
        from datetime import datetime

        # Get git state
        git_state = self._get_current_git_state()

        # Try to get vectors from latest checkpoint
        try:
            from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
            git_logger = GitEnhancedReflexLogger(session_id=session_id, enable_git_notes=True)
            checkpoints = git_logger.list_checkpoints(limit=1)

            if checkpoints:
                latest = checkpoints[0]
                vectors = latest.get('vectors', {})
                reasoning = latest.get('meta', {}).get('reasoning', 'Latest checkpoint reasoning')
                phase = latest.get('phase', 'UNKNOWN')
            else:
                # No checkpoints - use minimal default
                vectors = {
                    "engagement": 0.5,
                    "know": 0.5,
                    "uncertainty": 0.5,
                    "impact": 0.5,
                    "completion": 0.0
                }
                reasoning = "Fresh assessment (no prior checkpoints)"
                phase = None
        except Exception as e:
            # Fallback to minimal state
            vectors = {
                "engagement": 0.5,
                "know": 0.5,
                "uncertainty": 0.5,
                "impact": 0.5,
                "completion": 0.0
            }
            reasoning = f"Fresh assessment (error loading checkpoint: {e})"
            phase = None

        return {
            "vectors": vectors,
            "git": git_state,
            "reasoning": reasoning,
            "phase": phase,
            "timestamp": datetime.now().isoformat(),
            "fresh": True  # Flag to indicate this is fresh, not loaded checkpoint
        }

    def _load_latest_checkpoint_state(self, session_id: str) -> Optional[Dict]:
        """Load latest checkpoint from session (via GitEnhancedReflexLogger)"""
        try:
            from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
            from datetime import datetime

            git_logger = GitEnhancedReflexLogger(session_id=session_id, enable_git_notes=True)
            checkpoints = git_logger.list_checkpoints(limit=1)

            if not checkpoints:
                return None

            checkpoint = checkpoints[0]
            return {
                "vectors": checkpoint.get('vectors', {}),
                "git": self._get_current_git_state(),  # Current git state, not from checkpoint
                "reasoning": checkpoint.get('meta', {}).get('reasoning', ''),
                "phase": checkpoint.get('phase'),
                "timestamp": checkpoint.get('timestamp'),
                "fresh": False  # Loaded from checkpoint, not fresh
            }
        except Exception as e:
            return {"error": str(e)}

    def _get_current_git_state(self) -> Dict:
        """Get current git state (HEAD, branch, dirty flag, uncommitted changes)"""
        import subprocess

        try:
            # Get HEAD commit
            head = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=2
            )
            head_commit = head.stdout.strip() if head.returncode == 0 else None

            # Get branch
            branch = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=2
            )
            branch_name = branch.stdout.strip() if branch.returncode == 0 else None

            # Check if dirty (uncommitted changes)
            status = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True,
                text=True,
                timeout=2
            )
            dirty = len(status.stdout.strip()) > 0 if status.returncode == 0 else None
            uncommitted_count = len(status.stdout.strip().split('\n')) if dirty else 0

            return {
                "head": head_commit,
                "branch": branch_name,
                "dirty": dirty,
                "uncommitted_files": uncommitted_count
            }
        except Exception as e:
            return {"error": str(e)}

    def _apply_depth_filter(self, breadcrumbs: Dict, depth: str, trigger: Optional[str]) -> Dict:
        """
        Apply adaptive depth filtering to breadcrumbs based on drift or explicit depth.

        Depth levels:
        - minimal: Last 5 findings/unknowns, current goal only (~500 tokens)
        - moderate: Last 10 findings/unknowns, all active goals (~1500 tokens)
        - full: All findings/unknowns, all goals, all ref-docs (~3000-5000 tokens)
        - auto: Determine depth based on drift (if post_compact trigger)
        """
        if depth == "auto" and trigger == "post_compact":
            # Calculate drift from pre-snapshot to current
            try:
                from pathlib import Path
                import json
                ref_docs_dir = Path.cwd() / ".empirica" / "ref-docs"
                snapshots = sorted(ref_docs_dir.glob("pre_summary_*.json"), reverse=True)

                if snapshots and breadcrumbs.get('live_state'):
                    with open(snapshots[0], 'r') as f:
                        pre_snapshot = json.load(f)

                    pre_vectors = pre_snapshot.get('checkpoint', {}).get('vectors', {})
                    post_vectors = breadcrumbs['live_state'].get('vectors', {})

                    # Calculate drift (simple average of vector changes)
                    drift = 0.0
                    count = 0
                    for key in ['know', 'uncertainty', 'engagement', 'impact', 'completion']:
                        if key in pre_vectors and key in post_vectors:
                            drift += abs(pre_vectors[key] - post_vectors[key])
                            count += 1

                    drift = drift / count if count > 0 else 0.0

                    # Choose depth based on drift
                    if drift > 0.3:
                        depth = "full"
                    elif drift > 0.1:
                        depth = "moderate"
                    else:
                        depth = "minimal"
            except:
                depth = "moderate"  # Fallback to moderate on error

        # Apply depth filter
        if depth == "minimal":
            breadcrumbs['findings'] = breadcrumbs.get('findings', [])[:5]
            breadcrumbs['unknowns'] = breadcrumbs.get('unknowns', [])[:5]
            breadcrumbs['goals'] = [g for g in breadcrumbs.get('goals', []) if 'current' in str(g).lower()][:1]
            breadcrumbs['reference_docs'] = breadcrumbs.get('reference_docs', [])[:3]
        elif depth == "moderate":
            breadcrumbs['findings'] = breadcrumbs.get('findings', [])[:10]
            breadcrumbs['unknowns'] = breadcrumbs.get('unknowns', [])[:10]
            breadcrumbs['goals'] = breadcrumbs.get('goals', [])[:5]
            breadcrumbs['reference_docs'] = breadcrumbs.get('reference_docs', [])[:5]
        # depth == "full": no filtering

        return breadcrumbs

    def _get_latest_impact_score(self, session_id: str) -> float:
        """Get impact score from latest CASCADE assessment (PREFLIGHT/CHECK/POSTFLIGHT)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT impact FROM reflexes
            WHERE session_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (session_id,))
        row = cursor.fetchone()
        return row['impact'] if row and row['impact'] is not None else 0.5  # Default: moderate impact

    def log_finding(
        self,
        project_id: str,
        session_id: str,
        finding: str,
        goal_id: Optional[str] = None,
        subtask_id: Optional[str] = None,
        subject: Optional[str] = None,
        impact: Optional[float] = None
    ) -> str:
        """Log a project finding (delegates to BreadcrumbRepository)"""
        # Auto-derive impact from latest CASCADE if not provided
        if impact is None:
            impact = self._get_latest_impact_score(session_id)

        return self.breadcrumbs.log_finding(
            project_id, session_id, finding, goal_id, subtask_id, subject, impact
        )
    
    def log_unknown(
        self,
        project_id: str,
        session_id: str,
        unknown: str,
        goal_id: Optional[str] = None,
        subtask_id: Optional[str] = None,
        subject: Optional[str] = None,
        impact: Optional[float] = None
    ) -> str:
        """Log a project unknown (delegates to BreadcrumbRepository)"""
        # Auto-derive impact from latest CASCADE if not provided
        if impact is None:
            impact = self._get_latest_impact_score(session_id)

        return self.breadcrumbs.log_unknown(
            project_id, session_id, unknown, goal_id, subtask_id, subject, impact
        )
    
    def resolve_unknown(self, unknown_id: str, resolved_by: str):
        """Mark an unknown as resolved (delegates to BreadcrumbRepository)"""
        return self.breadcrumbs.resolve_unknown(unknown_id, resolved_by)
    
    def log_dead_end(
        self,
        project_id: str,
        session_id: str,
        approach: str,
        why_failed: str,
        goal_id: Optional[str] = None,
        subtask_id: Optional[str] = None,
        subject: Optional[str] = None,
        impact: Optional[float] = None
    ) -> str:
        """Log a project dead end (delegates to BreadcrumbRepository)

        Args:
            impact: Impact score 0.0-1.0 (importance). If None, auto-derives from latest CASCADE.
        """
        # Auto-derive impact from latest CASCADE if not provided
        if impact is None:
            impact = self._get_latest_impact_score(session_id)

        return self.breadcrumbs.log_dead_end(project_id, session_id, approach,
                                             why_failed, goal_id, subtask_id, subject, impact)
    
    def add_reference_doc(
        self,
        project_id: str,
        doc_path: str,
        doc_type: Optional[str] = None,
        description: Optional[str] = None
    ) -> str:
        """Add a reference document to project (delegates to BreadcrumbRepository)"""
        return self.breadcrumbs.add_reference_doc(project_id, doc_path, doc_type, description)
    
    def get_project_findings(self, project_id: str, limit: Optional[int] = None, subject: Optional[str] = None) -> List[Dict]:
        """Get all findings for a project (delegates to BreadcrumbRepository)"""
        return self.breadcrumbs.get_project_findings(project_id, limit, subject)
    
    def get_project_unknowns(self, project_id: str, resolved: Optional[bool] = None, subject: Optional[str] = None) -> List[Dict]:
        """Get unknowns for a project (delegates to BreadcrumbRepository)"""
        return self.breadcrumbs.get_project_unknowns(project_id, resolved, subject)
    
    def get_project_dead_ends(self, project_id: str, limit: Optional[int] = None, subject: Optional[str] = None) -> List[Dict]:
        """Get all dead ends for a project (delegates to BreadcrumbRepository)"""
        return self.breadcrumbs.get_project_dead_ends(project_id, limit, subject)
    
    def get_project_reference_docs(self, project_id: str) -> List[Dict]:
        """Get all reference docs for a project (delegates to BreadcrumbRepository)"""
        return self.breadcrumbs.get_project_reference_docs(project_id)

    def add_epistemic_source(
        self,
        project_id: str,
        source_type: str,
        title: str,
        session_id: Optional[str] = None,
        source_url: Optional[str] = None,
        description: Optional[str] = None,
        confidence: float = 0.5,
        epistemic_layer: Optional[str] = None,
        supports_vectors: Optional[Dict[str, float]] = None,
        related_findings: Optional[List[str]] = None,
        discovered_by_ai: Optional[str] = None,
        source_metadata: Optional[Dict] = None
    ) -> str:
        """Add an epistemic source to ground project knowledge
        
        Args:
            project_id: Project identifier
            source_type: Type of source ('url', 'doc', 'code_ref', 'paper', 'api_doc', 'git_commit', 'chat_transcript', 'epistemic_snapshot')
            title: Source title
            session_id: Optional session that discovered this source
            source_url: Optional URL or path
            description: Optional description
            confidence: Confidence in this source (0.0-1.0, default 0.5)
            epistemic_layer: Optional layer ('noetic', 'epistemic', 'action')
            supports_vectors: Optional dict of epistemic vectors this source supports
            related_findings: Optional list of finding IDs
            discovered_by_ai: Optional AI identifier
            source_metadata: Optional metadata dict
            
        Returns:
            source_id: UUID string
        """
        source_id = str(uuid.uuid4())
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO epistemic_sources (
                id, project_id, session_id,
                source_type, source_url, title, description,
                confidence, epistemic_layer,
                supports_vectors, related_findings,
                discovered_by_ai, discovered_at,
                source_metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            source_id, project_id, session_id,
            source_type, source_url, title, description,
            confidence, epistemic_layer,
            json.dumps(supports_vectors) if supports_vectors else None,
            json.dumps(related_findings) if related_findings else None,
            discovered_by_ai, datetime.now(),
            json.dumps(source_metadata) if source_metadata else None
        ))
        
        self.conn.commit()
        logger.info(f"📚 Epistemic source added: {title}")
        
        return source_id
    
    def get_epistemic_sources(
        self,
        project_id: str,
        session_id: Optional[str] = None,
        source_type: Optional[str] = None,
        min_confidence: float = 0.0,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Get epistemic sources for a project
        
        Args:
            project_id: Project identifier
            session_id: Optional filter by session
            source_type: Optional filter by type
            min_confidence: Minimum confidence threshold (default 0.0)
            limit: Optional limit on results
            
        Returns:
            List of source dictionaries
        """
        cursor = self.conn.cursor()
        
        query = """
            SELECT * FROM epistemic_sources
            WHERE project_id = ? AND confidence >= ?
        """
        params = [project_id, min_confidence]
        
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        
        if source_type:
            query += " AND source_type = ?"
            params.append(source_type)
        
        query += " ORDER BY confidence DESC, discovered_at DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            row_dict = dict(row)
            # Parse JSON fields
            if row_dict.get('supports_vectors'):
                row_dict['supports_vectors'] = json.loads(row_dict['supports_vectors'])
            if row_dict.get('related_findings'):
                row_dict['related_findings'] = json.loads(row_dict['related_findings'])
            if row_dict.get('source_metadata'):
                row_dict['source_metadata'] = json.loads(row_dict['source_metadata'])
            results.append(row_dict)
        
        return results

    def log_mistake(
        self,
        session_id: str,
        mistake: str,
        why_wrong: str,
        cost_estimate: Optional[str] = None,
        root_cause_vector: Optional[str] = None,
        prevention: Optional[str] = None,
        goal_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> str:
        """Log a mistake for learning (delegates to BreadcrumbRepository)

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
        return self.breadcrumbs.log_mistake(session_id, mistake, why_wrong,
                                           cost_estimate, root_cause_vector, prevention, goal_id, project_id)
    
    def get_mistakes(
        self,
        session_id: Optional[str] = None,
        goal_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """Retrieve logged mistakes (delegates to BreadcrumbRepository)

        Args:
            session_id: Optional filter by session
            goal_id: Optional filter by goal
            limit: Maximum number of results

        Returns:
            List of mistake dictionaries
        """
        return self.breadcrumbs.get_mistakes(session_id, goal_id, limit)

    def log_token_saving(
        self,
        session_id: str,
        saving_type: str,
        tokens_saved: int,
        evidence: str
    ) -> str:
        """Log a token saving event
        
        Args:
            session_id: Session identifier
            saving_type: Type of saving ('doc_awareness', 'finding_reuse', 'mistake_prevention', 'handoff_efficiency')
            tokens_saved: Estimated tokens saved
            evidence: What was avoided/reused
            
        Returns:
            saving_id: UUID string
        """
        saving_id = str(uuid.uuid4())
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO token_savings (
                id, session_id, saving_type, tokens_saved, evidence
            ) VALUES (?, ?, ?, ?, ?)
        """, (saving_id, session_id, saving_type, tokens_saved, evidence))
        
        self.conn.commit()
        logger.info(f"💰 Token saving logged: {tokens_saved} tokens ({saving_type})")
        
        return saving_id

    def get_session_token_savings(self, session_id: str) -> Dict:
        """Get token savings summary for a session
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with total_tokens_saved, cost_saved_usd, and breakdown by type
        """
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT saving_type, SUM(tokens_saved) as total, COUNT(*) as count
            FROM token_savings
            WHERE session_id = ?
            GROUP BY saving_type
        """, (session_id,))
        
        breakdown = {}
        total = 0
        for row in cursor.fetchall():
            saving_type = row[0]
            tokens = row[1]
            count = row[2]
            breakdown[saving_type] = {'tokens': tokens, 'count': count}
            total += tokens
        
        return {
            'total_tokens_saved': total,
            'cost_saved_usd': round(total * 0.00003, 4),
            'breakdown': breakdown
        }

    def get_workspace_overview(self) -> Dict[str, Any]:
        """Get workspace overview (delegates to WorkspaceRepository)"""
        return self.workspace.get_workspace_overview()
    
    def _get_workspace_stats(self) -> Dict[str, Any]:
        """Get workspace stats (delegates to WorkspaceRepository)"""
        return self.workspace._get_workspace_aggregate_stats()

    def close(self):
        """Close database connection and all repositories"""
        if hasattr(self, '_tasks') and self._tasks is not None:
            self._tasks.close()
        if hasattr(self, '_core_goals') and self._core_goals is not None:
            self._core_goals.close()
        self.conn.commit()
        self.conn.close()



if __name__ == "__main__":
    # Test the database
    logger.info("🧪 Testing Session Database...")
    db = SessionDatabase()
    db.close()
    logger.info("✅ Session Database ready")

    def log_command_usage(
        self,
        command_name: str,
        session_id: Optional[str] = None,
        execution_time_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        """Log CLI command usage for telemetry and legacy detection
        
        Args:
            command_name: Name of command executed (e.g., "goals-create")
            session_id: Optional session ID for context
            execution_time_ms: Execution time in milliseconds
            success: Whether command succeeded
            error_message: Error message if failed
            
        Returns:
            Usage log ID
        """
        import uuid
        import time
        
        usage_id = str(uuid.uuid4())
        timestamp = time.time()
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO command_usage 
            (id, command_name, session_id, timestamp, execution_time_ms, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (usage_id, command_name, session_id, timestamp, execution_time_ms, success, error_message))
        
        self.conn.commit()
        return usage_id
    
    def get_command_usage_stats(self, days: int = 30) -> Dict:
        """Get command usage stats (delegates to CommandRepository)"""
        return self.commands.get_command_usage_stats(days)
