# Handoff to Qwen - Validation & Testing Tasks

**Date:** 2025-11-14  
**From:** Claude (Co-lead Dev)  
**To:** Qwen (Validation Agent)  
**Session Coordination:** Via git commits + epistemic state  
**Estimated Total Time:** ~6-8 hours

---

## 🎯 Your Role

You're the **validation specialist** - your job is to verify that everything works correctly through systematic testing. You don't implement new features, you prove existing features work (or find bugs).

**Key Principle:** Test thoroughly, document findings, be skeptical. If something claims to work, prove it. If you find issues, document them clearly with reproduction steps.

---

## 📋 Task List (Priority Order)

### Task 1: Validate llm_callback with Real LLM ⚠️ HIGH PRIORITY
**Time:** ~2-3 hours  
**Impact:** Core feature validation

**Goal:** Prove that self-referential goal generation works with a real AI, not just mocks.

#### Setup
```python
# You'll need access to an LLM API (OpenAI, Anthropic, or local model)
# Example with OpenAI:

import openai
import os

def real_llm_callback(prompt: str) -> str:
    """Real LLM callback using OpenAI API"""
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a goal generation assistant for an AI agent."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    return response.choices[0].message.content
```

#### Test 1.1: Basic Goal Generation
```python
from empirica.bootstraps import bootstrap_metacognition

# Bootstrap with real LLM
components = bootstrap_metacognition(
    ai_id="qwen-validation",
    level="minimal",
    llm_callback=real_llm_callback
)

# Test goal generation
orchestrator = components['canonical_goal_orchestrator']

# Check configuration
assert orchestrator.use_placeholder == False, "Should be in AI mode"
assert orchestrator.llm_callback is not None, "Callback should be set"

print("✅ Bootstrap with real LLM successful")
```

#### Test 1.2: Generate Goals in Real Scenario
```python
# Simulate a real epistemic assessment
from empirica.core.canonical.canonical_epistemic_assessment import create_epistemic_assessment

assessment = create_epistemic_assessment()

# Create test epistemic state
test_state = {
    "engagement": 0.85,
    "know": 0.60,  # Low knowledge - should trigger learning goals
    "do": 0.75,
    "context": 0.70,
    "clarity": 0.80,
    "overall_confidence": 0.70
}

# Generate goals using real LLM
goals = orchestrator.generate_goals(
    conversation_context="I need to implement a new feature but I'm not sure about the architecture patterns to use.",
    epistemic_assessment=test_state
)

# Validate goals
print("\n📋 Generated Goals:")
for i, goal in enumerate(goals, 1):
    print(f"\n{i}. {goal.get('goal', 'N/A')}")
    print(f"   Priority: {goal.get('priority', 'N/A')}")
    print(f"   Type: {goal.get('type', 'N/A')}")
    print(f"   Reasoning: {goal.get('reasoning', 'N/A')[:100]}...")

# Assertions
assert len(goals) > 0, "Should generate at least one goal"
assert all('goal' in g for g in goals), "All goals should have 'goal' field"
assert all('reasoning' in g for g in goals), "All goals should have 'reasoning' field"

print("\n✅ Real LLM goal generation successful")
```

#### Test 1.3: Compare LLM vs Threshold Goals
```python
# Generate goals with LLM
llm_goals = orchestrator_llm.generate_goals(context, state)

# Generate goals with threshold mode
orchestrator_threshold = create_goal_orchestrator(use_placeholder=True)
threshold_goals = orchestrator_threshold.generate_goals(context, state)

# Compare
print("\n📊 Comparison: LLM vs Threshold Goals")
print(f"LLM goals: {len(llm_goals)}")
print(f"Threshold goals: {len(threshold_goals)}")
print(f"\nLLM goal types: {[g['type'] for g in llm_goals]}")
print(f"Threshold goal types: {[g['type'] for g in threshold_goals]}")

# Analysis
print("\n📝 Analysis:")
print("- Do LLM goals show more context awareness?")
print("- Are LLM goals more specific to the situation?")
print("- Do threshold goals follow predictable patterns?")

# Document findings in report
```

