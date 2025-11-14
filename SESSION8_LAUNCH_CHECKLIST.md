# ✅ MiniMax Session 8 Launch Checklist

**Date:** 2025-01-14  
**Status:** Ready to Launch 🚀  
**Estimated Duration:** 5-10 rounds

---

## 📋 Pre-Launch Checklist

### 1. Documentation Review ✅
- [x] **MINIMAX_SESSION8_FINAL_P2.md** - Instructions complete
- [x] **MINIMAX_CURRENT_STATUS.md** - Status documented
- [x] **HUMAN_SUMMARY_SESSION8_PREP.md** - Human review complete
- [x] **GIT_ENHANCED_REFLEX_LOGGER_PLAN.md** - Phase 1.5 ready
- [x] **FOLDER_CLEANUP_PLAN.md** - Post-session cleanup ready

### 2. Current State Verification ✅
```bash
cd /home/yogapad/empirical-ai/empirica

# Verify git state
git status  # Should be clean

# Verify remaining work
grep -n "self.*_critical = " empirica/core/canonical/reflex_frame.py
# Should show lines 129-131 with hardcoded values

# Verify import exists
grep "from.*thresholds import" empirica/core/canonical/reflex_frame.py
# Should show: from ..thresholds import ENGAGEMENT_THRESHOLD, CRITICAL_THRESHOLDS

# Verify no print statements remain
grep -rn "print(" empirica/core/metacognitive_cascade/metacognitive_cascade.py | wc -l
# Should show: 0
```

### 3. MiniMax System Check ✅
- [x] System prompt reviewed (`~/.mini-agent/config/system_prompt.md`)
- [x] Round tracking guidance present
- [x] Empirica MCP server working
- [x] Git repository clean and ready

### 4. Issue Resolution ✅
- [x] ~~`resume_previous_session` last_n not implemented~~ → VERIFIED WORKING
- [x] Folder cleanup plan created
- [x] Git integration roadmap updated
- [x] Threshold centralization 90% complete

---

## 🚀 Launch Instructions for MiniMax

### Command to Start Session 8
```bash
cd /home/yogapad/empirical-ai/empirica
mini-agent --mcp-config ~/.mini-agent/config/mcp.json
```

### Initial Prompt
```
Please read MINIMAX_SESSION8_FINAL_P2.md and execute the session. This is a simple 3-line fix to complete P2 threshold centralization. Should take 5-10 rounds. Follow Empirica workflow: PREFLIGHT → INVESTIGATE (optional) → CHECK → ACT → POSTFLIGHT.
```

---

## 📊 Expected Session Flow

### PREFLIGHT (Round 1-2)
- Load `MINIMAX_SESSION8_FINAL_P2.md`
- Assess task: 3-line fix in `reflex_frame.py`
- Initial vectors:
  - KNOW: 0.90 (task is clear)
  - UNCERTAINTY: 0.10 (minimal unknowns)
  - DO: 0.95 (simple edit)
  - COMPLETION: 0.95 (straightforward)

### INVESTIGATE (Round 2-3) - Optional
- Verify lines 129-131 in reflex_frame.py
- Confirm import exists
- Review CRITICAL_THRESHOLDS structure

### CHECK (Round 3-4)
- Findings: "3 hardcoded thresholds at lines 129-131, import exists"
- Unknowns: "None"
- Confidence: 0.95+
- Decision: "proceed"

### ACT (Round 4-6)
- Edit `reflex_frame.py` lines 129-131
- Replace hardcoded values with `CRITICAL_THRESHOLDS['...']`
- Git commit with descriptive message

### VERIFY (Round 6-7)
- Grep for remaining hardcoded thresholds
- Verify import usage
- Confirm no regressions

### POSTFLIGHT (Round 7-10)
- Summary: "P2 complete, 3 thresholds centralized"
- Calibration analysis
- Session complete

---

## 🎯 Success Criteria

### Must Achieve ✅
- [ ] Lines 129-131 updated to use `CRITICAL_THRESHOLDS`
- [ ] No hardcoded `0.50`, `0.90` values remain
- [ ] Import statement verified and used
- [ ] Clean git commit with descriptive message
- [ ] P2 marked as 100% COMPLETE

### Quality Markers
- [ ] Rounds: 5-10 (efficiency)
- [ ] Confidence: 0.90+ (well-calibrated)
- [ ] Git: 1 clean commit
- [ ] Tests: No regressions (not required to run, but should pass)

