# Documentation Cleanup Plan for Production Release

**Date:** 2025-11-15
**Purpose:** Clean documentation structure based on canonical reference
**Status:** Ready for execution
**Backup:** User confirmed backups exist

---

## Executive Summary

**Current state:** 748 markdown files (89% development artifacts)
**Target state:** ~80 production files (11%)
**Reduction:** 89% cleanup while preserving all production documentation

**Approach:**
1. Archive transient development docs
2. Delete redundant archive directories
3. Compress historical archives
4. Result: Clean production structure aligned with CANONICAL_DIRECTORY_STRUCTURE.md

---

## Phase 1: Immediate Cleanup (Safe to Execute)

### 1.1 Archive Transient Root Docs

**Move these to `docs/archive/2025-11/session_notes/`:**
```bash
docs/BUG_FIX_resume_previous_session_path.md
docs/CHECKPOINT_SESSION10_P1_PROGRESS.md
docs/PHASE_9_COMPLETION_REPORT.md
docs/SESSION_EXTENSION_BUG_2.md
```

**Reasoning:** Development session notes, not production docs

---

### 1.2 Archive Handoffs Directory

**Move entire directory to `docs/archive/2025-11/handoffs/`:**
```bash
docs/handoffs/  # All 11 files
```

**Reasoning:** All are inter-session handoffs, development artifacts

---

### 1.3 Archive Current Work Directory

**Move entire directory to `docs/archive/2025-11/development/`:**
```bash
docs/current_work/  # All 9 files
```

**Reasoning:** Active development work-in-progress, not production

---

### 1.4 Archive Architecture Design Docs

**Move to `docs/archive/architecture_design/`:**
```bash
docs/architecture/AUDIT_BOOTSTRAP_AND_GOALS.md
docs/architecture/BOOTSTRAP_REFACTOR_PLAN.md
docs/architecture/CASCADE_FIXED_INTERACTIVE_MODE.md
docs/architecture/DUAL_CASCADE_ARCHITECTURE.md
docs/architecture/GIT_ENHANCED_REFLEX_LOGGER_PLAN.md
docs/architecture/GIT_INTEGRATION_NEXT_STEPS.md
docs/architecture/GIT_INTEGRATION_ROADMAP_ENHANCED.md
docs/architecture/GIT_INTEGRATION_ROADMAP.md
docs/architecture/GOVERNANCE_DEPENDENCY_ANALYSIS.md
docs/architecture/GOVERNANCE_LAYER_CRITICAL_NOTES.md
docs/architecture/REFLEX_FRAME_ARCHIVAL_STRATEGY.md
docs/architecture/SESSION_SERVER_ROADMAP.md
docs/architecture/ARCHITECTURE_CLARIFICATION_META_UNCERTAINTY.md
docs/architecture/AI_SPECIFIC_MCP_ARCHITECTURE.md
```

**Keep in docs/architecture/ (production reference):**
```bash
docs/architecture/EMPIRICA_SYSTEM_OVERVIEW.md
docs/architecture/SYSTEM_ARCHITECTURE_DEEP_DIVE.md
```

**Reasoning:** Design/planning docs vs. reference docs

---

### 1.5 Delete Redundant Archive

**DELETE (already archived elsewhere):**
```bash
docs/_archive/  # 318 files - redundant with docs/archive/
```

**Verification before deleting:**
- Check that docs/archive/ contains all unique content
- Verify no production docs are in _archive/

---

### 1.6 Archive Root Planning Docs

**Move to `docs/archive/project_planning/`:**
```bash
FOLDER_REORGANIZATION_PLAN.md
EMPIRICA_FOUNDATION_SPECIFICATION.md
MULTI_AGENT_CHECKPOINT_STRATEGY.md
```

**Reasoning:** Project planning documents, task complete

---

## Phase 2: Archive Review Cleanup

### 2.1 Review _archive_for_review/

**Current:** 36 files awaiting review (per README_FOR_CLAUDE_REVIEW.md)

