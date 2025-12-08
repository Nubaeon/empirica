# Troubleshooting Guide

**Empirica v4.0 - Common Issues and Solutions**

**Storage Architecture:** See `docs/architecture/STORAGE_ARCHITECTURE_COMPLETE.md`  

---

## Quick Diagnosis

Run this diagnostic first:

```python
python3 << 'PYEOF'
import sys
print(f"Python version: {sys.version}")

try:
    from empirica.data.session_database import SessionDatabase
    print("✅ Empirica imports work")
except ImportError as e:
    print(f"❌ Import error: {e}")

try:
    db = SessionDatabase()
    session_id = db.create_session(ai_id="test")
    print(f"✅ Session creation works: {session_id}")
    db.close()
except Exception as e:
    print(f"❌ Session creation error: {e}")

try:
    from empirica.core.canonical import GitEnhancedReflexLogger
    logger = GitEnhancedReflexLogger(session_id=session_id)
    print(f"✅ Reflex logger works")
except Exception as e:
    print(f"❌ Reflex logger error: {e}")
PYEOF
```

---

## Installation Issues

### Issue 1: Module Not Found

**Error:** `ModuleNotFoundError: No module named 'empirica'`

**Solutions:**
```bash
# Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/empirica"

# OR install in development mode
cd /path/to/empirica && pip install -e .

# OR run from correct directory
cd /path/to/empirica && python3 your_script.py
```

### Issue 2: Old Import Paths

**Error:** `ImportError: cannot import name 'CanonicalEpistemicCascade' from 'empirica'`

**Solution:** Update imports
```python
# ✅ Correct imports
from empirica.core.canonical import CanonicalEpistemicAssessor
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade
```

### Issue 3: Missing Dependencies

**Error:** `ModuleNotFoundError: No module named 'watchdog'`

**Solution:**
```bash
pip install -r requirements.txt
# OR
pip install watchdog psutil numpy
```

---

## Bootstrap Issues

### Issue 4: Bootstrap Crashes

**Error:** `AttributeError: 'NoneType' object has no attribute 'generate_response'`

**Cause:** Wrong bootstrap level for required features

**Solution:** Use session-create (v4.0 simplified)
```bash
# ✅ CORRECT - Simple session creation (v4.0)
empirica session-create --ai-id myai --output json

# Or via Python:
db = SessionDatabase()
session_id = db.create_session(ai_id="myai")
```

**Note:** In v4.0, `bootstrap_level` parameter exists for backward compatibility but has no behavioral effect. "Bootstrap" refers only to system prompts installation, not session creation.

### Issue 5: Component Not Found

**Error:** `KeyError: 'canonical_cascade'` or similar component errors

**Solution:** Use CLI or MCP for session creation
```python
# ❌ OLD - Direct component instantiation removed
# This pattern no longer works

# ✅ NEW - Use CLI or MCP
# CLI: empirica session-create --ai-id myai
# MCP: create_session(ai_id="myai")

# Then use direct imports if needed
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade
from empirica.core.canonical import CanonicalEpistemicAssessor

cascade = CanonicalEpistemicCascade()
assessor = CanonicalEpistemicAssessor()
```

**v4.0 Note:** All sessions use lazy component loading. Components are loaded on-demand, not at session creation time.

---

## Cascade Issues

### Issue 6: Cascade Hangs

**Solution:** Add timeout
```python
import asyncio

async def run_with_timeout():
    try:
        result = await asyncio.wait_for(
            cascade.run_epistemic_cascade(task, context),
            timeout=30.0
        )
        return result
    except asyncio.TimeoutError:
        print("❌ Cascade timed out")
        return None
```

### Issue 7: Low Confidence Always (~0.5)

**Cause:** Placeholder mode (no LLM)

**Solution:** This is expected without LLM
- All vectors default to 0.5 (neutral)
- Action: "investigate" (conservative)
- To fix: Install ollama or configure OpenAI API

```bash
# Install ollama
# https://ollama.ai
ollama pull phi3
# Empirica auto-detects at localhost:11434
```

### Issue 8: ENGAGEMENT Gate Always Fails

**Cause:** Vague task description

**Solution:** Be specific
```python
# ❌ BAD
task = "Do that thing"

# ✅ GOOD
task = "Analyze auth.py for SQL injection vulnerabilities"
context = {'files': ['auth.py'], 'urgency': 'high'}
```

---

## Database Issues

### Issue 9: Database Permission Error

**Error:** `sqlite3.OperationalError: unable to open database file`

**Solution:**
```bash
# Check permissions
ls -la .empirica/sessions/sessions.db

# Fix permissions
chmod 664 .empirica/sessions/sessions.db
chmod 775 .empirica/sessions/
```

### Issue 10: Session Queries Return None/Empty

**Symptom:** `get_preflight_assessment(session_id)` returns `None` or empty

**Causes & Solutions:**

**Cause 1:** Session has no assessments submitted yet (normal behavior)
```python
# This is NOT an error - session exists but no PREFLIGHT submitted yet
session = db.get_session(session_id)  # ✅ Returns session
preflight = db.get_preflight_assessment(session_id)  # Returns None (expected)
```

**Cause 2:** Wrong database path (cwd-dependent)
```bash
# Database path depends on where you run the command
# From /empirica/ → .empirica/sessions/sessions.db ✅
# From /empirica/empirica/ → empirica/.empirica/sessions/sessions.db ❌

# Solution: Always run from project root
cd /path/to/empirica  # Project root
empirica sessions-list  # Uses correct DB
```

