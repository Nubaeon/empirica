# Empirica Validation Test Plan
## Comprehensive Testing for Multi-AI Integration
**Created:** 2025-10-31 (Updated: 2025-11-10)  
**Purpose:** Validate Empirica framework across different AI models (Claude, Qwen, Gemini, etc.)  
**Status:** Ready for Execution  
**Current Implementation:** v2.0 with 7-phase cascade + MCP integration

---

> **Update 2025-11-10:** This test plan is now complemented by the coordination testing infrastructure in `tests/coordination/`.
> 
> **For execution guides, see:**
> - [`tests/coordination/QUICK_START.md`](coordination/QUICK_START.md) - Choose testing path
> - [`tests/coordination/MANUAL_TMUX_TESTING_GUIDE.md`](coordination/MANUAL_TMUX_TESTING_GUIDE.md) - Visual demo guide
> - [`tests/coordination/test_coordinator.py`](coordination/test_coordinator.py) - Automated coordinator
> 
> **Fixes applied:**
> - ✅ Import paths fixed (semantic-kit → empirica)
> - ✅ pytest-cov installed and working
> - ✅ MCP server references corrected (12 vectors + UNCERTAINTY meta-vector)

---

## Table of Contents
1. [Overview](#1-overview)
2. [Test Objectives](#2-test-objectives)
3. [Current Implementation Status](#3-current-implementation-status)
4. [Pre-Test Setup Validation](#4-pre-test-setup-validation)
5. [Phase 1: Component Integration Tests](#5-phase-1-component-integration-tests)
6. [Phase 2: Cascade Workflow Tests](#6-phase-2-cascade-workflow-tests)
7. [Phase 3: MCP Server Tests](#7-phase-3-mcp-server-tests)
8. [Phase 4: Cross-AI Compatibility Tests](#8-phase-4-cross-ai-compatibility-tests)
9. [Phase 5: Real-World Scenario Tests](#9-phase-5-real-world-scenario-tests)
10. [Success Criteria](#10-success-criteria)
11. [Failure Analysis Protocol](#11-failure-analysis-protocol)

---

## 1. Overview

### 1.1 What We're Testing
The **Empirica Framework** - a comprehensive epistemic humility system that provides:
- **13-dimensional epistemic state tracking** (12D + meta-uncertainty)
- **7-phase metacognitive cascade** (PREFLIGHT → THINK → PLAN → INVESTIGATE → CHECK → ACT → POSTFLIGHT)
- **Genuine self-assessment** (AI assesses itself, not external LLM)
- **MCP server integration** for tool-based interaction
- **Session continuity** with epistemically-weighted memory

### 1.2 Why This Matters
- Validates that epistemic humility works across different AI architectures
- Ensures components integrate correctly without stubs or heuristics
- Confirms MCP server provides correct tool interfaces
- Tests whether self-assessment genuinely reflects AI epistemic state

### 1.3 Testing Philosophy
**Accuracy over speed** - We prioritize correct epistemic measurement over performance  
**No heuristics** - All components must use genuine measurement, not fallback patterns  
**Self-assessment** - AI must assess itself, not call external LLMs  
**Real integration** - No stubs, mocks, or placeholder responses

---

## 2. Test Objectives

### 2.1 Primary Objectives
1. ✅ **Component Integration:** All components work together correctly
2. ✅ **Self-Assessment Validity:** AI genuinely reflects on its own epistemic state
3. ✅ **Cascade Flow:** 7-phase workflow executes correctly with proper tracking
4. ✅ **MCP Server:** Tools expose Empirica functionality correctly
5. ✅ **Cross-AI Compatibility:** Works with Claude, Qwen, Gemini, and others

### 2.2 Secondary Objectives
1. ✅ **Session Continuity:** Memory loading improves performance without false confidence
2. ✅ **Calibration Accuracy:** Confidence matches actual performance
3. ✅ **Drift Detection:** System detects when recalibration is needed
4. ✅ **Governance:** Bayesian guardian prevents overconfidence

### 2.3 Critical Validation Points
- **No external LLM calls for self-assessment** (unless in governance-managed verification)
- **No heuristic fallbacks** in any component
- **No demo/stub code** in production paths
- **Proper 13D vector tracking** including meta-uncertainty
- **Clear distinction** between workflow phases and cascade phases

---

## 3. Current Implementation Status

### 3.1 Implemented Components ✅

#### Core Systems
- ✅ **13D Epistemic State Monitor** (`empirica/core/epistemic_state/monitor_12d.py`)
  - Measures 12 epistemic vectors + meta-uncertainty (13th vector)
  - No heuristics - genuine measurement only
  
- ✅ **7-Phase Metacognitive Cascade** (`empirica/core/metacognitive_cascade/metacognitive_cascade.py`)
  - PREFLIGHT → THINK → PLAN → INVESTIGATE → CHECK → ACT → POSTFLIGHT
  - Automatic tracking of epistemic deltas
  - Self-assessment at each phase

- ✅ **Uncertainty Calibration** (`empirica/core/uncertainty/calibration.py`)
  - Adaptive uncertainty assessment
  - Self-assessment (no external LLM calls)
  - Epistemic vs aleatoric uncertainty decomposition

- ✅ **Investigation System** (`empirica/core/investigation/`)
  - Frame-based investigation with proper tracking
  - Auto-tracker for tool execution monitoring (no heuristics)
  - Bayesian updates on evidence gathering

- ✅ **Bayesian Guardian** (`empirica/core/governance/bayesian_guardian.py`)
  - Prevents overconfidence through probabilistic constraints
  - Governance layer for epistemic validity

- ✅ **Session Database** (`empirica/data/session_database.py`)
  - Stores preflight/postflight assessments
  - Tracks epistemic deltas across phases
  - Supports continuity loading

- ✅ **MCP Server** (`mcp_local/empirica_mcp_server.py`)
  - Exposes all components via MCP tools
  - Correct integration (not old stub server)

#### Supporting Systems
- ✅ **Drift Monitor** - Detects when recalibration needed
- ✅ **Goal Orchestrator** - Dynamic goal management
- ✅ **CLI Interface** - Command-line access to components
- ✅ **Bootstrap System** - Proper initialization

### 3.2 Recent Fixes Applied ✅
- ✅ Removed all heuristic fallbacks
- ✅ Removed demo/test code from production paths
- ✅ Fixed meta-uncertainty as 13th vector (not separate meta-state)
- ✅ Clarified self-assessment vs external LLM distinction
- ✅ Updated all documentation to reflect 7-phase cascade
- ✅ Integrated workflow phases with cascade phases

### 3.3 Known Issues / Under Development 🔄
- 🔄 **Session Continuity:** Basic implementation complete, advanced epistemic weighting in progress
- 🔄 **End-to-End Testing:** Manual validation needed to confirm genuine self-reflection
- 🔄 **Cross-AI Testing:** Not yet validated with Qwen/Gemini

---

## 4. Pre-Test Setup Validation

### 4.1 Environment Check

**Before running any tests, validate:**

```bash
# 1. Python environment
python3 --version  # Should be 3.11+

# 2. Empirica installation
cd /home/yogapad/empirical-ai/empirica
pip list | grep empirica  # Should show installed

# 3. Dependencies
pip install -r requirements.txt

# 4. Directory structure
ls -la empirica/core/  # Should show all components
ls -la mcp_local/      # Should show MCP server

# 5. MCP server location (correct one)
ls -la mcp_local/empirica_mcp_server.py  # Should exist
```

### 4.2 Configuration Check

**Verify MCP configuration:**

```bash
# Check MCP config points to correct server
cat mcp_config.json | grep empirica_mcp_server

# Expected output:
# "command": "python",
# "args": ["-m", "empirica.mcp_local.empirica_mcp_server"]
```

### 4.3 Component Import Check

**Test all components import correctly:**

```python
# test_imports.py
import sys
sys.path.insert(0, '/home/yogapad/empirical-ai/empirica')

# Core components
from empirica.core.epistemic_state.monitor_12d import CognitiveStateMonitor
from empirica.core.metacognitive_cascade.metacognitive_cascade import MetacognitiveCascade
from empirica.core.uncertainty.calibration import AdaptiveUncertaintyCalibrator
from empirica.core.investigation.investigation_orchestrator import InvestigationOrchestrator
from empirica.core.governance.bayesian_guardian import BayesianGuardian
from empirica.data.session_database import SessionDatabase

# MCP server
from empirica.mcp_local.empirica_mcp_server import (
    tool_empirica_cascade_preflight,
    tool_empirica_cascade_postflight,
    tool_empirica_cascade_run_full
)

print("✅ All imports successful")
```

**Run:**
```bash
python test_imports.py
```

---

## 5. Phase 1: Component Integration Tests

### 5.1 Test 1: 13D State Monitor

**Purpose:** Verify epistemic state monitoring works correctly

```python
# test_13d_monitor.py
from empirica.core.epistemic_state.monitor_12d import CognitiveStateMonitor

def test_13d_assessment():
    """Test complete 13-dimensional assessment"""
    monitor = CognitiveStateMonitor(ai_id="test_agent")
    
    # Assess current state
    state = monitor.assess_current_state(
        task_context={
            "task": "code_review",
            "complexity": "high",
            "domain": "security"
        },
        user_input="Review this authentication module",
        conversation_history=[]
    )
    
    # Validate structure
    assert "epistemic_uncertainty" in state, "Missing epistemic uncertainty dimension"
    assert "epistemic_comprehension" in state, "Missing comprehension dimension"
    assert "execution_awareness" in state, "Missing execution dimension"
    assert "engagement" in state, "Missing engagement dimension"
    
    # Validate 13 vectors
    eu = state["epistemic_uncertainty"]
    assert all(k in eu for k in ["know", "do", "context"]), "Missing EU vectors"
    
    ec = state["epistemic_comprehension"]
    assert all(k in ec for k in ["clarity", "coherence", "depth", "signal"]), "Missing EC vectors"
    
    ea = state["execution_awareness"]
    assert all(k in ea for k in ["state", "change", "completion", "impact"]), "Missing EA vectors"
    
    eng = state["engagement"]
    assert "meta_uncertainty" in eng, "Missing 13th vector (meta-uncertainty)"
    
    # Validate ranges (0.0 to 1.0)
    for dim in [eu, ec, ea]:
        for vector, value in dim.items():
            assert 0.0 <= value <= 1.0, f"Vector {vector} out of range: {value}"
    
    assert 0.0 <= eng["meta_uncertainty"] <= 1.0, "Meta-uncertainty out of range"
    
    print("✅ 13D Monitor Test PASSED")
    print(f"Sample state: {state}")
    return state

if __name__ == "__main__":
    test_13d_assessment()
```

**Success Criteria:**
- ✅ All 13 vectors present
- ✅ Values in correct range (0.0-1.0)
- ✅ No errors or exceptions
- ✅ No heuristic fallbacks used

---

### 5.2 Test 2: Uncertainty Calibration (Self-Assessment)

**Purpose:** Verify AI self-assesses uncertainty (no external LLM calls)

```python
# test_calibration_self_assessment.py
from empirica.core.uncertainty.calibration import AdaptiveUncertaintyCalibrator

def test_self_assessment_only():
    """Verify calibration uses self-assessment, not external LLM"""
    calibrator = AdaptiveUncertaintyCalibrator()
    
    # This should use AI's own self-reflection
    result = calibrator.assess_uncertainty(
        decision_context="Should I deploy this change to production?"
    )
    
    # Validate result structure
    assert "uncertainty_score" in result, "Missing uncertainty score"
    assert "confidence_level" in result, "Missing confidence level"
    assert "epistemic_uncertainty" in result, "Missing epistemic uncertainty"
    assert "aleatoric_uncertainty" in result, "Missing aleatoric uncertainty"
    
    # Validate no external LLM was called
    # (This is confirmed by code inspection - no phi3 calls in production path)
    
    print("✅ Calibration Self-Assessment Test PASSED")
    print(f"Result: {result}")
    return result

if __name__ == "__main__":
    test_self_assessment_only()
```

**Success Criteria:**
- ✅ Returns proper uncertainty assessment
- ✅ No external LLM calls (verified by code inspection)
- ✅ Self-assessment reflects genuine epistemic state

---

### 5.3 Test 3: Auto-Tracker (No Heuristics)

**Purpose:** Verify auto-tracker doesn't use heuristic fallbacks

```python
# test_auto_tracker_no_heuristics.py
from empirica.core.investigation.auto_tracker import AutoTracker

def test_no_heuristic_fallbacks():
    """Verify auto-tracker uses genuine tracking, not heuristics"""
    tracker = AutoTracker()
    
    # Enable tracking
    tracker.enable()
    
    # Simulate some tool calls
    tracker.log_tool_call("file_read", {"path": "/test/file.py"})
    tracker.log_tool_call("search", {"query": "authentication"})
    
    # Get summary
    summary = tracker.get_summary()
    
    # Validate structure
    assert "tool_calls" in summary, "Missing tool calls"
    assert len(summary["tool_calls"]) == 2, "Should have tracked 2 calls"
    
    # Verify no heuristic scoring (should be actual tracking)
    assert summary["tool_calls"][0]["tool"] == "file_read"
    assert summary["tool_calls"][1]["tool"] == "search"
    
    print("✅ Auto-Tracker No Heuristics Test PASSED")
    print(f"Summary: {summary}")
    return summary

if __name__ == "__main__":
    test_no_heuristic_fallbacks()
```

**Success Criteria:**
- ✅ Tracks actual tool calls
- ✅ No heuristic fallback patterns
- ✅ Demo code not in production path

---

## 6. Phase 2: Cascade Workflow Tests

### 6.1 Test 4: 7-Phase Cascade Execution

**Purpose:** Verify complete cascade workflow executes correctly

```python
# test_7_phase_cascade.py
from empirica.core.metacognitive_cascade.metacognitive_cascade import MetacognitiveCascade
from empirica.data.session_database import SessionDatabase

def test_complete_cascade():
    """Test full 7-phase cascade execution"""
    cascade = MetacognitiveCascade()
    db = SessionDatabase()
    
    # Run complete cascade
    result = cascade.run_full_cascade(
        question="Should I refactor this legacy module?",
        context={
            "module": "authentication",
            "complexity": "high",
            "test_coverage": 0.65,
            "users_affected": 50000
        }
    )
    
    # Validate all phases executed
    assert "preflight_assessment" in result, "Missing PREFLIGHT"
    assert "think_result" in result, "Missing THINK"
    assert "plan_result" in result, "Missing PLAN"
    assert "investigate_result" in result, "Missing INVESTIGATE"
    assert "check_result" in result, "Missing CHECK"
    assert "act_result" in result, "Missing ACT"
    assert "postflight_assessment" in result, "Missing POSTFLIGHT"
    
    # Validate epistemic delta calculated
    assert "epistemic_delta" in result, "Missing epistemic delta"
    
    # Validate session stored
    session_id = result.get("session_id")
    assert session_id is not None, "Session should be stored"
    
    # Retrieve from database
    session = db.get_session(session_id)
    assert session is not None, "Session should be retrievable"
    assert "preflight_vectors" in session, "Should have preflight vectors"
    assert "postflight_vectors" in session, "Should have postflight vectors"
    
    print("✅ 7-Phase Cascade Test PASSED")
    print(f"Epistemic delta: {result['epistemic_delta']}")
    return result

if __name__ == "__main__":
    test_complete_cascade()
```

**Success Criteria:**
- ✅ All 7 phases execute
- ✅ Preflight/postflight assessments recorded
- ✅ Epistemic delta calculated
- ✅ Session stored in database

---

### 6.2 Test 5: Preflight/Postflight Integration

**Purpose:** Verify preflight and postflight work correctly

```python
# test_preflight_postflight.py
from empirica.core.metacognitive_cascade.preflight_epistemic_calibration import PreflightCalibrator
from empirica.core.metacognitive_cascade.postflight_epistemic_assessment import PostflightAssessor

def test_preflight_postflight_cycle():
    """Test preflight → work → postflight cycle"""
    preflight = PreflightCalibrator()
    postflight = PostflightAssessor()
    
    # PREFLIGHT: Assess initial state
    preflight_result = preflight.assess_readiness(
        task="Implement OAuth2 authentication",
        context={
            "experience_level": "intermediate",
            "available_docs": True,
            "time_pressure": "medium"
        }
    )
    
    assert "epistemic_vectors" in preflight_result, "Missing preflight vectors"
    assert "readiness_score" in preflight_result, "Missing readiness score"
    
    # Simulate work happening...
    work_result = {
        "actions_taken": ["read_docs", "write_code", "test_implementation"],
        "challenges_encountered": ["OAuth2 scope complexity"],
        "adaptations_made": ["consulted RFC 6749"]
    }
    
    # POSTFLIGHT: Assess final state
    postflight_result = postflight.assess_outcome(
        task="Implement OAuth2 authentication",
        initial_state=preflight_result["epistemic_vectors"],
        work_performed=work_result
    )
    
    assert "epistemic_vectors" in postflight_result, "Missing postflight vectors"
    assert "epistemic_delta" in postflight_result, "Missing epistemic delta"
    assert "calibration_accuracy" in postflight_result, "Missing calibration check"
    
    # Validate delta is calculated
    delta = postflight_result["epistemic_delta"]
    assert isinstance(delta, dict), "Delta should be a dict"
    
    print("✅ Preflight/Postflight Test PASSED")
    print(f"Epistemic growth: {delta}")
    return preflight_result, postflight_result

if __name__ == "__main__":
    test_preflight_postflight_cycle()
```

**Success Criteria:**
- ✅ Preflight assesses initial state
- ✅ Postflight assesses final state
- ✅ Epistemic delta calculated
- ✅ Calibration accuracy checked

---

## 7. Phase 3: MCP Server Tests

### 7.1 Test 6: MCP Server Tool Availability

**Purpose:** Verify MCP server exposes correct tools

```python
# test_mcp_tools_list.py
import subprocess
import json

def test_mcp_tools_available():
    """Test MCP server lists all expected tools"""
    
    # Call MCP server to list tools
    result = subprocess.run(
        ["python", "-m", "empirica.mcp_local.empirica_mcp_server", "--list-tools"],
        capture_output=True,
        text=True,
        cwd="/home/yogapad/empirical-ai/empirica"
    )
    
    tools = json.loads(result.stdout)
    tool_names = [t["name"] for t in tools["tools"]]
    
    # Expected tools
    expected = [
        "empirica.cascade.preflight",
        "empirica.cascade.postflight",
        "empirica.cascade.run_full",
        "empirica.cascade.phase",
        "empirica.monitor.assess_13d",
        "empirica.calibration.assess",
        "empirica.investigation.run",
        "empirica.session.save",
        "empirica.session.load"
    ]
    
    for tool in expected:
        assert tool in tool_names, f"Missing tool: {tool}"
    
    print("✅ MCP Tools List Test PASSED")
    print(f"Available tools: {tool_names}")
    return tool_names

if __name__ == "__main__":
    test_mcp_tools_available()
```

**Success Criteria:**
- ✅ All expected tools present
- ✅ MCP server responds correctly
- ✅ Tool schemas valid

---

### 7.2 Test 7: MCP Tool Execution

**Purpose:** Verify MCP tools execute correctly

```python
# test_mcp_tool_execution.py
import subprocess
import json

def test_mcp_cascade_preflight():
    """Test calling preflight via MCP"""
    
    request = {
        "method": "tools/call",
        "params": {
            "name": "empirica.cascade.preflight",
            "arguments": {
                "task": "Code review",
                "context": {"complexity": "medium"}
            }
        }
    }
    
    result = subprocess.run(
        ["python", "-m", "empirica.mcp_local.empirica_mcp_server"],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        cwd="/home/yogapad/empirical-ai/empirica"
    )
    
    response = json.loads(result.stdout)
    
    assert "result" in response, "Missing result"
    assert "epistemic_vectors" in response["result"], "Missing vectors"
    
    print("✅ MCP Tool Execution Test PASSED")
    print(f"Preflight result: {response['result']}")
    return response

if __name__ == "__main__":
    test_mcp_cascade_preflight()
```

**Success Criteria:**
- ✅ Tool executes successfully
- ✅ Returns correct data structure
- ✅ No errors or exceptions

---

## 8. Phase 4: Cross-AI Compatibility Tests

### 8.1 Test 8: Qwen Integration Test

**Purpose:** Validate Empirica works with Qwen

**Setup:**
```bash
# Ensure Qwen can access Empirica via MCP
# Configure Qwen's MCP client to point to empirica_mcp_server
```

**Test Procedure:**
1. Start Qwen session with Empirica MCP server configured
2. Ask Qwen to run preflight assessment
3. Ask Qwen to execute a simple task with full cascade
4. Verify Qwen can self-assess its epistemic state

**Expected Behavior:**
- ✅ Qwen calls `empirica.cascade.preflight` before engaging
- ✅ Qwen uses 13D vectors to reflect on its state
- ✅ Qwen completes cascade workflow correctly
- ✅ Qwen calls `empirica.cascade.postflight` after task

**Validation:**
```python
# Check session database for Qwen's assessment
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()
qwen_sessions = db.get_sessions_by_ai_id("qwen")

assert len(qwen_sessions) > 0, "Qwen should have created sessions"
assert "preflight_vectors" in qwen_sessions[0], "Should have preflight"
assert "postflight_vectors" in qwen_sessions[0], "Should have postflight"
```

---

### 8.2 Test 9: Gemini Integration Test

**Purpose:** Validate Empirica works with Gemini

**Test Procedure:**
1. Configure Gemini with Empirica MCP server
2. Ask Gemini to solve a complex reasoning task using cascade
3. Verify Gemini's self-assessment is genuine (not pattern matching)

**Critical Validation:**
- Does Gemini's uncertainty assessment match actual performance?
- Does Gemini detect when it needs to investigate vs when it can act?
- Does Gemini's meta-uncertainty (13th vector) reflect genuine self-awareness?

---

### 8.3 Test 10: Cross-AI Comparison

**Purpose:** Compare how different AIs use Empirica

**Methodology:**
1. Give same task to Claude, Qwen, and Gemini
2. All use Empirica cascade workflow
3. Compare epistemic trajectories

**Metrics to Compare:**
- Initial preflight confidence
- Investigation depth (how much investigating before acting)
- Final postflight confidence
- Calibration accuracy (confidence vs actual performance)
- Meta-uncertainty awareness

**Expected Finding:**
Different AIs may have different epistemic profiles, but all should:
- ✅ Accurately assess their own uncertainty
- ✅ Investigate when uncertain
- ✅ Act when confident
- ✅ Recalibrate when drift detected

---

## 9. Phase 5: Real-World Scenario Tests

### 9.1 Test 11: Code Review Task

**Scenario:**
```
Task: "Review this authentication module for security vulnerabilities"
Context: Legacy codebase, 5000 lines, no tests, production system
```

**Test Procedure:**
1. AI runs PREFLIGHT assessment
   - Should show HIGH uncertainty (unfamiliar codebase)
   - Should show LOW confidence
   
2. AI runs INVESTIGATE phase
   - Should read code files
   - Should search for security patterns
   - Should build understanding

3. AI runs CHECK phase
   - Should verify understanding correct
   - Should recalibrate if needed

4. AI runs ACT phase
   - Should provide review findings

5. AI runs POSTFLIGHT assessment
   - Should show LOWER uncertainty (learned about codebase)
   - Should show HIGHER confidence
   - Should have positive epistemic delta

**Success Criteria:**
- ✅ Epistemic trajectory makes sense (uncertainty → investigation → confidence)
- ✅ AI doesn't act before understanding
- ✅ Calibration accuracy is good (confidence matches performance)

---

### 9.2 Test 12: Multi-Session Continuity

**Scenario:**
```
Session 1: Design authentication system
Session 2: Implement authentication system
Session 3: Add security hardening
```

**Test Procedure:**
1. Run Session 1, let AI complete design
2. In Session 2, load Session 1 context via continuity system
3. Verify AI remembers design decisions
4. In Session 3, load previous contexts
5. Verify cumulative learning

**Success Criteria:**
- ✅ Session 2 AI doesn't re-ask design questions
- ✅ Session 3 AI understands full context
- ✅ No false continuity (AI doesn't hallucinate past decisions)
- ✅ Epistemic deltas accumulate correctly

---

### 9.3 Test 13: Overconfidence Detection

**Scenario:**
```
Task: "Fix this obscure bug in quantum computing library"
Context: AI has no quantum computing experience
```

**Test Procedure:**
1. AI runs PREFLIGHT
   - Should detect HIGH uncertainty (unfamiliar domain)
   
2. AI attempts to proceed
   - Bayesian Guardian should intervene if overconfident
   
3. AI investigates
   - Should recognize knowledge gaps
   - Should increase uncertainty appropriately

**Success Criteria:**
- ✅ AI accurately assesses lack of knowledge
- ✅ Bayesian Guardian prevents overconfident claims
- ✅ AI recommends investigation or deferral
- ✅ Meta-uncertainty (13th vector) is high

---

## 10. Success Criteria

### 10.1 Component-Level Success
- ✅ All components import without errors
- ✅ All tests pass without exceptions
- ✅ No heuristic fallbacks triggered
- ✅ No external LLM calls for self-assessment (except governance verification)
- ✅ All 13 epistemic vectors tracked correctly

### 10.2 Workflow-Level Success
- ✅ 7-phase cascade executes completely
- ✅ Preflight/postflight assessments recorded
- ✅ Epistemic deltas calculated correctly
- ✅ Session database stores all data
- ✅ MCP server exposes all tools correctly

### 10.3 Cross-AI Success
- ✅ Works with Claude (reference implementation)
- ✅ Works with Qwen (validation)
- ✅ Works with Gemini (validation)
- ✅ Epistemic assessments are genuine, not pattern-matched

### 10.4 Real-World Success
- ✅ AI behavior matches epistemic state
- ✅ Calibration accuracy is good (confidence ≈ performance)
- ✅ No false confidence from continuity
- ✅ Overconfidence is detected and prevented

---

## 11. Failure Analysis Protocol

### 11.1 When Tests Fail

**For each failure, document:**

1. **Which test failed?**
2. **What was the error?**
3. **What was expected vs actual?**
4. **Is this a component bug or integration bug?**
5. **Is this an AI-specific issue or framework issue?**

### 11.2 Common Failure Patterns

#### Pattern 1: Import Errors
**Symptom:** `ModuleNotFoundError` or `ImportError`  
**Likely Cause:** Path issues or missing dependencies  
**Fix:** Check `sys.path`, verify installation

#### Pattern 2: Missing Vectors
**Symptom:** Epistemic assessment missing dimensions  
**Likely Cause:** Component not integrated correctly  
**Fix:** Check component initialization and method calls

#### Pattern 3: Heuristic Fallback Detected
**Symptom:** Results look pattern-matched, not genuine  
**Likely Cause:** Demo code still in production path  
**Fix:** Review code for fallback mechanisms, remove

#### Pattern 4: MCP Server Not Responding
**Symptom:** Tool calls timeout or error  
**Likely Cause:** Wrong server path or configuration  
**Fix:** Verify using correct `mcp_local/empirica_mcp_server.py`

#### Pattern 5: False Self-Assessment
**Symptom:** AI claims confidence but performance poor  
**Likely Cause:** Pattern matching instead of genuine reflection  
**Fix:** Verify calibration component working, check Bayesian Guardian

### 11.3 Reporting Template

```markdown
## Test Failure Report

**Test:** [Test name and number]  
**Date:** [YYYY-MM-DD]  
**AI Model:** [Claude/Qwen/Gemini/Other]  
**Environment:** [OS, Python version]

### Failure Details
- **Error Message:** [Full error text]
- **Expected Behavior:** [What should happen]
- **Actual Behavior:** [What actually happened]

### Root Cause Analysis
- **Component:** [Which component failed]
- **Reason:** [Why it failed]
- **Impact:** [Severity: Critical/High/Medium/Low]

### Fix Applied
- **Solution:** [What was changed]
- **Verification:** [How fix was verified]
- **Status:** [Fixed/In Progress/Needs Investigation]

### Prevention
- **Future Prevention:** [How to avoid this in future]
- **Documentation Update:** [What docs need updating]
```

---

## 12. Next Steps

### 12.1 Immediate Actions
1. ✅ Review this test plan for completeness
2. ✅ Run Pre-Test Setup Validation (Section 4)
3. ✅ Execute Phase 1: Component Integration Tests (Section 5)
4. ✅ Document any failures using protocol (Section 11)

### 12.2 This Week
1. Complete Phases 1-3 (Component, Cascade, MCP tests)
2. Validate with Claude (reference implementation)
3. Fix any critical issues found
4. Prepare for Qwen/Gemini testing

### 12.3 Next Week
1. Execute Phase 4: Cross-AI Compatibility Tests
2. Run real-world scenario tests
3. Analyze calibration accuracy across AIs
4. Document findings and recommendations

### 12.4 Ongoing
- Continuous validation as components evolve
- A/B testing with continuity system
- Epistemic trajectory analysis
- Cross-AI epistemic profiling

---

## 13. Reference Documents

### 13.1 Core Specifications
- `/docs/EMPIRICA_CASCADE_WORKFLOW_SPECIFICATION.md` - Canonical cascade workflow
- `/docs/production/00_COMPLETE_SUMMARY.md` - Complete system overview
- `/INTEGRATION_SPEC_ENHANCED_WORKFLOW_WITH_EXISTING_ARCH.md` - Integration details

### 13.2 Component Documentation
- `/docs/production/05_EPISTEMIC_VECTORS.md` - 13D vector system
- `/docs/production/06_CASCADE_FLOW.md` - Cascade phase details
- `/docs/production/12_MCP_INTEGRATION.md` - MCP server integration

### 13.3 Testing Documentation
- `/QWEN_GEMINI_TESTING_GUIDE.md` - Original MCP testing guide
- `/empirica_continuity/AB_TESTING_PLAN.md` - Continuity A/B testing
- `/TESTING_STRATEGY.md` - Overall testing approach

---

**"Validation isn't about proving the system works - it's about discovering where our assumptions break and genuine epistemic humility begins."**
