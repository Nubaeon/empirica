# Handoff to Qwen: Test Updates & Comprehensive Test Plan

**Date:** December 5, 2025
**From:** Claude Code (Code Lead)
**To:** Qwen (Testing Specialist)
**Status:** Ready for Implementation
**Priority:** HIGH (unblocks production verification)

---

## TL;DR

**Your Task:**
1. Update 4 deprecated test files to use new reflexes table
2. Add 3 new test suites for reflexes integration, statusline, and MCO
3. Ensure 100% test pass rate + full coverage

**Why:** Current tests use removed SessionDatabase methods. Need comprehensive reflexes table testing.

**What's Affected:** 4 existing test files + 3 new test suites

**Timeline:** 10-12 days (4 days updates + 8 days new tests)

**Current Tests:** 722 tests across 94 files → **Target:** 770+ tests after updates

---

## The Problem

### Current State
- **4 test files** still use deprecated `log_preflight_assessment()`, `log_postflight_assessment()` methods
- **0 comprehensive reflexes table tests** (only basic schema tests exist)
- **No statusline integration tests** (statusline reads reflexes but untested)
- **Limited MCO configuration tests** (model profiles not validated)
- **No multi-AI coordination tests** (three-AI workflows untested)

### Risk
- Tests pass but use wrong API (false confidence)
- Reflexes table queries from statusline untested
- Mirror drift detection untested
- MCO bias corrections not validated

---

## PART 1: Update Deprecated Test Files (4-6 hours)

### Test File 1: `tests/integration/test_reflex_logging_integration.py`

**Current State:** Uses deprecated API
**Lines:** 150 lines
**Impact:** Reflexes + git notes integration test

**What to Change:**

| OLD | NEW |
|-----|-----|
| `db.log_preflight_assessment()` | `db.store_vectors(session_id, 'PREFLIGHT', vectors)` |
| Query `preflight_assessments` table | Query `reflexes` WHERE phase='PREFLIGHT' |
| Import deprecated GitEnhancedReflexLogger | (Keep - already correct) |

**Specific Updates:**

```python
# OLD (Line ~40):
assessment_id = db.log_preflight_assessment(
    session_id=session_id,
    cascade_id=cascade_id,
    prompt_summary="Test preflight",
    vectors=vectors_dict,
    uncertainty_notes="Test notes"
)

# NEW:
assessment_id = db.store_vectors(
    session_id=session_id,
    phase="PREFLIGHT",
    vectors=vectors_dict,
    cascade_id=cascade_id,
    round_num=1
)

# Then verify:
cursor.execute(
    "SELECT * FROM reflexes WHERE session_id = ? AND phase = 'PREFLIGHT'",
    (session_id,)
)
result = cursor.fetchone()
assert result is not None
```

**Verification Tests:**
- [ ] Vector storage works correctly
- [ ] Phase filtering works
- [ ] Round number increments
- [ ] Timestamp is recorded
- [ ] Git notes created (if enabled)

---

### Test File 2: `tests/integration/verify_empirica_integration.py`

**Current State:** Uses old schema queries
**Lines:** 120 lines
**Impact:** Integration sanity check

**What to Change:**

| OLD | NEW |
|-----|-----|
| PRAGMA queries on `preflight_assessments` | PRAGMA queries on `reflexes` |
| Check "12 tables" | Check "8 core tables" |
| Column references to old tables | Column references to reflexes |

**Specific Updates:**

```python
# OLD (Line ~50):
cursor.execute("""
    PRAGMA table_info(preflight_assessments)
""")
columns = {row[1] for row in cursor.fetchall()}
assert 'engagement' in columns
assert 'reflex_log_path' in columns

# NEW:
cursor.execute("""
    PRAGMA table_info(reflexes)
""")
columns = {row[1] for row in cursor.fetchall()}
assert 'engagement' in columns
assert 'phase' in columns  # NEW COLUMN
assert 'round' in columns  # NEW COLUMN
```

**Verification Tests:**
- [ ] Reflexes table exists
- [ ] All 13 vectors are columns
- [ ] phase column exists (PREFLIGHT/CHECK/POSTFLIGHT)
- [ ] round column exists
- [ ] Metadata columns exist (reflex_data, reasoning, evidence)
- [ ] Foreign keys are correct

---

### Test File 3: `tests/test_phase1.6_handoff_reports.py`

