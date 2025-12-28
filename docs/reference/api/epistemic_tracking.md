# Epistemic Tracking API

**Module:** `empirica.core.epistemic.tracking` and related modules
**Category:** Epistemic Self-Awareness
**Stability:** Production Ready

---

## Overview

The Epistemic Tracking API provides the core functionality for measuring and tracking AI self-awareness through 13-dimensional epistemic vectors. This system enables genuine self-assessment rather than heuristic-based evaluation.

### The 13 Epistemic Vectors

The system tracks 13 dimensions of epistemic state:

1. **engagement** - Active attention and focus
2. **know** - Domain knowledge and understanding
3. **do** - Capability and skill to execute
4. **context** - Situational awareness
5. **clarity** - Clarity of thought and reasoning
6. **coherence** - Logical consistency
7. **signal** - Quality of information processed
8. **density** - Information richness (can be too high)
9. **state** - Current cognitive state
10. **change** - Adaptability and learning
11. **completion** - Progress toward goals
12. **impact** - Expected significance of work
13. **uncertainty** - Acknowledged uncertainty

---

## Epistemic Tracker

### `class EpistemicTracker`

Main class for tracking epistemic state throughout AI workflows.

#### `__init__(self, session_id: str, ai_id: str, db_path: Optional[str] = None)`

Initialize the epistemic tracker.

**Parameters:**
- `session_id: str` - Session identifier
- `ai_id: str` - AI identifier
- `db_path: Optional[str]` - Database path, defaults to standard location

**Example:**
```python
from empirica.core.epistemic.tracking import EpistemicTracker

tracker = EpistemicTracker(
    session_id="sess-123",
    ai_id="claude-sonnet-4"
)
```

### `capture_assessment(self, phase: str, vectors: Dict[str, float], cascade_id: Optional[str] = None, round_num: int = 1, metadata: Optional[Dict[str, Any]] = None, reasoning: Optional[str] = None) -> str`

Capture an epistemic assessment at a specific phase.

**Parameters:**
- `phase: str` - Current phase ('PREFLIGHT', 'THINK', 'PLAN', 'INVESTIGATE', 'CHECK', 'ACT', 'POSTFLIGHT')
- `vectors: Dict[str, float]` - Dictionary of 13 epistemic vectors
- `cascade_id: Optional[str]` - Optional CASCADE identifier
- `round_num: int` - Current round number, default 1
- `metadata: Optional[Dict[str, Any]]` - Optional metadata
- `reasoning: Optional[str]` - Optional reasoning for the assessment

**Returns:** `str` - Assessment ID

**Example:**
```python
vectors = {
    "engagement": 0.85,
    "know": 0.72,
    "do": 0.68,
    "context": 0.91,
    "clarity": 0.75,
    "coherence": 0.82,
    "signal": 0.79,
    "density": 0.65,
    "state": 0.77,
    "change": 0.88,
    "completion": 0.60,
    "impact": 0.74,
    "uncertainty": 0.23
}

assessment_id = tracker.capture_assessment(
    phase="PREFLIGHT",
    vectors=vectors,
    reasoning="High uncertainty due to unfamiliar authentication patterns, but strong context about project requirements"
)
```

### `get_latest_assessment(self, session_id: str, phase: Optional[str] = None) -> Optional[Dict]`

Get the most recent assessment for a session, optionally filtered by phase.

**Parameters:**
- `session_id: str` - Session identifier
- `phase: Optional[str]` - Optional phase filter

**Returns:** `Optional[Dict]` - Latest assessment or None

**Example:**
```python
latest = tracker.get_latest_assessment(session_id="sess-123", phase="CHECK")
if latest:
    print(f"Current uncertainty: {latest['vectors']['uncertainty']}")
```

### `get_assessment_history(self, session_id: str, phase: Optional[str] = None, limit: Optional[int] = None) -> List[Dict]`

Get assessment history for a session.

**Parameters:**
- `session_id: str` - Session identifier
- `phase: Optional[str]` - Optional phase filter
- `limit: Optional[int]` - Optional limit on results

**Returns:** `List[Dict]` - List of assessment dictionaries

**Example:**
```python
history = tracker.get_assessment_history(session_id="sess-123", phase="CHECK", limit=5)
for assessment in history:
    print(f"Round {assessment['round']}: Uncertainty={assessment['vectors']['uncertainty']}")
```

