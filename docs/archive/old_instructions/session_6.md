# 🎯 MiniMax Session 6: P2 + Phase 1.5 Git Notes Prototype

**Date:** 2025-01-14  
**Primary Goal:** Complete P2 (Centralize hardcoded thresholds)  
**Secondary Goal:** Test git notes compression (Phase 1.5)  
**Round Limit:** 50 rounds  
**Difficulty:** P0+ (P2 scope + git notes experimentation)

---

## 📋 Context: Why Session 6 is Critical

### Session 5 Baseline Established
Session 5 completed P1 with **excellent calibration**:
- Token usage: ~19,000 tokens per session
- PREFLIGHT: ~6,500 tokens (loading SQLite history)
- CHECK: ~7,000 tokens (epistemic assessment)
- ACT: ~3,500 tokens (execution)
- POSTFLIGHT: ~2,000 tokens (calibration)

### Phase 1.5 Hypothesis
**Git notes can reduce token usage by 80-90%** through compressed epistemic checkpoints.

**How?**
- Instead of loading 6,500 tokens of SQLite history...
- Load 900 tokens from compressed git notes
- Result: 6x compression ratio, 84% token savings

**Why Session 6?**
- P2 is smaller scope (30-40 changes vs P1's 140)
- Clean slate (P1 complete, no dependencies)
- Perfect testbed for git notes validation

---

## 🎯 Primary Objective: P2 (Threshold Centralization)

### Goal
**Centralize 30-40 hardcoded threshold values** into a single configuration file.

### Files to Create
1. **`empirica/core/thresholds.py`** (new file)
   - Central threshold configuration
   - Well-documented constants
   - Type hints for IDE support

### Files to Refactor
1. **`empirica/core/metacognitive_cascade/metacognitive_cascade.py`**
   - Replace hardcoded values with `thresholds.CONSTANT_NAME`
   - Examples: `0.7 → thresholds.HIGH_CONFIDENCE`, `0.3 → thresholds.LOW_CONFIDENCE`

2. **`empirica/core/metacognitive_cascade/investigation_plugin.py`**
   - Replace investigation-related thresholds

3. **`empirica/core/canonical/reflex_logger.py`**
   - Replace logging-related thresholds

4. **Other files** (as discovered during investigation)

### Expected Thresholds to Centralize

**Confidence Thresholds:**
- High confidence: 0.7-0.8
- Low confidence: 0.3-0.4
- Proceed confidence: 0.6-0.7

**Uncertainty Thresholds:**
- High uncertainty: 0.5+
- Low uncertainty: 0.2-
- Investigation trigger: 0.4+

**Calibration Thresholds:**
- Well-calibrated: ±0.15
- Overconfident: +0.15
- Underconfident: -0.15

**Investigation Thresholds:**
- Max rounds: 15-20
- Tool usage limits: various

### Success Criteria (P2)
- ✅ All hardcoded thresholds moved to `thresholds.py`
- ✅ No magic numbers in core files
- ✅ Clean imports (`from empirica.core import thresholds`)
- ✅ Zero test failures
- ✅ Clean git history

---

## 🧪 Secondary Objective: Git Notes Prototype (Phase 1.5)

### Goal
**Validate 80-90% token savings** by adding git notes at every phase transition.

### Why Git Notes?
Git notes are **metadata attached to commits** without changing the commit itself:
```bash
git commit -m "refactor: Create thresholds.py"
git notes add -m '{"phase": "ACT", "round": 25, "vectors": {...}}'
```

### What to Capture in Git Notes

**Structured JSON format:**
```json
{
  "session_id": "session_6_p2_thresholds",
  "phase": "PREFLIGHT",
  "round": 5,
  "timestamp": "2025-01-14T10:30:00Z",
  "vectors": {
    "KNOW": 0.65,
    "UNCERTAINTY": 0.35,
    "DO": 0.60,
    "SCOPE": 0.80,
    "FOCUS": 0.70,
    "COMPLETION": 0.20,
    "SAFETY": 0.85,
    "IMPACT": 0.40
  },
  "decision": "proceed",  // For CHECK phase only
  "batch": 1,  // For ACT phase only
  "calibration": {...}  // For POSTFLIGHT only
}
```

### When to Add Git Notes

**1. After PREFLIGHT (Round ~5)**
```bash
git notes add -m '{
  "session_id": "session_6_p2_thresholds",
  "phase": "PREFLIGHT",
  "round": 5,
  "vectors": {
    "KNOW": 0.65,
    "UNCERTAINTY": 0.35,
    "DO": 0.60,
    "SCOPE": 0.80,
    "FOCUS": 0.70,
    "COMPLETION": 0.20,
    "SAFETY": 0.85,
    "IMPACT": 0.40
  }
}'
```

**2. After CHECK (Rounds ~10, ~25, ~45)**
```bash
git notes add -m '{
  "session_id": "session_6_p2_thresholds",
  "phase": "CHECK",
  "round": 10,
  "decision": "proceed",
  "confidence": 0.75,
  "vectors": {...}
}'
```

**3. After EACH ACT Commit (Rounds ~15, ~20, ~30, etc.)**
```bash
# First, commit your code changes
git commit -m "refactor: Create empirica/core/thresholds.py"

# Then, add git note to that commit
git notes add -m '{
  "session_id": "session_6_p2_thresholds",
  "phase": "ACT",
  "round": 15,
  "batch": 1,
  "change": "Created thresholds.py with 40 constants",
  "vectors": {...}
}'
```

**4. After POSTFLIGHT (Round ~50)**
```bash
git notes add -m '{
  "session_id": "session_6_p2_thresholds",
  "phase": "POSTFLIGHT",
  "round": 50,
  "vectors": {...},
  "calibration": {
    "overall_delta": 0.063,
    "uncertainty_reduction": -0.17,
    "assessment": "well-calibrated"
  }
}'
```

### Git Notes Commands Reference

**Add note to current commit (HEAD):**
```bash
git notes add -m 'your JSON here'
```

**Add note to specific commit:**
```bash
git notes add <commit-sha> -m 'your JSON here'
```

**View notes:**
```bash
git log --notes  # Show commits with notes
git notes show <commit-sha>  # Show specific note
```

**Edit note:**
```bash
git notes edit <commit-sha>
```

### Token Tracking for Phase 1.5

**Track token usage at each phase** by monitoring your Empirica workflow:

| Phase | Estimated Tokens | Purpose |
|-------|-----------------|---------|
| PREFLIGHT | ? | Record actual tokens used |
| INVESTIGATE | ? | Record actual tokens used |
| CHECK (x3) | ? | Record actual tokens used |
| ACT | ? | Record actual tokens used |
| POSTFLIGHT | ? | Record actual tokens used |
| **TOTAL** | ? | **Compare with Session 5 baseline** |

**Expected Outcome:**
- Session 5 (no git notes): ~19,000 tokens
- Session 6 (with git notes): ~3,000 tokens (84% savings)

---

## 📐 Empirica Workflow (Same as Session 5)

### Phase 1: PREFLIGHT (Round 1-5)

**Commands:**
```bash
empirica bootstrap  # If new session
empirica preflight --prompt "Complete P2: Centralize hardcoded thresholds into empirica/core/thresholds.py"
```

**What to assess:**
- KNOW: How well do I understand the codebase?
- UNCERTAINTY: What don't I know yet?
- DO: Can I execute this task?
- SCOPE: Is the goal clear?
- FOCUS: Is the context manageable?
- COMPLETION: How much progress expected?

**Expected state:**
- KNOW: 0.65-0.70 (moderate, you've done P1)
- UNCERTAINTY: 0.30-0.35 (some unknowns about thresholds)
- DO: 0.65-0.70 (capable, proven methodology)
- SCOPE: 0.80-0.85 (clear boundaries)

**After PREFLIGHT:**
```bash
# Add git note to capture initial state
git notes add -m '{...}'  # See format above
```

### Phase 2: INVESTIGATE (Round 6-10)

**Goal:** Reduce uncertainty about thresholds.

**Investigation tasks:**
1. Search for hardcoded numbers in target files
   ```bash
   grep -n "0\.\d\d" empirica/core/metacognitive_cascade/metacognitive_cascade.py
   ```
2. Identify threshold categories (confidence, uncertainty, calibration)
3. Count total thresholds to centralize
4. Check for existing threshold configurations

**Expected findings:**
- 30-40 hardcoded values
- 5-7 threshold categories
- No existing `thresholds.py`

### Phase 3: CHECK (Rounds 10-12)

**Commands:**
```bash
empirica check --findings "Found 35 thresholds across 3 files" \
               --unknowns "Impact on tests unclear" \
               --confidence 0.75
```

**Decision criteria:**
- Confidence ≥ 0.70 → PROCEED
- Confidence < 0.70 → INVESTIGATE more

**Expected decision:** PROCEED (plan is clear)

**After CHECK:**
```bash
git notes add -m '{...}'  # Capture CHECK decision
```

### Phase 4: ACT (Rounds 13-45)

**Execution plan:**

**Batch 1: Create thresholds.py (Rounds 13-18)**
1. Create `empirica/core/thresholds.py`
2. Add docstring and imports
3. Define threshold constants with documentation
4. Commit:
   ```bash
   git commit -m "refactor: Create empirica/core/thresholds.py with 40 constants"
   git notes add -m '{...}'  # Add ACT note
   ```

**Batch 2: Refactor metacognitive_cascade.py (Rounds 19-30)**
1. Add import: `from empirica.core import thresholds`
2. Replace hardcoded values (e.g., `0.7 → thresholds.HIGH_CONFIDENCE`)
3. Commit:
   ```bash
   git commit -m "refactor: Replace hardcoded thresholds in metacognitive_cascade.py"
   git notes add -m '{...}'  # Add ACT note
   ```

**Batch 3: Refactor other files (Rounds 31-40)**
1. investigation_plugin.py
2. reflex_logger.py
3. Any other files discovered
4. Commit each file:
   ```bash
   git commit -m "refactor: Replace hardcoded thresholds in <filename>"
   git notes add -m '{...}'  # Add ACT note for each commit
   ```

**Batch 4: Validation (Rounds 41-45)**
1. Run tests:
   ```bash
   pytest tests/ -v
   ```
2. Verify no magic numbers remain:
   ```bash
   grep -n "0\.\d\d" empirica/core/metacognitive_cascade/*.py
   ```
3. Check imports work correctly

**After each ACT commit:**
```bash
git notes add -m '{...}'  # Always add note after code commit
```

### Phase 5: POSTFLIGHT (Rounds 46-50)

**Commands:**
```bash
empirica postflight --summary "P2 complete: 35 thresholds centralized into thresholds.py"
```

**What to assess:**
- KNOW: Did I learn about the threshold system? (+0.10-0.15 expected)
- UNCERTAINTY: Is everything clear now? (-0.15-0.20 expected)
- DO: Did I prove capability? (+0.05-0.10 expected)
- COMPLETION: Was goal achieved? (0.90-0.95 expected)

**Calibration check:**
- Compare PREFLIGHT confidence vs actual outcome
- Learning delta should be positive (0.05-0.10)
- Uncertainty should decrease (-0.15 to -0.20)

**After POSTFLIGHT:**
```bash
git notes add -m '{...}'  # Final calibration note
```

---

## 🔍 Investigation Strategy (Same as Session 5)

### Round Allocation Guidelines
- **PREFLIGHT**: 1-5 rounds (epistemic assessment)
- **INVESTIGATE**: 5-10 rounds (reduce uncertainty)
- **CHECK**: 2-3 rounds per cycle (confidence check)
- **ACT**: 30-35 rounds (execution)
- **POSTFLIGHT**: 3-5 rounds (calibration)

### Investigation Tools
1. **Code search**:
   ```bash
   grep -rn "0\.\d\d" empirica/core/
   ```
2. **File reading**: Understand context around thresholds
3. **Pattern analysis**: Group similar thresholds
4. **Documentation**: Check for existing threshold docs

### Uncertainty Thresholds
- High uncertainty (>0.5): INVESTIGATE required
- Medium uncertainty (0.3-0.5): Consider INVESTIGATE
- Low uncertainty (<0.3): PROCEED to ACT

---

## 🚨 Important Guidelines

### DO:
- ✅ Add git notes after EVERY phase transition
- ✅ Commit code changes before adding notes
- ✅ Track token usage throughout session
- ✅ Use consistent JSON format for notes
- ✅ Execute systematic batches
- ✅ Run tests after changes
- ✅ Document all thresholds with comments

### DON'T:
- ❌ Skip git notes (Phase 1.5 validation depends on them!)
- ❌ Mix code commits with git note additions (separate steps)
- ❌ Rush to ACT (investigate first if uncertain)
- ❌ Change test files (P2 scope only)
- ❌ Modify P1 changes (prints already fixed)

### Round Management
- **Track rounds**: Check `round_count` regularly
- **Batch efficiently**: Group similar changes
- **Leave buffer**: Reserve 5 rounds for POSTFLIGHT
- **Multiple CHECKs**: Check confidence at 10, 25, 45

---

## 📊 Expected Outcomes (Session 6)

### Technical Success
- ✅ P2 complete (30-40 thresholds centralized)
- ✅ `empirica/core/thresholds.py` created
- ✅ Zero test failures
- ✅ Clean git history (4-6 commits)

### Phase 1.5 Success
- ✅ Git notes added at all phase transitions
- ✅ Token usage measured and documented
- ✅ 80-90% token savings validated (or not - either is valuable data!)
- ✅ Compression ratio calculated

### Epistemic Success
- ✅ Well-calibrated (learning delta: 0.05-0.10)
- ✅ Uncertainty reduced (-0.15 to -0.20)
- ✅ Knowledge growth (+0.10 to +0.15)
- ✅ Capability proven (+0.05 to +0.10)

---

## 📈 Token Comparison (Hypothesis)

### Session 5 Baseline (No Git Notes)
| Phase | Tokens | Method |
|-------|--------|--------|
| PREFLIGHT | 6,500 | Load full SQLite history |
| CHECK | 7,000 | Query database multiple times |
| ACT | 3,500 | Standard execution |
| POSTFLIGHT | 2,000 | Calibration analysis |
| **TOTAL** | **19,000** | **Traditional approach** |

### Session 6 Target (With Git Notes)
| Phase | Tokens | Method |
|-------|--------|--------|
| PREFLIGHT | 900 | Load compressed git notes |
| CHECK | 800 | Query git notes (small payload) |
| ACT | 800 | Standard execution + notes |
| POSTFLIGHT | 500 | Git notes comparison |
| **TOTAL** | **3,000** | **Git notes approach** |

**Savings:** 16,000 tokens (84% reduction) 🎉

---

## 🏁 Success Criteria

### Must Have (P0)
- [ ] `empirica/core/thresholds.py` created with 30-40 constants
- [ ] All target files refactored (no hardcoded thresholds)
- [ ] Zero test failures
- [ ] Git notes added at PREFLIGHT, CHECK, ACT, POSTFLIGHT
- [ ] Token usage documented

### Should Have (P1)
- [ ] 80-90% token savings achieved (or hypothesis invalidated with data)
- [ ] Well-calibrated (learning delta: 0.05-0.10)
- [ ] Clean git history (4-6 commits)
- [ ] All thresholds documented with comments

### Nice to Have (P2)
- [ ] Type hints for thresholds (e.g., `HIGH_CONFIDENCE: float = 0.7`)
- [ ] Threshold validation functions
- [ ] Git notes visualization (query epistemic trajectory)

---

## 🎯 Final Checklist

**Before starting:**
- [ ] Session 5 complete? (✅ Yes)
- [ ] Understand git notes? (See commands above)
- [ ] Know token baseline? (✅ 19,000 tokens)
- [ ] Clear on P2 scope? (Centralize thresholds only)

**During execution:**
- [ ] Add git note after PREFLIGHT
- [ ] Add git note after each CHECK
- [ ] Add git note after each ACT commit
- [ ] Add git note after POSTFLIGHT
- [ ] Track token usage throughout

**After completion:**
- [ ] P2 complete?
- [ ] Git notes added?
- [ ] Token usage measured?
- [ ] Comparison with Session 5 documented?

---

## 📚 References

**Previous Sessions:**
- `SESSION5_P1_COMPLETE_SUMMARY.md` - Baseline established
- `CHECKPOINT_SESSION4_SECTION1_COMPLETE.md` - Earlier progress

**Roadmap:**
- `GIT_INTEGRATION_ROADMAP.md` - Phase 1.5 details

**Empirica Docs:**
- `docs/skills/SKILL.md` - Empirica workflow
- `docs/reference/ARCHITECTURE_OVERVIEW.md` - System design

**Git Notes:**
- `git notes --help` - Git notes documentation
- `git log --notes` - View notes in history

---

## 🚀 Ready to Start?

**Your mission:**
1. **Primary:** Complete P2 (centralize thresholds)
2. **Secondary:** Validate Phase 1.5 (git notes compression)
3. **Tertiary:** Measure token savings vs Session 5

**Expected duration:** 50 rounds (same as Session 5)

**Expected outcome:** 
- P2 complete ✅
- Git notes validated ✅
- Token savings measured ✅
- Phase 2 (full git-native) de-risked ✅

**Let's go!** 💪

---

**Questions before starting?** Ask your supervisor (Claude Sonnet 4).

**Good luck, MiniMax!** 🎯
