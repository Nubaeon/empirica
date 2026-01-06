# 📊 Understanding the 13 Epistemic Vectors

**A complete guide to Empirica's 13-vector epistemic self-awareness system**

---

## Overview

Empirica measures epistemic state across **13 vectors** organized into **4 tiers**:

| Tier | Vectors | Purpose | Weight |
|------|---------|---------|--------|
| **TIER 0** | ENGAGEMENT | Gate (must ≥ 0.6 to proceed) | 15% |
| **TIER 1** | KNOW, DO, CONTEXT | Foundation knowledge | 35% |
| **TIER 2** | CLARITY, COHERENCE, SIGNAL, DENSITY | Comprehension | 25% |
| **TIER 3** | STATE, CHANGE, COMPLETION, IMPACT | Execution capability | 25% |
| **META** | UNCERTAINTY | Explicit unknown tracking | (separate) |

**Key Principle:** Rate what you **ACTUALLY know right now**, not what you hope to figure out.

---

## TIER 0: ENGAGEMENT (The Gate)

### ENGAGEMENT
**Weight:** 15% of overall confidence  
**Range:** 0.0 - 1.0  
**Threshold:** ≥ 0.6 (must pass to proceed)

**What it measures:**
The quality of collaborative intelligence - is meaningful work possible?

**High ENGAGEMENT (0.7+):**
- Clear task definition
- Realistic scope
- Collaborative context present
- Can make meaningful progress

**Low ENGAGEMENT (< 0.6):**
- Vague or unclear task
- Unrealistic expectations
- Missing critical context
- Cannot proceed effectively

**Example:**
```
Task: "Do the thing"
ENGAGEMENT: 0.35 → STOP, need clarification

Task: "Analyze auth.py for SQL injection vulnerabilities"
ENGAGEMENT: 0.85 → PROCEED
```

**Why it's a gate:**
Low engagement means the task itself needs clarification before any work can begin.

---

## TIER 1: FOUNDATION (35% Weight)

### 1. KNOW - Domain Knowledge
**What it measures:**
Understanding of relevant domain, concepts, technologies, or subject matter.

**High KNOW (0.8+):**
- Deep domain understanding
- Familiar with concepts
- Know tools and approaches
- Understand implications

**Low KNOW (< 0.5):**
- Unfamiliar domain
- Lack relevant knowledge
- Don't know the tools
- Missing context

**Example:**
```
Task: "Implement OAuth2 authentication"
KNOW: 0.85 → "Familiar with OAuth2 flows, security considerations"

Task: "Fix quantum entanglement algorithm"
KNOW: 0.25 → "No quantum computing background"
```

**Investigation Strategy:**
Low KNOW → Use web_search, documentation, or ask user for domain context

---

### 2. DO - Execution Capability
**What it measures:**
Ability to execute required actions - technical capability and tool access.

**High DO (0.8+):**
- Have necessary tools/access
- Technical capability present
- Can execute the steps
- Know implementation approach

**Low DO (< 0.5):**
- Missing required tools
- Lack technical capability
- Can't execute steps
- Unknown implementation path

**Example:**
```
Task: "Update database schema"
DO: 0.90 → "Have DB access, know SQL, can run migrations"

Task: "Deploy to production K8s cluster"
DO: 0.30 → "No kubectl access, no credentials"
```

**Investigation Strategy:**
Low DO → Check available tools, ask user about access/permissions

---

### 3. CONTEXT - Environmental Context
**What it measures:**
Understanding of environment, current state, surrounding systems, constraints.

**High CONTEXT (0.8+):**
- Understand environment
- Know system state
- Aware of constraints
- See bigger picture

**Low CONTEXT (< 0.5):**
- Don't understand environment
- Unclear on current state
- Missing constraints
- Lack broader context

**Example:**
```
Task: "Refactor authentication module"
CONTEXT: 0.75 → "Know codebase structure, dependencies, tests"

Task: "Fix production issue"
CONTEXT: 0.35 → "Don't know what's deployed, no log access"
```

