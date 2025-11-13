# Cache Refresh Guide - Qwen & Gemini

**Problem:** AI assistants cache file contents. After making changes, they may reference old cached versions instead of current files.

**Symptoms:**
- "But the file says X" when file actually says Y
- Import errors that should be fixed
- References to old code that's been updated
- Stale architecture understanding

---

## 🔄 When to Refresh Cache

### After These Events:
1. ✅ Installing new dependencies
2. ✅ Creating new `__init__.py` files
3. ✅ Modifying imports in source files
4. ✅ Updating architecture (new modules/classes)
5. ✅ Fixing bugs that tests are checking

### Symptoms of Cache Poisoning:
- "I already tried that" when file was actually changed
- Import errors persist after adding `__init__.py`
- References to code that was just modified
- Confusion about current state vs past state

---

## 🔧 How to Refresh (For You to Execute)

### Option 1: Explicit Re-read
**Tell them:**
```
"Please re-read the following files to refresh your cache:
- mcp_local/__init__.py
- empirica/bootstraps/__init__.py
- tests/mcp/test_mcp_tools.py"
```

### Option 2: Start Fresh Context
**In tmux:**
```bash
# Clear the session, start new conversation
# Or: Explicitly state "I've made changes, please re-read X"
```

### Option 3: Checkpoint and Reset
**Tell them:**
```
"CHECKPOINT: I've made changes to the codebase.
Please clear your cache and re-read:
1. Project structure (ls -la)
2. Modified files: [list]
3. New files: [list]

Treat this as a fresh start from this point."
```

---

## 📋 Current Session Status

### Files Modified Since Start:
- ✅ `mcp_local/__init__.py` - Created (if it wasn't there)
- ✅ `.venv-mcp/` - pytest-cov installed
- ✅ `tests/coordination/*.md` - Documentation updates

### Cache Refresh Needed For:
**Gemini:**
- [ ] `mcp_local/__init__.py` - May still think it's missing
- [ ] `empirica/bootstraps/` - Import structure
- [ ] Test files they created - May reference old versions

**Qwen:**
- [ ] Any files they modified
- [ ] Architecture if Gemini found gaps

---

## 🎯 Best Practices

### 1. Announce Changes
**After you make a fix:**
```
"UPDATE: I've created mcp_local/__init__.py
Gemini, please re-read:
- mcp_local/ directory structure
- Your test file that imports from mcp_local"
```

### 2. Explicit Verification
**Ask them to verify:**
```
"Gemini, can you verify that mcp_local/__init__.py now exists?
Please run: ls -la mcp_local/__init__.py"
```

### 3. Session Checkpoints
**Every major change:**
```
"CHECKPOINT: State has changed.
Previous state: X
Current state: Y
Please update your understanding."
```

---

## 🚨 Critical Moments

### When Cache Refresh is CRITICAL:

**1. After Installing Dependencies**
```bash
# You did:
pip install pytest-cov

# Tell Gemini:
"I've installed pytest-cov in .venv-mcp
Please verify: pytest --version
Your cached understanding that it's missing is now outdated."
```

**2. After Creating Package Files**
```bash
# You did:
touch mcp_local/__init__.py

# Tell Gemini:
"I've created mcp_local/__init__.py making it a proper package.
Your import errors should now be resolved.
Please re-test with this new state."
```

**3. After Fixing Their Test Code**
```bash
# You modified their test

# Tell them:
"I've updated your test file to fix the import.
Please re-read tests/mcp/test_mcp_tools.py
Your cached version is outdated."
```

---

## 🔍 Detecting Cache Poisoning

### Signs in Gemini's Behavior:
- ❌ "I already tried adding __init__.py" (when you just added it)
- ❌ "The import still fails" (when you fixed it)
- ❌ References old error messages
- ❌ Suggests solutions already implemented

### Signs in Qwen's Behavior:
- ❌ Creates tests for code that changed
- ❌ References old architecture
- ❌ Doesn't see Gemini's discoveries

---

## 🎬 For the Recording

### This is Actually Good Content!

**Show the reality:**
1. "AI assistants cache files"
2. "After changes, need to refresh"
3. "Explicit cache management improves coordination"

**Example narration:**
```
"Notice: Gemini was experiencing import errors.
I created the missing __init__.py file.
Now I need to tell Gemini to refresh their cache:

'Gemini, CHECKPOINT: I've created mcp_local/__init__.py
Please re-read the mcp_local/ directory structure
and re-run your tests.'"
```

**This demonstrates:**
- Real coordination challenges
- Human-AI handoff points
- Cache management in multi-AI systems
- Practical workflow issues

---

## 📝 Script for Right Now

### For Gemini (if still having import issues):

```
"Gemini, CACHE REFRESH:

I've made the following changes:
1. Created mcp_local/__init__.py (makes it a proper package)
2. Installed pytest-cov in .venv-mcp
3. Your import errors should now be resolved

Please:
1. Re-read: mcp_local/__init__.py (verify it exists)
2. Re-read: your test files
3. Re-run: pytest tests/mcp/ -v

Treat this as a fresh start from this point."
```

### For Qwen (if needed later):

```
"Qwen, CACHE REFRESH:

Gemini has discovered several gaps in the codebase:
1. SessionDatabase missing save_assessment() method
2. MCP tools had import issues (now fixed)
3. Some test infrastructure needed updates

Please re-read:
- empirica/data/session_database.py
- tests/mcp/ (Gemini's work)

Update your understanding of current state."
```

---

## 🎯 Prevention Strategies

### During Coordination:

**1. State Changes Explicitly**
```
"I'm about to modify file X"
→ Make change
→ "File X is now modified, new state is Y"
```

**2. Version Control Metaphor**
```
"Think of this as a git commit.
Previous commit: Import error
New commit: __init__.py added, imports work
Please checkout the new commit in your mental model."
```

**3. Incremental Updates**
```
Don't let too many changes accumulate.
After 3-5 changes, do a full cache refresh checkpoint.
```

---

## ✅ Summary

**Cache poisoning is real and affects:**
- File contents
- Directory structure
- Dependency availability
- Test results

**Solution:**
- Explicit refresh commands
- State change announcements
- Verification steps
- Regular checkpoints

**For the demo:**
- This is realistic coordination
- Shows human-AI handoff
- Demonstrates real workflow
- Educational content!

---

**Current Status:** If Gemini still has import issues, do cache refresh now!
