# Epistemic Health Quick Reference Card

**One-page guide to understanding Empirica's epistemic capabilities**

---

## What is Epistemic Health?

**Definition:** The AI's state of knowledge, clarity, and readiness to work effectively

Three Dimensions:
- **Health**: Readiness + capability + confidence levels
- **Clarity**: Understanding depth + coherence + signal strength  
- **Relevance**: Context alignment to current task

---

## The 13 Epistemic Vectors (What Empirica Measures)

### Foundation Layer (What You Know)
```
KNOW      (0.0-1.0) → Factual understanding of the domain
DO        (0.0-1.0) → Practical capability to execute
CONTEXT   (0.0-1.0) → Understanding of surrounding environment
```

### Comprehension Layer (How Well You Understand)
```
CLARITY   (0.0-1.0) → How clear concepts are in your mind
COHERENCE (0.0-1.0) → How connected ideas are
SIGNAL    (0.0-1.0) → Pattern recognition ability
DENSITY   (0.0-1.0) → Information richness in explanations
```

### Execution Layer (Your Progress)
```
STATE     (0.0-1.0) → Current progress in task
CHANGE    (0.0-1.0) → Rate of learning/improvement
COMPLETION(0.0-1.0) → Task progress toward goal
IMPACT    (0.0-1.0) → Significance of work done
```

### Meta Layer (Self-Awareness)
```
ENGAGEMENT(0.0-1.0) → Focus level on task
UNCERTAINTY(0.0-1.0) → Explicit doubt level
```

**Total: 13 dimensions tracked per session**

---

## Project Bootstrap: What Gets Captured

```
┌─────────────────────────────────────────────────────────┐
│ EPISTEMIC SNAPSHOT (per session end)                    │
├─────────────────────────────────────────────────────────┤
│ 1. Epistemic Vectors (all 13) from POSTFLIGHT           │
│ 2. Git State (branch, commits, uncommitted)             │
│ 3. Auto-Captured Issues (5-20 recent)                   │
│ 4. Recent Findings (10 most recent discoveries)         │
│ 5. Unresolved Unknowns (questions still open)           │
│ 6. Dead Ends (what didn't work + why)                   │
│ 7. Mistakes (errors to avoid)                           │
│ 8. Project Metadata (context info)                      │
└─────────────────────────────────────────────────────────┘
```

**Total Data:** ~15KB per session snapshot  
**Update Frequency:** Every session end  
**Retention:** Permanent (in SQLite + git notes)  
**Access:** `empirica project-bootstrap --ai-id <YOUR_ID>`

---

## Quick Interpretation Guide

### Health Level Assessment

**🟢 HEALTHY (Score: 70-100)**
```
Signals:
  • Low uncertainty (< 0.35)
  • High foundation (know + do > 1.4)
  • Few unknowns (< 5)
  • Recent findings (< 2h old)
  • No critical issues
  • Focused git branch
  • Clean workspace

Action: PROCEED with confidence
```

**🟡 AT RISK (Score: 50-69)**
```
Signals:
  • Moderate uncertainty (0.35-0.60)
  • Mixed foundation (0.8-1.4)
  • Several unknowns (5-10)
  • Older findings (2-6h old)
  • Some high issues
  • Uncommitted changes
  • Some dead ends

Action: LOAD FULL CONTEXT, use CHECK gates
```

**🔴 CRITICAL (Score: 0-49)**
```
Signals:
  • High uncertainty (> 0.60)
  • Low foundation (< 0.8)
  • Many unknowns (> 10)
  • Stale findings (> 1 day old)
  • Critical issues present
  • Massive uncommitted state
  • Repeated dead ends/mistakes

Action: INVESTIGATION SESSION REQUIRED
```

---

## The Bootstrap Output Structure

