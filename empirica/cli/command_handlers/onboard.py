"""
Onboarding Command - Interactive Introduction to Empirica

Shows the current Empirica capabilities, CASCADE workflow, and quick start guide.
"""

import sys
from ..cli_utils import handle_cli_error


def handle_onboard_command(args):
    """Interactive onboarding guide for new users"""
    try:
        ai_id = getattr(args, 'ai_id', 'claude-code')

        print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║  Empirica - Epistemic Self-Awareness for AI Agents                   ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

Empirica helps AI agents track what they KNOW, what they can DO, and
how UNCERTAIN they are - throughout any task. It measures learning,
detects overconfidence, and builds calibration over time.

═══════════════════════════════════════════════════════════════════════

CORE CONCEPTS

1. 13-Vector Epistemic State
   Every assessment uses 13 dimensions to track your knowledge:

   Foundation:    KNOW, DO, CONTEXT
   Comprehension: CLARITY, COHERENCE, SIGNAL, DENSITY
   Execution:     STATE, CHANGE, COMPLETION, IMPACT
   Gate:          ENGAGEMENT
   Meta:          UNCERTAINTY (higher = more uncertain)

2. CASCADE Workflow (Epistemic Transactions)
   PREFLIGHT --> CHECK --> POSTFLIGHT --> POST-TEST

   - PREFLIGHT:  Assess baseline before starting (what do you know?)
   - CHECK:      Sentinel gate - ready to act, or investigate more?
   - POSTFLIGHT: Measure learning delta (what did you learn?)
   - POST-TEST:  Automatic grounded verification against objective evidence

3. Noetic vs Praxic Phases
   - Noetic:  Investigation (read, search, explore, log findings)
   - Praxic:  Action (write code, edit files, commit)
   - The Sentinel gates praxic tools until CHECK passes

4. Dual-Track Calibration
   - Track 1 (Self-Referential): PREFLIGHT vs POSTFLIGHT delta
   - Track 2 (Grounded): Self-assessment vs objective evidence (tests, git, goals)
   - Bias corrections computed automatically from your history

═══════════════════════════════════════════════════════════════════════

QUICK START

Step 1: Initialize project (once per repo)
   $ cd /path/to/your/git/repo
   $ empirica project-init

Step 2: Create a session
   $ empirica session-create --ai-id {ai_id} --output json

Step 3: Load project context
   $ empirica project-bootstrap --output json

Step 4: Create a goal for your task
   $ empirica goals-create --objective "What you're trying to do"

Step 5: Run PREFLIGHT (opens a transaction)
   $ empirica preflight-submit - << 'EOF'
   {{
     "task_context": "What you're about to do",
     "vectors": {{"know": 0.6, "uncertainty": 0.4, "context": 0.7, "clarity": 0.8}},
     "reasoning": "Honest assessment of current state"
   }}
   EOF

Step 6: Investigate (noetic phase)
   - Read code, search patterns, explore
   - Log what you learn:
     $ empirica finding-log --finding "Discovered X works by Y" --impact 0.7
     $ empirica unknown-log --unknown "Need to investigate Z"
     $ empirica deadend-log --approach "Tried X" --why-failed "Failed because Y"

Step 7: CHECK gate (when ready to act)
   $ empirica check-submit - << 'EOF'
   {{
     "vectors": {{"know": 0.75, "uncertainty": 0.3, "context": 0.8, "clarity": 0.85}},
     "reasoning": "Why I'm ready to proceed"
   }}
   EOF

Step 8: Act (praxic phase) - write code, run tests, commit

Step 9: Complete your goal
   $ empirica goals-complete --goal-id <ID> --reason "Done because..."

Step 10: POSTFLIGHT (closes the transaction)
   $ empirica postflight-submit - << 'EOF'
   {{
     "vectors": {{"know": 0.85, "uncertainty": 0.2, "context": 0.9, "clarity": 0.9}},
     "reasoning": "What I learned - compare to PREFLIGHT"
   }}
   EOF

═══════════════════════════════════════════════════════════════════════

KEY CAPABILITIES

