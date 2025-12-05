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
        
        
        # Table 11: cascade_metadata (Enhanced Cascade Workflow - MCP Integration)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cascade_metadata (
                metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
                cascade_id TEXT NOT NULL,
                metadata_key TEXT NOT NULL,
                metadata_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (cascade_id) REFERENCES cascades(cascade_id)
            )
        """)
        
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

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_ai ON sessions(ai_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cascades_session ON cascades(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cascades_confidence ON cascades(final_confidence)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_divergence_cascade ON divergence_tracking(cascade_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_beliefs_cascade ON bayesian_beliefs(cascade_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tools_cascade ON investigation_tools(cascade_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cascade_metadata_lookup ON cascade_metadata(cascade_id, metadata_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_session ON epistemic_snapshots(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_ai ON epistemic_snapshots(ai_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_cascade ON epistemic_snapshots(cascade_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_created ON epistemic_snapshots(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reflexes_session ON reflexes(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reflexes_phase ON reflexes(phase)")

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
            
            # Calculate confidence scores (weighted per Empirica v2.0)
            foundation_confidence = (
                vectors.get('know', 0.5) * 0.4 +
                vectors.get('do', 0.5) * 0.3 +
                vectors.get('context', 0.5) * 0.3
            )
            comprehension_confidence = (
                vectors.get('clarity', 0.5) * 0.3 +
                vectors.get('coherence', 0.5) * 0.3 +
                vectors.get('signal', 0.5) * 0.2 +
                (1.0 - vectors.get('density', 0.5)) * 0.2
            )
            execution_confidence = sum([
                vectors.get('state', 0.5),
                vectors.get('change', 0.5),
                vectors.get('completion', 0.5),
                vectors.get('impact', 0.5)
            ]) / 4.0
            
            overall_confidence = (
                foundation_confidence * 0.35 +
                comprehension_confidence * 0.25 +
                execution_confidence * 0.25 +
                vectors.get('engagement', 0.5) * 0.15
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
        
        # Get PREFLIGHT/POSTFLIGHT from cascade_metadata
        cursor.execute("""
            SELECT cm.metadata_key, cm.metadata_value, c.cascade_id, c.task
            FROM cascade_metadata cm
            JOIN cascades c ON cm.cascade_id = c.cascade_id
            WHERE c.session_id = ?
            AND cm.metadata_key IN ('preflight_vectors', 'postflight_vectors')
            ORDER BY c.started_at
        """, (session_id,))
        
        assessments = {}
        cascade_tasks = {}
        for row in cursor.fetchall():
            key, value, cascade_id, task = row
            assessments[key] = json.loads(value)
            cascade_tasks[cascade_id] = task
        
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

    def close(self):
        """Close database connection"""
        self.conn.close()



if __name__ == "__main__":
    # Test the database
    logger.info("🧪 Testing Session Database...")
    db = SessionDatabase()
    db.close()
    logger.info("✅ Session Database ready")
