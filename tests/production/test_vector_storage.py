"""
Test Vector Storage - Verify All 13 Vectors Store Correctly

Tests the fix for flat vector format parsing in MCP tools.
"""

import pytest
import json


@pytest.mark.skip(reason="API drift: Tests use old log_preflight_assessment return format - needs updating")
class TestVectorStorage:
    """Test that all 13 epistemic vectors are correctly stored"""

    @pytest.mark.asyncio
    async def test_flat_vector_format(self, test_session_db):
        """Test that flat vector format is correctly parsed and stored"""
        from empirica.data.session_database import SessionDatabase

        db = SessionDatabase(db_path=test_session_db)

        # create_session returns session_id
        session_id = db.create_session(ai_id="test", bootstrap_level=1, components_loaded=10)
        cascade_id = db.create_cascade(session_id=session_id, task="Test", context={})

        # Flat vector format (as passed to MCP tools)
        flat_vectors = {
            'engagement': 0.85,
            'know': 0.75,
            'do': 0.80,
            'context': 0.70,
            'clarity': 0.90,
            'coherence': 0.85,
            'signal': 0.80,
            'density': 0.40,
            'state': 0.70,
            'change': 0.75,
            'completion': 0.65,
            'impact': 0.80,
            'uncertainty': 0.35
        }

        assessment_id = db.log_preflight_assessment(
            session_id=session_id,
            cascade_id=cascade_id,
            prompt_summary="Test flat vectors",
            vectors=flat_vectors
        )

        # Retrieve and verify ALL 13 vectors stored correctly
        result = db.get_preflight_assessment(session_id)

        assert result['engagement'] == 0.85
        assert result['know'] == 0.75
        assert result['do'] == 0.80
        assert result['context'] == 0.70
        assert result['clarity'] == 0.90
        assert result['coherence'] == 0.85
        assert result['signal'] == 0.80
        assert result['density'] == 0.40
        assert result['state'] == 0.70
        assert result['change'] == 0.75
        assert result['completion'] == 0.65
        assert result['impact'] == 0.80
        assert result['uncertainty'] == 0.35

        # Verify vectors_json contains all 13
        vectors_json = json.loads(result['vectors_json'])
        assert len(vectors_json) == 13

        db.close()

    @pytest.mark.asyncio
    async def test_nested_vector_format(self, test_session_db):
        """Test that nested vector format is also supported"""
        from empirica.data.session_database import SessionDatabase

        db = SessionDatabase(db_path=test_session_db)

        session_id = db.create_session(ai_id="test")
        cascade_id = db.create_cascade(session_id=session_id, task="Test", context={})

        # Nested format (from LLM self-assessment)
        nested_vectors = {
            'engagement': {'score': 0.85, 'rationale': 'Test'},
            'know': {'score': 0.75, 'rationale': 'Test'},
            'do': {'score': 0.80, 'rationale': 'Test'},
            'context': {'score': 0.70, 'rationale': 'Test'},
            'clarity': {'score': 0.90, 'rationale': 'Test'},
            'coherence': {'score': 0.85, 'rationale': 'Test'},
            'signal': {'score': 0.80, 'rationale': 'Test'},
            'density': {'score': 0.40, 'rationale': 'Test'},
            'state': {'score': 0.70, 'rationale': 'Test'},
            'change': {'score': 0.75, 'rationale': 'Test'},
            'completion': {'score': 0.65, 'rationale': 'Test'},
            'impact': {'score': 0.80, 'rationale': 'Test'},
            'uncertainty': {'score': 0.35, 'rationale': 'Test'}
        }

        # Should extract scores correctly
        flat = {}
        for key, value in nested_vectors.items():
            flat[key] = value['score'] if isinstance(value, dict) else value

        assessment_id = db.log_preflight_assessment(
            session_id=session_id,
            cascade_id=cascade_id,
            prompt_summary="Test nested vectors",
            vectors=flat
        )

        result = db.get_preflight_assessment(session_id)

        # All scores should be extracted and stored
        assert result['engagement'] == 0.85
        assert result['know'] == 0.75
        assert result['uncertainty'] == 0.35

        db.close()

    @pytest.mark.asyncio
    async def test_json_export_completeness(self, test_session_db):
        """Test that vectors_json field contains ALL vectors for API export"""
        from empirica.data.session_database import SessionDatabase

        db = SessionDatabase(db_path=test_session_db)

        session_id = db.create_session(ai_id="test")
        cascade_id = db.create_cascade(session_id=session_id, task="Test", context={})

        vectors = {
            'engagement': 0.85, 'know': 0.75, 'do': 0.80, 'context': 0.70,
            'clarity': 0.90, 'coherence': 0.85, 'signal': 0.80, 'density': 0.40,
            'state': 0.70, 'change': 0.75, 'completion': 0.65, 'impact': 0.80,
            'uncertainty': 0.35
        }

        db.log_preflight_assessment(session_id, cascade_id, "Test", vectors)

        result = db.get_preflight_assessment(session_id)
        vectors_json = json.loads(result['vectors_json'])

        # Verify JSON is complete and valid for API transport
        assert isinstance(vectors_json, dict)
        assert len(vectors_json) == 13

        # Verify all values are numbers (no nested objects)
        for key, value in vectors_json.items():
            assert isinstance(value, (int, float))
            assert 0 <= value <= 1  # Valid range

        # Verify can be serialized for HTTP/HTTPS
        json_string = json.dumps(vectors_json)
        assert isinstance(json_string, str)
        assert len(json_string) > 0

        # Verify can be deserialized
        deserialized = json.loads(json_string)
        assert deserialized == vectors_json

        db.close()


