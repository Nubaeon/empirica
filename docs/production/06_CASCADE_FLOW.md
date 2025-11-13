# Cascade Flow - Phase by Phase

**Empirica v2.0 - Understanding THINK → UNCERTAINTY → INVESTIGATE → CHECK → ACT**

---

## Overview

Every Empirica cascade follows this flow:

```
THINK → UNCERTAINTY → INVESTIGATE → CHECK → ACT
  ↓         ↓            ↓           ↓       ↓
Meta-    12-vector    Fill gaps   Verify   Final
prompt   assessment   (optional)  ready   decision
```

**Duration:** 5-30 seconds depending on investigation needs

---

## Phase 1: THINK

**Purpose:** Generate assessment prompt for self-assessment

**What Happens:**
1. Receives task and context
2. Classifies domain (code_analysis, security, etc.)
3. Generates assessment prompt asking AI to assess itself
4. Activates Bayesian Guardian if precision-critical domain

**Output:**
```python
{
    'assessment_prompt': "Assess your epistemic state for: [task]...",
    'domain': 'code_analysis',
    'bayesian_activated': True
}
```

**Duration:** < 1 second

---

## Phase 2: UNCERTAINTY

**Purpose:** Measure 12-vector epistemic state

**What Happens:**
1. AI receives assessment prompt
2. Performs genuine self-assessment (no heuristics)
3. Scores 13 epistemic vectors (0.0-1.0)
4. Checks ENGAGEMENT gate (≥0.60)
5. Applies canonical weights (35/25/25/15)
6. Calculates overall confidence
7. Recommends action

**The 12 Vectors:**
- **GATE:** ENGAGEMENT (≥0.60 required)
- **TIER 0 (35%):** KNOW, DO, CONTEXT
- **TIER 1 (25%):** CLARITY, COHERENCE, SIGNAL, DENSITY
- **TIER 2 (25%):** STATE, CHANGE, COMPLETION, IMPACT

**Output:**
```python
{
    'assessment': EpistemicAssessment,
    'overall_confidence': 0.65,
    'engagement_gate_passed': True,
    'recommended_action': 'investigate',
    'gaps_identified': ['know', 'context']
}
```

**Duration:** 2-5 seconds (LLM call)

---

## Phase 3: INVESTIGATE (Optional)

**Purpose:** Fill knowledge gaps through strategic investigation

**When It Runs:**
- Overall confidence < threshold (default: 0.70)
- ENGAGEMENT gate passed (≥0.60)
- No critical flags (RESET/STOP not needed)
- Improvable gaps exist

**When It Skips:**
- Confidence already met
- ENGAGEMENT gate failed
- Critical flags present
- No improvable gaps

**What Happens:**
1. Identify gaps (vectors < 0.85)
2. Recommend tools strategically
3. Execute investigation rounds (max 3)
4. Re-assess after each round
5. Update confidence

**Strategic Patterns:**
```
Low KNOW → documentation search, codebase analysis
Low CLARITY → user clarification (highest gain: 0.40-0.45)
Low CONTEXT → workspace scanning, web research
Low DO/CHANGE → test simulation, impact analysis
```

**Output:**
```python
{
    'rounds': 2,
    'tools_used': ['documentation_search', 'workspace_scan'],
    'confidence_gain': 0.15,  # 0.65 → 0.80
    'final_confidence': 0.80
}
```

**Duration:** 5-15 seconds per round (varies by tools)

---

## Phase 4: CHECK

**Purpose:** Verify readiness to act

**What Happens:**
1. **Bayesian Discrepancy Detection:**
   - Compare intuitive assessment vs evidence-based beliefs
   - Detect overconfidence (intuition > evidence)
   - Detect underconfidence (intuition < evidence)

2. **Drift Monitoring:**
   - Check for sycophancy drift (delegate weight increasing)
   - Check for tension avoidance (acknowledging tensions less)
   - Alert if behavioral patterns detected

3. **Generate Execution Guidance:**
   - What to do next
   - What to watch out for
   - Confidence in decision

