# SentinelOrchestrator Design

**Date**: 2025-11-28
**Session**: 31c902d0-684f-4681-862a-03b5595e0dcc
**Phase**: Phase 2 - Architecture Design

---

## Purpose

**SentinelOrchestrator** coordinates multiple PersonaHarness instances to perform multi-persona epistemic assessment with COMPOSE and ARBITRATE operations.

**Use case**: Run the same task through multiple domain-qualified personas (e.g., security + UX + performance) and merge their insights to get a comprehensive multi-perspective assessment.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   SentinelOrchestrator                      │
│                                                             │
│  orchestrate_task(task, personas, strategy)                 │
│     │                                                        │
│     ├─> Create PersonaHarness instances (security, ux, ...)│
│     ├─> Execute tasks (parallel or sequential)             │
│     ├─> Collect EpistemicAssessmentSchema from each        │
│     ├─> COMPOSE: Merge assessments into unified view       │
│     ├─> ARBITRATE: Resolve conflicts/disagreements         │
│     └─> Return OrchestrationResult                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ PersonaHarness│   │ PersonaHarness│   │ PersonaHarness│
│  (security)   │   │     (ux)      │   │ (performance)│
│               │   │               │   │               │
│ Returns:      │   │ Returns:      │   │ Returns:      │
│ EpistemicAss. │   │ EpistemicAss. │   │ EpistemicAss. │
└──────────────┘   └──────────────┘   └──────────────┘
```

---

## Core Components

### 1. SentinelOrchestrator Class

```python
class SentinelOrchestrator:
    """
    Multi-persona coordination for epistemic assessment

    Coordinates PersonaHarness instances to get multi-perspective
    assessment of a task, then composes and arbitrates results.
    """

    def __init__(
        self,
        sentinel_id: str,
        orchestration_strategy: OrchestrationStrategy = "parallel_consensus",
        composition_strategy: CompositionStrategy = "weighted_average",
        arbitration_strategy: ArbitrationStrategy = "confidence_weighted",
        personas_dir: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        Initialize orchestrator

        Args:
            sentinel_id: Identifier for this orchestrator instance
            orchestration_strategy: How to execute personas (parallel, sequential, adaptive)
            composition_strategy: How to merge assessments (average, weighted, bayesian)
            arbitration_strategy: How to resolve conflicts (majority, weighted, escalate)
            personas_dir: Custom persona directory
            session_id: Empirica session ID for tracking
        """

    async def orchestrate_task(
        self,
        task: str,
        personas: List[str],
        context: Optional[Dict[str, Any]] = None,
        execution_mode: str = "parallel"
    ) -> OrchestrationResult:
        """
        Execute task across multiple personas

        Workflow:
        1. Validate personas exist
        2. Create PersonaHarness for each
        3. Execute task (parallel or sequential)
        4. Collect EpistemicAssessmentSchema from each
        5. COMPOSE: Merge assessments
        6. ARBITRATE: Resolve conflicts
        7. Return unified result

        Args:
            task: Task description
            personas: List of persona IDs (e.g., ["security", "ux"])
            context: Optional context (session_id, git_branch, etc.)
            execution_mode: "parallel" or "sequential"

        Returns:
            OrchestrationResult with composed assessment and metadata
        """

    def compose_assessments(
        self,
        persona_assessments: Dict[str, EpistemicAssessmentSchema],
        persona_profiles: Dict[str, PersonaProfile]
    ) -> EpistemicAssessmentSchema:
        """
        COMPOSE operation: Merge multi-persona assessments

        Takes assessments from N personas and produces unified assessment.

        Composition strategies:
        - average: Simple average of scores across personas
        - weighted_average: Weight by persona confidence or domain relevance
        - weighted_by_domain: Weight by focus domain match to task
        - consensus_threshold: Require agreement above threshold

        Args:
            persona_assessments: {persona_id: EpistemicAssessmentSchema}
            persona_profiles: {persona_id: PersonaProfile} for weighting

        Returns:
            Unified EpistemicAssessmentSchema
        """

    def arbitrate_conflicts(
        self,
        persona_actions: Dict[str, str],
        persona_confidences: Dict[str, float],
        persona_assessments: Dict[str, EpistemicAssessmentSchema]
    ) -> ArbitrationResult:
        """
        ARBITRATE operation: Resolve conflicting recommendations

        When personas disagree on action (e.g., security says INVESTIGATE,
        UX says PROCEED), resolve the conflict.

        Arbitration strategies:
        - majority_vote: Most common action wins
        - confidence_weighted: Weight votes by persona confidence
        - pessimistic: Choose most cautious action (INVESTIGATE > PROCEED)
        - escalate_on_conflict: If any disagreement, escalate to human
        - domain_weighted: Weight by domain relevance to task

        Args:
            persona_actions: {persona_id: "proceed"|"investigate"|"escalate"}
            persona_confidences: {persona_id: confidence_score}
            persona_assessments: Full assessments for detailed arbitration

        Returns:
            ArbitrationResult with final action and reasoning
        """

    def _calculate_domain_relevance(
        self,
        persona: PersonaProfile,
        task: str,
        context: Dict[str, Any]
    ) -> float:
        """
        Calculate how relevant a persona's focus domains are to this task

        Used for domain-weighted composition and arbitration.

        Returns:
            Relevance score 0.0-1.0
        """
```

---

## Data Structures

### OrchestrationResult

```python
@dataclass
class OrchestrationResult:
    """Result of multi-persona orchestration"""

    # Composed assessment
    composed_assessment: EpistemicAssessmentSchema

    # Individual persona assessments
    persona_assessments: Dict[str, EpistemicAssessmentSchema]

    # Arbitration result
    final_action: str  # "proceed", "investigate", "escalate"
    arbitration_reasoning: str

    # Metadata
    personas_used: List[str]
    orchestration_strategy: str
    composition_strategy: str
    arbitration_strategy: str

    # Agreement metrics
    agreement_score: float  # 0.0-1.0, how much personas agreed
    conflicts_detected: List[str]  # List of conflicting assessments

    # Timing
    execution_time_seconds: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
```

### ArbitrationResult

```python
@dataclass
class ArbitrationResult:
    """Result of conflict arbitration"""

    final_action: str  # "proceed", "investigate", "escalate"
    reasoning: str
    confidence: float  # Confidence in arbitration decision

    # Individual persona positions
    persona_votes: Dict[str, str]  # {persona_id: action}
    persona_weights: Dict[str, float]  # {persona_id: weight_used}

    # Conflict details
    conflicts_found: List[str]
    consensus_level: float  # 0.0 (total disagreement) to 1.0 (full consensus)
```

---

## Orchestration Strategies

### 1. parallel_consensus (Default)
**When**: Most tasks, when personas can run independently
**How**:
- Execute all personas in parallel (asyncio.gather)
- Merge results with weighted average
- Require majority agreement for action

### 2. sequential_refinement
**When**: Later personas need to see earlier results
**How**:
- Execute personas in sequence
- Each persona sees previous persona's assessment
- Later personas can refine earlier insights

### 3. adaptive
**When**: Unknown task complexity
**How**:
- Start with broad personas (architecture, code_review)
- If high uncertainty, spawn specialist personas
- Dynamically adjust based on initial assessments

### 4. hierarchical
**When**: Coordinating many personas
**How**:
- Group personas by category (security/UX/performance)
- Run groups in parallel
- Have meta-Sentinel arbitrate between groups

---

## Composition Strategies

### 1. average (Baseline)

```python
def average_composition(assessments: Dict[str, EpistemicAssessmentSchema]) -> EpistemicAssessmentSchema:
    """
    Simple average of all persona scores

    For each vector:
      composed_score = mean([p1_score, p2_score, ...])
      composed_rationale = concatenate all rationales
    """
```

**Pros**: Simple, unbiased, transparent
**Cons**: Doesn't account for persona expertise, confidence, or domain relevance

### 2. weighted_average (Recommended)

```python
def weighted_composition(
    assessments: Dict[str, EpistemicAssessmentSchema],
    profiles: Dict[str, PersonaProfile],
    weighting_method: str = "by_confidence"
) -> EpistemicAssessmentSchema:
    """
    Weighted average based on persona characteristics

    Weighting methods:
    - by_confidence: Weight by persona's self-reported confidence
    - by_domain: Weight by domain relevance (focus_domains match)
    - by_priors: Weight by persona's epistemic priors
    - by_tier: Different weights for foundation/comprehension/execution
    """
```

**Pros**: Accounts for expertise, more accurate
**Cons**: Requires good weighting strategy

### 3. consensus_threshold

```python
def consensus_composition(
    assessments: Dict[str, EpistemicAssessmentSchema],
    threshold: float = 0.75
) -> EpistemicAssessmentSchema:
    """
    Only include assessments with high agreement

    For each vector:
      if std_dev(scores) < threshold:
        composed_score = mean(scores)
      else:
        flag for arbitration
    """
```

**Pros**: Surfaces disagreements explicitly
**Cons**: May deadlock on complex tasks

### 4. bayesian_fusion (Advanced)

```python
def bayesian_composition(
    assessments: Dict[str, EpistemicAssessmentSchema],
    profiles: Dict[str, PersonaProfile]
) -> EpistemicAssessmentSchema:
    """
    Bayesian combination of persona beliefs

    Treat each persona's assessment as Bayesian evidence.
    Update prior beliefs based on persona confidence and track record.

    For each vector:
      P(state | all_personas) ∝ ∏ P(persona_i | state) * P(state)
    """
```

**Pros**: Theoretically optimal, accounts for correlations
**Cons**: Complex, requires calibration

---

## Arbitration Strategies

### 1. majority_vote

```python
def majority_vote_arbitration(
    persona_actions: Dict[str, str]
) -> ArbitrationResult:
    """
    Most common action wins

    Count votes:
      proceed: 2
      investigate: 3
      escalate: 1
    → Result: investigate
    """
```

**Pros**: Simple, democratic
**Cons**: Ignores expertise, confidence

### 2. confidence_weighted (Recommended)

```python
def confidence_weighted_arbitration(
    persona_actions: Dict[str, str],
    persona_confidences: Dict[str, float]
) -> ArbitrationResult:
    """
    Weight votes by persona confidence

    For each action:
      weight = sum(confidences of personas voting for action)
    Choose action with highest weight
    """
```

**Pros**: Accounts for confidence, respects uncertainty
**Cons**: Requires well-calibrated confidence

### 3. pessimistic (Security-focused)

```python
def pessimistic_arbitration(
    persona_actions: Dict[str, str]
) -> ArbitrationResult:
    """
    Choose most cautious action

    Ranking (most to least cautious):
      1. escalate
      2. investigate
      3. proceed

    If ANY persona says escalate → escalate
    Else if ANY persona says investigate → investigate
    Else → proceed
    """
```

**Pros**: Safe for security-critical tasks
**Cons**: May over-investigate

### 4. domain_weighted

```python
def domain_weighted_arbitration(
    persona_actions: Dict[str, str],
    persona_profiles: Dict[str, PersonaProfile],
    task: str,
    context: Dict[str, Any]
) -> ArbitrationResult:
    """
    Weight by domain relevance

    1. Calculate domain relevance for each persona
    2. Weight votes by relevance
    3. Choose highest-weighted action

    Example:
      Task: "Implement caching"
      - performance persona: relevance=0.9, vote=proceed
      - security persona: relevance=0.6, vote=investigate
      - ux persona: relevance=0.3, vote=proceed
    → Result: proceed (0.9*1 + 0.3*1 = 1.2 > 0.6*1)
    """
```

**Pros**: Task-specific, respects expertise
**Cons**: Requires domain matching logic

### 5. escalate_on_conflict

```python
def escalate_on_conflict_arbitration(
    persona_actions: Dict[str, str]
) -> ArbitrationResult:
    """
    If any disagreement, escalate to human

    if len(set(persona_actions.values())) > 1:
        return ArbitrationResult(action="escalate", ...)
    else:
        return ArbitrationResult(action=unanimous_action, ...)
    """
```

**Pros**: Safe, human stays in loop
**Cons**: May escalate too frequently

---

## Implementation Plan

### Phase 3.1: Core Orchestration (2 hours)

**Files to create**:
```
empirica/core/persona/sentinel/
├── __init__.py
├── sentinel_orchestrator.py      # Main class
├── orchestration_result.py       # Data structures
└── orchestration_strategies.py   # Execution strategies
```

**Implementation**:
1. `SentinelOrchestrator.__init__()` - Initialize with strategies
2. `orchestrate_task()` - Main workflow
3. `_create_persona_harnesses()` - Instantiate PersonaHarness
4. `_execute_parallel()` - Parallel execution with asyncio
5. `_execute_sequential()` - Sequential execution
6. `_collect_results()` - Gather EpistemicAssessmentSchema from all

### Phase 3.2: Composition Strategies (1.5 hours)

**File**: `empirica/core/persona/sentinel/composition_strategies.py`

**Functions to implement**:
1. `average_composition()` - Baseline
2. `weighted_composition()` - By confidence or domain
3. `consensus_composition()` - Threshold-based
4. (Optional) `bayesian_composition()` - Advanced

### Phase 3.3: Arbitration Strategies (1.5 hours)

**File**: `empirica/core/persona/sentinel/arbitration_strategies.py`

**Functions to implement**:
1. `majority_vote_arbitration()` - Democratic
2. `confidence_weighted_arbitration()` - Recommended
3. `pessimistic_arbitration()` - Security-focused
4. `domain_weighted_arbitration()` - Task-specific
5. (Optional) `escalate_on_conflict_arbitration()` - Safe fallback

### Phase 3.4: Unit Tests (1 hour)

**File**: `tests/unit/persona/test_sentinel_orchestrator.py`

**Test cases**:
1. Test orchestration with 2 personas (security + UX)
2. Test COMPOSE with agreeing personas
3. Test COMPOSE with disagreeing personas
4. Test ARBITRATE majority vote
5. Test ARBITRATE confidence weighted
6. Test parallel execution
7. Test sequential execution
8. Mock PersonaHarness to avoid LLM calls

---

## Usage Examples

### Example 1: Security + UX Review

```python
orchestrator = SentinelOrchestrator(
    sentinel_id="multi-persona-review",
    orchestration_strategy="parallel_consensus",
    composition_strategy="weighted_average",
    arbitration_strategy="confidence_weighted"
)

result = await orchestrator.orchestrate_task(
    task="Review authentication implementation for security and usability",
    personas=["security", "ux"],
    context={"git_branch": "feature/auth", "session_id": "abc123"}
)

print(f"Final action: {result.final_action}")
print(f"Agreement score: {result.agreement_score}")
print(f"Composed assessment:")
print(f"  Foundation confidence: {result.composed_assessment.calculate_tier_confidence('foundation')}")
print(f"  Uncertainty: {result.composed_assessment.uncertainty.score}")
```

### Example 2: Full-Stack Review (5 Personas)

```python
result = await orchestrator.orchestrate_task(
    task="Review payment processing feature",
    personas=["security", "ux", "performance", "architecture", "code_review"],
    execution_mode="parallel"
)

# Check for conflicts
if result.conflicts_detected:
    print(f"Conflicts: {result.conflicts_detected}")
    print(f"Arbitration: {result.arbitration_reasoning}")
```

### Example 3: Adaptive Orchestration

```python
orchestrator = SentinelOrchestrator(
    orchestration_strategy="adaptive"
)

# Start with generalists
result = await orchestrator.orchestrate_task(
    task="Optimize database queries",
    personas=["code_review", "architecture"]
)

# If high uncertainty, spawn specialists
if result.composed_assessment.uncertainty.score > 0.7:
    result = await orchestrator.orchestrate_task(
        task="Optimize database queries",
        personas=["performance", "architecture"],
        context={"prior_assessment": result}
    )
```

---

## Integration with Existing Systems

### With PersonaHarness
- SentinelOrchestrator **creates** PersonaHarness instances
- Uses existing `execute_task()` method
- No changes to PersonaHarness needed

### With EpistemicAssessmentSchema
- Composition operates on EpistemicAssessmentSchema
- Uses existing `VectorAssessment` structure
- Can use `calculate_tier_confidence()` for weighting

### With Empirica SESSION
- Orchestration results stored in session DB
- Links to goal tracking
- Checkpoint creation after COMPOSE/ARBITRATE

### With CLI (Phase 4)
```bash
empirica orchestrate "task description" \
  --personas security,ux,performance \
  --strategy parallel_consensus \
  --session-id abc123
```

---

## Design Decisions

### Q1: Parallel vs Sequential Execution?
**Decision**: Support both, default to parallel
**Rationale**: Parallel is faster for independent assessments, sequential needed for refinement

### Q2: How to weight personas in composition?
**Decision**: Default to confidence-weighted, support domain-weighted
**Rationale**: Confidence is always available, domain requires task analysis

### Q3: How to handle persona disagreements?
**Decision**: Use arbitration strategies, make pluggable
**Rationale**: Different tasks need different conflict resolution (security vs UX)

### Q4: Should orchestrator run CASCADE or just assessment?
**Decision**: Run full PersonaHarness.execute_task() (includes CASCADE if needed)
**Rationale**: PersonaHarness already handles CASCADE flow, orchestrator just coordinates

### Q5: How to store orchestration results?
**Decision**: Store in Empirica session DB, create git checkpoint
**Rationale**: Consistent with existing Empirica storage, enables history tracking

---

## Success Criteria

After Phase 3 implementation:

- ✅ Can orchestrate 2-5 personas in parallel
- ✅ Can COMPOSE assessments with 3 strategies (average, weighted, consensus)
- ✅ Can ARBITRATE conflicts with 3 strategies (majority, confidence, pessimistic)
- ✅ Composition preserves all 13 epistemic vectors
- ✅ Arbitration reasoning is clear and traceable
- ✅ Unit tests cover main scenarios (agreement, disagreement, edge cases)
- ✅ Performance: <5s for 3 personas (with mock LLM)
- ✅ Integration: Works with existing PersonaHarness without modifications

---

## Future Enhancements (Post-MVP)

### 1. Dynamic Persona Selection
Orchestrator analyzes task and automatically selects relevant personas

### 2. Learning from History
Track which personas were most accurate for which tasks, adjust weights

### 3. Streaming Results
Return partial results as personas complete, don't wait for all

### 4. Cost Optimization
Skip low-relevance personas to save LLM costs

### 5. Visualization
Show multi-persona assessment as radar chart or heatmap

---

**Status**: Design complete, ready for Phase 3 implementation
**Risk**: LOW - building on stable foundation
**Estimated implementation time**: 5-6 hours
