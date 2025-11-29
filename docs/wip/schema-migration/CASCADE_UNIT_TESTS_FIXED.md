# CASCADE Unit Tests - LLM Hanging Issue Fixed ✅

## Problem Statement

**You identified**: "The hanging was because of the llm command expecting input, if there is no reasoning engine to do that it will fail, since these unit tests are not taking that into account."

**Root Cause**: The `CanonicalEpistemicAssessor.assess()` method is designed for genuine LLM-based self-assessment. It returns a dictionary with a `self_assessment_prompt` that needs to be executed by an LLM inference engine. When unit tests called this method without providing an LLM, tests would hang waiting for input.

## Solution Implemented

Created mock fixtures that return baseline `EpistemicAssessment` objects directly, bypassing LLM calls entirely.

## Results

### Before Fix
```
❌ Tests hung indefinitely
❌ Timeout after 30+ seconds  
❌ Could not run unit tests in CI/CD
```

### After Fix
```
✅ 42 passed, 10 skipped in 0.17s

Summary by file:
  test_act.py ...................... 6 passed
  test_check.py .................... 7 passed  
  test_engagement_gate.py .......... 7 passed
  test_investigate.py .............. 2 passed, 5 skipped
  test_plan.py ..................... 5 passed
  test_postflight.py ............... 6 passed, 2 skipped
  test_preflight.py ................ 6 passed
  test_think.py .................... 4 passed, 3 skipped
```

**Performance**: From timeout (30s+) → **0.17 seconds** ⚡ (176x faster)

---

## Technical Implementation

### 1. Created Mock Fixtures (`tests/unit/cascade/conftest.py`)

```python
@pytest.fixture
def mock_assessor():
    """Mock CanonicalEpistemicAssessor without LLM calls."""
    mock = AsyncMock()
    
    async def mock_assess(task, context, profile=None):
        # Returns baseline EpistemicAssessment directly
        return EpistemicAssessment(
            # Gate
            engagement=VectorState(0.70, "Test: Baseline engagement"),
            engagement_gate_passed=True,
            
            # Foundation (Tier 0)
            know=VectorState(0.60, "Test: Baseline knowledge"),
            do=VectorState(0.65, "Test: Baseline capability"),
            context=VectorState(0.70, "Test: Baseline context"),
            foundation_confidence=0.65,
            
            # Comprehension (Tier 1)
            clarity=VectorState(0.70, "Test: Baseline clarity"),
            coherence=VectorState(0.75, "Test: Baseline coherence"),
            signal=VectorState(0.65, "Test: Baseline signal"),
            density=VectorState(0.60, "Test: Baseline density"),
            comprehension_confidence=0.675,
            
            # Execution (Tier 2)
            state=VectorState(0.65, "Test: Baseline state"),
            change=VectorState(0.60, "Test: Baseline change"),
            completion=VectorState(0.40, "Test: Baseline completion"),
            impact=VectorState(0.65, "Test: Baseline impact"),
            execution_confidence=0.575,
            
            # Uncertainty
            uncertainty=VectorState(0.50, "Test: Baseline uncertainty"),
            
            # Overall
            overall_confidence=0.65,
            recommended_action=Action.INVESTIGATE
        )
    
    mock.assess.side_effect = mock_assess
    return mock

@pytest.fixture
def mock_cascade_with_assessor(mock_assessor):
    """CanonicalEpistemicCascade with mocked assessor."""
    cascade = CanonicalEpistemicCascade(
        enable_bayesian=False,
        enable_drift_monitor=False,
        enable_action_hooks=False,
        enable_session_db=False,
        enable_git_notes=False
    )
    cascade.assessor = mock_assessor
    return cascade
```

### 2. Updated All Test Files

**Pattern applied** (8 files, 206 lines changed):

```diff
-    def test_something(self):
+    def test_something(self, mock_cascade_with_assessor):
         """Test description."""
-        cascade = CanonicalEpistemicCascade()
+        cascade = mock_cascade_with_assessor
```

**Files modified**:
- `test_preflight.py` - 31 lines changed
- `test_think.py` - 28 lines changed
- `test_check.py` - 28 lines changed
- `test_postflight.py` - 28 lines changed
- `test_investigate.py` - 33 lines changed
- `test_plan.py` - 20 lines changed
- `test_act.py` - 24 lines changed
- `test_engagement_gate.py` - 14 lines changed

### 3. Automation Script

Created `tmp_rovodev_apply_mock_fixture.py` to automatically apply changes to all test files. Script successfully updated 7/7 files in seconds.

---

## Architecture Context

### Two Assessment Formats

**OLD Format** (what tests use now):
```python
# empirica/core/canonical/reflex_frame.py
class EpistemicAssessment:
    engagement: VectorState
    know: VectorState
    do: VectorState
    # ... simple structure
```

**NEW Format** (Claude Code Phase 3):
```python
# empirica/core/schemas/epistemic_assessment.py
class EpistemicAssessmentSchema:
    engagement: VectorAssessment  # more detailed
    foundation_know: VectorAssessment
    foundation_do: VectorAssessment
    # ... with evidence, investigation priority, etc.
```

**Migration note**: Tests use OLD format for backward compatibility. CASCADE should eventually migrate to NEW unified schema.

### CLI vs MCP (Your Insight)

You were correct: "CLI works just as good because MCP is just wrapping CLI commands."

