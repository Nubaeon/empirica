# Empirica v4.0 - Complete Documentation Map

**Version:** 4.0  
**Date:** 2025-12-05  
**Source of Truth:** `docs/system-prompts/CANONICAL_SYSTEM_PROMPT.md`

---

## Quick Reference

### Getting Started

**For AI Agents:**
- [`docs/01_a_AI_AGENT_START.md`](../01_a_AI_AGENT_START.md) - Complete introduction for AI agents
- [`docs/01_b_MCP_AI_START.md`](../01_b_MCP_AI_START.md) - MCP quick start (IDE integration)
- [`docs/03_CLI_QUICKSTART.md`](../03_CLI_QUICKSTART.md) - 5-minute CLI quick start

**For Developers:**
- [`docs/COMPLETE_INSTALLATION_GUIDE.md`](../COMPLETE_INSTALLATION_GUIDE.md) - Complete setup and installation
- [`docs/04_MCP_QUICKSTART.md`](../04_MCP_QUICKSTART.md) - MCP server setup
- [`production/13_PYTHON_API.md`](13_PYTHON_API.md) - Python API reference

### One-Minute Overview

```bash
# 1. Create session (simple, no ceremony)
empirica session-create --ai-id myai --output json
# → Returns session_id

# 2. Run PREFLIGHT (assess baseline knowledge)
empirica preflight --session-id <ID> --prompt "Your task description" --prompt-only
# → Perform genuine self-assessment (13 vectors)
empirica preflight-submit --session-id <ID> --vectors '{...}' --reasoning "..."

# 3. Do your work (implicit reasoning: THINK, INVESTIGATE, PLAN, ACT)
# → Optional: Create goals/subtasks for complex investigations

# 4. (Optional) Run CHECK (decision gate, 0-N times)
empirica check --session-id <ID> --confidence 0.75 --findings "..." --unknowns "..."

# 5. Run POSTFLIGHT (measure learning)
empirica postflight --session-id <ID> --task-summary "What you accomplished" --prompt-only
empirica postflight-submit --session-id <ID> --vectors '{...}' --reasoning "..."
```

---

## Core Concepts

### Understanding Empirica

**→ What is Empirica?** See: [`system-prompts/CANONICAL_SYSTEM_PROMPT.md`](../system-prompts/CANONICAL_SYSTEM_PROMPT.md) (Sections I-II)

Empirica is an **epistemic self-awareness framework** that helps AI agents:
- Track what they KNOW vs what they're guessing
- Measure uncertainty explicitly
- Learn systematically through investigation
- Resume work efficiently across sessions

**Key Principle:** Epistemic transparency > Task completion speed

### CASCADE Workflow (PREFLIGHT/CHECK/POSTFLIGHT)

**→ Complete guide:** [`production/06_CASCADE_FLOW.md`](06_CASCADE_FLOW.md)

CASCADE provides **formal epistemic assessments** stored in the `reflexes` table:

1. **PREFLIGHT** - Before starting work
   - Assess what you ACTUALLY know right now
   - 13-vector self-assessment (ENGAGEMENT, KNOW, DO, CONTEXT, etc.)
   - Be HONEST: "I could figure it out" ≠ "I know it"
   - High uncertainty is GOOD - triggers investigation

2. **Work Phase** - Your actual work (implicit reasoning)
   - THINK, INVESTIGATE, PLAN, ACT, EXPLORE, REFLECT
   - Natural work flow, not prescribed
   - Optional: Use goals/subtasks for complex work

3. **CHECK** - Optional decision gate (0-N times)
   - Decision point: proceed or investigate more?
   - Query unknowns from investigation
   - Not just another assessment - a GATE
   - Typical threshold: unknowns ≤2, confidence ≥0.75

4. **POSTFLIGHT** - After completing work
   - Final 13-vector assessment
   - Measure learning delta (PREFLIGHT → POSTFLIGHT)
   - Track uncertainty reduction