**Folders:**
- `obsolete_sessions/` (4 files) - DELETE (superseded)
- `old_validation/` (7 files) - DELETE (validation approach changed)
- `misc/` (20 files) - REVIEW individually, delete ~70%
- `model_prompts/` (4 files) - KEEP (may have reusable content)

**Action:**
1. Extract any unique insights from misc/ to reference docs
2. Keep model_prompts/ (move to docs/archive/model_prompts/)
3. Delete rest (~25 files)

---

## Phase 3: Compression

### 3.1 Compress docs/archive/

**Create:** `docs/archive.zip`
**Contents:** All of docs/archive/ (historical preservation)
**Size reduction:** Estimated 80% compression
**Result:** Clean directory structure, preserved history

---

## Phase 4: Documentation Alignment

### 4.1 Update Canonical Structure Markers

**In CANONICAL_DIRECTORY_STRUCTURE.md:**
- Remove "[TO BE ARCHIVED]" markers (tasks complete)
- Update file counts
- Verify all KEEP files are documented

### 4.2 Update README.md

**Verify references to:**
- All production entry points (00_START_HERE, etc.)
- Cross-platform installation docs
- Reference documentation

---

## Production Structure (Target)

```
empirica/
├── README.md                                  # ✅ KEEP
├── CONTRIBUTING.md                            # ✅ KEEP
├── CLAUDE.md                                  # ✅ KEEP (Claude Code)
├── QWEN.md                                    # ✅ KEEP (Qwen Code)
├── .github/copilot-instructions.md            # ✅ KEEP (Copilot)
├── ALL_PLATFORMS_INSTALLATION.md              # ✅ KEEP
├── ALL_PLATFORMS_QUICK_REFERENCE.md           # ✅ KEEP
├── MULTI_PLATFORM_COMPLETE_SUMMARY.md         # ✅ KEEP
├── PLATFORM_COMPARISON.md                     # ✅ KEEP
├── SYSTEM_PROMPT_QUICK_REFERENCE.md           # ✅ KEEP
├── INSTALLATION_COMPLETE_SUMMARY.md           # ✅ KEEP
│
└── docs/
    ├── README.md                              # ✅ KEEP
    ├── 00_START_HERE.md                       # ✅ KEEP
    ├── 01_a_AI_AGENT_START.md                 # ✅ KEEP
    ├── 01_b_MCP_AI_START.md                   # ✅ KEEP
    ├── 02_INSTALLATION.md                     # ✅ KEEP
    ├── 03_CLI_QUICKSTART.md                   # ✅ KEEP
    ├── 04_MCP_QUICKSTART.md                   # ✅ KEEP
    ├── 05_ARCHITECTURE.md                     # ✅ KEEP
    ├── 06_TROUBLESHOOTING.md                  # ✅ KEEP
    ├── ONBOARDING_GUIDE.md                    # ✅ KEEP
    │
    ├── reference/                             # 12 files ✅
    │   ├── CANONICAL_DIRECTORY_STRUCTURE.md   # THE authority
    │   ├── ARCHITECTURE_OVERVIEW.md
    │   ├── BOOTSTRAP_*.md                     # 3 files
    │   ├── CALIBRATION_SYSTEM.md
    │   ├── CHANGELOG.md
    │   ├── EMPIRICA_CASCADE_WORKFLOW_SPECIFICATION.md
    │   ├── INVESTIGATION_PROFILE_SYSTEM_SPEC.md
    │   ├── QUICK_REFERENCE.md
    │   ├── QUICK_STATUS.md
    │   └── SESSION_TRACKING.md
    │
    ├── production/                            # 25 files ✅
    │   ├── 00_COMPLETE_SUMMARY.md
    │   ├── 01_QUICK_START.md
    │   ├── ... (complete numbered series)
    │   └── 25_COMPLETE_TESTING.md
    │
    ├── guides/                                # 33 files ✅
    │   ├── CLI_GENUINE_SELF_ASSESSMENT.md
    │   ├── CLI_WORKFLOW_COMMANDS_COMPLETE.md
    │   ├── CRITICAL_NO_HEURISTICS_PRINCIPLE.md
    │   ├── development/                       # Dev guides
    │   ├── engineering/                       # Engineering guides
    │   ├── experimental/                      # Experimental
    │   ├── learning/                          # Learning guides
    │   ├── protocols/                         # Protocols
    │   └── setup/                             # Setup guides
    │
    ├── skills/                                # 1 file ✅
    │   └── SKILL.md                          # AI agent complete guide
    │
    ├── research/                              # 1 file ✅
    │   └── RECURSIVE_EPISTEMIC_REFINEMENT.md
    │
    ├── vision/                                # 8 files ✅
    │   ├── EMPIRICA_VISION.md
    │   ├── EPISTEMIC_DELTA_SECURITY.md
    │   └── ... (future roadmap)
    │
    ├── architecture/                          # 2 files ✅
    │   ├── EMPIRICA_SYSTEM_OVERVIEW.md       # Reference
    │   └── SYSTEM_ARCHITECTURE_DEEP_DIVE.md  # Reference
    │
    ├── _experimental/                         # Phase 1+ ⚠️
    │   └── ... (clearly marked NOT PRODUCTION)
    │
    ├── archive.zip                            # 📦 Historical
    │   └── ... (compressed historical docs)
    │
    └── examples/                              # ✅ Working examples
        └── reasoning_reconstruction/
```

