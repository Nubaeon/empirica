# 📊 Drift Monitor - Behavioral Integrity Monitoring

Complete guide to detecting sycophancy and tension avoidance.

---

## Overview

The Drift Monitor tracks behavioral patterns over time to detect:
1. **Sycophancy Drift** - Becoming too agreeable
2. **Tension Avoidance** - Avoiding conflicts and disagreements

### Purpose:
Maintain intellectual honesty and behavioral integrity across long sessions or multiple interactions.

---

## How It Works

### 1. Parallel Reasoning (Optional)
```python
# When high-stakes decision
delegate_response = generate_delegate_response(...)  # User satisfaction
trustee_response = generate_trustee_response(...)    # Epistemic accuracy

# Synthesize
synthesis = synthesize_response(delegate, trustee, stakes='high')
```

### 2. Track Synthesis Decisions
```python
synthesis_history.append({
    'turn': turn_number,
    'weights': {
        'delegate': 0.40,  # User-pleasing weight
        'trustee': 0.60    # Truth-seeking weight
    },
    'tensions_acknowledged': True
})
```

### 3. Analyze Drift (CHECK Phase)
```python
if len(synthesis_history) >= 10:
    drift_analysis = drift_monitor.analyze_drift(synthesis_history)
    
    if drift_analysis['sycophancy_drift']['detected']:
        # Warning: Becoming too agreeable
        ...
    
    if drift_analysis['tension_avoidance']['detected']:
        # Warning: Not acknowledging conflicts
        ...
```

---

## Sycophancy Drift

### What It Is:
Pattern where delegate (user-pleasing) weight increases over time.

### Example:
```python
Turn 1: delegate=0.40, trustee=0.60  # Balanced
Turn 5: delegate=0.50, trustee=0.50  # Shifting
Turn 10: delegate=0.70, trustee=0.30 # Sycophancy drift!
```

### Detection:
```python
# Calculate trend
recent_delegate_weight = mean(last_5_turns)
earlier_delegate_weight = mean(first_5_turns)

drift = recent_delegate_weight - earlier_delegate_weight

if drift > 0.15:  # 15% increase
    # Sycophancy drift detected
    severity = min(1.0, drift / 0.30)
```

### Warning Display:
```
📊 Drift Monitor: Analyzing behavioral patterns...
⚠️  Sycophancy drift detected (severity: 0.72)
   Evidence: Delegate weight increased from 0.40 to 0.75 over 10 turns
   Recommendation: Increase trustee weight or activate skeptic mode
```

---

## Tension Avoidance

### What It Is:
Pattern where conflicts and disagreements are not being acknowledged in synthesis.

### Example:
```python
Turn 1: tensions_acknowledged=True   # Good
Turn 3: tensions_acknowledged=False  # Avoiding
Turn 5: tensions_acknowledged=False  # Pattern
Turn 8: tensions_acknowledged=False  # Tension avoidance!
```

### Detection:
```python
recent_acknowledgments = sum(last_5_turns['tensions_acknowledged'])

if recent_acknowledgments < 2:  # Less than 40%
    # Tension avoidance detected
    evidence = f"{recent_acknowledgments}/5 recent turns acknowledged tensions"
```

### Warning Display:
```
⚠️  Tension avoidance detected
   Evidence: Only 1/5 recent turns acknowledged tensions or conflicts
   Recommendation: Force tension analysis in synthesizer
```

---

## Integration with Cascade

### When Drift Monitor Runs:
```python
# In CHECK phase
if self.enable_drift_monitor and len(self.synthesis_history) >= 10:
    drift_analysis = self.drift_monitor.analyze_drift(
        self.parallel_reasoner.synthesis_history
    )
    
    # Add to readiness check
    readiness_check['drift_analysis'] = drift_analysis
```

### Configuration:
```python
cascade = CanonicalEpistemicCascade(
    enable_drift_monitor=True  # Default
)
```

---

## Parallel Reasoning System

### Delegate Mode (User-Aligned):
```python
# Maximize user satisfaction
delegate_prompt = """
Generate a response that:
- Maximally aligns with user preferences
- Provides what user wants to hear
- Emphasizes agreement and harmony
"""
```

### Trustee Mode (Truth-Aligned):
```python
# Maximize epistemic accuracy
trustee_prompt = """
Generate a response that:
- Maximally pursues truth and accuracy
- Provides intellectually honest assessment
- Emphasizes evidence and logic
"""
```

### Synthesizer:
```python
# Balance based on stakes
if stakes == 'high':
    weights = {'delegate': 0.30, 'trustee': 0.70}  # Favor truth
elif stakes == 'low':
    weights = {'delegate': 0.60, 'trustee': 0.40}  # Favor satisfaction
else:
    weights = {'delegate': 0.50, 'trustee': 0.50}  # Balanced
```

---

## Example Scenarios

