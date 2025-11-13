# 16. Tuning Thresholds & Domain Calibration

**Version:** 2.0  
**Date:** 2025-10-29  
**Status:** Production Ready

---

## Overview

Empirica's canonical weights and thresholds work well out-of-the-box for general tasks, but domain-specific calibration can significantly improve assessment accuracy. This guide covers threshold tuning, domain calibration, and validation strategies.

---

## Understanding Canonical Weights

### Default Weights (35/25/25/15)

```
CONFIDENCE: 35% - How certain the assessment is
COHERENCE:  25% - Internal logical consistency
NECESSITY:  25% - Whether investigation is needed
ENGAGEMENT: 15% - Task importance and attention
```

**Why these defaults?**
- **CONFIDENCE (35%):** Primary signal - direct uncertainty measure
- **COHERENCE (25%):** Validation signal - prevents contradictory assessments
- **NECESSITY (25%):** Action signal - drives investigation decisions  
- **ENGAGEMENT (15%):** Context signal - task prioritization

**Weighted Score Formula:**
```
score = (C × 0.35) + (Coh × 0.25) + (N × 0.25) + (E × 0.15)
```

**Investigation Decision:**
```
if score < 0.65:  # Below threshold
    → INVESTIGATE
else:
    → PROCEED
```

---

## When to Tune Thresholds

### Keep Defaults If:
✓ General-purpose AI assistant  
✓ Diverse task types  
✓ No specific domain focus  
✓ Conservative investigation preferred

### Consider Tuning If:
⚠ Specific domain (e.g., medical, legal, financial)  
⚠ Known task patterns  
⚠ Too many false investigations  
⚠ Too few investigations (missing gaps)  
⚠ Domain-specific confidence requirements

---

## Domain-Specific Calibrations

### High-Stakes Domains (Medical, Legal, Financial)

**Characteristics:**
- Mistakes are costly
- Require high certainty
- Investigation preferred over errors
- False negatives worse than false positives

**Recommended Weights:**
```bash
EMPIRICA_WEIGHT_CONFIDENCE=45     # ↑ Higher confidence threshold
EMPIRICA_WEIGHT_COHERENCE=30      # ↑ More validation
EMPIRICA_WEIGHT_NECESSITY=20      # ↓ Less focus on necessity
EMPIRICA_WEIGHT_ENGAGEMENT=5      # ↓ Engagement less critical

EMPIRICA_INVESTIGATION_THRESHOLD=0.75  # ↑ Higher bar for proceeding
EMPIRICA_UNCERTAINTY_THRESHOLD=0.5     # ↓ Investigate at lower uncertainty
```

**Rationale:** Prioritize confidence and coherence. Investigate even moderate uncertainty.

### Creative/Exploratory Domains (Research, Design, Brainstorming)

**Characteristics:**
- Exploration encouraged
- Mistakes are learning opportunities
- Speed matters
- False positives worse than false negatives

**Recommended Weights:**
```bash
EMPIRICA_WEIGHT_CONFIDENCE=25     # ↓ Lower confidence needed
EMPIRICA_WEIGHT_COHERENCE=20      # ↓ Tolerate some inconsistency
EMPIRICA_WEIGHT_NECESSITY=30      # ↑ Focus on what's needed
EMPIRICA_WEIGHT_ENGAGEMENT=25     # ↑ Engagement drives exploration

EMPIRICA_INVESTIGATION_THRESHOLD=0.55  # ↓ Easier to proceed
EMPIRICA_UNCERTAINTY_THRESHOLD=0.7     # ↑ Only investigate high uncertainty
```

**Rationale:** Prioritize engagement and necessity. Avoid over-investigation.

### Technical/Engineering Domains (Code, DevOps, Systems)

**Characteristics:**
- Precision required but iteration expected
- Debugging is normal
- Context-dependent confidence
- Balance between speed and accuracy

**Recommended Weights:**
```bash
EMPIRICA_WEIGHT_CONFIDENCE=35     # = Balanced
EMPIRICA_WEIGHT_COHERENCE=30      # ↑ Technical consistency critical
EMPIRICA_WEIGHT_NECESSITY=25      # = Balanced
EMPIRICA_WEIGHT_ENGAGEMENT=10     # ↓ Lower engagement weight

EMPIRICA_INVESTIGATION_THRESHOLD=0.65  # = Standard threshold
EMPIRICA_UNCERTAINTY_THRESHOLD=0.6     # = Standard threshold
```

