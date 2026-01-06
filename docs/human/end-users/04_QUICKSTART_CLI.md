# CLI Quick Start

**Time:** 10 minutes  
**Best for:** Terminal workflows, scripts, automation  
**Prerequisites:** Empirica installed (see [04_INSTALLATION.md](04_INSTALLATION.md))

---

## Quick Example: Complete Workflow

### 1. Create a Session
```bash
# AI-first mode (JSON)
echo '{"ai_id": "myai", "session_type": "development"}' | empirica session-create -

# Output:
# {
#   "ok": true,
#   "session_id": "abc123...",
#   "ai_id": "myai",
#   "project_id": "auto-detected-uuid"
# }
```

**Save the session_id** - you'll need it for the workflow.

### 2. Run PREFLIGHT Assessment
```bash
empirica preflight --session-id <SESSION_ID>
```

**What it does:**
- Prompts you to assess 13 epistemic vectors honestly
- Calculates if you should investigate first
- Stores baseline for learning measurement

**Example output:**
```
Epistemic Assessment:
  KNOW: 0.45  ⚠️  Below threshold (0.60)
  CONTEXT: 0.50
  UNCERTAINTY: 0.70  ⚠️  High

→ RECOMMENDATION: Investigate before proceeding
```

### 3. Investigate (if needed)
```bash
# Search codebase or docs
empirica investigate "authentication architecture"

# Log what you learn
empirica finding-log --project-id <PROJECT_ID> \
    --finding "System uses Auth0 for SSO"

# Log what's unclear
empirica unknown-log --project-id <PROJECT_ID> \
    --unknown "How to handle token refresh?"
```

### 4. Check Gate
```bash
# Assess if you're ready to proceed
empirica check --session-id <SESSION_ID>
```

**Input:**
- What did you find?
- What's still unknown?
- Confidence to proceed (0.0-1.0)

**Output:**
```
Confidence: 0.75
Decision: PROCEED (threshold: 0.70)
```

### 5. Do the Work
```bash
# Log key actions as you work
empirica act-log --session-id <SESSION_ID> \
    --action "Implemented OAuth2 client with PKCE"

empirica act-log --session-id <SESSION_ID> \
    --action "Added session middleware"
```

### 6. Run POSTFLIGHT
```bash
empirica postflight --session-id <SESSION_ID>
```

**What it measures:**
- How much did you learn? (delta on all 13 vectors)
- Was your initial assessment accurate? (calibration)

**Example output:**
```
Epistemic Delta:
  KNOW: 0.45 → 0.85 (+0.40)  📈
  CONTEXT: 0.50 → 0.90 (+0.40)  📈
  UNCERTAINTY: 0.70 → 0.15 (-0.55)  ✓

Calibration: GOOD
Learning verified: Strong improvement
```

### 7. Create Handoff (optional)
```bash
# For resuming work later or handing off to another agent
empirica handoff-create --session-id <SESSION_ID> \
    --task-summary "Implemented OAuth2 authentication" \
    --key-findings "Auth0 SSO integrated" "PKCE flow works" \
    --next-session-context "Token refresh still needs work"

# Query handoffs later
empirica handoff-query --ai-id myai --limit 5
```

---

## Common Commands

### Session Management
```bash
# Create session
empirica session-create --ai-id myai

# List all sessions
empirica sessions-list

# Show session details
empirica sessions-show --session-id <ID>

# Resume previous sessions
empirica sessions-resume --ai-id myai --count 1
```

### Project Management
```bash
# Create project
empirica project-create --name "My Project" \
    --description "Project description"

# Bootstrap context
empirica project-bootstrap --project-id <PROJECT_ID>

# List projects
empirica project-list
```

### Goals & Subtasks
```bash
# Create goal
empirica goals-create --session-id <SESSION_ID> \
    --objective "Implement feature X"

# Add subtask
empirica goals-add-subtask --goal-id <GOAL_ID> \
    --description "Research approach" \
    --importance high

# Complete subtask
empirica goals-complete-subtask --task-id <TASK_ID>

# Check progress
empirica goals-progress --goal-id <GOAL_ID>
```

### Multi-Agent Collaboration (BEADS)
**BEADS** (Dependency-Aware Issue Tracker) integrates with Empirica for dependency-aware goal tracking.

```bash
# Create goal with BEADS tracking
empirica goals-create \
  --session-id <SESSION_ID> \
  --objective "Implement OAuth2" \
  --success-criteria "Auth works" \
  --use-beads  # ← Automatically creates BEADS issue

# Add subtasks with auto-dependencies
empirica goals-add-subtask \
  --goal-id <GOAL_ID> \
  --description "Research OAuth2 spec" \
  --use-beads  # ← Auto-links as dependency

# Find ready work (BEADS + Epistemic)
empirica goals-ready --session-id <SESSION_ID>
# Combines: BEADS dependencies + epistemic state
# Result: Tasks you can actually do right now
```

**Per-project default:**
```yaml
# .empirica/project.yaml
beads:
  default_enabled: true  # Enable by default
```

