# MiniMax Quick Start

**Task:** Fix code quality issues in Empirica codebase  
**Time:** ~2 hours for critical fixes  
**Reports:** Read these first ↓

## Must Read (5 min)
1. `CODE_QUALITY_REPORT.md` - What's wrong
2. `REFACTORING_PRIORITIES.md` - How to fix it
3. `DEEP_DIVE_ANALYSIS.md` - Security issues

## Quick Actions

### 1. FIX SQL INJECTION (5 min) 🔴 CRITICAL
File: `empirica/data/session_database.py:565`  
Add: `VALID_PHASES = {'preflight', 'think', 'plan', 'investigate', 'check', 'act', 'postflight'}`  
Then: Add `if phase not in VALID_PHASES: raise ValueError(...)` at start of `update_cascade_phase()`

### 2. REPLACE PRINTS (45 min) 🟡 P1
Replace 19 `print()` statements with `logger.info()`  
Files: Listed in REFACTORING_PRIORITIES.md P1

### 3. CENTRALIZE THRESHOLDS (30 min) 🟡 P2  
Create: `empirica/core/canonical/thresholds.py`  
Update: 3 files to use `CANONICAL_THRESHOLDS`  
Code: Copy from REFACTORING_PRIORITIES.md P2

## Test & Commit
```bash
python3 -m py_compile empirica/**/*.py
git commit -m "refactor: P1-P2 quick wins + SQL injection fix"
```

## Done? Report back!
- What completed
- Any issues
- Ready for more?

**Full details:** `MINIMAX_INSTRUCTIONS.md`
