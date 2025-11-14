# 📁 Empirica Root Folder Cleanup Plan

**Goal:** Keep only essential production files and most recent documentation in root folder

---

## ✅ Files to KEEP (Essential Production)

### Core Configuration
- `pyproject.toml` - Python project configuration ✅
- `setup.py` - Installation script ✅
- `requirements.txt` - Dependencies ✅
- `pytest.ini` - Test configuration ✅
- `MANIFEST.in` - Package manifest ✅
- `Makefile` - Build automation ✅

### Essential Documentation
- `README.md` - Main project documentation ✅
- `CONTRIBUTING.md` - Contribution guidelines ✅
- `LICENSE` - Legal ✅

### Git
- `.gitignore` - (if exists) ✅

---

## 📦 Files to MOVE to `docs/archive/session_notes/`

### Session Progress Checkpoints
- `CHECKPOINT_SESSION2_PROGRESS.md` → `docs/archive/session_notes/`
- `CHECKPOINT_SESSION3_PROGRESS.md` → `docs/archive/session_notes/`
- `CHECKPOINT_SESSION4_SECTION1_COMPLETE.md` → `docs/archive/session_notes/`
- `CHECKPOINT_SESSION5_P1_COMPLETE.md` → `docs/archive/session_notes/`
- `SESSION5_P1_COMPLETE_SUMMARY.md` → `docs/archive/session_notes/`
- `PHASE1_COMPLETE_SUMMARY.md` → `docs/archive/session_notes/`

### Investigative Reports (Completed)
- `ARCHITECTURAL_INVESTIGATION_SUMMARY.md` → `docs/archive/investigations/`
- `DATABASE_SESSION_QUERY_FINDINGS.md` → `docs/archive/investigations/`
- `DEEP_DIVE_ANALYSIS.md` → `docs/archive/investigations/`
- `CODE_QUALITY_REPORT.md` → `docs/archive/investigations/`
- `LEGACY_COMPONENTS_ASSESSMENT.md` → `docs/archive/investigations/`

### Strategy Documents (Completed)
- `INVESTIGATION_STRATEGY_EXTENSIBILITY_COMPLETE.md` → `docs/archive/completed_work/`
- `INVESTIGATION_STRATEGY_FIX_COMPLETE.md` → `docs/archive/completed_work/`
- `REFACTORING_PRIORITIES.md` → `docs/archive/completed_work/`

### Test/Status Reports
- `MCP_SERVER_TEST_RESULTS.md` → `docs/archive/test_results/`
- `END_TO_END_TEST_STATUS.md` → `docs/archive/test_results/`
- `MINI_AGENT_TEST_CHECKLIST.md` → `docs/archive/test_results/`
- `PHASE1_TMUX_MCP_REPORT.md` → `docs/archive/test_results/`

### Phase Documentation (Completed phases)
- `PHASE_8_COMPLETION_CHECKPOINT.md` → `docs/archive/phases/`
- `PHASE_8_DOCUMENTATION_UPDATE_PLAN.md` → `docs/archive/phases/`
- `PHASED_TESTING_REMINDER.md` → `docs/archive/phases/`

### Update/Migration Docs (Completed)
- `UPDATES_SUMMARY_PHASED_APPROACH.md` → `docs/archive/completed_work/`
- `COMPREHENSIVE_DOCS_ARCHIVE_PLAN.md` → `docs/archive/completed_work/`
- `DOCUMENTATION_ARCHIVING_COMPLETE.md` → `docs/archive/completed_work/`

---

## 📝 Files to KEEP in ROOT (Active Work)

### Current Session Instructions
- `MINIMAX_SESSION7_INSTRUCTIONS.md` - Latest instructions ✅
- `MINIMAX_SESSION8_FINAL_P2.md` - Next session ✅
- `NEW_SESSION_EMPIRICA_TEST_INSTRUCTIONS.md` - Active instructions ✅

### Active Roadmaps
- `WHAT_STILL_TO_DO.md` - Current status and next steps ✅
- `GIT_INTEGRATION_ROADMAP.md` - Phase 2+ planning ✅
- `FINAL_TEST_AND_WEBSITE_PLAN.md` - Deployment plan ✅

### Vision Documents
- `EMPIRICA_ACTION_REPLAY_VISION.md` - Future feature vision ✅
- `empirica_git.md` - Git integration vision ✅

---

## 🗑️ Files to ARCHIVE (Superseded)

### Old Session Instructions (Superseded by Session 7/8)
- `MINIMAX_INSTRUCTIONS.md` → `docs/archive/old_instructions/session_1.md`
- `MINIMAX_SESSION_2_RESUME.md` → `docs/archive/old_instructions/session_2.md`
- `MINIMAX_SESSION_4_INSTRUCTIONS.md` → `docs/archive/old_instructions/session_4.md`
- `MINIMAX_SESSION5_FINAL_PUSH.md` → `docs/archive/old_instructions/session_5.md`
- `MINIMAX_SESSION6_GIT_NOTES_PROTOTYPE.md` → `docs/archive/old_instructions/session_6.md`