### `calculate_delta(self, assessment_id_1: str, assessment_id_2: str) -> Dict[str, float]`

Calculate the epistemic delta between two assessments.

**Parameters:**
- `assessment_id_1: str` - First assessment ID
- `assessment_id_2: str` - Second assessment ID

**Returns:** `Dict[str, float]` - Delta values for each vector

**Example:**
```python
delta = tracker.calculate_delta(
    assessment_id_1="pre-assessment",
    assessment_id_2="post-assessment"
)

print(f"Knowledge gain: {delta['know']}")
print(f"Uncertainty reduction: {delta['uncertainty']}")
```

---

## Epistemic Snapshots

### `create_snapshot(self, session_id: str, ai_id: str, cascade_id: Optional[str] = None, description: Optional[str] = None) -> str`

Create an epistemic snapshot of the current state.

**Parameters:**
- `session_id: str` - Session identifier
- `ai_id: str` - AI identifier
- `cascade_id: Optional[str]` - Optional CASCADE identifier
- `description: Optional[str]` - Optional snapshot description

**Returns:** `str` - Snapshot ID

**Example:**
```python
snapshot_id = tracker.create_snapshot(
    session_id="sess-123",
    ai_id="claude-sonnet-4",
    description="After completing authentication module design"
)
```

### `get_snapshot(self, snapshot_id: str) -> Optional[Dict]`

Get a specific snapshot by ID.

**Parameters:**
- `snapshot_id: str` - Snapshot identifier

**Returns:** `Optional[Dict]` - Snapshot data or None

**Example:**
```python
snapshot = tracker.get_snapshot(snapshot_id="snap-456")
if snapshot:
    print(f"Snapshot from: {snapshot['timestamp']}")
    print(f"Vectors: {snapshot['vectors']}")
```

### `compare_snapshots(self, snapshot_id_1: str, snapshot_id_2: str) -> Dict[str, Any]`

Compare two snapshots to see changes.

**Parameters:**
- `snapshot_id_1: str` - First snapshot ID
- `snapshot_id_2: str` - Second snapshot ID

**Returns:** `Dict[str, Any]` - Comparison results

**Example:**
```python
comparison = tracker.compare_snapshots(
    snapshot_id_1="before-refactor",
    snapshot_id_2="after-refactor"
)

print(f"Knowledge improvement: {comparison['delta']['know']}")
print(f"Confidence gain: {comparison['delta']['clarity']}")
```

---

## Bayesian Belief Tracking

### `update_belief(self, cascade_id: str, vector_name: str, evidence: Dict[str, Any], confidence: float, prior_mean: Optional[float] = None, prior_variance: Optional[float] = None) -> Dict[str, float]`

Update Bayesian belief for a specific vector with new evidence.

**Parameters:**
- `cascade_id: str` - CASCADE identifier
- `vector_name: str` - Name of the vector to update
- `evidence: Dict[str, Any]` - New evidence
- `confidence: float` - Confidence in the evidence (0.0-1.0)
- `prior_mean: Optional[float]` - Prior mean, calculated if None
- `prior_variance: Optional[float]` - Prior variance, calculated if None

**Returns:** `Dict[str, float]` - Updated belief parameters (mean, variance, evidence_count)

**Example:**
```python
belief_update = tracker.update_belief(
    cascade_id="cascade-789",
    vector_name="know",
    evidence={"source": "documentation", "content": "auth patterns confirmed"},
    confidence=0.85
)

print(f"Updated mean: {belief_update['mean']}")
print(f"Updated variance: {belief_update['variance']}")
```

### `get_belief_state(self, cascade_id: str, vector_name: str) -> Optional[Dict[str, float]]`

Get current belief state for a specific vector in a CASCADE.

**Parameters:**
- `cascade_id: str` - CASCADE identifier
- `vector_name: str` - Vector name

**Returns:** `Optional[Dict[str, float]]` - Belief state or None

**Example:**
```python
belief = tracker.get_belief_state(cascade_id="cascade-789", vector_name="do")
if belief:
    print(f"Current capability estimate: {belief['mean']} ± {belief['std_dev']}")
```

---

## Divergence & Drift Monitoring

