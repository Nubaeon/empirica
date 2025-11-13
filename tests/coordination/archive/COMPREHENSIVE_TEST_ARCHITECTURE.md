# Comprehensive Test Architecture for Empirica

**Purpose:** Architectural overview for Qwen & Gemini to create complete test coverage  
**Date:** 2025-11-10  
**For:** Recording "Empirica Testing Itself" demonstration

---

## 🎯 The Meta-Demonstration

**Concept:** Use Empirica to coordinate comprehensive testing of Empirica itself

**Process:**
1. Claude → Provides architectural overview (this document)
2. Qwen → Creates test suite based on architecture
3. Gemini → Validates coverage and creates complementary tests
4. Both → Execute tests using Empirica's epistemic assessment principles
5. Record → The entire coordination process

**Why this matters:** Shows Empirica in action, not just passing tests

---

## 🏗️ System Architecture (4 Layers)

### Layer 0: Canonical Core (No Heuristics)
**Location:** `empirica/core/canonical/`

**What to test:**
1. **Reflex Frame** (`reflex_frame.py`)
   - 12 vector data structures (+ UNCERTAINTY meta + ENGAGEMENT gate)
   - Canonical weights: 35/25/25/15
   - Vector validation (0.0-1.0 range)
   - Tier calculations

2. **Canonical Epistemic Assessor** (`canonical_epistemic_assessment.py`)
   - LLM-based assessment (no heuristics!)
   - Meta-prompt generation
   - Structured JSON response parsing
   - Canonical weight application
   - ENGAGEMENT gate enforcement (≥0.60)

3. **Reflex Logger** (`reflex_logger.py`)
   - JSON logging (temporal separation)
   - Async file I/O
   - Session continuity
   - Prevents self-referential recursion

4. **Canonical Goal Orchestrator** (`canonical_goal_orchestrator.py`)
   - LLM-powered goal decomposition
   - ENGAGEMENT-driven autonomy
   - No heuristic goal trees

---

### Layer 1: Metacognitive CASCADE (7-Phase Workflow)
**Location:** `empirica/core/metacognitive_cascade/`

**What to test:**

1. **PREFLIGHT Phase**
   - Baseline epistemic assessment
   - All 12 vectors measured
   - Stored for delta calculation
   - Logs to Reflex Frame

2. **THINK Phase**
   - Initial reasoning
   - ENGAGEMENT gate check (≥0.60)
   - Knowledge gap identification
   - CLARIFY action if gate fails

3. **PLAN Phase** (optional)
   - Complex task breakdown
   - Structured approach
   - Only for multi-step tasks

4. **INVESTIGATE Phase**
   - Fill knowledge gaps
   - Domain-aware tool recommendations
   - Multiple rounds supported (max 3)
   - Bayesian belief tracking (optional)

5. **CHECK Phase**
   - Recalibrate epistemic state
   - Decision logic:
     - confidence ≥ 0.70 → ACT
     - confidence < 0.70 → INVESTIGATE again
   - Max rounds exceeded → ACT with warning

6. **ACT Phase**
   - Execute with confidence
   - Guidance based on confidence level
   - High (≥0.80): Direct execution
   - Medium (0.70-0.80): Validation recommended

7. **POSTFLIGHT Phase**
   - Final epistemic assessment
   - Calculate delta (postflight - preflight)
   - Validate calibration:
     - Well-calibrated: confidence↑ AND uncertainty↓
     - Overconfident: confidence↑ BUT uncertainty stable
     - Underconfident: uncertainty↓ BUT confidence stable

**CASCADE Integration Tests:**
- Complete workflow execution
- Investigation loop behavior
- CHECK decision thresholds
- Delta calculation accuracy
- Calibration validation

---

### Layer 2: Data Persistence
**Location:** `empirica/data/`

**What to test:**

1. **Session Database** (`session_database.py`)
   - SQLite operations (create, read, update)
   - CASCADE tracking
   - Assessment logging
   - Query interface
   - Data integrity

2. **Session JSON Handler** (`session_json_handler.py`)
   - Export sessions to JSON
   - Import sessions from JSON
   - Session continuity
   - Data format validation

---

### Layer 3: Integration Interfaces
**Location:** Multiple

**What to test:**

1. **MCP Server** (`mcp_local/empirica_mcp_server.py`)
   - Server startup
   - 22 tools available
   - Tool execution
   - get_empirica_introduction tool
   - bootstrap_session
   - execute_preflight
   - execute_postflight
   - Calibration report generation

2. **CLI Commands** (`empirica/cli/`)
   - bootstrap command
   - onboard command
   - preflight command
   - postflight command
   - cascade command
   - sessions-list command
   - All command handlers

