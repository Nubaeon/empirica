# Gemini's Test Creation Task - Empirica Coordination

**Role:** Create comprehensive test suite for Empirica's Data Persistence and Integration layers  
**Coordinator:** Claude (Rovo Dev)  
**Partner:** Qwen (creating Layer 0 + Layer 1 tests)

---

## 🎯 Your Mission

Create 15-25 tests covering:
- **Layer 2:** Data Persistence (SessionDatabase, JSON Handler)
- **Layer 3:** Integration (MCP server, CLI, complete workflows)

**Also:** Review Qwen's test coverage and fill any gaps

---

## 📚 Step 1: Initialize Empirica (RECOMMENDED)

### Option A: Bootstrap (Quick)
```bash
cd /home/yogapad/empirical-ai/empirica
source .venv-empirica/bin/activate
empirica bootstrap --ai-id gemini-test-validator
```

### Option B: Full Onboarding (15 min - Better understanding)
```bash
empirica onboard --ai-id gemini-test-validator
```

### Option C: Direct Start (If already familiar)
Skip to Step 2.

**Recommendation:** If you haven't used Empirica, do Option B (onboarding) to understand the principles.

---

## 📖 Step 2: Read Architecture Documentation

**Essential reading:**
```bash
# Primary: Architectural overview
cat tests/coordination/COMPREHENSIVE_TEST_ARCHITECTURE.md
```

**Focus on:**
- Layer 2: Data Persistence (SessionDatabase, JSON Handler)
- Layer 3: Integration Interfaces (MCP, CLI, API)
- Test principles (no heuristics, evidence-based)

**Optional:**
```bash
# Complete reference
cat docs/skills/SKILL.md

# MCP specifics
cat docs/04_MCP_QUICKSTART.md

# Architecture overview
cat docs/05_ARCHITECTURE.md
```

---

## 🧪 Step 3: Use Empirica for Test Creation

### Before Starting (PREFLIGHT):
```bash
empirica preflight "Create test suite for Empirica data persistence and integration layers"
```

**Self-assess:**
- KNOW: Do I understand data/integration architecture?
- DO: Can I create integration tests?
- CONTEXT: Have I reviewed Qwen's work?
- UNCERTAINTY: What needs clarification?

---

## 🔍 Step 4: Review Qwen's Work First

**Before creating your tests:**
```bash
# See what Qwen created
ls tests/unit/canonical/
ls tests/unit/cascade/

# Review for coverage
cat tests/unit/canonical/test_reflex_frame.py
# etc.
```

**Assess:**
- What's well covered?
- What's missing?
- Any gaps in Layer 0/1?

**Note gaps to fill later**

---

## 📝 Step 5: Create Your Tests

### Test Organization:
```bash
# Create directories
mkdir -p tests/unit/data
mkdir -p tests/mcp
mkdir -p tests/integration

# Start with Layer 2
cd tests/unit/data
```

### Test Priority Order:

**1. test_session_database.py** (Data Layer)
```python
"""Test SessionDatabase SQLite operations."""

def test_create_session():
    """Create new session in database"""
    
def test_save_assessment():
    """Save epistemic assessment to session"""
    
def test_load_session():
    """Load session from database"""
    
def test_data_integrity():
    """Verify data integrity across save/load"""
```

**2. test_json_handler.py** (Session Continuity)
```python
"""Test JSON export/import for session continuity."""

def test_export_session():
    """Export session to JSON"""
    
def test_import_session():
    """Import session from JSON"""
    
def test_session_continuity():
    """Session state preserved across export/import"""
```

**3. tests/mcp/test_mcp_server_startup.py** (Critical!)
```python
"""Test MCP server initialization."""

def test_server_starts():
    """MCP server starts without errors"""
    
def test_tools_registered():
    """All 22 tools are registered"""
    
def test_introduction_tool_exists():
    """get_empirica_introduction tool available"""
```

**4. tests/mcp/test_mcp_tools.py**
```python
"""Test individual MCP tools."""

def test_bootstrap_session():
    """bootstrap_session tool works"""
    
def test_execute_preflight():
    """execute_preflight returns meta-prompt"""
    
def test_execute_postflight():
    """execute_postflight calculates delta"""
```

**5. tests/integration/test_complete_workflow.py** (CRITICAL!)
```python
"""Test complete PREFLIGHT→POSTFLIGHT workflow."""

def test_full_workflow():
    """
    1. Bootstrap session
    2. Execute preflight
    3. Do work
    4. Execute postflight
    5. Validate delta and calibration
    """
```