Noetic Artifacts (breadcrumbs - log as you work):
   $ empirica finding-log --finding "..."       # What was learned
   $ empirica unknown-log --unknown "..."        # What's unclear
   $ empirica deadend-log --approach "..."       # Failed approaches
   $ empirica assumption-log --assumption "..."  # Unverified beliefs
   $ empirica decision-log --choice "..."        # Choice points

Praxic Artifacts (goals - track progress):
   $ empirica goals-create --objective "..."     # Create goal
   $ empirica goals-add-subtask --goal-id <ID>   # Add subtask
   $ empirica goals-complete --goal-id <ID>      # Complete goal
   $ empirica goals-list                         # Show active goals

Project Management:
   $ empirica project-init                       # Initialize in CWD
   $ empirica project-bootstrap                  # Load project context
   $ empirica project-list                       # List all projects
   $ empirica project-switch <name>              # Switch project

Calibration Reports:
   $ empirica calibration-report                 # Self-referential (Track 1)
   $ empirica calibration-report --grounded      # Grounded verification (Track 2)
   $ empirica calibration-report --trajectory    # Trend over time

Semantic Search (requires Qdrant):
   $ empirica project-search --task "query"      # Search past learnings
   $ empirica project-embed                      # Sync to vector store

Session Management:
   $ empirica sessions-show --session-id <ID>    # View session details
   $ empirica session-snapshot <ID>              # Save snapshot
   $ empirica handoff-create ...                 # Create handoff report

═══════════════════════════════════════════════════════════════════════

TRANSACTION DISCIPLINE

A transaction = one measured chunk of work. PREFLIGHT opens a measurement
window. POSTFLIGHT closes it and captures what you learned.

   Session Start
     +-- Create goals (from task description)
     +-- Transaction 1: Goal A
          PREFLIGHT -> [noetic: investigate] -> CHECK -> [praxic: implement] -> POSTFLIGHT
     +-- Transaction 2: Goal B (informed by T1's findings)
          PREFLIGHT -> [noetic: investigate] -> CHECK -> [praxic: implement] -> POSTFLIGHT

Scope each transaction by what you can handle without losing context.
Between transactions, review open artifacts: close completed goals,
resolve unknowns into findings, verify or falsify assumptions.

═══════════════════════════════════════════════════════════════════════

KEY PRINCIPLES

1. Honest Self-Assessment
   Rate what you ACTUALLY know, not what you hope to figure out.
   High uncertainty is valid data, not failure.

2. Measure Learning
   Compare PREFLIGHT vs POSTFLIGHT to see epistemic growth:
   - KNOW increase = learned domain knowledge
   - UNCERTAINTY decrease = reduced ambiguity
   - Grounded verification catches systematic biases

3. Log As You Discover
   Findings, unknowns, dead-ends - log them as they happen.
   This builds searchable memory and prevents re-exploration.

4. The Sentinel Is Your Ally
   It gates praxic action until you've investigated enough.
   Gaming vectors degrades calibration which degrades autonomy.

═══════════════════════════════════════════════════════════════════════

INTEGRATION OPTIONS

Claude Code (recommended):
   $ empirica setup-claude-code
   # Installs plugin, hooks, CLAUDE.md, MCP server

MCP Server (for any AI agent):
   $ empirica mcp-start
   # Exposes Empirica as MCP tools

Python API:
   from empirica.data.session_database import SessionDatabase
   db = SessionDatabase()
   session_id = db.create_session(ai_id="{ai_id}")
   db.close()

═══════════════════════════════════════════════════════════════════════

NEXT STEPS

1. Initialize your project:   empirica project-init
2. Set up Claude Code:        empirica setup-claude-code
3. Create your first session:  empirica session-create --ai-id {ai_id}
4. Run your first PREFLIGHT:  empirica preflight-submit -
5. Check your calibration:    empirica calibration-report

For help with any command:
   $ empirica <command> --help

For full command list:
   $ empirica --help
""")

    except Exception as e:
        handle_cli_error(e, "Onboarding", getattr(args, 'verbose', False))
        sys.exit(1)