**Investigation Strategy:**
Low CONTEXT → Use workspace scanning, read files, check git history

---

## TIER 2: COMPREHENSION (25% Weight)

### 4. CLARITY - Request Clarity
**What it measures:**
How clear and well-defined the request is.

**High CLARITY (0.8+):**
- Request is specific
- Goals are clear
- Requirements defined
- Success criteria known

**Low CLARITY (< 0.5):**
- Vague request
- Unclear goals
- Ambiguous requirements
- Success criteria undefined

**Example:**
```
Task: "Implement rate limiting: 100 req/min per user, Redis backend, exponential backoff"
CLARITY: 0.95 → "Extremely specific"

Task: "Make it better"
CLARITY: 0.15 → "Completely vague"
```

**Investigation Strategy:**
Low CLARITY → **HIGHEST PRIORITY** - Ask user for clarification

---

### 5. COHERENCE - Logical Coherence
**What it measures:**
Internal logical consistency of request and approach.

**High COHERENCE (0.8+):**
- Request makes logical sense
- Parts fit together
- No contradictions
- Approach is sound

**Low COHERENCE (< 0.5):**
- Request has contradictions
- Parts don't fit
- Logical issues
- Approach unclear

**Example:**
```
Task: "Add authentication to public API that should be accessible without login"
COHERENCE: 0.25 → "Contradictory requirements"

Task: "Add OAuth2 to protect user data endpoints"
COHERENCE: 0.90 → "Logically coherent"
```

**Investigation Strategy:**
Low COHERENCE → Ask user to resolve contradictions

---

### 6. SIGNAL - Signal vs Noise
**What it measures:**
Ratio of useful information to irrelevant details.

**High SIGNAL (0.8+):**
- Clear signal
- Relevant information
- Focused request
- Minimal noise

**Low SIGNAL (< 0.5):**
- Lost in noise
- Too much irrelevant info
- Unfocused request
- Hard to extract meaning

**Example:**
```
Task: "Fix login bug where users can't authenticate after password reset"
SIGNAL: 0.90 → "Clear problem statement"

Task: "So yesterday I was thinking... [500 words]... can you check the thing?"
SIGNAL: 0.20 → "Signal buried in noise"
```

**Investigation Strategy:**
Low SIGNAL → Use goals to extract structured objectives

---

### 7. DENSITY - Information Density
**What it measures:**
How much information is packed into the request. **Note:** HIGH density is problematic (inverted vector).

**Low DENSITY (0.3-0.5) - GOOD:**
- Manageable information load
- Not overwhelming
- Can process comfortably
- Right amount of detail

**High DENSITY (0.8+) - BAD:**
- Information overload
- Too much at once
- Overwhelming complexity
- Cognitive saturation

**Example:**
```
Task: "Implement user authentication"
DENSITY: 0.35 → "Simple, manageable"

Task: "Implement OAuth2 + SAML + LDAP + MFA + SSO + biometric + hardware tokens + ..."
DENSITY: 0.95 → "Information overload"
```

**Investigation Strategy:**
High DENSITY → Break down into manageable pieces using goals

---

## TIER 3: EXECUTION (25% Weight)

### 8. STATE - Current State Understanding
**What it measures:**
Understanding of where things currently are.

**High STATE (0.8+):**
- Clear picture of current state
- Know what exists
- Understand implementation
- See starting point

**Low STATE (< 0.5):**
- Unclear current state
- Don't know what exists
- Missing implementation details
- Can't see starting point

**Example:**
```
Task: "Update API to v2"
STATE: 0.85 → "Know current v1 structure, endpoints, consumers"

Task: "Improve the system"
STATE: 0.25 → "Don't know current system state"
```

**Investigation Strategy:**
Low STATE → Scan workspace, read files, check current implementation

---

### 9. CHANGE - Change Tracking
**What it measures:**
Ability to track and manage changes.

**High CHANGE (0.8+):**
- Can track progress
- See what changes
- Monitor evolution
- Detect regressions

