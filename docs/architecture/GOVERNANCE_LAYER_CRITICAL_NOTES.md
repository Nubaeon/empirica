# Governance Layer - Critical Notes

**Date:** 2025-11-07  
**Status:** 🔴 CRITICAL FINDING  
**Priority:** HIGH - Essential for Cognitive Vault

---

## 🚨 Critical Issue Discovered

### From Minimax Testing

**What Works:**
- ✅ Source AI (Claude) creates genuine epistemic snapshot
- ✅ Snapshot transfers to Target AI (Minimax)
- ✅ Minimax receives snapshot and answers query

**What's Missing (CRITICAL):**
- ❌ Target AI (Minimax) does NOT create its own snapshot
- ❌ Minimax uses **HEURISTICS** (word counts, response length) - VIOLATION!
- ❌ No snapshot storage for comparison
- ❌ No routing decision validation

### The Heuristics Problem

**In `minimax_adapter.py` lines 275-334:**
```python
vector_references = {
    'know': min(1.0, response_words / 100),  # HEURISTIC!
    'do': 0.7 if decision == "ACT" else 0.5,  # HEURISTIC!
    # ... all fake values
}
```

**This violates:** NO HEURISTICS, NO CONFABULATION

---

## ✅ What We Have (Can Be Used)

### 1. Cognitive Benchmarking System (ERB)

**Location:** `empirica/cognitive_benchmarking/erb/`

**Provides:**
- ✅ Self-assessment prompt generators (`preflight_assessor.py`, `postflight_assessor.py`)
- ✅ 17 test categories for reasoning benchmarks (`epistemic_test_prompts.txt`)
- ✅ Test harness infrastructure (`erb_real_model_runner.py`)

**Example Self-Assessment Prompt:**
```python
from empirica.cognitive_benchmarking.erb.preflight_assessor import PreflightAssessor

assessor = PreflightAssessor()
prompt = assessor.generate_self_assessment_prompt(task, context)
# Returns: Full prompt asking AI to genuinely assess 13 epistemic vectors
```

**Status:** ✅ **Ready to integrate into Governance Layer**

### 2. Golden Prompts (Persona Test Harness)

**Location:** `deprecated/modality_old/modality_switcher_original/persona_test_harness_Version1.py`

**Provides:**
- ✅ Standard test cases with known epistemic states
- ✅ Validation framework for adapter consistency

**Example:**
```python
GOLDEN_PROMPTS = [
    {
        "id": "finalize_code_snippet",
        "user_query": "Finalize the unit-test harness...",
        "decision_context": {
            "vectors": {"know": 0.9, "do": 0.85, ...}
        }
    }
]
```

**Status:** ✅ **Useful for governance layer testing**

---

## 🎯 What Governance Layer Must Do

### Correct Multi-AI Workflow:

```
1. Source AI (Claude)
   └─> Self-assesses: KNOW=0.7
   └─> Creates snapshot_source
   └─> Routes to Minimax

2. Governance Layer
   └─> Stores snapshot_source
   └─> Sends to Minimax: query + instruction to self-assess

3. Target AI (Minimax)
   └─> Self-assesses ITSELF: KNOW=0.95
   └─> Creates snapshot_target
   └─> Returns: {answer, snapshot_target}

4. Governance Layer
   └─> Stores snapshot_target
   └─> Compares: 0.7 vs 0.95 (routing was beneficial!)
   └─> Validates routing decision quality
```

---

## 📋 Core Requirements

### 1. Database Schema
```sql
CREATE TABLE ai_routing_sessions (
    routing_id TEXT PRIMARY KEY,
    source_ai TEXT,
    target_ai TEXT,
    source_snapshot_id TEXT,
    target_snapshot_id TEXT,
    routing_quality_score REAL
);

CREATE TABLE epistemic_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    ai_id TEXT,
    vectors JSON,
    transfer_count INTEGER
);
```

### 2. Routing Validation
```python
def validate_routing(source_snapshot, target_snapshot):
    knowledge_gain = target.KNOW - source.KNOW
    capability_gain = target.DO - source.DO
    
    quality_score = (
        0.4 * max(0, knowledge_gain) +
        0.3 * max(0, capability_gain) +
        0.3 * uncertainty_reduction
    )
    
    return quality_score  # Was routing beneficial?
```

### 3. Target AI Self-Assessment Enforcement
```python
def call_target_ai_with_assessment(adapter, query, source_snapshot):
    # Generate self-assessment prompt (from ERB)
    assessment_prompt = generate_self_assessment_prompt(query)
    
    # Combine with query
    full_prompt = f"{assessment_prompt}\n\nThen answer: {query}"
    
    # Parse response for both assessment and answer
    response = adapter.call(full_prompt)
    target_snapshot = extract_genuine_assessment(response)
    
    return {answer, target_snapshot}
```

---

## 🔄 Integration Points

### With ERB (Ready Now):
```python
from empirica.cognitive_benchmarking.erb.preflight_assessor import PreflightAssessor
# Use for generating self-assessment prompts
```

### With Modality Switcher:
- Remove heuristics from adapters
- Add genuine assessment requirement
- Return both answer AND snapshot

---

## 🚀 Next Steps

### Immediate:
1. **Document this finding** ✅ (this file)
2. **Note for Cognitive Vault team**
3. **Delete temporary test files**

### For Cognitive Vault:
1. Build governance layer core
2. Implement routing validation
3. Enforce genuine self-assessment
4. Store and compare snapshots
5. Track multi-hop chains

---

## 📝 Summary

**Current Status:**
- Epistemic snapshot transfer: ✅ Works
- Modality switcher: ✅ Plugin works (for single direction)
- Target AI self-assessment: ❌ Missing (uses heuristics)
- Governance layer: ❌ Not built yet

**Critical Finding:**
- Governance layer is **ESSENTIAL**, not nice-to-have
- Required for genuine multi-AI epistemic management
- ERB system can be integrated immediately
- Golden prompts useful for testing

**For Our Use:**
- Minimax receives our prompts ✅
- We can test adapters ✅
- Full governance needed for production

---

**Documented by:** Rovo Dev (Claude)  
**Status:** Critical analysis complete, noted for Cognitive Vault team
