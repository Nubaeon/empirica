# 🎯 Vector-Based Programmatic Guidance

**Practical patterns for using epistemic vectors in programmatic workflows**

---

## 🤖 Why Vector-Based Guidance?

Empirica's 13 epistemic vectors enable **fine-tuned, programmatic decision making** by:

1. **Quantifying knowledge state** (not just "I think I know")
2. **Measuring uncertainty explicitly** (not just confidence)
3. **Enabling data-driven workflow routing**
4. **Providing calibration scores** (prediction accuracy)

---

## 📊 The 13 Vectors (Quick Reference)

### Foundation Vectors (Always Use)
```json
{
  "engagement": 0.9,    // 0.0-1.0, Gate: ≥0.6 (want to work on this?)
  "know": 0.7,          // 0.0-1.0, What you ACTUALLY know
  "do": 0.8,            // 0.0-1.0, Capability to execute
  "context": 0.6,       // 0.0-1.0, Understanding of surrounding system
  "uncertainty": 0.3    // 0.0-1.0, Explicit uncertainty measurement
}
```

### Comprehension Vectors (As Needed)
```json
{
  "clarity": 0.7,       // 0.0-1.0, How clear is the task?
  "coherence": 0.8,     // 0.0-1.0, Does it make sense?
  "signal": 0.6,        // 0.0-1.0, Can you separate signal from noise?
  "density": 0.7        // 0.0-1.0, Information richness
}
```

### Execution Vectors (As Needed)
```json
{
  "state": 0.5,         // 0.0-1.0, System state understanding
  "change": 0.4,        // 0.0-1.0, Confidence in making changes
  "completion": 0.3,    // 0.0-1.0, Progress toward completion
  "impact": 0.5         // 0.0-1.0, Expected impact understanding
}
```

---

## 🚀 Practical Routing Patterns

### Pattern 1: Investigation vs Implementation

```bash
# Get current vectors
VECTORS=$(empirica epistemics-show --session-id $SESSION --output json)

# Extract key values
UNCERTAINTY=$(echo "$VECTORS" | jq '.vectors.uncertainty')
CONTEXT=$(echo "$VECTORS" | jq '.vectors.context')
KNOW=$(echo "$VECTORS" | jq '.vectors.know')

# Decision logic
if [ $(echo "$UNCERTAINTY > 0.6" | bc) -eq 1 ] && [ $(echo "$CONTEXT < 0.4" | bc) -eq 1 ]; then
  # High uncertainty, low context → Investigate first
  echo "🔍 INVESTIGATION MODE: Not enough context to proceed"
  empirica project-bootstrap --session-id $SESSION --depth full
  # Research phase...
  
elif [ $(echo "$KNOW > 0.7" | bc) -eq 1 ] && [ $(echo "$UNCERTAINTY < 0.3" | bc) -eq 1 ]; then
  # High knowledge, low uncertainty → Proceed with implementation
  echo "🚀 IMPLEMENTATION MODE: Ready to proceed"
  # Implementation phase...
  
else
  # Medium state → Ask specific questions
  echo "❓ QUESTION MODE: Need to ask specific questions"
  # Ask user for clarification...
fi
```

**Use Case:** Automatically route to investigation or implementation based on knowledge state

---

### Pattern 2: Dynamic Context Loading

```bash
# Load context based on uncertainty level
UNCERTAINTY=$(empirica epistemics-show --session-id $SESSION | jq '.vectors.uncertainty')

if [ $(echo "$UNCERTAINTY > 0.6" | bc) -eq 1 ]; then
  # High uncertainty → load full context
  empirica project-bootstrap --session-id $SESSION --depth full
  
elif [ $(echo "$UNCERTAINTY > 0.3" | bc) -eq 1 ]; then
  # Medium uncertainty → load moderate context
  empirica project-bootstrap --session-id $SESSION --depth moderate
  
else
  # Low uncertainty → load minimal context
  empirica project-bootstrap --session-id $SESSION --depth minimal
fi
```

**Use Case:** Automatically adjust context depth based on current uncertainty

---

### Pattern 3: Workflow Complexity Routing

