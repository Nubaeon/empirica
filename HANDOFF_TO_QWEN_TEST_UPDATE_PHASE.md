# Handoff to Qwen: Test Update Phase

**Date:** 2025-12-04
**Prepared by:** Claude Code
**Status:** Ready for Qwen's test updates
**Estimated Scope:** 4 deprecated test files + 3 new test suites

---

## Executive Summary

Sonnet has completed:
1. ✅ Database schema migration (4 deprecated tables → 1 reflexes table)
2. ✅ Production documentation updates (5 critical + 3 additional docs)
3. ✅ Bootstrap command cleanup (complete removal, no deprecation shims)

**Your job:** Update tests to use the new reflexes table API and add comprehensive test coverage for new functionality.

---

## Part 1: Fix 4 Deprecated Test Files

### Overview

These 4 test files are currently calling deprecated methods that no longer exist:
- `log_preflight_assessment()` → Use `store_vectors()` to reflexes table
- `log_postflight_assessment()` → Use `store_vectors()` to reflexes table
- `log_check_assessment()` → Use `store_vectors()` to reflexes table
- References to old tables: `preflight_assessments`, `postflight_assessments`, `check_phase_assessments`, `epistemic_assessments`

---

## File 1: `tests/integration/test_reflex_logging_integration.py`

**Current Status:** ❌ Broken (uses deprecated `log_preflight_assessment()`)

**Issue:**
```python
# Line 40-46: Calls non-existent method
assessment_id = db.log_preflight_assessment(
    session_id=session_id,
    cascade_id=None,
    prompt_summary="Test PREFLIGHT",
    vectors=vectors,
    uncertainty_notes="Test"
)

# Line 52: Queries deprecated table
cursor.execute("SELECT know, do, uncertainty FROM preflight_assessments WHERE assessment_id = ?", ...)
```

**Fix:**
```python
# Use GitEnhancedReflexLogger instead
from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger

logger = GitEnhancedReflexLogger(session_id=session_id, enable_git_notes=True)

# Store to reflexes table
logger.add_checkpoint(
    phase="PREFLIGHT",
    round_num=1,
    vectors=vectors,
    metadata={"prompt_summary": "Test PREFLIGHT", "cascade_id": None}
)

# Query reflexes table instead
cursor.execute("""
    SELECT know, do, uncertainty FROM reflexes
    WHERE session_id = ? AND phase = 'PREFLIGHT'
""", (session_id,))
```

**What to Update:**
- [ ] Replace all `db.log_*_assessment()` calls with `GitEnhancedReflexLogger`
- [ ] Update all SQL queries to query `reflexes` table
- [ ] Change column names: `assessment_id` → `reflex_id` (if querying)
- [ ] Update phase references: "PREFLIGHT", "CHECK", "POSTFLIGHT" (all caps)
- [ ] Verify 13 vectors are all present
- [ ] Test git notes storage (enable_git_notes=True)

**Expected Tests:** ~12-15 test methods (examine current file for count)

---

## File 2: `tests/integration/verify_empirica_integration.py`

**Current Status:** ❌ Similar issues to File 1

**Estimated Changes:**
- [ ] Update session creation to use `db.create_session()`
- [ ] Replace deprecated assessment logging calls
- [ ] Query reflexes table instead of old tables
- [ ] Add git notes verification

**Expected Tests:** ~8-10 test methods

---

## File 3: `tests/test_phase1.6_handoff_reports.py`

**Current Status:** ❌ May reference deprecated API

**Key Changes:**
- [ ] Verify it uses GitEnhancedReflexLogger (should be mostly OK)
- [ ] Check for any direct table queries that reference old tables
- [ ] Ensure handoff reports query from reflexes table

**Expected Tests:** ~6-8 test methods

---

## File 4: `tests/test_mini_agent_handoff_e2e.py`

**Current Status:** ❌ End-to-end test likely broken

**Key Changes:**
- [ ] Update session creation
- [ ] Replace deprecated assessment calls
- [ ] Verify cascade workflow (PREFLIGHT → CHECK → POSTFLIGHT)
- [ ] Ensure multi-agent coordination uses reflexes

