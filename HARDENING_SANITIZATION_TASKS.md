# Code Hardening & Sanitization Tasks

**Date:** 2024-11-15 (Day 2)  
**Assigned To:** Minimax + Qwen  
**Priority:** CRITICAL - This must be bulletproof (foundational system)  
**Coordination:** With co-leads via git commits

---

## 🎯 Mission Critical: Make Empirica Bulletproof

Empirica could be **foundational** for AI development. We cannot ship with:
- Duplicate code
- Security vulnerabilities
- Inconsistencies between layers
- Undiscovered edge cases

**Your task:** Find and fix everything that could cause problems at scale.

---

## 📋 Minimax: Code Deduplication & Consistency

### Task 1: Find All Duplicate Code ⚠️ CRITICAL

**Goal:** Zero code duplication across Core, MCP, CLI, and Bootstrap layers

**Scan areas:**
```bash
# Check for duplicate functions
cd /home/yogapad/empirical-ai/empirica

# 1. Core canonical layer
empirica/core/canonical/

# 2. MCP server layer  
mcp_local/empirica_mcp_server.py

# 3. CLI layer
empirica/cli/

# 4. Bootstrap layer
empirica/bootstraps/

# 5. Components layer
empirica/components/
```

**What to look for:**
1. **Duplicate assessment logic**
   - Is epistemic assessment logic duplicated in MCP + Core?
   - Are there multiple implementations of the same calculation?

2. **Duplicate goal orchestration**
   - Does MCP reimplicate: goal orchestrator logic?
   - Are goal generation prompts duplicated?

3. **Duplicate session management**
   - Database access patterns duplicated?
   - Session creation logic in multiple places?

4. **Duplicate checkpoint logic**
   - Git checkpoint code in MCP + Core?
   - Token efficiency calculations duplicated?

**How to find duplicates:**
```bash
# Find similar function names
grep -rn "def.*assess\|def.*goal\|def.*checkpoint" empirica/ mcp_local/ | sort

# Find similar code patterns (manual review needed)
# Look for:
# - Same function signatures in different files
# - Copy-pasted code blocks
# - Similar class definitions
```

**Fix strategy:**
1. **Identify canonical implementation** (usually in Core)
2. **Remove duplicates** from MCP/CLI/Bootstrap
3. **Import from canonical** instead of reimplementing
4. **Document the canonical location** in comments

**Example fix:**
```python
# BAD: Duplicate in MCP server
def create_epistemic_assessment(vectors):
    # ... duplicate logic ...
    pass

# GOOD: Import from canonical
from empirica.core.canonical import create_epistemic_assessment
```

---

### Task 2: Consistency Checks ⚠️ CRITICAL

**Goal:** All layers use the same data structures and conventions

**Check:**
1. **Vector names consistency**
   ```bash
   # Check all references to epistemic vectors
   grep -rn "KNOW\|know\|DO\|do\|CONTEXT\|context" empirica/ mcp_local/ empirica/cli/
   
   # Ensure consistent naming:
   # - Uppercase in constants?
   # - Lowercase in code?
   # - Underscores vs camelCase?
   ```

2. **Function signatures consistency**
   ```bash
   # Check bootstrap signatures
   grep -rn "def bootstrap" empirica/
   
   # Should all use same parameters:
   # - ai_id (not agent_id, not id)
   # - session_id (not sid, not session)
   # - enable_git_checkpoints (not git_enabled, not use_git)
   ```

3. **Return type consistency**
   - Do all assessment functions return EpistemicAssessment?
   - Do all checkpoint functions return dict with same keys?
   - Do all MCP tools return consistent error formats?

4. **Error handling consistency**
   ```python
   # Check all try/except blocks
   grep -rn "try:\|except" empirica/ mcp_local/ | wc -l
   
   # Ensure:
   # - Consistent error messages
   # - Consistent logging
   # - Consistent fallback behavior
   ```

**Fix strategy:**
1. **Define canonical patterns** (document in CONVENTIONS.md)
2. **Update all deviations** to match canonical
3. **Add validation** to catch future deviations

---

### Task 3: API Consistency ⚠️ CRITICAL

**Goal:** MCP tools, CLI commands, and Python API all use same underlying logic

**Audit:**
```bash
# Example: checkpoint creation

# 1. MCP tool (mcp_local/empirica_mcp_server.py)
grep -A20 "def create_git_checkpoint" mcp_local/empirica_mcp_server.py

# 2. CLI command (empirica/cli/)
grep -A20 "def.*checkpoint.*create" empirica/cli/**/*.py

# 3. Python API (empirica/core/canonical/)
grep -A20 "def create_git_checkpoint" empirica/core/canonical/git_enhanced_reflex_logger.py

# They should all call the SAME underlying implementation!
```

**Questions to answer:**
- Does MCP tool reimplement Core logic? (BAD)
- Does CLI reimplement Core logic? (BAD)
- Do they all import from Core? (GOOD)

