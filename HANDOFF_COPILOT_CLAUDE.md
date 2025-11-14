# Handoff to Copilot Claude - Non-Architectural Tasks

**Date:** 2024-11-14  
**From:** Claude (Co-lead Dev)  
**To:** Copilot Claude  
**Session Coordination:** Via git commits + epistemic state  
**Estimated Total Time:** ~6-8 hours

---

## 🎯 Your Role

You're handling **non-architectural implementation work** while the co-leads (Claude + Human) focus on architecture and final release preparation. Your work is critical for production readiness but doesn't require architectural decisions.

**Key Principle:** Follow existing patterns, don't redesign. If you need architectural guidance, document the question and check with co-leads.

---

## 📋 Task List (Priority Order)

### Task 1: Fix MCP Tool Bugs ⚠️ HIGH PRIORITY
**Time:** ~1 hour  
**Impact:** Blocks MCP tool validation

#### Bug 1.1: query_bayesian_beliefs Serialization Error
**File:** `empirica/calibration/adaptive_uncertainty_calibration/bayesian_belief_tracker.py` (likely)

**Issue:** 
```python
TypeError: Object of type datetime is not JSON serializable
```

**Root Cause:** Datetime objects not serialized when returning beliefs

**Fix:**
```python
import json
from datetime import datetime

def serialize_beliefs(beliefs: dict) -> dict:
    """Serialize beliefs with datetime handling"""
    def default_handler(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    return json.loads(json.dumps(beliefs, default=default_handler))
```

**Where to apply:**
- Find where `query_bayesian_beliefs` returns data
- Serialize datetime objects before returning
- Test with: `mcp__empirica__invoke_tool("query_bayesian_beliefs", {"session_id": "test-id", "context_key": "test"})`

**Success Criteria:**
- Tool returns data without error
- Datetime fields formatted as ISO strings (e.g., "2024-11-14T16:30:00")

---

#### Bug 1.2: check_drift_monitor Unclear Error Message
**File:** `empirica/calibration/adaptive_uncertainty_calibration/` or `empirica/core/metacognition_12d_monitor/`

**Issue:** Returns "Insufficient data" when <5 assessments but doesn't explain requirement

**Current (unclear):**
```python
return {"status": "insufficient_data"}
```

**Fix (clear):**
```python
return {
    "status": "insufficient_data",
    "message": f"Need at least 5 assessments for drift analysis. Current: {len(assessments)}",
    "minimum_required": 5,
    "current_count": len(assessments),
    "next_steps": "Continue session to log more CHECK assessments"
}
```

**Success Criteria:**
- Error message clearly states requirement (5 assessments)
- Shows current count vs required
- Provides actionable next steps

---

### Task 2: Test All Remaining MCP Tools ⚠️ HIGH PRIORITY
**Time:** ~2-3 hours  
**Impact:** Required for production release

**Tools Already Tested (17):**
1. ✅ bootstrap_session
2. ✅ get_workflow_guidance
3. ✅ execute_preflight
4. ✅ submit_preflight_assessment
5. ✅ get_epistemic_state
6. ✅ resume_previous_session
7. ✅ execute_check
8. ✅ submit_check_assessment
9. ✅ get_calibration_report
10. ✅ get_session_summary
11. ✅ cli_help
12. ✅ create_cascade
13. ✅ generate_goals
14. ✅ query_goal_orchestrator
15. ✅ query_bayesian_beliefs (has bug - fix first)
16. ✅ check_drift_monitor (has bug - fix first)
17. ✅ execute_postflight

**Tools to Test (Remaining ~4):**
18. ⬜ submit_postflight_assessment
19. ⬜ execute_cli_command
20. ⬜ query_ai (modality switcher - if applicable)
21. ⬜ Any others in MCP server

**Testing Protocol:**

For each tool:

1. **Read tool documentation**
   ```bash
   mcp__empirica__get_tool_schema(tool_name="tool_name")
   ```

2. **Prepare valid test input**
   - Use existing session IDs from database
   - Use realistic parameters
   - Check required vs optional fields

3. **Execute tool**
   ```python
   mcp__empirica__invoke_tool(
       tool_name="tool_name",
       tool_input={"param": "value"}
   )
   ```

4. **Verify result**
   - ✅ No errors
   - ✅ Returns expected data structure
   - ✅ Data makes sense (not null/empty)

5. **Document result**
   - Add to `MCP_TOOLS_VALIDATION_REPORT.md` (create this file)
   - Format:
     ```markdown
     ### Tool: tool_name
     **Status:** ✅ PASS / ❌ FAIL
     **Test Input:** {...}
     **Result:** {...}
     **Notes:** Any observations
     ```