**Expected Tests:** ~5-7 test methods

---

## Part 2: Add 3 New Test Suites

After fixing the 4 files above, create 3 comprehensive new test suites:

### New Test Suite 1: `tests/test_reflexes_table_comprehensive.py`

**Purpose:** Comprehensive reflexes table functionality tests

**Test Coverage (25 tests estimated):**

1. **Table Structure Tests** (5 tests)
   - [ ] Column existence: reflex_id, session_id, phase, round_num, vectors (all 13)
   - [ ] Data type validation
   - [ ] Constraints: NOT NULL, UNIQUE, etc.
   - [ ] Index performance
   - [ ] Auto-increment behavior

2. **Vector Storage Tests** (8 tests)
   - [ ] Store all 13 vectors correctly
   - [ ] Vector value ranges (0.0-1.0)
   - [ ] JSON serialization/deserialization
   - [ ] Float precision
   - [ ] Boundary values (0.0, 1.0, 0.5)
   - [ ] Invalid values rejection
   - [ ] Null handling
   - [ ] Delta calculations (POSTFLIGHT - PREFLIGHT)

3. **Phase Workflow Tests** (6 tests)
   - [ ] PREFLIGHT phase storage
   - [ ] CHECK phase storage (multiple rounds)
   - [ ] POSTFLIGHT phase storage
   - [ ] Round numbering (1, 2, 3...)
   - [ ] Phase sequence validation (no POSTFLIGHT before PREFLIGHT)
   - [ ] Query by phase filter

4. **Session Isolation Tests** (3 tests)
   - [ ] Multiple sessions don't interfere
   - [ ] Query single session's reflexes
   - [ ] Aggregate across sessions

5. **Backward Compatibility Tests** (3 tests)
   - [ ] Auto-migration from old tables
   - [ ] Legacy data preserved
   - [ ] Old method calls redirect to reflexes

**Example Test Structure:**
```python
def test_store_all_13_vectors_correctly(self):
    """Verify all 13 epistemic vectors stored correctly"""
    vectors = {
        'engagement': 0.85,
        'know': 0.70,
        'do': 0.80,
        'context': 0.75,
        'clarity': 0.75,
        'coherence': 0.75,
        'signal': 0.70,
        'density': 0.60,
        'state': 0.75,
        'change': 0.70,
        'completion': 0.0,
        'impact': 0.50,
        'uncertainty': 0.40
    }

    logger = GitEnhancedReflexLogger(session_id=self.session_id)
    logger.add_checkpoint(phase="PREFLIGHT", round_num=1, vectors=vectors)

    # Query reflexes table
    cursor = self.db.conn.cursor()
    cursor.execute("""
        SELECT engagement, know, do, context, clarity, coherence, signal,
               density, state, change, completion, impact, uncertainty
        FROM reflexes WHERE session_id = ? AND phase = 'PREFLIGHT'
    """, (self.session_id,))

    row = cursor.fetchone()
    assert row == tuple(vectors.values())
```

---

### New Test Suite 2: `tests/test_statusline_reflexes_integration.py`

**Purpose:** Integration tests for statusline reading reflexes table

**Test Coverage (18 tests estimated):**

1. **Mirror Drift Monitor Tests** (6 tests)
   - [ ] PREFLIGHT vs CHECK delta calculation
   - [ ] CHECK vs POSTFLIGHT delta calculation
   - [ ] Delta vectors extracted correctly (top 5 changes)
   - [ ] Drift detection (confidence oscillation)
   - [ ] Calibration drift warning
   - [ ] Load assessment from DENSITY vector

2. **Statusline Display Tests** (6 tests)
   - [ ] Phase display (PREFLIGHT/CHECK/POSTFLIGHT)
   - [ ] Delta display format (K↑0.15, U↓0.25, etc.)
   - [ ] Velocity calculation (tasks/hour)
   - [ ] AI_ID filtering (claude-code vs claude-sonnet)
   - [ ] Multi-agent display coordination
   - [ ] Confidence threshold display

