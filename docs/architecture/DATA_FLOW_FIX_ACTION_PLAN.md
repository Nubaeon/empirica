# Data Flow Fix Action Plan

**Priority: CRITICAL**
**Blocker Status**: YES - Statusline integration requires this to be fixed

---

## Overview

Three critical data flow issues must be fixed to achieve:
1. Working statusline integration
2. Correct drift detection
3. Valid learning curves
4. Complete audit trails

---

## Issue 1: PREFLIGHT Writes to Wrong Table

### Current Problem
```python
# empirica/cli/command_handlers/cascade_commands.py:242-254
cascade_id = db.create_cascade(...)
db.conn.execute("""
    INSERT INTO cascade_metadata (cascade_id, metadata_key, metadata_value)
    VALUES (?, ?, ?)
""", (cascade_id, "preflight_vectors", json.dumps(vectors)))
```

**Where data ends up:** cascade_metadata table (metadata_key='preflight_vectors')
**Where statusline looks:** reflexes table
**Result:** PREFLIGHT not found by statusline

### Fix

**File:** `empirica/cli/command_handlers/cascade_commands.py` (handle_preflight_command function)

**Replace lines 234-254 with:**

```python
# Unified storage path: use GitEnhancedReflexLogger for all three layers
from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger

# Store preflight using unified storage
logger_instance = GitEnhancedReflexLogger(
    session_id=session_id,
    enable_git_notes=True
)

checkpoint_id = logger_instance.add_checkpoint(
    phase="PREFLIGHT",
    round_num=1,
    vectors=vectors,
    metadata={
        "task": prompt,
        "reasoning": reasoning,
        "recommendation": recommendation['action'],
        "engagement": assessment.engagement.score if hasattr(assessment, 'engagement') else 0.5
    }
)
```

**What this fixes:**
- ✅ Writes to reflexes table (SQLite)
- ✅ Creates git notes (compressed)
- ✅ Creates JSON logs (audit trail)
- ✅ Statusline query finds PREFLIGHT

**Tests affected:** `tests/unit/cascade/test_preflight.py` (update to query reflexes table)

**Verification:**
```bash
$ sqlite3 .empirica/sessions/sessions.db
sqlite> SELECT phase, know, do FROM reflexes WHERE phase='PREFLIGHT';
PREFLIGHT|0.75|0.80
```

---

## Issue 2: CHECK Stores Hardcoded Dummy Vectors

### Current Problem

```python
# empirica/cli/command_handlers/workflow_commands.py:188-196
db.conn.execute("""
    INSERT INTO epistemic_assessments
    (..., engagement, know, do, context, ...)
    VALUES (?, ?, 'CHECK', 0.75, 0.7, 0.75, 0.75, ...)  # HARDCODED!
""", (str(uuid.uuid4()), cascade_id, uncertainty, confidence, recommended_action, now))
```

**Where data ends up:** epistemic_assessments with hardcoded 0.75 values
**What was submitted:** `vectors = {know: 0.92, do: 0.87, ...}` (IGNORED!)
**Result:** Drift detection gets fake data, learning curves wrong

### Fix

**File:** `empirica/cli/command_handlers/workflow_commands.py` (handle_check_command function)

**Replace lines 149-244 with:**

```python
def handle_check_command(args):
    """Handle check command - execute epistemic assessment with real vectors"""
    try:
        from empirica.core.canonical.git_enhanced_reflex_logger import GitEnhancedReflexLogger

        # Parse arguments
        session_id = args.session_id
        findings = parse_json_safely(args.findings) if isinstance(args.findings, str) else args.findings
        unknowns = parse_json_safely(args.unknowns) if isinstance(args.unknowns, str) else args.unknowns
        confidence = args.confidence
        verbose = getattr(args, 'verbose', False)
        cycle = getattr(args, 'cycle', 1)

        # Validate inputs
        if not isinstance(findings, list):
            raise ValueError("Findings must be a list")
        if not isinstance(unknowns, list):
            raise ValueError("Unknowns must be a list")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

        # Get actual vector data from a provided JSON file or args
        vectors = getattr(args, 'vectors', None)
        if vectors:
            if isinstance(vectors, str):
                vectors = parse_json_safely(vectors)
        else:
            # If no vectors provided, use confidence to infer some
            uncertainty = 1.0 - confidence
            vectors = {
                'engagement': 0.75,
                'know': confidence,
                'do': confidence,
                'context': confidence * 0.9,
                'clarity': confidence * 0.95,
                'coherence': confidence * 0.92,
                'signal': confidence * 0.88,
                'density': confidence * 0.85,
                'state': confidence,
                'change': confidence * 0.80,
                'completion': confidence * 0.70,
                'impact': confidence * 0.75,
                'uncertainty': uncertainty
            }

        # Use unified storage path
        logger_instance = GitEnhancedReflexLogger(
            session_id=session_id,
            enable_git_notes=True
        )

        checkpoint_id = logger_instance.add_checkpoint(
            phase="CHECK",
            round_num=cycle,
            vectors=vectors,
            metadata={
                "findings_count": len(findings),
                "unknowns_count": len(unknowns),
                "confidence": confidence,
                "decision": _calculate_decision(confidence),
                "findings": findings[:5],  # Store first 5 for metadata
                "unknowns": unknowns[:5]
            }
        )

        decision = _calculate_decision(confidence)

        result = {
            "ok": True,
            "session_id": session_id,
            "checkpoint_id": checkpoint_id,
            "findings_count": len(findings),
            "unknowns_count": len(unknowns),
            "confidence": confidence,
            "decision": decision,
            "cycle": cycle,
            "timestamp": datetime.utcnow().isoformat()
        }

        if hasattr(args, 'output') and args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            print("✅ CHECK assessment created and stored")
            print(f"   Session: {session_id[:8]}...")
            print(f"   Cycle: {cycle}")
            print(f"   Confidence: {confidence:.2f}")
            print(f"   Decision: {decision.upper()}")
            print(f"   Storage: SQLite + Git Notes + JSON")

        return result

    except Exception as e:
        handle_cli_error(e, "Check assessment", getattr(args, 'verbose', False))


def _calculate_decision(confidence: float) -> str:
    """Single source of truth for CHECK decision logic"""
    if confidence >= 0.7:
        return "proceed"
    elif confidence <= 0.3:
        return "investigate"
    else:
        return "proceed_with_caution"
```

