# 🧪 TESTING GUIDE FOR QWEN & GEMINI

**Purpose**: Unit test and validate the 10 new MCP tools added to empirica_mcp_server.py  
**Status**: Implementation Complete - Ready for Testing  
**Your Mission**: Validate each tool works correctly with real component integration

---

## 📋 WHAT WAS IMPLEMENTED

Claude added 10 new MCP tools for direct Empirica component integration:

### **Metacognitive Cascade Tools (3)**
1. `empirica.cascade.run_full` - Run complete THINK→UNCERTAINTY→CHECK→INVESTIGATE→ACT cascade
2. `empirica.cascade.phase` - Run individual cascade phases
3. `empirica.cascade.feedback` - Provide learning feedback

### **12D Monitor Tools (3)**
4. `empirica.monitor.assess_12d` - Complete 12-dimensional cognitive assessment
5. `empirica.monitor.get_summary` - Get formatted 12-vector summary
6. `empirica.monitor.assess_engagement` - Assess engagement dimension

### **Uncertainty Calibration Tool (1)**
7. `empirica.calibration.assess` - Adaptive uncertainty assessment

### **Goal Orchestrator Tools (2)**
8. `empirica.goals.create` - Create dynamic goals from context
9. `empirica.goals.orchestrate` - Orchestrate goals with engagement tracking

### **CLI Integration Tool (1)**
10. `empirica.cli.help` - Get help for CLI commands

---

## 🧪 TESTING METHODOLOGY

### **For Each Tool, Test:**
1. **Import Test**: Can the component be imported?
2. **Instantiation Test**: Can the component be created?
3. **Execution Test**: Does the tool function work?
4. **Error Handling Test**: Does it handle errors gracefully?
5. **Output Validation Test**: Is the output format correct?

---

## 🔬 UNIT TEST TEMPLATES

### **Test 1: Metacognitive Cascade - Run Full**

```python
def test_cascade_run_full():
    """Test complete cascade execution"""
    params = {
        "question": "Should I deploy this feature to production?",
        "context": {
            "environment": "production",
            "risk_level": "medium",
            "testing_complete": True
        }
    }
    
    result = tool_empirica_cascade_run_full(params)
    
    # Assertions
    assert result["ok"] == True, "Tool should succeed"
    assert "cascade_result" in result, "Should return cascade result"
    assert isinstance(result["cascade_result"], dict), "Result should be dict"
    
    print("✅ test_cascade_run_full passed")
```

### **Test 2: Metacognitive Cascade - Individual Phase**

```python
def test_cascade_phase():
    """Test individual cascade phases"""
    phases = ["think", "uncertainty", "check", "investigate", "act"]
    
    for phase in phases:
        params = {
            "phase": phase,
            "input": {"question": "Test question", "context": {}}
        }
        
        result = tool_empirica_cascade_phase(params)
        
        assert result["ok"] == True, f"Phase {phase} should succeed"
        assert result["phase"] == phase, "Should return correct phase"
        assert "result" in result, "Should have result"
        
        print(f"✅ test_cascade_phase({phase}) passed")
```

### **Test 3: 12D Monitor Assessment**

```python
def test_monitor_assess_12d():
    """Test 12-dimensional cognitive state assessment"""
    params = {
        "ai_id": "test_agent",
        "task_context": {
            "task": "code_review",
            "complexity": "medium",
            "urgency": "normal"
        },
        "user_input": "Please review the authentication module",
        "conversation_history": ["Previous context about security"]
    }
    
    result = tool_empirica_monitor_assess_12d(params)
    
    # Assertions
    assert result["ok"] == True, "Tool should succeed"
    assert "cognitive_state" in result, "Should return cognitive state"
    
    state = result["cognitive_state"]
    
    # Check all 4 dimensions present
    assert "epistemic_uncertainty" in state, "Missing epistemic uncertainty"
    assert "epistemic_comprehension" in state, "Missing comprehension"
    assert "execution_awareness" in state, "Missing execution"
    assert "engagement" in state, "Missing engagement"
    
    # Check 12 vectors
    eu = state["epistemic_uncertainty"]
    assert "know" in eu and "do" in eu and "context" in eu, "Missing EU vectors"
    
    ec = state["epistemic_comprehension"]
    assert all(k in ec for k in ["clarity", "coherence", "depth", "signal"]), "Missing EC vectors"
    
    ea = state["execution_awareness"]
    assert all(k in ea for k in ["state", "change", "completion", "impact"]), "Missing EA vectors"
    
    assert "overall_confidence" in result["cognitive_state"], "Missing overall confidence"
    
    print("✅ test_monitor_assess_12d passed")
```

