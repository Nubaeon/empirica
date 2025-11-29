# Bugfix: POSTFLIGHT Delta Calculation Type Mismatch

**Date**: 2025-11-28
**Issue**: `TypeError: unsupported operand type(s) for -: 'dict' and 'float'`
**Location**: `empirica/cli/command_handlers/workflow_commands.py:350`
**Status**: ✅ **FIXED**

---

## Problem

When submitting POSTFLIGHT assessments via MCP, the delta calculation failed with a type mismatch error:

```
❌ Postflight submit error: unsupported operand type(s) for -: 'dict' and 'float'
```

### Root Cause

The delta calculation assumed vector values were always simple floats:

```python
# Line 350 (BEFORE FIX)
deltas[key] = vectors[key] - preflight_vectors[key]
```

However, the MCP self-assessment prompt requested nested assessment objects:

```json
{
  "engagement": {
    "score": 0.95,
    "rationale": "High engagement with collaborative work",
    "evidence": "Multiple user clarifications"
  }
}
```

When calculating deltas, the code tried:
```python
{"score": 0.95, "rationale": "..."} - 0.90  # TypeError!
```

### Why Two Formats?

**Simple float format** (internal CLI):
```json
{"engagement": 0.95, "know": 0.85, "uncertainty": 0.15}
```

**Nested dict format** (MCP self-assessment prompt):
```json
{
  "engagement": {
    "score": 0.95,
    "rationale": "Your genuine reasoning",
    "evidence": "Supporting facts"
  }
}
```

The MCP self-assessment prompt follows the `VectorAssessment` schema structure, which includes rationale and evidence fields. However, the delta calculation code only expected simple floats.

---

## Solution

Added a helper function `_extract_numeric_value()` that handles both formats:

```python
def _extract_numeric_value(value):
    """
    Extract numeric value from vector data.

    Handles two formats:
    - Simple float: 0.85
    - Nested dict: {"score": 0.85, "rationale": "...", "evidence": "..."}

    Returns:
        float or None if value cannot be extracted
    """
    if isinstance(value, (int, float)):
        return float(value)
    elif isinstance(value, dict):
        # Extract 'score' key if present
        if 'score' in value:
            return float(value['score'])
        # Fallback: try to get any numeric value
        for k, v in value.items():
            if isinstance(v, (int, float)):
                return float(v)
    return None
```

Updated delta calculation to use the helper:

```python
# Line 350-354 (AFTER FIX)
# Extract numeric values (handle both float and dict formats)
post_val = _extract_numeric_value(vectors[key])
pre_val = _extract_numeric_value(preflight_vectors[key])
if post_val is not None and pre_val is not None:
    deltas[key] = post_val - pre_val
```

---

## Changes Made

### 1. Modified File
**File**: `empirica/cli/command_handlers/workflow_commands.py`

**Changes**:
- **Line 296-318**: Added `_extract_numeric_value()` helper function
- **Line 350-354**: Updated delta calculation to use helper

### 2. New Test File
**File**: `tests/unit/cli/test_workflow_commands_delta_fix.py`

**Coverage**: 10 unit tests covering:
- Simple float extraction
- Nested dict extraction (with/without 'score' key)
- Invalid input handling
- Delta calculation with simple format
- Delta calculation with nested format
- Delta calculation with mixed formats
- Delta calculation with missing keys
- Regression test for original error scenario

**Test Results**: ✅ **10/10 passed**

---

## Verification

