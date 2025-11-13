# Refactoring Priorities - Empirica Framework

**Date:** 2025-11-13  
**Based on:** CODE_QUALITY_REPORT.md  
**Priority:** Impact × Feasibility

---

## Priority Matrix

| Priority | Issue | Impact | Effort | ROI |
|----------|-------|--------|--------|-----|
| 🔴 P1 | Replace print() with logging | HIGH | LOW | **★★★★★** |
| 🔴 P2 | Centralize threshold constants | HIGH | LOW | **★★★★★** |
| 🟡 P3 | Refactor `__init__()` (868 lines) | HIGH | HIGH | **★★★☆☆** |
| 🟡 P4 | Refactor `_create_tables()` (447 lines) | MEDIUM | MEDIUM | **★★★☆☆** |
| ⚪ P5 | Refactor prompt builders (200+ lines) | MEDIUM | HIGH | **★★☆☆☆** |
| ⚪ P6 | Remove DEPRECATED parameters | LOW | MEDIUM | **★☆☆☆☆** |

---

## P1: Replace print() with logging 🔴 **DO FIRST**

**Impact:** HIGH - Enables production debugging, log levels, structured logging  
**Effort:** LOW - Straightforward find-and-replace with minimal logic changes  
**Files:** 6 files, 19 print statements

### Implementation Plan

**Step 1:** Add logging setup (5 min)
```python
# empirica/core/__init__.py
import logging

logger = logging.getLogger('empirica')
logger.setLevel(logging.INFO)
```

**Step 2:** Replace prints systematically (30 min)
```python
# Before:
print(f"🧠✨ 12-Vector Self-Awareness Monitor initialized")
print(f"   🤖 AI ID: {ai_id}")

# After:
logger.info("12-Vector Monitor initialized", 
            extra={"ai_id": ai_id, "vectors": 13})
```

**Priority Files:**
1. `twelve_vector_self_awareness.py` - 12 prints
2. `canonical_goal_orchestrator.py` - 3 prints  
3. `metacognition_12d_monitor.py` - 1 print
4. Others - 3 prints

**Estimated Time:** 45 minutes  
**Risk:** MINIMAL - Backward compatible, improves observability

---

## P2: Centralize Threshold Constants 🔴 **DO SECOND**

**Impact:** HIGH - Single source of truth, easier tuning, clearer semantics  
**Effort:** LOW - Create config class, update references  
**Files:** 3-4 files, 15+ hardcoded values

### Implementation Plan

**Step 1:** Create constants module (10 min)
```python
# empirica/core/canonical/thresholds.py

from dataclasses import dataclass

@dataclass(frozen=True)
class EpistemicThresholds:
    """Canonical epistemic thresholds for CASCADE workflow"""
    
    # Engagement gate
    ENGAGEMENT_MIN: float = 0.60  # Must meet to proceed
    ENGAGEMENT_HIGH: float = 0.80  # High collaboration mode
    ENGAGEMENT_CRITICAL: float = 0.40  # Request clarification
    
    # Foundation tier
    KNOW_MIN: float = 0.70  # Adequate domain knowledge
    CONTEXT_MIN: float = 0.70  # Adequate environmental understanding
    
    # Comprehension tier  
    CLARITY_MIN: float = 0.60  # Task understanding threshold
    
    # Meta-epistemic
    UNCERTAINTY_HIGH: float = 0.80  # Triggers investigation
    
    # Overall confidence
    CONFIDENCE_PROCEED: float = 0.70  # Minimum to ACT
    CONFIDENCE_CAUTION: float = 0.50  # Proceed with care

# Default instance
CANONICAL_THRESHOLDS = EpistemicThresholds()
```

**Step 2:** Update imports (20 min)
```python
# Before:
if engagement_score >= 0.80:
    ...

# After:
from empirica.core.canonical.thresholds import CANONICAL_THRESHOLDS as T

if engagement_score >= T.ENGAGEMENT_HIGH:
    ...
```

**Files to Update:**
- `canonical_goal_orchestrator.py` (8 hardcoded values)
- `canonical_epistemic_assessment.py` (3 values)
- `metacognitive_cascade.py` (2 values)
- `reflex_frame.py` (already has ENGAGEMENT_THRESHOLD constant - reuse pattern)

**Estimated Time:** 30 minutes  
**Risk:** MINIMAL - Pure refactoring, no logic changes

---

## P3: Refactor `__init__()` (868 lines) 🟡 **MEDIUM TERM**

**Impact:** HIGH - Massive maintainability improvement  
**Effort:** HIGH - Complex method with many responsibilities  
**File:** `metacognitive_cascade.py`

### Analysis

**Current structure (lines 169-1036):**
1. Parameter handling (30 lines)
2. Profile loading (50 lines)
3. Assessor initialization (40 lines)
4. Session database setup (60 lines)
5. Investigation plugins (80 lines)
6. Bayesian Guardian (100 lines)
7. Drift Monitor (90 lines)
8. Action hooks (70 lines)
9. Dashboard setup (60 lines)
10. Legacy compatibility (50 lines)
11. ...continues for 868 lines

### Refactoring Strategy

**Extract into private methods:**
```python
def __init__(self, ...):
    # 1. Load configuration (50 lines)
    self._load_profile(profile_name, ai_model, domain)
    
    # 2. Initialize core components (80 lines)
    self._init_assessor()
    self._init_database()
    
    # 3. Setup optional features (100 lines)
    self._init_monitoring(enable_bayesian, enable_drift_monitor)
    self._init_investigation(investigation_plugins)
    
    # 4. Configure integrations (80 lines)
    self._setup_action_hooks(enable_action_hooks)
    self._setup_dashboard(auto_start_dashboard)
    
    # Result: __init__() reduces to ~50 lines of orchestration
```

