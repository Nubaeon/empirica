# Empirica Dashboards - Quick Reference Guide

**Your single source of truth for what's happening in Empirica right now.**

---

## Quick Decision Matrix: Which Dashboard?

| Situation | Dashboard | Command |
|-----------|-----------|---------|
| **"What should I focus on right now?"** | Co-Lead Dashboard | `./empirica-coled.sh` |
| **"What's each AI working on?"** | Goals & Subtasks | `./empirica-goals-dashboard.sh` |
| **"Who's learning fastest?"** | Leaderboard | `./leaderboard.sh` |
| **"Full system health check"** | Status | `./status.sh` |
| **"What learning happened in commits?"** | Git History | `git log --format=%(trailers) -10` |

---

## The Dashboards

### 1. CO-LEAD DASHBOARD (`empirica-coled.sh`)

**For:** Quick overview, decision-making, what needs attention
**Shows:**
- System snapshot (active sessions, pending work)
- What each AI is working on RIGHT NOW
- Critical/high priority tasks (next 5)
- Learning status per AI
- Git mapping (reminder that all work is traceable)

**Usage:**
```bash
./empirica-coled.sh
```

**When to use:**
- First thing when joining a session with no memory
- Quick check before making decisions
- Delegating work to parallel AIs
- Identifying blockers

**Example output:**
```
SYSTEM SNAPSHOT
Sessions: 211 total | 121 active
Priority work: 0 critical | 0 high pending

🤖 WHAT'S IN PROGRESS
  🚀 claude-final-doc-sweep | Complete documentation sweep...
  🚀 test-new-methods | Test goal
  ⏸️  continuity-test2 | No active goal

🎯 CRITICAL WORK (Next 5)
  [Empty - no blocking work]

📈 LEARNING STATUS
  [Shows AI learning rates]
```

---

### 2. GOALS & SUBTASKS DASHBOARD (`empirica-goals-dashboard.sh`)

**For:** Detailed view of all work being tracked
**Shows:**
- Goals overview (total, completed, in-progress)
- Goals by AI/session
- Active goals in progress
- Subtasks breakdown (total, completed, in-progress)
- Subtasks by importance level
- Investigation logs
- Sample active goals with subtask counts
- Git mapping (links to commits)

**Usage:**
```bash
./empirica-goals-dashboard.sh
```

**When to use:**
- Planning work across team
- Assigning new subtasks
- Tracking investigations (unknowns/findings)
- Understanding full scope of work

**Key metrics it shows:**
- 80 total goals tracked
- 182 total subtasks (86 completed, 96 pending)
- Breakdown by importance: Critical, High, Medium, Low
- Which goals are "in progress" and their subtask count

---

### 3. LEADERBOARD (`leaderboard.sh`)

**For:** AI performance rankings and learning metrics
**Shows:**
- Top performers with learning growth
- Sessions completed per AI
- Achievement badges (🚀🧠🔬 etc)
- Mastery ratings
- Performance metrics ranked

**Usage:**
```bash
./leaderboard.sh
```

**When to use:**
- Evaluating AI learning curves
- Identifying high performers
- Tracking individual AI progress over time
- Understanding team learning velocity

---

### 4. FULL STATUS (`status.sh`)

**For:** Complete system health check
**Shows:**
- Git status (clean/dirty)
- Database status
- Session statistics
- Goal statistics
- Artifact inventory
- Full system inventory

**Usage:**
```bash
./status.sh
```

**When to use:**
- Troubleshooting system issues
- Full health audit
- Understanding all system components
- Verifying data integrity

---

### 5. GIT HISTORY (Native Git)

**For:** See epistemic data in commits
**Shows:**
- Learning deltas in commit trailers
- AI identity per commit
- Epistemic measurements per commit
- Complete audit trail

**Usage:**
```bash
# Show trailers (epistemic data) in last 5 commits
git log --format=%(trailers) -5

# Show commits by learning delta
git log --all --pretty=format:"%h %s | %(trailers:key=Epistemic-Learning-Delta)" | head -20

# Filter to high-learning commits
git log --all --pretty=format:"%h | %(trailers:key=Epistemic-Learning-Delta)" | grep -E "\+0\.[1-9]|+[1-9]"
```

**When to use:**
- Understanding what was learned during a session
- Tracing work to epistemic state
- Auditing decisions
- Analyzing learning curves in git history

---

## Understanding the Data

