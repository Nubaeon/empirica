# Database Schema Uniformity Migration Spec

**Status:** Ready for Sonnet Implementation
**Date:** 2025-12-05
**Priority:** High (blocking pre-deployment phase)
**Scope:** Complete removal of deprecated epistemic tables, unified to reflexes table

---

## I. EXECUTIVE SUMMARY

Currently, the database has **two competing systems**:
- **OLD (Deprecated):** `epistemic_assessments`, `preflight_assessments`, `postflight_assessments`, `check_phase_assessments` tables
- **NEW (Canonical):** `reflexes` table (stores all 13 vectors with phase information)

**Goal:** Complete migration to `reflexes` table only, with all code paths redirected.

**Why now:** Before deploying to production users, we need uniform storage. Currently 11 code files read/write deprecated tables, creating confusion and maintenance burden.

**Success Criteria:**
- All code reads from `reflexes` table only
- All writes go to `reflexes` table only
- Deprecated tables deleted from schema
- All tests pass
- No data loss (backward compatibility during transition)

---

## II. CURRENT STATE ANALYSIS

### Deprecated Tables (To Be Removed)
```sql
epistemic_assessments     -- Old 12-vector system (UNUSED, can delete)
preflight_assessments     -- 13-vector + metadata (MIGRATE TO reflexes)
postflight_assessments    -- 13-vector + metadata (MIGRATE TO reflexes)
check_phase_assessments   -- Confidence + decision (MIGRATE TO reflexes)
```

### Canonical Table (Target)
```sql
reflexes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    cascade_id TEXT,
    phase TEXT NOT NULL,  -- 'PREFLIGHT', 'CHECK', 'POSTFLIGHT'
    round INTEGER DEFAULT 1,
    timestamp REAL NOT NULL,

    -- 13 epistemic vectors
    engagement REAL,
    know REAL,
    do REAL,
    context REAL,
    clarity REAL,
    coherence REAL,
    signal REAL,
    density REAL,
    state REAL,
    change REAL,
    completion REAL,
    impact REAL,
    uncertainty REAL,

    -- Metadata (flexible JSON)
    reflex_data TEXT,
    reasoning TEXT,
    evidence TEXT,

    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
)
```

### Migration Mapping

| Old Table | Phase | Maps To reflexes | Data Mapping |
|-----------|-------|-----------------|--------------|
| `preflight_assessments` | PREFLIGHT | `reflexes` WHERE phase='PREFLIGHT' | All 13 vectors + prompt_summary → reflex_data |
| `check_phase_assessments` | CHECK | `reflexes` WHERE phase='CHECK' | confidence → uncertainty (inverse), decision → reflex_data |
| `postflight_assessments` | POSTFLIGHT | `reflexes` WHERE phase='POSTFLIGHT' | All 13 vectors + task_summary → reflex_data |
| `epistemic_assessments` | Various | `reflexes` | Unused (delete, no migration needed) |

---

## III. IMPLEMENTATION PLAN (Staged)

### STAGE 1: Code Migration (Data Reads/Writes)

**Target:** Update all code to use `reflexes` table via SessionDatabase methods

**Files to Update (Priority Order):**

#### 1.1 CRITICAL: `session_database.py`
**Impact:** Core API - ALL other code depends on this

**Changes:**
```python
# REMOVE these methods (they write to deprecated tables):
- log_preflight_assessment()        # Line 799
- log_check_phase_assessment()      # Line 861
- log_postflight_assessment()       # Line 916

# REMOVE these methods (they read from deprecated tables):
- get_preflight_assessment()        # Line 1174
- get_check_phase_assessments()     # Line 1186
- get_postflight_assessment()       # Line 1196

# KEEP & UPDATE these methods (already use reflexes):
- store_vectors()                   # Already correct (line 1510)
- get_latest_vectors()              # Already correct (line 1560)
- get_vectors_by_phase()            # Create if missing

# ADD new methods for common patterns:
- get_preflight_vector(session_id) -> returns latest PREFLIGHT from reflexes
- get_postflight_vector(session_id) -> returns latest POSTFLIGHT from reflexes
- get_check_vectors(session_id) -> returns all CHECK phases from reflexes
```

**Rationale:** These are wrapper methods that code already calls. By replacing the implementation to query `reflexes`, we update 70% of the codebase automatically.

