# Empirica Production Readiness Checklist

**Status:** IN PROGRESS - All Work Assigned
**Date:** December 5, 2025
**Target Completion:** December 19, 2025 (2 weeks)

---

## Overview

Empirica is **functionally complete** and **architecturally sound**, but needs final cleanup before production deployment. This checklist tracks all remaining work across three AI agents.

### Success Definition
✅ All unit tests pass (770+ tests)
✅ All integration tests pass
✅ All production documentation accurate
✅ No references to deprecated APIs
✅ Database schema uniform (reflexes only)
✅ MCO configuration fully tested
✅ Ready for user deployment

---

## TIER 1: CRITICAL PATH (Must Complete)

### Claude Code: Cognitive Load + Feedback Loops ✅ **COMPLETE**

- [x] Fix statusline heuristics → real DENSITY measurement
- [x] Create `feedback_loops.yaml` configuration system (880 lines)
- [x] Add feedback loop logic to `decision_utils.py`
- [x] Integrate into statusline display
- [x] Document architecture (migration spec + handoff for Sonnet)
- [x] Commit to main (2 commits)

**Outcome:** Cognitive load is now real epistemic measurement, not heuristics.

---

### Claude Sonnet: Database Schema Migration 🔄 **IN PROGRESS**

**Task:** Migrate from 4 deprecated tables → 1 canonical reflexes table

**Handoff Document:** `HANDOFF_TO_SONNET_DATABASE_MIGRATION.md`

#### Phase 1: Code Migration (Est. 6 hours)
- [ ] Update `session_database.py` (remove 4 write methods, 3 read methods, add 4 new methods)
- [ ] Update `report_generator.py` (handoff reports)
- [ ] Update `sessions.py` API endpoints
- [ ] Update 4 test files (Qwen will coordinate)
- [ ] Grep verification: zero stray queries to old tables

**Checkpoint:** All code writes to reflexes only

#### Phase 2: Schema Cleanup (Est. 2 hours)
- [ ] Create migration script for existing databases
- [ ] Test on sample database
- [ ] Drop deprecated tables from schema
- [ ] Verify backward compatibility

**Checkpoint:** Old tables deleted, no data loss

#### Phase 3: Documentation Updates (Est. 8 hours)
- [ ] Update 5 critical production docs (see below)
- [ ] Remove bootstrap class references
- [ ] Fix schema examples (12→8 tables)
- [ ] Fix API examples
- [ ] Update code examples to use new API

**Checkpoint:** All docs accurate, no broken examples

**Handoff Document:** `HANDOFF_TO_SONNET_DOCS_UPDATE.md`

**Files to Update:**
1. `production/03_BASIC_USAGE.md` - ~50 lines
2. `production/13_PYTHON_API.md` - ~80 lines (DELETE bootstrap section)
3. `production/12_SESSION_DATABASE.md` - ~40 lines (schema)
4. `production/15_CONFIGURATION.md` - ~35 lines (DELETE bootstrap section)
5. `production/17_PRODUCTION_DEPLOYMENT.md` - ~50 lines

**Expected Completion:** December 12-14

---

### Qwen: Comprehensive Test Updates 🔄 **PENDING**

**Task:** Update 4 test files + add 50+ new tests for reflexes/statusline/MCO

**Handoff Document:** `HANDOFF_TO_QWEN_TEST_UPDATES.md`

#### Phase 1: Update Deprecated Tests (Est. 4-6 hours)
- [ ] `test_reflex_logging_integration.py` - Remove `log_preflight_assessment()` calls
- [ ] `verify_empirica_integration.py` - Update schema validation
- [ ] `test_phase1.6_handoff_reports.py` - Use new API
- [ ] `test_mini_agent_handoff_e2e.py` - Update coordination tests
- [ ] Run full test suite, verify 100% pass

**Checkpoint:** All 4 updated files pass, no regressions

#### Phase 2: Add Reflexes Tests (Est. 2 days)
- [ ] Create `test_reflexes_table_comprehensive.py` (25 tests)
  - Performance tests
  - Edge case handling
  - Data integrity
  - Query patterns
- [ ] Verify reflexes table functionality 95%+ covered

**Checkpoint:** Reflexes suite complete + passing