---

## 📂 Directory Structure After Cleanup

```
empirica/
├── README.md ✅
├── CONTRIBUTING.md ✅
├── LICENSE ✅
├── pyproject.toml ✅
├── setup.py ✅
├── requirements.txt ✅
├── pytest.ini ✅
├── Makefile ✅
├── MANIFEST.in ✅
│
├── # Active Work (12 files)
├── MINIMAX_SESSION7_INSTRUCTIONS.md
├── MINIMAX_SESSION8_FINAL_P2.md
├── NEW_SESSION_EMPIRICA_TEST_INSTRUCTIONS.md
├── WHAT_STILL_TO_DO.md
├── GIT_INTEGRATION_ROADMAP.md
├── FINAL_TEST_AND_WEBSITE_PLAN.md
├── EMPIRICA_ACTION_REPLAY_VISION.md
├── empirica_git.md
├── FOLDER_CLEANUP_PLAN.md (this file - archive after use)
│
├── docs/
│   ├── archive/
│   │   ├── session_notes/         # 6 files
│   │   ├── investigations/        # 5 files
│   │   ├── completed_work/        # 5 files
│   │   ├── test_results/          # 4 files
│   │   ├── phases/                # 3 files
│   │   └── old_instructions/      # 6 files (renamed)
│   │
│   ├── guides/                    # Keep existing
│   ├── reference/                 # Keep existing
│   └── skills/                    # Keep existing
│
├── empirica/                      # Source code ✅
├── tests/                         # Tests ✅
├── examples/                      # Examples ✅
└── scripts/                       # Scripts ✅
```

---

## 🚀 Cleanup Execution Commands

```bash
cd /home/yogapad/empirical-ai/empirica

# Create archive directories
mkdir -p docs/archive/{session_notes,investigations,completed_work,test_results,phases,old_instructions}

# Move session checkpoints
mv CHECKPOINT_SESSION*.md SESSION5_P1_COMPLETE_SUMMARY.md PHASE1_COMPLETE_SUMMARY.md docs/archive/session_notes/

# Move investigations
mv ARCHITECTURAL_INVESTIGATION_SUMMARY.md DATABASE_SESSION_QUERY_FINDINGS.md DEEP_DIVE_ANALYSIS.md CODE_QUALITY_REPORT.md LEGACY_COMPONENTS_ASSESSMENT.md docs/archive/investigations/

# Move completed work
mv INVESTIGATION_STRATEGY_*.md REFACTORING_PRIORITIES.md UPDATES_SUMMARY_PHASED_APPROACH.md COMPREHENSIVE_DOCS_ARCHIVE_PLAN.md DOCUMENTATION_ARCHIVING_COMPLETE.md docs/archive/completed_work/

# Move test results
mv MCP_SERVER_TEST_RESULTS.md END_TO_END_TEST_STATUS.md MINI_AGENT_TEST_CHECKLIST.md PHASE1_TMUX_MCP_REPORT.md docs/archive/test_results/

# Move phase docs
mv PHASE_8_*.md PHASED_TESTING_REMINDER.md docs/archive/phases/

# Move old instructions (with rename)
mv MINIMAX_INSTRUCTIONS.md docs/archive/old_instructions/session_1_instructions.md
mv MINIMAX_SESSION_2_RESUME.md docs/archive/old_instructions/session_2_instructions.md
mv MINIMAX_SESSION_4_INSTRUCTIONS.md docs/archive/old_instructions/session_4_instructions.md
mv MINIMAX_SESSION5_FINAL_PUSH.md docs/archive/old_instructions/session_5_instructions.md
mv MINIMAX_SESSION6_GIT_NOTES_PROTOTYPE.md docs/archive/old_instructions/session_6_instructions.md

# Verify cleanup
echo "=== Files remaining in root ==="
ls -1 *.md | wc -l
echo "Should be ~8-10 active files"

echo "=== Archived files ==="
find docs/archive -type f | wc -l
echo "Should be ~29 archived files"
```

---

## 📊 Summary

**Before:** ~50 files in root (cluttered)  
**After:** ~20 files in root (clean)
  - 9 essential config/docs
  - 8-10 active work files
  - 29 files archived with organization

**Benefits:**
- ✅ Clear separation: active vs archived
- ✅ Easy to find current work
- ✅ Historical context preserved
- ✅ Professional project structure
- ✅ Easier onboarding for new contributors

---

**Execute this cleanup after completing Session 8 (P2)!**
