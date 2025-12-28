#!/usr/bin/env python3
"""
Test Phase 1 Optimization: Integrated Epistemic Assessment

Verifies that parallel reasoning can generate epistemic assessment
in a single synthesis pass instead of requiring a 4th mapping pass.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

async def test_integrated_assessment():
    """
    Test that synthesis can include epistemic assessment directly
    """
    print("=" * 70)
    print("Testing Phase 1 Optimization: Integrated Epistemic Assessment")
    print("=" * 70)

    system = ParallelReasoningSystem(llm_model="phi3")

    # Simple test case
    user_input = "What is 2 + 2?"
    history = []
    context_assessment = {
        "topic": "arithmetic",
        "stakes": "low",
        "user_emotional_state": "neutral",
        "fact_vs_opinion": "factual"
    }

    print("\n1️⃣  Testing WITH integrated epistemic assessment (3 passes)...")
    print(f"   Task: {user_input}")

    result_with = await system.generate_response(
        user_input=user_input,
        history=history,
        context_assessment=context_assessment,
        include_epistemic_assessment=True
    )

    print("\n✅ Synthesis Complete")
    print(f"   - Contains EPISTEMIC_ASSESSMENT: {'EPISTEMIC_ASSESSMENT' in result_with}")

    if 'EPISTEMIC_ASSESSMENT' in result_with:
        epistemic = result_with['EPISTEMIC_ASSESSMENT']
        print(f"   - Has 'engagement' key: {'engagement' in epistemic}")
        print(f"   - Has 'foundation' key: {'foundation' in epistemic}")
        print(f"   - Has 'comprehension' key: {'comprehension' in epistemic}")
        print(f"   - Has 'execution' key: {'execution' in epistemic}")

        # Check structure
        if 'engagement' in epistemic and isinstance(epistemic['engagement'], dict):
            eng = epistemic['engagement']
            print(f"   - Engagement score: {eng.get('score', 'N/A')}")
            print(f"   - Engagement rationale: {eng.get('rationale', 'N/A')[:60]}...")

        if 'foundation' in epistemic and isinstance(epistemic['foundation'], dict):
            found = epistemic['foundation']
            print(f"   - Foundation vectors: {list(found.keys())}")
            if 'know' in found:
                print(f"   - Know score: {found['know'].get('score', 'N/A')}")

        print("\n✅ Phase 1 Optimization WORKING - Integrated assessment generated!")
    else:
        print("\n⚠️  EPISTEMIC_ASSESSMENT not found in synthesis result")
        print("   This means we'll fall back to 4-pass process")

    print("\n" + "=" * 70)
    print("\n2️⃣  Testing WITHOUT integrated epistemic assessment (backward compat)...")

    result_without = await system.generate_response(
        user_input=user_input,
        history=history,
        context_assessment=context_assessment,
        include_epistemic_assessment=False
    )

    print("\n✅ Synthesis Complete (no epistemic assessment requested)")
    print(f"   - Contains EPISTEMIC_ASSESSMENT: {'EPISTEMIC_ASSESSMENT' in result_without}")
    print(f"   - Contains FINAL_RESPONSE: {'FINAL_RESPONSE' in result_without}")
    print(f"   - Contains WEIGHTS: {'WEIGHTS' in result_without}")

    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_integrated_assessment())
