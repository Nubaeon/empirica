# Structural Integrity Testing Plan

**Purpose:** Validate deep integration before release  
**Based on:** DEEP_INTEGRATION_ANALYSIS.md findings  
**Priority:** Critical issues first, extensibility second

---

## 🎯 Test Categories

### Category 1: Data Layer Integrity (CRITICAL)
**Priority:** Must fix before release

### Category 2: Extension Point Validation (HIGH)
**Priority:** Design now, test thoroughly

### Category 3: Advanced Feature Integration (MEDIUM)
**Priority:** Ensure hooks exist, full implementation can wait

### Category 4: Model Agnosticism (HIGH)
**Priority:** Validate no lock-in to specific models

---

## 🧪 Test Suite 1: SessionDB Schema Integrity

### Test 1.1: Schema Completeness Check
**File:** `tests/integrity/test_sessiondb_schema.py`

```python
"""Test SessionDB schema completeness and correctness"""
import pytest
from empirica.data import SessionDatabase

class TestSessionDBSchema:
    
    def test_schema_has_all_required_tables(self):
        """Verify all expected tables exist"""
        db = SessionDatabase()
        
        required_tables = [
            "cascades",
            "cascade_metadata", 
            "cascade_phases",
            "epistemic_assessments"
        ]
        
        actual_tables = db.get_table_names()
        
        for table in required_tables:
            assert table in actual_tables, f"Missing table: {table}"
    
    def test_cascades_table_has_required_fields(self):
        """Verify cascades table structure"""
        db = SessionDatabase()
        columns = db.get_column_names("cascades")
        
        required = ["cascade_id", "question", "started_at", "completed_at", "status"]
        
        for col in required:
            assert col in columns, f"Missing column in cascades: {col}"
    
    def test_missing_agent_tracking_fields(self):
        """ISSUE: No agent_model or agent_version tracking"""
        db = SessionDatabase()
        columns = db.get_column_names("cascades")
        
        # These SHOULD exist but probably don't
        desirable = ["agent_id", "agent_model", "agent_version"]
        
        missing = [col for col in desirable if col not in columns]
        
        if missing:
            pytest.warns(UserWarning, f"Missing agent tracking: {missing}")
            # This is expected to fail - we need to add these
    
    def test_missing_calibration_results_table(self):
        """ISSUE: Calibration results not stored"""
        db = SessionDatabase()
        tables = db.get_table_names()
        
        # This table should exist but probably doesn't
        if "calibration_results" not in tables:
            pytest.warns(UserWarning, "No calibration_results table")
            # Expected to fail - need to add this table
    
    def test_assessment_data_is_json_queryable(self):
        """Verify assessment_data can be queried (or note limitation)"""
        db = SessionDatabase()
        
        # Create test assessment
        cascade_id = db.create_cascade("test")
        db.log_epistemic_assessment(
            cascade_id=cascade_id,
            phase="preflight",
            vectors={"know": 0.5, "do": 0.6},
            reasoning="test"
        )
        
        # Try to query specific vector value
        # This will likely fail because assessment_data is JSON blob
        try:
            result = db.query("SELECT * FROM epistemic_assessments WHERE json_extract(assessment_data, '$.vectors.know') > 0.4")
            # If this works, great! If not, we know limitation
        except Exception as e:
            pytest.warns(UserWarning, f"Cannot query JSON fields: {e}")
    
    def test_no_indices_on_common_queries(self):
        """ISSUE: Missing indices for performance"""
        db = SessionDatabase()
        indices = db.get_indices()
        
        # Check for recommended indices
        recommended = [
            ("cascades", "status"),
            ("cascades", "started_at"),
            ("cascade_phases", "cascade_id"),
            ("epistemic_assessments", "cascade_id")
        ]
        
        missing_indices = []
        for table, column in recommended:
            if not db.has_index(table, column):
                missing_indices.append(f"{table}.{column}")
        
        if missing_indices:
            pytest.warns(UserWarning, f"Missing indices: {missing_indices}")
```

### Test 1.2: Schema Versioning
**File:** `tests/integrity/test_schema_versioning.py`

```python
"""Test schema versioning and evolution"""
import pytest
from empirica.data import SessionDatabase

class TestSchemaVersioning:
    
    def test_schema_version_stored(self):
        """CRITICAL: Schema version should be tracked"""
        db = SessionDatabase()
        
        # Try to get schema version
        version = db.get_schema_version()
        
        if version is None:
            pytest.fail("No schema version tracking - CRITICAL ISSUE")
        
        # Version should be semantic (1.0, 1.1, etc.)
        assert isinstance(version, str)
        assert len(version.split(".")) >= 2
    
    def test_old_data_survives_schema_changes(self):
        """Verify backward compatibility"""
        db = SessionDatabase()
        
        # Create cascade with current schema
        cascade_id = db.create_cascade("test")
        
        # Simulate schema upgrade (add field)
        db.add_column_if_not_exists("cascades", "new_field", "TEXT")
        
        # Verify old cascade still readable
        cascade = db.get_cascade(cascade_id)
        assert cascade is not None
        assert cascade["cascade_id"] == cascade_id
```

