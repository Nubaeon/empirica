# Deep Integration Analysis - Structural Integrity Review

**Purpose:** Pre-release architectural validation  
**Focus:** Data integrity, extensibility, model-agnostic design, drift detection  
**Goal:** Identify potential issues before release, ensure clean extension points

---

## 🎯 Analysis Scope

### 1. Data Layer Integrity
**Questions:**
- Are SessionDB fields complete, correct, or over-engineered?
- Are Reflex Frames capturing necessary data without bloat?
- Is the schema model-agnostic?
- Can we extend without breaking existing data?

### 2. Advanced Features Readiness
**Questions:**
- How will drift monitoring integrate?
- How will Bayesian belief tracking scale?
- Is investigation phase extensible for RAG/APIs?
- Where are the bottlenecks?

### 3. Extension Point Validation
**Questions:**
- Can developers add custom investigations without core changes?
- Can vector DBs (Qdrant) integrate cleanly?
- Can learning deltas be stored/retrieved for patterns?
- What will break if complexity increases?

### 4. Model Agnosticism
**Questions:**
- Are we locked into specific LLM output formats?
- Can different models use the same data structures?
- What happens with future 13+ vector extensions?
- Are we over-fitting to current implementations?

---

## 🔍 Deep Dive Areas

### Area 1: SessionDB Schema Analysis

**Current Schema (from session_database.py):**
```sql
CREATE TABLE cascades (
    cascade_id TEXT PRIMARY KEY,
    question TEXT,
    started_at TEXT,
    completed_at TEXT,
    status TEXT
);

CREATE TABLE cascade_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cascade_id TEXT,
    metadata_key TEXT,
    metadata_value TEXT,
    FOREIGN KEY(cascade_id) REFERENCES cascades(cascade_id)
);

CREATE TABLE cascade_phases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cascade_id TEXT,
    phase TEXT,
    started_at TEXT,
    completed_at TEXT,
    decision TEXT,
    FOREIGN KEY(cascade_id) REFERENCES cascades(cascade_id)
);

CREATE TABLE epistemic_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cascade_id TEXT,
    phase TEXT,
    assessment_data TEXT,  -- JSON blob
    timestamp TEXT,
    FOREIGN KEY(cascade_id) REFERENCES cascades(cascade_id)
);
```

**Analysis Questions:**

1. **Completeness:**
   - ✅ Cascade lifecycle tracked (started, completed, status)
   - ✅ Phases logged with decisions
   - ✅ Assessments stored as JSON (flexible)
   - ❓ Missing: Investigation round tracking (which round? why?)
   - ❓ Missing: Calibration results (well-calibrated status?)
   - ❓ Missing: Learning delta history
   - ❓ Missing: Agent metadata (model type, version)

2. **Correctness:**
   - ✅ Foreign keys properly constrained
   - ✅ Primary keys on cascades
   - ❓ No indices on commonly queried fields (cascade_id, phase, timestamp)
   - ❓ TEXT for timestamps (should be INTEGER/REAL for sorting?)
   - ❓ JSON blob in assessment_data (hard to query specific vectors)

3. **Over-Engineering:**
   - ❓ cascade_metadata with key-value pairs (flexible but may be unused)
   - ✅ Simple enough schema (not over-engineered)
   - ❓ Could assessment_data be broken out for queryability?

4. **Model Agnostic:**
   - ✅ JSON blob allows any assessment structure
   - ✅ No model-specific fields
   - ❓ But: Are we assuming 13 vectors always? What about future expansions?
   - ❓ Agent identification? (which model/version produced this?)

**Recommendations:**

