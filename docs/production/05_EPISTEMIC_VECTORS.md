# 📊 Understanding the 13 Epistemic Vectors

A complete guide to the 13-vector epistemic system with explicit uncertainty tracking.

---

> [!IMPORTANT]

---

## Overview

Empirica assesses epistemic state across **13 vectors** organized into 5 groups:

1. **ENGAGEMENT** (Gate) - 1 vector (15% weight)
   - Collaborative intelligence quality (≥0.60 required to proceed)

2. **FOUNDATION** (35% weight) - 3 vectors
   - KNOW, DO, CONTEXT

3. **COMPREHENSION** (25% weight) - 4 vectors
   - CLARITY, COHERENCE, SIGNAL, DENSITY

4. **EXECUTION** (25% weight) - 4 vectors
   - STATE, CHANGE, COMPLETION, IMPACT

5. **UNCERTAINTY** (Meta-Epistemic) - 1 vector ⭐
   - Explicit uncertainty measurement (not included in overall confidence calculation)

---

## The 1st Dimension: ENGAGEMENT

### ENGAGEMENT (The Gate)
**Weight:** 15% of overall confidence  
**Range:** 0.0 - 1.0  
**Threshold:** 0.60 (must pass to continue)

**What it measures:**
Collaborative intelligence quality - the degree to which meaningful collaboration is occurring.

**Sub-components:**
- **Collaborative Intelligence** (0.25): AI-human synergy quality
- **Co-creative Amplification** (0.25): Mutual enhancement loop strength
- **Belief Space Management** (0.25): Shared belief coherence
- **Authentic Collaboration** (0.25): Real vs performative collaboration

**Why it's a gate:**
Low engagement (< 0.60) indicates the task needs clarification before proceeding.

**Example:**
```
Task: "Do the thing"
ENGAGEMENT: 0.35 (FAIL)
→ Action: CLARIFY (need user clarification)

Task: "Analyze authentication system for SQL injection vulnerabilities"
ENGAGEMENT: 0.85 (PASS)
→ Continue to UNCERTAINTY phase
```

---

## Foundation Vectors (35% Weight)

### 1. KNOW - Domain Knowledge
**What it measures:**
Understanding of the relevant domain, concepts, technologies, or subject matter.

**High KNOW (0.8+):**
- Deep understanding of domain
- Familiar with relevant concepts
- Know the tools and approaches
- Understand context and implications

**Low KNOW (< 0.5):**
- Unfamiliar domain
- Lack relevant knowledge
- Don't know the tools
- Missing critical context

**Example:**
```
Task: "Implement OAuth2 authentication"
KNOW: 0.85 - "Familiar with OAuth2 protocol, flow types, security considerations"

Task: "Fix the quantum entanglement algorithm"
KNOW: 0.25 - "No background in quantum computing or physics"
```

**Investigation Strategy:**
Low KNOW → Use web_search, semantic_search_qdrant, or ask user for domain context

---

### 2. DO - Execution Capability
**What it measures:**
Ability to execute the required actions, technical capability, access to necessary tools.

**High DO (0.8+):**
- Have the tools/access needed
- Technical capability present
- Can execute the steps
- Know how to implement

**Low DO (< 0.5):**
- Missing required tools
- Lack technical capability
- Can't execute steps
- Don't know implementation approach

**Example:**
```
Task: "Update the database schema"
DO: 0.90 - "Have database access, know SQL, can execute migrations"

Task: "Deploy to production Kubernetes cluster"
DO: 0.30 - "No kubectl access, don't have deployment credentials"
```

**Investigation Strategy:**
Low DO → Check workspace_scan for available tools, ask user about access/permissions

---

### 3. CONTEXT - Environmental Context
**What it measures:**
Understanding of the environment, current state, surrounding systems, constraints.

**High CONTEXT (0.8+):**
- Understand current environment
- Know system state
- Aware of constraints
- See the bigger picture

**Low CONTEXT (< 0.5):**
- Don't understand environment
- Unclear on current state
- Missing constraints
- Lack broader context

**Example:**
```
Task: "Refactor the authentication module"
CONTEXT: 0.75 - "Know the codebase structure, dependencies, test coverage"

Task: "Fix the production issue"
CONTEXT: 0.35 - "Don't know what's deployed, no access to logs, unclear system state"
```

**Investigation Strategy:**
Low CONTEXT → Use workspace_scan, read_file, check session_manager_search for history

---

## Comprehension Vectors (25% Weight)

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
Task: "Implement rate limiting with 100 req/min per user, using Redis, with exponential backoff"
CLARITY: 0.95 - "Extremely specific and clear"

Task: "Make it better"
CLARITY: 0.15 - "Completely vague"
```

**Investigation Strategy:**
Low CLARITY → **HIGHEST PRIORITY** - Use user_clarification (0.40 gain) to ask user

---

### 5. COHERENCE - Logical Coherence
**What it measures:**
Internal logical consistency of the request and approach.

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
Task: "Add user authentication to the public API that should be accessible without login"
COHERENCE: 0.25 - "Contradictory requirements"

Task: "Add OAuth2 authentication to protect user data endpoints"
COHERENCE: 0.90 - "Logically coherent"
```

