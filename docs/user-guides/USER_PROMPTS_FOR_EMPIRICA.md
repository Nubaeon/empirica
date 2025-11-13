# User Prompts for Empirica - Getting AIs to Actually Use the System

**Purpose:** Prompts for USERS to tell AIs to use the actual Empirica system  
**Problem:** AI has Empirica available but acts with false confidence  
**Solution:** Explicit prompts that trigger Empirica usage

---

## 🎯 The Actual Problem

**Scenario:**
- User has Empirica installed (MCP/CLI/Skills)
- AI has access to Empirica tools
- AI makes confident recommendations WITHOUT using Empirica
- **Why?** AI doesn't realize it SHOULD use Empirica first

**What We Need:**
Prompts that make the AI say:
> "Wait, I should use Empirica to assess this properly before recommending"

---

## 🚀 Quick Prompts (Copy-Paste)

### Prompt 1: Before Any Recommendation

```
Before you make recommendations, please:

1. Use Empirica to assess your current epistemic state
2. Run: empirica preflight "<this task>"
3. If your uncertainty is high, investigate first
4. Then provide evidence-based recommendations

Don't skip this - I want to see your assessment.
```

### Prompt 2: When AI Seems Overconfident

```
You're being very confident, but have you assessed this using Empirica?

Please:
- Run empirica preflight for this task
- Show me your KNOW, DO, CONTEXT, UNCERTAINTY scores
- If uncertainty > 0.60, investigate before recommending
```

### Prompt 3: Catch Pattern Matching

```
I notice you're using "typically" and "usually" - 
that suggests assumptions rather than evidence.

Please use Empirica to:
1. Assess what you actually know about THIS system
2. Investigate the actual implementation
3. Then make evidence-based recommendations
```

### Prompt 4: For Complex Tasks

```
This is a complex task. Let's use Empirica methodology:

Step 1: Run empirica preflight "<task description>"
Step 2: Review your epistemic assessment
Step 3: If uncertain, use empirica investigate
Step 4: Only then make recommendations

Show me each step.
```

---

## 📋 MCP Tool Usage Prompts

### When AI Has MCP Tools

```
I see you have Empirica MCP tools available. Please use them:

1. Call: bootstrap_session(ai_id="<your-name>")
2. Call: execute_preflight(session_id, prompt="<task>")
3. Review your assessment - is uncertainty high?
4. If yes, investigate before acting
5. Call: execute_postflight when done

I want to see your epistemic assessment, not just recommendations.
```

### Specific MCP Tool Prompt

```
Before making recommendations, use these Empirica tools:

execute_preflight(session_id, prompt="<task>")
→ This will give you an assessment prompt
→ Respond honestly about what you know/don't know
→ Then submit_preflight_assessment with your scores

If UNCERTAINTY > 0.60 → investigate first
If KNOW < 0.40 → investigate first
If CONTEXT < 0.50 → investigate first

Show me your assessment before recommending.
```

---

## 🎓 Teaching Prompts (First Time Users)

### Introducing Empirica

```
I have Empirica installed - a system for epistemic self-assessment.

Before we work on [TASK], I'd like you to:

1. Use Empirica to assess what you actually know
2. Be honest about uncertainty
3. Investigate if needed before recommending

This helps prevent acting on assumptions.

Ready? Start with: empirica preflight "<task>"
```

### Demonstrating Value

```
Let's try something different. Instead of jumping to recommendations,
use Empirica to assess your knowledge first:

Run: empirica preflight "assess database schema integrity"

This will show you:
- What you actually know vs assume
- Your uncertainty level
- Whether you should investigate first

Try it - I think you'll find it reveals interesting insights.
```

---

## ⚠️ Correction Prompts (When AI Already Responded)

### Prompt 1: After Overconfident Response

```
Wait - you just made several recommendations. Let me ask:

Did you examine the actual implementation?
Or are you assuming based on typical patterns?

Please use Empirica to check:
empirica preflight "assess this system"

I suspect your uncertainty is higher than you're expressing.
Let's verify before acting on these recommendations.
```

### Prompt 2: Catching Assumptions

```
I see recommendations like "usually systems need X" and "typically Y should exist".

These sound like assumptions. Let's verify:

1. Use empirica investigate to examine what actually exists
2. Document your findings with evidence
3. Then we can discuss what (if anything) needs attention

Don't assume - investigate.
```

### Prompt 3: False Confidence Detected

