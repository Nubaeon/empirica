# Modality Switcher - Comprehensive Multi-Model Testing

**Date:** 2025-11-03 02:30 UTC
**Assigned to:** Copilot CLI Claude + Rovodev Claude
**Estimated Time:** 45-60 minutes
**Status:** Ready to start after adapter updates complete

---

## 🎯 Objective

Test the Modality Switcher with **all 7 adapters and 15+ models** to validate:
1. ✅ All adapters work with centralized credentials
2. ✅ Model selection works for each adapter
3. ✅ Epistemic snapshot transfers work across all models
4. ✅ Multi-hop transfers maintain quality across different AIs
5. ✅ ModalitySwitcher routing decisions work correctly

---

## 📊 Test Coverage Matrix

| Adapter | Models to Test | Snapshot Support | MCP Support |
|---------|---------------|------------------|-------------|
| **Qwen** | qwen-coder-plus, qwen-coder-turbo | ✅ Phase 4 | ✅ |
| **MiniMax** | abab6.5s-chat, abab6.5-chat | ✅ Phase 4 | ✅ |
| **Rovodev** | claude-3-5-sonnet, claude-3-opus | ✅ Phase 4 | ✅ |
| **Gemini** | gemini-2.0-flash-exp, gemini-1.5-pro | ✅ Phase 4 | ✅ |
| **Qodo** | gpt-4, gpt-3.5-turbo | ✅ Phase 4 | ✅ |
| **OpenRouter** | anthropic/claude-3.5-sonnet, openai/gpt-4-turbo | ✅ Phase 4 | ✅ |
| **Copilot** | claude-sonnet-4, gpt-5, grok-fast-1 | ✅ Phase 4 | ✅ |

**Total:** 7 adapters, 15+ models, all with snapshot support

---

## 🧪 Test Suite

### **Test 1: Basic Adapter Functionality** (10 min)

**Goal:** Verify all adapters work with default models

```bash
# Test each adapter with simple prompt
for adapter in qwen minimax rovodev gemini qodo openrouter copilot; do
    echo "Testing $adapter..."
    python3 -m empirica.cli decision "Say hello in exactly 10 words" --adapter $adapter
    echo ""
done
```

**Expected:**
- ✅ All 7 adapters respond successfully
- ✅ Responses are coherent
- ✅ Token counts tracked
- ✅ No errors

**If failures:** Document which adapters/models failed and why

---

### **Test 2: Model Selection** (15 min)

**Goal:** Verify model selection works for each adapter

```bash
# Qwen models
python3 -m empirica.cli decision "Quick test" --adapter qwen --model qwen-coder-plus
python3 -m empirica.cli decision "Quick test" --adapter qwen --model qwen-coder-turbo

# MiniMax models
python3 -m empirica.cli decision "Quick test" --adapter minimax --model abab6.5s-chat
python3 -m empirica.cli decision "Quick test" --adapter minimax --model abab6.5-chat

# Gemini models
python3 -m empirica.cli decision "Quick test" --adapter gemini --model gemini-2.0-flash-exp
python3 -m empirica.cli decision "Quick test" --adapter gemini --model gemini-1.5-pro

# Copilot models (multi-model in one adapter!)
python3 -m empirica.cli decision "Quick test" --adapter copilot --model claude-sonnet-4
python3 -m empirica.cli decision "Quick test" --adapter copilot --model gpt-5
python3 -m empirica.cli decision "Quick test" --adapter copilot --model grok-fast-1

# OpenRouter models
python3 -m empirica.cli decision "Quick test" --adapter openrouter --model anthropic/claude-3.5-sonnet
python3 -m empirica.cli decision "Quick test" --adapter openrouter --model openai/gpt-4-turbo
```

**Expected:**
- ✅ All model selections work
- ✅ Correct model used in API calls
- ✅ Logging shows model name
- ✅ No model validation errors

---

### **Test 3: Epistemic Snapshot Transfers** (20 min)

**Goal:** Test cross-AI snapshot transfers with quality tracking

