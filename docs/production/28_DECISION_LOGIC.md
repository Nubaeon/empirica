# 28. Epistemic Decision Logic

**Version:** 2.0  
**Date:** 2025-12-04  
**Status:** Production Ready

**Storage Architecture:** See `docs/architecture/STORAGE_ARCHITECTURE_COMPLETE.md`  

---

## Overview

The **Epistemic Decision Logic** system solves the "simple task paradox" by using the AI's own epistemic self-assessment to guide its next actions.

**Key Innovation**: Instead of pre-classifying tasks as "simple" or "complex", the AI:
1. Assesses its epistemic state (PREFLIGHT)
2. Checks decision criteria (comprehension + foundation)
3. Receives guidance on what to do next
4. Decides how to proceed

---

## Decision Matrix

### Input: 4 Epistemic Vectors

**Comprehension** (Do I understand the request?):
- `clarity` ≥ 0.6: Is the request clear?
- `signal` ≥ 0.5: Is information quality good?

**Foundation** (Can I operate effectively?):
- `know` ≥ 0.5: Do I know the domain/codebase?
- `context` ≥ 0.5: Do I understand the environment?

### Decision Logic

```
Comprehension = clarity ≥ 0.6 AND signal ≥ 0.5
Foundation = know ≥ 0.5 AND context ≥ 0.5

IF understands_request AND can_operate:
    → CREATE_GOAL (proceed immediately)
    
ELIF understands_request AND NOT can_operate:
    → INVESTIGATE_FIRST (learn before creating goal)
    
ELSE:
    → ASK_CLARIFICATION (don't understand request)
```

---

## Three Outcomes

### 1. CREATE_GOAL
**When**: High comprehension + high foundation  
**Meaning**: "I understand what to do AND I have the foundation to do it"  
**Action**: Create structured goal and proceed to ACT

**Example**:
```python
# clarity=0.85, signal=0.80, know=0.70, context=0.80
decision = decide_goal_creation(
    clarity=0.85, signal=0.80, know=0.70, context=0.80
)
# → should_create_goal_now: True
# → suggested_action: 'create_goal'
```

---

### 2. INVESTIGATE_FIRST
**When**: High comprehension + low foundation  
**Meaning**: "I understand what to do BUT lack domain knowledge or context"  
**Action**: Investigate to build foundation, then create goal

**Example**:
```python
# clarity=0.80, signal=0.75, know=0.30, context=0.70
decision = decide_goal_creation(
    clarity=0.80, signal=0.75, know=0.30, context=0.70
)
# → should_create_goal_now: False
# → suggested_action: 'investigate_first'
# → reasoning: "Clear request but low know (0.30). Should investigate 
#              domain knowledge/codebase before creating goal."
```

---

### 3. ASK_CLARIFICATION
**When**: Low comprehension (regardless of foundation)  
**Meaning**: "I don't understand the request"  
**Action**: Ask user for clarification

**Example**:
```python
# clarity=0.30, signal=0.40, know=0.70, context=0.80
decision = decide_goal_creation(
    clarity=0.30, signal=0.40, know=0.70, context=0.80
)
# → should_create_goal_now: False
# → suggested_action: 'ask_clarification'
# → reasoning: "Cannot create goal: request is unclear (low clarity 
#              and signal). Should ask for clarification."
```

---

## CASCADE Integration

### Full Flow

```
1. BOOTSTRAP
   ↓
2. PREFLIGHT (assess epistemic state)
   ├─ 13 epistemic vectors assessed
   └─ Returns: clarity, signal, know, context, etc.
   ↓
3. DECISION LOGIC (automatic check)
   ├─ Checks: clarity ≥ 0.6 AND signal ≥ 0.5?
   ├─ Checks: know ≥ 0.5 AND context ≥ 0.5?
   └─ Returns: create_goal / investigate_first / ask_clarification
   ↓
4. EPISTEMIC BUS (optional)
   └─ Publishes GOAL_DECISION_MADE event for observers
   ↓
5. AI DECIDES (based on guidance)
   ├─ If create_goal → CREATE GOAL → ACT
   ├─ If investigate_first → INVESTIGATE → CHECK → (loop or ACT)
   └─ If ask_clarification → ASK USER → (restart with new info)
```

### Code Example

```python
from empirica.core.metacognitive_cascade import MetacognitiveCascade
from empirica.core.goals.decision_logic import decide_goal_creation

# 1. PREFLIGHT
cascade = MetacognitiveCascade(agent_id="my-agent")
preflight_result = await cascade.preflight(task, context)

# 2. DECISION LOGIC (automatic in CASCADE)
decision = decide_goal_creation(
    clarity=preflight_result.clarity,
    signal=preflight_result.signal,
    know=preflight_result.know,
    context=preflight_result.context
)

# 3. AI SEES GUIDANCE
print(format_decision_for_ai(decision))
# Output:
# 📊 Goal Creation Decision:
# 
# Assessment:
#   • Clarity: 0.85
#   • Signal: 0.80
#   • Know: 0.70
#   • Context: 0.80
# 
# Reasoning: Clear request and sufficient foundation. Ready to create goal.
# Suggested Action: CREATE_GOAL
# Confidence in Decision: 0.70
```

