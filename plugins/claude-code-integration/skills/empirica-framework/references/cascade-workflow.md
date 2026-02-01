# CASCADE Workflow: Detailed Guide

**Related docs:**
- [SENTINEL_ARCHITECTURE.md](../../../../docs/architecture/SENTINEL_ARCHITECTURE.md) - Gate control between phases
- [NOETIC_PRAXIC_FRAMEWORK.md](../../../../docs/architecture/NOETIC_PRAXIC_FRAMEWORK.md) - Noetic (investigate) vs Praxic (act) phases
- [Architecture README](../../../../docs/architecture/README.md) - System overview with CASCADE in context
- [Vector Guide](./vector-guide.md) - Epistemic vectors used in assessments

## Overview

CASCADE is the epistemic workflow that ensures you measure what you know before and after tasks.

```
PREFLIGHT → INVESTIGATE → CHECK → ACT → POSTFLIGHT → POST-TEST
    ↓           ↓          ↓       ↓        ↓            ↓
 Baseline    Reduce     Gate    Execute   Measure     Grounded
  state    uncertainty  check    work     learning   Verification
```

POST-TEST is automatic — triggered by POSTFLIGHT. It collects objective evidence
(tests, artifacts, git, goals) and compares to self-assessed vectors for grounded calibration.

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

## Phase 6: POST-TEST (Grounded Verification) — Automatic

**Purpose:** Compare self-assessed vectors against objective evidence.

**Triggered automatically** by POSTFLIGHT. No manual step needed.

**Evidence collected:**
| Source | Quality | Vectors Grounded |
|--------|---------|-----------------|
| pytest results | OBJECTIVE | know, do, clarity |
| Git metrics | OBJECTIVE | do, change, state |
| Goal completion | SEMI_OBJECTIVE | completion, do, know |
| Artifact counts | SEMI_OBJECTIVE | know, uncertainty, signal |
| Issue tracking | SEMI_OBJECTIVE | impact, signal |
| Sentinel decisions | SEMI_OBJECTIVE | context, uncertainty |

**Ungroundable vectors:** engagement, coherence, density — no objective signal exists.

## Dual-Track Calibration

The system uses two parallel calibration tracks:

### Track 1: Self-Referential (PREFLIGHT → POSTFLIGHT)

**Learning delta:**
```
know: 0.6 → 0.85 = +0.25 (significant learning)
uncertainty: 0.5 → 0.2 = -0.3 (uncertainty reduced)
context: 0.4 → 0.9 = +0.5 (major context gain)
```

### Track 2: Grounded (POSTFLIGHT → Objective Evidence)

**Calibration accuracy:**
```
POSTFLIGHT know=0.85 vs evidence know=0.80 → gap = +0.05 (well calibrated)
POSTFLIGHT completion=0.9 vs evidence completion=0.6 → gap = +0.30 (overestimate)
```

When tracks disagree, Track 2 (grounded) is more trustworthy.

```bash
# Self-referential calibration
empirica calibration-report

# Grounded calibration — self-assessment vs evidence
empirica calibration-report --grounded

# Trajectory — is calibration improving over time?
empirica calibration-report --trajectory
```

## Workflow Variations

### Quick Task (< 30 min)
```
PREFLIGHT → ACT → POSTFLIGHT → POST-TEST
```
Skip CHECK for low-risk, well-understood tasks.

### Investigation Task
```
PREFLIGHT → INVESTIGATE → POSTFLIGHT → POST-TEST
```
When the goal is understanding, not action.

### Complex Feature
```
PREFLIGHT → Goal + Subtasks → [INVESTIGATE → CHECK]* → ACT → POSTFLIGHT → POST-TEST
```
Multiple CHECK cycles as uncertainty is reduced.

### Multi-Session
```
Session 1: PREFLIGHT → INVESTIGATE → CHECK → Handoff
Session 2: Load Handoff → PREFLIGHT → ACT → POSTFLIGHT → POST-TEST
```
Handoffs preserve epistemic state across sessions.

POST-TEST is automatic — triggered by POSTFLIGHT. No manual step needed.