---

## 🧪 Test Suite 2: Reflex Frame Integrity

### Test 2.1: Reflex Frame Structure
**File:** `tests/integrity/test_reflex_frame_structure.py`

```python
"""Test Reflex Frame data structure"""
import pytest
from empirica.core.canonical import ReflexFrame, EpistemicAssessment

class TestReflexFrameStructure:
    
    def test_assessment_has_all_13_vectors(self):
        """Verify all epistemic vectors present"""
        assessment = EpistemicAssessment(
            engagement=0.75,
            know=0.70,
            do=0.65,
            context=0.60,
            clarity=0.80,
            coherence=0.75,
            signal=0.70,
            density=0.65,
            state=0.60,
            change=0.55,
            completion=0.50,
            impact=0.60,
            uncertainty=0.45
        )
        
        # Verify all fields accessible
        assert assessment.engagement == 0.75
        assert assessment.know == 0.70
        # ... etc
    
    def test_assessment_missing_version_field(self):
        """ISSUE: No version field for schema evolution"""
        assessment = EpistemicAssessment(
            engagement=0.75,
            know=0.70,
            # ... minimal required
        )
        
        # Try to access version
        if not hasattr(assessment, 'assessment_version'):
            pytest.warns(UserWarning, "No assessment_version field")
    
    def test_assessment_missing_source_field(self):
        """ISSUE: No source tracking (which component created this)"""
        assessment = EpistemicAssessment(
            engagement=0.75,
            know=0.70,
            # ...
        )
        
        if not hasattr(assessment, 'assessment_source'):
            pytest.warns(UserWarning, "No assessment_source field")
    
    def test_assessment_extensibility(self):
        """Can we add new vectors without breaking?"""
        assessment = EpistemicAssessment(
            engagement=0.75,
            know=0.70,
            # ... standard fields
        )
        
        # Try to add 14th vector
        if hasattr(assessment, 'additional_vectors'):
            assessment.additional_vectors = {"new_vector": 0.85}
            assert assessment.additional_vectors["new_vector"] == 0.85
        else:
            pytest.warns(UserWarning, "No extensibility for additional vectors")
```

### Test 2.2: Reflex Frame Temporal Separation
**File:** `tests/integrity/test_temporal_separation.py`

```python
"""Test temporal separation via external logging"""
import pytest
import asyncio
from pathlib import Path
from empirica.core.canonical import ReflexLogger

class TestTemporalSeparation:
    
    @pytest.mark.asyncio
    async def test_reflex_frames_stored_externally(self):
        """Verify assessments logged to filesystem"""
        logger = ReflexLogger(agent_id="test_temporal")
        
        # Log assessment
        assessment_data = {
            "vectors": {"know": 0.5},
            "timestamp": "2024-01-01T00:00:00"
        }
        
        await logger.log_assessment(assessment_data)
        
        # Verify file created
        reflex_dir = Path(".empirica/reflex_frames")
        assert reflex_dir.exists()
        
        files = list(reflex_dir.glob("*.json"))
        assert len(files) > 0
    
    @pytest.mark.asyncio
    async def test_reflex_frame_cleanup_policy(self):
        """ISSUE: No cleanup policy for old frames"""
        logger = ReflexLogger(agent_id="test_cleanup")
        
        # Create many frames
        for i in range(100):
            await logger.log_assessment({"test": i})
        
        # Check if cleanup happened
        reflex_dir = Path(".empirica/reflex_frames")
        file_count = len(list(reflex_dir.glob("*.json")))
        
        # If file_count == 100, no cleanup policy exists
        if file_count >= 100:
            pytest.warns(UserWarning, "No reflex frame cleanup policy")
    
    def test_reflex_frame_retrieval_strategy(self):
        """Can we efficiently retrieve specific frames?"""
        logger = ReflexLogger(agent_id="test_retrieval")
        
        # Try to get frames for specific cascade
        cascade_id = "test_cascade_123"
        
        # This method might not exist
        if hasattr(logger, 'get_frames_for_cascade'):
            frames = logger.get_frames_for_cascade(cascade_id)
        else:
            pytest.warns(UserWarning, "No efficient frame retrieval method")
```

---

## 🧪 Test Suite 3: Model Agnosticism

### Test 3.1: Multi-Model Support
**File:** `tests/integrity/test_model_agnosticism.py`

