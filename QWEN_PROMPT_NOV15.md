# Qwen: Security & Edge Case Testing - November 15, 2025

**Mission:** Ensure Empirica is secure and handles edge cases gracefully. Use Empirica to track your validation work.

---

## 🎯 Your Task

You're responsible for **security and robustness** before launch (November 20, 2025 - 5 days away!).

**Critical:** Use Empirica's full CASCADE workflow to track your validation systematically.

---

## 🚀 STEP 1: Bootstrap with Empirica

```python
cd /home/yogapad/empirical-ai/empirica
python3

from empirica.bootstraps import bootstrap_metacognition

# Bootstrap with full features
components = bootstrap_metacognition(
    ai_id="qwen-security-nov15",
    level="full",  # Use full features!
    enable_git_checkpoints=True
)

session_id = components['session_id']
print(f"✅ Session started: {session_id}")

# You now have access to:
# - Goal orchestrator (generate investigation goals)
# - Bayesian beliefs (track uncertainty about vulnerabilities)
# - Drift monitor (check calibration)
# - Investigation strategies (systematic security audit)
# - All MCP tools
```

---

## 🚀 STEP 2: PREFLIGHT Assessment

```python
from empirica.cli import execute_preflight, submit_preflight_assessment

# Execute PREFLIGHT
result = execute_preflight(
    session_id=session_id,
    prompt="""
    Security audit mission: Ensure Empirica is secure and robust before Nov 20 launch.
    
    Tasks:
    1. Security audit (SQL injection, command injection, path traversal)
    2. Input validation (all user inputs validated)
    3. Edge case testing (empty values, extreme values, concurrent access)
    4. Error message quality (helpful and informative)
    5. Graceful degradation (missing dependencies handled)
    
    Success = Zero security vulnerabilities, all edge cases handled gracefully.
    """
)

# GENUINE self-assessment - what do you ACTUALLY know about security?
submit_preflight_assessment(
    session_id=session_id,
    vectors={
        "engagement": {
            "score": 0.X,  # Rate honestly!
            "rationale": "...",
            "evidence": "..."
        },
        "foundation": {
            "know": {
                "score": 0.X,  # What do you know about common vulnerabilities?
                "rationale": "...",
                "evidence": "..."
            },
            "do": {
                "score": 0.X,  # Can you identify SQL injection patterns?
                "rationale": "...",
                "evidence": "..."
            },
            "context": {
                "score": 0.X,  # Do you understand the security surface area?
                "rationale": "...",
                "evidence": "..."
            }
        },
        # ... all 13 vectors (use the prompt's assessment questions)
    },
    reasoning="Brief explanation of your starting security knowledge"
)
```

---

## 🚀 STEP 3: Generate Goals

```python
# Use goal orchestrator to generate security investigation goals
orchestrator = components['canonical_goal_orchestrator']

goals = orchestrator.generate_goals(
    conversation_context="Security audit: find vulnerabilities, test edge cases",
    epistemic_assessment=result['assessment']
)

print(f"\n📋 Generated {len(goals)} security goals:")
for i, goal in enumerate(goals, 1):
    print(f"{i}. {goal['description']}")
    print(f"   Priority: {goal['priority']}, Type: {goal['type']}")
```

---

## 🚀 STEP 4: INVESTIGATE (Multi-turn Security Audit)

### Investigation 1: SQL Injection Check

```bash
cd /home/yogapad/empirical-ai/empirica

# Find all database operations
grep -rn "execute\|executemany\|cursor" empirica/data/

# Check each one:
# GOOD: cursor.execute("SELECT * FROM sessions WHERE ai_id = ?", (ai_id,))
# BAD:  cursor.execute(f"SELECT * FROM sessions WHERE ai_id = '{ai_id}'")

# Look for string formatting in SQL
grep -rn "execute.*f\"\|execute.*%" empirica/data/
```

**Update beliefs after checking:**
```python
from empirica.calibration.adaptive_uncertainty_calibration import update_bayesian_belief

# After checking database code
update_bayesian_belief(
    session_id=session_id,
    context_key="sql_injection_risk",
    belief_type="risk_assessment",
    prior_confidence=0.5,  # Initially unsure
    posterior_confidence=0.95,  # After audit
    evidence="Reviewed all 23 SQL queries, all use parameterized queries",
    reasoning="No string formatting in SQL found, low risk"
)
```

