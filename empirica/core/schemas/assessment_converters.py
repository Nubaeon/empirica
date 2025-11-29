"""
Assessment Schema Converters

Bidirectional conversion between OLD and NEW assessment schemas.
Used during migration to ensure compatibility.

OLD Schema: empirica.core.canonical.reflex_frame.EpistemicAssessment
NEW Schema: empirica.core.schemas.epistemic_assessment.EpistemicAssessmentSchema

Note: Some data loss is acceptable when converting NEW -> OLD (OLD format is less rich).
"""

from typing import Optional, List
from dataclasses import dataclass


def convert_old_to_new(old_assessment):
    """
    Convert OLD EpistemicAssessment to NEW EpistemicAssessmentSchema.
    
    Args:
        old_assessment: EpistemicAssessment from reflex_frame.py
        
    Returns:
        EpistemicAssessmentSchema with converted values
        
    Data mapping:
        OLD VectorState(score, reasoning) -> NEW VectorAssessment(score, rationale, evidence, warrants_investigation)
        - reasoning -> rationale
        - evidence = None (OLD format doesn't track evidence)
        - warrants_investigation = False (default, OLD doesn't track this)
    """
    from empirica.core.schemas.epistemic_assessment import (
        EpistemicAssessmentSchema,
        VectorAssessment
    )
    
    def convert_vector(vector_state, vector_name: str) -> VectorAssessment:
        """Convert OLD VectorState to NEW VectorAssessment."""
        # Convert investigation_priority from Optional[str] to int
        inv_priority = 0
        if hasattr(vector_state, 'investigation_priority') and vector_state.investigation_priority:
            priority_map = {'low': 2, 'medium': 5, 'high': 8, 'critical': 10}
            inv_priority = priority_map.get(vector_state.investigation_priority.lower(), 0)
        
        return VectorAssessment(
            score=vector_state.score,
            rationale=vector_state.rationale,  # OLD uses 'rationale' not 'reasoning'
            evidence=vector_state.evidence if hasattr(vector_state, 'evidence') else None,
            warrants_investigation=vector_state.warrants_investigation if hasattr(vector_state, 'warrants_investigation') else False,
            investigation_priority=inv_priority
        )
    
    # Convert all 13 vectors
    return EpistemicAssessmentSchema(
        # Gate
        engagement=convert_vector(old_assessment.engagement, "engagement"),
        
        # Foundation (Tier 0)
        foundation_know=convert_vector(old_assessment.know, "know"),
        foundation_do=convert_vector(old_assessment.do, "do"),
        foundation_context=convert_vector(old_assessment.context, "context"),
        
        # Comprehension (Tier 1)
        comprehension_clarity=convert_vector(old_assessment.clarity, "clarity"),
        comprehension_coherence=convert_vector(old_assessment.coherence, "coherence"),
        comprehension_signal=convert_vector(old_assessment.signal, "signal"),
        comprehension_density=convert_vector(old_assessment.density, "density"),
        
        # Execution (Tier 2)
        execution_state=convert_vector(old_assessment.state, "state"),
        execution_change=convert_vector(old_assessment.change, "change"),
        execution_completion=convert_vector(old_assessment.completion, "completion"),
        execution_impact=convert_vector(old_assessment.impact, "impact"),
        
        # Uncertainty
        uncertainty=convert_vector(old_assessment.uncertainty, "uncertainty"),
        
        # Metadata - NEW schema doesn't store these in the same way
        # EpistemicAssessmentSchema only has phase, round_num, investigation_count
        phase=_convert_phase_to_enum(old_assessment.task) if hasattr(old_assessment, 'task') else None,
        round_num=0,
        investigation_count=0
    )


def convert_new_to_old(new_assessment):
    """
    Convert NEW EpistemicAssessmentSchema to OLD EpistemicAssessment.
    
    Args:
        new_assessment: EpistemicAssessmentSchema from schemas/epistemic_assessment.py
        
    Returns:
        EpistemicAssessment with converted values
        
    Data loss:
        - Evidence is dropped (OLD format doesn't support it)
        - warrants_investigation flag is dropped
        - Persona priors are dropped
        - Rich metadata is simplified
        
    This converter is for backwards compatibility during migration only.
    """
    from empirica.core.canonical.reflex_frame import (
        EpistemicAssessment,
        VectorState,
        Action
    )
    
    def convert_vector(vector_assessment) -> VectorState:
        """Convert NEW VectorAssessment to OLD VectorState."""
        # Convert investigation_priority from int to str
        inv_priority_str = None
        if vector_assessment.investigation_priority > 0:
            if vector_assessment.investigation_priority >= 9:
                inv_priority_str = 'critical'
            elif vector_assessment.investigation_priority >= 6:
                inv_priority_str = 'high'
            elif vector_assessment.investigation_priority >= 3:
                inv_priority_str = 'medium'
            else:
                inv_priority_str = 'low'
        
        return VectorState(
            score=vector_assessment.score,
            rationale=vector_assessment.rationale,  # OLD uses 'rationale' not 'reasoning'
            evidence=vector_assessment.evidence,  # Preserve if present
            warrants_investigation=vector_assessment.warrants_investigation,
            investigation_priority=inv_priority_str,
            investigation_reason=None  # NEW doesn't have this field
        )
    
    # Calculate tier confidences first
    foundation_confidence = _calculate_tier_confidence([
        new_assessment.foundation_know.score,
        new_assessment.foundation_do.score,
        new_assessment.foundation_context.score
    ])
    
    comprehension_confidence = _calculate_tier_confidence([
        new_assessment.comprehension_clarity.score,
        new_assessment.comprehension_coherence.score,
        new_assessment.comprehension_signal.score,
        new_assessment.comprehension_density.score
    ])
    
    execution_confidence = _calculate_tier_confidence([
        new_assessment.execution_state.score,
        new_assessment.execution_change.score,
        new_assessment.execution_completion.score,
        new_assessment.execution_impact.score
    ])
    
    # Calculate overall using NEW schema method
    tier_confidences = new_assessment.calculate_tier_confidences()
    
    # Convert all 13 vectors
    return EpistemicAssessment(
        # Gate
        engagement=convert_vector(new_assessment.engagement),
        engagement_gate_passed=new_assessment.engagement.score >= 0.6,  # Standard threshold
        
        # Foundation (Tier 0)
        know=convert_vector(new_assessment.foundation_know),
        do=convert_vector(new_assessment.foundation_do),
        context=convert_vector(new_assessment.foundation_context),
        foundation_confidence=foundation_confidence,
        
        # Comprehension (Tier 1)
        clarity=convert_vector(new_assessment.comprehension_clarity),
        coherence=convert_vector(new_assessment.comprehension_coherence),
        signal=convert_vector(new_assessment.comprehension_signal),
        density=convert_vector(new_assessment.comprehension_density),
        comprehension_confidence=comprehension_confidence,
        
        # Execution (Tier 2)
        state=convert_vector(new_assessment.execution_state),
        change=convert_vector(new_assessment.execution_change),
        completion=convert_vector(new_assessment.execution_completion),
        impact=convert_vector(new_assessment.execution_impact),
        execution_confidence=execution_confidence,
        
        # Uncertainty
        uncertainty=convert_vector(new_assessment.uncertainty),
        
        # Overall confidence (from NEW schema calculation)
        overall_confidence=tier_confidences["overall_confidence"],
        
        # Recommended action
        recommended_action=_convert_action_to_old(new_assessment.determine_action()),
        
        # Metadata (OLD has different fields)
        assessment_id=f"converted_{new_assessment.phase.value}_{new_assessment.round_num}",
        task="",  # OLD format, minimal info
        timestamp=""  # Will be set by __post_init__
    )


