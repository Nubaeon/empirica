# NEW EpistemicAssessmentSchema Guide

## Overview

**Status**: Schema migration 60% complete (as of 2025-01)

Empirica is migrating from the OLD schema (`EpistemicAssessment`) to the NEW schema (`EpistemicAssessmentSchema`). This guide documents the NEW schema format.

---

## Quick Reference

### Import
```python
from empirica.core.schemas.epistemic_assessment import (
    EpistemicAssessmentSchema,
    VectorAssessment,
    CascadePhase
)
```

### Field Name Changes

| OLD Schema | NEW Schema |
|------------|------------|
| `engagement` | `engagement` (same) |
| `know` | `foundation_know` ✨ |
| `do` | `foundation_do` ✨ |
| `context` | `foundation_context` ✨ |
| `clarity` | `comprehension_clarity` ✨ |
| `coherence` | `comprehension_coherence` ✨ |
| `signal` | `comprehension_signal` ✨ |
| `density` | `comprehension_density` ✨ |
| `state` | `execution_state` ✨ |
| `change` | `execution_change` ✨ |
| `completion` | `execution_completion` ✨ |
| `impact` | `execution_impact` ✨ |
| `uncertainty` | `uncertainty` (same) |

---

## Schema Structure

### VectorAssessment
Each vector uses `VectorAssessment` instead of `VectorState`:

```python
@dataclass
class VectorAssessment:
    score: float  # 0.0 to 1.0
    rationale: str  # Why this score
    evidence: Optional[str] = None  # Supporting facts
    warrants_investigation: bool = False  # Needs investigation?
    investigation_priority: int = 0  # 0-10 priority
```

**Example**:
```python
foundation_know = VectorAssessment(
    score=0.65,
    rationale="Familiar with concepts but need to learn specifics",
    evidence="Have worked with similar systems before",
    warrants_investigation=True,
    investigation_priority=7
)
```

### EpistemicAssessmentSchema

Complete assessment structure:

```python
@dataclass
class EpistemicAssessmentSchema:
    # GATE
    engagement: VectorAssessment
    
    # FOUNDATION (Tier 0) - Note the "foundation_" prefix
    foundation_know: VectorAssessment
    foundation_do: VectorAssessment
    foundation_context: VectorAssessment
    
    # COMPREHENSION (Tier 1) - Note the "comprehension_" prefix
    comprehension_clarity: VectorAssessment
    comprehension_coherence: VectorAssessment
    comprehension_signal: VectorAssessment
    comprehension_density: VectorAssessment
    
    # EXECUTION (Tier 2) - Note the "execution_" prefix
    execution_state: VectorAssessment
    execution_change: VectorAssessment
    execution_completion: VectorAssessment
    execution_impact: VectorAssessment
    
    # UNCERTAINTY
    uncertainty: VectorAssessment
    
    # METADATA (different from OLD schema)
    phase: CascadePhase  # PREFLIGHT, INVESTIGATE, CHECK, ACT, POSTFLIGHT
    round_num: int = 0
    investigation_count: int = 0
```

---

## Creating Assessments

### Basic Example
```python
from empirica.core.schemas.epistemic_assessment import (
    EpistemicAssessmentSchema,
    VectorAssessment,
    CascadePhase
)

# Create assessment
assessment = EpistemicAssessmentSchema(
    # GATE
    engagement=VectorAssessment(0.75, "Good collaborative engagement"),
    
    # FOUNDATION
    foundation_know=VectorAssessment(0.60, "Moderate domain knowledge"),
    foundation_do=VectorAssessment(0.65, "Good capability"),
    foundation_context=VectorAssessment(0.70, "Context understood"),
    
    # COMPREHENSION
    comprehension_clarity=VectorAssessment(0.70, "Clear requirements"),
    comprehension_coherence=VectorAssessment(0.75, "Coherent understanding"),
    comprehension_signal=VectorAssessment(0.65, "Good signal quality"),
    comprehension_density=VectorAssessment(0.60, "Manageable complexity"),
    
    # EXECUTION
    execution_state=VectorAssessment(0.65, "Environment mapped"),
    execution_change=VectorAssessment(0.60, "Tracking changes"),
    execution_completion=VectorAssessment(0.40, "Early stage"),
    execution_impact=VectorAssessment(0.65, "Impact understood"),
    
    # UNCERTAINTY
    uncertainty=VectorAssessment(0.50, "Moderate uncertainty"),
    
    # METADATA
    phase=CascadePhase.PREFLIGHT,
    round_num=0,
    investigation_count=0
)
```

---

## Using Assessments

### Calculate Confidences
```python
# Get tier confidences
tier_confidences = assessment.calculate_tier_confidences()

print(tier_confidences['foundation_confidence'])      # 0.65
print(tier_confidences['comprehension_confidence'])   # 0.675
print(tier_confidences['execution_confidence'])       # 0.575
print(tier_confidences['overall_confidence'])         # 0.65
```

### Determine Action
```python
# Get recommended action
action = assessment.determine_action()
print(action)  # 'investigate' or 'proceed' or 'escalate'
```

### Access Vector Scores
```python
# NEW field names with prefixes
print(assessment.foundation_know.score)          # 0.60
print(assessment.comprehension_clarity.score)    # 0.70
print(assessment.execution_state.score)          # 0.65

# Access rationale
print(assessment.foundation_know.rationale)
# "Moderate domain knowledge"

# Check investigation flags
if assessment.foundation_know.warrants_investigation:
    priority = assessment.foundation_know.investigation_priority
    print(f"Investigate KNOW (priority: {priority})")
```

---

## Migration from OLD Schema

### Using Converters

