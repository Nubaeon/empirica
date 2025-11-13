# Phase 8 Documentation Update Plan

**Date:** 2025-11-13  
**Session:** 9c4bffc4-8622-4c80-a756-0763504eff52  
**Purpose:** Plan documentation updates after Phase 7 testing completion

---

## Current Documentation Status

### Main Docs (docs/)
- **Total files (non-archived):** ~80+ files
- **Production docs:** 31 files in `docs/production/`
- **Issue:** Many docs are **redundant, outdated, or not production-ready**

### Database Query Findings
- ✅ All query mechanisms (MCP, CLI, Python API) working
- ✅ Created: `DATABASE_SESSION_QUERY_FINDINGS.md`
- ✅ No bugs found - minimax issue likely user error (empty results, wrong ID format)

---

## Documentation Update Strategy

### Priority 1: Profile System Documentation (NEW)

**Files to Update:**

1. **`docs/reference/INVESTIGATION_PROFILE_SYSTEM_SPEC.md`** ✅ EXISTS
   - Status: Complete specification (848 lines)
   - Action: **KEEP AS-IS** (reference documentation)

2. **`docs/production/15_CONFIGURATION.md`**
   - Current: Basic configuration guide
   - **ADD:** Profile system configuration section
   - **ADD:** Profile management CLI commands
   - **ADD:** Example profiles (development, research, critical)

3. **`docs/03_CLI_QUICKSTART.md`** or **`docs/production/03_BASIC_USAGE.md`**
   - **ADD:** Profile CLI commands:
     - `profile-list`
     - `profile-show <name>`
     - `profile-create <name>`
     - `profile-set-default <name>`
   - **ADD:** Bootstrap with profile examples

4. **`docs/production/20_TOOL_CATALOG.md`**
   - **ADD:** MCP bootstrap_session profile parameters:
     - `profile` (string, optional)
     - `ai_model` (string, optional)
     - `domain` (string, optional)

5. **NEW:** `docs/guides/PROFILE_MANAGEMENT.md`
   - Profile system user guide
   - When to use which profile
   - Creating custom profiles
   - Profile selection logic

---

### Priority 2: Database & Reflex Logs (TESTED)

**Files to Update:**

1. **`docs/production/12_SESSION_DATABASE.md`**
   - Current: Comprehensive database docs (updated Nov 10)
   - **ADD:** Schema clarification about `epistemic_assessments` vs `preflight_assessments`
   - **ADD:** Correct query patterns (avoid `session_id` on `epistemic_assessments`)
   - **ADD:** Reflex log linking (`reflex_log_path` column)

2. **`docs/production/13_PYTHON_API.md`**
   - **ADD:** Database query best practices
   - **ADD:** Helper method examples (`get_preflight_assessment`, etc.)
   - **ADD:** Reflex log retrieval patterns

3. **`docs/production/21_TROUBLESHOOTING.md`**
   - **ADD:** "Session queries returning None" - normal behavior
   - **ADD:** "No such column: session_id" - wrong table error
   - **ADD:** Reference to `DATABASE_SESSION_QUERY_FINDINGS.md`

---

### Priority 3: Archive/Deprecate Redundant Docs

**Candidates for Archiving:**

**Development Status Docs (move to `docs/_archive/development/`):**
- `docs/production/CLI_VALIDATION_COMPLETE.md`
- `docs/production/COMPLETE_PRE_RELEASE_ASSESSMENT.md`
- `docs/production/FINAL_PRE_RELEASE_SUMMARY.md`
- `docs/production/FINAL_RELEASE_READY_SUMMARY.md`
- `docs/production/PRE_RELEASE_FIXES_SUMMARY.md`
- `docs/production/SEMANTIC_REASONING_EXTENSION.md`

**Rationale:** These are **development status reports**, not production documentation. Users don't need them.

**Architecture Deep Dives (keep but reorganize):**
- `docs/architecture/` - Contains 8 detailed architecture docs
- **Action:** Keep for advanced users, ensure README.md explains purpose
- **Verify:** No redundancy with `docs/reference/ARCHITECTURE_OVERVIEW.md`

**Duplicate Guides:**
- `docs/ONBOARDING_GUIDE.md` vs `docs/archive/ONBOARDING_GUIDE.md`
- **Action:** Keep main one, ensure archive version has deprecation notice

---

### Priority 4: Update Main Entry Points

**Files to Update:**

1. **`docs/README.md`**
   - **ADD:** Profile system quick start
   - **ADD:** Link to `DATABASE_SESSION_QUERY_FINDINGS.md`
   - **UPDATE:** Production docs count (after archiving status docs)

2. **`docs/00_START_HERE.md`**
   - **ADD:** Profile system in "What's New" section
   - **UPDATE:** Links to updated production docs

3. **`docs/skills/SKILL.md`**
   - **ADD:** Profile system CLI commands
   - **ADD:** Bootstrap with profile examples
   - **UPDATE:** Investigation profile reference

4. **`docs/production/README.md`**
   - **UPDATE:** List of production docs (after archiving status docs)
   - **ADD:** Profile management guide

---

## Documentation Cleanup Actions

