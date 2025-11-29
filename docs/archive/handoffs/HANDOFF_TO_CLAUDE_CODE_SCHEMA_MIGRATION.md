# Handoff to Claude Code - Schema Migration & Cognitive Vault

## Context: What Rovo Dev Learned

### Problem Solved: Unit Test Hanging
**Issue**: Unit tests in `tests/unit/cascade/` were hanging because `CanonicalEpistemicAssessor.assess()` expected LLM input without a reasoning engine available.

**Solution**: Created mock fixtures in `tests/unit/cascade/conftest.py` that return baseline `EpistemicAssessment` objects directly.

**Result**: ✅ 42 tests pass in 0.17s (previously hung indefinitely)

### Critical Discovery: Two Assessment Schemas Exist

We have **two competing assessment formats** that need to be unified:

#### 1. OLD Schema (Currently Used by CASCADE)
**Location**: `empirica/core/canonical/reflex_frame.py`

```python
class EpistemicAssessment:
    engagement: VectorState
    know: VectorState
    do: VectorState
    context: VectorState
    # ... simple VectorState(score, reasoning) structure
```

**Used by**:
- ✅ `CanonicalEpistemicCascade` (core CASCADE logic)
- ✅ `CanonicalEpistemicAssessor` (assessment generation)
- ✅ All unit tests in `tests/unit/cascade/`
- ✅ Internal CASCADE phase transitions

**Pros**: Currently working, well-tested
**Cons**: Simple, not extensible, duplicates logic

#### 2. NEW Schema (Your Phase 3 Work)
**Location**: `empirica/core/schemas/epistemic_assessment.py`

```python
class EpistemicAssessmentSchema:
    engagement: VectorAssessment
    foundation_know: VectorAssessment
    foundation_do: VectorAssessment
    # ... detailed VectorAssessment with evidence, warrants_investigation
```

**Features**:
- 445 lines, single source of truth
- Persona prior blending
- Confidence calculation logic
- Action determination (INVESTIGATE vs PROCEED)
- Evidence tracking, investigation prioritization

**Intended for**:
- CLI commands (`empirica preflight`, etc.)
- MCP tools (wrapping CLI)
- PersonaHarness
- Sentinel coordination
- Multi-persona workflows

**Pros**: Comprehensive, extensible, unified
**Cons**: Not yet integrated with CASCADE core

### Architecture Understanding

#### CLI = MCP (User Insight Confirmed)
- MCP tools are thin wrappers around CLI commands
- No special "MCP server" logic needed for assessments
- Domain expertise lives in templates (YAML), not code
- Both CLI and MCP should use same `EpistemicAssessmentSchema`

#### Empirica Works Standalone (Without Sentinel)
**Without Sentinel**:
- ✅ Single-agent CASCADE
- ✅ PREFLIGHT → INVESTIGATE → CHECK → ACT → POSTFLIGHT
- ✅ 13-vector epistemic tracking
- ✅ Git checkpoints, goals, handoff reports

**With Sentinel** (advanced use cases):
- ➕ Multi-persona coordination
- ➕ COMPOSE phase (merge insights)
- ➕ Conflict arbitration
- ➕ Hierarchical orchestration

**Sentinel location**: `192.168.1.66` (empirica-server)
- cognitive_vault - partially implemented
- bayesian_guardian - partially implemented
- Not yet fully tested

### Current State of Assessment Generation

#### Where LLM Calls Happen

**CanonicalEpistemicAssessor** (`empirica/core/canonical/canonical_epistemic_assessment.py`):
```python
async def assess(self, task: str, context: dict, profile=None):
    # Generates a self_assessment_prompt
    # Returns dict with prompt, NOT final assessment
    # Expects external LLM to execute prompt and return values
```

**Problem**: This method returns a **prompt**, not an assessment. Someone needs to:
1. Take the prompt
2. Send it to an LLM (Sentinel, API, whatever)
3. Parse LLM response
4. Return `EpistemicAssessment` object

**Current workarounds**:
- Unit tests: Mock it (returns baseline assessment directly)
- MCP tools: User manually assesses, submits via `submit_preflight_assessment()`
- CLI: ???

