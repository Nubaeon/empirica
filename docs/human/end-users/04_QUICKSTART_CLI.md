# CLI Quick Start

**Time:** 10 minutes  
**Best for:** Terminal workflows, scripts, automation  
**Prerequisites:** Empirica installed (see [02_INSTALLATION.md](02_INSTALLATION.md))

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
# AI-first mode (JSON via stdin) — opens a transaction
empirica preflight-submit - << 'EOF'
{
  "task_context": "What you're about to do",
  "vectors": {"know": 0.45, "uncertainty": 0.7, "context": 0.5, "clarity": 0.6},
  "reasoning": "Honest baseline assessment"
}
EOF

# Legacy mode (flags)
empirica preflight --session-id <SESSION_ID>
```

**What it does:**
- Opens an epistemic transaction (measurement window)
- Records your baseline vectors for learning measurement
- Returns session_id + transaction_id for subsequent commands

### 3. Investigate (noetic phase)
```bash
# Log what you learn (session_id auto-derived from active transaction)
empirica finding-log --finding "System uses Auth0 for SSO" --impact 0.7

# Log what's unclear
empirica unknown-log --unknown "How to handle token refresh?"

# Log failed approaches (prevents re-exploration)
empirica deadend-log --approach "Tried WebSockets" --why-failed "Server doesn't support WS"
```

### 4. CHECK Gate (Sentinel)
```bash
# AI-first mode (JSON via stdin)
empirica check-submit - << 'EOF'
{
  "vectors": {"know": 0.75, "uncertainty": 0.3, "context": 0.8, "clarity": 0.85},
  "reasoning": "Investigated auth architecture, ready to implement"
}
EOF

# Legacy mode (flags)
empirica check --session-id <SESSION_ID>
```

**Output:**
- `proceed` — ready for praxic action (write code, edit files)
- `investigate` — keep exploring in noetic phase

### 5. Do the Work (praxic phase)
```bash
# Create and complete goals
empirica goals-create --objective "Implement OAuth2 client with PKCE"
empirica goals-complete --goal-id <GOAL_ID> --reason "OAuth2 PKCE flow implemented and tested"
```

### 6. Run POSTFLIGHT (closes the transaction)
```bash
# AI-first mode (JSON via stdin) — closes transaction + triggers grounded verification
empirica postflight-submit - << 'EOF'
{
  "vectors": {"know": 0.85, "uncertainty": 0.15, "context": 0.9, "clarity": 0.9},
  "reasoning": "Learned OAuth2 PKCE flow, implemented and tested. Compare to PREFLIGHT baseline."
}
EOF

# Legacy mode (flags)
empirica postflight --session-id <SESSION_ID>
```

**What it measures:**
- Learning delta: PREFLIGHT vs POSTFLIGHT vectors
- Grounded verification (POST-TEST): compares self-assessment to objective evidence (tests, git, goals)
- Calibration accuracy: are you over/under-estimating?

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

**Learn more:** [BEADS Quickstart](BEADS_QUICKSTART.md)

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

# 2. Load project context
empirica project-bootstrap --output json

# 3. Create goal + assess
empirica goals-create --objective "Fix auth bug"
empirica preflight-submit -    # JSON via stdin

# 4. Investigate + act
empirica finding-log --finding "Found root cause in token validation"
empirica check-submit -        # Gate check
# ... write code ...

# 5. Complete
empirica goals-complete --goal-id <ID> --reason "Bug fixed, tests pass"
empirica postflight-submit -   # Closes transaction
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
- Use `finding-log`, `unknown-log`, `deadend-log` during work
- Creates searchable epistemic trail for future sessions

### 4. Create Handoffs
- Even for solo work, handoffs help resume efficiently
- ~90% token reduction vs full context

### 5. Leverage Git Integration
- Checkpoints are cheap (~85% token reduction)
- Create checkpoints before risky changes

---

## What's Next?

- **Learn about vectors:** [05_EPISTEMIC_VECTORS_EXPLAINED.md](05_EPISTEMIC_VECTORS_EXPLAINED.md)
- **Understand CASCADE:** [Sentinel Architecture](../../architecture/SENTINEL_ARCHITECTURE.md) - PREFLIGHT→CHECK→POSTFLIGHT workflow
- **See all commands:** [CLI Commands Unified](../developers/CLI_COMMANDS_UNIFIED.md)
- **Having issues?** [03_TROUBLESHOOTING.md](03_TROUBLESHOOTING.md)

---

## Quick Reference Card

```bash
# Essential Commands (CASCADE workflow)
empirica session-create --ai-id myai          # Start session
empirica project-bootstrap                    # Load project context
empirica goals-create --objective "..."       # Create goal
empirica preflight-submit -                   # PREFLIGHT (JSON stdin)
empirica check-submit -                       # CHECK gate (JSON stdin)
empirica postflight-submit -                  # POSTFLIGHT (JSON stdin)
empirica handoff-create --session-id <ID>     # Create handoff

# Noetic Artifacts (log as you work)
empirica finding-log --finding "..."          # What was learned
empirica unknown-log --unknown "..."          # What's unclear
empirica deadend-log --approach "..."         # Failed approaches

# Praxic Artifacts (track progress)
empirica goals-create --objective "..."       # Create goal
empirica goals-complete --goal-id <ID>        # Complete goal
empirica goals-list                           # List active goals

# Calibration
empirica calibration-report                   # Self-referential
empirica calibration-report --grounded        # Grounded verification

# Global Workspace (cross-project)
empirica workspace-overview                   # Portfolio view
empirica project-switch <name>                # Switch project
```

---

## Sessions vs Transactions

**Key distinction** for understanding Empirica:

| Concept | What It Is | When It Ends |
|---------|------------|--------------|
| **Session** | Context window | When Claude compacts memory |
| **Transaction** | Epistemic measurement unit | POSTFLIGHT completes |

- **Sessions** are internal (context boundaries)
- **Transactions** are the real unit (PREFLIGHT→work→POSTFLIGHT)
- All findings/unknowns/dead-ends have a `transaction_id`
- Transactions can span multiple sessions (if compaction happens mid-work)

---

**Remember:** Empirica works best when you're honest about what you know. The system is designed to help you learn systematically, not to judge you for uncertainty.