**Rationale:** Emphasis on coherence (technical correctness), standard thresholds.

### Customer Service/Support

**Characteristics:**
- User satisfaction matters
- Quick responses valued
- Mistakes recoverable
- Engagement critical

**Recommended Weights:**
```bash
EMPIRICA_WEIGHT_CONFIDENCE=30     # ↓ Slightly lower confidence OK
EMPIRICA_WEIGHT_COHERENCE=20      # ↓ Flexibility in approach
EMPIRICA_WEIGHT_NECESSITY=20      # ↓ Less investigation
EMPIRICA_WEIGHT_ENGAGEMENT=30     # ↑ High engagement critical

EMPIRICA_INVESTIGATION_THRESHOLD=0.60  # ↓ Lower threshold
EMPIRICA_UNCERTAINTY_THRESHOLD=0.65    # ↑ Higher tolerance
```

**Rationale:** Maximize engagement, minimize delays from investigation.

---

## Threshold Tuning Process

### Step 1: Baseline Measurement

```bash
# Run with default settings
empirica cascade "typical task" --verbose

# Check results
# Note: 'query' command is planned for future release
# Use sqlite3 directly for now:
sqlite3 .empirica/*/empirica.db "SELECT AVG(confidence), AVG(coherence), AVG(necessity), AVG(engagement) 
                FROM assessments 
                WHERE created_at > datetime('now', '-7 days')"

# Look for patterns
# Note: analyze-thresholds command is planned for future release
# For now, manually analyze results from query above
```

**Record:**
- Average vector scores
- Investigation frequency
- False positive rate (unnecessary investigations)
- False negative rate (missed investigations)

### Step 2: Identify Issues

**Too Many Investigations?**
```
Symptom: >50% of tasks trigger investigation
Problem: Threshold too low or weights misaligned
Solution: ↑ investigation_threshold or reweight
```

**Too Few Investigations?**
```
Symptom: <10% trigger investigation, errors frequent
Problem: Threshold too high
Solution: ↓ investigation_threshold
```

**Specific Vector Always Low?**
```
Symptom: COHERENCE always <0.5 in domain
Problem: Weight too high for domain characteristics
Solution: ↓ coherence weight, ↑ other weights
```

### Step 3: Experimental Tuning

```bash
# Create test configuration
cat > test_config.yaml << EOF
assessment:
  weights:
    confidence: 40  # Trying higher confidence
    coherence: 25
    necessity: 25
    engagement: 10
  
  thresholds:
    investigation: 0.70  # Trying higher threshold
    uncertainty: 0.55
EOF

# Test on representative tasks
empirica cascade "task 1" --config test_config.yaml
empirica cascade "task 2" --config test_config.yaml
empirica cascade "task 3" --config test_config.yaml

# Compare results
empirica compare-configs default.yaml test_config.yaml \
  --tasks tasks.json \
  --metrics investigation_rate,accuracy,false_positives
```

### Step 4: Validation

```bash
# A/B test configurations (manual approach)
# Note: ab-test and analyze-ab-test commands are planned for future release

# For now, run tests manually with different configs:
# Test 1: Use default config
EMPIRICA_CONFIG=default.yaml empirica cascade "validation task 1"
# ... repeat for all validation tasks ...

# Test 2: Use tuned config
EMPIRICA_CONFIG=tuned.yaml empirica cascade "validation task 1"
# ... repeat for all validation tasks ...

# Compare results manually using sessions-list and sessions-show
empirica sessions-list --recent 100
```

**Validation Metrics:**
1. **Investigation Rate:** 15-30% is healthy
2. **Δuncertainty:** Should average -0.15 to -0.35 (learning)
3. **False Positive Rate:** <20% unnecessary investigations
4. **False Negative Rate:** <10% missed investigations
5. **Task Success Rate:** ↑ after investigation

### Step 5: Deploy & Monitor

```bash
# Deploy tuned config
cp tuned.yaml config.yaml
export EMPIRICA_CONFIG_PATH=config.yaml

# Monitor for 1 week
empirica monitor --config config.yaml --duration 7d

# Check drift
empirica check-drift --baseline baseline_stats.json
```

---

## Per-Vector Tuning

### Tuning CONFIDENCE Weight

