# Epistemic Prediction System Design

**Status:** Experimental
**Branch:** `feature/epistemic-prediction`
**Version:** 0.1.0-alpha

## Vision

Predictive epistemic learning through noetic pattern matching based on epistemic
artifacts via epistemic vector clustering.

**Core Insight:** Epistemic journeys have structure. Knowledge doesn't accumulate
randomly - it follows recognizable patterns that can be predicted.

## The Problem

Currently, Empirica tracks epistemic state reactively:
- PREFLIGHT: Measure baseline
- CHECK: Validate readiness
- POSTFLIGHT: Measure learning

This captures WHAT happened but doesn't predict WHAT SHOULD happen.

## The Solution

Build a prediction layer that analyzes accumulated epistemic artifacts to:
1. **Predict** where knowledge gaps exist
2. **Suggest** exploration directions
3. **Detect** convergent discovery paths
4. **Warn** about likely dead-ends

## Theoretical Foundation

### Epistemic Gravity

Knowledge has structure. Related concepts cluster together like mass in a
gravitational field:

```
High-density regions: Well-understood domains
Low-density regions: Knowledge gaps
Trajectories: How understanding evolves
Attraction: Related concepts pull toward each other
```

### Vector Trajectories

Epistemic vectors follow recognizable patterns:

```
Breakthrough Pattern:
  t0: know=0.3, uncertainty=0.7  (initial confusion)
  t1: know=0.5, uncertainty=0.8  (investigation)
  t2: know=0.5, uncertainty=0.9  (peak confusion)
  t3: know=0.8, uncertainty=0.3  (breakthrough)

Dead-End Pattern:
  t0: know=0.3, uncertainty=0.7
  t1: know=0.4, uncertainty=0.8
  t2: know=0.4, uncertainty=0.9
  t3: know=0.3, uncertainty=0.9  (regression)
```

### Concept Co-occurrence

Certain concepts reliably appear together:

```
If you understand A and B, you usually need C.
If you discovered X, you'll likely encounter Y.
If you rejected Z, but now found W similar to Z, reconsider Z.
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     EPISTEMIC PREDICTION ENGINE                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  DATA LAYER (Existing)                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │   SQLite    │  │   Qdrant    │  │  Git Notes  │                 │
│  │  (reflexes, │  │  (eidetic,  │  │ (checkpoints│                 │
│  │   findings) │  │  episodic)  │  │   phases)   │                 │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                 │
│         └────────────────┼────────────────┘                         │
│                          │                                          │
│  ANALYSIS LAYER (New)    │                                          │
│  ┌───────────────────────▼───────────────────────┐                 │
│  │              Trajectory Analyzer               │                 │
│  │  - Vector time series                          │                 │
│  │  - Pattern matching (breakthrough, dead-end)   │                 │
│  │  - Phase detection                             │                 │
│  └───────────────────────┬───────────────────────┘                 │
│                          │                                          │
│  ┌───────────────────────▼───────────────────────┐                 │
│  │              Concept Graph Builder             │                 │
│  │  - Co-occurrence matrix                        │                 │
│  │  - Semantic clustering                         │                 │
│  │  - Edge weight = epistemic confidence          │                 │
│  └───────────────────────┬───────────────────────┘                 │
│                          │                                          │
│  ┌───────────────────────▼───────────────────────┐                 │
│  │              Sequence Recognizer               │                 │
│  │  - Unknown → Finding transitions               │                 │
│  │  - Investigation patterns                      │                 │
│  │  - Discovery sequences                         │                 │
│  └───────────────────────┬───────────────────────┘                 │
│                          │                                          │
│  PREDICTION LAYER (New)  │                                          │
│  ┌───────────────────────▼───────────────────────┐                 │
│  │                Gap Detector                    │                 │
│  │  - Missing middle concepts                     │                 │
│  │  - Incomplete clusters                         │                 │
│  │  - Stalled unknowns                            │                 │
│  └───────────────────────┬───────────────────────┘                 │
│                          │                                          │
│  ┌───────────────────────▼───────────────────────┐                 │
│  │              Suggestion Engine                 │                 │
│  │  - Proactive recommendations                   │                 │
│  │  - Confidence-ranked suggestions               │                 │
│  │  - Convergent path detection                   │                 │
│  └───────────────────────────────────────────────┘                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Phases

### Phase 1: Vector Trajectory Tracking

**Goal:** Store and analyze vector time series per session/concept.

**Data Model:**
```python
@dataclass
class VectorSnapshot:
    session_id: str
    timestamp: float
    phase: str  # PREFLIGHT, CHECK, POSTFLIGHT
    vectors: Dict[str, float]
    concept_tags: List[str]  # What domain/topic

@dataclass
class Trajectory:
    snapshots: List[VectorSnapshot]
    pattern: str  # 'breakthrough', 'dead_end', 'stable', 'oscillating'
    confidence: float
```

**Implementation:**
- Hook into CASCADE phases to capture snapshots
- Store in new `vector_trajectories` table
- Implement pattern matching for common trajectories

**Deliverables:**
- `trajectory_tracker.py` - Capture and store vector trajectories
- `trajectory_patterns.py` - Pattern definitions and matching
- CLI: `empirica trajectory-show --session-id <ID>`

### Phase 2: Concept Co-occurrence Graphs

**Goal:** Build graph of concept relationships from findings/unknowns.

**Data Model:**
```python
@dataclass
class ConceptNode:
    concept_id: str
    content: str
    type: str  # 'finding', 'unknown', 'noetic'
    vector_state: Dict[str, float]  # State when captured

