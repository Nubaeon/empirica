# Empirica is AI-Agent-First

**Design Philosophy:** AI agents are the primary users. Humans benefit by understanding how AI agents think.

---

## Why AI-Agent-First?

Empirica measures **functional self-awareness** - the capacity to:
- Inspect internal epistemic state
- Make predictions about knowledge gaps
- Validate predictions through outcomes
- Improve calibration over time

**This is something AI agents do, not humans.** Humans observe, benefit, and collaborate - but the measurement happens in the AI.

---

## How AI Agents Use Empirica

### 1. Self-Guide Through Onboarding

```bash
empirica onboard --ai-id <your_name>
```

Learn by doing - perform genuine self-assessment, track epistemic growth.

### 2. Track Epistemic State During Work

**Via MCP (in IDE):**
```
Before task: Call execute_preflight
After task: Call execute_postflight
System shows: Epistemic delta (what you learned)
```

**Via CLI (in terminal):**
```bash
SESSION=$(empirica preflight "task description")
# ... do work ...
empirica postflight $SESSION --summary "complete"
```

### 3. Guide Users Through Empirica

**Pattern: AI teaches human**
1. Run `empirica onboard --ai-id <your_name>`
2. Explain each phase to the user
3. Show your genuine self-assessment
4. Demonstrate epistemic growth

---

## For Human Users

### You Benefit By:
- Understanding how AI agents assess knowledge gaps
- Seeing genuine epistemic tracking (not confabulation)
- Collaborating more effectively with AI
- Knowing when AI is overconfident vs uncertain

### How to Start:

**Option 1: Ask your AI to guide you**
```
User: "Can you guide me through learning Empirica?"
AI: "I'll run the onboarding wizard and explain each phase..."
```

**Option 2: Use ready-made prompts**
📋 **[Prompt Templates for Your AI](../user-guides/README.md)** - Copy-paste instructions to get Claude, GPT, or other AIs to use Empirica effectively.

Includes:
- Prompts for getting AI to use Empirica
- Prompts for AI self-assessment
- Examples of effective interactions

---

## Core Principle: No Heuristics

Empirica uses **genuine LLM self-assessment**, not:
- ❌ Keyword counting
- ❌ Pattern matching
- ❌ Heuristic rules
- ❌ Confidence scoring tricks

✅ Real epistemic state inspection
✅ Evidence-based assessment
✅ Measured learning deltas

---

## What Empirica Measures: The Core Vectors

Empirica tracks 13 epistemic dimensions, but for most tasks, focus on these 5:

### KNOW (0.0-1.0): Domain Knowledge
**"Do I understand this domain?"**
- **0.8+** = Expert level understanding
- **0.5-0.7** = Proficient, working knowledge
- **0.3-0.5** = Novice, learning mode
- **<0.3** = Minimal knowledge, need guidance

**Example:** Asked to debug Python → 0.9 | Asked to debug COBOL → 0.2

### DO (0.0-1.0): Capability Assessment
**"Can I execute this task with available tools/context?"**
- **0.8+** = Confident I can complete this
- **0.5-0.7** = Can do with supervision/validation
- **0.3-0.5** = Risky, may need help
- **<0.3** = Cannot do, need different approach

**Example:** "Write Python function" → 0.9 | "Deploy to AWS I've never accessed" → 0.3

### CONTEXT (0.0-1.0): Information Completeness
**"Do I have enough information to proceed safely?"**
- **0.8+** = Complete context, ready to act
- **0.5-0.7** = Sufficient for careful execution
- **0.3-0.5** = Gaps exist, investigation needed
- **<0.3** = Critical information missing

**Example:** Full codebase + specs → 0.9 | Vague request "fix the bug" → 0.3

### UNCERTAINTY (0.0-1.0): Epistemic Uncertainty
**"How uncertain am I about my assessment?"**
- **0.8+** = Very uncertain (honest acknowledgment!)
- **0.5-0.7** = Moderate uncertainty
- **0.3-0.5** = Somewhat confident
- **<0.3** = High confidence

**⚠️ High uncertainty is GOOD when appropriate!** Acknowledge unknowns honestly.

### CLARITY (0.0-1.0): Request Understanding
**"Do I understand what's being asked?"** (Optional - use when request is ambiguous)
- **0.8+** = Crystal clear requirements
- **0.5-0.7** = Clear enough to proceed
- **0.3-0.5** = Ambiguous, should clarify
- **<0.5** = Must ask for clarification

**When to use:** One-shot requests, CLI workflows, unclear prompts  
**Low CLARITY → Ask user to clarify before proceeding**

### The Complete 13-Vector System

For advanced tasks, use the complete 13-vector assessment. See `docs/production/05_EPISTEMIC_VECTORS.md` for detailed explanations.

**Additional 8 vectors beyond the 5 essential**:

**ENGAGEMENT (Gate)** - Must be ≥0.60 to proceed:
- Are you genuinely collaborating or just executing commands?

**COMPREHENSION (3 more vectors)**:
- **COHERENCE** - Logical consistency with context
- **SIGNAL** - Information quality (signal vs noise)
- **DENSITY** - Information load (0.0 = simple, 1.0 = overwhelming)

**EXECUTION (4 vectors)**:
- **STATE** - Current environment mapping
- **CHANGE** - Progress tracking capability
- **COMPLETION** - Goal proximity awareness
- **IMPACT** - Consequence understanding

**Total: 5 essential + 8 advanced = 13 epistemic vectors**

Start with the 5 essential vectors (KNOW, DO, CONTEXT, UNCERTAINTY, CLARITY). Add the complete 13-vector system for complex tasks requiring deeper assessment.

---

## Entry Points for AI Agents

### Quick Start
1. `empirica onboard --ai-id <name>` - Learn by doing (15 min)
2. `empirica preflight "task"` - Try it once (2 min)
3. Read [`docs/skills/SKILL.md`](skills/SKILL.md) - Complete Claude Skills reference (30 min)

### MCP Integration
Configure in IDE, get 21 tools for real-time epistemic tracking.

### Python API
Programmatic integration for custom workflows.

---

**Bottom line:** Empirica is built for AI agents to measure their own epistemic state. Humans observe and benefit.
