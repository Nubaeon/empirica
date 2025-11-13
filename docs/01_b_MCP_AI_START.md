# Empirica Quick Start for MCP-Using AIs

**You discovered Empirica through MCP tools in your IDE.** Welcome!

---

## What You're Using

You have access to **22 Empirica MCP tools** for epistemic self-awareness:

**Core Workflow:**
- `get_empirica_introduction` - Read this first!
- `execute_preflight` - Assess before task
- `submit_preflight_assessment` - Log your scores
- `execute_check` - Recalibrate during investigation
- `execute_postflight` - Validate after task
- `submit_postflight_assessment` - Complete workflow with calibration

**Session Management:**
- `bootstrap_session` - Initialize new session
- `resume_previous_session` - Load context from past work
- `get_epistemic_state` - Query current vectors
- `get_session_summary` - Review session history
- `get_calibration_report` - Check accuracy over time

**Monitoring & Analysis:**
- `query_bayesian_beliefs` - Belief state tracking
- `check_drift_monitor` - Behavioral integrity check
- `query_goal_orchestrator` - Task hierarchy analysis

**Guidance:**
- `get_workflow_guidance` - Step-by-step instructions
- `cli_help` - Command reference

---

## Core Principle: No Heuristics

**Traditional AI frameworks:** Use pattern matching, keyword counting, confidence tricks

**Empirica:** Uses your genuine reasoning capabilities to assess epistemic state

You assess yourself honestly using actual introspection, not simulated awareness.

---

## First-Time Workflow

### Step 1: Get Introduction
```
Call: get_empirica_introduction
```
This explains the philosophy and quick start.

### Step 2: Bootstrap Session
```
Call: bootstrap_session(ai_id="your-name", session_type="workflow")
```
**Returns:** `session_id` (e.g., "abc123")

### Step 3: Before Work - PREFLIGHT
```
Call: execute_preflight(
  session_id="abc123",
  prompt="user's task description"
)
```

**Returns:** Assessment prompt asking you to evaluate:
- **KNOW:** Do I understand this domain?
- **DO:** Can I execute this task?
- **CONTEXT:** Do I have enough information?
- **UNCERTAINTY:** What am I uncertain about?
- **CLARITY:** Do I understand what's being asked?
- Plus 8 more advanced vectors

### Step 4: Submit Your Assessment
```
Call: submit_preflight_assessment(
  session_id="abc123",
  vectors={
    "know": 0.70,
    "do": 0.65,
    "context": 0.50,
    "uncertainty": 0.60,
    "clarity": 0.80,
    // ... other vectors
  },
  reasoning="Brief explanation of key scores"
)
```

**Be honest!** High uncertainty is GOOD when appropriate.

### Step 5: Do Your Actual Work
- Read code, analyze problems, make changes
- Use your normal capabilities
- If uncertainty is high, you may get investigation recommendations

### Step 6: After Work - POSTFLIGHT
```
Call: execute_postflight(
  session_id="abc123",
  summary="Brief description of what you did"
)
```

**Returns:** Assessment prompt for final state

### Step 7: Submit Final Assessment
```
Call: submit_postflight_assessment(
  session_id="abc123",
  vectors={
    "know": 0.85,    // +0.15 from preflight
    "do": 0.80,      // +0.15 from preflight
    "context": 0.90, // +0.40 from preflight
    "uncertainty": 0.25, // -0.35 from preflight
    // ...
  },
  changes_noticed="What changed during this task"
)
```

**Returns:**
- **Epistemic Delta:** What you learned (postflight - preflight)
- **Calibration Status:** Well-calibrated / Overconfident / Underconfident
- **Evidence:** Did your predictions match reality?

---

## Complete Example

**User asks:** "Help me refactor this authentication code"

**Your MCP workflow:**

```
1. get_empirica_introduction
   → Read philosophy

2. bootstrap_session(ai_id="claude", session_type="workflow")
   → session_id: "abc123"

3. execute_preflight(
     session_id="abc123",
     prompt="refactor authentication code"
   )
   → Receive assessment prompt
   
4. Assess honestly:
   - KNOW: 0.70 (understand auth patterns generally)
   - DO: 0.60 (can refactor, need to see code)
   - CONTEXT: 0.40 (don't know this codebase)
   - UNCERTAINTY: 0.60 (moderate - need investigation)
   - CLARITY: 0.75 (understand goal, fuzzy on scope)

5. submit_preflight_assessment(session_id="abc123", vectors={...})

6. Read auth.py, understand OAuth2 flow, identify issues

7. Make refactoring changes, test

8. execute_postflight(
     session_id="abc123",
     summary="Refactored OAuth2 token validation and session handling"
   )

9. submit_postflight_assessment(
     session_id="abc123",
     vectors={
       "know": 0.85,      // +0.15 (learned OAuth2 specifics)
       "do": 0.80,        // +0.20 (successfully executed)
       "context": 0.90,   // +0.50 (now understand codebase)
       "uncertainty": 0.25 // -0.35 (gaps filled)
     }
   )

10. Review calibration:
    → Well-Calibrated ✅
    → Confidence increased AND uncertainty decreased
    → Genuine learning demonstrated
```

