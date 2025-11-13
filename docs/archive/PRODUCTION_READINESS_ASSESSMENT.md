# Production Readiness Assessment

**Date:** 2025-11-08  
**Purpose:** Assess what needs cleanup/removal before Phase 0 MVP release  
**Status:** Analysis Complete

---

## 1. Main docs/ Folder Cleanup

### Current State (15 files in root)

**Essential Files (Keep - 7 files):**
1. ✅ `00_START_HERE.md` - User entry point
2. ✅ `02_INSTALLATION.md` - Setup guide
3. ✅ `03_CLI_QUICKSTART.md` - CLI guide
4. ✅ `04_MCP_QUICKSTART.md` - MCP guide
5. ✅ `05_ARCHITECTURE.md` - System overview
6. ✅ `06_TROUBLESHOOTING.md` - Problem solving
7. ✅ `README.md` - Navigation hub
8. ✅ `ONBOARDING_GUIDE.md` - Complete learning path

**Session Documentation (Move to docs/sessions/ - 8 files):**
9. 📦 `CLEANUP_COMPLETE_SUMMARY.md` - Repository cleanup session
10. 📦 `GENUINE_SELF_ASSESSMENT_PLAN.md` - MCP integration session
11. 📦 `HANDOFF_NEXT_SESSION_COMPLETE.md` - Session handoff
12. 📦 `ONBOARDING_WIZARD_INTEGRATION_COMPLETE.md` - Wizard integration session
13. 📦 `PHASE_4_6_COMPLETE.md` - Documentation phases session
14. 📦 `SKILLS_CONSOLIDATION_COMPLETE.md` - Skills consolidation session
15. 📦 `SKILLS_CONSOLIDATION_SUMMARY.md` - Skills summary

**Recommendation:**
```bash
# Move session docs to archive
mkdir -p docs/sessions/2025-11-08/
mv docs/CLEANUP_COMPLETE_SUMMARY.md docs/sessions/2025-11-08/
mv docs/GENUINE_SELF_ASSESSMENT_PLAN.md docs/sessions/2025-11-08/
mv docs/HANDOFF_NEXT_SESSION_COMPLETE.md docs/sessions/2025-11-08/
mv docs/ONBOARDING_WIZARD_INTEGRATION_COMPLETE.md docs/sessions/2025-11-08/
mv docs/PHASE_4_6_COMPLETE.md docs/sessions/2025-11-08/
mv docs/SKILLS_CONSOLIDATION_COMPLETE.md docs/sessions/2025-11-08/
mv docs/SKILLS_CONSOLIDATION_SUMMARY.md docs/sessions/2025-11-08/

# Create README in sessions folder
cat > docs/sessions/2025-11-08/README.md << 'EOF'
# Development Session Documentation - November 8, 2025

This folder contains documentation from the November 8, 2025 development session.

**What was accomplished:**
- Repository cleanup (50+ files → 17)
- Skills documentation consolidation (7 docs → 1)
- Onboarding wizard integration
- Documentation phases 4-6 complete
- MCP + CLI integration

**For production users:** These docs are not needed - they're internal development history.
**For developers:** Useful for understanding how the system was built.
EOF
```

**Result:** Main docs/ folder will have **8 essential files** (down from 15)

---

## 2. Database Templates Assessment

### Current Situation

**Databases Found:**
1. `.empirica/sessions/sessions.db` - ✅ **Production database** (user sessions)
2. `empirica/.empirica/sessions/sessions.db` - ⚠️ **Development database** (our Empirica use)
3. `_archive/empirica_web1/empirica_content.db` - ❌ **Old web UI** (archived)

**Qdrant:**
- ❌ **NOT FOUND** - No Qdrant vector database present
- ✅ **Not needed for Phase 0** - SQLite is sufficient

### Analysis

#### SQLite (sessions.db)
**Purpose:** Session and cascade storage
- ✅ **Required for Phase 0**
- ✅ **Schema is code-defined** (no template needed)
- ✅ **Auto-created** by `SessionDatabase.__init__()`
- ✅ **Tables:** sessions, cascades, cascade_metadata, reflex_frames

**Schema Location:** `empirica/data/session_database.py`
```python
def _initialize_database(self):
    # Creates tables automatically
    cursor.execute("""CREATE TABLE IF NOT EXISTS sessions ...""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS cascades ...""")
    # etc.
```

**Recommendation:** ✅ **No template needed** - Schema is in code, auto-created on first run

#### Qdrant Vector Database
**Status:** Not present in Phase 0
**Future Use:** Phase 1+ (multi-AI routing, semantic search)