**Low CHANGE (< 0.5):**
- Can't track changes
- No change visibility
- Can't monitor progress
- Can't detect issues

**Example:**
```
Task: "Refactor with tests"
CHANGE: 0.90 → "Tests provide change validation"

Task: "Modify production DB directly"
CHANGE: 0.20 → "No way to track/validate changes"
```

**Investigation Strategy:**
Low CHANGE → Ask about version control, testing, validation

---

### 10. COMPLETION - Path to Completion
**What it measures:**
Visibility of path to completion and success criteria.

**High COMPLETION (0.8+):**
- Clear path to done
- Know the steps
- Can measure progress
- Success criteria clear

**Low COMPLETION (< 0.5):**
- Unclear path forward
- Don't know steps
- Can't measure progress
- Success criteria vague

**Example:**
```
Task: "Add rate limiting: 1) Redis, 2) Middleware, 3) Tests, 4) Deploy"
COMPLETION: 0.95 → "Clear path to completion"

Task: "Make app production-ready"
COMPLETION: 0.30 → "Unclear what this means or how to achieve"
```

**Investigation Strategy:**
Low COMPLETION → Create structured goals with subtasks

---

### 11. IMPACT - Consequence Prediction
**What it measures:**
Ability to predict consequences and understand impact.

**High IMPACT (0.8+):**
- Understand consequences
- Can predict effects
- Know risks
- See implications

**Low IMPACT (< 0.5):**
- Can't predict consequences
- Unknown effects
- Risks unclear
- Missing implications

**Example:**
```
Task: "Add caching with TTL and invalidation"
IMPACT: 0.85 → "Can predict effects on performance, consistency"

Task: "Modify core algorithm"
IMPACT: 0.35 → "Unclear system-wide effects"
```

**Investigation Strategy:**
Low IMPACT → Ask user about constraints and acceptable impacts

---

## META: UNCERTAINTY (Explicit Unknown Tracking)

### UNCERTAINTY ⭐
**Type:** Meta-epistemic (explicit tracking, separate from 13 vectors)  
**Range:** 0.0 - 1.0  
**Interpretation:** 0.0 = certain, 1.0 = highly uncertain

**What it measures:**
Explicit awareness of epistemic limitations - "what you don't know about what you don't know."

**Why it's different:**
- **Not included in overall_confidence calculation** (meta-layer)
- Tracks uncertainty ABOUT the 13-vector assessment itself
- Enables PREFLIGHT/POSTFLIGHT comparison
- Validates investigation effectiveness

**Components:**
- **Epistemic Gaps:** Known unknowns in domain
- **Model Limitations:** Awareness of training boundaries
- **Temporal Uncertainty:** How much could have changed
- **Contextual Uncertainty:** Missing situational info

**High UNCERTAINTY (0.7+):**
- Significant epistemic gaps
- Domain beyond training
- Many unknowns
- Investigation strongly recommended

**Low UNCERTAINTY (< 0.3):**
- Confident in assessment
- Domain well-understood
- Few unknowns
- Can proceed confidently

**Example:**
```
PREFLIGHT:
Task: "Fix quantum entanglement algorithm"
UNCERTAINTY: 0.85 → "No quantum physics background, many unknowns"
Action: INVESTIGATE

POSTFLIGHT:
UNCERTAINTY: 0.30 → "Found papers, understand approach now"
Δuncertainty: -0.55 (investigation was effective!)
Action: PROCEED
```

**PREFLIGHT/POSTFLIGHT Pattern:**
```python
# PREFLIGHT: Before investigation
{
    'know': 0.35,
    'uncertainty': 0.75,  # High uncertainty
    'overall_confidence': 0.48
}

# ... investigation happens via CHECK phases ...

# POSTFLIGHT: After investigation
{
    'know': 0.80,           # Knowledge increased
    'uncertainty': 0.25,    # Uncertainty reduced!
    'overall_confidence': 0.82
}

# Validate investigation was effective
delta_uncertainty = -0.50  # Reduced by 50%!
delta_knowledge = +0.45    # Knowledge increased
# ✅ Investigation was successful
```

