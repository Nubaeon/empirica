"""
Onboarding Command - Interactive Introduction to Empirica

Simplified onboarding for new users. Shows the core CASCADE workflow
without outdated bootstrap ceremony.
"""

import sys
from ..cli_utils import handle_cli_error


def handle_onboard_command(args):
    """Interactive onboarding wizard for new users"""
    try:
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║  🧠 Welcome to Empirica - Epistemic Self-Awareness for AI Agents    ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

Empirica helps AI agents track what they KNOW, what they can DO, and
how UNCERTAIN they are - throughout any task.

═══════════════════════════════════════════════════════════════════════

📚 CORE CONCEPTS

1. 13-Vector Epistemic State
   Every assessment uses 13 dimensions to track your knowledge:
   
   TIER 0 (Foundation): KNOW, DO, CONTEXT
   TIER 1 (Comprehension): CLARITY, COHERENCE, SIGNAL, DENSITY
   TIER 2 (Execution): STATE, CHANGE, COMPLETION, IMPACT
   
   Gate: ENGAGEMENT (must be ≥ 0.6)
   Meta: UNCERTAINTY (explicit uncertainty tracking)

2. CASCADE Workflow
   PREFLIGHT → [INVESTIGATE → CHECK]* → ACT → POSTFLIGHT
   
   - PREFLIGHT: Assess before starting (what do you know?)
   - INVESTIGATE: Fill knowledge gaps (reduce uncertainty)
   - CHECK: Validate readiness (proceed or investigate more?)
   - ACT: Do the work
   - POSTFLIGHT: Reflect on learning (what did you learn?)

3. Session-Based Tracking
   Create a session to track epistemic state across workflow:
   
   $ empirica session-create --ai-id myai
   
   This stores your assessments in SQLite + git notes for continuity.

═══════════════════════════════════════════════════════════════════════

🚀 QUICK START

Step 1: Create a session
   $ empirica session-create --ai-id myai --output json
   # Returns session_id

Step 2: Run PREFLIGHT assessment
   $ empirica preflight --session-id <ID> --prompt "Your task"
   # Returns self-assessment prompt

Step 3: Submit your assessment (as JSON)
   $ empirica preflight-submit \\
       --session-id <ID> \\
       --vectors '{"engagement":0.8,"know":0.6,...}' \\
       --reasoning "Your honest self-assessment"

Step 4: Do your work...

Step 5: Run POSTFLIGHT to measure learning
   $ empirica postflight-submit \\
       --session-id <ID> \\
       --vectors '{"engagement":0.9,"know":0.85,...}' \\
       --reasoning "What you learned"

Step 6: Get calibration report
   $ empirica sessions-show --session-id <ID>
   # Shows learning delta: PREFLIGHT → POSTFLIGHT

═══════════════════════════════════════════════════════════════════════

💡 KEY PRINCIPLES

1. Genuine Self-Assessment
   Rate what you ACTUALLY know, not what you hope to figure out.
   High uncertainty → triggers INVESTIGATE phase.

2. No Bootstrap Ceremony
   Sessions create instantly. Components lazy-load on demand.
   No pre-configuration needed.

3. Epistemic Transparency
   Track your uncertainty explicitly. Admit what you don't know.
   This builds trust and enables systematic investigation.

4. Measurable Learning
   Compare PREFLIGHT vs POSTFLIGHT to see epistemic growth:
   - KNOW increase = learned domain knowledge
   - DO increase = built capability
   - UNCERTAINTY decrease = reduced ambiguity

═══════════════════════════════════════════════════════════════════════

📖 EXAMPLES

Python API:
   from empirica.data.session_database import SessionDatabase
   from empirica.core.canonical import GitEnhancedReflexLogger
   
   # Create session
   db = SessionDatabase()
   session_id = db.create_session(ai_id="myai")
   db.close()
   
   # Log assessment
   logger = ReflexLogger(session_id=session_id)
   logger.log_reflex(
       phase="PREFLIGHT",
       # round auto-increments
       vectors={"engagement": 0.8, "know": 0.6, ...},
       reasoning="Starting with moderate knowledge"
   )

MCP Tool (for AI agents):
   # Create session
   session_create(ai_id="myai")

   # Execute workflow
   execute_preflight(session_id=sid, prompt="Task")
   submit_preflight_assessment(session_id=sid, vectors={...})
   execute_postflight(session_id=sid, task_summary="Done")

═══════════════════════════════════════════════════════════════════════

📚 NEXT STEPS

1. Try the quick start above
2. Read the docs: docs/production/03_BASIC_USAGE.md
3. Explore Python API: docs/production/13_PYTHON_API.md
4. Understand CASCADE: docs/production/06_CASCADE_FLOW.md

═══════════════════════════════════════════════════════════════════════

❓ QUESTIONS?

- When should I use CHECK?
  After INVESTIGATE, to validate readiness before ACT

- What if I don't know my vectors?
  Use preflight --prompt-only to get self-assessment prompt

- How do I resume after memory compression?
  Use handoff reports or git checkpoints for continuity

═══════════════════════════════════════════════════════════════════════

For detailed documentation:
  $ cd docs/production/
  $ cat 03_BASIC_USAGE.md

For help with specific commands:
  $ empirica <command> --help

Happy epistemic tracking! 🧠✨
        """)
        
    except Exception as e:
        handle_cli_error(e, "Onboarding", getattr(args, 'verbose', False))
        sys.exit(1)
