# Qwen's Test Creation Task - Empirica Coordination

**Role:** Create comprehensive test suite for Empirica's Canonical Core and CASCADE workflow  
**Coordinator:** Claude (Rovo Dev)  
**Using:** Empirica's epistemic assessment principles

---

## 🎯 Your Mission

Create 20-30 tests covering:
- **Layer 0:** Canonical Core (ReflexFrame, Assessor, Logger, Orchestrator)
- **Layer 1:** CASCADE Workflow (7 phases, ENGAGEMENT gate, investigation loops)

---

## 📚 Step 1: Initialize Empirica (RECOMMENDED)

### Option A: Bootstrap (Quick)
```bash
cd /home/yogapad/empirical-ai/empirica
source .venv-empirica/bin/activate
empirica bootstrap --ai-id qwen-test-creator
```

### Option B: Full Onboarding (15 min - Better understanding)
```bash
empirica onboard --ai-id qwen-test-creator
```

### Option C: Direct Start (If already familiar)
Skip to Step 2 and use epistemic principles intuitively.

**Recommendation:** If you haven't used Empirica before, do Option B (onboarding). It will teach you the principles you'll need for creating principled tests.

---

## 📖 Step 2: Read Architecture Documentation

**Essential reading:**
```bash
# Primary: Architectural overview for testing
cat tests/coordination/COMPREHENSIVE_TEST_ARCHITECTURE.md
```

**Optional but helpful:**
```bash
# Complete Empirica reference
cat docs/skills/SKILL.md

# Core architecture
cat docs/05_ARCHITECTURE.md

# AI quick start
cat docs/01_a_AI_AGENT_START.md
```

**Time:** 10-15 minutes to understand architecture

---

## 🧪 Step 3: Use Empirica for Test Creation

### Before Starting (PREFLIGHT):
```bash
# Assess your epistemic state
empirica preflight "Create comprehensive test suite for Empirica Layer 0 and Layer 1"
```

**Self-assess:**
- KNOW: Do I understand Empirica's architecture?
- DO: Can I create pytest tests following Empirica principles?
- CONTEXT: Do I have enough information about what to test?
- UNCERTAINTY: What am I uncertain about?

**If UNCERTAINTY > 0.70 or CONTEXT < 0.50:** INVESTIGATE first (read more docs)

---

## 📝 Step 4: Create Tests

### Test Organization:
```bash
# Create directories
mkdir -p tests/unit/canonical
mkdir -p tests/unit/cascade

# Start with Layer 0
cd tests/unit/canonical
```

### Test Priority Order:

**1. test_reflex_frame.py** (Foundation)
```python
"""Test Reflex Frame data structures and canonical weights."""

def test_vector_validation():
    """Vectors must be 0.0-1.0 range"""
    
def test_canonical_weights():
    """Foundation: 35%, Comprehension: 25%, Execution: 25%, Engagement: 15%"""
    
def test_engagement_gate():
    """ENGAGEMENT ≥ 0.60 required to proceed"""
```

**2. test_epistemic_assessor.py** (Critical!)
```python
"""Test Canonical Epistemic Assessor - LLM reasoning only."""

def test_llm_assessment():
    """Verify genuine LLM reasoning, not heuristics"""
    
def test_meta_prompt_generation():
    """Returns proper self-assessment prompt for AI"""
    
def test_json_parsing():
    """Parses structured assessment correctly"""
```

**3. test_reflex_logger.py** (Temporal Separation)
```python
"""Test Reflex Logger - external JSON logging."""

def test_temporal_separation():
    """Logs assessments externally to prevent recursion"""
    
def test_async_logging():
    """Async file I/O works correctly"""
```

**4. test_goal_orchestrator.py**
```python
"""Test Goal Orchestrator - LLM-based decomposition."""

def test_goal_decomposition():
    """Decomposes complex goals using LLM reasoning"""
```

### Then Layer 1 (CASCADE):