**Current State:** Uses old handoff schema
**Lines:** 180 lines
**Impact:** Handoff report creation test

**What to Change:**

| OLD | NEW |
|-----|-----|
| `db.log_preflight_assessment()` | `db.store_vectors(..., phase='PREFLIGHT')` |
| `db.log_postflight_assessment()` | `db.store_vectors(..., phase='POSTFLIGHT')` |
| Query deprecated tables for handoff data | Query reflexes table |

**Specific Updates:**

```python
# OLD:
db.log_preflight_assessment(session_id, cascade_id, "prompt", vectors)
db.log_postflight_assessment(session_id, cascade_id, "summary", vectors)

# NEW:
db.store_vectors(session_id, 'PREFLIGHT', vectors, cascade_id, round_num=1)
db.store_vectors(session_id, 'POSTFLIGHT', vectors, cascade_id, round_num=1)

# Handoff report should now query reflexes:
preflight = db.get_latest_vectors(session_id, phase='PREFLIGHT')
postflight = db.get_latest_vectors(session_id, phase='POSTFLIGHT')
```

**Verification Tests:**
- [ ] Preflight vectors stored correctly
- [ ] Postflight vectors stored correctly
- [ ] Deltas calculated correctly (POSTFLIGHT - PREFLIGHT)
- [ ] Handoff report generation works
- [ ] Token efficiency measured correctly

---

### Test File 4: `tests/test_mini_agent_handoff_e2e.py`

**Current State:** Uses old handoff API
**Lines:** 220 lines
**Impact:** Three-agent coordination test (Phase 1)

**What to Change:**

| OLD | NEW |
|-----|-----|
| `db.log_preflight_assessment()` calls | `db.store_vectors(..., phase='PREFLIGHT')` |
| Query old tables for agent comparison | Query reflexes for agent vectors |
| Reference to deprecated handoff methods | Use new handoff API |

**Specific Updates:**

```python
# OLD:
claude_code.log_preflight_assessment(session_id, ...)
sonnet.log_preflight_assessment(session_id, ...)

# NEW:
db.store_vectors(session_id, 'PREFLIGHT', claude_code_vectors, ai_id='claude-code')
db.store_vectors(session_id, 'PREFLIGHT', sonnet_vectors, ai_id='claude-sonnet')

# Compare via handoff report:
handoff = EpistemicHandoffReportGenerator().generate_handoff_report(
    session_id=session_id,
    task_summary="Three-AI coordination test",
    key_findings=["Claude-code faster", "Sonnet more careful"]
)
```

**Verification Tests:**
- [ ] Multi-AI vectors stored correctly
- [ ] Handoff report generation works with multiple AIs
- [ ] Session sharing works
- [ ] Token efficiency good (compression verified)

---

## PART 2: Add New Test Suites (8-10 days)

### New Test Suite 1: `tests/integration/test_reflexes_table_comprehensive.py`

**Purpose:** Exhaustive reflexes table testing
**Estimated Lines:** 300-350 test lines
**Estimated Tests:** 20-25 tests
**Effort:** 2 days

**Test Categories:**

#### A. Query Performance Tests (5 tests)
```python
def test_reflexes_query_performance_latest_vectors():
    """Verify get_latest_vectors() is fast"""
    # Create 100 assessments
    # Measure query time
    # Assert < 100ms for latest vector retrieval

def test_reflexes_phase_filter_performance():
    """Verify phase filtering is efficient"""
    # Create 100 mixed-phase assessments
    # Query by phase
    # Assert correct filtering + fast execution

def test_reflexes_bulk_insert_performance():
    """Verify bulk vector storage is efficient"""
    # Store 100 vectors in rapid succession
    # Assert < 1 second total

def test_reflexes_concurrent_access():
    """Verify concurrent reads work"""
    # Multiple threads reading simultaneously
    # Assert no lock/corruption

def test_reflexes_index_usage():
    """Verify database indexes are optimal"""
    # Check EXPLAIN QUERY PLAN
    # Verify indexes are used
```

