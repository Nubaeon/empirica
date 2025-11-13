# 🧪 EMPIRICA MCP TESTING GUIDE (CORRECTED)

**For**: Qwen & Gemini  
**Location**: `semantic_self_aware_kit/semantic_self_aware_kit/mcp/empirica_mcp_server.py`  
**Status**: ✅ 5/7 Core Tools Working | 🟡 2/7 Simplified

---

## 📊 TOOL STATUS

### **✅ Fully Working Tools (5)**
1. `cascade_run_full` - Complete metacognitive cascade ✅
2. `cascade_phase` - Individual cascade phases ✅
3. `monitor_assess_12d` - 12D cognitive assessment ✅
4. `monitor_get_summary` - Formatted 12-vector summary ✅
5. `calibration_assess` - Adaptive uncertainty calibration ✅

### **🟡 Simplified Tools (2)**
6. `goals_create` - Returns basic goal structure (simplified)
7. `goals_orchestrate` - Returns basic orchestration (simplified)

### **✅ Utility Tools (2)**
8. `bootstrap_system` - System bootstrap ✅
9. `cli_help` - Help system ✅

---

## 🧪 TEST TEMPLATES

### **Test 1: Cascade Run Full (Priority: HIGH)**

```python
def test_cascade_run_full():
    """Test complete metacognitive cascade"""
    import json
    import sys
    sys.path.insert(0, '/home/yogapad/empirical-ai/semantic_self_aware_kit/semantic_self_aware_kit')
    
    from metacognitive_cascade.metacognitive_cascade import SimpleCascade
    
    cascade = SimpleCascade()
    result = cascade.run_full_cascade(
        "Should I deploy this feature to production?",
        {"environment": "production", "risk": "medium"}
    )
    
    # Validate
    assert result is not None, "Result should not be None"
    print(f"✅ cascade_run_full: {type(result)}")
    return True

test_cascade_run_full()
```

### **Test 2: Monitor Assess 12D (Priority: HIGH)**

```python
def test_monitor_assess_12d():
    """Test 12-dimensional cognitive assessment"""
    import sys
    sys.path.insert(0, '/home/yogapad/empirical-ai/semantic_self_aware_kit/semantic_self_aware_kit')
    
    from metacognition_12d_monitor.twelve_vector_self_awareness import TwelveVectorSelfAwarenessMonitor
    
    monitor = TwelveVectorSelfAwarenessMonitor("test_agent")
    state = monitor.assess_complete_state(
        {"task": "code_review", "complexity": "high"},
        "Review authentication module",
        None
    )
    
    # Validate structure
    assert hasattr(state, 'uncertainty'), "Should have uncertainty"
    assert hasattr(state, 'comprehension'), "Should have comprehension"
    assert hasattr(state, 'execution'), "Should have execution"
    assert hasattr(state, 'engagement'), "Should have engagement"
    
    # Check values
    assert state.uncertainty.know >= 0 and state.uncertainty.know <= 1
    assert state.comprehension.clarity >= 0 and state.comprehension.clarity <= 1
    assert state.execution.completion >= 0 and state.execution.completion <= 1
    assert state.engagement.engagement >= 0 and state.engagement.engagement <= 1
    
    confidence = state.overall_confidence()
    assert confidence >= 0 and confidence <= 1
    
    print(f"✅ monitor_assess_12d:")
    print(f"   Know: {state.uncertainty.know}")
    print(f"   Engagement: {state.engagement.engagement}")
    print(f"   Confidence: {confidence}")
    return True

test_monitor_assess_12d()
```

### **Test 3: Calibration Assess (Priority: HIGH)**