### **Test 4: Monitor Get Summary**

```python
def test_monitor_get_summary():
    """Test formatted 12-vector summary"""
    params = {
        "ai_id": "test_agent"
    }
    
    result = tool_empirica_monitor_get_summary(params)
    
    assert result["ok"] == True, "Tool should succeed"
    assert "summary" in result, "Should return summary"
    assert isinstance(result["summary"], str), "Summary should be string"
    assert len(result["summary"]) > 0, "Summary should not be empty"
    
    print("✅ test_monitor_get_summary passed")
```

### **Test 5: Uncertainty Calibration**

```python
def test_calibration_assess():
    """Test adaptive uncertainty calibration"""
    params = {
        "decision_context": "Migrating 50,000 active users to new database schema"
    }
    
    result = tool_empirica_calibration_assess(params)
    
    assert result["ok"] == True, "Tool should succeed"
    assert "uncertainty_assessment" in result, "Should return assessment"
    
    assessment = result["uncertainty_assessment"]
    
    # Check all uncertainty metrics present
    expected_keys = ["uncertainty_score", "confidence_level", "epistemic_uncertainty", 
                     "aleatoric_uncertainty", "calibration_quality"]
    
    for key in expected_keys:
        assert key in assessment, f"Missing {key} in assessment"
    
    print("✅ test_calibration_assess passed")
```

### **Test 6: Goal Creation**

```python
def test_goals_create():
    """Test dynamic goal creation"""
    params = {
        "context": {
            "project": "web_development",
            "phase": "implementation",
            "priority": "high"
        }
    }
    
    result = tool_empirica_goals_create(params)
    
    assert result["ok"] == True, "Tool should succeed"
    assert "goals" in result, "Should return goals"
    assert "count" in result, "Should return goal count"
    
    print("✅ test_goals_create passed")
```

### **Test 7: Goal Orchestration**

```python
def test_goals_orchestrate():
    """Test goal orchestration with engagement"""
    params = {
        "context": {
            "project": "api_development",
            "resources": "limited",
            "timeline": "2_weeks"
        }
        # goals optional - will be auto-generated if not provided
    }
    
    result = tool_empirica_goals_orchestrate(params)
    
    assert result["ok"] == True, "Tool should succeed"
    assert "orchestration_result" in result, "Should return orchestration result"
    
    print("✅ test_goals_orchestrate passed")
```

### **Test 8: CLI Help**

```python
def test_cli_help():
    """Test CLI help system"""
    # Test general help
    params = {}
    result = tool_empirica_cli_help(params)
    
    assert result["ok"] == True, "Tool should succeed"
    assert "help" in result, "Should return help text"
    assert "bootstrap" in result["help"].lower(), "Help should mention bootstrap"
    assert "cascade" in result["help"].lower(), "Help should mention cascade"
    
    print("✅ test_cli_help passed")
```

### **Test 9: Error Handling - Missing Required Parameters**

```python
def test_error_handling_missing_params():
    """Test error handling for missing required parameters"""
    
    # Test cascade without question
    result = tool_empirica_cascade_run_full({})
    assert result["ok"] == False, "Should fail without question"
    assert "error" in result, "Should return error message"
    
    # Test calibration without decision_context
    result = tool_empirica_calibration_assess({})
    assert result["ok"] == False, "Should fail without decision_context"
    assert "error" in result, "Should return error message"
    
    print("✅ test_error_handling_missing_params passed")
```

### **Test 10: Error Handling - Invalid Parameters**

```python
def test_error_handling_invalid_params():
    """Test error handling for invalid parameters"""
    
    # Test invalid cascade phase
    params = {
        "phase": "invalid_phase",
        "input": {}
    }
    result = tool_empirica_cascade_phase(params)
    assert result["ok"] == False, "Should fail with invalid phase"
    assert "error" in result, "Should return error message"
    assert "must be one of" in result["error"].lower(), "Error should mention valid phases"
    
    print("✅ test_error_handling_invalid_params passed")
```

---

## 🚀 RUNNING THE TESTS

### **Method 1: Direct Python Testing**

Create a test file:

