# Why Unified Storage Architecture Matters

**The Case Against Scattered Storage Paths**

---

## The Problem Statement

The current implementation splits assessment storage across **three independent code paths** with **different tables, formats, and timing**:

```
PREFLIGHT:   cascade_metadata + git notes (partial) + auto_checkpoint
CHECK:       epistemic_assessments + git notes + different location
POSTFLIGHT:  epistemic_assessments + git notes + reflex logs
```

**Question:** Why is this bad if all three "eventually" get stored somewhere?

**Answer:** Because distributed writes WITHOUT coordination break fundamental guarantees.

---

## Guarantee 1: Consistency (ACID-C)

### Unified Storage (CORRECT)

```python
# Single transaction
with db.transaction():
    checkpoint_id = logger.add_checkpoint(
        phase="PREFLIGHT",
        vectors=vectors,
        metadata=metadata
    )
    # This call atomically writes to:
    # - SQLite (reflexes table)
    # - Git notes (compressed)
    # - JSON logs (full)
    # All succeed together or all fail together
```

**Guarantee:** If the function returns, all three storage layers are consistent.

### Scattered Storage (BROKEN)

```python
# Three independent operations
db.conn.execute("INSERT INTO cascade_metadata...")  # Write 1
db.conn.commit()

auto_checkpoint(...)  # Write 2

# (JSON never written for PREFLIGHT)

# If Write 1 succeeds but Write 2 fails:
# - cascade_metadata has the data
# - git notes doesn't have the data
# - statusline queries git notes (or reflexes) and finds nothing
# - System state is INCONSISTENT
```

**Problem:** Distributed writes with no coordination = eventual inconsistency.

---

## Guarantee 2: Query Consistency (Single Query)

### Unified Storage (CORRECT)

```python
# Get complete epistemic state with ONE query
results = db.execute("""
    SELECT phase, know, do, context, uncertainty, overall_confidence
    FROM reflexes
    WHERE session_id = ? AND phase IN ('PREFLIGHT', 'CHECK', 'POSTFLIGHT')
    ORDER BY assessed_at
""")

# Returns:
# PREFLIGHT: know=0.75, do=0.80, uncertainty=0.25, ...
# CHECK:     know=0.92, do=0.87, uncertainty=0.08, ...
# POSTFLIGHT: know=0.95, do=0.90, uncertainty=0.05, ...
```

**All epistemic state in ONE result set.**

### Scattered Storage (BROKEN)

```python
# Get PREFLIGHT from cascade_metadata
preflight = db.execute("""
    SELECT metadata_value FROM cascade_metadata
    WHERE cascade_id IN (SELECT cascade_id FROM cascades WHERE session_id = ?)
    AND metadata_key = 'preflight_vectors'
""")

# Get CHECK from epistemic_assessments
check = db.execute("""
    SELECT * FROM epistemic_assessments
    WHERE cascade_id IN (SELECT cascade_id FROM cascades WHERE session_id = ?)
    AND phase = 'CHECK'
""")

# Get POSTFLIGHT from epistemic_assessments
postflight = db.execute("""
    SELECT * FROM epistemic_assessments
    WHERE cascade_id IN (SELECT cascade_id FROM cascades WHERE session_id = ?)
    AND phase = 'POSTFLIGHT'
""")

# Results in THREE result sets from THREE different queries
# on THREE different tables with THREE different schemas
```

**Problems:**
- Three separate queries = 3x slower
- Three different schemas = complex join logic
- Three different locations = must know where each phase stored
- Higher chance of query bugs (one schema mismatch breaks everything)

---

## Guarantee 3: Referential Integrity

### Unified Storage (CORRECT)

```sql
-- Single reflexes table has:
-- - session_id (FK to sessions)
-- - cascade_id (FK to cascades)
-- - phase, round, timestamp
-- - all 13 vectors
-- - reflex_data (JSON), reasoning, evidence

-- Database enforces integrity:
ALTER TABLE reflexes
ADD FOREIGN KEY (session_id) REFERENCES sessions(session_id);

-- If a cascade is deleted, reflexes are cleaned up automatically
DELETE FROM cascades WHERE cascade_id = ?
-- → reflexes rows are automatically deleted (ON DELETE CASCADE)
```

**Guarantee:** Data structure is enforced by database.

### Scattered Storage (BROKEN)

