# Comprehensive Documentation Archive Plan

**Date:** 2025-11-13  
**Current Stats:** 463 total docs, 188 non-archived (275 already in `_archive/`)  
**Goal:** Reduce to ~50-60 production-ready docs

---

## Archive Strategy

### Folders to FULLY Archive (Move to `_archive/`)

#### 1. **`docs/development/`** (60K, 7 files)
**Reason:** Development status reports, not production documentation
**Move to:** `_archive/development/`
- CLEANUP_COMPLETE.md
- CLEANUP_PLAN.md
- CODE_FIX_COMPLETE.md
- CODE_INVESTIGATION_SUMMARY.md
- DEEP_INVESTIGATION_COMPLETE.md
- README.md (keep structure)
- RELEASE_CHECKLIST.md (move to production if needed)

#### 2. **`docs/fixes/`** (32K, 6 files)
**Reason:** Historical bug fixes, not needed for production users
**Move to:** `_archive/fixes/`
- All 6 files (JSON_FORMAT_FIX, MCP_BOOTSTRAP_FIX, etc.)

#### 3. **`docs/phase_0/`** (64K, 4 files)
**Reason:** Phase 0 planning docs, historical
**Move to:** `_archive/phase_0/`
- EMPIRICA_SINGLE_AI_FOCUS.md
- LAUNCH_READINESS_ASSESSMENT.md
- MVP_MINIMAL_WORK_PLAN.md
- PHASE_0_MASTER_INDEX.md
- SESSION_SERVER_QUICK_REF.md

#### 4. **`docs/sessions/`** (80K)
**Reason:** Historical session records
**Move to:** `_archive/sessions/`
- All session documentation (dated folders)

#### 5. **`docs/session-handoffs/`** (32K, 2 files)
**Reason:** Development handoff docs
**Move to:** `_archive/session-handoffs/`
- README.md
- SESSION_HANDOFF_PRODUCTION_VALIDATION.md

#### 6. **`docs/_experimental/`** (240K)
**Reason:** Already marked experimental, consolidate into _archive
**Move to:** `_archive/experimental/`

#### 7. **`docs/archive/`** (496K)
**Reason:** Merge with main `_archive/`
**Move to:** `_archive/old_archive/`

---

### Folders to KEEP (Production-Ready)

#### ✅ **`docs/production/`** (404K, 25 files after cleanup)
**Purpose:** Core production documentation
**Action:** Remove 6 status reports (already planned)

#### ✅ **`docs/reference/`** (156K)
**Purpose:** Reference documentation (architecture, specs)
**Action:** Keep all, verify no redundancy

#### ✅ **`docs/guides/`** (480K)
**Purpose:** User guides and how-tos
**Action:** Keep all, add PROFILE_MANAGEMENT.md

#### ✅ **`docs/skills/`** (48K)
**Purpose:** SKILL.md - essential for AI agents
**Action:** Keep, update with profile info

---

### Folders to EVALUATE

#### 🔍 **`docs/architecture/`** (176K, 8 files)
**Purpose:** Deep architecture documentation
**Decision:** Keep but verify against `reference/ARCHITECTURE_OVERVIEW.md`
**Files:**
- AI_SPECIFIC_MCP_ARCHITECTURE.md
- ARCHITECTURE_CLARIFICATION_META_UNCERTAINTY.md
- CASCADE_FIXED_INTERACTIVE_MODE.md
- DUAL_CASCADE_ARCHITECTURE.md
- EMPIRICA_SYSTEM_OVERVIEW.md ← May duplicate reference/
- GOVERNANCE_DEPENDENCY_ANALYSIS.md
- GOVERNANCE_LAYER_CRITICAL_NOTES.md
- REFLEX_FRAME_ARCHIVAL_STRATEGY.md
- SESSION_SERVER_ROADMAP.md
- SYSTEM_ARCHITECTURE_DEEP_DIVE.md ← May duplicate reference/

**Recommendation:** Keep 4 unique ones, archive 4 duplicates/outdated

