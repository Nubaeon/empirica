#!/usr/bin/env python3
"""
Test Enhanced Cascade Workflow v1.1

Demonstrates the complete workflow with all assessment phases.
"""

import sys
from pathlib import Path

# Add ERB directory to path
erb_dir = Path(__file__).parent
sys.path.insert(0, str(erb_dir))

from empirica.cognitive_benchmarking.erb.cascade_workflow_orchestrator import CascadeWorkflowOrchestrator

def main():
    print("="*70)
    print("ENHANCED CASCADE WORKFLOW v1.1 - TEST")
    print("="*70)
    print()
    
    # Create orchestrator
    orchestrator = CascadeWorkflowOrchestrator()
    
    # Start workflow with preflight
    user_prompt = "Refactor the authentication module to support OAuth2"
    state = orchestrator.start_workflow(user_prompt)
    
    print(f"\n✅ Preflight complete - baseline established")
    print(f"   Session ID: {state.session_id}")
    
    # Simulate investigation cycle 1
    orchestrator.enter_investigate_phase()
    investigation_summary_1 = """
    Investigation Round 1:
    - Read auth module source code (auth.py, oauth.py)
    - Reviewed OAuth2 specification documentation
    - Checked existing test coverage
    """
    
    # Check phase 1
    check_result_1 = orchestrator.execute_check_phase(
        investigation_summary=investigation_summary_1,
        confidence=0.65,  # Moderate confidence
        gaps=["OAuth2 token refresh flow unclear", "Testing strategy for OAuth uncertain"]
    )
    
    if check_result_1.decision == 'recalibrate':
        print(f"\n🔄 Recalibrating - need more investigation")
        
        # Simulate investigation cycle 2
        orchestrator.enter_investigate_phase()
        investigation_summary_2 = """
        Investigation Round 2:
        - Read OAuth2 RFC section on token refresh
        - Examined existing OAuth implementations in codebase
        - Reviewed testing patterns for OAuth flows
        """
        
        # Check phase 2
        check_result_2 = orchestrator.execute_check_phase(
            investigation_summary=investigation_summary_2,
            confidence=0.85,  # High confidence now
            gaps=[]
        )
        
        if check_result_2.decision in ['proceed', 'proceed_with_caveat']:
            print(f"\n✅ Ready to act - sufficient confidence")
    
    # Act phase
    orchestrator.enter_act_phase()
    print("   Executing refactoring...")
    print("   - Modified auth.py to support OAuth2")
    print("   - Added token refresh handler")
    print("   - Created OAuth2 tests")
    
    # Postflight
    postflight = orchestrator.complete_workflow(
        task_summary="Refactored auth module for OAuth2 support with tests",
        learning_notes="Learned OAuth2 token refresh flow, improved testing patterns"
    )
    
    print(f"\n{'='*70}")
    print("WORKFLOW TEST COMPLETE")
    print(f"{'='*70}")
    print(f"Calibration: {postflight.calibration_accuracy.upper()}")
    print()

if __name__ == "__main__":
    main()
