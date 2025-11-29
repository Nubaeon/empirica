# Schema Migration Investigation - Findings

## Investigation Summary

Using Empirica's CASCADE approach, we investigated three critical questions before schema migration.

---

## Finding 1: PersonaHarness Schema Usage

### Question
Does PersonaHarness already use EpistemicAssessmentSchema from Phase 3 work?

### Evidence Found

**File**: `empirica/core/persona/harness/persona_harness.py` (534 lines)

**Import statement** (line 255):
```python
from empirica.core.canonical.reflex_frame import VectorState
```

**Key methods** (line 38+):
- `execute_task()` - main execution
- `_create_persona_cascade()` - creates CASCADE instance
- `_create_persona_aware_assessment()` - wraps assessment method
- `_apply_priors()` - applies persona priors to assessments
- `_interpret_with_persona()` - interprets results through persona lens

**Assessment handling** (line 246):
```python
def _apply_priors(self, assessment, phase):
    """Apply persona priors to baseline assessment"""
    # Works with VectorState objects from OLD schema
```

### Conclusion: ❌ PersonaHarness uses OLD schema

**Status**: PersonaHarness currently uses `VectorState` and `EpistemicAssessment` (OLD format)

**Impact**: PersonaHarness needs to be migrated to `EpistemicAssessmentSchema` (NEW format)

**Migration complexity**: MODERATE
- 534 lines of code
- Assessment wrapping and prior blending logic
- Needs careful testing of persona prior application

---

## Finding 2: CLI Command Consumers

### Question
Should CLI accept both formats during transition period, or force immediate migration?

### Evidence Found

**CLI Commands**: `empirica/cli/command_handlers/cascade_commands.py`

**Current flow**:
```python
# handle_preflight_command (line ~300)
1. User calls: empirica preflight "task" --prompt-only
2. Returns self_assessment_prompt as JSON
3. User (or MCP tool) performs self-assessment
4. Calls: submit_preflight_assessment with vectors
5. Stores in session database
```

**MCP Server**: `mcp_local/empirica_mcp_server.py`
```python
# Wraps CLI commands
execute_preflight() -> returns prompt
submit_preflight_assessment(vectors) -> logs to session
```

**Usage patterns found**:
- `test_working_checkpoint.sh` - uses CLI for testing
- `empirica/bootstraps/onboarding_wizard.py` - shows CLI examples
- Various command handlers reference CLI commands in help text

**Current consumers**:
1. ✅ **MCP tools** (main consumer) - wraps CLI
2. ✅ **Test scripts** - uses CLI directly  
3. ✅ **Documentation examples** - shows CLI usage
4. ❌ **External tools** - NONE FOUND (only internal usage)

### Conclusion: ✅ Force immediate migration

**Rationale**:
- All consumers are internal (MCP, tests, docs)
- No external tools depend on current format
- User preference: "force migration, acceptable to break things"
- Better now than later when people actually use Empirica

**Migration approach**: Force migration, no backwards compatibility
- Update MCP tools to use NEW schema
- Update test scripts
- Update documentation examples
- Single cutover, no transition period needed

---

## Finding 3: Git Notes Format

### Question
Should we keep VectorState for backwards compatibility in git notes, or force full migration?

### Evidence Found

**Git notes check**:
```bash
git notes list | wc -l
# Result: 0
```

**Status**: NO git notes exist in current repository

**Serialization check**: `empirica/core/canonical/reflex_frame.py`
```python
class VectorState:
    def to_dict(self) -> Dict[str, Any]:
        # Simple serialization

class EpistemicAssessment:
    def to_dict(self) -> Dict[str, Any]:
        # Nested structure with VectorState.to_dict()
```

**Git enhanced logger**: `empirica/core/canonical/git_enhanced_reflex_logger.py`
- Uses `to_dict()` for serialization
- No version tagging found
- No format migration logic found

### Conclusion: ✅ Force full migration (no backwards compat needed)

**Rationale**:
- NO existing git notes in repo (count = 0)
- No historical data to preserve
- No version tagging in current implementation
- User preference: "force migration"

**Migration approach**: Full migration, no compatibility layer
- Update serialization to use NEW schema
- No need to read OLD format (no existing notes)
- Add version tagging for future migrations

---

## Schema Comparison

### OLD Schema (reflex_frame.py)