#### 🔍 **`docs/vision/`** (92K)
**Purpose:** Vision and future direction docs
**Decision:** Keep for context, but not essential for production
**Recommendation:** Move to `_archive/vision/` or keep minimal set

#### 🔍 **`docs/research/`** (32K)
**Purpose:** Research documentation
**Decision:** Archive unless actively referenced
**Recommendation:** Move to `_archive/research/`

#### 🔍 **`docs/integrations/`** (12K)
**Purpose:** Integration docs (Minimax)
**Decision:** Keep if current, archive if historical
**Recommendation:** Keep MINIMAX_INTEGRATION.md, archive rest

#### 🔍 **`docs/user-guides/`** (32K)
**Purpose:** User-facing guides
**Decision:** Check for duplicates with `guides/`
**Recommendation:** Merge into `guides/` or archive

#### 🔍 **`docs/examples/`** (8K)
**Purpose:** Example code/configs
**Decision:** Keep if working examples
**Recommendation:** Verify examples work, archive if outdated

---

## Root Directory Cleanup

### Files in Project Root to Archive

**Temporary Investigation Docs (mine):**
- `tmp_rovodev_deep_architecture_investigation.md` → Archive
- `tmp_rovodev_session_complete_summary.md` → Archive
- `tmp_rovodev_investigation_complete_summary.md` → Archive
- `tmp_rovodev_implementation_plan.md` → Archive

**Current Investigation Docs (keep for now, archive after Phase 8):**
- `END_TO_END_TEST_STATUS.md` → Keep until Phase 8 complete
- `DATABASE_SESSION_QUERY_FINDINGS.md` → Keep until Phase 8 complete
- `ARCHITECTURAL_INVESTIGATION_SUMMARY.md` → Keep until Phase 8 complete
- `MINI_AGENT_TEST_CHECKLIST.md` → Keep until Phase 8 complete
- `PHASE_8_DOCUMENTATION_UPDATE_PLAN.md` → Keep until Phase 8 complete

**Production Docs in Root (move to docs/):**
- `docs/PHASE_7_TESTING_REPORT.md` → Move to `docs/_archive/phase_reports/`
- `docs/PHASE_4_COMPLETION.md` → Move to `docs/_archive/phase_reports/`
- `docs/MCP_SERVER_INTEGRATION_STATUS.md` → Move to `docs/_archive/development/`

---

## Archive Commands

### Step 1: Create Archive Structure
```bash
cd /home/yogapad/empirical-ai/empirica
mkdir -p docs/_archive/{development,fixes,phase_0,sessions,session-handoffs,experimental,vision,research,phase_reports,investigation_docs}
```

### Step 2: Archive Full Folders
```bash
# Development docs
mv docs/development/* docs/_archive/development/

# Fixes
mv docs/fixes/* docs/_archive/fixes/

# Phase 0
mv docs/phase_0/* docs/_archive/phase_0/

# Sessions
mv docs/sessions/* docs/_archive/sessions/

# Session handoffs
mv docs/session-handoffs/* docs/_archive/session-handoffs/

# Experimental
mv docs/_experimental/* docs/_archive/experimental/

# Research
mv docs/research/* docs/_archive/research/

# Merge old archive
mv docs/archive/* docs/_archive/old_archive/
```

### Step 3: Archive Production Status Reports
```bash
# Already in plan
mkdir -p docs/_archive/development/status_reports
mv docs/production/CLI_VALIDATION_COMPLETE.md docs/_archive/development/status_reports/
mv docs/production/COMPLETE_PRE_RELEASE_ASSESSMENT.md docs/_archive/development/status_reports/
mv docs/production/FINAL_PRE_RELEASE_SUMMARY.md docs/_archive/development/status_reports/
mv docs/production/FINAL_RELEASE_READY_SUMMARY.md docs/_archive/development/status_reports/
mv docs/production/PRE_RELEASE_FIXES_SUMMARY.md docs/_archive/development/status_reports/
mv docs/production/SEMANTIC_REASONING_EXTENSION.md docs/_archive/development/status_reports/
```