**Storage:** All CASCADE phases write atomically to:
- SQLite `reflexes` table (queryable)
- Git notes (97.5% token reduction)
- JSON logs (full audit trail)

### Goal/Subtask Tracking (NEW in v4.0)

**→ Complete guide:** [`guides/GOAL_TREE_USAGE_GUIDE.md`](../guides/GOAL_TREE_USAGE_GUIDE.md)

**When to use:** Complex tasks, high uncertainty (>0.6), multi-session work

Goals/subtasks provide:
- **Decision Quality** - Unknowns inform CHECK decisions
- **Continuity** - Goal tree included in handoff reports
- **Audit Trail** - Complete investigation path visible

**Python API:**
```python
from empirica.data.session_database import SessionDatabase
db = SessionDatabase()

# Create goal after PREFLIGHT shows high uncertainty
goal_id = db.create_goal(
    session_id=session_id,
    objective="Understand OAuth2 implementation requirements",
    scope_breadth=0.6,  # How wide (0.0-1.0)
    scope_duration=0.4   # How deep (0.0-1.0)
)

# Create subtasks for investigation
subtask_id = db.create_subtask(
    goal_id=goal_id,
    description="Map OAuth2 endpoints and flow",
    importance='high'  # 'critical', 'high', 'medium', 'low'
)

# Log discoveries incrementally
db.update_subtask_findings(subtask_id, [
    "Authorization endpoint: /oauth/authorize",
    "Token endpoint: /oauth/token",
    "PKCE required for security"
])

db.update_subtask_unknowns(subtask_id, [
    "Token rotation interval unclear",
    "Refresh token storage best practice?"
])

# Use for CHECK decisions
unknowns_summary = db.query_unknowns_summary(session_id)
# If unknowns ≤2 → ready to proceed
# If unknowns >2 → investigate more

# Mark complete when done
db.complete_subtask(subtask_id, evidence="Documented in design doc")
```

**CLI:**
```bash
empirica goals-create --session-id <ID> --objective "..." --complexity 0.65
empirica goals-list <ID>
empirica subtask-add --goal-id <ID> --description "..." --importance high
```

### 13 Epistemic Vectors

**→ Complete reference:** [`production/05_EPISTEMIC_VECTORS.md`](05_EPISTEMIC_VECTORS.md)

All vectors range 0.0-1.0:

**TIER 0 (Foundation):**
- **ENGAGEMENT** (gate, must be ≥0.6) - Task engagement level
- **KNOW** - Domain knowledge
- **DO** - Execution capability
- **CONTEXT** - Information sufficiency

**TIER 1 (Comprehension):**
- **CLARITY** - Task understanding
- **COHERENCE** - Internal consistency
- **SIGNAL** - Information quality
- **DENSITY** - Cognitive load

**TIER 2 (Execution):**
- **STATE** - Current progress
- **CHANGE** - Change tracking
- **COMPLETION** - Progress toward goal
- **IMPACT** - Downstream effects

**Meta:**
- **UNCERTAINTY** - Explicit doubt (higher = more uncertain)

### Three Separate Concerns (v4.0 Architecture)

**→ Full explanation:** [`system-prompts/CANONICAL_SYSTEM_PROMPT.md`](../system-prompts/CANONICAL_SYSTEM_PROMPT.md) (Sections IV, VI)

1. **CASCADE Phases** - Epistemic checkpoints (PREFLIGHT/CHECK/POSTFLIGHT)
   - Formal assessments stored in `reflexes` table
   - When you explicitly measure epistemic state

2. **Goals/Subtasks** - Investigation logging (optional, during work)
   - Tracks findings, unknowns, dead ends
   - Stored in `goals` and `subtasks` tables
   - Used for decision quality and continuity

3. **Implicit Reasoning** - Natural work (THINK, INVESTIGATE, PLAN, ACT)
   - Your actual work process
   - Not prescribed or controlled
   - Observed, not mandated

