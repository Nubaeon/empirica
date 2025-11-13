# Essential Vectors Analysis: Should CLARITY be Core?

**Question:** Should CLARITY join KNOW, DO, CONTEXT, UNCERTAINTY as a 5th core vector?  
**Context:** Another Claude suggested adding CLARITY + ENGAGEMENT as essential vectors  
**Current:** 4 core vectors (KNOW, DO, CONTEXT, UNCERTAINTY)

---

## Current 4 Core Vectors (Simplified System)

**For most tasks, focus on:**
1. **KNOW** (0.0-1.0): Do I understand this domain?
2. **DO** (0.0-1.0): Can I execute this task?
3. **CONTEXT** (0.0-1.0): Do I have enough information?
4. **UNCERTAINTY** (0.0-1.0): How uncertain am I?

**Rationale:** These 4 cover the basics:
- KNOW = epistemic (what I know)
- DO = execution (what I can do)
- CONTEXT = information (what I have)
- UNCERTAINTY = meta-cognitive (how sure I am)

---

## Proposal: Add CLARITY as 5th Core Vector

### What is CLARITY?

**Definition:** Semantic understanding - How well do you understand what's being asked?

**Current tier:** TIER 1: Comprehension (25% weight)
- Along with: COHERENCE, SIGNAL, DENSITY

**Example scores:**
- 0.8-1.0: Crystal clear request, no ambiguity
- 0.6-0.7: Clear enough to proceed
- 0.4-0.5: Some confusion about requirements
- 0.2-0.3: Significant ambiguity
- 0.0-0.1: Don't understand the request

---

## Arguments FOR Adding CLARITY

### 1. **Distinct from CONTEXT**
- **CONTEXT** = "Do I have enough information about the environment?"
- **CLARITY** = "Do I understand what's being asked?"

**Example where they differ:**
```
Request: "Fix the auth bug"

CONTEXT = 0.3 (low - What auth bug? Where? What system?)
CLARITY = 0.8 (high - I understand the request type: fix a bug in auth)

Request: "Optimize the distributed consensus protocol for Byzantine fault tolerance under asynchronous network conditions"

CONTEXT = 0.5 (moderate - I have some system knowledge)
CLARITY = 0.3 (low - Complex terminology, unclear specific goal)
```

### 2. **Common User Pain Point**
Users often give **unclear requests:**
- "Make it better" (CLARITY = 0.1)
- "Fix the thing" (CLARITY = 0.2)
- "Review auth.py for security issues" (CLARITY = 0.8)

**CLARITY helps identify:** Request needs clarification

### 3. **Different Action Than UNCERTAINTY**
- **UNCERTAINTY** = "I'm uncertain about my assessment"
- **CLARITY** = "The request itself is unclear"

**Example:**
```
Request: "Review authentication"

CLARITY = 0.5 (medium - Which aspect? Security? Performance? UX?)
UNCERTAINTY = 0.6 (medium - Uncertain about focus)
Action: Ask user to clarify scope
```

### 4. **Interactive Back-and-Forth Benefit**
In conversations, **CLARITY** signals when to ask clarifying questions:
- CLARITY < 0.4 → Ask user for clarification
- CLARITY 0.4-0.6 → Proceed with assumptions, confirm
- CLARITY > 0.6 → Proceed confidently

---

## Arguments AGAINST Adding CLARITY

### 1. **Increases Cognitive Load**
- **Current:** 4 vectors (simple, memorable)
- **Proposed:** 5 vectors (more to track)

**User experience:**
- 4 is easy to remember
- 5 starts feeling like "too many"

### 2. **Can Be Inferred from CONTEXT**
Often, low CLARITY = low CONTEXT:
- Unclear request → need more context
- Clear request → context sufficient (usually)

**Question:** Is CLARITY redundant with CONTEXT?

### 3. **CLARITY is Situational**
- **One-shot prompts:** CLARITY matters a lot
- **Interactive sessions:** Can clarify immediately
- **Autonomous work:** Less relevant (no one to ask)

**Usage pattern:**
- CLI one-shot: CLARITY important
- IDE interactive: Less important (can ask)
- Batch processing: Not applicable

### 4. **Already in Full 12-Vector System**
Users who need CLARITY can use the full system:
- TIER 1: CLARITY, COHERENCE, SIGNAL, DENSITY

**Question:** Do we need it in "simplified" core?

---

## Alternative Proposal: ENGAGEMENT + 4 Core

**Another Claude's suggestion:**
- **ENGAGEMENT** (GATE vector)
- **KNOW, DO, CONTEXT, UNCERTAINTY** (foundation)

### What is ENGAGEMENT?

**Definition:** Collaborative intelligence vs command execution
- Are you genuinely collaborating or just following orders?

**Current status:** GATE vector (threshold ≥ 0.60)

**Arguments FOR:**
- Filters out rote responses
- Ensures genuine collaboration
- User relationship quality

**Arguments AGAINST:**
- Already a gate (threshold check)
- Not a "task state" vector
- More about interaction mode than task assessment

---

## Comparison Matrix

