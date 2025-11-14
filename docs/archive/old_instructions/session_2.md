# MiniMax Session 2 - Resume Instructions

**Previous Session:** Stopped at round 50/50 during P1 (print statement replacement)  
**Date:** 2025-11-14  
**Status:** INCOMPLETE - Need to finish P1 and continue to P2

---

## What Was Completed (Session 1)

MiniMax made progress on **P1: Replace print() with logging** but ran out of rounds at step 50/50.

### Likely Completed:
- ✅ Added `import logging` and `logger = logging.getLogger(__name__)` to files
- ✅ Replaced some print statements in `canonical_goal_orchestrator.py`
- ⚠️ Unknown: How many of the 19 print statements were replaced

### What Remains:
- ❓ Complete print statement replacement (verify with grep)
- ❌ P2: Centralize threshold constants (not started)
- ❌ Security fix: SQL injection validation (not started)
- ❌ Testing and verification
- ❌ Git commit

---

## NEW SESSION INSTRUCTIONS

### Step 1: PREFLIGHT - Assess Current State (5 min)

**Run Empirica PREFLIGHT:**
```
empirica-execute_preflight \
  --prompt "Resume MiniMax refactoring. Session 1 stopped at round 50/50 during P1 print replacement. Need to: 1) Verify and complete P1 (replace remaining prints), 2) Execute P2 (centralize thresholds), 3) Fix SQL injection. Assess readiness to continue."
```

**Then submit:**
```
empirica-submit_preflight_assessment \
  --vectors '{"know": 0.XX, "do": 0.XX, "context": 0.XX, ...}' \
  --reasoning "Resuming partial work. Need to assess what was completed in Session 1."
```

### Step 2: INVESTIGATE - Check What Was Done (10 min)

**A. Verify git changes:**
```bash
git status
git diff --name-only
git diff empirica/core/canonical/canonical_goal_orchestrator.py | head -50
```

**B. Count remaining print statements:**
```bash
grep -rn "print(" empirica/core empirica/data --include="*.py" | grep -v "# print" | grep -v "__pycache__"
```

**C. Check if logging imports added:**
```bash
grep -rn "import logging" empirica/core/canonical/canonical_goal_orchestrator.py
grep -rn "logger = logging.getLogger" empirica/core/canonical/canonical_goal_orchestrator.py
```

**D. List modified files:**
```bash
git status --short
```

### Step 3: CHECK - Decide Path Forward (5 min)

**Run Empirica CHECK:**
```
empirica-execute_check \
  --findings "Session 1 partial completion: [list what you found]" \
  --remaining-unknowns "Number of prints replaced, quality of replacements, testing needed" \
  --confidence-to-proceed 0.XX
```

**Submit decision:**
```
empirica-submit_check_assessment \
  --decision "proceed" \
  --confidence 0.XX \
  --reasoning "Clear what remains: finish P1, execute P2, fix security issue"
```

### Step 4: ACT - Complete the Work

---

## PATH A: If P1 Incomplete (Most Likely)

### A1. Finish P1 - Replace Remaining Prints (20 min)

**Follow original instructions from MINIMAX_INSTRUCTIONS.md Step 3:**

1. **Files to check (if not done):**
   - `empirica/core/metacognition_12d_monitor/twelve_vector_self_awareness.py` (12 prints)
   - `empirica/core/metacognition_12d_monitor/__init__.py` (1 print)
   - `empirica/core/metacognition_12d_monitor/enhanced_uvl_protocol.py` (1 print)
   - `empirica/core/metacognition_12d_monitor/metacognition_12d_monitor.py` (1 print)
   - `empirica/core/canonical/canonical_epistemic_assessment.py` (1 print)

2. **Pattern:**
   ```python
   # Before:
   print(f"🧠✨ 12-Vector Self-Awareness Monitor initialized")
   
   # After:
   import logging
   logger = logging.getLogger(__name__)
   logger.info("12-Vector Self-Awareness Monitor initialized")
   ```