#### Test 1.4: Performance Measurement
```python
import time

# Measure LLM mode
start = time.time()
llm_goals = orchestrator_llm.generate_goals(context, state)
llm_time = time.time() - start

# Measure threshold mode
start = time.time()
threshold_goals = orchestrator_threshold.generate_goals(context, state)
threshold_time = time.time() - start

print(f"\n⏱️  Performance:")
print(f"LLM mode: {llm_time:.2f}s")
print(f"Threshold mode: {threshold_time:.4f}s")
print(f"Difference: {llm_time / threshold_time:.0f}x slower")

# Acceptability: LLM should be <5s for goal generation
assert llm_time < 5.0, f"LLM mode too slow: {llm_time:.2f}s"
print("✅ Performance acceptable")
```

#### Deliverable
**File:** `VALIDATION_LLM_CALLBACK.md`

**Contents:**
```markdown
# llm_callback Validation Report

**Validator:** Qwen
**Date:** YYYY-MM-DD
**LLM Used:** [OpenAI GPT-4 / Anthropic Claude / Local model]

## Test Results

### Test 1.1: Basic Goal Generation
**Status:** ✅ PASS / ❌ FAIL
**Details:** ...

### Test 1.2: Real Scenario
**Status:** ✅ PASS / ❌ FAIL
**Generated Goals:** [list goals]
**Quality Assessment:** [your analysis]

### Test 1.3: LLM vs Threshold Comparison
**Findings:** [detailed comparison]
**Advantages of LLM mode:** ...
**Disadvantages of LLM mode:** ...

### Test 1.4: Performance
**LLM mode:** X.XX seconds
**Threshold mode:** X.XX seconds
**Acceptable:** ✅ YES / ❌ NO

## Issues Found
[List any bugs, unexpected behavior, or concerns]

## Recommendations
[Your suggestions for improvements]
```

---

### Task 2: Investigation Strategies Hands-On Testing ⚠️ HIGH PRIORITY
**Time:** ~2 hours  
**Impact:** Validates investigation framework

**Goal:** Prove that investigation strategies actually work, not just exist.

#### Discovery Phase
```bash
# Find all investigation strategies
cd /home/yogapad/empirical-ai/empirica
find empirica/investigation -name "*.py" -type f

# Check investigation_strategy.py
cat empirica/core/metacognitive_cascade/investigation_strategy.py
```

#### Test 2.1: CodeAnalysisStrategy
```python
# Test code analysis strategy
from empirica.investigation.code_analysis_strategy import CodeAnalysisStrategy

strategy = CodeAnalysisStrategy()

# Create test context
context = {
    "task": "Find all uses of heuristics in the codebase",
    "files": ["empirica/core/canonical/canonical_goal_orchestrator.py"],
    "search_pattern": "if.*<.*:"
}

# Plan investigation
investigation_plan = strategy.plan_investigation(context)

print("📋 Investigation Plan:")
for step in investigation_plan:
    print(f"  - {step['action']}: {step['description']}")

# Execute investigation
results = []
for step in investigation_plan:
    result = strategy.execute_step(step)
    results.append(result)
    print(f"\n✅ Step complete: {step['action']}")
    print(f"   Result: {result.get('summary', 'N/A')}")

# Validate
assert len(investigation_plan) > 0, "Should generate investigation steps"
assert len(results) == len(investigation_plan), "Should execute all steps"
print("\n✅ CodeAnalysisStrategy works")
```

#### Test 2.2: ResearchStrategy
```python
# Test research strategy
from empirica.investigation.research_strategy import ResearchStrategy

strategy = ResearchStrategy()

context = {
    "task": "Understand how goal orchestrators work in AI systems",
    "knowledge_gap": "self-referential goal generation",
    "current_knowledge": ["goal orchestrator exists", "has llm_callback parameter"]
}

# Plan research
research_plan = strategy.plan_investigation(context)

print("📋 Research Plan:")
for step in research_plan:
    print(f"  - {step['action']}: {step['description']}")

# Execute (if possible)
# Note: Research strategy might require external resources
# Document what it attempts to do
```

