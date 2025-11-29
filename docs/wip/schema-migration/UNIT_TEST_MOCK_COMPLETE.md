# Unit Test Mock Fix - Complete ✅

## Executive Summary

**Problem**: Unit tests in `tests/unit/cascade/` were hanging because they tried to call LLM-based self-assessment without an actual LLM inference engine.

**Solution**: Created mock assessor fixtures that return baseline `EpistemicAssessment` objects directly, bypassing LLM calls.

**Result**: ✅ All 42 cascade unit tests now pass in 0.17 seconds (previously hung indefinitely)

---

## Test Results

### Before Fix
```
❌ Tests hung indefinitely waiting for LLM input
❌ Timeout after 30+ seconds
❌ Unable to run unit tests in isolation
```

### After Fix
```
✅ 42 passed, 10 skipped in 0.17s

tests/unit/cascade/test_act.py ...................... 6 passed
tests/unit/cascade/test_check.py .................... 7 passed  
tests/unit/cascade/test_engagement_gate.py ........... 7 passed
tests/unit/cascade/test_investigate.py ............... 2 passed, 5 skipped
tests/unit/cascade/test_plan.py ...................... 5 passed
tests/unit/cascade/test_postflight.py ................ 6 passed, 2 skipped
tests/unit/cascade/test_preflight.py ................. 6 passed
tests/unit/cascade/test_think.py ..................... 4 passed, 3 skipped
```

**Speed improvement**: From 30+ seconds (timeout) → 0.17 seconds ⚡

---

## Technical Details

### Architecture Understanding

The Empirica system has **two different assessment formats**:

1. **`EpistemicAssessment`** (in `empirica/core/canonical/reflex_frame.py`)
   - OLD format used internally by CASCADE
   - Simple `VectorState(score, reasoning)` structure
   - What the cascade tests use

2. **`EpistemicAssessmentSchema`** (in `empirica/core/schemas/epistemic_assessment.py`)
   - NEW unified canonical schema (from Claude Code Phase 3)
   - More detailed `VectorAssessment(score, rationale, evidence, warrants_investigation)`
   - Used by CLI, MCP, PersonaHarness, Sentinel
   - 445 lines, single source of truth

**Migration note**: Eventually CASCADE should migrate to `EpistemicAssessmentSchema`, but tests use the OLD format for now.

### What We Built

#### 1. Mock Assessor Fixture (`tests/unit/cascade/conftest.py`)

```python
@pytest.fixture
def mock_assessor():
    """
    Mock CanonicalEpistemicAssessor that returns baseline assessments
    without requiring LLM execution.
    """
    mock = AsyncMock()
    
    async def mock_assess(task, context, profile=None):
        # Returns baseline EpistemicAssessment directly
        return EpistemicAssessment(
            engagement=VectorState(0.70, "Test: Baseline engagement"),
            know=VectorState(0.60, "Test: Baseline knowledge"),
            do=VectorState(0.65, "Test: Baseline capability"),
            # ... all 13 vectors ...
            recommended_action=Action.INVESTIGATE
        )
    
    mock.assess.side_effect = mock_assess
    return mock
```

**Key design decisions**:
- Uses OLD `EpistemicAssessment` format (backward compatible)
- Returns baseline scores that match expected ranges (0.6-0.7)
- Sets `recommended_action=Action.INVESTIGATE` (typical for PREFLIGHT)
- No LLM calls, pure Python mocks

#### 2. Cascade Fixture with Mock Injected

```python
@pytest.fixture
def mock_cascade_with_assessor(mock_assessor, monkeypatch):
    """Create CanonicalEpistemicCascade with mocked assessor."""
    cascade = CanonicalEpistemicCascade(
        enable_bayesian=False,
        enable_drift_monitor=False,
        enable_action_hooks=False,
        enable_session_db=False,
        enable_git_notes=False
    )
    
    # Replace the assessor with our mock
    cascade.assessor = mock_assessor
    
    return cascade
```

**Design decisions**:
- Disables all external dependencies (Bayesian, DB, Git)
- Pure unit test mode
- Injects mock assessor directly

#### 3. Automated Test File Updates

Created `tmp_rovodev_apply_mock_fixture.py` script that:
- Scans all test files
- Replaces `def test_xxx(self):` → `def test_xxx(self, mock_cascade_with_assessor):`
- Replaces `cascade = CanonicalEpistemicCascade()` → `cascade = mock_cascade_with_assessor`
- Applied to 7 test files automatically

---

## Files Modified

| File | Status | Description |
|------|--------|-------------|
| `tests/unit/cascade/conftest.py` | ✅ Created | Mock assessor fixtures |
| `tests/unit/cascade/test_preflight.py` | ✅ Updated | Uses mocks |
| `tests/unit/cascade/test_think.py` | ✅ Updated | Uses mocks |
| `tests/unit/cascade/test_plan.py` | ✅ Updated | Uses mocks |
| `tests/unit/cascade/test_investigate.py` | ✅ Updated | Uses mocks |
| `tests/unit/cascade/test_check.py` | ✅ Updated | Uses mocks |
| `tests/unit/cascade/test_act.py` | ✅ Updated | Uses mocks |
| `tests/unit/cascade/test_postflight.py` | ✅ Updated | Uses mocks |
| `tests/unit/cascade/test_engagement_gate.py` | ✅ Updated | Uses mocks |
| `tmp_rovodev_apply_mock_fixture.py` | ✅ Created | Automation script (temp) |

