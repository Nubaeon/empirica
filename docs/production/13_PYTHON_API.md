# Python API Reference

**Empirica v2.0 - Direct API Usage**

---

## Quick Reference

### Core Imports
```python
# Bootstrap
from empirica.bootstraps.extended_metacognitive_bootstrap import ExtendedMetacognitiveBootstrap
from empirica.bootstraps.optimal_metacognitive_bootstrap import OptimalMetacognitiveBootstrap

# Core assessment & cascade
from empirica.core.canonical import CanonicalEpistemicAssessor, ReflexLogger
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

# Data & session management
from empirica.data.session_database import SessionDatabase
from empirica.data.session_json_handler import SessionJSONHandler
```

---

## Bootstrap API

### ExtendedMetacognitiveBootstrap

Initialize the system with tiered component loading.

```python
from empirica.bootstraps.extended_metacognitive_bootstrap import ExtendedMetacognitiveBootstrap

bootstrap = ExtendedMetacognitiveBootstrap(
    ai_id="your_ai_name",          # Identifier for this AI
    level="2"                      # Init level: "0"-"4"
)
components = bootstrap.bootstrap()
```

**Parameters:**
- `ai_id` (str): AI identifier for logging
- `level` (str): "0" (minimal), "1" (basic), "2" (standard), "3" (extended), "4" (complete)

**Returns:** dict of loaded components

**Levels:**
- `"0"`: 14 components (canonical + core)
- `"1"`: 25 components (+ foundation)
- `"2"`: 30 components (+ calibration) ← **DEFAULT**
- `"3"`: ~35 components (+ advanced)
- `"4"`: ~40 components (complete)

**Example:**
```python
bootstrap = ExtendedMetacognitiveBootstrap(level="2", ai_id="production")
components = bootstrap.bootstrap()

# Access components
cascade = components['canonical_cascade']
assessor = components['canonical_assessor']
bayesian = components.get('bayesian_tracker')  # Optional
```

---

## Cascade API

### CanonicalEpistemicCascade

Main reasoning cascade: THINK → UNCERTAINTY → INVESTIGATE → CHECK → ACT

```python
from empirica.core.metacognitive_cascade import CanonicalEpistemicCascade

cascade = CanonicalEpistemicCascade(
    action_confidence_threshold=0.70,
    max_investigation_rounds=3,
    agent_id="cascade",
    enable_bayesian=True,
    enable_drift_monitor=True,
    enable_action_hooks=True,
    enable_session_db=True
)
```

**Parameters:**
- `action_confidence_threshold` (float): Minimum confidence to proceed (0.0-1.0)
- `max_investigation_rounds` (int): Maximum investigation loops
- `agent_id` (str): Agent identifier
- `enable_bayesian` (bool): Activate Bayesian Guardian
- `enable_drift_monitor` (bool): Activate drift detection
- `enable_action_hooks` (bool): Enable tmux dashboard
- `enable_session_db` (bool): Enable database tracking

### run_epistemic_cascade()

Execute complete cascade.

```python
result = await cascade.run_epistemic_cascade(
    task="Your task description",
    context={
        'cwd': '/path/to/project',
        'available_tools': ['read', 'write', 'edit'],
        'urgency': 'high'
    }
)
```

**Parameters:**
- `task` (str): Task description (clear and specific)
- `context` (dict): Contextual information

**Returns:** dict with:
```python
{
    'action': str,                # 'proceed', 'investigate', 'clarify', 'reset', 'stop'
    'confidence': float,          # Final confidence (0.0-1.0)
    'investigation_rounds': int,  # Number of rounds executed
    'phases': {
        'think': {...},
        'uncertainty': {...},
        'investigate': {...},
        'check': {...},
        'act': {...}
    }
}
```

---

## Assessment API

### CanonicalEpistemicAssessor

LLM-powered epistemic self-assessment.

```python
from empirica.core.canonical import CanonicalEpistemicAssessor

assessor = CanonicalEpistemicAssessor()
assessment = await assessor.assess(
    task="Analyze authentication system",
    context={'domain': 'security'}
)
```

**Returns:** `EpistemicAssessment` with:
- `engagement`: VectorState (GATE)
- `know`, `do`, `context`: VectorState (FOUNDATION)
- `clarity`, `coherence`, `signal`, `density`: VectorState (COMPREHENSION)
- `state`, `change`, `completion`, `impact`: VectorState (EXECUTION)
- `overall_confidence`: float
- `recommended_action`: Action enum

### VectorState

Individual vector measurement with self-assessment capabilities.