#### Test 2.3: Strategy Selection
```python
# Test that correct strategy is selected for context
from empirica.core.metacognitive_cascade.investigation_plugin import select_investigation_strategy

# Code-focused context
code_context = {"task": "analyze codebase", "files": ["file.py"]}
strategy = select_investigation_strategy(code_context)
assert strategy.__class__.__name__ == "CodeAnalysisStrategy"

# Research-focused context
research_context = {"task": "understand concept", "knowledge_gap": "topic"}
strategy = select_investigation_strategy(research_context)
assert strategy.__class__.__name__ == "ResearchStrategy"

print("✅ Strategy selection works correctly")
```

#### Deliverable
**File:** `VALIDATION_INVESTIGATION_STRATEGIES.md`

**Contents:**
```markdown
# Investigation Strategies Validation Report

**Validator:** Qwen
**Date:** YYYY-MM-DD

## Strategies Found
- [ ] CodeAnalysisStrategy
- [ ] ResearchStrategy
- [ ] CollaborativeStrategy
- [ ] GeneralStrategy
- [ ] MedicalStrategy (domain-specific)

## Test Results

### CodeAnalysisStrategy
**Status:** ✅ PASS / ❌ FAIL
**Test:** [describe what you tested]
**Result:** [what happened]
**Quality:** [analysis of strategy effectiveness]

### ResearchStrategy
**Status:** ✅ PASS / ❌ FAIL
**Details:** ...

### Strategy Selection
**Status:** ✅ PASS / ❌ FAIL
**Details:** ...

## Issues Found
[List any bugs or problems]

## Usability Assessment
- Are strategies easy to use?
- Is documentation clear?
- Do they produce useful results?

## Recommendations
[Suggestions for improvement]
```

---

### Task 3: Full CASCADE Integration Test ⚠️ HIGH PRIORITY
**Time:** ~2 hours  
**Impact:** Validates complete workflow

**Goal:** Execute a complete CASCADE with AI-powered goals and verify all phases work together.

#### Test 3.1: Complete CASCADE Flow
```python
from empirica.bootstraps import bootstrap_metacognition

# Start with Empirica workflow
components = bootstrap_metacognition(
    ai_id="qwen-cascade-test",
    level="minimal",
    llm_callback=real_llm_callback  # Use real LLM
)

# PHASE 1: PREFLIGHT
from empirica.cli import execute_preflight

preflight_result = execute_preflight(
    session_id=components['session_id'],
    prompt="Test task: Validate a feature in the codebase"
)

print("✅ PREFLIGHT complete")
print(f"   Assessment ID: {preflight_result['assessment_id']}")

# Submit assessment
from empirica.cli import submit_preflight_assessment

submit_result = submit_preflight_assessment(
    session_id=components['session_id'],
    vectors={
        "engagement": {"score": 0.9, "rationale": "...", "evidence": "..."},
        # ... all vectors
    },
    reasoning="..."
)

print("✅ PREFLIGHT assessment submitted")

# PHASE 2: INVESTIGATE (use investigation strategy)
# [investigation work here]

# PHASE 3: CHECK
from empirica.cli import execute_check

check_result = execute_check(
    session_id=components['session_id'],
    findings=["Finding 1", "Finding 2"],
    remaining_unknowns=["Unknown 1"],
    confidence_to_proceed=0.85
)

# Submit CHECK
submit_check_assessment(...)

print("✅ CHECK phase complete")

# PHASE 4: ACT (with AI-generated goals)
goals = components['canonical_goal_orchestrator'].generate_goals(
    conversation_context="...",
    epistemic_assessment=...
)

print(f"✅ Generated {len(goals)} AI-powered goals")
# [Act on goals]

# PHASE 5: POSTFLIGHT
from empirica.cli import execute_postflight

postflight_result = execute_postflight(
    session_id=components['session_id'],
    task_summary="..."
)

# Submit POSTFLIGHT
submit_postflight_assessment(...)

print("✅ POSTFLIGHT complete")

# Verify complete flow in database
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()
session = db.get_session(components['session_id'])

assert session is not None
assert session.preflight_count >= 1
assert session.check_count >= 1
assert session.postflight_count >= 1

print("\n🎉 Complete CASCADE flow validated!")
```