```
PROJECT CONTEXT
├─ Project ID & Location
├─ Repository URL
└─ Database location

PROJECT SUMMARY
├─ Total sessions count
└─ Last activity timestamp

GIT STATUS
├─ Current branch
├─ Uncommitted changes
├─ Untracked files
└─ Recent 3 commits

AUTO-CAPTURED ISSUES
├─ Critical issues (red 🔴)
├─ High issues (orange 🟠)
├─ Medium issues (yellow 🟡)
└─ Low issues (blue 🔵)

EPISTEMIC HANDOFF
├─ All 13 vectors from previous session
├─ Engagement level
├─ Foundation understanding
├─ Comprehension depth
├─ Execution progress
└─ Uncertainty level

RECENT FINDINGS
├─ 10 most recent discoveries
├─ Verified knowledge
├─ Timestamps
└─ Related goals

UNRESOLVED UNKNOWNS
├─ Open questions
├─ Assignment (if any)
├─ Status (new/investigating/etc)
└─ Blocker indicators

DEAD ENDS
├─ Failed approaches
├─ Why they failed
├─ When tried
└─ Prevention hints

RECENT MISTAKES
├─ Errors made
├─ Impact
├─ How fixed
└─ Prevention
```

---

## Reading Bootstrap for Different Roles

### For Implementation AIs
```
FOCUS ON:
  ✓ Issues (what's broken)
  ✓ Git Status (what code to modify)
  ✓ Findings (what was discovered)
  ✓ Dead Ends (what doesn't work)

USE:
  • Fix high/critical issues first
  • Check findings before implementing
  • Avoid dead end approaches
  • Commit frequently
```

### For Reasoning/Planning AIs
```
FOCUS ON:
  ✓ Unknowns (open questions)
  ✓ Dead Ends (patterns of failure)
  ✓ Uncertainty (confidence levels)
  ✓ Mistakes (conceptual gaps)

USE:
  • Design sessions to resolve unknowns
  • Investigate repeated dead ends
  • High uncertainty = needs investigation
  • Mistakes suggest missing concepts
```

### For Testing AIs
```
FOCUS ON:
  ✓ Issues (bugs to verify)
  ✓ Dead Ends (failed test approaches)
  ✓ Mistakes (regressions to watch for)
  ✓ Findings (what's supposed to work)

USE:
  • Test reported issues first
  • Avoid dead end test approaches
  • Verify mistakes are fixed
  • Validate findings with tests
```

### For Project Managers
```
FOCUS ON:
  ✓ Health Score (overall readiness)
  ✓ Issue Count (blocking work)
  ✓ Unknown Count (clarity)
  ✓ Recent Findings (progress)

USE:
  • Health < 50 = escalate
  • Issue count rising = attention needed
  • Finding count shows learning rate
  • Unknown count shows scope clarity
```

---

## Decision Framework: What to Do Based on Bootstrap

### Issue Severity Guide

```
CRITICAL (🔴):
  Examples: System down, commands broken, data corruption
  Action: FIX IMMEDIATELY before any other work
  Impact: Blocks all productivity

HIGH (🟠):
  Examples: Missing features, bugs in active code paths
  Action: Fix before new work starts
  Impact: Blocks current workstream

MEDIUM (🟡):
  Examples: Performance issues, TODOs in active code
  Action: Plan for this sprint/cycle
  Impact: Slows work, not blocking

LOW (🔵):
  Examples: Nice-to-haves, cosmetic issues
  Action: Backlog for future
  Impact: No immediate impact
```

### Uncertainty-Driven Decisions

```
UNCERTAINTY < 0.35 (Confident):
  ├─ Load: Minimal context (~500 tokens)
  ├─ Proceed: Immediately
  ├─ CHECK Gates: Optional
  └─ Outcome: Fast iteration, high productivity

UNCERTAINTY 0.35-0.60 (Moderate):
  ├─ Load: Moderate context (~1500 tokens)
  ├─ Proceed: After review
  ├─ CHECK Gates: Recommended
  └─ Outcome: Careful progress, validated steps

UNCERTAINTY 0.60-0.80 (High):
  ├─ Load: Full context (~3000 tokens)
  ├─ Proceed: After deep review
  ├─ CHECK Gates: Required
  └─ Outcome: Slow but validated progress

UNCERTAINTY > 0.80 (Very High):
  ├─ Load: EVERYTHING
  ├─ Proceed: Investigation session only
  ├─ CHECK Gates: Every decision
  └─ Outcome: Deep learning session, no productivity work
```

---

## Health Metrics Calculation

### Simple Health Score (0-100)