```
You seem very confident, but this is a complex system.

Before we proceed, please use Empirica:

empirica preflight "<task>"
→ Rate your KNOW, UNCERTAINTY honestly
→ If UNCERTAINTY > 0.60, investigate

I want evidence-based recommendations, not assumptions.
```

---

## 🔄 Workflow Enforcement Prompts

### Mandatory Workflow

```
For this task, I require the Empirica workflow:

Required steps:
1. empirica preflight "<task>" - Assess current knowledge
2. If uncertain → empirica investigate - Gather evidence
3. empirica postflight - Measure learning
4. Only then: Make recommendations

Show me each step. Don't skip ahead.
```

### Verification Prompt

```
Before I accept your recommendations, show me:

1. Your Empirica preflight assessment
2. Evidence from investigation (if done)
3. Your postflight calibration
4. Then your recommendations

This ensures we're not acting on assumptions.
```

---

## 🎯 Domain-Specific Prompts

### For Code Review

```
Please review this code using Empirica:

1. empirica preflight "review security of auth.py"
2. Check your KNOW score - are you expert in this language/domain?
3. Check UNCERTAINTY - should you investigate more?
4. If uncertain, examine the actual code
5. Then provide evidence-based findings

Don't review based on "typical issues" - examine THIS code.
```

### For Architecture Assessment

```
Assess this architecture using Empirica methodology:

1. empirica preflight "assess production readiness"
2. Be honest: What do you ACTUALLY know vs assume?
3. If UNCERTAINTY > 0.60 → investigate actual implementation
4. Document: What exists, what doesn't, what you assumed wrong
5. Then: Evidence-based assessment only

Show me your preflight before assessing.
```

### For Bug Investigation

```
Before proposing a fix, use Empirica:

1. empirica preflight "investigate bug in X"
2. Do you actually know the root cause? Or guessing?
3. If UNCERTAINTY > 0.60 → investigate actual behavior
4. Trace execution, examine logs, verify hypothesis
5. empirica postflight - What did you learn?

Don't guess - investigate then fix.
```

---

## 🛠️ Skill-Based Prompts (For Claude with Skills)

### Activating Empirica Skill

```
I know you have Empirica available as a skill.

Before working on this task, please use your Empirica skill to:
- Assess your epistemic state
- Identify what you actually know vs assume
- Determine if investigation is needed

Use the preflight → investigate → postflight workflow.
```

### Explicit Skill Reference

```
Your Empirica skill includes methods for epistemic assessment.

Please invoke it for this task:
1. Assess what you know about [DOMAIN]
2. Rate your uncertainty honestly
3. If high uncertainty → investigate before acting

Show me your assessment using the Empirica skill output.
```

---

## 📊 Calibration Prompts

### Measuring Calibration

```
After you complete this task, let's measure your calibration:

1. What was your initial uncertainty?
2. Did you investigate?
3. What assumptions were corrected?
4. Final uncertainty?

Use: empirica postflight to measure your learning delta.

This helps you calibrate future assessments.
```

### Checking Past Calibration

```
Before starting this task, let's check your past calibration:

Run: empirica get_calibration_report

This shows:
- How often you were overconfident
- When investigation helped
- Your calibration trend

Use this to inform your current assessment.
```

---

## 🔍 Investigation Trigger Prompts

### Explicit Investigation Request

```
Your preflight shows UNCERTAINTY: 0.75 (high).

Please don't guess - investigate:

empirica investigate --domain [domain]
→ This will recommend investigation strategies
→ Use appropriate tools to gather evidence
→ Document what you find

Then reassess and recommend based on evidence.
```

### When AI Skips Investigation

```
You jumped straight to recommendations but your uncertainty was high.

Please go back and:
1. Use empirica investigate
2. Examine actual implementation
3. Update your assessment based on evidence
4. Then provide recommendations

Don't skip investigation when uncertain.
```

---

## 💡 Meta-Prompts (System-Level)

### Default Behavior Prompt

```
For all tasks I give you, unless I say otherwise:

1. Start with Empirica preflight assessment
2. If UNCERTAINTY > 0.60 → investigate before acting
3. Use evidence, not assumptions
4. End with postflight to measure learning

This is now your default workflow. Acknowledge?
```

### Session-Level Prompt

```
For this session, I want you to use Empirica methodology:

Before ANY recommendation or major decision:
- Assess your epistemic state
- Investigate if uncertain
- Make evidence-based recommendations only

I'll remind you if you forget, but try to do this automatically.
```