```sql
-- Add for investigation tracking
ALTER TABLE cascade_phases ADD COLUMN round_number INTEGER DEFAULT 0;
ALTER TABLE cascade_phases ADD COLUMN investigation_strategy TEXT;

-- Add for calibration tracking
CREATE TABLE calibration_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cascade_id TEXT,
    preflight_assessment_id INTEGER,
    postflight_assessment_id INTEGER,
    delta JSON,  -- Vector deltas
    calibration_status TEXT,  -- well-calibrated, overconfident, underconfident
    timestamp TEXT,
    FOREIGN KEY(cascade_id) REFERENCES cascades(cascade_id)
);

-- Add for agent tracking (model agnostic)
ALTER TABLE cascades ADD COLUMN agent_id TEXT;
ALTER TABLE cascades ADD COLUMN agent_model TEXT;  -- e.g., "claude-sonnet-4", "gpt-4"
ALTER TABLE cascades ADD COLUMN agent_version TEXT;

-- Add indices for queries
CREATE INDEX idx_cascade_status ON cascades(status);
CREATE INDEX idx_cascade_timestamps ON cascades(started_at, completed_at);
CREATE INDEX idx_phase_cascade ON cascade_phases(cascade_id, phase);
CREATE INDEX idx_assessment_cascade_phase ON epistemic_assessments(cascade_id, phase);
```

---

### Area 2: Reflex Frame Structure Analysis

**Current Structure (from reflex_frame.py):**
```python
@dataclass
class EpistemicAssessment:
    engagement: float
    know: float
    do: float
    context: float
    clarity: float
    coherence: float
    signal: float
    density: float
    state: float
    change: float
    completion: float
    impact: float
    uncertainty: float
    # ... additional fields
```

**Analysis Questions:**

1. **Data Capture:**
   - ✅ All 13 vectors captured
   - ✅ Timestamp included
   - ✅ Rationale/reasoning stored
   - ❓ Missing: Confidence in assessment itself (meta-uncertainty?)
   - ❓ Missing: Which component generated this? (assessor, cascade, manual?)
   - ❓ Missing: Context hash (to detect context changes)?

2. **Temporal Separation:**
   - ✅ Stored as JSON externally (prevents recursion)
   - ✅ Async logging (non-blocking)
   - ❓ File naming scheme: How to retrieve specific assessments?
   - ❓ Cleanup strategy: Old reflex frames accumulate?

3. **Model Agnostic:**
   - ✅ Float values (any model can produce)
   - ❓ But: Are we assuming specific reasoning format?
   - ❓ What if future model adds new vectors? (14th, 15th?)

4. **Extensibility:**
   - ❓ Can we add metadata without breaking existing frames?
   - ❓ Version field? (for schema evolution)

**Recommendations:**

```python
@dataclass
class EpistemicAssessment:
    # Existing 13 vectors
    engagement: float
    know: float
    # ... etc
    
    # Add for robustness
    assessment_version: str = "1.0"  # Schema versioning
    assessment_source: str = "canonical_assessor"  # Which component
    context_hash: Optional[str] = None  # Detect context drift
    meta_uncertainty: Optional[float] = None  # Confidence in assessment
    
    # Add for extensibility
    additional_vectors: Optional[Dict[str, float]] = None  # Future vectors
    metadata: Optional[Dict[str, Any]] = None  # Flexible extension

# Reflex Frame JSON structure
{
    "version": "1.0",
    "assessment": { ... },
    "timestamp": "...",
    "cascade_id": "...",
    "phase": "...",
    "agent_id": "...",
    "agent_model": "..."
}
```

---

### Area 3: Drift Detection Integration

**Current Implementation:**
- `empirica/calibration/adaptive_uncertainty_calibration/` exists
- Bayesian belief tracker available
- Drift monitor in place

**Deep Integration Questions:**

1. **How does drift monitoring hook into CASCADE?**
   - Current: Optional component
   - Question: Should drift checks be automatic or manual?
   - Question: At what points in CASCADE should drift be measured?
   
2. **What constitutes "drift"?**
   - Behavioral drift (sycophancy, tension avoidance)
   - Epistemic drift (confidence inflation over time)
   - Calibration drift (predictions becoming less accurate)
   - Context drift (environment changes during task)

3. **Data requirements for drift detection:**
   - Need: Historical assessments (have via SessionDB)
   - Need: Baseline behavior (where stored?)
   - Need: Drift thresholds (configurable? hardcoded?)
   - Need: Alert mechanism (how to surface drift warnings?)

