# ⚠️ CRITICAL: Git Repository State Issue

**Date:** 2025-11-14  
**Discovered:** Phase 1-2 completion review  
**Severity:** HIGH - Code not in version control

---

## Problem

The Empirica repository has undergone a major refactoring from `semantic_self_aware_kit/` to `empirica/` structure, but **the new code is NOT committed to git**.

### Current State:

**Master Branch Contains (OLD):**
```
semantic_self_aware_kit/
├── __init__.py
├── bootstrap.py
├── cli.py
├── advanced_collaboration/
├── metacognitive_cascade/
└── ... (old structure)
```

**Working Directory Contains (NEW - UNTRACKED):**
```
empirica/                    ← NOT IN GIT
├── core/
├── data/
├── plugins/
├── investigation/
└── ...

mcp_local/                   ← NOT IN GIT  
├── empirica_mcp_server.py
├── empirica_tmux_mcp_server.py
└── ...

docs/                        ← PARTIALLY TRACKED
├── 00_START_HERE.md        ← NOT IN GIT
├── reference/              ← NOT IN GIT
└── ... (new docs)
```

---

## Git Status

```bash
# 154 unstaged/untracked files
# Key directories NOT tracked:
- empirica/ (entire directory)
- mcp_local/ (entire directory)
- docs/* (new documentation)
- All Phase 1-2 reports
```

---

## What's at Risk

### Code (NOT in git):
- `empirica/core/` - All canonical components
- `empirica/data/` - Session database
- `empirica/plugins/` - Dashboard spawner
- `empirica/investigation/` - Investigation strategies
- `mcp_local/empirica_mcp_server.py` - **MCP server with our fixes**

### Documentation (NOT in git):
- All new docs/ structure
- Phase 1-2 reports:
  - CODE_QUALITY_REPORT.md
  - REFACTORING_PRIORITIES.md
  - DEEP_DIVE_ANALYSIS.md
  - MINIMAX_INSTRUCTIONS.md
  - etc.

### What IS tracked:
- Old semantic_self_aware_kit/ (deleted in working dir)
- Some root files (README, LICENSE, etc.)

---

## Impact

🔴 **CRITICAL:**
1. All refactored code could be lost if working directory damaged
2. No version history for new structure
3. Can't revert changes
4. Can't collaborate safely
5. MiniMax refactoring will modify untracked code

---

## Recommended Actions

### Option A: Commit Everything (RECOMMENDED)

```bash
cd /home/yogapad/empirical-ai/empirica

# Stage all new structure
git add empirica/
git add mcp_local/
git add docs/
git add *.md  # Phase reports

# Commit the refactoring
git commit -m "refactor: Major restructure from semantic_self_aware_kit to empirica

- Rename semantic_self_aware_kit/ → empirica/
- Extract MCP servers to mcp_local/
- Reorganize documentation structure
- Add Phase 1-2 code quality analysis reports
- Fix last_n mode in MCP server
- Remove duplicate investigation_strategy.py

This is a breaking change - old import paths no longer work.
See docs/05_ARCHITECTURE.md for new structure."

# Update remote
git push origin master
```

### Option B: Create Feature Branch First

```bash
# Create branch for refactoring
git checkout -b feature/empirica-restructure

# Stage and commit
git add empirica/ mcp_local/ docs/ *.md
git commit -m "refactor: Complete empirica restructure"

# Push branch
git push origin feature/empirica-restructure

# Then merge to master after review
```

### Option C: Investigate Why Not Tracked

Check if there's a reason these weren't committed:
```bash
# Check for .gitignore issues
cat .gitignore

# Check if submodule
cat .gitmodules

# Check repo config
git config --list | grep -i ignore
```

---

## Verification Steps

After committing:

```bash
# Verify files tracked
git ls-files | grep empirica/ | wc -l  # Should be >100

# Verify on master
git ls-tree -r --name-only master | grep empirica/ | head

# Check size
du -sh empirica/ mcp_local/
git count-objects -vH
```

---

## Questions to Answer

1. **Why wasn't empirica/ committed?** 
   - Intentional (work in progress)?
   - Accidental (forgot to add)?
   - .gitignore issue?

2. **Is this a new repository?**
   - Forked from semantic_self_aware_kit?
   - Fresh start with empirica?

3. **What about old code?**
   - Keep semantic_self_aware_kit/ in history?
   - Complete break from old structure?

4. **Should we preserve history?**
   - `git mv semantic_self_aware_kit/ empirica/`?
   - Or fresh start with new structure?

---

## Immediate Action Required

**BEFORE MiniMax starts refactoring:**

1. ✅ **Commit current working directory** to preserve all work
2. ✅ **Verify empirica/ in git** with `git ls-files | grep empirica`
3. ✅ **Push to remote** for backup
4. ✅ **Update .gitignore** if needed

**DO NOT:**
- ❌ Run `git clean -fd` (would delete empirica/)
- ❌ Checkout old commits (would lose working directory)
- ❌ Let MiniMax modify untracked files

---

## Current Branch State

```
* refactor/p1-p2-quick-wins (HEAD)
* master
  - Both point to same commit (f75df74)
  - Both have semantic_self_aware_kit/ structure
  - Neither has empirica/ structure

Working Directory:
  - Has empirica/ (untracked)
  - Missing semantic_self_aware_kit/ (deleted, not staged)
  - 154 files changed/untracked
```

---

## Recommendation

**Commit NOW before any more work:**

```bash
# Quick commit of everything
git add -A
git commit -m "WIP: Save current empirica restructure state

Contains:
- Complete empirica/ package structure
- MCP servers in mcp_local/
- New documentation structure  
- Phase 1-2 analysis reports
- All code quality findings

Ready for MiniMax refactoring after this commit."

git push origin master
```

This ensures we don't lose 7 comprehensive reports + entire new codebase!

---

**Status:** ⚠️ **URGENT - CODE AT RISK**  
**Action:** Commit to git ASAP  
**Priority:** Before any refactoring begins

---

*Discovered: 2025-11-14 00:12 UTC*  
*Session: a89b9d94-d907-4a95-ab8d-df8824990bec*