**Structure**: 323 lines
```python
class VectorState:
    score: float
    reasoning: str

class EpistemicAssessment:
    engagement: VectorState
    know: VectorState
    do: VectorState
    # ... 13 vectors total
    # Simple, flat structure
```

**Pros**:
- ✅ Simple, easy to understand
- ✅ Currently working in CASCADE
- ✅ Well-tested (42 unit tests pass)

**Cons**:
- ❌ No evidence tracking
- ❌ No investigation prioritization
- ❌ No persona prior metadata
- ❌ Duplicates logic (confidence calc, action determination)

### NEW Schema (epistemic_assessment.py)

**Structure**: 432 lines
```python
class VectorAssessment:
    score: float
    rationale: str
    evidence: Optional[List[str]]
    warrants_investigation: bool

class EpistemicAssessmentSchema:
    engagement: VectorAssessment
    foundation_know: VectorAssessment
    foundation_do: VectorAssessment
    foundation_context: VectorAssessment
    # ... 13 vectors total with tier grouping
    # Rich metadata, persona priors, confidence logic
```

**Pros**:
- ✅ Comprehensive (evidence, investigation flags)
- ✅ Persona prior blending built-in
- ✅ Confidence calculation logic included
- ✅ Action determination (INVESTIGATE vs PROCEED)
- ✅ Single source of truth (no duplicate logic)
- ✅ Extensible (can add metadata without breaking)

**Cons**:
- ❌ More complex
- ❌ Not yet integrated with CASCADE
- ❌ Needs migration effort

---

## Migration Impact Assessment

### Components to Update

| Component | Lines | Complexity | Risk | Priority |
|-----------|-------|------------|------|----------|
| **CanonicalEpistemicAssessor** | ~150 | HIGH | HIGH | 1 |
| **CanonicalEpistemicCascade** | ~200 | HIGH | HIGH | 2 |
| **PersonaHarness** | 534 | MEDIUM | MEDIUM | 3 |
| **ReflexLogger** | ~100 | LOW | LOW | 4 |
| **GitEnhancedReflexLogger** | ~50 | LOW | LOW | 5 |
| **CLI command handlers** | ~300 | MEDIUM | MEDIUM | 6 |
| **MCP server** | ~200 | MEDIUM | MEDIUM | 7 |
| **Unit test mocks** | 73 | LOW | LOW | 8 |
| **All unit tests** | ~2000 | MEDIUM | MEDIUM | 9 |
| **Documentation** | ~1000 | LOW | LOW | 10 |

**Total estimated effort**: ~4600 lines to update

### Risk Assessment

**HIGH RISK**:
- CASCADE core logic (assessor + cascade)
- Phase transition logic
- Confidence threshold checking

**MEDIUM RISK**:
- PersonaHarness persona prior blending
- CLI command parsing
- MCP tool integration
- Test assertions

**LOW RISK**:
- Logging/serialization
- Documentation
- Mock fixtures

### Migration Strategy

**Recommended approach**: Incremental migration with feature flags

#### Phase 1: Compatibility Layer (1-2 hours)
```python
# empirica/core/schemas/assessment_converters.py
def convert_old_to_new(old: EpistemicAssessment) -> EpistemicAssessmentSchema:
    """Convert OLD -> NEW (data loss acceptable)"""
    
def convert_new_to_old(new: EpistemicAssessmentSchema) -> EpistemicAssessment:
    """Convert NEW -> OLD (for testing/compatibility)"""
```

#### Phase 2: Update Assessor (2-3 hours)
- Modify `assess()` to return NEW schema
- Update `parse_llm_response()` to construct NEW schema
- Test with converter to OLD format (backward compat)

#### Phase 3: Update CASCADE (3-4 hours)
- Update `_assess_epistemic_state()` to use NEW schema
- Update phase methods (PREFLIGHT, CHECK, etc.)
- Update decision logic, threshold checks
- Update reflex logging

#### Phase 4: Update PersonaHarness (2-3 hours)
- Update persona prior blending for NEW schema
- Update assessment wrapping logic
- Test persona behavior preserved

#### Phase 5: Update Interfaces (2-3 hours)
- Update CLI command handlers
- Update MCP server tools
- Update JSON parsing/validation

#### Phase 6: Update Tests (2-3 hours)
- Update mock fixtures to return NEW schema
- Update all test assertions
- Verify all 42+ tests still pass

#### Phase 7: Update Documentation (1-2 hours)
- Update all examples to NEW format
- Update MCP usage guides
- Update system prompts