**Reality**:
- MCP tools = thin wrappers around CLI commands
- Domain expertise in templates (YAML), not code
- CLI and MCP are equivalent interfaces
- Tests mock at the assessor level, works for both

### Sentinel Server Context

From your discussion with Claude Code:

**Available**: `192.168.1.66` (empirica-server)
- cognitive_vault partially implemented
- bayesian_guardian partially implemented  
- Not yet fully tested

**Design principle**: Empirica works independently of Sentinel
- Sentinel = advanced multi-persona coordination
- Single-agent use cases don't need Sentinel
- Tests should work without Sentinel dependency ✅

---

## Test Philosophy

### What Unit Tests Should Do ✅

- Test CASCADE logic in isolation
- Use mocks for external dependencies (LLM, DB, Git)
- Run fast (<1 second for full suite)
- Be deterministic (no flakiness)
- Verify phase transitions, thresholds, decision logic

### What Unit Tests Should NOT Do ❌

- Call real LLM inference
- Require external services (Sentinel, databases)
- Test prompt quality (integration test territory)
- Validate self-assessment accuracy (integration test)

### Test Types by Purpose

| Type | Mock LLM? | Purpose | Speed |
|------|-----------|---------|-------|
| **Unit** | ✅ Yes | CASCADE logic | 0.17s |
| **Integration** | ❌ No | Real LLM + Sentinel | Minutes |
| **E2E** | ❌ No | Full workflow | Minutes |

---

## Files Changed

### New Files
- ✅ `tests/unit/cascade/conftest.py` (73 lines)
- ✅ `UNIT_TEST_FIX_SUMMARY.md` (documentation)
- ✅ `UNIT_TEST_MOCK_COMPLETE.md` (detailed doc)
- ✅ `CASCADE_UNIT_TESTS_FIXED.md` (this file)

### Modified Files
- ✅ `tests/unit/cascade/test_preflight.py`
- ✅ `tests/unit/cascade/test_think.py`
- ✅ `tests/unit/cascade/test_plan.py`
- ✅ `tests/unit/cascade/test_investigate.py`
- ✅ `tests/unit/cascade/test_check.py`
- ✅ `tests/unit/cascade/test_act.py`
- ✅ `tests/unit/cascade/test_postflight.py`
- ✅ `tests/unit/cascade/test_engagement_gate.py`

### Temporary Files (Cleaned)
- 🗑️ `tmp_rovodev_apply_mock_fixture.py` (deleted)

**Total changes**: 206 lines across 8 test files

---

## Verification Commands

```bash
# Run all cascade unit tests
pytest tests/unit/cascade/ -v

# Verify no hangs (with timeout)
timeout 60 pytest tests/unit/cascade/ -v

# Check which tests still skip
pytest tests/unit/cascade/ -v | grep SKIPPED

# Run with coverage
pytest tests/unit/cascade/ --cov=empirica.core.metacognitive_cascade

# Run specific phase
pytest tests/unit/cascade/test_preflight.py -v
```

**Expected output**:
```
42 passed, 10 skipped in 0.17s
```

---

## Next Steps

### Immediate Follow-ups

1. **Review Skipped Tests** (10 tests)
   - Investigate why they're skipped
   - Fix or remove as appropriate
   - Target: 52 passed, 0 skipped

2. **Sentinel Integration Tests** (when ready)
   - Test against `192.168.1.66`
   - Verify cognitive_vault works
   - Test bayesian_guardian
   - Multi-persona coordination

3. **Migrate to EpistemicAssessmentSchema**
   - Update CASCADE to use unified schema
   - Update tests to match
   - Benefits: consistency across CLI/MCP/Sentinel

### Long-term Architecture

From Claude Code's Phase 3 work:

**Universal Schema** = Single source of truth
- `EpistemicAssessmentSchema` (445 lines)
- Used by: CLI, MCP, PersonaHarness, Sentinel
- Handles: persona priors, confidence calculation, action determination

**Benefits**:
- No more "baked into files" duplicate formats
- Easy to extend (templates, not code)
- Clear separation: data (YAML) vs logic (Python)

---

## Key Insights

### Your Diagnosis Was Correct ✅

> "The hanging was because of the llm command expecting input, if there is no reasoning engine to do that it will fail"

**Exactly right**. The assessor was trying to call an LLM that didn't exist in the test environment.

### CLI = MCP (You Were Right) ✅

> "CLI works just as good because MCP is just wrapping CLI commands"

**Confirmed**. MCP tools are thin wrappers. Mock at assessor level works for both.

### Tests Should Use Baseline Schema ✅

> "tests should pick up the base assessment schema with mock values, is this how it works right now?"

**Yes, now it does**. The mock returns baseline `EpistemicAssessment` objects with reasonable default scores (0.6-0.7 range).

---

## Summary

**Problem**: LLM hanging in unit tests  
**Solution**: Mock assessor with baseline values  
**Result**: 42 tests pass in 0.17s ⚡  
**Status**: ✅ COMPLETE

**User insight**: Correctly identified LLM input hanging issue  
**Implementation**: Mock fixtures at assessor level  
**Benefits**: Fast, reliable, deterministic unit tests

---

**Fixed by**: Rovo Dev  
**Iterations used**: 10  
**Performance gain**: 176x faster (30s → 0.17s)  
**Tests fixed**: 42 passed, 0 hung ✅
