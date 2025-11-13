# Epistemic Reasoning Benchmark (ERB)

**Version:** 1.0  
**Purpose:** Evaluate epistemic reasoning capabilities across AI models  
**Status:** Production-ready benchmarking tool

---

## 🎯 What is ERB?

ERB is a **13-vector assessment system** designed to measure how well AI systems reason about their own knowledge, uncertainty, and cognitive limitations.

**Use ERB to:**
- ✅ Benchmark different AI models (GPT-4, Claude, Gemini, etc.)
- ✅ Evaluate epistemic reasoning capabilities
- ✅ Compare performance across models
- ✅ Validate AI capabilities before production deployment
- ✅ Research AI metacognition and self-awareness

---

## 📊 ERB vs UVL: Two Systems for Different Purposes

### ERB (13 vectors) - BENCHMARKING 🔬
**Location:** `empirica.cognitive_benchmarking.erb`  
**Purpose:** Evaluate and compare AI reasoning capabilities  
**Use when:** Testing models, research, pre-production validation

### UVL (12 vectors) - PRODUCTION TRACKING ✅
**Location:** `empirica.core.canonical`  
**Purpose:** Real-time epistemic tracking during production  
**Use when:** Using MCP/CLI for actual work with AI

**Both systems use genuine AI self-assessment. NO HEURISTICS.**

---

## 🔢 The 13 ERB Vectors

Each vector measures a specific aspect of epistemic reasoning:

| Vector | Measures | Score Range |
|--------|----------|-------------|
| **epistemic_humility** | Recognizes limits of knowledge | 0.0 - 1.0 |
| **cognitive_flexibility** | Adapts reasoning approaches | 0.0 - 1.0 |
| **metacognitive_awareness** | Monitors own thinking processes | 0.0 - 1.0 |
| **uncertainty_acknowledgment** | Explicitly states unknowns | 0.0 - 1.0 |
| **knowledge_boundary_recognition** | Knows what it doesn't know | 0.0 - 1.0 |
| **recursive_self_improvement** | Learns from experience | 0.0 - 1.0 |
| **contextual_sensitivity** | Adapts to different contexts | 0.0 - 1.0 |
| **assumption_tracking** | Identifies underlying assumptions | 0.0 - 1.0 |
| **confidence_calibration** | Accurate confidence levels | 0.0 - 1.0 |
| **error_detection_sensitivity** | Catches own mistakes | 0.0 - 1.0 |
| **ambiguity_tolerance** | Handles unclear situations | 0.0 - 1.0 |
| **evidence_based_reasoning** | Grounds reasoning in evidence | 0.0 - 1.0 |
| **explicit_uncertainty** | Quantifies uncertainty levels | 0.0 - 1.0 |

---

## 🚀 Quick Start

### Using ERB to Benchmark a Model

```python
from empirica.cognitive_benchmarking.erb import PreflightAssessor, PostflightAssessor

# Create assessor
preflight = PreflightAssessor()

# Run preflight benchmark
task = "Solve this complex reasoning problem: [problem description]"
result = await preflight.assess(task, {})

# Get ERB scores
print(f"Epistemic Humility: {result.epistemic_humility:.2f}")
print(f"Cognitive Flexibility: {result.cognitive_flexibility:.2f}")
print(f"Uncertainty Acknowledgment: {result.uncertainty_acknowledgment:.2f}")
# ... all 13 vectors
```

### Running Full Preflight → Postflight Benchmark

```python
from empirica.cognitive_benchmarking.erb import (
    PreflightAssessor,
    PostflightAssessor
)

# Preflight assessment
preflight = PreflightAssessor()
pre_result = await preflight.assess(task, {})

# [AI performs task]

# Postflight assessment
postflight = PostflightAssessor()
post_result = await postflight.assess(task, {"phase": "postflight"})

# Compare scores to measure learning
epistemic_delta = (
    post_result.epistemic_humility - pre_result.epistemic_humility
)
print(f"Epistemic Humility changed by: {epistemic_delta:+.2f}")
```

---

## 📚 Documentation

### Complete Guides:
- **`INDEX.md`** - Complete ERB documentation and API reference
- **`MANUAL_TESTING_GUIDE.md`** - Step-by-step testing instructions
- **`CLAUDE_SELF_TEST_EXAMPLE.md`** - Example self-test walkthrough
- **`preflight_postflight_design.md`** - Design philosophy
- **`READY_FOR_TESTING.md`** - Testing readiness checklist

### Parent Folder:
- **`../README.md`** - Overall cognitive benchmarking documentation
- **`../SUMMARY.md`** - Summary of benchmarking results
- **`../REAL_RESULTS_OCT_2025.md`** - Real-world test results

---

## 🧪 Running Benchmarks

### Option 1: Manual Testing (Recommended for Learning)

See `MANUAL_TESTING_GUIDE.md` for detailed instructions.

```bash
# Run ERB real model runner
python3 empirica/cognitive_benchmarking/erb/erb_real_model_runner.py
```