#### B. Edge Case Tests (6 tests)
```python
def test_reflexes_null_vectors():
    """Handle partially-null vector rows"""
    # Store vectors with some nulls
    # Query should handle gracefully

def test_reflexes_missing_phase():
    """Handle queries for non-existent phases"""
    # Query phase='NONEXISTENT'
    # Should return empty list, not error

def test_reflexes_round_number_edge_cases():
    """Verify round numbering is correct"""
    # Multiple rounds same session
    # Round numbers should increment properly

def test_reflexes_timestamp_ordering():
    """Verify timestamps order correctly"""
    # Store multiple vectors with microsecond differences
    # ORDER BY timestamp should be correct

def test_reflexes_cascade_id_null_handling():
    """Handle sessions without cascade_id"""
    # Some vectors might not have cascade_id
    # Queries should still work

def test_reflexes_large_metadata_json():
    """Handle large reflex_data JSON"""
    # Store 50KB of metadata
    # Should not corrupt or fail
```

#### C. Data Integrity Tests (6 tests)
```python
def test_reflexes_foreign_key_constraints():
    """Verify foreign key integrity"""
    # Try to store vector for non-existent session
    # Should fail (FK constraint)

def test_reflexes_vector_value_ranges():
    """Verify vector values are 0.0-1.0"""
    # Store invalid values (>1.0 or <0.0)
    # Should fail or normalize

def test_reflexes_phase_enum_validation():
    """Verify phase is valid enum"""
    # Try to store phase='INVALID'
    # Should fail

def test_reflexes_no_duplicate_latest():
    """Verify get_latest_vectors returns exactly 1"""
    # Create 10 PREFLIGHT assessments
    # get_latest_vectors should return 1

def test_reflexes_round_uniqueness():
    """Verify round numbers per phase are unique"""
    # Try to store 2 rows with same session/phase/round
    # Should fail (unique constraint)

def test_reflexes_data_consistency():
    """Verify data consistency across queries"""
    # Store vectors
    # Query via multiple methods
    # All should return same data
```

#### D. Query Pattern Tests (4 tests)
```python
def test_reflexes_get_by_phase():
    """Test common pattern: get all vectors for phase"""
    # Query WHERE phase='PREFLIGHT'
    # Verify all results are PREFLIGHT

def test_reflexes_get_latest_per_ai():
    """Test getting latest for specific AI"""
    # Multi-AI session
    # Get latest for claude-code
    # Verify correct AI's vectors

def test_reflexes_get_with_metadata_filter():
    """Test filtering by metadata"""
    # Query where reflex_data contains specific json
    # Verify correct subset returned

def test_reflexes_date_range_query():
    """Test querying by timestamp range"""
    # Get all vectors between timestamps
    # Verify correct temporal range
```

**Coverage Target:** 95%+ reflexes table functionality

---

### New Test Suite 2: `tests/integration/test_statusline_reflexes_integration.py`

**Purpose:** Verify statusline correctly queries reflexes
**Estimated Lines:** 250-300 test lines
**Estimated Tests:** 15-18 tests
**Effort:** 2 days

**Test Categories:**

#### A. Statusline Data Reading Tests (5 tests)
```python
def test_statusline_reads_latest_vectors():
    """Verify statusline gets latest vectors from reflexes"""
    # Create assessments
    # Call statusline function
    # Verify it reads from reflexes, not old tables

def test_statusline_cognitive_load_calculation():
    """Verify cognitive load uses DENSITY vector"""
    # Store assessment with DENSITY=0.75
    # Call calculate_cognitive_load()
    # Verify load_level='high' (not heuristic-based)

def test_statusline_delta_calculation():
    """Verify delta calculations are accurate"""
    # PREFLIGHT: know=0.7
    # POSTFLIGHT: know=0.85
    # Delta should be +0.15

def test_statusline_velocity_calculation():
    """Verify progress velocity is accurate"""
    # Create multiple assessments over time
    # Calculate velocity
    # Verify tasks/hour is reasonable

def test_statusline_scope_stability():
    """Verify scope stability is calculated"""
    # Create assessments with changing breadth
    # Verify stability detection works
```