#### 1.2 HIGH: `report_generator.py`
**Impact:** Handoff reports (production)

**Current Code (Lines 268-348):**
```python
def _get_preflight_assessment(self, session_id):
    cursor = db.conn.cursor()
    cursor.execute("""SELECT * FROM preflight_assessments WHERE session_id = ?""")
```

**Updated Code:**
```python
def _get_preflight_assessment(self, session_id):
    # Use SessionDatabase API instead of raw queries
    from empirica.data.session_database import SessionDatabase
    db = SessionDatabase()
    vectors_data = db.get_latest_vectors(session_id, phase="PREFLIGHT")
    return {
        "vectors": vectors_data['vectors'],
        "timestamp": vectors_data['timestamp'],
        "phase": "PREFLIGHT"
    }
    db.close()
```

**Changes Required:**
- Replace `_get_preflight_assessment()` implementation
- Replace `_get_postflight_assessment()` implementation
- Update calibration_accuracy logic (fetch from reflex_data JSON, not schema column)

#### 1.3 MEDIUM: `sessions.py` (API Routes)
**Impact:** API endpoints used by dashboard

**Current Code (Line 207-245):**
```python
def get_session_checks(session_id):
    cursor.execute("SELECT * FROM check_phase_assessments WHERE session_id = ?")
```

**Updated Code:**
```python
def get_session_checks(session_id):
    db = SessionDatabase()
    checks = db.get_vectors_by_phase(session_id, phase="CHECK")
    db.close()
    return [
        {
            "phase": "CHECK",
            "cycle": check['round'],
            "vectors": check['vectors'],
            "timestamp": check['timestamp']
        }
        for check in checks
    ]
```

#### 1.4 LOW: Test Files (5 files)
- `test_phase1.6_handoff_reports.py` - Replace INSERTs with SessionDatabase.store_vectors()
- `test_mini_agent_handoff_e2e.py` - Same
- `test_reflex_logging_integration.py` - Update schema validation
- `verify_empirica_integration.py` - Update PRAGMA queries
- Example code in `/examples` - Update queries

#### 1.5 LOW: Utility Files (4 files)
- `session_replay.py` - Use reflexes instead of epistemic_assessments
- `cascade_monitor.py` - Use reflexes with phase filter
- `session_json_handler.py` - Query reflexes phase column
- Example code - Update to reflexes queries

---

### STAGE 2: Data Backward Compatibility (Optional but Recommended)

**During transition:** Keep deprecated tables for rollback

**Option A (Safest): Dual-Write Period**
```python
# In log_preflight_assessment() replacement:
def store_preflight_vectors(self, session_id, vectors, ...):
    # Write to reflexes (new)
    self.store_vectors(session_id, 'PREFLIGHT', vectors, ...)

    # TEMPORARILY also write to preflight_assessments (old) for safety
    # This allows rollback if reflexes has bugs
    # REMOVE THIS BLOCK after 1 week of production validation
    cursor.execute("""INSERT INTO preflight_assessments ...""")
```

**Option B (Clean): No Dual-Write**
- Migrate code first
- Delete deprecated tables immediately
- Faster, cleaner, but zero rollback option

**Recommendation:** Option B (we control the only production system, can recover from git if needed)

---

### STAGE 3: Schema Cleanup

**After all code migrated and tested:**

```python
# In session_database.py _create_tables():
# REMOVE these CREATE TABLE statements:
cursor.execute("DROP TABLE IF EXISTS epistemic_assessments")
cursor.execute("DROP TABLE IF EXISTS preflight_assessments")
cursor.execute("DROP TABLE IF EXISTS postflight_assessments")
cursor.execute("DROP TABLE IF EXISTS check_phase_assessments")
```