**Recommendations:**

```python
# Add to CanonicalEpistemicCascade
class CanonicalEpistemicCascade:
    def __init__(
        self,
        enable_drift_monitor: bool = True,
        drift_window_size: int = 10,  # Last N assessments
        drift_threshold: float = 0.2   # Significant drift
    ):
        self.drift_monitor = DriftMonitor(
            window_size=drift_window_size,
            threshold=drift_threshold
        ) if enable_drift_monitor else None
    
    async def _check_drift(self, current_assessment: EpistemicAssessment):
        """Check for drift after each assessment"""
        if not self.drift_monitor:
            return None
        
        # Compare to historical baseline
        drift_report = await self.drift_monitor.check_drift(
            current=current_assessment,
            history=self.session_db.get_recent_assessments(
                agent_id=self.agent_id,
                count=self.drift_window_size
            )
        )
        
        if drift_report["significant_drift"]:
            # Log warning
            logger.warning(f"Drift detected: {drift_report}")
            
            # Store in DB
            self.session_db.log_drift_event(
                cascade_id=self.cascade_id,
                drift_type=drift_report["type"],
                magnitude=drift_report["magnitude"],
                details=drift_report
            )
        
        return drift_report

# New table for drift tracking
CREATE TABLE drift_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cascade_id TEXT,
    drift_type TEXT,  -- behavioral, epistemic, calibration, context
    magnitude REAL,
    details JSON,
    timestamp TEXT,
    FOREIGN KEY(cascade_id) REFERENCES cascades(cascade_id)
);
```

---

### Area 4: Bayesian Belief Integration

**Current Implementation:**
- `bayesian_belief_tracker.py` exists
- Tracks belief evolution over time
- Evidence-based updates

**Deep Integration Questions:**

1. **When should beliefs be updated?**
   - After each assessment? (too frequent?)
   - After postflight? (better for delta)
   - On explicit evidence? (manual)

2. **What are "beliefs"?**
   - Domain knowledge ("I know Python")
   - Task capabilities ("I can refactor")
   - Environmental facts ("API is available")
   - Meta-beliefs ("My assessments are accurate")

3. **Storage:**
   - Where are beliefs stored? (SessionDB? Separate?)
   - How to query beliefs? ("What do I believe about X?")
   - How to visualize belief evolution?

**Recommendations:**

```python
# Bayesian belief storage
CREATE TABLE bayesian_beliefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT,
    belief_key TEXT,  -- e.g., "domain_knowledge.python"
    prior_probability REAL,
    posterior_probability REAL,
    evidence JSON,  -- Supporting evidence
    updated_at TEXT,
    cascade_id TEXT  -- Which cascade updated this
);

# Integration point
class CanonicalEpistemicCascade:
    async def _update_beliefs_from_delta(
        self,
        preflight: EpistemicAssessment,
        postflight: EpistemicAssessment,
        delta: Dict[str, float]
    ):
        """Update Bayesian beliefs based on learning delta"""
        
        if not self.bayesian_tracker:
            return
        
        # If KNOW increased significantly, update domain belief
        if delta["know"] > 0.2:
            await self.bayesian_tracker.update_belief(
                belief_key=f"domain.{self.domain}",
                evidence={
                    "type": "successful_task",
                    "delta": delta["know"],
                    "task": self.task
                },
                cascade_id=self.cascade_id
            )
        
        # If consistently overconfident, update meta-belief
        if self.calibration_status == "overconfident":
            await self.bayesian_tracker.update_belief(
                belief_key="meta.assessment_accuracy",
                evidence={
                    "type": "overconfident_prediction",
                    "magnitude": delta["uncertainty"]
                },
                cascade_id=self.cascade_id
            )
```

---

### Area 5: Investigation Phase Extensibility

**Current Implementation:**
- `investigation_strategy.py` with domain classification
- Tool recommendation system
- Limited to built-in tools

**Extension Scenarios:**