### Investigation 2: Command Injection Check

```bash
# Find all subprocess/system calls
grep -rn "subprocess\|os.system\|os.popen" empirica/

# Check for shell=True with user input
grep -rn "shell=True" empirica/

# Check git operations (Phase 1.5)
grep -rn "subprocess.*git" empirica/core/canonical/git_enhanced_reflex_logger.py
```

### Investigation 3: Path Traversal Check

```bash
# Find all file operations
grep -rn "open(\|Path(\|os.path" empirica/

# Check for user input in paths
# Look for validation of paths (should stay within workspace)
```

### Investigation 4: Input Validation Check

```python
# Test MCP tools with invalid inputs
from empirica.cli import execute_preflight

# Test 1: Empty session_id
try:
    execute_preflight("", "test prompt")
    print("❌ Empty session_id accepted (BAD!)")
except ValueError as e:
    print(f"✅ Empty session_id rejected: {e}")

# Test 2: None session_id
try:
    execute_preflight(None, "test prompt")
    print("❌ None session_id accepted (BAD!)")
except (ValueError, TypeError) as e:
    print(f"✅ None session_id rejected: {e}")

# Test 3: Very long session_id
try:
    execute_preflight("x" * 10000, "test prompt")
    print("❌ Huge session_id accepted (BAD!)")
except ValueError as e:
    print(f"✅ Huge session_id rejected: {e}")

# Test 4: Wrong type for boolean
from empirica.bootstraps import bootstrap_metacognition
try:
    bootstrap_metacognition("test", "minimal", enable_git_checkpoints="yes")
    print("❌ String accepted for boolean (BAD!)")
except TypeError as e:
    print(f"✅ Wrong type rejected: {e}")
```

### Investigation 5: Edge Case Testing

```python
# Test concurrent session creation
import threading

def create_session():
    components = bootstrap_metacognition(f"test-{threading.current_thread().name}", "minimal")
    return components['session_id']

threads = []
for i in range(10):
    t = threading.Thread(target=create_session)
    threads.append(t)
    t.start()

for t in threads:
    t.join()

print("✅ Concurrent session creation handled")

# Test database locking
# Test with corrupted database
# Test with missing git
# Test with disk full (simulation)
```

---

## 🚀 STEP 5: CHECK Phase

```python
from empirica.cli import execute_check, submit_check_assessment

# After security audit, CHECK if system is secure
result = execute_check(
    session_id=session_id,
    findings=[
        "SQL injection: No vulnerabilities found (all queries parameterized)",
        "Command injection: Git operations use list args (safe)",
        "Path traversal: No user paths accepted without validation",
        "Input validation: Found X locations missing validation",
        "Edge cases: Empty values crash Y functions",
        # ... all findings
    ],
    remaining_unknowns=[
        "Behavior under sustained 1000+ concurrent writes untested",
        "Recovery from database corruption not tested",
        # ... unknowns
    ],
    confidence_to_proceed=0.X  # Honest assessment!
)

# Submit CHECK assessment
submit_check_assessment(
    session_id=session_id,
    vectors={...},  # Update based on security findings
    reasoning="...",
    decision="proceed",  # or "investigate_more"
    confidence_to_proceed=0.X,
    investigation_cycle=1
)

# Check for calibration drift
from empirica.cli import check_drift_monitor

drift = check_drift_monitor(session_id=session_id, window_size=3)
if drift.get('drift_detected'):
    print(f"⚠️ Drift detected: {drift['drift_type']}")
```

---

## 🚀 STEP 6: ACT (Fix Vulnerabilities & Add Validation)

### Fix 1: Add Input Validation

```python
# Example: Add validation to execute_preflight
def execute_preflight(session_id: str, prompt: str):
    # Add validation
    if not session_id:
        raise ValueError("session_id cannot be empty")
    if not isinstance(session_id, str):
        raise TypeError(f"session_id must be string, got {type(session_id)}")
    if len(session_id) > 255:
        raise ValueError(f"session_id too long: {len(session_id)} chars")
    if not prompt:
        raise ValueError("prompt cannot be empty")
    if len(prompt) > 100000:
        raise ValueError(f"prompt too long: {len(prompt)} chars")
    
    # Original logic continues...
```

### Fix 2: Improve Error Messages