### Session Mapping
```
Session UUID (1 per task)
    ├─ PREFLIGHT (baseline epistemic state)
    ├─ CHECK cycles (investigation rounds)
    ├─ ACT (do the work)
    └─ POSTFLIGHT (measure learning)
        └─ Learning Delta = POSTFLIGHT - PREFLIGHT
```

### Priority Levels
- **Critical (🔴):** Blocking other work, must do first
- **High (🟠):** Important but not blocking
- **Medium (🟡):** Nice to have
- **Low:** Background, when time available

### Learning Status Indicators
- **🚀 Fast:** Learning > 0.15 points
- **⚡ Learning:** Learning > 0.05 points
- **⏸️ Slow:** Learning ≤ 0.05 points

### Epistemic Vectors (What Gets Measured)
Each session measures 13 dimensions:
1. **ENGAGEMENT** - Focus/motivation
2. **KNOW** - Domain knowledge
3. **DO** - Can execute
4. **CONTEXT** - Understand situation
5. **CLARITY** - Understand requirements
6. **COHERENCE** - Things make sense
7. **SIGNAL** - Extract useful info
8. **DENSITY** - Handle complexity
9. **STATE** - Current state understanding
10. **CHANGE** - Manage changes
11. **COMPLETION** - Finish confidence
12. **IMPACT** - Understand effects
13. **UNCERTAINTY** - Explicit doubt (lower=better)

---

## Common Workflows

### "I'm joining fresh, what should I do?"
1. Run: `./empirica-coled.sh`
2. Identify critical/high priority work
3. Check which AIs are working on what
4. See learning status
5. For details: `./empirica-goals-dashboard.sh`

### "I want to assign new work"
1. Run: `./empirica-goals-dashboard.sh`
2. See what's already in progress
3. Check subtasks by importance
4. See investigation status
5. Assign to AI with capacity

### "What's the team learning?"
1. Run: `./leaderboard.sh`
2. See learning deltas per AI
3. Identify fast/slow learners
4. For detail: `git log --format=%(trailers)`

### "Something seems wrong"
1. Run: `./status.sh` (full health check)
2. Check git log for recent changes
3. Verify database is accessible
4. Check for data integrity issues

### "Need to trace work to commits"
1. Note the session_id from goals/subtasks
2. Run: `git log --all --grep="session_id"` to find commits
3. View epistemic data: `git log --format=%(trailers) <commit>`
4. See full details in git notes

---

## File Organization

### Executable Dashboards
Located in: `scripts/dashboards/`

```
scripts/dashboards/
├── empirica-coled.sh (main co-lead view)
├── empirica-goals-dashboard.sh (detailed goals)
├── leaderboard.sh (performance rankings)
├── status.sh (full system health)
├── test-commit-hook.sh (validation)
└── empirica-git-stats.sh (git analytics)
```

### Documentation
Main reference: `docs/DASHBOARDS.md` (this file)
Technical details: See `empirica-dev/` folder

---

## Key Principles

1. **Co-Lead Dashboard First:** Always start with `empirica-coled.sh` when you need a quick overview
2. **Drill Down as Needed:** Use other dashboards only when you need specific details
3. **Everything is Traceable:** Every goal → session → commits → git history
4. **Learning is Measurable:** Every decision shows what was learned in epistemic deltas
5. **Unified Storage:** SQLite (queryable) + Git (auditable) + JSON (full detail)

---

## Advanced Usage

### Analyze Team Learning
```bash
# Total team learning
git log --all --pretty=format:"%(trailers:key=Epistemic-Learning-Delta)" \
  | grep -oE '[+-][0-9.]+' | awk '{sum+=$1} END {print "Total learning:", sum}'

# Learning per AI
for ai in claude-code claude-sonnet qwen-code; do
  echo -n "$ai: "
  git log --all --grep="Epistemic-AI: $ai" --pretty=format:"%(trailers:key=Epistemic-Learning-Delta)" \
    | grep -oE '[+-][0-9.]+' | awk '{sum+=$1} END {print sum}'
done
```

### Find High-Impact Commits
```bash
# Commits with significant learning (>0.20 delta)
git log --all --pretty=format:"%h %s | %(trailers:key=Epistemic-Learning-Delta)" \
  | grep -E "\+0\.[2-9]|+[1-9]"
```

