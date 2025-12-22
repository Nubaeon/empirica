# Goals Validation Module

The `empirica.core.goals.validation` module provides validation functions for goal-related data structures.

## Functions

### validate_complexity

**Module**: `empirica.core.goals.validation`

**Purpose**: Validates that a complexity value is within the acceptable range (0.0 to 1.0)

**Parameters**:
- `complexity` (`Optional[float]`): The complexity value to validate. Can be None for optional complexity fields.

**Raises**:
- `ValidationError`: If the complexity value is outside the 0.0-1.0 range

**Example**:
```python
from empirica.core.goals.validation import validate_complexity

# Valid complexity values
validate_complexity(0.5)  # ✅ Valid
validate_complexity(0.0)  # ✅ Valid (minimum)
validate_complexity(1.0)  # ✅ Valid (maximum)
validate_complexity(None)  # ✅ Valid (optional)

# Invalid complexity values
validate_complexity(-0.1)  # ❌ Raises ValidationError
validate_complexity(1.1)   # ❌ Raises ValidationError
```

**Related**:
- `validate_success_criteria()` - Validates goal success criteria
- `ValidationError` - Custom validation exception class

**Usage Context**:
This function is used when creating or updating goals to ensure complexity values are within the expected range. Complexity values represent the estimated difficulty of achieving a goal, where 0.0 is trivial and 1.0 is extremely complex.

---

### validate_success_criteria

**Module**: `empirica.core.goals.validation`

**Purpose**: Validates goal success criteria to ensure they meet quality standards

**Parameters**:
- `success_criteria` (`List[SuccessCriterion]`): List of success criteria to validate

**Raises**:
- `ValidationError`: If any success criterion is invalid (missing description, invalid threshold, etc.)

**Example**:
```python
from empirica.core.goals.types import SuccessCriterion
from empirica.core.goals.validation import validate_success_criteria

# Valid success criteria
criteria = [
    SuccessCriterion(description="Complete documentation", threshold=0.8),
    SuccessCriterion(description="Pass all tests", threshold=1.0)
]
validate_success_criteria(criteria)  # ✅ Valid

# Invalid success criteria
bad_criteria = [
    SuccessCriterion(description="", threshold=0.5),  # ❌ Empty description
    SuccessCriterion(description="Test coverage", threshold=1.1)  # ❌ Invalid threshold
]
validate_success_criteria(bad_criteria)  # ❌ Raises ValidationError
```

**Related**:
- `SuccessCriterion` - Data class for success criteria
- `validate_complexity()` - Validates complexity values

**Usage Context**:
This validation ensures that goal success criteria are well-defined and measurable. It's called automatically when goals are created or updated through the repository.

---

## Classes

### ValidationError

**Module**: `empirica.core.goals.validation`

**Purpose**: Custom exception class for goal validation errors

**Inherits**: `Exception`

**Usage**:
```python
from empirica.core.goals.validation import ValidationError

try:
    # Some validation operation
    validate_complexity(1.5)
except ValidationError as e:
    print(f"Validation failed: {e}")
```

**Related**: All validation functions in this module raise this exception type.

---

## Module Overview

The goals validation module ensures data integrity for the goal management system. It provides:

- **Input validation** for goal creation and updates
- **Consistent error handling** through `ValidationError`
- **Automatic validation** integrated with the goals repository

This module is part of Empirica's defensive programming approach, catching invalid data early to prevent issues downstream.