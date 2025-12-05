# 24. MCO Architecture

**Meta-Agent Configuration Object - Dynamic Configuration System**

**Storage Architecture:** See `docs/architecture/STORAGE_ARCHITECTURE_COMPLETE.md`  

---

## Overview

The **MCO (Meta-Agent Configuration Object)** is Empirica's dynamic configuration architecture that automatically loads optimal settings based on:
- **Persona type** (researcher, implementer, analyst, coordinator, learner, expert)
- **Model profile** (bias correction for specific AI models)
- **Threshold profiles** (confidence gates, uncertainty tolerance)
- **Protocol schemas** (standardized tool interfaces)

**Key Principle**: AI determines goals and actions; MCO provides scope recommendations and operational parameters based on epistemic state.

---

## Architecture Components

### 1. Persona Selection

Personas define behavioral patterns and threshold adjustments for different work modes.

**Available Personas:**
- `researcher` - Exploration-focused, higher uncertainty tolerance
- `implementer` - Execution-focused, requires higher confidence
- `analyst` - Analysis-focused, systematic investigation
- `coordinator` - Multi-agent coordination, collaboration emphasis
- `learner` - Learning mode, lower initial confidence expectations
- `expert` - Domain expert mode, higher baseline confidence

**Auto-Selection**: MCO recommends persona based on task type and epistemic vectors.

---

### 2. Model Profiles

Model-specific bias corrections to account for known calibration patterns.

**Purpose**: Different AI models have different confidence calibration patterns. MCO adjusts thresholds accordingly.

**Example Adjustments:**
```python
# Model tends to be overconfident
model_profile = {
    "bias_type": "overconfident",
    "confidence_adjustment": -0.10,  # Reduce reported confidence
    "uncertainty_boost": +0.05       # Increase uncertainty awareness
}

# Model tends to be underconfident  
model_profile = {
    "bias_type": "underconfident",
    "confidence_adjustment": +0.08,
    "uncertainty_boost": -0.03
}
```

---

### 3. Threshold Profiles

Dynamic confidence gates and decision thresholds.

**Standard Thresholds:**
```python
thresholds = {
    "engagement_gate": 0.60,          # Minimum engagement to proceed
    "action_confidence": 0.70,        # Minimum confidence for ACT phase
    "investigation_trigger": 0.55,    # Below this → INVESTIGATE
    "uncertainty_high": 0.70,         # High uncertainty threshold
    "uncertainty_critical": 0.85      # Critical uncertainty (must investigate)
}
```

**Persona-Adjusted Thresholds:**
```python
# Researcher persona (higher uncertainty tolerance)
researcher_thresholds = {
    "action_confidence": 0.65,        # Lower bar for action
    "uncertainty_high": 0.75,         # Higher tolerance
}

# Implementer persona (requires higher confidence)
implementer_thresholds = {
    "action_confidence": 0.75,        # Higher bar for action
    "uncertainty_high": 0.60,         # Lower tolerance
}
```

---

### 4. Goal Scope Loader

Maps epistemic vectors to recommended scope vectors for goal creation.

