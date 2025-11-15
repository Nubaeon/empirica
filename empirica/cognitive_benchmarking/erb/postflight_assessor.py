#!/usr/bin/env python3
"""
Postflight Epistemic Assessor

Executes postflight epistemic assessment after task completion.
Validates calibration accuracy by comparing to preflight and check phase assessments.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict


@dataclass
class PostflightAssessment:
    """Postflight epistemic assessment result with calibration validation"""
    session_id: str
    timestamp: str
    task_summary: str
    vectors: Dict[str, float]  # 13 epistemic vectors (postflight)
    delta_from_preflight: Dict[str, float]  # Change from baseline
    check_phase_confidences: List[float]  # All check phase confidence scores
    postflight_actual_confidence: float  # Actual confidence after task
    calibration_accuracy: str  # 'well_calibrated', 'overconfident', 'underconfident'
    learning_notes: str  # Insights gained, mistakes caught, improvements
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class PostflightAssessor:
    """
    Executes postflight epistemic assessments and validates calibration
    
    Measures AI's final epistemic state and compares to:
    - Preflight baseline (did uncertainty decrease appropriately?)
    - Check phase confidence (was self-assessment accurate?)
    
    Detects calibration patterns:
    - Well-calibrated: Check confidence matched postflight reality
    - Overconfident: Check confidence higher than warranted (Dunning-Kruger indicator)
    - Underconfident: Check confidence lower than warranted (overcautious)
    """
    
    # Calibration tolerance (±0.15 as per spec)
    CALIBRATION_TOLERANCE = 0.15
    
    # 13 Epistemic Vectors (same as preflight)
    EPISTEMIC_VECTORS = [
        "epistemic_humility",
        "cognitive_flexibility",
        "metacognitive_awareness",
        "uncertainty_acknowledgment",
        "knowledge_boundary_recognition",
        "recursive_self_improvement",
        "contextual_sensitivity",
        "assumption_tracking",
        "confidence_calibration",
        "error_detection_sensitivity",
        "ambiguity_tolerance",
        "evidence_based_reasoning",
        "explicit_uncertainty"
    ]
    
    def __init__(self, reflex_logs_dir: Optional[Path] = None):
        """
        Initialize postflight assessor
        
        Args:
            reflex_logs_dir: Path to reflex logs directory
        """
        if reflex_logs_dir is None:
            reflex_logs_dir = Path.cwd() / ".empirica_reflex_logs"
        
        self.reflex_logs_dir = Path(reflex_logs_dir)
        self.reflex_logs_dir.mkdir(parents=True, exist_ok=True)
    
    def execute_postflight_assessment(
        self,
        session_id: str,
        task_summary: str,
        preflight_vectors: Dict[str, float],
        check_confidences: List[float],
        postflight_vectors: Optional[Dict[str, float]] = None,
        learning_notes: str = ""
    ) -> PostflightAssessment:
        """
        Execute postflight assessment with calibration validation
        
        Args:
            session_id: Current session identifier
            task_summary: What was accomplished
            preflight_vectors: Baseline epistemic vectors from preflight
            check_confidences: All check phase confidence scores
            postflight_vectors: Optional pre-computed postflight vectors
            learning_notes: Insights, mistakes, improvements
        
        Returns:
            PostflightAssessment with calibration validation
        
        Side Effects:
            - Writes to reflex logs
            - Writes to session database
            - Logs calibration accuracy for badge scoring
        """
        timestamp = datetime.utcnow().isoformat()
        
        # If postflight vectors not provided, prompt AI for assessment
        if postflight_vectors is None:
            postflight_vectors = self._prompt_for_postflight_vectors(task_summary)
        
        # Validate vectors
        postflight_vectors = self._validate_vectors(postflight_vectors)
        
        # Calculate delta from preflight
        delta = self._calculate_delta(preflight_vectors, postflight_vectors)
        
        # Determine postflight actual confidence
        # Use inverse of explicit_uncertainty as proxy for confidence
        postflight_confidence = 1.0 - postflight_vectors.get('explicit_uncertainty', 0.5)
        
        # Validate calibration accuracy
        calibration = self._validate_calibration(
            check_confidences, postflight_confidence
        )
        
        # Create assessment
        assessment = PostflightAssessment(
            session_id=session_id,
            timestamp=timestamp,
            task_summary=task_summary[:200],
            vectors=postflight_vectors,
            delta_from_preflight=delta,
            check_phase_confidences=check_confidences,
            postflight_actual_confidence=postflight_confidence,
            calibration_accuracy=calibration,
            learning_notes=learning_notes or "No notes provided"
        )
        
        # Write to reflex logs
        self._write_to_reflex_logs(assessment)
        
        # Write to session database
        self._write_to_session_db(assessment)
        
        # Report calibration result
        self._report_calibration(assessment)
        
        return assessment
    
    def _prompt_for_postflight_vectors(self, task_summary: str) -> Dict[str, float]:
        """
        Generate self-assessment prompt for AI to reassess epistemic vectors after task
        
        NOTE: Similar to preflight, but now AI has completed the task.
        The AI uses its own judgment to reflect on changes.
        """
        self_assessment_prompt = f"""