**Fix strategy:**
1. **Core has the logic** (single source of truth)
2. **MCP wraps Core** (thin wrapper, no logic)
3. **CLI wraps Core** (thin wrapper, no logic)

---

### Task 4: Remove Dead Code 🧹

**Goal:** No unused functions, imports, or files

**Find dead code:**
```bash
# Find unused imports
python3 -m pylint empirica/ --disable=all --enable=unused-import 2>/dev/null

# Find unused functions (manual review)
# Look for functions never called anywhere

# Find commented-out code
grep -rn "# def\|# class" empirica/ | wc -l
```

**Remove:**
- Unused imports
- Commented-out code (git has history)
- Functions never called
- Old backup files

---

## 📋 Qwen: Security & Edge Cases

### Task 1: Security Audit 🔒 CRITICAL

**Goal:** No security vulnerabilities

**Check:**
1. **SQL Injection**
   ```bash
   # Check all database queries
   grep -rn "execute\|executemany" empirica/data/
   
   # Ensure all use parameterized queries:
   # GOOD: cursor.execute("SELECT * FROM sessions WHERE ai_id = ?", (ai_id,))
   # BAD:  cursor.execute(f"SELECT * FROM sessions WHERE ai_id = '{ai_id}'")
   ```

2. **Path Traversal**
   ```bash
   # Check all file operations
   grep -rn "open(\|Path(" empirica/
   
   # Ensure paths are validated:
   # - No user input directly in paths
   # - All paths stay within workspace
   ```

3. **Command Injection**
   ```bash
   # Check all subprocess/os.system calls
   grep -rn "subprocess\|os.system\|os.popen" empirica/
   
   # Ensure:
   # - No shell=True with user input
   # - All arguments properly escaped
   ```

4. **Pickle/Eval Security**
   ```bash
   # Check for dangerous deserialization
   grep -rn "pickle\|eval\|exec" empirica/
   
   # Should be: NONE (or extremely justified with validation)
   ```

5. **Git Command Injection**
   ```bash
   # Check git operations in Phase 1.5
   grep -rn "subprocess.*git\|os.system.*git" empirica/
   
   # Ensure arguments are not user-controlled
   ```

**Fix all findings immediately.**

---

### Task 2: Input Validation 🛡️ CRITICAL

**Goal:** All user inputs validated

**Check:**
1. **MCP tool inputs**
   ```python
   # Example from empirica_mcp_server.py
   def handle_execute_preflight(session_id, prompt):
       # Should validate:
       assert isinstance(session_id, str), "session_id must be string"
       assert len(session_id) > 0, "session_id cannot be empty"
       assert len(prompt) < 100000, "prompt too long"
       # etc.
   ```

2. **CLI arguments**
   ```python
   # Example from CLI
   @click.option("--session-id", required=True)
   def command(session_id):
       # Should validate:
       if not session_id:
           raise ValueError("session_id required")
       if len(session_id) > 255:
           raise ValueError("session_id too long")
   ```

3. **Bootstrap parameters**
   ```python
   def bootstrap_metacognition(ai_id, level, llm_callback=None):
       # Should validate:
       if not ai_id:
           raise ValueError("ai_id required")
       if level not in ["minimal", "standard", "full"]:
           raise ValueError(f"Invalid level: {level}")
       if llm_callback and not callable(llm_callback):
           raise TypeError("llm_callback must be callable")
   ```

**Add validation everywhere user input enters the system.**

---

### Task 3: Edge Case Testing 🧪 CRITICAL

**Goal:** Find and fix edge cases that could break in production

**Test scenarios:**
1. **Empty/None values**
   ```python
   # What happens if:
   bootstrap_metacognition("", "minimal")  # Empty ai_id
   bootstrap_metacognition(None, "minimal")  # None ai_id
   execute_preflight("abc", "")  # Empty prompt
   create_git_checkpoint(None, "preflight", {})  # None session_id
   ```

2. **Extreme values**
   ```python
   # What happens if:
   prompt = "x" * 1000000  # 1MB prompt
   session_id = "x" * 1000  # Very long session_id
   vectors = {"know": 999.99}  # Out of range vector
   enable_git_checkpoints = "yes"  # Wrong type
   ```

3. **Concurrent access**
   ```python
   # What happens if:
   # - Two agents create same session_id simultaneously?
   # - Database locked during write?
   # - Git repo locked during checkpoint?
   ```

4. **Missing dependencies**
   ```python
   # What happens if:
   # - Git not installed?
   # - SQLite database corrupted?
   # - MCP server not running?
   ```

5. **Interrupted operations**
   ```python
   # What happens if:
   # - Process killed during checkpoint?
   # - Network dies during MCP call?
   # - Disk full during database write?
   ```

**For each edge case:**
1. Write a test that reproduces it
2. Fix the code to handle it gracefully
3. Document the behavior