1. **RAG File Searches:**
   - Query: "Find similar code patterns"
   - Need: Vector DB integration (Qdrant, Pinecone, Chroma)
   - Storage: Learning deltas → embeddings → vector DB
   - Retrieval: Semantic similarity search

2. **Custom Web API Searches:**
   - Query: "Check latest documentation"
   - Need: Plugin architecture for custom APIs
   - Auth: API keys, OAuth
   - Rate limiting: Built-in

3. **Vector DB for Pattern Storage:**
   - Store: Successful task patterns
   - Store: Learning deltas (what worked?)
   - Query: "Similar tasks I've done before"
   - Retrieve: Context for new tasks

**Deep Integration Questions:**

1. **Plugin Architecture:**
   - How do custom investigation tools register?
   - How does CASCADE discover available tools?
   - How to prevent tool conflicts?

2. **Data Flow:**
   - Investigation results → Where stored?
   - Evidence collected → How linked to assessment?
   - Learning patterns → How extracted and stored?

3. **Extensibility vs Complexity:**
   - Simple tasks shouldn't load all plugins
   - Complex tasks need rich tooling
   - How to balance?

**Recommendations:**

```python
# Plugin registry for investigation tools
class InvestigationPluginRegistry:
    """Registry for custom investigation tools"""
    
    def __init__(self):
        self._plugins: Dict[str, InvestigationPlugin] = {}
    
    def register(self, plugin: InvestigationPlugin):
        """Register a custom investigation plugin"""
        self._plugins[plugin.name] = plugin
    
    def get_tools_for_domain(self, domain: str) -> List[InvestigationPlugin]:
        """Get relevant tools for domain"""
        return [p for p in self._plugins.values() if domain in p.domains]

# Base class for plugins
class InvestigationPlugin(ABC):
    """Base class for investigation plugins"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name"""
        pass
    
    @property
    @abstractmethod
    def domains(self) -> List[str]:
        """Applicable domains (code, docs, security, etc.)"""
        pass
    
    @abstractmethod
    async def investigate(self, query: str, context: Dict) -> Dict:
        """Execute investigation"""
        pass

# Example: RAG plugin
class RAGInvestigationPlugin(InvestigationPlugin):
    """RAG-based investigation using vector DB"""
    
    def __init__(self, vector_db: VectorDB):
        self.vector_db = vector_db
    
    @property
    def name(self) -> str:
        return "rag_search"
    
    @property
    def domains(self) -> List[str]:
        return ["code", "documentation"]
    
    async def investigate(self, query: str, context: Dict) -> Dict:
        """Search vector DB for similar patterns"""
        
        # Embed query
        query_embedding = await self.embed(query)
        
        # Search similar
        results = await self.vector_db.search(
            embedding=query_embedding,
            limit=5
        )
        
        return {
            "plugin": self.name,
            "results": results,
            "evidence": [r["metadata"] for r in results]
        }

# Integration in CASCADE
class CanonicalEpistemicCascade:
    def __init__(
        self,
        investigation_plugins: Optional[List[InvestigationPlugin]] = None
    ):
        self.plugin_registry = InvestigationPluginRegistry()
        
        # Register plugins
        if investigation_plugins:
            for plugin in investigation_plugins:
                self.plugin_registry.register(plugin)
    
    async def _investigate(self, strategy: Dict) -> Dict:
        """Execute investigation with plugins"""
        
        domain = strategy.get("domain", "general")
        
        # Get relevant plugins
        plugins = self.plugin_registry.get_tools_for_domain(domain)
        
        # Execute investigations
        results = {}
        for plugin in plugins:
            try:
                result = await plugin.investigate(
                    query=strategy["query"],
                    context=self.context
                )
                results[plugin.name] = result
            except Exception as e:
                logger.warning(f"Plugin {plugin.name} failed: {e}")
        
        return results
```

---

### Area 6: Learning Delta Pattern Storage

**Use Case:** Store successful patterns for future retrieval

**Questions:**

1. **What patterns to store?**
   - Tasks with large positive deltas (successful learning)
   - Well-calibrated workflows (accurate predictions)
   - Investigation strategies that worked
   - Domain-specific successful approaches