These are **separate concerns** that can interact but don't require each other.

---

## API & Implementation

### Python API

**→ Full reference:** [`production/13_PYTHON_API.md`](13_PYTHON_API.md)

#### Session Management

```python
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()

# Create session
session_id = db.create_session(ai_id="myagent")

# Get session info
session = db.get_session(session_id)

# Close database when done
db.close()
```

#### CASCADE Operations

```python
# PREFLIGHT assessment
reflex_id = db.store_reflex(
    session_id=session_id,
    phase='preflight',
    vectors={
        'engagement': 0.9,
        'know': 0.6,
        'do': 0.7,
        'context': 0.65,
        'clarity': 0.75,
        'coherence': 0.7,
        'signal': 0.6,
        'density': 0.65,
        'state': 0.5,
        'change': 0.5,
        'completion': 0.0,
        'impact': 0.6,
        'uncertainty': 0.4
    },
    reasoning="Starting with moderate knowledge, high uncertainty about X",
    task_prompt="Your task description"
)

# CHECK assessment
check_id = db.store_reflex(
    session_id=session_id,
    phase='check',
    vectors={...},
    reasoning="Investigation revealed 2 unknowns, ready to proceed",
    findings=["Finding 1", "Finding 2"],
    unknowns=["Unknown 1", "Unknown 2"],
    confidence=0.75
)

# POSTFLIGHT assessment
post_id = db.store_reflex(
    session_id=session_id,
    phase='postflight',
    vectors={...},
    reasoning="Learned significantly, uncertainty reduced",
    task_summary="Completed OAuth2 implementation"
)
```

#### Goal/Subtask Operations (NEW v4.0)

```python
# Create goal
goal_id = db.create_goal(
    session_id=session_id,
    objective="Understand OAuth2 implementation requirements",
    scope_breadth=0.6,
    scope_duration=0.4,
    estimated_complexity=0.65
)

# Create subtask
subtask_id = db.create_subtask(
    goal_id=goal_id,
    description="Map OAuth2 endpoints and flow",
    importance='high',
    dependencies=[]
)

# Update subtask with findings
db.update_subtask_findings(subtask_id, [
    "Authorization endpoint: /oauth/authorize",
    "Token endpoint: /oauth/token"
])

# Update subtask with unknowns
db.update_subtask_unknowns(subtask_id, [
    "Token rotation interval?",
    "Refresh token storage?"
])

# Mark subtask complete
db.complete_subtask(subtask_id, evidence="Documented in design doc")

# Query unknowns for CHECK decision
unknowns_summary = db.query_unknowns_summary(session_id)
# Returns: {"total_unknowns": 2, "by_subtask": {...}}
```

### CLI Commands

**→ All commands:** Run `empirica --help`

#### Essential Commands

```bash
# Session management
empirica session-create --ai-id myagent --output json
empirica sessions-list
empirica session-summary <SESSION_ID>

# CASCADE workflow
empirica preflight --session-id <ID> --prompt "task" --prompt-only
empirica preflight-submit --session-id <ID> --vectors '{...}' --reasoning "..."
empirica check --session-id <ID> --confidence 0.75
empirica postflight --session-id <ID> --task-summary "completed"

# Goals/subtasks (v4.0)
empirica goals-create --session-id <ID> --objective "..." --complexity 0.65
empirica goals-list <SESSION_ID>
empirica goals-progress <GOAL_ID>
empirica goals-discover --ai-id other-ai
empirica subtask-add --goal-id <ID> --description "..." --importance high
empirica subtask-complete --subtask-id <ID> --evidence "..."

# Continuity & Checkpoints
empirica handoff-create --session-id <ID> --task-summary "..." --key-findings '["Finding 1", "Finding 2"]' --remaining-unknowns '["Unknown 1"]' --next-session-context "..."
empirica handoff-query --ai-id myagent --limit 5
empirica sessions-resume <SESSION_ID>
empirica checkpoint-create --session-id <ID> --phase preflight
empirica checkpoint-load --session-id <ID>
empirica checkpoint-list <SESSION_ID>

# Identity/Crypto
empirica identity-create --ai-id myai
empirica identity-list
```

