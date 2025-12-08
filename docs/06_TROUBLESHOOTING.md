# Troubleshooting Guide

Common issues and solutions for Empirica.

---

## Installation Issues

### `command not found: empirica`

**Symptoms:** Running `empirica` shows "command not found"

**Cause:** Installation directory not in PATH

**Solutions:**
```bash
# Option 1: Add to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Option 2: Use python module
python3 -m empirica.cli --help

# Option 3: Reinstall
pip install -e . --user
```

### Import errors: `ModuleNotFoundError`

**Symptoms:** `ImportError: No module named 'empirica'`

**Cause:** Package not installed or wrong Python environment

**Solutions:**
```bash
# Check installation
pip list | grep empirica

# Reinstall
cd /path/to/empirica
pip install -e .

# Or use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Permission denied errors

**Symptoms:** Cannot write to `.empirica/` directory

**Solutions:**
```bash
# Fix permissions
chmod -R u+rw ~/.empirica

# Or reinstall for user
pip install -e . --user
```

---

## CLI Issues

### Commands return "No such command"

**Symptoms:** `empirica preflight` shows "Error: No such command"

**Cause:** Old installation or corrupted files

**Solutions:**
```bash
# Reinstall fresh
pip uninstall empirica
pip install -e . --force-reinstall

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
```

### Preflight/postflight hang or timeout

**Symptoms:** Commands never complete, just hang

**Cause:** Waiting for user input in interactive mode

**Solutions:**
```bash
# For scripts, use MCP integration for automated assessment
# Interactive CLI requires manual self-assessment input
empirica preflight "task"  # Shows prompt, waits for assessment

# Or provide assessment JSON
empirica preflight "task" --assessment-json '{...}'

# Or use MCP server for automated workflows
```

### "Assessment failed" errors

**Symptoms:** `❌ Assessment failed` message

**Cause:** Invalid JSON input or missing assessment

**Solutions:**
```bash
# Check JSON syntax
echo '{...}' | jq .  # Validate JSON

# Use interactive mode to see prompt
empirica preflight "task"  # Interactive mode - default

# Or skip to see what's expected
empirica preflight "task" --help
```

---

## MCP Server Issues

### MCP tools not appearing in IDE

**Symptoms:** AI assistant doesn't see Empirica tools

**Check 1: Verify configuration**
```bash
# Find config file location
# Claude Desktop:
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Verify Python path
which python3

# Test server manually
python3 /path/to/empirica/mcp_local/empirica_mcp_server.py --help
```

**Check 2: Restart IDE**
- Close IDE completely
- Restart to reload MCP configuration

**Check 3: Check IDE logs**
- Look for MCP connection errors
- Verify paths are correct
- Check Python is accessible

### MCP server won't start

**Note:** MCP server lifecycle is managed automatically by your IDE (Claude Desktop, Cursor, etc.). There are no CLI commands for starting/stopping the MCP server.

**If MCP tools aren't working:**

1. **Check IDE MCP configuration:**
   - Claude Desktop: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
   - Cursor: Check IDE settings for MCP servers

2. **View server logs:**
   ```bash
   # Check IDE-specific log location
   # Claude Desktop logs: ~/Library/Logs/Claude/
   # Cursor logs: Check IDE settings
   ```

3. **Restart IDE:**
   - Completely quit and reopen your IDE
   - MCP server will restart automatically

### Tools fail with errors

**Symptoms:** MCP tools execute but return errors

**Solutions:**
```bash
# Check database exists
ls ~/.empirica/sessions/sessions.db

# Create if missing
empirica session-create

# Check permissions
chmod -R u+rw ~/.empirica

# View server logs
tail -f ~/.empirica/mcp_server.log
```

---

## Database Issues

### "Database locked" errors

**Symptoms:** `sqlite3.OperationalError: database is locked`

**Cause:** Multiple processes accessing database

**Solutions:**
```bash
# Check for running CLI processes
ps aux | grep empirica

# Restart your IDE (MCP server managed by IDE)
# The IDE will restart the MCP server automatically

# Wait a moment and retry
sleep 2
empirica preflight "task"
```

### Session not found

**Symptoms:** `Session <id> not found` when running postflight

**Cause:** Session ID incorrect or preflight wasn't saved

**Solutions:**
```bash
# List all sessions
empirica sessions-list

# Check session ID
echo $SESSION  # If using variable

