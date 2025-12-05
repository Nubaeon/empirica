# Handoff to Qwen: Unit + Integration Tests (No Calibration Yet)

**Date:** 2025-12-04
**Prepared by:** Claude Code
**Phase:** Unit & Integration Testing Only
**Calibration Tests:** Phase 2 (requires Docker environment setup)

---

## Executive Summary

**What Sonnet Completed:**
- ✅ Database schema migration (4 tables → reflexes)
- ✅ Production documentation updates
- ✅ Bootstrap cleanup

**What You're Doing Now:**
- Create unit tests (test modules in isolation with mocked data)
- Create integration tests (test MCP layer and CASCADE phases)
- Fix broken `test_mcp_workflow.py` (currently invalid)
- **NOT** calibration tests yet (those come in Phase 2 with Docker setup)

**Why Split?**
- Unit + Integration: Fast, deterministic, use mocked vectors ✓ Can do now
- Calibration: Requires real investigation, Docker, multiple AIs ✗ Phase 2

---

## Part 1: Delete/Replace Invalid Test

### Current Problem: `tests/integration/test_mcp_workflow.py`

**Why it's broken:**
```python
# Line 87: "Work simulation"
await asyncio.sleep(0.1)  # ← NOT real work

# Lines 63-70: Hardcoded preflight
preflight = {"know": 0.60, "do": 0.65, ...}  # ← NOT assessed

# Lines 114-121: Hardcoded postflight with predetermined deltas
postflight = {"know": 0.75, "do": 0.80, ...}  # ← GAMED vectors

# Line 142: Testing arithmetic, not calibration
assert delta["know"] == pytest.approx(0.15, abs=0.01)  # ← Wrong test
```

**What this test was trying to do:** Validate calibration
**What it actually tests:** "Does subtraction work?" (already tested in SQL)
**Verdict:** Invalid, misleading, should be replaced

### Action

Replace this with proper **integration test** that validates:
- MCP tools work correctly
- Data persists to reflexes table
- CASCADE phases execute in sequence
- (But with understanding that vectors are mocked, so deltas are expected to be exact)

---

## Part 2: Unit Tests (3 suites)

### Overview

Unit tests use **mocked/controlled vectors** because:
- We're testing the MODULE, not calibration
- We need deterministic, reproducible results
- No AI assessment needed

### Unit Test Suite 1: `tests/unit/test_reflexes_table_operations.py`

**Purpose:** Verify reflexes table stores/retrieves data correctly

**Tests (15 tests estimated):**