**Recommendation:** ❌ **Not needed for Phase 0 MVP**

---

## 3. Our Own Empirica Use (Development Database)

### Issue: Development vs Production Data

**Problem:**
```
.empirica/sessions/sessions.db          # User's production database
empirica/.empirica/sessions/sessions.db  # OUR development database
```

**Our usage pollutes the codebase with development data:**
- Our session IDs
- Our epistemic assessments
- Our test runs
- Our calibration history

### Solutions

#### Option A: Separate Development Environment ✅ **RECOMMENDED**

Create a separate Empirica installation for development:

```bash
# Current structure:
/home/yogapad/empirical-ai/empirica/  # Production codebase

# Proposed structure:
/home/yogapad/empirical-ai/
├── empirica/                          # Clean production codebase
│   ├── .empirica/                     # User config template only
│   └── .empirica_reflex_logs/         # Empty (will be created by users)
└── empirica-dev/                      # Our development environment
    ├── .empirica/                     # OUR development data
    ├── .empirica_reflex_logs/         # OUR reflex logs
    └── [development scripts, tests]
```

**How to set up:**
```bash
# Create dev environment
cd /home/yogapad/empirical-ai/
cp -r empirica empirica-dev

# In empirica-dev: Keep our data, continue development
cd empirica-dev
# This is where we work and test

# In empirica: Clean for production
cd empirica
rm -rf .empirica/sessions/*.db
rm -rf .empirica_reflex_logs/*
rm -rf empirica/.empirica/  # Our nested development db
# Keep only template files
```

**Benefits:**
- ✅ Clean production codebase
- ✅ Preserve our development history
- ✅ Can test production setup without polluting dev data
- ✅ Clear separation

#### Option B: Clean and Use Environment Variables

Keep single codebase but use environment variables:

```bash
# Development
export EMPIRICA_DATA_DIR=~/.empirica-dev
export EMPIRICA_REFLEX_DIR=~/.empirica_reflex_logs_dev

# Production (default)
unset EMPIRICA_DATA_DIR
unset EMPIRICA_REFLEX_DIR
```

**Requires:** Code changes to support custom data directories

#### Option C: Clean Before Each Release

Clean development data before tagging releases:

```bash
# Before release
rm -rf .empirica/sessions/*.db
rm -rf .empirica_reflex_logs/*
rm -rf empirica/.empirica/
git tag v1.0.0-phase0
```

**Cons:** 
- ❌ Lose development history
- ❌ Manual process (error-prone)

---

## 4. Git Strategy for Production

### Current State: No Git

**Why avoided so far:**
- ✅ Fast iteration without git overhead
- ✅ Full backups instead of version control
- ✅ No branches/merges to manage during rapid development

### Moving to Production: Need Git

**Why we need it now:**
- ✅ Track stable versions (Phase 0 MVP)
- ✅ Enable external contributions
- ✅ Distribution (git clone, pip install)
- ✅ Issue tracking
- ✅ Release management

### Recommended Git Strategy

#### Initialize Git
```bash
cd /home/yogapad/empirical-ai/empirica

# Initialize
git init

# Add .gitignore (already exists)
cat .gitignore  # Verify it includes:
# - .empirica/credentials.yaml
# - .empirica/sessions/*.db
# - .empirica_reflex_logs/
# - *.api*
# - _archive/
# - _dev/

# Initial commit (clean production code)
git add .
git commit -m "Phase 0 MVP - Initial Release

- 12-vector epistemic self-assessment system (UVL)
- CLI, MCP, Bootstrap, and Python API interfaces
- Session management with local SQLite storage
- Reflex logging for epistemic audit trail
- Calibration validation
- Complete documentation (8 guides + 21 production docs)
- NO HEURISTICS - Genuine self-assessment only

Version: 1.0.0-phase0"

# Create release tag
git tag -a v1.0.0-phase0 -m "Phase 0 MVP Release"
```

#### .gitignore Verification
```bash
# Ensure these are in .gitignore:
cat >> .gitignore << 'EOF'
# User data (never commit)
.empirica/sessions/*.db
.empirica_reflex_logs/
.empirica/credentials.yaml
*.api*

# Development artifacts
_archive/
_dev/
empirica/.empirica/  # Our nested dev db

# Python
__pycache__/
*.pyc
*.egg-info/
dist/
build/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
EOF
```

#### Branch Strategy (Simple)

**For Phase 0:**
```
main (production)
└── Phase 0 stable releases only

dev (development)
└── Active development, testing

feature/* (optional)
└── Feature branches for big changes
```

