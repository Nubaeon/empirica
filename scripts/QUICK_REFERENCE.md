# Quick Reference: Safe Branch Switching

## ⚠️ NEVER use `git checkout` directly!

## ✅ ALWAYS use the safe script:

```bash
./scripts/safe-branch-switch.sh <branch-name>
```

## Examples:

```bash
# Switch to gh-pages
./scripts/safe-branch-switch.sh gh-pages

# Switch back to main
./scripts/safe-branch-switch.sh main

# Switch to a feature branch
./scripts/safe-branch-switch.sh feature/new-epistemic-vectors
```

## What gets protected:

- ✅ `.empirica/` (project-local sessions, goals, findings - PRIMARY storage)
- ✅ `~/.empirica/` (global hub: credentials, cross-project data - FALLBACK)
- ✅ `.empirica_reflex_logs/` (legacy session history)
- ✅ `.agent_memory.json` (agent state)

**Note:** Modern Empirica uses project-local `.empirica/sessions/sessions.db` as primary.
Global `~/.empirica/` is used for credentials and as fallback when no local dir exists.

## If you accidentally lost data:

1. **Check automatic backups:**
   ```bash
   ls -lt ~/.empirica_branch_backups/
   ```

2. **Restore from empirica-server:**
   ```bash
   # Reflex logs
   rsync -av empirica@192.168.1.66:empirica-server/empirica/.empirica_reflex_logs/ .empirica_reflex_logs/

   # Sessions DB
   rsync -av empirica@192.168.1.66:empirica-dev/.empirica/sessions.db ~/.empirica/

   # Credentials
   rsync -av empirica@192.168.1.66:empirica_backup2/.empirica/credentials.yaml ~/.empirica/
   ```

3. **Verify restoration:**
   ```bash
   # Check project-local (primary)
   sqlite3 .empirica/sessions/sessions.db "SELECT COUNT(*) FROM sessions;"
   # Or global fallback
   sqlite3 ~/.empirica/sessions/sessions.db "SELECT COUNT(*) FROM sessions;"
   ```

## See full guide:
```bash
cat BRANCH_SWITCHING_GUIDE.md
```
