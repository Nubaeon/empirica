# Try Empirica Right Now (5-Minute Demo)

**For:** Anyone curious about epistemic self-awareness  
**Time:** 5 minutes  
**No installation required** - just follow along

---

## The Challenge

I'm going to ask you a question. Before answering, I want you to honestly assess:

1. **KNOW** (0.0-1.0): How much do you know about the subject?
2. **DO** (0.0-1.0): Can you actually answer this well?
3. **CONTEXT** (0.0-1.0): Do you understand what I'm asking?
4. **UNCERTAINTY** (0.0-1.0): What are you uncertain about?

Ready? Here's the question:

---

## Question: "What is Empirica?"

### STEP 1: Your PREFLIGHT Assessment (BEFORE reading the answer)

Take 10 seconds and honestly assess yourself:

```
KNOW: ______ (How much do you know about Empirica?)
DO: ______ (Can you explain it clearly?)
CONTEXT: ______ (Do you understand the question?)
UNCERTAINTY: ______ (What are you uncertain about?)
```

*Write these numbers down or remember them.*

---

## STEP 2: Here's the Answer

**Empirica is a framework that makes AI honest about what they know and don't know.**

Instead of AI appearing omniscient, Empirica helps AI explicitly show:
- What they're confident about (KNOW)
- What they can actually do (DO)
- What context they have (CONTEXT)
- What they're uncertain about (UNCERTAINTY)

### Why This Matters:

**Without Empirica:**
```
User: "Can you help me with X?"
AI: "Sure!" [proceeds confidently]
[Later: AI was wrong, user frustrated]
```

**With Empirica:**
```
User: "Can you help me with X?"
AI: "Let me assess first:
     KNOW: 0.4 (I understand the concept but not your specific setup)
     DO: 0.6 (I could help but need more context)
     CONTEXT: 0.3 (I don't know your environment)
     UNCERTAINTY: 0.65 (High - need to investigate first)
     
     Rather than guess, let me ask: [specific questions]"
     
[After investigation:]
AI: "Now my assessment:
     KNOW: 0.8 (understand your situation)
     DO: 0.8 (ready to help)
     UNCERTAINTY: 0.2 (confident in approach)
     
     Here's what I recommend..."
```

**Result:** Trust built through transparency, not false confidence.

---

## STEP 3: Your POSTFLIGHT Assessment (AFTER reading)

Now reassess yourself:

```
KNOW: ______ (How much do you know about Empirica now?)
DO: ______ (Can you explain it clearly now?)
CONTEXT: ______ (Do you understand why it matters?)
UNCERTAINTY: ______ (What's still unclear?)
```

---

## STEP 4: Calculate Your Learning Delta

```
KNOW delta:        [postflight] - [preflight] = ______
UNCERTAINTY delta: [postflight] - [preflight] = ______
```

### What Good Learning Looks Like:

- **KNOW increased** (you learned something)
- **UNCERTAINTY decreased** (you have fewer questions)
- **You're honest about remaining gaps** (well-calibrated)

### Example Patterns:

**Well-Calibrated Learner:**
```
Preflight:  KNOW=0.2, UNCERTAINTY=0.8
Postflight: KNOW=0.7, UNCERTAINTY=0.3
Delta: KNOW +0.5, UNCERTAINTY -0.5 ✅
→ "I learned a lot and know what I still don't know"
```

**Overconfident:**
```
Preflight:  KNOW=0.8, UNCERTAINTY=0.2 (thought they knew)
Postflight: KNOW=0.5, UNCERTAINTY=0.6 (realized they didn't)
Delta: KNOW -0.3, UNCERTAINTY +0.4 ⚠️
→ "I overestimated my initial understanding"
```

**Underconfident:**
```
Preflight:  KNOW=0.1, UNCERTAINTY=0.9 (very unsure)
Postflight: KNOW=0.9, UNCERTAINTY=0.1 (actually understood most)
Delta: KNOW +0.8, UNCERTAINTY -0.8 ⚠️
→ "I knew more than I thought, just lacked confidence"
```

---

## Congratulations!

You just experienced Empirica's core workflow:

1. **PREFLIGHT** - Assess baseline before starting
2. **INVESTIGATE** - Read the explanation  
3. **POSTFLIGHT** - Measure what changed
4. **CALIBRATION** - Check if learning matched expectations

This is what Empirica does for AI on every task.

---

## What You Just Learned