**What this fixes:**
- ✅ Stores actual submitted vectors (not hardcoded)
- ✅ Uses unified storage (SQLite + Git Notes + JSON)
- ✅ Removes duplicate decision logic
- ✅ Drift detection gets real data

**Tests affected:**
- `tests/unit/cascade/test_check.py` (update for unified storage)
- `tests/unit/cascade/test_drift_detection.py` (verify drift works)

**Verification:**
```bash
$ sqlite3 .empirica/sessions/sessions.db
sqlite> SELECT phase, know, do FROM reflexes WHERE phase='CHECK' AND cycle=1;
CHECK|0.92|0.87
```

---

## Issue 3: POSTFLIGHT Missing reflex_log_path Link

### Current Problem

```python
# empirica/cli/command_handlers/cascade_commands.py:670+
# No reflex_log_path is set!
# Schema expects: epistemic_assessments.reflex_log_path TEXT
```

**Where data ends up:** epistemic_assessments, but no link to JSON logs
**Result:** Inspector can't find JSON files, audit trail broken

### Fix

**File:** `empirica/cli/command_handlers/cascade_commands.py` (handle_postflight_command function)

**Change metadata to include reflex_log_path:**

```python
# Around line 670 in handle_postflight_command:

metadata = {
    "calibration": calibration,
    "delta": delta,
    "reflex_log_path": checkpoint_id  # GitEnhancedReflexLogger returns path
}

# Pass to git checkpoint:
checkpoint_hash = auto_checkpoint(
    session_id=session_id,
    ai_id=ai_id if ai_id else session_id,
    phase='POSTFLIGHT',
    vectors=postflight_vectors,
    round_num=1,
    metadata=metadata,  # <-- Includes reflex_log_path
    no_git_flag=no_git
)
```

**Better: Use unified storage (same as PREFLIGHT/CHECK fix):**

```python
# Replace lines 413-700 with unified approach:
logger_instance = GitEnhancedReflexLogger(
    session_id=session_id,
    enable_git_notes=True
)

checkpoint_id = logger_instance.add_checkpoint(
    phase="POSTFLIGHT",
    round_num=1,
    vectors=postflight_vectors,
    metadata={
        "calibration": calibration,
        "delta": delta,
        "task": task_description
    }
)
```

**What this fixes:**
- ✅ reflex_log_path is populated
- ✅ Inspector can find JSON logs
- ✅ Delta stored with checkpoint
- ✅ Unified storage (no scattered paths)

**Tests affected:** `tests/unit/cascade/test_postflight.py` (verify reflex_log_path)

**Verification:**
```bash
$ sqlite3 .empirica/sessions/sessions.db
sqlite> SELECT reflex_log_path FROM epistemic_assessments WHERE phase='POSTFLIGHT';
abc-123/POSTFLIGHT/1
```

---

## Issue 4: Centralize Decision Logic

### Current Problem

Decision threshold logic appears in **three places**:
- `cascade_commands.py:268`
- `workflow_commands.py:186`
- `workflow_commands.py:207`

### Fix

**File:** `empirica/cli/command_handlers/decision_commands.py` (or new util module)

**Add single decision function:**

```python
def _calculate_decision(confidence: float) -> str:
    """
    Single source of truth for CHECK decision logic.

    Determines next action based on confidence assessment:
    - confidence ≥ 0.7: Proceed with work
    - confidence ≤ 0.3: Investigate further
    - 0.3 < confidence < 0.7: Proceed with caution
    """
    if confidence >= 0.7:
        return "proceed"
    elif confidence <= 0.3:
        return "investigate"
    else:
        return "proceed_with_caution"
```

