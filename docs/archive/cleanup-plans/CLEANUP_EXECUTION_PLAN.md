# Cleanup Execution Plan

**Based on:** Deep architectural analysis  
**Approach:** Safe removal, strategic consolidation, controlled archiving  
**Risk Level:** Low to Medium

---

## Phase 1: Safe Consolidation (Low Risk)

### 1.1 Merge Duplicate Investigation Systems
**Target:** `empirica/investigation/investigation_plugin.py` vs `empirica/core/metacognitive_cascade/investigation_plugin.py`

**Action:** 
- Analyze both files thoroughly
- Merge with best features from both
- Preserve functionality while eliminating duplication
- Test investigation workflow after merge

**Risk:** Low - Both files serve same purpose
**Impact:** ~300 lines duplicated code eliminated
**Testing:** Run investigation commands, CASCADE workflow tests

### 1.2 Archive Cognitive Benchmarking
**Target:** Entire `empirica/cognitive_benchmarking/` directory

**Action:** 
- Move to `experiments/cognitive_benchmarking/` 
- Preserve for research purposes
- Document why it was archived

**Risk:** Low - No active imports detected
**Impact:** ~12 files moved out of main codebase
**Testing:** Ensure main workflows still function

---

## Phase 2: Functional Testing (Medium Risk)

### 2.1 Dashboard System Testing
**Target:** `empirica/dashboard/` files

**Action:**
- Test dashboard functionality
- If broken: Remove
- If working but unused: Archive
- If working and useful: Keep with documentation

**Risk:** Medium - Unknown functionality
**Impact:** 3 files decision pending
**Testing:** Run dashboard commands, monitor for errors

### 2.2 Advanced Investigation Analysis  
**Target:** `empirica/investigation/advanced_investigation/`

**Action:**
- Analyze advanced investigation system
- Determine if used by current workflow
- Consolidate with core or archive

**Risk:** Medium - May be part of investigation strategy
**Impact:** Unknown number of files
**Testing:** Investigation workflow testing

---

## Phase 3: Component Architecture Review

### 3.1 Bootstrap Component Validation
**Target:** All 11 bootstrap-loaded components

**Action:**
- Verify each component is functional
- Document loading levels and purposes
- Identify any non-functional components

**Risk:** High - These are intentionally loaded
**Impact:** Potential to break bootstrap system
**Testing:** Bootstrap at all levels (0, 1, 2)

### 3.2 Modality Switcher System
**Target:** `empirica/plugins/modality_switcher/`

**Action:**
- Confirm active usage patterns
- Document integration points
- Optimize if needed

**Risk:** High - Actively imported system
**Impact:** Multiple files potentially affecting AI routing
**Testing:** Plugin registration, AI model switching

---

## Detailed Implementation Steps

### Step 1: Create Cleanup Branch
```bash
git checkout -b codebase-cleanup-architectural
git tag pre-cleanup-architectural
```

### Step 2: Safe File Consolidation
```bash
# Consolidate investigation plugins
cp empirica/core/metacognitive_cascade/investigation_plugin.py empirica/core/metacognitive_cascade/investigation_plugin_merged.py
# (Manual merge process with best of both files)
# Remove duplicate from empirica/investigation/
```

### Step 3: Archive Experimental Code
```bash
# Archive cognitive benchmarking
mkdir -p experiments/cognitive_benchmarking
mv empirica/cognitive_benchmarking/* experiments/cognitive_benchmarking/
rmdir empirica/cognitive_benchmarking || true
```

### Step 4: Test After Each Change
```bash
# Always test after each phase:
pytest tests/integration/test_mcp_workflow.py
empirica bootstrap --ai-id test-cleanup --level 0
empirica bootstrap --ai-id test-cleanup --level 1  
empirica bootstrap --ai-id test-cleanup --level 2
empirica preflight --session-id test --prompt "Test cleanup" --output json
```

### Step 5: Dashboard Testing (if implemented)
```bash
# Test dashboard commands
empirica dashboard --help
empirica cascade-monitor --help
# If commands work, keep. If not, archive.
```

---

## Risk Assessment

### Low Risk Changes
- ✅ Merging duplicate investigation files (same functionality)
- ✅ Archiving unused cognitive benchmarking
- ✅ Removing confirmed unused test files

### Medium Risk Changes
- ⚠️ Dashboard system status determination
- ⚠️ Advanced investigation system analysis
- ⚠️ Legacy utility file removal

### High Risk Changes
- ❌ Any bootstrap component modification
- ❌ Core system file removal
- ❌ Modality switcher alteration

---

## Success Criteria

### Immediate Success
- [ ] Investigation plugin duplication eliminated
- [ ] Cognitive benchmarking archived safely
- [ ] All tests continue to pass
- [ ] Bootstrap levels 0, 1, 2 all functional

### Long-term Success
- [ ] Clearer codebase structure
- [ ] Eliminated duplication
- [ ] Preserved intentional architecture
- [ ] Updated documentation

---

## Backup and Rollback Strategy

### Before Each Phase
```bash
# Create checkpoint
git add .
git commit -m "checkpoint: Before [Phase Name]"
```

### If Issues Arise
```bash
# Revert to last checkpoint
git reset --hard HEAD~1

# Or revert specific commit
git revert <commit-hash>
```

### Final Verification
```bash
# Ensure everything still works
pytest tests/ -v
empirica bootstrap --ai-id final-test
```

---

## Documentation Updates Required

### After Cleanup
1. Update `CANONICAL_DIRECTORY_STRUCTURE.md`
2. Update `ARCHITECTURE_OVERVIEW.md`
3. Create archive documentation for moved files
4. Update bootstrap loading documentation

### Archive Documentation
1. Cognitive benchmarking: Why archived, how to use if needed
2. Dashboard system: Current status and revival steps
3. Investigation system: Consolidation rationale

---

## Expected Impact

### Code Reduction
- **Files:** ~15-20 files removed/archived
- **Lines:** ~3,000-5,000 lines cleaned
- **Duplication:** Investigation plugins eliminated

### Quality Improvement
- **Clarity:** Clearer architecture understanding
- **Maintainability:** Reduced duplication
- **Onboarding:** Less confusion about unused code

### Risk Mitigation
- **Zero breaking changes** to core functionality
- **Preserved experimental features** in archive
- **Maintained bootstrap loading** system integrity

---

## Timeline

### Day 1: Phase 1 (Safe Consolidation)
- Morning: Investigation plugin merge
- Afternoon: Cognitive benchmarking archive
- Testing: Full test suite validation

### Day 2: Phase 2 (Functional Analysis)  
- Morning: Dashboard system testing
- Afternoon: Advanced investigation analysis
- Testing: Investigation workflow validation

### Day 3: Phase 3 (Documentation)
- Morning: Update architecture docs
- Afternoon: Final testing and verification

---

## Quality Gates

### Before Each Phase
- [ ] All tests pass
- [ ] Backup created
- [ ] Components still load

### After Each Phase  
- [ ] Tests still pass
- [ ] Bootstrap works
- [ ] Core functionality verified
- [ ] No import errors

### Final Verification
- [ ] Complete test suite passes
- [ ] All bootstrap levels functional
- [ ] Documentation updated
- [ ] Archive properly organized
