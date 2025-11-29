# 25. ScopeVector Guide

**3D Goal Scoping System**

---

## Overview

**ScopeVector** replaces the old enum-based scope system (`task_specific`, `session_scoped`, `project_wide`) with a **3-dimensional vector** for precise goal scoping.

**Three Dimensions:**
1. **Breadth** (0.0-1.0): How wide the goal spans
2. **Duration** (0.0-1.0): Expected lifetime  
3. **Coordination** (0.0-1.0): Multi-agent/session coordination needed

**Key Advantage**: Genuine AI self-assessment instead of categorical templates.

---

## The Three Dimensions

### 1. Breadth (Scope Width)

**Range**: 0.0 (narrow) → 1.0 (entire domain)

**Scale:**
- `0.0-0.2`: Single function/file/component
- `0.2-0.4`: Single module/package
- `0.4-0.6`: Multiple related modules
- `0.6-0.8`: Entire subsystem
- `0.8-1.0`: Entire codebase/domain

**Examples:**
```python
# Single function refactor
ScopeVector(breadth=0.1, ...)

# Module-level feature
ScopeVector(breadth=0.3, ...)

# Cross-cutting concern (logging, auth)
ScopeVector(breadth=0.7, ...)

# Complete system redesign
ScopeVector(breadth=0.9, ...)
```

---

### 2. Duration (Time Scope)

**Range**: 0.0 (minutes/hours) → 1.0 (weeks/months)

**Scale:**
- `0.0-0.2`: Minutes to hours
- `0.2-0.4`: Hours to days
- `0.4-0.6`: Days to week
- `0.6-0.8`: Weeks to month
- `0.8-1.0`: Months+

**Examples:**
```python
# Quick fix
ScopeVector(duration=0.1, ...)

# Feature implementation
ScopeVector(duration=0.4, ...)

# Multi-week project
ScopeVector(duration=0.7, ...)

# Long-term initiative
ScopeVector(duration=0.9, ...)
```

---

### 3. Coordination (Collaboration Needs)

**Range**: 0.0 (independent) → 1.0 (heavy collaboration)

**Scale:**
- `0.0-0.2`: Solo work, no dependencies
- `0.2-0.4`: Minimal coordination needed
- `0.4-0.6`: Moderate collaboration
- `0.6-0.8`: Heavy coordination required
- `0.8-1.0`: Complex multi-agent orchestration

**Examples:**
```python
# Solo investigation
ScopeVector(coordination=0.1, ...)

# Needs occasional input
ScopeVector(coordination=0.3, ...)

# Multi-agent collaboration
ScopeVector(coordination=0.7, ...)

# Complex orchestration
ScopeVector(coordination=0.9, ...)
```

---

## Creating ScopeVectors

### Method 1: Direct Creation

```python
from empirica.core.goals.types import ScopeVector, Goal

# Create scope vector
scope = ScopeVector(
    breadth=0.5,      # Module-level
    duration=0.3,     # Few days
    coordination=0.2  # Minimal coordination
)

# Create goal with scope
goal = Goal.create(
    objective="Implement rate limiting middleware",
    success_criteria=[
        "Rate limiter implemented",
        "Tests passing",
        "Documentation complete"
    ],
    scope=scope
)
```

### Method 2: MCO Recommendations (Preferred)

```python
from empirica.config.goal_scope_loader import get_scope_recommendations
from empirica.core.goals.types import ScopeVector

# Get recommendation based on epistemic state
rec = get_scope_recommendations(
    epistemic_vectors={
        'know': 0.75,
        'do': 0.80,
        'uncertainty': 0.35,
        'clarity': 0.85
    }
)

# Use recommended scope
scope = ScopeVector(
    breadth=rec['breadth'],
    duration=rec['duration'],
    coordination=rec['coordination']
)
```

### Method 3: MCP Tool (CLI/API)

