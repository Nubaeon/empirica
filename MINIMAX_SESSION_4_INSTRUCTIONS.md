# MiniMax Session 4 - Strategic Instructions

**Date:** 2025-11-14  
**Resume From:** Session 3 checkpoint (24/140 prints complete)  
**Primary Goal:** Tackle `metacognitive_cascade.py` (116 prints) strategically

---

## Context: Where You Left Off

**Session 3 Achievement:** ✅ 
- Completed 24 prints across 2 files (quick wins)
- investigation_plugin.py: 11 → 0 prints ✅
- session_database.py: 13 → 0 prints ✅

**Remaining Work:**
- 🔄 **P1:** 116 prints in `metacognitive_cascade.py` (LARGE FILE)
- ❌ **P2:** Threshold centralization
- ❌ **Security:** SQL injection fix

---

## 🎯 Session 4 Objective

**Tackle the large file strategically** - Don't try to do all 116 prints at once!

### Recommended Approach: Strategic Division

**Option B from your checkpoint** is the right call:
1. Analyze file structure first
2. Identify logical sections
3. Complete ONE section this session
4. Create checkpoint
5. Resume in Session 5 for next section

---

## 🚀 Empirica Workflow Reminder

### Phase Sequence:
```
PREFLIGHT → INVESTIGATE → CHECK → ACT → POSTFLIGHT
```

### ⚠️ CRITICAL: Round Tracking

**You have 50 rounds per session.** Track your progress:

1. **Rounds 1-10:** PREFLIGHT + INVESTIGATE
2. **Rounds 10-15:** CHECK (epistemic assessment)
3. **Rounds 15-45:** ACT (implementation)
4. **Rounds 45-48:** CHECK again if needed
5. **Rounds 48-50:** POSTFLIGHT + checkpoint

### 🎯 Uncertainty Management

**As you approach round 40-45:**
- If uncertainty > 0.3: **Create checkpoint, resume next session**
- If confidence > 0.8 AND < 10 rounds left: **Push to complete**
- If multiple unknowns remain: **Checkpoint early**

**From your system prompt:**
> "As I approach 50 rounds or when my confidence reaches high levels, 
> I should perform an epistemic CHECK to validate my understanding."

---

## 📋 Step-by-Step Instructions

### Step 1: PREFLIGHT (Rounds 1-3)

```bash
# Bootstrap or resume session
empirica bootstrap-session --session_type development

# Run PREFLIGHT
empirica preflight --prompt "Resume P1 refactoring at metacognitive_cascade.py (116 prints). Strategic approach: analyze file structure, identify sections, complete ONE section this session."
```

