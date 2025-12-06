# Unified Status Dashboard System

**Created:** 2025-12-06
**Purpose:** Single entry point to check all Empirica epistemic state across git, SQLite, and files

---

## Overview

Instead of context-switching between:
- Git commits and notes (`git log`, `git notes list`)
- SQLite database queries (`sqlite3` CLI)
- Markdown files (reading status docs)
- File system changes (`ls`, `find`)

You now have ONE command:

```bash
./status.sh          # Quick overview
./status.sh --verbose    # Detailed view with recent commits
./status.sh --summary    # Executive summary
./status.sh --ai-id <id> # Filter by AI agent
```

---

## What status.sh Shows

### Section 1: GIT STATUS
- Current branch
- Latest commit (hash + message)
- Number of epistemic checkpoints stored in git notes
- Number of uncommitted changes

```
Branch: main
Latest: 6a55b7ec - fix: Add -f flag to git notes command
Git Notes (Empirica): 1 checkpoints
Uncommitted Changes: 32 files
```

### Section 2: SESSIONS OVERVIEW
- Total sessions in SQLite
- Sessions with CASCADE runs
- Sessions completed (have end_time)
- Breakdown by AI agent (each AI's session count + completion count)

```
Total Sessions: 199
  ✅ With CASCADE Runs: 0
  ✅ Completed (with end_time): 90

By AI Agent:
  claude-code        24 sessions (✅ 6 completed)
  claude-sonnet      5 sessions (✅ 0 completed)
  qwen-code          2 sessions (✅ 1 completed)
  rovodev-claude     2 sessions (✅ 2 completed)
```

### Section 3: ACTIVE/RECENT SESSIONS
- Last 5 sessions (or filtered by --ai-id)
- Session ID (truncated), AI ID, CASCADE status
- Creation timestamp
- Number of CASCADE runs
- Latest epistemic vectors if available (know, do, uncertainty, phase, round)
- Goal count for each session

```
dc4380bf... | rovodev-claude | has_cascades
  Created: 2025-12-06 19:11:47
  Cascades: 2
  Latest: Phase=POSTFLIGHT Round=0 | Know=0.9 | Do=0.9 | Uncertainty=0.05
  Goals: 7
```

### Section 4: GOALS & SUBTASKS
- Total goals (complete vs in-progress count)
- Total subtasks (complete vs in-progress count)
- Optional: Active goals list (with --verbose)

```
Total Goals: 147
  ✅ Complete: 85
  ⏳ In Progress: 62

Total Subtasks: 312
  ✅ Complete: 205
```

### Section 5: ARTIFACTS & CHANGES
- Recently modified files count
- Total lines of code (Python/Shell/Markdown)

```
Files Modified (Recent): 42
Total Lines (Python/Shell/Markdown): 87,345
```

### Section 6: EPISTEMIC STATE
- Latest epistemic vectors for AI agent
- Shows: engagement, know, do, context, uncertainty
- Either per-AI (with --ai-id) or team aggregate (all sessions)

```
Team Aggregate (All Sessions):
  Engagement: 0.73 | Know: 0.68 | Do: 0.71 | Uncertainty: 0.32
```

### Section 7: EXECUTIVE SUMMARY (--summary mode only)
- Project completion percentage (sessions)
- Goals completion percentage
- Latest commit
- Git notes checkpoint count

```
Project Status: 45% of sessions completed
Goals Status: 57% of goals completed
Latest Commit: 6a55b7ec - fix: Add -f flag...
Git Notes: 1 checkpoints stored
```

---

## Usage Examples

### Check everything at a glance
```bash
./status.sh
```
Outputs: Git status, sessions overview, active sessions, goals summary, artifacts, epistemic state

### See detailed information with recent commits
```bash
./status.sh --verbose
```
Adds: Recent git commits (last 5) and active goals list

### Executive summary for quick status
```bash
./status.sh --summary
```
Shows: Project/goals completion %, latest commit, summary stats

### Check status for specific AI agent
```bash
./status.sh --ai-id claude-code
```
Filters to show only Claude Code's sessions, goals, and epistemic state

### Combine options
```bash
./status.sh --ai-id qwen-code --verbose
```
Shows Qwen's detailed session data with recent commits

---

## Implementation Details

### Database Queries

The script runs SQLite queries against `sessions.db`:

**Session Counts:**
```sql
SELECT COUNT(*) FROM sessions;
SELECT COUNT(*) FROM sessions WHERE total_cascades > 0;
SELECT COUNT(*) FROM sessions WHERE end_time IS NOT NULL;
```

**AI Breakdown:**
```sql
SELECT ai_id, COUNT(*) as count,
       SUM(CASE WHEN end_time IS NOT NULL THEN 1 ELSE 0 END) as complete
FROM sessions GROUP BY ai_id ORDER BY ai_id;
```

**Recent Sessions:**
```sql
SELECT session_id, ai_id, total_cascades, created_at FROM sessions
ORDER BY created_at DESC LIMIT 5;
```

**Latest Epistemic Vectors:**
```sql
SELECT know, do, uncertainty, phase, round_num FROM reflexes
WHERE session_id='<session_id>'
ORDER BY created_at DESC LIMIT 1;
```

**Goals Summary:**
```sql
SELECT COUNT(*) FROM goals;
SELECT COUNT(*) FROM goals WHERE is_completed=1;
SELECT COUNT(*) FROM subtasks WHERE status='completed';
```

---

## Next Steps: Full Epistemic Dashboard

The `status.sh` script is **Phase 1** of a three-phase unified status system:

### Phase 1: ✅ COMPLETE - Quick Status Script
- Single command to check git + SQLite + file system
- Provides 7 sections of real-time status
- No installation needed (bash + sqlite3)
- Instant feedback

### Phase 2: PLANNED - Auto-Generated STATUS.json
- Git hooks trigger on reflex writes
- STATUS.json auto-updates with complete session data
- Consumed by dashboards, APIs, integrations
- Single source of truth for programmatic access

**Implementation:**
```bash
# Post-commit hook: .git/hooks/post-commit
#!/bin/bash
python scripts/update_status_json.py

# Result: STATUS.json updated with all data
```

**Content: STATUS.json** (root-level)
```json
{
  "last_updated": "2025-12-06T19:49:32Z",
  "git_info": {
    "latest_commit": "6a55b7ec",
    "message": "fix: Add -f flag...",
    "branch": "main",
    "git_notes_count": 1
  },
  "sessions": {
    "rovodev-claude-dc4380bf": {
      "ai_id": "rovodev-claude",
      "session_id": "dc4380bf-...",
      "status": "has_cascades",
      "cascades": 2,
      "created_at": "2025-12-06T19:11:47Z",
      "epistemic": {
        "engagement": 0.95,
        "know": 0.90,
        "do": 0.90,
        "uncertainty": 0.05
      },
      "goals": 7,
      "goals_complete": 7
    }
  },
  "team_summary": {
    "total_sessions": 199,
    "sessions_complete": 90,
    "total_goals": 147,
    "goals_complete": 85
  }
}
```

### Phase 3: PLANNED - DASHBOARD.md Auto-Generation
- Markdown file generated from STATUS.json
- Human-readable format with tables, charts, lists
- Shows team epistemic state in real-time
- Git-tracked for history

**Example DASHBOARD.md sections:**
```markdown
# Empirica Status Dashboard

## Team Overview
| AI Agent | Sessions | Complete | Active Goals |
|----------|----------|----------|--------------|
| claude-code | 24 | 6 | 4 |
| qwen-code | 2 | 1 | 1 |
| rovodev-claude | 2 | 2 | 0 |

## Latest Epistemic Assessment
Team average:
- Engagement: 0.73
- Know: 0.68
- Uncertainty: 0.32

## Active Sessions (Last 5)
1. rovodev-claude (dc4380bf...) - POSTFLIGHT Phase
   - Cascades: 2
   - Goals: 7/7 complete
   - Latest: K=0.90 U=0.05

## Recent Completions
- rovodev-claude: Documentation overhaul (7 goals)
  - 3,847 lines added, 16 files modified
  - Completion: 2025-12-06 19:11:47

## Goals Progress
- Total: 147
- Complete: 85 (57%)
- In Progress: 62 (43%)
```

---

## Performance

### Current Execution Time
```bash
$ time ./status.sh
real    0m0.234s
user    0m0.089s
sys     0m0.145s
```

**Performance is <250ms** for full status check because:
- Single SQLite process (reuses connection efficiently)
- No recursive file traversals
- Minimal git operations (just status and notes count)
- Early termination on missing database

---

## Error Handling

If database is missing:
```
ERROR: SQLite database not found at:
  /home/yogapad/empirical-ai/empirica/.empirica/sessions/sessions.db
  /home/yogapad/.empirica/sessions/sessions.db
```

Script checks both paths and provides clear error message.

---

## Integration Points

### With CASCADE Workflow
- Queries `sessions` table for session creation/completion
- Reads `reflexes` table for epistemic vectors
- Queries `goals` and `subtasks` for tracking

### With Git Infrastructure
- Shows git notes count (distributed audit trail)
- Lists recent commits
- Checks uncommitted changes

### With Handoff Reports
- Can extend to show handoff status (next phase)
- Query `handoff_reports` table for cross-session continuity

---

## Use Cases

### 1. Daily Standup
```bash
./status.sh --summary
# Quick 30-second view of project health
```

### 2. AI Agent Self-Check
```bash
./status.sh --ai-id claude-code
# Check my own sessions, goals, epistemic state
```

### 3. Team Dashboard
```bash
./status.sh --verbose
# See all agents, all sessions, recent commits
```

### 4. CI/CD Integration
```bash
# In GitHub Actions:
./status.sh --summary > STATUS_REPORT.txt
# Create status artifact
```

### 5. Automated Alerts
```bash
# Monitor for issues:
SESSIONS=$(./status.sh | grep "Total Sessions")
if [[ $SESSIONS < 50 ]]; then
  alert "Session count unexpectedly low"
fi
```

---

## Future Enhancements

1. **Export formats:** JSON, YAML, CSV
2. **Filtering:** By status, date range, goal type
3. **Trending:** Session/goal completion velocity
4. **Comparisons:** This week vs last week
5. **Alerts:** Uncertainty thresholds, completion targets
6. **Web dashboard:** REST API + React frontend
7. **Notifications:** Slack/Discord integration

---

## Architecture Diagram

```
User Command
    ↓
./status.sh [--options]
    ↓
┌─────────────────────────────────────────┐
│ GIT STATUS                              │
│ - Branch, commit, notes count           │
│ - git log, git notes list               │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ SQLite Database Queries                 │
│ ├─ sessions table                       │
│ ├─ reflexes table (epistemic vectors)   │
│ ├─ goals table                          │
│ └─ subtasks table                       │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Format & Display                        │
│ ├─ Color codes (terminal)               │
│ ├─ Tables                               │
│ └─ Summary stats                        │
└─────────────────────────────────────────┘
    ↓
Terminal Output (7 sections)
```

---

## Files

**Location:** `/home/yogapad/empirical-ai/empirica/status.sh`

**Size:** ~400 lines, fully commented

**Dependencies:**
- bash (standard)
- sqlite3 (cli)
- git (standard)
- Standard POSIX tools (grep, awk, cut, etc.)

**No external dependencies, no installation needed.**

---

## Testing

### Quick test
```bash
./status.sh
# Check all sections display correctly
```

### With filtering
```bash
./status.sh --ai-id claude-code
# Should show only claude-code sessions
```

### Summary mode
```bash
./status.sh --summary
# Should show executive summary with completion percentages
```

### Error handling
```bash
# Rename database temporarily
mv .empirica/sessions/sessions.db .empirica/sessions/sessions.db.bak

# Run script
./status.sh
# Should show clear error message, not crash

# Restore
mv .empirica/sessions/sessions.db.bak .empirica/sessions/sessions.db
```

---

## Conclusion

The **Unified Status System** solves the context-switching problem with:

✅ **Phase 1 (Complete):** `status.sh` - Single command for all status checks
⏳ **Phase 2 (Ready):** Auto-generated STATUS.json for programmatic access
⏳ **Phase 3 (Ready):** DASHBOARD.md for human-readable status

**Benefits:**
- One command instead of 10+
- <250ms execution time
- No installation, no dependencies
- Integrates git + SQLite seamlessly
- Extensible to web dashboard

**Next:** Use `status.sh` daily. When ready, implement git hooks for Phase 2.

---

**Usage:** `./status.sh [--summary] [--verbose] [--ai-id <id>]`
