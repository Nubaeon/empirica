# Pre-Release Action Plan - Structural Integrity

**Status:** Analysis Complete  
**Next:** Review → Prioritize → Implement  
**Timeline:** Before empirica-dev demo

---

## 🎯 Executive Summary

**Analysis Completed:**
- ✅ 825-line deep integration analysis
- ✅ 675-line structural integrity test plan
- ✅ Identified 10 critical issues, 9 important issues

**Recommendation:** Fix critical issues before release, design extension points now (implement later)

---

## 🚨 Critical Issues (Must Fix Before Release)

### Issue #1: No Schema Versioning
**Impact:** Breaking changes will corrupt old data  
**Severity:** CRITICAL  
**Effort:** Low (add version field)

**Fix:**
```python
# Add to SessionDatabase
class SessionDatabase:
    SCHEMA_VERSION = "1.0"
    
    def __init__(self):
        self._ensure_schema_version()
    
    def _ensure_schema_version(self):
        """Ensure schema version is tracked"""
        self.execute("""
            CREATE TABLE IF NOT EXISTS schema_info (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        current = self.get_value("schema_version")
        if not current:
            self.set_value("schema_version", self.SCHEMA_VERSION)
```

**Test:** `tests/integrity/test_schema_versioning.py`

---

### Issue #2: No Agent Model/Version Tracking
**Impact:** Can't analyze model-specific patterns or bugs  
**Severity:** CRITICAL  
**Effort:** Low (add columns)

**Fix:**
```sql
ALTER TABLE cascades ADD COLUMN agent_id TEXT;
ALTER TABLE cascades ADD COLUMN agent_model TEXT;  -- e.g., "claude-sonnet-4"
ALTER TABLE cascades ADD COLUMN agent_version TEXT;  -- e.g., "20241022"
```

**Update CanonicalEpistemicCascade:**
```python
def __init__(self, agent_id: str, agent_model: str = None):
    self.agent_id = agent_id
    self.agent_model = agent_model or self._detect_model()
```

**Test:** `tests/integrity/test_model_agnosticism.py::test_can_track_which_model_produced_assessment`

---

### Issue #3: No Calibration Results Storage
**Impact:** Can't query historical calibration accuracy  
**Severity:** HIGH  
**Effort:** Medium (new table)

**Fix:**
```sql
CREATE TABLE calibration_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cascade_id TEXT,
    preflight_assessment_id INTEGER,
    postflight_assessment_id INTEGER,
    delta_json TEXT,  -- JSON with all vector deltas
    calibration_status TEXT,  -- well-calibrated, overconfident, underconfident
    confidence_change REAL,
    uncertainty_change REAL,
    timestamp TEXT,
    FOREIGN KEY(cascade_id) REFERENCES cascades(cascade_id)
);
```

**Update CASCADE postflight:**
```python
# After calculating delta and calibration
self.session_db.store_calibration_result(
    cascade_id=self.cascade_id,
    delta=delta,
    calibration_status=calibration_status
)
```

**Test:** `tests/integrity/test_sessiondb_schema.py::test_missing_calibration_results_table`

---

### Issue #4: Missing Database Indices
**Impact:** Slow queries on large datasets  
**Severity:** HIGH  
**Effort:** Low (add indices)

**Fix:**
```sql
CREATE INDEX IF NOT EXISTS idx_cascade_status ON cascades(status);
CREATE INDEX IF NOT EXISTS idx_cascade_started ON cascades(started_at);
CREATE INDEX IF NOT EXISTS idx_cascade_agent ON cascades(agent_id);
CREATE INDEX IF NOT EXISTS idx_phase_cascade ON cascade_phases(cascade_id, phase);
CREATE INDEX IF NOT EXISTS idx_assessment_cascade ON epistemic_assessments(cascade_id, phase);
CREATE INDEX IF NOT EXISTS idx_calibration_cascade ON calibration_results(cascade_id);
```

**Test:** `tests/integrity/test_sessiondb_schema.py::test_no_indices_on_common_queries`

---

### Issue #5: No Assessment Version Field
**Impact:** Can't evolve assessment structure without breaking old data  
**Severity:** HIGH  
**Effort:** Low (add field)

**Fix:**
```python
@dataclass
class EpistemicAssessment:
    # Existing fields
    engagement: float
    know: float
    # ... etc
    
    # Add versioning
    assessment_version: str = "1.0"
    assessment_source: str = "canonical_assessor"  # Which component
    
    # Add for future extensions
    additional_vectors: Optional[Dict[str, float]] = None
    metadata: Optional[Dict[str, Any]] = None
```

