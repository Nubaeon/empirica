# Handoff: CLI Cleanup & Website Validation

**From:** Rovo Dev (Session 126d5c66)  
**To:** Mini-Agent  
**Goal ID:** e5cc36cb-c813-47e3-8f44-7c6b8890ab85  
**Priority:** High (affects website content)

---

## 🎯 Mission

Clean up CLI commented code, validate all commands work, and ensure website content matches reality.

---

## 📋 Context

**What Just Happened:**
- Fixed CLI error: deprecated `cascade` command (was ModalitySwitcher plugin)
- Left commented-out code in `_add_cascade_parsers()` 
- Website content references commands we just deprecated
- Need to ensure all CLI commands actually work

**The Problem:**
- Commented code makes CLI confusing
- Website might reference removed commands
- Need reality check on what commands exist vs documentation

---

## ✅ Your Tasks (7 subtasks)

### 1. Remove Commented Cascade Code
**Task ID:** `631e6490-6c90-4d93-b628-5f2c4ccba6c4`

**File:** `empirica/cli/cli_core.py`

**What to do:**
- Find `_add_cascade_parsers()` function (around line 131)
- Remove the entire function or replace with single-line comment
- The function currently just has `pass` - clean it up

**Current state:**
```python
def _add_cascade_parsers(subparsers):
    """Add cascade command parsers (DEPRECATED - use MCP tools instead)
    ...long docstring...
    """
    # Deprecated - CASCADE workflow now uses MCP tools
    pass
```

**Replace with:**
```python
# cascade command removed - was ModalitySwitcher plugin
# Use MCP tools: execute-preflight, execute-check, execute-postflight
```

---

### 2. Remove Session-End Comments
**Task ID:** `ba9296bd-7982-4d69-bad5-3979329163d1`

**Search for:**
```bash
grep -rn "# session-end\|# 'session-end'" empirica/cli/
```

**Remove any commented-out session-end references**

---

### 3. Audit CLI Command Mappings ⚠️ CRITICAL
**Task ID:** `ea7feb94-863f-4f43-9fe3-6bef5f953c3f`

**File:** `empirica/cli/cli_core.py` (around line 675-700)

**What to do:**
1. Find the `COMMAND_MAP` dictionary
2. For each command, verify the handler function exists
3. Test that imports are correct

**Check pattern:**
```python
COMMAND_MAP = {
    'bootstrap': handle_bootstrap_command,  # ← Does this function exist?
    'preflight': handle_preflight_command,  # ← Is it imported?
    ...
}
```

**How to verify:**
```bash
# For each handler in COMMAND_MAP
grep "def handle_bootstrap_command" empirica/cli/command_handlers/*.py
grep "from .* import.*handle_bootstrap_command" empirica/cli/command_handlers/__init__.py
```

**Document findings in your evidence**

---

### 4. Test MCP Workflow Commands ⚠️ CRITICAL
**Task ID:** `a047ce0c-7ad1-4ae6-b350-b526aa1ec95d`

**Commands to test:**
```bash
# Session management
empirica bootstrap --help
empirica session-list --help

# Workflow
empirica preflight --help
empirica preflight-submit --help
empirica check --help  
empirica check-submit --help
empirica postflight --help
empirica postflight-submit --help

# Goals
empirica goals-create --help
empirica goals-add-subtask --help
empirica goals-complete-subtask --help
empirica goals-list --help

# Handoff
empirica handoff-create --help
empirica handoff-query --help
```

**For each command:**
- ✅ Does it show help?
- ✅ Does help text match reality?
- ❌ Note any errors

---

### 5. Update Help Text
**Task ID:** `21e82a1f-4192-40bc-8735-47eea06db6fb`

**File:** `empirica/cli/cli_core.py` (top of file, around line 20-28)

**Current epilog:**
```python
epilog="""
Examples:
  empirica bootstrap              # Bootstrap the framework
  empirica assess "my question"   # Run uncertainty assessment
  empirica cascade "should I?"    # Run metacognitive cascade  ← REMOVE THIS
  ...
```

**Update to show actual MCP workflow commands**

---

### 6. Create CLI Reality Check Document
**Task ID:** `c83c94a0-ce7e-4aed-993b-58dd83c4618a`

**File to create:** `CLI_COMMANDS_REALITY_CHECK.md`