### What Needs to Happen: Schema Migration

#### Goal
**Single unified schema** used everywhere:
- CASCADE core logic
- CLI commands
- MCP tools
- PersonaHarness
- Sentinel coordination
- Unit tests

#### Migration Path

**Phase 1: Understand Current Usage**
1. Find all places that create/use `EpistemicAssessment` (OLD)
2. Find all places that create/use `EpistemicAssessmentSchema` (NEW)
3. Map dependencies and call sites

**Phase 2: Create Compatibility Layer**
1. Add converter: `OLD → NEW` format
2. Add converter: `NEW → OLD` format
3. Allow both to coexist temporarily

**Phase 3: Migrate CASCADE Core**
1. Update `CanonicalEpistemicAssessor` to return `EpistemicAssessmentSchema`
2. Update `CanonicalEpistemicCascade` to use `EpistemicAssessmentSchema`
3. Update phase logic (PREFLIGHT, CHECK, etc.)
4. Update reflex_logger, git_notes storage

**Phase 4: Update Tests**
1. Update unit test mocks to return `EpistemicAssessmentSchema`
2. Update test assertions to match new format
3. Verify all 42+ tests still pass

**Phase 5: Update Documentation**
1. Fix any docs referencing OLD format
2. Update examples to use NEW format
3. Update MCP usage guides
4. Update system prompts if needed

**Phase 6: Remove OLD Schema**
1. Delete `EpistemicAssessment` from `reflex_frame.py`
2. Delete any OLD format converters
3. Clean up imports
4. Final test pass

### Critical Questions for You (Claude Code)

#### 1. Cognitive Vault & Bayesian Guardian
**User mentioned these exist on `192.168.1.66`**:
- What is cognitive_vault? What does it do?
- What is bayesian_guardian? What does it do?
- Are they related to `EpistemicAssessmentSchema`?
- Do they need to be integrated into migration?

#### 2. LLM Execution Strategy
**Who executes the self-assessment prompt?**

Current flow (broken):
```
Assessor.assess() 
  → returns prompt
  → ??? who calls LLM ???
  → returns assessment
```

Should it be:
- A) Sentinel executes prompts (192.168.1.66 server)
- B) CLI calls `llm` command locally
- C) MCP expects user to self-assess manually
- D) PersonaHarness has LLM client built-in
- E) Something else?

**User's context**: "Sentinel can run inference at 192.168.1.66 but not fully tested yet"

#### 3. Schema Design Questions

**EpistemicAssessmentSchema** has:
- `VectorAssessment(score, rationale, evidence, warrants_investigation)`
- Persona prior blending logic
- Confidence calculation logic

