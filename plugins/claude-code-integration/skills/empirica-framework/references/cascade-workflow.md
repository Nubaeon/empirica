# CASCADE Workflow: Detailed Guide

## Overview

CASCADE is the epistemic workflow that ensures you measure what you know before and after tasks.

```
PREFLIGHT → INVESTIGATE → CHECK → ACT → POSTFLIGHT
    ↓           ↓          ↓       ↓        ↓
 Baseline    Reduce     Gate    Execute   Measure
  state    uncertainty  check    work     learning
```

## Phase 1: PREFLIGHT (Baseline Assessment)

**Purpose:** Establish honest baseline BEFORE starting work.

**What to assess:**
- KNOW: How well do I understand this domain/codebase/task?
- DO: Can I actually execute this? (proven capability, not aspiration)
- CONTEXT: Do I have sufficient information?
- CLARITY: Do I understand what's being asked?
- UNCERTAINTY: How uncertain am I about the above?

**Key principle:** Not "What score looks good?" but "What is my genuine state RIGHT NOW?"

**Rating scale:** 0-1, with rationale and evidence. High uncertainty (0.7-0.9) is valid data.

```bash
empirica preflight-submit - << 'EOF'
{
  "session_id": "<ID>",
  "task_context": "Review authentication module for security issues",
  "vectors": {
    "know": 0.6,
    "uncertainty": 0.5,
    "context": 0.4,
    "clarity": 0.9
  },
  "reasoning": "Familiar with auth concepts but not this codebase. Haven't seen architecture docs."
}
EOF
```

## Phase 2: INVESTIGATE (Fill Knowledge Gaps)

**Purpose:** Systematically reduce uncertainty before acting.

**Activities:**
- Read relevant code/docs
- Search for patterns
- Log findings and unknowns as you learn
- Update mental model

**Breadcrumb logging:**
```bash
# Discovery
empirica finding-log --finding "Auth uses stateless JWT, not sessions" --impact 0.7

# Question that emerged
empirica unknown-log --unknown "Where are refresh tokens stored?"

# Dead end (for future reference)
empirica deadend-log --approach "Tried grep for 'session'" --why-failed "Wrong mental model"
```

**Key:** Track WHAT you learned and HOW it changed your understanding.

## Phase 3: CHECK (Ready to Act?)

**Purpose:** Gate before major actions. Prevents premature execution.

**When to CHECK:**
- Uncertainty > 0.5
- Scope > 0.6 (high-impact changes)
- Post-compact (context was just reduced)
- Before irreversible actions

**What to provide:**
- Current vectors (updated from investigation)
- List of findings
- List of remaining unknowns
- Reasoning for proceed/investigate decision

```bash
empirica check-submit - << 'EOF'
{
  "session_id": "<ID>",
  "task_context": "Ready to implement token rotation?",
  "vectors": {
    "know": 0.75,
    "uncertainty": 0.3,
    "context": 0.8,
    "clarity": 0.85
  },
  "findings": [
    "JWT implementation uses RS256",
    "Refresh tokens stored in httpOnly cookies",
    "No current rotation mechanism"
  ],
  "unknowns": [
    "Rate limiting on refresh endpoint?"
  ],
  "reasoning": "Good understanding of current auth. One minor unknown acceptable for initial implementation."
}
EOF
```

**Decision:**
- **Proceed:** Confidence >= 0.7, unknowns are acceptable risk
- **Investigate:** Confidence < 0.7, or unknowns are showstoppers

## Phase 4: ACT (Execute the Work)

**Purpose:** Do the actual work with epistemic awareness.

**During ACT:**
- Execute the planned changes
- Log findings as you discover new information
- Create git checkpoints at natural breakpoints
- Track any scope changes

**If new unknowns emerge:** Consider returning to INVESTIGATE → CHECK cycle.

## Phase 5: POSTFLIGHT (Measure Learning)

**Purpose:** Measure epistemic delta (how much you learned).

**What to assess:**
- Same vectors as PREFLIGHT
- Compare to baseline
- Note unexpected discoveries
- Evaluate calibration quality

```bash
empirica postflight-submit - << 'EOF'
{
  "session_id": "<ID>",
  "task_context": "Completed token rotation implementation",
  "vectors": {
    "know": 0.85,
    "uncertainty": 0.2,
    "context": 0.9,
    "clarity": 0.9
  },
  "reasoning": "Much better understanding now. Discovered rate limiting was already in place. Implementation went smoother than expected."
}
EOF
```

## Calibration Report

The system compares PREFLIGHT → POSTFLIGHT to measure:

**Learning delta:**
```
know: 0.6 → 0.85 = +0.25 (significant learning)
uncertainty: 0.5 → 0.2 = -0.3 (uncertainty reduced)
context: 0.4 → 0.9 = +0.5 (major context gain)
```

**Calibration quality:**
- Were your PREFLIGHT estimates accurate?
- Did you over/underestimate your knowledge?
- How can you calibrate better next time?

## Workflow Variations

### Quick Task (< 30 min)
```
PREFLIGHT → ACT → POSTFLIGHT
```
Skip CHECK for low-risk, well-understood tasks.

### Investigation Task
```
PREFLIGHT → INVESTIGATE → POSTFLIGHT
```
When the goal is understanding, not action.

### Complex Feature
```
PREFLIGHT → Goal + Subtasks → [INVESTIGATE → CHECK]* → ACT → POSTFLIGHT
```
Multiple CHECK cycles as uncertainty is reduced.

### Multi-Session
```
Session 1: PREFLIGHT → INVESTIGATE → CHECK → Handoff
Session 2: Load Handoff → PREFLIGHT → ACT → POSTFLIGHT
```
Handoffs preserve epistemic state across sessions.
