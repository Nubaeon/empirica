# Data Flow Audit - Complete Documentation

**Status:** CRITICAL FINDINGS DOCUMENTED
**Date:** 2025-12-04
**Impact:** Statusline integration, drift detection, learning curves, audit trails all BROKEN

---

## Quick Summary

The empirica data flow violates the documented storage architecture in **three critical ways**:

1. **PREFLIGHT** writes to wrong table (cascade_metadata instead of reflexes)
2. **CHECK** stores hardcoded dummy vectors instead of submitted assessment
3. **POSTFLIGHT** missing reflex_log_path link to audit logs

**Result:** Statusline can't find epistemic state, drift detection is meaningless, learning curves show wrong data.

---

## Documents in This Audit

### 1. DATA_FLOW_INCONSISTENCIES_AUDIT.md (Main Findings)

**What:** Complete technical analysis of what's broken and why

**Contains:**
- Executive summary
- Architecture spec vs reality comparison
- Critical violations (PREFLIGHT, CHECK, POSTFLIGHT)
- Secondary issues (scattered decision logic)
- Storage path decision matrix
- Impact on dependent systems
- Testing impact analysis

**Read this for:** Understanding the exact problems and their scope

---

### 2. SPEC_VS_IMPLEMENTATION_SIDE_BY_SIDE.md (Visual Comparison)

**What:** Side-by-side code and data flow comparison

**Contains:**
- PREFLIGHT spec vs implementation
- CHECK spec vs implementation (with the hardcoded bug highlighted)
- POSTFLIGHT spec vs implementation
- The three wrong tables problem
- Decision logic duplication
- Summary table by violation

**Read this for:** Quick visual understanding of what's different

---

### 3. WHY_UNIFIED_STORAGE_MATTERS.md (Architecture Rationale)

**What:** Explains why the spec design makes sense

**Contains:**
- Problem statement
- Five critical guarantees from unified storage:
  - Consistency (ACID-C)
  - Query consistency (single query)
  - Referential integrity
  - Atomic completion
  - Audit trail continuity
- Cost analysis (runtime, code, testing)
- Lessons from distributed systems theory
- Why parallel writes ARE justified
- The correct pattern

**Read this for:** Understanding architectural principles and why scattered storage is bad

---

### 4. DATA_FLOW_FIX_ACTION_PLAN.md (Implementation Guide)

**What:** Step-by-step fix instructions

**Contains:**
- Detailed fix for each of 4 issues
- Code snippets showing exact changes
- File locations and line numbers
- Tests affected by each fix
- Implementation roadmap (phases)
- Test plan with examples
- Verification checklist
- Success criteria (before/after)
- Rollback plan

**Read this for:** Implementing the fixes

---

## Key Findings at a Glance

### The Three Violations

```
VIOLATION 1: PREFLIGHT
├─ Location: cascade_commands.py:234-254
├─ Problem: Writes to cascade_metadata (wrong table)
├─ Impact: Statusline can't find PREFLIGHT data
└─ Severity: CRITICAL

VIOLATION 2: CHECK
├─ Location: workflow_commands.py:188-196
├─ Problem: Stores hardcoded 0.75 instead of submitted vectors
├─ Impact: Drift detection meaningless, learning curves wrong
└─ Severity: CRITICAL

VIOLATION 3: POSTFLIGHT
├─ Location: cascade_commands.py:670+
├─ Problem: reflex_log_path never populated
├─ Impact: Audit trail broken, debugging impossible
└─ Severity: MEDIUM-HIGH
```

### The Storage Architecture Spec

From `STORAGE_ARCHITECTURE_COMPLETE.md`:

```
Single unified method writes to all three layers atomically:

    GitEnhancedReflexLogger.add_checkpoint()
        ├─ SQLite reflexes table (for queries)
        ├─ Git notes (for distribution + crypto signing)
        └─ JSON logs (for audit trail + full reasoning)
```

### What's Actually Happening

```
PREFLIGHT:
    ├─ cascade_metadata (WRONG TABLE) ✗
    └─ git notes (partial) ✓

CHECK:
    ├─ epistemic_assessments with hardcoded vectors (WRONG DATA) ✗
    └─ git notes ✓

POSTFLIGHT:
    ├─ epistemic_assessments (no reflex_log_path) ✗
    └─ git notes ✓
```

---

## Impact Analysis

### Statusline Dashboard

**Expected:** Complete epistemic learning curve
```
PREFLIGHT: know=0.75, uncertainty=0.25
CHECK:     know=0.92, uncertainty=0.08
POSTFLIGHT: know=0.95, uncertainty=0.05
```

**Actual:** Partial and corrupted data
```
PREFLIGHT: NOT FOUND (wrong table)
CHECK:     know=0.75, uncertainty=0.25 (HARDCODED, not submitted!)
POSTFLIGHT: know=0.95, uncertainty=0.05 (only one that works)
```

### Drift Detection

**Expected:** Accurate drift between phases
```
PREFLIGHT → CHECK: know +0.17 (correct drift detected)
```

**Actual:** Meaningless drift
```
PREFLIGHT → CHECK: know +0.0 (both have wrong data!)
```

### Learning Curves

**Expected:** Show actual knowledge growth
```
PREFLIGHT 0.75 → CHECK 0.92 → POSTFLIGHT 0.95
Shows realistic learning progression
```

**Actual:** Show false pattern
```
PREFLIGHT (missing) → CHECK 0.75 (fake) → POSTFLIGHT 0.95
Looks like huge jump at end, actually all wrong
```

### Audit Trail

**Expected:** Complete traceability
```
reflexes.reflex_log_path → JSON logs → full reasoning
```