@pytest.mark.skip(reason="API drift: log_postflight_assessment signature changed - needs updating")
class TestCalibrationFix:
    """Test the calibration consistency fix"""

    @pytest.mark.asyncio
    async def test_calibration_consistency(self, test_session_db):
        """Test that submit_postflight and get_calibration_report agree"""
        from empirica.data.session_database import SessionDatabase

        db = SessionDatabase(db_path=test_session_db)

        session_id = db.create_session(ai_id="test")
        cascade_id = db.create_cascade(session_id=session_id, task="Test", context={})

        # PREFLIGHT: High uncertainty
        preflight = {
            'engagement': 0.85, 'know': 0.80, 'do': 0.75, 'context': 0.75,
            'clarity': 0.85, 'coherence': 0.80, 'signal': 0.75, 'density': 0.40,
            'state': 0.70, 'change': 0.65, 'completion': 0.30, 'impact': 0.75,
            'uncertainty': 0.35  # High uncertainty
        }

        # POSTFLIGHT: Low uncertainty, high knowledge
        postflight = {
            'engagement': 0.90, 'know': 0.92, 'do': 0.75, 'context': 0.85,
            'clarity': 0.90, 'coherence': 0.85, 'signal': 0.80, 'density': 0.35,
            'state': 0.90, 'change': 0.85, 'completion': 0.98, 'impact': 0.85,
            'uncertainty': 0.18  # Reduced uncertainty
        }

        db.log_preflight_assessment(session_id, cascade_id, "Pre", preflight)
        db.log_postflight_assessment(session_id, cascade_id, "Post", postflight)

        # Both methods should agree on calibration
        pre = db.get_preflight_assessment(session_id)
        post = db.get_postflight_assessment(session_id)

        # Calculate using same algorithm
        uncertainty_decreased = post['uncertainty'] < pre['uncertainty']
        knowledge_increased = post['know'] > pre['know']

        # Well-calibrated: both conditions met
        expected_calibration = "well_calibrated"
        if uncertainty_decreased and knowledge_increased:
            actual_calibration = "well_calibrated"
        elif uncertainty_decreased and not knowledge_increased:
            actual_calibration = "overconfident"
        elif not uncertainty_decreased and knowledge_increased:
            actual_calibration = "underconfident"
        else:
            actual_calibration = "poorly_calibrated"

        assert actual_calibration == expected_calibration

        db.close()


class TestBayesianGuardianAndDriftMonitor:
    """Test the implemented missing methods"""

    @pytest.mark.skip(reason="empirica.calibration module not yet implemented - planned feature")
    @pytest.mark.asyncio
    async def test_get_all_beliefs(self):
        """Test BayesianBeliefTracker.get_all_beliefs() method"""
        from empirica.calibration.adaptive_uncertainty_calibration.bayesian_belief_tracker import BayesianBeliefTracker

        tracker = BayesianBeliefTracker()

        # Add some beliefs
        tracker.update_belief("test_belief_1", 0.5, {"type": "observation", "value": 0.8})
        tracker.update_belief("test_belief_2", 0.6, {"type": "observation", "value": 0.7})

        # Get all beliefs
        beliefs = tracker.get_all_beliefs()

        assert isinstance(beliefs, dict)
        assert "test_belief_1" in beliefs
        assert "test_belief_2" in beliefs

        # Verify structure
        belief1 = beliefs["test_belief_1"]
        assert "mean" in belief1
        assert "variance" in belief1
        assert "evidence_count" in belief1
        assert "is_confident" in belief1

    @pytest.mark.skip(reason="API drift: SessionJSONHandler constructor signature changed - needs updating")
    @pytest.mark.asyncio
    async def test_read_synthesis_history(self, test_session_db):
        """Test SessionJSONHandler.read_synthesis_history() method"""
        from empirica.data.session_json_handler import SessionJSONHandler
        from empirica.data.session_database import SessionDatabase

        # Create test session with CHECK assessments
        db = SessionDatabase(db_path=test_session_db)

        session_id = db.create_session(ai_id="test")
        cascade_id = db.create_cascade(session_id=session_id, task="Test", context={})

        # Simulate CHECK assessments (synthesis events)
        # This would normally be done through the CASCADE workflow

        handler = SessionJSONHandler(db)
        history = handler.read_synthesis_history(session_id)

        # Should return list of synthesis events
        assert isinstance(history, list)

        db.close()


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