**Cause 3:** Using shortened session ID
```python
# ❌ WRONG - shortened ID
preflight = db.get_preflight_assessment('6f86708e')

# ✅ CORRECT - full UUID
preflight = db.get_preflight_assessment('6f86708e-3c3d-4252-a73c-f3ce3daf1aa3')
```

### Issue 11: "No such column" or "No such table" Error

**Error:** `sqlite3.OperationalError: no such column/table`

**Cause:** Using deprecated table names or columns

**Solution:** Use the unified `reflexes` table
```python
# ❌ WRONG - Old deprecated tables
db.conn.execute("SELECT * FROM epistemic_assessments WHERE session_id=?", (sid,))
db.conn.execute("SELECT * FROM preflight_assessments WHERE session_id=?", (sid,))

# ✅ CORRECT - Use reflexes table with phase filtering
db.get_latest_vectors(session_id, phase="PREFLIGHT")  # Latest PREFLIGHT
db.get_latest_vectors(session_id, phase="POSTFLIGHT")  # Latest POSTFLIGHT
db.get_vectors_by_phase(session_id, phase="CHECK")  # All CHECK phases

# Raw SQL with reflexes table
cursor.execute("""
    SELECT * FROM reflexes
    WHERE session_id = ? AND phase = 'PREFLIGHT'
    ORDER BY timestamp DESC LIMIT 1
""", (session_id,))
```

**Migration Note:** Old tables (`epistemic_assessments`, `preflight_assessments`, 
`postflight_assessments`, `check_phase_assessments`) were unified into `reflexes` table.
Data migration happens automatically on first database access.

**Reference:** See `12_SESSION_DATABASE.md` for full schema details and `docs/architecture/STORAGE_ARCHITECTURE_COMPLETE.md` for storage architecture

---
mkdir -p .empirica/sessions
chmod 755 .empirica/sessions

# OR specify custom location
db = SessionDatabase("/custom/path/sessions.db")
```

### Issue 10: Database Locked

**Error:** `sqlite3.OperationalError: database is locked`

**Cause:** Multiple processes accessing database

**Solution:**
```python
# Always close database
db = SessionDatabase()
try:
    # your code
finally:
    db.close()

# OR use context manager (future)
```

---

## Import Path Issues

### Common Import Errors

**All old imports need updating:**

**Package Migration:**

Empirica uses consistent module paths:

| Module | Path |
|--------|------|
| Core Canonical | `empirica.core.canonical` |
| Metacognitive Cascade | `empirica.core.metacognitive_cascade` |
| Session Database | `empirica.data` |
| Bootstraps | `empirica.bootstraps` |
| Calibration | `empirica.calibration` |

**Find Deprecated Imports:**
```bash
# All imports should use empirica.*
grep -r "from empirica" your_project/
```

---

## Performance Issues

### Issue 11: Slow Session Creation

**Symptom:** Session creation takes > 1 second

**Cause:** This should NOT happen in v4.0 (instant creation with lazy loading)

**Solution:**
```python
# v4.0 sessions are instant (no pre-loading)
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()
session_id = db.create_session(ai_id="test")  # <100ms
db.close()

# If slow, check database permissions or disk I/O
```

**Note:** v4.0 uses lazy component loading - no initialization overhead at session creation time.

### Issue 12: Slow Cascade

**Symptom:** Cascade takes > 30 seconds

**Causes:**
1. LLM calls (normal - each call ~2-5s)
2. Multiple investigation rounds (3 rounds = 3 LLM calls)

**Solutions:**
```python
# Limit investigation rounds
cascade = CanonicalEpistemicCascade(max_investigation_rounds=1)

# Increase confidence threshold (less investigation)
cascade = CanonicalEpistemicCascade(action_confidence_threshold=0.60)
```

---

## Tmux Dashboard Issues

### Issue 13: Dashboard Not Working

**Warning:** `⚠️ Tmux dashboard unavailable`

**Cause:** Tmux not installed or not in tmux session

**Solution:**
```bash
# Install tmux
sudo apt install tmux  # Linux
brew install tmux      # macOS

# Start tmux session
tmux new -s empirica

# OR disable dashboard
cascade = CanonicalEpistemicCascade(enable_action_hooks=False)
```

---

## Getting More Help

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run cascade with debug output
```

### Check System Info

```bash
python3 --version
pip list | grep -E "watchdog|psutil|numpy"
which python3
echo $PYTHONPATH
```

### Common Checklist

- [ ] Python 3.8+ installed
- [ ] In correct directory (`cd /path/to/empirica`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Using new import paths (`from empirica.core...`)
- [ ] Using bootstrap level 2 or higher
- [ ] `.empirica/` directory has write permissions

---

## Still Stuck?

1. **Re-run diagnostic** at top of this guide
2. **Check FAQ:** [22_FAQ.md](22_FAQ.md)
3. **Review logs:** Look for error messages
4. **Try minimal example:** [03_BASIC_USAGE.md](03_BASIC_USAGE.md)
5. **File issue:** Contact maintainers (GitHub coming when open-sourced)

---

**Most issues are:** Import paths, bootstrap level, or missing dependencies. Check these first! ✅


---

**Note:** Empirica uses goals (with vectorial scope and subtasks) and git notes (checkpoints, goals, handoffs) for automatic session continuity and cross-AI coordination. See [Storage Architecture](../architecture/STORAGE_ARCHITECTURE_COMPLETE.md) and [Cross-AI Coordination](26_CROSS_AI_COORDINATION.md).
