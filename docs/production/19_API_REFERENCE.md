# API Reference

**Empirica v2.0 - Complete Method Signatures**

---

## Core Classes

### ExtendedMetacognitiveBootstrap

```python
class ExtendedMetacognitiveBootstrap:
    def __init__(
        self,
        ai_id: str = "empirica_ai",
        level: str = "2"
    ) -> None
```

**Parameters:**
- `ai_id` (str): AI identifier for logging
- `level` (str): Bootstrap level "0"-"4"

**Methods:**

#### bootstrap()
```python
def bootstrap(self) -> Dict[str, Any]
```
Load components based on initialization level.

**Returns:** dict[str, component] - Loaded components

---

### CanonicalEpistemicCascade

```python
class CanonicalEpistemicCascade:
    def __init__(
        self,
        action_confidence_threshold: float = 0.70,
        max_investigation_rounds: int = 3,
        agent_id: str = "cascade",
        tmux_extension = None,
        enable_bayesian: bool = True,
        enable_drift_monitor: bool = True,
        investigation_plugins: Optional[Dict[str, InvestigationPlugin]] = None,
        enable_action_hooks: bool = True,
        auto_start_dashboard: bool = False,
        enable_perspective_caching: bool = True,
        cache_ttl: int = 300,
        enable_session_db: bool = True
    ) -> None
```

**Methods:**

#### run_epistemic_cascade()
```python
async def run_epistemic_cascade(
    self,
    task: str,
    context: Dict[str, Any]
) -> Dict[str, Any]
```

**Returns:**
```python
{
    'action': str,  # Action enum value
    'confidence': float,
    'investigation_rounds': int,
    'phases': {
        'think': Dict[str, Any],
        'uncertainty': Dict[str, Any],
        'investigate': Dict[str, Any],
        'check': Dict[str, Any],
        'act': Dict[str, Any]
    }
}
```

---

### CanonicalEpistemicAssessor

```python
class CanonicalEpistemicAssessor:
    def __init__(self) -> None
    
    async def assess(
        self,
        task: str,
        context: Dict[str, Any]
    ) -> EpistemicAssessment
```

---

## Data Classes

### EpistemicAssessment

```python
@dataclass
class EpistemicAssessment:
    assessment_id: str
    
    # GATE
    engagement: VectorState
    engagement_gate_passed: bool
    
    # FOUNDATION (35%)
    know: VectorState
    do: VectorState
    context: VectorState
    foundation_confidence: float
    
    # COMPREHENSION (25%)
    clarity: VectorState
    coherence: VectorState
    signal: VectorState
    density: VectorState
    comprehension_confidence: float
    
    # EXECUTION (25%)
    state: VectorState
    change: VectorState
    completion: VectorState
    impact: VectorState
    execution_confidence: float
    
    # OVERALL
    overall_confidence: float
    recommended_action: Action
```

### VectorState

```python
@dataclass
class VectorState:
    score: float  # 0.0-1.0
    rationale: str
    evidence: Optional[str] = None

    # Self-assessment fields (NO HEURISTICS)
    warrants_investigation: bool = False           # AI decides if this vector needs investigation
    investigation_priority: Optional[str] = None    # 'low', 'medium', 'high', 'critical'
    investigation_reason: Optional[str] = None      # Why investigation is warranted
```

**Self-Assessment Fields:**
- `warrants_investigation`: AI flags whether this vector needs investigation (NOT system thresholds)
- `investigation_priority`: AI's priority assessment ('low', 'medium', 'high', 'critical')
- `investigation_reason`: AI's reasoning for why investigation is warranted

### Action (Enum)

```python
class Action(Enum):
    PROCEED = "proceed"
    INVESTIGATE = "investigate"
    CLARIFY = "clarify"
    RESET = "reset"
    STOP = "stop"
```

---

## Database Classes

### SessionDatabase

```python
class SessionDatabase:
    def __init__(
        self,
        db_path: Optional[str] = None
    ) -> None
```

