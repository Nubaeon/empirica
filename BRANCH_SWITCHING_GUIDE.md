# Branch Switching Guide for Empirica

## The Problem

**Critical data files are lost when switching between branches** because they're in `.gitignore`:

- `.empirica_reflex_logs/` - Session history and CASCADE workflow logs (7.8MB)
- `.agent_memory.json` - Agent state information
- `~/.empirica/sessions.db` - Session database (932KB with 131+ sessions)
- `~/.empirica/credentials.yaml` - API keys and provider configurations

When you run `git checkout <branch>`, these files may be deleted or overwritten.

## The Solution

### 1. Use the Safe Branch Switch Script (Recommended)

```bash
./scripts/safe-branch-switch.sh <branch-name>
```

**What it does:**
- Backs up all ignored files before switching
- Switches to the target branch
- Restores the backed up files
- Saves backups to `~/.empirica_branch_backups/` with timestamps

**Example:**
```bash
# Switch from main to gh-pages safely
./scripts/safe-branch-switch.sh gh-pages

# Switch back to main safely
./scripts/safe-branch-switch.sh main
```

### 2. Manual Recovery (If Data Was Lost)

If you already switched branches and lost data:

**Check recent automatic backups:**
```bash
ls -lt ~/.empirica_branch_backups/
# Restore from most recent backup if available
```

**Restore from empirica-server:**
```bash
# Restore reflex logs (7.8MB of session history)
rsync -av empirica@192.168.1.66:empirica-server/empirica/.empirica_reflex_logs/ .empirica_reflex_logs/

# Restore sessions database
rsync -av empirica@192.168.1.66:empirica-dev/.empirica/sessions.db ~/.empirica/

# Restore credentials
rsync -av empirica@192.168.1.66:empirica_backup2/.empirica/credentials.yaml ~/.empirica/
```

**Verify restoration:**
```bash
# Check sessions database
sqlite3 ~/.empirica/sessions.db "SELECT COUNT(*) FROM sessions;"
# Should show: 131 (or more)

# Check reflex logs
ls -lh .empirica_reflex_logs/ | head
# Should show session directories

# Check credentials
cat ~/.empirica/credentials.yaml | head -5
# Should show YAML config with API keys
```

## Git Hook Warning

A `post-checkout` hook has been installed that will warn you when switching branches using regular `git checkout`. The warning reminds you to:

1. Use the safe branch switch script instead
2. Or manually backup your data before switching

## Why This Happens

These files are in `.gitignore` because:
- They contain sensitive data (API keys, session history)
- They're too large to commit to git efficiently
- They're environment-specific (different on each machine/container)

But `.gitignore` means git doesn't track them, so they can be lost during branch operations.

## Best Practices

1. **Always use `./scripts/safe-branch-switch.sh`** instead of `git checkout`
2. **Keep regular backups** on empirica-server (already set up)
3. **Verify data integrity** after any branch operation:
   ```bash
   sqlite3 ~/.empirica/sessions.db "SELECT COUNT(*) FROM sessions;"
   ls -lh .empirica_reflex_logs/ | wc -l
   ```
4. **Document any branch switches** in case recovery is needed

## Recovery Checklist

If you suspect data loss after a branch switch:

- [ ] Check `~/.empirica_branch_backups/` for recent automatic backups
- [ ] Verify sessions.db size: `du -sh ~/.empirica/sessions.db` (should be ~932KB)
- [ ] Count sessions: `sqlite3 ~/.empirica/sessions.db "SELECT COUNT(*) FROM sessions;"` (should be 131+)
- [ ] Check reflex logs exist: `ls -la .empirica_reflex_logs/` (should have 158+ directories)
- [ ] Verify credentials: `cat ~/.empirica/credentials.yaml | wc -l` (should be ~80 lines)
- [ ] If any missing, restore from empirica-server using rsync commands above

## Technical Details

**Backup locations:**
- Local automatic backups: `~/.empirica_branch_backups/`
- Remote backup server: `empirica@192.168.1.66`
  - `empirica-server/empirica/.empirica_reflex_logs/` - Most complete reflex logs
  - `empirica-dev/.empirica/sessions.db` - Most recent sessions database
  - `empirica_backup2/.empirica/` - Credentials and older backups

**Protected files in safe-branch-switch.sh:**
```bash
PRESERVE_ITEMS=(
    ".empirica_reflex_logs"
    ".agent_memory.json"
)
# Plus ~/.empirica/ directory (sessions.db, credentials.yaml)
```

---

**Last updated:** 2025-11-27
**Tested with:** Git 2.x, Empirica v1.0+
