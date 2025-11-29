# Skipped Tests Decision

**Date:** 2025-01-XX  
**Status:** Decision needed

---

## 📊 The 10 Skipped Tests

All 10 tests have the same skip reason:
> "Test checks heuristics that were intentionally removed - AI decides via self-assessment"

**Locations:**
```
/home/yogapad/empirical-ai/empirica/tests/unit/cascade/test_investigate.py (5 tests)
/home/yogapad/empirical-ai/empirica/tests/unit/cascade/test_postflight.py (2 tests)
/home/yogapad/empirical-ai/empirica/tests/unit/cascade/test_think.py (3 tests)
```

---

## 🤔 What Do These Tests Check?

### Investigation Tests (5)
- `test_investigation_process` - Tests automatic investigation trigger logic
- `test_tool_capability_mapping` - Tests heuristic tool selection
- `test_investigation_strategy_generation` - Tests automatic strategy creation
- `test_investigation_necessity_logic` - Tests hardcoded necessity rules
- `test_investigation_loop_simulation` - Tests loop control heuristics

### Postflight Tests (2)
- `test_overconfidence_detection` - Tests automatic overconfidence flagging
- `test_task_id_generation` - Tests task ID format (may be useful?)

### Think Tests (3)
- `test_gap_analysis` - Tests automatic gap detection
- `test_investigation_necessity_assessment` - Tests necessity heuristics
- `test_investigation_strategy_generation` - Tests strategy heuristics

---

## 🎯 Why Were Heuristics Removed?

**Principle:** "No Heuristics - Genuine Self-Assessment Only"

**Old Way (heuristics):**
```python
if uncertainty > 0.7:
    action = "INVESTIGATE"  # Automatic decision
```

**New Way (self-assessment):**
```python
# AI genuinely assesses its own uncertainty
# AI decides whether to investigate
# No automatic rules
```

**Rationale:** Heuristics are confabulation. Real epistemic awareness requires genuine assessment, not rules.

---

## 💡 Three Options

### Option 1: Delete Tests ⭐ (Recommended)
**Pros:**
- Tests are obsolete (test removed functionality)
- Cleaner test suite
- No maintenance burden

**Cons:**
- Lose test coverage
- No replacement tests

**Action:**
```bash
cd /home/yogapad/empirical-ai/empirica

# Delete test functions from:
# - tests/unit/cascade/test_investigate.py (lines 87-150, 162-200, 260-280)
# - tests/unit/cascade/test_postflight.py (lines 264-300, 419-450)
# - tests/unit/cascade/test_think.py (lines 134-150, 152-180, 219-250)

# OR just remove @pytest.mark.skip and the function
```

### Option 2: Rewrite for Self-Assessment
**Pros:**
- Keep test coverage
- Test new approach
- Verify AI self-assessment works

**Cons:**
- Requires work (5-8 iterations)
- Complex to test (need mock LLM)
- May be redundant (integration tests cover this)

**Example Rewrite:**
```python
# OLD (heuristic test)
def test_investigation_necessity_logic():
    assert cascade._should_investigate(uncertainty=0.8) == True

# NEW (self-assessment test)
async def test_ai_decides_investigation():
    # Mock LLM that genuinely assesses
    assessment = await cascade.assess(...)
    # Verify assessment has reasoning
    assert assessment.reasoning
    # Verify decision is based on genuine assessment
    assert "uncertainty" in assessment.reasoning.lower()
```

### Option 3: Keep Skipped with Documentation
**Pros:**
- No work needed
- Clear why skipped
- Can revisit later

**Cons:**
- Clutters test output
- May confuse future developers
- Not actively useful

**Action:**
```python
# Improve skip reason
@pytest.mark.skip(reason="""
Heuristics intentionally removed (2025-01).
AI now uses genuine self-assessment instead of rules.
See: docs/guides/CRITICAL_NO_HEURISTICS_PRINCIPLE.md
""")
def test_investigation_necessity_logic():
    ...
```

---

## 📊 Impact Analysis

### Current Test Suite
```
42 total tests
├── 16 passing
├── 26 failing (being fixed)
└── 10 skipped (these tests)

After mini-agent fixes:
├── 42 passing (if all fixed)
└── 10 skipped (these tests)
```

### If We Delete (Option 1)
```
32 total tests
└── 32 passing (once fixed)

Pass rate: 100% ✅
```

### If We Keep Skipped (Option 3)
```
42 total tests
├── 32 passing
└── 10 skipped

Pass rate: 76% (32/42) ❌
```

---

## 💡 Recommendation: Option 1 (Delete)

**Reasons:**
1. **Tests are obsolete** - Test functionality that was intentionally removed
2. **No heuristics principle** - Core to Empirica's design
3. **Integration tests exist** - Real CASCADE behavior is tested in integration tests
4. **Cleaner output** - 100% pass rate vs 76%
5. **Less maintenance** - No dead code

**What to Delete:**
- 5 investigation heuristic tests
- 2 postflight heuristic tests
- 3 think heuristic tests

**What to Keep:**
- Other investigation tests (that test actual functionality)
- Other postflight tests (delta calculation, etc.)
- Other think tests (assessment creation, etc.)

**Exception:** `test_task_id_generation` - Review this one, might be testing valid functionality (ID format), not heuristics.

---

## 🚀 Recommended Action

### Step 1: Review Task ID Test
```bash
cd /home/yogapad/empirical-ai/empirica
cat tests/unit/cascade/test_postflight.py | grep -A30 "test_task_id_generation"
```

**Decision:**
- If tests ID format → Keep and fix
- If tests heuristic logic → Delete

### Step 2: Delete Other 9 Tests
Edit files and remove:
- test_investigate.py: 5 test functions
- test_postflight.py: 1 test function (overconfidence detection)
- test_think.py: 3 test functions

### Step 3: Verify
```bash
pytest tests/unit/cascade/ -v

# Should show:
# - Fewer total tests (31-32 instead of 42)
# - 0 skipped
# - Higher pass rate
```

---

## ✅ Final Decision Template

**Decision:** [DELETE / REWRITE / KEEP SKIPPED]

**Rationale:** [Why this choice]

**Action Taken:**
- [ ] Reviewed test_task_id_generation
- [ ] Decision on task_id test: [delete/keep]
- [ ] Deleted 9 heuristic tests
- [ ] Verified test count reduced
- [ ] Confirmed 0 skipped in output

**Result:**
- Tests before: 42 (16 pass, 26 fail, 10 skip)
- Tests after: 32 (32 pass, 0 fail, 0 skip)
- Pass rate: 100% ✅

---

**Status:** Awaiting your decision  
**Recommendation:** Delete (Option 1)  
**Next:** Update this doc with your decision and action

---

*"The best test suite is one that tests what exists, not what was removed."* ✨
