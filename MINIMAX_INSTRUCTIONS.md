# Instructions for MiniMax: Empirica Code Refactoring

**Date:** 2025-11-13  
**Context:** Phase 1 & 2 testing complete, deep dive security audit done  
**Reports Available:** 3 comprehensive analysis documents  
**Your Role:** Execute refactoring based on prioritized findings

---

## Quick Context

Claude (me) just completed comprehensive code quality analysis of Empirica framework. Found 4 main issues + 1 security risk. All documented with locations, severity, and actionable fixes.

**Key Finding:** Code quality is EXCELLENT overall, just needs cleanup in 4 areas.

---

## Your Task

**Fix code quality issues in priority order, following the documented plan.**

**Time Budget:** ~2-3 hours (start with P1-P2 quick wins)

---

## Step 1: Read the Reports (5 minutes)

**Required Reading (in order):**
1. `/home/yogapad/empirical-ai/empirica/CODE_QUALITY_REPORT.md` - Overview of all issues
2. `/home/yogapad/empirical-ai/empirica/REFACTORING_PRIORITIES.md` - Your action plan
3. `/home/yogapad/empirical-ai/empirica/DEEP_DIVE_ANALYSIS.md` - Security findings

**What to look for:**
- Priority levels (P1-P6)
- Time estimates
- Code examples provided
- Locations (file:line numbers)

---

## Step 2: Fix CRITICAL Security Issue (5 minutes)

**⚠️ DO THIS FIRST - Security Risk**

**File:** `empirica/data/session_database.py`  
**Function:** `update_cascade_phase()` (lines 565-571)  
**Issue:** SQL injection risk via f-string column name

**Fix Option A (Recommended - Whitelist):**
```python
# Add at top of SessionDatabase class or module level:
VALID_PHASES = {'preflight', 'think', 'plan', 'investigate', 'check', 'act', 'postflight'}

# Modify function (line 565):
def update_cascade_phase(self, cascade_id: str, phase: str, completed: bool = True):
    """Mark cascade phase as completed"""
    # SECURITY: Validate phase parameter
    if phase not in VALID_PHASES:
        raise ValueError(f"Invalid phase: {phase}. Must be one of {VALID_PHASES}")
    
    phase_column = f"{phase}_completed"
    cursor = self.conn.cursor()
    cursor.execute(f"""
        UPDATE cascades SET {phase_column} = ? WHERE cascade_id = ?
    """, (completed, cascade_id))
    self.conn.commit()
```

**Verification:** Run existing tests to ensure no breakage.

---

## Step 3: P1 - Replace print() with logging (45 minutes)

**Impact:** HIGH | **Effort:** LOW | **ROI:** ★★★★★

**Files to modify (19 print statements):**
1. `empirica/core/metacognition_12d_monitor/twelve_vector_self_awareness.py` - 12 prints
2. `empirica/core/canonical/canonical_goal_orchestrator.py` - 3 prints
3. `empirica/core/metacognition_12d_monitor/__init__.py` - 1 print
4. `empirica/core/metacognition_12d_monitor/enhanced_uvl_protocol.py` - 1 print
5. `empirica/core/metacognition_12d_monitor/metacognition_12d_monitor.py` - 1 print
6. `empirica/core/canonical/canonical_epistemic_assessment.py` - 1 print

**Setup (add to empirica/core/__init__.py or each file):**
```python
import logging
logger = logging.getLogger(__name__)
```

**Replacement Pattern:**
```python
# Before:
print(f"🧠✨ 12-Vector Self-Awareness Monitor initialized")
print(f"   🤖 AI ID: {ai_id}")

# After:
logger.info("12-Vector Self-Awareness Monitor initialized", extra={"ai_id": ai_id})
```

**Keep emojis or strip?** Your choice - emojis are fine in logs if desired.

**Verification:** 
```bash
grep -rn "print(" empirica/core empirica/data --include="*.py" | grep -v "# print"
# Should return 0 results
```

---

## Step 4: P2 - Centralize Threshold Constants (30 minutes)

