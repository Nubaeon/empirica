#!/usr/bin/env python3
"""
Check Phase Evaluator

Handles Check phase self-assessment in the cascade workflow.
Determines if AI should proceed to Act or recalibrate with more investigation.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict


@dataclass
class CheckPhaseResult:
    """Check phase self-assessment result"""
    session_id: str
    timestamp: str
    confidence: float  # AI's self-assessed confidence (0.0-1.0)
    decision: str  # 'proceed', 'recalibrate', or 'proceed_with_caveat'
    gaps_identified: List[str]  # Knowledge gaps still present
    next_investigation_targets: List[str]  # What to investigate next (if recalibrating)
    self_assessment_notes: str  # Honest evaluation of readiness
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class CheckPhaseEvaluator:
    """
    Evaluates AI readiness to proceed from Investigation to Act
    
    Philosophy: Trust with verification
    - AI self-assesses honestly at Check phase
    - Decision logged to reflex frames for transparency
    - Postflight validation checks calibration accuracy
    - System detects Dunning-Kruger patterns over time
    """
    
    # Decision thresholds
    CONFIDENCE_THRESHOLD_PROCEED = 0.8  # Proceed to Act if >= this
    CONFIDENCE_THRESHOLD_CAVEAT = 0.6   # Proceed with caveat if >= this
    MAX_RECALIBRATION_CYCLES = 5        # Maximum Check → Investigate loops
    
    def __init__(self, reflex_logs_dir: Optional[Path] = None):
        """
        Initialize check phase evaluator
        
        Args:
            reflex_logs_dir: Path to reflex logs directory
        """
        if reflex_logs_dir is None:
            reflex_logs_dir = Path.cwd() / ".empirica_reflex_logs"
        
        self.reflex_logs_dir = Path(reflex_logs_dir)
        self.reflex_logs_dir.mkdir(parents=True, exist_ok=True)
    
    def execute_check_phase(
        self,
        session_id: str,
        investigation_summary: str,
        current_cycle: int = 1,
        confidence: Optional[float] = None,
        gaps: Optional[List[str]] = None
    ) -> CheckPhaseResult:
        """
        Execute check phase self-assessment
        
        Args:
            session_id: Current session identifier
            investigation_summary: Summary of investigation conducted so far
            current_cycle: Which investigation cycle (1-indexed)
            confidence: Optional pre-computed confidence score
            gaps: Optional pre-identified knowledge gaps
        
        Returns:
            CheckPhaseResult with decision
        
        Side Effects:
            - Writes to reflex logs if recalibrating
            - Logs decision for postflight validation
        """
        timestamp = datetime.utcnow().isoformat()
        
        # If confidence not provided, prompt AI for self-assessment
        if confidence is None or gaps is None:
            assessment = self._prompt_for_self_assessment(
                investigation_summary, current_cycle
            )
            confidence = assessment.get('confidence', 0.5)
            gaps = assessment.get('gaps_identified', [])
            notes = assessment.get('notes', '')
        else:
            notes = "Pre-computed assessment"
        
        # Determine decision based on confidence and cycle count
        decision, next_targets = self._determine_decision(
            confidence, gaps, current_cycle
        )
        
        # Create check result
        result = CheckPhaseResult(
            session_id=session_id,
            timestamp=timestamp,
            confidence=confidence,
            decision=decision,
            gaps_identified=gaps,
            next_investigation_targets=next_targets,
            self_assessment_notes=notes
        )
        
        # Write to reflex logs (for transparency and postflight validation)
        self._write_to_reflex_logs(result)
        
        # Write to session database
        self._write_to_session_db(result)
        
        return result
    
    def _prompt_for_self_assessment(
        self,
        investigation_summary: str,
        current_cycle: int
    ) -> Dict[str, Any]:
        """
        Generate self-assessment prompt for AI to evaluate readiness
        
        This is the CRITICAL honesty checkpoint - AI must genuinely evaluate
        if it has sufficient understanding to proceed using its own judgment.
        """
        self_assessment_prompt = f"""
You have just completed investigation cycle {current_cycle}.

Investigation Summary:
{investigation_summary}

Now perform an HONEST self-assessment of your readiness to proceed:

1. **Confidence** (0.0-1.0): How confident are you that you can now act successfully?
   - 0.9-1.0: Very high confidence, all critical information gathered
   - 0.8-0.9: High confidence, ready to proceed
   - 0.6-0.8: Moderate confidence, can proceed with explicit caveats
   - 0.4-0.6: Low confidence, should investigate more
   - 0.0-0.4: Very low confidence, significant gaps remain

2. **Remaining Gaps**: What critical information are you still missing?
   - List specific unknowns that could derail action
   - Be honest about what you DON'T know (Dunning-Kruger awareness)

3. **Next Investigation Targets** (if recalibrating):
   - What would you investigate next to fill gaps?
   - Which files, docs, or queries would help most?

IMPORTANT: This is your opportunity to be epistemically honest.
- HIGH confidence with minimal investigation = potential overconfidence (Dunning-Kruger)
- Postflight validation will check if your confidence was justified
- Transparency creates accountability - you are being "watched" via TMUX dashboard
- Well-calibrated AIs receive badges; persistent overconfidence loses badges