**Should CASCADE use all these features?**
- Does CASCADE need persona priors? (it's single-agent)
- Does CASCADE need evidence tracking? (or is that for Sentinel?)
- Should CASCADE determine `warrants_investigation` per vector?

**Or is there a simpler interface?**
- Maybe CASCADE just needs `{vector: score}` 
- Schema handles the rich metadata
- Converters map between them

#### 4. Persona Harness Integration

**Your Phase 3 work** created:
- Universal PersonaHarness (wraps any persona)
- Domain-specific personas (security, UX, ML templates)
- Sentinel orchestration (multi-persona)

**Does PersonaHarness use EpistemicAssessmentSchema?**
- If yes, good! CASCADE should too
- If no, what does it use?

**Should CASCADE and PersonaHarness share schema?**
- Probably yes for consistency
- But maybe different interfaces?

### Constraints & Principles

#### From User
> "The foundational docs and code is strong, this won't break anything too much, but if it does better now than later when people are actually using Empirica, now its just me and many AIs"

**Translation**: 
- ✅ OK to make breaking changes now
- ✅ Better to fix architecture issues early
- ✅ No production users yet
- ⚠️ But don't break core functionality

#### Design Principles (User's Insights)
1. **CLI = MCP** - They're equivalent, use same schema
2. **Domain in data, not code** - YAML templates, not specialized classes
3. **Empirica works standalone** - Don't require Sentinel for basic usage
4. **13 vectors are fixed** - Don't make them configurable (they ARE the theory)
5. **Thresholds/priors configurable** - But vectors themselves are not

### Files to Review

#### Assessment Schemas
- `empirica/core/canonical/reflex_frame.py` - OLD EpistemicAssessment
- `empirica/core/schemas/epistemic_assessment.py` - NEW EpistemicAssessmentSchema

#### Assessment Generation
- `empirica/core/canonical/canonical_epistemic_assessment.py` - Assessor
- `empirica/core/metacognitive_cascade/metacognitive_cascade.py` - CASCADE

#### Persona System (Your Work)
- `empirica/core/persona/persona_profile.py` - Persona definitions
- `empirica/core/persona/harness/persona_harness.py` - Universal harness
- `empirica/core/canonical/canonical_goal_orchestrator.py` - Goal decomposition

#### Tests
- `tests/unit/cascade/conftest.py` - Mock fixtures (uses OLD schema)
- `tests/unit/cascade/test_*.py` - All CASCADE tests (use OLD schema)

#### Documentation
- `docs/guides/CLI_WORKFLOW_COMMANDS_COMPLETE.md` - CLI reference
- `docs/system-prompts/comprehensive/COMPLETE_MCP_TOOL_REFERENCE.md` - MCP tools
- `/home/yogapad/.rovodev/EMPIRICA_MCP_USAGE.md` - Your MCP guide

### Success Criteria

After migration, we should have:

1. ✅ **Single unified schema** used everywhere
2. ✅ **All 42+ unit tests pass** (no regression)
3. ✅ **CLI commands work** with new schema
4. ✅ **MCP tools work** with new schema
5. ✅ **PersonaHarness uses** same schema
6. ✅ **Documentation updated** to reflect new schema
7. ✅ **No duplicate assessment logic** anywhere
8. ✅ **Clear LLM execution strategy** (Sentinel? CLI? where?)

### Questions for User

Before you start, please answer:

1. **Cognitive Vault**: What is it? Should it be part of migration?
2. **Sentinel LLM**: Should we test against 192.168.1.66 first?
3. **PersonaHarness**: Does it use EpistemicAssessmentSchema already?
4. **Breaking changes**: OK to break CLI/MCP interfaces if needed?
5. **Timeline**: High priority or can it wait for Sentinel testing?

### Recommended Approach

**My suggestion** (Rovo Dev's opinion):

1. **First**: Investigate what exists on 192.168.1.66
   - What is cognitive_vault?
   - What is bayesian_guardian?
   - How do they relate to assessments?

2. **Second**: Map current assessment usage
   - Where is OLD schema used?
   - Where is NEW schema used?
   - What breaks if we unify?

3. **Third**: Design compatibility layer
   - Converters between formats
   - Allow coexistence during transition

4. **Fourth**: Migrate CASCADE incrementally
   - One phase at a time
   - Test after each change
   - Roll back if broken

5. **Fifth**: Update docs and tests
   - Fix all references
   - Update examples
   - Verify nothing breaks

6. **Sixth**: Remove OLD schema
   - Clean up duplicates
   - Final verification

**Don't rush**. Better to understand the full picture before changing core architecture.

### What Rovo Dev Did

- ✅ Fixed unit test hanging with mocks
- ✅ Documented two competing schemas
- ✅ Identified migration need
- ✅ Created this handoff doc
- ⏸️ Waiting for your guidance on Sentinel/cognitive_vault

### Next Session Goals

For Claude Code's next session:

1. Answer critical questions above
2. Create detailed migration plan
3. Map all assessment usage sites
4. Design compatibility layer
5. Begin migration (if user approves)

Or if needed:
1. Investigate 192.168.1.66 Sentinel server
2. Document cognitive_vault and bayesian_guardian
3. Test existing Sentinel functionality
4. Then plan migration with full context

---

**Handoff from**: Rovo Dev  
**Handoff to**: Claude Code  
**Session date**: 2025-01-XX  
**Status**: Unit tests fixed ✅, Schema migration planned ⏳  
**Blocker**: Need Sentinel/cognitive_vault context  
**User preference**: "Better now than later" - OK to make breaking changes
