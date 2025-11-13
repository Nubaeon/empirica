# 🧮 Bayesian Guardian - Evidence-Based Belief Tracking

Complete guide to Empirica's real-time evidence tracking system.

---

## Overview

The Bayesian Guardian tracks beliefs about epistemic vectors using evidence from actual tool execution, detecting when intuition diverges from accumulated evidence.

### Key Features:
- Real-time belief updates from tool execution
- Overconfidence/underconfidence detection
- Selective activation (precision-critical domains)
- Variance tracking (quantifying uncertainty)
- Discrepancy alerts in CHECK phase

---

## How It Works

### 1. Initialize (UNCERTAINTY Phase)
```python
# Domain classification
domain = DomainClassifier.classify_domain(task, context)

# Activate for precision-critical domains
if should_activate:
    bayesian_tracker.activate(f"Domain: {domain}")
    
    # Initialize beliefs from assessment
    initial_beliefs = {
        'know': assessment.know.score,
        'do': assessment.do.score,
        'context': assessment.context.score,
        # ... all vectors
    }
    
    bayesian_tracker.initialize_beliefs(context_key, initial_beliefs)
```

### 2. Update (During Investigation)
```python
# LLM executes a tool and reports back
evidence = Evidence(
    outcome=True,           # Tool succeeded
    strength=0.8,          # Strong evidence
    timestamp=time.time(),
    source='web_search',
    vector_addressed='know'
)

# Bayesian updates belief
updated_belief = bayesian_tracker.update_belief(belief_key, evidence)
# KNOW: 0.45 → 0.62 (evidence-based update)
```

### 3. Detect Discrepancies (CHECK Phase)
```python
# Compare intuitive vs evidence-based beliefs
intuitive_beliefs = {
    'know': 0.70,  # What you think
    'do': 0.80
}

discrepancies = bayesian_tracker.detect_discrepancies(
    context_key,
    intuitive_beliefs
)

# If evidence shows know should be 0.50:
# → Overconfidence detected (gap: 0.20)
```

---

## When Bayesian Activates

### Precision-Critical Domains:
- **Medical:** Patient care, drug interactions, diagnosis
- **Legal:** Compliance, contracts, regulations
- **Financial:** Trading, risk assessment, compliance
- **Security:** Vulnerabilities, threat analysis, access control
- **Safety:** Critical systems, life safety, hazards

### Other Triggers:
- Low clarity (< 0.50) - Confusion needs evidence tracking
- Multiple discrepancies detected - Pattern of miscalibration
- User request - Explicit activation

### When It Stays Dormant:
- **Creative tasks:** Design, writing, brainstorming
- **High confidence:** Overall confidence > 0.80
- **Simple tasks:** Well-understood, straightforward

---

## Example Workflows

### Example 1: Medical Domain

```python
Task: "Analyze patient medication interactions"
Domain: medical (precision-critical)

# UNCERTAINTY Phase
Bayesian activates: "Domain: medical"
Initial beliefs:
  KNOW: 0.45 (limited medical knowledge)
  CLARITY: 0.50 (medical terminology unclear)

# INVESTIGATE Phase
LLM uses web_search to find drug interaction data
Reports back: success=True, strength=0.8

# Bayesian updates
update_from_tool_execution(
    tool_name='web_search',
    success=True,
    vector_addressed='know',
    strength=0.8
)
# KNOW belief: 0.45 → 0.62

# CHECK Phase
Intuitive assessment: KNOW = 0.70 (LLM feels more confident)
Bayesian belief: KNOW = 0.62 (evidence suggests caution)
→ Overconfidence detected (gap: 0.08)

Warning: "You may be overconfident about 'know'"
```

### Example 2: Security Analysis

```python
Task: "Analyze authentication system for vulnerabilities"
Domain: security_review (precision-critical)

# Bayesian activates
Initial: KNOW: 0.55, CONTEXT: 0.50

# Investigation
Tool 1: workspace_scan → success → CONTEXT: 0.50 → 0.62
Tool 2: read_file (auth.py) → success → KNOW: 0.55 → 0.68
Tool 3: web_search (CVE database) → partial → KNOW: 0.68 → 0.72

# CHECK Phase
Intuitive: KNOW: 0.75, CONTEXT: 0.70
Bayesian: KNOW: 0.72, CONTEXT: 0.62
→ Minor overconfidence (within tolerance)
→ "Beliefs reasonably aligned with evidence"
```

### Example 3: Creative Task (Dormant)

```python
Task: "Design a beautiful logo"
Domain: creative_flow

# Bayesian stays dormant
Reason: "Creative task - preserve flow state"

# No evidence tracking needed
# LLM free to explore creatively
```

---

## Belief Update Formula

### Simplified Bayesian Update:

```python
# Positive evidence (success=True)
update = strength * UPDATE_STRENGTH  # 0.3
new_mean = old_mean + (1.0 - old_mean) * update

# Negative evidence (success=False)
update = strength * UPDATE_STRENGTH
new_mean = old_mean - old_mean * update

# Variance reduction (more evidence = more certain)
new_variance = old_variance * (1.0 - VARIANCE_REDUCTION_RATE * strength)
```