```
Base: 50

Add Points:
  + 10 if uncertainty < 0.35
  + 10 if foundation_avg > 0.70
  + 10 if recent findings > 5
  + 10 if no critical issues
  + 10 if uncommitted < 3 files
  + 10 if unknowns < 5
  + 10 if no repeated dead ends
  + 10 if branch matches goal

Subtract Points:
  - 20 if any critical issues
  - 10 if high unknowns (> 10)
  - 10 if uncertainty > 0.70
  - 5 per repeated dead end (same area)
  - 5 if uncommitted > 10

Score Interpretation:
  90-100: Excellent    (proceed immediately)
  70-89:  Good         (proceed carefully)
  50-69:  At Risk      (load context, CHECK gates)
  30-49:  Risky        (investigation needed)
  0-29:   Critical     (system may be broken)
```

---

## Common Scenarios & Responses

### Scenario 1: "Starting Fresh Session"
```
Bootstrap shows:
  • Health Score: 75 (good)
  • Uncertainty: 0.45 (moderate)
  • Issues: 1 medium, 0 critical
  • Recent findings: 6 (< 1h old)
  • Git: Branch matches goal ✓

Response:
  ✓ Load moderate context
  ✓ Read 3 recent findings
  ✓ Fix medium issue OR proceed with goal
  ✓ Use CHECK after 2 hours
  ✓ Proceed immediately
```

### Scenario 2: "Finding Bugs"
```
Bootstrap shows:
  • Health Score: 55 (at risk)
  • Critical issues: 2
  • High issues: 4
  • Unknowns: 8
  • Dead ends: 3 (same area)

Response:
  ✓ Fix critical issues FIRST (blocks work)
  ✓ Investigate repeated dead ends (root cause)
  ✓ Load full context (understand system)
  ✓ Resolve unknowns related to failures
  ✓ Use CHECK frequently (validate fixes)
  ✓ Don't start new work until critical resolved
```

### Scenario 3: "Continuing Previous Session"
```
Bootstrap shows:
  • Health Score: 82 (good)
  • Uncertainty: 0.30 (confident)
  • Recent findings: 8 (< 30m old)
  • Git: 4 uncommitted files in same module
  • No critical issues

Response:
  ✓ Load minimal context (you know this area)
  ✓ Read most recent finding (context)
  ✓ Continue current work (finish changes)
  ✓ Commit before starting new work
  ✓ Proceed immediately, CHECK optional
```

### Scenario 4: "System Confused"
```
Bootstrap shows:
  • Health Score: 28 (critical)
  • Uncertainty: 0.82 (very high)
  • Critical issues: 3
  • Unknowns: 15+
  • Dead ends: 8+ (scattered)
  • Repeated mistakes

Response:
  ✓ DO NOT START WORK
  ✓ Load EVERYTHING (full context)
  ✓ Run INVESTIGATION session
  ✓ Create diagram of system understanding
  ✓ Resolve top 3 unknowns
  ✓ Fix critical issues
  ✓ Document lessons learned
  ✓ Return to work ONLY when health > 50
```

---

## Handoff Checklist: From One AI to Next

Before finishing session:

- [ ] All work is committed to git
- [ ] POSTFLIGHT was submitted (epistemic vectors recorded)
- [ ] Critical issues are fixed or clearly documented
- [ ] Findings reflect actual work done
- [ ] Unknowns are documented with context
- [ ] Dead ends include "why it failed" reasoning
- [ ] Mistakes include prevention steps
- [ ] Next focus is clear and documented

Result: Next AI's bootstrap will show everything needed to proceed.

---

## Pro Tips

### Tip 1: Trust Your Health Score
"If bootstrap shows critical issues, fix them FIRST before starting new work. This isn't a suggestion - it's a signal that the foundation is broken."

### Tip 2: Recent Findings are Gold
"Recent findings (< 1 hour old) are context-adjacent knowledge from the same session. Read them first - they often contain the answer you need."

### Tip 3: Dead Ends Prevent Rework
"If bootstrap shows a dead end in your planned approach, don't retry it. Read WHY it failed - the lesson applies to your similar approach too."

