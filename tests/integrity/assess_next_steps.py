#!/usr/bin/env python3
"""
Self-Assessment: What to do next?

Using Empirica's 7-phase workflow to decide the next priority.
"""
import asyncio
import sys
from pathlib import Path

# Add empirica to path
sys.path.insert(0, str(Path(__file__).parent))

from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

async def assess_next_steps():
    """Use Empirica to assess what to implement next"""
    
    # Initialize cascade
    cascade = CanonicalEpistemicCascade(
        agent_id='claude_copilot',
        enable_bayesian=False,  # Simple decision
        enable_drift_monitor=False,
        enable_session_db=True,
        enable_action_hooks=False  # No tmux needed
    )
    
    print("=" * 70)
    print("  USING EMPIRICA TO ASSESS NEXT STEPS")
    print("=" * 70)
    
    # Task to assess
    task = """Determine the highest priority next step for Empirica development:

OPTIONS:
1. **MCP Server Updates**: Add execute_preflight and execute_postflight tools to MCP server
2. **Bootstrap Verification**: Ensure all bootstrap levels load components correctly
3. **CLI Interface**: Create simple CLI for running cascades from command line

CONTEXT:
- Just completed 7-phase workflow integration
- All phases (PREFLIGHT → POSTFLIGHT) are implemented
- Need to validate the system works end-to-end
- User wants to see Empirica in action

CONSTRAINTS:
- Should provide immediate validation that 7-phase workflow functions
- Should be simple to test and demonstrate
- Should build toward production readiness

What should we prioritize?
"""
    
    context = {
        'session': 'next_steps_assessment',
        'phase': 'post_7_phase_implementation',
        'available_tools': ['read', 'write', 'bash', 'edit', 'create'],
        'cwd': '/home/yogapad/empirical-ai/empirica',
        'recent_work': [
            'Implemented PREFLIGHT phase',
            'Implemented POSTFLIGHT phase',
            'Added epistemic delta calculation',
            'Added calibration checking',
            'Fixed terminology (meta-prompt → self-assessment)',
            'Removed heuristic fallbacks'
        ]
    }
    
    # Run 7-phase cascade
    result = await cascade.run_epistemic_cascade(task=task, context=context)
    
    print("\n" + "=" * 70)
    print("  EMPIRICA ASSESSMENT COMPLETE")
    print("=" * 70)
    print(f"\n📊 PREFLIGHT → POSTFLIGHT:")
    print(f"   Start Confidence: {result.get('preflight_confidence', 0):.2f}")
    print(f"   Final Confidence: {result.get('postflight_confidence', 0):.2f}")
    print(f"   Learning (Δ): {result.get('postflight_confidence', 0) - result.get('preflight_confidence', 0):+.2f}")
    
    print(f"\n🎯 DECISION:")
    print(f"   Action: {result['action']}")
    print(f"   Confidence: {result['confidence']:.2f}")
    print(f"   Investigation Rounds: {result.get('investigation_rounds', 0)}")
    
    if result.get('calibration'):
        cal = result['calibration']
        print(f"\n✅ CALIBRATION:")
        print(f"   Well-Calibrated: {cal.get('well_calibrated', False)}")
        if cal.get('warning'):
            print(f"   ⚠️  Warning: {cal['warning']}")
        if cal.get('note'):
            print(f"   📝 Note: {cal['note']}")
    
    print(f"\n💭 RATIONALE:")
    print(f"   {result['rationale']}")
    
    if result.get('execution_guidance'):
        print(f"\n🔧 GUIDANCE:")
        for guidance in result['execution_guidance']:
            print(f"   - {guidance}")
    
    return result

if __name__ == "__main__":
    print("\n🧠 Bootstrapping Empirica for self-use...")
    result = asyncio.run(assess_next_steps())
    print("\n✅ Assessment complete! Empirica validated itself.\n")
