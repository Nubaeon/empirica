# Troubleshooting Guide

**Common issues and solutions for Empirica**

---

## Installation Issues

### Problem: Command not found
```bash
empirica: command not found
```

**Cause:** Pip binaries not in PATH

**Solution:**
```bash
# Find pip install location
pip show empirica | grep Location

# Add to PATH (bash)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Add to PATH (zsh)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Problem: Module not found
```python
ModuleNotFoundError: No module named 'empirica'
```

**Cause:** Wrong Python environment or installation failed

**Solution:**
```bash
# Check Python version (3.8+ required)
python --version

# Verify installation
pip show empirica

# Reinstall if needed
pip uninstall empirica
pip install empirica
```

---

## Database Issues

### Problem: Database locked
```
sqlite3.OperationalError: database is locked
```

**Cause:** Multiple processes accessing database simultaneously

**Solution:**
```bash
# Check for running Empirica processes
ps aux | grep empirica

# Kill if necessary
pkill -f empirica

# Restart command
```

### Problem: Cannot open database
```
sqlite3.OperationalError: unable to open database file
```

**Cause:** Permission issues or missing directory

**Solution:**
```bash
# Create directory with correct permissions
mkdir -p ~/.empirica
chmod 755 ~/.empirica

# Check ownership
ls -la ~/.empirica

# Fix if needed
chown -R $USER:$USER ~/.empirica
```

### Problem: Database corrupted
```
sqlite3.DatabaseError: database disk image is malformed
```

**Cause:** Unexpected shutdown or disk issues

**Solution:**
```bash
# Backup current database
cp ~/.empirica/empirica.db ~/.empirica/empirica.db.backup

# Try to recover
sqlite3 ~/.empirica/empirica.db "PRAGMA integrity_check;"

# If unrecoverable, start fresh (loses history)
rm ~/.empirica/empirica.db

# Create new database
empirica session-create --ai-id recovery
```

---

## Session Issues

### Problem: Session not found
```
Error: Session with ID 'xyz' not found
```

**Cause:** Invalid session ID or database issue

**Solution:**
```bash
# List all sessions
empirica sessions-list

# Verify session ID is correct
# If session missing, check database:
sqlite3 ~/.empirica/empirica.db "SELECT * FROM sessions;"
```

### Problem: Cannot create session
```
Error: Failed to create session
```

**Cause:** Database write permission or disk space issue

**Solution:**
```bash
# Check disk space
df -h ~/.empirica

# Check database permissions
ls -la ~/.empirica/empirica.db

# Fix permissions
chmod 644 ~/.empirica/empirica.db

# Check if directory is writable
touch ~/.empirica/test && rm ~/.empirica/test
```

---

## Git Integration Issues

### Problem: Git notes not working
```
fatal: refs/empirica/checkpoints does not exist
```

**Cause:** Git notes namespace not initialized

**Solution:**
```bash
# Create first checkpoint to initialize
empirica checkpoint-create --session-id <SESSION_ID>

# Or manually initialize
git notes --ref=empirica/checkpoints add -m "init" HEAD
```

### Problem: Cannot push checkpoints
```
error: cannot update ref 'refs/notes/empirica/checkpoints'
```

**Cause:** Git repository not configured or no commits

**Solution:**
```bash
# Ensure you're in a git repository
git status

# Make initial commit if needed
git commit --allow-empty -m "Initial commit"

# Create checkpoint
empirica checkpoint-create --session-id <SESSION_ID>
```

### Problem: Git identity not configured
```
fatal: unable to auto-detect email address
```

**Cause:** Git user not configured

**Solution:**
```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

---

## Assessment Issues

### Problem: PREFLIGHT prompt not showing
```
Error: Could not generate PREFLIGHT prompt
```

**Cause:** Missing session data or template issue

**Solution:**
```bash
# Verify session exists
empirica sessions-show --session-id <SESSION_ID>

# Try with verbose output
empirica --verbose preflight --session-id <SESSION_ID>

# Check for core module issues
python -c "from empirica.core.canonical import CanonicalEpistemicAssessor; print('OK')"
```

### Problem: Invalid vector values
```
Error: Vector 'know' must be between 0.0 and 1.0
```

**Cause:** Incorrect value format in JSON input

**Solution:**
```json
{
  "vectors": {
    "engagement": 0.8,
    "foundation": {
      "know": 0.7,    // Must be 0.0-1.0
      "do": 0.6,
      "context": 0.5
    }
  }
}
```

---

## Project Issues

### Problem: Project not found
```
Error: Project with ID 'xyz' not found
```

**Cause:** Invalid project ID or not in git repository

**Solution:**
```bash
# List all projects
empirica project-list

# Create new project if needed
empirica project-create --name "My Project"

# Project auto-detection requires git
git remote -v  # Check git remotes
```

### Problem: Project bootstrap shows nothing
```
Warning: No breadcrumbs found for project
```

**Cause:** No findings/unknowns logged yet

**Solution:**
```bash
# Log some findings
empirica finding-log --project-id <PROJECT_ID> \
    --finding "Initial exploration complete"

# Bootstrap again
empirica project-bootstrap --project-id <PROJECT_ID>
```