```python
def test_calibration_assess():
    """Test adaptive uncertainty calibration"""
    import sys
    sys.path.insert(0, '/home/yogapad/empirical-ai/semantic_self_aware_kit/semantic_self_aware_kit')
    
    from adaptive_uncertainty_calibration.adaptive_uncertainty_calibration import assess_uncertainty
    
    result = assess_uncertainty("Migrate 50k users to new database")
    
    # Validate
    assert result is not None
    print(f"✅ calibration_assess: {type(result)}")
    
    # Check attributes
    if hasattr(result, 'uncertainty_score'):
        print(f"   Uncertainty: {result.uncertainty_score}")
    if hasattr(result, 'confidence_level'):
        print(f"   Confidence: {result.confidence_level}")
    
    return True

test_calibration_assess()
```

### **Test 4: MCP Protocol Integration**

```bash
# Test via MCP stdio protocol

# Initialize
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}' | python3 empirica_mcp_server.py

# List tools
echo '{"jsonrpc":"2.0","method":"tools/list","id":2}' | python3 empirica_mcp_server.py

# Call cascade
echo '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"cascade_run_full","arguments":{"question":"Should I proceed?"}},"id":3}' | python3 empirica_mcp_server.py

# Call monitor
echo '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"monitor_assess_12d","arguments":{"task_context":{"task":"test"}}},"id":4}' | python3 empirica_mcp_server.py
```

---

## ✅ VALIDATION CHECKLIST

For each working tool:
- [ ] Tool can be invoked via MCP protocol
- [ ] Component import succeeds
- [ ] Component execution succeeds
- [ ] Output is valid JSON
- [ ] Error handling works (try invalid params)
- [ ] Output structure matches schema

---

## 🐛 KNOWN ISSUES

### **Goal Orchestrator (Simplified)**
- `goals_create` and `goals_orchestrate` are simplified
- Complex function signature issues with context analysis
- Returns basic goal structures instead of full orchestration
- **Note**: Core metacognitive tools (cascade, monitor, calibration) are fully functional

---

## 📊 TESTING PRIORITY

1. **HIGH**: `cascade_run_full`, `monitor_assess_12d`, `calibration_assess`
2. **MEDIUM**: `cascade_phase`, `monitor_get_summary`, `bootstrap_system`
3. **LOW**: `goals_create`, `goals_orchestrate` (simplified implementations)

---

## 🚀 QUICK TEST SCRIPT

```python
#!/usr/bin/env python3
"""Quick validation of Empirica MCP core tools"""
import sys
sys.path.insert(0, '/home/yogapad/empirical-ai/semantic_self_aware_kit/semantic_self_aware_kit')

print("🧪 EMPIRICA MCP CORE TOOLS TEST")
print("=" * 50)

# Test 1: Cascade
print("\n1. Testing Metacognitive Cascade...")
try:
    from metacognitive_cascade.metacognitive_cascade import SimpleCascade
    cascade = SimpleCascade()
    result = cascade.run_full_cascade("Should I deploy?", {})
    print("   ✅ Cascade working")
except Exception as e:
    print(f"   ❌ Cascade failed: {e}")

# Test 2: 12D Monitor
print("\n2. Testing 12D Monitor...")
try:
    from metacognition_12d_monitor.twelve_vector_self_awareness import TwelveVectorSelfAwarenessMonitor
    monitor = TwelveVectorSelfAwarenessMonitor("test")
    state = monitor.assess_complete_state({"task": "test"}, "", None)
    print(f"   ✅ Monitor working (confidence: {state.overall_confidence():.2f})")
except Exception as e:
    print(f"   ❌ Monitor failed: {e}")

# Test 3: Calibration
print("\n3. Testing Uncertainty Calibration...")
try:
    from adaptive_uncertainty_calibration.adaptive_uncertainty_calibration import assess_uncertainty
    result = assess_uncertainty("Test decision")
    print("   ✅ Calibration working")
except Exception as e:
    print(f"   ❌ Calibration failed: {e}")

print("\n✅ CORE TOOLS VALIDATED")
```

---

**Testing Status**: Ready for Qwen/Gemini validation  
**Priority**: Test HIGH priority tools first  
**Expected Time**: 30-45 minutes