**Learn more:** [BEADS Quickstart](../integrations/BEADS_QUICKSTART.md)

### Git Integration
```bash
# Create checkpoint (saves to git notes)
empirica checkpoint-create --session-id <SESSION_ID>

# Load checkpoint
empirica checkpoint-load --session-id <SESSION_ID>

# List checkpoints
empirica checkpoint-list --session-id <SESSION_ID>

# Show differences
empirica checkpoint-diff --session-id <SESSION_ID>
```

---

## Output Formats

### Default (Human-Friendly)
```bash
empirica sessions-list
# Colorized, formatted output with tables
```

### JSON (AI-Friendly)
```bash
empirica sessions-list --output json
# Machine-readable JSON
```

### AI-First Mode (stdin)
```bash
# Send JSON via stdin
echo '{"ai_id": "myai"}' | empirica session-create -

# Useful for programmatic usage
cat config.json | empirica goals-create -
```

---

## Typical Workflows

### Solo Development Session
```bash
# 1. Start
SESSION_ID=$(empirica session-create --ai-id myai --output json | jq -r .session_id)

# 2. Assess
empirica preflight --session-id $SESSION_ID

# 3. Work (with optional investigation)
empirica investigate "relevant_file.py"
empirica act-log --session-id $SESSION_ID --action "Fixed bug in auth"

# 4. Complete
empirica postflight --session-id $SESSION_ID

# 5. Handoff
empirica handoff-create --session-id $SESSION_ID
```

### Multi-Agent Goal Handoff
```bash
# Agent 1: Create goal
GOAL_ID=$(empirica goals-create --session-id $SESSION_ID \
    --objective "Refactor authentication" --output json | jq -r .goal_id)

empirica goals-add-subtask --goal-id $GOAL_ID \
    --description "Research current implementation" --importance high

empirica goals-claim --goal-id $GOAL_ID  # Creates branch + issue

# Agent 2: Discover and resume
empirica goals-discover
empirica goals-resume --goal-id $GOAL_ID --ai-id agent2
empirica goals-complete --goal-id $GOAL_ID  # Merges + closes
```

### Long-Running Project
```bash
# Day 1: Initialize
PROJECT_ID=$(empirica project-create --name "Feature X" --output json | jq -r .project_id)

# Day 2: Bootstrap context
empirica project-bootstrap --project-id $PROJECT_ID
# Shows: recent findings, unknowns, dead-ends, reference docs

# Day N: Track discoveries
empirica finding-log --project-id $PROJECT_ID \
    --finding "API uses REST not GraphQL"

empirica deadend-log --project-id $PROJECT_ID \
    --approach "Tried using WebSockets" \
    --why-failed "Server doesn't support WS protocol"
```

---

## Tips & Best Practices

### 1. Be Honest in Assessments
- PREFLIGHT: Rate what you know **right now**, not what you can figure out
- Don't inflate scores - the system learns from accurate self-assessment

### 2. Use Project Bootstrap
- Start each session with `project-bootstrap` to load relevant context
- Saves tokens and prevents "starting from scratch"

### 3. Log as You Go
- Use `finding-log`, `unknown-log`, `act-log` during work
- Creates epistemic trail for future sessions

### 4. Create Handoffs
- Even for solo work, handoffs help resume efficiently
- ~90% token reduction vs full context

### 5. Leverage Git Integration
- Checkpoints are cheap (~85% token reduction)
- Create checkpoints before risky changes

---

## What's Next?

- **Learn about vectors:** [05_EPISTEMIC_VECTORS_EXPLAINED.md](05_EPISTEMIC_VECTORS_EXPLAINED.md) *(to be created)*
- **Understand CASCADE:** [07_CASCADE_WORKFLOW.md](07_CASCADE_WORKFLOW.md) *(to be created)*
- **See all commands:** [reference/CLI_COMMANDS_COMPLETE.md](reference/CLI_COMMANDS_COMPLETE.md)
- **Try MCP integration:** [03_QUICKSTART_MCP.md](03_QUICKSTART_MCP.md)
- **Having issues?** [06_TROUBLESHOOTING.md](06_TROUBLESHOOTING.md)

---

## Quick Reference Card

```bash
# Essential Commands
empirica session-create --ai-id myai          # Start
empirica preflight --session-id <ID>          # Assess
empirica check --session-id <ID>              # Gate
empirica investigate <concept>                # Learn
empirica act-log --session-id <ID> --action   # Track
empirica postflight --session-id <ID>         # Measure
empirica handoff-create --session-id <ID>     # Resume

# Context Management
empirica project-bootstrap --project-id <ID>  # Load
empirica finding-log --project-id <ID>        # Discover
empirica unknown-log --project-id <ID>        # Clarify

# Collaboration
empirica goals-discover                       # Find work
empirica goals-claim --goal-id <ID>           # Start
empirica goals-complete --goal-id <ID>        # Finish
```

---

**Remember:** Empirica works best when you're honest about what you know. The system is designed to help you learn systematically, not to judge you for uncertainty.