### Step 1: Move Development Status Docs to Archive
```bash
mkdir -p docs/_archive/development/status_reports
mv docs/production/CLI_VALIDATION_COMPLETE.md docs/_archive/development/status_reports/
mv docs/production/COMPLETE_PRE_RELEASE_ASSESSMENT.md docs/_archive/development/status_reports/
mv docs/production/FINAL_PRE_RELEASE_SUMMARY.md docs/_archive/development/status_reports/
mv docs/production/FINAL_RELEASE_READY_SUMMARY.md docs/_archive/development/status_reports/
mv docs/production/PRE_RELEASE_FIXES_SUMMARY.md docs/_archive/development/status_reports/
mv docs/production/SEMANTIC_REASONING_EXTENSION.md docs/_archive/development/status_reports/
```

**Result:** `docs/production/` reduced from 31 to 25 files (more focused)

### Step 2: Create Archive README
**File:** `docs/_archive/development/status_reports/README.md`
**Content:** Explain these are historical status reports from development

### Step 3: Verify No Broken Links
```bash
# Check for references to moved files
grep -r "CLI_VALIDATION_COMPLETE\|COMPLETE_PRE_RELEASE\|FINAL_PRE_RELEASE\|FINAL_RELEASE_READY\|PRE_RELEASE_FIXES\|SEMANTIC_REASONING_EXTENSION" docs/ --include="*.md"
```

---

## New Documents to Create

### 1. Profile Management Guide
**File:** `docs/guides/PROFILE_MANAGEMENT.md`
**Content:**
- What are investigation profiles?
- Built-in profiles (development, research, critical, exploratory, balanced)
- Profile selection logic (explicit > domain > AI model > default)
- Creating custom profiles
- Profile CLI commands
- MCP bootstrap with profiles

### 2. Database Query Best Practices
**Option A:** Add to existing `docs/production/12_SESSION_DATABASE.md`
**Option B:** Create `docs/guides/DATABASE_QUERY_PATTERNS.md`
**Recommendation:** Option A (extend existing doc)

### 3. Phase 8 Completion Checkpoint
**File:** `docs/PHASE_8_COMPLETION_CHECKPOINT.md`
**Content:**
- Phase 7 testing results (link to report)
- Phase 8 tasks completed
- Database query validation results
- Documentation update summary
- Profile system production status
- Recommended next steps

---

## Documentation Quality Standards

### Production Documentation Must Have:
1. **Clear purpose** - What problem does this solve?
2. **Practical examples** - Working code/commands
3. **Current status** - Is this implemented or planned?
4. **Links to related docs** - Cross-references

### Archive Documentation Should Have:
1. **Deprecation notice** - "This is archived for historical reference"
2. **Date archived** - When and why
3. **Replacement link** - Where to find current info

---

## Estimated Work

### Phase 8 Documentation Tasks

| Task | Files | Effort | Priority |
|------|-------|--------|----------|
| Profile system docs | 5 files | 2 hours | HIGH |
| Database query docs | 3 files | 1 hour | MEDIUM |
| Archive status reports | 6 files | 30 min | HIGH |
| Update entry points | 4 files | 1 hour | MEDIUM |
| Create new guides | 2 files | 1.5 hours | MEDIUM |
| Verify links | All docs | 30 min | HIGH |
| **TOTAL** | **20 files** | **6.5 hours** | - |

### Quick Wins (Do First)
1. ✅ Archive development status reports (30 min)
2. ✅ Add profile commands to CLI quickstart (30 min)
3. ✅ Update database troubleshooting (30 min)
4. ✅ Create Phase 8 checkpoint (30 min)

**Total Quick Wins:** 2 hours

---

## Validation Checklist

After documentation updates:

- [ ] All links work (no 404s)
- [ ] Code examples tested and working
- [ ] No contradictions between docs
- [ ] Entry points updated (README, START_HERE, SKILL)
- [ ] Archive notices added
- [ ] Production docs focused on production use
- [ ] Development docs properly archived

---

## Recommendation

**Start with Quick Wins:**
1. Archive status reports → Clean up `docs/production/`
2. Add profile CLI commands → Update `docs/03_CLI_QUICKSTART.md`
3. Add database troubleshooting → Update `docs/production/21_TROUBLESHOOTING.md`
4. Create Phase 8 checkpoint → Document completion

**Then tackle comprehensive updates:**
5. Create profile management guide
6. Update all entry point docs
7. Extend database documentation
8. Verify all links

**Total time:** ~6.5 hours spread across sessions

---

## Files Summary

**To Update (13 files):**
1. `docs/production/15_CONFIGURATION.md`
2. `docs/03_CLI_QUICKSTART.md`
3. `docs/production/03_BASIC_USAGE.md`
4. `docs/production/20_TOOL_CATALOG.md`
5. `docs/production/12_SESSION_DATABASE.md`
6. `docs/production/13_PYTHON_API.md`
7. `docs/production/21_TROUBLESHOOTING.md`
8. `docs/README.md`
9. `docs/00_START_HERE.md`
10. `docs/skills/SKILL.md`
11. `docs/production/README.md`
12. `docs/reference/INVESTIGATION_PROFILE_SYSTEM_SPEC.md` (keep as-is)
13. `docs/reference/ARCHITECTURE_OVERVIEW.md` (verify no redundancy)

**To Create (2 files):**
1. `docs/guides/PROFILE_MANAGEMENT.md`
2. `docs/PHASE_8_COMPLETION_CHECKPOINT.md`

**To Archive (6 files):**
1-6. Development status reports → `docs/_archive/development/status_reports/`

**Total work:** 21 files, ~6.5 hours

---

**Next Step:** Execute Quick Wins (archiving + basic updates)

**Ready to proceed?** Yes - all planning complete ✅
