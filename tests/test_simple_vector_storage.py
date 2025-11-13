"""Simple test for vector storage - no async, just basics"""

def test_flat_vectors_store_correctly(tmp_path):
    """Test that all 13 vectors are stored correctly"""
    from empirica.data.session_database import SessionDatabase
    import json

    db_path = tmp_path / "test.db"
    db = SessionDatabase(db_path=str(db_path))

    # Create session
    session_id = db.create_session(ai_id="test", bootstrap_level=1, components_loaded=10)

    # Create cascade
    cascade_id = db.create_cascade(
        session_id=session_id,
        task="Test vector storage",
        context={}
    )

    # Log PREFLIGHT with all 13 vectors (flat format)
    vectors = {
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
        vectors=vectors
    )

    # Retrieve and verify ALL 13 vectors
    result = db.get_preflight_assessment(session_id)

    assert result is not None, "Should retrieve assessment"
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

    # Verify vectors_json has all 13
    vectors_json = json.loads(result['vectors_json'])
    assert len(vectors_json) == 13, f"Expected 13 vectors, got {len(vectors_json)}"

    db.close()
    print("✅ All 13 vectors stored correctly!")


def test_epistemic_delta_calculation(tmp_path):
    """Test that epistemic delta proves learning"""
    from empirica.data.session_database import SessionDatabase

    db_path = tmp_path / "test.db"
    db = SessionDatabase(db_path=str(db_path))

    session_id = db.create_session(ai_id="test", bootstrap_level=1, components_loaded=10)
    cascade_id = db.create_cascade(session_id=session_id, task="Test", context={})

    # PREFLIGHT
    preflight_vectors = {
        'engagement': 0.85, 'know': 0.80, 'do': 0.75, 'context': 0.70,
        'clarity': 0.85, 'coherence': 0.80, 'signal': 0.75, 'density': 0.40,
        'state': 0.70, 'change': 0.65, 'completion': 0.30, 'impact': 0.75,
        'uncertainty': 0.35
    }
    db.log_preflight_assessment(session_id, cascade_id, "Before", preflight_vectors)

    # POSTFLIGHT (after learning)
    postflight_vectors = {
        'engagement': 0.90, 'know': 0.92, 'do': 0.75, 'context': 0.85,
        'clarity': 0.90, 'coherence': 0.85, 'signal': 0.80, 'density': 0.30,
        'state': 0.90, 'change': 0.85, 'completion': 0.95, 'impact': 0.85,
        'uncertainty': 0.18
    }
    db.log_postflight_assessment(session_id, cascade_id, "After", postflight_vectors)

    # Calculate delta
    preflight = db.get_preflight_assessment(session_id)
    postflight = db.get_postflight_assessment(session_id)

    know_delta = postflight['know'] - preflight['know']
    uncertainty_delta = postflight['uncertainty'] - preflight['uncertainty']
    completion_delta = postflight['completion'] - preflight['completion']

    # Verify learning occurred
    assert know_delta > 0.10, f"Knowledge should increase, got {know_delta}"
    assert uncertainty_delta < -0.15, f"Uncertainty should decrease, got {uncertainty_delta}"
    assert completion_delta > 0.60, f"Completion should increase, got {completion_delta}"

    db.close()
    print("✅ Epistemic delta proves learning!")


def test_calibration_consistency(tmp_path):
    """Test that calibration is calculated consistently"""
    from empirica.data.session_database import SessionDatabase

    db_path = tmp_path / "test.db"
    db = SessionDatabase(db_path=str(db_path))

    session_id = db.create_session(ai_id="test", bootstrap_level=1, components_loaded=10)
    cascade_id = db.create_cascade(session_id=session_id, task="Test", context={})

    # PREFLIGHT: Higher uncertainty
    preflight = {
        'engagement': 0.85, 'know': 0.75, 'do': 0.70, 'context': 0.75,
        'clarity': 0.80, 'coherence': 0.75, 'signal': 0.75, 'density': 0.40,
        'state': 0.70, 'change': 0.65, 'completion': 0.30, 'impact': 0.75,
        'uncertainty': 0.35
    }

    # POSTFLIGHT: Lower uncertainty, higher knowledge
    postflight = {
        'engagement': 0.88, 'know': 0.88, 'do': 0.70, 'context': 0.85,
        'clarity': 0.85, 'coherence': 0.80, 'signal': 0.80, 'density': 0.35,
        'state': 0.85, 'change': 0.80, 'completion': 0.95, 'impact': 0.85,
        'uncertainty': 0.18
    }

    db.log_preflight_assessment(session_id, cascade_id, "Pre", preflight)
    db.log_postflight_assessment(session_id, cascade_id, "Post", postflight)

    # Verify calibration
    pre = db.get_preflight_assessment(session_id)
    post = db.get_postflight_assessment(session_id)

    uncertainty_decreased = post['uncertainty'] < pre['uncertainty']
    knowledge_increased = post['know'] > pre['know']

    # Should be well-calibrated
    assert uncertainty_decreased, "Uncertainty should decrease"
    assert knowledge_increased, "Knowledge should increase"

    db.close()
    print("✅ Calibration is consistent!")


def test_bayesian_guardian_get_all_beliefs():
    """Test that BayesianBeliefTracker.get_all_beliefs() works"""
    from empirica.calibration.adaptive_uncertainty_calibration.bayesian_belief_tracker import BayesianBeliefTracker

    tracker = BayesianBeliefTracker()

    # Should have the method
    assert hasattr(tracker, 'get_all_beliefs'), "get_all_beliefs method should exist"

    # Should return dict
    beliefs = tracker.get_all_beliefs()
    assert isinstance(beliefs, dict), "Should return dict"

    # Initially empty
    assert len(beliefs) == 0, "Should start with no beliefs"

    print("✅ Bayesian Guardian get_all_beliefs() works!")


def test_drift_monitor_read_synthesis_history():
    """Test that SessionJSONHandler.read_synthesis_history() exists"""
    from empirica.data.session_json_handler import SessionJSONHandler

    handler = SessionJSONHandler()

    # Should have the method
    assert hasattr(handler, 'read_synthesis_history'), "read_synthesis_history method should exist"

    print("✅ Drift Monitor read_synthesis_history() exists!")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