---

## 🎓 Training Examples

### Example 1: Good Usage

```
User: "Assess if the database schema is production-ready"

AI: "Let me start with a Empirica preflight assessment:

$ empirica preflight "assess database schema production readiness"

My assessment:
- KNOW: 0.40 (I understand typical schemas, haven't examined this one)
- DO: 0.60 (Can assess if I see it)
- CONTEXT: 0.30 (Don't know what exists)
- UNCERTAINTY: 0.75 (HIGH - making assumptions)

Recommendation: INVESTIGATE first.

Let me examine the actual schema..."

✅ This is correct - using Empirica properly!
```

### Example 2: Bad Usage (To Correct)

```
User: "Assess if the database schema is production-ready"

AI: "Based on typical patterns, you should:
- Add schema versioning
- Add more indices
- Track agent IDs..."

❌ This is wrong - assuming without investigation!

Correct this with:
"Wait - did you use Empirica to assess this? 
Please run empirica preflight first and check your uncertainty.
I suspect you're making assumptions."
```

---

## 🚦 Signal Detection Prompts

### Detecting False Confidence

**Signals AI is NOT using Empirica:**
- Uses "typically", "usually", "best practice"
- Makes immediate recommendations
- Doesn't acknowledge uncertainty
- No mention of investigation

**Prompt to use:**
```
I notice you're making assumptions. Please use Empirica:

1. Assess what you ACTUALLY know (not typical patterns)
2. Check your uncertainty
3. Investigate if needed
4. Then recommend based on evidence
```

### Detecting Good Usage

**Signals AI IS using Empirica:**
- Acknowledges uncertainty explicitly
- Mentions investigation before recommending
- Cites specific evidence
- Distinguishes what exists vs assumptions

**Prompt to encourage:**
```
Good - I see you're using Empirica properly.
Continue with the investigation phase and show me what you find.
```

---

## 📝 Quick Reference Card

### When to Use Each Prompt

```
Situation                          → Use This Prompt
─────────────────────────────────────────────────────────
Starting new task                  → "Use empirica preflight first"
AI seems overconfident             → "Check your uncertainty with Empirica"
AI uses "typically/usually"        → "Don't assume - investigate"
Complex/risky task                 → "Use full Empirica workflow"
AI already gave recommendations    → "Wait - did you investigate?"
First time user                    → "Let me introduce Empirica..."
Want to enforce workflow           → "Required: show preflight/postflight"
Checking calibration               → "Use empirica postflight"
```

---

## ✅ Success Criteria

**You know the prompt worked when AI:**
1. ✅ Actually runs Empirica commands (preflight/investigate/postflight)
2. ✅ Shows epistemic assessment scores
3. ✅ Acknowledges uncertainty explicitly
4. ✅ Investigates when uncertain (doesn't guess)
5. ✅ Makes evidence-based recommendations
6. ✅ Cites specific sources (files, lines, data)
7. ✅ Measures learning delta
8. ✅ Reports calibration status

---

## 🎯 The Key Insight

**The problem isn't that AIs don't know HOW to assess uncertainty.**

**The problem is they don't realize they SHOULD.**

**These prompts make the AI:**
- Pause before acting
- Use the actual Empirica system
- Investigate before guessing
- Measure their own calibration

**That's what makes these prompts different from the methodology docs!**

---

## 💡 Usage Tips

### Tip 1: Be Explicit
Don't assume AI will use Empirica automatically.
Explicitly tell it to: "Use empirica preflight"

### Tip 2: Enforce Workflow
For important tasks, require: "Show me preflight before proceeding"

### Tip 3: Catch Early
Interrupt overconfident responses: "Wait - did you investigate?"

### Tip 4: Train Over Time
After several uses, AI learns the pattern: "Use Empirica for complex tasks"

### Tip 5: Measure Impact
Track: How often investigation prevented errors?

---

## 🚀 Getting Started

### This Week:
```
Try this prompt on your next AI task:

"Before you make recommendations, please use Empirica:
empirica preflight '<your task>'
Show me your assessment before proceeding."

See how it changes the response!
```

### This Month:
```
Make it your default:

"For all complex tasks, use the Empirica workflow:
preflight → investigate if uncertain → postflight

I'll expect to see your epistemic assessment."
```

---

**These prompts get AIs to USE the actual Empirica system, not replace it!** 🎯