2. **Storage format:**
   - Vector embeddings for semantic search
   - Structured metadata for filtering
   - Full cascade data for inspection

3. **Retrieval:**
   - "Find similar tasks I succeeded at"
   - "What investigation strategy worked for X domain?"
   - "Show me well-calibrated assessments"

**Recommendations:**

```python
# New table for pattern storage
CREATE TABLE learning_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cascade_id TEXT,
    pattern_type TEXT,  -- successful_task, investigation_strategy, etc.
    domain TEXT,
    task_description TEXT,
    delta_know REAL,
    delta_do REAL,
    calibration_status TEXT,
    investigation_strategy JSON,
    embedding BLOB,  -- Vector embedding for similarity search
    created_at TEXT,
    FOREIGN KEY(cascade_id) REFERENCES cascades(cascade_id)
);

# Pattern extraction after successful cascade
async def _extract_learning_pattern(
    self,
    cascade_result: Dict
) -> Optional[LearningPattern]:
    """Extract pattern from successful cascade"""
    
    delta = cascade_result["delta"]
    
    # Only store successful learning
    if delta["know"] < 0.2 and delta["do"] < 0.2:
        return None
    
    # Only store well-calibrated
    if cascade_result["calibration"]["status"] != "well-calibrated":
        return None
    
    # Create pattern
    pattern = LearningPattern(
        cascade_id=self.cascade_id,
        pattern_type="successful_task",
        domain=self.domain,
        task_description=self.task,
        delta_know=delta["know"],
        delta_do=delta["do"],
        calibration_status=cascade_result["calibration"]["status"],
        investigation_strategy=cascade_result.get("investigation_strategy"),
        embedding=await self.embed(self.task)  # For similarity search
    )
    
    # Store
    await self.session_db.store_learning_pattern(pattern)
    
    return pattern

# Retrieval for similar tasks
async def get_similar_successful_tasks(
    self,
    current_task: str,
    limit: int = 5
) -> List[LearningPattern]:
    """Retrieve similar successful tasks for guidance"""
    
    # Embed current task
    query_embedding = await self.embed(current_task)
    
    # Search similar patterns
    patterns = await self.session_db.search_learning_patterns(
        embedding=query_embedding,
        limit=limit,
        filters={"calibration_status": "well-calibrated"}
    )
    
    return patterns
```

---

## 🚨 Potential Issues to Address Now

### Issue 1: SessionDB Querying
**Problem:** assessment_data as JSON blob is hard to query
**Impact:** Can't easily query "all assessments where KNOW > 0.8"
**Solution:** Add vector columns for common queries OR use JSONB in PostgreSQL

### Issue 2: Reflex Frame Cleanup
**Problem:** Reflex frames accumulate indefinitely
**Impact:** Disk space, slow lookups
**Solution:** Add cleanup policy (keep last N, or TTL-based)

### Issue 3: Model Version Tracking
**Problem:** No way to know which model/version produced assessment
**Impact:** Can't analyze model-specific patterns or bugs
**Solution:** Add agent_model, agent_version fields

### Issue 4: Schema Versioning
**Problem:** No version field in data structures
**Impact:** Breaking changes will corrupt old data
**Solution:** Add version field to all data structures

### Issue 5: Investigation Loop Limits
**Problem:** max_investigation_rounds hardcoded to 3
**Impact:** May be too few for complex tasks, too many for simple
**Solution:** Make configurable, track why loop exited

### Issue 6: Calibration Result Storage
**Problem:** Calibration status computed but not stored
**Impact:** Can't query historical calibration accuracy
**Solution:** Add calibration_results table

### Issue 7: Plugin Discovery
**Problem:** No plugin registry, tools are hardcoded
**Impact:** Can't extend investigation without core changes
**Solution:** Implement InvestigationPluginRegistry

### Issue 8: Context Drift Detection
**Problem:** Context changes not tracked
**Impact:** May not notice when environment changed
**Solution:** Add context hashing and drift detection