**Increase CONFIDENCE if:**
- Domain requires high certainty
- Errors are costly
- Investigation capacity is high

**Decrease CONFIDENCE if:**
- Speed is critical
- Iteration expected
- Over-investigation occurring

**Example:**
```yaml
# High-stakes: 45% CONFIDENCE
weights:
  confidence: 45
  coherence: 25
  necessity: 20
  engagement: 10

# Fast iteration: 25% CONFIDENCE  
weights:
  confidence: 25
  coherence: 25
  necessity: 30
  engagement: 20
```

### Tuning COHERENCE Weight

**Increase COHERENCE if:**
- Technical precision required
- Logical consistency critical
- Multi-step reasoning common

**Decrease COHERENCE if:**
- Creative tasks
- Exploratory work
- Flexibility valued

### Tuning NECESSITY Weight

**Increase NECESSITY if:**
- Investigation resources limited
- Want to focus on truly needed investigations
- Efficiency critical

**Decrease NECESSITY if:**
- Investigation encouraged
- Learning prioritized
- Thoroughness valued

### Tuning ENGAGEMENT Weight

**Increase ENGAGEMENT if:**
- User-facing tasks
- Attention/focus matters
- Task importance variable

**Decrease ENGAGEMENT if:**
- Automated workflows
- All tasks equal priority
- Engagement irrelevant

---

## Advanced Calibration

### Dynamic Thresholds

```python
# Adjust thresholds based on context
from empirica.core import EmpiricalCascade

cascade = EmpiricalCascade(ai_id="adaptive_agent")

# High-stakes context
if context.get("domain") == "medical":
    cascade.set_thresholds(
        investigation=0.75,
        uncertainty=0.5
    )
    cascade.set_weights(45, 30, 20, 5)

# Low-stakes context
elif context.get("domain") == "brainstorming":
    cascade.set_thresholds(
        investigation=0.55,
        uncertainty=0.7
    )
    cascade.set_weights(25, 20, 30, 25)
```

### Bayesian Prior Tuning

```bash
# Conservative prior (assume low confidence)
EMPIRICA_BAYESIAN_PRIOR=0.3

# Optimistic prior (assume high confidence)
EMPIRICA_BAYESIAN_PRIOR=0.7

# Neutral (default)
EMPIRICA_BAYESIAN_PRIOR=0.5
```

### Evidence Strength Tuning

```bash
# Weak evidence (require more investigation)
EMPIRICA_EVIDENCE_STRENGTH=weak

# Strong evidence (trust assessments more)
EMPIRICA_EVIDENCE_STRENGTH=strong

# Moderate (default)
EMPIRICA_EVIDENCE_STRENGTH=moderate
```

---

## Validation Strategies

### Holdout Testing

```bash
# Split tasks into train/test
empirica split-dataset tasks.json \
  --train train.json \
  --test test.json \
  --ratio 0.8

# Tune on training set
empirica tune --tasks train.json --output tuned.yaml

# Validate on test set
empirica validate tuned.yaml --tasks test.json
```

### Cross-Validation

```bash
# K-fold cross-validation
empirica cross-validate \
  --tasks tasks.json \
  --folds 5 \
  --config test_config.yaml \
  --metric investigation_accuracy
```

### Temporal Validation

```bash
# Tune on past data, test on recent
empirica tune \
  --start-date 2025-01-01 \
  --end-date 2025-09-30 \
  --output tuned.yaml

empirica validate tuned.yaml \
  --start-date 2025-10-01 \
  --end-date 2025-10-29
```

---

## Common Calibration Patterns

### Pattern 1: Over-Investigation

**Symptoms:**
- >50% tasks trigger investigation
- Many investigations yield minimal learning (Δuncertainty ≈ 0)
- Slow task completion

**Solution:**
```yaml
# Raise threshold and rebalance
thresholds:
  investigation: 0.70  # Was 0.65
  
weights:
  confidence: 30       # Reduce sensitivity
  coherence: 25
  necessity: 30        # Increase necessity focus
  engagement: 15
```

### Pattern 2: Under-Investigation

**Symptoms:**
- <10% tasks trigger investigation
- Frequent errors
- Low confidence but no investigation