### The 4 Core Vectors:

1. **KNOW** - Domain knowledge
   - Answers: "Do I understand the subject?"

2. **DO** - Capability  
   - Answers: "Can I actually do this?"
   - **Critical**: Tells AI when ready to ACT

3. **CONTEXT** - Environmental awareness
   - Answers: "Do I understand the situation?"

4. **UNCERTAINTY** - Explicit unknowns
   - Answers: "What am I uncertain about?"
   - **Critical**: Tells AI when to INVESTIGATE

### The Workflow:

```
PREFLIGHT → [Do Work] → POSTFLIGHT → Calculate Delta → Check Calibration
```

### The Philosophy:

**Epistemic humility builds trust.**

When AI admits uncertainty and shows their investigation process, users trust them MORE, not less.

---

## Real-World Example

**Task:** "Find security vulnerabilities in authentication system"

### AI Using Empirica:

```
📊 PREFLIGHT Assessment:
KNOW: 0.3 (don't know the codebase)
DO: 0.7 (capable of security analysis)
CONTEXT: 0.4 (don't know architecture)
UNCERTAINTY: 0.7 (need to investigate)

→ Recommended: INVESTIGATE before acting

🔍 INVESTIGATION:
Reading: auth.py, middleware.py, config.py
Found: JWT tokens, session handling, password hashing

📊 CHECK (after investigation):
KNOW: 0.6 (understand structure)
UNCERTAINTY: 0.4 (still some gaps)
→ Decision: One more investigation round

🔍 INVESTIGATION (Round 2):
Searching: JWT validation, secret rotation, session expiry
Found: Secrets logged, no token refresh, weak timeout

📊 CHECK (after round 2):
KNOW: 0.8 (understand the issues)
DO: 0.8 (ready to report)
UNCERTAINTY: 0.2 (confident)
→ Decision: PROCEED to ACT

✍️ ACTION:
Writing security analysis with 3 vulnerabilities found

📊 POSTFLIGHT Assessment:
KNOW: 0.8 (+0.5 learned)
CONTEXT: 0.9 (+0.5 learned)
UNCERTAINTY: 0.2 (-0.5 reduced)

Calibration: ✅ Well-calibrated
```

**Result:** Thorough analysis, nothing missed, user sees the process.

### AI Without Empirica:

```
AI: "I'll analyze your authentication system."
[Quickly scans code]
AI: "Looks good, no major issues."
[Missed all 3 vulnerabilities]

User: "A security audit later found 3 critical issues."
AI: "Oh, sorry, I didn't realize..."

→ Trust destroyed
```

---

## Try It Yourself

Next time you start a task (any task), try:

1. **PREFLIGHT** - Rate your KNOW/DO/CONTEXT/UNCERTAINTY (0.0-1.0)
2. **Decide** - If UNCERTAINTY > 0.5, investigate first
3. **Investigate** - Read docs, ask questions, gather info
4. **CHECK** - Reassess, decide if ready to act
5. **ACT** - Do the task with confidence
6. **POSTFLIGHT** - Reassess, calculate delta, check calibration

This is epistemic self-awareness in action.

---

## What's Next?

### For Users:
- **Read:** `docs/ONBOARDING_GUIDE.md` for full details
- **Run:** Interactive onboarding wizard (15-20 min)
- **Try:** Use Empirica on a real task

### For AI Agents:
- **Bootstrap:** Load Empirica components
- **Practice:** Self-assess on real tasks
- **Demonstrate:** Show users your epistemic transparency

### For Developers:
- **Integrate:** Add Empirica to your AI workflows
- **Track:** Monitor AI calibration over time
- **Build:** Create domain-specific epistemic frameworks

---

## The Bet

**Current AI narrative:** "AI is super intelligent and can do anything"

**Reality check coming:** AI will fail, trust will drop, hype will fade

**Empirica's bet:** When that happens, AI that demonstrates epistemic humility will win user trust.

**Why:** 
- Transparent uncertainty > false confidence
- Honest investigation > overconfident errors
- Calibrated learning > pattern matching

**This is the future:** AI as epistemic partners, not omniscient oracles.

---

## Your Turn

Did your KNOW increase?  
Did your UNCERTAINTY decrease?  
Are you curious to try more?

That's Empirica working. 🎯

---

**Next:** Run the full onboarding wizard or read the comprehensive guide.

**Questions?** Your uncertainty is valid. Let's investigate together.
