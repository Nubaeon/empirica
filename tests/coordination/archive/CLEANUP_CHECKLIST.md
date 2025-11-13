# Cleanup Checklist - Manual Actions Required

**Purpose:** Final cleanup before Phase 0 MVP release  
**Status:** Ready to execute

---

## ✅ Completed (By AI)

- [x] Documentation consolidated (7 docs → 1)
- [x] 6 quick start guides created
- [x] Navigation hub created (docs/README.md)
- [x] Session docs moved to docs/sessions/2025-11-08/
- [x] Main docs/ cleaned (15 → 9 files)
- [x] .gitignore created
- [x] Production readiness assessed

---

## 🔧 Manual Actions Required (You)

### 1. Delete Empty Folders
```bash
# Empty skills folder (consolidated to docs/skills/)
rmdir docs/empirica_skills
```

### 2. Choose Development Strategy

**Option A: Separate Dev Environment** (✅ RECOMMENDED)
```bash
cd /home/yogapad/empirical-ai/

# Copy to separate dev environment
cp -r empirica empirica-dev

# In empirica-dev: Keep our development data, continue working
# In empirica: Clean for production release

cd empirica
rm -rf .empirica/sessions/*.db
rm -rf .empirica_reflex_logs/*
rm -rf empirica/.empirica/
```

**Option B: Just Clean Current**
```bash
cd /home/yogapad/empirical-ai/empirica
rm -rf .empirica/sessions/*.db
rm -rf .empirica_reflex_logs/*
rm -rf empirica/.empirica/
```

### 3. Optional: Delete Archived Artifacts
```bash
cd /home/yogapad/empirical-ai/empirica

# These contain old development files (already backed up)
rm -rf _archive/
rm -rf _dev/
```

### 4. Initialize Git (Production Ready)
```bash
cd /home/yogapad/empirical-ai/empirica

# Initialize
git init

# Verify .gitignore
cat .gitignore  # Should protect user data

# Initial commit
git add .
git commit -m "Phase 0 MVP - Initial Release

- 12-vector epistemic self-assessment system (UVL)
- CLI, MCP, Bootstrap, and Python API interfaces
- Session management with local SQLite storage
- Reflex logging for epistemic audit trail
- Calibration validation
- Complete documentation (9 guides + 21 production docs)
- NO HEURISTICS - Genuine self-assessment only

Version: 1.0.0-phase0"

# Tag release
git tag -a v1.0.0-phase0 -m "Phase 0 MVP Release"

# Optional: Push to GitHub
# git remote add origin https://github.com/your-org/empirica.git
# git push -u origin main
# git push --tags
```

---

## 📋 Verification Checklist

After manual actions, verify:

```bash
# Check main docs folder (should be 9 files)
ls -1 docs/*.md

# Check no user data in repo
ls .empirica/sessions/  # Should be empty or only templates
ls .empirica_reflex_logs/  # Should be empty

# Check empty folder gone
ls docs/empirica_skills/  # Should not exist

# Check git initialized
git status  # Should show git repo
```

---

## 🎯 Expected Final State

### Repository Structure:
```
empirica/
├── empirica/              # Main package
├── mcp_local/             # MCP server
├── docs/                  # 9 essential docs + subdirs
├── tests/                 # Test suite
├── requirements.txt       # Dependencies
├── setup.py               # Package setup
├── README.md              # Main readme
├── LICENSE                # MIT License
├── CONTRIBUTING.md        # Contributing guide
├── .gitignore             # Git ignore
└── .git/                  # Git repository (after init)
```

### Clean State:
- ✅ No development databases
- ✅ No user reflex logs
- ✅ No archived artifacts (optional)
- ✅ Only essential documentation
- ✅ Git initialized with clean commit

---

## 🚀 After Cleanup

You'll have:
1. ✅ Clean production codebase
2. ✅ Complete documentation
3. ✅ Git version control
4. ✅ Ready for distribution
5. ✅ (Optional) Separate dev environment

**Next:** Push to GitHub, announce Phase 0 MVP! 🎉

---

**See also:**
- `docs/SESSION_COMPLETE_2025-11-08_FINAL.md` - Complete session summary
- `docs/PRODUCTION_READINESS_ASSESSMENT.md` - Detailed analysis
