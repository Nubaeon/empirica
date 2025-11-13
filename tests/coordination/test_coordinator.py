#!/usr/bin/env python3
"""
Testing Coordinator for Empirica
Uses Qwen and Gemini via modality switcher to execute test phases
"""

import asyncio
import sys
from pathlib import Path

# Add empirica to path
sys.path.insert(0, str(Path(__file__).parent))

from empirica.plugins.modality_switcher.modality_switcher import ModalitySwitcher


class TestCoordinator:
    """Coordinates testing between Qwen, Gemini, and Claude"""
    
    def __init__(self):
        self.switcher = ModalitySwitcher()
        self.test_results = {
            "qwen": [],
            "gemini": [],
            "claude": []
        }
    
    async def assign_test_to_qwen(self, test_name: str, instructions: str):
        """Assign a test task to Qwen"""
        print(f"\n{'='*60}")
        print(f"🤖 ASSIGNING TO QWEN: {test_name}")
        print(f"{'='*60}\n")
        
        prompt = f"""
You are Qwen, testing the Empirica framework.

TEST: {test_name}

INSTRUCTIONS:
{instructions}

REPORT FORMAT:
1. Test Name: {test_name}
2. Status: PASS/FAIL/WARNING
3. Details: What you tested and results
4. Issues: Any problems found (with severity)
5. Recommendations: Suggested fixes

Execute this test and report your findings.
"""
        
        try:
            response = await self.switcher.route_query(
                prompt=prompt,
                context={"test": test_name, "ai": "qwen"},
                preferred_adapter="qwen"
            )
            
            self.test_results["qwen"].append({
                "test": test_name,
                "response": response
            })
            
            print(f"\n📊 QWEN RESPONSE:\n{response}\n")
            return response
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return None
    
    async def assign_test_to_gemini(self, test_name: str, instructions: str):
        """Assign a test task to Gemini"""
        print(f"\n{'='*60}")
        print(f"🤖 ASSIGNING TO GEMINI: {test_name}")
        print(f"{'='*60}\n")
        
        prompt = f"""
You are Gemini, validating the Empirica framework.

TEST: {test_name}

INSTRUCTIONS:
{instructions}

REPORT FORMAT:
1. Test Name: {test_name}
2. Status: PASS/FAIL/WARNING
3. Details: What you tested and results
4. Issues: Any problems found (with severity)
5. Recommendations: Suggested fixes

Execute this test and report your findings.
"""
        
        try:
            response = await self.switcher.route_query(
                prompt=prompt,
                context={"test": test_name, "ai": "gemini"},
                preferred_adapter="gemini"
            )
            
            self.test_results["gemini"].append({
                "test": test_name,
                "response": response
            })
            
            print(f"\n📊 GEMINI RESPONSE:\n{response}\n")
            return response
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return None
    
    async def run_phase_1_tests(self):
        """Phase 1: Post-Documentation Validation"""
        print("\n" + "="*60)
        print("🚀 PHASE 1: POST-DOCUMENTATION VALIDATION")
        print("="*60 + "\n")
        
        # Test 1: Installation (Qwen)
        await self.assign_test_to_qwen(
            test_name="Fresh Installation Test",
            instructions="""
1. Create fresh venv: python3 -m venv .venv-test-qwen
2. Activate: source .venv-test-qwen/bin/activate
3. Install: pip install -e .
4. Install deps: pip install -r requirements.txt
5. Test command: empirica --help
6. Verify: Should show all commands including 'onboard'

Report any errors, missing dependencies, or confusing steps.
"""
        )
        
        # Test 2: Onboarding (Gemini)
        await self.assign_test_to_gemini(
            test_name="Onboarding Experience Test",
            instructions="""
1. Run: empirica onboard --ai-id test-gemini
2. Complete all 6 phases
3. Verify: 
   - Post-onboarding reference points to docs/skills/SKILL.md
   - All links work
   - Checkpoint questions make sense
   - Learning delta is measured

Report the experience, any errors, and clarity of instructions.
"""
        )
        
        # Test 3: MCP Server (Qwen)
        await self.assign_test_to_qwen(
            test_name="MCP Server Test",
            instructions="""
1. Start server: python3 mcp_local/empirica_mcp_server.py
2. Verify it starts without errors
3. Check tool count: Should list 22 tools
4. Verify 'get_empirica_introduction' tool exists
5. Test calling the introduction tool

Report any startup errors, missing tools, or broken functionality.
"""
        )
        
        # Test 4: Documentation Links (Gemini)
        await self.assign_test_to_gemini(
            test_name="Documentation Cross-Reference Test",
            instructions="""
1. Check docs/README.md routing:
   - MCP AI path → 01_b_MCP_AI_START.md
   - AI learning path → 01_a_AI_AGENT_START.md
   - Human path → 02_INSTALLATION.md

2. Verify all links work in:
   - Root README.md
   - docs/01_a_AI_AGENT_START.md
   - docs/01_b_MCP_AI_START.md
   - docs/02_INSTALLATION.md

Report any broken links or incorrect routing.
"""
        )
    
    async def run_phase_2_tests(self):
        """Phase 2: Core Functionality"""
        print("\n" + "="*60)
        print("🚀 PHASE 2: CORE FUNCTIONALITY TESTING")
        print("="*60 + "\n")
        
        # Test 5: Canonical Assessment (Qwen)
        await self.assign_test_to_qwen(
            test_name="Canonical Epistemic Assessment Test",
            instructions="""
Test the core assessment functionality:

```python
from empirica.core.canonical import CanonicalEpistemicAssessor

assessor = CanonicalEpistemicAssessor(agent_id="test-qwen")
result = await assessor.assess(
    task="Explain quantum entanglement",
    context={"domain": "physics"}
)

# Verify:
1. Returns EpistemicAssessment object
2. Has 13 vectors (know, do, context, uncertainty, etc.)
3. Uses genuine LLM reasoning (no heuristics)
4. Scores are between 0.0 and 1.0
```

Report if assessment works and uses genuine reasoning.
"""
        )
        
        # Test 6: CASCADE Workflow (Gemini)
        await self.assign_test_to_gemini(
            test_name="CASCADE Workflow Test",
            instructions="""
Test the 7-phase CASCADE workflow:

```python
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

cascade = CanonicalEpistemicCascade(agent_id="test-gemini")
result = await cascade.run_epistemic_cascade(
    task="Write a function to sort a list",
    context={"language": "python"}
)

# Verify:
1. Completes all 7 phases
2. Preflight assessment recorded
3. Postflight assessment recorded
4. Delta calculated (postflight - preflight)
5. Calibration status provided
```

Report if workflow completes and delta is calculated.
"""
        )
    
    async def generate_final_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("📊 FINAL TEST REPORT")
        print("="*60 + "\n")
        
        report = []
        report.append("# Empirica Testing Report")
        report.append(f"\n**Date:** {Path(__file__).stat().st_mtime}")
        report.append("\n## Summary\n")
        
        # Qwen results
        report.append("### Qwen Tests\n")
        for result in self.test_results["qwen"]:
            report.append(f"**{result['test']}:**")
            report.append(f"```\n{result['response']}\n```\n")
        
        # Gemini results
        report.append("### Gemini Tests\n")
        for result in self.test_results["gemini"]:
            report.append(f"**{result['test']}:**")
            report.append(f"```\n{result['response']}\n```\n")
        
        # Save report
        report_text = "\n".join(report)
        report_path = Path(__file__).parent / "docs" / "tmp_rovodev_TEST_REPORT.md"
        report_path.write_text(report_text)
        
        print(f"✅ Report saved to: {report_path}")
        print(report_text)
        
        return report_text
    
    async def run_all_tests(self):
        """Execute all test phases"""
        try:
            # Phase 1
            await self.run_phase_1_tests()
            
            # Wait before phase 2
            print("\n⏸️  Pausing 10 seconds before Phase 2...\n")
            await asyncio.sleep(10)
            
            # Phase 2
            await self.run_phase_2_tests()
            
            # Generate report
            await self.generate_final_report()
            
        except Exception as e:
            print(f"\n❌ TESTING FAILED: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Main entry point"""
    coordinator = TestCoordinator()
    
    print("""
╔════════════════════════════════════════════════════════════╗
║          EMPIRICA TESTING COORDINATOR                      ║
║  Coordinating Qwen + Gemini for comprehensive testing     ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    await coordinator.run_all_tests()
    
    print("""
╔════════════════════════════════════════════════════════════╗
║          TESTING COMPLETE                                  ║
║  Review results in docs/tmp_rovodev_TEST_REPORT.md        ║
╚════════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    asyncio.run(main())