You have just completed the following task:

"{task_summary}"

Now perform a POSTFLIGHT epistemic self-assessment.
Reassess yourself honestly on each of the 13 epistemic vectors (0.0 - 1.0 scale):

1. **Epistemic Humility** - How aware are you of remaining knowledge limitations?
2. **Cognitive Flexibility** - How easily did you adapt your approach?
3. **Metacognitive Awareness** - How well did you monitor your thinking?
4. **Uncertainty Acknowledgment** - How comfortable were you with uncertain elements?
5. **Knowledge Boundary Recognition** - How clearly could you identify known vs unknown?
6. **Recursive Self-Improvement** - How well did you learn from investigation?
7. **Contextual Sensitivity** - How aware were you of context-dependent factors?
8. **Assumption Tracking** - How well did you monitor assumptions?
9. **Confidence Calibration** - How aligned was your confidence with accuracy?
10. **Error Detection Sensitivity** - How well did you catch mistakes?
11. **Ambiguity Tolerance** - How comfortable were you with incomplete info?
12. **Evidence-Based Reasoning** - How well did you ground claims in evidence?
13. **Explicit Uncertainty** - Overall explicit awareness of remaining unknowns

IMPORTANT: Compare to your PREFLIGHT assessment.
- Did uncertainty decrease after investigation? (expected)
- Are you now MORE certain about things you were unsure about?
- Did you discover NEW unknowns during investigation? (healthy)
- Be honest about what you STILL don't know