```bash
# Determine workflow complexity based on scope vectors
SCOPE=$(empirica goals-get --goal-id $GOAL_ID --output json | jq '.scope')
BREADTH=$(echo "$SCOPE" | jq '.breadth')
DURATION=$(echo "$SCOPE" | jq '.duration')

if [ $(echo "$BREADTH > 0.7" | bc) -eq 1 ]; then
  # Large scope → Use full CASCADE with multiple CHECK gates
  echo "🎯 COMPLEX WORKFLOW: Multiple CHECK gates recommended"
  
elif [ $(echo "$BREADTH > 0.4" | bc) -eq 1 ]; then
  # Medium scope → Use standard CASCADE
  echo "⚡ STANDARD WORKFLOW: PREFLIGHT → CHECK → POSTFLIGHT"
  
else
  # Small scope → Simplified workflow
  echo "✨ SIMPLE WORKFLOW: PREFLIGHT → POSTFLIGHT (skip CHECK)"
fi
```

**Use Case:** Automatically select workflow complexity based on goal scope

---

### Pattern 4: Learning Efficiency Measurement

```bash
# Measure learning efficiency (POSTFLIGHT vs PREFLIGHT)
PREFLIGHT=$(empirica epistemics-get --session-id $SESSION --phase preflight --output json)
POSTFLIGHT=$(empirica epistemics-get --session-id $SESSION --phase postflight --output json)

KNOW_DELTA=$(echo "$POSTFLIGHT.vectors.know - $PREFLIGHT.vectors.know" | bc)
UNCERTAINTY_DELTA=$(echo "$PREFLIGHT.vectors.uncertainty - $POSTFLIGHT.vectors.uncertainty" | bc)
TIME_SPENT=$(echo "$POSTFLIGHT.timestamp - $PREFLIGHT.timestamp" | bc)

# Calculate learning efficiency (knowledge gain per time unit)
if [ $TIME_SPENT -gt 0 ]; then
  LEARNING_EFFICIENCY=$(echo "$KNOW_DELTA / $TIME_SPENT" | bc)
  echo "📊 Learning Efficiency: $LEARNING_EFFICIENCY (KNOW delta: $KNOW_DELTA, Time: $TIME_SPENT)"
fi
```

**Use Case:** Measure and optimize learning efficiency over time

---

## 🎯 Decision Thresholds

### Common Decision Points

```json
{
  "engagement": {
    "min": 0.6,
    "ideal": 0.8,
    "max": 1.0,
    "gate": "If < 0.6, consider disengaging or switching tasks"
  },
  "know": {
    "novice": 0.3,
    "proficient": 0.5,
    "expert": 0.8,
    "gate": "If < 0.4, research needed; if > 0.7, ready to implement"
  },
  "uncertainty": {
    "low": 0.2,
    "medium": 0.5,
    "high": 0.8,
    "gate": "If > 0.6, investigate; if < 0.3, proceed"
  },
  "confidence": {
    "proceed": 0.7,
    "investigate": 0.5,
    "gate": "CHECK gate: ≥0.7 proceed, <0.7 investigate"
  }
}
```

---

## 📚 Vector-Based Functions

### Function 1: Should I Ask or Investigate?

```bash
# Ask-Before-Investigate Pattern
function ask_or_investigate() {
  local SESSION_ID=$1
  local VECTORS=$(empirica epistemics-show --session-id $SESSION_ID --output json)
  
  local UNCERTAINTY=$(echo "$VECTORS" | jq '.vectors.uncertainty')
  local CONTEXT=$(echo "$VECTORS" | jq '.vectors.context')
  
  # Ask first if: uncertainty >= 0.65 AND context >= 0.50
  if [ $(echo "$UNCERTAINTY >= 0.65" | bc) -eq 1 ] && [ $(echo "$CONTEXT >= 0.50" | bc) -eq 1 ]; then
    echo "ASK: You have enough context to ask specific questions"
    return 0
  
  # Investigate first if: context < 0.30
  elif [ $(echo "$CONTEXT < 0.30" | bc) -eq 1 ]; then
    echo "INVESTIGATE: Not enough context to ask meaningful questions"
    return 1
  
  else
    echo "PROCEED: Sufficient knowledge to continue"
    return 2
  fi
}

# Usage
ask_or_investigate $SESSION_ID
case $? in
  0) echo "→ Ask specific questions";;
  1) echo "→ Investigate/explore first";;
  2) echo "→ Proceed with work";;
esac
```

---

### Function 2: Workflow Recommendation