**Output:**
```python
{
    'bayesian_active': True,
    'discrepancies': [],  # or [{type, vector, gap, severity}]
    'drift_detected': False,
    'execution_guidance': [
        "Proceed with authentication analysis",
        "Focus on SQL injection patterns",
        "Review password hashing implementation"
    ]
}
```

**Duration:** < 1 second

---

## Phase 5: ACT

**Purpose:** Make final decision

**What Happens:**
1. Review all phase results
2. Make final action decision
3. Calculate final confidence
4. Provide reasoning and guidance
5. Log to Reflex Frame
6. Update session database (if enabled)

**Possible Actions:**
- **PROCEED** - Confidence met, ready to act
- **INVESTIGATE** - Need more information
- **CLARIFY** - Task unclear, need user input
- **RESET** - Task incoherent or cognitive overload
- **STOP** - Cannot proceed (fundamental issue)

**Output:**
```python
{
    'action': 'proceed',
    'confidence': 0.82,
    'rationale': "Sufficient understanding achieved...",
    'execution_guidance': [...],
    'vector_summary': {
        'foundation': 0.78,
        'comprehension': 0.85,
        'execution': 0.83
    }
}
```

**Duration:** < 1 second

---

## Complete Example Flow

```python
import asyncio
from empirica.bootstraps import ExtendedMetacognitiveBootstrap

async def example():
    bootstrap = ExtendedMetacognitiveBootstrap(level="2")
    components = bootstrap.bootstrap()
    cascade = components['canonical_cascade']
    
    result = await cascade.run_epistemic_cascade(
        task="Refactor the authentication module",
        context={'cwd': '/project', 'urgency': 'high'}
    )
    
    # Check each phase
    print(f"THINK: Domain = {result['phases']['think']['domain']}")
    print(f"UNCERTAINTY: Confidence = {result['phases']['uncertainty']['assessment'].overall_confidence:.2f}")
    print(f"INVESTIGATE: Rounds = {result['phases']['investigate']['rounds']}")
    print(f"CHECK: Discrepancies = {len(result['phases']['check']['bayesian_discrepancies'])}")
    print(f"ACT: Action = {result['action']}, Final confidence = {result['confidence']:.2f}")

asyncio.run(example())
```

---

## Decision Flow Logic

```
START
  ↓
THINK (classify domain)
  ↓
UNCERTAINTY (assess 12 vectors)
  ↓
ENGAGEMENT >= 0.60? → NO → ACT: clarify
  ↓ YES
Critical flags? → YES → ACT: reset/stop
  ↓ NO
Confidence >= threshold? → YES → CHECK → ACT: proceed
  ↓ NO
INVESTIGATE (improve confidence)
  ↓
CHECK (verify + detect discrepancies/drift)
  ↓
ACT (final decision)
```

---

## Timing Breakdown

**Typical cascade timing:**
- THINK: < 1s
- UNCERTAINTY: 2-5s (LLM call)
- INVESTIGATE: 0-30s (0-3 rounds × 5-10s each)
- CHECK: < 1s
- ACT: < 1s

**Total:** 3-37 seconds depending on investigation needs

**Fast path (high confidence):** ~3-6 seconds
**Normal path (1-2 rounds):** ~10-20 seconds
**Deep investigation (3 rounds):** ~25-37 seconds

---

## Reflex Frame Logging

Each phase logs a Reflex Frame:

```
.empirica_reflex_logs/cascade/YYYY-MM-DD/
├── cascade_abc123_think_TIMESTAMP.json
├── cascade_abc123_uncertainty_TIMESTAMP.json
├── cascade_abc123_investigate_TIMESTAMP.json
├── cascade_abc123_check_TIMESTAMP.json
└── cascade_abc123_act_TIMESTAMP.json
```

**Purpose:** Temporal separation prevents self-referential recursion

---

## Next Steps

- **Investigation Details:** [07_INVESTIGATION_SYSTEM.md](07_INVESTIGATION_SYSTEM.md)
- **API Usage:** [13_PYTHON_API.md](13_PYTHON_API.md)
- **Troubleshooting:** [21_TROUBLESHOOTING.md](21_TROUBLESHOOTING.md)

---

**Understanding the flow helps debug issues and optimize performance!** 🚀