**Impact:** HIGH | **Effort:** LOW | **ROI:** ★★★★★

**Create new file:** `empirica/core/canonical/thresholds.py`

**Content (copy from REFACTORING_PRIORITIES.md lines 73-99):**
```python
"""
Canonical Epistemic Thresholds

Central configuration for all epistemic assessment thresholds.
Modify values here to tune CASCADE behavior globally.
"""

from dataclasses import dataclass

@dataclass(frozen=True)
class EpistemicThresholds:
    """Canonical epistemic thresholds for CASCADE workflow"""
    
    # Engagement gate
    ENGAGEMENT_MIN: float = 0.60  # Must meet to proceed
    ENGAGEMENT_HIGH: float = 0.80  # High collaboration mode
    ENGAGEMENT_CRITICAL: float = 0.40  # Request clarification
    
    # Foundation tier
    KNOW_MIN: float = 0.70  # Adequate domain knowledge
    CONTEXT_MIN: float = 0.70  # Adequate environmental understanding
    
    # Comprehension tier  
    CLARITY_MIN: float = 0.60  # Task understanding threshold
    
    # Meta-epistemic
    UNCERTAINTY_HIGH: float = 0.80  # Triggers investigation
    
    # Overall confidence
    CONFIDENCE_PROCEED: float = 0.70  # Minimum to ACT
    CONFIDENCE_CAUTION: float = 0.50  # Proceed with care

# Default instance
CANONICAL_THRESHOLDS = EpistemicThresholds()
```

**Update 3 files to use thresholds:**

1. **`canonical_goal_orchestrator.py`** (8 hardcoded values around lines 178-350):
```python
# Add import:
from .thresholds import CANONICAL_THRESHOLDS as T

# Replace:
if engagement >= 0.80:  →  if engagement >= T.ENGAGEMENT_HIGH:
if engagement >= 0.60:  →  if engagement >= T.ENGAGEMENT_MIN:
if clarity.score < 0.60:  →  if clarity.score < T.CLARITY_MIN:
if know.score < 0.70:  →  if know.score < T.KNOW_MIN:
if context.score < 0.70:  →  if context.score < T.CONTEXT_MIN:
```

2. **`canonical_epistemic_assessment.py`** (3 values):
```python
from .thresholds import CANONICAL_THRESHOLDS as T
# Update engagement checks
```

3. **`metacognitive_cascade.py`** (2 values):
```python
from empirica.core.canonical.thresholds import CANONICAL_THRESHOLDS as T
# Update confidence checks
```

**Note:** `reflex_frame.py` already has `ENGAGEMENT_THRESHOLD = 0.60` constant - you can replace it or keep for backward compat.

**Verification:**
```bash
# Should find fewer hardcoded threshold comparisons:
grep -rn "0\.60\|0\.70\|0\.80" empirica/core/canonical empirica/core/metacognitive_cascade --include="*.py"
```

---

## Step 5: STOP and Report (5 minutes)

**After P1 & P2 (total ~80 minutes):**

1. Run tests: `pytest tests/` (if tests exist)
2. Check git diff: `git diff --stat`
3. Commit changes: 
   ```bash
   git add -A
   git commit -m "refactor: P1-P2 quick wins - replace print() with logging, centralize thresholds

   - Replace 19 print() statements with logging module
   - Create canonical thresholds.py with EpistemicThresholds class
   - Update 3 files to use centralized threshold constants
   - Fix SQL injection in update_cascade_phase() with whitelist validation
   
   Fixes: CODE_QUALITY_REPORT.md P1, P2 + DEEP_DIVE_ANALYSIS.md security issue"
   ```

4. Report back to user:
   - What you completed
   - Test results
   - Any issues encountered
   - Ready for P3-P6 or stop here?

---

## Optional: P3-P6 (Defer if Time Limited)

**Only do these if explicitly requested or you have 4+ hours:**

### P3: Refactor `__init__()` (3-4 hours)
- Extract 868-line __init__() into smaller methods
- See REFACTORING_PRIORITIES.md lines 125-176
- **Risk:** MEDIUM (core component, test thoroughly)