#### Phase 3: Add Statusline Tests (Est. 2 days)
- [ ] Create `test_statusline_reflexes_integration.py` (18 tests)
  - Data reading from reflexes
  - Cognitive load calculation (DENSITY-based)
  - Mirror drift detection
  - Per-AI configuration loading
  - Decision gate impact
- [ ] Verify statusline 100% tested

**Checkpoint:** Statusline suite complete + passing

#### Phase 4: Add MCO Configuration Tests (Est. 2 days)
- [ ] Create `test_mco_configuration_and_bias_correction.py` (15 tests)
  - Model profile loading
  - Bias correction application
  - Persona configuration
  - Feedback loops YAML loading
  - Agent-specific overrides
- [ ] Verify MCO 100% tested

**Checkpoint:** MCO suite complete + passing

#### Phase 5: Integration & Verification (Est. 1 day)
- [ ] Run full test suite (target: 770+ tests)
- [ ] Generate coverage report (target: >95%)
- [ ] Fix any cross-test issues
- [ ] Final verification

**Checkpoint:** All tests pass, coverage >95%, ready for production

**Expected Completion:** December 16-18

**Final Test Count:** 770+ tests (from current 722)

---

## TIER 2: DOCUMENTATION CLEANUP (Nice to Have, But Recommended)

### Dev Lead: Documentation Organization 📋 **PENDING**

#### Task 1: Consolidate Data Flow Audit (Est. 2 hours)
- [ ] Merge 4 overlapping data flow docs into 1:
  - `DATA_FLOW_INCONSISTENCIES_AUDIT.md` (keep as diagnostic)
  - `DATA_FLOW_FIX_ACTION_PLAN.md` (keep as actionable)
  - Delete: `DATA_FLOW_AUDIT_INDEX.md`, `README_DATA_FLOW_AUDIT.md`
- [ ] Move to `/empirica-dev/diagnostics/`

**Impact:** Reduce confusion, single source of truth

#### Task 2: Archive Coordination Docs (Est. 1 hour)
- [ ] Move 40 session archive docs from `tests/coordination/archive/` to `/empirica-dev/archive/2025-11-10/`
- [ ] Keep only: `README.md`, `test_coordinator.py`, `VECTOR_TERMINOLOGY_STANDARDIZED.md`

**Impact:** Clean up test directory, preserve history in dev

#### Task 3: Move Dev Docs to `/empirica-dev` (Est. 3 hours)
- [ ] Move architecture deep dives (8 files)
- [ ] Move migration specs (2 files)
- [ ] Keep in `/docs/production`: only user-facing guides

**Impact:** Production docs minimal, dev docs organized

**Expected Completion:** December 13

---

## TIER 3: VALIDATION (Before Deploying to Users)

### Final Checklist (Est. 4 hours)

- [ ] **Database:**
  - [ ] All 4 deprecated tables deleted
  - [ ] Zero references to old tables in code
  - [ ] Migration script works on test database
  - [ ] No data loss verified

- [ ] **Code:**
  - [ ] Bootstrap classes removed (if used anywhere else)
  - [ ] `reflex_logger.py` deprecated (git_enhanced_reflex_logger only)
  - [ ] All imports updated
  - [ ] No deprecated method calls anywhere

- [ ] **Tests:**
  - [ ] All 770+ tests passing
  - [ ] Coverage >95%
  - [ ] No test flakiness
  - [ ] Regression suite clean

- [ ] **Documentation:**
  - [ ] All production docs accurate
  - [ ] No bootstrap references
  - [ ] No broken API examples
  - [ ] No "TBD" or "TODO" in user docs

- [ ] **Architecture:**
  - [ ] MCO configuration fully tested
  - [ ] Feedback loops config validated
  - [ ] Statusline real DENSITY-based (not heuristics)
  - [ ] Three-layer storage intact (SQLite + Git + JSON)

- [ ] **Deployment:**
  - [ ] README updated with deployment instructions
  - [ ] Troubleshooting guide current
  - [ ] FAQ updated
  - [ ] System prompt finalized

---

## Timeline Overview