```bash
# Create goal with scope via MCP
empirica create-goal \
  --session-id "uuid" \
  --objective "Implement authentication" \
  --scope '{"breadth": 0.6, "duration": 0.5, "coordination": 0.4}' \
  --success-criteria "Auth working" "Tests pass"
```

---

## Common Scope Patterns

### Pattern 1: Quick Fix

```python
ScopeVector(
    breadth=0.1,      # Single function
    duration=0.1,     # Hours
    coordination=0.1  # Solo
)

# Example: Fix typo, update constant, small bug fix
```

### Pattern 2: Feature Implementation

```python
ScopeVector(
    breadth=0.4,      # Module-level
    duration=0.4,     # Days
    coordination=0.3  # Some coordination
)

# Example: Add new API endpoint, implement feature
```

### Pattern 3: Refactoring

```python
ScopeVector(
    breadth=0.6,      # Multiple modules
    duration=0.5,     # Week
    coordination=0.4  # Moderate coordination
)

# Example: Refactor authentication system
```

### Pattern 4: Investigation

```python
ScopeVector(
    breadth=0.3,      # Focused area
    duration=0.2,     # Hours to days
    coordination=0.2  # Minimal
)

# Example: Investigate performance issue
```

### Pattern 5: Cross-Cutting Change

```python
ScopeVector(
    breadth=0.8,      # Entire codebase
    duration=0.6,     # Weeks
    coordination=0.7  # Heavy coordination
)

# Example: Add logging framework, implement security layer
```

### Pattern 6: Multi-Agent Project

```python
ScopeVector(
    breadth=0.7,      # Large subsystem
    duration=0.7,     # Weeks
    coordination=0.9  # Complex orchestration
)

# Example: Multi-agent system redesign
```

---

## Migration from Old Scope Enums

### Old System (Deprecated)

```python
# OLD: Enum-based scope
create_goal(
    scope="task_specific",    # or "session_scoped", "project_wide"
    ...
)
```

### New System (Current)

```python
# NEW: ScopeVector
create_goal(
    scope={"breadth": 0.3, "duration": 0.2, "coordination": 0.1},
    ...
)
```

### Migration Mapping

| Old Enum | Approximate ScopeVector |
|----------|------------------------|
| `task_specific` | `{breadth: 0.2, duration: 0.2, coordination: 0.1}` |
| `session_scoped` | `{breadth: 0.5, duration: 0.5, coordination: 0.4}` |
| `project_wide` | `{breadth: 0.8, duration: 0.7, coordination: 0.6}` |

**Note**: These are approximations. ScopeVector allows much more precise scoping.

---

## Validation and Coherence

### Automatic Validation

ScopeVector validates ranges on creation:

```python
# ✅ Valid
scope = ScopeVector(breadth=0.5, duration=0.5, coordination=0.5)

# ❌ Invalid - out of range
scope = ScopeVector(breadth=1.5, duration=0.5, coordination=0.5)
# Raises: ValueError: breadth must be 0.0-1.0, got 1.5
```

### Coherence Checking

MCO validates scope coherence:

```python
from empirica.config.goal_scope_loader import validate_scope_coherence

scope = {'breadth': 0.9, 'duration': 0.2, 'coordination': 0.1}

validation = validate_scope_coherence(scope)

if not validation['coherent']:
    print(validation['warnings'])
    # ["High breadth with low duration may be unrealistic"]
    
    print(validation['suggestions'])
    # ["Consider increasing duration for broad scope"]
```

**Common Incoherent Patterns:**
- High breadth + low duration (unrealistic timeline)
- High coordination + low breadth (over-coordination for small scope)
- Low coordination + high breadth (under-coordination for large scope)

---

## Best Practices

### 1. Use MCO Recommendations

Let MCO recommend scope based on epistemic state:

