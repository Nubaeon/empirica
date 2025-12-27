# Project Bootstrap: Visual Guide & Real Output Example

This document shows **exactly what Empirica captures** using a real project-bootstrap run, annotated with epistemic meanings.

---

## Real Bootstrap Output (Empirica Project)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 PROJECT CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 Project: empirica
🆔 ID: ea2f33a4-d808-434b-b776-b7246bd6134a
🔗 Repository: https://github.com/Nubaeon/empirica.git
📍 Location: /home/yogapad/empirical-ai/empirica/.empirica
💾 Database: .empirica/sessions/sessions.db
```

**What This Tells You:**
- ✅ Project is properly initialized in git
- ✅ Database location is tracked
- ✅ All work is confined to this project context
- 🎯 Any findings/goals/sessions go here

---

## Section 1: Project Summary

```
📋 Project Summary
   Empirica CLI and framework core - empirical-ai/empirica git repo
   Repos: https://github.com/Nubaeon/empirica.git
   Total sessions: 1

🕐 Last Activity:
   Last activity: 1765467355.323723
   Next focus: Continue with incomplete work and unknown resolutions
```

**Epistemic Meaning:**
- **Only 1 total session**: This project is in early stages
- **Last activity timestamp**: Tells you how recently work was done
- **"Continue with incomplete work"**: Signals that work is ongoing

---

## Section 2: Git Status (Current State)

```
🌿 Git Status:
   Branch: epistemic/reasoning/goal-2393d8ff
   Uncommitted: 6 file(s)
   Untracked: 0 file(s)
   Recent commits:
      • ca99caf3 feat: Phase 8 Batch 8 - Extract migration + session_summary (hit <2000 target!)
      • c3d44994 feat: Phase 8 Batch 7 - Token delegation + dead code removal (saved 91 lines)
      • 69d47482 feat: Phase 8 Batch 6 - Delegate _load_goals_for_project (saved 28 lines)
```

**What This Tells You:**

| Data | Meaning | Action |
|------|---------|--------|
| `epistemic/reasoning/goal-2393d8ff` | Working on a specific goal | Context is clear - branch name tells story |
| `6 uncommitted files` | Incomplete thought | Finish current changes before new work |
| `0 untracked files` | Clean workspace | No exploratory dead ends |
| Recent commits all "feat:" | Making progress | Momentum is positive |
| Messages show metrics | Work is measured | Quality-conscious work |

**Epistemic Health Signal:**
🟢 **GOOD** - Branch is focused, commits are progress-oriented, workspace is clean

---

## Section 3: Auto-Captured Issues (Current Problems)

```
⚠️  Auto-Captured Issues (5):
   🟠 HIGH (4):
      • bug: CHECK-SUBMIT command doesn't support JSON stdin/config input
        Location: <stdin>:7
      • bug: CHECK command doesn't support JSON stdin input - expects CLI
        Location: <stdin>:7
      • todo: TODO (high): Implement connection pooling for database
        Location: /home/yogapad/empirical-ai/empirica/empirica/core/issue_capture.py:261
      ... and 1 more high issues
   🟡 MEDIUM (1):
      • performance: Performance issue: Query user_profiles table took 2500.0ms
        Location: /home/yogapad/empirical-ai/empirica/empirica/core/issue_capture.py:237
```

**What This Tells You:**

| Issue | Type | Severity | Next AI Should... |
|-------|------|----------|------------------|
| CHECK-SUBMIT no JSON | bug | HIGH | Fix immediately (blocking AI workflow) |
| CHECK no JSON | bug | HIGH | Fix immediately (blocking AI workflow) |
| Connection pooling | todo | HIGH | Add to backlog (important for scale) |
| Query performance | perf | MEDIUM | Investigate if slowing work |

**Epistemic Clarity Signal:**
🟡 **AT RISK** - 4 high issues found, some blocking automation. System needs fixes before scaling.

**Decision Point:**
```
IF critical_issues > 0:
    Action: Fix bugs first, THEN continue work