#### B. Mirror Drift Detection Tests (5 tests)
```python
def test_statusline_detects_true_drift():
    """Verify true epistemic drift is detected"""
    # PREFLIGHT: know=0.8
    # Assessment 1: know=0.75
    # Assessment 2: know=0.6
    # Assessment 3: know=0.4
    # Detect downward drift

def test_statusline_detects_learning():
    """Verify learning progression is recognized"""
    # Progressive knowledge increase
    # Categorize as LEARNING (not drift)

def test_statusline_detects_oscillation():
    """Verify uncertainty oscillation is flagged"""
    # uncertainty: 0.3, 0.6, 0.2, 0.7, 0.1
    # Detect pattern, classify as OSCILLATION

def test_statusline_detects_calibration_drift():
    """Verify calibration accuracy is tracked"""
    # PREFLIGHT: uncertainty=0.2
    # POSTFLIGHT: uncertainty=0.8
    # Detect high calibration drift

def test_statusline_warning_threshold():
    """Verify warnings only shown when needed"""
    # Small drift: no warning
    # Large drift: warning
    # Critical drift: critical warning
```

#### C. Per-AI Configuration Tests (5 tests)
```python
def test_statusline_loads_feedback_loops_config():
    """Verify feedback_loops.yaml is loaded"""
    # Call with ai_id='claude-code'
    # Verify config loaded from YAML
    # Verify agent-specific thresholds used

def test_statusline_falls_back_to_defaults():
    """Verify graceful fallback if config missing"""
    # Rename feedback_loops.yaml temporarily
    # Call statusline
    # Should use sensible defaults, not error

def test_statusline_different_agents_different_loads():
    """Verify different AIs have different thresholds"""
    # DENSITY=0.75
    # claude-code: high (threshold 0.75)
    # claude-sonnet: sustainable (threshold 0.70)
    # Verify different results

def test_statusline_cognitive_load_actions():
    """Verify actions specified in config are used"""
    # High load for claude-code
    # Verify checkpoint_recommended=true
    # Verify correct severity level

def test_statusline_decision_gate_impact():
    """Verify cognitive load affects CHECK gate"""
    # High load
    # Verify confidence_adjustment applied
    # Verify CHECK gate raised
```

**Coverage Target:** 100% statusline reflexes interactions

---

### New Test Suite 3: `tests/unit/canonical/test_mco_configuration_and_bias_correction.py`

**Purpose:** Validate MCO profiles + bias corrections
**Estimated Lines:** 200-250 test lines
**Estimated Tests:** 12-15 tests
**Effort:** 2 days

**Test Categories:**

#### A. Model Profile Loading Tests (4 tests)
```python
def test_mco_loads_model_profiles_yaml():
    """Verify model_profiles.yaml is loaded correctly"""
    # Load claude_haiku profile
    # Verify all fields present

def test_mco_applies_bias_corrections():
    """Verify bias corrections are applied"""
    # Haiku model assessment: know=0.75
    # Applied correction: -0.05
    # Effective know: 0.70

def test_mco_applies_uncertainty_adjustments():
    """Verify uncertainty adjustments work"""
    # Haiku assessment: uncertainty=0.30
    # Applied adjustment: +0.10
    # Effective uncertainty: 0.40

def test_mco_cascades_style_switching():
    """Verify cascade style profiles switch"""
    # Load default profile (thresholds A)
    # Switch to rigorous (thresholds B)
    # Verify correct thresholds used
```

#### B. Persona Configuration Tests (4 tests)
```python
def test_mco_loads_personas_yaml():
    """Verify personas.yaml is loaded"""
    # Load implementer persona
    # Verify epistemic_priors

def test_mco_persona_investigation_budget():
    """Verify persona investigation cycles enforced"""
    # implementer: max_rounds=5
    # Try to do 6 rounds
    # Should be prevented (or warned)

def test_mco_persona_uncertainty_threshold():
    """Verify uncertainty thresholds per persona"""
    # implementer: uncertainty_threshold=0.60
    # investigator: uncertainty_threshold=0.70
    # Verify different thresholds applied

def test_mco_persona_learning_style():
    """Verify learning characteristics"""
    # learner: requires_clarification=true
    # expert: requires_clarification=false
    # Verify behavior differs
```

#### C. Feedback Loops Configuration Tests (4 tests)
```python
def test_mco_loads_feedback_loops_yaml():
    """Verify feedback_loops.yaml is loaded"""
    # Load claude-code config
    # Verify listeners + thresholds

def test_mco_agent_specific_config():
    """Verify agent-specific overrides work"""
    # Default: ai_automatic=false
    # claude-code: ai_automatic=true
    # Verify claude-code uses true

def test_mco_fallback_to_global_default():
    """Verify fallback when agent not configured"""
    # Unknown agent 'gpt-test'
    # Should fall back to global_default

def test_mco_config_validation():
    """Verify config is validated"""
    # Load invalid config (missing required field)
    # Should raise error or warning
```