```python
# Before:
raise Exception("Error")

# After:
raise ValueError(
    f"Invalid session_id: '{session_id}'. "
    f"Must be non-empty string (1-255 chars), got {type(session_id).__name__}"
)
```

### Fix 3: Add Edge Case Handling

```python
# Handle empty database gracefully
def get_session(session_id):
    try:
        cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        result = cursor.fetchone()
        if result is None:
            return None  # Not found (graceful)
        return result
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            # Database not initialized
            logger.warning("Database tables not found, initializing...")
            initialize_database()
            return None
        raise  # Re-raise other errors
```

---

## 🚀 STEP 7: Create Test Suite

```python
# Create test_security_edge_cases.py

def test_empty_session_id():
    with pytest.raises(ValueError, match="session_id cannot be empty"):
        execute_preflight("", "test")

def test_huge_session_id():
    with pytest.raises(ValueError, match="session_id too long"):
        execute_preflight("x" * 10000, "test")

def test_concurrent_sessions():
    # Test 10 concurrent session creations
    results = run_concurrent(create_session, count=10)
    assert len(results) == 10
    assert len(set(results)) == 10  # All unique

def test_corrupted_database():
    # Simulate corrupted database
    # Should handle gracefully, not crash

# ... 20+ more tests
```

---

## 🚀 STEP 8: POSTFLIGHT

```python
from empirica.cli import execute_postflight, submit_postflight_assessment

result = execute_postflight(
    session_id=session_id,
    task_summary="Security audit complete: 0 critical vulnerabilities, X validation issues fixed, Y edge cases tested"
)

# GENUINE reflection - what did you learn about Empirica's security?
submit_postflight_assessment(
    session_id=session_id,
    vectors={...},  # Reflect on learning
    reasoning="What I learned about the security posture...",
    changes_noticed="KNOW increased from 0.X to 0.Y because I now understand..."
)

# Get calibration report
from empirica.cli import get_calibration_report

calibration = get_calibration_report(session_id=session_id)
print(f"\n📊 Calibration Report:")
print(f"PREFLIGHT confidence: {calibration['preflight']['overall_confidence']}")
print(f"POSTFLIGHT confidence: {calibration['postflight']['overall_confidence']}")
print(f"Security posture confidence: {calibration['delta']}")
```

---

## 📊 Deliverables

### 1. SECURITY_AUDIT_REPORT.md
```markdown
# Security Audit Report

**Session:** [your session ID]
**Date:** 2025-11-15

## Vulnerabilities Found
### Critical: 0
### High: X
### Medium: Y
### Low: Z

## Detailed Findings

### 1. Input Validation Missing
- Location: empirica/cli/command_handlers/preflight.py:45
- Issue: session_id not validated
- Risk: Could accept malicious input
- Fix: Added validation (commit abc123)

[... all findings ...]

## Security Posture: GOOD/ACCEPTABLE/NEEDS WORK
```

### 2. EDGE_CASE_TESTING_REPORT.md
Document all edge cases tested and fixes applied.

### 3. Test Suite
`tests/security/test_security_edge_cases.py` with 20+ tests

### 4. Git Commits
```bash
git commit -m "security: Add input validation to all CLI commands"
git commit -m "security: Improve error messages throughout system"
git commit -m "test: Add 23 security and edge case tests"
```

---

## ⏰ Timeline

**Target:** Complete in 6-8 hours (today + tomorrow morning)

**Breakdown:**
- PREFLIGHT: 30 min
- INVESTIGATE (security): 3-4 hours
- CHECK: 30 min
- ACT (fixes + tests): 2-3 hours
- POSTFLIGHT: 30 min
- Reports: 1 hour

---

## 🎯 Success Criteria

- ✅ Zero critical security vulnerabilities
- ✅ All inputs validated
- ✅ All edge cases handled gracefully
- ✅ 20+ security/edge case tests added
- ✅ Calibration report shows learning
- ✅ Reports document all findings

---

## 💡 Key Points

1. **Use Empirica throughout** - Track your security confidence!
2. **Track Bayesian beliefs** - Update risk assessments as you audit
3. **Use goal orchestrator** - Let it guide your security investigation
4. **Multi-turn audit** - Be thorough, not rushed
5. **Test everything** - Write tests for all fixes

---

**You're up, Qwen. Bootstrap Empirica and start your security audit. We launch in 5 days!** 🔒