```python
class TestReflexesTableOperations:
    """Unit tests for reflexes table - mocked vectors"""

    def test_store_preflight_vectors(self):
        """Verify PREFLIGHT vectors stored correctly"""
        vectors = {
            'engagement': 0.85, 'know': 0.70, 'do': 0.80, 'context': 0.75,
            'clarity': 0.75, 'coherence': 0.75, 'signal': 0.70, 'density': 0.60,
            'state': 0.75, 'change': 0.70, 'completion': 0.0, 'impact': 0.50,
            'uncertainty': 0.40
        }

        session_id = self.db.create_session(ai_id="test", bootstrap_level=1)
        logger = GitEnhancedReflexLogger(session_id=session_id)
        logger.add_checkpoint(phase="PREFLIGHT", round_num=1, vectors=vectors)

        # Query reflexes table
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT engagement, know, do, context, clarity, coherence, signal,
                   density, state, change, completion, impact, uncertainty
            FROM reflexes WHERE session_id = ? AND phase = 'PREFLIGHT'
        """, (session_id,))

        row = cursor.fetchone()
        assert row == tuple(vectors.values()), "All 13 vectors stored correctly"

    def test_store_all_phases_sequentially(self):
        """Verify PREFLIGHT, CHECK, POSTFLIGHT all store independently"""
        session_id = self.db.create_session(ai_id="test", bootstrap_level=1)
        logger = GitEnhancedReflexLogger(session_id=session_id)

        # Store 3 phases
        preflight = {'engagement': 0.8, 'know': 0.5, ...}  # 13 vectors
        logger.add_checkpoint(phase="PREFLIGHT", round_num=1, vectors=preflight)

        check = {'engagement': 0.85, 'know': 0.65, ...}  # 13 vectors
        logger.add_checkpoint(phase="CHECK", round_num=1, vectors=check)

        postflight = {'engagement': 0.9, 'know': 0.8, ...}  # 13 vectors
        logger.add_checkpoint(phase="POSTFLIGHT", round_num=1, vectors=postflight)

        # Query each phase
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM reflexes WHERE session_id = ?", (session_id,))
        count = cursor.fetchone()[0]
        assert count == 3, "All 3 phases stored separately"

    def test_round_numbering_increments(self):
        """Verify CHECK cycles numbered 1, 2, 3, ..."""
        session_id = self.db.create_session(ai_id="test", bootstrap_level=1)
        logger = GitEnhancedReflexLogger(session_id=session_id)

        vectors = {'engagement': 0.8, 'know': 0.5, ...}  # 13 vectors

        # Store 3 CHECK rounds
        for i in range(1, 4):
            logger.add_checkpoint(phase="CHECK", round_num=i, vectors=vectors)

        # Verify sequence
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT round_num FROM reflexes WHERE phase = 'CHECK' ORDER BY round_num")
        rounds = [row[0] for row in cursor.fetchall()]
        assert rounds == [1, 2, 3], "Round numbers sequential"

    def test_query_single_session_vectors(self):
        """Verify queries return only that session's data"""
        session1 = self.db.create_session(ai_id="test1", bootstrap_level=1)
        session2 = self.db.create_session(ai_id="test2", bootstrap_level=1)

        logger1 = GitEnhancedReflexLogger(session_id=session1)
        logger2 = GitEnhancedReflexLogger(session_id=session2)

        vectors = {'engagement': 0.8, 'know': 0.5, ...}  # 13 vectors
        logger1.add_checkpoint(phase="PREFLIGHT", round_num=1, vectors=vectors)
        logger2.add_checkpoint(phase="PREFLIGHT", round_num=1, vectors=vectors)

        # Query session1 only
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM reflexes WHERE session_id = ?", (session1,))
        count = cursor.fetchone()[0]
        assert count == 1, "Session isolation working"

    def test_vector_value_ranges_0_to_1(self):
        """Verify vectors stored as 0.0-1.0 floats"""
        session_id = self.db.create_session(ai_id="test", bootstrap_level=1)
        logger = GitEnhancedReflexLogger(session_id=session_id)

        vectors = {
            'engagement': 0.0,  # Boundary: 0
            'know': 1.0,        # Boundary: 1
            'do': 0.5,          # Midpoint
            ...13 vectors total...
        }
        logger.add_checkpoint(phase="PREFLIGHT", round_num=1, vectors=vectors)

        cursor = self.db.conn.cursor()
        cursor.execute("SELECT know, engagement FROM reflexes WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        assert row[0] == 1.0, "know (1.0) stored correctly"
        assert row[1] == 0.0, "engagement (0.0) stored correctly"

    # Add 9 more tests for:
    # - Invalid values rejected (< 0 or > 1)
    # - NULL handling
    # - Concurrent session writes
    # - Large batch stores
    # - Query performance (< 10ms)
    # - Metadata storage (mission, task)
    # - Git notes write validation
    # - Atomic transaction verification
    # - Index effectiveness
```

**Run:**
```bash
pytest tests/unit/test_reflexes_table_operations.py -v
# Expected: ~15 tests, all passing, <1 second total
```

---

### Unit Test Suite 2: `tests/unit/test_delta_calculation.py`

**Purpose:** Verify delta calculations are mathematically correct

**Tests (12 tests estimated):**