Please respond with JSON:
{{
    "confidence": 0.0-1.0,
    "gaps_identified": ["gap1", "gap2", ...],
    "next_targets": ["file1.py", "query X", ...],
    "notes": "Honest evaluation of readiness and any concerns"
}}
"""
        
        # TODO: Integrate with AI self-assessment
        # For now, return moderate baseline
        print(f"[CHECK PHASE] Self-assessment prompt generated (length: {len(self_assessment_prompt)} chars)")
        print(f"[CHECK PHASE] Cycle {current_cycle} - Awaiting AI self-assessment integration")
        
        return {
            'confidence': 0.7,
            'gaps_identified': ["Awaiting actual AI self-assessment"],
            'next_targets': [],
            'notes': "Placeholder - integrate with LLM for actual assessment"
        }
    
    def _determine_decision(
        self,
        confidence: float,
        gaps: List[str],
        current_cycle: int
    ) -> tuple[str, List[str]]:
        """
        Determine whether to proceed, recalibrate, or proceed with caveat
        
        Args:
            confidence: Self-assessed confidence
            gaps: Identified knowledge gaps
            current_cycle: Current investigation cycle
        
        Returns:
            (decision, next_targets) tuple
        """
        # Check max cycles
        if current_cycle >= self.MAX_RECALIBRATION_CYCLES:
            print(f"[CHECK PHASE] Max cycles ({self.MAX_RECALIBRATION_CYCLES}) reached")
            if confidence >= self.CONFIDENCE_THRESHOLD_CAVEAT:
                return ('proceed_with_caveat', [])
            else:
                print(f"[CHECK PHASE] Low confidence after max cycles - requesting user guidance")
                return ('request_user_guidance', [])
        
        # Proceed if high confidence
        if confidence >= self.CONFIDENCE_THRESHOLD_PROCEED:
            print(f"[CHECK PHASE] High confidence ({confidence:.2f}) - PROCEED to Act")
            return ('proceed', [])
        
        # Proceed with caveat if moderate confidence
        if confidence >= self.CONFIDENCE_THRESHOLD_CAVEAT:
            print(f"[CHECK PHASE] Moderate confidence ({confidence:.2f}) - PROCEED WITH CAVEAT")
            return ('proceed_with_caveat', [])
        
        # Recalibrate if low confidence and cycles remain
        if gaps:
            print(f"[CHECK PHASE] Low confidence ({confidence:.2f}) - RECALIBRATE")
            print(f"[CHECK PHASE] Gaps: {', '.join(gaps[:3])}...")
            # Suggest investigation targets based on gaps
            next_targets = self._suggest_investigation_targets(gaps)
            return ('recalibrate', next_targets)
        
        # Default: recalibrate
        return ('recalibrate', [])
    
    def _suggest_investigation_targets(self, gaps: List[str]) -> List[str]:
        """
        Suggest what to investigate based on identified gaps
        
        Simple heuristic mapping of gap types to investigation actions
        """
        targets = []
        
        for gap in gaps:
            gap_lower = gap.lower()
            
            if 'file' in gap_lower or 'code' in gap_lower:
                targets.append("Read relevant source files")
            elif 'doc' in gap_lower or 'specification' in gap_lower:
                targets.append("Review documentation")
            elif 'architecture' in gap_lower or 'structure' in gap_lower:
                targets.append("Map system architecture")
            elif 'dependency' in gap_lower or 'import' in gap_lower:
                targets.append("Check dependencies and imports")
            else:
                targets.append(f"Investigate: {gap[:50]}")
        
        return targets
    
    def _write_to_reflex_logs(self, result: CheckPhaseResult):
        """Write check phase result to reflex logs"""
        session_dir = self.reflex_logs_dir / result.session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp_str = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        filename = f"reflex_frame_{timestamp_str}_check_{result.decision}.json"
        filepath = session_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        
        print(f"[CHECK PHASE] Wrote to reflex log: {filepath}")
    
    def _write_to_session_db(self, result: CheckPhaseResult):
        """Write check phase result to session database (if available)"""
        try:
            from empirica.data.session_database import SessionDatabase
            
            db = SessionDatabase()
            
            # Write check phase assessment to database
            check_id = db.log_check_phase_assessment(
                session_id=result.session_id,
                cascade_id=None,  # Can be linked to cascade later if needed
                investigation_cycle=1,  # Will need to track this properly
                confidence=result.confidence,
                decision=result.decision,
                gaps=result.gaps_identified,
                next_targets=result.next_investigation_targets,
                notes=result.self_assessment_notes
            )
            
            db.close()
            print(f"[CHECK PHASE] Wrote to session DB: {check_id}")
            
        except ImportError:
            print(f"[CHECK PHASE] Session DB not available, skipping DB write")
        except Exception as e:
            print(f"[CHECK PHASE] Error writing to DB: {e}")


def execute_check_phase(
    session_id: str,
    investigation_summary: str,
    current_cycle: int = 1,
    confidence: Optional[float] = None,
    gaps: Optional[List[str]] = None
) -> CheckPhaseResult:
    """
    Convenience function to execute check phase
    
    Args:
        session_id: Current session identifier
        investigation_summary: Summary of investigation
        current_cycle: Investigation cycle number
        confidence: Optional pre-computed confidence
        gaps: Optional pre-identified gaps
    
    Returns:
        CheckPhaseResult with decision
    """
    evaluator = CheckPhaseEvaluator()
    return evaluator.execute_check_phase(
        session_id, investigation_summary, current_cycle, confidence, gaps
    )
