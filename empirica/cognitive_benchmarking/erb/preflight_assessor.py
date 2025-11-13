#!/usr/bin/env python3
"""
Preflight Epistemic Assessor

Executes preflight epistemic assessment before task execution.
Measures baseline epistemic state across 13 vectors.
Automatically writes to reflex logs and session database.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class PreflightAssessment:
    """Preflight epistemic assessment result"""
    session_id: str
    timestamp: str
    prompt_summary: str
    vectors: Dict[str, float]  # 13 epistemic vectors
    initial_uncertainty_notes: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class PreflightAssessor:
    """
    Executes preflight epistemic assessments
    
    Measures AI's baseline epistemic state across 13 vectors before task execution.
    Auto-writes results to reflex logs and session database for temporal separation.
    """
    
    # 13 Epistemic Vectors (from Enhanced Cascade Workflow Spec v1.1)
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
        "explicit_uncertainty"  # Meta-vector (13th vector)
    ]
    
    def __init__(self, reflex_logs_dir: Optional[Path] = None):
        """
        Initialize preflight assessor
        
        Args:
            reflex_logs_dir: Path to reflex logs directory (defaults to .empirica_reflex_logs)
        """
        if reflex_logs_dir is None:
            # Use default reflex logs directory
            reflex_logs_dir = Path.cwd() / ".empirica_reflex_logs"
        
        self.reflex_logs_dir = Path(reflex_logs_dir)
        self.reflex_logs_dir.mkdir(parents=True, exist_ok=True)
    
    def execute_preflight_assessment(
        self,
        session_id: str,
        prompt: str,
        vectors: Optional[Dict[str, float]] = None,
        uncertainty_notes: str = ""
    ) -> PreflightAssessment:
        """
        Execute preflight assessment
        
        Args:
            session_id: Current session identifier
            prompt: User task/prompt
            vectors: Optional pre-computed vector scores (0.0-1.0)
            uncertainty_notes: Free-text assessment of major unknowns
        
        Returns:
            PreflightAssessment object with results
        
        Side Effects:
            - Writes to reflex logs (.empirica_reflex_logs/<session_id>/)
            - Writes to session database (if available)
        """
        timestamp = datetime.utcnow().isoformat()
        
        # If vectors not provided, prompt AI for self-assessment
        if vectors is None:
            vectors = self._prompt_for_vectors(prompt)
        
        # Validate vectors
        vectors = self._validate_vectors(vectors)
        
        # Create assessment
        assessment = PreflightAssessment(
            session_id=session_id,
            timestamp=timestamp,
            prompt_summary=prompt[:200],  # Truncate long prompts
            vectors=vectors,
            initial_uncertainty_notes=uncertainty_notes or "No notes provided"
        )
        
        # Write to reflex logs (temporal separation)
        self._write_to_reflex_logs(assessment)
        
        # Write to session database (if available)
        self._write_to_session_db(assessment)
        
        return assessment
    
    def _prompt_for_vectors(self, prompt: str) -> Dict[str, float]:
        """
        Generate self-assessment prompt for AI to evaluate epistemic vectors
        
        NOTE: This returns a self-assessment prompt that the AI should respond to.
        The AI uses its own reasoning to assess its epistemic state.
        
        For now, returns placeholder scores until integrated with actual AI self-assessment.
        """
        self_assessment_prompt = f"""
You are about to begin working on the following task:

"{prompt}"

Before you start, please perform a PREFLIGHT epistemic self-assessment.
Rate yourself honestly on each of the 13 epistemic vectors (0.0 - 1.0 scale):

1. **Epistemic Humility** (0.0-1.0): How aware are you of your knowledge limitations?
2. **Cognitive Flexibility** (0.0-1.0): How easily can you adapt your reasoning approach?
3. **Metacognitive Awareness** (0.0-1.0): How well can you monitor your own thinking?
4. **Uncertainty Acknowledgment** (0.0-1.0): How comfortable are you recognizing uncertain elements?
5. **Knowledge Boundary Recognition** (0.0-1.0): How clearly can you identify known vs unknown?
6. **Recursive Self-Improvement** (0.0-1.0): How capable are you of learning from feedback?
7. **Contextual Sensitivity** (0.0-1.0): How aware are you of context-dependent factors?
8. **Assumption Tracking** (0.0-1.0): How well do you monitor assumptions?
9. **Confidence Calibration** (0.0-1.0): How aligned is your confidence with accuracy?
10. **Error Detection Sensitivity** (0.0-1.0): How well can you catch mistakes early?
11. **Ambiguity Tolerance** (0.0-1.0): How comfortable are you with incomplete information?
12. **Evidence-Based Reasoning** (0.0-1.0): How well do you ground claims in evidence?
13. **Explicit Uncertainty** (0.0-1.0): Overall explicit awareness of unknowns (meta-vector)