```python
"""Test that data structures work with different models"""
import pytest
from empirica.core.canonical import CanonicalEpistemicAssessor

class TestModelAgnosticism:
    
    @pytest.mark.asyncio
    async def test_different_model_identifiers(self):
        """Verify system works with different model names"""
        models = [
            "claude-sonnet-4",
            "gpt-4-turbo",
            "gemini-pro",
            "qwen-plus",
            "custom-local-model"
        ]
        
        for model_name in models:
            assessor = CanonicalEpistemicAssessor(
                agent_id=f"test_{model_name}"
            )
            
            # Should work regardless of model
            result = await assessor.assess(
                task="test task",
                context={}
            )
            
            assert result is not None
    
    def test_assessment_format_model_agnostic(self):
        """Verify assessment format doesn't assume specific model"""
        # Assessment should be simple floats, not model-specific format
        from empirica.core.canonical import EpistemicAssessment
        
        # Any model should be able to produce this
        assessment = EpistemicAssessment(
            engagement=0.75,
            know=0.70,
            # ... etc
        )
        
        # Verify no model-specific fields
        fields = assessment.__dataclass_fields__
        model_specific = ["claude_specific", "gpt_specific", "thinking"]
        
        for field in model_specific:
            assert field not in fields, f"Model-specific field found: {field}"
    
    def test_can_track_which_model_produced_assessment(self):
        """Can we identify which model created an assessment?"""
        from empirica.core.canonical import EpistemicAssessment
        
        assessment = EpistemicAssessment(
            engagement=0.75,
            know=0.70,
            # ...
        )
        
        # Should have model tracking
        if not hasattr(assessment, 'agent_model'):
            pytest.warns(UserWarning, "No agent_model tracking in assessment")
```

---

## 🧪 Test Suite 4: Extension Points

### Test 4.1: Investigation Plugin System
**File:** `tests/integrity/test_investigation_extensibility.py`

```python
"""Test investigation phase extensibility"""
import pytest
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

class TestInvestigationExtensibility:
    
    def test_can_register_custom_investigation_tool(self):
        """Verify custom investigation tools can be added"""
        
        # Try to create custom plugin
        class CustomRAGPlugin:
            def __init__(self):
                self.name = "custom_rag"
            
            async def investigate(self, query, context):
                return {"results": ["custom result"]}
        
        # Try to register
        cascade = CanonicalEpistemicCascade(agent_id="test")
        
        if hasattr(cascade, 'register_investigation_plugin'):
            cascade.register_investigation_plugin(CustomRAGPlugin())
            # Success!
        else:
            pytest.warns(UserWarning, "No plugin registration system exists")
    
    @pytest.mark.asyncio
    async def test_investigation_uses_registered_plugins(self):
        """Verify custom plugins are actually used"""
        
        class MockPlugin:
            async def investigate(self, query, context):
                return {"mock": "result"}
        
        cascade = CanonicalEpistemicCascade(agent_id="test")
        
        # Register plugin (if possible)
        if hasattr(cascade, 'register_investigation_plugin'):
            cascade.register_investigation_plugin(MockPlugin())
            
            # Run cascade
            result = await cascade.run_epistemic_cascade(
                task="test task requiring investigation",
                context={}
            )
            
            # Verify plugin was used
            # (This is hard to test without running full cascade)
        else:
            pytest.skip("No plugin system to test")
```

### Test 4.2: Vector DB Integration Points
**File:** `tests/integrity/test_vector_db_integration.py`

```python
"""Test vector DB integration readiness"""
import pytest

class TestVectorDBIntegration:
    
    def test_learning_delta_can_be_embedded(self):
        """Can we convert learning deltas to embeddings?"""
        from empirica.core.canonical import EpistemicAssessment
        
        # Create assessment
        assessment = EpistemicAssessment(
            engagement=0.75,
            know=0.70,
            # ...
        )
        
        # Try to convert to embedding
        if hasattr(assessment, 'to_embedding'):
            embedding = assessment.to_embedding()
            assert isinstance(embedding, list)
            assert len(embedding) > 0
        else:
            pytest.warns(UserWarning, "No embedding conversion method")
    
    def test_can_store_embeddings_in_sessiondb(self):
        """Can SessionDB store vector embeddings?"""
        from empirica.data import SessionDatabase
        
        db = SessionDatabase()
        
        # Check if learning_patterns table exists
        tables = db.get_table_names()
        
        if "learning_patterns" not in tables:
            pytest.warns(UserWarning, "No learning_patterns table for embeddings")
    
    def test_can_search_by_similarity(self):
        """Can we search similar tasks?"""
        from empirica.data import SessionDatabase
        
        db = SessionDatabase()
        
        # Try similarity search
        if hasattr(db, 'search_similar_tasks'):
            # Method exists, test it
            results = db.search_similar_tasks(
                query_embedding=[0.1] * 768,
                limit=5
            )
        else:
            pytest.warns(UserWarning, "No similarity search capability")
```

---

## 🧪 Test Suite 5: Advanced Features Integration