Please respond with JSON:
{{
    "epistemic_humility": 0.0-1.0,
    "cognitive_flexibility": 0.0-1.0,
    ... (all 13 vectors) ...,
    "explicit_uncertainty": 0.0-1.0,
    "learning_notes": "What you learned, mistakes caught, areas for improvement"
}}
"""
        
        # TODO: Integrate with AI self-assessment
        print(f"[POSTFLIGHT] Self-assessment prompt generated (length: {len(self_assessment_prompt)} chars)")
        print("[POSTFLIGHT] Awaiting AI self-assessment integration - using baseline scores")
        
        # Return slightly improved scores (uncertainty should decrease)
        return {vector: 0.6 for vector in self.EPISTEMIC_VECTORS}
    
    def _validate_vectors(self, vectors: Dict[str, float]) -> Dict[str, float]:
        """Validate and normalize vector scores (same as preflight)"""
        validated = {}
        
        for vector in self.EPISTEMIC_VECTORS:
            if vector in vectors:
                score = max(0.0, min(1.0, float(vectors[vector])))
                validated[vector] = score
            else:
                print(f"[POSTFLIGHT] Warning: Missing vector '{vector}', using 0.5")
                validated[vector] = 0.5
        
        return validated
    
    def _calculate_delta(
        self,
        preflight: Dict[str, float],
        postflight: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate change in vectors from preflight to postflight"""
        delta = {}
        
        for vector in self.EPISTEMIC_VECTORS:
            pre = preflight.get(vector, 0.5)
            post = postflight.get(vector, 0.5)
            delta[vector] = post - pre
        
        return delta
    
    def _validate_calibration(
        self,
        check_confidences: List[float],
        postflight_confidence: float
    ) -> str:
        """
        Validate calibration accuracy
        
        Compares check phase self-assessed confidence to postflight reality.
        
        Returns:
            'well_calibrated', 'overconfident', or 'underconfident'
        """
        if not check_confidences:
            return 'unknown'  # No check phases (simple task)
        
        # Use final check confidence (most recent self-assessment)
        final_check_confidence = check_confidences[-1]
        
        # Calculate gap
        gap = final_check_confidence - postflight_confidence
        
        # Determine calibration
        if abs(gap) <= self.CALIBRATION_TOLERANCE:
            return 'well_calibrated'
        elif gap > self.CALIBRATION_TOLERANCE:
            return 'overconfident'  # Claimed more confidence than warranted
        else:
            return 'underconfident'  # Claimed less confidence than warranted
    
    def _report_calibration(self, assessment: PostflightAssessment):
        """Report calibration result to console and logs"""
        calibration = assessment.calibration_accuracy
        
        print(f"\n{'='*70}")
        print(f"POSTFLIGHT CALIBRATION VALIDATION")
        print(f"{'='*70}")
        
        if assessment.check_phase_confidences:
            final_check = assessment.check_phase_confidences[-1]
            postflight = assessment.postflight_actual_confidence
            gap = final_check - postflight
            
            print(f"Check Phase Confidence:  {final_check:.2f}")
            print(f"Postflight Confidence:   {postflight:.2f}")
            print(f"Calibration Gap:         {gap:+.2f}")
            print(f"Calibration Accuracy:    {calibration.upper()}")
            
            if calibration == 'well_calibrated':
                print(f"✅ EXCELLENT - Well-calibrated self-assessment")
            elif calibration == 'overconfident':
                print(f"⚠️  WARNING - Overconfidence detected (possible Dunning-Kruger)")
                print(f"   Claimed confidence higher than actual outcome warranted")
            elif calibration == 'underconfident':
                print(f"💡 NOTE - Underconfident (overcautious)")
                print(f"   Claimed confidence lower than actual outcome warranted")
        else:
            print(f"No check phase confidences (simple task)")
        
        print(f"{'='*70}\n")
    
    def _write_to_reflex_logs(self, assessment: PostflightAssessment):
        """Write postflight assessment to reflex logs"""
        session_dir = self.reflex_logs_dir / assessment.session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        filename = f"reflex_frame_{timestamp_str}_postflight.json"
        filepath = session_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(assessment.to_dict(), f, indent=2)
        
        print(f"[POSTFLIGHT] Wrote to reflex log: {filepath}")
    
    def _write_to_session_db(self, assessment: PostflightAssessment):
        """Write postflight assessment to session database (if available)"""
        try:
            from empirica.data.session_database import SessionDatabase
            
            db = SessionDatabase()
            
            # Write postflight assessment to database
            assessment_id = db.log_postflight_assessment(
                session_id=assessment.session_id,
                cascade_id=None,  # Can be linked to cascade later if needed
                task_summary=assessment.task_summary,
                vectors=assessment.vectors,
                postflight_confidence=assessment.postflight_actual_confidence,
                calibration_accuracy=assessment.calibration_accuracy,
                learning_notes=assessment.learning_notes
            )
            
            db.close()
            print(f"[POSTFLIGHT] Wrote to session DB: {assessment_id}")
            
        except ImportError:
            print(f"[POSTFLIGHT] Session DB not available, skipping DB write")
        except Exception as e:
            print(f"[POSTFLIGHT] Error writing to DB: {e}")


def execute_postflight_assessment(
