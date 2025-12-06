# Status Dashboard - Quick Reference

**Location:** `/home/yogapad/empirical-ai/empirica/status.sh`

**Created:** 2025-12-06

---

## One Command to Check Everything

```bash
./status.sh
```

This replaces:
```bash
# ❌ OLD (10+ commands)
git log --oneline -n 5
git notes --ref=refs/notes/empirica/checkpoints list | wc -l
sqlite3 .empirica/sessions/sessions.db "SELECT COUNT(*) FROM sessions;"
sqlite3 .empirica/sessions/sessions.db "SELECT * FROM reflexes LIMIT 1;"
grep "complete" DOCS_OVERHAUL_COMPLETE.md
ls -la docs/
# ... and more

# ✅ NEW (1 command)
./status.sh
```

---

## Quick Commands

| Goal | Command | Output |
|------|---------|--------|
| **Quick overview** | `./status.sh` | All 7 status sections |
| **Detailed view** | `./status.sh --verbose` | + recent commits + active goals |
| **Executive summary** | `./status.sh --summary` | Completion %, metrics only |
| **Your sessions** | `./status.sh --ai-id claude-code` | Filter to your AI agent |
| **Another AI's work** | `./status.sh --ai-id qwen-code` | Filter to Qwen's sessions |
| **Help** | `./status.sh --help` | Show usage options |

---

## What You See

### Section 1: GIT STATUS (30 seconds)
- Current branch
- Latest commit
- Git notes count (distributed audit trail)
- Uncommitted changes

### Section 2: SESSIONS OVERVIEW
- Total sessions
- Sessions with CASCADE runs
- Completed sessions
- Breakdown by AI agent

### Section 3: ACTIVE/RECENT SESSIONS
- Last 5 sessions
- Session ID, AI ID, status
- Epistemic vectors (if available)
- Goal count

### Section 4: GOALS & SUBTASKS
- Total goals (complete/in-progress)
- Total subtasks (complete/in-progress)

### Section 5: ARTIFACTS & CHANGES
- Recently modified files
- Total lines of code

### Section 6: EPISTEMIC STATE
- Latest epistemic vectors
- Engagement, know, do, uncertainty
- Team aggregate or per-AI

### Section 7: SUMMARY (--summary only)
- Project completion %
- Goals completion %
- Latest commit
- Git notes count

---

## Real-World Examples

### Before standup (30 seconds)
```bash
./status.sh --summary
```

### Check your work
```bash
./status.sh --ai-id claude-code
```

### Check team progress
```bash
./status.sh --verbose
```

### Monitor during session
```bash
# Run every 5 minutes
watch -n 5 './status.sh'
```

### Create status report
```bash
./status.sh > STATUS_REPORT.txt
# Include in commit message, email, or Slack
```

---

## Performance

**Execution time:** <250ms (typically 0.2 seconds)

This makes it fast enough to:
- Run as pre-commit hook
- Check in shell prompt
- Monitor continuously
- Embed in CI/CD

---

## Database Location

The script automatically finds the database at:
1. `.empirica/sessions/sessions.db` (repo root)
2. `~/.empirica/sessions/sessions.db` (home directory)
3. Falls back to error if not found

---

## Color Coding

- 🔵 **BLUE** - Section headers
- 🟢 **GREEN** - Session IDs, positive indicators
- 🟡 **YELLOW** - Labels, secondary info
- 🔴 **RED** - Errors, if any
- 🟦 **CYAN** - Dividers, structure

---

## Common Uses

### Daily Standup
```bash
./status.sh --summary
# 30 seconds to report status
```

### Code Review
```bash
./status.sh --verbose
# See all changes, commits, goals
```

### Debugging Issues
```bash
./status.sh --ai-id <problem-ai>
# Focus on one AI's sessions
```

### CI/CD Check
```bash
if ./status.sh | grep -q "Total Sessions: 0"; then
  echo "ERROR: No sessions found"
  exit 1
fi
```

### Monitor Real-Time
```bash
watch './status.sh'
# Auto-refresh every 2 seconds
```

---

## Troubleshooting

### "Permission denied" error
```bash
chmod +x ./status.sh
```

### "Database not found" error
```bash
# Ensure database exists at one of:
# 1. .empirica/sessions/sessions.db
# 2. ~/.empirica/sessions/sessions.db

# Or set database path:
DB_PATH=/custom/path ./status.sh
```

### No output
```bash
# Redirect stderr to see what's happening
./status.sh 2>&1 | head -20
```

### "sqlite3: command not found"
```bash
# Install sqlite3
# Ubuntu: sudo apt install sqlite3
# macOS: brew install sqlite3
# Already installed on most systems
```

---

## Next Phase: Full Dashboard

This script is Phase 1. Future phases:

**Phase 2:** Auto-generated `STATUS.json`
- Git hooks trigger on writes
- Single source of truth
- For programmatic access

**Phase 3:** Auto-generated `DASHBOARD.md`
- Human-readable markdown
- Real-time team status
- Tracked in git history

---

## Files

| File | Purpose |
|------|---------|
| `status.sh` | Main script (this section) |
| `UNIFIED_STATUS_SYSTEM.md` | Full documentation |
| `STATUS_QUICK_REFERENCE.md` | This file |

---

**Usage:** `./status.sh [--summary] [--verbose] [--ai-id <id>]`

**Time to learn:** 2 minutes
**Time to use:** <1 second
**Value:** Massive (context switching eliminated)
