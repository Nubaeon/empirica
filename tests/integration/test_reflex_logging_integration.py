"""
Integration tests for reflex logging system.

Tests the complete flow: MCP tool call → Database write → Reflex log creation → Database linking

These tests verify the fix for the db.cursor AttributeError bug and ensure
reflex logging works correctly for all workflow phases.
"""
import pytest
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from empirica.data.session_database import SessionDatabase
from mcp_local.empirica_mcp_server import call_tool
from mcp import types


class TestReflexLoggingIntegration:
    """Test reflex logging integration across workflow phases"""
    
    @pytest.fixture
    def db(self):
        """Create test database"""
        db_path = ".empirica/sessions/test_reflex_integration.db"
        db = SessionDatabase(db_path=db_path)
        yield db
        db.close()
        # Cleanup
        Path(db_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def session_id(self, db):
        """Create test session"""
        return db.create_session(
            ai_id="test-reflex-agent",
            bootstrap_level=1,
            components_loaded=5
        )
    
    @pytest.mark.asyncio
    async def test_preflight_creates_reflex_log(self, db, session_id):
        """Test PREFLIGHT creates reflex log and links to database"""
        
        # Submit PREFLIGHT assessment via MCP tool
        vectors = {
            'engagement': 0.85,
            'know': 0.6,
            'do': 0.7,
            'context': 0.5,
            'clarity': 0.8,
            'coherence': 0.75,
            'signal': 0.7,
            'density': 0.6,
            'state': 0.4,
            'change': 0.5,
            'completion': 0.3,
            'impact': 0.6,
            'uncertainty': 0.65
        }
        
        result = await call_tool(
            name="submit_preflight_assessment",
            arguments={
                "session_id": session_id,
                "vectors": vectors,
                "reasoning": "Test PREFLIGHT assessment"
            }
        )
        
        # Parse response
        response = json.loads(result[0].text)
        assert response.get("ok") is True, f"PREFLIGHT failed: {response}"
        
        # Check reflex_log_path is NOT an error message
        reflex_path = response.get("reflex_log_path", "")
        assert "failed" not in reflex_path.lower(), f"Reflex logging failed: {reflex_path}"
        assert "error" not in reflex_path.lower(), f"Reflex logging error: {reflex_path}"
        assert reflex_path.endswith(".json"), f"Invalid reflex path: {reflex_path}"
        
        # Verify database has reflex_log_path
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT reflex_log_path FROM preflight_assessments 
            WHERE session_id = ?
        """, (session_id,))
        row = cursor.fetchone()
        
        assert row is not None, "No PREFLIGHT assessment found in database"
        db_reflex_path = row[0]
        assert db_reflex_path is not None, "reflex_log_path is NULL in database"
        assert db_reflex_path == reflex_path, "Database path doesn't match response path"
        
        # Verify reflex log file exists
        reflex_file = Path(reflex_path)
        assert reflex_file.exists(), f"Reflex log file doesn't exist: {reflex_path}"
        
        # Verify reflex log content
        with open(reflex_file) as f:
            reflex_data = json.load(f)
        
        assert reflex_data.get("frameId", "").startswith("preflight_"), "Invalid frame ID"
        assert "epistemicVector" in reflex_data, "Missing epistemic vectors"
        assert reflex_data["epistemicVector"]["know"] == 0.6, "Vector mismatch"
        assert reflex_data["epistemicVector"]["uncertainty"] == 0.65, "Uncertainty mismatch"
    
    @pytest.mark.asyncio
    async def test_postflight_creates_reflex_log(self, db, session_id):
        """Test POSTFLIGHT creates reflex log and links to database"""
        
        # First create a PREFLIGHT (required for calibration)
        preflight_vectors = {
            'engagement': 0.8,
            'know': 0.5,
            'do': 0.6,
            'context': 0.4,
            'clarity': 0.7,
            'coherence': 0.7,
            'signal': 0.6,
            'density': 0.5,
            'state': 0.3,
            'change': 0.4,
            'completion': 0.2,
            'impact': 0.5,
            'uncertainty': 0.7
        }
        
        await call_tool(
            name="submit_preflight_assessment",
            arguments={
                "session_id": session_id,
                "vectors": preflight_vectors,
                "reasoning": "Test PREFLIGHT for calibration"
            }
        )
        
        # Now submit POSTFLIGHT
        postflight_vectors = {
            'engagement': 0.9,
            'know': 0.85,
            'do': 0.8,
            'context': 0.9,
            'clarity': 0.9,
            'coherence': 0.85,
            'signal': 0.8,
            'density': 0.4,
            'state': 0.85,
            'change': 0.8,
            'completion': 0.9,
            'impact': 0.85,
            'uncertainty': 0.25
        }
        
        result = await call_tool(
            name="submit_postflight_assessment",
            arguments={
                "session_id": session_id,
                "vectors": postflight_vectors,
                "changes_noticed": "Significant learning occurred"
            }
        )
        
        # Parse response
        response = json.loads(result[0].text)
        assert response.get("ok") is True, f"POSTFLIGHT failed: {response}"
        
        # Check reflex_log_path is NOT an error message
        reflex_path = response.get("reflex_log_path", "")
        assert "failed" not in reflex_path.lower(), f"Reflex logging failed: {reflex_path}"
        assert "error" not in reflex_path.lower(), f"Reflex logging error: {reflex_path}"
        assert reflex_path.endswith(".json"), f"Invalid reflex path: {reflex_path}"
        
        # Verify database has reflex_log_path
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT reflex_log_path FROM postflight_assessments 
            WHERE session_id = ?
        """, (session_id,))
        row = cursor.fetchone()
        
        assert row is not None, "No POSTFLIGHT assessment found in database"
        db_reflex_path = row[0]
        assert db_reflex_path is not None, "reflex_log_path is NULL in database"
        assert db_reflex_path == reflex_path, "Database path doesn't match response path"
        
        # Verify reflex log file exists
        reflex_file = Path(reflex_path)
        assert reflex_file.exists(), f"Reflex log file doesn't exist: {reflex_path}"
        
        # Verify reflex log content
        with open(reflex_file) as f:
            reflex_data = json.load(f)
        
        assert reflex_data.get("frameId", "").startswith("postflight_"), "Invalid frame ID"
        assert "epistemicVector" in reflex_data, "Missing epistemic vectors"
        assert reflex_data["epistemicVector"]["know"] == 0.85, "Vector mismatch"
        assert reflex_data["epistemicVector"]["uncertainty"] == 0.25, "Uncertainty mismatch"
        
        # Verify calibration was calculated
        assert "calibration_result" in response, "Missing calibration result"
        calibration = response["calibration_result"]
        assert "calibration" in calibration, "Missing calibration status"
        assert calibration["calibration"] == "well_calibrated", "Should be well-calibrated"
    
    @pytest.mark.asyncio
    async def test_check_phase_reflex_logging(self, db, session_id):
        """Test CHECK phase reflex logging (uses different pattern)"""
        
        # Submit CHECK assessment
        vectors = {
            'engagement': 0.85,
            'know': 0.7,
            'do': 0.75,
            'context': 0.65,
            'clarity': 0.8,
            'coherence': 0.8,
            'signal': 0.75,
            'density': 0.5,
            'state': 0.7,
            'change': 0.6,
            'completion': 0.5,
            'impact': 0.7,
            'uncertainty': 0.4
        }
        
        result = await call_tool(
            name="submit_check_assessment",
            arguments={
                "session_id": session_id,
                "vectors": vectors,
                "decision": "proceed",
                "reasoning": "Ready to proceed after investigation",
                "confidence_to_proceed": 0.85,
                "investigation_cycle": 1
            }
        )
        
        # Parse response
        response = json.loads(result[0].text)
        assert response.get("ok") is True, f"CHECK failed: {response}"
        
        # Check reflex_log_path exists (CHECK uses database method)
        reflex_path = response.get("reflex_log_path")
        if reflex_path:  # CHECK may or may not return reflex path
            assert "failed" not in reflex_path.lower(), f"Reflex logging failed: {reflex_path}"
            
            # Verify file exists
            reflex_file = Path(reflex_path)
            assert reflex_file.exists(), f"Reflex log file doesn't exist: {reflex_path}"
    
    @pytest.mark.asyncio
    async def test_reflex_log_directory_structure(self, db, session_id):
        """Test reflex logs are organized by date and AI ID"""
        
        # Submit assessment
        vectors = {
            'engagement': 0.8,
            'know': 0.6,
            'do': 0.7,
            'context': 0.5,
            'clarity': 0.75,
            'coherence': 0.7,
            'signal': 0.65,
            'density': 0.55,
            'state': 0.5,
            'change': 0.5,
            'completion': 0.4,
            'impact': 0.6,
            'uncertainty': 0.6
        }
        
        result = await call_tool(
            name="submit_preflight_assessment",
            arguments={
                "session_id": session_id,
                "vectors": vectors,
                "reasoning": "Test directory structure"
            }
        )
        
        response = json.loads(result[0].text)
        reflex_path = response.get("reflex_log_path")
        
        # Verify directory structure: .empirica_reflex_logs/YYYY-MM-DD/ai_id/session_id/
        reflex_file = Path(reflex_path)
        
        # Should be: .empirica_reflex_logs/2024-11-13/test-reflex-agent/session_id/file.json
        parts = reflex_file.parts
        assert ".empirica_reflex_logs" in parts or "empirica_reflex_logs" in parts[0], "Wrong root directory"
        
        # Check date format (YYYY-MM-DD)
        date_part = None
        for part in parts:
            if len(part) == 10 and part[4] == '-' and part[7] == '-':
                date_part = part
                break
        
        assert date_part is not None, f"No date directory found in path: {reflex_path}"
        
        # Verify date is valid
        try:
            datetime.strptime(date_part, "%Y-%m-%d")
        except ValueError:
            pytest.fail(f"Invalid date format: {date_part}")
        
        # Check AI ID directory exists
        assert "test-reflex-agent" in parts, f"AI ID not in path: {reflex_path}"
        
        # Check session ID directory exists
        assert session_id in parts, f"Session ID not in path: {reflex_path}"
    
    @pytest.mark.asyncio
    async def test_no_cursor_attribute_error(self, db, session_id):
        """Test that db.cursor AttributeError is fixed"""
        
        # This test verifies the bug fix
        # Before fix: AttributeError: 'SessionDatabase' object has no attribute 'cursor'
        # After fix: Uses db.conn.cursor() correctly
        
        vectors = {
            'engagement': 0.8,
            'know': 0.6,
            'do': 0.7,
            'context': 0.5,
            'clarity': 0.75,
            'coherence': 0.7,
            'signal': 0.65,
            'density': 0.55,
            'state': 0.5,
            'change': 0.5,
            'completion': 0.4,
            'impact': 0.6,
            'uncertainty': 0.6
        }
        
        # This should NOT raise AttributeError
        result = await call_tool(
            name="submit_preflight_assessment",
            arguments={
                "session_id": session_id,
                "vectors": vectors,
                "reasoning": "Test cursor fix"
            }
        )
        
        response = json.loads(result[0].text)
        
        # Verify no error about cursor
        reflex_path = response.get("reflex_log_path", "")
        assert "attribute 'cursor'" not in reflex_path.lower(), "db.cursor bug not fixed!"
        assert "AttributeError" not in reflex_path, "AttributeError still occurring!"
        
        # Should have valid path
        assert reflex_path.endswith(".json"), f"Should have valid reflex path: {reflex_path}"
    
    def test_database_schema_has_reflex_log_path(self, db):
        """Test database tables have reflex_log_path column"""
        
        cursor = db.conn.cursor()
        
        # Check preflight_assessments table
        cursor.execute("PRAGMA table_info(preflight_assessments)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "reflex_log_path" in columns, "preflight_assessments missing reflex_log_path column"
        
        # Check postflight_assessments table
        cursor.execute("PRAGMA table_info(postflight_assessments)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "reflex_log_path" in columns, "postflight_assessments missing reflex_log_path column"
    
    @pytest.mark.asyncio
    async def test_reflex_log_content_structure(self, db, session_id):
        """Test reflex log JSON has correct structure"""
        
        vectors = {
            'engagement': 0.85,
            'know': 0.7,
            'do': 0.75,
            'context': 0.65,
            'clarity': 0.8,
            'coherence': 0.8,
            'signal': 0.75,
            'density': 0.5,
            'state': 0.7,
            'change': 0.6,
            'completion': 0.5,
            'impact': 0.7,
            'uncertainty': 0.4
        }
        
        result = await call_tool(
            name="submit_preflight_assessment",
            arguments={
                "session_id": session_id,
                "vectors": vectors,
                "reasoning": "Test reflex structure"
            }
        )
        
        response = json.loads(result[0].text)
        reflex_path = response.get("reflex_log_path")
        
        # Load reflex log
        with open(reflex_path) as f:
            reflex_data = json.load(f)
        
        # Verify required fields
        assert "frameId" in reflex_data, "Missing frameId"
        assert "timestamp" in reflex_data, "Missing timestamp"
        assert "epistemicVector" in reflex_data, "Missing epistemicVector"
        assert "task" in reflex_data, "Missing task"
        assert "phase" in reflex_data, "Missing phase"
        
        # Verify epistemic vector structure
        ev = reflex_data["epistemicVector"]
        assert "know" in ev, "Missing know in epistemicVector"
        assert "do" in ev, "Missing do in epistemicVector"
        assert "context" in ev, "Missing context in epistemicVector"
        assert "uncertainty" in ev, "Missing uncertainty in epistemicVector"
        assert "overall_confidence" in ev, "Missing overall_confidence in epistemicVector"
        
        # Verify values match input
        assert ev["know"] == 0.7, f"know mismatch: {ev['know']} != 0.7"
        assert ev["uncertainty"] == 0.4, f"uncertainty mismatch: {ev['uncertainty']} != 0.4"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