ELSE:
    Action: Proceed with work
```

---

## Section 4: Recent Findings (What Was Learned)

```
📝 Recent Findings (last 10):
   1. "CHECK command auto-loading confirmed: Lines 247-263 in workflow_commands.py 
       use BreadcrumbRepository to auto-load all project findings and unresolved 
       unknowns. Evidence-based decision making is fully functional."
       
   2. "System prompt updated to v5.0 (CLAUDE.md). Git notes storage bug fixed 
       (wrong command syntax). CHECK auto-load verified working with 297 findings loaded."
       
   3. "CASCADE commands fixed for AI-first automation: CHECK and CHECK-SUBMIT now 
       support stdin JSON + config files. All commands support AI-first JSON mode. 
       Enables seamless automation."
       
   4. "Auto-capture enables continuous epistemic learning: Issues stored with status 
       lifecycle (new→investigating→resolved/wontfix/handoff). Next AI learns what 
       was tried, what worked, what failed. Foundation for Phase 3 Qdrant semantic learning."
       
   5. "Auto Issue Capture Phase 1 Complete: Core service (427 lines), 6 CLI commands 
       (issue-list/show/handoff/resolve/export/stats), database schema auto_captured_issues 
       table, multi-AI handoff with full context..."
```

**Epistemic Meaning:**

| Finding | Knowledge Type | Confidence | Age |
|---------|---|---|---|
| CHECK auto-load confirmed | Implementation detail | VERIFIED (code-backed) | Recent |
| System prompt v5.0 + fixes | Architecture change | VERIFIED | Recent |
| CASCADE AI-first ready | Feature complete | VERIFIED | Recent |
| Auto-capture lifecycle | System design | VERIFIED | Recent |
| Phase 1 Complete | Milestone | VERIFIED | Recent |

**Epistemic Health Signal:**
🟢 **HEALTHY** - 5 recent, verified findings. System is stable and advancing.

**What Next AI Learns:**
- CHECK is verified working ✅
- JSON mode is available ✅
- AUTO-CAPTURE is Phase 1 complete ✅
- v5.0 system prompt is active ✅

---

## Section 5: Unresolved Unknowns (Open Questions)

```
❓ Unresolved Unknowns:
   1. "Exit codes fix (68 commands): Assigned to Qwen. All CLI handlers should 
       return 0 (success) or sys.exit(1) (error) instead of returning dicts."
       
   2. "Phase 2: Integrate issues into project-bootstrap output. Display active 
       issues in CHECK gate for context. Auto-capture CASCADE errors. Plan in 
       IMPLEMENTATION_PLAN_AUTO_CAPTURE_PHASE2.develop.md on develop branch."
       
   3. "Should pre-compact hook auto-commit working directory before snapshot? 
       Currently doesn't - may miss uncommitted changes in snapshot"
       
   4. "Testing auto-resolution of project ID in unknown-log command"
       
   5. "Is --verbose flag work still pending? Plan file says incomplete but 
       didnt verify against git history or current codebase state."
