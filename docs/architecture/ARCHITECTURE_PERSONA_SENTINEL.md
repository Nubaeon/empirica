# Persona-Sentinel Architecture: Domain Expertise Design

## The Question

Where should domain expertise live in the Persona-Sentinel system?

**Option A: Universal Components + Domain-Specific Configuration**
- Universal PersonaHarness (runtime execution)
- Domain-specific Personas (templates: security, UX, etc.)
- Domain-qualified Sentinels (trained via knowledge distillation)

**Option B: Specialized Components**
- Domain-specific PersonaHarness classes (SecurityHarness, UXHarness)
- Specialized Sentinels per domain
- Hard-coded domain logic

## Recommended: Hybrid Architecture

### Layer 1: Universal Schema (NEW!)

**Create canonical EpistemicAssessment schema**

```python
# empirica/core/schemas/epistemic_assessment.py
"""
Canonical Epistemic Assessment Schema

Used by:
- CLI parser
- MCP tools
- PersonaHarness
- SentinelOrchestrator
- Validation layer
"""

from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class VectorAssessment:
    """Single epistemic vector assessment"""
    score: float  # 0.0-1.0
    rationale: str
    evidence: Optional[str] = None

@dataclass
class EpistemicAssessmentSchema:
    """
    Canonical 13-vector epistemic assessment

    This is THE format for all epistemic assessments across:
    - PREFLIGHT, CHECK, POSTFLIGHT phases
    - CLI, MCP, Harness, Sentinel
    - Human and AI assessments
    """
    # Gate
    engagement: VectorAssessment

    # Foundation (Tier 0)
    foundation_know: VectorAssessment
    foundation_do: VectorAssessment
    foundation_context: VectorAssessment

    # Comprehension (Tier 1)
    comprehension_clarity: VectorAssessment
    comprehension_coherence: VectorAssessment
    comprehension_signal: VectorAssessment
    comprehension_density: VectorAssessment

    # Execution (Tier 2)
    execution_state: VectorAssessment
    execution_change: VectorAssessment
    execution_completion: VectorAssessment
    execution_impact: VectorAssessment

    # Meta
    uncertainty: VectorAssessment

    def to_nested_dict(self) -> Dict:
        """Convert to nested format (for CLI/MCP)"""
        return {
            "engagement": {
                "score": self.engagement.score,
                "rationale": self.engagement.rationale,
                "evidence": self.engagement.evidence
            },
            "foundation": {
                "know": {
                    "score": self.foundation_know.score,
                    "rationale": self.foundation_know.rationale,
                    "evidence": self.foundation_know.evidence
                },
                "do": {...},
                "context": {...}
            },
            "comprehension": {...},
            "execution": {...},
            "uncertainty": {...}
        }

    @classmethod
    def from_nested_dict(cls, data: Dict) -> 'EpistemicAssessmentSchema':
        """Parse from nested format"""
        return cls(
            engagement=VectorAssessment(**data["engagement"]),
            foundation_know=VectorAssessment(**data["foundation"]["know"]),
            # ... etc
        )

    def apply_persona_priors(self, persona: 'PersonaProfile', strength: float) -> 'EpistemicAssessmentSchema':
        """Apply persona priors to this assessment"""
        # Blend baseline with persona priors
        blended = EpistemicAssessmentSchema(
            engagement=self._blend_vector(self.engagement, persona.epistemic_config.priors['engagement'], strength),
            foundation_know=self._blend_vector(self.foundation_know, persona.epistemic_config.priors['know'], strength),
            # ... etc
        )
        return blended
```

**Benefits:**
- ✅ Single source of truth for assessment format
- ✅ Used by CLI, MCP, Harness, Sentinel
- ✅ Validates before submission
- ✅ Converts between formats (nested dict, flat object, etc.)
- ✅ Handles persona prior application

### Layer 2: Universal PersonaHarness

**PersonaHarness remains universal:**
- Wraps any PersonaProfile
- Applies persona priors using `EpistemicAssessmentSchema.apply_persona_priors()`
- Maps persona types to investigation profiles
- Reports to Sentinel via signed messages

**Why universal?**
- Separation of concerns: runtime vs domain knowledge
- Extensibility: add domains via templates, not code
- Simplicity: one harness implementation to maintain

### Layer 3: Domain-Specific Personas