### P4: Refactor `_create_tables()` (2 hours)
- Split 447-line function into per-table methods
- See REFACTORING_PRIORITIES.md lines 178-213

### P5-P6: Lower priority
- Prompt builders (risky, might break LLM assessment)
- DEPRECATED parameters (needs migration plan)

---

## Testing Guidelines

**Before each change:**
```bash
# Create branch
git checkout -b refactor/p1-p2-quick-wins
```

**After changes:**
```bash
# Check syntax
python3 -m py_compile empirica/core/**/*.py empirica/data/*.py

# Run Python import test
cd /home/yogapad/empirical-ai/empirica
python3 -c "
import sys
sys.path.insert(0, '.')
from empirica.core.canonical import CanonicalEpistemicAssessor
from empirica.data.session_database import SessionDatabase
print('✅ Imports successful')
"

# If tests exist:
pytest tests/ -v

# If no tests, spot check:
python3 -c "
from empirica.data.session_database import SessionDatabase
db = SessionDatabase()
print('✅ Database initialized')
"
```

---

## What NOT to Do

❌ **Don't** modify logic/algorithms (just cleanup)  
❌ **Don't** change function signatures (breaks backward compat)  
❌ **Don't** refactor P3-P6 without explicit approval (too risky)  
❌ **Don't** remove comments or documentation  
❌ **Don't** "improve" working code that isn't in the reports  

✅ **Do** follow the reports exactly  
✅ **Do** test after each change  
✅ **Do** ask if unclear  
✅ **Do** report any issues you find  

---

## Error Handling

**If tests fail:**
1. Read error message carefully
2. Check if you broke an import
3. Revert last change: `git checkout -- <file>`
4. Try again more carefully
5. Report issue to user if stuck

**If imports fail:**
1. Check for typos in new code
2. Verify file paths are correct
3. Check Python syntax: `python3 -m py_compile <file>`

---

## Success Criteria

**P1-P2 Complete When:**
- ✅ Zero print() statements in empirica/core and empirica/data
- ✅ thresholds.py created with EpistemicThresholds class
- ✅ 3 files updated to use CANONICAL_THRESHOLDS
- ✅ SQL injection fixed with validation
- ✅ All imports work
- ✅ No test failures (if tests exist)
- ✅ Git commit created with clear message

---

## Time Breakdown

| Task | Time | Priority |
|------|------|----------|
| Read reports | 5 min | REQUIRED |
| Fix SQL injection | 5 min | **CRITICAL** |
| P1: Replace prints | 45 min | HIGH |
| P2: Centralize thresholds | 30 min | HIGH |
| Testing & commit | 15 min | REQUIRED |
| **TOTAL** | **100 min** | **P1-P2** |

---

## Questions to Ask if Unclear

1. "Should I keep emojis in log messages?"
2. "Should I handle P3-P6 or stop after P1-P2?"
3. "Tests are failing - what should I do?"
4. "Found additional issues - should I fix them?"

---

## Final Notes

- **Code quality is already EXCELLENT** - you're just cleaning up
- **No critical bugs exist** - this is maintenance, not firefighting
- **Take your time** - accuracy > speed
- **Ask questions** - better to clarify than guess
- **Small commits** - one per priority (P1, P2, security fix)

**You've got comprehensive reports with exact locations and fixes. Just follow the plan!**

Good luck! 🚀

---

**Reports Location:**
- `/home/yogapad/empirical-ai/empirica/CODE_QUALITY_REPORT.md`
- `/home/yogapad/empirical-ai/empirica/REFACTORING_PRIORITIES.md`
- `/home/yogapad/empirical-ai/empirica/DEEP_DIVE_ANALYSIS.md`

**Working Directory:** `/home/yogapad/empirical-ai/empirica`

---

*Created: 2025-11-13 by Claude Sonnet 3.5*  
*For: MiniMax autonomous agent*  
*Session: a89b9d94-d907-4a95-ab8d-df8824990bec*