### MCP Tools

**→ MCP setup:** [`docs/04_MCP_QUICKSTART.md`](../04_MCP_QUICKSTART.md)  
**→ All MCP tools:** [`system-prompts/CANONICAL_SYSTEM_PROMPT.md`](../system-prompts/CANONICAL_SYSTEM_PROMPT.md) (Section XV)

**Essential tools for MCP usage:**

**Session Management:**
- `session_create` - Create new session
- `get_session_summary` - Get session details
- `get_epistemic_state` - Get current epistemic state

**CASCADE Workflow:**
- `execute_preflight` - Generate PREFLIGHT self-assessment prompt
- `submit_preflight_assessment` - Submit 13-vector assessment
- `execute_check` - Execute CHECK phase with findings/unknowns
- `submit_check_assessment` - Submit CHECK assessment
- `execute_postflight` - Execute POSTFLIGHT assessment
- `submit_postflight_assessment` - Submit POSTFLIGHT assessment

**Goals/Subtasks (v4.0):**
- `create_goal` - Create investigation goal
- `add_subtask` - Add subtask to goal
- `complete_subtask` - Mark subtask complete
- `get_goal_progress` - Get goal completion status

**Continuity:**
- `create_handoff_report` - Create handoff for next session
- `query_handoff_reports` - Load previous handoffs

**Goal Discovery (Cross-AI):**
- `discover_goals` - Find goals from other AIs via git notes
- `resume_goal` - Resume another AI's goal with handoff
- `list_goals` - List all goals for a session

**Identity/Crypto:**
- `create_identity` - Create AI identity with Ed25519 keypair
- `list_identities` - List all AI identities
- `export_public_key` - Export public key for sharing
- `verify_signature` - Verify signed session

**Documentation:**
- `get_empirica_introduction` - Get comprehensive intro to Empirica
- `get_workflow_guidance` - Get CASCADE workflow guidance
- `cli_help` - Get CLI command help

---

## Visualization Tools

Empirica stores epistemic states in git/SQLite, enabling real-time visualization:

**Statusline:**
```bash
# Show epistemic state in status bar (tmux/vim)
scripts/statusline_empirica.py --session-id <ID>
```

**Dashboards:**
```bash
# Main dashboard
scripts/dashboards/empirica.sh

# Leaderboard (compare AI performance)
scripts/dashboards/leaderboard.sh

# Goals progress
scripts/dashboards/empirica-goals-dashboard.sh

# Git statistics
scripts/dashboards/empirica-git-stats.sh
```

**Session Replay:**
```bash
# Replay session history with visualization
scripts/session_replay.py --session-id <ID>
```

**→ How it works:** 3-layer storage (SQLite/Git/JSON) makes epistemic data queryable → enables real-time dashboards

---

## Database & Storage

### Schema

**→ Complete schema:** [`production/12_SESSION_DATABASE.md`](12_SESSION_DATABASE.md)

**Key tables:**

#### `reflexes` table (unified in v4.0)
All CASCADE assessments (PREFLIGHT, CHECK, POSTFLIGHT):
- 13 epistemic vectors
- Phase indicator
- Reasoning text
- Findings/unknowns (CHECK phase)
- Task prompt/summary
- Timestamps

#### `goals` table (NEW v4.0)
Investigation goals with scope:
- `objective` - What you're investigating
- `scope_breadth` - How wide (0.0-1.0)
- `scope_duration` - How deep (0.0-1.0)
- `estimated_complexity` - Complexity estimate
- Associated session_id

