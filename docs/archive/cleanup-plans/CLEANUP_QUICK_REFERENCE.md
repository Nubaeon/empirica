# Codebase Cleanup - Quick Reference

**Task File:** `TASK_CODEBASE_CLEANUP_AUDIT.md`
**Purpose:** Remove unused/legacy code safely
**Priority:** P2 (Post-release maintenance)
**Estimated Time:** 4-6 hours

---

## 🎯 **Quick Start for AI Agent**

### Step 1: Run These Commands First (15 min)

```bash
# 1. Count current state
echo "Total Python files:" && find empirica/empirica -name "*.py" | wc -l
echo "Total lines of code:" && find empirica/empirica -name "*.py" | xargs wc -l | tail -1

# 2. Find active imports
grep -rh "^from empirica\|^import empirica" empirica/{cli,bootstraps,core}/**/*.py | sort -u > /tmp/active_imports.txt
echo "Active imports found:" && wc -l /tmp/active_imports.txt

# 3. Find all modules
find empirica/empirica -name "*.py" -not -path "*/__pycache__/*" | sed 's|empirica/empirica/||' | sed 's|\.py||' | sed 's|/|.|g' > /tmp/all_modules.txt
echo "Total modules:" && wc -l /tmp/all_modules.txt

# 4. Quick orphan detection
comm -23 <(sort /tmp/all_modules.txt) <(cut -d' ' -f2 /tmp/active_imports.txt | sort) > /tmp/potential_orphans.txt
echo "Potential orphans:" && wc -l /tmp/potential_orphans.txt
```

### Step 2: Review Low-Hanging Fruit (30 min)

```bash
# Check these directories first (likely candidates):

# 1. Cognitive benchmarking
echo "=== Cognitive Benchmarking ===" && \
find empirica/empirica/cognitive_benchmarking -name "*.py" | wc -l && \
grep -r "cognitive_benchmarking" empirica/{cli,bootstraps}/**/*.py 2>/dev/null | wc -l

# 2. Components (check which are loaded)
echo "=== Components ===" && \
ls -d empirica/empirica/components/*/ && \
grep -r "from empirica.components" empirica/bootstraps/*.py | cut -d: -f2 | sort -u

# 3. Investigation
echo "=== Investigation ===" && \
find empirica/empirica/investigation -name "*.py" && \
grep -r "from empirica.investigation" empirica/{cli,core}/**/*.py | wc -l

# 4. Dashboard
echo "=== Dashboard ===" && \
find empirica/empirica/dashboard -name "*.py" && \
grep "dashboard" empirica/cli/cli_core.py
```

### Step 3: Create Audit Report (1-2 hours)

Follow tasks 1-8 in `TASK_CODEBASE_CLEANUP_AUDIT.md`

---

## ⚠️ **CRITICAL: Do NOT Remove These**

### Core Systems (ALWAYS KEEP)
```
empirica/core/canonical/          - Core epistemic system
empirica/core/goals/              - Goal management
empirica/core/tasks/              - Task management
empirica/core/handoff/            - Handoff reports (P3!)
empirica/core/metacognition_12d_monitor/  - 12D vector system
empirica/data/session_database.py - Database core
```

### CLI Systems (ALWAYS KEEP)
```
empirica/cli/cli_core.py         - Main CLI
empirica/cli/command_handlers/   - All command handlers
empirica/cli/cli_utils.py        - CLI utilities
```

### Bootstrap (ALWAYS KEEP)
```
empirica/bootstraps/optimal_metacognitive_bootstrap.py
```

### Storage (ALWAYS KEEP)
```
empirica/data/                   - All data storage
```

---

## ✅ **Likely Safe to Remove/Archive**

### After Verification:

**Cognitive Benchmarking** (if not used):
```bash
# Check first:
grep -r "erb\|benchmark" empirica/cli/cli_core.py

# If no matches, likely safe to archive
# mv empirica/cognitive_benchmarking experiments/cognitive_benchmarking
```

**Dashboard** (if broken):
```bash
# Test first:
python -c "from empirica.dashboard.cascade_monitor import CascadeMonitor"

# If fails and not in CLI, archive:
# mv empirica/dashboard archive/dashboard
```

**Advanced Investigation** (if redundant):
```bash
# Check if used:
grep -r "advanced_investigation" empirica/{cli,core,bootstraps}/**/*.py

# If not used, archive:
# mv empirica/investigation/advanced_investigation archive/
```

---

## 🧪 **Testing After Each Removal**

```bash
# Run this after EVERY file removal:

# 1. Quick test
python -c "import empirica; print('Import OK')"

# 2. Bootstrap test
empirica bootstrap --ai-id test-cleanup --level 0

# 3. CLI test
empirica --help

# 4. Core workflow test
empirica preflight --session-id test-cleanup --prompt "Test cleanup" --output json

# If ALL pass → Commit
git add .
git commit -m "remove: Description of what was removed"

# If ANY fail → Revert immediately
git restore .
```