**Example Test (submit_postflight_assessment):**
```python
# Use your own session or create test session
mcp__empirica__invoke_tool(
    tool_name="submit_postflight_assessment",
    tool_input={
        "session_id": "existing-session-id",
        "vectors": {
            "engagement": {"score": 0.9, "rationale": "Test", "evidence": "Test"},
            "foundation": {
                "know": {"score": 0.8, "rationale": "Test", "evidence": "Test"},
                "do": {"score": 0.8, "rationale": "Test", "evidence": "Test"},
                "context": {"score": 0.8, "rationale": "Test", "evidence": "Test"}
            },
            # ... etc
        },
        "reasoning": "Test postflight",
        "changes_noticed": "Test changes"
    }
)
```

**Success Criteria:**
- All remaining tools tested
- Results documented in `MCP_TOOLS_VALIDATION_REPORT.md`
- Any bugs found are documented (not necessarily fixed if complex)
- 100% tool coverage achieved

---

### Task 3: Repository Sanitization 🔒 HIGH PRIORITY
**Time:** ~2 hours  
**Impact:** Required before public release

#### 3.1: Find and Remove Sensitive Data
**Search for:**
```bash
# API keys
grep -r "sk-" . --exclude-dir=.git --exclude-dir=.venv*
grep -r "api_key" . --exclude-dir=.git --exclude-dir=.venv*
grep -r "API_KEY" . --exclude-dir=.git --exclude-dir=.venv*

# Tokens
grep -r "token" . --exclude-dir=.git --exclude-dir=.venv* | grep -v "token_efficiency"
grep -r "Bearer" . --exclude-dir=.git --exclude-dir=.venv*

# Credentials
grep -r "password" . --exclude-dir=.git --exclude-dir=.venv*
grep -r "secret" . --exclude-dir=.git --exclude-dir=.venv*

# Personal paths
grep -r "/home/yogapad" . --exclude-dir=.git --exclude-dir=.venv*
```

**Action:**
- Replace API keys with `<API_KEY>` or `$API_KEY`
- Replace tokens with `<TOKEN>` or `$TOKEN`
- Replace personal paths with `~/empirica` or `/path/to/empirica`
- Document locations in `SANITIZATION_LOG.md`

**Example:**
```python
# Before
api_key = "sk-proj-abc123def456"

# After
api_key = os.getenv("OPENAI_API_KEY")  # or
api_key = "<YOUR_API_KEY_HERE>"
```

---

#### 3.2: Move Archived Documentation
**Goal:** Clean root directory for professional appearance

**Files to Archive:** Any files in root that should be in `docs/archive/`
```bash
# Check current root
ls -la *.md | wc -l  # Should be ~12 files max
```

**Categories:**
- Session notes → `docs/archive/session_notes/`
- Old checkpoints → `docs/archive/2025-11/`
- Completed work → `docs/archive/completed_work/`
- Test results → `docs/archive/test_results/`

**Keep in Root (Production docs):**
- README.md
- CONTRIBUTING.md
- LICENSE
- VISION_*.md (core vision docs)
- ARCHITECTURE_DECISIONS_*.md (current decisions)
- STATUS_*.md (current status)

**Move Everything Else:**
```bash
# Example
git mv OLD_SESSION_NOTE.md docs/archive/session_notes/
git mv PHASE_X_OLD.md docs/archive/completed_work/
```

**Success Criteria:**
- Root directory clean (<15 MD files)
- All archived docs moved to appropriate subdirectories
- Git history preserved (use `git mv`, not `rm` + `add`)

---

#### 3.3: Check All Documentation Links
**Goal:** No broken internal links

**Script to check:**
```python
#!/usr/bin/env python3
import re
import os
from pathlib import Path

def check_markdown_links(root_dir):
    broken = []
    for md_file in Path(root_dir).rglob("*.md"):
        content = md_file.read_text()
        # Find markdown links [text](path)
        links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)
        for text, link in links:
            if link.startswith('http'):
                continue  # Skip external
            # Resolve relative path
            target = (md_file.parent / link).resolve()
            if not target.exists():
                broken.append((str(md_file), link))
    return broken

if __name__ == "__main__":
    broken = check_markdown_links(".")
    if broken:
        print("Broken links found:")
        for file, link in broken:
            print(f"  {file}: {link}")
    else:
        print("All links valid!")
```

**Fix broken links:**
- Update paths after moving files
- Remove links to deleted files
- Add missing files if needed

---