**Solution:**
```yaml
# Lower threshold and increase confidence weight
thresholds:
  investigation: 0.60  # Was 0.65
  uncertainty: 0.55    # Was 0.60

weights:
  confidence: 40       # Increase sensitivity
  coherence: 25
  necessity: 25
  engagement: 10
```

### Pattern 3: Coherence Issues

**Symptoms:**
- COHERENCE always low
- Logically valid but scores poorly
- Domain has unique reasoning patterns

**Solution:**
```yaml
# Reduce coherence weight
weights:
  confidence: 40
  coherence: 15        # Was 25
  necessity: 30        # Increased
  engagement: 15
```

---

## Testing Calibration Changes

### Before Deploying

```bash
# 1. Backup current config
cp config.yaml config.yaml.backup

# 2. Test new config on sample tasks
empirica test-config new_config.yaml \
  --tasks sample_tasks.json \
  --compare-to config.yaml

# 3. Review differences
empirica diff-results \
  baseline_results.json \
  new_results.json

# 4. If satisfied, deploy
cp new_config.yaml config.yaml

# 5. Monitor for 24 hours
empirica monitor --duration 24h --alert-on-anomaly
```

### Rollback if Needed

```bash
# Restore previous config
cp config.yaml.backup config.yaml

# Clear any cached calibration
empirica clear-cache --calibration

# Restart monitoring
empirica bootstrap --level standard
```

---

## Domain-Specific Examples

### Example: Medical Diagnosis Support

```yaml
# medical_config.yaml
assessment:
  weights:
    confidence: 50  # Critical certainty
    coherence: 30   # Logical consistency essential
    necessity: 15   # Investigation always good
    engagement: 5   # Less relevant
  
  thresholds:
    investigation: 0.80  # Very high bar
    uncertainty: 0.4     # Investigate early
    delta_uncertainty_min: -0.3  # Expect significant learning

bayesian:
  prior: 0.3  # Conservative - assume uncertainty
  evidence_strength: "strong"  # Trust medical sources
```

### Example: Code Review

```yaml
# code_review_config.yaml
assessment:
  weights:
    confidence: 35  # Standard
    coherence: 35   # Technical consistency critical
    necessity: 20   # Moderate
    engagement: 10  # Lower
  
  thresholds:
    investigation: 0.65  # Standard
    uncertainty: 0.6
    delta_uncertainty_min: -0.2

bayesian:
  prior: 0.5  # Neutral
  evidence_strength: "moderate"
```

### Example: Creative Writing

```yaml
# creative_config.yaml
assessment:
  weights:
    confidence: 20  # Low - embrace uncertainty
    coherence: 15   # Flexibility valued
    necessity: 30   # Focus on what's needed
    engagement: 35  # Engagement critical
  
  thresholds:
    investigation: 0.50  # Low bar
    uncertainty: 0.75    # High tolerance
    delta_uncertainty_min: -0.1  # Less learning expected

bayesian:
  prior: 0.6  # Optimistic
  evidence_strength: "weak"  # Don't over-constrain
```

---

## Monitoring Calibration Health

### Key Metrics

```bash
# Weekly calibration report
empirica calibration-report --window 7d

# Check:
# 1. Investigation rate: 15-30%
# 2. Avg Δuncertainty: -0.15 to -0.35
# 3. False positive rate: <20%
# 4. False negative rate: <10%
# 5. Task success rate: >80%
```

### Calibration Drift Detection

```bash
# Compare current vs baseline
empirica check-calibration-drift \
  --baseline baseline_stats.json \
  --current-window 7d \
  --alert-threshold 0.15

# If drift detected, investigate:
# - Domain shift?
# - New task types?
# - External factors?
```

---

## Best Practices

1. **Start with defaults** - Only tune if clear need
2. **Document changes** - Record why you tuned
3. **Validate thoroughly** - Test before deploying
4. **Monitor continuously** - Watch for drift
5. **Version configs** - Git track configuration files
6. **A/B test changes** - Compare old vs new
7. **Review quarterly** - Domains evolve
8. **Keep it simple** - Fewer changes better

---

## Next Steps

- **Configuration:** See `15_CONFIGURATION.md`
- **Monitoring:** See `18_MONITORING_LOGGING.md`
- **Production:** See `17_PRODUCTION_DEPLOYMENT.md`
- **Troubleshooting:** See `21_TROUBLESHOOTING.md`

---

**Last Updated:** 2025-10-29  
**Version:** 2.0
