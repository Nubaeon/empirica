# Empirica Explained Simply

**What it is:** A system that helps AI agents know what they know (and don't know), track project learning, and collaborate effectively.

**Date:** 2026-02-22
**Version:** 5.0

---

## The Problem

AI agents are often **confidently wrong**:

```
You: "Can you implement OAuth2 authentication?"
AI:  "Sure! I know OAuth2 well." [Actually doesn't]
AI:  [Implements something that compiles but is wrong]
You: [Wastes hours debugging]
```

**Root cause:** AI can't distinguish between "I know this" and "I think I can figure this out."

---

## The Solution: Empirica

Empirica makes AI agents **epistemically honest** - they track what they actually know vs what they're guessing about.

```
You: "Can you implement OAuth2 authentication?"
AI:  "My knowledge: 0.45/1.0, uncertainty: 0.70
      Let me investigate the spec first..."
AI:  [Reads docs, searches codebase]
AI:  "Knowledge now: 0.85, uncertainty: 0.20. Ready to proceed."
AI:  [Implements correctly]
```

---

## Three Systems in One

### 1. Epistemic Ledger (Self-Awareness)

Track **13 dimensions** of knowledge across 3 tiers:

**Tier 0 - Foundation:**
- **ENGAGEMENT**: Am I focused on the right thing?
- **KNOW**: Do I understand the domain? (not confidence - actual knowledge)
- **DO**: Can I actually do this? (skills, tools, access)
- **CONTEXT**: Do I understand the situation? (files, architecture, constraints)

**Tier 1 - Comprehension:**
- **CLARITY**: Do I understand the requirements?
- **COHERENCE**: Does my understanding make sense?
- **SIGNAL**: Is the information I have useful?
- **DENSITY**: Is this too much/too little information?

**Tier 2 - Execution:**
- **STATE**: Where am I in the process?
- **CHANGE**: What's changing as I work?
- **COMPLETION**: How complete is this?
- **IMPACT**: What's the effect of my work?

**Meta:**
- **UNCERTAINTY**: What am I unsure about?

### 2. Dynamic Context Loader (Project Memory)

**Problem:** AI agents lose context between sessions.

**Solution:** Load relevant project memory on-demand:

```bash
empirica project-bootstrap --project-id <PROJECT_ID>
```

**Shows (~800 tokens):**
- Recent **findings** (what was learned)
- Open **unknowns** (what's still unclear)
- **Dead ends** (what didn't work)
- Key **reference docs**
- Related **skills**

**Result:** New session starts with compressed, relevant context instead of blank slate.

### 3. Predictive Task Management (Goal System)

**Problem:** Traditional task tracking doesn't capture epistemic uncertainty.

**Solution:** Goals scoped by epistemic dimensions:

```python
goal = {
    "objective": "Implement OAuth2 authentication",
    "scope": {
        "breadth": 0.6,      # Medium scope (0=function, 1=codebase)
        "duration": 0.4,     # Medium duration (0=hours, 1=months)
        "coordination": 0.3  # Low coordination needed
    },
    "estimated_complexity": 0.65
}
```

**Subtasks** track:
- Importance (critical/high/medium/low)
- Dependencies
- Completion status
- Findings/unknowns per subtask

**BEADS Integration:**
- `goals-claim`: Create git branch + link to issue tracker
- `goals-discover`: Find goals from other AI agents
- `goals-resume`: Take over someone else's goal
- `goals-complete`: Merge branch + close issue

**Result:** Multi-agent collaboration with epistemic handoff.

---

## The CASCADE Workflow

Think of CASCADE like doing homework properly:

### 1. PREFLIGHT (Before Starting)
**"What do I already know?"**

```bash
# Opens an epistemic transaction (measurement window)
empirica preflight-submit - << 'EOF'
{
  "task_context": "Implement OAuth2 authentication",
  "vectors": {"know": 0.45, "uncertainty": 0.7, "context": 0.5, "clarity": 0.6},
  "reasoning": "Low domain knowledge, high uncertainty"
}
EOF
```

- Assess epistemic vectors **honestly**
- Not "I can figure it out" but "What do I know RIGHT NOW?"
- Opens a transaction for measuring learning

### 2. INVESTIGATE (Reduce Uncertainty)
**"Let me learn what I need to know"**

```bash
# Log findings as you discover them (session_id auto-derived)
empirica finding-log --finding "OAuth2 uses PKCE flow for public clients" --impact 0.7
empirica unknown-log --unknown "How to handle token refresh in our architecture?"
empirica deadend-log --approach "Tried implicit flow" --why-failed "Deprecated for security"
```

- Research documentation, search codebase
- Log findings, unknowns, dead-ends as breadcrumbs
- These persist in memory and inform future sessions

### 3. CHECK (Decision Gate)
**"Am I ready to proceed?"**

```bash
empirica check-submit - << 'EOF'
{
  "vectors": {"know": 0.75, "uncertainty": 0.3, "context": 0.8, "clarity": 0.85},
  "reasoning": "Investigated OAuth2 spec, found existing patterns"
}
EOF
```

- Sentinel gates praxic action (Edit, Write) until CHECK passes
- Returns `proceed` or `investigate` (keep exploring)

### 4. PRAXIC Phase (Do the Work)
**"Execute with goal tracking"**

```bash
# Create and complete goals
empirica goals-create --objective "Implement OAuth2 client with PKCE"
# ... write code, run tests ...
empirica goals-complete --goal-id <ID> --reason "Implementation verified"
```

### 5. POSTFLIGHT (Measure Learning)
**"What did I actually learn?"**

```bash
# Closes the transaction + triggers grounded verification
empirica postflight-submit - << 'EOF'
{
  "vectors": {"know": 0.85, "uncertainty": 0.15, "context": 0.9, "clarity": 0.9},
  "reasoning": "Learned OAuth2 PKCE flow, implemented and tested"
}
EOF
```

- Learning delta: PREFLIGHT vs POSTFLIGHT vectors
- Grounded verification (POST-TEST): compares self-assessment to objective evidence
- Calibration: Were initial assessments accurate?

---

## Real-World Example

### Scenario: "Implement user authentication"

**Without Empirica:**
```
1. AI starts implementing immediately
2. Makes architectural assumptions
3. Implements OAuth2 incorrectly
4. Code compiles but has security holes
5. Hours wasted debugging
```

**With Empirica:**

**PREFLIGHT:**
```
KNOW (auth domain): 0.40  ⚠️
CONTEXT (our architecture): 0.30  ⚠️
UNCERTAINTY: 0.75  ⚠️
→ Recommendation: INVESTIGATE
```

**INVESTIGATE:**
```bash
# Log as you discover (session_id auto-derived)
empirica finding-log --finding "System uses Auth0 for SSO" --impact 0.7
empirica unknown-log --unknown "How to handle session persistence?"
```

**CHECK:**
```bash
empirica check-submit -   # Returns: proceed
```

**PRAXIC (Execute):**
```bash
empirica goals-create --objective "Integrate Auth0 OAuth2"
# ... implement ...
empirica goals-complete --goal-id <ID> --reason "Auth0 integrated, tests pass"
```

**POSTFLIGHT:**
```bash
empirica postflight-submit -
# Learning delta: KNOW 0.40 → 0.85 (+0.45), UNCERTAINTY 0.75 → 0.20 (-0.55)
# Grounded verification: tests pass, git shows 3 files changed
# Calibration: GOOD
```

---

## Key Benefits

### 1. Prevents Confabulation
AI can't claim knowledge it doesn't have - the ledger tracks reality.

### 2. Systematic Learning
Investigate **before** acting when uncertainty is high.

### 3. Measurable Progress
Learning deltas show **actual** knowledge growth, not subjective claims.

### 4. Project Continuity
Context loader eliminates "starting from scratch" between sessions.

### 5. Multi-Agent Collaboration
BEADS integration allows AI agents to discover and resume each other's work.

### 6. Token Efficiency
- Git checkpoints: ~85% token reduction
- Handoff reports: ~90% token reduction
- Project bootstrap: Compressed context (~800 tokens)

---

## Architecture Overview

### Core Components

```
empirica/
├── core/                          # Epistemic framework
│   ├── canonical/                 # 13-vector assessment
│   ├── qdrant/                    # Semantic search (optional)
│   └── lessons/                   # Procedural knowledge
│
├── data/                          # SQLite storage
│   ├── session_database.py        # Main API
│   └── schema/                    # Table schemas
│
├── cli/                           # Command-line interface (138+ commands)
│   ├── command_handlers/          # Command implementations
│   └── parsers/                   # Argument parsers
│
└── utils/                         # Session resolver, path resolver
```

### Data Storage (per-project)

```
.empirica/
├── sessions/
│   └── sessions.db                # SQLite database (per project)
├── ref-docs/                      # Reference documents
├── PROJECT_CONFIG.yaml            # Project configuration
└── .breadcrumbs.yaml              # Calibration data
```

### Git Integration

```
git notes refs/empirica/checkpoints   # Compressed session data
git notes refs/empirica/handoffs      # Session handoff reports
git notes refs/empirica/breadcrumbs   # Learning trajectory
git notes refs/empirica/goals         # Goal discovery
```

---

## Command Quick Reference

### Session Management
```bash
empirica session-create --ai-id myai
empirica sessions-list
empirica sessions-resume --ai-id myai
```

### CASCADE Workflow
```bash
empirica preflight-submit -             # PREFLIGHT (JSON stdin)
empirica check-submit -                 # CHECK gate (JSON stdin)
empirica postflight-submit -            # POSTFLIGHT (JSON stdin)
```

### Noetic Artifacts (log as you work)
```bash
empirica finding-log --finding "..." --impact 0.7    # What was learned
empirica unknown-log --unknown "..."                  # What's unclear
empirica deadend-log --approach "..." --why-failed "..."  # Failed approaches
```

### Project Tracking
```bash
empirica project-init                   # Initialize in CWD
empirica project-bootstrap              # Load project context
empirica project-list                   # List all projects
empirica project-switch <name>          # Switch project
```

### Goals & Subtasks
```bash
empirica goals-create --session-id <ID> --objective "..."
empirica goals-add-subtask --goal-id <ID> --description "..."
empirica goals-complete-subtask --task-id <ID>
empirica goals-progress --goal-id <ID>
```

### Multi-Agent Collaboration
```bash
empirica goals-discover                    # Find goals from other AIs
empirica goals-resume --goal-id <ID>       # Resume someone's goal
empirica goals-claim --goal-id <ID>        # Create branch + issue link
empirica goals-complete --goal-id <ID>     # Merge + close
```

### Git Integration
```bash
empirica checkpoint-create --session-id <ID>
empirica checkpoint-load --session-id <ID>
empirica handoff-create --session-id <ID>
empirica handoff-query --ai-id myai
```

---

## What Makes Empirica Different?

### Traditional AI Workflows:
- AI claims confidence without evidence
- No systematic learning tracking
- Context lost between sessions
- No collaboration framework
- Token-inefficient handoffs

### Empirica:
- ✅ **Genuine self-assessment** (13 epistemic vectors)
- ✅ **Systematic investigation** (CASCADE workflow)
- ✅ **Measurable learning** (delta tracking)
- ✅ **Dynamic context loading** (project-bootstrap)
- ✅ **Multi-agent collaboration** (BEADS integration)
- ✅ **Token-efficient persistence** (git notes)

---

## Getting Started

### 1. Install
```bash
pip install empirica
```

### 2. Initialize project + create session
```bash
cd your-project
empirica project-init
empirica session-create --ai-id myai --output json
```

### 3. Run CASCADE workflow
```bash
empirica preflight-submit -        # Assess baseline (JSON stdin)
# Investigate... log findings...
empirica check-submit -            # Gate check
# Act... complete goals...
empirica postflight-submit -       # Measure learning
```

### 4. For Claude Code integration
```bash
empirica setup-claude-code         # Installs plugin, hooks, CLAUDE.md
```

---

## Next Steps

- **For users:** See [01_START_HERE.md](01_START_HERE.md)
- **For developers:** See [CLI Commands](../developers/CLI_COMMANDS_UNIFIED.md)
- **For Claude Code:** Run `empirica setup-claude-code`

---

**Key Insight:** Empirica isn't just tracking - it's a **systematic approach to AI that knows what it knows**, learns efficiently, and collaborates effectively across sessions and agents.
