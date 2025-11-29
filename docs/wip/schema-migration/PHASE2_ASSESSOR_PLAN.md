# Phase 2: Update CanonicalEpistemicAssessor - Plan

## Current State

### What Assessor Does Now
1. `assess(task, context)` → Returns dict with `self_assessment_prompt`
2. External LLM executes prompt → Returns JSON
3. `parse_llm_response(json)` → Parses JSON and returns **OLD** `EpistemicAssessment`

### Key Code Locations
- **File**: `empirica/core/canonical/canonical_epistemic_assessment.py`
- **Lines 71-137**: `assess()` method (returns dict, not schema)
- **Lines 585-788**: `parse_llm_response()` method (creates OLD EpistemicAssessment)
- **Lines 629-709**: Vector parsing (creates OLD VectorState objects)
- **Lines 714-734**: Tier confidence calculation
- **Lines 736-748**: Action determination

---

## Migration Strategy

### Approach: Minimal Breaking Changes

**Keep**:
- ✅ `assess()` method signature (still returns dict with prompt)
- ✅ Prompt format (still asks for same JSON structure)
- ✅ Action determination logic
- ✅ Tier confidence calculation logic

**Change**:
- ❌ `parse_llm_response()` returns NEW schema instead of OLD
- ❌ Vector parsing creates NEW VectorAssessment instead of OLD VectorState
- ❌ Final assembly creates NEW EpistemicAssessmentSchema

**Add**:
- ➕ Backwards compatibility: `parse_llm_response_to_old()` (uses converter)

---

## Step-by-Step Implementation

### Step 1: Add NEW Schema Import
```python
from empirica.core.schemas.epistemic_assessment import (
    EpistemicAssessmentSchema,
    VectorAssessment,
    CascadePhase
)
from empirica.core.schemas.assessment_converters import convert_new_to_old
```

### Step 2: Create `parse_llm_response_new()` Method
New method that:
- Parses same JSON format
- Creates NEW VectorAssessment objects
- Calculates tier confidences
- Returns NEW EpistemicAssessmentSchema

### Step 3: Update `parse_llm_response()` to Call New Method
Make it a wrapper:
```python
def parse_llm_response(...) -> EpistemicAssessment:
    # Call new method
    new_assessment = self.parse_llm_response_new(...)
    # Convert to OLD for backwards compat
    return convert_new_to_old(new_assessment)
```

### Step 4: Add Direct NEW Method
```python
def assess_new(...) -> EpistemicAssessmentSchema:
    # Returns NEW schema directly
    pass
```

### Step 5: Test with Converters
- Parse sample JSON
- Verify NEW schema created correctly
- Convert to OLD
- Verify conversion works

### Step 6: Update Callers (Next Phase)
- CASCADE
- PersonaHarness
- Tests

---

## Code Changes Required

### Change 1: Imports
**Location**: Lines 25-40

**Add**:
```python
from empirica.core.schemas.epistemic_assessment import (
    EpistemicAssessmentSchema,
    VectorAssessment,
    CascadePhase
)
from empirica.core.schemas.assessment_converters import convert_new_to_old
```

### Change 2: New Parse Method
**Location**: After line 788 (after `parse_llm_response`)

**Add**: `parse_llm_response_new()` method (~200 lines)

### Change 3: Update Old Parse Method
**Location**: Lines 585-788

**Modify**: Make it wrapper that calls new method + converts

### Change 4: Add Convenience Method
**Location**: After new parse method

**Add**: `assess_new()` that returns NEW schema directly

---

## Testing Strategy

### Unit Tests
1. Test `parse_llm_response_new()` with sample JSON
2. Test `parse_llm_response()` still works (uses converter)
3. Test tier confidence calculation matches
4. Test action determination matches
5. Test round-trip: JSON → NEW → OLD → verify

### Integration Tests
1. Test with actual LLM response
2. Test with CASCADE (next phase)
3. Test backwards compatibility

---

## Risk Assessment

### LOW RISK ✅
- Adding new methods (doesn't break existing)
- New imports (additive only)
- Converter already tested

### MEDIUM RISK ⚠️
- Changing`parse_llm_response()` behavior
- Need to ensure backwards compatibility
- Tier confidence calculation must match

### HIGH RISK ❌
- None (keeping existing methods as wrappers)

---

## Success Criteria

After Phase 2:
- ✅ `parse_llm_response_new()` returns NEW schema
- ✅ `parse_llm_response()` still works (uses converter)
- ✅ All assessor unit tests pass
- ✅ Converters integrate cleanly
- ✅ No breaking changes to callers (yet)

---

## What NOT to Change (Yet)

- ❌ CASCADE (Phase 3)
- ❌ PersonaHarness (Phase 4)
- ❌ CLI handlers (Phase 5)
- ❌ Unit test mocks (Phase 7)
- ❌ Documentation (Phase 8)

Keep these using OLD schema via converters until their phases.

---

## Estimated Effort

- Step 1 (imports): 5 min
- Step 2 (new parse method): 60 min
- Step 3 (wrapper): 15 min
- Step 4 (convenience method): 15 min
- Step 5 (testing): 30 min

**Total**: ~2 hours

---

## Next: Implementation

Ready to proceed with implementation?