#### `subtasks` table (NEW v4.0)
Investigation items:
- `description` - What to investigate
- `importance` - 'critical', 'high', 'medium', 'low'
- `findings` - JSON array of discoveries
- `unknowns` - JSON array of questions
- `dead_ends` - JSON array of failed approaches
- `status` - 'pending', 'in_progress', 'completed'
- `evidence` - Completion evidence

### Storage Architecture

**→ Full details:** [`system-prompts/CANONICAL_SYSTEM_PROMPT.md`](../system-prompts/CANONICAL_SYSTEM_PROMPT.md) (Section III)

**Three-layer atomic writes:**

1. **SQLite database** - Primary storage
   - `reflexes` table (all CASCADE assessments)
   - `goals` table (investigation goals)
   - `subtasks` table (investigation items)
   - Queryable, structured data

2. **Git notes** - Compressed checkpoints
   - 97.5% token reduction (46 vs 1,821 tokens)
   - Handoff reports (~400 vs 20,000 tokens)
   - Cross-AI coordination via git

3. **JSON logs** - Full audit trail
   - Complete session history
   - Human-readable backups
   - Debugging and analysis

All three layers updated atomically to maintain consistency.

---

## Detailed Guides

| Topic | Location | Purpose |
|-------|----------|---------|
| CASCADE Workflow | [`06_CASCADE_FLOW.md`](06_CASCADE_FLOW.md) | Understanding phases, using CHECK gates |
| Goal Tracking | [`../guides/GOAL_TREE_USAGE_GUIDE.md`](../guides/GOAL_TREE_USAGE_GUIDE.md) | Complex investigations, high uncertainty |
| Basic Usage | [`03_BASIC_USAGE.md`](03_BASIC_USAGE.md) | Getting started, simple examples |
| Database Schema | [`12_SESSION_DATABASE.md`](12_SESSION_DATABASE.md) | Complete schema details |
| Python API | [`13_PYTHON_API.md`](13_PYTHON_API.md) | Complete API reference |
| Epistemic Vectors | [`05_EPISTEMIC_VECTORS.md`](05_EPISTEMIC_VECTORS.md) | Understanding all 13 vectors |
| Session Continuity | [`23_SESSION_CONTINUITY.md`](23_SESSION_CONTINUITY.md) | Handoff reports, resuming sessions |
| MCP Integration | [`../04_MCP_QUICKSTART.md`](../04_MCP_QUICKSTART.md) | IDE integration setup |

---

## Working Examples

### Example 1: Simple Task (No Goals)

**Scenario:** Write a function to parse JSON

```bash
# 1. Create session
session_id=$(empirica session-create --ai-id json-parser --output json | jq -r .session_id)

# 2. PREFLIGHT: Quick assessment
empirica preflight --session-id $session_id --prompt "Write JSON parser function"
# Submit: know=0.8, do=0.9, uncertainty=0.2 (low uncertainty, straightforward)

# 3. Write the function (implicit work)
# No goals needed - task is simple and clear

# 4. POSTFLIGHT: Measure learning
empirica postflight --session-id $session_id --task-summary "JSON parser completed"
# Submit: know=0.85, do=0.95, uncertainty=0.1 (minimal learning, as expected)
```

### Example 2: Complex Investigation (With Goals)

**Scenario:** Research OAuth2 implementation before coding

