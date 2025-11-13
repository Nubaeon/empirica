# Empirica Comprehensive Test Plan

**Date:** 2025-11-08  
**Goal:** Prepare Empirica for production release with thorough testing  
**Approach:** Inspired by Pydantic AI's testing methodology  
**Status:** Ready for implementation

---

## 📋 Overview

This plan covers all testing needed for Empirica Phase 0 MVP release:
- ✅ **Unit tests** - Individual component testing
- ✅ **Integration tests** - Component interaction testing
- ✅ **Linting & formatting** - Code quality
- ✅ **Type checking** - Static type validation
- ✅ **Integrity tests** - Framework principle validation
- ✅ **CLI tests** - Command-line interface testing
- ✅ **MCP tests** - MCP server testing

---

## 🎯 Testing Philosophy

### Core Principles (from Phase 0 focus):

1. **NO HEURISTICS** - Test that no static values or shortcuts exist
2. **GENUINE SELF-ASSESSMENT** - Validate real epistemic tracking
3. **NO CONFABULATION** - Ensure no fake or simulated assessments
4. **PRIVACY-FIRST** - All tests use local data only

### Test Coverage Goals:

- **Unit tests:** >80% coverage
- **Integration tests:** All major workflows
- **Linting:** Zero violations
- **Type checking:** 100% pass rate
- **Integrity tests:** All principles validated

---

## 🧪 Test Categories

### 1. Linting & Formatting (Code Quality)

**Tools:**
- `ruff` - Fast Python linter and formatter (like Pydantic AI uses)
- `black` (alternative) - Code formatter
- `isort` - Import sorting

**What to check:**
- ✅ Code style consistency
- ✅ Import ordering
- ✅ Line length (120 chars max)
- ✅ Unused imports
- ✅ Undefined variables
- ✅ Type annotation completeness

**Files to check:**
```
empirica/
├── bootstraps/
├── calibration/
├── cli/
├── components/
├── config/
├── core/
├── dashboard/
├── data/
├── integration/
├── investigation/
└── plugins/
```

**Configuration:** `pyproject.toml` with ruff settings

---

### 2. Type Checking (Static Analysis)