**Actual:** Broken trail
```
PREFLIGHT: no link (data in cascade_metadata)
CHECK: no link
POSTFLIGHT: no link (reflex_log_path is NULL)
```

---

## Design Questions Answered

### Q: Why not just query cascade_metadata for PREFLIGHT?

**A:** Because statusline was designed to query `reflexes` table (the spec). Three different tables = three different query patterns = 3x code complexity + 3x test coverage.

### Q: Why is CHECK storing hardcoded vectors?

**A:** Appears to be incomplete refactoring. Old code directly inserted into `epistemic_assessments` with placeholder values. New `handle_check_submit_command()` exists but isn't wired up.

### Q: Why not populate reflex_log_path from the metadata that already exists?

**A:** The metadata exists in git notes, but it's never transferred to the `reflex_log_path` field in the database. The link between layers was never implemented.

### Q: Is there a good reason for scattered storage?

**A:** No. The spec documents that three layers should exist (SQLite + Git Notes + JSON), but they should be written **atomically in one call**, not scattered across multiple locations and times.

---

## Recommended Reading Order

1. **Start here:** `SPEC_VS_IMPLEMENTATION_SIDE_BY_SIDE.md` (5 min read)
   - Quick visual understanding of what's wrong

2. **Then read:** `WHY_UNIFIED_STORAGE_MATTERS.md` (10 min read)
   - Understand why scattered storage is bad

3. **Deep dive:** `DATA_FLOW_INCONSISTENCIES_AUDIT.md` (20 min read)
   - Complete technical analysis

4. **Implementation:** `DATA_FLOW_FIX_ACTION_PLAN.md` (reference during coding)
   - Step-by-step fixes with code examples

---

## Immediate Next Steps

### For Architects/Reviewers

1. [ ] Review the audit findings: `DATA_FLOW_INCONSISTENCIES_AUDIT.md`
2. [ ] Review the fix plan: `DATA_FLOW_FIX_ACTION_PLAN.md`
3. [ ] Confirm fixes align with `STORAGE_ARCHITECTURE_COMPLETE.md`

### For Developers

1. [ ] Implement fixes in order (PREFLIGHT → CHECK → POSTFLIGHT)
2. [ ] Follow code snippets in `DATA_FLOW_FIX_ACTION_PLAN.md`
3. [ ] Update tests as specified
4. [ ] Run integration tests from the action plan

### For QA/Testing

1. [ ] Use verification checklist in action plan
2. [ ] Test full workflow: PREFLIGHT → CHECK → POSTFLIGHT
3. [ ] Verify statusline displays correctly
4. [ ] Test drift detection accuracy
5. [ ] Verify audit trail is complete

---

## File Statistics

| Document | Size | Read Time | Purpose |
|----------|------|-----------|---------|
| DATA_FLOW_INCONSISTENCIES_AUDIT.md | ~12 KB | 20 min | Complete technical analysis |
| SPEC_VS_IMPLEMENTATION_SIDE_BY_SIDE.md | ~10 KB | 15 min | Visual code comparison |
| WHY_UNIFIED_STORAGE_MATTERS.md | ~8 KB | 10 min | Architecture rationale |
| DATA_FLOW_FIX_ACTION_PLAN.md | ~15 KB | 20 min | Implementation guide |
| README_DATA_FLOW_AUDIT.md | This file | 5 min | Navigation guide |

---

## Status Summary

### What's Broken ✗

- [x] PREFLIGHT writes to wrong table
- [x] CHECK stores hardcoded vectors
- [x] POSTFLIGHT missing audit link
- [x] Scattered storage across 3 locations
- [x] Decision logic duplicated in 3 places
- [x] Statusline integration broken
- [x] Drift detection meaningless
- [x] Learning curves show wrong data
- [x] Audit trails incomplete

### What's Documented ✓

- [x] Complete inconsistencies audit
- [x] Side-by-side spec vs implementation
- [x] Architecture rationale
- [x] Detailed fix action plan
- [x] Code snippets with line numbers
- [x] Test update guide
- [x] Verification checklist

### What Needs to Happen Next

- [ ] Review and approve audit findings
- [ ] Implement fixes in order
- [ ] Update tests as specified
- [ ] Run full integration test suite
- [ ] Verify statusline works correctly
- [ ] Deploy fixes to main branch

---

## Contact Points

### Related Documentation

- `docs/architecture/STORAGE_ARCHITECTURE_COMPLETE.md` - Storage spec
- `docs/architecture/STORAGE_ARCHITECTURE_VISUAL_GUIDE.md` - Visual reference
- `empirica/core/canonical/git_enhanced_reflex_logger.py` - Correct implementation
- `empirica/data/session_database.py` - Database schema

### Code Locations

**Broken code:**
- `empirica/cli/command_handlers/cascade_commands.py` (PREFLIGHT, POSTFLIGHT)
- `empirica/cli/command_handlers/workflow_commands.py` (CHECK)

**Tests to update:**
- `tests/unit/cascade/test_preflight.py`
- `tests/unit/cascade/test_check.py`
- `tests/unit/cascade/test_postflight.py`

---

## Questions?

1. **"What's the priority?"** → All three violations are CRITICAL. PREFLIGHT and CHECK block statusline entirely.
2. **"How long to fix?"** → ~5 hours total (see DATA_FLOW_FIX_ACTION_PLAN.md roadmap)
3. **"Will this break anything?"** → Tests will fail until updated (see action plan for which ones)
4. **"Is this blocking?"** → YES. Statusline integration cannot work without these fixes.

---

**Audit Complete. Ready for implementation.**