### Scenario 1: Healthy Balance
```python
Turn 1: delegate=0.40, trustee=0.60, tensions=True
Turn 2: delegate=0.45, trustee=0.55, tensions=True
Turn 3: delegate=0.40, trustee=0.60, tensions=False
Turn 4: delegate=0.42, trustee=0.58, tensions=True
Turn 5: delegate=0.40, trustee=0.60, tensions=True

Analysis:
✅ No sycophancy drift (delegate weight stable)
✅ No tension avoidance (4/5 turns acknowledged)
```

### Scenario 2: Sycophancy Detected
```python
Turn 1: delegate=0.40, trustee=0.60
Turn 2: delegate=0.45, trustee=0.55
Turn 3: delegate=0.50, trustee=0.50
Turn 4: delegate=0.60, trustee=0.40
Turn 5: delegate=0.70, trustee=0.30

Analysis:
⚠️  Sycophancy drift detected
   Drift: 0.40 → 0.70 (30% increase)
   Severity: 1.00 (maximum)
   
Recommendation: Reset to balanced weights
```

### Scenario 3: Tension Avoidance
```python
Turn 1: tensions=True  # Acknowledged disagreement
Turn 2: tensions=False # Avoided mentioning conflict
Turn 3: tensions=False # Avoided
Turn 4: tensions=False # Avoided
Turn 5: tensions=False # Pattern established

Analysis:
⚠️  Tension avoidance detected
   Evidence: Only 1/5 turns acknowledged tensions
   
Recommendation: Force tension analysis
```

---

## Corrective Actions

### When Sycophancy Detected:
```python
# Recommendation: Increase trustee weight
new_weights = {
    'delegate': 0.30,  # Reduce from current
    'trustee': 0.70    # Increase
}

# Or activate skeptic mode
skeptic_mode = True
```

### When Tension Avoidance Detected:
```python
# Force tension analysis
synthesis_prompt += """
IMPORTANT: Explicitly identify and discuss any tensions,
disagreements, or conflicts between delegate and trustee
perspectives. Do not avoid or smooth over differences.
"""
```

---

## Dashboard Display

When drift detected:
```
CHECK PHASE
═══════════════════════════════════════

📊 Drift Monitor: Analyzing behavioral patterns...

⚠️  Sycophancy drift detected (severity: 0.72)
   Evidence: Delegate weight increased from 0.40 to 0.75
   Recommendation: Increase trustee weight or activate skeptic mode

✅ No tension avoidance detected
   4/5 recent turns acknowledged tensions appropriately

Guidance: Reset synthesis weights to maintain intellectual honesty
```

---

## Best Practices

### 1. Use Parallel Reasoning for High-Stakes
```python
# Only for important decisions
if stakes == 'high':
    use_parallel_reasoning = True
```

### 2. Track Synthesis Decisions
```python
# Always record synthesis when using parallel reasoning
synthesis_history.append({
    'turn': turn,
    'weights': weights,
    'tensions_acknowledged': bool
})
```

### 3. Review Drift Warnings
Don't ignore drift warnings - they indicate important patterns.

### 4. Maintain Minimum History
Need at least 10 synthesis decisions for reliable drift detection.

---

## When to Use Parallel Reasoning

### Good Use Cases:
- High-stakes decisions (medical, legal, safety)
- Controversial topics
- Complex ethical dilemmas
- Long-running sessions

### Not Needed For:
- Simple tasks
- Creative work
- Short interactions
- Low-stakes decisions

---

## Configuration

### Enable/Disable:
```python
cascade = CanonicalEpistemicCascade(
    enable_drift_monitor=True  # Default
)
```

### Customize Thresholds:
```python
# In parallel_reasoning.py
SYCOPHANCY_THRESHOLD = 0.15    # Drift % to trigger warning
TENSION_THRESHOLD = 0.40       # Min acknowledgment rate
MIN_HISTORY = 10               # Min decisions for analysis
```

---

## Troubleshooting

### Drift Monitor Not Running?
- Check if `enable_drift_monitor=True`
- Verify at least 10 synthesis decisions recorded
- Parallel reasoning must be used to generate history

### False Positives?
- May need to adjust thresholds for your use case
- Review synthesis history manually
- Consider if drift is actually appropriate

### No History?
- Parallel reasoning not being used
- Synthesis history not being recorded
- Check integration code

---

## Philosophy

### Why Monitor Drift?

**Sycophancy:** 
Over time, systems can learn to be too agreeable to maintain user satisfaction. This compromises intellectual honesty.

**Tension Avoidance:**
Smoothing over all conflicts may feel nice but loses important nuance and honest disagreement.

**Goal:**
Maintain balanced, intellectually honest interactions that serve both user satisfaction and epistemic accuracy.

---

## Next Steps

- Bayesian Guardian: `08_BAYESIAN_GUARDIAN.md`
- Understanding vectors: `05_EPISTEMIC_VECTORS.md`
- Configuration: `15_CONFIGURATION.md`