```bash
function recommend_workflow() {
  local SESSION_ID=$1
  local VECTORS=$(empirica epistemics-show --session-id $SESSION_ID --output json)
  
  local KNOW=$(echo "$VECTORS" | jq '.vectors.know')
  local UNCERTAINTY=$(echo "$VECTORS" | jq '.vectors.uncertainty')
  local SCOPE=$(echo "$VECTORS" | jq '.vectors.scope.breadth')
  
  # Complex workflow: high uncertainty + wide scope
  if [ $(echo "$UNCERTAINTY > 0.6" | bc) -eq 1 ] && [ $(echo "$SCOPE > 0.6" | bc) -eq 1 ]; then
    echo "COMPLEX: PREFLIGHT → CHECK → WORK → CHECK → POSTFLIGHT"
    
  # Standard workflow: medium uncertainty/scope
  elif [ $(echo "$UNCERTAINTY > 0.3" | bc) -eq 1 ] || [ $(echo "$SCOPE > 0.3" | bc) -eq 1 ]; then
    echo "STANDARD: PREFLIGHT → CHECK → POSTFLIGHT"
    
  # Simple workflow: low uncertainty + narrow scope
  else
    echo "SIMPLE: PREFLIGHT → POSTFLIGHT"
  fi
}

# Usage
WORKFLOW=$(recommend_workflow $SESSION_ID)
echo "Recommended workflow: $WORKFLOW"
```

---

### Function 3: Calibration Check

```bash
function check_calibration() {
  local SESSION_ID=$1
  
  # Get PREFLIGHT and POSTFLIGHT
  local PREFLIGHT=$(empirica epistemics-get --session-id $SESSION_ID --phase preflight --output json)
  local POSTFLIGHT=$(empirica epistemics-get --session-id $SESSION_ID --phase postflight --output json)
  
  if [ -z "$PREFLIGHT" ] || [ -z "$POSTFLIGHT" ]; then
    echo "CALIBRATION: Incomplete (missing PREFLIGHT or POSTFLIGHT)"
    return
  fi
  
  local PREDICTED_DIFFICULTY=$(echo "$PREFLIGHT" | jq '.vectors.uncertainty')
  local ACTUAL_DIFFICULTY=$(echo "$POSTFLIGHT" | jq '.vectors.uncertainty')
  
  # Calibration score: 1 - |predicted - actual|
  local CALIBRATION=$(echo "1 - ($(echo "$PREDICTED_DIFFICULTY - $ACTUAL_DIFFICULTY" | bc | awk '{print $1 < 0 ? $1 * -1 : $1}')" | bc)
  
  if [ $(echo "$CALIBRATION > 0.8" | bc) -eq 1 ]; then
    echo "CALIBRATION: Well calibrated ($CALIBRATION)"
  elif [ $(echo "$CALIBRATION > 0.6" | bc) -eq 1 ]; then
    echo "CALIBRATION: Moderate ($CALIBRATION)"
  else
    echo "CALIBRATION: Poor ($CALIBRATION) - Improve self-assessment"
  fi
}

# Usage
check_calibration $SESSION_ID
```

---

## 💡 Practical Use Cases

### Use Case 1: Automated Workflow Selection
```bash
# Automatically select workflow based on current state
SESSION=$(empirica session-create --ai-id "auto-workflow" --quiet)
VECTORS=$(empirica epistemics-show --session-id $SESSION --output json)

# Route based on vectors
if [ $(echo "$VECTORS" | jq '.vectors.uncertainty > 0.6') ]; then
  echo "🔍 Starting investigation workflow"
  # Investigation phase...
else
  echo "🚀 Starting implementation workflow"
  # Implementation phase...
fi
```

### Use Case 2: Dynamic CHECK Gate Frequency
```bash
# Adjust CHECK gate frequency based on uncertainty
UNCERTAINTY=$(empirica epistemics-show --session-id $SESSION | jq '.vectors.uncertainty')

if [ $(echo "$UNCERTAINTY > 0.7" | bc) -eq 1 ]; then
  # High uncertainty → CHECK every 30 minutes
  CHECK_INTERVAL=1800
elif [ $(echo "$UNCERTAINTY > 0.4" | bc) -eq 1 ]; then
  # Medium uncertainty → CHECK every hour
  CHECK_INTERVAL=3600
else
  # Low uncertainty → CHECK every 2 hours
  CHECK_INTERVAL=7200
fi
```