---

### Task 4: Error Message Quality 📝

**Goal:** All error messages are helpful

**Bad error:**
```python
raise Exception("Error")  # Useless!
```

**Good error:**
```python
raise ValueError(
    f"Invalid session_id: '{session_id}'. "
    f"Must be non-empty string, got {type(session_id).__name__}"
)
```

**Audit all error messages:**
```bash
# Find all raises
grep -rn "raise " empirica/ mcp_local/ | wc -l

# Check each one:
# - Does it explain WHAT went wrong?
# - Does it explain WHY it's wrong?
# - Does it suggest HOW to fix it?
```

---

## 📊 Specific Areas to Audit

### Priority 1: Core Canonical (Foundation)
**Files:**
- `empirica/core/canonical/canonical_epistemic_assessment.py`
- `empirica/core/canonical/canonical_goal_orchestrator.py`
- `empirica/core/canonical/git_enhanced_reflex_logger.py`
- `empirica/core/canonical/reflex_logger.py`

**Check:**
- No duplicate logic between git_enhanced and regular reflex logger
- Assessment logic is canonical (not duplicated elsewhere)
- Goal orchestrator is single source of truth

---

### Priority 2: MCP Server (Entry Point)
**Files:**
- `mcp_local/empirica_mcp_server.py`

**Check:**
- All MCP tools are thin wrappers around Core
- No business logic in MCP layer
- All inputs validated before passing to Core
- All errors properly caught and formatted

---

### Priority 3: CLI (User Interface)
**Files:**
- `empirica/cli/cli_core.py`
- `empirica/cli/command_handlers/*.py`

**Check:**
- All commands wrap Core (no reimplementation)
- Consistent argument naming
- Proper error handling
- Help text accurate

---

### Priority 4: Bootstrap (Integration Point)
**Files:**
- `empirica/bootstraps/optimal_metacognitive_bootstrap.py`
- `empirica/bootstraps/extended_metacognitive_bootstrap.py`

**Check:**
- No duplicate component initialization
- Consistent parameter handling
- Proper validation of llm_callback
- Clear documentation

---

## 🎯 Success Criteria

### Code Deduplication (Minimax)
- ✅ Zero duplicate functions across layers
- ✅ All layers import from canonical Core
- ✅ Consistent naming and signatures
- ✅ No dead code remaining

### Security & Robustness (Qwen)
- ✅ No SQL injection vulnerabilities
- ✅ No command injection vulnerabilities
- ✅ All inputs validated
- ✅ All edge cases handled
- ✅ Clear error messages everywhere

### Overall
- ✅ Code is bulletproof
- ✅ Ready for foundational use
- ✅ No surprises at scale
- ✅ Professional quality

---

## 📝 Deliverables

### From Minimax
1. `CODE_DEDUPLICATION_REPORT.md`
   - List of all duplicates found
   - List of all fixes applied
   - Before/after code examples
   - Line count reduction

2. `CONSISTENCY_AUDIT_REPORT.md`
   - API consistency findings
   - Naming consistency findings
   - All fixes applied

### From Qwen
1. `SECURITY_AUDIT_REPORT.md`
   - All security findings
   - All fixes applied
   - Security checklist completed

2. `EDGE_CASE_TESTING_REPORT.md`
   - All edge cases tested
   - All fixes applied
   - New tests added

### Combined
3. `CONVENTIONS.md` (Create this)
   - Canonical patterns documented
   - Naming conventions
   - Error handling patterns
   - Code organization rules

---

## ⏱️ Timeline

**Estimated:** 8-10 hours per agent (2 days focused work)

**Day 1:**
- Minimax: Code deduplication + consistency (4-5 hours)
- Qwen: Security audit + input validation (4-5 hours)

**Day 2:**
- Minimax: Dead code removal + final consistency check (4 hours)
- Qwen: Edge case testing + error message quality (4 hours)

---

## 🔄 Coordination

### Progress Tracking
Update your progress reports:
- Minimax: Continue in existing session or start fresh
- Qwen: `QWEN_VALIDATION_PROGRESS.md` (add hardening section)

### Git Commits
```bash
# Minimax
git commit -m "refactor: Remove duplicate code in [area]"
git commit -m "refactor: Standardize API signatures across layers"

# Qwen
git commit -m "security: Fix [vulnerability] in [file]"
git commit -m "test: Add edge case tests for [scenario]"
```

### Questions/Blockers
Document in your progress reports and flag in commit messages.

---

## 💡 Why This Matters

**Empirica could be foundational** for AI development. If it's foundational, it must be:
- **Reliable:** No crashes from edge cases
- **Secure:** No vulnerabilities at scale
- **Consistent:** Predictable behavior everywhere
- **Maintainable:** No duplicate code to keep in sync

**This is not optional. This is what makes Empirica production-ready for serious use.**

---

**Let's make this bulletproof. 🛡️**