```

**Epistemic Meaning:**

| Unknown | Blocker? | Assigned? | Status |
|---------|----------|-----------|--------|
| Exit codes fix | LOW | Yes (Qwen) | Delegated |
| Phase 2 integration | MEDIUM | No | Open |
| Auto-commit behavior | MEDIUM | No | Design question |
| Project ID testing | LOW | No | Testing |
| --verbose flag | LOW | No | Verification |

**Epistemic Clarity Signal:**
🟡 **PARTIALLY CLEAR** - Design decisions are still open. Next AI should consider these before new work.

**What Next AI Should Know:**
- Exit codes work is assigned to Qwen (don't duplicate)
- Phase 2 plan exists on develop branch (check it)
- Auto-commit behavior is TBD (design decision needed)
- Some testing still pending (verify before trusting results)

---

## Section 6: Dead Ends (What Didn't Work)

```
💀 Dead Ends (What Didn't Work):
   1. "Testing auto-resolution of project ID in deadend-log command"
      → Why: Testing that project ID auto-resolves properly
      
   2. "Using --project-id parameter with mistake-log command"
      → Why: Command doesn't accept --project-id parameter
      
   3. "Test approach"
      → Why: Test failure reason
      
   4. "Final verification test"
      → Why: Success - not a real failure
```

**Epistemic Meaning:**

| Dead End | Type | Lesson |
|----------|------|--------|
| Project ID auto-resolution | Testing | Sometimes it works, sometimes manual needed |
| --project-id on mistake-log | API Limitation | Command interface is inconsistent |
| Test approach | Method | Initial approach didn't work |
| Final test | N/A | Success (false positive in dead ends) |

**Epistemic Clarity Signal:**
🟡 **NEEDS ATTENTION** - Some dead ends are marked "Success" which shouldn't be dead ends. Data hygiene issue.

**What Next AI Should Know:**
- Don't assume all commands accept --project-id
- Project ID resolution may need fallback handling
- Be consistent with command interfaces

---

## Section 7: Recent Mistakes (Avoid These!)

```
⚠️  Recent Mistakes to Avoid:
❌ Project bootstrap error: 'cost'
```

**Epistemic Meaning:**

This indicates a recent bug where the 'cost' key was missing from breadcrumbs structure.

**What This Tells You:**
- This bug was encountered and fixed
- Next AI should avoid this: breadcrumbs must include 'cost' field
- If you see this error again, it means the fix regressed

**Prevention Checklist:**
- [ ] Verify breadcrumbs has 'cost' field before using
- [ ] Test project-bootstrap after any breadcrumbs schema changes
- [ ] Add regression test for this

---

## Complete Epistemic Picture

### Health Summary
```
✅ HEALTH:        GREEN  (Recent findings, clean git state, focused work)
🟡 CLARITY:       YELLOW (Some unknowns, some dead ends need cleanup)
🟠 ISSUES:        ORANGE (4 high-severity bugs blocking automation)
```

### What This Bootstrap Session Tells You

**Starting Point for Next AI:**
```
You are starting on: empirica/reasoning/goal-2393d8ff (goal ID)

Context:
  • Project is at Phase 8, batches 6-8 complete
  • Session_database refactoring in progress (extraction + modularization)
  • Previous AI: Claude (from name guessing)

Immediate Actions Needed:
  1. FIX: CHECK-SUBMIT JSON stdin support (bug blocking automation)
  2. FIX: CHECK JSON stdin support (same issue)
  3. REVIEW: Phase 2 plan for auto-capture integration
  4. DECISION: Auto-commit behavior for pre-compact hook

Verified Working:
  ✅ CHECK auto-load of findings (297 findings available)
  ✅ CASCADE JSON mode for all commands
  ✅ Auto-capture Phase 1 complete
  ✅ v5.0 system prompt active

Active Unknowns:
  ❓ Exit code normalization (delegated to Qwen)
  ❓ Project ID auto-resolution edge cases
  ❓ --verbose flag status

Recent Progress:
  • Phase 8 Batch 8: Extract migration + session_summary (target <2000 lines met!)
  • Phase 8 Batch 7: Token delegation + dead code (saved 91 lines)
  • Phase 8 Batch 6: _load_goals_for_project delegation (saved 28 lines)

Git State:
  • Branch: epistemic/reasoning/goal-2393d8ff
  • Uncommitted: 6 files (in progress)
  • Untracked: 0 (clean)
  • Ready for: Continue extraction work or bug fixes
```

---

## Decision Tree: What to Do Based on Bootstrap Output

```
START: Review Bootstrap

├─ Critical Issues Found?
│  ├─ YES → Fix immediately before new work
│  └─ NO → Continue below
│
├─ High Uncertainty in Handoff?
│  ├─ YES (> 0.60) → Load full context, add CHECK gates
│  └─ NO → Continue below
│
├─ Many Unresolved Unknowns?
│  ├─ YES (> 10) → Investigation session first
│  └─ NO → Continue below
│
├─ Recent Dead Ends in Same Area?
│  ├─ YES → Different approach needed, review lessons
│  └─ NO → Continue below
│
├─ Uncommitted Changes > 5?
│  ├─ YES → Finish or commit current work first
│  └─ NO → Ready to start
│
└─ PROCEED: With understanding of context
```

---

## Measuring Epistemic Health

### Metrics from Bootstrap

```
Health Score (0-100):

Factors:
  ✅ Recent findings (1 point per finding < 1 hour old)           [Points: 5]
  ✅ Low uncertainty (10 - uncertainty*10)                         [Points: 7.5]
  ✅ High foundation (foundation_avg * 10)                         [Points: 6.5]
  ❌ Critical issues (-20 per critical)                            [Points: -20]
  ❌ High unknowns (-1 per unknown > 10)                           [Points: -0]
  ❌ Dead ends (-2 per dead end)                                   [Points: -6]
  ✅ Focused branch (+5 if branch matches goal)                    [Points: +5]
  ✅ Clean workspace (+5 if uncommitted < 3)                      [Points: 0]

Total Health Score: 73/100 = GOOD (borderline needs attention)
```

### Interpretation

```
90-100: EXCELLENT  → Proceed with confidence, minimal context needed
70-89:  GOOD       → Proceed carefully, pay attention to flagged issues
50-69:  CAUTION    → Load full context, use CHECK gates, take measured approach
30-49:  RISKY      → Deep investigation required, expert review needed
0-29:   CRITICAL   → System may be broken, consider rollback/reset
```

---

## For Documentation & Sharing

### Quick Bootstrap Summary (For Teams)

```
Empirica Project Bootstrap Summary
Project: empirica (id: ea2f33a4-d808-434b-b776-b7246bd6134a)
Captured: [timestamp]
AI: claude-rovodev

Health: 73/100 GOOD
Status: Phase 8 Batch 8 (Session_database refactoring)
Branch: epistemic/reasoning/goal-2393d8ff
Uncommitted: 6 files

Top Issues:
  🔴 HIGH: CHECK-SUBMIT JSON stdin support missing
  🔴 HIGH: CHECK JSON stdin support missing
  🟠 HIGH: Connection pooling not implemented

Ready Work:
  ✅ Continue extraction (goal-2393d8ff in progress)
  ✅ Fix JSON stdin bugs
  ✅ Review Phase 2 auto-capture plan

Blockers:
  ❓ 5 unknowns (1 assigned to Qwen)
  ⚠️  4 high issues (2 blocking automation)

Recent Learning:
  • CHECK auto-load: 297 findings available ✅
  • CASCADE JSON mode: Ready for automation ✅
  • Auto-capture Phase 1: Complete ✅
```

---

## What Each Section Enables

| Section | Enables | Prevents |
|---------|---------|----------|
| **Project Context** | Knowing where work is stored | Working on wrong project |
| **Git Status** | Understanding current state | Starting with stale code |
| **Issues** | Fixing blockers first | Building on broken foundation |
| **Findings** | Acting on verified knowledge | Re-discovering known things |
| **Unknowns** | Asking right questions | Wasting time on answered questions |
| **Dead Ends** | Learning from failures | Repeating failed approaches |
| **Mistakes** | Avoiding repeated errors | Making same mistakes twice |

---

## Conclusion

The complete bootstrap output provides:

1. **Epistemic Health**: Current readiness level and uncertainty
2. **Epistemic Clarity**: What's known, unknown, and failed
3. **Epistemic Relevance**: Context alignment with current work

Together, these enable AI agents to make informed decisions from the very start, guided by evidence from previous sessions rather than guesses or assumptions.