```
cascade_metadata → cascade_id (linked to cascades)
epistemic_assessments → cascade_id (linked to cascades)
reflexes → cascade_id (linked to cascades)

If a cascade is deleted:
- cascade_metadata might be cleaned up
- epistemic_assessments might not be
- reflexes might not be

Result: Orphaned records in three different tables!
```

**Problem:** No single referential integrity model.

---

## Guarantee 4: Atomic Completion

### Unified Storage (CORRECT)

```python
# Atomic checkpoint:
checkpoint_id = logger.add_checkpoint(...)

# Either:
# - All three layers written AND checkpoint_id returned (success)
# - Nothing written AND exception raised (failure)
#
# No middle state where:
# - SQLite written but git notes failed
# - git notes written but JSON failed
# - etc.
```

### Scattered Storage (BROKEN)

```python
# Step 1: Write to cascade_metadata
db.conn.execute(...)
db.conn.commit()  # SUCCESS

# Step 2: Write to git notes
auto_checkpoint(...)  # If this fails:
                      # - cascade_metadata already committed (not rolled back)
                      # - git notes not created
                      # - System is PARTIALLY written

# Step 3: Write to JSON (PREFLIGHT never does this)
# If anyone was expecting JSON logs: disappointed!
```

**Problem:** Partial writes leave system in inconsistent state.

---

## Guarantee 5: Audit Trail Continuity

### Unified Storage (CORRECT)

```python
# All three layers linked by checkpoint_id:
checkpoint_id = "abc-123"

# SQLite: reflexes.reflex_data contains checkpoint_id
# Git notes: refs/notes/.../abc-123 contains the checkpoint
# JSON logs: .empirica_reflex_logs/.../abc-123.json contains full data

# Inspector can navigate: reflexes → git notes → JSON logs
cursor.execute("""
    SELECT reflex_data FROM reflexes WHERE checkpoint_id = ?
""", (checkpoint_id,))
```

### Scattered Storage (BROKEN)

```
PREFLIGHT:
  - cascade_metadata (no checkpoint_id)
  - git notes (disconnected from reflexes)
  - JSON logs (missing)

CHECK:
  - epistemic_assessments (hardcoded vectors, wrong data)
  - git notes (compressed, incomplete)

POSTFLIGHT:
  - epistemic_assessments (missing reflex_log_path)
  - git notes (valid)
  - JSON logs (valid but not linked)

Result: Inspector can't navigate between layers!
```

---

## The Cost of Scattered Storage

### Runtime Cost

```
Unified (one query):
SELECT * FROM reflexes WHERE session_id = ?
  → 1 query, all data in one result set, 10ms

Scattered (three queries):
SELECT ... FROM cascade_metadata WHERE ...
SELECT ... FROM epistemic_assessments WHERE phase='CHECK'
SELECT ... FROM epistemic_assessments WHERE phase='POSTFLIGHT'
  → 3 queries, three different schemas, 30ms
  → Complex join logic in application code
```

**3x slower for same result.**

### Code Cost

```
Unified: 20 lines of code
  logger.add_checkpoint(phase, vectors, metadata)
  # Done. Done. Done.

Scattered: 200+ lines of code
  # PREFLIGHT: cascade_metadata write + git checkpoint
  # CHECK: epistemic_assessments write + decision logic + git checkpoint
  # POSTFLIGHT: epistemic_assessments write + delta calc + no reflex_log_path + git checkpoint
  # Duplicate decision logic in 3 places
```

**10x more code to maintain.**

### Testing Cost

```
Unified: 1 test
  def test_add_checkpoint_writes_three_layers():
    checkpoint_id = logger.add_checkpoint(...)
    assert sqlite_has_data()
    assert git_notes_has_data()
    assert json_logs_have_data()

Scattered: 9 tests
  test_preflight_cascade_metadata()
  test_preflight_git_notes()
  test_check_epistemic_assessments()
  test_check_decision_logic_path1()
  test_check_decision_logic_path2()
  test_postflight_epistemic_assessments()
  test_postflight_delta_calc()
  test_postflight_git_notes()
  test_postflight_missing_reflex_log_path()
```

**9x more test cases.**

---

## Lessons from Distributed Systems

This isn't theoretical—we're violating well-known principles from distributed systems theory:

### CAP Theorem Applied to Storage

```
Consistency: All storage layers have same data
Availability: Can always write
Partition Tolerance: Graceful degradation

Unified storage achieves: CAP
Scattered storage achieves: Only A (sometimes P)
```