**Update all three locations to use this function:**

```python
# cascade_commands.py (line 268)
'recommended_action': _calculate_decision(confidence),

# workflow_commands.py (line 186)
recommended_action = _calculate_decision(confidence)

# workflow_commands.py (line 207)
"decision": _calculate_decision(confidence),
```

**What this fixes:**
- ✅ Single definition (change once, works everywhere)
- ✅ Easier to test (one function)
- ✅ Consistent logic (no divergence)

---

## Implementation Roadmap

### Phase 1: Unified Storage Framework (2 hours)

- [ ] Review GitEnhancedReflexLogger API
- [ ] Understand reflexes table schema
- [ ] Test add_checkpoint() with all three storage layers

### Phase 2: Fix PREFLIGHT (1 hour)

- [ ] Replace cascade_metadata write with GitEnhancedReflexLogger
- [ ] Update test_preflight.py
- [ ] Verify statusline finds PREFLIGHT

### Phase 3: Fix CHECK (1 hour)

- [ ] Replace hardcoded vectors with submitted vectors
- [ ] Replace scattered storage with GitEnhancedReflexLogger
- [ ] Update test_check.py
- [ ] Verify drift detection works

### Phase 4: Fix POSTFLIGHT (1 hour)

- [ ] Add reflex_log_path linking
- [ ] Replace scattered storage with GitEnhancedReflexLogger
- [ ] Update test_postflight.py
- [ ] Verify audit trail complete

### Phase 5: Centralize Decision Logic (30 min)

- [ ] Create _calculate_decision() function
- [ ] Replace all three implementations
- [ ] Update tests

### Phase 6: Integration Testing (2 hours)

- [ ] Full session workflow: PREFLIGHT → CHECK → POSTFLIGHT
- [ ] Verify statusline shows complete learning curve
- [ ] Verify drift detection accurate
- [ ] Verify audit trail complete (SQL + Git + JSON)

---

## Test Plan

### Unit Tests to Update

```
tests/unit/cascade/test_preflight.py
  - Change query from cascade_metadata to reflexes
  - Verify all 13 vectors stored
  - Verify git notes created
  - Verify JSON logs created

tests/unit/cascade/test_check.py
  - Remove hardcoded vector tests
  - Test actual submitted vectors stored
  - Test decision logic (proceed, investigate, proceed_with_caution)
  - Verify unified storage

tests/unit/cascade/test_postflight.py
  - Verify reflex_log_path populated
  - Verify delta calculated and stored
  - Verify unified storage
```

### Integration Tests to Add

```
tests/integration/test_full_cascade_workflow.py
  - PREFLIGHT assessment → stored in reflexes
  - CHECK assessment → stored in reflexes with real vectors
  - POSTFLIGHT assessment → stored with reflex_log_path
  - Statusline query returns complete learning curve
  - Drift detection finds correct drift between PREFLIGHT and CHECK
  - Audit trail linked across all three storage layers
```

---

## Verification Checklist

After implementing all fixes:

- [ ] PREFLIGHT in reflexes table (not cascade_metadata)
- [ ] CHECK has submitted vectors (not hardcoded 0.75)
- [ ] POSTFLIGHT has reflex_log_path link
- [ ] All three phases use GitEnhancedReflexLogger
- [ ] Decision logic centralized (one function)
- [ ] Statusline query returns all phases
- [ ] Learning curve shows correct progression
- [ ] Drift detection accurate
- [ ] Audit trail complete (can navigate SQLite → Git → JSON)
- [ ] All tests pass
- [ ] No cascades or reflexes orphaned in database

---

## Success Criteria

### Before Fix
```
Statusline: "⚠️ PREFLIGHT not found, CHECK has dummy data, POSTFLIGHT missing audit link"
Learning curve: "UNKNOWN → 0.75 → 0.95" (looks like sudden jump)
Drift: "0.0" (looks like no change, but CHECK had wrong data)
```

### After Fix
```
Statusline: "[empirica] │ POSTFLIGHT │ → VEL:0.0/hr │ C↑1.00 K↑0.20"
Learning curve: "0.75 → 0.92 → 0.95" (shows actual progression)
Drift: "0.17" (correct drift detected between PREFLIGHT and CHECK)
Audit trail: Can navigate reflexes.reflex_log_path → JSON file
```

---

## Rollback Plan

If issues arise:

1. Keep original code in git branch
2. Test fixes on development database first
3. Create database backup before applying schema changes
4. Roll back specific fixes individually if needed

---

## References

- **Storage Architecture Spec:** `STORAGE_ARCHITECTURE_COMPLETE.md`
- **Visual Guide:** `STORAGE_ARCHITECTURE_VISUAL_GUIDE.md`
- **Inconsistencies Audit:** `DATA_FLOW_INCONSISTENCIES_AUDIT.md`
- **GitEnhancedReflexLogger:** `empirica/core/canonical/git_enhanced_reflex_logger.py`
- **Session Database:** `empirica/data/session_database.py`

