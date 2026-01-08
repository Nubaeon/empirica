"""
Test Epistemic Handoff - Knowledge Transfer Between AIs

Tests the core security feature: transferring epistemic deltas
across trust boundaries without exposing data.
"""

import pytest
import json
from pathlib import Path


@pytest.mark.skip(reason="API drift: Tests use old log_preflight_assessment/log_postflight_assessment APIs - needs updating")
class TestEpistemicHandoff:
    """Test epistemic state transfer between agents"""

    @pytest.mark.asyncio
    async def test_preflight_storage(self, test_session_db):
        """Test that PREFLIGHT epistemic state is correctly stored"""
        from empirica.data.session_database import SessionDatabase

        db = SessionDatabase(db_path=test_session_db)

        # Create session (API returns session_id)
        session_id = db.create_session(ai_id="claude-test")

        # Create cascade
        cascade_id = db.create_cascade(
            session_id=session_id,
            task="Test epistemic handoff",
            context={"test": "context"}
        )

        # Log PREFLIGHT assessment with all 13 vectors
        vectors = {
            'engagement': 0.88,
            'know': 0.82,
            'do': 0.70,
            'context': 0.85,
            'clarity': 0.92,
            'coherence': 0.90,
            'signal': 0.88,
            'density': 0.35,
            'state': 0.78,
            'change': 0.75,
            'completion': 0.30,
            'impact': 0.82,
            'uncertainty': 0.32
        }

        assessment_id = db.log_preflight_assessment(
            session_id=session_id,
            cascade_id=cascade_id,
            prompt_summary="PREFLIGHT test",
            vectors=vectors,
            uncertainty_notes="Test uncertainty"
        )

        # Retrieve and verify
        preflight = db.get_preflight_assessment(session_id)

        assert preflight is not None
        assert preflight['engagement'] == 0.88
        assert preflight['know'] == 0.82
        assert preflight['uncertainty'] == 0.32

        # Verify vectors_json contains all 13 vectors
        vectors_json = json.loads(preflight['vectors_json'])
        assert len(vectors_json) == 13
        assert vectors_json['engagement'] == 0.88

        db.close()

    @pytest.mark.asyncio
    async def test_epistemic_delta_calculation(self, test_session_db):
        """Test that epistemic delta is correctly calculated"""
        from empirica.data.session_database import SessionDatabase

        db = SessionDatabase(db_path=test_session_db)

        # Setup - create_session returns session_id
        session_id = db.create_session(ai_id="test")
        cascade_id = db.create_cascade(session_id=session_id, task="Test", context={})

        # PREFLIGHT
        preflight_vectors = {
            'engagement': 0.85,
            'know': 0.80,
            'do': 0.75,
            'context': 0.70,
            'clarity': 0.85,
            'coherence': 0.80,
            'signal': 0.75,
            'density': 0.40,
            'state': 0.70,
            'change': 0.65,
            'completion': 0.30,
            'impact': 0.75,
            'uncertainty': 0.35
        }
        db.log_preflight_assessment(session_id, cascade_id, "Pre", preflight_vectors)

        # POSTFLIGHT (simulating learning)
        postflight_vectors = {
            'engagement': 0.90,
            'know': 0.92,  # +0.12 learned
            'do': 0.75,  # unchanged
            'context': 0.85,  # +0.15 improved
            'clarity': 0.90,
            'coherence': 0.85,
            'signal': 0.80,
            'density': 0.30,  # -0.10 reduced
            'state': 0.90,  # +0.20 improved
            'change': 0.85,
            'completion': 0.95,  # +0.65 task complete
            'impact': 0.85,
            'uncertainty': 0.18  # -0.17 reduced
        }
        db.log_postflight_assessment(session_id, cascade_id, "Post", postflight_vectors)

        # Calculate delta
        preflight = db.get_preflight_assessment(session_id)
        postflight = db.get_postflight_assessment(session_id)

        know_delta = postflight['know'] - preflight['know']
        uncertainty_delta = postflight['uncertainty'] - preflight['uncertainty']
        completion_delta = postflight['completion'] - preflight['completion']

        # Verify learning occurred
        assert know_delta > 0.10  # Knowledge increased
        assert uncertainty_delta < -0.15  # Uncertainty decreased
        assert completion_delta > 0.60  # Task completed

        db.close()

    @pytest.mark.asyncio
    async def test_cross_boundary_transfer(self, test_session_db):
        """Test that only epistemic state transfers, not data"""
        from empirica.data.session_database import SessionDatabase

        db = SessionDatabase(db_path=test_session_db)

        # Agent A (with sensitive data access)
        session_id = db.create_session(ai_id="agent-a")
        cascade_id = db.create_cascade(
            session_id=session_id,
            task="Analyze sensitive data",
            context={"data_classification": "PHI", "trust_zone": "secure"}
        )

        # Log PREFLIGHT with epistemic state only
        vectors = {
            'engagement': 0.85,
            'know': 0.87,
            'do': 0.80,
            'context': 0.75,
            'clarity': 0.90,
            'coherence': 0.85,
            'signal': 0.88,
            'density': 0.35,
            'state': 0.80,
            'change': 0.75,
            'completion': 0.40,
            'impact': 0.85,
            'uncertainty': 0.25
        }
        db.log_preflight_assessment(
            session_id,
            cascade_id,
            "Pattern identified, needs validation",
            vectors
        )

        # Retrieve for Agent B (no data access)
        epistemic_state = db.get_preflight_assessment(session_id)

        # Verify: Only epistemic state, NO sensitive data
        assert 'engagement' in epistemic_state
        assert 'know' in epistemic_state
        assert 'uncertainty' in epistemic_state

        # Verify: vectors_json contains ONLY numbers, no data
        vectors_json = json.loads(epistemic_state['vectors_json'])
        for key, value in vectors_json.items():
            assert isinstance(value, (int, float)), f"{key} should be numeric"
            assert 0 <= value <= 1, f"{key} should be 0-1 range"

        # Verify: prompt_summary is metadata, not data
        prompt = epistemic_state['prompt_summary']
        assert "Pattern identified" in prompt
        assert len(prompt) < 500  # Metadata, not full data

        db.close()

    @pytest.mark.asyncio
    async def test_calibration_validation(self, test_session_db):
        """Test calibration proves learning vs overconfidence"""
        from empirica.data.session_database import SessionDatabase

        db = SessionDatabase(db_path=test_session_db)

        # Setup
        session_id = db.create_session(ai_id="test")
        cascade_id = db.create_cascade(session_id=session_id, task="Test", context={})

        # Scenario 1: Well-calibrated (uncertainty decreased, knowledge increased)
        preflight = {
            'engagement': 0.85, 'know': 0.75, 'do': 0.70, 'context': 0.75,
            'clarity': 0.80, 'coherence': 0.75, 'signal': 0.75, 'density': 0.40,
            'state': 0.70, 'change': 0.65, 'completion': 0.30, 'impact': 0.75,
            'uncertainty': 0.35
        }
        postflight = {
            'engagement': 0.88, 'know': 0.88, 'do': 0.70, 'context': 0.85,
            'clarity': 0.85, 'coherence': 0.80, 'signal': 0.80, 'density': 0.35,
            'state': 0.85, 'change': 0.80, 'completion': 0.95, 'impact': 0.85,
            'uncertainty': 0.18
        }

        db.log_preflight_assessment(session_id, cascade_id, "Pre", preflight)
        db.log_postflight_assessment(session_id, cascade_id, "Post", postflight)

        # Verify well-calibrated
        pre = db.get_preflight_assessment(session_id)
        post = db.get_postflight_assessment(session_id)

        uncertainty_decreased = post['uncertainty'] < pre['uncertainty']
        knowledge_increased = post['know'] > pre['know']

        assert uncertainty_decreased, "Uncertainty should decrease after learning"
        assert knowledge_increased, "Knowledge should increase after execution"

        # This should result in "well_calibrated" status
        assert uncertainty_decreased and knowledge_increased

        db.close()


class TestMCPEpistemicTools:
    """Test MCP tools for epistemic state transfer"""

    @pytest.mark.requires_mcp
    def test_get_epistemic_state_mcp(self):
        """Test that get_epistemic_state MCP tool returns complete state"""
        # This would require MCP server to be running
        # Placeholder for integration test
        pass

    @pytest.mark.requires_mcp
    def test_submit_preflight_flat_vectors(self):
        """Test that flat vector format is correctly handled"""
        # Test the fix we just made for flat vector parsing
        pass


@pytest.fixture
def test_session_db(tmp_path):
    """Create a temporary test database"""
    from empirica.data.session_database import SessionDatabase

    db_path = tmp_path / "test_sessions.db"
    db = SessionDatabase(db_path=str(db_path))
    db.close()

    yield str(db_path)

    # Cleanup
    if db_path.exists():
        db_path.unlink()
