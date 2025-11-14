# Handoff: Phase 1.5 Git Integration Implementation

**Assigned To:** Claude (Implementation Agent)  
**Assigned By:** Claude (Co-lead Developer) + Developer  
**Date:** 2024-11-14  
**Estimated Time:** 6-9 hours (1 day)  
**Priority:** High (blocks Minimax Session 9 token efficiency testing)

---

## 🎯 Mission

Implement git-backed context retrieval to achieve **80-90% token reduction** for AI agents like Minimax.

**Current Problem:** Minimax uses ~19,000 tokens/session loading full context from SQLite  
**Target Solution:** Load compressed checkpoints from git notes (~3,000 tokens/session)  
**Your Job:** Build the infrastructure to enable and measure this

---

## 📚 Context Documents (Read These First)

**Primary Spec (MUST READ):**
- `GIT_INTEGRATION_ROADMAP_ENHANCED.md` - Complete architecture and requirements (819 lines)

**Supporting Docs:**
- `POSTFLIGHT_VERIFICATION_IMPLEMENTATION.md` - Related workflow enhancement (for context)
- `empirica/data/session_database.py` - Current database layer (lines 1-1230)
- `empirica/core/canonical/reflex_logger.py` - Current reflex logger (lines 1-200)

**Key Sections in Roadmap:**
- Lines 45-180: GitEnhancedReflexLogger specification
- Lines 182-290: TokenEfficiencyMetrics specification
- Lines 292-390: Minimax integration instructions
- Lines 585-680: Implementation timeline and tasks

---

## ✅ Deliverables

### 1. GitEnhancedReflexLogger Class
**File:** `empirica/core/canonical/git_enhanced_reflex_logger.py` (NEW)

**Requirements:**
- Extends existing `ReflexLogger` (backward compatible)
- Hybrid storage: SQLite + git notes
- Opt-in via `enable_git_notes=False` default
- Falls back to SQLite if git unavailable
- Creates compressed checkpoints (~450 tokens vs ~6,500)

**Key Methods (from spec lines 45-180):**
```python
class GitEnhancedReflexLogger(ReflexLogger):
    def __init__(self, session_id: str, enable_git_notes: bool = False)
    def _check_git_available(self) -> bool
    def _add_git_checkpoint(phase, round, vectors, metadata) -> Optional[str]
    def get_last_checkpoint(max_age_hours=24) -> Optional[Dict]
    def get_vector_diff(since_checkpoint) -> Dict
    def _git_add_note(checkpoint) -> str
    def _git_get_latest_note() -> Optional[Dict]
```

**Git Commands to Use:**
- `git notes add -m '{"phase": "PREFLIGHT", ...}'` - Add checkpoint
- `git notes show HEAD` - Retrieve latest checkpoint
- `git log --notes` - Query checkpoint history

**Safety Requirements:**
- Validate git repo exists before operations
- Never fail if git unavailable (fall back to SQLite)
- Validate JSON before writing to git notes
- Handle subprocess errors gracefully

---

### 2. TokenEfficiencyMetrics Class
**File:** `empirica/metrics/token_efficiency.py` (NEW, create directory if needed)

**Requirements:**
- Measure token usage per workflow phase
- Compare baseline (prompt-based) vs target (git-based)
- Generate efficiency reports with % reduction and cost savings
- Export to JSON, CSV, and Markdown formats

**Key Methods (from spec lines 182-290):**
```python
class TokenEfficiencyMetrics:
    def __init__(self, session_id: str)
    def measure_context_load(phase, method, content) -> Dict
    def compare_efficiency(baseline_session) -> Dict
    def export_report(format="json") -> str
    def _count_tokens(text) -> int
```

**Token Counting:**
- Use simple approximation: `len(text.split()) * 1.3`
- (Production will use tiktoken, but not needed for Phase 1.5)

**Metrics to Track:**
```python
{
    "phase": "PREFLIGHT",
    "method": "git",  # or "prompt"
    "tokens": 453,
    "timestamp": "2024-11-14T12:00:00Z",
    "content_type": "checkpoint"
}
```

---

### 3. Integration with Existing Code
**File:** `empirica/core/metacognitive_cascade/metacognitive_cascade.py` (UPDATE)

**Changes Needed:**
- Add optional `enable_git_notes` parameter to `__init__`
- Replace `ReflexLogger()` with `GitEnhancedReflexLogger()` when enabled
- Add `TokenEfficiencyMetrics` initialization
- Update `preflight()` to load from git checkpoint
- Update `check()` to use vector diff
- See spec lines 400-520 for detailed code examples

**Backward Compatibility:**
- Default: `enable_git_notes=False` (current behavior)
- When False: Uses standard ReflexLogger (no changes)
- When True: Uses GitEnhancedReflexLogger (new behavior)

---