### `log_divergence(self, cascade_id: str, turn_number: int, delegate_perspective: str, trustee_perspective: str, divergence_score: float, divergence_reason: str, synthesis_needed: bool, synthesis_data: Optional[Dict[str, Any]] = None) -> str`

Log delegate-trustee divergence during multi-agent coordination.

**Parameters:**
- `cascade_id: str` - CASCADE identifier
- `turn_number: int` - Current turn number
- `delegate_perspective: str` - Delegate's perspective
- `trustee_perspective: str` - Trustee's perspective
- `divergence_score: float` - Divergence magnitude (0.0-1.0)
- `divergence_reason: str` - Reason for divergence
- `synthesis_needed: bool` - Whether synthesis is needed
- `synthesis_data: Optional[Dict[str, Any]]` - Optional synthesis information

**Returns:** `str` - Divergence record ID

**Example:**
```python
divergence_id = tracker.log_divergence(
    cascade_id="cascade-123",
    turn_number=5,
    delegate_perspective="Use OAuth2 with custom tokens",
    trustee_perspective="Use standard JWT implementation",
    divergence_score=0.6,
    divergence_reason="Different security approach preferences",
    synthesis_needed=True
)
```

### `check_drift(self, session_id: str, analysis_window_hours: float = 24.0) -> Dict[str, Any]`

Check for behavioral drift in the session.

**Parameters:**
- `session_id: str` - Session identifier
- `analysis_window_hours: float` - Window for analysis in hours, default 24.0

**Returns:** `Dict[str, Any]` - Drift analysis results

**Example:**
```python
drift_report = tracker.check_drift(session_id="sess-123", analysis_window_hours=4.0)
if drift_report['detected']:
    print(f"Drift severity: {drift_report['severity']}")
    print(f"Recommendation: {drift_report['recommendation']}")
```

### `reset_drift_monitoring(self, session_id: str)`

Reset drift monitoring for a session.

**Parameters:**
- `session_id: str` - Session identifier

**Example:**
```python
tracker.reset_drift_monitoring(session_id="sess-123")
# Call after intentional approach changes
```

---

## Epistemic Calibration

### `calibrate_assessment(self, actual_outcome: Dict[str, Any], predicted_vectors: Dict[str, float], actual_vectors: Dict[str, float]) -> Dict[str, float]`

Calibrate assessment based on actual outcomes.

**Parameters:**
- `actual_outcome: Dict[str, Any]` - Actual outcome data
- `predicted_vectors: Dict[str, float]` - Predicted vectors
- `actual_vectors: Dict[str, float]` - Actual vectors after completion

**Returns:** `Dict[str, float]` - Calibration adjustments

**Example:**
```python
calibration = tracker.calibrate_assessment(
    actual_outcome={"success": True, "time": 120, "quality": 0.85},
    predicted_vectors=preflight_vectors,
    actual_vectors=postflight_vectors
)

print(f"Calibration adjustments: {calibration}")
```

### `get_calibration_report(self, ai_id: str, time_window_days: int = 30) -> Dict[str, Any]`

Get calibration report for an AI over a time period.

**Parameters:**
- `ai_id: str` - AI identifier
- `time_window_days: int` - Time window in days, default 30

**Returns:** `Dict[str, Any]` - Calibration report

**Example:**
```python
calibration = tracker.get_calibration_report(ai_id="claude-sonnet-4", time_window_days=7)
print(f"Accuracy: {calibration['accuracy_score']}")
print(f"Overconfidence: {calibration['overconfidence_score']}")
```

---

## Source Attribution

### `add_epistemic_source(self, project_id: str, source_type: str, title: str, session_id: Optional[str] = None, source_url: Optional[str] = None, description: Optional[str] = None, confidence: float = 0.5, epistemic_layer: Optional[str] = None, supports_vectors: Optional[Dict[str, float]] = None, related_findings: Optional[List[str]] = None, discovered_by_ai: Optional[str] = None, source_metadata: Optional[Dict] = None) -> str`

Add an epistemic source to track knowledge provenance.