**Expected epistemic state:**
- KNOW: ~0.70 (you've done this twice already)
- DO: ~0.65 (large file, but known pattern)
- UNCERTAINTY: ~0.35 (size is unknown, structure unclear)

### Step 2: INVESTIGATE (Rounds 3-15)

**Investigation Goal:** Understand file structure + print distribution

```bash
# Analyze the file structure
view /home/yogapad/empirical-ai/empirica/empirica/core/metacognitive_cascade/metacognitive_cascade.py

# Count prints by section (estimate distribution)
grep -n "print(" empirica/core/metacognitive_cascade/metacognitive_cascade.py | head -40
grep -n "print(" empirica/core/metacognitive_cascade/metacognitive_cascade.py | tail -40

# Identify logical sections (classes, methods, phases)
grep -n "class\|def " empirica/core/metacognitive_cascade/metacognitive_cascade.py
```

**Investigation deliverables:**
1. ✅ Identified 3-4 logical sections in the file
2. ✅ Estimated print count per section
3. ✅ Chosen target section for Session 4
4. ✅ Confirmed logging import location

**Target epistemic state after investigation:**
- KNOW: 0.80+ (understand file structure)
- DO: 0.75+ (clear plan for Section 1)
- UNCERTAINTY: <0.30

### Step 3: CHECK (Rounds 15-18)

```bash
empirica execute-check \
  --session_id YOUR_SESSION_ID \
  --findings "File has X logical sections. Section 1 contains ~Y prints. Strategy: tackle Section 1 (lines A-B) this session." \
  --remaining_unknowns "May encounter unexpected print patterns" \
  --confidence_to_proceed 0.80
```

**Decision criteria:**
- ✅ If confidence ≥ 0.80 → Proceed to ACT
- ⚠️ If confidence < 0.70 → More investigation
- ❌ If confidence < 0.60 → Checkpoint, reassess strategy

### Step 4: ACT (Rounds 18-45)

**Target:** Complete ONE section of metacognitive_cascade.py

**Suggested Section 1:** Phase management prints (estimated ~30-40 prints)
- Focus on: `__init__`, `run()`, phase transitions
- Avoid: Plugin system, assessment logic (save for later)

**Implementation pattern:**
```python
# 1. Verify logging import exists (should be at top)
import logging
logger = logging.getLogger(__name__)

# 2. Replace prints in targeted section
# Old: print(f"🎯 Starting cascade...")
# New: logger.info("Starting cascade...")

# 3. Test after every 10-15 replacements
pytest tests/ -k metacognitive_cascade -v

# 4. Commit progress incrementally
git add empirica/core/metacognitive_cascade/metacognitive_cascade.py
git commit -m "refactor: Replace Section 1 prints in metacognitive_cascade.py (X/116)"
```

**Round tracking during ACT:**
- **Round 25:** Should have completed ~10-15 prints
- **Round 35:** Should have completed ~20-30 prints
- **Round 45:** Decision point (see below)

### Step 5: Decision Point at Round 45

**If you've completed Section 1:**
✅ **Proceed to POSTFLIGHT** (Step 6)

**If Section 1 incomplete:**
⚠️ **Create emergency checkpoint:**
```bash
# Commit current work
git add -A
git commit -m "WIP: Section 1 progress (X/Y prints) - checkpoint at round 45"

# Document in checkpoint file
echo "Session 4 incomplete - resume Section 1 at line Z" >> CHECKPOINT_SESSION4_PROGRESS.md
```

**If uncertainty increased:**
❌ **Stop, checkpoint, reassess:**
- Something unexpected happened
- Document unknowns
- Resume with fresh strategy in Session 5

### Step 6: POSTFLIGHT (Rounds 45-50)

```bash
empirica execute-postflight \
  --session_id YOUR_SESSION_ID \
  --task_summary "Completed Section 1 of metacognitive_cascade.py: X prints replaced. Y prints remain in Sections 2-3."
```

**Update checkpoint:**
```bash
# Edit CHECKPOINT_SESSION4_PROGRESS.md
# Document:
# - Prints completed: X (Session 4) + 24 (Session 3) = Total
# - Prints remaining: 116 - X
# - Section 1 status: COMPLETE ✅
# - Next session target: Section 2
```

**Commit and push:**
```bash
git add -A
git commit -m "refactor: Complete Section 1 of metacognitive_cascade.py (Session 4 checkpoint)"
git push origin master
```

---

## 🎯 Success Criteria

### Minimum Success (Complete P1 Section 1):
- ✅ 30-40 prints replaced in metacognitive_cascade.py Section 1
- ✅ Tests pass
- ✅ Checkpoint created
- ✅ Clear plan for Section 2

### Stretch Goal (If time permits):
- ✅ Section 1 complete + Section 2 started
- ✅ 50-70 prints replaced total
- ✅ Less than 70 prints remaining

---

## ⚠️ Common Pitfalls to Avoid

### 1. Don't try to do all 116 prints at once
**Why:** You'll hit round limit before completion, lose progress
**Fix:** Strategic division (Section 1 this session, Section 2 next)

### 2. Don't forget to track rounds
**Why:** Running out of rounds without checkpoint is bad
**Fix:** Check round count every 10 rounds, checkpoint at 45 if needed

### 3. Don't skip CHECK phase
**Why:** You need epistemic validation before large work
**Fix:** Explicit CHECK at rounds 15-18 before ACT

### 4. Don't ignore increasing uncertainty
**Why:** Sign you've hit unexpected complexity
**Fix:** Checkpoint early, reassess strategy

---

## 📊 Epistemic Self-Assessment Guidance

### PREFLIGHT targets:
- KNOW: 0.70-0.75 (familiar pattern, unknown file structure)
- DO: 0.65-0.70 (proven approach, but large scale)
- UNCERTAINTY: 0.30-0.35 (file size is unknown)

### After INVESTIGATION targets:
- KNOW: 0.80-0.85 (file structure understood)
- DO: 0.75-0.80 (clear section plan)
- UNCERTAINTY: 0.20-0.25 (reduced unknowns)

### CHECK decision:
- Confidence ≥ 0.80 → ACT ✅
- Confidence 0.70-0.79 → More investigation ⚠️
- Confidence < 0.70 → Checkpoint, reassess ❌

### POSTFLIGHT reflection:
- Did Section 1 take longer than expected?
- Was print distribution accurate?
- Should Section 2 strategy change?

---

## 📚 Reference Files

**Completed examples:**
- `empirica/core/metacognitive_cascade/investigation_plugin.py` (Session 3)
- `empirica/data/session_database.py` (Session 3)

**Current target:**
- `empirica/core/metacognitive_cascade/metacognitive_cascade.py`

**Checkpoint tracking:**
- `CHECKPOINT_SESSION3_PROGRESS.md` (your last checkpoint)
- `CHECKPOINT_SESSION4_PROGRESS.md` (create this session)

**Instructions archive:**
- `MINIMAX_SESSION_2_RESUME.md`
- `MINIMAX_SESSION_4_INSTRUCTIONS.md` (this file)

---

## 🚦 Go/No-Go Decision Tree

```
START
  ↓
PREFLIGHT: Can I understand the file structure?
  ├─ Yes (confidence ≥ 0.70) → INVESTIGATE
  └─ No (confidence < 0.70) → Need guidance, ask human
       ↓
INVESTIGATE: Can I identify clear sections?
  ├─ Yes (3-4 sections identified) → CHECK
  └─ No (file too complex) → Checkpoint, ask for guidance
       ↓
CHECK: Can I complete Section 1 in 30 rounds?
  ├─ Yes (confidence ≥ 0.80) → ACT
  ├─ Maybe (confidence 0.70-0.79) → More investigation
  └─ No (confidence < 0.70) → Checkpoint, reassess
       ↓
ACT: Am I making progress?
  ├─ Yes + Round < 45 → Continue
  ├─ Yes + Round ≥ 45 → Complete section, POSTFLIGHT
  ├─ Slow + Round < 40 → Continue cautiously
  └─ Blocked + Any round → Emergency checkpoint
       ↓
POSTFLIGHT: Was Section 1 completed?
  ├─ Yes → Success! ✅ Ready for Session 5
  └─ No → Partial success ⚠️ Resume Section 1 in Session 5
```

---

## 🎓 Learning from Session 3

**What worked:**
- ✅ Strategic checkpoint creation
- ✅ "Quick wins" approach for smaller files
- ✅ Consistent logging pattern

**What to apply:**
- Strategic division for large files
- Round tracking discipline
- Early checkpointing if uncertainty rises

---

## 🚀 Ready to Start?

**Your first command:**
```bash
empirica bootstrap-session --session_type development
```

**Then:**
```bash
empirica preflight --prompt "Resume P1 refactoring at metacognitive_cascade.py (116 prints). Strategic approach: analyze file structure, identify sections, complete ONE section this session."
```

**Remember:**
1. Track rounds (you have 50)
2. Checkpoint at round 45 if incomplete
3. One section per session is success
4. Uncertainty > 0.3 at round 40+ → checkpoint early

---

**Good luck, MiniMax! Focus on Section 1 completion. 🎯**

*File: `/home/yogapad/empirical-ai/empirica/MINIMAX_SESSION_4_INSTRUCTIONS.md`*