```python
vector = assessment.know
print(f"Score: {vector.score}")        # 0.0-1.0
print(f"Rationale: {vector.rationale}") # AI reasoning

# Self-assessment fields (NO HEURISTICS)
if vector.warrants_investigation:
    print(f"Priority: {vector.investigation_priority}")  # 'low', 'medium', 'high', 'critical'
    print(f"Reason: {vector.investigation_reason}")
```

**Attributes:**
- `score` (float): 0.0-1.0 measurement
- `rationale` (str): AI's genuine reasoning
- `evidence` (str, optional): Supporting context
- `warrants_investigation` (bool): AI flags if investigation needed (NOT system thresholds)
- `investigation_priority` (str, optional): 'low', 'medium', 'high', 'critical'
- `investigation_reason` (str, optional): Why investigation is warranted

---

## Database API

### SessionDatabase

SQLite storage for epistemic states and cascades.

```python
from empirica.data.session_database import SessionDatabase

db = SessionDatabase()  # Uses .empirica/sessions/sessions.db
# OR
db = SessionDatabase("/custom/path/sessions.db")
```

#### create_session()
```python
session_id = db.create_session(
    ai_id="my_ai",
    bootstrap_level=2,
    components_loaded=30,
    user_id="user123"  # optional
)
```

#### create_cascade()
```python
cascade_id = db.create_cascade(
    session_id=session_id,
    task="My task",
    context={'test': True}
)
```

#### complete_cascade()
```python
db.complete_cascade(
    cascade_id=cascade_id,
    final_action="proceed",
    final_confidence=0.82,
    investigation_rounds=2,
    duration_ms=5000,
    engagement_gate_passed=True,
    bayesian_active=True,
    drift_monitored=True
)
```

#### log_epistemic_assessment()
```python
db.log_epistemic_assessment(
    cascade_id=cascade_id,
    assessment=assessment,
    phase='uncertainty'  # or 'investigate_round_1', 'check'
)
```

#### Query Methods
```python
# Get session data
session = db.get_session(session_id)

# Get all cascades for session
cascades = db.get_session_cascades(session_id)

# Get assessments for cascade
assessments = db.get_cascade_assessments(cascade_id)

# Close database
db.close()
```

---

### SessionJSONHandler

Export SQLite data to AI-readable JSON.

```python
from empirica.data.session_json_handler import SessionJSONHandler

handler = SessionJSONHandler()  # Uses .empirica/exports/

# Export complete session
filepath = handler.export_session(db, session_id)
# Creates: .empirica/exports/session_{session_id}.json

# Export cascade as graph
graph_path = handler.export_cascade_graph(db, cascade_id)
# Creates: .empirica/exports/cascade_{cascade_id}_graph.json

# Load session context (for continuity)
previous_session = handler.load_session_context(session_id)

# Create compact summary
summary = handler.create_compact_summary(db, session_id)
```

---

## Investigation API

### recommend_investigation_tools()

Get strategic tool recommendations for gaps.

```python
from empirica.investigation import recommend_investigation_tools

recommendations = recommend_investigation_tools(
    assessment=epistemic_assessment,
    context={'domain': 'code_analysis'},
    domain='code_analysis'
)

for rec in recommendations:
    print(f"{rec.tool_name}: {rec.reasoning}")
    print(f"Gap: {rec.gap_addressed}, Gain: {rec.confidence}")
```

**Returns:** List of `ToolRecommendation` with:
- `tool_name` (str): Tool identifier
- `reasoning` (str): Why this tool
- `gap_addressed` (str): Which vector it improves
- `confidence` (float): Expected confidence gain

---

## Plugin API

### InvestigationPlugin

Define custom investigation tools.

```python
from empirica.investigation import InvestigationPlugin

plugin = InvestigationPlugin(
    name='custom_tool',
    description='What it does',
    execute_fn=lambda ctx: my_function(ctx),
    improves_vectors=['know', 'context'],
    confidence_gain=0.25,
    required_context=['key1', 'key2'],
    domain_specific='code_analysis'  # optional
)

# Use in cascade
cascade = CanonicalEpistemicCascade(
    investigation_plugins={'custom_tool': plugin}
)
```

### PluginRegistry

Manage multiple plugins.

```python
from empirica.investigation import PluginRegistry

registry = PluginRegistry()
registry.register(plugin1)
registry.register(plugin2)

# Query
plugins_for_know = registry.get_plugins_by_vector('know')
plugins_for_domain = registry.get_plugins_by_domain('security')

# Validate
is_valid = registry.validate_plugin(plugin)
```

---

## Calibration API

### BayesianBeliefTracker