**Migration Script:**
```bash
# For existing databases (backward compat):
# This migration should run automatically on next SessionDatabase init

def _migrate_if_needed(self):
    """Migrate data from old tables to reflexes if old tables exist"""
    cursor = self.conn.cursor()

    try:
        # Check if old tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='preflight_assessments'")
        if not cursor.fetchone():
            return  # Already migrated

        # Migrate preflight_assessments → reflexes
        cursor.execute("""
            INSERT INTO reflexes (session_id, phase, round, timestamp,
                                engagement, know, do, context, clarity, coherence, signal, density,
                                state, change, completion, impact, uncertainty, reflex_data)
            SELECT session_id, 'PREFLIGHT', 1, assessed_at,
                   engagement, know, do, context, clarity, coherence, signal, density,
                   state, change, completion, impact, uncertainty, vectors_json
            FROM preflight_assessments
            WHERE NOT EXISTS (
                SELECT 1 FROM reflexes r
                WHERE r.session_id = preflight_assessments.session_id
                AND r.phase = 'PREFLIGHT'
            )
        """)

        # Similar for check_phase_assessments, postflight_assessments
        # ...

        self.conn.commit()
        logger.info("✓ Migrated legacy tables to reflexes")

        # Drop old tables
        for table in ['epistemic_assessments', 'preflight_assessments',
                      'postflight_assessments', 'check_phase_assessments']:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")

        self.conn.commit()
        logger.info("✓ Deleted deprecated tables")

    except Exception as e:
        logger.warning(f"Migration check failed (may be OK): {e}")
```

---

## IV. DETAILED FILE-BY-FILE CHANGES

### 4.1 session_database.py

**Lines to DELETE:**
```
Lines 72-162: Old table creation and migrations (epistemic_assessments references)
Lines 175-226: epistemic_assessments CREATE TABLE
Lines 327-356: preflight_assessments CREATE TABLE
Lines 358-377: check_phase_assessments CREATE TABLE
Lines 379-412: postflight_assessments CREATE TABLE
Lines 658-703: log_epistemic_assessment() method
Lines 799-859: log_preflight_assessment() method
Lines 861-914: log_check_phase_assessment() method
Lines 916-974: log_postflight_assessment() method
Lines 1174-1206: get_preflight_assessment(), get_check_phase_assessments(), get_postflight_assessment() methods
```

**Lines to ADD (New Methods):**
```python
def get_preflight_vectors(self, session_id: str) -> Optional[Dict]:
    """Get latest PREFLIGHT vectors for session (convenience method)"""
    return self.get_latest_vectors(session_id, phase="PREFLIGHT")

def get_check_vectors(self, session_id: str, cycle: Optional[int] = None) -> List[Dict]:
    """Get CHECK phase vectors, optionally filtered by cycle"""
    cursor = self.conn.cursor()
    query = "SELECT * FROM reflexes WHERE session_id = ? AND phase = 'CHECK' ORDER BY round"
    cursor.execute(query, (session_id,))
    return [dict(row) for row in cursor.fetchall()]

def get_postflight_vectors(self, session_id: str) -> Optional[Dict]:
    """Get latest POSTFLIGHT vectors for session (convenience method)"""
    return self.get_latest_vectors(session_id, phase="POSTFLIGHT")

def get_vectors_by_phase(self, session_id: str, phase: str) -> List[Dict]:
    """Get all vectors for a specific phase"""
    cursor = self.conn.cursor()
    cursor.execute(
        "SELECT * FROM reflexes WHERE session_id = ? AND phase = ? ORDER BY timestamp",
        (session_id, phase)
    )
    return [dict(row) for row in cursor.fetchall()]
```

**Lines to UPDATE:**
```
Lines 1434-1508: _get_checkpoint_from_reflexes() - Remove fallback to old tables
Lines 1510-1558: store_vectors() - Already correct, no change
Lines 1560-1602: get_latest_vectors() - Already correct, no change
Lines 1239-1320: get_session_summary() - Update to use reflexes, remove cascade_metadata queries
```

### 4.2 report_generator.py (Lines 268-348)

**Replace entire `_get_preflight_assessment()` method:**
```python
def _get_preflight_assessment(self, session_id: str) -> Dict:
    """Get preflight vectors for handoff report"""
    from empirica.data.session_database import SessionDatabase

    db = SessionDatabase()
    try:
        vectors_data = db.get_latest_vectors(session_id, phase="PREFLIGHT")
        if not vectors_data:
            return None

        return {
            "vectors": vectors_data['vectors'],
            "timestamp": vectors_data['timestamp']
        }
    finally:
        db.close()
```

