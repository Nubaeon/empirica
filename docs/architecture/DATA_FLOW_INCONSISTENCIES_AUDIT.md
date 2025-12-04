# Empirica Data Flow Inconsistencies Audit

**Date:** 2025-12-04
**Status:** CRITICAL - Multiple storage path violations
**Severity:** High - Storage architecture violated in 3 assessment phases

---

## Executive Summary

The implementation **violates the documented storage architecture** in three critical ways:

1. **PREFLIGHT**: Writes to wrong table (`cascade_metadata` instead of `reflexes`)
2. **CHECK**: Stores hardcoded dummy vectors instead of submitted assessment
3. **POSTFLIGHT**: Missing `reflex_log_path` link to JSON audit logs

**Result**: Statusline dashboard can't find complete epistemic state, delta calculations are lost, and audit trail is broken.

---

## Architecture Spec vs Reality

### The Spec (from STORAGE_ARCHITECTURE_COMPLETE.md)

```
Epistemic Event (AI assessment)
    ↓
GitEnhancedReflexLogger.add_checkpoint()
    ↓
Single unified call writes to ALL THREE layers atomically:
    ├─→ SQLite reflexes table (full vectors + metadata)
    ├─→ Git Notes (compressed checkpoint)
    └─→ JSON Logs (full reasoning for audit)
```

**Key principle from STORAGE_ARCHITECTURE_VISUAL_GUIDE.md:**

> "Three parallel writes from GitEnhancedReflexLogger... Different storage for different use cases"
>
> **But crucially: writes happen ONCE via ONE method** to ensure consistency

---

## Critical Violations Found

### VIOLATION 1: PREFLIGHT Writes to Wrong Table

**Location**: `empirica/cli/command_handlers/cascade_commands.py:234-254`

**What the code does:**
```python
# Creates a CASCADE record
cascade_id = db.create_cascade(
    session_id=session_id,
    task=f"PREFLIGHT: {prompt}",
    context={"phase": "preflight", "prompt": prompt}
)

# Writes vectors to cascade_metadata, NOT reflexes!
db.conn.execute("""
    INSERT INTO cascade_metadata (cascade_id, metadata_key, metadata_value)
    VALUES (?, ?, ?)
""", (cascade_id, "preflight_vectors", json.dumps(vectors)))
```

**What should happen (per spec):**
```python
# Should call GitEnhancedReflexLogger.add_checkpoint() which writes to:
# 1. reflexes table (SQLite)
# 2. Git Notes (compressed)
# 3. JSON Logs (full)
```

**Impact:**
- Statusline queries SQLite `reflexes` table → finds NOTHING for PREFLIGHT
- Audit trail (JSON logs) never created
- Git checkpoint created (line 258) but with incomplete vector data
- PREFLIGHT cannot be compared to POSTFLIGHT for delta (vectors in wrong place)

**Evidence:**
```sql
-- This statusline query FAILS for PREFLIGHT:
SELECT phase, AVG(know) FROM reflexes WHERE session_id = ?
-- Returns: NO PREFLIGHT RECORDS (they're in cascade_metadata!)
```

---

### VIOLATION 2: CHECK Stores Hardcoded Dummy Vectors

**Location**: `empirica/cli/command_handlers/workflow_commands.py:188-196`

**What the code does:**
```python
# AI submits these vectors:
# vectors = {
#     "know": 0.92,
#     "do": 0.87,
#     "clarity": 0.95,
#     ... (real assessment)
# }

# System IGNORES them and stores hardcoded values:
db.conn.execute("""
    INSERT INTO epistemic_assessments
    (assessment_id, cascade_id, phase, engagement, know, do, context, ...)
    VALUES (?, ?, 'CHECK', 0.75, 0.7, 0.75, 0.75, ...)  # ALL HARDCODED!
""", (str(uuid.uuid4()), cascade_id, uncertainty, confidence, recommended_action, now))
```

**What should happen:**
```python
# Use submitted vectors directly:
vectors = _extract_all_vectors(args.vectors)  # Get real vectors
logger_instance.add_checkpoint(
    phase="CHECK",
    round_num=cycle,
    vectors=vectors,  # USE ACTUAL SUBMITTED VECTORS
    metadata={"decision": decision, "reasoning": reasoning}
)
```

**Impact:**
- CHECK assessment permanently loses all epistemic data
- Dashboard shows dummy 0.75 vectors instead of actual confidence state
- Learning curves calculated from fake data
- Statusline velocity calculations meaningless (based on dummy vectors)
- Drift detection broken (comparing to fake CHECK data)

**Evidence:**
Two different code paths handle CHECK:
1. `handle_check_command()` (line 149) - Creates cascade + epistemic_assessments with **HARDCODED values**
2. `handle_check_submit_command()` (line 247) - Uses **REAL vectors** from args

