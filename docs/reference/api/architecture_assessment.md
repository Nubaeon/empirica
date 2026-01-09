# Architecture Assessment API

**Module:** `empirica.core.architecture_assessment`
**Category:** Code Quality Analysis
**Stability:** Beta

---

## Overview

Maps Empirica's 13 epistemic vectors to code architecture concerns. Enables AI agents to assess code quality, coupling, and stability using the same vector framework.

---

## Data Classes

### ArchitectureVectors

Epistemic vectors applied to architecture assessment.

```python
from empirica.core.architecture_assessment.schema import ArchitectureVectors

vectors = ArchitectureVectors(
    know=0.8,          # Code understanding (docs, tests, readability)
    uncertainty=0.2,   # Technical debt (hidden complexity)
    context=0.7,       # Integration clarity (system fit)
    clarity=0.75,      # API surface cleanliness
    coherence=0.8,     # Single responsibility adherence
    signal=0.6,        # Meaningful change patterns
    density=0.3,       # Complexity (inverted: low = simple)
    engagement=0.5,    # Development activity level
    state=0.7,         # Health indicators (coverage, linting)
    change=0.2,        # Stability (inverted: low = stable)
    completion=0.9,    # Feature completeness
    impact=0.4,        # Blast radius (inverted: low = isolated)
    do=0.6,            # Actionability (clear improvement path)
)

confidence = vectors.confidence_score()  # Weighted average
```

---

### CouplingMetrics

Metrics from CouplingAnalyzer - dependency and API surface analysis.

```python
from empirica.core.architecture_assessment.schema import CouplingMetrics

@dataclass
class CouplingMetrics:
    afferent_coupling: int = 0      # Incoming dependencies (who uses us)
    efferent_coupling: int = 0      # Outgoing dependencies (who we use)
    instability: float = 0.5        # Ce / (Ca + Ce) - 0=stable, 1=unstable
    abstractness: float = 0.0       # Abstract types / total types
    distance_from_main: float = 0.5 # |A + I - 1| - distance from ideal

    # API surface
    public_functions: int = 0
    private_functions: int = 0
    api_surface_ratio: float = 0.0  # public / total

    # Boundary clarity
    clear_interface: bool = True
    leaked_internals: List[str] = field(default_factory=list)
```

---

### StabilityMetrics

Metrics from StabilityEstimator - git history analysis.

```python
from empirica.core.architecture_assessment.schema import StabilityMetrics

@dataclass
class StabilityMetrics:
    total_commits: int = 0
    recent_commits_30d: int = 0
    unique_authors: int = 0

    # Change patterns
    avg_lines_per_commit: float = 0.0
    churn_rate: float = 0.0         # Lines changed / total lines
    hotspot_score: float = 0.0      # Frequency * complexity

    # Time-based
    days_since_last_change: int = 0
    age_days: int = 0
    maintenance_ratio: float = 0.0  # Bug fixes / total commits
```

---

## Analyzers

### CouplingAnalyzer

Analyzes dependency relationships and API surface.

```python
from empirica.core.architecture_assessment.coupling_analyzer import CouplingAnalyzer

analyzer = CouplingAnalyzer(project_root="/path/to/project")

# Analyze a module
metrics = analyzer.analyze("empirica/core/session.py")

# Convert to epistemic vectors
vectors = analyzer.to_vectors(metrics)
# Returns: {'clarity': 0.8, 'context': 0.7, 'impact': 0.3}
```

**Methods:**

| Method | Description |
|--------|-------------|
| `analyze(component_path)` | Analyze coupling for file or package |
| `to_vectors(metrics)` | Convert to clarity, context, impact vectors |

**Vector Mappings:**
- `clarity` → Clean API surface (high public/private ratio, no leaked internals)
- `context` → Balanced coupling (low distance from main sequence)
- `impact` → Blast radius (high afferent coupling = many dependents)

---

### StabilityEstimator

Analyzes git history for stability metrics.

```python
from empirica.core.architecture_assessment.stability_estimator import StabilityEstimator

estimator = StabilityEstimator(project_root="/path/to/repo")

# Analyze a component
metrics = estimator.analyze("empirica/core/session.py")

# Get author breakdown
authors = estimator.get_authors("empirica/core/session.py")
# Returns: [("Alice", 15), ("Bob", 8), ...]

# Convert to epistemic vectors
vectors = estimator.to_vectors(metrics)
# Returns: {'change': 0.2, 'engagement': 0.7, 'signal': 0.8}
```

**Methods:**

| Method | Description |
|--------|-------------|
| `analyze(component_path)` | Analyze stability from git history |
| `get_authors(component_path)` | Get author commit counts |
| `to_vectors(metrics)` | Convert to change, engagement, signal vectors |

**Vector Mappings:**
- `change` → Stability (low churn rate = stable)
- `engagement` → Activity level (recent commits)
- `signal` → Meaningful changes (healthy maintenance ratio)

---

### ComponentAssessment

Complete epistemic assessment combining all analyzers.

```python
from empirica.core.architecture_assessment.schema import ComponentAssessment

assessment = ComponentAssessment(
    component_path="empirica/core/session.py",
    component_name="session",
    component_type="module",
    vectors=ArchitectureVectors(...),
    coupling=CouplingMetrics(...),
    stability=StabilityMetrics(...),
    risk_level="low",
    recommendations=["Add more tests", "Reduce coupling to X"]
)

# Get summary
print(assessment.summary())

# Convert to dict for storage
data = assessment.to_dict()
```

---

## Implementation Files

- `empirica/core/architecture_assessment/schema.py` - ArchitectureVectors, CouplingMetrics, StabilityMetrics, ComponentAssessment
- `empirica/core/architecture_assessment/coupling_analyzer.py` - CouplingAnalyzer
- `empirica/core/architecture_assessment/stability_estimator.py` - StabilityEstimator

---

**API Stability:** Beta
**Last Updated:** 2026-01-09