### Use Case 3: Context-Aware Help
```bash
# Provide help based on current context
CONTEXT=$(empirica epistemics-show --session-id $SESSION | jq '.vectors.context')

if [ $(echo "$CONTEXT < 0.4" | bc) -eq 1 ]; then
  echo "💡 Tip: Load more context with: empirica project-bootstrap --depth full"
elif [ $(echo "$CONTEXT < 0.7" | bc) -eq 1 ]; then
  echo "💡 Tip: Review findings with: empirica epistemics-list --type findings"
fi
```

---

## 📊 Vector-Based CLI Commands

### Get Current Vectors
```bash
empirica epistemics-show --session-id $SESSION --output json
```

### Get Specific Phase Vectors
```bash
empirica epistemics-get --session-id $SESSION --phase preflight --output json
empirica epistemics-get --session-id $SESSION --phase postflight --output json
```

### Compare Vectors (Learning Delta)
```bash
empirica epistemics-compare --session-id $SESSION --output json
```

---

## 🎯 Best Practices

### 1. **Always Start with PREFLIGHT**
```bash
# Establish baseline before any work
VECTORS=$(empirica epistemics-show --session-id $SESSION --output json)
echo "Baseline: KNOW=$(jq '.vectors.know' <<< $VECTORS), UNCERTAINTY=$(jq '.vectors.uncertainty' <<< $VECTORS)"
```

### 2. **Use Vectors for Routing**
```bash
# Route work based on current state
if [ $(jq '.vectors.uncertainty > 0.6' <<< $VECTORS) ]; then
  # Investigation path
else
  # Implementation path
fi
```

### 3. **Measure Learning Deltas**
```bash
# Compare PREFLIGHT vs POSTFLIGHT
PRE=$(empirica epistemics-get --session-id $SESSION --phase preflight --output json)
POST=$(empirica epistemics-get --session-id $SESSION --phase postflight --output json)
echo "Learning: KNOW +$(jq '.vectors.know' <<< $POST - jq '.vectors.know' <<< $PRE), UNCERTAINTY $(jq '.vectors.uncertainty' <<< $PRE - jq '.vectors.uncertainty' <<< $POST)"
```

### 4. **Cache Vectors for Performance**
```bash
# Cache vectors to avoid repeated calls
VECTORS=$(empirica epistemics-show --session-id $SESSION --output json)
UNCERTAINTY=$(jq '.vectors.uncertainty' <<< $VECTORS)
KNOW=$(jq '.vectors.know' <<< $VECTORS)
```

---

## 🔮 Future Enhancements

### 1. **Automated Routing Command**
```bash
# Proposed: Automatic workflow selection
empirica route --session-id $SESSION
# Output: "Use investigation workflow - high uncertainty detected"
```

### 2. **Vector-Based Templates**
```bash
# Proposed: Pre-defined workflow templates
empirica template --vectors '{"know": 0.6, "uncertainty": 0.5}'
# Output: "Recommended: Investigation workflow with CHECK gates"
```

### 3. **Real-Time Vector Monitoring**
```bash
# Proposed: Continuous vector monitoring
empirica monitor --session-id $SESSION --threshold uncertainty=0.6
# Output: "Uncertainty threshold exceeded - investigate recommended"
```

---

## 🎓 Learning Vector-Based Programming

### Progressive Mastery
```
1. Start with basic vector checks (KNOW, UNCERTAINTY)
2. Add context-based routing (CONTEXT, SCOPE)
3. Implement learning measurement (PREFLIGHT vs POSTFLIGHT)
4. Build automated workflow selection
5. Create vector-based functions and templates
```

### Key Insights
- **Vectors enable programmatic decision making**
- **Start simple, add complexity as needed**
- **Cache vectors to avoid repeated API calls**
- **Use vectors for both routing and measurement**
- **Combine vectors for sophisticated decision logic**

---

## 🧠 Cognitive Patterns

### Think → Assess Vectors
```bash
# Before starting any task, assess current state
VECTORS=$(empirica epistemics-show --session-id $SESSION --output json)
```

### Decide → Use Vector Logic
```bash
# At decision points, use vector-based routing
if [ $(jq '.vectors.uncertainty > 0.6' <<< $VECTORS) ]; then
  # Investigate
else
  # Proceed
fi
```

### Learn → Measure Deltas
```bash
# After completing work, measure what you learned
empirica epistemics-compare --session-id $SESSION
```

---

**Vector-based programmatic guidance enables fine-tuned, data-driven workflows!** 📊✨