3. **Cognitive Load Assessment Tests** (3 tests)
   - [ ] DENSITY 0.0-0.3 → "low"
   - [ ] DENSITY 0.3-0.7 → "moderate"
   - [ ] DENSITY 0.7-1.0 → "high"

4. **Query Performance Tests** (3 tests)
   - [ ] Query 1 session's latest phase: <10ms
   - [ ] Query multi-agent reflexes: <50ms
   - [ ] Calculate deltas across 100 reflexes: <100ms

**Example Test Structure:**
```python
def test_delta_calculation_preflight_to_check(self):
    """Verify delta calculations are correct"""
    preflight_vectors = {...}
    check_vectors = {...}

    # Store both phases
    logger = GitEnhancedReflexLogger(...)
    logger.add_checkpoint(phase="PREFLIGHT", round_num=1, vectors=preflight_vectors)
    logger.add_checkpoint(phase="CHECK", round_num=1, vectors=check_vectors)

    # Query deltas
    deltas = calculate_vector_deltas(self.session_id)

    # Verify: CHECK.know - PREFLIGHT.know
    assert deltas['know'] == check_vectors['know'] - preflight_vectors['know']
```

---

### New Test Suite 3: `tests/test_mco_configuration_and_bias_correction.py`

**Purpose:** Test MCO configuration loading and bias corrections

**Test Coverage (15 tests estimated):**

1. **MCO Configuration Loading Tests** (5 tests)
   - [ ] Load model_profiles.yaml
   - [ ] Load personas.yaml
   - [ ] Load cascade_styles.yaml
   - [ ] Load feedback_loops.yaml
   - [ ] Merge with CLI overrides

2. **Model Profile Bias Correction Tests** (4 tests)
   - [ ] Claude Haiku: know -= 0.05
   - [ ] Claude Haiku: uncertainty += 0.10
   - [ ] Claude Sonnet: different bias profile
   - [ ] Qwen: different bias profile

3. **Persona Investigation Budget Tests** (3 tests)
   - [ ] Implementer persona: max 5 CHECK rounds
   - [ ] Researcher persona: max 7 CHECK rounds
   - [ ] Reviewer persona: different budget

4. **CASCADE Style Tests** (3 tests)
   - [ ] Implementation style decision gates
   - [ ] Research style decision gates
   - [ ] Validation style decision gates

**Example Test Structure:**
```python
def test_haiku_model_bias_corrections_applied(self):
    """Verify Haiku model bias corrections"""
    config = load_mco_config(model_profile="claude_haiku")

    # Know should be reduced by 0.05
    original_know = 0.75
    corrected_know = original_know - config['bias_corrections']['know']
    assert corrected_know == 0.70

    # Uncertainty should be increased by 0.10
    original_uncertainty = 0.30
    corrected_uncertainty = original_uncertainty + config['bias_corrections']['uncertainty']
    assert corrected_uncertainty == 0.40
```

---

## Part 3: Expected Test Results

### Before Changes
```
464 tests collected
12 collection errors (deprecated API references)
0 passed
```

### After Changes
```
464 existing tests updated + 58 new tests
512 total tests
0 collection errors
510+ passed (some may need minor fixes)
0 failed (all passing)
```

---

## Part 4: Git Workflow for Qwen

### Phase 1: Fix 4 Deprecated Test Files

```bash
# Create feature branch
git checkout -b qwen/test-updates-phase1

# Update 4 files
# - tests/integration/test_reflex_logging_integration.py
# - tests/integration/verify_empirica_integration.py
# - tests/test_phase1.6_handoff_reports.py
# - tests/test_mini_agent_handoff_e2e.py

# Run tests
pytest tests/ -v

# Commit
git commit -m "fix: Update 4 test files to use reflexes table instead of deprecated API"

# Create PR
gh pr create --title "Test: Update deprecated test files to reflexes table"
```

### Phase 2: Add 3 New Test Suites