**Benefits:**
- Each method <100 lines
- Testable in isolation
- Clear responsibilities
- Easier to understand flow

**Estimated Time:** 3-4 hours  
**Risk:** MEDIUM - Core component, needs thorough testing

---

## P4: Refactor `_create_tables()` (447 lines) 🟡 **MEDIUM TERM**

**Impact:** MEDIUM - Improves database module maintainability  
**Effort:** MEDIUM - Repetitive SQL CREATE statements  
**File:** `session_database.py`

### Refactoring Strategy

**Extract per-table methods:**
```python
def _create_tables(self):
    """Create all database tables"""
    self._create_sessions_table()
    self._create_cascades_table()
    self._create_assessments_table()
    self._create_divergence_table()
    self._create_drift_table()
    self._create_bayesian_table()
    self._create_tools_table()
    self._create_indexes()

def _create_sessions_table(self):
    """Create sessions table (40 lines)"""
    self.conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (...)
    """)

# ... etc for each table
```

**Benefits:**
- Each method represents one table
- Easier to modify schema
- Clearer structure

**Estimated Time:** 2 hours  
**Risk:** LOW - Pure reorganization, no logic changes

---

## P5: Refactor Prompt Builders (200+ lines) ⚪ **LONG TERM**

**Impact:** MEDIUM - Cleaner code, but prompts are inherently long  
**Effort:** HIGH - Complex prompt construction, risk of breaking assessments  
**Files:** `canonical_epistemic_assessment.py`

### Analysis

**Functions:**
- `_build_self_assessment_prompt()` - 215 lines
- `parse_llm_response()` - 203 lines
- `_build_self_assessment_template_for_mapping()` - 187 lines

**Challenge:** These are long because they construct detailed LLM prompts. Splitting might harm prompt quality.

### Recommendation

**Option A:** Extract sub-sections as template strings
```python
ENGAGEMENT_SECTION = """
## GATE: ENGAGEMENT (Prerequisite - Must be ≥ 0.60)
...
"""

def _build_self_assessment_prompt(self, ...):
    sections = [
        self._build_header(),
        ENGAGEMENT_SECTION,
        self._build_foundation_section(),
        self._build_comprehension_section(),
        ...
    ]
    return "\n".join(sections)
```

**Option B:** Accept that prompt builders are inherently long (200+ lines is OK for complex prompts)

**Estimated Time:** 4-6 hours  
**Risk:** MEDIUM - Could break LLM assessment quality

---

## P6: Remove DEPRECATED Parameters ⚪ **FUTURE**

**Impact:** LOW - Code cleanup, minor complexity reduction  
**Effort:** MEDIUM - Need migration plan, deprecation warnings  
**File:** `metacognitive_cascade.py`

### Implementation Plan

**Phase 1:** Add deprecation warnings (30 min)
```python
def __init__(self, ..., action_confidence_threshold=None, ...):
    if action_confidence_threshold is not None:
        warnings.warn(
            "action_confidence_threshold is deprecated, use profile_name instead",
            DeprecationWarning,
            stacklevel=2
        )
```

**Phase 2:** Document migration (1 hour)
```markdown
# Migration Guide

## Deprecated Parameters

Before:
cascade = CanonicalEpistemicCascade(
    action_confidence_threshold=0.70,
    max_investigation_rounds=3
)

After:
cascade = CanonicalEpistemicCascade(
    profile_name='balanced'  # Encapsulates these settings
)
```

**Phase 3:** Remove after 2-3 releases (30 min)

**Estimated Time:** 2 hours total over multiple releases  
**Risk:** LOW - Can plan carefully

---

## Implementation Roadmap

### Sprint 1: Quick Wins (1-2 hours)
- ✅ P1: Replace print() with logging (45 min)
- ✅ P2: Centralize threshold constants (30 min)

### Sprint 2: Medium Refactoring (1 week)
- ✅ P3: Refactor `__init__()` (3-4 hours)
- ✅ P4: Refactor `_create_tables()` (2 hours)

### Sprint 3: Long-term (Future releases)
- P5: Consider prompt builder refactoring (evaluate benefit/risk)
- P6: Deprecation timeline for old parameters

---

## Success Metrics

**After P1-P2 (Quick Wins):**
- ✅ Zero print() statements in production code
- ✅ All thresholds use named constants
- ✅ Logging configurable via standard Python logging

**After P3-P4 (Medium):**
- ✅ No functions >200 lines
- ✅ `__init__()` <100 lines
- ✅ Each database table in separate method

**After P5-P6 (Long-term):**
- ✅ All functions <150 lines
- ✅ No deprecated parameters
- ✅ Clean, modern codebase

---

## Risk Mitigation

**For all refactorings:**
1. ✅ Create feature branch
2. ✅ Run full test suite before/after
3. ✅ Keep refactorings small and focused
4. ✅ Review with domain expert (you!)
5. ✅ Deploy to testing environment first

**Special caution for:**
- P3 (`__init__` refactoring) - Core component, test thoroughly
- P5 (Prompt builders) - Could affect LLM assessment quality

---

**Total Estimated Effort:**
- Quick wins (P1-P2): **1-2 hours**
- Medium term (P3-P4): **5-6 hours**
- Long term (P5-P6): **6-8 hours** (optional)

**Recommended:** Start with P1-P2 for immediate impact with minimal risk.

---

*Generated: 2025-11-13 23:33:17 UTC*  
*Session: a89b9d94-d907-4a95-ab8d-df8824990bec*  
*Method: Impact/effort analysis via Empirica CASCADE*
