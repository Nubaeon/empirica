# Schema Migration - What I Know & Don't Know

## What I KNOW ✅

### 1. OLD Schema Location
**File**: `empirica/core/canonical/reflex_frame.py`

**Structure**:
```python
@dataclass
class VectorState:
    score: float
    rationale: str  # NOT "reasoning"!
    evidence: Optional[str] = None
    warrants_investigation: bool = False
    investigation_priority: Optional[str] = None
    investigation_reason: Optional[str] = None

@dataclass
class EpistemicAssessment:
    # GATE
    engagement: VectorState
    engagement_gate_passed: bool
    
    # FOUNDATION (Tier 0)
    know: VectorState
    do: VectorState
    context: VectorState
    foundation_confidence: float
    
    # COMPREHENSION (Tier 1)
    clarity: VectorState
    coherence: VectorState
    signal: VectorState
    density: VectorState
    comprehension_confidence: float
    
    # EXECUTION (Tier 2)
    state: VectorState
    change: VectorState
    completion: VectorState
    impact: VectorState
    execution_confidence: float
    
    # UNCERTAINTY
    uncertainty: VectorState
    
    # OVERALL
    overall_confidence: float
    recommended_action: Action
    
    # METADATA (no phase field!)
    assessment_id: str
    timestamp: str
    task: str = ""
```

### 2. NEW Schema Location
**File**: `empirica/core/schemas/epistemic_assessment.py`

**Structure**:
```python
@dataclass
class VectorAssessment:
    score: float
    rationale: str
    evidence: Optional[str] = None
    warrants_investigation: bool = False
    investigation_priority: int = 0  # int not str!

@dataclass
class EpistemicAssessmentSchema:
    # GATE
    engagement: VectorAssessment
    
    # FOUNDATION (prefixed with "foundation_")
    foundation_know: VectorAssessment
    foundation_do: VectorAssessment
    foundation_context: VectorAssessment
    
    # COMPREHENSION (prefixed with "comprehension_")
    comprehension_clarity: VectorAssessment
    comprehension_coherence: VectorAssessment
    comprehension_signal: VectorAssessment
    comprehension_density: VectorAssessment
    
    # EXECUTION (prefixed with "execution_")
    execution_state: VectorAssessment
    execution_change: VectorAssessment
    execution_completion: VectorAssessment
    execution_impact: VectorAssessment
    
    # UNCERTAINTY
    uncertainty: VectorAssessment
    
    # METADATA (includes phase, persona info)
    task: Optional[str] = None
    phase: Optional[str] = None
    timestamp: Optional[str] = None
    assessment_id: Optional[str] = None
    persona_priors: Optional[Dict] = None
    persona_profile: Optional[str] = None
```

### 3. Key Differences Found

| Aspect | OLD (reflex_frame.py) | NEW (epistemic_assessment.py) |
|--------|----------------------|-------------------------------|
| Vector class | `VectorState` | `VectorAssessment` |
| Vector fields | Same! (score, rationale, evidence, warrants_investigation) | Same! |
| investigation_priority | `Optional[str]` | `int` (0-10) |
| investigation_reason | Has this field | Doesn't have this field |
| Vector names | `know`, `do`, `context` | `foundation_know`, `foundation_do`, `foundation_context` |
| Tier confidence | Stored in assessment | Calculated on demand? |
| Phase field | NO `phase` field | Has `phase` field |
| Persona fields | NO persona fields | Has `persona_priors`, `persona_profile` |

### 4. CRITICAL Discovery

**The OLD VectorState ALREADY has most NEW features!**
- ✅ Has `rationale` (not `reasoning`)
- ✅ Has `evidence`
- ✅ Has `warrants_investigation`
- ✅ Has investigation fields

**This means**:
- The schemas are MORE similar than expected
- Main differences: field naming (prefixes) and metadata
- Conversion is simpler than I thought!

## NEW Understanding - 4 Vector Classes ✅

After investigation, found 4 different vector classes:

### 1. **reflex_frame.py** - OLD CASCADE schema (MIGRATE THIS)
```python
class VectorState:
    score, rationale, evidence, warrants_investigation
    investigation_priority: Optional[str]
    investigation_reason: Optional[str]
```
**Used by**: CASCADE, PersonaHarness
**Status**: Target for migration

### 2. **epistemic_assessment.py** - NEW canonical schema (MIGRATE TO THIS)
```python
class VectorAssessment:
    score, rationale, evidence, warrants_investigation
    investigation_priority: int (0-10)
```
**Used by**: CLI, MCP (intended)
**Status**: Target schema

### 3. **metacognition_12d_monitor.py** - Independent monitoring system
```python
class VectorAssessment:
    name, value, confidence, description, thresholds
```
**Used by**: MetacognitionMonitor (separate system)
**Status**: INDEPENDENT - don't touch

### 4. **twelve_vector_self_awareness.py** - Enum for display
```python
class VectorState(Enum):
    HIGH_CONFIDENCE, MODERATE, LOW_CONFIDENCE
```
**Used by**: Display/visualization
**Status**: INDEPENDENT - don't touch

**Conclusion**: Only migrate #1 → #2. Leave #3 and #4 alone.

## NEW Understanding - Schema Methods ✅

### EpistemicAssessmentSchema Methods

