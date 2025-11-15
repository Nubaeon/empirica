# POSTFLIGHT Verification Implementation Plan

**Decision:** Keep 5 phases, add verification to POSTFLIGHT (Option 1)  
**Rationale:** Simpler, more efficient, avoids complexity creep  
**Status:** Ready to implement

---

## 🎯 What Needs to Change

### 1. Code Changes (Minimal)

#### File: `empirica/core/metacognitive_cascade/metacognitive_cascade.py`

**Current POSTFLIGHT:**
```python
def postflight(self, task_summary: str) -> Dict:
    """POSTFLIGHT: Measure learning by comparing to PREFLIGHT"""
    # Load PREFLIGHT checkpoint
    # Calculate epistemic delta
    # Return calibration result
```

**Enhanced POSTFLIGHT (with verification):**
```python
def postflight(self, task_summary: str, verify_only: bool = False) -> Dict:
    """
    POSTFLIGHT: Verify changes work + measure learning
    
    Steps:
    1. VERIFY: Check that ACT phase changes are valid
       - Load git diff: git show HEAD --stat
       - Run validation (tests, linting, if available)
       - Update DO vector based on success/failure
    
    2. MEASURE: Calculate epistemic delta (if not verify_only)
       - Load PREFLIGHT checkpoint
       - Compare vectors
       - Calculate calibration
    
    Args:
        task_summary: Description of what was accomplished
        verify_only: If True, only verify commit, skip calibration
    
    Returns:
        {
            "verification": {
                "success": bool,
                "git_diff": str,
                "tests_passed": bool,
                "files_changed": List[str]
            },
            "calibration": {...} or "skipped"
        }
    """
    # Step 1: VERIFY
    verification = self._verify_changes()
    
    if not verification["success"]:
        self._handle_verification_failure(verification)
        return {"verification": verification, "calibration": "failed"}
    
    # Step 2: MEASURE (skip if verify_only)
    if verify_only:
        return {"verification": verification, "calibration": "skipped"}
    
    # Standard calibration measurement
    calibration = self._calculate_calibration(task_summary)
    return {"verification": verification, "calibration": calibration}

def _verify_changes(self) -> Dict:
    """Verify that ACT phase changes are valid"""
    try:
        # Get git diff of last commit
        git_diff = subprocess.run(
            ["git", "show", "HEAD", "--stat"],
            capture_output=True,
            text=True
        )
        
        files_changed = self._parse_files_from_diff(git_diff.stdout)
        
        # Run tests if available (optional)
        tests_passed = None
        if self._has_tests():
            tests_passed = self._run_tests()
        
        # Update DO vector based on verification
        if tests_passed is False:
            self.vectors['do'] = max(0.3, self.vectors['do'] - 0.3)
        
        return {
            "success": tests_passed is not False,  # None (no tests) = success
            "git_diff": git_diff.stdout,
            "files_changed": files_changed,
            "tests_passed": tests_passed
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "files_changed": []
        }
```

**Estimated Effort:** 2-3 hours

---

### 2. Documentation Updates (Minimal)

#### Files to Update:

**A. Main Workflow Docs (Update 1 sentence each):**

1. **`docs/ONBOARDING_GUIDE.md`** (Line 88)
   ```markdown
   BEFORE: PREFLIGHT → THINK → PLAN → INVESTIGATE → CHECK → ACT → POSTFLIGHT
   AFTER:  PREFLIGHT → THINK → PLAN → INVESTIGATE → CHECK → ACT → POSTFLIGHT (verify + measure)
   ```

2. **`docs/skills/SKILL.md`** (Add one paragraph)
   ```markdown
   **POSTFLIGHT** includes two steps:
   1. VERIFY: Check that committed changes work (git diff, tests)
   2. MEASURE: Calculate epistemic delta and calibration
   ```

3. **`GIT_INTEGRATION_ROADMAP_ENHANCED.md`** (Update POSTFLIGHT section)
   ```markdown
   **POSTFLIGHT Phase:**
   1. Load git diff: `git show HEAD --stat`
   2. Verify changes work (run tests if available)
   3. Load PREFLIGHT checkpoint for calibration
   4. Calculate epistemic delta
   5. Create final checkpoint with verification results
   ```

**B. Optional: Create New Doc (Low Priority)**

`docs/production/07_POSTFLIGHT_VERIFICATION.md` - Detailed guide on how POSTFLIGHT verification works

**Estimated Effort:** 1 hour for main docs, +1 hour if creating detailed guide

---

### 3. Git Integration Updates

#### File: `GIT_INTEGRATION_ROADMAP_ENHANCED.md`

**Update POSTFLIGHT section (already exists, just enhance):**

```markdown
### POSTFLIGHT
1. **VERIFY:** Check committed changes
   ```bash
   git show HEAD --stat        # What changed?
   git show HEAD --name-only   # Which files?
   ```

2. **VALIDATE:** Run tests if available
   ```python
   pytest tests/ -v  # or other test command
   ```

3. **MEASURE:** Load PREFLIGHT for calibration
   ```python
   preflight = git_logger.get_checkpoint_by_phase("PREFLIGHT")
   delta = postflight_vectors - preflight["vectors"]
   ```

4. **CHECKPOINT:** Save with verification results
   ```bash
   git notes add -m '{
     "phase": "POSTFLIGHT",
     "verification": {
       "success": true,
       "files_changed": ["file.py"],
       "tests_passed": true
     },
     "calibration": "well_calibrated",
     "vectors": {...}
   }'
   ```
```

