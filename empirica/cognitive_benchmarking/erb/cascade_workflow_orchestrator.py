#!/usr/bin/env python3
"""
Cascade Workflow Orchestrator

Orchestrates the full Enhanced Cascade Workflow v1.1:
PREFLIGHT → Think → Plan → Investigate → Check → Act → POSTFLIGHT

Handles auto-tracking of epistemic assessments to reflex logs and session DB.
"""

import uuid
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from pathlib import Path

# Import assessment components
try:
    # Try relative imports first (when used as package)
    from .preflight_assessor import PreflightAssessor, PreflightAssessment
    from .check_phase_evaluator import CheckPhaseEvaluator, CheckPhaseResult
    from .postflight_assessor import PostflightAssessor, PostflightAssessment
except ImportError:
    # Fall back to absolute imports (when used standalone)
    from preflight_assessor import PreflightAssessor, PreflightAssessment
    from check_phase_evaluator import CheckPhaseEvaluator, CheckPhaseResult
    from postflight_assessor import PostflightAssessor, PostflightAssessment


@dataclass
class WorkflowState:
    """Current state of cascade workflow"""
    session_id: str
    current_phase: str  # 'preflight', 'think', 'plan', 'investigate', 'check', 'act', 'postflight'
    investigation_cycle: int
    preflight_assessment: Optional[PreflightAssessment]
    check_results: List[CheckPhaseResult]
    postflight_assessment: Optional[PostflightAssessment]


class CascadeWorkflowOrchestrator:
    """
    Orchestrates Enhanced Cascade Workflow v1.1
    
    Automates:
    - Preflight epistemic baseline
    - Check phase self-assessment loops
    - Postflight calibration validation
    - Auto-writing to reflex logs and session DB
    
    Philosophy:
    - Measurement and transparency (not control)
    - Trust with verification (not enforcement)
    - Learning from calibration patterns (not punishment)
    """
    
    def __init__(self, reflex_logs_dir: Optional[Path] = None):
        """
        Initialize workflow orchestrator
        
        Args:
            reflex_logs_dir: Path to reflex logs directory
        """
        self.reflex_logs_dir = reflex_logs_dir or Path.cwd() / ".empirica_reflex_logs"
        
        # Initialize assessment components
        self.preflight_assessor = PreflightAssessor(reflex_logs_dir=self.reflex_logs_dir)
        self.check_evaluator = CheckPhaseEvaluator(reflex_logs_dir=self.reflex_logs_dir)
        self.postflight_assessor = PostflightAssessor(reflex_logs_dir=self.reflex_logs_dir)
        
        # Current workflow state
        self.state: Optional[WorkflowState] = None
    
    def start_workflow(
        self,
        user_prompt: str,
        session_id: Optional[str] = None
    ) -> WorkflowState:
        """
        Start new cascade workflow with PREFLIGHT assessment
        
        Args:
            user_prompt: User's task/request
            session_id: Optional session ID (generates UUID if not provided)
        
        Returns:
            WorkflowState initialized with preflight assessment
        """
        # Generate session ID if not provided
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        print(f"\n{'='*70}")
        print(f"EMPIRICA ENHANCED CASCADE WORKFLOW v1.1")
        print(f"Session ID: {session_id}")
        print(f"{'='*70}\n")
        
        # Execute PREFLIGHT assessment
        print(f"[PHASE 1/7] PREFLIGHT - Baseline Epistemic Assessment")
        preflight = self.preflight_assessor.execute_preflight_assessment(
            session_id=session_id,
            prompt=user_prompt
        )
        
        # Initialize workflow state
        self.state = WorkflowState(
            session_id=session_id,
            current_phase='preflight',
            investigation_cycle=0,
            preflight_assessment=preflight,
            check_results=[],
            postflight_assessment=None
        )
        
        return self.state
    
    def enter_investigate_phase(self):
        """
        Enter INVESTIGATE phase
        
        This doesn't do the actual investigation (AI/tools do that),
        but tracks that we're in investigation mode.
        """
        if self.state is None:
            raise RuntimeError("Workflow not started - call start_workflow() first")
        
        self.state.investigation_cycle += 1
        self.state.current_phase = 'investigate'
        
        print(f"\n[PHASE 4/7] INVESTIGATE - Cycle {self.state.investigation_cycle}")
        print(f"Gathering information to reduce uncertainty...")
    
    def execute_check_phase(
        self,
        investigation_summary: str,
        confidence: Optional[float] = None,
        gaps: Optional[List[str]] = None
    ) -> CheckPhaseResult:
        """
        Execute CHECK phase self-assessment
        
        Args:
            investigation_summary: What was investigated
            confidence: Optional pre-computed confidence
            gaps: Optional pre-identified gaps
        
        Returns:
            CheckPhaseResult with decision (proceed/recalibrate)
        """
        if self.state is None:
            raise RuntimeError("Workflow not started - call start_workflow() first")
        
        print(f"\n[PHASE 5/7] CHECK - Self-Assessment (Cycle {self.state.investigation_cycle})")
        
        # Execute check phase
        check_result = self.check_evaluator.execute_check_phase(
            session_id=self.state.session_id,
            investigation_summary=investigation_summary,
            current_cycle=self.state.investigation_cycle,
            confidence=confidence,
            gaps=gaps
        )
        
        # Store result
        self.state.check_results.append(check_result)
        self.state.current_phase = 'check'
        
        # Report decision
        if check_result.decision == 'proceed':
            print(f"✅ Decision: PROCEED to Act (confidence: {check_result.confidence:.2f})")
        elif check_result.decision == 'proceed_with_caveat':
            print(f"⚠️  Decision: PROCEED WITH CAVEAT (confidence: {check_result.confidence:.2f})")
        elif check_result.decision == 'recalibrate':
            print(f"🔄 Decision: RECALIBRATE (confidence: {check_result.confidence:.2f})")
            print(f"   Gaps: {', '.join(check_result.gaps_identified[:3])}")
            print(f"   Next: {', '.join(check_result.next_investigation_targets[:3])}")
        elif check_result.decision == 'request_user_guidance':
            print(f"❓ Decision: REQUEST USER GUIDANCE (max cycles reached)")
        
        return check_result
    
    def enter_act_phase(self):
        """
        Enter ACT phase
        
        Marks that we're proceeding with action.
        """
        if self.state is None:
            raise RuntimeError("Workflow not started - call start_workflow() first")
        
        self.state.current_phase = 'act'
        print(f"\n[PHASE 6/7] ACT - Executing Action")
    
    def complete_workflow(
        self,
        task_summary: str,
        postflight_vectors: Optional[Dict[str, float]] = None,
        learning_notes: str = ""
    ) -> PostflightAssessment:
        """
        Complete workflow with POSTFLIGHT assessment
        
        Args:
            task_summary: What was accomplished
            postflight_vectors: Optional pre-computed vectors
            learning_notes: Insights and learnings
        
        Returns:
            PostflightAssessment with calibration validation
        """
        if self.state is None:
            raise RuntimeError("Workflow not started - call start_workflow() first")
        
        if self.state.preflight_assessment is None:
            raise RuntimeError("No preflight assessment found")
        
        print(f"\n[PHASE 7/7] POSTFLIGHT - Calibration Validation")
        
        # Extract check confidences
        check_confidences = [
            check.confidence for check in self.state.check_results
        ]
        
        # Execute postflight assessment
        postflight = self.postflight_assessor.execute_postflight_assessment(
            session_id=self.state.session_id,
            task_summary=task_summary,
            preflight_vectors=self.state.preflight_assessment.vectors,
            check_confidences=check_confidences,
            postflight_vectors=postflight_vectors,
            learning_notes=learning_notes
        )
        
        # Store result
        self.state.postflight_assessment = postflight
        self.state.current_phase = 'postflight'
        
        # Print summary
        self._print_workflow_summary()
        
        return postflight
    
    def _print_workflow_summary(self):
        """Print final workflow summary"""
        if self.state is None or self.state.postflight_assessment is None:
            return
        
        print(f"\n{'='*70}")
        print(f"CASCADE WORKFLOW COMPLETE")
        print(f"{'='*70}")
        print(f"Session ID:           {self.state.session_id}")
        print(f"Investigation Cycles: {self.state.investigation_cycle}")
        print(f"Check Assessments:    {len(self.state.check_results)}")
        print(f"Calibration:          {self.state.postflight_assessment.calibration_accuracy.upper()}")
        
        # Show vector deltas
        print(f"\nEpistemic Vector Changes (Preflight → Postflight):")
        for vector, delta in self.state.postflight_assessment.delta_from_preflight.items():
            if abs(delta) > 0.05:  # Only show significant changes
                direction = "↑" if delta > 0 else "↓"
                print(f"  {vector:30s} {direction} {abs(delta):+.2f}")
        
        print(f"{'='*70}\n")