# Verify database
sqlite3 ~/.empirica/sessions/sessions.db "SELECT session_id FROM sessions;"
```

### Missing uncertainty vector

**Symptoms:** Old sessions missing uncertainty data

**Cause:** Upgrading from pre-uncertainty version

**Solution:**
```bash
# Run migration
empirica migrate

# Or recreate database
mv ~/.empirica/sessions/sessions.db ~/.empirica/sessions/sessions.db.backup
empirica session-create
```

---

## MCP Parameter Errors

### `create_goal` parameter errors

**Common Issues:**
- `scope` parameter errors (not enum value)
- `success_criteria` type errors (string instead of array)

**Solutions:**
```python
# ❌ WRONG
create_goal(scope="any text")  # Must be enum!
create_goal(success_criteria="Tests pass")  # Must be array!

# ✅ CORRECT  
create_goal(scope="project_wide")  # enum: task_specific|session_scoped|project_wide
create_goal(success_criteria=["Tests pass", "Docs updated"])  # Array
```

### `add_subtask` parameter errors

**Common Issues:**
- Using `epistemic_importance` instead of `importance`
- Wrong parameter types

**Solutions:**
```python
# ❌ WRONG
add_subtask(epistemic_importance="high")  # Wrong parameter name!

# ✅ CORRECT
add_subtask(
    goal_id="uuid",
    description="Write unit tests", 
    importance="high",  # Correct parameter
    estimated_tokens=500
)
```

### `complete_subtask` parameter errors

**Common Issues:**
- Using `subtask_id` instead of `task_id`

**Solutions:**
```python
# ❌ WRONG
complete_subtask(subtask_id="uuid")  # Wrong parameter name!

# ✅ CORRECT
complete_subtask(task_id="uuid", evidence="Completed task")  # Correct parameter
```

### Postflight parameter errors

**Common Issues:**
- Using `changes` instead of `reasoning` 
- Using `summary` instead of `reasoning`

**Solutions:**
```python
# ❌ WRONG
submit_postflight_assessment(session_id="uuid", changes="What I learned")
submit_postflight_assessment(session_id="uuid", summary="Task complete")

# ✅ CORRECT
submit_postflight_assessment(
    session_id="uuid",
    vectors={...},
    reasoning="What I learned during this task"  # Unified parameter
)
```

### Parameter Type Errors

**Common Issues:**
- Arrays passed as strings
- Wrong enum values
- Missing required parameters

**Quick Reference:**
```python
# Scope must be enum
scope="project_wide"  # ✅ OK
scope="invalid"       # ❌ Error

# Success criteria must be array  
success_criteria=["Test 1", "Test 2"]  # ✅ OK
success_criteria="Test 1"              # ❌ Error

# Importance must be enum
importance="high"      # ✅ OK  
importance="urgent"    # ❌ Error
```

### Debugging MCP Parameter Errors

**Steps to fix:**
1. **Check parameter names:** Use IDE autocomplete or check schemas
2. **Validate types:** Arrays vs strings, enums vs free text
3. **Use MCP tool guidance:** See [`docs/00_START_HERE.md`](00_START_HERE.md#mcp-tool-parameters-guide)
4. **Test individually:** Test each parameter separately

---

## Assessment Issues

### "I don't know what score to give"

**This is normal!** High uncertainty is valid:

```json
{
  "uncertainty": {
    "score": 0.8,
    "rationale": "I'm very uncertain about this assessment - many unknowns"
  }
}
```

**Remember:** Be honest. Uncertainty is NOT failure.

### Getting different scores each time

**This is expected!** Context changes:
- More information → higher CONTEXT score
- After research → higher KNOW score
- Better requirements → higher CLARITY score

**Not a bug:** Scores should change as your state changes.

### "System says I'm overconfident"

**What it means:** Your preflight predictions didn't match postflight reality

**Example:**
- Preflight: KNOW=0.8 (thought I knew a lot)
- Postflight: KNOW=0.6 (realized gaps)
- Status: Overconfident ⚠️

**How to improve:**
- Be more honest in preflight
- Acknowledge unknowns
- Increase UNCERTAINTY when appropriate

**This is valuable feedback!** Calibration improves over time.

---

## Configuration Issues

### `.empirica/` directory not created

**Symptoms:** Directory missing after installation

**Solutions:**
```bash
# Create manually
mkdir -p ~/.empirica/sessions