### Issue 9: Belief Storage
**Problem:** Bayesian beliefs not persisted
**Impact:** Beliefs lost between sessions
**Solution:** Add bayesian_beliefs table

### Issue 10: Vector DB Integration
**Problem:** No standard way to integrate vector DBs
**Impact:** Every developer implements differently
**Solution:** Create VectorDBPlugin interface

---

## 🧪 Testing Strategy

### Test 1: Schema Evolution
**Test:** Add new field, verify old data still works
```python
def test_schema_evolution():
    # Create cascade with old schema
    old_cascade = create_cascade_v1()
    
    # Upgrade schema
    upgrade_database()
    
    # Verify old cascade still readable
    assert can_read_cascade(old_cascade)
```

### Test 2: Plugin Integration
**Test:** Register custom plugin, verify it's used
```python
def test_custom_investigation_plugin():
    # Register custom plugin
    registry.register(CustomRAGPlugin())
    
    # Run CASCADE
    result = await cascade.run(task="...")
    
    # Verify plugin was used
    assert "custom_rag" in result["investigation"]["plugins_used"]
```

### Test 3: Drift Detection
**Test:** Simulate drift, verify detection
```python
def test_drift_detection():
    # Create baseline assessments
    for i in range(10):
        create_assessment(know=0.5)
    
    # Create drifted assessment
    create_assessment(know=0.9)  # Sudden jump
    
    # Verify drift detected
    drift = check_drift()
    assert drift["significant_drift"] == True
```

### Test 4: Calibration Tracking
**Test:** Verify calibration results stored
```python
def test_calibration_storage():
    # Run cascade
    result = await cascade.run(task="...")
    
    # Verify calibration stored
    calibration = db.get_calibration_result(result["cascade_id"])
    assert calibration["status"] == "well-calibrated"
```

### Test 5: Learning Pattern Retrieval
**Test:** Store pattern, retrieve similar
```python
def test_learning_pattern_retrieval():
    # Complete successful cascade
    await cascade.run(task="Implement OAuth2")
    
    # Query similar tasks
    similar = await get_similar_successful_tasks("Implement JWT auth")
    
    # Verify similarity
    assert len(similar) > 0
    assert "OAuth2" in similar[0].task_description
```

---

## 📋 Action Items

### Before Release (Critical)
1. [ ] Add schema versioning to all data structures
2. [ ] Add agent_model/agent_version fields
3. [ ] Add calibration_results table
4. [ ] Add indices for common queries
5. [ ] Implement reflex frame cleanup policy
6. [ ] Add context drift detection
7. [ ] Document extension points clearly

### Before 1.1 (High Priority)
8. [ ] Implement InvestigationPluginRegistry
9. [ ] Add bayesian_beliefs persistence
10. [ ] Create VectorDBPlugin interface
11. [ ] Add learning_patterns table
12. [ ] Implement pattern extraction
13. [ ] Add drift_events table

### Future (Nice to Have)
14. [ ] Migration tools for schema changes
15. [ ] Performance optimization (vector search)
16. [ ] Distributed CASCADE (multiple nodes)
17. [ ] Real-time drift monitoring dashboard

---

## 🎯 Summary

**Current State:**
- ✅ Basic data layer works (unit tests passing)
- ⚠️ Missing: Version tracking, calibration storage, plugin system
- ⚠️ Over-engineered: cascade_metadata (unused?)
- ⚠️ Under-engineered: No extension points for investigation

**Recommendations:**
1. **Add before release:** Versioning, agent tracking, calibration storage
2. **Design now, implement later:** Plugin registry, vector DB interface
3. **Document:** Extension points, data schema, migration strategy

**Risk Assessment:**
- **High Risk:** No schema versioning (breaking changes will hurt)
- **Medium Risk:** No plugin system (developers will hack core)
- **Low Risk:** Missing indices (can add later without breaking)

**Next Steps:**
1. Review this analysis
2. Prioritize fixes (before release vs later)
3. Implement critical items (versioning, agent tracking)
4. Create extension point documentation
5. Test with realistic complexity scenarios

---

**Ready for detailed implementation planning when you are!**
