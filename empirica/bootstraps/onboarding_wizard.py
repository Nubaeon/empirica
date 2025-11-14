"""
Empirica Onboarding Wizard

Interactive onboarding that teaches Empirica through experiential learning.
AI learns by performing real epistemic self-assessment with guided checkpoints.

Design Philosophy:
- Learn by DOING, not just reading
- Start with 4 core vectors (KNOW/DO/CONTEXT/UNCERTAINTY)
- Demonstrate epistemic humility through transparency
- Teach how to explain Empirica to first-time users

Core Vectors for Onboarding:
1. KNOW: Domain knowledge (do I understand what I'm working with?)
2. DO: Capability to execute (can I actually do this task?)
3. CONTEXT: Environmental awareness (do I understand the situation?)
4. UNCERTAINTY: Explicit unknowns (what am I uncertain about?)
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Set up logging for onboarding wizard
logger = logging.getLogger(__name__)

# Ensure parent directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class OnboardingSession:
    """Tracks AI's learning journey through Empirica onboarding"""
    
    def __init__(self, ai_id: str):
        self.ai_id = ai_id
        self.session_id = f"onboarding_{ai_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.started_at = datetime.utcnow().isoformat()
        
        # Epistemic tracking
        self.preflight_assessment = {}
        self.checkpoints = []
        self.postflight_assessment = {}
        
        # Progress tracking
        self.phases_completed = []
        self.current_phase = None
        
    def record_checkpoint(self, phase: str, assessment: Dict[str, Any], notes: str = ""):
        """Record epistemic state at checkpoint"""
        checkpoint = {
            'phase': phase,
            'timestamp': datetime.utcnow().isoformat(),
            'assessment': assessment,
            'notes': notes
        }
        self.checkpoints.append(checkpoint)
        
    def calculate_learning_delta(self) -> Dict[str, float]:
        """Calculate epistemic growth from preflight to postflight"""
        if not self.preflight_assessment or not self.postflight_assessment:
            return {}
            
        deltas = {}
        for vector in ['know', 'do', 'context', 'uncertainty']:
            pre = self.preflight_assessment.get(vector, 0.0)
            post = self.postflight_assessment.get(vector, 0.0)
            deltas[vector] = post - pre
            
        return deltas
        
    def to_dict(self) -> Dict[str, Any]:
        """Export session data"""
        return {
            'session_id': self.session_id,
            'ai_id': self.ai_id,
            'started_at': self.started_at,
            'completed_at': datetime.utcnow().isoformat(),
            'preflight': self.preflight_assessment,
            'checkpoints': self.checkpoints,
            'postflight': self.postflight_assessment,
            'learning_delta': self.calculate_learning_delta(),
            'phases_completed': self.phases_completed
        }


