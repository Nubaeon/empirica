# Legacy Components Status & Integration Assessment

**Date:** 2025-11-13T20:35:00Z  
**Assessment:** Production readiness of legacy components

---

## Components Analyzed

1. `twelve_vector_self_awareness.py` - 12-vector self-awareness (with ENGAGEMENT)
2. `mcp_aware_investigation.py` - MCP tool-aware investigation coordinator
3. `adaptive_uncertainty_calibration.py` - Adaptive calibration system
4. `auto_tracker.py` - Automatic session/cascade tracking

---

## Status Summary

| Component | Status | Used By | Canonical Compatible? | Action Needed |
|-----------|--------|---------|----------------------|---------------|
| `twelve_vector_self_awareness` | ⚠️ Legacy | 2 files | ❌ Uses old format | Bridge or deprecate |
| `mcp_aware_investigation` | 🟡 Orphaned | 0 files | ⚠️ Unknown | Test or deprecate |
| `adaptive_uncertainty_calibration` | ✅ Active | 10 files | ✅ Works | Document |
| `auto_tracker` | ✅ Active | 4 files | ✅ Works | Document |

---

## Detailed Analysis

### 1. twelve_vector_self_awareness.py ⚠️

**Purpose:** 12-vector self-awareness framework with ENGAGEMENT dimension

**Status:** LEGACY - Uses pre-canonical assessment format

**Issues:**
- Uses `EpistemicUncertainty` and `SelfAwarenessResult` (old classes)
- Canonical system uses `EpistemicAssessment` (13 vectors)
- Export issue: `SelfAwarenessResult` not in `__all__`
- Only imported by its own `__init__.py` (unused elsewhere)

**Usage:**
```python
# Used in:
- empirica/core/metacognition_12d_monitor/__init__.py (self-import only)

# Not used in production CASCADE
```

**Recommendation:**
```
OPTION 1: Deprecate (RECOMMENDED)
- Canonical system (13-vector) replaced this
- No active production usage
- Move to docs/_archive/

OPTION 2: Create Bridge
- Build adapter: twelve_vector → canonical
- Only if needed for backward compatibility
- Effort: 2-3 hours
```

**Action:** Archive unless there's a specific need

---

### 2. mcp_aware_investigation.py 🟡

**Purpose:** Makes CASCADE INVESTIGATE phase aware of MCP tools

**Status:** ORPHANED - Not imported anywhere

**Issues:**
- Zero imports in codebase
- May be superseded by newer investigation_strategy.py
- Uses old `SelfAwarenessResult` format
- Tool management integration unclear

**Usage:**
```python
# Used in:
- NONE (0 imports found)
```

**Recommendation:**
```
OPTION 1: Deprecate (RECOMMENDED)
- investigation_strategy.py provides similar functionality
- Not used in production
- Move to docs/_archive/

OPTION 2: Integrate with Investigation Strategy
- Merge MCP awareness into StrategySelector
- Update to use canonical EpistemicAssessment
- Effort: 4-5 hours
```

**Action:** Archive unless MCP tool recommendation is missing from investigation_strategy

---

### 3. adaptive_uncertainty_calibration.py ✅

**Purpose:** Adaptive calibration based on feedback outcomes

**Status:** ACTIVE - Used in 10 files

**Usage:**
```python
# Used in:
- empirica/calibration/adaptive_uncertainty_calibration/__init__.py
- empirica/bootstraps/optimal_metacognitive_bootstrap.py
- empirica/bootstraps/extended_metacognitive_bootstrap.py
- empirica/cli/command_handlers/cascade_commands.py
- empirica/cli/command_handlers/assessment_commands.py
- ... 5 more files
```

**Functionality:**
- Tracks feedback outcomes (correct/incorrect predictions)
- Adjusts uncertainty based on calibration accuracy
- Provides `FeedbackOutcome` for postflight validation
- Integrates with CLI and bootstraps

**Documentation Status:** ⚠️ Not in main production docs

**Recommendation:**
```
KEEP AND DOCUMENT
- Actively used in production
- Important for calibration validation
- Needs documentation in:
  - docs/reference/CALIBRATION_SYSTEM.md
  - Integration guide with CASCADE
```

**Action:** Create documentation

---

### 4. auto_tracker.py ✅

**Purpose:** Automatic session and cascade tracking

**Status:** ACTIVE - Used in 4 files

**Usage:**
```python
# Used in:
- empirica/bootstraps/optimal_metacognitive_bootstrap.py
- empirica/bootstraps/extended_metacognitive_bootstrap.py  
- empirica/dashboard/snapshot_monitor.py
- empirica/plugins/modality_switcher/snapshot_provider.py
```

**Functionality:**
- Tracks sessions automatically
- Provides snapshot capabilities
- Integrates with dashboard and modality switcher
- Used by bootstrap processes

**Documentation Status:** ✓ Partially documented in archived docs

**Recommendation:**
```
KEEP AND DOCUMENT
- Actively used in production
- Critical for dashboard/monitoring
- Needs documentation in:
  - docs/reference/SESSION_TRACKING.md
  - Integration with dashboard
```