### 4. Unit Tests
**File:** `tests/unit/test_git_enhanced_reflex_logger.py` (NEW)

**Minimum 6 Tests:**
```python
def test_git_available_check()
def test_add_git_checkpoint_success()
def test_add_git_checkpoint_fallback_when_git_unavailable()
def test_get_last_checkpoint_from_git()
def test_get_last_checkpoint_fallback_to_sqlite()
def test_get_vector_diff_calculation()
```

**File:** `tests/unit/test_token_efficiency_metrics.py` (NEW)

**Minimum 4 Tests:**
```python
def test_measure_context_load()
def test_token_counting_approximation()
def test_compare_efficiency()
def test_export_report_json()
```

---

### 5. Minimax Session 9 Instructions
**File:** `MINIMAX_SESSION9_GIT_INTEGRATION_TEST.md` (NEW)

**Content:**
- Modified workflow instructions (how to use git checkpoints)
- Git commands reference (git notes operations)
- Success criteria (>70% token reduction)
- Troubleshooting guide
- See spec lines 292-390 for template

**Key Sections:**
```markdown
## Modified Workflow:

### PREFLIGHT
1. Load checkpoint: `git_logger.get_last_checkpoint()`
2. Self-assess as normal
3. Create checkpoint: `git notes add -m '{...}'`
4. Measure tokens: `metrics.measure_context_load("PREFLIGHT", "git", checkpoint)`

### CHECK
1. Load vector diff: `git_logger.get_vector_diff(last_checkpoint)`
2. Self-assess decision
3. Create checkpoint

### ACT
1. Make changes + commit
2. Attach git note: `git notes add -m '{...}'`

### POSTFLIGHT
1. Generate efficiency report: `metrics.compare_efficiency("session-5")`
2. Save to: `docs/metrics/session_9_token_efficiency.md`
```

---

## 🚀 Implementation Workflow (Use Empirica!)

### PREFLIGHT
**Task:** Read specs, assess complexity, plan implementation

**Self-Assessment Questions:**
- Do I understand the git notes API?
- Do I know the ReflexLogger interface to extend?
- Am I confident I can implement in 6-9 hours?
- What are my knowledge gaps?

**Expected Vectors:**
- KNOW: 0.6-0.7 (understand concept, need to read existing code)
- DO: 0.7-0.8 (straightforward implementation)
- UNCERTAINTY: 0.3-0.4 (well-specified, some unknowns)

**Output:** Create PREFLIGHT checkpoint (your baseline for POSTFLIGHT calibration)

---

### INVESTIGATE
**Tasks:**
1. Read `empirica/core/canonical/reflex_logger.py` (~200 lines)
2. Read `empirica/data/session_database.py` checkpoint methods
3. Test git notes commands locally:
   ```bash
   git notes add -m '{"test": "checkpoint"}'
   git notes show HEAD
   git notes list
   ```
4. Understand ReflexFrame format (check existing reflex logs)

**Questions to Answer:**
- How does current ReflexLogger create reflex frames?
- What's the ReflexFrame JSON structure?
- Where is `log_preflight_assessment()` called from?
- Does git repo always exist? (check .git folder)

**Output:** Notes on integration points and design decisions

---

### CHECK
**Decision Gate:** Am I ready to implement?

**Self-Assessment:**
- Do I understand all the interfaces?
- Have I tested git commands?
- Do I know where to integrate?
- Am I confident in the approach?

**If NO:** Go back to INVESTIGATE  
**If YES:** Proceed to ACT

**Expected Confidence:** 0.8-0.9 to proceed

---

### ACT
**Implementation Order:**

#### Round 1-2: GitEnhancedReflexLogger Core (2 hours)
```bash
# Create file
touch empirica/core/canonical/git_enhanced_reflex_logger.py

# Implement:
# - __init__ with enable_git_notes flag
# - _check_git_available()
# - Basic ReflexLogger extension
# - Test git availability

git add empirica/core/canonical/git_enhanced_reflex_logger.py
git commit -m "feat: Add GitEnhancedReflexLogger skeleton with git availability check"
git notes add -m '{"phase": "ACT", "round": 1, "task": "logger_skeleton"}'
```

#### Round 3-4: Git Notes Operations (2 hours)
```bash
# Implement:
# - _add_git_checkpoint()
# - _git_add_note()
# - _git_get_latest_note()
# - get_last_checkpoint()

git add empirica/core/canonical/git_enhanced_reflex_logger.py
git commit -m "feat: Implement git notes checkpoint creation and retrieval"
git notes add -m '{"phase": "ACT", "round": 3, "task": "git_notes_ops"}'
```

#### Round 5-6: Vector Diff & Fallback (1.5 hours)
```bash
# Implement:
# - get_vector_diff()
# - SQLite fallback logic
# - Error handling

git commit -m "feat: Add vector diff calculation and SQLite fallback"
git notes add -m '{"phase": "ACT", "round": 5, "task": "diff_fallback"}'
```

