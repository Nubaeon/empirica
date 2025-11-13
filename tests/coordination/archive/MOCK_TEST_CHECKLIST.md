# Mock Test Run Checklist - Before Recording

**Purpose:** Dry run to identify issues before recording demonstration  
**Date:** 2025-11-10  
**Status:** Ready to execute

---

## 🎯 Mock Test Goals

1. **Verify all commands work** - No surprises during recording
2. **Check output clarity** - Results are readable and meaningful
3. **Test timing** - Estimate how long each phase takes
4. **Identify friction points** - Fix before recording
5. **Practice narration** - Know what to explain

---

## ✅ Pre-Test Checklist

### Environment Setup
- [ ] Virtual environment activated: `.venv-empirica`
- [ ] pytest-cov installed and working
- [ ] empirica command available
- [ ] Working directory: `/home/yogapad/empirical-ai/empirica`

### Test Commands Ready
```bash
# Quick verification
pytest tests/unit/test_drift_monitor.py -v
pytest tests/integration/test_e2e_cascade.py -v
pytest tests/integrity/test_no_heuristics.py -v

# Full suite
pytest tests/ -v

# With coverage
pytest tests/ --cov=empirica -v
```

### Optional: Qwen/Gemini Credentials
- [ ] Check if `.empirica/credentials.yaml` exists
- [ ] Check if QWEN_API_KEY configured
- [ ] Check if GEMINI_API_KEY configured
- [ ] (Skip automated coordinator if not configured)

---

## 🧪 Mock Test Phases

### Phase 1: Quick Validation (5 minutes)

**Test individual fixed files:**
```bash
echo "=== Testing Import Fixes ==="
pytest tests/unit/test_drift_monitor.py -v
pytest tests/unit/test_llm_assessment.py -v
pytest tests/unit/test_integrated_workflow.py -v
```

**Expected:**
- ✅ All 3 tests should PASS
- ✅ No import errors
- ✅ Quick execution (<10 seconds each)

**Record:**
- Actual result: ___________
- Time taken: ___________
- Issues: ___________

---

### Phase 2: Test Suites (10 minutes)

**Test each suite:**
```bash
echo "=== Integrity Tests (Critical!) ==="
pytest tests/integrity/ -v

echo "=== Unit Tests ==="
pytest tests/unit/ -v

echo "=== Integration Tests ==="
pytest tests/integration/ -v

echo "=== Modality Tests ==="
pytest tests/modality/ -v
```

**Expected:**
- ✅ Integrity tests pass (no heuristics validation)
- ⚠️ Some unit/integration tests may fail (dependencies, etc.)
- Record which ones fail for fixing

**Record:**
- Integrity: PASS/FAIL ___________
- Unit: X passed, Y failed ___________
- Integration: X passed, Y failed ___________
- Issues to fix: ___________

---

### Phase 3: Full Test Suite (5 minutes)

**Run everything:**
```bash
echo "=== Full Test Suite ==="
pytest tests/ -v
```

**Expected:**
- See overall pass/fail count
- Identify patterns in failures
- Note execution time

**Record:**
- Total tests: ___________
- Passed: ___________
- Failed: ___________
- Skipped: ___________
- Time: ___________

---

### Phase 4: Coverage Report (5 minutes)

**Generate coverage:**
```bash
echo "=== Coverage Report ==="
pytest tests/ --cov=empirica --cov-report=term --cov-report=html -v
```

**Expected:**
- Coverage report generates
- htmlcov/ directory created
- Can identify coverage gaps

**Record:**
- Overall coverage: ___________%
- Key modules covered: ___________
- Gaps identified: ___________

---

### Phase 5: Onboarding Test (Optional - 10 minutes)

**Test onboarding flow:**
```bash
echo "=== Onboarding Test ==="
empirica onboard --ai-id mock-test
```

**Expected:**
- Completes 6 phases
- References docs/skills/SKILL.md (fixed!)
- Learning delta measured

**Record:**
- Completed: YES/NO ___________
- References correct: YES/NO ___________
- Time: ___________
- Issues: ___________

---

### Phase 6: MCP Server Test (Optional - 5 minutes)

**Test MCP server startup:**
```bash
echo "=== MCP Server Test ==="
source .venv-mcp/bin/activate
python3 mcp_local/empirica_mcp_server.py &
MCP_PID=$!
sleep 3

# Check if running
ps -p $MCP_PID

# Kill after test
kill $MCP_PID
```

**Expected:**
- Server starts without errors
- Process runs (doesn't crash immediately)
- 22 tools registered (check logs)

**Record:**
- Started: YES/NO ___________
- Errors: ___________
- Tool count: ___________

---

## 📊 Mock Test Results Summary

### Overall Status:
- [ ] All critical tests pass
- [ ] Import fixes work
- [ ] No blocking issues found
- [ ] Ready for recording

### Issues Found:
1. ___________________________________________
2. ___________________________________________
3. ___________________________________________

### Fixes Needed Before Recording:
1. ___________________________________________
2. ___________________________________________
3. ___________________________________________

### Estimated Recording Time:
- Quick validation: ~5 minutes
- Test suites: ~10 minutes
- Full suite + coverage: ~10 minutes
- Total: ~25 minutes

---

## 🎬 Recording Preparation

### Based on mock test results:

**What to show in recording:**
- [ ] Import fixes verification (3 tests)
- [ ] Integrity test (no heuristics - critical!)
- [ ] Full test suite run
- [ ] Coverage report generation
- [ ] Onboarding flow (if time permits)

**What to narrate:**
- Documentation fixes completed
- Import paths corrected
- pytest-cov installed
- Testing infrastructure ready
- Production readiness validated

**What to skip:**
- Tests that consistently fail (known issues)
- Very long-running tests
- Tests requiring external dependencies

---

## 🚀 Ready for Recording Checklist

After mock test completion:

- [ ] All critical tests pass
- [ ] Know which tests to show
- [ ] Know which tests to skip
- [ ] Timing is reasonable (~25 min total)
- [ ] Narration prepared
- [ ] Environment clean (no stray files)
- [ ] Terminal font/colors readable
- [ ] Ready to start tmux/asciinema

---

## 📝 Notes from Mock Test

**What worked well:**
- ___________________________________________
- ___________________________________________

**What needs adjustment:**
- ___________________________________________
- ___________________________________________

**Surprises/unexpected:**
- ___________________________________________
- ___________________________________________

**For recording:**
- ___________________________________________
- ___________________________________________

---

**Status:** Ready for mock test execution  
**Next:** Run through all phases, fill in results, then decide on recording approach