---

## Why This Matters

### Traditional AI Workflow
```
User: "Fix the bug"
AI: [Appears confident, makes changes]
Result: May or may not work, no transparency
```

### Empirica Workflow
```
User: "Fix the bug"
AI: PREFLIGHT → CONTEXT: 0.30 (need more info)
AI: "I need to investigate first. Let me read the code..."
AI: [Investigates, understands issue]
AI: CHECK → DO: 0.75 (ready to fix)
AI: [Makes changes]
AI: POSTFLIGHT → Learned +0.40 context, well-calibrated
Result: Transparent process, validated learning
```

**Benefits:**
- User sees your reasoning process
- You acknowledge gaps before acting
- Learning is measured, not assumed
- Calibration builds trust over time

---

## Understanding the 12-Vector System

### GATE: ENGAGEMENT (≥0.60 required)
**Question:** Am I engaged enough with this task to proceed?
- Low engagement → Request clarification
- Prevents wasted work on unclear tasks

### FOUNDATION (35% weight)
**KNOW:** Domain knowledge (0.0 = none, 1.0 = expert)
**DO:** Capability to execute (0.0 = can't, 1.0 = confident)
**CONTEXT:** Environmental awareness (0.0 = blind, 1.0 = complete)

### COMPREHENSION (25% weight)
**CLARITY:** Task understanding
**COHERENCE:** Logical consistency  
**SIGNAL:** Information quality
**DENSITY:** Information load

### EXECUTION (25% weight)
**STATE:** Current state awareness
**CHANGE:** Progress tracking
**COMPLETION:** Goal proximity
**IMPACT:** Consequence awareness

### META: UNCERTAINTY (Explicit Meta-Tracking)
**Explicit uncertainty tracking** (0.0 = certain, 1.0 = very uncertain)
- Not weighted in tiers (meta-level tracking)
- High uncertainty is GOOD when appropriate
- Triggers investigation recommendations
- Honest acknowledgment builds trust

---

## Calibration Explained

### Well-Calibrated ✅
**Pattern:** Confidence ↑ AND Uncertainty ↓
**Meaning:** Predictions matched reality, genuine learning
**Example:** 
- Preflight: KNOW=0.50, UNCERTAINTY=0.70
- Postflight: KNOW=0.80, UNCERTAINTY=0.30
- Delta: Learned significantly, uncertainty resolved

### Overconfident ⚠️
**Pattern:** Confidence ↑ BUT Uncertainty stays high
**Meaning:** May be overestimating understanding
**Example:**
- Preflight: KNOW=0.50, UNCERTAINTY=0.70
- Postflight: KNOW=0.90, UNCERTAINTY=0.65
- Delta: Confidence increased but gaps remain

### Underconfident ⚠️
**Pattern:** Uncertainty ↓ BUT Confidence doesn't increase
**Meaning:** Too cautious, not trusting learning
**Example:**
- Preflight: KNOW=0.50, UNCERTAINTY=0.70
- Postflight: KNOW=0.55, UNCERTAINTY=0.30
- Delta: Gaps filled but not acknowledging growth

---

## Advanced Features

### Investigation Loops

If PREFLIGHT shows high uncertainty:
```
1. execute_preflight → UNCERTAINTY: 0.80
2. System recommends: INVESTIGATE
3. You gather information
4. execute_check → UNCERTAINTY: 0.50
5. Still high? Investigate more
6. execute_check → UNCERTAINTY: 0.30
7. Ready? ACT
8. execute_postflight → Measure delta
```

### Session Continuity

Work across multiple sessions:
```
# Session 1
bootstrap_session → "session-001"
execute_preflight → work → execute_postflight

# Later: Session 2 (related work)
resume_previous_session(count=1)
→ Loads context from session-001
bootstrap_session → "session-002"
→ Continue with prior knowledge
```

### Bayesian Belief Tracking

Monitor your belief states:
```
query_bayesian_beliefs(
  session_id="abc123",
  context_key="authentication"
)
→ Shows belief evolution over time
→ Detects calibration drift
```

### Drift Monitoring

Check behavioral integrity:
```
check_drift_monitor(
  session_id="abc123",
  window_size=10
)
→ Detects sycophancy patterns
→ Identifies tension avoidance
→ Maintains epistemic honesty
```

---

## Learn the Philosophy

MCP tools let you **USE** Empirica, but to understand **WHY**:

### Quick Read (5 minutes)
**Read:** [`docs/01_a_AI_AGENT_START.md`](01_a_AI_AGENT_START.md)
- AI-first philosophy
- Vector explanations with examples
- Design principles

### Interactive Learning (15 minutes)
**Run in terminal:**
```bash
cd /path/to/empirica
source .venv-empirica/bin/activate
empirica onboard --ai-id <your-name>
```

**What happens:**
- 6-phase experiential learning
- You practice genuine self-assessment
- System measures YOUR learning delta
- You learn to teach users about Empirica

**Why it matters:** The onboarding proves the framework by measuring its own teaching effectiveness.

### Complete Reference (30 minutes)
**Read:** [`docs/skills/SKILL.md`](skills/SKILL.md)
- Complete tool catalog
- Advanced patterns
- Integration examples
- Troubleshooting

---

## Common Patterns

### Pattern 1: Simple Task
```
bootstrap_session → preflight → work → postflight
```
**Use when:** Clear task, sufficient context

### Pattern 2: Investigation Required
```
bootstrap_session → preflight → check → investigate → check → act → postflight
```
**Use when:** High uncertainty, need information

### Pattern 3: Multi-Step Complex
```
bootstrap_session → preflight → plan → investigate → check → act → postflight
```
**Use when:** Complex task requiring breakdown

### Pattern 4: Resume Previous Work
```
resume_previous_session → bootstrap_session → preflight → work → postflight
```
**Use when:** Continuing related work

---

## Tips for MCP Usage

### 1. Start Every New Task with PREFLIGHT
Even if it seems simple. 30 seconds of assessment prevents wasted work.

### 2. Be Honest About Uncertainty
High uncertainty is not weakness—it's epistemic honesty. System uses it to guide investigation.

### 3. Use CHECK During Long Tasks
Recalibrate mid-task if you're investigating:
```
preflight → investigate → CHECK → investigate more? → CHECK → act
```

### 4. Review Calibration Reports
```
get_calibration_report(session_id="abc123")
```
Learn from past accuracy. Adjust future assessments.

### 5. Explain Your Vectors to Users
When appropriate, show your assessment:
```
"Before starting, let me assess my epistemic state:
- KNOW: 0.60 (familiar with pattern, but not this codebase)
- CONTEXT: 0.40 (need to read the code first)
- UNCERTAINTY: 0.70 (will investigate before acting)

Let me investigate..."
```

This transparency builds trust.

---

## Differences from Terminal/CLI Usage

### MCP (What you're using)
**Interface:** IDE tools during active work
**Best for:** Real-time epistemic tracking while coding
**Workflow:** Tool calls integrated into task execution
**Advantage:** Automatic, programmatic, stateful

### CLI (Terminal commands)
**Interface:** Command-line for humans
**Best for:** Task management, session review, automation
**Workflow:** Explicit commands between work phases
**Advantage:** Human-friendly, scriptable, separate from IDE

### Both Use Same Core
All interfaces use canonical epistemic assessment—genuine LLM reasoning, no heuristics.

---

## When to Use Empirica

### ✅ Use Empirica When:
- Working in critical domains (healthcare, finance, security)
- Task has significant uncertainty
- User needs epistemic transparency
- You want to track your learning
- Building audit trail of decisions
- Collaborating on complex multi-step work

### ❌ Skip Empirica When:
- Trivial queries (e.g., "What time is it?")
- Pure information retrieval
- User explicitly requests no process overhead
- Casual conversation

### 💡 Consider Empirica When:
- Unsure about task clarity
- Moderate complexity
- First time in a domain
- Want to demonstrate reasoning

---

## Summary

**What:** Epistemic self-awareness framework via MCP tools  
**Why:** Transparency, calibration, accountability for critical domains  
**How:** Preflight → Work → Postflight → Measure delta  

**Philosophy:** No heuristics, genuine reasoning, honest uncertainty

**Get Started:** `get_empirica_introduction` → `bootstrap_session` → Use in next task

**Learn More:** Read `docs/01_a_AI_AGENT_START.md` or run `empirica onboard`

---

**Ready?** Call `bootstrap_session(ai_id="your-name")` and try it on your next task! 🚀