### Red Flags 🚨
- ❌ Rounds > 15 (overthinking)
- ❌ Confidence < 0.80 (misunderstanding task)
- ❌ Multiple commits (should be single atomic change)
- ❌ Edits beyond lines 129-131 (scope creep)

---

## 📝 Post-Session Actions

### Immediate (After POSTFLIGHT)
- [ ] Review commit quality
- [ ] Verify P2 100% complete
- [ ] Check calibration report

### Housekeeping (Same Day)
```bash
cd /home/yogapad/empirical-ai/empirica

# Execute folder cleanup
mkdir -p docs/archive/{session_notes,investigations,completed_work,test_results,phases,old_instructions}

# Move files (see FOLDER_CLEANUP_PLAN.md)
mv CHECKPOINT_SESSION*.md SESSION5_P1_COMPLETE_SUMMARY.md PHASE1_COMPLETE_SUMMARY.md docs/archive/session_notes/
mv ARCHITECTURAL_INVESTIGATION_SUMMARY.md DATABASE_SESSION_QUERY_FINDINGS.md DEEP_DIVE_ANALYSIS.md CODE_QUALITY_REPORT.md LEGACY_COMPONENTS_ASSESSMENT.md docs/archive/investigations/
# ... (see full plan in FOLDER_CLEANUP_PLAN.md)

# Verify cleanup
ls -1 *.md | wc -l  # Should be ~10 files
```

### Documentation Updates
- [ ] Update `WHAT_STILL_TO_DO.md` - mark P2 as ✅ COMPLETE
- [ ] Archive `MINIMAX_SESSION8_FINAL_P2.md` to `docs/archive/old_instructions/session_8_instructions.md`
- [ ] Create Session 9 plan (Phase 1.5 git notes)

---

## 🚀 Phase 1.5 Preparation (After Cleanup)

### Next Major Milestone: Git-Enhanced Reflex Logger
**Goal:** Validate 84% token compression hypothesis

**Steps:**
1. Implement `GitEnhancedReflexLogger` class
2. Add git notes integration
3. Run benchmarking session (Session 9)
4. Measure token usage
5. Validate compression (target: 80%+)

**If Successful:**
- Proceed to Phase 2 (git-native storage)
- Build Sentinel git manager
- Multi-AI coordination via branches

**Documentation Ready:**
- `GIT_ENHANCED_REFLEX_LOGGER_PLAN.md` (14.6 KB)
- `GIT_INTEGRATION_ROADMAP.md` (updated)

---

## 📊 Session 8 Monitoring

### Real-Time Checks (Every 3-5 Rounds)
```
✓ Round count: X/50
✓ Current confidence: 0.XX
✓ Current uncertainty: 0.XX
✓ Task progress: X%
✓ On track? Yes/No
```

### Intervention Triggers
- **Round > 12:** Check if stuck or overthinking
- **Confidence < 0.80:** Clarify task understanding
- **Uncertainty > 0.30:** Investigate what's unclear
- **No commit by Round 10:** Verify not blocked

---

## 💡 Human Supervisor Notes

### MiniMax Track Record ✅
- **Session 5 (P1):** WELL-CALIBRATED, 100% complete
- **Session 7 (P2):** EXCELLENT, 90% complete
- **Pattern:** Systematic, clean commits, good epistemic awareness

### Expected Session 8 Outcome
- **Probability of Success:** 95%+ (simple, well-defined task)
- **Calibration:** Should remain well-calibrated
- **Learning:** Minimal (task is straightforward)
- **Completion:** High confidence

### If Issues Arise
1. **Overthinking:** Remind it's just 3 lines
2. **Confusion:** Point to lines 129-131 and CRITICAL_THRESHOLDS dict
3. **Scope Creep:** Refocus on surgical fix only
4. **Round Limit:** Shouldn't happen, but checkpoint if >40 rounds

---

## ✅ Final Pre-Launch Check

```bash
# Human verifies:
□ MiniMax system running
□ Instructions file exists and is correct
□ Git repo is clean
□ Target file exists (reflex_frame.py)
□ Target lines identified (129-131)
□ No blocking issues

# If all checked:
✅ CLEARED FOR LAUNCH! 🚀
```

---

**Session 8 is GO! Simple task, high confidence, ready to complete P2!** 🎉