def _calculate_tier_confidence(scores: List[float]) -> float:
    """Calculate tier confidence from vector scores."""
    return sum(scores) / len(scores) if scores else 0.0


def _convert_phase_to_enum(task_str):
    """Convert task string to CascadePhase enum (best effort)."""
    from empirica.core.schemas.epistemic_assessment import CascadePhase
    
    if not task_str:
        return CascadePhase.PREFLIGHT
    
    task_lower = task_str.lower()
    if 'preflight' in task_lower:
        return CascadePhase.PREFLIGHT
    elif 'think' in task_lower:
        return CascadePhase.THINK
    elif 'investigate' in task_lower:
        return CascadePhase.INVESTIGATE
    elif 'check' in task_lower:
        return CascadePhase.CHECK
    elif 'act' in task_lower:
        return CascadePhase.ACT
    elif 'postflight' in task_lower:
        return CascadePhase.POSTFLIGHT
    else:
        return CascadePhase.PREFLIGHT  # Default


def _convert_action(old_action):
    """Convert OLD Action enum to NEW action string."""
    if old_action is None:
        return None
    
    # OLD Action enum values
    action_str = str(old_action).upper()
    if 'INVESTIGATE' in action_str:
        return 'investigate'
    elif 'PROCEED' in action_str or 'ACT' in action_str:
        return 'proceed'
    else:
        return 'investigate'  # Default to investigate


def _convert_action_to_old(new_action: Optional[str]):
    """Convert NEW action string to OLD Action enum."""
    if new_action is None:
        from empirica.core.canonical.reflex_frame import Action
        return Action.INVESTIGATE
    
    from empirica.core.canonical.reflex_frame import Action
    
    if new_action.lower() in ['investigate', 'investigate_more']:
        return Action.INVESTIGATE
    elif new_action.lower() in ['proceed', 'act', 'ready']:
        return Action.PROCEED
    else:
        return Action.INVESTIGATE  # Default


# Utility functions for validation

def validate_conversion_old_to_new(old_assessment) -> bool:
    """
    Validate that OLD -> NEW conversion preserves critical data.
    
    Returns:
        True if conversion is valid, False otherwise
    """
    try:
        new_assessment = convert_old_to_new(old_assessment)
        
        # Check all vectors converted
        assert new_assessment.engagement.score == old_assessment.engagement.score
        assert new_assessment.foundation_know.score == old_assessment.know.score
        assert new_assessment.foundation_do.score == old_assessment.do.score
        assert new_assessment.foundation_context.score == old_assessment.context.score
        
        # Check rationale preserved
        assert new_assessment.engagement.rationale == old_assessment.engagement.rationale
        assert new_assessment.foundation_know.rationale == old_assessment.know.rationale
        
        return True
    except Exception as e:
        print(f"Conversion validation failed: {e}")
        return False


def validate_conversion_new_to_old(new_assessment) -> bool:
    """
    Validate that NEW -> OLD conversion preserves critical data.
    
    Note: Some data loss is expected (evidence, investigation flags).
    
    Returns:
        True if conversion is valid, False otherwise
    """
    try:
        old_assessment = convert_new_to_old(new_assessment)
        
        # Check all vectors converted
        assert old_assessment.engagement.score == new_assessment.engagement.score
        assert old_assessment.know.score == new_assessment.foundation_know.score
        assert old_assessment.do.score == new_assessment.foundation_do.score
        assert old_assessment.context.score == new_assessment.foundation_context.score
        
        # Check rationale preserved
        assert old_assessment.engagement.rationale == new_assessment.engagement.rationale
        assert old_assessment.know.rationale == new_assessment.foundation_know.rationale
        
        return True
    except Exception as e:
        print(f"Conversion validation failed: {e}")
        return False