#### **3a. Simple Transfer Chain**
```python
#!/usr/bin/env python3
"""
Test simple snapshot transfer: Qwen → MiniMax
"""
from empirica.plugins.modality_switcher.snapshot_provider import EpistemicSnapshotProvider
from empirica.plugins.modality_switcher.plugin_registry import get_registry, AdapterPayload

# Create initial snapshot
provider = EpistemicSnapshotProvider()

# Simulate Qwen session
snapshot1 = provider.create_snapshot_from_session(
    session_id="test_qwen",
    context_summary_text="Code analysis: Found SQL injection vulnerability in login function",
    semantic_tags={"domain": "security", "severity": "critical"},
    cascade_phase="investigate"
)
provider.save_snapshot(snapshot1)

print(f"✅ Created snapshot: {snapshot1.snapshot_id}")
print(f"   Compression: {snapshot1.compression_ratio:.1%}")
print(f"   Reliability: {snapshot1.estimate_memory_reliability():.1%}")

# Transfer to MiniMax
registry = get_registry()
minimax = registry.get('minimax')()

payload = AdapterPayload(
    system="You are a security expert",
    state_summary="Security analysis",
    user_query="Continue the security analysis and provide recommendations",
    epistemic_snapshot=snapshot1,
    context_level="standard"
)

token_meta = {}
result = minimax.call(payload, token_meta)

print(f"\n✅ Transfer to MiniMax complete")
print(f"   Transfer count: {snapshot1.transfer_count}")
print(f"   Reliability after transfer: {snapshot1.estimate_memory_reliability():.1%}")
print(f"   Response: {result['content'][:100]}...")
```

**Expected:**
- ✅ Snapshot created successfully
- ✅ Transfer count increments to 1
- ✅ Reliability drops by ~3% (90% → 87%)
- ✅ MiniMax receives context and continues analysis
- ✅ Response is coherent with original context

#### **3b. Multi-Hop Transfer Chain**
```python
"""
Test 5-hop transfer: Qwen → MiniMax → Gemini → Copilot(Claude) → OpenRouter
"""

# Continue from previous test...
# Transfer 2: MiniMax → Gemini
snapshot2 = provider.create_snapshot_from_session("test_minimax")
gemini = registry.get('gemini')()
payload2 = AdapterPayload(
    system="You are a security expert",
    state_summary="Security recommendations",
    user_query="Review the recommendations and add testing strategies",
    epistemic_snapshot=snapshot2,
    context_level="standard"
)
result2 = gemini.call(payload2, {})

# Transfer 3: Gemini → Copilot (Claude Sonnet)
snapshot3 = provider.create_snapshot_from_session("test_gemini")
copilot = registry.get('copilot')(model='claude-sonnet-4')
payload3 = AdapterPayload(
    system="You are a security expert",
    state_summary="Testing strategies",
    user_query="Provide implementation guidance",
    epistemic_snapshot=snapshot3,
    context_level="full"
)
result3 = copilot.call(payload3, {})

# Transfer 4: Copilot → OpenRouter
snapshot4 = provider.create_snapshot_from_session("test_copilot")
openrouter = registry.get('openrouter')()
payload4 = AdapterPayload(
    system="You are a security expert",
    state_summary="Implementation guidance",
    user_query="Finalize the security remediation plan",
    epistemic_snapshot=snapshot4,
    context_level="full"
)
result4 = openrouter.call(payload4, {})

print(f"\n✅ 4-hop transfer complete")
print(f"   Transfer count: {snapshot4.transfer_count}")
print(f"   Reliability: {snapshot4.estimate_memory_reliability():.1%}")
print(f"   Should refresh: {snapshot4.should_refresh()}")
```

**Expected:**
- ✅ All 4 hops complete successfully
- ✅ Transfer count = 4
- ✅ Reliability ~78% (90% - 3%*4 = 78%)
- ✅ Context maintained across all 4 AIs
- ✅ Final response coherent with original task

---

### **Test 4: Cross-Vendor Comparison** (15 min)

**Goal:** Compare same model across different providers

#### **Test: Claude 3.5 Sonnet Comparison**
```bash
# Same model, different providers
# 1. Rovodev Claude
python3 -m empirica.cli decision "Explain quantum entanglement in 50 words" --adapter rovodev --model claude-3-5-sonnet-20241022

# 2. OpenRouter Claude
python3 -m empirica.cli decision "Explain quantum entanglement in 50 words" --adapter openrouter --model anthropic/claude-3.5-sonnet

# 3. Copilot Claude
python3 -m empirica.cli decision "Explain quantum entanglement in 50 words" --adapter copilot --model claude-sonnet-4
```

**Analysis:**
- Compare response quality
- Compare token usage
- Compare latency
- Document any differences

**Expected:**
- ✅ Responses should be similar (same underlying model)
- ✅ Small variations acceptable
- ✅ All should understand the prompt correctly

---

### **Test 5: ModalitySwitcher Routing** (10 min)

**Goal:** Test intelligent adapter selection