### Tip 4: Unknowns are Blockers
"Each unknown is a question someone couldn't answer. If you're going to work in that area, resolve the unknown first. Otherwise you'll hit the same wall."

### Tip 5: Mistakes are Prevention Training
"Mistakes show conceptual gaps. If you see a repeated mistake, read the resolution - it's teaching you the missing concept."

### Tip 6: Branch Name is Context
"Git branch names often contain goal IDs or descriptions. If your branch doesn't match your work, you might be in the wrong context."

---

## Getting Started

### Command Reference

```bash
# Load bootstrap for your AI
empirica project-bootstrap --project-id <ID> --ai-id <YOUR_ID>

# Output as JSON (for parsing/automation)
empirica project-bootstrap --project-id <ID> --ai-id <YOUR_ID> --output json

# Save to file for reference
empirica project-bootstrap --project-id <ID> --ai-id <YOUR_ID> > bootstrap.txt

# Start a new session (before work)
empirica session-create --ai-id <YOUR_ID>

# Submit PREFLIGHT (before work, record baseline)
cat preflight.json | empirica preflight-submit -

# Use CHECK (mid-session decision gate)
cat check.json | empirica check -

# Submit POSTFLIGHT (after work, record final state)
cat postflight.json | empirica postflight-submit -
```

### Example Epistemic Vectors

**PREFLIGHT Example (Starting):**
```json
{
  "session_id": "...",
  "vectors": {
    "engagement": 0.80,
    "foundation": {"know": 0.60, "do": 0.70, "context": 0.50},
    "comprehension": {"clarity": 0.70, "coherence": 0.65, "signal": 0.60, "density": 0.50},
    "execution": {"state": 0.20, "change": 0.60, "completion": 0.20, "impact": 0.40},
    "uncertainty": 0.70
  },
  "reasoning": "Starting session. Moderate uncertainty due to codebase complexity."
}
```

**POSTFLIGHT Example (Ending):**
```json
{
  "session_id": "...",
  "vectors": {
    "engagement": 0.85,
    "foundation": {"know": 0.75, "do": 0.80, "context": 0.65},
    "comprehension": {"clarity": 0.80, "coherence": 0.75, "signal": 0.70, "density": 0.55},
    "execution": {"state": 0.85, "change": 0.80, "completion": 0.85, "impact": 0.90},
    "uncertainty": 0.35
  },
  "reasoning": "Session complete. Found root cause of performance issue. Know +0.15, Uncertainty -0.35"
}
```

---

## FAQ

**Q: What if bootstrap shows 0.5 for all vectors?**  
A: This means no POSTFLIGHT was recorded. The previous session didn't close properly. Treat it as unknown state.

**Q: How fresh is the bootstrap data?**  
A: As fresh as the last session's POSTFLIGHT submission. If no session is running, it's static.

**Q: Can I manually edit bootstrap data?**  
A: No - it's generated from database tables. Edit the source (findings, issues, unknowns tables) instead.

**Q: How do I improve health score?**  
A: 1) Fix issues, 2) Resolve unknowns, 3) Record findings, 4) Avoid dead ends, 5) Keep git clean.

**Q: What's the difference between a finding and an unknown?**  
A: Finding = something you learned (verified). Unknown = something you don't understand (question).

**Q: How long should bootstrap be?**  
A: Typical: 10-20 findings, 5-15 unknowns, 3-8 issues. >30 findings = too much history; <3 findings = too new.

---

## Summary

**Epistemic Health** = Your knowledge state across 13 dimensions  
**Project Bootstrap** = Snapshot of all epistemic data at session end  
**Health Score** = Quick quantification (0-100) of readiness  
**Vectors** = Measurable dimensions of understanding

**Use Bootstrap to:**
- Start sessions with complete context
- Make informed decisions before coding
- Avoid repeating failed approaches
- Understand system readiness
- Enable smooth AI-to-AI handoffs

**Result:** Cumulative learning, error prevention, and genuine knowledge transfer across session boundaries.

---

**Last Updated:** 2025-12-26  
**For Questions:** See EPISTEMIC_HEALTH_DOCUMENTATION.md or BOOTSTRAP_OUTPUT_VISUAL_GUIDE.md