### Saga Pattern (Distributed Transactions)

**Unified (single ACID transaction):**
```
PREFLIGHT assessment → [SQLite + Git Notes + JSON] → Done
```

**Scattered (saga pattern):**
```
cascade_metadata → (commit)
↓
auto_checkpoint → (might fail)
↓
JSON logs → (never called for PREFLIGHT)

If step 2 fails: step 1 already committed (no rollback!)
```

**Recommendation:** Don't use saga pattern when ACID transaction (unified storage) is available!

---

## Why Parallel Writes ARE Justified

The spec says three layers exist for good reasons:

1. **SQLite (reflexes table)**: Dashboard queries, fast lookups, aggregation
2. **Git notes**: Distributed version control, crypto signing, external systems
3. **JSON logs**: Audit trail, full reasoning, debugging

**But they should be written ONCE via ONE method** that handles all three atomically.

```
❌ WRONG: Three separate code paths that write to different layers at different times
✅ RIGHT: One method that writes to all three layers in one atomic operation
```

---

## The Correct Pattern

From STORAGE_ARCHITECTURE_COMPLETE.md (lines 19-22):

```
GitEnhancedReflexLogger
  └─ add_checkpoint(phase, round, vectors, meta)
      ├─ Write to SQLite (reflexes)
      ├─ Write to Git Notes (compressed)
      └─ Write to JSON Logs (full)

      All in ONE function call
      All atomic (succeed together or fail together)
```

This is the **single point of truth** for writing epistemic data.

---

## Implementation Strategy

### Current (BROKEN)

```python
# cascade_commands.py - PREFLIGHT
db.conn.execute("INSERT INTO cascade_metadata...")
auto_checkpoint(...)

# workflow_commands.py - CHECK
db.conn.execute("INSERT INTO epistemic_assessments...")

# cascade_commands.py - POSTFLIGHT
db.conn.execute("INSERT INTO epistemic_assessments...")
auto_checkpoint(...)
```

### Correct (UNIFIED)

```python
# All phases use the same pattern
logger = GitEnhancedReflexLogger(session_id=session_id)
checkpoint_id = logger.add_checkpoint(
    phase=phase,  # PREFLIGHT, CHECK, ACT, POSTFLIGHT
    round_num=round,
    vectors=vectors,
    metadata=metadata
)
```

**Single method, same pattern, every time.**

---

## Verification: Before vs After

### Before (scattered storage)

```
Session abc-123:

PREFLIGHT: WHERE?
  SQLite reflexes: NOT FOUND
  Git notes: EXISTS but incomplete
  JSON logs: MISSING

CHECK: WHERE?
  SQLite reflexes: NOT FOUND
  epistemic_assessments: FOUND but hardcoded vectors!
  Git notes: EXISTS
  JSON logs: MISSING

POSTFLIGHT: WHERE?
  SQLite reflexes: NOT FOUND
  epistemic_assessments: FOUND
  Git notes: EXISTS
  JSON logs: EXISTS but not linked
```

### After (unified storage)

```
Session abc-123:

PREFLIGHT:
  SQLite reflexes: ✓ (know=0.75, do=0.80, ...)
  Git notes: ✓ (compressed)
  JSON logs: ✓ (linked via reflex_log_path)

CHECK:
  SQLite reflexes: ✓ (know=0.92, do=0.87, ...)
  Git notes: ✓ (compressed)
  JSON logs: ✓ (linked via reflex_log_path)

POSTFLIGHT:
  SQLite reflexes: ✓ (know=0.95, do=0.90, ...)
  Git notes: ✓ (compressed)
  JSON logs: ✓ (linked via reflex_log_path)

Complete learning curve:
  PREFLIGHT → CHECK → POSTFLIGHT
  All queryable in single SELECT
  All verifiable via git history
  All debuggable via JSON logs
```

---

## Conclusion

**Unified storage is not just cleaner code—it's a fundamental architectural requirement** for:

- ✅ Consistency (ACID guarantees)
- ✅ Query efficiency (single query vs 3)
- ✅ Code maintainability (one pattern vs scattered)
- ✅ Audit trails (linked across all layers)
- ✅ Testing (fewer test cases)
- ✅ Future features (dashboards, crypto signing, drift detection)

**The fix is straightforward:** Use `GitEnhancedReflexLogger.add_checkpoint()` for all assessment phases.