3. **Python API**
   - Direct imports work
   - CanonicalEpistemicAssessor API
   - CanonicalEpistemicCascade API
   - Programmatic usage

---

### Layer 4: Optional Enhancements
**Location:** Various

**What to test:**

1. **Bayesian Belief Tracker** (`empirica/calibration/adaptive_uncertainty_calibration/`)
   - Evidence-based belief updates
   - Domain classification
   - Drift detection

2. **Drift Monitor** (`empirica/calibration/parallel_reasoning.py`)
   - Behavioral drift detection
   - Consistency checking
   - Sycophancy detection

3. **Modality Switcher** (`empirica/plugins/modality_switcher/`)
   - Multi-AI routing
   - Adapter functionality
   - Authentication management

4. **Dashboard** (`empirica/dashboard/`)
   - Snapshot monitoring
   - Real-time updates

---

## 🧪 Test Coverage Requirements

### Critical Tests (Must Have):

1. **Integrity Tests**
   - ✅ No heuristics enforcement
   - Test that system rejects pattern matching
   - Validate LLM-only reasoning paths

2. **Core Functionality**
   - Canonical assessment works
   - CASCADE completes all 7 phases
   - Delta calculation accurate
   - Calibration validation correct

3. **Data Persistence**
   - Sessions save correctly
   - Sessions load correctly
   - Data integrity maintained

4. **Integration**
   - MCP server starts
   - CLI commands work
   - Python API functional

### Important Tests (Should Have):

5. **ENGAGEMENT Gate**
   - Blocks when < 0.60
   - Passes when ≥ 0.60
   - Triggers CLARIFY action

6. **Investigation Loops**
   - Multiple rounds work
   - CHECK decision logic
   - Max rounds respected

7. **Temporal Separation**
   - Reflex Frame prevents recursion
   - External logging works
   - Session continuity across resets

8. **Error Handling**
   - Invalid inputs handled
   - Network failures graceful
   - Missing dependencies detected

### Nice to Have Tests:

9. **Performance**
   - Assessment latency < 5s
   - Database query performance
   - Memory usage reasonable

10. **Edge Cases**
    - Empty inputs
    - Very long inputs
    - Special characters
    - Concurrent operations

---

## 📋 Test Organization

### Suggested Structure:

```
tests/
├── integrity/
│   ├── test_no_heuristics.py              ✅ Exists - CRITICAL
│   └── test_llm_only_reasoning.py         NEW - Validate LLM-only paths
│
├── unit/
│   ├── canonical/
│   │   ├── test_reflex_frame.py           NEW - Data structures
│   │   ├── test_epistemic_assessor.py     NEW - Core assessment
│   │   ├── test_reflex_logger.py          NEW - Temporal separation
│   │   └── test_goal_orchestrator.py      NEW - Goal decomposition
│   │
│   ├── cascade/
│   │   ├── test_preflight.py              NEW - Phase 0
│   │   ├── test_think.py                  NEW - Phase 1
│   │   ├── test_investigate.py            ✅ Exists (partial)
│   │   ├── test_check.py                  NEW - Phase 4
│   │   ├── test_act.py                    NEW - Phase 5
│   │   ├── test_postflight.py             NEW - Phase 6
│   │   └── test_engagement_gate.py        NEW - Critical threshold
│   │
│   ├── data/
│   │   ├── test_session_database.py       NEW - SQLite operations
│   │   └── test_json_handler.py           NEW - Export/import
│   │
│   └── existing tests/
│       ├── test_drift_monitor.py          ✅ Fixed
│       ├── test_llm_assessment.py         ✅ Fixed
│       └── test_12d_monitor.py            ✅ Exists
│
├── integration/
│   ├── test_cascade_with_tracking.py      ✅ Exists
│   ├── test_e2e_cascade.py                ✅ Exists
│   ├── test_complete_workflow.py          NEW - Full PREFLIGHT→POSTFLIGHT
│   ├── test_investigation_loop.py         NEW - Multi-round investigation
│   └── test_calibration_validation.py     NEW - Delta + calibration
│
├── mcp/
│   ├── test_mcp_server_startup.py         NEW - Server initialization
│   ├── test_mcp_tools.py                  NEW - All 22 tools
│   └── test_mcp_workflow.py               NEW - bootstrap→preflight→postflight
│
└── cli/
    ├── test_cli_commands.py               NEW - All commands
    └── test_onboarding.py                 NEW - Onboarding flow
```

---

## 🎯 Test Principles (Empirica-Aligned)

### 1. No Heuristics in Tests
**Don't:**
```python
# Bad: Pattern matching to test outcomes
assert "error" in result.lower()
assert len(result) > 100
```