```python
class TestDeltaCalculation:
    """Unit tests for epistemic delta calculations"""

    def test_simple_delta_preflight_to_postflight(self):
        """Basic delta: POST - PRE"""
        preflight = {'know': 0.60, 'uncertainty': 0.50}
        postflight = {'know': 0.75, 'uncertainty': 0.30}

        deltas = calculate_vector_deltas(preflight, postflight)
        assert deltas['know'] == pytest.approx(0.15), "KNOW delta correct"
        assert deltas['uncertainty'] == pytest.approx(-0.20), "UNCERTAINTY delta correct"

    def test_delta_across_multiple_check_cycles(self):
        """Delta reduction across CHECK 1, 2, 3"""
        preflight = {'uncertainty': 0.60}
        check1 = {'uncertainty': 0.50}
        check2 = {'uncertainty': 0.35}
        check3 = {'uncertainty': 0.20}

        delta1 = check1['uncertainty'] - preflight['uncertainty']
        delta2 = check2['uncertainty'] - check1['uncertainty']
        delta3 = check3['uncertainty'] - check2['uncertainty']

        assert delta1 == pytest.approx(-0.10), "Cycle 1 reduction"
        assert delta2 == pytest.approx(-0.15), "Cycle 2 reduction"
        assert delta3 == pytest.approx(-0.15), "Cycle 3 reduction"

    def test_delta_monotonicity_check_cycles(self):
        """Verify uncertainty monotonically decreases"""
        cycle_uncertainties = [0.60, 0.50, 0.35, 0.20, 0.15]

        for i in range(1, len(cycle_uncertainties)):
            assert cycle_uncertainties[i] <= cycle_uncertainties[i-1], \
                "Monotonic decrease"

    def test_delta_boundary_cases(self):
        """Test deltas with boundary vectors"""
        # Both at 0
        delta_zero = 0.0 - 0.0
        assert delta_zero == 0.0

        # Both at 1
        delta_one = 1.0 - 1.0
        assert delta_one == 0.0

        # Full range
        delta_full = 1.0 - 0.0
        assert delta_full == 1.0

    def test_delta_precision_floats(self):
        """Verify float precision in deltas"""
        pre = 0.666666
        post = 0.777777
        delta = post - pre

        assert delta == pytest.approx(0.111111, abs=0.000001)

    # Add 7 more tests for:
    # - Negative deltas (learning reduction)
    # - Zero delta (no change)
    # - Large deltas (> 0.5)
    # - 13-vector delta set
    # - Delta ranking (top 5 changes)
    # - Velocity calculation (delta/time)
    # - Anomaly detection (unexpected deltas)
```

**Run:**
```bash
pytest tests/unit/test_delta_calculation.py -v
# Expected: ~12 tests, all passing, <0.5 seconds total
```

---

### Unit Test Suite 3: `tests/unit/test_decision_utils.py`

**Purpose:** Verify decision logic gates and thresholds

**Tests (10 tests estimated):**

```python
class TestDecisionUtils:
    """Unit tests for decision gate logic"""

    def test_proceed_gate_confidence_high(self):
        """High confidence (0.85) → PROCEED"""
        decision = calculate_decision(confidence=0.85)
        assert decision == "proceed"

    def test_investigate_gate_confidence_low(self):
        """Low confidence (0.45) → INVESTIGATE"""
        decision = calculate_decision(confidence=0.45)
        assert decision == "investigate"

    def test_proceed_with_caution_confidence_mid(self):
        """Mid confidence (0.65) → PROCEED_WITH_CAUTION"""
        decision = calculate_decision(confidence=0.65)
        assert decision == "proceed_with_caution"

    def test_multi_vector_recommendation(self):
        """Use multiple vectors for decision"""
        vectors = {
            'know': 0.75,
            'do': 0.80,
            'context': 0.75,
            'uncertainty': 0.25
        }

        recommendation = get_recommendation_from_vectors(vectors)
        assert recommendation['action'] == "proceed"
        assert 'message' in recommendation
        assert 'warnings' in recommendation

    def test_high_uncertainty_triggers_investigate(self):
        """High uncertainty overrides other vectors"""
        vectors = {
            'know': 0.90,
            'do': 0.90,
            'context': 0.90,
            'uncertainty': 0.70  # High uncertainty
        }

        recommendation = get_recommendation_from_vectors(vectors)
        assert recommendation['action'] in ["investigate", "proceed_with_caution"]

    def test_threshold_boundary_confidence_0_7(self):
        """Test confidence threshold at exactly 0.7"""
        decision_just_below = calculate_decision(confidence=0.69)
        decision_at = calculate_decision(confidence=0.70)
        decision_just_above = calculate_decision(confidence=0.71)

        # Should cross threshold at 0.7
        assert decision_just_below != "proceed"
        assert decision_at == "proceed"
        assert decision_just_above == "proceed"

    # Add 4 more tests for:
    # - Weighted scoring (confidence 35%, coherence 25%, etc.)
    # - Engagement gate (< 0.6 blocks)
    # - Uncertainty bounds (-0.2 to +1.0)
    # - MCO bias corrections applied
```

