# Empirica Explained Simply

**What it is:** A system that helps AI agents know what they know (and don't know), track project learning, and collaborate effectively.

**Date:** 2025-12-18  
**Version:** 4.0

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
empirica preflight --session-id <SESSION_ID>
```

- Assess all 13 epistemic vectors **honestly**
- Not "I can figure it out" but "What do I know RIGHT NOW?"
- System calculates: **Should I investigate first?**

**Output:**
```
KNOW: 0.45  ⚠️  Below threshold (0.60)
UNCERTAINTY: 0.70  ⚠️  High uncertainty
→ RECOMMENDATION: Investigate before proceeding
```

### 2. CHECK (Decision Gate)
**"Am I ready to proceed?"**

```bash
empirica check --session-id <SESSION_ID>
```

- Review findings from investigation
- Assess remaining unknowns
- Confidence to proceed (0.0-1.0)

**If confidence ≥ 0.7:** Proceed to ACT  
**If confidence < 0.7:** Investigate more

### 3. INVESTIGATE (Reduce Uncertainty)
**"Let me learn what I need to know"**

```bash
empirica investigate <file_or_concept>
```

- Research documentation
- Search codebase
- Run experiments
- Log findings/unknowns

**Example:**
```bash
empirica finding-log --project-id <ID> \
    --finding "OAuth2 uses PKCE flow for public clients"

empirica unknown-log --project-id <ID> \
    --unknown "How to handle token refresh in our architecture?"
```

### 4. ACT (Do the Work)
**"Execute with epistemic tracking"**

```bash
empirica act-log --session-id <SESSION_ID> \
    --action "Implemented OAuth2 client with PKCE"
```

- Do the actual implementation
- Log key actions
- Track progress

### 5. POSTFLIGHT (Measure Learning)
**"What did I actually learn?"**

```bash
empirica postflight --session-id <SESSION_ID>
```

- Re-assess all 13 vectors
- Calculate learning delta: `KNOW: 0.45 → 0.85 (+0.40)`
- Measure calibration: Were initial assessments accurate?

**Output:**
```
Epistemic Delta:
  KNOW: 0.45 → 0.85 (+0.40)  📈
  CONTEXT: 0.50 → 0.90 (+0.40)  📈
  UNCERTAINTY: 0.70 → 0.15 (-0.55)  ✓

Calibration: GOOD (initial assessment was realistic)
```

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
empirica investigate "authentication architecture"
# Searches codebase, finds existing patterns
# Reads OAuth2 spec

empirica finding-log \
    --finding "System uses Auth0 for SSO, need to integrate"

empirica unknown-log \
    --unknown "How to handle session persistence?"
```

**CHECK:**
```
Findings: 3 items
Unknowns: 1 item (session persistence)
Confidence: 0.75  ✓
→ Decision: PROCEED (acceptable confidence)
```

**ACT:**
```bash
# Implement with Auth0 integration
empirica act-log --action "Integrated Auth0 SDK"
empirica act-log --action "Added session middleware"
```

**POSTFLIGHT:**
```
KNOW: 0.40 → 0.85 (+0.45)  📈
CONTEXT: 0.30 → 0.90 (+0.60)  📈
UNCERTAINTY: 0.75 → 0.20 (-0.55)  ✓

Learning verified: Strong improvement
Implementation: Correct on first try
Time saved: ~3 hours of debugging
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
│   └── metacognitive_cascade/     # CASCADE workflow
│
├── data/                          # SQLite storage
│   ├── session_database.py        # Main API
│   └── schema.sql                 # Tables (sessions, goals, reflexes, etc.)
│
├── cli/                           # Command-line interface
│   └── commands/                  # 67 commands
│
└── vision/                        # Content assessment (NEW)
    ├── slide_processor.py         # OCR + epistemic scoring
    └── readable_translator.py     # Human-friendly output
```

### Data Storage

```
.empirica/
├── empirica.db                    # SQLite database
├── sessions/                      # Session data
├── projects/                      # Project breadcrumbs
└── slides/                        # Vision assessments
```

### Git Integration

```
git notes refs/empirica/checkpoints   # Compressed session data
git notes refs/empirica/handoffs      # Session handoff reports
git notes refs/empirica/goals         # Goal discovery (Phase 1)
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
empirica preflight --session-id <ID>
empirica check --session-id <ID>
empirica investigate <file_or_concept>
empirica act-log --session-id <ID> --action "..."
empirica postflight --session-id <ID>
```

### Project Tracking
```bash
empirica project-create --name "My Project"
empirica project-bootstrap --project-id <ID>
empirica finding-log --project-id <ID> --finding "..."
empirica unknown-log --project-id <ID> --unknown "..."
empirica deadend-log --project-id <ID> --approach "..." --why-failed "..."
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

### 2. Create a session
```bash
empirica session-create --ai-id myai --output json
```

### 3. Run PREFLIGHT
```bash
empirica preflight --session-id <SESSION_ID>
```

### 4. Follow CASCADE workflow
- If uncertain → INVESTIGATE
- If confident → ACT
- Always → POSTFLIGHT

### 5. Create handoff for next session
```bash
empirica handoff-create --session-id <SESSION_ID>
```

---

## Next Steps

- **For users:** See [01_START_HERE.md](01_START_HERE.md)
- **For developers:** See [reference/CANONICAL_DIRECTORY_STRUCTURE.md](reference/CANONICAL_DIRECTORY_STRUCTURE.md)
- **For AI agents:** See [system-prompts/CANONICAL_SYSTEM_PROMPT.md](system-prompts/CANONICAL_SYSTEM_PROMPT.md)

---

**Key Insight:** Empirica isn't just tracking - it's a **systematic approach to AI that knows what it knows**, learns efficiently, and collaborates effectively across sessions and agents.