### Example:
```python
Initial: mean=0.45, variance=0.30
Evidence: success=True, strength=0.8

Update: 0.8 * 0.3 = 0.24
new_mean = 0.45 + (1.0 - 0.45) * 0.24 = 0.45 + 0.132 = 0.582
new_variance = 0.30 * (1.0 - 0.2 * 0.8) = 0.30 * 0.84 = 0.252

Result: mean=0.58, variance=0.25 (more certain)
```

---

## Discrepancy Detection

### Types of Discrepancies:

#### 1. Overconfidence
```python
Intuitive belief: 0.75
Bayesian belief: 0.55
Gap: 0.20
Severity: HIGH

Warning: "You may be overconfident about 'know'"
Guidance: "Evidence suggests lower confidence"
```

#### 2. Underconfidence
```python
Intuitive belief: 0.55
Bayesian belief: 0.75
Gap: 0.20
Severity: HIGH

Guidance: "You may be underconfident - evidence supports higher confidence"
```

### Threshold:
Discrepancy detected when gap > 2 * standard_deviation

```python
std = sqrt(variance)
threshold = std * 2.0

if abs(intuitive - bayesian) > threshold:
    # Discrepancy detected
```

---

## Integration with Investigation

### Reporting Tool Results:

```python
# LLM decides to investigate
result = await cascade.run_epistemic_cascade(task, context)

if result['action'] == 'investigate':
    # See suggested tools
    suggestions = result['investigation_guidance']['suggestions']
    
    # LLM chooses and executes tool
    tool_result = llm_execute_tool('web_search', query)
    
    # Report back to Bayesian
    cascade.update_from_tool_execution(
        tool_name='web_search',
        success=tool_result.success,
        vector_addressed='know',
        strength=0.7 if tool_result.quality == 'good' else 0.4
    )
    
    # Re-run cascade with updated beliefs
    final_result = await cascade.run_epistemic_cascade(task, context)
```

---

## Configuration

### Enable/Disable:
```python
cascade = CanonicalEpistemicCascade(
    enable_bayesian=True  # Default
)
```

### Custom Parameters:
```python
# In bayesian_belief_tracker.py
UPDATE_STRENGTH = 0.3           # How much evidence affects belief
VARIANCE_REDUCTION_RATE = 0.2   # How fast variance reduces
MIN_VARIANCE = 0.05             # Minimum uncertainty
```

---

## Dashboard Display

When Bayesian is active, the dashboard shows:

```
CHECK PHASE
═══════════════════════════════════════
Readiness: proceed
Confidence: 0.72

🧮 Bayesian Guardian: ACTIVE
   Domain: security_review
   
⚠️  Detected 2 discrepancies:
   • OVERCONFIDENCE: know
     Intuitive: 0.75 | Evidence: 0.62
     Gap: 0.13 (severity: 0.65)
   
   • OVERCONFIDENCE: context
     Intuitive: 0.70 | Evidence: 0.58
     Gap: 0.12 (severity: 0.60)

Guidance: Evidence suggests lower confidence
than intuitive assessment. Proceed with caution.
```

---

## Best Practices

### 1. Report Accurate Tool Results
```python
# ✅ Good
cascade.update_from_tool_execution(
    tool_name='web_search',
    success=True,              # Actually succeeded
    vector_addressed='know',
    strength=0.8              # Strong evidence
)

# ❌ Bad
# Always reporting success=True regardless of actual outcome
```

### 2. Choose Appropriate Strength
```python
# Strong evidence (0.7-0.9)
- Official documentation found
- Clear answer obtained
- High-quality source

# Medium evidence (0.5-0.7)
- Partial answer
- Multiple sources needed
- Some uncertainty

# Weak evidence (0.3-0.5)
- Unclear results
- Low confidence in source
- Contradictory information
```

### 3. Respect Dormancy
Don't force Bayesian activation for creative tasks:
```python
if domain == 'creative_flow':
    # Let it stay dormant
    pass
```

### 4. Review Discrepancies
When discrepancies detected:
- Read the guidance
- Consider if overconfident
- Gather more evidence if needed
- Don't blindly override Bayesian

---

## Persistence

Bayesian state is saved:
```
.empirica_beliefs/
├── bayesian_state.json
└── evidence_history.json
```

Load previous state:
```python
bayesian_tracker.load_state()
```

---

## Troubleshooting

### Bayesian Not Activating?
- Check domain classification
- Verify clarity scores
- May be correctly dormant for creative tasks

### Too Many Discrepancies?
- Review tool result reporting
- Check evidence strength values
- May indicate genuine overconfidence

### Beliefs Not Updating?
- Ensure `update_from_tool_execution()` called
- Check Bayesian is active
- Verify correct vector_addressed

---

## Next Steps

- Understanding vectors: `05_EPISTEMIC_VECTORS.md`
- Investigation system: `07_INVESTIGATION_SYSTEM.md`
- Python API: `13_PYTHON_API.md`