# Or run onboarding
empirica onboard

# Or run bootstrap
empirica session-create
```

### Credentials file errors

**Symptoms:** Cannot read `credentials.yaml`

**Solutions:**
```bash
# Check if file exists
ls ~/.empirica/credentials.yaml

# Copy template
cp .empirica/credentials.yaml.template ~/.empirica/credentials.yaml

# Edit if needed (only for Phase 1+ features)
nano ~/.empirica/credentials.yaml
```

---

## Performance Issues

### Slow preflight/postflight

**Symptoms:** Commands take >5 seconds

**Causes & Solutions:**

**Large database:**
```bash
# Check database size
du -h ~/.empirica/sessions/sessions.db

# Archive old sessions (future feature)
# For now, backup and recreate:
mv ~/.empirica/sessions/sessions.db ~/.empirica/sessions/sessions.db.old
empirica session-create
```

**Many reflex logs:**
```bash
# Check log size
du -sh .empirica_reflex_logs/

# Archive old logs
tar -czf logs_backup.tar.gz .empirica_reflex_logs/
rm -rf .empirica_reflex_logs/cascade/2024-*
```

---

## Platform-Specific Issues

### Windows: Path issues

**Symptoms:** Can't find files, wrong slashes

**Solutions:**
```bash
# Use forward slashes in configs
"args": ["/path/to/empirica/mcp_local/empirica_mcp_server.py"]
# NOT: "\\path\\to\\..."

# Use WSL for better compatibility
wsl -d Ubuntu
```

### macOS: Code signing issues

**Symptoms:** "cannot be opened because the developer cannot be verified"

**Solutions:**
```bash
# Allow in System Preferences > Security
# Or remove quarantine
xattr -d com.apple.quarantine /path/to/empirica
```

### Linux: SQLite issues

**Symptoms:** SQLite not found

**Solutions:**
```bash
# Install SQLite (usually included)
sudo apt-get install sqlite3 libsqlite3-dev  # Debian/Ubuntu
sudo yum install sqlite sqlite-devel  # RHEL/CentOS
```

---

## Getting Help

### Still stuck?

**1. Check logs:**
```bash
# CLI/Python errors
empirica --help

# MCP server logs
cat ~/.empirica/mcp_server.log

# Session database
sqlite3 ~/.empirica/sessions/sessions.db ".tables"
```

**2. Verify installation:**
```bash
# Check version
empirica --version

# Test imports
python3 -c "from empirica.core.canonical import CanonicalEpistemicAssessor; print('OK')"

# List commands
empirica --help
```

**3. Check documentation:**
- Installation: [`docs/02_INSTALLATION.md`](02_INSTALLATION.md)
- CLI guide: [`docs/03_CLI_QUICKSTART.md`](03_CLI_QUICKSTART.md)
- MCP guide: [`docs/04_MCP_QUICKSTART.md`](04_MCP_QUICKSTART.md)
- Architecture: [`docs/05_ARCHITECTURE.md`](05_ARCHITECTURE.md)

**4. File an issue:**
- Include: Error message, command run, OS version
- Include: `empirica --version` output
- Include: Relevant logs

---

## Common Misunderstandings

### "Why do my scores keep changing?"

✅ **Expected!** Your epistemic state changes with context.

### "High uncertainty means I'm failing?"

❌ **No!** High uncertainty when appropriate is GOOD metacognition.

### "Should I try to get perfect scores?"

❌ **No!** Goal is ACCURATE scores, not high scores. Be honest!

### "Calibration says 'overconfident' - am I broken?"

❌ **No!** This is valuable feedback. Adjust future assessments.

### "Do I need API keys to use Empirica?"

❌ **No!** Phase 0 works entirely locally. API keys only needed for:
- Modality Switcher (Phase 1+, optional)
- Custom integrations

---

## Quick Fixes Checklist

Try these in order:

1. ☐ **Restart:** Close IDE/terminal, reopen
2. ☐ **Reinstall:** `pip install -e . --force-reinstall`
3. ☐ **Clear cache:** `find . -name __pycache__ -exec rm -rf {} +`
4. ☐ **Check logs:** View error messages
5. ☐ **Verify installation:** `empirica --version`
6. ☐ **Check docs:** Review relevant guide
7. ☐ **File issue:** If still stuck

---

**Most issues resolve with:** Reinstall + restart! 🔄