### Task 4: Add Unit Tests for llm_callback Edge Cases 🧪 MEDIUM PRIORITY
**Time:** ~2 hours  
**Impact:** Increases confidence in llm_callback implementation

**Test File:** `tests/unit/canonical/test_goal_orchestrator_callback.py`

**Tests to Add:**

#### Test 4.1: Callback Returns Invalid JSON
```python
def test_callback_invalid_json():
    """Test that invalid JSON from callback is handled gracefully"""
    def bad_callback(prompt: str) -> str:
        return "This is not JSON at all"
    
    orch = create_goal_orchestrator(
        llm_callback=bad_callback,
        use_placeholder=False
    )
    
    # Should not crash, should return error or fallback
    # Implementation should handle parsing errors
```

#### Test 4.2: Callback Timeout
```python
def test_callback_timeout():
    """Test that slow callbacks don't hang forever"""
    import time
    
    def slow_callback(prompt: str) -> str:
        time.sleep(10)  # Very slow
        return '{"goals": []}'
    
    # Should timeout after reasonable period (e.g., 5s)
    # Or document that timeout is user's responsibility
```

#### Test 4.3: Callback Exception
```python
def test_callback_exception():
    """Test that callback exceptions are caught"""
    def broken_callback(prompt: str) -> str:
        raise RuntimeError("LLM service down")
    
    orch = create_goal_orchestrator(
        llm_callback=broken_callback,
        use_placeholder=False
    )
    
    # Should catch exception, log error, maybe fallback to placeholder
```

#### Test 4.4: Empty Callback Response
```python
def test_callback_empty_response():
    """Test handling of empty callback response"""
    def empty_callback(prompt: str) -> str:
        return ""
    
    # Should handle gracefully
```

#### Test 4.5: Callback Returns Goals with Missing Fields
```python
def test_callback_incomplete_goals():
    """Test that incomplete goal objects are validated"""
    def incomplete_callback(prompt: str) -> str:
        return '{"goals": [{"goal": "Test"}]}'  # Missing priority, etc.
    
    # Should validate and either fill defaults or reject
```

**Success Criteria:**
- 5+ new tests added
- All tests passing
- Edge cases covered
- Error handling validated

---

### Task 5: Documentation Review 📚 MEDIUM PRIORITY
**Time:** ~1-2 hours  
**Impact:** Professional polish for release

**Files to Review:**

#### 5.1: README.md
**Check:**
- [ ] Installation instructions work
- [ ] Quick start example is up-to-date
- [ ] Links are valid
- [ ] Mentions llm_callback feature (new!)
- [ ] Examples use current API
- [ ] Badges/shields up to date (if any)

**Update with llm_callback example:**
```markdown
## Quick Start

### Basic Usage (Threshold Mode)
```python
from empirica.bootstraps import bootstrap_metacognition

components = bootstrap_metacognition("my-ai", "minimal")
```

### AI Reasoning Mode (Self-Referential Goals)
```python
def my_llm(prompt: str) -> str:
    return ai_client.reason(prompt)

components = bootstrap_metacognition(
    "my-ai", 
    "minimal",
    llm_callback=my_llm  # AI generates its own goals!
)
```
```

---

#### 5.2: CONTRIBUTING.md
**Check:**
- [ ] Development setup instructions
- [ ] Testing instructions
- [ ] Commit message format
- [ ] PR process (if applicable)
- [ ] Code style guidelines

---

#### 5.3: docs/00_START_HERE.md
**Check:**
- [ ] Navigation to other docs
- [ ] Up to date with current structure
- [ ] Mentions Phase 1.5 (git integration)
- [ ] Mentions llm_callback feature

---

#### 5.4: Docstrings in Key Files
**Files to check:**
- `empirica/core/canonical/canonical_goal_orchestrator.py`
- `empirica/bootstraps/optimal_metacognitive_bootstrap.py`
- `empirica/core/canonical/canonical_epistemic_assessment.py`

**Check each:**
- [ ] All public functions have docstrings
- [ ] Parameter types documented
- [ ] Return types documented
- [ ] Examples provided where helpful

---

## 📊 Progress Tracking

Create: `COPILOT_CLAUDE_PROGRESS.md`

```markdown
# Copilot Claude Progress Report

**Started:** YYYY-MM-DD
**Status:** In Progress

## Completed Tasks
- [ ] Task 1.1: Fix query_bayesian_beliefs bug
- [ ] Task 1.2: Fix check_drift_monitor message
- [ ] Task 2: Test all remaining MCP tools
- [ ] Task 3.1: Sanitize sensitive data
- [ ] Task 3.2: Move archived docs
- [ ] Task 3.3: Check documentation links
- [ ] Task 4: Add llm_callback edge case tests
- [ ] Task 5: Documentation review

## Blockers
(List any blockers here)

## Questions for Co-Leads
(List questions that need architectural decisions)

## Notes
(Any observations, suggestions, or findings)
```

