# MiniMax Session 5 - Final Push Instructions

**Date:** 2025-11-14  
**Resume From:** Session 4 complete (42/140 prints done, 30% complete)  
**Primary Goal:** Complete remaining 49 prints in metacognitive_cascade.py

---

## 🎉 Session 4 Achievement Review

**Excellent work!** You completed Section 1 strategically:
- ✅ 18 prints refactored (lines 65-343)
- ✅ Clean checkpoint created at round 35/50
- ✅ Confidence: 0.833 (well-calibrated)
- ✅ Strategic division approach validated

**Total Progress:** 42/140 prints complete (30%)

---

## 📊 Current State: What Remains

### Remaining Prints: 49 total

**Already identified in metacognitive_cascade.py:**

1. **Line 712:** ACT DB error handler (1 print)
2. **Lines 816-819:** Calibration delta results (4 prints)
3. **Lines 878, 887-888:** MCP assessment messages (3 prints)
4. **Line 1037:** MCP error handler (1 print)
5. **Line 1169:** Log path info (1 print)
6. **Lines 1234, 1239:** Gap analysis headers (2 prints)
7. **Lines 1242-1243:** Gap details loop (2 prints)
8. **Lines 1265, 1267-1269:** Tool capabilities (4 prints)
9. **Lines 1274-1275:** Focus recommendations (2 prints)

**Plus unknown prints in other files (if any)**

---

## 🎯 Session 5 Objective

**Complete P1 entirely** - All 140 print statements → logger

### Two-Phase Approach:

**Phase A (Priority):** Complete metacognitive_cascade.py
- 49 prints remaining in this file
- These are scattered (not contiguous like Section 1)
- Most are error handlers, results display, debug info

**Phase B (If time):** Scan for any missed prints in other files
- Quick grep to verify no prints left behind
- Should be 0-5 at most

---

## 🚀 Empirica Workflow for Session 5

### Phase Sequence:
```
PREFLIGHT (Rounds 1-5)
  ↓
INVESTIGATE (Rounds 5-12)
  ↓
CHECK (Rounds 12-15)
  ↓
ACT - Phase A (Rounds 15-40)
  ↓
CHECK (Round 40-42) [if needed]
  ↓
ACT - Phase B (Rounds 42-47) [if time permits]
  ↓
POSTFLIGHT (Rounds 47-50)
```

---

## 📋 Step-by-Step Instructions

### Step 1: PREFLIGHT (Rounds 1-5)

```bash
# Bootstrap session
empirica bootstrap-session --session_type development

# Run PREFLIGHT
empirica preflight --prompt "Complete P1 refactoring: 49 prints remaining in metacognitive_cascade.py. These are scattered (error handlers, results, debug). Goal: finish P1 entirely this session."
```