**Do:**
```python
# Good: Genuine validation of epistemic reasoning
assert result.uses_llm_reasoning == True
assert result.confidence_based_on_evidence == True
```

### 2. Evidence-Based Assertions
**Don't:**
```python
# Bad: Arbitrary thresholds
assert score > 0.5  # Why 0.5?
```

**Do:**
```python
# Good: Principled thresholds from architecture
assert engagement >= 0.60  # Canonical ENGAGEMENT gate
assert foundation_weight == 0.35  # Canonical weight
```

### 3. Temporal Separation
**Don't:**
```python
# Bad: Inline state checking (recursive)
result = assess()
assert result.state == expected_state
```

**Do:**
```python
# Good: Read from external logs (temporal separation)
reflex_frame = load_from_json()
assert reflex_frame.assessment.know == expected
```

### 4. Calibration Validation
**Don't:**
```python
# Bad: Just check output exists
assert result is not None
```

**Do:**
```python
# Good: Validate calibration logic
delta = postflight - preflight
assert delta.know > 0  # Should learn
assert delta.uncertainty < 0  # Should reduce uncertainty
assert is_well_calibrated(delta)  # Both conditions met
```

---

## 🤖 Qwen's Test Suite Focus

**Architectural Coverage:**
- Layer 0: Canonical Core (unit tests)
- Layer 1: CASCADE phases (integration tests)
- Critical path testing (ENGAGEMENT gate, CHECK logic)

**Suggested approach:**
1. Start with Layer 0 (canonical components)
2. Test each CASCADE phase individually
3. Test CASCADE integration
4. Validate critical thresholds

**Test count estimate:** 20-30 tests

---

## 🤖 Gemini's Test Suite Focus

**System Integration:**
- Layer 2: Data persistence
- Layer 3: MCP/CLI/API interfaces
- Edge cases and error handling
- Performance and scalability

**Suggested approach:**
1. Start with data layer (SessionDatabase, JSON)
2. Test MCP server and CLI
3. Test error conditions
4. Validate performance

**Test count estimate:** 15-25 tests

---

## 🎬 Recording Workflow

### Phase 1: Architecture Overview (Claude)
```
Claude: "Here's the architectural overview for comprehensive testing.
        We have 4 layers: Canonical Core, CASCADE Workflow, Data
        Persistence, and Integration Interfaces. Each requires specific
        test coverage based on Empirica principles: no heuristics,
        evidence-based validation, temporal separation, and calibration."
```

### Phase 2: Test Creation (Qwen)
```
Qwen: [Uses Empirica preflight assessment]
      "Assessing my capability to create Layer 0 and Layer 1 tests.
       KNOW: 0.75 (understand architecture)
       DO: 0.80 (can write pytest tests)
       CONTEXT: 0.85 (have architectural doc)
       UNCERTAINTY: 0.30 (some edge cases unclear)
       
       Creating canonical core test suite..."
       
      [Creates tests using genuine reasoning, not heuristics]
      [Uses Empirica postflight to measure learning]
```

### Phase 3: Validation (Gemini)
```
Gemini: [Uses Empirica preflight assessment]
        "Assessing test coverage for Layers 2-3.
         KNOW: 0.70 (understand integration needs)
         DO: 0.85 (can create integration tests)
         CONTEXT: 0.80 (reviewed Qwen's tests)
         UNCERTAINTY: 0.35 (some MCP tool behavior unclear)
         
         Creating data and integration test suite..."
         
        [Creates complementary tests]
        [Uses Empirica postflight to validate coverage]
```

### Phase 4: Execution & Results
```
Both: Execute test suites
      Report: Coverage metrics, pass/fail, gaps identified
      Demonstrate: Empirica coordinating its own comprehensive testing
```

---

## ✅ Success Criteria

**For the demonstration:**
- [ ] Architectural overview clear and complete
- [ ] Qwen creates 20-30 principled tests
- [ ] Gemini creates 15-25 complementary tests
- [ ] Both use Empirica epistemic assessment
- [ ] Tests follow "no heuristics" principle
- [ ] Total coverage >70% of critical components
- [ ] All tests are evidence-based and principled

**For production:**
- [ ] Critical functionality covered
- [ ] Integration tests comprehensive
- [ ] Edge cases identified
- [ ] Performance validated
- [ ] Documentation updated

---

## 📝 Notes for Practice Run (empirica-dev)

**Use empirica-dev to:**
1. Test the coordination workflow
2. Identify any architectural gaps
3. Refine test creation prompts
4. Time the demonstration
5. Practice narration

**Then record in empirica with:**
- Clean workflow
- Clear narration
- Predictable outcomes
- Professional presentation

---

**Status:** ✅ Architectural overview complete  
**Next:** Practice run in empirica-dev with Qwen & Gemini