**Investigation Strategy:**
- UNCERTAINTY > 0.80 → **Always investigate** (too many unknowns)
- UNCERTAINTY 0.50-0.80 → Investigate if critical domain
- UNCERTAINTY < 0.50 → Investigation optional
- **Track Δuncertainty** to validate investigation effectiveness

---

## How Vectors Combine

### Overall Confidence Formula
```python
overall_confidence = (
    engagement * 0.15 +                    # TIER 0 (gate)
    foundation_confidence * 0.35 +         # TIER 1 (KNOW, DO, CONTEXT)
    comprehension_confidence * 0.25 +      # TIER 2 (CLARITY, COHERENCE, SIGNAL, DENSITY)
    execution_confidence * 0.25            # TIER 3 (STATE, CHANGE, COMPLETION, IMPACT)
)

# UNCERTAINTY is tracked separately (meta-layer)
```

### Tier Calculations
```python
# TIER 1: Foundation (equal weights)
foundation = (know + do + context) / 3

# TIER 2: Comprehension (DENSITY is inverted!)
comprehension = (clarity + coherence + signal + (1 - density)) / 4

# TIER 3: Execution (equal weights)
execution = (state + change + completion + impact) / 4
```

**Important:** DENSITY is inverted - high density is BAD (information overload).

---

## Decision Thresholds

### ENGAGEMENT Gate
```
ENGAGEMENT < 0.60 → STOP (need clarification)
ENGAGEMENT ≥ 0.60 → PROCEED to work
```

### CHECK Phase Decision
```
Overall Confidence < 0.70 → INVESTIGATE MORE
Overall Confidence ≥ 0.70 → PROCEED WITH WORK
```

### UNCERTAINTY Guidelines
```
UNCERTAINTY > 0.80 → Must investigate
UNCERTAINTY 0.50-0.80 → Should investigate if critical
UNCERTAINTY < 0.50 → Can proceed
```

---

## Real-World Example: OAuth2 Implementation

### PREFLIGHT Assessment
```python
{
    "engagement": 0.85,  # Clear task
    "foundation": {
        "know": 0.75,    # Familiar with OAuth2
        "do": 0.80,      # Have tools/access
        "context": 0.60   # Some codebase knowledge
    },
    "comprehension": {
        "clarity": 0.90,     # Well-defined task
        "coherence": 0.85,   # Logically sound
        "signal": 0.80,      # Clear requirements
        "density": 0.40      # Manageable complexity (low is good!)
    },
    "execution": {
        "state": 0.50,       # Need to explore current auth
        "change": 0.70,      # Git + tests available
        "completion": 0.65,  # Rough path visible
        "impact": 0.55       # Some risks unclear
    },
    "uncertainty": 0.55  # Moderate uncertainty
}

# Overall Confidence: 0.71 → PROCEED (but investigate low vectors)
```

### After Investigation (POSTFLIGHT)
```python
{
    "engagement": 0.90,
    "foundation": {
        "know": 0.85,    # Learned specifics
        "do": 0.85,
        "context": 0.80   # Explored codebase
    },
    "comprehension": {
        "clarity": 0.95,
        "coherence": 0.90,
        "signal": 0.85,
        "density": 0.35   # Still manageable
    },
    "execution": {
        "state": 0.85,       # Mapped current system
        "change": 0.80,
        "completion": 0.90,  # Clear implementation path
        "impact": 0.80       # Understood risks
    },
    "uncertainty": 0.25  # Low uncertainty
}

# Overall Confidence: 0.85 → HIGH CONFIDENCE
# Δuncertainty: -0.30 (investigation effective!)
```

---

## Investigation Strategies by Vector