**Methods:**

#### create_session()
```python
def create_session(
    self,
    ai_id: str,
    bootstrap_level: int,
    components_loaded: int,
    user_id: Optional[str] = None
) -> str
```
Returns: session_id

#### end_session()
```python
def end_session(
    self,
    session_id: str,
    avg_confidence: Optional[float] = None,
    drift_detected: bool = False,
    notes: Optional[str] = None
) -> None
```

#### create_cascade()
```python
def create_cascade(
    self,
    session_id: str,
    task: str,
    context: Dict[str, Any]
) -> str
```
Returns: cascade_id

#### complete_cascade()
```python
def complete_cascade(
    self,
    cascade_id: str,
    final_action: str,
    final_confidence: float,
    investigation_rounds: int,
    duration_ms: int,
    engagement_gate_passed: bool,
    bayesian_active: bool = False,
    drift_monitored: bool = False
) -> None
```

#### log_epistemic_assessment()
```python
def log_epistemic_assessment(
    self,
    cascade_id: str,
    assessment: EpistemicAssessment,
    phase: str
) -> None
```

#### get_session()
```python
def get_session(
    self,
    session_id: str
) -> Optional[Dict[str, Any]]
```

#### get_session_cascades()
```python
def get_session_cascades(
    self,
    session_id: str
) -> List[Dict[str, Any]]
```

#### get_cascade_assessments()
```python
def get_cascade_assessments(
    self,
    cascade_id: str
) -> List[Dict[str, Any]]
```

#### close()
```python
def close(self) -> None
```

---

### SessionJSONHandler

```python
class SessionJSONHandler:
    def __init__(
        self,
        export_dir: Optional[str] = None
    ) -> None
```

**Methods:**

#### export_session()
```python
def export_session(
    self,
    db: SessionDatabase,
    session_id: str
) -> Path
```
Returns: Path to exported JSON file

#### export_cascade_graph()
```python
def export_cascade_graph(
    self,
    db: SessionDatabase,
    cascade_id: str
) -> Path
```
Returns: Path to graph JSON file

#### load_session_context()
```python
def load_session_context(
    self,
    session_id: str
) -> Optional[Dict[str, Any]]
```

#### create_compact_summary()
```python
def create_compact_summary(
    self,
    db: SessionDatabase,
    session_id: str
) -> Dict[str, Any]
```

---

## Investigation Classes

### InvestigationPlugin

```python
@dataclass
class InvestigationPlugin:
    name: str
    description: str
    execute_fn: Callable
    improves_vectors: List[str]
    confidence_gain: float
    required_context: List[str] = field(default_factory=list)
    domain_specific: Optional[str] = None
```

### PluginRegistry

```python
class PluginRegistry:
    def __init__(self) -> None
    
    def register(
        self,
        plugin: InvestigationPlugin
    ) -> None
    
    def unregister(
        self,
        plugin_name: str
    ) -> None
    
    def get_plugins_by_vector(
        self,
        vector: str
    ) -> List[InvestigationPlugin]
    
    def get_plugins_by_domain(
        self,
        domain: str
    ) -> List[InvestigationPlugin]
    
    def validate_plugin(
        self,
        plugin: InvestigationPlugin
    ) -> bool
    
    def get_all_plugins(self) -> Dict[str, InvestigationPlugin]
```

### recommend_investigation_tools()

```python
def recommend_investigation_tools(
    assessment: EpistemicAssessment,
    context: Dict[str, Any],
    domain: str
) -> List[ToolRecommendation]
```

---

## Calibration Classes

### BayesianBeliefTracker

```python
class BayesianBeliefTracker:
    def __init__(
        self,
        persistence_dir: Optional[str] = None
    ) -> None
```

**Methods:**

#### initialize_beliefs()
```python
def initialize_beliefs(
    self,
    context_key: str,
    initial_assessment: Dict[str, float],
    initial_variance: float = 0.3
) -> None
```