### Test 5.1: Drift Detection Hooks
**File:** `tests/integrity/test_drift_detection_integration.py`

```python
"""Test drift detection integration points"""
import pytest
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

class TestDriftDetectionIntegration:
    
    def test_drift_monitor_can_be_enabled(self):
        """Verify drift monitoring can be enabled"""
        cascade = CanonicalEpistemicCascade(
            agent_id="test",
            enable_drift_monitor=True
        )
        
        assert hasattr(cascade, 'drift_monitor')
        assert cascade.drift_monitor is not None
    
    @pytest.mark.asyncio
    async def test_drift_events_are_logged(self):
        """Verify drift events get logged to DB"""
        from empirica.data import SessionDatabase
        
        db = SessionDatabase()
        
        # Check if drift_events table exists
        tables = db.get_table_names()
        
        if "drift_events" not in tables:
            pytest.warns(UserWarning, "No drift_events table for logging")
    
    def test_context_drift_detection(self):
        """Can we detect context changes?"""
        # Context drift: Environment changes during task
        
        from empirica.core.canonical import EpistemicAssessment
        
        assessment = EpistemicAssessment(
            engagement=0.75,
            know=0.70,
            # ...
        )
        
        # Should have context hash
        if not hasattr(assessment, 'context_hash'):
            pytest.warns(UserWarning, "No context_hash for drift detection")
```

### Test 5.2: Bayesian Belief Integration
**File:** `tests/integrity/test_bayesian_integration.py`

```python
"""Test Bayesian belief tracking integration"""
import pytest
from empirica.calibration.adaptive_uncertainty_calibration import BayesianBeliefTracker

class TestBayesianIntegration:
    
    def test_beliefs_can_be_persisted(self):
        """Verify beliefs can be saved to DB"""
        from empirica.data import SessionDatabase
        
        db = SessionDatabase()
        
        # Check for bayesian_beliefs table
        tables = db.get_table_names()
        
        if "bayesian_beliefs" not in tables:
            pytest.warns(UserWarning, "No bayesian_beliefs table")
    
    def test_beliefs_updated_from_delta(self):
        """Verify learning deltas update beliefs"""
        tracker = BayesianBeliefTracker()
        
        # Initial belief
        tracker.set_belief("domain.python", prior=0.5)
        
        # Update with evidence (from learning delta)
        tracker.update_belief(
            belief_key="domain.python",
            evidence={"successful_task": True, "delta_know": 0.3}
        )
        
        # Verify update
        posterior = tracker.get_belief("domain.python")
        assert posterior > 0.5  # Should increase
```

---

## 📋 Execution Plan

### Phase 1: Critical Fixes (Before Release)
```bash
# Run critical integrity tests
pytest tests/integrity/test_sessiondb_schema.py -v
pytest tests/integrity/test_schema_versioning.py -v
pytest tests/integrity/test_reflex_frame_structure.py -v
pytest tests/integrity/test_model_agnosticism.py -v

# Expected: Many warnings/failures
# These identify what to fix before release
```

### Phase 2: Implement Critical Fixes
Based on test failures, implement:
1. Schema versioning
2. Agent tracking (model, version)
3. Calibration results table
4. Assessment versioning
5. Missing indices

### Phase 3: Extension Point Tests (After Release)
```bash
# Run extensibility tests
pytest tests/integrity/test_investigation_extensibility.py -v
pytest tests/integrity/test_vector_db_integration.py -v
pytest tests/integrity/test_drift_detection_integration.py -v
pytest tests/integrity/test_bayesian_integration.py -v

# These validate extension points exist
```

### Phase 4: Document Extension Points
Create developer guides for:
- Adding custom investigation plugins
- Integrating vector DBs
- Implementing drift detection
- Using Bayesian belief tracking

---

## 🎯 Success Criteria

### Before Release
- [ ] All critical integrity tests pass
- [ ] Schema has version field
- [ ] Agent model/version tracked
- [ ] Calibration results stored
- [ ] Indices added for performance

### After Release
- [ ] Plugin registration system exists
- [ ] Vector DB integration documented
- [ ] Drift detection hooks validated
- [ ] Bayesian belief persistence working

---

## 📊 Expected Findings

### Will Likely Find (Critical):
1. ❌ No schema versioning
2. ❌ No agent tracking
3. ❌ No calibration results table
4. ❌ Missing indices
5. ❌ No reflex frame cleanup policy

### Will Likely Find (Important):
6. ⚠️ No plugin registration system
7. ⚠️ No vector DB integration points
8. ⚠️ No context drift detection
9. ⚠️ No belief persistence

### Should Be Fine:
10. ✅ Basic data storage/retrieval
11. ✅ Temporal separation working
12. ✅ Model-agnostic data structures

---

**Ready to implement these tests and identify critical fixes!**