**Action:** Create/update documentation

---

## Documentation Gaps

### Critical (Needs Documentation)

**1. Adaptive Uncertainty Calibration**
- **Missing:** Comprehensive guide on calibration system
- **Needed:** 
  - How calibration adapts over time
  - FeedbackOutcome usage
  - Integration with POSTFLIGHT
  - Calibration accuracy tracking
- **File:** `docs/reference/CALIBRATION_SYSTEM.md`
- **Priority:** HIGH

**2. Auto Tracker**
- **Missing:** Session tracking guide
- **Needed:**
  - Automatic tracking features
  - Snapshot system
  - Integration with dashboard
  - Bootstrap usage patterns
- **File:** `docs/reference/SESSION_TRACKING.md`
- **Priority:** MEDIUM

### Optional (Can Archive)

**3. Twelve Vector Self-Awareness**
- Status: Legacy, replaced by canonical 13-vector system
- Action: Move to `docs/_archive/legacy_systems/`
- Include migration guide if needed

**4. MCP-Aware Investigation**
- Status: Orphaned, likely superseded
- Action: Move to `docs/_archive/prototypes/`
- Note: Concept may be valuable for future reference

---

## Action Plan

### Immediate (Pre-Release)

1. **Archive Legacy Components** ✅ Can do now
   ```bash
   mkdir -p docs/_archive/legacy_systems
   mv empirica/core/metacognition_12d_monitor docs/_archive/legacy_systems/
   # Add README explaining canonical replacement
   ```

2. **Archive Orphaned Components** ✅ Can do now
   ```bash
   mkdir -p docs/_archive/prototypes
   mv empirica/core/metacognitive_cascade/mcp_aware_investigation.py \
      docs/_archive/prototypes/
   # Add note about investigation_strategy.py
   ```

3. **Document Adaptive Calibration** ⚠️ Important
   - Create `docs/reference/CALIBRATION_SYSTEM.md`
   - Explain feedback loop
   - Show integration with POSTFLIGHT
   - Priority: HIGH

4. **Document Auto Tracker** 🟡 Nice-to-have
   - Create `docs/reference/SESSION_TRACKING.md`
   - Explain automatic tracking
   - Show dashboard integration
   - Priority: MEDIUM

### Post-Release

5. **Verify Investigation Strategy Complete**
   - Check if mcp_aware_investigation concepts are in investigation_strategy
   - If missing, extract useful patterns
   - Document any gaps

6. **Create Migration Guide**
   - For users of twelve_vector_self_awareness
   - Show how to migrate to canonical system
   - Include code examples

---

## Recommendations Summary

### Keep & Document ✅
- `adaptive_uncertainty_calibration.py` - Active, important
- `auto_tracker.py` - Active, used by dashboard

### Archive (Legacy) 📦
- `twelve_vector_self_awareness.py` - Replaced by canonical system
- `mcp_aware_investigation.py` - Orphaned, superseded

### Documentation Needed 📝
1. **HIGH:** Calibration system guide
2. **MEDIUM:** Session tracking guide
3. **LOW:** Legacy migration guide

---

## Files Proposed for Archiving

**Move to `docs/_archive/legacy_systems/`:**
```
empirica/core/metacognition_12d_monitor/
├── __init__.py
├── twelve_vector_self_awareness.py
├── metacognition_12d_monitor.py
└── README_LEGACY.md (create - explains canonical replacement)
```

**Move to `docs/_archive/prototypes/`:**
```
empirica/core/metacognitive_cascade/mcp_aware_investigation.py
└── README_PROTOTYPE.md (create - explains investigation_strategy)
```

**Rationale:**
- Not breaking anything (not imported in production)
- Clean up for release
- Preserve for reference
- Clear migration path documented

---

## Impact Assessment

**Risk of Archiving:** ✅ LOW
- `twelve_vector`: Only imported by itself (safe to archive)
- `mcp_aware_investigation`: Not imported anywhere (safe to archive)

**Risk of Not Documenting:** ⚠️ MEDIUM
- `adaptive_calibration`: Users won't understand calibration system
- `auto_tracker`: Dashboard integration unclear

**Recommendation:** 
1. Archive legacy/orphaned components now
2. Document active components before v1.0 release
3. Create migration guides as needed

---

## Next Steps

**Before Release:**
1. ✅ Archive `twelve_vector_self_awareness` (safe, not used)
2. ✅ Archive `mcp_aware_investigation` (safe, not used)  
3. ⚠️ Document `adaptive_uncertainty_calibration` (HIGH priority)
4. 🟡 Document `auto_tracker` (MEDIUM priority)

**After Release:**
5. Verify investigation strategy completeness
6. Create migration guides if requested
7. Monitor for any backward compatibility issues

---

**Assessment Complete:** 2025-11-13T20:35:00Z  
**Conclusion:** Safe to archive 2 legacy components, document 2 active components  
**Risk:** LOW - No production impact from archiving, missing docs can be added incrementally