**Expected epistemic state:**
- KNOW: 0.85+ (you've done this successfully 3 times)
- DO: 0.80+ (proven pattern, known file)
- UNCERTAINTY: 0.20-0.25 (scattered prints but known locations)

### Step 2: INVESTIGATE (Rounds 5-12)

**Investigation Goal:** Confirm exact locations of all 49 prints

```bash
# Get full list of remaining prints
cd /home/yogapad/empirical-ai/empirica
grep -n "print(" empirica/core/metacognitive_cascade/metacognitive_cascade.py > /tmp/remaining_prints.txt
cat /tmp/remaining_prints.txt

# Count to verify
wc -l /tmp/remaining_prints.txt
# Should show 49

# Check if any prints in other files
grep -rn "print(" empirica/ --include="*.py" | grep -v "test" | grep -v ".pyc" | grep -v "__pycache__" | wc -l
# Should be 49 (all in metacognitive_cascade.py)
```

**Investigation deliverables:**
1. ✅ Confirmed 49 prints in metacognitive_cascade.py
2. ✅ Verified 0 prints in other non-test files
3. ✅ Grouped prints by function/section for systematic replacement
4. ✅ Identified any tricky patterns (multi-line prints, f-strings)

**Target epistemic state after investigation:**
- KNOW: 0.90+ (complete understanding)
- DO: 0.85+ (clear execution plan)
- UNCERTAINTY: <0.20

### Step 3: CHECK (Rounds 12-15)

```bash
empirica execute-check \
  --session_id YOUR_SESSION_ID \
  --findings "49 prints confirmed in metacognitive_cascade.py. All are single-line or simple patterns. No prints in other files. Strategy: systematic replacement in order, test every 10 prints." \
  --remaining_unknowns "None - all locations identified" \
  --confidence_to_proceed 0.90
```

**Decision criteria:**
- ✅ If confidence ≥ 0.85 → Proceed to ACT (you're ready!)
- ⚠️ If confidence 0.75-0.84 → Quick clarification, then ACT
- ❌ If confidence < 0.75 → Something's wrong, reassess

### Step 4: ACT - Phase A (Rounds 15-40)

**Target:** Complete all 49 prints in metacognitive_cascade.py

**Systematic Approach:**

```python
# Group prints by function for logical processing:

# Group 1: Error handlers (lines 712, 1037)
# Replace with: logger.warning() or logger.error()

# Group 2: Result displays (lines 816-819, 878, 1169)
# Replace with: logger.info()

# Group 3: Debug/analysis (lines 887-888, 1234, 1239, 1242-1243)
# Replace with: logger.debug() or logger.info()

# Group 4: Tool recommendations (lines 1265, 1267-1269, 1274-1275)
# Replace with: logger.info()
```

**Implementation Pattern:**

```python
# 1. Work in batches of 8-10 prints at a time
# 2. After each batch:
#    - Save file
#    - Quick syntax check: python -m py_compile <file>
#    - Commit progress

# Example commit pattern:
git add empirica/core/metacognitive_cascade/metacognitive_cascade.py
git commit -m "refactor: Replace prints 1-10 in metacognitive_cascade.py (error handlers)"
```

**Round Tracking (CRITICAL):**
- **Round 20:** Should have completed ~10 prints (batch 1-2)
- **Round 25:** Should have completed ~20 prints (batch 1-4)
- **Round 30:** Should have completed ~30 prints (batch 1-6)
- **Round 35:** Should have completed ~40 prints (batch 1-8)
- **Round 40:** CHECK point (see Step 5)

### Step 5: CHECK at Round 40

**At round 40, assess progress:**

**If all 49 prints complete:**
✅ **Excellent!** Proceed to Phase B (verify no other files)

**If 40-49 prints complete:**
✅ **Good progress!** Push to finish remaining ~9 prints by round 45

**If < 40 prints complete:**
⚠️ **Reassess:** 
- Skip Phase B
- Focus on completing metacognitive_cascade.py only
- Create checkpoint at round 48

### Step 6: ACT - Phase B (Rounds 42-47) [Optional]

**Only if Phase A complete with time remaining**

```bash
# Verify no prints in other files
grep -rn "print(" empirica/ --include="*.py" \
  | grep -v "test" \
  | grep -v ".pyc" \
  | grep -v "__pycache__" \
  | grep -v "metacognitive_cascade.py"

# Should return 0 results
# If any found: replace them
```

### Step 7: POSTFLIGHT (Rounds 47-50)

```bash
empirica execute-postflight \
  --session_id YOUR_SESSION_ID \
  --task_summary "P1 COMPLETE: All 140 print statements replaced with logging. 49 prints in metacognitive_cascade.py replaced this session. Total: 140/140 (100%)"
```

**Final verification:**

```bash
# Verify P1 complete
grep -rn "print(" empirica/ --include="*.py" | grep -v "test" | wc -l
# Should show 0

# Check all modified files
git status
git diff --stat
```

**Create final checkpoint:**

```bash
# Create CHECKPOINT_SESSION5_P1_COMPLETE.md
cat > CHECKPOINT_SESSION5_P1_COMPLETE.md << 'EOF'
# Session 5 - P1 COMPLETE! 🎉

**Date:** 2025-11-14
**Status:** P1 (Print → Logging) 100% COMPLETE

## Achievement
- 49 prints replaced in metacognitive_cascade.py
- 140/140 total prints replaced across all files
- 0 print statements remain in production code

## Files Completed
1. ✅ investigation_plugin.py (11 prints)
2. ✅ session_database.py (13 prints)
3. ✅ metacognitive_cascade.py (116 prints total)
   - Section 1: 18 prints (Session 4)
   - Sections 2-4: 49 prints (Session 5)
   - Missed in Session 4: 49 prints (Session 5)

## Next Tasks
- P2: Threshold centralization
- Security: SQL injection fix

## Calibration
- Predicted completion: Session 5 ✅
- Actual completion: Session 5 ✅
- Confidence: Well-calibrated across all sessions
EOF

# Commit everything
git add -A
git commit -m "refactor: P1 COMPLETE - All 140 print statements replaced with logging

Session 5 final push:
- Completed remaining 49 prints in metacognitive_cascade.py
- Verified 0 prints remain in production code
- All files use proper logging framework

Next: P2 (threshold centralization) and security fix"

git push origin master
```

---

## 🎯 Success Criteria

### Minimum Success (Complete P1):
- ✅ All 49 prints in metacognitive_cascade.py replaced
- ✅ 0 prints remaining in any production file (non-test)
- ✅ Tests pass (or at least no new failures)
- ✅ Checkpoint created

### Stretch Goal (Start P2):
- ✅ P1 complete by round 40
- ✅ Created `thresholds.py` with centralized constants
- ✅ Started replacing hardcoded thresholds
- ✅ Clear plan for P2 completion

---

## ⚠️ Common Pitfalls to Avoid

### 1. Don't batch too aggressively
**Why:** 49 prints in one go = risky, hard to debug
**Fix:** Work in batches of 8-10, commit each batch

### 2. Don't forget the test files
**Why:** Test files can legitimately have prints
**Fix:** Only replace prints in `empirica/` (not `tests/`)

### 3. Don't skip verification
**Why:** Easy to miss a print in a large file
**Fix:** Run grep verification at round 40 and round 47

### 4. Don't run out of rounds
**Why:** 49 prints is doable but needs discipline
**Fix:** Track progress every 5 rounds, checkpoint at 48 if needed

---

## 📊 Epistemic Self-Assessment Targets

### PREFLIGHT targets:
- KNOW: 0.85-0.90 (very familiar pattern, known file)
- DO: 0.80-0.85 (proven approach 3x already)
- UNCERTAINTY: 0.20-0.25 (minimal unknowns)

### After INVESTIGATION targets:
- KNOW: 0.90-0.95 (complete print inventory)
- DO: 0.85-0.90 (clear systematic plan)
- UNCERTAINTY: 0.15-0.20 (almost no unknowns)

### CHECK decision at round 12-15:
- Confidence ≥ 0.85 → ACT immediately ✅
- Confidence 0.75-0.84 → Brief clarification, then ACT ⚠️
- Confidence < 0.75 → Unexpected issue, reassess ❌

### CHECK decision at round 40:
- If ≥ 40 prints done → Finish remaining + Phase B ✅
- If 30-39 prints done → Focus only on finishing P1 ⚠️
- If < 30 prints done → Emergency checkpoint ❌

### POSTFLIGHT reflection:
- Was P1 completed? (Should be YES!)
- Any unexpected challenges?
- Ready for P2?

---

## 📚 Reference Files

**Your completed work:**
- Session 3: investigation_plugin.py (11 prints)
- Session 3: session_database.py (13 prints)
- Session 4: metacognitive_cascade.py Section 1 (18 prints)

**Current target:**
- metacognitive_cascade.py: 49 remaining prints (scattered throughout)

**Checkpoints:**
- `CHECKPOINT_SESSION3_PROGRESS.md`
- `CHECKPOINT_SESSION4_SECTION1_COMPLETE.md`
- `CHECKPOINT_SESSION5_P1_COMPLETE.md` (create this!)

---

## 🚦 Go/No-Go Decision Tree

```
START
  ↓
PREFLIGHT: Can I complete 49 scattered prints in ~35 rounds?
  ├─ Yes (confidence ≥ 0.85) → INVESTIGATE
  └─ No → Unexpected, ask for guidance
       ↓
INVESTIGATE: Have I located all 49 prints?
  ├─ Yes (verified with grep) → CHECK
  └─ No (count mismatch) → Investigate more
       ↓
CHECK: Ready to execute systematic replacement?
  ├─ Yes (confidence ≥ 0.85) → ACT Phase A
  └─ No → Clarify approach
       ↓
ACT Phase A: Making progress on 49 prints?
  ├─ Round < 40 → Continue batching
  ├─ Round 40 + ≥40 prints done → Finish + Phase B
  ├─ Round 40 + 30-39 prints done → Focus on P1 only
  └─ Round 40 + <30 prints done → Emergency checkpoint
       ↓
Round 47-50: Is P1 complete?
  ├─ Yes → POSTFLIGHT ✅
  └─ No → Document what remains, checkpoint
```

---

## 🎓 Learning From Sessions 3-4

**What worked exceptionally well:**
- ✅ Strategic division (Section 1 approach)
- ✅ Disciplined checkpointing (round 35/50)
- ✅ Consistent logging pattern
- ✅ Incremental commits
- ✅ Empirica workflow adherence

**Apply to Session 5:**
- Same systematic batch approach (8-10 prints at a time)
- Check progress every 10 rounds
- Commit each batch
- Verify with grep at rounds 40 and 47

---

## 📈 Overall Project Roadmap

**P1 (Print → Logging):** 30% → **100%** (THIS SESSION)
- Files: 3 files, 140 prints total
- Timeline: Sessions 3-5
- Status after Session 5: **COMPLETE** ✅

**P2 (Threshold Centralization):** Start after P1
- Files: Create `thresholds.py` + update 3 files
- Estimated: 1 session
- Status: Not started (Next!)

**Security (SQL Injection):** After P2
- File: `session_database.py`
- Estimated: <1 session
- Status: Not started

---

## 🚀 Ready to Finish P1?

**Your first command:**
```bash
empirica bootstrap-session --session_type development
```

**Then:**
```bash
empirica preflight --prompt "Complete P1 refactoring: 49 prints remaining in metacognitive_cascade.py. These are scattered (error handlers, results, debug). Goal: finish P1 entirely this session."
```

**Remember:**
1. You have 50 rounds (use them wisely!)
2. Work in batches of 8-10 prints
3. Verify at rounds 40 and 47
4. P1 completion is achievable - you've got this! 🎯

---

## 💪 Confidence Boost

**You've already proven you can do this:**
- Session 3: 24 prints replaced ✅
- Session 4: 18 prints replaced ✅
- **Total:** 42/140 (30% done, all successful)

**Session 5 target:** 49 prints (35% of original total)

**You're averaging ~20-25 prints per session.**  
**49 prints in 50 rounds is very doable!**

**One final push, and P1 is DONE!** 🎉

---

**Good luck, MiniMax! Let's finish P1 strong! 💪**

*File: `/home/yogapad/empirical-ai/empirica/MINIMAX_SESSION5_FINAL_PUSH.md`*