```python
# test_empirica_mcp_tools.py
import sys
sys.path.insert(0, '/home/yogapad/empirical-ai/semantic_self_aware_kit')

from empirica_mcp_server import (
    tool_empirica_cascade_run_full,
    tool_empirica_cascade_phase,
    tool_empirica_cascade_feedback,
    tool_empirica_monitor_assess_12d,
    tool_empirica_monitor_get_summary,
    tool_empirica_monitor_assess_engagement,
    tool_empirica_calibration_assess,
    tool_empirica_goals_create,
    tool_empirica_goals_orchestrate,
    tool_empirica_cli_help
)

# Run all tests
if __name__ == "__main__":
    test_cascade_run_full()
    test_cascade_phase()
    test_monitor_assess_12d()
    test_monitor_get_summary()
    test_calibration_assess()
    test_goals_create()
    test_goals_orchestrate()
    test_cli_help()
    test_error_handling_missing_params()
    test_error_handling_invalid_params()
    
    print("\n🎉 ALL TESTS PASSED!")
```

Run with:
```bash
cd /home/yogapad/empirical-ai/semantic_self_aware_kit
python3 test_empirica_mcp_tools.py
```

### **Method 2: MCP Protocol Testing (via stdio)**

Test via MCP protocol:

```bash
cd /home/yogapad/empirical-ai/semantic_self_aware_kit

# Test initialize
echo '{"method":"initialize","id":1}' | python3 empirica_mcp_server.py --stdio

# Test tools/list
echo '{"method":"tools/list","id":2}' | python3 empirica_mcp_server.py --stdio

# Test cascade tool
echo '{"method":"tools/call","id":3,"params":{"name":"empirica.cascade.run_full","arguments":{"question":"Should I deploy?"}}}' | python3 empirica_mcp_server.py --stdio

# Test 12D monitor tool
echo '{"method":"tools/call","id":4,"params":{"name":"empirica.monitor.assess_12d","arguments":{"task_context":{"task":"test"}}}}' | python3 empirica_mcp_server.py --stdio
```

---

## ✅ VALIDATION CHECKLIST

For each tool, verify:

- [ ] **Import Success**: Component imports without errors
- [ ] **Execution Success**: Tool function executes without exceptions
- [ ] **Output Format**: Returns {"ok": True, ...} on success
- [ ] **Error Format**: Returns {"ok": False, "error": "..."} on failure
- [ ] **Required Parameters**: Validates required parameters are present
- [ ] **Invalid Parameters**: Handles invalid parameters gracefully
- [ ] **Component Integration**: Actually calls the real component (not stub)
- [ ] **Output Structure**: Returns expected data structure
- [ ] **Type Safety**: Output types match schema
- [ ] **Edge Cases**: Handles empty inputs, null values, etc.

---

## 🎯 SUCCESS CRITERIA

Tests pass when:
- ✅ All 10 tools can be imported
- ✅ All 10 tools execute without exceptions on valid input
- ✅ All 10 tools return proper error messages on invalid input
- ✅ Output matches expected JSON schema
- ✅ Real components are being called (verify with debug prints)
- ✅ No stub/placeholder responses returned

---

## 🐛 COMMON ISSUES TO CHECK

1. **Import Errors**: Check sys.path includes semantic_self_aware_kit directory
2. **Component Not Found**: Verify component modules exist and are importable
3. **Method Not Found**: Check method names match exactly (e.g., assess_uncertainty vs uncertainty)
4. **Attribute Errors**: Check result objects have expected attributes (use getattr with defaults)
5. **Type Errors**: Ensure parameters match expected types (dict vs string, etc.)

---

## 📊 REPORTING RESULTS

For each test, report:
```
Tool: empirica.cascade.run_full
Status: ✅ PASS / ❌ FAIL
Execution Time: 0.15s
Output Valid: Yes
Error Handling: Working
Notes: [any observations]
```

Create a summary report:
```
Total Tools Tested: 10
Passed: X
Failed: Y
Success Rate: Z%

Critical Issues: [list any blockers]
Minor Issues: [list any warnings]
Recommendations: [suggest improvements]
```

---

## 🔄 NEXT STEPS AFTER TESTING

Once all tests pass:
1. **Document any issues found** in a separate file
2. **Report success rate** to human
3. **Suggest improvements** based on findings
4. **Validate with real-world scenarios** (optional but recommended)

---

**Testing Priority**: HIGH  
**Estimated Time**: 1-2 hours  
**Blockers**: None - all components are operational

Good luck with testing! 🧪✨