Evidence-based belief tracking.

```python
from empirica.calibration.adaptive_uncertainty_calibration.bayesian_belief_tracker import (
    BayesianBeliefTracker,
    Evidence
)

tracker = BayesianBeliefTracker()

# Initialize beliefs
tracker.initialize_beliefs(
    context_key='task_123',
    initial_assessment={'know': 0.7, 'do': 0.6},
    initial_variance=0.3
)

# Update with evidence
evidence = Evidence(
    outcome=True,
    strength=0.8,
    timestamp=time.time(),
    source='documentation_search',
    vector_addressed='know'
)
belief = tracker.update_belief('task_123:know', evidence)

# Detect discrepancies
discrepancies = tracker.detect_discrepancies(
    context_key='task_123',
    intuitive_assessment={'know': 0.7, 'do': 0.6}
)
```

---

## Logging API

### ReflexLogger

Temporal separation via JSON logging.

```python
from empirica.core.canonical import ReflexLogger

logger = ReflexLogger()

# Log reflex frame
await logger.log_frame(
    frame=reflex_frame,
    task_id='task_123',
    phase='uncertainty'
)

# Query frames
frames = await logger.get_frames_by_phase('uncertainty', date='2025-10-28')
frames = await logger.get_frames_by_task('task_123')
```

---

## Complete Example

```python
import asyncio
from empirica.bootstraps import ExtendedMetacognitiveBootstrap
from empirica.data import SessionDatabase, SessionJSONHandler

async def complete_example():
    # 1. Initialize database
    db = SessionDatabase()
    handler = SessionJSONHandler()
    
    # 2. Create session
    session_id = db.create_session("my_ai", bootstrap_level=2, components_loaded=30)
    
    # 3. Bootstrap
    bootstrap = ExtendedMetacognitiveBootstrap(level="2", ai_id="my_ai")
    components = bootstrap.bootstrap()
    cascade = components['canonical_cascade']
    
    # 4. Create cascade tracking
    cascade_id = db.create_cascade(session_id, "Analyze auth.py", {'tracked': True})
    
    # 5. Run cascade
    result = await cascade.run_epistemic_cascade(
        task="Analyze authentication.py for security issues",
        context={'cwd': '/project', 'urgency': 'high'}
    )
    
    # 6. Complete tracking
    db.complete_cascade(
        cascade_id,
        final_action=result['action'],
        final_confidence=result['confidence'],
        investigation_rounds=result['investigation_rounds'],
        duration_ms=5000,
        engagement_gate_passed=True,
        bayesian_active=True
    )
    
    # 7. Export to JSON
    handler.export_session(db, session_id)
    
    # 8. Check results
    print(f"Action: {result['action']}")
    print(f"Confidence: {result['confidence']:.2f}")
    
    db.close()
    return result

asyncio.run(complete_example())
```

---

## Error Handling

```python
import asyncio
from empirica.bootstraps import ExtendedMetacognitiveBootstrap

async def with_errors():
    try:
        bootstrap = ExtendedMetacognitiveBootstrap(level="2")
        components = bootstrap.bootstrap()
        cascade = components['canonical_cascade']
        
        result = await cascade.run_epistemic_cascade(task, context)
        return result
        
    except KeyError as e:
        print(f"Component not found: {e}")
    except AttributeError as e:
        print(f"Attribute error (check imports): {e}")
    except asyncio.TimeoutError:
        print("Cascade timed out")
    except Exception as e:
        print(f"Unexpected error: {e}")
```

---

## Type Hints

```python
from typing import Dict, List, Any, Optional
from empirica.core.canonical import EpistemicAssessment
from empirica.bootstraps import ExtendedMetacognitiveBootstrap

async def typed_function(
    task: str,
    context: Dict[str, Any],
    level: str = "2"
) -> Dict[str, Any]:
    bootstrap: ExtendedMetacognitiveBootstrap = ExtendedMetacognitiveBootstrap(level=level)
    components: Dict[str, Any] = bootstrap.bootstrap()
    
    result: Dict[str, Any] = await components['canonical_cascade'].run_epistemic_cascade(
        task=task,
        context=context
    )
    
    return result
```

---

## Next Steps

- **Cascade Flow:** [06_CASCADE_FLOW.md](06_CASCADE_FLOW.md)
- **Custom Plugins:** [14_CUSTOM_PLUGINS.md](14_CUSTOM_PLUGINS.md)
- **Troubleshooting:** [21_TROUBLESHOOTING.md](21_TROUBLESHOOTING.md)

---

**Complete API reference for direct Python usage!** 📚
