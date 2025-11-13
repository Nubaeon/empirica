# Calibration System Reference

**Component:** Adaptive Uncertainty Calibration  
**Status:** Production Active  
**Used By:** 10+ files including CASCADE, CLI, bootstraps

---

## Overview

Empirica's calibration system tracks AI prediction accuracy over time and adapts uncertainty estimates based on feedback. This enables the AI to learn from its mistakes and improve confidence calibration.

**Key Concept:** If the AI consistently overestimates confidence, the calibration system adjusts to be more conservative. If it consistently underestimates, it adjusts to be more confident.

---

## Architecture

### Core Component

**`AdaptiveUncertaintyCalibration`** - Main calibration engine

**Location:** `empirica/calibration/adaptive_uncertainty_calibration/`

**Purpose:**
- Track feedback outcomes (correct/incorrect predictions)
- Calculate calibration accuracy
- Adjust uncertainty based on performance
- Provide calibration metrics for POSTFLIGHT

---

## Integration Points

### 1. CASCADE Workflow

**POSTFLIGHT Phase:**
```python
from empirica.calibration.adaptive_uncertainty_calibration import (
    AdaptiveUncertaintyCalibration,
    FeedbackOutcome
)

calibration = AdaptiveUncertaintyCalibration()

# After task completion, provide feedback
outcome = FeedbackOutcome.CORRECT  # or INCORRECT, PARTIAL
calibration.update(
    predicted_confidence=0.8,
    actual_outcome=outcome,
    task_context={'domain': 'code_analysis'}
)

# Get calibrated adjustment
adjustment = calibration.get_adjustment()
```

**Used In:**
- `empirica/cli/command_handlers/cascade_commands.py`
- `empirica/cli/command_handlers/assessment_commands.py`
- Bootstrap processes

### 2. Bootstraps

**Optimal Metacognitive Bootstrap:**
```python
from empirica.bootstraps.optimal_metacognitive_bootstrap import bootstrap_session
from empirica.calibration.adaptive_uncertainty_calibration import AdaptiveUncertaintyCalibration

# Calibration is initialized automatically
session = bootstrap_session(
    ai_id='claude',
    session_type='production',
    enable_calibration=True  # Default
)
```

### 3. CLI Commands

**Manual Feedback:**
```bash
# Provide feedback after cascade
empirica cascade feedback --session-id <id> --outcome correct
empirica cascade feedback --session-id <id> --outcome incorrect
empirica cascade feedback --session-id <id> --outcome partial
```

---

## API Reference

### AdaptiveUncertaintyCalibration

```python
class AdaptiveUncertaintyCalibration:
    """
    Adaptive calibration based on feedback outcomes
    
    Tracks prediction accuracy and adjusts uncertainty estimates
    to improve calibration over time.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize calibration system
        
        Args:
            db_path: Path to calibration database (default: .empirica/calibration.db)
        """
        pass
    
    def update(
        self,
        predicted_confidence: float,
        actual_outcome: FeedbackOutcome,
        task_context: Optional[Dict] = None
    ) -> None:
        """
        Update calibration based on feedback
        
        Args:
            predicted_confidence: What the AI predicted (0.0-1.0)
            actual_outcome: What actually happened
            task_context: Optional context (domain, task type, etc.)
        """
        pass
    
    def get_adjustment(
        self,
        domain: Optional[str] = None
    ) -> float:
        """
        Get calibration adjustment factor
        
        Returns:
            Adjustment factor to apply to confidence scores
            > 1.0: AI is underconfident, increase confidence
            < 1.0: AI is overconfident, decrease confidence
            = 1.0: AI is well-calibrated
        """
        pass
    
    def get_accuracy(
        self,
        domain: Optional[str] = None
    ) -> float:
        """
        Get calibration accuracy percentage
        
        Returns:
            Accuracy as 0.0-1.0 (0.0 = always wrong, 1.0 = always right)
        """
        pass
```

### FeedbackOutcome

```python
class FeedbackOutcome(Enum):
    """Outcome of a prediction/task"""
    CORRECT = "correct"      # Prediction was accurate
    INCORRECT = "incorrect"  # Prediction was wrong
    PARTIAL = "partial"      # Partially correct
```

---

## Usage Patterns

### Pattern 1: Automatic Calibration (Recommended)

Let the CASCADE workflow handle calibration automatically:

```python
from empirica.core.metacognitive_cascade import run_canonical_cascade

result = await run_canonical_cascade(
    task="Review authentication module",
    context={'cwd': '/project'},
    enable_calibration=True  # Default
)

# Calibration happens automatically in POSTFLIGHT
# No manual intervention needed
```

### Pattern 2: Manual Calibration

For custom workflows, manually update calibration:

```python
from empirica.calibration.adaptive_uncertainty_calibration import (
    AdaptiveUncertaintyCalibration,
    FeedbackOutcome
)

calibration = AdaptiveUncertaintyCalibration()

# Make prediction
predicted_confidence = 0.85

# ... execute task ...

# Provide feedback
if task_succeeded:
    outcome = FeedbackOutcome.CORRECT
else:
    outcome = FeedbackOutcome.INCORRECT

calibration.update(predicted_confidence, outcome)

# Get adjustment for next prediction
adjustment = calibration.get_adjustment()
next_confidence = base_confidence * adjustment
```

### Pattern 3: Domain-Specific Calibration

Track calibration per domain:

```python
calibration = AdaptiveUncertaintyCalibration()

# Code analysis task
calibration.update(
    predicted_confidence=0.9,
    actual_outcome=FeedbackOutcome.CORRECT,
    task_context={'domain': 'code_analysis'}
)

# Research task
calibration.update(
    predicted_confidence=0.7,
    actual_outcome=FeedbackOutcome.INCORRECT,
    task_context={'domain': 'research'}
)

# Get domain-specific adjustments
code_adjustment = calibration.get_adjustment(domain='code_analysis')
research_adjustment = calibration.get_adjustment(domain='research')
```

