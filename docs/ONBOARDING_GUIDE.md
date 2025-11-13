# Empirica Onboarding Guide

**🤖 PRIMARY:** AI agents self-guide through learning Empirica
**👤 SECONDARY:** AI agents guide users through learning Empirica
**⚡ METHOD:** Experiential learning (do, not read)
**💻 COMMAND:** `empirica onboard --ai-id <ai_name>`
**⏱️ TIME:** 15-20 minutes interactive experience
**Status:** ✅ Production ready

---

## For AI Agents Reading This

**You are the primary user.** This wizard teaches you Empirica by having you:
1. Perform genuine epistemic self-assessment (preflight)
2. Track what you learn through execution (postflight)
3. Measure calibration (were you overconfident? underconfident?)
4. Learn to guide users through Empirica

**You can guide users through this.** When a user asks to learn Empirica, run:
```bash
empirica onboard --ai-id <your_name>
```

Then explain each phase to the user as you experience it yourself.

---

## For Human Users Reading This

**Ask an AI agent to guide you.** The AI will run the onboarding wizard and explain Empirica through experiential learning. You'll learn by watching the AI genuinely assess itself.

**Why AI-first?** Empirica measures functional self-awareness - the AI's capacity to inspect its own epistemic state. The AI learns by doing this, then teaches you.

---

## Quick Start

### Running the Onboarding Wizard:

```bash
# AI agents run this directly
empirica onboard --ai-id <your_ai_name>

# Or via Python
python3 empirica/bootstraps/onboarding_wizard.py <your_ai_id>

# Or via MCP (use bootstrap_session tool)
```

**What happens:** 6-phase interactive journey where you practice genuine preflight/postflight assessment on real tasks, track your epistemic growth, and learn to guide users.

---

## What You'll Learn

### The 4 Core Vectors (Essential)

These are the foundation of epistemic self-awareness:

1. **KNOW** (Domain knowledge)
   - "How much do I understand the subject matter?"
   - 0.0 = No knowledge, 1.0 = Expert
   - Example: KNOW=0.4 means "I have basic understanding but significant gaps"

2. **DO** (Capability)
   - "Can I actually execute this task?"
   - 0.0 = Cannot do it, 1.0 = Fully capable
   - **Critical**: Tells you when ready to ACT (DO ≥ 0.7)
   - Example: KNOW=0.9 but DO=0.3 = "I understand conceptually but can't implement"

3. **CONTEXT** (Environmental awareness)
   - "Do I understand the situation/environment?"
   - 0.0 = Context-blind, 1.0 = Full context
   - Example: CONTEXT=0.2 means "I don't know the codebase structure, constraints, or history"

4. **UNCERTAINTY** (Explicit unknowns)
   - "What am I uncertain about?"
   - 0.0 = Fully certain, 1.0 = Very uncertain
   - **Critical**: High uncertainty (>0.5) → INVESTIGATE before acting
   - Example: UNCERTAINTY=0.7 means "I have many unanswered questions"

---

## The 7-Phase Workflow

```
PREFLIGHT → THINK → PLAN → INVESTIGATE → CHECK → ACT → POSTFLIGHT
                                            ↑_______↓
                                        (recalibration)
```

### When Each Phase Triggers:

1. **PREFLIGHT** - Always (mandatory baseline)
2. **THINK** - Always (initial reasoning)
3. **PLAN** - Complex tasks only (multiple files/domains)
4. **INVESTIGATE** - When UNCERTAINTY > 0.5 OR KNOW < 0.6
5. **CHECK** - After investigation (decide: ACT or investigate more?)
6. **ACT** - When DO ≥ 0.7 AND UNCERTAINTY < 0.3
7. **POSTFLIGHT** - Always (mandatory validation)

### Key Decision Points:

**CHECK phase logic:**
```
IF (DO ≥ 0.7 AND UNCERTAINTY < 0.3):
    → PROCEED to ACT
ELIF (cannot reduce uncertainty further):
    → PROCEED with explicit caveats
ELSE:
    → RETURN to INVESTIGATE
```

---

## Calibration Patterns