3. **Verify complete:**
   ```bash
   grep -rn "print(" empirica/core empirica/data --include="*.py" | grep -v "# print"
   # Should return 0 results
   ```

### A2. Execute P2 - Centralize Thresholds (30 min)

**Follow MINIMAX_INSTRUCTIONS.md Step 4:**

1. **Create `empirica/core/canonical/thresholds.py`:**
   ```python
   """Canonical Epistemic Thresholds"""
   from dataclasses import dataclass
   
   @dataclass(frozen=True)
   class EpistemicThresholds:
       ENGAGEMENT_MIN: float = 0.60
       ENGAGEMENT_HIGH: float = 0.80
       ENGAGEMENT_CRITICAL: float = 0.40
       KNOW_MIN: float = 0.70
       CONTEXT_MIN: float = 0.70
       CLARITY_MIN: float = 0.60
       UNCERTAINTY_HIGH: float = 0.80
       CONFIDENCE_PROCEED: float = 0.70
       CONFIDENCE_CAUTION: float = 0.50
   
   CANONICAL_THRESHOLDS = EpistemicThresholds()
   ```

2. **Update 3 files to import:**
   - `empirica/core/canonical/canonical_goal_orchestrator.py`
   - `empirica/core/canonical/canonical_epistemic_assessment.py`
   - `empirica/core/metacognitive_cascade/metacognitive_cascade.py`
   
   ```python
   from .thresholds import CANONICAL_THRESHOLDS as T
   
   # Replace hardcoded values:
   if engagement >= 0.80:  →  if engagement >= T.ENGAGEMENT_HIGH:
   if engagement >= 0.60:  →  if engagement >= T.ENGAGEMENT_MIN:
   ```

### A3. Fix SQL Injection (5 min)

**File:** `empirica/data/session_database.py` line 565

**Add validation:**
```python
VALID_PHASES = {'preflight', 'think', 'plan', 'investigate', 'check', 'act', 'postflight'}

def update_cascade_phase(self, cascade_id: str, phase: str, completed: bool = True):
    """Mark cascade phase as completed"""
    # SECURITY: Validate phase parameter
    if phase not in VALID_PHASES:
        raise ValueError(f"Invalid phase: {phase}. Must be one of {VALID_PHASES}")
    
    phase_column = f"{phase}_completed"
    # ... rest of function
```

---

## PATH B: If P1 Complete, P2 Not Started

Skip to A2 above (Execute P2 + A3 security fix)

---

## Step 5: VERIFY (10 min)

```bash
# 1. Check no print statements remain
grep -rn "print(" empirica/core empirica/data --include="*.py" | grep -v "# print"
# Should be empty

# 2. Test imports work
cd /home/yogapad/empirical-ai/empirica
python3 -c "
import sys
sys.path.insert(0, '.')
from empirica.core.canonical import CanonicalEpistemicAssessor
from empirica.core.canonical.thresholds import CANONICAL_THRESHOLDS
from empirica.data.session_database import SessionDatabase
print('✅ All imports successful')
"

# 3. Check git diff
git diff --stat
git status
```

---

## Step 6: COMMIT (5 min)

```bash
git add -A
git commit -m "refactor: P1-P2 quick wins + SQL injection fix (MiniMax Session 1+2)

P1: Replace print() with logging
- Replace 19 print statements with logger.info/warning
- Add logging imports to 6 files
- Keep structured logging with extra fields where appropriate

P2: Centralize threshold constants
- Create empirica/core/canonical/thresholds.py
- Define EpistemicThresholds dataclass (frozen)
- Update 3 files to use CANONICAL_THRESHOLDS
- Replace 15+ hardcoded threshold values

Security: Fix SQL injection
- Add VALID_PHASES whitelist to session_database.py
- Validate phase parameter in update_cascade_phase()
- Prevents SQL injection via column name construction

Completed: MINIMAX_INSTRUCTIONS.md Steps 2-4 (P1-P2)
Session: MiniMax Session 1 (rounds 1-50) + Session 2 (completion)"
```