---

## Calibration Workflow

### Complete Cycle

```
1. PREFLIGHT
   ├─ Initial confidence assessment
   └─ Apply previous calibration adjustment
   
2. INVESTIGATE
   └─ Execute with calibrated confidence
   
3. CHECK
   └─ Verify with calibrated thresholds
   
4. ACT
   └─ Execute task
   
5. POSTFLIGHT
   ├─ Compare predicted vs actual
   ├─ Update calibration
   └─ Store for next cycle
```

### Example Flow

```python
# Cycle 1
initial_confidence = 0.8
adjustment = 1.0  # No history yet
calibrated_confidence = 0.8 * 1.0 = 0.8
# Task succeeds
calibration.update(0.8, FeedbackOutcome.CORRECT)

# Cycle 2
initial_confidence = 0.9
adjustment = 1.0  # Still well-calibrated
calibrated_confidence = 0.9 * 1.0 = 0.9
# Task fails
calibration.update(0.9, FeedbackOutcome.INCORRECT)

# Cycle 3
initial_confidence = 0.85
adjustment = 0.9  # System learned to be less confident
calibrated_confidence = 0.85 * 0.9 = 0.765
# Task succeeds (better calibrated!)
```

---

## Monitoring Calibration

### Check Calibration Status

```bash
# View calibration accuracy
empirica calibration show --domain code_analysis

# View calibration history
empirica calibration history --limit 10

# Export calibration data
empirica calibration export --output calibration.json
```

### Programmatic Access

```python
calibration = AdaptiveUncertaintyCalibration()

# Get overall accuracy
accuracy = calibration.get_accuracy()
print(f"Calibration accuracy: {accuracy:.1%}")

# Get domain-specific accuracy
code_accuracy = calibration.get_accuracy(domain='code_analysis')
research_accuracy = calibration.get_accuracy(domain='research')

print(f"Code analysis: {code_accuracy:.1%}")
print(f"Research: {research_accuracy:.1%}")
```

---

## Configuration

### Database Location

Default: `.empirica/calibration.db`

Custom:
```python
calibration = AdaptiveUncertaintyCalibration(
    db_path='/custom/path/calibration.db'
)
```

### Adjustment Bounds

Adjustments are bounded to prevent extreme corrections:

- Minimum: 0.5 (max 50% reduction in confidence)
- Maximum: 1.5 (max 50% increase in confidence)

This prevents the system from overcorrecting based on limited data.

---

## Best Practices

### 1. Provide Honest Feedback

```python
# Good - honest assessment
outcome = FeedbackOutcome.PARTIAL  # Task partially succeeded

# Bad - inflating accuracy
outcome = FeedbackOutcome.CORRECT  # Even though it was only partial
```

### 2. Use Domain Context

```python
# Good - domain tracking
calibration.update(
    0.8,
    outcome,
    task_context={'domain': 'code_analysis', 'complexity': 'high'}
)

# Acceptable - no context
calibration.update(0.8, outcome)
```

### 3. Let It Learn Gradually

Don't expect perfect calibration immediately. The system needs:
- 10-20 samples for initial calibration
- 50+ samples for stable calibration
- 100+ samples for domain-specific calibration

### 4. Monitor Trends

```python
# Check if calibration is improving
history = calibration.get_history(limit=50)
recent_accuracy = sum(h.correct for h in history[-10:]) / 10
older_accuracy = sum(h.correct for h in history[-50:-40]) / 10

if recent_accuracy > older_accuracy:
    print("✅ Calibration improving")
```

---

## Troubleshooting

### Low Calibration Accuracy

**Symptom:** Accuracy < 50%

**Possible Causes:**
- Insufficient data (< 10 samples)
- Task difficulty mismatch
- Inconsistent feedback

**Solution:**
```python
# Check sample count
sample_count = calibration.get_sample_count()
if sample_count < 20:
    print("⚠️ Need more samples for stable calibration")
```

### Over/Under Adjustment

**Symptom:** Adjustment factor stuck at extremes (0.5 or 1.5)

**Possible Causes:**
- Consistently wrong predictions
- Domain mismatch

**Solution:**
```python
# Reset calibration for domain
calibration.reset(domain='problematic_domain')
```

---

## Integration Examples

### Example 1: CLI Integration

```bash
# Run cascade with calibration
empirica cascade run "Review authentication" --enable-calibration

# Provide feedback
empirica cascade feedback --session-id abc123 --outcome correct

# Check calibration
empirica calibration show
```

### Example 2: Python Integration

```python
from empirica import run_canonical_cascade
from empirica.calibration.adaptive_uncertainty_calibration import AdaptiveUncertaintyCalibration

# Run with calibration
result = await run_canonical_cascade(
    task="Analyze security vulnerability",
    enable_calibration=True
)

# Manual verification
calibration = AdaptiveUncertaintyCalibration()
print(f"Current accuracy: {calibration.get_accuracy():.1%}")
```

---

## See Also

- `docs/reference/CASCADE_WORKFLOW.md` - Full CASCADE documentation
- `docs/reference/POSTFLIGHT_PHASE.md` - POSTFLIGHT integration
- `empirica/calibration/adaptive_uncertainty_calibration/` - Source code
- `LEGACY_COMPONENTS_ASSESSMENT.md` - Component analysis

---

**Status:** Production Active ✅  
**Used In:** CASCADE, CLI, Bootstraps, Dashboard  
**Maintained:** Yes  
**Documented:** 2025-11-13