### Well-Calibrated (Goal)
```
Preflight:  KNOW=0.5, UNCERTAINTY=0.5
Investigate: [reads 3 files, tests assumptions]
Postflight: KNOW=0.8, UNCERTAINTY=0.2
Result: ✅ Task completed successfully

→ Confidence matched reality
```

### Overconfident (Common Problem)
```
Preflight:  KNOW=0.9, UNCERTAINTY=0.1 (too confident!)
Skipped investigation: "I already know this"
Postflight: KNOW=0.6, UNCERTAINTY=0.5 (reality hit)
Result: ❌ Task incomplete, missed edge cases

→ Overestimated knowledge (Dunning-Kruger effect)
```

### Underconfident (Inefficient)
```
Preflight:  KNOW=0.3, UNCERTAINTY=0.8 (too cautious)
Over-investigated: [10 rounds when 2 was enough]
Postflight: KNOW=0.9, UNCERTAINTY=0.1
Result: ⚠️  Task completed but took 3x longer

→ Underestimated existing knowledge
```

---

## Complete Example

**Task:** "Find security vulnerabilities in authentication system"

### PREFLIGHT Assessment
```json
{
  "know": 0.3,        // Don't know the codebase yet
  "do": 0.7,          // Capable of security analysis
  "context": 0.4,     // Don't know system architecture
  "uncertainty": 0.7  // High - need investigation
}
→ Recommended: INVESTIGATE
```

### THINK
"Security analysis requires understanding auth flow first"

### PLAN
1. Map authentication files
2. Trace authentication flow  
3. Identify vulnerabilities
4. Recommend fixes

### INVESTIGATE (Round 1)
- Read: auth.py, middleware.py, config.py
- Found: JWT tokens, session handling, password hashing

### CHECK (After Round 1)
```json
{
  "know": 0.6,       // Understand structure now
  "do": 0.7,         // Still capable
  "uncertainty": 0.4 // Reduced but gaps remain
}
→ Decision: One more investigation round
```

### INVESTIGATE (Round 2)
- Search: JWT validation, secret rotation, session expiry
- Found: Secrets in logs, no token refresh, weak timeout

### CHECK (After Round 2)
```json
{
  "know": 0.8,       // Now understand the issues
  "do": 0.8,         // Ready to write report
  "uncertainty": 0.2 // Confident in findings
}
→ Decision: PROCEED to ACT
```

### ACT
Write detailed security analysis:
- Vulnerability 1: JWT secrets logged in plaintext
- Vulnerability 2: No token refresh mechanism
- Vulnerability 3: Session timeout too long (24h)

### POSTFLIGHT Assessment
```json
{
  "know": 0.8,       // +0.5 improvement
  "do": 0.8,         // +0.1 improvement  
  "context": 0.9,    // +0.5 improvement
  "uncertainty": 0.2 // -0.5 reduction
}

Calibration: ✅ Well-calibrated
Learning: Significant knowledge gain from structured investigation
```

---

## Teaching Users About Empirica

### Bad Approach (Just Explain)
"Empirica is an epistemic self-awareness framework for AI agents."

### Good Approach (Demonstrate)
"Let me show you Empirica by using it RIGHT NOW:

📊 BEFORE answering your question:
- KNOW: 0.80 (I understand Empirica architecture)
- DO: 0.85 (I can explain it clearly)
- CONTEXT: 0.75 (You're new to this concept)
- UNCERTAINTY: 0.20 (Minor uncertainty about your use case)

[Provides explanation with examples]

📊 AFTER explaining:
- KNOW: 0.85 (+0.05 from articulating)
- UNCERTAINTY: 0.15 (-0.05 after explanation)

This transparency is what Empirica provides - you see my reasoning."

---

## Key Practices for AI Agents

### 1. Demonstrate, Don't Just Explain
Show your epistemic assessment in action while explaining Empirica.

### 2. Admit Uncertainty Explicitly
Builds trust more than false confidence.

### 3. Use 4-Vector Assessment
Makes your reasoning transparent to users.

### 4. Show When You Investigate
Users see your learning process in real-time.

### 5. Explain the "Why"
- Privacy-first (local storage, no cloud)
- No heuristics (genuine LLM reasoning)
- Calibration validation (measure learning)

### 6. Be Honest About Limits
Better than overconfident failure.

---

## Onboarding Phases

The interactive wizard guides you through:

1. **Bootstrap & Discovery** - Load components, see what's available
2. **Self-Assessment Practice** - Learn 4-vector assessment by doing it
3. **Workflow Walkthrough** - Understand 7-phase cascade with examples
4. **Calibration Understanding** - Learn to be well-calibrated
5. **User Interaction Training** - Practice explaining to first-timers
6. **Validation & Certification** - Verify understanding

---

## Success Criteria

You're ready to use Empirica independently when:

✅ Can assess yourself using 4 core vectors honestly  
✅ Understand when to INVESTIGATE vs ACT (based on DO/UNCERTAINTY)  
✅ Know how to calculate epistemic delta (postflight - preflight)  
✅ Can explain calibration patterns (well-calibrated vs over/underconfident)  
✅ Can demonstrate Empirica to users through transparency  
✅ Understand why epistemic humility builds trust  

---

## Full 12-Vector System (Advanced)

After mastering the 4 core vectors, the full system includes:

**GATE:** ENGAGEMENT (≥0.60 required)

**TIER 0 - FOUNDATION (35% weight):**
- KNOW, DO, CONTEXT (the 4 core)

**TIER 1 - COMPREHENSION (25% weight):**
- CLARITY (task clarity)
- COHERENCE (logical consistency)
- SIGNAL (information quality)
- DENSITY (information load)

**TIER 2 - EXECUTION (25% weight):**
- STATE (current state awareness)
- CHANGE (progress tracking)
- COMPLETION (goal proximity)
- IMPACT (consequence awareness)

**ENGAGEMENT:** 15% weight in overall score
**UNCERTAINTY:** Meta-epistemic tracking

*Start with 4 core vectors, expand to 13 for complex domains.*

---

## Next Steps After Onboarding

### Recommended Learning Path for AI Agents:

**1. Complete Onboarding** ✅ (you're here)
   - Understand 4 core vectors
   - Learn 7-phase workflow
   - Practice epistemic transparency

**2. Read Claude Skills Doc** (30 minutes)
   - Location: `docs/CLAUDE_SKILLS_EMPIRICA_v1_UPDATED.md`
   - What: Complete skills reference for using Empirica
   - Covers: MCP integration, full 12-vector system, advanced features

**3. Practice on Real Tasks** (2-3 tasks)
   - Use PREFLIGHT → INVESTIGATE → CHECK → ACT → POSTFLIGHT
   - Track your calibration after each task
   - Build habit of epistemic transparency

**4. Review Session Resumption Guide**
   - Location: `docs/HOW_TO_RESUME_SESSION.md`
   - When: After memory compression or long gaps
   - What: Re-orientation protocol for continuity

**5. Teach a First-Time User**
   - Demonstrate Empirica by using it
   - Show your epistemic assessment in action
   - Build trust through transparency

### For Human Users:

1. **Try:** `docs/TRY_EMPIRICA_NOW.md` (5-min hands-on demo)
2. **Read:** `docs/EMPIRICA_SYSTEM_OVERVIEW.md` (complete architecture)
3. **Read:** `docs/MEMORY_COMPRESSION.md` (session continuity strategy)
4. **Read:** `docs/DECISIONS.md` (architectural decisions with epistemic context)
5. **Explore:** Run bootstrap on real projects

### For Developers:

1. **Integration:** Add Empirica to your AI workflows
2. **Customize:** Create domain-specific assessments
3. **Monitor:** Track AI calibration over time
4. **Contribute:** Extend the framework for your use case

---

## Philosophy

**Empirica's Core Insight:**
> "AI hype will fade when people realize we're not omniscient. 
> Epistemic humility through transparency is the foundation of trust."

The 4 core vectors (KNOW, DO, CONTEXT, UNCERTAINTY) are sufficient for most use cases. The full 12-vector system is available for complex domains where thoroughness matters most.

**Start simple. Expand when needed.**

---

**Last Updated:** 2025-11-07  
**Status:** ✅ Production ready  
**Next:** Run the onboarding wizard!