**Test:** `tests/integrity/test_reflex_frame_structure.py::test_assessment_missing_version_field`

---

## ⚠️ Important Issues (Design Now, Implement Soon)

### Issue #6: No Plugin Registration System
**Impact:** Developers will hack core for custom investigations  
**Severity:** MEDIUM  
**Effort:** Medium (design interface)

**Solution:** Design `InvestigationPluginRegistry` interface NOW, document it, implement later

**Action:**
1. Create `empirica/investigation/plugin_interface.py` with abstract base class
2. Document in `docs/guides/INVESTIGATION_PLUGIN_GUIDE.md`
3. Add placeholder in CASCADE for future integration
4. Test interface design (not full implementation)

---

### Issue #7: No Reflex Frame Cleanup Policy
**Impact:** Disk space accumulation  
**Severity:** MEDIUM  
**Effort:** Low (add TTL or limit)

**Solution:**
```python
class ReflexLogger:
    def __init__(self, max_frames: int = 1000, ttl_days: int = 30):
        self.max_frames = max_frames
        self.ttl_days = ttl_days
    
    async def _cleanup_old_frames(self):
        """Remove frames older than TTL or beyond limit"""
        # Implement cleanup logic
```

---

### Issue #8: No Context Drift Detection
**Impact:** Won't notice when environment changes  
**Severity:** MEDIUM  
**Effort:** Medium (add hashing)

**Solution:**
```python
@dataclass
class EpistemicAssessment:
    # ... existing
    context_hash: Optional[str] = None  # SHA256 of context
    
    @classmethod
    def from_context(cls, context: Dict, **kwargs):
        context_hash = hashlib.sha256(
            json.dumps(context, sort_keys=True).encode()
        ).hexdigest()
        return cls(context_hash=context_hash, **kwargs)
```

---

### Issue #9: No Bayesian Belief Persistence
**Impact:** Beliefs lost between sessions  
**Severity:** MEDIUM  
**Effort:** Medium (new table)

**Solution:**
```sql
CREATE TABLE bayesian_beliefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT,
    belief_key TEXT,  -- e.g., "domain.python"
    prior_probability REAL,
    posterior_probability REAL,
    evidence_json TEXT,
    updated_at TEXT,
    cascade_id TEXT
);

CREATE INDEX idx_belief_agent_key ON bayesian_beliefs(agent_id, belief_key);
```

---

### Issue #10: No Vector DB Integration Points
**Impact:** Everyone implements differently  
**Severity:** LOW  
**Effort:** Low (design interface)

**Solution:** Document interface NOW, implement later
```python
# Create empirica/integrations/vector_db_interface.py
class VectorDBInterface(ABC):
    @abstractmethod
    async def store_embedding(self, id: str, embedding: List[float], metadata: Dict):
        pass
    
    @abstractmethod
    async def search_similar(self, query_embedding: List[float], limit: int) -> List[Dict]:
        pass
```

---

## 📋 Prioritized Action Items

### Before Release (Do Now - 2-4 hours)

**Priority 1: Schema Versioning** (30 min)
- [ ] Add schema_info table
- [ ] Add SCHEMA_VERSION constant
- [ ] Add migration check on init
- [ ] Write test

**Priority 2: Agent Tracking** (30 min)
- [ ] Add agent_model, agent_version columns
- [ ] Update CASCADE to capture
- [ ] Update all create_cascade calls
- [ ] Write test

**Priority 3: Calibration Storage** (60 min)
- [ ] Create calibration_results table
- [ ] Add store_calibration_result method
- [ ] Update CASCADE postflight
- [ ] Write test

**Priority 4: Database Indices** (15 min)
- [ ] Add all recommended indices
- [ ] Test query performance
- [ ] Document in migration guide

**Priority 5: Assessment Versioning** (30 min)
- [ ] Add version fields to EpistemicAssessment
- [ ] Update all instantiation points
- [ ] Write test

**Total Estimated Time: 2.5 hours**

---

### Before 1.1 Release (Design Now, Implement Later - 4-8 hours)

**Priority 6: Plugin Interface** (2 hours)
- [ ] Design InvestigationPluginRegistry interface
- [ ] Create abstract base class
- [ ] Document extension guide
- [ ] Add placeholder in CASCADE
- [ ] Write interface tests (not full implementation)

**Priority 7: Cleanup Policy** (1 hour)
- [ ] Implement reflex frame TTL
- [ ] Add max_frames limit
- [ ] Test cleanup logic

**Priority 8: Context Drift** (1 hour)
- [ ] Add context_hash field
- [ ] Implement hash computation
- [ ] Add drift detection method
- [ ] Test drift detection