#### update_belief()
```python
def update_belief(
    self,
    belief_key: str,
    evidence: Evidence
) -> BeliefState
```

#### detect_discrepancies()
```python
def detect_discrepancies(
    self,
    context_key: str,
    intuitive_assessment: Dict[str, float],
    threshold_std_devs: float = 2.0
) -> List[Dict[str, Any]]
```

#### activate()
```python
def activate(
    self,
    reason: str
) -> None
```

#### deactivate()
```python
def deactivate(self) -> None
```

### Evidence

```python
@dataclass
class Evidence:
    outcome: bool
    strength: float
    timestamp: float
    source: str
    vector_addressed: str
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### BeliefState

```python
@dataclass
class BeliefState:
    mean: float
    variance: float
    evidence_count: int
    last_updated: float
    prior_mean: float
    prior_variance: float
    
    def confidence_interval(
        self,
        std_devs: float = 2.0
    ) -> Tuple[float, float]
    
    def is_confident(
        self,
        threshold: float = 0.15
    ) -> bool
```

---

## Drift Monitoring

### DriftMonitor

```python
class DriftMonitor:
    def __init__(self) -> None
    
    def analyze_drift(
        self,
        synthesis_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]
```

**Returns:**
```python
{
    'sycophancy_drift': {
        'detected': bool,
        'evidence': str,
        'recommendation': str
    },
    'tension_avoidance_drift': {
        'detected': bool,
        'evidence': str,
        'recommendation': str
    }
}
```

---

## Logging

### ReflexLogger

```python
class ReflexLogger:
    def __init__(
        self,
        log_dir: Optional[str] = None
    ) -> None
```

**Methods:**

#### log_frame()
```python
async def log_frame(
    self,
    frame: ReflexFrame,
    task_id: str,
    phase: str
) -> None
```

#### get_frames_by_phase()
```python
async def get_frames_by_phase(
    self,
    phase: str,
    date: Optional[str] = None,
    task_id: Optional[str] = None
) -> List[ReflexFrame]
```

#### get_frames_by_task()
```python
async def get_frames_by_task(
    self,
    task_id: str
) -> List[ReflexFrame]
```

---

## Type Hints

```python
from typing import Dict, List, Any, Optional, Callable, Tuple
from empirica.core.canonical import EpistemicAssessment, VectorState, Action
from empirica.data import SessionDatabase
from empirica.investigation import InvestigationPlugin

# Function signature with types
async def my_function(
    task: str,
    context: Dict[str, Any],
    threshold: float = 0.70
) -> Dict[str, Any]:
    pass
```

---

## Constants

```python
# Bootstrap Levels
BOOTSTRAP_MINIMAL = "0"
BOOTSTRAP_BASIC = "1"
BOOTSTRAP_STANDARD = "2"  # Default/Recommended
BOOTSTRAP_EXTENDED = "3"
BOOTSTRAP_COMPLETE = "4"

# Canonical Weights
FOUNDATION_WEIGHT = 0.35
COMPREHENSION_WEIGHT = 0.25
EXECUTION_WEIGHT = 0.25
ENGAGEMENT_WEIGHT = 0.15

# Thresholds
ENGAGEMENT_GATE_THRESHOLD = 0.60
DEFAULT_CONFIDENCE_THRESHOLD = 0.70
COHERENCE_CRITICAL_THRESHOLD = 0.50
DENSITY_CRITICAL_THRESHOLD = 0.90
CHANGE_CRITICAL_THRESHOLD = 0.50
```

---

## Next Steps

- **Python API Guide:** [13_PYTHON_API.md](13_PYTHON_API.md)
- **Usage Examples:** [03_BASIC_USAGE.md](03_BASIC_USAGE.md)
- **Troubleshooting:** [21_TROUBLESHOOTING.md](21_TROUBLESHOOTING.md)

---

**Complete method signatures for all public APIs!** 📚