### Step 4: Archive Root Investigation Docs
```bash
mkdir -p docs/_archive/investigation_docs
mv tmp_rovodev_*.md docs/_archive/investigation_docs/
```

### Step 5: Archive Phase Reports from docs/
```bash
mv docs/PHASE_7_TESTING_REPORT.md docs/_archive/phase_reports/
mv docs/PHASE_4_COMPLETION.md docs/_archive/phase_reports/
mv docs/MCP_SERVER_INTEGRATION_STATUS.md docs/_archive/development/
```

### Step 6: Remove Empty Folders
```bash
rmdir docs/development docs/fixes docs/phase_0 docs/sessions docs/session-handoffs docs/_experimental docs/research docs/archive 2>/dev/null || true
```

---

## Final Structure (After Archive)

```
docs/
├── production/           # 25 files (clean, focused)
├── reference/            # Architecture & specs
├── guides/               # User guides
├── skills/               # SKILL.md
├── architecture/         # Deep dives (curated)
├── integrations/         # Active integrations only
├── vision/               # Optional: future direction
├── user-guides/          # Optional: merge into guides/
├── examples/             # Working examples only
├── _archive/             # Everything else
│   ├── development/
│   ├── fixes/
│   ├── phase_0/
│   ├── sessions/
│   ├── session-handoffs/
│   ├── experimental/
│   ├── vision/
│   ├── research/
│   ├── phase_reports/
│   ├── investigation_docs/
│   └── old_archive/
├── 00_START_HERE.md
├── 01_a_AI_AGENT_START.md
├── 01_b_MCP_AI_START.md
├── 02_INSTALLATION.md
├── 03_CLI_QUICKSTART.md
├── 04_MCP_QUICKSTART.md
├── 05_ARCHITECTURE.md
├── 06_TROUBLESHOOTING.md
├── ONBOARDING_GUIDE.md
└── README.md
```

**Result:** ~60-80 production docs (from 188), much cleaner structure

---

## Validation Steps

After archiving:

1. **Check broken links:**
   ```bash
   grep -r "docs/development/\|docs/fixes/\|docs/phase_0/\|docs/sessions/" docs/ --include="*.md" | grep -v "_archive"
   ```

2. **Verify production docs intact:**
   ```bash
   ls docs/production/*.md | wc -l  # Should be 25
   ```

3. **Test key workflows:**
   - Open 00_START_HERE.md - all links work?
   - Open production/README.md - accurate list?
   - Open SKILL.md - complete?

4. **Create archive README:**
   ```bash
   cat > docs/_archive/README.md << 'EOF'
   # Archived Documentation
   
   This directory contains historical documentation archived during cleanup.
   
   **Archive Date:** 2025-11-13
   **Reason:** Focus on production-ready documentation
   
   ## Contents
   - development/ - Development status reports
   - fixes/ - Historical bug fixes
   - phase_0-7/ - Phase planning and completion reports
   - sessions/ - Historical session records
   - investigation_docs/ - Investigation and analysis docs
   
   For current documentation, see parent docs/ directory.
   EOF
   ```

---

## Estimated Impact

**Before:**
- Total docs: 463
- Non-archived: 188
- Production docs: 31

**After:**
- Total docs: 463 (same)
- Non-archived: ~60-80
- Production docs: 25 (cleaner)
- Archive: ~380-400 (well organized)

**Benefits:**
- ✅ Easier for new users to find relevant docs
- ✅ Clear production vs historical distinction
- ✅ Faster doc searches
- ✅ Better organization

---

## Execution Order

**Phase 1: Safe Archives (Do Now)**
1. Archive development/ fixes/ phase_0/ sessions/ session-handoffs/
2. Archive production status reports
3. Archive root tmp_rovodev_*.md files
4. Remove empty folders

**Phase 2: Evaluation (After Phase 8)**
5. Evaluate architecture/ for duplicates
6. Decide on vision/ and research/
7. Merge user-guides/ into guides/
8. Verify examples/ work

**Phase 3: Validation**
9. Check links
10. Test workflows
11. Create archive README

**Estimated Time:** 1-2 hours

---

**Ready to Execute Phase 1?** Yes ✅