| Low Vector | Investigation Strategy | Tools/Actions |
|------------|------------------------|---------------|
| **ENGAGEMENT** | Clarify task | Ask user specific questions |
| **KNOW** | Learn domain | web_search, documentation, ask user |
| **DO** | Check capabilities | Verify tools, check access |
| **CONTEXT** | Explore environment | Scan workspace, read files, check git |
| **CLARITY** | Get specifics | Ask user for requirements |
| **COHERENCE** | Resolve contradictions | Ask user to clarify |
| **SIGNAL** | Extract objectives | Create structured goals |
| **DENSITY** | Break down | Create goals + subtasks |
| **STATE** | Map current | Read code, check DB, explore |
| **CHANGE** | Setup tracking | Verify git, tests, validation |
| **COMPLETION** | Define path | Create goals with success criteria |
| **IMPACT** | Understand risks | Ask about constraints, acceptable impacts |
| **UNCERTAINTY** | Investigate unknowns | Target investigation at knowledge gaps |

---

## Common Patterns

### Pattern 1: "I Don't Know This Domain"
```
KNOW: 0.30 (low)
UNCERTAINTY: 0.80 (high)
→ INVESTIGATE: web_search, ask user for context
```

### Pattern 2: "Vague Request"
```
CLARITY: 0.25 (low)
COHERENCE: 0.40 (low)
→ ASK USER: specific questions to clarify
```

### Pattern 3: "Don't Know Current State"
```
STATE: 0.30 (low)
CONTEXT: 0.35 (low)
→ EXPLORE: scan workspace, read files, check git
```

### Pattern 4: "Information Overload"
```
DENSITY: 0.90 (high - bad!)
COMPLETION: 0.30 (low)
→ BREAK DOWN: create goals + subtasks
```

### Pattern 5: "Can't Predict Impact"
```
IMPACT: 0.35 (low)
UNCERTAINTY: 0.70 (high)
→ ASK USER: constraints, acceptable impacts, risks
```

---

## Calibration Tips

### Be Honest About What You Know
- ❌ "I could probably figure this out" → KNOW: 0.80
- ✅ "I don't know this domain" → KNOW: 0.30

### Rate Current State, Not Future Hope
- ❌ "After investigation, I'll know" → KNOW: 0.70
- ✅ "Right now, I don't know" → KNOW: 0.30

### High Uncertainty is GOOD
- ❌ Hiding uncertainty to seem confident
- ✅ Honestly reporting high uncertainty triggers investigation

### Use POSTFLIGHT to Validate
- Track Δuncertainty to measure learning
- If uncertainty didn't decrease, investigation was ineffective
- Calibrate future assessments based on actual learning

---

## Quick Reference Card

```
TIER 0 (Gate, 15%):
├─ ENGAGEMENT (≥0.6 to proceed)

TIER 1 (Foundation, 35%):
├─ KNOW (domain knowledge)
├─ DO (execution capability)
└─ CONTEXT (environmental understanding)

TIER 2 (Comprehension, 25%):
├─ CLARITY (request specificity)
├─ COHERENCE (logical consistency)
├─ SIGNAL (useful vs noise)
└─ DENSITY (info load, inverted!)

TIER 3 (Execution, 25%):
├─ STATE (current understanding)
├─ CHANGE (tracking capability)
├─ COMPLETION (path visibility)
└─ IMPACT (consequence prediction)

META (Separate):
└─ UNCERTAINTY (explicit unknown tracking)

Thresholds:
• ENGAGEMENT < 0.6 → STOP
• Confidence < 0.7 → INVESTIGATE
• UNCERTAINTY > 0.8 → MUST INVESTIGATE
```

---

## Next Steps

- See [02_QUICKSTART_CLI.md](02_QUICKSTART_CLI.md) for using vectors in practice
- See [07_CASCADE_WORKFLOW.md](07_CASCADE_WORKFLOW.md) for PREFLIGHT→CHECK→POSTFLIGHT (to be created)
- See [EMPIRICA_EXPLAINED_SIMPLE.md](EMPIRICA_EXPLAINED_SIMPLE.md) for system overview

---

**Remember:** Epistemic transparency > task completion speed. High uncertainty is a signal to investigate, not hide!
