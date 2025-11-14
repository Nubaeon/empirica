"""
Integration tests for reflex logging system - simplified for database testing
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
    
    def test_preflight_creates_assessment(self, db, session_id):
        """Test PREFLIGHT creates assessment correctly"""
        vectors = {
            'engagement': 0.85, 'know': 0.6, 'do': 0.7, 'context': 0.5,
            'clarity': 0.8, 'coherence': 0.75, 'signal': 0.7, 'density': 0.6,
            'state': 0.4, 'change': 0.5, 'completion': 0.3, 'impact': 0.6,
            'uncertainty': 0.65
        }
        
        assessment_id = db.log_preflight_assessment(
            session_id=session_id,
            cascade_id=None,
            prompt_summary="Test PREFLIGHT",
            vectors=vectors,
            uncertainty_notes="Test"
        )
        
        assert assessment_id is not None
        
        # Verify in database
        cursor = db.conn.cursor()
        cursor.execute("SELECT know, do, uncertainty FROM preflight_assessments WHERE assessment_id = ?", (assessment_id,))
        row = cursor.fetchone()
        assert row[0] == 0.6
        assert row[1] == 0.7
        assert row[2] == 0.65
    
    def test_postflight_creates_assessment(self, db, session_id):
        """Test POSTFLIGHT creates assessment with calibration"""
        vectors = {
            'engagement': 0.9, 'know': 0.85, 'do': 0.8, 'context': 0.9,
            'clarity': 0.9, 'coherence': 0.85, 'signal': 0.8, 'density': 0.4,
            'state': 0.85, 'change': 0.8, 'completion': 0.9, 'impact': 0.85,
            'uncertainty': 0.25
        }
        
        # Correct signature: postflight_confidence and calibration_accuracy required
        assessment_id = db.log_postflight_assessment(
            session_id=session_id,
            cascade_id=None,
            task_summary="Test completed",
            vectors=vectors,
            postflight_confidence=0.85,
            calibration_accuracy="well_calibrated",
            learning_notes="Test learning"
        )
        
        assert assessment_id is not None
        
        cursor = db.conn.cursor()
        cursor.execute("SELECT know, uncertainty, calibration_accuracy FROM postflight_assessments WHERE assessment_id = ?", (assessment_id,))
        row = cursor.fetchone()
        assert row[0] == 0.85
        assert row[1] == 0.25
        assert row[2] == "well_calibrated"
    
    def test_check_phase_assessment(self, db, session_id):
        """Test CHECK phase logging"""
        vectors = {
            'engagement': 0.85, 'know': 0.7, 'do': 0.75, 'context': 0.65,
            'clarity': 0.8, 'coherence': 0.8, 'signal': 0.75, 'density': 0.5,
            'state': 0.7, 'change': 0.6, 'completion': 0.5, 'impact': 0.7,
            'uncertainty': 0.4
        }
        
        # Correct signature: investigation_cycle, confidence, decision, gaps, next_targets, notes, vectors
        check_id = db.log_check_phase_assessment(
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
        
        assert check_id is not None
        
        cursor = db.conn.cursor()
        cursor.execute("SELECT decision, confidence FROM check_phase_assessments WHERE check_id = ?", (check_id,))
        row = cursor.fetchone()
        assert row[0] == "proceed"
        assert row[1] == 0.85
    
    def test_database_schema_has_reflex_log_path(self, db):
        """Verify reflex_log_path column exists"""
        cursor = db.conn.cursor()
        
        cursor.execute("PRAGMA table_info(preflight_assessments)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "reflex_log_path" in columns
        
        cursor.execute("PRAGMA table_info(postflight_assessments)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "reflex_log_path" in columns
    
    def test_session_creation(self, db):
        """Test session creation"""
        session_id = db.create_session(
            ai_id="test-session",
            bootstrap_level=2,
            components_loaded=10
        )
        
        assert session_id is not None
        
        cursor = db.conn.cursor()
        cursor.execute("SELECT ai_id, bootstrap_level FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        assert row[0] == "test-session"
        assert row[1] == 2
    
    def test_no_cursor_attribute_error(self, db, session_id):
        """Verify db.cursor AttributeError bug is fixed"""
        vectors = {
            'engagement': 0.8, 'know': 0.6, 'do': 0.7, 'context': 0.5,
            'clarity': 0.75, 'coherence': 0.7, 'signal': 0.65, 'density': 0.55,
            'state': 0.5, 'change': 0.5, 'completion': 0.4, 'impact': 0.6,
            'uncertainty': 0.6
        }
        
        try:
            assessment_id = db.log_preflight_assessment(
                session_id=session_id,
                cascade_id=None,
                prompt_summary="Test cursor fix",
                vectors=vectors
            )
            assert assessment_id is not None
        except AttributeError as e:
            if "'SessionDatabase' object has no attribute 'cursor'" in str(e):
                pytest.fail("db.cursor bug not fixed!")
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