**Personas encode domain expertise:**
```python
# Built-in templates (already implemented)
SECURITY_EXPERT = {
    "priors": {"know": 0.90, "uncertainty": 0.15, ...},
    "thresholds": {"uncertainty_trigger": 0.30, "confidence_to_proceed": 0.85},
    "weights": {"foundation": 0.40, "comprehension": 0.25, ...},
    "focus_domains": ["security", "authentication", "vulnerabilities"]
}

# Custom domain-specific templates
ML_ENGINEER = {
    "priors": {"know": 0.85, "do": 0.90, "context": 0.75, ...},
    "thresholds": {"uncertainty_trigger": 0.35, "confidence_to_proceed": 0.80},
    "weights": {"foundation": 0.35, "execution": 0.30, ...},
    "focus_domains": ["machine_learning", "model_training", "data_pipelines"]
}
```

**Extensibility:**
- Add new domains by creating persona templates
- No code changes to PersonaHarness
- Templates can be:
  - Built-in (`empirica/core/persona/templates/`)
  - User-defined (`.empirica/personas/custom/`)
  - Organization-specific (shared via git)

### Layer 4: Domain-Qualified Sentinels

**Sentinels are trained/qualified for specific domains or domain sets:**

```python
# Single-domain Sentinel
SecuritySentinel = SentinelOrchestrator(
    sentinel_id="security_sentinel",
    qualified_domains=["security", "authentication", "authorization"],
    managed_personas=["security_expert", "penetration_tester", "compliance_auditor"],
    orchestration_strategy="parallel_with_consensus"
)

# Multi-domain Sentinel (Full-Stack)
FullStackSentinel = SentinelOrchestrator(
    sentinel_id="fullstack_sentinel",
    qualified_domains=["security", "ux", "performance", "architecture"],
    managed_personas=["security", "ux", "performance", "architecture"],
    orchestration_strategy="weighted_by_domain"
)

# Meta-Sentinel (Orchestrator of Orchestrators)
MetaSentinel = SentinelOrchestrator(
    sentinel_id="meta_sentinel",
    qualified_domains=["*"],  # All domains
    managed_sentinels=["security_sentinel", "fullstack_sentinel"],
    orchestration_strategy="hierarchical"
)
```

**Knowledge Distillation Target:**
- Distill domain expertise → Persona templates (priors, thresholds)
- Distill orchestration patterns → Sentinel training
- Distill conflict resolution → Sentinel arbitration logic

**Sentinel Training Approaches:**

1. **Single-Domain Specialist Sentinel**
   - Trained on security domain only
   - Manages security personas (expert, pen-tester, auditor)
   - Deep expertise in security trade-offs
   - Use case: Security-critical applications

2. **Multi-Domain Generalist Sentinel**
   - Trained on common domain combinations (security + UX + performance)
   - Manages standard persona set
   - Balances competing concerns (security vs UX vs performance)
   - Use case: General application development

3. **Meta-Domain Orchestrator Sentinel**
   - Trained on orchestration patterns across all domains
   - Manages other Sentinels, not personas directly
   - Handles complex projects with many personas
   - Use case: Large-scale systems, enterprise applications

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Unified Schema Layer                       │
│  EpistemicAssessmentSchema (canonical format)               │
│  - Used by CLI, MCP, Harness, Sentinel                     │
│  - Single source of truth                                   │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┴──────────────────┐
        │                                     │
┌───────▼────────┐                   ┌────────▼────────┐
│ PersonaHarness │                   │ SentinelOrch.   │
│ (Universal)    │◄───────────────────│ (Domain-Qual.) │
│                │    manages         │                │
│ - Wraps any    │                   │ - Single domain │
│   persona      │                   │ - Multi domain  │
│ - Applies      │                   │ - Meta domain   │
│   priors       │                   │                │
└────────┬───────┘                   └────────┬────────┘
         │                                    │
         │ uses                               │ trained on
         │                                    │