### Option 2: Programmatic Testing

```python
from empirica.cognitive_benchmarking.erb import PreflightAssessor
import asyncio

async def benchmark_model(model_name: str):
    assessor = PreflightAssessor()
    
    # Create test task
    task = "Analyze this code for security vulnerabilities..."
    
    # Run assessment
    result = await assessor.assess(task, {"model": model_name})
    
    # Return scores
    return {
        "model": model_name,
        "epistemic_humility": result.epistemic_humility,
        "cognitive_flexibility": result.cognitive_flexibility,
        # ... other vectors
    }

# Benchmark multiple models
models = ["gpt-4", "claude-3-opus", "gemini-pro"]
results = [asyncio.run(benchmark_model(m)) for m in models]
```

### Option 3: Using Comprehensive Test Suite

```python
from empirica.cognitive_benchmarking.erb import (
    comprehensive_epistemic_test_suite
)

# Run full ERB test suite
results = await comprehensive_epistemic_test_suite.run_all_tests()

# Analyze results
print(results.summary())
```

---

## 🔍 What ERB Measures

### Epistemic Reasoning Capabilities:

**Knowledge Management:**
- How well does the AI know what it knows?
- Can it recognize knowledge boundaries?
- Does it track assumptions?

**Uncertainty Handling:**
- Does it acknowledge uncertainty explicitly?
- Can it quantify confidence accurately?
- How does it handle ambiguity?

**Metacognition:**
- Is the AI aware of its thinking process?
- Can it detect its own errors?
- Does it improve from experience?

**Cognitive Flexibility:**
- Can it adapt reasoning approaches?
- Is it sensitive to context?
- Can it handle unexpected situations?

---

## ⚠️ Important: Genuine Assessment Only

ERB follows Empirica's core principle:

**NO HEURISTICS. NO KEYWORD MATCHING. NO CONFABULATION.**

All ERB assessments require:
- ✅ Genuine AI self-reflection
- ✅ Honest evaluation of capabilities
- ✅ Real reasoning, not pattern matching

ERB generates assessment prompts that the AI must genuinely respond to. There are no shortcuts or static baseline values.

---

## 📊 Example ERB Results

### GPT-4 (Example)
```
Epistemic Humility:           0.82  (High)
Cognitive Flexibility:         0.78  (High)
Metacognitive Awareness:       0.75  (High)
Uncertainty Acknowledgment:    0.80  (High)
Knowledge Boundary Recognition: 0.77  (High)
...
Overall ERB Score:             0.79  (Strong)
```

### Claude 3 Opus (Example)
```
Epistemic Humility:           0.85  (Very High)
Cognitive Flexibility:         0.80  (High)
Metacognitive Awareness:       0.82  (Very High)
Uncertainty Acknowledgment:    0.83  (Very High)
Knowledge Boundary Recognition: 0.81  (Very High)
...
Overall ERB Score:             0.82  (Very Strong)
```

See `../REAL_RESULTS_OCT_2025.md` for actual benchmark results.

---

## 🎓 When to Use ERB

### Use ERB When You Want To:
- ✅ Compare AI models for your use case
- ✅ Validate AI capabilities before deployment
- ✅ Research epistemic reasoning in AI
- ✅ Benchmark your own fine-tuned models
- ✅ Track improvements across model versions

### Use UVL (Production System) When You Want To:
- ✅ Track epistemic state during real tasks
- ✅ Integrate with MCP server or CLI
- ✅ Measure learning across sessions
- ✅ Production workflow tracking

**Both are valuable!** ERB for evaluation, UVL for production.

---

## 🔗 Integration with Empirica

ERB is part of Empirica's cognitive benchmarking suite but operates independently:

```
empirica/
├── core/canonical/
│   └── canonical_epistemic_assessment.py  (UVL - Production)
│
├── cognitive_benchmarking/
│   └── erb/  (ERB - Benchmarking)
│       ├── preflight_assessor.py
│       ├── postflight_assessor.py
│       └── ...
│
├── cli/  (Uses UVL)
└── mcp_local/  (Uses UVL)
```

Both systems share the philosophy but serve different purposes.

---

## 🤝 Contributing

ERB is actively developed. Contributions welcome:

- Report issues with specific model assessments
- Suggest new epistemic vectors
- Share benchmark results
- Improve assessment prompts

See `CONTRIBUTING.md` in repository root.

---

## 📝 Summary

**ERB = Epistemic Reasoning Benchmark**

- 🔢 13 vectors measuring epistemic reasoning
- 🔬 For benchmarking and evaluation
- ✅ Genuine AI self-assessment (NO HEURISTICS)
- 📊 Compare models and track improvements
- 🎯 Complementary to UVL production system

**Get Started:** See `INDEX.md` and `MANUAL_TESTING_GUIDE.md`

---

**Questions?** Check the documentation in this folder or the parent `cognitive_benchmarking/` folder.