**See**: [25_SCOPEVECTOR_GUIDE.md](file:///home/yogapad/empirical-ai/empirica/docs/production/25_SCOPEVECTOR_GUIDE.md) for detailed ScopeVector documentation.

**Integration:**
```python
from empirica.config.goal_scope_loader import get_scope_recommendations

# Get scope recommendation based on epistemic state
recommendations = get_scope_recommendations(
    epistemic_vectors={
        'know': 0.85,
        'uncertainty': 0.30,
        'clarity': 0.80,
        'engagement': 0.75
    }
)

# Returns recommended scope
{
    'breadth': 0.7,
    'duration': 0.6,
    'coordination': 0.4,
    'pattern': 'knowledge_leader',
    'rationale': 'High knowledge enables broader scope'
}
```

---

## Bootstrap Integration

MCO configuration is loaded automatically during bootstrap.

```python
# ❌ DEPRECATED - Bootstrap classes removed (bootstrap reserved for system prompts)
# from empirica.bootstraps.optimal_metacognitive_bootstrap import OptimalMetacognitiveBootstrap

# ✅ CORRECT - Use session-create with MCO configuration
from empirica.data.session_database import SessionDatabase

# Create session with MCO settings
db = SessionDatabase()
session_id = db.create_session(
    ai_id="my-ai",
    bootstrap_level=2  # Full metacognitive tracking
)

# MCO configuration can be applied via:
# 1. CLI: empirica session-create --ai-id my-ai --bootstrap-level 2
# 2. Configuration files in empirica/config/mco/
# 3. Direct API calls with persona and model profile settings

db.close()
# Thresholds, personas, and scope recommendations are loaded
```

---

## Usage Patterns

### Pattern 1: Adaptive Thresholds

```python
from empirica.core.thresholds import get_active_thresholds

# Get current thresholds (persona-adjusted)
thresholds = get_active_thresholds()

if assessment.overall_confidence < thresholds['action_confidence']:
    # Below threshold → investigate
    action = "investigate"
else:
    # Above threshold → proceed
    action = "proceed"
```

### Pattern 2: Scope Recommendations

```python
from empirica.config.goal_scope_loader import get_scope_recommendations
from empirica.core.goals.types import ScopeVector, Goal

# Get recommendation
rec = get_scope_recommendations(
    epistemic_vectors=current_assessment,
    context={'priority': 'high', 'deadline_tight': False}
)

# Create goal with recommended scope
scope = ScopeVector(
    breadth=rec['breadth'],
    duration=rec['duration'],
    coordination=rec['coordination']
)

goal = Goal.create(
    objective="Implement authentication module",
    success_criteria=[...],
    scope=scope
)
```

### Pattern 3: Persona Switching

```python
from empirica.config.threshold_loader import switch_persona

# Switch to researcher mode for exploration
switch_persona("researcher")

# Investigation with higher uncertainty tolerance
result = cascade.run_epistemic_cascade(task, context)

# Switch back to implementer for execution
switch_persona("implementer")
```

---

## Configuration Files

MCO configurations are stored in `/empirica/config/mco/`:

```
/empirica/config/mco/
├── personas.yaml           # Persona definitions
├── model_profiles.yaml     # Model-specific adjustments
├── thresholds.yaml         # Threshold profiles
└── goal_scopes.yaml        # Scope recommendation patterns
```

### Example: `personas.yaml`

```yaml
researcher:
  description: "Exploration and investigation focused"
  threshold_adjustments:
    action_confidence: -0.05
    uncertainty_high: +0.10
  behavioral_traits:
    - systematic_exploration
    - hypothesis_testing
    - evidence_gathering

implementer:
  description: "Execution and delivery focused"
  threshold_adjustments:
    action_confidence: +0.05
    uncertainty_high: -0.10
  behavioral_traits:
    - test_driven
    - quality_focused
    - completion_oriented
```

---

## Advanced Features

### 1. Dynamic Threshold Adjustment

MCO can adjust thresholds mid-session based on performance:

```python
from empirica.config.threshold_loader import adjust_thresholds_dynamic

# After calibration analysis
calibration_report = get_calibration_report(session_id)

if calibration_report['overconfidence_detected']:
    # Increase action threshold
    adjust_thresholds_dynamic(action_confidence=+0.05)
```

### 2. Custom Personas

Define custom personas for specialized workflows:

```python
from empirica.config.threshold_loader import register_custom_persona

custom_persona = {
    "name": "security_auditor",
    "description": "Security-focused with high verification standards",
    "threshold_adjustments": {
        "action_confidence": +0.10,
        "uncertainty_high": -0.15
    },
    "behavioral_traits": [
        "paranoid_verification",
        "threat_modeling",
        "defense_in_depth"
    ]
}

register_custom_persona(custom_persona)
```

### 3. Scope Coherence Validation

MCO validates scope vectors for coherence:

```python
from empirica.config.goal_scope_loader import validate_scope_coherence

scope_vector = {'breadth': 0.9, 'duration': 0.2, 'coordination': 0.1}

validation = validate_scope_coherence(scope_vector)

if not validation['coherent']:
    print(f"Warnings: {validation['warnings']}")
    print(f"Suggestions: {validation['suggestions']}")
    # Example warning: "High breadth with low duration may be unrealistic"
```

---

## Best Practices

### 1. Let MCO Recommend

Don't hardcode scope values - use MCO recommendations:

```python
# ❌ Hardcoded scope
scope = ScopeVector(breadth=0.5, duration=0.5, coordination=0.5)

# ✅ MCO-recommended scope
rec = get_scope_recommendations(epistemic_vectors)
scope = ScopeVector(**rec)
```

### 2. Respect Persona Thresholds

Use active thresholds, not hardcoded values:

```python
# ❌ Hardcoded threshold
if confidence > 0.70:
    proceed()

# ✅ Persona-adjusted threshold
thresholds = get_active_thresholds()
if confidence > thresholds['action_confidence']:
    proceed()
```

### 3. Validate Scope Coherence

Always validate custom scopes:

```python
# Create custom scope
scope = ScopeVector(breadth=0.9, duration=0.3, coordination=0.2)

# Validate coherence
validation = validate_scope_coherence(scope.to_dict())
if not validation['coherent']:
    # Adjust based on warnings
    scope.duration = 0.6  # Increase duration for high breadth
```

---

## Integration with CASCADE

MCO is fully integrated with the CASCADE workflow:

```
BOOTSTRAP → Load MCO configuration (persona, thresholds, model profile)
    ↓
PREFLIGHT → Use persona-adjusted thresholds for assessment
    ↓
INVESTIGATE → Get scope recommendations for goal creation
    ↓
CHECK → Apply model-specific bias corrections
    ↓
ACT → Use persona-adjusted action thresholds
    ↓
POSTFLIGHT → Calibration analysis for dynamic adjustment
```

---

## Next Reading

- **ScopeVector Guide**: [25_SCOPEVECTOR_GUIDE.md](file:///home/yogapad/empirical-ai/empirica/docs/production/25_SCOPEVECTOR_GUIDE.md)
- **Cross-AI Coordination**: [26_CROSS_AI_COORDINATION.md](file:///home/yogapad/empirical-ai/empirica/docs/production/26_CROSS_AI_COORDINATION.md)
- **Thresholds**: [16_TUNING_THRESHOLDS.md](file:///home/yogapad/empirical-ai/empirica/docs/production/16_TUNING_THRESHOLDS.md)

---

**MCO Architecture - Dynamic, Adaptive, Intelligent Configuration** 🎯
