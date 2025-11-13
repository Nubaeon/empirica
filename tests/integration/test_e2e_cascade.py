"""
End-to-End Integration Tests for Cascade

Assignment: Gemini
Priority: CRITICAL
"""
import pytest


def test_e2e_cascade_complete():
    """Test complete cascade flow from task to decision"""
    from semantic_self_aware_kit.metacognitive_cascade import run_epistemic_cascade
    
    # Complex task that should trigger multiple phases
    result = run_epistemic_cascade(
        task="Should I refactor the authentication module given current technical debt?",
        context={
            "module": "auth",
            "debt_score": 7.5,
            "test_coverage": 0.65,
            "last_modified": "2024-01-15"
        },
        confidence_threshold=0.75
    )
    
    # Verify complete flow
    assert 'final_decision' in result
    assert 'confidence' in result
    assert 'reasoning' in result
    assert result['final_decision'] in ['PROCEED', 'INVESTIGATE', 'DEFER', 'ABORT']
    
    # Should have epistemic state
    assert 'epistemic_state' in result
    epistemic = result['epistemic_state']
    assert isinstance(epistemic, dict)


def test_e2e_cascade_with_investigation():
    """Test cascade triggers and completes investigation"""
    from semantic_self_aware_kit.metacognitive_cascade import run_epistemic_cascade
    
    # Intentionally vague task to trigger investigation
    result = run_epistemic_cascade(
        task="Handle the thing with the stuff",
        context={},
        confidence_threshold=0.8
    )
    
    # Should complete even with low confidence
    assert 'final_decision' in result
    assert 'confidence' in result


def test_e2e_decision_quality():
    """Test decision quality with clear vs unclear tasks"""
    from semantic_self_aware_kit.metacognitive_cascade import run_epistemic_cascade
    
    # Clear task
    clear_result = run_epistemic_cascade(
        task="Add a print statement to log entry",
        context={"simple": True, "clear": True},
        confidence_threshold=0.7
    )
    
    # Unclear task
    unclear_result = run_epistemic_cascade(
        task="Do something about the performance issues maybe",
        context={},
        confidence_threshold=0.7
    )
    
    # Both should complete
    assert 'confidence' in clear_result
    assert 'confidence' in unclear_result