**Investigation Strategy:**
Low COHERENCE → Use user_clarification to resolve contradictions

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
- Hard to extract signal

**Example:**
```
Task: "Fix the login bug where users can't authenticate after password reset"
SIGNAL: 0.90 - "Clear problem statement"

Task: "So yesterday I was thinking about the login and then I remembered that time when... [500 words]... anyway, can you check the thing?"
SIGNAL: 0.20 - "Signal buried in noise"
```

**Investigation Strategy:**
Low SIGNAL → Use goals_create to extract structured objectives

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
DENSITY: 0.35 - "Simple, manageable"

Task: "Implement OAuth2 + SAML + LDAP + MFA + SSO + biometric + hardware tokens + session management + refresh tokens + ..." [continues]
DENSITY: 0.95 - "Information overload"
```

**Investigation Strategy:**
High DENSITY → Use goals_create to break down into manageable pieces

---

## Execution Vectors (25% Weight)

### 8. STATE - Current State Understanding
**What it measures:**
Understanding of where things currently are.

**High STATE (0.8+):**
- Clear picture of current state
- Know what exists
- Understand current implementation
- See the starting point

**Low STATE (< 0.5):**
- Unclear current state
- Don't know what exists
- Missing implementation details
- Can't see starting point

**Example:**
```
Task: "Update the API to v2"
STATE: 0.85 - "Know current v1 API structure, endpoints, consumers"

Task: "Improve the system"
STATE: 0.25 - "Don't know current system state"
```

**Investigation Strategy:**
Low STATE → Use workspace_scan, read_file, bash commands to assess current state

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
CHANGE: 0.90 - "Tests provide change validation"

Task: "Modify the production database directly"
CHANGE: 0.20 - "No way to track or validate changes"
```

**Investigation Strategy:**
Low CHANGE → Ask user about version control, testing, validation approach

---

### 10. COMPLETION - Path to Completion
**What it measures:**
Visibility of the path to completion and success criteria.

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
Task: "Add rate limiting: 1) Install Redis, 2) Implement middleware, 3) Add tests, 4) Deploy"
COMPLETION: 0.95 - "Clear path to completion"

Task: "Make the app production-ready"
COMPLETION: 0.30 - "Unclear what 'production-ready' means or how to achieve it"
```

**Investigation Strategy:**
Low COMPLETION → Use goals_orchestrate to create structured completion path

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
Task: "Add caching layer with TTL and invalidation strategy"
IMPACT: 0.85 - "Can predict effects on performance, consistency, complexity"

Task: "Modify the core algorithm"
IMPACT: 0.35 - "Unclear what effects this will have system-wide"
```

**Investigation Strategy:**
Low IMPACT → Use user_clarification to understand constraints and acceptable impacts

---

## Meta-Epistemic Tracking: UNCERTAINTY ⭐

### UNCERTAINTY (Explicit Meta-Epistemic Awareness)
**Type:** Meta-epistemic (explicit tracking, not implicit in the 13-vector system)
**Range:** 0.0 - 1.0
**Interpretation:** 0.0 = certain, 1.0 = highly uncertain

**What it measures:**
Explicit awareness of epistemic limitations - "what you don't know about what you don't know."

**Why it's different:**
- **Not included in overall_confidence calculation** (meta-layer, not one of the 12 vectors)
- Tracks uncertainty ABOUT the 13-vector assessment itself
- Enables pre-flight/post-flight comparison
- Validates investigation effectiveness

**Components:**
- **Epistemic Gaps**: Known unknowns in the domain
- **Model Limitations**: Awareness of training data boundaries
- **Temporal Uncertainty**: How much could have changed since training
- **Contextual Uncertainty**: Missing situational information

**High UNCERTAINTY (0.7+):**
- Significant epistemic gaps
- Domain beyond training data
- Many unknowns present
- Investigation strongly recommended

**Low UNCERTAINTY (< 0.3):**
- Confident in assessment
- Domain well-understood
- Few unknowns
- Can proceed with confidence

**Example:**
```
Pre-investigation:
Task: "Fix the quantum entanglement algorithm"
UNCERTAINTY: 0.85 - "No background in quantum physics, many unknowns"
Action: INVESTIGATE

Post-investigation:
UNCERTAINTY: 0.30 - "Found relevant papers, understand approach now"
Δuncertainty: -0.55 (investigation was effective!)
Action: PROCEED
```

**Pre-Flight / Post-Flight Pattern:**
```python
# PRE-FLIGHT: Before investigation
assessment_pre = {
    'know': 0.35,
    'uncertainty': 0.75,  # High uncertainty
    'overall_confidence': 0.48
}

# ... investigation happens ...

# POST-FLIGHT: After investigation
assessment_post = {
    'know': 0.80,           # Knowledge increased
    'uncertainty': 0.25,    # Uncertainty reduced!
    'overall_confidence': 0.82
}

# Validate investigation was effective
delta_uncertainty = -0.50  # Reduced by 50%!
delta_knowledge = +0.45     # Knowledge increased
# ✅ Investigation was successful
```