#### Round 7-8: TokenEfficiencyMetrics (2 hours)
```bash
# Create directory
mkdir -p empirica/metrics

# Implement TokenEfficiencyMetrics class
touch empirica/metrics/__init__.py
touch empirica/metrics/token_efficiency.py

git add empirica/metrics/
git commit -m "feat: Add TokenEfficiencyMetrics for measuring token usage"
git notes add -m '{"phase": "ACT", "round": 7, "task": "token_metrics"}'
```

#### Round 9-10: Integration (1 hour)
```bash
# Update metacognitive_cascade.py
# - Add enable_git_notes parameter
# - Use GitEnhancedReflexLogger conditionally
# - Add TokenEfficiencyMetrics initialization

git add empirica/core/metacognitive_cascade/metacognitive_cascade.py
git commit -m "feat: Integrate GitEnhancedReflexLogger into metacognitive cascade"
git notes add -m '{"phase": "ACT", "round": 9, "task": "integration"}'
```

#### Round 11-14: Tests (2-3 hours)
```bash
# Write all unit tests
# Run: pytest tests/unit/test_git_enhanced_reflex_logger.py -v
# Run: pytest tests/unit/test_token_efficiency_metrics.py -v

git add tests/unit/test_git_enhanced_reflex_logger.py
git add tests/unit/test_token_efficiency_metrics.py
git commit -m "test: Add comprehensive tests for git integration"
git notes add -m '{"phase": "ACT", "round": 11, "task": "tests"}'
```

#### Round 15: Documentation (30 min)
```bash
# Create Minimax Session 9 instructions
touch MINIMAX_SESSION9_GIT_INTEGRATION_TEST.md

git add MINIMAX_SESSION9_GIT_INTEGRATION_TEST.md
git commit -m "docs: Add Minimax Session 9 git integration test instructions"
git notes add -m '{"phase": "ACT", "round": 15, "task": "minimax_instructions"}'
```

---

### POSTFLIGHT
**Measure Learning:**

Compare your PREFLIGHT assessment to actual results:
- Did KNOW increase? (Did you learn the codebase?)
- Did UNCERTAINTY decrease? (Were unknowns resolved?)
- Was DO accurate? (Could you implement in expected time?)
- Were you well-calibrated?

**Create Efficiency Report:**
```python
# Test token efficiency locally
from empirica.metrics.token_efficiency import TokenEfficiencyMetrics
metrics = TokenEfficiencyMetrics("test-session")

# Simulate PREFLIGHT load
checkpoint = git_logger.get_last_checkpoint()
metrics.measure_context_load("PREFLIGHT", "git", json.dumps(checkpoint))

# Report expected: ~450 tokens (vs baseline 6,500)
print(metrics.export_report("markdown"))
```

**Output:** POSTFLIGHT assessment + token efficiency preview

---

## ✅ Success Criteria

### Code Quality:
- [ ] All code follows PEP 8 style
- [ ] Type hints used throughout
- [ ] Docstrings for all public methods
- [ ] Error handling for all git operations
- [ ] Backward compatible (enable_git_notes=False works)

### Functionality:
- [ ] GitEnhancedReflexLogger creates git notes
- [ ] Checkpoints are ~450 tokens (not 6,500)
- [ ] SQLite fallback works when git unavailable
- [ ] TokenEfficiencyMetrics measures tokens correctly
- [ ] Integration with metacognitive_cascade works

### Testing:
- [ ] All 10 unit tests pass
- [ ] Manual testing: create checkpoint, retrieve it
- [ ] Git notes visible with `git notes list`
- [ ] No errors when git unavailable

### Documentation:
- [ ] Minimax Session 9 instructions complete
- [ ] Code comments explain git operations
- [ ] Docstrings reference spec document

---

## 📊 Expected Results

**Token Compression:**
```
Phase          | Before (SQLite) | After (Git) | Reduction
---------------|-----------------|-------------|----------
PREFLIGHT      | 6,500 tokens    | 450 tokens  | -93%
CHECK          | 3,500 tokens    | 400 tokens  | -89%
ACT            | 1,500 tokens    | 500 tokens  | -67%
POSTFLIGHT     | 5,500 tokens    | 850 tokens  | -85%
---------------|-----------------|-------------|----------
TOTAL/SESSION  | 19,000 tokens   | 3,000       | -84%
```

**Checkpoint Format:**
```json
{
  "session_id": "test-session",
  "phase": "PREFLIGHT",
  "round": 5,
  "timestamp": "2024-11-14T12:00:00Z",
  "vectors": {
    "know": 0.85, "do": 0.90, "uncertainty": 0.25,
    "engagement": 0.95, "context": 0.80, ...
  },
  "overall_confidence": 0.847,
  "meta": {
    "token_count": 453,
    "storage": "git_notes"
  }
}
```