```bash
# 1. Create session
session_id=$(empirica session-create --ai-id oauth-researcher --output json | jq -r .session_id)

# 2. PREFLIGHT: Assess baseline (shows high uncertainty)
empirica preflight --session-id $session_id --prompt "Understand OAuth2 implementation requirements"
# Submit: know=0.6, uncertainty=0.5, context=0.55 (HIGH uncertainty → use goals)

# 3. Create investigation goal
goal_id=$(empirica goals-create --session-id $session_id \
  --objective "Understand OAuth2 implementation requirements" \
  --complexity 0.65 --output json | jq -r .goal_id)

# 4. Create subtasks
empirica subtask-add --goal-id $goal_id --description "Map OAuth2 endpoints and flow" --importance high
empirica subtask-add --goal-id $goal_id --description "Research PKCE security requirements" --importance high
empirica subtask-add --goal-id $goal_id --description "Understand token storage best practices" --importance medium

# 5. Investigate (implicit work phase)
# As you investigate, update findings and unknowns using Python API:
# db.update_subtask_findings(subtask_id, ["Authorization endpoint: /oauth/authorize", ...])
# db.update_subtask_unknowns(subtask_id, ["Token rotation interval?", ...])

# 6. CHECK: Query unknowns to assess readiness
# unknowns_summary = db.query_unknowns_summary(session_id)
# → 2 unknowns remain (manageable)
empirica check --session-id $session_id --confidence 0.75 \
  --findings "Mapped endpoints, PKCE requirements clear" \
  --unknowns "Token rotation interval?, Storage encryption method?"
# Decision: confidence ≥0.75, unknowns ≤2 → PROCEED

# 7. Implement OAuth2 (implicit work)

# 8. POSTFLIGHT: Measure learning
empirica postflight --session-id $session_id --task-summary "OAuth2 implementation complete"
# Submit: know=0.85 (+0.25 learned), uncertainty=0.25 (-0.25 resolved)

# 9. Create handoff for next session
empirica handoff-create --session-id $session_id \
  --task-summary "OAuth2 basic flow implemented" \
  --key-findings '["PKCE required for security", "Endpoints documented in spec"]' \
  --remaining-unknowns '["Token rotation interval not finalized", "Refresh token storage approach TBD"]' \
  --next-session-context "Next: implement refresh token rotation with secure storage"
```

**Result:** Goal tree in handoff shows:
- What was investigated (subtasks)
- What was learned (findings)
- What remains unclear (unknowns)
- Next AI can resume with full context

---

## FAQ & Common Questions

**Q: Do I have to use goals/subtasks?**  
A: No, they're optional. Use for complex investigations or high uncertainty (>0.6). PREFLIGHT/CHECK/POSTFLIGHT work standalone for simple tasks.

**Q: What's the difference between CASCADE and goals?**  
A: CASCADE = epistemic checkpoints (when you formally assess). Goals = investigation logging (optional, during work). They're separate but can interact (CHECK queries unknowns from goals).

**Q: What's "bootstrap" vs "session-create"?**  
A: Bootstrap = system prompts (AI instructions in `docs/system-prompts/`). session-create = command to create a session. Don't confuse them. The `--bootstrap-level` parameter exists for backward compatibility but has no behavioral effect.

**Q: How do I know if I'm ready for CHECK?**  
A: Query `db.query_unknowns_summary(session_id)`. If unknowns ≤2 and confidence ≥0.75, ready to proceed. Otherwise, investigate more or document unknowns for next session.

**Q: Can I resume a previous session?**  
A: Yes. Handoff reports preserve goal tree + learnings. Next AI loads handoff with `query_handoff_reports()` and continues investigation.

**Q: What if CHECK shows I'm not ready?**  
A: Investigate more! Create additional subtasks, log findings, reduce unknowns. Run CHECK again when confidence improves. CHECK can be run 0-N times.

**Q: Do I need to use all 13 vectors?**  
A: Yes, for CASCADE phases (PREFLIGHT/CHECK/POSTFLIGHT). All 13 vectors must be provided. Be honest in your assessment - high uncertainty is better than false confidence.

**Q: What's the "reflexes" table?**  
A: Unified table for all CASCADE assessments (PREFLIGHT, CHECK, POSTFLIGHT). v4.0 architecture improvement - all epistemic data in one place.

**→ More FAQs:** [`production/22_FAQ.md`](22_FAQ.md)

---

## Architecture Diagram

