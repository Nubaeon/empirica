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

Location: .empirica/sessions/sessions.db
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
            # Default to .empirica/sessions/sessions.db (in current working directory)
            base_dir = Path.cwd() / '.empirica' / 'sessions'
            base_dir.mkdir(parents=True, exist_ok=True)
            db_path = base_dir / 'sessions.db'
        
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
        
        # Migration: Add reflex_log_path to existing tables (for databases created before this update)
        try:
            cursor.execute("ALTER TABLE epistemic_assessments ADD COLUMN reflex_log_path TEXT")
            logger.info("✓ Migration: Added reflex_log_path column to epistemic_assessments")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE preflight_assessments ADD COLUMN reflex_log_path TEXT")
            logger.info("✓ Migration: Added reflex_log_path column to preflight_assessments")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE postflight_assessments ADD COLUMN reflex_log_path TEXT")
            logger.info("✓ Migration: Added reflex_log_path column to postflight_assessments")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Table 3: epistemic_assessments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS epistemic_assessments (
                assessment_id TEXT PRIMARY KEY,
                cascade_id TEXT NOT NULL,
                phase TEXT NOT NULL,
                
                engagement REAL NOT NULL,
                engagement_gate_passed BOOLEAN,
                
                know REAL NOT NULL,
                know_rationale TEXT,
                do REAL NOT NULL,
                do_rationale TEXT,
                context REAL NOT NULL,
                context_rationale TEXT,
                foundation_confidence REAL,
                
                clarity REAL NOT NULL,
                clarity_rationale TEXT,
                coherence REAL NOT NULL,
                coherence_rationale TEXT,
                signal REAL NOT NULL,
                signal_rationale TEXT,
                density REAL NOT NULL,
                density_rationale TEXT,
                comprehension_confidence REAL,
                
                state REAL NOT NULL,
                state_rationale TEXT,
                change REAL NOT NULL,
                change_rationale TEXT,
                completion REAL NOT NULL,
                completion_rationale TEXT,
                impact REAL NOT NULL,
                impact_rationale TEXT,
                execution_confidence REAL,
                
                uncertainty REAL NOT NULL,
                uncertainty_rationale TEXT,
                uncertainty_evidence TEXT,
                
                overall_confidence REAL NOT NULL,
                recommended_action TEXT NOT NULL,
                
                reflex_log_path TEXT,  -- Link to reflex frame JSON file
                
                assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (cascade_id) REFERENCES cascades(cascade_id)
            )
        """)
        
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
        
        # Table 8: preflight_assessments (NEW 13-Vector System v2.0)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preflight_assessments (
                assessment_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                cascade_id TEXT,
                prompt_summary TEXT NOT NULL,
                
                engagement REAL NOT NULL,
                know REAL NOT NULL,
                do REAL NOT NULL,
                context REAL NOT NULL,
                clarity REAL NOT NULL,
                coherence REAL NOT NULL,
                signal REAL NOT NULL,
                density REAL NOT NULL,
                state REAL NOT NULL,
                change REAL NOT NULL,
                completion REAL NOT NULL,
                impact REAL NOT NULL,
                uncertainty REAL NOT NULL,
                
                initial_uncertainty_notes TEXT,
                vectors_json TEXT,
                reflex_log_path TEXT,
                assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                FOREIGN KEY (cascade_id) REFERENCES cascades(cascade_id)
            )
        """)
        
        # Table 9: check_phase_assessments (Enhanced Cascade Workflow v1.1)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS check_phase_assessments (
                check_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                cascade_id TEXT,
                investigation_cycle INTEGER NOT NULL,
                
                confidence REAL NOT NULL,
                decision TEXT NOT NULL,
                gaps_identified TEXT,
                next_investigation_targets TEXT,
                self_assessment_notes TEXT,
                
                assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                FOREIGN KEY (cascade_id) REFERENCES cascades(cascade_id)
            )
        """)
        
        # Table 10: postflight_assessments (NEW 13-Vector System v2.0)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS postflight_assessments (
                assessment_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                cascade_id TEXT,
                task_summary TEXT NOT NULL,
                
                engagement REAL NOT NULL,
                know REAL NOT NULL,
                do REAL NOT NULL,
                context REAL NOT NULL,
                clarity REAL NOT NULL,
                coherence REAL NOT NULL,
                signal REAL NOT NULL,
                density REAL NOT NULL,
                state REAL NOT NULL,
                change REAL NOT NULL,
                completion REAL NOT NULL,
                impact REAL NOT NULL,
                uncertainty REAL NOT NULL,
                
                postflight_actual_confidence REAL NOT NULL,
                calibration_accuracy TEXT NOT NULL,
                learning_notes TEXT,
                vectors_json TEXT,
                reflex_log_path TEXT,
                
                assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (session_id) REFERENCES sessions(session_id),
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

        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_ai ON sessions(ai_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions(start_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cascades_session ON cascades(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cascades_confidence ON cascades(final_confidence)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_assessments_cascade ON epistemic_assessments(cascade_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_divergence_cascade ON divergence_tracking(cascade_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_beliefs_cascade ON bayesian_beliefs(cascade_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tools_cascade ON investigation_tools(cascade_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cascade_metadata_lookup ON cascade_metadata(cascade_id, metadata_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_session ON epistemic_snapshots(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_ai ON epistemic_snapshots(ai_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_cascade ON epistemic_snapshots(cascade_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_created ON epistemic_snapshots(created_at)")

        self.conn.commit()
    
    def create_session(self, ai_id: str, bootstrap_level: int, components_loaded: int, 
                      user_id: Optional[str] = None) -> str:
        """Create new session, return session_id"""
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
        """Store 13D epistemic assessment (12 vectors + UNCERTAINTY)"""
        if not CANONICAL_AVAILABLE:
            logger.warning("[DB] Canonical structures not available, skipping epistemic assessment")
            return
        
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO epistemic_assessments (
                assessment_id, cascade_id, phase,
                engagement, engagement_gate_passed,
                know, know_rationale, do, do_rationale, context, context_rationale,
                foundation_confidence,
                clarity, clarity_rationale, coherence, coherence_rationale,
                signal, signal_rationale, density, density_rationale,
                comprehension_confidence,
                state, state_rationale, change, change_rationale,
                completion, completion_rationale, impact, impact_rationale,
                execution_confidence,
                uncertainty, uncertainty_rationale, uncertainty_evidence,
                overall_confidence, recommended_action
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assessment.assessment_id, cascade_id, phase,
            assessment.engagement.score, assessment.engagement_gate_passed,
            assessment.know.score, assessment.know.rationale,
            assessment.do.score, assessment.do.rationale,
            assessment.context.score, assessment.context.rationale,
            assessment.foundation_confidence,
            assessment.clarity.score, assessment.clarity.rationale,
            assessment.coherence.score, assessment.coherence.rationale,
            assessment.signal.score, assessment.signal.rationale,
            assessment.density.score, assessment.density.rationale,
            assessment.comprehension_confidence,
            assessment.state.score, assessment.state.rationale,
            assessment.change.score, assessment.change.rationale,
            assessment.completion.score, assessment.completion.rationale,
            assessment.impact.score, assessment.impact.rationale,
            assessment.execution_confidence,
            assessment.uncertainty.score, assessment.uncertainty.rationale,
            assessment.uncertainty.evidence if hasattr(assessment.uncertainty, 'evidence') else None,
            assessment.overall_confidence, assessment.recommended_action.value
        ))
        
        self.conn.commit()
    
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
        """Get all assessments for a cascade"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM epistemic_assessments WHERE cascade_id = ? ORDER BY assessed_at
        """, (cascade_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def log_preflight_assessment(self, session_id: str, cascade_id: Optional[str],
                                 prompt_summary: str, vectors: Dict[str, float],
                                 uncertainty_notes: str = "") -> str:
        """Store preflight epistemic assessment (NEW 13-vector system)
        
        Vectors: engagement, know, do, context, clarity, coherence, signal, density,
                 state, change, completion, impact, uncertainty
        """
        assessment_id = str(uuid.uuid4())
        
        cursor = self.conn.cursor()
        
        # Store in new format with JSON for flexibility
        cursor.execute("""
            INSERT INTO preflight_assessments (
                assessment_id, session_id, cascade_id, prompt_summary,
                engagement, know, do, context,
                clarity, coherence, signal, density,
                state, change, completion, impact,
                uncertainty,
                initial_uncertainty_notes,
                vectors_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assessment_id, session_id, cascade_id, prompt_summary,
            float(vectors.get('engagement', 0.5)) if not isinstance(vectors.get('engagement', 0.5), dict) else 0.5,
            float(vectors.get('know', 0.5)) if not isinstance(vectors.get('know', 0.5), dict) else 0.5,
            float(vectors.get('do', 0.5)) if not isinstance(vectors.get('do', 0.5), dict) else 0.5,
            float(vectors.get('context', 0.5)) if not isinstance(vectors.get('context', 0.5), dict) else 0.5,
            float(vectors.get('clarity', 0.5)) if not isinstance(vectors.get('clarity', 0.5), dict) else 0.5,
            float(vectors.get('coherence', 0.5)) if not isinstance(vectors.get('coherence', 0.5), dict) else 0.5,
            float(vectors.get('signal', 0.5)) if not isinstance(vectors.get('signal', 0.5), dict) else 0.5,
            float(vectors.get('density', 0.5)) if not isinstance(vectors.get('density', 0.5), dict) else 0.5,
            float(vectors.get('state', 0.5)) if not isinstance(vectors.get('state', 0.5), dict) else 0.5,
            float(vectors.get('change', 0.5)) if not isinstance(vectors.get('change', 0.5), dict) else 0.5,
            float(vectors.get('completion', 0.5)) if not isinstance(vectors.get('completion', 0.5), dict) else 0.5,
            float(vectors.get('impact', 0.5)) if not isinstance(vectors.get('impact', 0.5), dict) else 0.5,
            float(vectors.get('uncertainty', 0.5)) if not isinstance(vectors.get('uncertainty', 0.5), dict) else 0.5,
            uncertainty_notes,
            json.dumps(vectors)
        ))
        
        self.conn.commit()
        
        # Export to reflex logs for dashboard visualization
        try:
            self._export_to_reflex_logs(
                session_id=session_id,
                phase="preflight",
                assessment_data={
                    "assessment_id": assessment_id,
                    "cascade_id": cascade_id,
                    "vectors": vectors,
                    "prompt_summary": prompt_summary,
                    "uncertainty_notes": uncertainty_notes
                }
            )
        except Exception:
            pass  # Silent fail - not critical
        
        return assessment_id
    
    def log_check_phase_assessment(self, session_id: str, cascade_id: Optional[str],
                                   investigation_cycle: int, confidence: float,
                                   decision: str, gaps: List[str],
                                   next_targets: List[str],
                                   notes: str = "",
                                   vectors: Optional[Dict[str, float]] = None) -> str:
        """Store check phase self-assessment with NEW 13-vector system support"""
        check_id = str(uuid.uuid4())
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO check_phase_assessments (
                check_id, session_id, cascade_id, investigation_cycle,
                confidence, decision, gaps_identified, next_investigation_targets,
                self_assessment_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            check_id, session_id, cascade_id, investigation_cycle,
            confidence, decision, json.dumps(gaps), json.dumps(next_targets), notes
        ))
        
        self.conn.commit()
        
        # Export to reflex logs for dashboard visualization
        if vectors:
            try:
                self._export_to_reflex_logs(
                    session_id=session_id,
                    phase="check",
                    assessment_data={
                        "assessment_id": check_id,
                        "cascade_id": cascade_id,
                        "vectors": vectors,
                        "task_summary": f"CHECK cycle {investigation_cycle}: {decision}",
                        "confidence": confidence,
                        "decision": decision,
                        "gaps_identified": gaps,
                        "next_targets": next_targets,
                        "notes": notes
                    }
                )
            except Exception:
                pass  # Silent fail - not critical
        
        return check_id
    
    def log_postflight_assessment(self, session_id: str, cascade_id: Optional[str],
                                  task_summary: str, vectors: Dict[str, float],
                                  postflight_confidence: float,
                                  calibration_accuracy: str,
                                  learning_notes: str = "") -> str:
        """Store postflight epistemic assessment with calibration validation (NEW 13-vector system)"""
        assessment_id = str(uuid.uuid4())
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO postflight_assessments (
                assessment_id, session_id, cascade_id, task_summary,
                engagement, know, do, context,
                clarity, coherence, signal, density,
                state, change, completion, impact,
                uncertainty,
                postflight_actual_confidence, calibration_accuracy, learning_notes,
                vectors_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assessment_id, session_id, cascade_id, task_summary,
            vectors.get('engagement', 0.5),
            vectors.get('know', 0.5),
            vectors.get('do', 0.5),
            vectors.get('context', 0.5),
            vectors.get('clarity', 0.5),
            vectors.get('coherence', 0.5),
            vectors.get('signal', 0.5),
            vectors.get('density', 0.5),
            vectors.get('state', 0.5),
            vectors.get('change', 0.5),
            vectors.get('completion', 0.5),
            vectors.get('impact', 0.5),
            vectors.get('uncertainty', 0.5),
            postflight_confidence, calibration_accuracy, learning_notes,
            json.dumps(vectors)
        ))
        
        self.conn.commit()
        
        # Export to reflex logs for dashboard visualization
        try:
            self._export_to_reflex_logs(
                session_id=session_id,
                phase="postflight",
                assessment_data={
                    "assessment_id": assessment_id,
                    "cascade_id": cascade_id,
                    "vectors": vectors,
                    "task_summary": task_summary,
                    "postflight_confidence": postflight_confidence,
                    "calibration_accuracy": calibration_accuracy,
                    "learning_notes": learning_notes
                }
            )
        except Exception:
            pass  # Silent fail - not critical
        
        return assessment_id
    
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
        """Get most recent preflight assessment for session"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM preflight_assessments 
            WHERE session_id = ? 
            ORDER BY assessed_at DESC 
            LIMIT 1
        """, (session_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_check_phase_assessments(self, session_id: str) -> List[Dict]:
        """Get all check phase assessments for session"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM check_phase_assessments 
            WHERE session_id = ? 
            ORDER BY assessed_at
        """, (session_id,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_postflight_assessment(self, session_id: str) -> Optional[Dict]:
        """Get most recent postflight assessment for session"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM postflight_assessments 
            WHERE session_id = ? 
            ORDER BY assessed_at DESC 
            LIMIT 1
        """, (session_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
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
        
        # Get latest assessment for session
        query = """
            SELECT 
                ea.assessment_id,
                ea.phase,
                ea.vectors_json,
                ea.created_at
            FROM epistemic_assessments ea
            WHERE ea.session_id = ?
        """
        params = [session_id]
        
        if phase:
            query += " AND ea.phase = ?"
            params.append(phase)
        
        query += " ORDER BY ea.created_at DESC LIMIT 1"
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        
        if result:
            return {
                "checkpoint_id": result['assessment_id'],
                "vectors": json.loads(result['vectors_json']),
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
        
        cursor.execute("""
            SELECT vectors_json
            FROM epistemic_assessments
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (session_id,))
        
        result = cursor.fetchone()
        
        if result:
            return json.loads(result['vectors_json'])
        
        return None
    
    def close(self):
        """Close database connection"""
        self.conn.close()


if __name__ == "__main__":
    # Test the database
    logger.info("🧪 Testing Session Database...")
    
    db = SessionDatabase()
    
    # Create test session
    session_id = db.create_session("test_claude", bootstrap_level=2, components_loaded=30)
    logger.info(f"✅ Created session: {session_id}")
    
    # Create test cascade
    cascade_id = db.create_cascade(session_id, "Test task", {"test": True})
    logger.info(f"✅ Created cascade: {cascade_id}")
    
    # Mark phases complete
    for phase in ['think', 'uncertainty', 'investigate', 'check', 'act']:
        db.update_cascade_phase(cascade_id, phase, True)
    logger.info(f"✅ Updated cascade phases")
    
    # Complete cascade
    db.complete_cascade(cascade_id, "proceed", 0.85, 2, 5000, True, True, True)
    logger.info(f"✅ Completed cascade")
    
    # Query back
    session = db.get_session(session_id)
    logger.info(f"✅ Retrieved session: {session['ai_id']}")
    
    cascades = db.get_session_cascades(session_id)
    logger.info(f"✅ Retrieved {len(cascades)} cascades")
    
    db.close()
    logger.info("\n🎉 Session Database tests passed!")