```python
# ✅ Recommended
rec = get_scope_recommendations(epistemic_vectors)
scope = ScopeVector(**rec)

# ❌ Avoid hardcoding
scope = ScopeVector(0.5, 0.5, 0.5)  # Generic, not context-aware
```

### 2. Validate Coherence

Always validate custom scopes:

```python
scope = ScopeVector(breadth=0.8, duration=0.3, coordination=0.2)

validation = validate_scope_coherence(scope.to_dict())
if validation['severity'] == 'high':
    # Adjust scope based on warnings
    scope.duration = 0.6
```

### 3. Be Honest About Scope

Assess scope realistically based on:
- **Breadth**: How many components actually affected?
- **Duration**: Realistic timeline given complexity?
- **Coordination**: How much collaboration truly needed?

```python
# ❌ Overconfident
ScopeVector(breadth=0.9, duration=0.2, coordination=0.1)
# "Redesign entire system in a day solo" - unrealistic

# ✅ Realistic
ScopeVector(breadth=0.9, duration=0.7, coordination=0.7)
# "Redesign entire system over weeks with team" - coherent
```

### 4. Adjust During Execution

Scope can be updated as understanding improves:

```python
# Initial scope (high uncertainty)
initial_scope = ScopeVector(breadth=0.3, duration=0.3, coordination=0.2)

# After investigation, scope expands
updated_scope = ScopeVector(breadth=0.5, duration=0.5, coordination=0.4)

# Update goal
goal.scope = updated_scope
```

---

## Integration with CASCADE

ScopeVector integrates with the CASCADE workflow:

```
PREFLIGHT → Assess epistemic state
    ↓
INVESTIGATE → Get scope recommendations from MCO
    ↓
    scope = get_scope_recommendations(epistemic_vectors)
    goal = create_goal(scope=ScopeVector(**scope))
    ↓
CHECK → Validate scope coherence
    ↓
ACT → Execute within scope boundaries
    ↓
POSTFLIGHT → Assess if scope was accurate
```

---

## Python API

### Full Example

```python
from empirica.core.goals.types import ScopeVector, Goal, SuccessCriterion
from empirica.config.goal_scope_loader import get_scope_recommendations
import uuid

# Get epistemic state
epistemic_vectors = {
    'know': 0.75,
    'do': 0.80,
    'context': 0.70,
    'clarity': 0.85,
    'uncertainty': 0.35
}

# Get MCO recommendation
rec = get_scope_recommendations(epistemic_vectors)

# Create scope
scope = ScopeVector(
    breadth=rec['breadth'],
    duration=rec['duration'],
    coordination=rec['coordination']
)

# Create success criteria
criteria = [
    SuccessCriterion(
        id=str(uuid.uuid4()),
        description="Rate limiter implemented",
        validation_method="completion",
        is_required=True
    ),
    SuccessCriterion(
        id=str(uuid.uuid4()),
        description="Tests passing",
        validation_method="quality_gate",
        is_required=True
    )
]

# Create goal
goal = Goal.create(
    objective="Implement rate limiting middleware",
    success_criteria=criteria,
    scope=scope,
    estimated_complexity=0.6
)

print(f"Goal ID: {goal.id}")
print(f"Scope: breadth={scope.breadth}, duration={scope.duration}, coord={scope.coordination}")
```

---

## Next Reading

- **MCO Architecture**: [24_MCO_ARCHITECTURE.md](file:///home/yogapad/empirical-ai/empirica/docs/production/24_MCO_ARCHITECTURE.md)
- **Cross-AI Coordination**: [26_CROSS_AI_COORDINATION.md](file:///home/yogapad/empirical-ai/empirica/docs/production/26_CROSS_AI_COORDINATION.md)
- **Goal Management**: [20_TOOL_CATALOG.md](file:///home/yogapad/empirical-ai/empirica/docs/production/20_TOOL_CATALOG.md#5-goal-management)

---

**ScopeVector - Precise, Flexible, AI-Driven Goal Scoping** 🎯