```
Week 1 (Dec 5-12):
├─ Claude Code: ✅ COMPLETE (Cognitive load)
├─ Sonnet: Phase 1-2 (Schema migration + cleanup)
│         → 8 hours code + 2 hours schema = 10 hours
├─ Qwen: Phase 1 (Update 4 test files)
│        → 4-6 hours
└─ Dev Lead: Tasks 1-2 (Data flow consolidation)
             → 3 hours

Week 2 (Dec 13-19):
├─ Sonnet: Phase 3 (Docs updates)
│         → 8 hours
├─ Qwen: Phase 2-5 (New test suites)
│        → 8-10 hours
├─ Dev Lead: Task 3 (Move docs to /empirica-dev)
│            → 3 hours
└─ Final Validation: 4 hours
```

**Critical Path:** Sonnet (16 hrs) → Ready for production deployment

---

## Success Metrics

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Tests Passing | 722 | 770+ | 📊 Will increase |
| Code Coverage | ~85% | >95% | 📊 Will increase |
| Deprecated References | 14 docs | 0 docs | 🔴 In progress |
| Deprecated Tables | 4 tables | 0 tables | 🔴 In progress |
| Production Docs | Outdated | Current | 🔴 In progress |
| Heuristics in Code | DENSITY only | ZERO elsewhere | ✅ Complete |
| MCO Tested | Partial | 100% | 🔴 In progress |

---

## Risk Mitigation

### Risk: Schema Migration Breaks Existing Data
**Mitigation:**
- Migration script tested on sample DB first
- Backward compatibility script auto-runs
- Can restore from git if needed
- Verify row counts before/after

### Risk: Tests Still Use Deprecated API
**Mitigation:**
- Grep verification: zero stray queries
- Full test run before deployment
- Regression suite checks nothing broke

### Risk: Documentation Still References Removed APIs
**Mitigation:**
- Grep all .md files for deprecated terms
- Code review on all doc updates
- Test example code (doesn't have to run, but valid)

### Risk: Users Follow Old Docs
**Mitigation:**
- Version old docs to `/empirica-dev/archive/`
- Add header warning to deprecated docs
- Latest docs only in `/docs/production/`

---

## Handoff Documents Ready

✅ **HANDOFF_TO_SONNET_DATABASE_MIGRATION.md** - Complete schema migration spec
✅ **HANDOFF_TO_SONNET_DOCS_UPDATE.md** - 5 docs to update, specific search/replace patterns
✅ **HANDOFF_TO_QWEN_TEST_UPDATES.md** - 4 tests + 3 new suites, phase-by-phase plan

All handoffs include:
- Clear problem statement
- Specific file locations
- Expected timeline
- Success criteria
- Verification checklists

---

## How to Use This Checklist

### For Sonnet
1. Read `HANDOFF_TO_SONNET_DATABASE_MIGRATION.md`
2. Execute Phase 1 (code migration)
3. Execute Phase 2 (schema cleanup)
4. Read `HANDOFF_TO_SONNET_DOCS_UPDATE.md`
5. Execute Phase 3 (docs updates)
6. Check off items as completed

### For Qwen
1. Read `HANDOFF_TO_QWEN_TEST_UPDATES.md`
2. Execute Phase 1-5 (tests + new suites)
3. Check off items as completed
4. Report final test count + coverage

### For Dev Lead
1. Consolidate data flow docs (2 hours)
2. Archive coordination docs (1 hour)
3. Move dev docs (3 hours)
4. Check off items as completed

### For Code Lead (You)
1. Monitor progress
2. Unblock dependencies
3. Coordinate final validation
4. Gate production deployment

---

## Contact Points

**Sonnet's Questions:** Ask in this checklist or handoff docs
**Qwen's Questions:** Ask in this checklist or handoff docs
**Blockers:** Flag immediately, don't wait

---

## Final Sign-Off

When all items checked:

```
✅ Database schema uniform (reflexes only)
✅ Production docs accurate (no deprecated refs)
✅ Tests comprehensive (770+, >95% coverage)
✅ MCO fully validated
✅ No heuristics (only real epistemic measurements)
✅ Three-layer storage intact + verified
✅ Ready for production deployment
```

---

**Target Completion:** December 19, 2025
**Estimated Effort:**
- Sonnet: 16 hours
- Qwen: 10-12 days
- Dev Lead: 6 hours
- Total: ~120 hours across 3 agents

**Status:** On Track ✅