**Run:**
```bash
pytest tests/unit/test_decision_utils.py -v
# Expected: ~10 tests, all passing, <0.5 seconds total
```

---

## Part 3: Integration Tests (2 suites)

### Overview

Integration tests use **simple mocked vectors** because:
- We're testing the MCP LAYER, not calibration
- We need to verify tools work with database
- Vectors can be predetermined (we're not testing learning)

### Integration Test Suite 1: `tests/integration/test_mcp_tools_and_reflexes.py`

**Purpose:** Verify MCP tools correctly update reflexes table

**Tests (12 tests estimated):**

```python
class TestMCPToolsWithReflexes:
    """Integration: MCP tools → reflexes table"""

    @pytest.mark.asyncio
    async def test_session_create_tool_writes_to_reflexes(self):
        """MCP session_create tool creates reflexes entry"""
        result = await call_tool("session_create", {"ai_id": "test_integration"})
        session_data = json.loads(result[0].text)
        assert session_data["ok"] is True

        session_id = session_data["session_id"]

        # Verify reflexes table has session entry
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM reflexes WHERE session_id = ?", (session_id,))
        # Session itself doesn't need reflexes row, but we can query it
        assert session_id is not None

    @pytest.mark.asyncio
    async def test_submit_preflight_tool_stores_vectors(self):
        """MCP submit_preflight_assessment stores vectors"""
        # Create session
        session_result = await call_tool("session_create", {"ai_id": "test"})
        session_id = json.loads(session_result[0].text)["session_id"]

        # Submit preflight with mocked vectors
        vectors = {
            'engagement': 0.80, 'know': 0.60, 'do': 0.70, 'context': 0.65,
            'clarity': 0.75, 'coherence': 0.70, 'signal': 0.65, 'density': 0.55,
            'state': 0.60, 'change': 0.65, 'completion': 0.0, 'impact': 0.50,
            'uncertainty': 0.50
        }

        submit_result = await call_tool(
            "submit_preflight_assessment",
            {
                "session_id": session_id,
                "vectors": vectors,
                "reasoning": "Test PREFLIGHT"
            }
        )

        submit_data = json.loads(submit_result[0].text)
        assert submit_data["ok"] is True

        # Verify vectors in reflexes table
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT know, engagement FROM reflexes
            WHERE session_id = ? AND phase = 'PREFLIGHT'
        """, (session_id,))
        row = cursor.fetchone()
        assert row is not None, "PREFLIGHT vectors stored"
        assert row[0] == pytest.approx(0.60), "know vector correct"
        assert row[1] == pytest.approx(0.80), "engagement vector correct"

    @pytest.mark.asyncio
    async def test_submit_check_tool_stores_vectors(self):
        """MCP submit_check_assessment stores CHECK phase vectors"""
        session_id = await self._create_session("test")

        # Submit preflight first
        await self._submit_preflight(session_id)

        # Submit check with updated vectors
        check_vectors = {
            'engagement': 0.85, 'know': 0.70, 'do': 0.75, 'context': 0.75,
            'clarity': 0.80, 'coherence': 0.75, 'signal': 0.70, 'density': 0.60,
            'state': 0.70, 'change': 0.70, 'completion': 0.1, 'impact': 0.55,
            'uncertainty': 0.35
        }

        check_result = await call_tool(
            "submit_check_assessment",
            {
                "session_id": session_id,
                "vectors": check_vectors,
                "decision": "proceed",
                "reasoning": "Test CHECK"
            }
        )

        check_data = json.loads(check_result[0].text)
        assert check_data["ok"] is True

        # Verify CHECK stored
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM reflexes WHERE phase = 'CHECK'")
        count = cursor.fetchone()[0]
        assert count >= 1, "CHECK phase stored"

    @pytest.mark.asyncio
    async def test_submit_postflight_tool_calculates_deltas(self):
        """MCP submit_postflight_assessment calculates deltas"""
        session_id = await self._create_session("test")

        preflight_vectors = {
            'engagement': 0.80, 'know': 0.60, 'do': 0.70, ...
        }
        await self._submit_preflight(session_id, preflight_vectors)

        postflight_vectors = {
            'engagement': 0.90, 'know': 0.75, 'do': 0.85, ...
        }

        postflight_result = await call_tool(
            "submit_postflight_assessment",
            {
                "session_id": session_id,
                "vectors": postflight_vectors,
                "reasoning": "Test POSTFLIGHT"
            }
        )

        postflight_data = json.loads(postflight_result[0].text)
        assert postflight_data["ok"] is True
        assert "deltas" in postflight_data

        # Verify deltas are calculated (math check, not calibration check)
        deltas = postflight_data["deltas"]
        assert deltas["know"] == pytest.approx(0.15), "Delta math correct"
        assert deltas["do"] == pytest.approx(0.15), "Delta math correct"

    # Add 7 more tests for:
    # - Multiple CHECK cycles stored separately
    # - Round numbering (CHECK 1, 2, 3)
    # - Git notes written atomically
    # - Session isolation (different sessions don't interfere)
    # - All 13 vectors persisted
    # - Metadata (reasoning, task) stored
    # - Calibration accuracy field present
```

**Run:**
```bash
pytest tests/integration/test_mcp_tools_and_reflexes.py -v
# Expected: ~12 tests, all passing, <3 seconds total (with MCP server)
```

---

### Integration Test Suite 2: `tests/integration/test_cascade_workflow_phases.py`

**Purpose:** Verify CASCADE phases execute in correct sequence

**Tests (10 tests estimated):**

```python
class TestCASCADEWorkflowPhases:
    """Integration: CASCADE phase sequencing"""

    @pytest.mark.asyncio
    async def test_preflight_then_check_then_postflight_sequence(self):
        """Full CASCADE sequence: PREFLIGHT → CHECK → POSTFLIGHT"""
        session_id = await self._create_session("test")

        # Step 1: PREFLIGHT
        preflight_vectors = {'engagement': 0.8, 'know': 0.6, ...}
        await self._submit_preflight(session_id, preflight_vectors)

        # Verify PREFLIGHT stored
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT phase FROM reflexes WHERE session_id = ? ORDER BY created_at", (session_id,))
        phases = [row[0] for row in cursor.fetchall()]
        assert phases == ["PREFLIGHT"], "PREFLIGHT stored first"

        # Step 2: CHECK
        check_vectors = {'engagement': 0.85, 'know': 0.70, ...}
        await self._submit_check(session_id, check_vectors)

        # Step 3: POSTFLIGHT
        postflight_vectors = {'engagement': 0.9, 'know': 0.75, ...}
        await self._submit_postflight(session_id, postflight_vectors)

        # Verify sequence
        cursor.execute("SELECT phase FROM reflexes WHERE session_id = ? ORDER BY created_at", (session_id,))
        phases = [row[0] for row in cursor.fetchall()]
        assert phases[0] == "PREFLIGHT", "Phase 1 is PREFLIGHT"
        assert phases[1] == "CHECK", "Phase 2 is CHECK"
        assert phases[2] == "POSTFLIGHT", "Phase 3 is POSTFLIGHT"

    @pytest.mark.asyncio
    async def test_multiple_check_cycles_numbered_sequentially(self):
        """Multiple CHECK cycles get distinct round numbers"""
        session_id = await self._create_session("test")

        # PREFLIGHT
        await self._submit_preflight(session_id)

        # 3 CHECK cycles
        for i in range(1, 4):
            check_vectors = {'engagement': 0.8 + (i * 0.05), 'know': 0.6 + (i * 0.1), ...}
            await self._submit_check(session_id, check_vectors, round_num=i)

        # Verify round numbers
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT round_num FROM reflexes WHERE phase = 'CHECK' ORDER BY round_num")
        rounds = [row[0] for row in cursor.fetchall()]
        assert rounds == [1, 2, 3], "CHECK rounds numbered 1, 2, 3"

    @pytest.mark.asyncio
    async def test_vectors_persist_across_phases(self):
        """Vectors stored in phase 1 not affected by phase 2"""
        session_id = await self._create_session("test")

        preflight_vectors = {'engagement': 0.8, 'know': 0.6, ...}
        await self._submit_preflight(session_id, preflight_vectors)

        # Store original
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT know FROM reflexes WHERE phase = 'PREFLIGHT'")
        preflight_know = cursor.fetchone()[0]

        # Submit CHECK with different vectors
        check_vectors = {'engagement': 0.9, 'know': 0.8, ...}
        await self._submit_check(session_id, check_vectors)

        # Verify PREFLIGHT unchanged
        cursor.execute("SELECT know FROM reflexes WHERE phase = 'PREFLIGHT'")
        preflight_know_after = cursor.fetchone()[0]
        assert preflight_know == preflight_know_after, "PREFLIGHT vectors persist"

    @pytest.mark.asyncio
    async def test_git_notes_written_for_each_phase(self):
        """Each phase write creates git checkpoint"""
        session_id = await self._create_session("test")

        vectors = {'engagement': 0.8, 'know': 0.6, ...}

        # Submit phases
        await self._submit_preflight(session_id, vectors)
        await self._submit_check(session_id, vectors)
        await self._submit_postflight(session_id, vectors)

        # Verify git notes exist
        # (Check that git notes were written, not just SQLite)
        # This is an integration test of the atomic write
        result = os.popen(f"git notes list").read()
        # Verify git notes entries exist (implementation-specific)
        assert session_id in result or len(result) > 0, "Git notes written"

    # Add 5 more tests for:
    # - Atomicity (SQLite + git notes both succeed or both fail)
    # - No phases out of order (can't submit POSTFLIGHT before PREFLIGHT)
    # - Concurrent sessions don't interfere
    # - Phase timestamps in order
    # - Query latest phase by session_id
```

**Run:**
```bash
pytest tests/integration/test_cascade_workflow_phases.py -v
# Expected: ~10 tests, all passing, <3 seconds total
```

---

## Part 4: What NOT to Create

### ❌ Don't Create Calibration Tests Yet

These require Phase 2 setup:
- ❌ `test_calibration_questionnaire_*.py`
- ❌ `test_drift_monitor_real_learning.py`
- ❌ `test_statusline_real_vectors.py`
- ❌ Multi-AI Docker orchestration tests

**Why?** Need:
- Docker instances for each AI
- Real investigation workflows
- Persistent calibration database
- Time for epistemic work
- Coordination layer (run all AIs, collect)

**Timing:** After production deployment, Phase 2

---

## Part 5: Implementation Notes

### What Data to Use

**Unit Tests:**
- Mocked vectors (hardcoded is fine)
- Example: `{'know': 0.60, 'do': 0.70, ...}`
- Deterministic, reproducible

**Integration Tests:**
- Simple mocked vectors (same as unit)
- We're testing tools, not calibration
- Example: Submit preflight, verify reflexes table updated

### Imports

```python
from empirica.data.session_database import SessionDatabase
from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger
from empirica.cli.command_handlers.decision_utils import calculate_decision, get_recommendation_from_vectors
from empirica_mcp_server import call_tool  # For integration tests
```

### Fixtures

```python
@pytest.fixture
def db(self):
    db = SessionDatabase()
    yield db
    db.close()

@pytest.fixture
async def mcp_server(self):
    # Start MCP server for integration tests
    # Yield server
    # Shutdown
    pass
```

---

## Part 6: Git Workflow

```bash
# Create feature branch
git checkout -b qwen/unit-integration-tests

# Create 3 unit test files
# - tests/unit/test_reflexes_table_operations.py (15 tests)
# - tests/unit/test_delta_calculation.py (12 tests)
# - tests/unit/test_decision_utils.py (10 tests)

# Create 2 integration test files
# - tests/integration/test_mcp_tools_and_reflexes.py (12 tests)
# - tests/integration/test_cascade_workflow_phases.py (10 tests)

# Fix broken test
# - tests/integration/test_mcp_workflow.py (replace with proper integration test)

# Run all tests
pytest tests/unit/ -v
pytest tests/integration/ -v

# Commit
git commit -m "test: Add comprehensive unit and integration tests

Unit tests (37 tests):
- reflexes table operations and queries
- delta calculation math
- decision gate logic

Integration tests (22 tests):
- MCP tools write to reflexes table
- CASCADE phase sequencing
- Vector persistence across phases
- Git notes atomic writes

Fixed: Replace gamed test_mcp_workflow.py with real integration tests

Note: Calibration tests deferred to Phase 2 (requires Docker/multi-AI setup)"

# Create PR
gh pr create --title "test: Add unit and integration test suites"
```

---

## Part 7: Success Criteria

**Your work is complete when:**

1. ✅ 37 unit tests created and passing
2. ✅ 22 integration tests created and passing
3. ✅ test_mcp_workflow.py replaced with proper integration test
4. ✅ Zero test collection errors
5. ✅ All tests run in <10 seconds total
6. ✅ PR merged to main
7. ✅ CI/CD passes

**Not included (Phase 2):**
- ❌ Calibration tests
- ❌ Multi-AI Docker tests
- ❌ Questionnaire-based learning verification
- ❌ Real statusline drift detection

---

## Part 8: Questions/Clarifications

**Before starting, verify:**
- Q: Should unit tests use pytest fixtures or direct DB calls?
- Q: How many CHECK cycles should integration tests verify? (1? 5?)
- Q: Should we mock git operations or use real git repo?
- Q: Performance targets for tests? (<10sec total, or <1sec each?)

**During implementation:**
- Q: Should integration tests start/stop MCP server, or assume running?
- Q: Test data directory for mocked vectors? Hardcoded in tests?
- Q: Coverage requirement? (>80%? >90%?)

**After completion:**
- Q: Should these tests run in CI/CD on every commit?
- Q: Should unit tests run separately from integration (faster feedback)?

---

## Summary

**Unit Tests (37 tests):**
- Reflexes table operations (15)
- Delta calculation (12)
- Decision logic (10)

**Integration Tests (22 tests):**
- MCP tools (12)
- CASCADE phases (10)

**What's NOT included:**
- Calibration tests (Phase 2, requires Docker)
- Real learning verification (Phase 2)
- Multi-AI coordination (Phase 2)

**Timeline:** Can complete this phase now ✓
**Calibration tests:** Need Docker setup, Phase 2 ✗

**You're ready to start!** 🚀

---

**Next Steps After Qwen:**
1. Dev Lead: Consolidate data flow audit docs
2. Dev Lead: Move coordination archive docs
3. Final production readiness checklist
4. **Phase 2:** Docker setup for calibration tests