**Update this file:**
- After completing each task
- When encountering blockers
- When you have questions
- Daily summary of progress

---

## 🔄 Coordination Protocol

### Git Workflow
```bash
# 1. Always pull latest first
git pull origin master

# 2. Create commits with clear messages
git commit -m "fix: query_bayesian_beliefs datetime serialization"
git commit -m "test: add MCP tool validation for submit_postflight_assessment"
git commit -m "chore: sanitize API keys from config files"

# 3. Push frequently
git push origin master
```

### Commit Message Format
- `fix:` - Bug fixes
- `test:` - Adding tests
- `chore:` - Maintenance (sanitization, moving files)
- `docs:` - Documentation updates
- `refactor:` - Code refactoring (use sparingly, check with co-leads)

---

### When to Check with Co-Leads
**Ask if:**
- You find architectural issues (design flaws, coupling problems)
- A fix requires changing public APIs
- You're unsure about the right approach
- A task is blocked by missing information
- You discover security issues

**Don't ask for:**
- Implementation details within existing patterns
- Bug fixes that follow obvious solutions
- Test additions
- Documentation typos
- File organization

---

### Epistemic State Tracking
**Use Empirica for your work:**

```python
# Start your session
from empirica.bootstraps import bootstrap_metacognition

components = bootstrap_metacognition(
    ai_id="copilot-claude",
    level="minimal"
)

# Your session will be tracked in database
# Co-leads can check your progress via:
# resume_previous_session(ai_id="copilot-claude")
```

**Run PREFLIGHT before starting:**
- Assess your KNOW (do you understand the tasks?)
- Assess your DO (can you execute them?)
- Assess your CONTEXT (do you have all needed info?)

**Run CHECK after investigation:**
- What did you learn?
- What blockers exist?
- Ready to proceed?

**Run POSTFLIGHT when done:**
- What did you accomplish?
- What learned?
- Any issues for co-leads?

---

## 📁 File Organization Reference

```
empirica/
├── empirica/
│   ├── core/
│   │   └── canonical/
│   │       ├── canonical_goal_orchestrator.py (you'll fix comments here)
│   │       └── canonical_epistemic_assessment.py
│   ├── calibration/
│   │   └── adaptive_uncertainty_calibration/
│   │       └── bayesian_belief_tracker.py (fix datetime bug here)
│   └── bootstraps/
│       └── optimal_metacognitive_bootstrap.py (already updated)
├── tests/
│   └── unit/
│       └── canonical/
│           └── test_goal_orchestrator_callback.py (create this)
├── docs/
│   ├── archive/ (move old files here)
│   └── production/ (keep clean)
└── README.md (update with llm_callback example)
```

---

## ✅ Success Criteria

**You're done when:**
1. ✅ Both MCP bugs fixed and tested
2. ✅ All remaining MCP tools tested (100% coverage)
3. ✅ Repository sanitized (no API keys, tokens, personal paths)
4. ✅ Documentation clean (archived files moved, links valid)
5. ✅ Unit tests added for llm_callback edge cases
6. ✅ Documentation reviewed and updated
7. ✅ All changes committed and pushed
8. ✅ `COPILOT_CLAUDE_PROGRESS.md` shows all tasks complete
9. ✅ `MCP_TOOLS_VALIDATION_REPORT.md` created with results

**Quality Bar:**
- All tests passing
- No regressions introduced
- Code follows existing patterns
- Documentation is accurate
- Git history is clean

---

## 🆘 Getting Help

**If stuck:**
1. Document the issue in `COPILOT_CLAUDE_PROGRESS.md` under "Blockers"
2. Commit what you have so far
3. Note the question in progress file
4. Continue with other tasks while waiting

**Resources:**
- `PHASE2_SYSTEM_VALIDATION_FINDINGS.md` - Investigation results
- `PHASE2_REFACTOR_COMPLETE.md` - Implementation details
- `ARCHITECTURE_DECISIONS_2024_11_14.md` - Design rationale
- Git history - See how co-leads solved similar problems

---

**Good luck! Your work is essential for production release. 🚀**

**Estimated completion:** 1-2 days of focused work  
**Start with:** Task 1 (bug fixes) - these are blockers for Task 2