```python
from empirica.core.schemas.assessment_converters import (
    convert_old_to_new,
    convert_new_to_old
)

# Convert OLD → NEW
old_assessment = get_old_assessment()
new_assessment = convert_old_to_new(old_assessment)

# Now use NEW field names
print(new_assessment.foundation_know.score)  # Use prefix!

# Convert NEW → OLD (if needed for backwards compat)
old_again = convert_new_to_old(new_assessment)
print(old_again.know.score)  # No prefix in OLD
```

### Current State (60% Migration)

**What uses NEW schema**:
- ✅ CASCADE (internally)
- ✅ Assessor (parse_llm_response_new method)
- ✅ PersonaHarness (internally)
- ✅ Converters

**What still uses OLD schema externally**:
- External API returns (via wrappers)
- Existing tests (via mock fixtures)
- CLI output (converted automatically)

**Wrappers handle conversion automatically!**

---

## Metadata Differences

### OLD Schema Metadata
```python
assessment.assessment_id  # UUID string
assessment.task           # Task description
assessment.timestamp      # ISO timestamp string
```

### NEW Schema Metadata
```python
assessment.phase          # CascadePhase enum
assessment.round_num      # Integer (0, 1, 2...)
assessment.investigation_count  # How many investigations
```

**Note**: `task` and `assessment_id` removed in NEW schema. Use `phase` to identify context.

---

## Best Practices

### 1. Use Prefixed Field Names
```python
# ✅ CORRECT (NEW schema)
score = assessment.foundation_know.score
clarity = assessment.comprehension_clarity.score

# ❌ WRONG (OLD schema)
score = assessment.know.score  # AttributeError!
```

### 2. Use Methods for Calculations
```python
# ✅ CORRECT - Use built-in method
confidences = assessment.calculate_tier_confidences()

# ❌ WRONG - Don't calculate manually
# OLD schema had these stored, NEW calculates them
```

### 3. Check Investigation Flags
```python
# ✅ CORRECT - Check which vectors need investigation
for vector_name in ['foundation_know', 'foundation_do', 'foundation_context']:
    vector = getattr(assessment, vector_name)
    if vector.warrants_investigation:
        print(f"{vector_name} needs investigation (priority: {vector.investigation_priority})")
```

### 4. Use Converters for Compatibility
```python
# ✅ CORRECT - Use converters when needed
if needs_old_format:
    old_assessment = convert_new_to_old(new_assessment)
    return old_assessment
```

---

## Common Patterns

### Pattern 1: Check if Ready to Proceed
```python
action = assessment.determine_action()

if action == 'proceed':
    print("Ready to act!")
elif action == 'investigate':
    # Find what needs investigation
    vectors_to_investigate = []
    for attr in dir(assessment):
        if attr.startswith(('foundation_', 'comprehension_', 'execution_')):
            vector = getattr(assessment, attr)
            if vector.warrants_investigation:
                vectors_to_investigate.append(attr)
    print(f"Investigate: {vectors_to_investigate}")
```

### Pattern 2: PREFLIGHT Assessment
```python
def create_preflight_assessment(task: str) -> EpistemicAssessmentSchema:
    """Create conservative PREFLIGHT baseline."""
    return EpistemicAssessmentSchema(
        engagement=VectorAssessment(0.70, "Initial engagement"),
        foundation_know=VectorAssessment(0.55, "Limited initial knowledge"),
        foundation_do=VectorAssessment(0.60, "Capability to be verified"),
        foundation_context=VectorAssessment(0.65, "Basic context"),
        # ... other vectors with conservative scores
        phase=CascadePhase.PREFLIGHT,
        round_num=0,
        investigation_count=0
    )
```

### Pattern 3: Compare Assessments
```python
def measure_learning(preflight: EpistemicAssessmentSchema, 
                     postflight: EpistemicAssessmentSchema) -> dict:
    """Measure epistemic delta between PREFLIGHT and POSTFLIGHT."""
    return {
        'know_delta': postflight.foundation_know.score - preflight.foundation_know.score,
        'do_delta': postflight.foundation_do.score - preflight.foundation_do.score,
        'uncertainty_delta': preflight.uncertainty.score - postflight.uncertainty.score
    }
```

---

## JSON Format

### Example JSON
```json
{
  "engagement": {
    "score": 0.75,
    "rationale": "Good engagement",
    "evidence": "Clear prompt provided",
    "warrants_investigation": false,
    "investigation_priority": 0
  },
  "foundation_know": {
    "score": 0.60,
    "rationale": "Moderate knowledge",
    "warrants_investigation": true,
    "investigation_priority": 7
  },
  "phase": "PREFLIGHT",
  "round_num": 0,
  "investigation_count": 0
}
```

---

## API Methods

### EpistemicAssessmentSchema Methods

#### `calculate_tier_confidences() -> dict`
Returns dict with:
- `foundation_confidence`: Average of foundation vectors
- `comprehension_confidence`: Average of comprehension vectors  
- `execution_confidence`: Average of execution vectors
- `overall_confidence`: Weighted average of tiers

#### `determine_action() -> str`
Returns:
- `'investigate'`: Low confidence, need more info
- `'proceed'`: High confidence, ready to act
- `'escalate'`: Complex situation, need help

#### `to_dict() -> dict`
Serialize to dictionary

#### `from_dict(data: dict) -> EpistemicAssessmentSchema`
Deserialize from dictionary

---

## See Also

- [Migration Status](../wip/schema-migration/PROGRESS_60_PERCENT.md) - Current migration progress
- [OLD vs NEW Comparison](../wip/schema-migration/HALFWAY_MILESTONE.md) - Detailed comparison
- [Converter Documentation](../wip/schema-migration/PHASE1_CONVERTERS_COMPLETE.md) - How converters work

---

**Last updated**: 2025-01 (60% migration complete)  
**Status**: NEW schema is production-ready, wrappers maintain backwards compatibility