```
SESSION CREATION (instant, no ceremony)
    ↓
PREFLIGHT → Baseline epistemic assessment (13 vectors)
    ↓
[WORK PHASE - Implicit reasoning: THINK, INVESTIGATE, PLAN, ACT, EXPLORE, REFLECT]
    ├─ (OPTIONAL) High uncertainty? Create goal → Create subtasks
    ├─ (INVESTIGATION) Log findings/unknowns incrementally
    ├─ (0-N TIMES) CHECK gate → Query unknowns → Decide readiness
    │     ├─ Ready (unknowns ≤2, confidence ≥0.75)? → Proceed to completion
    │     └─ Not ready? → Investigate more, run CHECK again
    └─ Refine investigation based on CHECK decision
    ↓
POSTFLIGHT → Final assessment (13 vectors, measure PREFLIGHT→POSTFLIGHT delta)
    ↓
HANDOFF REPORT → Goal tree + learnings + unknowns + next session context
    ↓
(NEXT SESSION) Load handoff → Resume with complete investigation history
```

**Storage Flow (Atomic Writes):**
```
CASCADE Phase (PREFLIGHT/CHECK/POSTFLIGHT)
    ↓
    ├─ SQLite `reflexes` table (primary, queryable)
    ├─ Git notes (compressed checkpoints)
    └─ JSON logs (full audit trail)
```

---

## Next Steps

### For New Users
1. **Read:** "One-Minute Overview" above
2. **Read:** [`docs/01_a_AI_AGENT_START.md`](../01_a_AI_AGENT_START.md) - Complete introduction
3. **Try:** Create a session and run PREFLIGHT
   ```bash
   empirica session-create --ai-id myai
   empirica preflight --session-id <ID> --prompt "Your task"
   ```

### For Developers
1. **Read:** [`docs/COMPLETE_INSTALLATION_GUIDE.md`](../COMPLETE_INSTALLATION_GUIDE.md)
2. **Read:** [`production/13_PYTHON_API.md`](13_PYTHON_API.md)
3. **Try:** Create session via Python API
   ```python
   from empirica.data.session_database import SessionDatabase
   db = SessionDatabase()
   session_id = db.create_session(ai_id="myai")
   ```

### For Understanding CASCADE
1. **Read:** [`production/06_CASCADE_FLOW.md`](06_CASCADE_FLOW.md) - Complete workflow guide
2. **Understand:** Three separate concerns (CASCADE/goals/implicit)
3. **Practice:** Run a simple PREFLIGHT → POSTFLIGHT cycle

### For Complex Investigations
1. **Read:** [`guides/GOAL_TREE_USAGE_GUIDE.md`](../guides/GOAL_TREE_USAGE_GUIDE.md)
2. **Understand:** When to use goals (uncertainty >0.6, complex tasks)
3. **Practice:** Create goal with subtasks, log findings/unknowns

### For Everything
- **Start:** This documentation map (you're here!)
- **Deep dive:** [`system-prompts/CANONICAL_SYSTEM_PROMPT.md`](../system-prompts/CANONICAL_SYSTEM_PROMPT.md) - v4.0 canonical reference
- **Details:** Linked guides throughout this document

---

## Source of Truth

**All information in this map references:**
- [`system-prompts/CANONICAL_SYSTEM_PROMPT.md`](../system-prompts/CANONICAL_SYSTEM_PROMPT.md) - v4.0 canonical system prompt
- `empirica/data/session_database.py` - Implementation source code
- Detailed guides in `docs/production/` and `docs/guides/`

**Do not duplicate architecture information.** This map provides navigation and quick reference. For authoritative details, follow links to source documents.

---

**Last updated:** 2025-12-05  
**Version:** v4.0  
**Status:** Production Ready

---

**Ready to start?** → [`docs/01_a_AI_AGENT_START.md`](../01_a_AI_AGENT_START.md)