```bash
# Create feature branch
git checkout -b qwen/new-test-suites

# Add 3 files:
# - tests/test_reflexes_table_comprehensive.py
# - tests/test_statusline_reflexes_integration.py
# - tests/test_mco_configuration_and_bias_correction.py

# Run tests
pytest tests/test_reflexes_table_comprehensive.py -v
pytest tests/test_statusline_reflexes_integration.py -v
pytest tests/test_mco_configuration_and_bias_correction.py -v

# Commit
git commit -m "test: Add 3 comprehensive test suites for reflexes, statusline, and MCO"

# Create PR
gh pr create --title "Test: Add reflexes table, statusline, and MCO configuration test coverage"
```

---

## Part 5: Key Implementation Details

### What NOT to do
- ❌ Don't create new deprecated methods
- ❌ Don't add bootstrap_session tests (removed)
- ❌ Don't reference old table names in assertions
- ❌ Don't skip git notes verification (97.5% token reduction)

### What to verify
- ✅ All 13 epistemic vectors present
- ✅ Phase names are UPPERCASE (PREFLIGHT, CHECK, POSTFLIGHT)
- ✅ Round numbers increment (1, 2, 3...)
- ✅ Session IDs match across reflexes table and git notes
- ✅ Atomic writes: SQLite + Git + JSON all update together
- ✅ Query performance acceptable (<100ms for statusline)

### Imports to use
```python
from empirica.data.session_database import SessionDatabase
from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
from empirica.cli.command_handlers.decision_utils import calculate_vector_deltas
from empirica.core.mco_loader import MCOConfigLoader  # For Part 2, Test Suite 3
```

---

## Part 6: Code Review Checklist for Qwen

Before submitting PRs, verify:

### PR 1 (Fix 4 Test Files)
- [ ] No references to old table names (preflight_assessments, etc.)
- [ ] All tests import GitEnhancedReflexLogger
- [ ] All assertions query reflexes table
- [ ] Test file runs with `pytest -v` (0 failures)
- [ ] Git commit message is clear and specific
- [ ] PR description explains why each test was changed

### PR 2 (3 New Test Suites)
- [ ] File 1: 25 comprehensive reflexes tests
- [ ] File 2: 18 statusline integration tests
- [ ] File 3: 15 MCO configuration tests
- [ ] All tests pass locally
- [ ] Coverage for edge cases (boundary values, nulls, etc.)
- [ ] Performance tests included for statusline
- [ ] PR description explains test strategy

---

## Part 7: Success Criteria

**Your work is complete when:**

1. ✅ All 4 deprecated test files updated and passing
2. ✅ 3 new test suites created with comprehensive coverage
3. ✅ 512+ total tests in codebase
4. ✅ Zero failing tests
5. ✅ Zero collection errors
6. ✅ Both PRs merged to main
7. ✅ CI/CD passes (if applicable)

**Time Estimate:** 4-6 hours (depends on test suite complexity)

---

## Part 8: Questions for Claude Code (if needed)

**Before starting, verify:**
- Q: Are there other test files I should check for deprecated API?
- Q: Should I add performance benchmarks to statusline tests?
- Q: Is the MCO bias correction test suite the right complexity?

**During implementation:**
- Q: What's the expected behavior for invalid vector values?
- Q: Should tests verify both SQLite and git notes writes?
- Q: How should tests handle concurrent session writes?

**After implementation:**
- Q: Should these tests run in CI/CD on every commit?
- Q: Are test names and docstrings clear enough for documentation?

---

## Summary

**Clean Codebase Status:** ✅
- No bootstrap patterns left
- All CASCADE commands use reflexes
- Database schema unified
- Production docs updated

**Your Tasks:**
1. Fix 4 deprecated test files (use reflexes API)
2. Add 3 new comprehensive test suites
3. Verify all tests pass
4. Submit 2 PRs

**Expected Outcome:**
- 512+ passing tests
- Full reflexes table coverage
- Statusline integration verified
- MCO configuration tested

**You're ready to start!** 🚀

---

**Next Steps After Qwen:**
1. Dev Lead: Consolidate data flow audit docs
2. Dev Lead: Move coordination archive docs
3. Final production readiness checklist
4. Deployment phase