### Dashboard Comparison
```bash
# Run all dashboards in sequence for complete picture
echo "=== CO-LEAD VIEW ===" && ./empirica-coled.sh
echo ""
echo "=== FULL GOALS ===" && ./empirica-goals-dashboard.sh
echo ""
echo "=== PERFORMANCE ===" && ./leaderboard.sh
```

---

## Troubleshooting

### Dashboard shows no data
- Check database exists: `ls -la .empirica/sessions/sessions.db`
- Check connectivity: `sqlite3 .empirica/sessions/sessions.db "SELECT COUNT(*) FROM sessions;"`
- Run status.sh for full diagnostic: `./status.sh`

### Git trailers not showing
- Check hook is installed: `ls -la .git/hooks/prepare-commit-msg`
- Check recent commits: `git log -1 --format=%(trailers)`
- If missing: commits made before hook was installed

### Learning deltas seem wrong
- Check PREFLIGHT was recorded: Check SQLite reflexes table
- Check POSTFLIGHT was recorded: Same table
- Run status.sh to verify data integrity

---

## Legend & Symbols

| Symbol | Meaning |
|--------|---------|
| 🚀 | Fast learning / High priority / Ready to act |
| ⚡ | Moderate learning / Active work |
| ⏸️ | Paused / Slow learning |
| 🔴 | Critical priority |
| 🟠 | High priority |
| 🟡 | Medium priority |
| ✅ | Complete / Healthy |
| ⚠️ | Warning / Attention needed |
| 🔗 | Linked to git |

---

**Last Updated:** 2025-12-06
**Status:** Active & Production Ready
**Maintained by:** Claude Code (Co-Lead)

### empirica.sh - Unified Overview Dashboard

**Purpose:** Single-pane view combining system health, active work, and decision guidance.

**What it shows:**
- Total sessions (completed and active)
- Goals being tracked
- Learning data (epistemic vectors)
- System health indicators
- Next steps recommendations

**When to use:**
- Quick system status check
- Onboarding overview
- Decision-making support

**Usage:**
```bash
./scripts/dashboards/empirica.sh
```

**Example output:**
```
════════════════════════════════════════════════════════════════
EMPIRICA UNIFIED DASHBOARD - YOUR SINGLE SOURCE OF TRUTH
════════════════════════════════════════════════════════════════

📊 Sessions:      222 total | 90 completed (41%) | 132 active
🎯 Goals:         48 tracked
📈 Learning Data: 205 epistemic vectors

System Health:
  ✓ 58 AIs showing measurable learning
  ⚠ Monitor 74 active AIs

Next Steps:
  • Run: ./status.sh for detailed system view
  • Run: ./leaderboard.sh for performance metrics
```

---

### empirica-tracking.sh - Comprehensive Tracking Dashboard

**Purpose:** Complete AI → Session → CASCADE → Goals → Subtasks tracking with findings and unknowns.

**What it shows:**
- Active AIs with session/goal counts
- Recent sessions with PREFLIGHT/POSTFLIGHT metrics
- Active goals with subtask progress percentages
- CHECK phases with findings, unknowns, and deadends
- Learning deltas (knowledge gain, uncertainty reduction)

**When to use:**
- Deep dive into specific AI's work
- Investigating what was discovered vs what remains unclear
- Tracking goal completion and subtask progress
- Understanding learning progression

**Usage:**
```bash
# View all active AIs
./scripts/dashboards/empirica-tracking.sh

# Filter by specific AI
./scripts/dashboards/empirica-tracking.sh claude
./scripts/dashboards/empirica-tracking.sh rovodev
```

**Example output:**
```
📊 ACTIVE AIs
┌─────────────────────────┬──────────┬───────┬──────────┬────────────┐
│          AI_ID          │ Sessions │ Goals │ Subtasks │ Preflights │
├─────────────────────────┼──────────┼───────┼──────────┼────────────┤
│ claude-code             │ 18       │ 2     │ 5        │ 5          │
│ rovodev-test            │ 1        │ 4     │ 2        │ 1          │
└─────────────────────────┴──────────┴───────┴──────────┴────────────┘

🔍 CHECK PHASES (Findings & Unknowns)
  AI: rovodev-test
  Session: 33c3d4cb... | CHECK Round 1
  ✅ Findings (3):
     • Fixed dashboard colors
     • Created tracking dashboard
     • Verified unified storage
  ❓ Unknowns (2):
     • Deadends tracking needs implementation
     • Need to test with more AIs
```

---