**Priority 9: Belief Persistence** (2 hours)
- [ ] Create bayesian_beliefs table
- [ ] Implement CRUD methods
- [ ] Integrate with BayesianBeliefTracker
- [ ] Test persistence

**Priority 10: Vector DB Interface** (1 hour)
- [ ] Design VectorDBInterface
- [ ] Document integration guide
- [ ] Create example implementation
- [ ] Test interface

**Total Estimated Time: 7 hours**

---

## 🧪 Testing Strategy

### Phase 1: Create Integrity Tests (1 hour)
```bash
# Create test files
tests/integrity/
├── test_sessiondb_schema.py
├── test_schema_versioning.py
├── test_reflex_frame_structure.py
├── test_model_agnosticism.py
├── test_investigation_extensibility.py
└── test_drift_detection_integration.py
```

### Phase 2: Run Tests (Expect Failures)
```bash
pytest tests/integrity/ -v

# Expected: Many warnings/failures
# This identifies what to fix
```

### Phase 3: Implement Fixes
Fix issues one by one, re-run tests

### Phase 4: Validate
```bash
pytest tests/integrity/ -v

# Expected: All pass or documented as "not implemented yet"
```

---

## 📊 Risk Assessment

### If We DON'T Fix Critical Issues:
1. **No schema versioning** → Can't upgrade database without breaking
2. **No agent tracking** → Can't debug model-specific issues
3. **No calibration storage** → Can't analyze accuracy over time
4. **No indices** → Slow queries at scale
5. **No assessment versioning** → Can't evolve assessment structure

**Risk Level:** HIGH - These will cause pain immediately after release

### If We DON'T Fix Important Issues:
6. **No plugin system** → Developers hack core (messy)
7. **No cleanup** → Disk fills up slowly
8. **No drift detection** → Miss subtle issues
9. **No belief persistence** → Manual workarounds
10. **No vector DB interface** → Inconsistent integrations

**Risk Level:** MEDIUM - These cause pain as complexity grows

---

## 🎯 Recommended Approach

### Option A: Fix All Critical Issues Now (Recommended)
**Time:** 2.5 hours  
**Benefit:** Clean release, no immediate pain  
**Risk:** Slight delay in demo

**Timeline:**
- Now: Implement fixes (2.5 hours)
- Then: Run integrity tests
- Then: Demo in empirica-dev

### Option B: Document Issues, Fix After Demo
**Time:** 30 min documentation  
**Benefit:** Demo happens faster  
**Risk:** Technical debt, harder to fix later

**Timeline:**
- Now: Document known issues
- Demo: Show current state
- After: Fix issues before public release

### Option C: Hybrid - Fix P1-P3, Document P4-P5
**Time:** 2 hours  
**Benefit:** Most critical issues fixed  
**Risk:** Minor issues remain

**Timeline:**
- Now: Fix schema versioning, agent tracking, calibration (2 hours)
- Document: Indices and assessment versioning as known improvements
- Demo: Mostly clean system

---

## 💡 Recommendation

**Go with Option A: Fix All Critical Issues Now**

**Why:**
1. Only 2.5 hours of work
2. Prevents immediate post-release pain
3. Shows professional polish in demo
4. Easier to fix now than later
5. Sets good foundation for extensions

**Process:**
1. Review this action plan (15 min)
2. Implement critical fixes (2.5 hours)
3. Run integrity tests (15 min)
4. Demo in empirica-dev (clean system!)

**Total Time:** 3 hours before demo

---

## 📝 Next Steps

### Immediate (You)
1. Review DEEP_INTEGRATION_ANALYSIS.md
2. Review STRUCTURAL_INTEGRITY_TEST_PLAN.md
3. Review this action plan
4. Decide: Option A, B, or C?

### Next (Me - Claude)
1. Implement chosen fixes
2. Create integrity test suite
3. Run tests and validate
4. Document any remaining issues

### Then (Both)
1. Demo in empirica-dev
2. Gather feedback
3. Iterate on extensions
4. Release!

---

## 🎉 Big Picture

**What We're Doing:**
Ensuring Empirica has a solid foundation for:
- Long-term evolution (schema versioning)
- Model diversity (agent tracking)
- Quality measurement (calibration storage)
- Performance at scale (indices)
- Clean extensions (plugin interfaces)

**Why It Matters:**
- Users will want to extend Empirica
- Data will accumulate over time
- Multiple models will be used
- Calibration history is valuable
- Complexity will increase

**The Payoff:**
- Clean architecture from day one
- Easy to extend without hacks
- Professional quality release
- Confident in long-term maintainability

---

**Ready to implement when you give the word!** 🚀
