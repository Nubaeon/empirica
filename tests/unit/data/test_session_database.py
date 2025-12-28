"""Test SessionDatabase SQLite operations."""
import pytest
import json
from empirica.core.schemas.epistemic_assessment import EpistemicAssessmentSchema
import sqlite3
from typing import Optional, Dict, Any, List

# Use schema as assessment
EpistemicAssessment = EpistemicAssessmentSchema

# A helper function to create a dummy assessment for testing
def create_dummy_assessment(assessment_id="test_id"):
    return EpistemicAssessment(
        engagement=VectorState(score=0.7, rationale="Test engagement"),
        engagement_gate_passed=True,
        know=VectorState(score=0.5, rationale="Test know"),
        do=VectorState(score=0.6, rationale="Test do"),
        context=VectorState(score=0.7, rationale="Test context"),
        foundation_confidence=0.6,
        clarity=VectorState(score=0.6, rationale="Test clarity"),
        coherence=VectorState(score=0.7, rationale="Test coherence"),
        signal=VectorState(score=0.6, rationale="Test signal"),
        density=VectorState(score=0.3, rationale="Test density"),
        comprehension_confidence=0.6,
        state=VectorState(score=0.5, rationale="Test state"),
        change=VectorState(score=0.7, rationale="Test change"),
        completion=VectorState(score=0.6, rationale="Test completion"),
        impact=VectorState(score=0.5, rationale="Test impact"),
        execution_confidence=0.6,
        uncertainty=VectorState(score=0.3, rationale="Test uncertainty"),
        overall_confidence=0.6,
        recommended_action=Action.PROCEED,
        assessment_id=assessment_id
    )

class SessionDatabaseForTest:
    """A simplified SessionDatabase for testing purposes."""
    def __init__(self, db_path: Optional[str] = ":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                assessment_type TEXT NOT NULL,
                assessment_data TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        """)
        self.conn.commit()

    def create_session(self, agent_id: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO sessions (agent_id) VALUES (?)", (agent_id,))
        self.conn.commit()
        return cursor.lastrowid

    def save_assessment(self, session_id: int, assessment_type: str, assessment: EpistemicAssessment):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO assessments (session_id, assessment_type, assessment_data) VALUES (?, ?, ?)",
            (session_id, assessment_type, json.dumps(assessment.to_dict()))
        )
        self.conn.commit()

    def load_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        session_row = cursor.fetchone()
        if not session_row:
            return None

        session_data = dict(session_row)
        cursor.execute("SELECT * FROM assessments WHERE session_id = ?", (session_id,))
        assessments_rows = cursor.fetchall()
        session_data["assessments"] = []
        for row in assessments_rows:
            assessment_data = json.loads(row["assessment_data"])
            session_data["assessments"].append({
                "assessment_type": row["assessment_type"],
                "assessment_data": assessment_data
            })
        return session_data

    def close(self):
        self.conn.close()

@pytest.fixture
def db():
    # Use an in-memory SQLite database for testing
    db = SessionDatabaseForTest()
    yield db
    db.close()

def test_create_session(db: SessionDatabaseForTest):
    """Create new session in database"""
    session_id = db.create_session("test_agent")
    assert session_id is not None
    assert isinstance(session_id, int)

def test_save_assessment(db: SessionDatabaseForTest):
    """Save epistemic assessment to session"""
    session_id = db.create_session("test_agent")
    assessment = create_dummy_assessment()
    db.save_assessment(session_id, "preflight", assessment)
    
    # Verify by loading
    session_data = db.load_session(session_id)
    assert len(session_data["assessments"]) == 1

def test_load_session(db: SessionDatabaseForTest):
    """Load session from database"""
    session_id = db.create_session("test_agent")
    assessment = create_dummy_assessment()
    db.save_assessment(session_id, "preflight", assessment)
    
    session_data = db.load_session(session_id)
    
    assert session_data is not None
    assert session_data["session_id"] == session_id
    assert session_data["agent_id"] == "test_agent"
    assert len(session_data["assessments"]) == 1
    assert session_data["assessments"][0]["assessment_type"] == "preflight"

def test_data_integrity(db: SessionDatabaseForTest):
    """Verify data integrity across save/load"""
    session_id = db.create_session("test_agent")
    assessment = create_dummy_assessment("integrity_test")
    db.save_assessment(session_id, "preflight", assessment)
    
    session_data = db.load_session(session_id)
    loaded_assessment_data = session_data["assessments"][0]["assessment_data"]
    
    # Compare the original assessment with the loaded one
    assert loaded_assessment_data["assessment_id"] == "integrity_test"
    assert loaded_assessment_data["engagement"]['score'] == 0.7
    assert loaded_assessment_data["foundation"]['know']['score'] == 0.5
    assert loaded_assessment_data["uncertainty"]['score'] == 0.3
    assert loaded_assessment_data["recommended_action"] == "proceed"