**Tools:**
- `pyright` - Fast type checker (Pydantic AI's choice)
- `mypy` (alternative) - Python type checker

**What to check:**
- ✅ Type hints on all functions
- ✅ Return type annotations
- ✅ Parameter type annotations
- ✅ No `Any` types without justification
- ✅ Generic types properly specified

**Target:** 100% type coverage for public APIs

---

### 3. Unit Tests (Component Testing)

**Tool:** `pytest` with coverage

**Test Structure:**
```
tests/
├── unit/
│   ├── test_canonical_assessor.py
│   ├── test_reflex_logger.py
│   ├── test_session_database.py
│   ├── test_cli_commands.py
│   ├── test_mcp_server.py
│   ├── test_bootstraps.py
│   ├── test_calibration.py
│   └── test_vector_assessment.py
├── integration/
│   ├── test_preflight_postflight_flow.py
│   ├── test_cascade_workflow.py
│   ├── test_mcp_cli_integration.py
│   └── test_session_continuity.py
├── integrity/
│   ├── test_no_heuristics.py
│   ├── test_genuine_assessment.py
│   └── test_framework_principles.py
└── conftest.py
```

---

### 4. Integrity Tests (Framework Principles)

**Critical tests to validate core principles:**

#### Test 1: No Heuristics
```python
def test_no_static_baseline_values():
    """Verify no static epistemic values exist in codebase"""
    # Search for patterns like: 'know': 0.5 (hardcoded)
    # Ensure all values come from genuine assessment
```

#### Test 2: Genuine Assessment Required
```python
def test_assessment_requires_llm_response():
    """Verify assessment prompts are generated and responses parsed"""
    # Check CanonicalEpistemicAssessor returns prompts
    # Verify parse_llm_response extracts genuine scores
```

#### Test 3: No Confabulation
```python
def test_no_keyword_matching():
    """Verify no keyword-based scoring exists"""
    # Ensure assessment doesn't use simple rules
    # Validate structured self-assessment parsing
```

#### Test 4: Privacy-First
```python
def test_local_storage_only():
    """Verify all data stored locally, no cloud calls"""
    # Check no external API calls for storage
    # Verify .empirica/ folder usage
```

---

### 5. Unit Test Details

#### Core Components

**`test_canonical_assessor.py`**
```python
import pytest
from empirica.core.canonical import CanonicalEpistemicAssessor

@pytest.mark.asyncio
async def test_canonical_assessor_generates_prompt():
    """Test that assessor generates self-assessment prompt"""
    assessor = CanonicalEpistemicAssessor(agent_id="test")
    result = await assessor.assess("test task", {})
    
    assert isinstance(result, dict)
    assert "self_assessment_prompt" in result
    assert "assessment_id" in result
    assert len(result["self_assessment_prompt"]) > 100

@pytest.mark.asyncio
async def test_canonical_assessor_parses_response():
    """Test that assessor parses genuine LLM response"""
    assessor = CanonicalEpistemicAssessor(agent_id="test")
    
    # Mock genuine LLM response
    llm_response = {
        "engagement": {"score": 0.8, "rationale": "Genuine collaboration"},
        "foundation": {
            "know": {"score": 0.6, "rationale": "Moderate knowledge"},
            "do": {"score": 0.7, "rationale": "Can execute"},
            "context": {"score": 0.5, "rationale": "Limited context"}
        },
        # ... all 12 vectors
    }
    
    assessment = assessor.parse_llm_response(
        json.dumps(llm_response),
        "test_id",
        "test task",
        {}
    )
    
    assert assessment.know.score == 0.6
    assert assessment.do.score == 0.7
    assert "Moderate knowledge" in assessment.know.rationale

def test_no_static_values_in_assessor():
    """Ensure CanonicalEpistemicAssessor has no hardcoded scores"""
    import inspect
    source = inspect.getsource(CanonicalEpistemicAssessor)
    
    # Check for suspicious patterns
    assert "'know': 0.5" not in source
    assert "'do': 0.5" not in source
    # Ensure all scores come from parsing
```

**`test_reflex_logger.py`**
```python
import pytest
import json
from pathlib import Path
from empirica.core.canonical import ReflexLogger

def test_reflex_logger_creates_file():
    """Test reflex logger creates JSON files"""
    logger = ReflexLogger(session_id="test")
    frame = {
        "phase": "preflight",
        "vectors": {"know": 0.6, "do": 0.7},
        "timestamp": "2025-11-08T10:00:00"
    }
    
    logger.log_frame(frame)
    
    # Verify file exists
    log_path = Path(".empirica_reflex_logs/cascade/2025-11-08/")
    assert log_path.exists()

def test_reflex_logger_valid_json():
    """Test reflex logs are valid JSON"""
    logger = ReflexLogger(session_id="test")
    frame = {"phase": "preflight", "vectors": {}}
    
    logger.log_frame(frame)
    
    # Read and parse
    log_files = list(Path(".empirica_reflex_logs/cascade/").rglob("*.json"))
    assert len(log_files) > 0
    
    with open(log_files[0]) as f:
        data = json.load(f)  # Should not raise
        assert "phase" in data
```

**`test_session_database.py`**
```python
import pytest
from empirica.data.session_database import SessionDatabase
import tempfile
from pathlib import Path

@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = SessionDatabase(db_path=str(db_path))
        yield db
        db.close()

def test_create_session(temp_db):
    """Test session creation"""
    from datetime import datetime
    
    temp_db.create_session(
        session_id="test123",
        ai_id="test_ai",
        started_at=datetime.utcnow()
    )
    
    # Verify session exists
    cursor = temp_db.conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE session_id = ?", ("test123",))
    row = cursor.fetchone()
    
    assert row is not None
    assert row[0] == "test123"

def test_create_cascade(temp_db):
    """Test cascade creation"""
    from datetime import datetime
    
    temp_db.create_session("test123", "test_ai", datetime.utcnow())
    cascade_id = temp_db.create_cascade(
        session_id="test123",
        task="test task",
        context={"phase": "preflight"}
    )
    
    assert cascade_id is not None
    assert isinstance(cascade_id, str)
```

**`test_cli_commands.py`**
```python
import pytest
from empirica.cli.command_handlers import (
    handle_preflight_command,
    handle_mcp_status_command
)
from argparse import Namespace

def test_mcp_status_command():
    """Test MCP status command"""
    args = Namespace(verbose=False)
    
    # Should not raise
    handle_mcp_status_command(args)

def test_preflight_requires_assessment():
    """Test preflight requires genuine assessment"""
    args = Namespace(
        prompt="test task",
        session_id=None,
        assessment_json=None,
        json=False,
        compact=False,
        kv=False,
        quiet=True,
        verbose=False
    )
    
    # Should display prompt but not proceed without assessment
    # (we're testing that it doesn't use static values)
    handle_preflight_command(args)
    # In quiet mode without assessment_json, it should exit early
```

---

### 6. Integration Tests

**`test_preflight_postflight_flow.py`**
```python
import pytest
import json
from empirica.core.canonical import CanonicalEpistemicAssessor

@pytest.mark.asyncio
async def test_full_preflight_postflight_flow():
    """Test complete workflow from preflight to postflight"""
    session_id = "test_flow"
    assessor = CanonicalEpistemicAssessor(agent_id=session_id)
    
    # 1. Preflight
    preflight_request = await assessor.assess("test task", {})
    assert "self_assessment_prompt" in preflight_request
    
    # 2. Mock genuine response
    preflight_response = {
        "engagement": {"score": 0.7, "rationale": "Genuine"},
        "foundation": {
            "know": {"score": 0.5, "rationale": "Starting knowledge"},
            "do": {"score": 0.6, "rationale": "Can execute"},
            "context": {"score": 0.4, "rationale": "Limited context"}
        },
        # ... all vectors
    }
    
    preflight_assessment = assessor.parse_llm_response(
        json.dumps(preflight_response),
        preflight_request["assessment_id"],
        "test task",
        {}
    )
    
    assert preflight_assessment.know.score == 0.5
    
    # 3. Postflight
    postflight_request = await assessor.assess(
        "POSTFLIGHT: test task",
        {"phase": "postflight"}
    )
    
    postflight_response = {
        "engagement": {"score": 0.8, "rationale": "Improved engagement"},
        "foundation": {
            "know": {"score": 0.7, "rationale": "Learned more"},
            "do": {"score": 0.7, "rationale": "Better execution"},
            "context": {"score": 0.6, "rationale": "More context"}
        },
        # ... all vectors
    }
    
    postflight_assessment = assessor.parse_llm_response(
        json.dumps(postflight_response),
        postflight_request["assessment_id"],
        "POSTFLIGHT: test task",
        {"phase": "postflight"}
    )
    
    # 4. Validate learning
    know_delta = postflight_assessment.know.score - preflight_assessment.know.score
    assert know_delta > 0  # Learning occurred
    assert know_delta == 0.2
```

**`test_mcp_cli_integration.py`**
```python
import pytest
import subprocess
import time

def test_mcp_start_stop():
    """Test MCP server start/stop via CLI"""
    # Start
    result = subprocess.run(
        ["python3", "-m", "empirica.cli", "mcp-start"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "started successfully" in result.stdout.lower() or \
           "already running" in result.stdout.lower()
    
    # Wait a bit
    time.sleep(2)
    
    # Status
    result = subprocess.run(
        ["python3", "-m", "empirica.cli", "mcp-status"],
        capture_output=True,
        text=True
    )
    
    assert "Running" in result.stdout
    
    # Stop
    result = subprocess.run(
        ["python3", "-m", "empirica.cli", "mcp-stop"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0

def test_mcp_list_tools():
    """Test MCP tools listing"""
    result = subprocess.run(
        ["python3", "-m", "empirica.cli", "mcp-list-tools"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "execute_preflight" in result.stdout
    assert "execute_postflight" in result.stdout
    assert "19 tools" in result.stdout or "14 tools" in result.stdout
```

---

### 7. Test Configuration Files

**`pyproject.toml`** (new file or section)
```toml
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[project]
name = "empirica"
version = "0.1.0"
description = "Genuine AI epistemic self-assessment framework"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "Empirica Team"}
]

dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    # Add other dependencies
]

[project.optional-dependencies]
test = [
    "pytest>=7.0",
    "pytest-asyncio>=0.21",
    "pytest-cov>=4.0",
    "pytest-mock>=3.10",
]
lint = [
    "ruff>=0.1.0",
]
typecheck = [
    "pyright>=1.1.300",
]
dev = [
    "empirica[test,lint,typecheck]",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
asyncio_mode = "auto"
addopts = [
    "--strict-markers",
    "--strict-config",
    "-ra",
    "--cov=empirica",
    "--cov-report=term-missing",
    "--cov-report=html",
]

[tool.coverage.run]
source = ["empirica"]
omit = [
    "tests/*",
    "_archive/*",
    "_dev/*",
]

[tool.coverage.report]
precision = 2
exclude_lines = [
    "pragma: no cover",
    "raise AssertionError",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "@abstractmethod",
]

[tool.ruff]
line-length = 120
target-version = "py310"
include = [
    "empirica/**/*.py",
    "mcp_local/**/*.py",
    "tests/**/*.py",
]

[tool.ruff.lint]
extend-select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "C",  # flake8-comprehensions
    "B",  # flake8-bugbear
    "UP", # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by formatter)
]

[tool.ruff.lint.isort]
known-first-party = ["empirica"]

[tool.pyright]
include = ["empirica", "mcp_local", "tests"]
exclude = [
    "_archive",
    "_dev",
    ".venv",
    "venv",
]
pythonVersion = "3.10"
typeCheckingMode = "basic"
reportMissingImports = true
reportMissingTypeStubs = false
```

**`tests/conftest.py`**
```python
"""
Pytest configuration and shared fixtures for Empirica tests
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

# Pytest fixtures

@pytest.fixture
def temp_empirica_dir():
    """Create temporary .empirica directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        empirica_path = Path(tmpdir) / ".empirica"
        empirica_path.mkdir()
        (empirica_path / "sessions").mkdir()
        yield empirica_path

@pytest.fixture
def temp_session_db(temp_empirica_dir):
    """Create temporary session database"""
    from empirica.data.session_database import SessionDatabase
    
    db_path = temp_empirica_dir / "sessions" / "test.db"
    db = SessionDatabase(db_path=str(db_path))
    yield db
    db.close()

@pytest.fixture
def sample_assessment_response():
    """Sample genuine assessment response for testing"""
    return {
        "engagement": {
            "score": 0.8,
            "rationale": "Genuine collaborative intelligence"
        },
        "foundation": {
            "know": {
                "score": 0.6,
                "rationale": "Moderate domain knowledge"
            },
            "do": {
                "score": 0.7,
                "rationale": "Good execution capability"
            },
            "context": {
                "score": 0.5,
                "rationale": "Adequate environmental context"
            }
        },
        "comprehension": {
            "clarity": {"score": 0.8, "rationale": "Clear understanding"},
            "coherence": {"score": 0.7, "rationale": "Coherent grasp"},
            "signal": {"score": 0.6, "rationale": "Key signals identified"},
            "density": {"score": 0.4, "rationale": "Manageable complexity"}
        },
        "execution": {
            "state": {"score": 0.5, "rationale": "Basic state mapping"},
            "change": {"score": 0.6, "rationale": "Can track changes"},
            "completion": {"score": 0.7, "rationale": "Clear completion path"},
            "impact": {"score": 0.6, "rationale": "Understand consequences"}
        },
        "uncertainty": {
            "score": 0.4,
            "rationale": "Moderate uncertainty about edge cases"
        }
    }

# Pytest markers

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "integrity: mark test as framework integrity test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
```

**`Makefile`**
```makefile
.PHONY: help
help: ## Show this help message
	@echo "Empirica Testing & Development Commands"
	@echo "========================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: ## Install package and dev dependencies
	pip install -e ".[dev]"

.PHONY: test
test: ## Run all tests
	pytest tests/

.PHONY: test-unit
test-unit: ## Run unit tests only
	pytest tests/unit/

.PHONY: test-integration
test-integration: ## Run integration tests only
	pytest tests/integration/ -m integration

.PHONY: test-integrity
test-integrity: ## Run integrity tests (framework principles)
	pytest tests/integrity/ -m integrity

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	pytest tests/ --cov=empirica --cov-report=html --cov-report=term-missing

.PHONY: format
format: ## Format code with ruff
	ruff format empirica/ mcp_local/ tests/

.PHONY: lint
lint: ## Lint code with ruff
	ruff check empirica/ mcp_local/ tests/

.PHONY: lint-fix
lint-fix: ## Lint and auto-fix issues
	ruff check --fix empirica/ mcp_local/ tests/

.PHONY: typecheck
typecheck: ## Run type checking with pyright
	pyright empirica/ mcp_local/

.PHONY: check
check: lint typecheck test ## Run all checks (lint + typecheck + test)

.PHONY: clean
clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/ .coverage

.PHONY: validate
validate: format lint typecheck test-integrity ## Validate release readiness
```

---

## 🚀 Implementation Plan

### Phase 1: Setup (1-2 hours)
1. Create `pyproject.toml` with test configuration
2. Install test dependencies: `pytest`, `pytest-cov`, `pytest-asyncio`, `pytest-mock`
3. Install linting: `ruff`
4. Install type checking: `pyright`
5. Create `tests/` directory structure
6. Create `conftest.py` with fixtures
7. Create `Makefile` for convenience

### Phase 2: Linting & Formatting (1-2 hours)
1. Run `ruff format` on all code
2. Fix any linting issues
3. Configure `.gitignore` for test artifacts
4. Verify clean linting pass

### Phase 3: Type Checking (2-3 hours)
1. Add missing type hints
2. Run `pyright` and fix issues
3. Aim for >90% type coverage
4. Document any `Any` types

### Phase 4: Unit Tests (4-6 hours)
1. Write tests for core components:
   - CanonicalEpistemicAssessor
   - ReflexLogger
   - SessionDatabase
   - CLI commands
   - MCP server functions
2. Achieve >80% code coverage
3. All tests passing

### Phase 5: Integration Tests (2-3 hours)
1. Test preflight→postflight flow
2. Test MCP+CLI integration
3. Test session continuity
4. All workflows validated

### Phase 6: Integrity Tests (2-3 hours)
1. Test no heuristics exist
2. Verify genuine assessment required
3. Validate framework principles
4. Ensure privacy-first architecture

### Phase 7: CI/CD Setup (Optional, 1-2 hours)
1. Create GitHub Actions workflow
2. Run tests on push
3. Generate coverage reports
4. Automated checks

---

## 📊 Success Criteria

### Code Quality:
- ✅ Zero linting violations
- ✅ Zero type errors
- ✅ Consistent code style

### Test Coverage:
- ✅ >80% unit test coverage
- ✅ All critical paths tested
- ✅ All CLI commands tested
- ✅ All MCP tools tested

### Integrity:
- ✅ No heuristics detected
- ✅ Genuine assessment enforced
- ✅ Privacy-first validated
- ✅ Framework principles upheld

### Documentation:
- ✅ All tests documented
- ✅ Test plan complete
- ✅ README updated with testing instructions

---

## 📝 Next Steps

1. **Review this plan** - Confirm approach
2. **Set up environment** - Install test tools
3. **Assign to AI testers** - Qwen, Gemini, etc.
4. **Implement tests** - Phase by phase
5. **Fix issues** - As tests reveal problems
6. **Validate release** - All tests passing

---

## 🤝 Handoff to Test AI

**For Qwen/Gemini/Testing AI:**

1. Read this test plan
2. Set up test environment: `pip install -e ".[dev]"`
3. Start with Phase 1 (setup)
4. Work through phases systematically
5. Report any issues found
6. Submit test results

**Key Files to Test:**
- `empirica/core/canonical/` - Core assessment logic
- `empirica/cli/` - CLI commands
- `mcp_local/` - MCP server
- `empirica/data/` - Database operations

**Focus Areas:**
- NO HEURISTICS validation
- Genuine assessment enforcement
- Type safety
- Integration workflows

---

**Status:** ⏳ Ready for implementation  
**Estimated Time:** 12-18 hours total  
**Priority:** HIGH (needed for release)