**Why this happened**: Two different CLI commands, two different storage paths, no unified interface.

---

### VIOLATION 3: POSTFLIGHT Missing Reflex Log Link

**Location**: `empirica/cli/command_handlers/cascade_commands.py:670+`

**Schema expectation** (from session_database.py):
```sql
CREATE TABLE epistemic_assessments (
    ...
    reflex_log_path TEXT,  -- Link to reflex frame JSON file
    ...
)
```

**What the code does:**
- POSTFLIGHT stores vectors, confidence, calibration
- **Never populates `reflex_log_path`**
- JSON logs created somewhere else, but link never stored

**What should happen:**
```python
logger_instance.add_checkpoint(
    phase="POSTFLIGHT",
    round_num=1,
    vectors=postflight_vectors,
    metadata={
        "calibration": calibration,
        "delta": delta,
        "reflex_log_path": f".empirica_reflex_logs/{date}/{ai_id}/{session_id}/POSTFLIGHT.json"
    }
)
```

**Impact:**
- Audit trail broken (can't trace back from epistemic_assessments to JSON logs)
- Debugging impossible (inspector can't find full reasoning for assessment)
- Regulatory compliance broken (audit trail incomplete)
- Crypto signing broken for Phase 2 (no reference to actual log file)

---

## Secondary Issues: Scattered Decision Logic

### CHECK Decision Calculated Twice

**Location**: `workflow_commands.py:186` and `workflow_commands.py:207`

```python
# Line 186: Calculate decision from confidence
recommended_action = "proceed" if confidence >= 0.7 else "investigate" if confidence <= 0.3 else "proceed_with_caution"

# ... 20 lines later ...

# Line 207: Calculate decision AGAIN (identical logic)
"decision": "proceed" if confidence >= 0.7 else "investigate" if confidence <= 0.3 else "proceed_with_caution",
```

**Impact:**
- Code duplication (maintenance nightmare)
- Decision logic scattered across two places
- Hard to change decision thresholds consistently
- Test coverage unclear (which one is tested?)

---

## Storage Path Decision Matrix

### Current Implementation (BROKEN)

| Phase | Intended | Actual | Issue |
|-------|----------|--------|-------|
| **PREFLIGHT** | reflexes table | cascade_metadata | Wrong table |
| **CHECK** | reflexes + real vectors | epistemic_assessments + dummy vectors | Wrong data + wrong table |
| **ACT** | reflexes + actual vectors | ??? | Unknown/untested |
| **POSTFLIGHT** | reflexes + reflex_log_path link | epistemic_assessments, no link | Wrong table + missing link |

### Correct Implementation (Per Spec)

All phases should use **GitEnhancedReflexLogger.add_checkpoint()** which atomically writes to:

| Layer | Location | Trigger |
|-------|----------|---------|
| **SQLite** | reflexes table | add_checkpoint() |
| **Git Notes** | refs/notes/empirica/session/{id}/{phase}/{round} | add_checkpoint() |
| **JSON Logs** | .empirica_reflex_logs/{date}/{ai}/{session}/{phase}.json | add_checkpoint() |

---

## Why Parallel Writes Make Sense

From STORAGE_ARCHITECTURE_VISUAL_GUIDE.md (lines 27-33):

> "Three parallel writes from GitEnhancedReflexLogger"
>
> "Different storage for different use cases:
> - SQLite: Fast SQL queries for dashboards
> - Git Notes: Compressed, distributed, crypto-signable
> - JSON Logs: Full reasoning for debugging"

**BUT** - writes happen atomically in ONE call:

```python
# This is what SHOULD happen (and what spec describes)
logger_instance.add_checkpoint(
    phase="PREFLIGHT",
    vectors=vectors,
    metadata=metadata
)
# ^ Single call, three layers written atomically
```

**NOT** what currently happens:

```python
# Current code does:
db.conn.execute(...)  # Write to cascade_metadata (WRONG)
auto_checkpoint(...)  # Write to git notes (partial)
# JSON never written for PREFLIGHT
# RefreshLog path never recorded
```

---

## Impact on Dependent Systems

### Statusline Dashboard (BROKEN)

Expected to query:
```sql
SELECT phase, know, do, context, uncertainty, overall_confidence
FROM reflexes
WHERE session_id = ? AND phase IN ('PREFLIGHT', 'CHECK', 'POSTFLIGHT')
```

**Actual results:**
- PREFLIGHT: MISSING (in cascade_metadata, not reflexes)
- CHECK: WRONG DATA (hardcoded 0.75, not submitted vectors)
- POSTFLIGHT: PRESENT but no reflex_log_path link

**Result**: Dashboard shows incomplete/incorrect epistemic state

### Drift Detection (BROKEN)

Mirror Drift Monitor expects CHECK vectors to compare against PREFLIGHT:
```python
# Get baseline from PREFLIGHT
preflight = db.query("SELECT * FROM reflexes WHERE phase='PREFLIGHT'")
# Get current from CHECK
check = db.query("SELECT * FROM reflexes WHERE phase='CHECK'")
# Detect drift
drift = calculate_drift(preflight, check)
```

**Actual result:**
- PREFLIGHT query returns nothing (wrong table)
- CHECK query returns dummy 0.75 vectors (wrong data)
- Drift detection meaningless

### Learning Curve Tracking (BROKEN)

Expected to show KNOW growth:
```
PREFLIGHT: know=0.75
CHECK 1:   know=0.82
CHECK 2:   know=0.90
POSTFLIGHT: know=0.95
```

**Actual result:**
```
PREFLIGHT: (missing)
CHECK 1:   know=0.75 (hardcoded)
CHECK 2:   know=0.75 (hardcoded)
POSTFLIGHT: know=0.95 (real)
```

Looks like learning only happened in POSTFLIGHT (false signal).

---

## Recommended Fix Strategy

### Phase 1: Unify to Single Storage Path

**For all assessment phases**, use GitEnhancedReflexLogger:

```python
def handle_preflight_command(args):
    # ... get vectors ...

    logger = GitEnhancedReflexLogger(session_id=session_id)
    checkpoint_id = logger.add_checkpoint(
        phase="PREFLIGHT",
        round_num=1,
        vectors=vectors,
        metadata={
            "task": prompt,
            "reasoning": reasoning,
            "recommendation": recommendation
        }
    )
    # ^ Single call writes to SQLite + Git Notes + JSON atomically
```

**Benefit**:
- No scattered storage paths
- Audit trail complete
- Statusline finds complete data
- Drift detection works correctly

### Phase 2: Eliminate Dummy Data in CHECK

Replace hardcoded values:
```python
# BEFORE (wrong):
VALUES (?, ?, 'CHECK', 0.75, 0.7, 0.75, 0.75, ...)

# AFTER (correct):
VALUES (?, ?, 'CHECK', vectors['engagement'], vectors['know'],
        vectors['do'], vectors['context'], ...)
```

### Phase 3: Add reflex_log_path Linking

Persist reference in metadata:
```python
metadata={
    "reflex_log_path": checkpoint_id  # Returned by add_checkpoint
}
```

### Phase 4: Centralize Decision Logic

Single decision function:
```python
def calculate_decision(confidence: float) -> str:
    """Single source of truth for CHECK decision logic"""
    if confidence >= 0.7:
        return "proceed"
    elif confidence <= 0.3:
        return "investigate"
    else:
        return "proceed_with_caution"
```

---

## Testing Impact

Current tests that will break when fixed:

| File | Issue | Fix |
|------|-------|-----|
| `tests/unit/cascade/test_preflight.py` | Tests write to cascade_metadata | Update to query reflexes |
| `tests/unit/cascade/test_check.py` | Tests hardcoded values | Use actual submitted vectors |
| `tests/unit/cascade/test_postflight.py` | No reflex_log_path tests | Add path linking tests |

---

## Storage Architecture Compliance Checklist

- [ ] **PREFLIGHT**: Uses `GitEnhancedReflexLogger.add_checkpoint()`
- [ ] **CHECK**: Uses submitted vectors (not hardcoded)
- [ ] **ACT**: Stores actual epistemic state
- [ ] **POSTFLIGHT**: Includes `reflex_log_path` in metadata
- [ ] All phases write to reflexes table (not cascade_metadata or epistemic_assessments)
- [ ] All phases create git notes in correct namespace
- [ ] All phases create JSON logs in correct directory
- [ ] No scattered storage paths or duplicate writes
- [ ] Decision logic centralized in one function
- [ ] Statusline queries return complete data for all phases

---

## References

- **Storage Architecture Spec**: `docs/architecture/STORAGE_ARCHITECTURE_COMPLETE.md`
- **Visual Guide**: `docs/architecture/STORAGE_ARCHITECTURE_VISUAL_GUIDE.md`
- **Reflex Logger**: `empirica/core/canonical/git_enhanced_reflex_logger.py`
- **Session Database**: `empirica/data/session_database.py`
- **Broken Command Handlers**:
  - `empirica/cli/command_handlers/cascade_commands.py` (lines 234-254, 413-700)
  - `empirica/cli/command_handlers/workflow_commands.py` (lines 149-244, 247-336)

---

**This audit documents systematic violations of documented architecture that must be fixed before the data flow can be trusted for metacognitive signaling or calibration.**