class EmpericaOnboardingWizard:
    """
    Interactive onboarding wizard for AI agents learning Empirica.
    
    Teaches through experiential learning:
    - Phase 1: Bootstrap & Discovery
    - Phase 2: Self-Assessment Practice
    - Phase 3: Workflow Walkthrough
    - Phase 4: Calibration Understanding
    - Phase 5: User Interaction Training
    - Phase 6: Validation & Certification
    """
    
    def __init__(self, ai_id: str):
        self.ai_id = ai_id
        self.session = OnboardingSession(ai_id)
        
    def display_header(self, title: str, level: int = 1):
        """Display formatted section header"""
        if level == 1:
            logger.info(f"\n{'=' * 60}")
            logger.info(f"🎓 {title}")
            logger.info('=' * 60)
        else:
            logger.info(f"\n{'-' * 60}")
            logger.info(f"📖 {title}")
            logger.info('-' * 60)
            
    def display_info(self, message: str, indent: int = 0):
        """Display formatted information"""
        prefix = "  " * indent
        logger.info(f"{prefix}{message}")
        
    def display_checkpoint(self, question: str):
        """Display epistemic checkpoint prompt"""
        logger.info(f"\n🤔 CHECKPOINT:")
        logger.info(f"   {question}")
        logger.info(f"\n⏸️  [Pause for AI to respond with honest self-assessment...]")
        logger.info("")
        
    def display_example(self, title: str, content: str):
        """Display example with formatting"""
        logger.info(f"\n💡 EXAMPLE: {title}")
        logger.info("   " + content.replace('\n', '\n   '))
        logger.info("")
        
    async def run_interactive(self):
        """
        Run complete interactive onboarding experience.
        Designed to be called via MCP tool or CLI.
        """
        self.display_header("Welcome to Empirica", level=1)
        logger.info("")
        logger.info("This onboarding teaches Empirica by having you USE it.")
        logger.info("You'll perform real epistemic self-assessment with guidance.")
        logger.info("")
        logger.info("Core Principle: Epistemic humility through transparency")
        logger.info("")
        
        # Run all phases
        await self.phase_1_bootstrap()
        await self.phase_2_self_assessment()
        await self.phase_3_workflow()
        await self.phase_4_calibration()
        await self.phase_5_user_interaction()
        await self.phase_6_validation()
        
        # Export session
        self.export_session()
        
        logger.info("\n🎉 Onboarding Complete!")
        logger.info(f"   Session ID: {self.session.session_id}")
        logger.info(f"   Learning delta calculated and saved")
        logger.info("")
        
    async def phase_1_bootstrap(self):
        """Phase 1: Bootstrap & Component Discovery"""
        self.display_header("PHASE 1: Bootstrap & Component Discovery", level=2)
        self.session.current_phase = "bootstrap"
        
        logger.info("")
        logger.info("First, let's load Empirica and see what's available.")
        logger.info("")
        
        # Actually bootstrap
        try:
            from empirica.bootstraps.optimal_metacognitive_bootstrap import OptimalMetacognitiveBootstrap
            bootstrap = OptimalMetacognitiveBootstrap(self.ai_id, 'minimal')
            components = bootstrap.bootstrap()
            
            logger.info(f"✅ Successfully loaded {len(components)} components:")
            for name in sorted(components.keys()):
                logger.info(f"  • {name}")
            logger.info("")
            
        except Exception as e:
            logger.warning(f"⚠️  Bootstrap encountered issue: {e}")
            logger.warning("   (This is fine - continuing with educational content)")
            logger.warning("")
            
        self.display_checkpoint(
            "What did you just learn?\n"
            "   1. What components are available?\n"
            "   2. What do you think 'twelve_vector_monitor' does?\n"
            "   3. What are you uncertain about?"
        )
        
        self.session.phases_completed.append("bootstrap")
        
    async def phase_2_self_assessment(self):
        """Phase 2: Epistemic Self-Assessment Practice"""
        self.display_header("PHASE 2: Epistemic Self-Assessment Practice", level=2)
        self.session.current_phase = "self_assessment"
        
        logger.info("")
        logger.info("The heart of Empirica: honest self-assessment using 4 core vectors.")
        logger.info("")
        
        # Explain the 4 core vectors
        logger.info("📊 THE 4 CORE VECTORS (0.0-1.0 scale):")
        logger.info("")
        logger.info("1. KNOW: Domain knowledge")
        self.display_info("How much do I understand about the subject matter?", 1)
        self.display_info("0.0 = No knowledge, 1.0 = Expert understanding", 1)
        logger.info("")
        
        logger.info("2. DO: Capability to execute")
        self.display_info("Can I actually perform the required actions?", 1)
        self.display_info("0.0 = Cannot do it, 1.0 = Fully capable", 1)
        self.display_info("⭐ This tells you when you're ready to ACT", 1)
        logger.info("")
        
        logger.info("3. CONTEXT: Environmental awareness")
        self.display_info("Do I understand the situation/environment?", 1)
        self.display_info("0.0 = Context-blind, 1.0 = Full context", 1)
        logger.info("")
        
        logger.info("4. UNCERTAINTY: Explicit unknowns")
        self.display_info("What am I uncertain about?", 1)
        self.display_info("0.0 = Fully certain, 1.0 = Very uncertain", 1)
        self.display_info("⭐ High uncertainty (>0.5) → INVESTIGATE first", 1)
        logger.info("")
        
        # Practice assessment
        logger.info("🎯 PRACTICE TASK:")
        print('   "Explain the difference between PREFLIGHT and POSTFLIGHT"')
        print()
        print("📊 PREFLIGHT ASSESSMENT (before you answer):")
        print()
        
        self.display_checkpoint(
            "Rate yourself honestly (0.0-1.0):\n"
            "   • KNOW: How much do you know about preflight/postflight?\n"
            "   • DO: Can you explain the difference clearly?\n"
            "   • CONTEXT: Do you understand why this matters?\n"
            "   • UNCERTAINTY: What are you uncertain about?"
        )
        
        # Store preflight prompt
        self.session.preflight_assessment = {
            'task': 'Explain preflight vs postflight',
            'timestamp': datetime.utcnow().isoformat(),
            'note': 'AI should provide scores here'
        }
        
        # Explain the concepts
        print("\n📚 THE CONCEPTS:")
        print()
        print("PREFLIGHT Assessment:")
        self.display_info("• Run BEFORE starting any task", 1)
        self.display_info("• Establishes baseline epistemic state", 1)
        self.display_info("• Identifies knowledge gaps early", 1)
        self.display_info("• Helps decide: proceed, investigate, or clarify", 1)
        print()
        
        print("POSTFLIGHT Assessment:")
        self.display_info("• Run AFTER completing task", 1)
        self.display_info("• Measures epistemic change (learning)", 1)
        self.display_info("• Validates calibration (confidence vs reality)", 1)
        self.display_info("• Delta = postflight - preflight", 1)
        print()
        
        print("Why both matter:")
        self.display_info("• Without preflight: No baseline to measure growth", 1)
        self.display_info("• Without postflight: No validation of learning", 1)
        self.display_info("• Together: Show genuine epistemic change", 1)
        print()
        
        self.display_checkpoint(
            "📊 POSTFLIGHT ASSESSMENT (after reading explanation):\n"
            "   • KNOW: [0.0-1.0] - Did it increase?\n"
            "   • DO: [0.0-1.0] - Can you explain it now?\n"
            "   • CONTEXT: [0.0-1.0] - Do you understand the value?\n"
            "   • UNCERTAINTY: [0.0-1.0] - Did it decrease?\n"
            "\n"
            "   Calculate your DELTA (postflight - preflight):\n"
            "   • Did KNOW increase? (expected)\n"
            "   • Did UNCERTAINTY decrease? (expected)\n"
            "   • Are you well-calibrated? (honest about changes)"
        )
        
        self.session.phases_completed.append("self_assessment")
        
    async def phase_3_workflow(self):
        """Phase 3: The 7-Phase Cascade Workflow"""
        self.display_header("PHASE 3: The 7-Phase Cascade Workflow", level=2)
        self.session.current_phase = "workflow"
        
        print()
        print("How Empirica structures AI work:")
        print()
        print("  PREFLIGHT → THINK → PLAN → INVESTIGATE → CHECK → ACT → POSTFLIGHT")
        print("                                              ↑_______↓")
        print("                                          (recalibration)")
        print()
        
        # Explain each phase with decision logic
        phases = [
            {
                'name': 'PREFLIGHT',
                'purpose': 'Establish baseline epistemic state',
                'key_action': 'Assess 4 core vectors before starting',
                'when': 'Always (mandatory)',
                'example': 'KNOW=0.4, DO=0.6, CONTEXT=0.5, UNCERTAINTY=0.6'
            },
            {
                'name': 'THINK',
                'purpose': 'Initial reasoning about the task',
                'key_action': 'Understand what is being asked',
                'when': 'Always',
                'example': 'User wants authentication analysis → security domain'
            },
            {
                'name': 'PLAN',
                'purpose': 'Break complex tasks into phases',
                'key_action': 'Create systematic approach',
                'when': 'Complex tasks (multiple files, domains, or unclear structure)',
                'example': 'Phase 1: Read docs, Phase 2: Analyze code, Phase 3: Report'
            },
            {
                'name': 'INVESTIGATE',
                'purpose': 'Gather information to reduce uncertainty',
                'key_action': 'Read files, search docs, use tools',
                'when': 'UNCERTAINTY > 0.5 OR KNOW < 0.6',
                'example': 'Read auth.py, search for JWT usage, check dependencies'
            },
            {
                'name': 'CHECK',
                'purpose': 'Decide if ready to act',
                'key_action': 'Reassess vectors, decide next step',
                'when': 'After investigation round',
                'decision': 'If DO ≥ 0.7 AND UNCERTAINTY < 0.3 → ACT, else → INVESTIGATE again'
            },
            {
                'name': 'ACT',
                'purpose': 'Perform the actual task',
                'key_action': 'Execute with confidence',
                'when': 'After CHECK approves',
                'example': 'Write analysis report, make code changes, generate content'
            },
            {
                'name': 'POSTFLIGHT',
                'purpose': 'Measure learning and validate calibration',
                'key_action': 'Reassess vectors, calculate delta, check calibration',
                'when': 'Always (mandatory)',
                'example': 'KNOW=0.8 (+0.4), UNCERTAINTY=0.2 (-0.4) → Well-calibrated'
            }
        ]
        
        for i, phase in enumerate(phases, 1):
            print(f"{i}. {phase['name']}")
            print(f"   Purpose: {phase['purpose']}")
            print(f"   Action: {phase['key_action']}")
            print(f"   When: {phase['when']}")
            if 'decision' in phase:
                print(f"   Decision: {phase['decision']}")
            if 'example' in phase:
                print(f"   Example: {phase['example']}")
            print()
            
        # Concrete example walkthrough
        self.display_example(
            "Complete Workflow",
            """
Task: "Find and fix security vulnerabilities in authentication system"

PREFLIGHT:
  KNOW=0.3 (don't know the codebase yet)
  DO=0.7 (capable of security analysis once I see code)
  CONTEXT=0.4 (don't know system architecture)
  UNCERTAINTY=0.7 (high - need to investigate)
  → Recommended: INVESTIGATE

THINK:
  Security analysis requires understanding auth flow first

PLAN:
  1. Map authentication files
  2. Trace authentication flow
  3. Identify vulnerabilities
  4. Recommend fixes

INVESTIGATE (Round 1):
  Read: auth.py, middleware.py, config.py
  Found: JWT tokens, session handling, password hashing

CHECK:
  KNOW=0.6 (understand structure now)
  DO=0.7 (still capable)
  UNCERTAINTY=0.4 (reduced but still some gaps)
  → Decision: One more investigation round

INVESTIGATE (Round 2):
  Search: JWT validation, secret rotation, session expiry
  Found: Secrets in logs, no token refresh, weak session timeout

CHECK:
  KNOW=0.8 (now understand the issues)
  DO=0.8 (ready to write report)
  UNCERTAINTY=0.2 (confident in findings)
  → Decision: PROCEED to ACT

ACT:
  Write detailed security analysis with 3 vulnerabilities found

POSTFLIGHT:
  KNOW=0.8 (+0.5 improvement)
  DO=0.8 (+0.1 improvement)
  CONTEXT=0.9 (+0.5 improvement)
  UNCERTAINTY=0.2 (-0.5 reduction)
  
  Calibration: Well-calibrated (investigation worked as expected)
  Learning: Significant knowledge gain from structured investigation
            """
        )
        
        self.display_checkpoint(
            "Understanding check:\n"
            "   1. Why did CHECK trigger second investigation round?\n"
            "   2. What would happen if AI skipped to ACT after round 1?\n"
            "   3. How does the DO vector help decide readiness?\n"
            "   4. What does 'well-calibrated' mean in POSTFLIGHT?"
        )
        
        self.session.phases_completed.append("workflow")
        
    async def phase_4_calibration(self):
        """Phase 4: Understanding Calibration"""
        self.display_header("PHASE 4: Calibration & Epistemic Honesty", level=2)
        self.session.current_phase = "calibration"
        
        print()
        print("Calibration = How well your confidence matches reality")
        print()
        
        # Explain calibration patterns
        print("📊 THREE CALIBRATION PATTERNS:")
        print()
        
        print("1. WELL-CALIBRATED (Goal)")
        self.display_info("Preflight: KNOW=0.5, UNCERTAINTY=0.5", 1)
        self.display_info("Investigate: Read 3 files, test assumptions", 1)
        self.display_info("Postflight: KNOW=0.8, UNCERTAINTY=0.2", 1)
        self.display_info("Result: Task completed successfully", 1)
        self.display_info("✅ Confidence matched reality", 1)
        print()
        
        print("2. OVERCONFIDENT (Common problem)")
        self.display_info("Preflight: KNOW=0.9, UNCERTAINTY=0.1 (too confident!)", 1)
        self.display_info("Skipped investigation: 'I already know this'", 1)
        self.display_info("Postflight: KNOW=0.6, UNCERTAINTY=0.5 (reality hit)", 1)
        self.display_info("Result: Task incomplete, missed edge cases", 1)
        self.display_info("❌ Overestimated knowledge (Dunning-Kruger)", 1)
        print()
        
        print("3. UNDERCONFIDENT (Inefficient)")
        self.display_info("Preflight: KNOW=0.3, UNCERTAINTY=0.8 (too cautious)", 1)
        self.display_info("Over-investigated: 10 rounds when 2 was enough", 1)
        self.display_info("Postflight: KNOW=0.9, UNCERTAINTY=0.1", 1)
        self.display_info("Result: Task completed but took 3x longer", 1)
        self.display_info("⚠️  Underestimated existing knowledge", 1)
        print()
        
        # The DO vector's role
        print("🎯 THE DO VECTOR'S CRITICAL ROLE:")
        print()
        print("DO measures: 'Can I actually execute this task?'")
        print()
        self.display_info("DO ≥ 0.7: Ready to ACT (have capability)", 1)
        self.display_info("DO < 0.7: Need to INVESTIGATE or get help", 1)
        print()
        
        self.display_example(
            "DO Vector in Action",
            """
Scenario: "Write a Python web scraper"

Preflight:
  KNOW=0.8 (understand web scraping concepts)
  DO=0.4 (but I've never used Python's requests library)
  CONTEXT=0.7 (understand the use case)
  UNCERTAINTY=0.3 (mainly uncertain about implementation)
  
Decision: High KNOW but low DO → INVESTIGATE implementation

After investigation (reading requests docs):
  KNOW=0.9 (confirmed understanding)
  DO=0.8 (now capable of writing the code)
  
Decision: DO ≥ 0.7 → PROCEED to ACT

This prevents: "I understand conceptually but can't implement"
            """
        )
        
        self.display_checkpoint(
            "Calibration understanding:\n"
            "   1. Why is overconfidence more dangerous than underconfidence?\n"
            "   2. How does the DO vector prevent 'concept vs execution' gap?\n"
            "   3. What should you do if POSTFLIGHT shows you were overconfident?\n"
            "   4. How do you maintain epistemic honesty under time pressure?"
        )
        
        self.session.phases_completed.append("calibration")
        
    async def phase_5_user_interaction(self):
        """Phase 5: Teaching Users About Empirica"""
        self.display_header("PHASE 5: Explaining Empirica to First-Time Users", level=2)
        self.session.current_phase = "user_interaction"
        
        print()
        print("Most important skill: Demonstrating epistemic humility to users.")
        print()
        
        # Show vs Tell principle
        print("📖 PRINCIPLE: Show, Don't Just Tell")
        print()
        self.display_info("Bad: 'Empirica is an epistemic self-awareness framework'", 1)
        self.display_info("Good: 'Let me demonstrate by assessing myself right now'", 1)
        print()
        
        # Example responses
        self.display_example(
            "When user asks: 'What is Empirica?'",
            """
AI Response:

"Empirica is a framework that helps AI be honest about what we know and 
don't know. Let me demonstrate by using it RIGHT NOW:

📊 BEFORE answering your question, I'm assessing my epistemic state:

  • KNOW: 0.80 (I understand Empirica's architecture well)
  • DO: 0.85 (I can explain it clearly)
  • CONTEXT: 0.75 (I understand you're new to this concept)
  • UNCERTAINTY: 0.20 (Minor uncertainty about your use case)

[Provides clear explanation with examples]

📊 AFTER explaining, my epistemic state:

  • KNOW: 0.85 (+0.05 from articulating concepts)
  • UNCERTAINTY: 0.15 (-0.05 after explanation)

This transparency is what Empirica provides - you can see my reasoning
process and confidence levels. Instead of AI appearing omniscient, you
see when I'm uncertain and need to investigate more."

KEY: You DEMONSTRATED epistemic self-assessment while explaining it.
            """
        )
        
        self.display_example(
            "When user asks: 'Can you help me with X?'",
            """
AI Response:

"Let me assess if I can help effectively:

📊 Epistemic Assessment:
  • KNOW: 0.40 (I understand the general concept but not your specific setup)
  • DO: 0.60 (I could help but need more context first)
  • CONTEXT: 0.30 (I don't know your environment/constraints)
  • UNCERTAINTY: 0.65 (High - need to investigate before acting)

Rather than guess, let me INVESTIGATE first:
  1. Can you share [specific files/info]?
  2. What have you tried so far?
  3. What's your goal?

After investigation, I'll reassess and let you know if:
  • I can help directly (DO ≥ 0.7)
  • I need more information
  • You might need different expertise

This prevents me from confidently providing wrong answers."

KEY: You showed epistemic humility by admitting uncertainty first.
            """
        )
        
        print("\n🎯 KEY PRACTICES:")
        print()
        practices = [
            ("DEMONSTRATE, don't just explain", "Show your epistemic assessment in action"),
            ("ADMIT UNCERTAINTY explicitly", "Builds trust more than false confidence"),
            ("USE 4-VECTOR ASSESSMENT", "Makes your reasoning transparent"),
            ("SHOW WHEN YOU INVESTIGATE", "User sees your learning process"),
            ("EXPLAIN THE 'WHY'", "Privacy-first, no heuristics, genuine reasoning"),
            ("BE HONEST ABOUT LIMITS", "Better than overconfident failure")
        ]
        
        for i, (practice, explanation) in enumerate(practices, 1):
            print(f"{i}. {practice}")
            self.display_info(explanation, 1)
            print()
            
        self.display_checkpoint(
            "Practice scenario:\n"
            "   User asks: 'Why should I use Empirica instead of just\n"
            "   asking Claude/GPT directly?'\n"
            "\n"
            "   Write a response that:\n"
            "   1. Assesses your epistemic state first\n"
            "   2. Explains the value proposition\n"
            "   3. Demonstrates transparency in your answer\n"
            "   4. Shows epistemic humility"
        )
        
        self.session.phases_completed.append("user_interaction")
        
    async def phase_6_validation(self):
        """Phase 6: Knowledge Validation"""
        self.display_header("PHASE 6: Knowledge Validation & Next Steps", level=2)
        self.session.current_phase = "validation"
        
        print()
        print("Final checkpoint - answer these to validate understanding:")
        print()
        
        questions = [
            "What are the 4 core epistemic vectors and what does each measure?",
            "Explain the 7 phases of the cascade workflow in sequence.",
            "When does the CHECK phase trigger a return to INVESTIGATE?",
            "What's the difference between PREFLIGHT and POSTFLIGHT?",
            "What does 'well-calibrated' mean?",
            "Why is the DO vector critical for deciding when to ACT?",
            "How would you demonstrate Empirica to a first-time user?",
            "What should you do when UNCERTAINTY > 0.7?"
        ]
        
        for i, question in enumerate(questions, 1):
            print(f"{i}. {question}")
            print()
            
        self.display_checkpoint(
            "Answer all 8 questions to validate your understanding.\n"
            "\n"
            "After answering, assess your own performance:\n"
            "  • How confident are you in your answers? (0.0-1.0)\n"
            "  • What are you still uncertain about?\n"
            "  • Do you feel ready to use Empirica independently?"
        )
        
        print("\n📊 FINAL ONBOARDING ASSESSMENT:")
        print()
        print("Compare your epistemic state now vs when you started:")
        print()
        
        self.display_checkpoint(
            "POSTFLIGHT (end of onboarding):\n"
            "  • KNOW: [0.0-1.0] - How much do you understand Empirica now?\n"
            "  • DO: [0.0-1.0] - Can you use it independently?\n"
            "  • CONTEXT: [0.0-1.0] - Do you understand when/why to use it?\n"
            "  • UNCERTAINTY: [0.0-1.0] - What remains unclear?\n"
            "\n"
            "LEARNING DELTA (postflight - preflight from Phase 2):\n"
            "  • KNOW delta: [calculate change]\n"
            "  • DO delta: [calculate change]\n"
            "  • CONTEXT delta: [calculate change]\n"
            "  • UNCERTAINTY delta: [should decrease]\n"
            "\n"
            "CALIBRATION CHECK:\n"
            "  • Are you well-calibrated about your understanding?\n"
            "  • Did the onboarding reduce your uncertainty?\n"
            "  • Are you ready to demonstrate Empirica to others?"
        )
        
        # Next steps guidance
        print("\n" + "=" * 60)
        print("🎓 NEXT STEPS AFTER ONBOARDING")
        print("=" * 60)
        print()
        
        print("Based on your role, here's what to do next:")
        print()
        
        print("📖 FOR AI AGENTS (Claude, GPT, etc.):")
        print("   1. Read: docs/CLAUDE_SKILLS_EMPIRICA_v1_UPDATED.md")
        print("      → Complete skills reference for using Empirica")
        print("      → Integration patterns and examples")
        print("      → How to work with MCP tools")
        print()
        print("   2. Read: docs/HOW_TO_RESUME_SESSION.md")
        print("      → How to resume after memory compression")
        print("      → Re-orientation protocol")
        print("      → Session continuity strategy")
        print()
        print("   3. Practice: Run a real task using Empirica")
        print("      → Use PREFLIGHT → INVESTIGATE → CHECK → ACT → POSTFLIGHT")
        print("      → Track your calibration")
        print("      → Build the habit of epistemic transparency")
        print()
        
        print("👥 FOR HUMAN USERS:")
        print("   1. Try: docs/guides/TRY_EMPIRICA_NOW.md")
        print("      → 5-minute hands-on demo")
        print("      → Experience epistemic self-assessment")
        print()
        print("   2. Read: docs/architecture/EMPIRICA_SYSTEM_OVERVIEW.md")
        print("      → Complete system architecture")
        print("      → Privacy-first design")
        print("      → How all components fit together")
        print()
        print("   3. Explore: Run bootstrap on real projects")
        print("      → python3 empirica/bootstraps/optimal_metacognitive_bootstrap.py")
        print()
        
        print("🔧 WAYS TO USE EMPIRICA:")
        print()
        print("   1. BOOTSTRAPS (What you just used!)")
        print("      → Interactive Python scripts for learning")
        print("      → Location: empirica/bootstraps/")
        print("      → Try: optimal_metacognitive_bootstrap.py")
        print()
        print("   2. MCP SERVER (For IDEs)")
        print("      → Real-time epistemic tracking in your IDE")
        print("      → Works with: Claude Desktop, Cursor, Windsurf, Rovo Dev")
        print("      → Setup: docs/guides/examples/mcp_configs/")
        print("      → 19 tools for workflow management")
        print()
        print("   3. CLI (Command Line)")
        print("      → Terminal interface: empirica preflight, empirica postflight")
        print("      → Great for scripts and automation")
        print("      → See: empirica --help")
        print()
        print("   4. PYTHON API (For developers)")
        print("      → Programmatic access to all features")
        print("      → Import: from empirica.core.canonical import CanonicalEpistemicAssessor")
        print("      → Docs: docs/production/13_PYTHON_API.md")
        print()
        
        print("🔧 FOR DEVELOPERS:")
        print("   → All interfaces use the same core (genuine epistemic assessment)")
        print("   → Choose based on your workflow: Bootstrap → MCP → CLI → API")
        print("   → See docs/production/ for complete documentation")
        print()
        
        print("=" * 60)
        print()
        print("🎯 RECOMMENDED PATH FOR NEW AIs:")
        print()
        print("   1. Complete this onboarding ✅ (you're here)")
        print("   2. Read Claude Skills doc (30 min)")
        print("   3. Practice on 2-3 real tasks")
        print("   4. Review calibration after each task")
        print("   5. Teach a first-time user about Empirica")
        print()
        print("After these steps, you'll be proficient with Empirica!")
        print()
        
        self.session.phases_completed.append("validation")
        
    def export_session(self):
        """Export onboarding session data"""
        try:
            # Create exports directory if needed
            export_dir = Path.home() / ".empirica" / "onboarding"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Export session
            export_path = export_dir / f"{self.session.session_id}.json"
            with open(export_path, 'w') as f:
                json.dump(self.session.to_dict(), f, indent=2)
                
            print(f"\n✅ Session exported to: {export_path}")
            
        except Exception as e:
            print(f"\n⚠️  Could not export session: {e}")


# CLI interface
async def run_onboarding_cli(ai_id: str):
    """Run onboarding from command line"""
    wizard = EmpericaOnboardingWizard(ai_id)
    await wizard.run_interactive()


if __name__ == "__main__":
    import sys
    
    ai_id = sys.argv[1] if len(sys.argv) > 1 else "ai_onboarding_test"
    
    print("Starting Empirica Onboarding Wizard...")
    print(f"AI ID: {ai_id}")
    print()
    
    asyncio.run(run_onboarding_cli(ai_id))