**Parameters:**
- `project_id: str` - Project identifier
- `source_type: str` - Type of source
- `title: str` - Source title
- `session_id: Optional[str]` - Optional session that discovered source
- `source_url: Optional[str]` - Optional URL/path to source
- `description: Optional[str]` - Optional description
- `confidence: float` - Confidence in source (0.0-1.0), default 0.5
- `epistemic_layer: Optional[str]` - Optional epistemic layer
- `supports_vectors: Optional[Dict[str, float]]` - Vectors this source supports
- `related_findings: Optional[List[str]]` - Related finding IDs
- `discovered_by_ai: Optional[str]` - Discovering AI identifier
- `source_metadata: Optional[Dict]` - Additional metadata

**Returns:** `str` - Source ID

**Example:**
```python
source_id = tracker.add_epistemic_source(
    project_id="proj-123",
    source_type="documentation",
    title="OAuth 2.0 Security Best Current Practice",
    source_url="https://tools.ietf.org/html/draft-ietf-oauth-security-topics-16",
    confidence=0.9,
    supports_vectors={"know": 0.8, "context": 0.9}
)
```

### `get_epistemic_sources(self, project_id: str, min_confidence: float = 0.0, source_types: Optional[List[str]] = None, limit: Optional[int] = None) -> List[Dict]`

Get epistemic sources for a project with filters.

**Parameters:**
- `project_id: str` - Project identifier
- `min_confidence: float` - Minimum confidence threshold, default 0.0
- `source_types: Optional[List[str]]` - Optional source type filters
- `limit: Optional[int]` - Optional limit on results

**Returns:** `List[Dict]` - List of source dictionaries

**Example:**
```python
reliable_sources = tracker.get_epistemic_sources(
    project_id="proj-123",
    min_confidence=0.8,
    source_types=["spec", "paper"]
)
```

---

## Utility Methods

### `validate_epistemic_consistency(self, vectors: Dict[str, float], threshold: float = 0.15) -> Dict[str, Any]`

Validate internal consistency of epistemic vectors.

**Parameters:**
- `vectors: Dict[str, float]` - Epistemic vectors to validate
- `threshold: float` - Maximum allowable inconsistency, default 0.15

**Returns:** `Dict[str, Any]` - Validation results

**Example:**
```python
validation = tracker.validate_epistemic_consistency(vectors=assessment_vectors)
if not validation['consistent']:
    print(f"Inconsistencies: {validation['inconsistencies']}")
```

### `normalize_vectors(self, vectors: Dict[str, float]) -> Dict[str, float]`

Normalize epistemic vectors to ensure valid ranges.

**Parameters:**
- `vectors: Dict[str, float]` - Vectors to normalize

**Returns:** `Dict[str, float]` - Normalized vectors

**Example:**
```python
normalized = tracker.normalize_vectors(vectors=raw_vectors)
# Ensures all values are between 0.0 and 1.0
```

### `calculate_epistemic_health(self, vectors: Dict[str, float]) -> Dict[str, float]`

Calculate composite epistemic health metrics.

**Parameters:**
- `vectors: Dict[str, float]` - Current epistemic vectors

**Returns:** `Dict[str, float]` - Health metrics

**Example:**
```python
health = tracker.calculate_epistemic_health(vectors=current_vectors)
print(f"Overall health: {health['overall_health']}")
print(f"Certainty index: {health['certainty_index']}")
print(f"Readiness score: {health['readiness_score']}")
```

---

## Best Practices

1. **Capture genuine self-assessments** - Use actual AI self-reflection rather than heuristic proxies.

2. **Maintain temporal consistency** - Track vectors over time to identify patterns and learning.

3. **Log sufficient metadata** - Include reasoning and context for assessments.

4. **Monitor for drift** - Regularly check for behavioral inconsistencies.

5. **Attribute sources properly** - Track where knowledge comes from for verification.

6. **Update beliefs incrementally** - Use Bayesian updates to refine estimates over time.

7. **Validate consistency** - Check for internal contradictions in self-assessment.

8. **Calibrate regularly** - Compare predictions with actual outcomes to improve accuracy.

---

## Error Handling

Methods typically raise:
- `ValueError` for invalid vector values or parameters
- `sqlite3.Error` for database issues
- `KeyError` when referenced entities don't exist
- `RuntimeError` for state-related issues

---

**Module Location:** `empirica/core/epistemic/tracking.py`
**API Stability:** Stable
**Last Updated:** 2025-12-27