---

## ⚠️ Common Pitfalls

### 1. Git Not Available
**Issue:** Some environments don't have git  
**Solution:** Always check with `_check_git_available()`, fallback to SQLite

### 2. Git Notes Conflicts
**Issue:** Multiple notes on same commit  
**Solution:** Use `git notes add` (creates new), not `git notes append`

### 3. JSON Formatting
**Issue:** Git notes don't parse as JSON  
**Solution:** Validate JSON before writing with `json.loads(json.dumps(checkpoint))`

### 4. Subprocess Errors
**Issue:** `subprocess.run()` throws exceptions  
**Solution:** Always use try/except, check `returncode`, handle `CalledProcessError`

### 5. Token Count Accuracy
**Issue:** Simple word count isn't accurate  
**Solution:** Use `len(text.split()) * 1.3` approximation (good enough for Phase 1.5)

---

## 🔍 Testing Checklist

**Before Committing:**
```bash
# Run all tests
pytest tests/unit/test_git_enhanced_reflex_logger.py -v
pytest tests/unit/test_token_efficiency_metrics.py -v

# Check code style
flake8 empirica/core/canonical/git_enhanced_reflex_logger.py
flake8 empirica/metrics/token_efficiency.py

# Test git notes manually
python3 -c "
from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
logger = GitEnhancedReflexLogger('test', enable_git_notes=True)
logger._add_git_checkpoint('TEST', 1, {'know': 0.8}, {})
print('✓ Git checkpoint created')
"

# Verify git note exists
git notes list

# Verify fallback works
python3 -c "
from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
logger = GitEnhancedReflexLogger('test', enable_git_notes=False)
checkpoint = logger.get_last_checkpoint()
print('✓ Fallback works')
"
```

---

## 📝 Handoff Back to Co-Lead

**When Complete, Create:**

`PHASE1.5_IMPLEMENTATION_COMPLETE.md`:
```markdown
# Phase 1.5 Implementation Complete

## Summary
- ✅ GitEnhancedReflexLogger implemented (X lines)
- ✅ TokenEfficiencyMetrics implemented (X lines)
- ✅ Integration with metacognitive_cascade complete
- ✅ 10 unit tests passing
- ✅ Minimax Session 9 instructions created

## Token Efficiency Preview
- Checkpoint size: X tokens (target: ~450)
- Reduction: X% (target: >80%)

## Files Changed:
- empirica/core/canonical/git_enhanced_reflex_logger.py (NEW, X lines)
- empirica/metrics/token_efficiency.py (NEW, X lines)
- empirica/core/metacognitive_cascade/metacognitive_cascade.py (UPDATED)
- tests/unit/test_git_enhanced_reflex_logger.py (NEW)
- tests/unit/test_token_efficiency_metrics.py (NEW)
- MINIMAX_SESSION9_GIT_INTEGRATION_TEST.md (NEW)

## POSTFLIGHT Assessment:
[Your epistemic delta measurements]

## Ready for:
- Code review by co-lead
- Minimax Session 9 testing
- Token efficiency measurement
```

**Tag me:** @claude-colead-dev for review

---

## 🎯 Timeline

**Estimated:** 6-9 hours (1 working day)

**Breakdown:**
- Read specs & investigate: 1-2 hours
- GitEnhancedReflexLogger: 3-4 hours
- TokenEfficiencyMetrics: 1-2 hours
- Integration: 1 hour
- Tests: 2-3 hours
- Documentation: 0.5 hour

**Realistic:** Start today, finish tomorrow

---

## 💬 Questions?

If anything is unclear:
1. Check `GIT_INTEGRATION_ROADMAP_ENHANCED.md` (most answers there)
2. Check existing code (reflex_logger.py, session_database.py)
3. Test git commands manually to understand behavior
4. Ask in handoff message if still unclear

---

## 🎓 Learning Goals

By completing this task, you will:
- Understand git notes API and use cases
- Practice extending existing classes (ReflexLogger)
- Learn token efficiency measurement techniques
- Experience Empirica workflow firsthand (PREFLIGHT→POSTFLIGHT)
- Contribute to a production system with real impact

**This is meaningful work!** The token efficiency you enable will:
- Reduce costs for all AI agents
- Enable longer working sessions
- Provide data for architecture decisions
- Scale to the entire Empirica ecosystem

---

**Ready to start? Let's ship this! 🚀**

**Status:** Ready for assignment  
**Assigned To:** [Your name]  
**Start Date:** 2024-11-14  
**Expected Completion:** 2024-11-15  

**Good luck!** Remember to use the Empirica workflow yourself - it's designed for exactly this type of implementation task.