┌────────▼───────┐                   ┌────────▼────────┐
│ Persona        │                   │ Knowledge       │
│ Templates      │                   │ Distillation    │
│                │                   │                │
│ - security     │                   │ - Domain exp.   │
│ - ux           │                   │ - Orchestration │
│ - performance  │                   │ - Conflict res. │
│ - ml_engineer  │                   │                │
│ - devops       │                   │                │
│ (extensible)   │                   │                │
└────────────────┘                   └─────────────────┘
```

## Implementation Plan

### Phase 1: Unified Schema (Immediate)
1. Create `empirica/core/schemas/epistemic_assessment.py`
2. Implement `EpistemicAssessmentSchema` with to/from nested dict
3. Update CLI parser to use schema
4. Update MCP tools to use schema
5. Update PersonaHarness to use schema

### Phase 2: CLI Commands (Current Work)
1. `empirica persona-create` - Create persona from template
2. `empirica persona-list` - List available personas
3. `empirica persona-validate` - Validate persona config
4. `empirica orchestrate` - Run multi-persona CASCADE
5. `empirica orchestrate-monitor` - Monitor orchestration

### Phase 3: Sentinel Implementation
1. Implement SentinelOrchestrator base class
2. Add domain qualification system
3. Implement orchestration strategies:
   - `parallel_with_consensus` - Run personas in parallel, merge insights
   - `weighted_by_domain` - Weight personas by domain relevance
   - `hierarchical` - Sentinel manages other Sentinels
4. Implement COMPOSE operation (merge persona insights)
5. Add conflict arbitration (when personas disagree)

### Phase 4: Knowledge Distillation Integration
1. Define Sentinel training data format
2. Implement distillation pipeline:
   - Input: Empirica CASCADE traces + human feedback
   - Output: Sentinel orchestration patterns
3. Train domain-specific Sentinels
4. Validate Sentinel performance

## Extensibility Model

**Add New Domain (Example: ML Engineering):**

```python
# 1. Create persona template
ML_ENGINEER_TEMPLATE = {
    "priors": {
        "engagement": 0.85,
        "know": 0.85,  # High ML knowledge
        "do": 0.90,    # Strong implementation capability
        "context": 0.75,
        "clarity": 0.80,
        "coherence": 0.75,
        "signal": 0.80,  # Data quality focus
        "density": 0.70,
        "state": 0.80,   # Model state tracking
        "change": 0.85,  # Training dynamics
        "completion": 0.05,
        "impact": 0.85,  # Performance impact
        "uncertainty": 0.30  # Some uncertainty in hyperparameters
    },
    "thresholds": {
        "uncertainty_trigger": 0.35,
        "confidence_to_proceed": 0.80,
        "signal_quality_min": 0.75  # Data quality critical
    },
    "weights": {
        "foundation": 0.35,
        "comprehension": 0.25,
        "execution": 0.30,  # Emphasize execution (training, deployment)
        "engagement": 0.10
    },
    "focus_domains": [
        "machine_learning", "deep_learning", "model_training",
        "hyperparameter_tuning", "data_pipelines", "model_deployment",
        "overfitting", "underfitting", "regularization"
    ]
}

# 2. Add to BUILTIN_TEMPLATES
BUILTIN_TEMPLATES["ml_engineer"] = ML_ENGINEER_TEMPLATE

# 3. Use immediately (no harness code changes!)
manager = PersonaManager()
ml_persona = manager.create_persona(
    persona_id="ml_engineer",
    name="ML Engineer",
    template="builtin:ml_engineer"
)

harness = PersonaHarness("ml_engineer")
result = await harness.execute_task("Train sentiment analysis model")
```

**Add Domain-Qualified Sentinel:**

```python
# Train Sentinel on ML + Data Engineering domains
MLDataSentinel = SentinelOrchestrator(
    sentinel_id="ml_data_sentinel",
    qualified_domains=["machine_learning", "data_engineering"],
    managed_personas=["ml_engineer", "data_engineer", "mlops_specialist"],
    orchestration_strategy="parallel_with_consensus",
    conflict_resolution="weighted_by_confidence"
)

# Use for ML projects
result = await MLDataSentinel.orchestrate(
    task="Build recommendation system",
    personas=["ml_engineer", "data_engineer", "mlops_specialist"]
)
```

## Answer to Your Question

**Should Sentinels be qualified in one domain or multiple?**

**It depends on use case:**

1. **Security-critical apps**: Use single-domain Security Sentinel
   - Deep expertise in security trade-offs
   - Manages security personas only
   - No compromises on security for UX

2. **General web apps**: Use multi-domain Generalist Sentinel
   - Balances security + UX + performance
   - Manages standard persona set
   - Makes practical trade-offs

3. **Enterprise systems**: Use Meta Sentinel + Domain Sentinels
   - Meta Sentinel orchestrates domain Sentinels
   - Each domain Sentinel manages its personas
   - Hierarchical decision-making

**The architecture supports all three!**

## Summary

✅ **Universal PersonaHarness** - runtime execution
✅ **Domain-Specific Personas** - expertise in templates
✅ **Domain-Qualified Sentinels** - trained for specific domains
✅ **Unified Schema** - canonical assessment format
✅ **Extensible** - add domains via templates, not code
✅ **Flexible** - single/multi/meta domain Sentinels

**Next Step:** Create the unified EpistemicAssessmentSchema, then continue with CLI commands and Sentinel implementation.