#### Test 3.2: Calibration Analysis
```python
# Get calibration report
from empirica.cli import get_calibration_report

calibration = get_calibration_report(session_id=components['session_id'])

print("\n📊 Calibration Report:")
print(f"PREFLIGHT confidence: {calibration['preflight']['overall_confidence']}")
print(f"POSTFLIGHT confidence: {calibration['postflight']['overall_confidence']}")
print(f"Delta: {calibration['delta']}")

# Verify learning occurred (or stayed stable if already high)
assert 'preflight' in calibration
assert 'postflight' in calibration
print("✅ Calibration tracking works")
```

#### Deliverable
**File:** `VALIDATION_CASCADE_INTEGRATION.md`

---

### Task 4: Performance & Stress Testing 🔥 MEDIUM PRIORITY
**Time:** ~1-2 hours  
**Impact:** Validates production readiness

#### Test 4.1: Multiple Concurrent Sessions
```python
import threading

def create_session(ai_id: str):
    """Create session in thread"""
    components = bootstrap_metacognition(
        ai_id=f"stress-test-{ai_id}",
        level="minimal"
    )
    return components

# Create 10 concurrent sessions
threads = []
for i in range(10):
    t = threading.Thread(target=create_session, args=(str(i),))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("✅ 10 concurrent sessions created")

# Verify all in database
db = SessionDatabase()
sessions = db.list_sessions(limit=10)
assert len(sessions) >= 10
print("✅ All sessions persisted")
```

#### Test 4.2: Large Data Handling
```python
# Test with many cascades
for i in range(50):
    create_cascade(session_id=..., task=f"Task {i}", goal_json="{}")

# Test with many assessments
for i in range(20):
    submit_preflight_assessment(...)
    submit_check_assessment(...)

# Verify database performance
import time
start = time.time()
sessions = db.list_sessions(limit=100)
query_time = time.time() - start

print(f"Query time for 100 sessions: {query_time:.4f}s")
assert query_time < 1.0, "Database queries should be fast"
print("✅ Database performance acceptable")
```

#### Test 4.3: Memory Usage
```python
import psutil
import os

process = psutil.Process(os.getpid())

# Baseline memory
baseline = process.memory_info().rss / 1024 / 1024  # MB

# Create many sessions
for i in range(100):
    bootstrap_metacognition(f"memory-test-{i}", "minimal")

# Check memory
final = process.memory_info().rss / 1024 / 1024  # MB
increase = final - baseline

print(f"\n💾 Memory Usage:")
print(f"Baseline: {baseline:.1f} MB")
print(f"After 100 sessions: {final:.1f} MB")
print(f"Increase: {increase:.1f} MB")
print(f"Per session: {increase / 100:.2f} MB")

# Memory should not leak excessively
assert increase < 500, f"Memory increase too high: {increase:.1f} MB"
print("✅ Memory usage acceptable")
```

#### Deliverable
**File:** `VALIDATION_PERFORMANCE.md`

---

### Task 5: Cross-Agent Coordination Testing 🤝 MEDIUM PRIORITY
**Time:** ~1 hour  
**Impact:** Validates multi-agent scenarios

#### Test 5.1: Session Resumption
```python
# Create session as one agent
components1 = bootstrap_metacognition(
    ai_id="agent-alpha",
    level="minimal"
)
session_id = components1['session_id']

# Do some work
execute_preflight(session_id, "Task 1")
submit_preflight_assessment(...)

# Simulate different agent resuming
from empirica.cli import resume_previous_session

resume_data = resume_previous_session(
    ai_id="agent-alpha",
    resume_mode="last",
    detail_level="detailed"
)

print("📋 Resumed Session:")
print(f"   Session ID: {resume_data['session_id']}")
print(f"   Task: {resume_data['task']}")
print(f"   Last confidence: {resume_data['last_confidence']}")

# Verify data matches
assert resume_data['session_id'] == session_id
assert 'epistemic_state' in resume_data
print("✅ Session resumption works")
```

#### Test 5.2: Concurrent Agent Work
```python
# Agent 1 creates session
session1 = bootstrap_metacognition("agent-1", "minimal")

# Agent 2 creates different session
session2 = bootstrap_metacognition("agent-2", "minimal")

# Both work simultaneously
execute_preflight(session1['session_id'], "Agent 1 task")
execute_preflight(session2['session_id'], "Agent 2 task")

# Verify no conflicts
state1 = get_epistemic_state(session1['session_id'])
state2 = get_epistemic_state(session2['session_id'])

assert state1 != state2, "Sessions should be independent"
print("✅ Concurrent agents work independently")
```