**Dashboard Display:**
```
UNCERTAINTY: 0.85 ⚠️  [INVESTIGATE]
            ████████████░ Very High
            
After investigation:
UNCERTAINTY: 0.30 ✅  [REDUCED]
            ███░░░░░░░░░ Low
            Δ: -0.55 (effective investigation)
```

**Investigation Strategy:**
- UNCERTAINTY > 0.80 → **Always investigate** (too many unknowns)
- UNCERTAINTY 0.50-0.80 → Investigate if critical domain
- UNCERTAINTY < 0.50 → Investigation optional
- **Track Δuncertainty** to validate investigation effectiveness

---

## How Vectors Combine

### Canonical Weights
```python
overall_confidence = (
    foundation_confidence * 0.35 +      # KNOW, DO, CONTEXT
    comprehension_confidence * 0.25 +   # CLARITY, COHERENCE, SIGNAL, DENSITY
    execution_confidence * 0.25 +       # STATE, CHANGE, COMPLETION, IMPACT
    engagement * 0.15                   # ENGAGEMENT
)
```

### Group Calculations
```python
foundation_confidence = (know + do + context) / 3
comprehension_confidence = (clarity + coherence + signal + (1 - density)) / 4  # density inverted
execution_confidence = (state + change + completion + impact) / 4
```

---

## Reading Vector Patterns

### Pattern 1: Knowledge Gap
```
KNOW: 0.35 (low)
DO: 0.80 (high)
CONTEXT: 0.70 (good)
→ Strategy: External search (web_search, semantic_search)
```

### Pattern 2: Unclear Request
```
CLARITY: 0.40 (low)
KNOW: 0.75 (good)
DO: 0.80 (good)
→ Strategy: User clarification (HIGHEST PRIORITY)
```

### Pattern 3: Missing Environment Context
```
CONTEXT: 0.35 (low)
STATE: 0.40 (low)
KNOW: 0.70 (good)
→ Strategy: Environmental scanning (workspace_scan, read_file)
```

### Pattern 4: Complex Domain + Low Knowledge
```
KNOW: 0.30 (low)
CLARITY: 0.45 (low)
DENSITY: 0.85 (high - overload)
Domain: medical/legal/financial
→ Strategy: Comprehensive user information gathering
```

### Pattern 5: Ready to Proceed
```
All vectors > 0.70
ENGAGEMENT: 0.80
Overall: 0.78
→ Action: PROCEED with confidence
```

---

## Dashboard Visualization

In the tmux dashboard, all 13 vectors are shown with visual bars:

```
13-VECTOR EPISTEMIC STATE
═══════════════════════════════════════
KNOW:        0.65 ████████░░ Domain knowledge
DO:          0.75 ██████████░ Execution capability
CONTEXT:     0.58 ██████░░░░ Environmental context
CLARITY:     0.85 ████████████ Request clarity
COHERENCE:   0.80 ███████████░ Logical coherence
SIGNAL:      0.90 █████████████ Signal vs noise
DENSITY:     0.40 ████░░░░░░ Info density (low=good)
STATE:       0.70 █████████░░ Current state
CHANGE:      0.75 ██████████░ Change tracking
COMPLETION:  0.60 ███████░░░ Path to completion
IMPACT:      0.80 ███████████░ Consequence prediction
ENGAGEMENT:  0.85 ████████████ Collaborative intelligence
UNCERTAINTY: 0.45 █████░░░░░ Meta-epistemic (low=good)
───────────────────────────────────────
OVERALL:     0.72 ██████████░░ [PROCEED]
Δuncertainty: N/A (first assessment)
```

**Pre-Flight / Post-Flight Comparison:**
```
PRE-FLIGHT (Uncertainty Phase)
═══════════════════════════════════════
KNOW:        0.35 ███░░░░░░░ Low knowledge
UNCERTAINTY: 0.75 █████████░ ⚠️ HIGH
OVERALL:     0.48 █████░░░░░ [INVESTIGATE]

POST-FLIGHT (Check Phase)  
═══════════════════════════════════════
KNOW:        0.80 ███████████░ ↑ +0.45 ✅
UNCERTAINTY: 0.25 ██░░░░░░░░ ↓ -0.50 ✅
OVERALL:     0.82 ████████████ [PROCEED]

Investigation Result: EFFECTIVE ✅
```

---

## Best Practices

### For Users:
1. **Be Specific** - Improves CLARITY, SIGNAL
2. **Provide Context** - Improves CONTEXT, STATE
3. **Define Success** - Improves COMPLETION
4. **Clarify Constraints** - Improves IMPACT, COHERENCE

### For System:
1. **Prioritize User Clarification** - When CLARITY < 0.60
2. **External Search** - When KNOW < 0.55
3. **Environmental Scan** - When CONTEXT or STATE < 0.60
4. **Skip Investigation** - When all vectors > 0.70

---

## Next Reading

- **Investigation strategies:** `07_INVESTIGATION_SYSTEM.md`
- **Tool mapping:** `20_TOOL_CATALOG.md`
- **Python API:** `13_PYTHON_API.md`

---

**Questions about vectors?** → `22_FAQ.md`