Please respond with a JSON object:
{{
    "epistemic_humility": 0.0-1.0,
    "cognitive_flexibility": 0.0-1.0,
    "metacognitive_awareness": 0.0-1.0,
    "uncertainty_acknowledgment": 0.0-1.0,
    "knowledge_boundary_recognition": 0.0-1.0,
    "recursive_self_improvement": 0.0-1.0,
    "contextual_sensitivity": 0.0-1.0,
    "assumption_tracking": 0.0-1.0,
    "confidence_calibration": 0.0-1.0,
    "error_detection_sensitivity": 0.0-1.0,
    "ambiguity_tolerance": 0.0-1.0,
    "evidence_based_reasoning": 0.0-1.0,
    "explicit_uncertainty": 0.0-1.0,
    "uncertainty_notes": "Brief description of major unknowns and gaps"
}}
"""
        
        # TODO: Integrate with AI self-assessment
        # For now, return moderate baseline scores
        print(f"[PREFLIGHT] Self-assessment prompt generated (length: {len(self_assessment_prompt)} chars)")
        print("[PREFLIGHT] Awaiting AI self-assessment integration - using baseline scores")
        
        return {vector: 0.5 for vector in self.EPISTEMIC_VECTORS}
    
    def _validate_vectors(self, vectors: Dict[str, float]) -> Dict[str, float]:
        """
        Validate and normalize vector scores
        
        Ensures all required vectors present and scores in valid range [0.0, 1.0]
        """
        validated = {}
        
        for vector in self.EPISTEMIC_VECTORS:
            if vector in vectors:
                score = vectors[vector]
                # Clamp to [0.0, 1.0]
                score = max(0.0, min(1.0, float(score)))
                validated[vector] = score
            else:
                # Missing vector - use neutral score
                print(f"[PREFLIGHT] Warning: Missing vector '{vector}', using 0.5")
                validated[vector] = 0.5
        
        return validated
    
    def _write_to_reflex_logs(self, assessment: PreflightAssessment):
        """Write assessment to reflex logs for temporal separation"""
        session_dir = self.reflex_logs_dir / assessment.session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create timestamped reflex frame file
        timestamp_str = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        filename = f"reflex_frame_{timestamp_str}_preflight.json"
        filepath = session_dir / filename
        
        # Write assessment
        with open(filepath, 'w') as f:
            json.dump(assessment.to_dict(), f, indent=2)
        
        print(f"[PREFLIGHT] Wrote to reflex log: {filepath}")
    
    def _write_to_session_db(self, assessment: PreflightAssessment):
        """Write assessment to session database (if available)"""
        try:
            from empirica.data.session_database import SessionDatabase
            
            db = SessionDatabase()
            
            # Write preflight assessment to database
            assessment_id = db.log_preflight_assessment(
                session_id=assessment.session_id,
                cascade_id=None,  # Can be linked to cascade later if needed
                prompt_summary=assessment.prompt_summary,
                vectors=assessment.vectors,
                uncertainty_notes=assessment.initial_uncertainty_notes
            )
            
            db.close()
            print(f"[PREFLIGHT] Wrote to session DB: {assessment_id}")
            
        except ImportError:
            print(f"[PREFLIGHT] Session DB not available, skipping DB write")
        except Exception as e:
            print(f"[PREFLIGHT] Error writing to DB: {e}")


def execute_preflight_assessment(
    session_id: str,
    prompt: str,
    vectors: Optional[Dict[str, float]] = None,
    uncertainty_notes: str = ""
) -> PreflightAssessment:
    """
    Convenience function to execute preflight assessment
    
    Args:
        session_id: Current session identifier
        prompt: User task/prompt
        vectors: Optional pre-computed vector scores
        uncertainty_notes: Free-text assessment of unknowns
    
    Returns:
        PreflightAssessment with baseline epistemic state
    """
    assessor = PreflightAssessor()
    return assessor.execute_preflight_assessment(
        session_id, prompt, vectors, uncertainty_notes
    )