**Workflow:**
```bash
# Development
git checkout -b dev
# ... make changes ...
git commit -m "Add feature X"

# Ready for release
git checkout main
git merge dev --no-ff
git tag v1.0.1-phase0
```

---

## 5. Production Release Checklist

### Pre-Release Cleanup

#### ✅ Code Cleanup
- [ ] Remove development databases (`empirica/.empirica/`)
- [ ] Clear user data folders (`.empirica/sessions/`, `.empirica_reflex_logs/`)
- [ ] Keep only template files in `.empirica/`
- [ ] Remove `_archive/` and `_dev/` (or ensure in .gitignore)
- [ ] Move session docs to `docs/sessions/2025-11-08/`

#### ✅ Documentation Cleanup
- [ ] Main docs/ has only 8 essential files
- [ ] Session docs moved to `docs/sessions/`
- [ ] All links verified
- [ ] README.md updated with quick start

#### ✅ Database/Storage
- [ ] No user data in repository
- [ ] Schema auto-creates (no templates needed)
- [ ] Qdrant not included (Phase 1+)
- [ ] .gitignore protects user data

#### ✅ Git Setup
- [ ] Initialize git repository
- [ ] Verify .gitignore
- [ ] Create initial commit
- [ ] Tag v1.0.0-phase0
- [ ] (Optional) Push to GitHub/GitLab

---

## 6. Recommendations Summary

### Immediate Actions (Before Phase 0 Release)

**1. Clean Main docs/ Folder**
```bash
mkdir -p docs/sessions/2025-11-08/
mv docs/*COMPLETE*.md docs/*SUMMARY*.md docs/HANDOFF*.md docs/sessions/2025-11-08/
```
Result: 15 files → 8 files

**2. Separate Development Environment** ✅ RECOMMENDED
```bash
cd /home/yogapad/empirical-ai/
cp -r empirica empirica-dev  # Our development environment
cd empirica  # Clean for production
rm -rf .empirica/sessions/*.db .empirica_reflex_logs/* empirica/.empirica/
```

**3. Initialize Git**
```bash
cd /home/yogapad/empirical-ai/empirica
git init
git add .
git commit -m "Phase 0 MVP - Initial Release"
git tag v1.0.0-phase0
```

**4. Database Templates**
✅ **No action needed** - Schema is code-defined, auto-created
❌ **Qdrant not needed** for Phase 0

---

## 7. Files/Folders to Delete Manually

### In Production Codebase (empirica/)

**Empty folders:**
```bash
rmdir docs/empirica_skills  # Empty after consolidation
```

**Development artifacts (after backup to empirica-dev/):**
```bash
rm -rf _archive/  # Old cleanup artifacts (50+ files)
rm -rf _dev/      # Dev tools and test files
rm -rf .empirica/sessions/*.db  # Development sessions
rm -rf .empirica_reflex_logs/*  # Development logs
rm -rf empirica/.empirica/      # Nested development database
```

**Old archived database:**
```bash
# Already in _archive/, will be deleted with _archive/
```

---

## 8. Distribution Strategy

### Phase 0 MVP Distribution

**Option A: GitHub + pip install (Recommended)**
```bash
# Users install via:
git clone https://github.com/your-org/empirica.git
cd empirica
pip install -e .
empirica onboard
```

**Option B: PyPI (Future)**
```bash
# Users install via:
pip install empirica
empirica onboard
```
Requires: `setup.py` finalized, PyPI account, package testing

---

## Summary

### What to Keep:
✅ SQLite schema (code-defined, auto-created)  
✅ Essential documentation (8 main docs)  
✅ Production code  
✅ Template configs  

### What to Remove/Move:
📦 Session documentation → `docs/sessions/2025-11-08/`  
🗑️ Development databases → Clean before release  
🗑️ `_archive/`, `_dev/` → Delete or keep in .gitignore  
🗑️ Empty folders → Remove  

### What to Set Up:
🔧 Git repository → Initialize with clean state  
🔧 Separate dev environment → `empirica-dev/` for our use  
🔧 .gitignore → Protect user data  

### What's NOT Needed:
❌ Qdrant templates → Phase 1+  
❌ SQLite templates → Auto-created  
❌ Database migration scripts → No external users yet  

---

**Next Steps:** Execute cleanup, initialize git, separate dev environment

**Documented by:** Rovo Dev (Claude)  
**Date:** November 8, 2025  
**Status:** ✅ Assessment Complete