---

## Configurable Thresholds

Default thresholds can be adjusted via MCO personas:

```python
DEFAULT_THRESHOLDS = {
    'clarity': 0.6,   # Request must be reasonably clear
    'signal': 0.5,    # Information quality must be acceptable
    'know': 0.5,      # Must have some domain knowledge
    'context': 0.5    # Must understand environment
}
```

**MCO Integration**: Different personas can have different thresholds:
- **Researcher**: Lower `know` threshold (0.3) - comfortable with uncertainty
- **Implementer**: Higher `know` threshold (0.7) - needs solid foundation
- **Learner**: Lower all thresholds - willing to explore

See [24_MCO_ARCHITECTURE.md](file:///home/yogapad/empirical-ai/empirica/docs/production/24_MCO_ARCHITECTURE.md) for persona configuration.

---

## Epistemic Bus Integration

Decision logic publishes events for external observers (Sentinels, MCO):

```python
# Event published automatically
{
  "event_type": "goal_decision_made",
  "agent_id": "my-agent",
  "session_id": "session-123",
  "data": {
    "should_create_goal_now": true,
    "suggested_action": "create_goal",
    "clarity": 0.85,
    "signal": 0.80,
    "know": 0.70,
    "context": 0.80,
    "confidence": 0.70,
    "reasoning": "Clear request and sufficient foundation..."
  }
}
```

**Observers can**:
- Monitor decision patterns
- Suggest routing to specialist AIs
- Track comprehension/foundation trends
- Alert on repeated `ask_clarification` (spinning)

---

## Practical Examples

### Example 1: Bug Fix (Clear and Ready)

```python
# User: "Fix token validation bug in auth.py"
# AI PREFLIGHT assessment:
decision = decide_goal_creation(
    clarity=0.85,  # Clear: knows what to fix
    signal=0.80,   # Good: specific file mentioned
    know=0.70,     # Knows auth system
    context=0.80   # Understands codebase
)

# Result: CREATE_GOAL
# AI creates goal and proceeds immediately
```

---

### Example 2: New Feature (Clear but Need Learning)

```python
# User: "Implement WebAssembly module"
# AI PREFLIGHT assessment:
decision = decide_goal_creation(
    clarity=0.80,  # Clear: knows what to implement
    signal=0.75,   # Good: specific technology
    know=0.30,     # LOW: doesn't know WebAssembly well
    context=0.70   # Understands project structure
)

# Result: INVESTIGATE_FIRST
# AI investigates WebAssembly, then creates goal
```

---

### Example 3: Vague Request (Unclear)

```python
# User: "Something's broken"
# AI PREFLIGHT assessment:
decision = decide_goal_creation(
    clarity=0.30,  # LOW: unclear what's broken
    signal=0.40,   # LOW: no specific information
    know=0.70,     # Knows codebase (irrelevant)
    context=0.80   # Understands environment (irrelevant)
)

# Result: ASK_CLARIFICATION
# AI asks: "What specifically is broken? Can you provide error messages?"
```

---

## Philosophy

### Guidance, Not Prescription

**Important**: Decision logic provides **guidance**, not commands. The AI can override based on context.

**Example**:
```python
decision = decide_goal_creation(...)
# decision.suggested_action == 'investigate_first'

# But AI might decide:
# "Actually, I can create a minimal goal now and refine it during investigation"
# This is acceptable - AI agency is preserved
```

### Epistemic Transparency

The decision logic embodies Empirica's core principle: **know what you know, know what you don't know, act accordingly**.

- High clarity + signal → "I understand"
- High know + context → "I can operate"
- Both → "I'm ready to create a goal"
- Neither → "I need help"

---

## Related Documentation

- [06_CASCADE_FLOW.md](file:///home/yogapad/empirical-ai/empirica/docs/production/06_CASCADE_FLOW.md) - CASCADE phases
- [25_SCOPEVECTOR_GUIDE.md](file:///home/yogapad/empirical-ai/empirica/docs/production/25_SCOPEVECTOR_GUIDE.md) - Goal scoping
- [24_MCO_ARCHITECTURE.md](file:///home/yogapad/empirical-ai/empirica/docs/production/24_MCO_ARCHITECTURE.md) - Threshold configuration
- [20_TOOL_CATALOG.md](file:///home/yogapad/empirical-ai/empirica/docs/production/20_TOOL_CATALOG.md) - Goal management tools

---

## Implementation Details

For implementation details, see:
- `empirica/core/goals/decision_logic.py` - Decision logic implementation
- `empirica/core/epistemic_bus.py` - Event bus
- `docs/archive/session-logs/EPISTEMIC_BUS_INTEGRATION_COMPLETE.md` - Integration summary