@dataclass
class ConceptEdge:
    source: str
    target: str
    weight: float  # Co-occurrence strength
    relationship: str  # 'leads_to', 'similar', 'contradicts'
```

**Implementation:**
- Extract concepts from findings/unknowns/noetic
- Build co-occurrence matrix from session proximity
- Use semantic similarity for edge weights
- Store in Qdrant with graph metadata

**Deliverables:**
- `concept_graph.py` - Graph construction and queries
- `semantic_clustering.py` - Cluster related concepts
- CLI: `empirica concept-graph --project-id <ID> --visualize`

### Phase 3: Sequence Pattern Recognition

**Goal:** Identify patterns in how unknowns lead to findings.

**Data Model:**
```python
@dataclass
class DiscoverySequence:
    sequence_id: str
    steps: List[Dict]  # [{type: 'unknown', content: '...'}, {type: 'finding', ...}]
    vector_trajectory: Trajectory
    success: bool  # Did it lead to resolution?

@dataclass
class SequencePattern:
    pattern_id: str
    template: List[str]  # ['unknown:auth', 'finding:tokens', 'finding:refresh']
    frequency: int
    avg_success_rate: float
```

**Implementation:**
- Track unknown → finding transitions
- Cluster similar sequences
- Identify recurring patterns
- Calculate pattern reliability

**Deliverables:**
- `sequence_tracker.py` - Track investigation sequences
- `sequence_patterns.py` - Pattern identification
- CLI: `empirica sequence-analyze --project-id <ID>`

### Phase 4: Gap Detection & Prediction

**Goal:** Identify missing knowledge and predict needs.

**Algorithms:**
```python
def detect_missing_middle(graph: ConceptGraph) -> List[Gap]:
    """
    Find concepts A and C where:
    - A and C are connected through other graphs
    - No direct A→C edge in current graph
    - High probability B should exist between them
    """

def detect_stalled_unknowns(unknowns: List, findings: List) -> List[Unknown]:
    """
    Find unknowns that:
    - Were logged N sessions ago
    - Have high impact
    - Were never resolved or marked dead-end
    - Similar unknowns in other projects led to findings
    """

def predict_next_unknown(trajectory: Trajectory, patterns: List) -> Prediction:
    """
    Based on current trajectory and historical patterns,
    predict what unknown the AI will likely encounter.
    """
```

**Deliverables:**
- `gap_detector.py` - Missing knowledge detection
- `predictor.py` - Forward prediction
- CLI: `empirica predict-gaps --session-id <ID>`

### Phase 5: Proactive Suggestion Engine

**Goal:** Surface actionable recommendations during CASCADE phases.

**Integration Points:**
```
PREFLIGHT:
  - "Based on patterns, you'll likely need to understand X"
  - "Similar tasks required knowledge of Y before proceeding"

CHECK:
  - "Your trajectory matches pre-breakthrough pattern, persist"
  - "Warning: This matches dead-end pattern, consider pivot"
  - "Gap detected: You understand A and C but not B"

POSTFLIGHT:
  - "Your learning matches pattern P, next likely step: Z"
  - "Convergent discovery: Your rejected_alternative X is now relevant"
```

**Deliverables:**
- `suggestion_engine.py` - Generate contextual suggestions
- `confidence_ranker.py` - Rank suggestions by reliability
- Integration with CASCADE phase hooks
- CLI: `empirica suggest --session-id <ID>`

## Quality Scoring

Predictions need confidence scores:

```python
def calculate_prediction_confidence(
    pattern_frequency: int,
    pattern_success_rate: float,
    semantic_similarity: float,
    vector_trajectory_match: float
) -> float:
    """
    Confidence = weighted combination of:
    - How often this pattern occurs (frequency)
    - How often it leads to success (reliability)
    - How similar current context is (relevance)
    - How well vectors match pattern (trajectory fit)
    """
    return (
        0.2 * min(1.0, pattern_frequency / 10) +
        0.3 * pattern_success_rate +
        0.3 * semantic_similarity +
        0.2 * vector_trajectory_match
    )
```

## Data Requirements

This system needs sufficient historical data to work well:

| Component | Minimum Data | Optimal Data |
|-----------|-------------|--------------|
| Trajectory patterns | 10 sessions | 50+ sessions |
| Concept graph | 50 findings | 200+ findings |
| Sequence patterns | 20 sequences | 100+ sequences |
| Gap detection | 3 projects | 10+ projects |

## Privacy & Safety

- All prediction is local (no external API calls for patterns)
- Predictions are suggestions, not mandates
- User can disable with `EMPIRICA_DISABLE_PREDICTION=true`
- No cross-project data sharing without explicit consent

## Success Metrics

1. **Prediction Accuracy:** % of suggested gaps that user confirms
2. **Pattern Reliability:** % of predicted outcomes that occur
3. **Time Savings:** Reduction in exploration cycles
4. **User Trust:** Adoption rate of suggestions

## Timeline

- Phase 1: 2-3 sessions of focused work
- Phase 2: 2-3 sessions
- Phase 3: 2-3 sessions
- Phase 4: 3-4 sessions
- Phase 5: 2-3 sessions
- Integration & Testing: 2-3 sessions

**Total:** ~15-20 focused sessions over multiple weeks

## Open Questions

1. How do we handle cross-project pattern learning without privacy concerns?
2. What's the minimum viable data for useful predictions?
3. Should predictions be project-specific or global?
4. How do we avoid over-fitting to one user's style?
5. How do we surface predictions without being annoying?

## References

- Empirica noetic_eidetic.py - Concept extraction patterns
- Empirica cascade phases - Integration points
- Qdrant vector store - Semantic search foundation