#### Deliverable
**File:** `VALIDATION_MULTI_AGENT.md`

---

## 📊 Progress Tracking

Create: `QWEN_VALIDATION_PROGRESS.md`

```markdown
# Qwen Validation Progress Report

**Started:** YYYY-MM-DD
**Status:** In Progress

## Completed Tasks
- [ ] Task 1: Validate llm_callback with real LLM
  - [ ] 1.1: Basic goal generation
  - [ ] 1.2: Real scenario testing
  - [ ] 1.3: LLM vs Threshold comparison
  - [ ] 1.4: Performance measurement
- [ ] Task 2: Investigation strategies testing
  - [ ] 2.1: CodeAnalysisStrategy
  - [ ] 2.2: ResearchStrategy
  - [ ] 2.3: Strategy selection
- [ ] Task 3: Full CASCADE integration
  - [ ] 3.1: Complete flow
  - [ ] 3.2: Calibration analysis
- [ ] Task 4: Performance testing
  - [ ] 4.1: Concurrent sessions
  - [ ] 4.2: Large data handling
  - [ ] 4.3: Memory usage
- [ ] Task 5: Multi-agent coordination
  - [ ] 5.1: Session resumption
  - [ ] 5.2: Concurrent work

## Issues Found
[List all bugs, unexpected behavior, or concerns]

## Performance Metrics
- LLM goal generation: X.XX seconds
- Database queries: X.XX seconds
- Memory per session: X.XX MB

## Quality Assessment
[Overall assessment of system quality]

## Recommendations
[Your suggestions for improvements]
```

---

## 🔄 Coordination Protocol

### Use Empirica for Your Work
```python
# Bootstrap your validation session
components = bootstrap_metacognition(
    ai_id="qwen-validator",
    level="minimal",
    llm_callback=your_llm_callback  # Use yourself!
)

# Track your work through CASCADE
execute_preflight(session_id, "Validate llm_callback feature")
# ... do validation work ...
execute_postflight(session_id, "Validation complete: found 2 issues")
```

### Git Workflow
```bash
# Pull latest
git pull origin master

# Commit validation reports
git add VALIDATION_*.md QWEN_VALIDATION_PROGRESS.md
git commit -m "test: llm_callback validation complete - all tests passing"

# Push frequently
git push origin master
```

### Commit Message Format
- `test:` - Test results and validation reports
- `docs:` - Documentation of findings
- `fix:` - If you fix any bugs you find (coordinate with co-leads first)

---

## ✅ Success Criteria

**You're done when:**
1. ✅ llm_callback validated with real LLM (VALIDATION_LLM_CALLBACK.md)
2. ✅ Investigation strategies tested hands-on (VALIDATION_INVESTIGATION_STRATEGIES.md)
3. ✅ Full CASCADE integration verified (VALIDATION_CASCADE_INTEGRATION.md)
4. ✅ Performance metrics documented (VALIDATION_PERFORMANCE.md)
5. ✅ Multi-agent coordination tested (VALIDATION_MULTI_AGENT.md)
6. ✅ All issues documented in progress report
7. ✅ Recommendations provided for improvements
8. ✅ All commits pushed to git

**Quality Bar:**
- Thorough testing (not just happy path)
- Clear bug reports with reproduction steps
- Performance metrics documented
- Honest assessment of quality
- Actionable recommendations

---

## 🆘 Getting Help

**If you find critical bugs:**
1. Document in progress report immediately
2. Create clear reproduction steps
3. Assess impact (blocker, high, medium, low)
4. Note in git commit message

**Resources:**
- `PHASE2_SYSTEM_VALIDATION_FINDINGS.md` - What co-leads found
- `PHASE2_REFACTOR_COMPLETE.md` - Implementation details
- `HANDOFF_COPILOT_CLAUDE.md` - What other agent is doing

---

**Your validation work is critical - you're the quality gatekeeper! 🛡️**

**Estimated completion:** 1-2 days of focused work  
**Start with:** Task 1 (llm_callback validation) - most important feature