**6. tests/integration/test_investigation_loop.py**
```python
"""Test investigation loop behavior."""

def test_multiple_investigation_rounds():
    """System supports up to 3 investigation rounds"""
    
def test_check_decision_logic():
    """CHECK phase decides correctly: confidence ≥ 0.70 → ACT"""
```

---

## 🎯 Test Principles (CRITICAL!)

### 1. Integration Tests vs Unit Tests
```python
# Unit test - isolated component
def test_database_save():
    db = SessionDatabase()
    db.save(session)
    assert db.load(session.id) == session

# Integration test - multiple components
def test_complete_cascade():
    cascade = CanonicalEpistemicCascade()
    result = cascade.run(task)
    assert result.preflight_assessment is not None
    assert result.postflight_assessment is not None
    assert result.delta is not None
```

### 2. MCP Server Testing
```python
# Test server lifecycle
def test_mcp_server():
    server = start_mcp_server()
    assert server.is_running()
    
    tools = server.list_tools()
    assert len(tools) == 22
    
    server.stop()
```

### 3. End-to-End Validation
```python
# Test complete user journey
def test_e2e_workflow():
    # Bootstrap
    session = empirica_bootstrap("test-user")
    
    # Preflight
    preflight = empirica_preflight(session, "test task")
    assert preflight.engagement >= 0.60
    
    # Postflight
    postflight = empirica_postflight(session, "complete")
    
    # Validate
    delta = postflight - preflight
    assert delta.know > 0  # Should learn
```

---

## 📊 Step 6: Validate Coverage

**After creating your tests:**
```bash
# Check overall coverage
pytest tests/ --cov=empirica --cov-report=term

# Identify gaps
pytest tests/ --cov=empirica --cov-report=html
# Open htmlcov/index.html to see what's missing
```

**Fill gaps:**
- What critical paths aren't tested?
- What error conditions aren't covered?
- Any edge cases missed?

---

## 🤝 Step 7: Coordinate with Qwen

**Review Qwen's tests:**
- Are Layer 0/1 tests comprehensive?
- Any obvious gaps?
- Suggest additional tests if needed

**Report to coordinator:**
```
Status: Created test_session_database.py (5 tests)
Progress: 5/15 tests complete
Qwen review: Layer 0 looks good, CASCADE missing test_investigate.py
Suggestion: Qwen should add investigation loop test
```

---

## ✅ Step 8: After Completion (POSTFLIGHT)

```bash
empirica postflight "Test suite validation complete"
```

**Report:**
- What you learned
- Tests created
- Coverage gaps identified
- Qwen's coverage review
- Calibration status

---

## 📋 Deliverables

**Expected output:**
- 15-25 test files in `tests/unit/data/`, `tests/mcp/`, `tests/integration/`
- All tests follow pytest conventions
- Integration tests cover end-to-end workflows
- MCP server tests validate all tools
- Coverage analysis identifies remaining gaps

**Test execution:**
```bash
# Run your tests
pytest tests/unit/data/ -v
pytest tests/mcp/ -v
pytest tests/integration/ -v

# Overall coverage
pytest tests/ --cov=empirica -v
```

---

## 🤝 Coordination

**Report to coordinator (Claude):**
- Progress updates
- Qwen's coverage review
- Coverage gap analysis
- Integration test results

**Format:**
```
Status: Created test_mcp_server_startup.py
Progress: 8/15 tests complete
Coverage: Layer 2 at 75%, Layer 3 at 60%
Gaps: Need CLI command tests, error handling tests
```

---

## 🎯 Success Criteria

- [ ] 15-25 tests created
- [ ] Layer 2 fully covered (data persistence)
- [ ] Layer 3 key integration points covered
- [ ] Reviewed Qwen's test coverage
- [ ] Identified and documented gaps
- [ ] Integration tests validate complete workflows
- [ ] MCP server tests comprehensive

---

**Ready to start?**

1. Bootstrap/onboard if needed
2. Read architecture doc (focus on Layer 2-3)
3. Review Qwen's work first
4. Use Empirica preflight
5. Create tests following principles
6. Validate overall coverage
7. Report findings

**Time estimate:** 1-2 hours for 15-25 quality tests

Good luck! 🚀
