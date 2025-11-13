# Live Coordination Session - Qwen & Gemini Test Creation

**Date:** 2025-11-10  
**Coordinator:** Claude (Rovo Dev)  
**Testers:** Qwen (Pane 0), Gemini (Pane 1)  
**Goal:** Create comprehensive test suite for Empirica

---

## 🎯 Session Plan

### Phase 1: Briefing (5 minutes)
**Coordinator provides:**
- Architectural overview
- Test assignments
- Empirica principles

### Phase 2: Qwen Test Creation (20 minutes)
**Focus:** Layer 0 (Canonical Core) + Layer 1 (CASCADE)
**Output:** 20-30 unit/integration tests

### Phase 3: Gemini Test Creation (20 minutes)
**Focus:** Layer 2 (Data) + Layer 3 (Integration)
**Output:** 15-25 integration/system tests

### Phase 4: Review & Execution (10 minutes)
**Both:** Run tests, report results

---

## 📝 Qwen's Assignment

**Read:** `tests/coordination/COMPREHENSIVE_TEST_ARCHITECTURE.md`

**Create tests for:**

### Layer 0: Canonical Core
```
tests/unit/canonical/
├── test_reflex_frame.py           # NEW
├── test_epistemic_assessor.py     # NEW
├── test_reflex_logger.py          # NEW
└── test_goal_orchestrator.py      # NEW
```

**What to test:**
- Reflex Frame: 12 vectors, weights (35/25/25/15), validation
- Epistemic Assessor: LLM reasoning, no heuristics, ENGAGEMENT gate
- Reflex Logger: Temporal separation, JSON logging
- Goal Orchestrator: LLM-based decomposition

### Layer 1: CASCADE Workflow
```
tests/unit/cascade/
├── test_preflight.py              # NEW
├── test_think.py                  # NEW
├── test_investigate.py            # ENHANCE existing
├── test_check.py                  # NEW
├── test_postflight.py             # NEW
└── test_engagement_gate.py        # NEW
```

**What to test:**
- Each phase works independently
- ENGAGEMENT gate blocks when < 0.60
- CHECK decision logic (0.70 threshold)
- Investigation loops (max 3 rounds)
- Delta calculation
- Calibration validation

**Key principle:** Use Empirica's epistemic assessment while creating tests!

---

## 📝 Gemini's Assignment

**Read:** `tests/coordination/COMPREHENSIVE_TEST_ARCHITECTURE.md`

**Create tests for:**

### Layer 2: Data Persistence
```
tests/unit/data/
├── test_session_database.py       # NEW
└── test_json_handler.py           # NEW
```

**What to test:**
- SessionDatabase: CRUD operations, data integrity
- JSON Handler: Export/import, session continuity

### Layer 3: Integration
```
tests/integration/
├── test_complete_workflow.py      # NEW
├── test_investigation_loop.py     # NEW
├── test_calibration_validation.py # NEW
└── test_mcp_integration.py        # NEW
```

```
tests/mcp/
├── test_mcp_server_startup.py     # NEW
├── test_mcp_tools.py              # NEW
└── test_mcp_workflow.py           # NEW
```

**What to test:**
- Complete PREFLIGHT→POSTFLIGHT workflow
- Investigation loop behavior
- MCP server startup and tools
- CLI command execution
- Error handling

**Key principle:** Validate Qwen's test coverage and fill gaps!

---

## 🎯 Test Principles (Both)

### 1. No Heuristics
```python
# BAD - Pattern matching
assert "error" in str(result)

# GOOD - Evidence-based
assert result.uses_genuine_reasoning == True
```

### 2. Evidence-Based
```python
# BAD - Arbitrary
assert score > 0.5

# GOOD - Principled
assert engagement >= 0.60  # Canonical gate threshold
```

### 3. Temporal Separation
```python
# GOOD - External state
reflex_frame = ReflexLogger.load()
assert reflex_frame.assessment.know == expected
```

### 4. Calibration
```python
# GOOD - Validate delta
delta = postflight - preflight
assert delta.know > 0  # Learning occurred
assert delta.uncertainty < 0  # Uncertainty reduced
```

---

## 📊 Success Criteria

**For Qwen:**
- [ ] 20-30 tests created
- [ ] Layer 0 covered (canonical core)
- [ ] Layer 1 covered (CASCADE phases)
- [ ] All tests follow principles
- [ ] Tests use pytest conventions

**For Gemini:**
- [ ] 15-25 tests created
- [ ] Layer 2 covered (data persistence)
- [ ] Layer 3 covered (integration)
- [ ] Validates Qwen's coverage
- [ ] Fills any gaps

**Overall:**
- [ ] >70% coverage of critical components
- [ ] All tests evidence-based
- [ ] No heuristic patterns in tests
- [ ] Professional test organization

---

## 🔄 Coordination Protocol

### Qwen Reports:
```
Status: Creating test for [component]
Progress: X of Y tests complete
Issues: [Any blockers]
```

### Gemini Reports:
```
Status: Reviewing Qwen's [component], creating [test]
Progress: X of Y tests complete
Coverage gaps: [What's missing]
```

### Coordinator (Claude):
```
Guidance: [Architecture clarification]
Decisions: [Test priority adjustments]
Review: [Test quality feedback]
```

---

## 🚀 Starting Commands

### Qwen (Pane 0):
```bash
cd /home/yogapad/empirical-ai/empirica
source .venv-empirica/bin/activate

# Read architecture
cat tests/coordination/COMPREHENSIVE_TEST_ARCHITECTURE.md

# Start creating tests in tests/unit/canonical/
mkdir -p tests/unit/canonical
mkdir -p tests/unit/cascade

# Create first test
# Example: tests/unit/canonical/test_reflex_frame.py
```

### Gemini (Pane 1):
```bash
cd /home/yogapad/empirical-ai/empirica
source .venv-empirica/bin/activate

# Read architecture
cat tests/coordination/COMPREHENSIVE_TEST_ARCHITECTURE.md

# Wait for Qwen to create some tests, then:
mkdir -p tests/unit/data
mkdir -p tests/mcp

# Review Qwen's work, create complementary tests
```

---

## 📝 Session Log

**Start time:** _____________

**Qwen progress:**
- [ ] test_reflex_frame.py
- [ ] test_epistemic_assessor.py
- [ ] test_reflex_logger.py
- [ ] test_goal_orchestrator.py
- [ ] test_preflight.py
- [ ] test_think.py
- [ ] test_check.py
- [ ] test_postflight.py
- [ ] test_engagement_gate.py

**Gemini progress:**
- [ ] test_session_database.py
- [ ] test_json_handler.py
- [ ] test_complete_workflow.py
- [ ] test_investigation_loop.py
- [ ] test_mcp_server_startup.py
- [ ] test_mcp_tools.py
- [ ] test_mcp_workflow.py

**Issues encountered:** _____________

**End time:** _____________

---

**Status:** Ready to begin coordination