**Coverage Target:** 100% MCO configuration loading + validation

---

## Test Execution Plan

### Phase 1: Update Existing Tests (Days 1-2)

1. **Day 1 - Morning:** Update test files 1 & 2
2. **Day 1 - Afternoon:** Update test files 3 & 4
3. **Day 2:** Run full test suite, fix any breakage
4. **Day 2 - End:** Verify 100% pass rate

**Checkpoint:** All 4 updated files pass

---

### Phase 2: New Reflexes Tests (Days 3-4)

1. **Day 3:** Write reflexes table comprehensive tests
2. **Day 4:** Run tests, verify all pass
3. **Day 4 - End:** Verify 95%+ reflexes coverage

**Checkpoint:** Reflexes suite complete + passing

---

### Phase 3: New Statusline Tests (Days 5-6)

1. **Day 5:** Write statusline integration tests
2. **Day 6:** Run tests, verify all pass
3. **Day 6 - End:** Verify 100% statusline coverage

**Checkpoint:** Statusline suite complete + passing

---

### Phase 4: New MCO Tests (Days 7-8)

1. **Day 7:** Write MCO configuration tests
2. **Day 8:** Run tests, verify all pass
3. **Day 8 - End:** Verify 100% MCO coverage

**Checkpoint:** MCO suite complete + passing

---

### Phase 5: Integration & Verification (Days 9-10)

1. **Day 9:** Run full test suite (722 → 770+ tests)
2. **Day 9:** Fix any cross-test issues
3. **Day 10:** Code coverage report
4. **Day 10:** Final verification
5. **Day 10 - End:** Ready for production

**Final Checkpoint:** All tests pass, coverage >95%

---

## Running Tests

### Individual Test Suites
```bash
# Updated tests
pytest tests/integration/test_reflex_logging_integration.py -v
pytest tests/integration/verify_empirica_integration.py -v
pytest tests/test_phase1.6_handoff_reports.py -v
pytest tests/test_mini_agent_handoff_e2e.py -v

# New tests
pytest tests/integration/test_reflexes_table_comprehensive.py -v
pytest tests/integration/test_statusline_reflexes_integration.py -v
pytest tests/unit/canonical/test_mco_configuration_and_bias_correction.py -v
```

### Full Test Suite
```bash
# Run everything
pytest tests/ -v --tb=short

# With coverage
pytest tests/ --cov=empirica --cov-report=html
```

### Regression Check
```bash
# Make sure we didn't break anything
pytest tests/ -x  # Stop on first failure
```

---

## Success Criteria

✅ All 4 deprecated test files updated + passing
✅ 20+ new reflexes table tests passing
✅ 15+ new statusline integration tests passing
✅ 12+ new MCO configuration tests passing
✅ Total test count: 770+ (from 722)
✅ Code coverage: >95%
✅ Zero regressions (all existing tests still pass)
✅ All tests can run in < 2 minutes

---

## Questions Before You Start

1. **Test Environment:** Should tests run against SQLite or mock database?
2. **Concurrency:** Should tests use threading or async?
3. **Coverage Threshold:** Is 95% acceptable or require 98%+?
4. **Performance:** Should we add performance benchmarks?

---

## References

**Source Code:**
- `/home/yogapad/empirical-ai/empirica/empirica/data/session_database.py` - DB API
- `/home/yogapad/empirical-ai/empirica/scripts/statusline_empirica.py` - Statusline code
- `/home/yogapad/empirical-ai/empirica/empirica/config/mco/` - Config files

**Existing Tests (as reference):**
- `/home/yogapad/empirical-ai/empirica/tests/integration/` - 15 integration tests
- `/home/yogapad/empirical-ai/empirica/tests/unit/cascade/` - 8 phase tests
- `/home/yogapad/empirical-ai/empirica/tests/integrity/test_no_heuristics.py` - Integrity checks

---

## Next Steps

1. Review this handoff
2. Set up test environment
3. Execute Phase 1 (updates)
4. Execute Phases 2-4 (new tests)
5. Execute Phase 5 (integration + verification)

Good luck! Complete test coverage is critical for production readiness. 🚀
