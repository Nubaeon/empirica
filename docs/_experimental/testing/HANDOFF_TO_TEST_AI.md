# Handoff to Test AI (Qwen/Gemini)

**Date:** 2025-11-08  
**Task:** Implement comprehensive test suite for Empirica Phase 0 MVP  
**Status:** Ready for implementation  
**Estimated Time:** 12-18 hours

---

## 🎯 Your Mission

Implement a comprehensive test suite for Empirica to validate it's ready for production release. Focus on:

1. ✅ **NO HEURISTICS validation** - Ensure no static values or shortcuts
2. ✅ **Genuine self-assessment enforcement** - Verify real epistemic tracking
3. ✅ **Code quality** - Linting, formatting, type checking
4. ✅ **Component testing** - Unit and integration tests
5. ✅ **Framework integrity** - Core principle validation

---

## 📋 What's Already Done

### ✅ Test Infrastructure Created:
- `pyproject.toml` - Full test configuration
- `Makefile` - Convenient test commands
- `tests/conftest.py` - Pytest fixtures and helpers
- `tests/integrity/test_no_heuristics.py` - Integrity test starter
- `docs/testing/COMPREHENSIVE_TEST_PLAN.md` - Detailed plan

### ✅ Cleanup Complete:
- Repository cleaned and organized
- 50+ old files archived to `_archive/`
- Root directory now has only ~15 essential files
- Clean structure for Phase 0 MVP

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd /home/yogapad/empirical-ai/empirica

# Install with all dev dependencies
pip install -e ".[dev,mcp]"

# Or just test dependencies
pip install -e ".[test]"
```

### 2. Verify Setup
```bash
# Check installation
python3 -c "import empirica; print('✅ Empirica installed')"

# Run existing tests (if any)
pytest tests/ -v

# Check linting
make lint

# Check types
make typecheck
```

### 3. Review Documentation
Read these files in order:
1. `docs/testing/COMPREHENSIVE_TEST_PLAN.md` - Full test plan
2. `docs/phase_0/EMPIRICA_SINGLE_AI_FOCUS.md` - Phase 0 focus
3. `docs/production/README.md` - Production docs
4. `README.md` - Main readme

---

## 📝 Implementation Plan

### Phase 1: Setup & Validation (1-2 hours)

**Goal:** Get environment working and validate current state

**Tasks:**
1. Install dependencies: `make install`
2. Run linting: `make lint`
3. Run type checking: `make typecheck`
4. Fix any immediate issues found
5. Run existing integrity test: `pytest tests/integrity/ -v`

**Expected Output:**
- Dependencies installed
- Linting shows violations (we'll fix in Phase 2)
- Type checking may show errors (we'll fix in Phase 3)
- Integrity test should PASS (validates no heuristics)

---

### Phase 2: Linting & Formatting (1-2 hours)

**Goal:** Clean up code style and ensure consistency

**Tasks:**
1. Format code: `make format`
2. Fix linting issues: `make lint-fix`
3. Review remaining violations
4. Manually fix complex violations
5. Verify clean: `make lint`

**Files to focus on:**
- `empirica/cli/` - CLI commands
- `empirica/core/` - Core components
- `mcp_local/` - MCP server

**Commands:**
```bash
# Auto-format everything
make format

# Auto-fix linting issues
make lint-fix

# Check remaining issues
make lint