**Format:**
```markdown
# CLI Commands Reality Check

**Generated:** [date]  
**Purpose:** Document all working CLI commands for website validation

## Session Management
- `empirica bootstrap` - [TESTED ✅/❌] - Description
- `empirica session-list` - [TESTED ✅/❌] - Description

## CASCADE Workflow (MCP)
- `empirica preflight` - [TESTED ✅/❌] - Description
- `empirica preflight-submit` - [TESTED ✅/❌] - Description
...

## Goals Management
...

## Handoff & Continuity
...

## DEPRECATED/REMOVED
- `empirica cascade` - REMOVED - Was ModalitySwitcher plugin
- `empirica session-end` - REMOVED - Use handoff-create

## Command Parameter Examples

### preflight-submit
```bash
empirica preflight-submit \\
  --session-id UUID \\
  --vectors '{"engagement": 0.8, ...}' \\
  --reasoning "Starting assessment"  # ← NOT --changes
```

### postflight-submit
```bash
empirica postflight-submit \\
  --session-id UUID \\
  --vectors '{"engagement": 0.9, ...}' \\
  --reasoning "Completion assessment"  # ← NOT --changes
```

## MCP Tool Parameters (Critical)

**create_goal:**
- scope: MUST be enum ["task_specific", "session_scoped", "project_wide"]
- success_criteria: MUST be array

**add_subtask:**
- importance: ["critical", "high", "medium", "low"]  
- NOT epistemic_importance

**complete_subtask:**
- task_id: UUID  
- NOT subtask_id
```

---

### 7. Validate Website Content ⚠️ CRITICAL
**Task ID:** `499b99d1-ec67-4d49-9256-84751eb12d85`

**What to do:**
1. Read `CLI_COMMANDS_REALITY_CHECK.md` (you just created)
2. Check website content files:
   - `website/content/*.md`
   - Look for command examples
   - Look for CLI references

3. Find and fix:
   - ❌ References to `cascade` command
   - ❌ References to `session-end` command
   - ❌ Wrong parameter names (epistemic_importance, subtask_id, changes)
   - ❌ Commands that don't exist

4. Update with correct:
   - ✅ MCP workflow commands (execute-preflight, etc.)
   - ✅ Correct parameter names (importance, task_id, reasoning)
   - ✅ Working CLI commands only

**Evidence:** List each file checked and changes made

---

## 🎯 Success Criteria

**Code:**
- [ ] No commented-out code in cli_core.py
- [ ] All COMMAND_MAP entries have working handlers
- [ ] All MCP commands tested and working

**Documentation:**
- [ ] CLI_COMMANDS_REALITY_CHECK.md created
- [ ] All commands documented with test status
- [ ] Parameter examples are correct

**Website:**
- [ ] No references to deprecated commands
- [ ] All CLI examples are accurate
- [ ] Parameter names match reality

---

## 📚 Reference Materials

**CLI Files:**
- `empirica/cli/cli_core.py` - Main CLI and command mapping
- `empirica/cli/command_handlers/__init__.py` - Handler imports
- `empirica/cli/command_handlers/*.py` - Individual command handlers

**Website Files:**
- `website/content/*.md` - All content pages
- `website/content/*_VALIDATED.md` - Already validated (check these first!)

**Key Changes From Previous Sessions:**
- ✅ session-end → handoff-create
- ✅ reasoning parameter (unified for preflight/postflight)
- ✅ cascade command → removed (use MCP tools)
- ✅ MCP tool parameters fixed (importance, task_id, etc.)

---

## 🛠️ Quick Commands

**Find commented code:**
```bash
grep -n "^[[:space:]]*#.*cascade\|^[[:space:]]*#.*session-end" empirica/cli/cli_core.py
```

**Test command:**
```bash
empirica <command> --help 2>&1 | head -5
```

**Find website command references:**
```bash
grep -rn "empirica cascade\|empirica session-end" website/content/
```

---

## ⏱️ Estimated Time

- Cleanup (tasks 1-2): 30 min
- Audit & test (tasks 3-4): 1 hour
- Documentation (tasks 5-6): 45 min
- Website validation (task 7): 45 min

**Total:** ~3 hours

---

## 🚨 Important Notes

**Don't skip the audit (task 3)!**
- We just fixed one broken command mapping
- There might be more
- Better to find them now than have users hit errors

**Website validation is critical:**
- Website will be public-facing
- Incorrect command examples = bad user experience
- This is the final check before launch

---

**Ready to start! Begin with task 1 (cleanup) and work through systematically.**
