"""
Integration tests for reflex logging system - tests the reflexes table storage
"""
import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from empirica.data.session_database import SessionDatabase


class TestReflexLoggingIntegration:
    """Test reflex logging integration via database methods"""

    @pytest.fixture
    def db(self):
        """Use default SessionDatabase"""
        db = SessionDatabase()
        yield db
        db.close()

    @pytest.fixture
    def session_id(self, db):
        """Create test session"""
        return db.create_session(
            ai_id="test-reflex-integration",
            bootstrap_level=1,
            components_loaded=5
        )

    def test_preflight_creates_reflex(self, db, session_id):
        """Test PREFLIGHT creates reflex entry correctly"""
        vectors = {
            'engagement': 0.85, 'know': 0.6, 'do': 0.7, 'context': 0.5,
            'clarity': 0.8, 'coherence': 0.75, 'signal': 0.7, 'density': 0.6,
            'state': 0.4, 'change': 0.5, 'completion': 0.3, 'impact': 0.6,
            'uncertainty': 0.65
        }

        row_id = db.log_preflight_assessment(
            session_id=session_id,
            cascade_id=None,
            prompt_summary="Test PREFLIGHT",
            vectors=vectors,
            uncertainty_notes="Test"
        )

        assert row_id is not None

        # Verify in reflexes table (new schema)
        cursor = db.conn.cursor()
        cursor.execute(
            "SELECT know, do, uncertainty, phase FROM reflexes WHERE id = ?",
            (row_id,)
        )
        row = cursor.fetchone()
        assert row[0] == 0.6   # know
        assert row[1] == 0.7   # do
        assert row[2] == 0.65  # uncertainty
        assert row[3] == "PREFLIGHT"

    def test_postflight_creates_reflex(self, db, session_id):
        """Test POSTFLIGHT creates reflex with calibration"""
        vectors = {
            'engagement': 0.9, 'know': 0.85, 'do': 0.8, 'context': 0.9,
            'clarity': 0.9, 'coherence': 0.85, 'signal': 0.8, 'density': 0.4,
            'state': 0.85, 'change': 0.8, 'completion': 0.9, 'impact': 0.85,
            'uncertainty': 0.25
        }

        row_id = db.log_postflight_assessment(
            session_id=session_id,
            cascade_id=None,
            task_summary="Test completed",
            vectors=vectors,
            postflight_confidence=0.85,
            calibration_accuracy="well_calibrated",
            learning_notes="Test learning"
        )

        assert row_id is not None

        cursor = db.conn.cursor()
        cursor.execute(
            "SELECT know, uncertainty, phase FROM reflexes WHERE id = ?",
            (row_id,)
        )
        row = cursor.fetchone()
        assert row[0] == 0.85  # know
        assert row[1] == 0.25  # uncertainty
        assert row[2] == "POSTFLIGHT"

    def test_check_phase_creates_reflex(self, db, session_id):
        """Test CHECK phase logging"""
        vectors = {
            'engagement': 0.85, 'know': 0.7, 'do': 0.75, 'context': 0.65,
            'clarity': 0.8, 'coherence': 0.8, 'signal': 0.75, 'density': 0.5,
            'state': 0.7, 'change': 0.6, 'completion': 0.5, 'impact': 0.7,
            'uncertainty': 0.4
        }

        row_id = db.log_check_phase_assessment(
            session_id=session_id,
            cascade_id=None,
            investigation_cycle=1,
            confidence=0.85,
            decision="proceed",
            gaps=["none"],
            next_targets=[],
            notes="Ready to proceed",
            vectors=vectors
        )

        assert row_id is not None

        cursor = db.conn.cursor()
        cursor.execute(
            "SELECT phase, round FROM reflexes WHERE id = ?",
            (row_id,)
        )
        row = cursor.fetchone()
        assert row[0] == "CHECK"
        assert row[1] == 1  # investigation_cycle becomes round

    def test_reflexes_table_schema(self, db):
        """Verify reflexes table has required columns"""
        cursor = db.conn.cursor()

        cursor.execute("PRAGMA table_info(reflexes)")
        columns = [row[1] for row in cursor.fetchall()]

        # Check essential columns exist
        assert "session_id" in columns
        assert "phase" in columns
        assert "know" in columns
        assert "uncertainty" in columns
        assert "engagement" in columns
        assert "reflex_data" in columns

    def test_session_creation(self, db):
        """Test session creation"""
        session_id = db.create_session(
            ai_id="test-session",
            bootstrap_level=2,
            components_loaded=10
        )

        assert session_id is not None

        cursor = db.conn.cursor()
        cursor.execute(
            "SELECT ai_id, bootstrap_level FROM sessions WHERE session_id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        assert row[0] == "test-session"
        # bootstrap_level may be stored as string or int depending on schema
        assert str(row[1]) == "2"

    def test_store_vectors_returns_id(self, db, session_id):
        """Verify store_vectors returns row ID"""
        vectors = {
            'engagement': 0.8, 'know': 0.6, 'do': 0.7, 'context': 0.5,
            'clarity': 0.75, 'coherence': 0.7, 'signal': 0.65, 'density': 0.55,
            'state': 0.5, 'change': 0.5, 'completion': 0.4, 'impact': 0.6,
            'uncertainty': 0.6
        }

        row_id = db.store_vectors(
            session_id=session_id,
            phase="PREFLIGHT",
            vectors=vectors
        )

        assert row_id is not None
        assert isinstance(row_id, int)
        assert row_id > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