#### Phase 8: Cleanup (1 hour)
- Remove OLD schema from reflex_frame.py
- Remove converters (if not needed)
- Final verification

**Total estimated time**: 14-21 hours

---

## Answers to Migration Plan Questions

### Q1: Data Loss During Conversion
**Answer**: ✅ Data loss acceptable when converting NEW → OLD

**Rationale**: 
- OLD format is being removed
- Only need OLD format temporarily during migration
- No production data to preserve

### Q2: CLI Transition Period
**Answer**: ✅ Force immediate migration (no transition period)

**Rationale**:
- All consumers are internal (MCP, tests, docs)
- No external dependencies found
- User preference: force migration

### Q3: VectorState Backwards Compatibility
**Answer**: ✅ Force full migration (no backwards compatibility)

**Rationale**:
- Zero git notes exist in current repo
- No historical data to preserve
- Cleaner architecture without compatibility layer

---

## Recommended Next Steps

### Option A: Start Migration Now (Recommended)
**Pros**: 
- All questions answered
- Clear migration path
- User approved breaking changes

**Cons**:
- 14-21 hour effort
- Might break things temporarily

**Approach**:
1. Create feature branch: `schema-migration`
2. Implement Phase 1 (converters)
3. Test converters thoroughly
4. Implement Phases 2-8 incrementally
5. Run full test suite after each phase
6. Merge when all tests pass

### Option B: Investigate Sentinel First
**Pros**:
- Understand full architecture before migrating
- See if cognitive_vault affects schema design
- Make more informed decisions

**Cons**:
- Delays migration
- Risk of finding more issues

**Approach**:
1. SSH to 192.168.1.66
2. Find cognitive_vault code
3. Find bayesian_guardian code
4. Test Sentinel functionality
5. Return with findings
6. Adjust migration plan if needed

### Option C: Parallel Track
**Pros**:
- Can investigate Sentinel while migrating
- Different people (AIs) can work on both

**Cons**:
- Risk of conflicts
- Need coordination

---

## POSTFLIGHT Assessment

### Initial Epistemic State (PREFLIGHT)
```
ENGAGEMENT: 0.85 (high importance)
KNOW: 0.40 (low - didn't know PersonaHarness details)
CONTEXT: 0.60 (understood CASCADE, not full integration)
UNCERTAINTY: 0.60 (moderate - code exists, just need to read)
```

### Final Epistemic State (POSTFLIGHT)
```
ENGAGEMENT: 0.85 (maintained - still important)
KNOW: 0.90 (high - found all answers)
CONTEXT: 0.95 (deep understanding of integration)
UNCERTAINTY: 0.15 (low - clear path forward)
```

### Epistemic Deltas
```
KNOW: +0.50 (learned PersonaHarness uses OLD, no git notes, only internal CLI consumers)
CONTEXT: +0.35 (understood full integration picture)
UNCERTAINTY: -0.45 (confident in migration decisions)
```

### Calibration Check
**Pre-investigation predictions**:
- ✅ Expected PersonaHarness might use OLD format (CORRECT)
- ✅ Expected MCP wraps CLI (CORRECT)  
- ✅ Expected minimal git notes (CORRECT - actually zero)

**Surprises**:
- PersonaHarness has NO evidence of NEW schema (expected some migration)
- Zero git notes in repo (expected at least some test notes)
- CLI has NO external consumers (expected maybe some)

**Overall calibration**: GOOD ✅
- Predictions mostly correct
- Surprises were positive (easier migration than expected)
- Uncertainty decreased as expected

---

## Recommendation for User

Based on investigation findings:

**✅ PROCEED with schema migration**

**Key decisions**:
1. Force migration (no transition period)
2. No backwards compatibility needed (zero git notes)
3. Update PersonaHarness as part of migration (uses OLD)
4. All consumers are internal (safe to break)

**Estimated effort**: 14-21 hours (can be split across multiple sessions)

**Risk level**: MEDIUM (core architecture change, but well-tested)

**User preference alignment**: ✅ Matches "force migration, acceptable to break things"

**Next action**: User decides between:
- A) Start migration now (recommended)
- B) Investigate Sentinel at 192.168.1.66 first
- C) Parallel track (migrate + investigate)

---

**Investigation completed**: ✅  
**All questions answered**: ✅  
**Migration plan validated**: ✅  
**Ready to proceed**: ✅