# For specific files
ruff check --fix empirica/cli/command_handlers/cascade_commands.py
```

**Success Criteria:**
- ✅ Zero linting violations
- ✅ Consistent code style
- ✅ All imports sorted

---

### Phase 3: Type Checking (2-3 hours)

**Goal:** Add type hints and fix type errors

**Tasks:**
1. Run type checking: `make typecheck`
2. Add missing type hints to functions
3. Fix type errors
4. Re-run until clean: `make typecheck`

**Priority files:**
- `empirica/core/canonical/canonical_epistemic_assessment.py`
- `empirica/cli/command_handlers/*.py`
- `mcp_local/empirica_mcp_server.py`

**Common fixes:**
```python
# Before
def assess(self, prompt, context):
    ...

# After
def assess(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
    ...
```

**Success Criteria:**
- ✅ >90% functions have type hints
- ✅ Zero type errors from pyright
- ✅ Public API fully typed

---

### Phase 4: Unit Tests - Core Components (4-6 hours)

**Goal:** Test individual components

**Create these test files:**

#### 4.1 `tests/unit/test_canonical_assessor.py`
Test CanonicalEpistemicAssessor:
- ✅ Generates self-assessment prompt
- ✅ Returns assessment_id
- ✅ Does NOT return vector scores directly
- ✅ Parses LLM responses correctly
- ✅ Validates assessment structure

```python
import pytest
from empirica.core.canonical import CanonicalEpistemicAssessor

@pytest.mark.asyncio
async def test_assessor_generates_prompt():
    assessor = CanonicalEpistemicAssessor(agent_id="test")
    result = await assessor.assess("test task", {})
    
    assert isinstance(result, dict)
    assert "self_assessment_prompt" in result
    assert "assessment_id" in result
    assert "vectors" not in result  # Should NOT have pre-computed scores

# Add more tests following the plan...
```

#### 4.2 `tests/unit/test_reflex_logger.py`
Test ReflexLogger:
- ✅ Creates log files in correct location
- ✅ Writes valid JSON
- ✅ Includes all required fields
- ✅ Handles concurrent writes

#### 4.3 `tests/unit/test_session_database.py`
Test SessionDatabase:
- ✅ Creates sessions
- ✅ Creates cascades
- ✅ Stores metadata
- ✅ Retrieves session history

#### 4.4 `tests/unit/test_cli_commands.py`
Test CLI command handlers:
- ✅ MCP commands work
- ✅ Preflight requires assessment
- ✅ Postflight calculates delta
- ✅ Output formats work (JSON, compact, etc.)

**Success Criteria:**
- ✅ >80% code coverage
- ✅ All tests passing
- ✅ Core components validated

---

### Phase 5: Integration Tests (2-3 hours)

**Goal:** Test component interactions

**Create these test files:**

#### 5.1 `tests/integration/test_preflight_postflight_flow.py`
Test complete workflow:
- ✅ Preflight → work → postflight
- ✅ Delta calculation
- ✅ Calibration assessment
- ✅ Learning validation

#### 5.2 `tests/integration/test_mcp_cli_integration.py`
Test MCP + CLI:
- ✅ MCP server start/stop
- ✅ MCP tools listing
- ✅ CLI can manage MCP server

#### 5.3 `tests/integration/test_session_continuity.py`
Test session management:
- ✅ Session creation
- ✅ Session retrieval
- ✅ Multiple cascades per session
- ✅ History tracking

**Success Criteria:**
- ✅ All major workflows tested
- ✅ Integration points validated
- ✅ End-to-end scenarios working

---

### Phase 6: Integrity Tests (2-3 hours)

**Goal:** Validate framework principles

The starter file `tests/integrity/test_no_heuristics.py` already exists.

**Additional tests to add:**

#### 6.1 Expand `test_no_heuristics.py`
- ✅ Scan all Python files for static vectors
- ✅ Verify no keyword matching
- ✅ Check no confabulation patterns

#### 6.2 Create `tests/integrity/test_genuine_assessment.py`
Test genuine assessment enforcement:
- ✅ Assessment requires LLM response
- ✅ Parse_llm_response extracts real scores
- ✅ No simulation or fake data

#### 6.3 Create `tests/integrity/test_framework_principles.py`
Test core principles:
- ✅ Privacy-first (local storage only)
- ✅ Universal interface (no model lock-in)
- ✅ 13-vector system complete

**Success Criteria:**
- ✅ NO HEURISTICS validated
- ✅ Genuine assessment enforced
- ✅ Framework integrity confirmed

---

### Phase 7: Final Validation (1 hour)

**Goal:** Ensure everything is ready for release

**Tasks:**
1. Run full test suite: `make test-cov`
2. Generate coverage report
3. Run all checks: `make validate-full`
4. Document any known issues
5. Create test report

**Commands:**
```bash
# Run everything with coverage
make validate-full

# Check results
open htmlcov/index.html  # View coverage report

# Create test report
pytest tests/ --html=test_report.html --self-contained-html
```

**Success Criteria:**
- ✅ >80% code coverage
- ✅ All tests passing
- ✅ Zero linting violations
- ✅ Zero type errors
- ✅ All integrity tests passing

---

## 🧪 Testing Commands Reference

### Quick Commands
```bash
make help                 # Show all commands
make test                 # Run all tests
make test-unit            # Unit tests only
make test-integration     # Integration tests only
make test-integrity       # Integrity tests only
make test-cov             # Tests with coverage
make lint                 # Check code quality
make lint-fix             # Auto-fix linting
make format               # Format code
make typecheck            # Check types
make validate             # Full validation
```

### Pytest Commands
```bash
# Run specific test file
pytest tests/unit/test_canonical_assessor.py -v

# Run specific test function
pytest tests/unit/test_canonical_assessor.py::test_assessor_generates_prompt -v

# Run with markers
pytest -m integrity        # Only integrity tests
pytest -m "not slow"       # Exclude slow tests

# Run with coverage
pytest tests/unit/ --cov=empirica --cov-report=html

# Run with verbose output
pytest tests/ -vv
```

---

## 📊 What to Report

After completing each phase, report:

### Progress Report Format:
```markdown
## Phase X: [Name] - [Status]

**Time Spent:** X hours
**Status:** ✅ Complete / ⏳ In Progress / ❌ Blocked

**Completed:**
- ✅ Task 1
- ✅ Task 2

**Issues Found:**
- ⚠️ Issue description
- 📝 How fixed / workaround

**Test Results:**
- Tests run: X
- Tests passed: X
- Coverage: X%

**Next Steps:**
- Move to Phase X+1
- Fix remaining issues
```

### Final Report Should Include:
1. **Summary** - Overall status
2. **Test Coverage** - Percentage and report
3. **Issues Found** - List of problems discovered
4. **Issues Fixed** - What was corrected
5. **Known Issues** - Remaining problems (if any)
6. **Recommendations** - Suggestions for improvement

---

## ⚠️ Important Notes

### Critical: NO HEURISTICS
- If you find static baseline values, report immediately
- All vector scores MUST come from genuine LLM responses
- No shortcuts, no simulations, no fake data
- This is non-negotiable

### Testing Philosophy
- Write tests that validate behavior, not implementation
- Focus on public APIs and interfaces
- Mock external dependencies (APIs, file system when appropriate)
- Use fixtures from conftest.py

### Code Quality Standards
- Line length: 120 characters max
- Type hints on all public functions
- Docstrings on classes and public methods
- Consistent import ordering (handled by ruff)

---

## 🆘 Getting Help

### Documentation:
- `docs/testing/COMPREHENSIVE_TEST_PLAN.md` - Full details
- `docs/phase_0/EMPIRICA_SINGLE_AI_FOCUS.md` - What matters for Phase 0
- `docs/production/README.md` - How Empirica works

### Pytest Help:
```bash
pytest --help              # General help
pytest --markers           # Show available markers
pytest --fixtures          # Show available fixtures
```

### Debugging Tests:
```bash
# Run with print statements visible
pytest tests/unit/ -s

# Run with pdb on failure
pytest tests/unit/ --pdb

# Run single test with verbose output
pytest tests/unit/test_file.py::test_function -vv
```

---

## ✅ Success Criteria

### Minimum Release Requirements:
- ✅ All integrity tests passing (NO HEURISTICS validated)
- ✅ >80% unit test coverage
- ✅ All integration tests passing
- ✅ Zero linting violations
- ✅ Zero type errors
- ✅ All CLI commands tested
- ✅ MCP server tested

### Stretch Goals:
- ✅ >90% test coverage
- ✅ Performance benchmarks
- ✅ Load testing
- ✅ Security audit

---

## 🎉 When Complete

1. Commit all test code
2. Generate final coverage report
3. Create test summary document
4. Tag version as "test-ready"
5. Report back to main development team

---

**Good luck! Remember: Focus on validating NO HEURISTICS and genuine self-assessment. Everything else is secondary.**

**Questions?** Review the comprehensive test plan or check existing test examples in `/home/yogapad/empirical-ai/pydantic-ai/tests/` for inspiration.

---

**Status:** ✅ Ready for AI tester handoff  
**Next:** Begin Phase 1 (Setup & Validation)