---

## File Counts

| Category | Before | After | Change |
|----------|--------|-------|--------|
| **Total .md files** | 748 | ~80 | -89% |
| **Root docs** | 7 | 11 | +4 (platform docs) |
| **docs/ root** | 15 | 11 | -4 (archive transient) |
| **docs/reference/** | 15 | 12 | -3 (consolidate) |
| **docs/production/** | 25 | 25 | 0 (keep all) |
| **docs/guides/** | 45 | 33 | -12 (archive obsolete) |
| **docs/architecture/** | 16 | 2 | -14 (archive design docs) |
| **docs/handoffs/** | 11 | 0 | -11 (archive all) |
| **docs/current_work/** | 9 | 0 | -9 (archive all) |
| **docs/_archive/** | 318 | 0 | -318 (delete, redundant) |
| **docs/archive/** | 89 | 0 | -89 (→ archive.zip) |
| **_archive_for_review/** | 36 | 4 | -32 (cleanup per plan) |

---

## Verification Checklist

Before executing cleanup:

- [ ] Verify user has backups
- [ ] Check docs/_archive/ is truly redundant with docs/archive/
- [ ] Scan for any production docs in transient directories
- [ ] Verify all CANONICAL_DIRECTORY_STRUCTURE.md references are kept
- [ ] Check root platform docs are production-ready
- [ ] Verify examples/ directory is production-ready

After executing cleanup:

- [ ] All 80 production files present
- [ ] No broken cross-references in docs
- [ ] archive.zip created successfully
- [ ] Clean directory structure
- [ ] README.md updated with correct references
- [ ] CANONICAL_DIRECTORY_STRUCTURE.md markers updated

---

## Execution Commands

### Phase 1: Archive Transient Docs

```bash
# Create archive directories
mkdir -p docs/archive/2025-11/{session_notes,handoffs,development,architecture_design,project_planning}

# Archive root transient docs
mv docs/BUG_FIX_resume_previous_session_path.md docs/archive/2025-11/session_notes/
mv docs/CHECKPOINT_SESSION10_P1_PROGRESS.md docs/archive/2025-11/session_notes/
mv docs/PHASE_9_COMPLETION_REPORT.md docs/archive/2025-11/session_notes/
mv docs/SESSION_EXTENSION_BUG_2.md docs/archive/2025-11/session_notes/

# Archive handoffs
mv docs/handoffs docs/archive/2025-11/

# Archive current work
mv docs/current_work docs/archive/2025-11/development/

# Archive architecture design docs
mv docs/architecture/AUDIT_BOOTSTRAP_AND_GOALS.md docs/archive/2025-11/architecture_design/
mv docs/architecture/BOOTSTRAP_REFACTOR_PLAN.md docs/archive/2025-11/architecture_design/
mv docs/architecture/CASCADE_FIXED_INTERACTIVE_MODE.md docs/archive/2025-11/architecture_design/
mv docs/architecture/DUAL_CASCADE_ARCHITECTURE.md docs/archive/2025-11/architecture_design/
mv docs/architecture/GIT_ENHANCED_REFLEX_LOGGER_PLAN.md docs/archive/2025-11/architecture_design/
mv docs/architecture/GIT_INTEGRATION_NEXT_STEPS.md docs/archive/2025-11/architecture_design/
mv docs/architecture/GIT_INTEGRATION_ROADMAP_ENHANCED.md docs/archive/2025-11/architecture_design/
mv docs/architecture/GIT_INTEGRATION_ROADMAP.md docs/archive/2025-11/architecture_design/
mv docs/architecture/GOVERNANCE_DEPENDENCY_ANALYSIS.md docs/archive/2025-11/architecture_design/
mv docs/architecture/GOVERNANCE_LAYER_CRITICAL_NOTES.md docs/archive/2025-11/architecture_design/
mv docs/architecture/REFLEX_FRAME_ARCHIVAL_STRATEGY.md docs/archive/2025-11/architecture_design/
mv docs/architecture/SESSION_SERVER_ROADMAP.md docs/archive/2025-11/architecture_design/
mv docs/architecture/ARCHITECTURE_CLARIFICATION_META_UNCERTAINTY.md docs/archive/2025-11/architecture_design/
mv docs/architecture/AI_SPECIFIC_MCP_ARCHITECTURE.md docs/archive/2025-11/architecture_design/

# Archive root planning docs
mv FOLDER_REORGANIZATION_PLAN.md docs/archive/2025-11/project_planning/
mv EMPIRICA_FOUNDATION_SPECIFICATION.md docs/archive/2025-11/project_planning/
mv MULTI_AGENT_CHECKPOINT_STRATEGY.md docs/archive/2025-11/project_planning/
```

### Phase 2: Delete Redundant Archive

```bash
# VERIFY FIRST - Check for unique content
# Then delete
rm -rf docs/_archive/
```

### Phase 3: Process _archive_for_review/

```bash
# Create final archive directory
mkdir -p docs/archive/model_prompts

# Keep model prompts
mv _archive_for_review/model_prompts/* docs/archive/model_prompts/

# Delete obsolete folders
rm -rf _archive_for_review/obsolete_sessions/
rm -rf _archive_for_review/old_validation/

# Review misc/ individually (manual step)
# Delete after extracting insights

# Clean up empty directory
rm -rf _archive_for_review/
```

### Phase 4: Compress Archive

```bash
# Compress docs/archive/ to archive.zip
cd docs
zip -r archive.zip archive/
rm -rf archive/
cd ..
```

---

## Timeline

**Estimated time:** 30 minutes

1. **Phase 1** (15 min): Archive transient docs
2. **Phase 2** (2 min): Delete redundant archive
3. **Phase 3** (10 min): Process _archive_for_review/
4. **Phase 4** (3 min): Compress archive

---

## Rollback Plan

If needed:

```bash
# User has backups, can restore
# Or extract from archive.zip:
unzip docs/archive.zip -d docs/

# Or retrieve specific files from git history
git log --all --full-history -- "path/to/file.md"
git checkout <commit> -- "path/to/file.md"
```

---

## Success Criteria

✅ **Production structure matches CANONICAL_DIRECTORY_STRUCTURE.md**
✅ **All 80 production files present and accessible**
✅ **No broken cross-references in documentation**
✅ **archive.zip preserves historical context**
✅ **Clean, professional directory structure**
✅ **89% reduction in file clutter**

---

**Ready to execute:** All commands prepared, verification checklist ready, rollback plan documented.