```python
"""
Test ModalitySwitcher routing decisions
"""
from empirica.plugins.modality_switcher import ModalitySwitcher

switcher = ModalitySwitcher()

# Test routing decisions for different scenarios
test_cases = [
    {
        "task": "Write Python code to parse JSON",
        "expected_adapter": "qwen",  # Code-specialized
        "reason": "Code generation task"
    },
    {
        "task": "Analyze complex reasoning patterns",
        "expected_adapter": "rovodev",  # Claude = reasoning
        "reason": "Complex reasoning task"
    },
    {
        "task": "Quick factual query: What is 2+2?",
        "expected_adapter": "gemini",  # Fast, free tier
        "reason": "Simple factual query"
    }
]

for test in test_cases:
    route = switcher.route_task(test["task"])
    print(f"Task: {test['task']}")
    print(f"  Routed to: {route['adapter']}")
    print(f"  Expected: {test['expected_adapter']}")
    print(f"  Match: {'✅' if route['adapter'] == test['expected_adapter'] else '⚠️'}")
    print(f"  Reason: {route.get('reason', 'N/A')}")
    print()
```

**Expected:**
- ✅ Routing decisions are logical
- ✅ Different adapters selected for different task types
- ✅ Routing reasons make sense

---

## 📊 Quality Metrics to Track

### **For Each Test:**
1. **Success Rate:** % of tests passing
2. **Token Usage:** Average tokens per request
3. **Latency:** Average response time
4. **Reliability Degradation:** Actual vs expected (3% per hop)
5. **Error Rate:** Failures per adapter

### **Comparison Metrics:**
| Adapter | Avg Tokens | Avg Latency | Error Rate | Cost/1k |
|---------|------------|-------------|------------|---------|
| Qwen | ? | ? | ? | $0.001 |
| MiniMax | ? | ? | ? | $0.0015 |
| Gemini | ? | ? | ? | $0.00 |
| ... | ... | ... | ... | ... |

---

## 🐛 Known Issues to Watch For

1. **Gemini query param auth** - Different auth method
2. **Copilot CLI** - Subprocess vs HTTP
3. **MiniMax group_id** - Extra parameter needed?
4. **OpenRouter rate limits** - May need delays
5. **Token estimation** - CLI adapters may not have exact counts

---

## ✅ Success Criteria

### **Functional:**
- [ ] All 7 adapters work with credentials.yaml
- [ ] All 15+ models accessible
- [ ] Model selection works for all adapters
- [ ] Snapshot transfers work cross-adapter
- [ ] Multi-hop transfers maintain quality
- [ ] ModalitySwitcher routing works

### **Quality:**
- [ ] Success rate >90% across all tests
- [ ] Reliability degradation ~3% per hop
- [ ] No critical errors
- [ ] Token tracking works

### **Performance:**
- [ ] Average latency <10 seconds per request
- [ ] No timeout errors
- [ ] Acceptable token usage

---

## 📦 Deliverables

1. **Test Results Matrix** - Success/failure for each test
2. **Quality Metrics** - Token usage, latency, reliability
3. **Comparison Analysis** - Cross-vendor model comparison
4. **Issue Log** - Any failures or unexpected behaviors
5. **Completion Report** - `MODALITY_SWITCHER_TEST_RESULTS.md`

---

## 🚀 Execution Plan

### **Parallel Execution:**

**Copilot CLI Claude:**
1. Run Tests 1-2 (Basic + Model Selection) - 25 min
2. Run Test 3a (Simple Transfers) - 10 min
3. Document results

**Rovodev Claude:**
1. Run Test 3b (Multi-Hop) - MiniMax focus - 15 min
2. Run Test 4 (Cross-Vendor) - 15 min
3. Document results

**Both:**
1. Run Test 5 (ModalitySwitcher) together - 10 min
2. Consolidate results
3. Create final report

**Total:** ~60 minutes (parallel)

---

## 📝 Test Script Template

```bash
#!/bin/bash
# modality_switcher_test.sh

echo "=========================================="
echo "  MODALITY SWITCHER COMPREHENSIVE TEST"
echo "=========================================="

# Test 1: Basic Functionality
echo "\nTest 1: Basic Adapter Functionality"
for adapter in qwen minimax rovodev gemini qodo openrouter copilot; do
    echo "\nTesting $adapter..."
    python3 -m empirica.cli decision "Say hello in 10 words" --adapter $adapter || echo "❌ FAILED: $adapter"
done

# Test 2: Model Selection
echo "\n\nTest 2: Model Selection"
python3 -m empirica.cli decision "test" --adapter qwen --model qwen-coder-turbo || echo "❌ FAILED: qwen model selection"
python3 -m empirica.cli decision "test" --adapter copilot --model gpt-5 || echo "❌ FAILED: copilot model selection"

# Test 3: Snapshot Transfers
echo "\n\nTest 3: Snapshot Transfers"
python3 test_snapshot_transfers.py || echo "❌ FAILED: snapshot transfers"

echo "\n\n=========================================="
echo "  TEST COMPLETE"
echo "=========================================="
```

---

**Status:** Ready to execute after adapter updates complete
**Assigned to:** Copilot CLI Claude + Rovodev Claude
**Coordination:** Run tests in parallel, share results

**Let's test all 15+ models!** 🚀