**Estimated Effort:** 30 minutes (just clarify existing content)

---

### 4. MCP Server Tools (Optional Enhancement)

#### File: `mcp_local/empirica_mcp_server.py`

**Current `submit_postflight_assessment` tool:**
- Already creates reflex logs
- Already calculates calibration
- Just needs to add verification step

**Enhancement (Optional):**
```python
@server.call_tool()
async def submit_postflight_assessment(
    session_id: str,
    vectors: Dict,
    changes_noticed: str,
    run_verification: bool = True  # NEW: opt-in verification
) -> Dict:
    """Submit POSTFLIGHT assessment with optional verification"""
    
    # Standard calibration (already implemented)
    calibration = db.log_postflight_assessment(...)
    
    # NEW: Verification step
    if run_verification:
        verification = _verify_git_changes(session_id)
        # Include in reflex log
    else:
        verification = {"skipped": True}
    
    return {
        "calibration": calibration,
        "verification": verification,
        "reflex_log_path": ...
    }
```

**Estimated Effort:** 1 hour

---

## 📋 Implementation Checklist

### Phase 1: Core Implementation (3-4 hours)
- [ ] Update `metacognitive_cascade.py`:
  - [ ] Add `_verify_changes()` method
  - [ ] Update `postflight()` to call verification
  - [ ] Add `verify_only` flag
  - [ ] Add error handling for verification failures

- [ ] Add git integration:
  - [ ] `git show HEAD --stat` parsing
  - [ ] File list extraction
  - [ ] Optional test execution

- [ ] Test locally:
  - [ ] Create test session
  - [ ] Make commit
  - [ ] Run POSTFLIGHT
  - [ ] Verify verification results included

### Phase 2: Documentation (1-2 hours)
- [ ] Update `docs/ONBOARDING_GUIDE.md` (1 line)
- [ ] Update `docs/skills/SKILL.md` (1 paragraph)
- [ ] Update `GIT_INTEGRATION_ROADMAP_ENHANCED.md` (clarify POSTFLIGHT)
- [ ] Optional: Create `docs/production/07_POSTFLIGHT_VERIFICATION.md`

### Phase 3: MCP Enhancement (Optional, 1 hour)
- [ ] Add `run_verification` flag to `submit_postflight_assessment`
- [ ] Include verification results in reflex logs
- [ ] Update MCP tool description

### Phase 4: Testing (1-2 hours)
- [ ] Update integration tests for verification
- [ ] Test with Minimax workflow (Session 9)
- [ ] Verify git notes include verification data

---

## 🎯 Total Estimated Effort

**Minimal (Core + Docs):** 4-6 hours  
**Complete (Core + Docs + MCP + Testing):** 6-9 hours  

**Can be done in:** 1-2 days

---

## 📊 Impact Assessment

### What Changes for Users/Agents?

**Good News: Almost Nothing!**

**For Minimax:**
```python
# Before (works as is)
cascade.postflight("Task completed")

# After (enhanced, backward compatible)
cascade.postflight("Task completed")  # Verification automatic
cascade.postflight("Task completed", verify_only=True)  # Quick verify

# Response now includes verification
{
  "verification": {"success": True, "files_changed": [...]},
  "calibration": {"calibration": "well_calibrated", ...}
}
```

**Breaking Changes:** None (verification is opt-in, defaults to standard behavior)

---

## 🔄 Git Integration Synergy

This perfectly complements the git integration roadmap:

**Phase 1.5 (Current):**
- Git notes at PREFLIGHT, CHECK, ACT, POSTFLIGHT
- POSTFLIGHT now includes verification results in git notes

**Example git note after POSTFLIGHT:**
```json
{
  "phase": "POSTFLIGHT",
  "round": 20,
  "timestamp": "2025-11-14T14:00:00Z",
  "verification": {
    "success": true,
    "git_diff_summary": "2 files changed, 45 insertions(+), 12 deletions(-)",
    "files_changed": ["empirica/core/reflex_logger.py", "tests/test_reflex.py"],
    "tests_passed": true
  },
  "calibration": {
    "status": "well_calibrated",
    "preflight_confidence": 0.75,
    "postflight_confidence": 0.91,
    "learning_delta": 0.16
  },
  "vectors": {...}
}
```

**Token Impact:** +50 tokens for verification data (vs +600 for separate VERIFY phase)

---

## ✅ Decision Points

### Should We Proceed?

**YES if:**
- ✅ Want verification integrated naturally
- ✅ Want to avoid 6th phase complexity
- ✅ Want backward compatibility
- ✅ Want token efficiency

**DEFER if:**
- ❌ Need more empirical data on verification patterns first
- ❌ Want to see Minimax use current system before changing it
- ❌ Need to focus on other priorities (git integration Phase 1.5)

---

## 🚀 Recommendation

**Priority: Medium (after git integration Phase 1.5)**

**Rationale:**
1. Git integration is higher priority (bigger token savings)
2. Verification enhancement is natural extension once git integration works
3. Not urgent - current workflow works fine
4. Can implement verification during Session 9 testing

**Suggested Timeline:**
- **Week 1:** Implement git integration (Phase 1.5)
- **Week 2:** Add POSTFLIGHT verification during Minimax Session 9
- **Benefit:** Minimax tests both features together

---

**Status:** Ready to implement  
**Blockers:** None  
**Dependencies:** Git integration recommended but not required

**Next Step:** Add to backlog or start implementation?