**Replace entire `_get_postflight_assessment()` method:**
```python
def _get_postflight_assessment(self, session_id: str) -> Dict:
    """Get postflight vectors for handoff report"""
    from empirica.data.session_database import SessionDatabase

    db = SessionDatabase()
    try:
        vectors_data = db.get_latest_vectors(session_id, phase="POSTFLIGHT")
        if not vectors_data:
            return None

        vectors = vectors_data['vectors']

        # For calibration accuracy, check if it's in reflex_data metadata
        calibration = "unknown"
        if vectors_data.get('reflex_data'):
            metadata = json.loads(vectors_data['reflex_data'])
            calibration = metadata.get('calibration_accuracy', 'unknown')

        return {
            "vectors": vectors,
            "calibration": calibration,
            "timestamp": vectors_data['timestamp']
        }
    finally:
        db.close()
```

### 4.3 sessions.py (API routes, Lines 207-245)

**Replace `get_session_checks()` function:**
```python
def get_session_checks(session_id: str):
    """Get CHECK phase assessments for session"""
    from empirica.data.session_database import SessionDatabase

    db = SessionDatabase()
    try:
        checks = db.get_vectors_by_phase(session_id, phase="CHECK")

        return [
            {
                "cycle": check['round'],
                "phase": "CHECK",
                "vectors": check['vectors'],
                "timestamp": check['timestamp'],
                "metadata": json.loads(check.get('reflex_data', '{}')) if check.get('reflex_data') else {}
            }
            for check in checks
        ]
    finally:
        db.close()
```

### 4.4 Test Files

**test_reflex_logging_integration.py**
- Replace PRAGMA queries to check reflexes table columns instead
- Remove assertions for preflight_assessments/postflight_assessments existence

**test_phase1.6_handoff_reports.py**
```python
# OLD:
cursor.execute("""INSERT INTO preflight_assessments (...)""")

# NEW:
db = SessionDatabase()
db.store_vectors(session_id, "PREFLIGHT", vectors_dict)
db.close()
```

**test_mini_agent_handoff_e2e.py**
- Same pattern as above

**verify_empirica_integration.py**
- Update schema verification to check only reflexes table exists

---

## V. MIGRATION TESTING CHECKLIST

- [ ] **Unit Tests:** All SessionDatabase methods work with reflexes only
- [ ] **Integration Tests:** Handoff reports generate correctly from reflexes data
- [ ] **API Tests:** Session endpoints return correct data structure
- [ ] **Dashboard Tests:** Statusline reads correct cognitive load from reflexes
- [ ] **Data Integrity:** Migrated data has no loss (row count verification)
- [ ] **Backward Compat:** Existing databases auto-migrate on first run
- [ ] **Rollback Plan:** Can restore from git if issues discovered

---

## VI. DEPLOYMENT CHECKLIST

Before merging:
- [ ] All deprecated table reads/writes removed
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Code review completed
- [ ] Documentation updated (remove deprecated table references)
- [ ] Migration script tested on sample database
- [ ] Verify no hanging queries to old tables (grep entire codebase)

---

## VII. ROLLBACK PLAN

If issues discovered post-migration:

1. **Data Recovery:** Old tables still in git history (can restore from backup)
2. **Code Recovery:** Previous commit has working code with deprecated tables
3. **Timeline:** If found within 24 hours, revert commit + restore session.db from backup

---

## VIII. SUCCESS METRICS

- ✅ Single source of truth: reflexes table only
- ✅ No dead code paths reading/writing deprecated tables
- ✅ All tests green
- ✅ Code coverage maintained (>80%)
- ✅ Production deployment ready
- ✅ Documentation updated

---

## IX. HANDOFF NOTES FOR SONNET

1. **Start with:** `session_database.py` - it's the bottleneck
2. **Test early:** Write test_reflexes_migration.py before making changes
3. **Use grep:** Verify no stray queries to old tables remain
4. **Document changes:** Each method removed should have a comment explaining the replacement
5. **Backward compat script:** The migration function should log success/failure clearly

**Estimated effort:** 4-6 hours (mostly testing and verification)

---

## X. APPROVAL & SIGN-OFF

**Spec prepared by:** Claude Code (Haiku, Implementer)
**Ready for:** Claude Sonnet (High-reasoning architect)
**Approval:** User confirmation before Sonnet begins
**Status:** ⏳ Awaiting Sonnet implementation
