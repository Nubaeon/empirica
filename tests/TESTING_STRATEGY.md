# Empirica Testing Strategy

## Test Categories

### 1. Unit Tests (tests/unit/)
**Purpose:** Verify CLI interface structure and basic functionality
**Scope:** Command existence, argument parsing, help text, error handling

**What to test:**
- Commands exist and are registered
- `--help` flags work
- Required arguments are enforced
- Output formats are supported (e.g., `--output json`)
- Error messages are clear

**What NOT to test:**
- Epistemic reasoning quality
- Assessment accuracy
- Learning deltas
- Calibration metrics

**Example:**
```python
def test_preflight_submit_help(self):
    """Preflight-submit command has working --help"""
    result = subprocess.run(["empirica", "preflight-submit", "--help"], capture_output=True)
    assert result.returncode == 0
```

### 2. Integration Tests (tests/integration/)
**Purpose:** Verify end-to-end workflows with real reasoning
**Scope:** CASCADE workflow, goal management, session lifecycle

**What to test:**
- PREFLIGHT → CHECK → POSTFLIGHT workflow
- Goal creation → subtask completion → goal closure
- Session handoffs across AI identities
- Epistemic artifacts (findings, unknowns, dead ends)
- Learning deltas (preflight vs postflight)

**Example:**
```python
def test_cascade_workflow_with_real_reasoning(tmp_session):
    """Test full CASCADE workflow with genuine epistemic assessment"""
    # PREFLIGHT - genuine self-assessment (direct submission)
    preflight = empirica.submit_preflight_assessment(
        session_id=tmp_session,
        vectors={...},  # 13 epistemic vectors
        reasoning="Initial assessment for OAuth2 implementation"
    )

    # Work happens here...

    # POSTFLIGHT - assess CURRENT state, system calculates deltas
    postflight = empirica.submit_postflight_assessment(
        session_id=tmp_session,
        vectors={...},  # Current 13 epistemic vectors
        reasoning="Completed OAuth2 implementation"
    )
    # System automatically calculates learning deltas from PREFLIGHT vs POSTFLIGHT
```

### 3. Production Tests (tests/production/)
**Purpose:** Verify production-critical functionality
**Scope:** Storage integrity, data consistency, performance

**What to test:**
- Database writes (SQLite + git notes + JSON)
- Vector storage consistency
- Git notes attachment
- Session recovery
- Performance benchmarks

---

## ⚠️ CRITICAL: Dummy Data Warning

**DO NOT use fake epistemic data in unit tests.**

### Why?
AIs reading test code might interpret dummy values as canonical thresholds:

```python
# ❌ BAD - AIs might think 0.7 is the "correct" know value
def test_preflight():
    vectors = {"know": 0.7, "uncertainty": 0.3}  # DUMMY DATA
    assert submit_preflight(vectors)
```

```python
# ✅ GOOD - Test interface, not epistemic values
def test_preflight_accepts_vectors():
    result = subprocess.run([
        "empirica", "preflight-submit", "--help"
    ], capture_output=True)
    assert "--vectors" in result.stdout.decode()
```

### Safe Approach
- **Unit tests:** Test structure only (commands exist, args accepted)
- **Integration tests:** Use REAL reasoning or clearly marked synthetic data
- **Add comments:** `# SYNTHETIC TEST DATA - NOT CANONICAL VALUES`

---

## Test Naming Convention

```
test_<command>_<aspect>

Examples:
- test_preflight_help()           # Command has --help
- test_preflight_requires_args()  # Enforces required args
- test_goals_create_json_output() # Supports --output json
```

---

## Running Tests

```bash
# All unit tests
pytest tests/unit/ -v

# Specific test file
pytest tests/unit/test_all_cli_commands.py -v

# Integration tests (require real sessions)
pytest tests/integration/ -v

# Production tests (verify storage integrity)
pytest tests/production/ -v

# Fast smoke test (unit + integration critical paths)
pytest tests/unit/ tests/integration/test_cascade_workflow.py -v
```

---

## Coverage Goals

- **Unit tests:** 100% of CLI commands tested for interface
- **Integration tests:** 80% of workflows tested with real reasoning
- **Production tests:** 100% of storage paths tested

---

## When Tests Fail

### Unit Test Failure
→ CLI interface changed (command removed, arg renamed, etc.)
→ Fix: Update test to match new interface

### Integration Test Failure
→ Epistemic logic changed (threshold adjusted, vector added, etc.)
→ Fix: Update test expectations OR fix regression

### Production Test Failure
→ Storage layer broken (database, git notes, JSON)
→ Fix: CRITICAL - fix storage immediately

---

## Current Status (2025-12-24)

- **Unit tests:** 40 passing, 1 skipped (chat - interactive)
- **Integration tests:** Need expansion (CASCADE workflow coverage)
- **Production tests:** Need creation (storage verification)

**Recent changes:**
- Removed 16 tests for deleted commands (assess, decision, profile, component, bootstrap)
- Added clear distinction: unit (interface) vs integration (reasoning)
- Updated TestCLISummary to check for working commands only
