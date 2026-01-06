# Assessment & Signaling Components

**Components for architecture assessment and epistemic signaling.**

---

## Architecture Assessment

**Module:** `empirica.core.architecture_assessment`

Apply epistemic framework to code architecture decisions.

### ArchitectureVectors

Epistemic vectors specific to architecture assessment.

```python
@dataclass
class ArchitectureVectors:
    coupling: float      # 0-1, lower is better
    cohesion: float      # 0-1, higher is better
    complexity: float    # 0-1, lower is better
    testability: float   # 0-1, higher is better
    maintainability: float
    confidence: float    # How confident in this assessment
```

### ComponentAssessment

Assessment result for a single component/module.

```python
@dataclass
class ComponentAssessment:
    component_path: str
    vectors: ArchitectureVectors
    issues: List[str]
    recommendations: List[str]
    dependencies: List[str]
    dependents: List[str]
    risk_score: float
```

### ComponentAssessor

Assesses architecture of code components.

```python
assessor = ComponentAssessor(repo_path=".")

# Assess single component
result = assessor.assess_component("src/auth/oauth.py")
print(f"Complexity: {result.vectors.complexity}")
print(f"Recommendations: {result.recommendations}")

# Assess directory
results = assessor.assess_directory("src/auth/")
for component in results:
    print(f"{component.component_path}: risk={component.risk_score}")
```

### CommitInfo

Information about commits for change tracking.

```python
@dataclass
class CommitInfo:
    hash: str
    message: str
    author: str
    timestamp: datetime
    files_changed: List[str]
    insertions: int
    deletions: int
```

---

## Signaling System

**Module:** `empirica.core.signaling`

Epistemic state signaling for real-time monitoring.

### SignalingState

Current epistemic signaling state.

```python
@dataclass
class SignalingState:
    session_id: str
    vectors: Dict[str, float]
    drift_level: DriftLevel
    sentinel_action: SentinelAction
    last_update: float
    alerts: List[str]
```

### DriftLevel (Enum)

Levels of epistemic drift severity.

```python
class DriftLevel(Enum):
    NONE = "none"           # No drift detected
    LOW = "low"             # Minor drift, continue
    MEDIUM = "medium"       # Monitor closely
    HIGH = "high"           # Investigate
    CRITICAL = "critical"   # Stop and reassess
```

### SentinelAction (Enum)

Actions recommended by Sentinel based on signaling.

```python
class SentinelAction(Enum):
    CONTINUE = "continue"       # Proceed normally
    MONITOR = "monitor"         # Continue with increased monitoring
    INVESTIGATE = "investigate" # Return to noetic phase
    HALT = "halt"              # Stop until resolved
    ESCALATE = "escalate"      # Escalate to human/lead AI
```

### VectorConfig

Configuration for epistemic vector behavior.

```python
@dataclass
class VectorConfig:
    name: str
    min_value: float = 0.0
    max_value: float = 1.0
    default: float = 0.5
    decay_rate: float = 0.0    # Temporal decay per hour
    alert_threshold: float = None  # Alert if crosses threshold
```

---

## Schemas

**Module:** `empirica.core.schemas`

Core data schemas for epistemic operations.

### AssessmentType (Enum)

Types of epistemic assessments.

```python
class AssessmentType(Enum):
    PREFLIGHT = "preflight"
    CHECK = "check"
    POSTFLIGHT = "postflight"
    SNAPSHOT = "snapshot"
    HANDOFF = "handoff"
```

### CascadePhase (Enum)

Phases in the CASCADE workflow.

```python
class CascadePhase(Enum):
    PREFLIGHT = "PREFLIGHT"   # Baseline assessment
    NOETIC = "NOETIC"         # Investigation phase
    CHECK = "CHECK"           # Gate decision
    PRAXIC = "PRAXIC"         # Action phase
    POSTFLIGHT = "POSTFLIGHT" # Learning delta
```

### VectorAssessment

Individual vector assessment with reasoning.

```python
@dataclass
class VectorAssessment:
    vector_name: str
    score: float              # 0.0 to 1.0
    confidence: float         # How confident in this score
    reasoning: str            # Why this score
    evidence: List[str]       # Supporting evidence
    change_from_previous: float  # Delta from last assessment
```

---

## Issue Capture

**Module:** `empirica.core.issue_capture`

Automatic issue capture from errors and logs.

### AutoIssueCaptureService

Service that automatically captures issues from errors.

```python
service = AutoIssueCaptureService(
    session_id="abc123",
    capture_errors=True,
    capture_warnings=False,
    min_severity="error"
)

# Start capturing
service.start()

# Issues are automatically captured when errors occur
# ...code that might raise exceptions...

# Get captured issues
issues = service.get_issues()
for issue in issues:
    print(f"{issue.id}: {issue.title} ({issue.status})")
```

### AutoCaptureLoggingHandler

Python logging handler that captures errors as issues.

```python
import logging

handler = AutoCaptureLoggingHandler(
    service=auto_issue_service,
    level=logging.ERROR
)

logger = logging.getLogger("my_app")
logger.addHandler(handler)

# Errors now auto-create issues
logger.error("Authentication failed")  # Creates issue automatically
```

### IssueStatus (Enum)

Status of captured issues.

```python
class IssueStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    WONT_FIX = "wont_fix"
    DUPLICATE = "duplicate"
```

---

## Skills

**Module:** `empirica.core.skills`

### SkillExtractor

Extract reusable skills from session execution patterns.

```python
extractor = SkillExtractor(session_id="abc123")

# Extract skills from successful session
skills = extractor.extract_skills(
    min_confidence=0.7,
    min_reuse_potential=0.5
)

for skill in skills:
    print(f"Skill: {skill.name}")
    print(f"  Pattern: {skill.trigger_pattern}")
    print(f"  Steps: {skill.execution_steps}")
```

---

## Source Files

- `empirica/core/architecture_assessment/` - Architecture assessment
- `empirica/core/signaling/` - Signaling components
- `empirica/core/schemas/` - Core schemas
- `empirica/core/issue_capture/` - Auto issue capture
- `empirica/core/skills/` - Skill extraction