1. **`to_nested_dict()`** - Returns nested format for CLI/MCP
2. **`to_flat_dict()`** - Returns flat scores for storage
3. **`from_nested_dict()`** - Parse from CLI/MCP input
4. **`apply_persona_priors()`** - Blend with persona expertise
5. **`calculate_tier_confidences()`** - Calculate foundation/comprehension/execution confidence
6. **`determine_action()`** - Returns "proceed", "investigate", or "escalate"

**Key findings**:
- NEW schema calculates tier confidences (not stored)
- OLD schema stores tier confidences
- NEW has persona prior blending built-in
- Action determination is similar but returns strings not enums

## What I DON'T KNOW ❌

### 1. Multiple VectorState/VectorAssessment Classes
**Found via grep**:
```
empirica/core/schemas/epistemic_assessment.py:32:class VectorAssessment:
empirica/core/metacognition_12d_monitor/metacognition_12d_monitor.py:40:class VectorAssessment:
empirica/core/metacognition_12d_monitor/twelve_vector_self_awareness.py:24:class VectorState(Enum):
empirica/core/canonical/reflex_frame.py:36:class VectorState:
```

**Questions**:
- ❓ Are there FOUR different vector classes?
- ❓ Which one is the "real" OLD schema?
- ❓ Which one is the "real" NEW schema?
- ❓ Are metacognition_12d_monitor classes independent?
- ❓ Will migration break metacognition_12d_monitor?

**Need to investigate**: Open all 4 files and compare structures

### 2. EpistemicAssessmentSchema Methods
**Need to check**:
- ❓ `calculate_overall_confidence()` - How does it work?
- ❓ `determine_action()` - What does it return?
- ❓ `apply_persona_priors()` - How are priors applied?
- ❓ `to_dict()` / `from_dict()` - Serialization format
- ❓ Does NEW schema have tier confidence fields?

**Need to investigate**: Open epistemic_assessment.py and read all methods

### 3. Converter Error
**My converter assumes**:
- OLD VectorState has `score` and `reasoning` fields
- But ACTUAL OLD VectorState has `score` and `rationale` fields!

**This means**:
- ❌ My converter is WRONG
- ❌ My tests will fail
- ✅ Need to fix converter before proceeding

### 4. PersonaHarness Usage
**Found**: PersonaHarness imports OLD VectorState
```python
from empirica.core.canonical.reflex_frame import VectorState
```

**Questions**:
- ❓ Does PersonaHarness create OLD EpistemicAssessment objects?
- ❓ Or does it just manipulate VectorState objects?
- ❓ How does it apply persona priors?
- ❓ Will it break when we migrate to NEW schema?

**Need to investigate**: Read PersonaHarness more carefully

### 5. CASCADE Usage
**Need to check**:
- ❓ How does CASCADE create assessments?
- ❓ Does it call `assessor.assess()` which returns what?
- ❓ How does it pass assessments between phases?
- ❓ Does it serialize/deserialize assessments?

### 6. Tier Confidence Calculation
**OLD schema**:
- Stores `foundation_confidence`, `comprehension_confidence`, `execution_confidence`

**NEW schema**:
- Has `calculate_overall_confidence()` method
- ❓ Does it also calculate tier confidences?
- ❓ Or are they stored?
- ❓ How do we convert?

## PHASE 2: Understanding Assessor ✅

### Current Assessor Flow

**`assess()` method**:
1. Generates `self_assessment_prompt`
2. Returns dict with prompt (NOT EpistemicAssessment)
3. External LLM executes prompt
4. `parse_llm_response()` converts JSON to EpistemicAssessment

**Key insight**: Assessor already returns structured data, not OLD schema objects directly.

### What parse_llm_response() Does

1. Parses JSON from LLM (handles markdown code blocks)
2. Creates OLD VectorState objects from JSON
3. Calculates tier confidences
4. Determines recommended action
5. Returns OLD EpistemicAssessment

### Migration Strategy for Assessor

**Option A**: Keep current flow, just change return type
- `assess()` still returns dict with prompt
- `parse_llm_response()` returns NEW schema instead of OLD
- Minimal changes to interface

**Option B**: Make assessor schema-agnostic
- Return prompt dict (no schema)
- Separate parser for OLD format
- Separate parser for NEW format
- Caller chooses which to use

**Recommendation**: Option A - simpler, less breaking

## What I Need to Do Next

### Step 1: Understand the landscape ✅ CURRENT
1. ✅ Check all 4 VectorState/VectorAssessment classes
2. ✅ Compare their structures
3. ✅ Determine which are relevant for migration
4. ⏳ Document findings

### Step 2: Fix My Converter
1. Update converter to use `rationale` not `reasoning`
2. Handle `investigation_priority` type difference (str vs int)
3. Handle `investigation_reason` (OLD has it, NEW doesn't)
4. Fix tier confidence calculation
5. Test converter

### Step 3: Understand NEW Schema Methods
1. Read `calculate_overall_confidence()`
2. Read `determine_action()`
3. Read serialization methods
4. Document behavior

### Step 4: Test Converter
1. Run tests
2. Fix any failures
3. Add more edge case tests

### Step 5: Plan Next Phase
Based on what I learn, determine:
- Is migration harder or easier than expected?
- What are the real blockers?
- What can break?

## Epistemic State

```
KNOW: 0.60 (know OLD structure, know NEW exists, don't know details)
CONTEXT: 0.70 (understand migration goal, don't know all dependencies)
UNCERTAINTY: 0.50 (moderate - need to investigate multiple classes)
```

**Recommended Action**: INVESTIGATE before proceeding

**Next**: Check all 4 vector classes to understand landscape