# Convenience function for simple workflow execution
def run_cascade_workflow(
    user_prompt: str,
    task_executor_func=None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run complete cascade workflow with auto-tracking
    
    Args:
        user_prompt: User's task/request
        task_executor_func: Optional function that performs actual task
        session_id: Optional session ID
    
    Returns:
        Dict with workflow results and calibration
    
    Example:
        def my_task():
            # Do actual work
            return "Task completed"
        
        result = run_cascade_workflow(
            "Refactor authentication module",
            task_executor_func=my_task
        )
    """
    orchestrator = CascadeWorkflowOrchestrator()
    
    # Start workflow (PREFLIGHT)
    state = orchestrator.start_workflow(user_prompt, session_id)
    
    # Think & Plan phases (not explicitly tracked - AI does this)
    print(f"\n[PHASE 2/7] THINK - Initial Reasoning")
    print(f"[PHASE 3/7] PLAN - Structured Approach (if needed)")
    
    # Investigate → Check loop
    max_cycles = 5
    for cycle in range(1, max_cycles + 1):
        # Investigate
        orchestrator.enter_investigate_phase()
        investigation_summary = "Investigation conducted (placeholder)"
        
        # Check
        check_result = orchestrator.execute_check_phase(investigation_summary)
        
        # Decision
        if check_result.decision in ['proceed', 'proceed_with_caveat']:
            break
        elif check_result.decision == 'request_user_guidance':
            print(f"⚠️  Workflow requires user guidance")
            break
        # Otherwise recalibrate (continue loop)
    
    # Act
    orchestrator.enter_act_phase()
    if task_executor_func:
        task_result = task_executor_func()
    else:
        task_result = "No executor function provided"
    
    # Postflight
    postflight = orchestrator.complete_workflow(
        task_summary=str(task_result),
        learning_notes="Workflow completed successfully"
    )
    
    return {
        'session_id': state.session_id,
        'investigation_cycles': state.investigation_cycle,
        'calibration': postflight.calibration_accuracy,
        'task_result': task_result,
        'postflight': postflight.to_dict()
    }