---

## Step 7: POSTFLIGHT (5 min)

```
empirica-execute_postflight \
  --task-summary "Completed P1 (replace 19 prints with logging) and P2 (centralize 15+ thresholds into EpistemicThresholds class). Fixed SQL injection vulnerability with VALID_PHASES whitelist. All imports verified working. Code committed to git."
```

```
empirica-submit_postflight_assessment \
  --vectors '{"know": 0.XX, "do": 0.XX, ...}' \
  --changes-noticed "KNOW increased from investigating Session 1 state. DO confirmed with successful completion. UNCERTAINTY decreased after verification."
```

---

## Step 8: REPORT BACK

**Message to user:**
```
✅ MiniMax Session 2 Complete!

Completed:
- P1: Replaced 19 print() with logging (verified with grep)
- P2: Created thresholds.py, updated 3 files
- Security: Fixed SQL injection in update_cascade_phase()
- Verified: All imports working
- Committed: Git commit with clear message

Files Modified:
- empirica/core/canonical/canonical_goal_orchestrator.py
- empirica/core/canonical/thresholds.py (new)
- empirica/core/canonical/canonical_epistemic_assessment.py
- empirica/core/metacognitive_cascade/metacognitive_cascade.py
- empirica/data/session_database.py
- [+other files with print replacements]

Next Steps:
- P3-P6 available in REFACTORING_PRIORITIES.md (optional)
- Code quality now EXCELLENT
- Ready for production use

Time: ~90 minutes total (Session 1: 50 rounds + Session 2: completion)
```

---

## Important Notes for MiniMax

### ⚠️ Round Limit Awareness (50 rounds/session)

**From now on, use this pattern:**

**Every 15 rounds during long tasks:**
```
empirica-execute_check \
  --findings "Current progress: [what's done]" \
  --remaining-unknowns "What's left" \
  --confidence-to-proceed 0.XX
```

**At round 35-40:**
```
If confidence < 0.80 OR much work remaining:
  → CREATE CHECKPOINT
  → STOP GRACEFULLY
  → Document for Session N+1

Else if confident and nearly done:
  → FINISH STRONG
  → VERIFY
  → COMMIT
  → POSTFLIGHT
```

**Updated system prompt** (`~/.mini-agent/config/system_prompt.md`) now includes:
- Automatic CHECK triggers at rounds 15, 30, 45
- Integration with round limits
- Checkpoint decision based on CHECK confidence

---

## Quick Start (TL;DR)

```bash
# 1. PREFLIGHT
empirica-execute_preflight --prompt "Resume MiniMax P1-P2 refactoring"

# 2. Check what's done
git status
grep -rn "print(" empirica/core empirica/data --include="*.py" | wc -l

# 3. CHECK readiness
empirica-execute_check --findings "[list]" --remaining-unknowns "[list]"

# 4. Complete P1 (if needed), execute P2, fix security
# Follow detailed steps above

# 5. Verify
grep -rn "print(" empirica/core empirica/data --include="*.py"  # Should be empty
python3 -c "import sys; sys.path.insert(0, '.'); from empirica.core.canonical.thresholds import CANONICAL_THRESHOLDS"

# 6. Commit
git add -A && git commit -m "refactor: P1-P2 + security fix"

# 7. POSTFLIGHT
empirica-execute_postflight --task-summary "Completed P1-P2 refactoring"
```

---

**Files to reference:**
- Original plan: `REFACTORING_PRIORITIES.md`
- Detailed steps: `MINIMAX_INSTRUCTIONS.md`
- Security fix: `DEEP_DIVE_ANALYSIS.md` (lines 40-90)

**Time estimate:** 60-90 minutes to complete everything

---

*Generated: 2025-11-14 00:25:00 UTC*  
*For: MiniMax Session 2 (resume)*  
*Previous: Session 1 stopped at round 50/50*