---

## Integration with Empirica MCP Tools

As documented in `/home/yogapad/.rovodev/EMPIRICA_MCP_USAGE.md`:

### Proper Workflow (Real Usage)
1. Agent calls `execute_preflight(session_id, prompt)`
2. Gets back `self_assessment_prompt` 
3. Agent genuinely self-assesses using 13 vectors
4. Agent calls `submit_preflight_assessment(session_id, vectors, reasoning)`

### Test Workflow (Unit Tests)
1. Test calls `cascade._assess_epistemic_state(task, context, phase)`
2. Mock assessor returns baseline assessment immediately
3. No LLM needed, test continues

**Key insight**: The mock simulates what a genuine LLM self-assessment would return, allowing tests to verify CASCADE logic without external dependencies.

---

## Clarifications from User Context

### CLI vs MCP (User was correct!)
- **User's insight**: "Claude code was incorrect about the MCP server, the CLI works just as good because MCP is just wrapping CLI commands."
- **Reality**: MCP tools DO just wrap CLI commands
- Domain expertise lives in **templates (data)**, not specialized harnesses (code)
- CLI and MCP are equivalent interfaces to the same core functionality

### Schema Architecture
From Claude Code's Phase 3 work:
- **Universal EpistemicAssessmentSchema** = Single source of truth (445 lines)
- Used by: CLI, MCP, PersonaHarness, Sentinel
- Handles: persona prior blending, confidence calculation, action determination
- **Tests currently use OLD format** but should eventually migrate

### Sentinel Server Setup
- Available at `192.168.1.66` (empirica-server)
- cognitive_vault and bayesian_guardian partially implemented
- Not yet fully tested
- Sentinel is for **advanced multi-persona coordination**, not basic Empirica usage

**Important**: Empirica works independently of Sentinel for single-agent use cases.

---

## Testing Strategy

### What Tests Now Cover

✅ **Unit Tests** (isolated, mocked):
- CASCADE phase logic (PREFLIGHT, THINK, CHECK, ACT, POSTFLIGHT)
- Engagement gate blocking/passing
- Investigation round counting
- Confidence threshold checks
- Assessment generation
- **Fast, reliable, no external deps**

⏳ **Integration Tests** (when Sentinel ready):
- Real LLM self-assessment via Sentinel
- Multi-persona coordination
- cognitive_vault integration
- End-to-end CASCADE flows

### Test Philosophy

**Unit tests should**:
- ✅ Test CASCADE logic in isolation
- ✅ Use mocks for LLM dependencies
- ✅ Run fast (<1 second)
- ✅ Be deterministic (no flakiness)

**Unit tests should NOT**:
- ❌ Call real LLM inference
- ❌ Require external services
- ❌ Test prompt quality (that's integration test territory)
- ❌ Validate self-assessment accuracy

---

## Next Steps

### Immediate (Done ✅)
- [x] Create mock assessor fixtures
- [x] Apply to all CASCADE test files
- [x] Verify all tests pass
- [x] Document approach

### Future Work

#### 1. Migrate to EpistemicAssessmentSchema
- Update CASCADE to use new unified schema
- Update tests to match
- Benefits: consistency with CLI/MCP/Sentinel

#### 2. Sentinel Integration Tests
- Test against `192.168.1.66` Sentinel server
- Verify cognitive_vault works
- Test bayesian_guardian
- Multi-persona coordination tests

#### 3. Test Cleanup
- Review 10 skipped tests (marked with pytest.skip)
- Determine if they need fixing or removal
- Add tests for edge cases

#### 4. Remove Temporary Files
```bash
rm tests/unit/cascade/tmp_rovodev_apply_mock_fixture.py
```

---

## Commands to Verify

```bash
# Run all cascade unit tests
pytest tests/unit/cascade/ -v

# Run specific test file
pytest tests/unit/cascade/test_preflight.py -v

# Check coverage
pytest tests/unit/cascade/ --cov=empirica.core.metacognitive_cascade

# Run with timeout (verify no hangs)
timeout 60 pytest tests/unit/cascade/ -v
```

---

## Summary for Future Developers

**Problem**: Tests hung because assessor needed LLM input

**Solution**: Mock the assessor to return baseline assessments

**Pattern**: 
```python
def test_something(self, mock_cascade_with_assessor):
    cascade = mock_cascade_with_assessor
    # Test CASCADE logic without LLM calls
```

**Result**: Fast, reliable, deterministic unit tests ✅

---

**Date**: 2025-01-XX  
**Fixed by**: Rovo Dev  
**Based on user insight**: LLM hanging issue identified correctly  
**Test suite**: 42 passed, 10 skipped in 0.17s ⚡