---

## 📊 **Analysis Cheat Sheet**

### Check if Module is Imported
```bash
MODULE="cognitive_benchmarking"
grep -r "from empirica.$MODULE\|import empirica.$MODULE" empirica/ | wc -l
# If 0 → Likely unused
# If >0 → Check what imports it
```

### Check Git Activity
```bash
DIR="empirica/investigation"
git log --since="4 months ago" --oneline $DIR | wc -l
# If 0 → No recent changes (might be abandoned)
# If >10 → Active development (keep it)
```

### Check Directory Size
```bash
DIR="cognitive_benchmarking"
du -sh empirica/$DIR
find empirica/$DIR -name "*.py" | xargs wc -l | tail -1
# Large + unused = good cleanup candidate
```

### Check Bootstrap Loading
```bash
grep -A 5 "bootstrap_level == 2\|bootstrap_level == 1" empirica/bootstraps/optimal_metacognitive_bootstrap.py
# Shows what's loaded at each level
```

---

## 📋 **Decision Tree**

```
For each file/directory:

1. Is it imported anywhere?
   NO → Check #2
   YES → KEEP (but verify it's actually used)

2. Is it in core/, cli/, or data/?
   YES → KEEP (critical systems)
   NO → Check #3

3. Does CLI reference it?
   YES → KEEP
   NO → Check #4

4. Does bootstrap load it?
   YES → KEEP
   NO → Check #5

5. Git activity in last 6 months?
   YES → Verify with stakeholder before removing
   NO → Check #6

6. Is it mentioned in documentation?
   YES → Archive (might be revived)
   NO → Check #7

7. Is it >100 LOC?
   YES → Archive (preserve the work)
   NO → REMOVE (low effort, low risk)
```

---

## 🎯 **Expected Cleanup Results**

### Conservative Estimate
- Remove: 10-20 files (~1,500-3,000 LOC)
- Archive: 5-10 directories (~5,000-10,000 LOC)
- Keep: 130-140 files (core functionality)

### Moderate Estimate
- Remove: 20-30 files (~3,000-5,000 LOC)
- Archive: 10-15 directories (~10,000-15,000 LOC)
- Keep: 120-130 files (core functionality)

### Aggressive Estimate
- Remove: 30-40 files (~5,000-7,000 LOC)
- Archive: 15-20 directories (~15,000-20,000 LOC)
- Keep: 100-120 files (core functionality)

---

## 💡 **Pro Tips**

### Start With Obvious Wins
1. Remove `__pycache__/` directories (always safe)
2. Remove files with "old", "deprecated", "backup" in name
3. Remove duplicate implementations (keep newest)
4. Remove empty directories

### Work Incrementally
- Remove 1 file → Test → Commit
- Don't batch removals (harder to debug failures)
- Create separate commits for each logical removal

### Archive vs Delete
**Archive if:**
- Experimental feature (might be useful)
- Large codebase (represents significant work)
- Recent activity (< 6 months)
- Mentioned in docs

**Delete if:**
- Orphaned file (no imports)
- Small file (< 50 LOC)
- Very old (no activity > 1 year)
- Duplicate/backup

### Document Everything
```bash
# Good commit messages:
git commit -m "remove: orphaned test file (no imports found)"
git commit -m "archive: cognitive_benchmarking (experimental, not in core)"
git commit -m "remove: duplicate implementation (replaced by X)"

# Bad commit messages:
git commit -m "cleanup"
git commit -m "remove stuff"
```

---

## 🚨 **Emergency Rollback**

If something breaks:

```bash
# Option 1: Revert last commit
git revert HEAD

# Option 2: Restore specific file
git restore path/to/file.py

# Option 3: Reset to before cleanup
git reset --hard pre-cleanup-audit  # Tag created at start

# Option 4: Cherry-pick good commits
git checkout -b cleanup-recovery
git cherry-pick <good-commit-hash>
```

---

## 📊 **Success Criteria**

**Minimum (MUST ACHIEVE):**
- ✅ All tests still pass
- ✅ Bootstrap works at all levels
- ✅ CLI commands functional
- ✅ No import errors
- ✅ Documentation updated

**Good (SHOULD ACHIEVE):**
- ✅ 10-20% reduction in file count
- ✅ Clearer directory structure
- ✅ Archive created for experimental code
- ✅ Audit report documents decisions

**Excellent (NICE TO HAVE):**
- ✅ 20-30% reduction in file count
- ✅ Component consolidation
- ✅ Faster test suite
- ✅ Updated architecture docs

---

**Assigned To:** Any AI agent (Mini-agent, Gemini, etc.)
**Main Task File:** `TASK_CODEBASE_CLEANUP_AUDIT.md`
**This File:** Quick reference for common operations
**Timeline:** 4-6 hours total

Good luck with the cleanup! 🧹✨