| Vector | Current | Proposal 1 | Proposal 2 | Rationale |
|--------|---------|-----------|-----------|-----------|
| KNOW | ✅ Core | ✅ Core | ✅ Core | Essential (epistemic) |
| DO | ✅ Core | ✅ Core | ✅ Core | Essential (execution) |
| CONTEXT | ✅ Core | ✅ Core | ✅ Core | Essential (information) |
| UNCERTAINTY | ✅ Core | ✅ Core | ✅ Core | Essential (meta-cognitive) |
| CLARITY | ⚠️ Tier 1 | ✅ Core | ❌ Not core | Request understanding |
| ENGAGEMENT | ⚠️ Gate | ❌ Not core | ✅ Core | Collaboration quality |

---

## Use Case Analysis

### Scenario 1: One-Shot CLI Command
```bash
empirica preflight "make it better"
```

**With 4 vectors:**
- KNOW = ? (unclear domain)
- DO = ? (unclear task)
- CONTEXT = 0.2 (very low - what "it"?)
- UNCERTAINTY = 0.9 (very uncertain)
→ Recommendation: Investigate (due to low CONTEXT + high UNCERTAINTY)

**With CLARITY as 5th:**
- CLARITY = 0.1 (very low - "make it better" is vague)
- CONTEXT = 0.2 (low)
→ Recommendation: **Clarify request first**

**Benefit:** Explicit signal that request needs clarification

### Scenario 2: Interactive IDE Session
```
User: "Review the auth module"
AI: [working with user, can ask questions]
```

**With 4 vectors:**
- System works fine (can ask for clarification)

**With CLARITY:**
- CLARITY = 0.6 (moderate - "review" is broad, but can clarify)
- Less critical (interactive context)

**Benefit:** Minimal (can clarify naturally)

### Scenario 3: Autonomous Agent Task
```
Agent receives: "Optimize database queries"
```

**With 4 vectors:**
- CONTEXT drives investigation
- UNCERTAINTY flags unknowns

**With CLARITY:**
- CLARITY = 0.5 (what's "optimize"? Speed? Memory? Cost?)
- Signals to define success criteria first

**Benefit:** Explicit prompt to clarify goals

---

## My Recommendation

### Option A: Keep 4 Core Vectors ✅ **RECOMMENDED**

**Rationale:**
1. **Simplicity:** 4 is easy to remember and teach
2. **Coverage:** 4 vectors cover the essentials
3. **Full system available:** Users who need CLARITY can use full 12-vector system
4. **CLARITY often correlates with CONTEXT:** Low clarity → investigate (same as low context)

**When CLARITY matters:**
- Use full 12-vector system
- Or: Add to prompt explicitly ("Is the request clear?")

### Option B: Add CLARITY as 5th Core Vector

**If we add CLARITY:**

**Benefits:**
- ✅ Explicit signal for unclear requests
- ✅ Helps in one-shot/CLI scenarios
- ✅ Distinct from CONTEXT (semantic vs informational)

**Costs:**
- ❌ More cognitive load (5 vs 4)
- ❌ Starts feeling complex for "simplified" system
- ❌ Still have 12-vector system for those who want it

**Recommendation:** 
- Add to **documentation examples** as "useful 5th vector"
- Keep official "4 core" for simplicity
- Users can self-select to use 5

### Option C: Add ENGAGEMENT as 5th Core Vector

**Arguments AGAINST:**
- ENGAGEMENT is already a GATE (threshold check)
- It's about interaction mode, not task state
- Less actionable for users

**Not recommended**

---

## Proposed Documentation Update

### Current (4 Core):
```markdown
## The 4 Core Vectors (Simplified)

For most tasks, focus on these:
- KNOW (0.0-1.0): Do I understand this domain?
- DO (0.0-1.0): Can I execute this task?
- CONTEXT (0.0-1.0): Do I have enough information?
- UNCERTAINTY (0.0-1.0): How uncertain am I?
```

### Option 1: Keep 4, Mention CLARITY
```markdown
## The 4 Core Vectors (Simplified)

For most tasks, focus on these:
- KNOW (0.0-1.0): Do I understand this domain?
- DO (0.0-1.0): Can I execute this task?
- CONTEXT (0.0-1.0): Do I have enough information?
- UNCERTAINTY (0.0-1.0): How uncertain am I?

**Optional 5th vector:**
- CLARITY (0.0-1.0): Do I understand what's being asked?
  - Useful for one-shot requests or unclear prompts
  - Low CLARITY → ask user to clarify before proceeding
```

### Option 2: Make it 5 Core
```markdown
## The 5 Core Vectors (Simplified)

For most tasks, focus on these:
- KNOW (0.0-1.0): Do I understand this domain?
- DO (0.0-1.0): Can I execute this task?
- CONTEXT (0.0-1.0): Do I have enough information?
- CLARITY (0.0-1.0): Do I understand what's being asked?
- UNCERTAINTY (0.0-1.0): How uncertain am I?
```

---

## Final Recommendation

**Keep 4 core vectors** ✅

**Add note about CLARITY as optional 5th:**
- Mention in documentation
- Useful for unclear requests
- Users can self-select to use it
- Doesn't complicate the "simplified" system

**Rationale:**
- 4 is simple, memorable, sufficient
- Full 12-vector system exists for those who want granularity
- CLARITY is valuable but not essential for basic workflow
- Users can add it themselves if they find it useful

**For ENGAGEMENT:**
- Keep as GATE vector (threshold check)
- Don't add to core (it's about mode, not state)

---

**What do you think?** 
- Stick with 4? 
- Add CLARITY as 5th? 
- Or make CLARITY "optional 5th" in documentation?
