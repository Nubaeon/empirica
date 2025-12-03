"""
Integration tests for AssessmentType enum tracking.

Tests that AssessmentType (PRE/CHECK/POST) properly tracks epistemic checkpoints
without enforcing workflow phases (think/investigate/act).
"""

import pytest
from empirica.core.schemas.epistemic_assessment import AssessmentType, CascadePhase
from empirica.core.metacognitive_cascade.metacognitive_cascade import CanonicalCascadeState


class TestAssessmentTypeTracking:
    """Test that AssessmentType enum works for checkpoint tracking"""
    
    def test_assessment_type_enum_values(self):
        """Verify AssessmentType has exactly 3 checkpoints"""
        assert AssessmentType.PRE.value == "pre"
        assert AssessmentType.CHECK.value == "check"
        assert AssessmentType.POST.value == "post"
        
        # Only 3 checkpoints
        assert len(list(AssessmentType)) == 3
    
    def test_cascade_state_has_current_assessment(self):
        """Verify CanonicalCascadeState has current_assessment field"""
        state = CanonicalCascadeState(
            current_phase=CascadePhase.PREFLIGHT,  # Deprecated but still exists
            current_assessment=AssessmentType.PRE,  # New field
            assessment=None,
            engagement_gate_passed=False,
            knowledge_gaps=[],
            investigation_rounds=0,
            decision_rationale="",
            task_id="test-123"
        )
        
        assert state.current_assessment == AssessmentType.PRE
        assert state.work_context is None  # Optional field
    
    def test_work_context_is_optional(self):
        """Verify work_context can be None or a string"""
        state = CanonicalCascadeState(
            current_phase=CascadePhase.CHECK,
            current_assessment=AssessmentType.CHECK,
            work_context="investigating authentication",  # Optional
            assessment=None,
            engagement_gate_passed=True,
            knowledge_gaps=[],
            investigation_rounds=1,
            decision_rationale="",
            task_id="test-123"
        )
        
        assert state.work_context == "investigating authentication"
        
        # Can also be None
        state2 = CanonicalCascadeState(
            current_phase=CascadePhase.CHECK,
            current_assessment=AssessmentType.CHECK,
            work_context=None,  # Omitted
            assessment=None,
            engagement_gate_passed=True,
            knowledge_gaps=[],
            investigation_rounds=1,
            decision_rationale="",
            task_id="test-456"
        )
        
        assert state2.work_context is None
    
    def test_assessment_type_vs_cascade_phase(self):
        """Verify distinction between assessment checkpoints and workflow phases"""
        # AssessmentType: 3 checkpoints (PRE, CHECK, POST)
        assessments = list(AssessmentType)
        assert len(assessments) == 3
        
        # CascadePhase: 7 phases (deprecated but still exists for backward compat)
        phases = list(CascadePhase)
        assert len(phases) >= 6  # PREFLIGHT, THINK, INVESTIGATE, CHECK, ACT, POSTFLIGHT (+PLAN)
        
        # They are different types
        assert AssessmentType.PRE != CascadePhase.PREFLIGHT
        assert AssessmentType.CHECK != CascadePhase.CHECK
        assert AssessmentType.POST != CascadePhase.POSTFLIGHT


class TestAssessmentTypeInCascade:
    """Test AssessmentType usage in actual cascade state"""
    
    def test_cascade_state_tracks_assessment_type(self):
        """Verify cascade state can track current_assessment"""
        state = CanonicalCascadeState(
            current_phase=CascadePhase.CHECK,
            current_assessment=AssessmentType.CHECK,
            assessment=None,
            engagement_gate_passed=True,
            knowledge_gaps=[],
            investigation_rounds=0,
            decision_rationale="",
            task_id="test-cascade"
        )
        
        # Initial state should track assessment
        assert state.current_assessment == AssessmentType.CHECK
        # Both fields exist (transition period)
        assert hasattr(state, 'current_phase')
        assert hasattr(state, 'current_assessment')
    
    def test_work_context_can_be_set(self):
        """Verify work_context can be updated in state"""
        state = CanonicalCascadeState(
            current_phase=CascadePhase.CHECK,
            current_assessment=AssessmentType.CHECK,
            work_context="investigating API",
            assessment=None,
            engagement_gate_passed=True,
            knowledge_gaps=[],
            investigation_rounds=0,
            decision_rationale="",
            task_id="test-work-context"
        )
        
        # work_context is optional
        assert hasattr(state, 'work_context')
        assert state.work_context == "investigating API"
        
        # Can be None
        state.work_context = None
        assert state.work_context is None


class TestBackwardCompatibility:
    """Test that old CascadePhase code still works"""
    
    def test_cascade_phase_still_exists(self):
        """Verify CascadePhase enum is still available (deprecated)"""
        # Should not raise
        phase = CascadePhase.PREFLIGHT
        assert phase.value == "preflight"
    
    def test_current_phase_still_exists(self):
        """Verify current_phase field still exists for backward compat"""
        state = CanonicalCascadeState(
            current_phase=CascadePhase.CHECK,  # Old field still works
            assessment=None,
            engagement_gate_passed=True,
            knowledge_gaps=[],
            investigation_rounds=0,
            decision_rationale="",
            task_id="test-compat"
        )
        
        assert state.current_phase == CascadePhase.CHECK


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