**5. tests/unit/cascade/test_engagement_gate.py** (CRITICAL!)
```python
"""Test ENGAGEMENT gate - must be ≥ 0.60 to proceed."""

def test_gate_blocks_low_engagement():
    """ENGAGEMENT < 0.60 → CLARIFY action"""
    
def test_gate_passes_high_engagement():
    """ENGAGEMENT ≥ 0.60 → Proceed to THINK"""
```

**6. test_preflight.py, test_think.py, test_check.py, test_postflight.py**
- Test each CASCADE phase individually
- Verify phase transitions
- Validate outputs

---

## 🎯 Test Principles (CRITICAL!)

### 1. NO HEURISTICS in your tests!
```python
# ❌ BAD - Pattern matching
assert "error" in result.lower()
assert len(response) > 100

# ✅ GOOD - Evidence-based
assert result.uses_genuine_reasoning == True
assert result.assessment.know >= 0.0 and result.assessment.know <= 1.0
```

### 2. Use Canonical Values
```python
# ✅ GOOD - From architecture
assert FOUNDATION_WEIGHT == 0.35
assert ENGAGEMENT_GATE_THRESHOLD == 0.60
assert ACTION_CONFIDENCE_THRESHOLD == 0.70
```

### 3. Validate Temporal Separation
```python
# ✅ GOOD - External state
reflex_logger = ReflexLogger()
assessment = reflex_logger.load_assessment(session_id)
assert assessment.vectors.know == expected_value
```

### 4. Test Calibration Logic
```python
# ✅ GOOD - Delta validation
delta = postflight_assessment - preflight_assessment
assert delta.know > 0  # Should learn
assert delta.uncertainty < 0  # Should reduce uncertainty
```

---

## 📊 Step 5: Self-Assessment During Work

**Every 5-10 tests, check in:**
```bash
# Quick self-reflection
empirica check "Test creation progress check"
```

**Ask yourself:**
- Am I following Empirica principles?
- Are my tests evidence-based?
- Am I avoiding heuristics?
- Do I need more architectural understanding?

**If CHECK shows low confidence:** INVESTIGATE more (read docs, review existing tests)

---

## ✅ Step 6: After Completion (POSTFLIGHT)

```bash
# Assess what you learned
empirica postflight "Test suite creation complete"
```

**Report:**
- What you learned about Empirica
- What tests you created
- Any gaps or uncertainties
- Calibration: Were you well-calibrated?

---

## 📋 Deliverables

**Expected output:**
- 20-30 test files in `tests/unit/canonical/` and `tests/unit/cascade/`
- All tests follow pytest conventions
- All tests follow Empirica principles (no heuristics)
- Tests are evidence-based and principled
- Good coverage of Layer 0 and Layer 1

**Test execution:**
```bash
# Run your tests
pytest tests/unit/canonical/ -v
pytest tests/unit/cascade/ -v

# With coverage
pytest tests/unit/canonical/ tests/unit/cascade/ --cov=empirica.core -v
```

---

## 🤝 Coordination

**Report to coordinator (Claude):**
- Progress updates every 5-10 tests
- Questions about architecture
- Decisions about test priorities
- Issues or blockers

**Format:**
```
Status: Created test_reflex_frame.py (4 tests)
Progress: 4/20 tests complete
Question: Should I test all 12 vectors or just foundation vectors?
```

---

## 🎯 Success Criteria

- [ ] 20-30 tests created
- [ ] Layer 0 fully covered (canonical core)
- [ ] Layer 1 key phases covered (CASCADE)
- [ ] All tests follow "no heuristics" principle
- [ ] Tests are evidence-based
- [ ] Tests validate calibration logic
- [ ] Good pytest coverage of `empirica/core/`

---

**Ready to start?**

1. Bootstrap/onboard if needed
2. Read architecture doc
3. Use Empirica preflight assessment
4. Create tests following principles
5. Use check/postflight to track progress

**Time estimate:** 1-2 hours for 20-30 quality tests

Good luck! 🚀