---

## Goal Issues

### Problem: Cannot create goal
```
Error: Failed to create goal
```

**Cause:** Missing required fields or session issue

**Solution:**
```bash
# Verify session exists
empirica sessions-show --session-id <SESSION_ID>

# Use JSON mode for clarity
cat > goal.json << EOF
{
  "session_id": "<SESSION_ID>",
  "objective": "Clear objective description",
  "scope": {
    "breadth": 0.5,
    "duration": 0.5,
    "coordination": 0.3
  }
}
EOF

echo "$(cat goal.json)" | empirica goals-create -
```

### Problem: Subtask not completing
```
Error: Cannot complete subtask
```

**Cause:** Invalid task ID or dependency issues

**Solution:**
```bash
# List all subtasks for goal
empirica goals-get-subtasks --goal-id <GOAL_ID>

# Verify task ID is correct
# Check dependencies are completed first
```

---

## BEADS Integration Issues

### Problem: Cannot discover goals
```
Error: No goals found
```

**Cause:** No goals published to git notes or wrong remote

**Solution:**
```bash
# Check git notes
git notes --ref=empirica/goals list

# Fetch from remote
git fetch origin refs/notes/empirica/goals:refs/notes/empirica/goals

# Try discovery again
empirica goals-discover
```

### Problem: Cannot claim goal
```
Error: Goal already claimed
```

**Cause:** Another agent already claimed this goal

**Solution:**
```bash
# Check goal status
empirica goals-list

# Find unclaimed goals
empirica goals-ready

# Or resume an existing goal
empirica goals-resume --goal-id <GOAL_ID> --ai-id myai
```

---

## Performance Issues

### Problem: Commands are slow
```
(Taking >10 seconds to respond)
```

**Cause:** Database size or git repository size

**Solution:**
```bash
# Check database size
ls -lh ~/.empirica/empirica.db

# Vacuum database to optimize
sqlite3 ~/.empirica/empirica.db "VACUUM;"

# Clean old sessions (optional)
empirica sessions-list --output json | \
    jq -r '.sessions[] | select(.last_activity < "2024-01-01") | .id' | \
    xargs -I {} empirica sessions-delete --session-id {}
```

---

## Output Issues

### Problem: JSON output malformed
```
Error parsing JSON response
```

**Cause:** Mixed stdout/stderr or encoding issue

**Solution:**
```bash
# Redirect stderr
empirica sessions-list --output json 2>/dev/null

# Use jq for validation
empirica sessions-list --output json | jq .

# Check for binary output issues
empirica sessions-list --output json | cat -v
```

---

## Getting More Help

### Enable Verbose Mode
```bash
empirica --verbose <command>
```

### Check Logs
```bash
# View session logs (if logging enabled)
ls -la ~/.empirica/sessions/

# Check system logs
journalctl | grep empirica  # Linux systemd
tail -f /var/log/syslog     # Linux syslog
```

### Diagnostic Information
```bash
# Gather debug info
echo "Empirica version:"
pip show empirica | grep Version

echo "Python version:"
python --version

echo "Git version:"
git --version

echo "Database info:"
ls -lh ~/.empirica/empirica.db

echo "Session count:"
empirica sessions-list --output json | jq '.sessions_count'

echo "Project count:"
empirica project-list --output json | jq '.projects_count'
```

### Reset Everything (Last Resort)
```bash
# Backup first!
tar -czf empirica-backup-$(date +%Y%m%d).tar.gz ~/.empirica/

# Remove all data
rm -rf ~/.empirica/

# Remove project data
rm -rf .empirica/

# Reinstall
pip uninstall empirica
pip install empirica

# Start fresh
empirica session-create --ai-id myai
```

---

## Still Having Issues?

1. **Check documentation:** Browse other docs in `docs/` directory
2. **Verify ground truth:** See [reference/CANONICAL_DIRECTORY_STRUCTURE.md](reference/CANONICAL_DIRECTORY_STRUCTURE.md)
3. **Check the code:** Empirica is open source - look at the implementation
4. **Ask specific questions:** Use `empirica ask "your question"` (if implemented)

---

## Common Gotchas

### 1. Session IDs are UUIDs
```bash
# Wrong: Using short IDs
empirica sessions-show --session-id abc

# Right: Full UUID
empirica sessions-show --session-id abc123-456-789-...
```

### 2. JSON stdin needs trailing dash
```bash
# Wrong:
echo '{"ai_id": "myai"}' | empirica session-create

# Right:
echo '{"ai_id": "myai"}' | empirica session-create -
```

### 3. Git integration requires commits
```bash
# Checkpoints won't work in empty repo
# Make at least one commit first
git commit --allow-empty -m "Initial commit"
```

### 4. Project auto-detection uses git remote
```bash
# Ensure git remote is set
git remote -v

# If no remote, project won't auto-detect
git remote add origin <URL>
```

### 5. Vectors must be 0.0-1.0
```bash
# All epistemic vectors are normalized to [0.0, 1.0]
# 0.0 = none/minimal
# 1.0 = complete/maximum
```

---

**Most issues are:** database permissions, git configuration, or malformed input. Check those first!