### Test Output
```bash
$ python -m pytest tests/unit/cli/test_workflow_commands_delta_fix.py -v

tests/unit/cli/test_workflow_commands_delta_fix.py::TestExtractNumericValue::test_simple_float PASSED
tests/unit/cli/test_workflow_commands_delta_fix.py::TestExtractNumericValue::test_simple_int PASSED
tests/unit/cli/test_workflow_commands_delta_fix.py::TestExtractNumericValue::test_nested_dict_with_score PASSED
tests/unit/cli/test_workflow_commands_delta_fix.py::TestExtractNumericValue::test_nested_dict_without_score PASSED
tests/unit/cli/test_workflow_commands_delta_fix.py::TestExtractNumericValue::test_invalid_inputs PASSED
tests/unit/cli/test_workflow_commands_delta_fix.py::TestDeltaCalculation::test_delta_simple_format PASSED
tests/unit/cli/test_workflow_commands_delta_fix.py::TestDeltaCalculation::test_delta_nested_format PASSED
tests/unit/cli/test_workflow_commands_delta_fix.py::TestDeltaCalculation::test_delta_mixed_format PASSED
tests/unit/cli/test_workflow_commands_delta_fix.py::TestDeltaCalculation::test_delta_with_missing_keys PASSED
tests/unit/cli/test_workflow_commands_delta_fix.py::TestRegressionForOriginalError::test_original_error_scenario PASSED

============================== 10 passed in 0.09s
```

### Example: Fixed Delta Calculation

**PREFLIGHT** (simple floats):
```json
{"engagement": 0.90, "know": 0.65, "do": 0.80, "uncertainty": 0.25}
```

**POSTFLIGHT** (nested dicts):
```json
{
  "engagement": {"score": 0.95, "rationale": "Highly collaborative"},
  "know": {"score": 0.85, "rationale": "Deep knowledge"},
  "do": {"score": 0.90, "rationale": "Successful delivery"},
  "uncertainty": {"score": 0.15, "rationale": "Low uncertainty"}
}
```

**DELTAS** (now calculated correctly):
```json
{
  "engagement": 0.05,   # ✅ 0.95 - 0.90
  "know": 0.20,         # ✅ 0.85 - 0.65
  "do": 0.10,           # ✅ 0.90 - 0.80
  "uncertainty": -0.10  # ✅ 0.15 - 0.25 (decreased uncertainty)
}
```

---

## Impact

### Before Fix
- ❌ POSTFLIGHT submission failed when using MCP self-assessment prompt format
- ❌ Delta calculation threw TypeError
- ❌ Session calibration could not be calculated
- ⚠️ Workaround: Manually submit with simple float format

### After Fix
- ✅ POSTFLIGHT submission works with both formats
- ✅ Delta calculation handles nested VectorAssessment objects
- ✅ Session calibration calculated correctly
- ✅ MCP self-assessment prompt can be used as-is
- ✅ Backwards compatible with simple float format

---

## Related Components

### Unaffected
The following components **do NOT** have the same issue:
- ✅ `handle_preflight_submit_command()` - No delta calculation (first assessment)
- ✅ `handle_check_submit_command()` - No delta calculation

Only **POSTFLIGHT** calculates deltas (comparing to PREFLIGHT), so this was the only affected component.

---

## Backwards Compatibility

✅ **Fully backwards compatible**

The fix handles:
1. **Simple float format** (existing behavior): `{"engagement": 0.95}`
2. **Nested dict format** (new support): `{"engagement": {"score": 0.95, "rationale": "..."}}`
3. **Mixed formats** (flexible): Some vectors simple, some nested

No breaking changes to existing code or workflows.

---

## Lessons Learned

### Schema Consistency
The MCP self-assessment prompt uses the full `VectorAssessment` schema (with `score`, `rationale`, `evidence`), but the internal delta calculation expected simplified scalar values. This mismatch caused the error.

### Solution Pattern
When accepting user/API input, always normalize to a canonical internal format before performing operations. The `_extract_numeric_value()` helper provides this normalization layer.

### Testing Importance
The original implementation assumed a single format. Unit tests now cover multiple input formats to prevent regressions.

---

## Conclusion

**Status**: ✅ **FIXED and TESTED**

The POSTFLIGHT delta calculation now correctly handles both simple float and nested dict vector formats, enabling the MCP self-assessment workflow to function as designed.

**Lines changed**: ~30
**Tests added**: 10
**Backwards compatibility**: 100%
**Regression risk**: Low (new helper only used in delta calculation, existing functionality unchanged)
